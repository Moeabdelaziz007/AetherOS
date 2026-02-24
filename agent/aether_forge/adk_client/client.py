"""
🧠 AetherOS ADK Client - Main Client
=====================================
Production-ready ADK client with all features:
- Connection pooling
- Authentication
- Retry logic
- Circuit breaker
- Rate limiting
- Logging & Telemetry
- Request/Response interceptors
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx

from .types import (
    ADKConfig, ADKRequest, ADKResponse, AuthCredentials, AuthType,
    Environment, InterceptorChain, RequestHandler, TelemetryEvent
)
from .exceptions import (
    ADKException, ADKAuthenticationError, ADKBadRequestError,
    ADKServerError, ADKTimeoutError, ADKErrorFactory
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, get_circuit_breaker
from .rate_limiter import RateLimiter, RateLimitConfig, get_rate_limiter
from .retry import RetryExecutor, RetryConfig, RetryStrategy
from .telemetry import AetherTelemetryHandler, TelemetryEvent as TEvent

logger = logging.getLogger(__name__)


class ADKClient:
    """
    Production-ready ADK client with comprehensive features.
    
    Features:
    - Connection pooling via httpx
    - Configurable authentication
    - Exponential backoff retry
    - Circuit breaker pattern
    - Rate limiting
    - Request/response interceptors
    - Structured logging
    - Telemetry tracking
    
    Example:
        >>> config = ADKConfig(
        ...     project_id="my-project",
        ...     api_key="your-api-key"
        ... )
        >>> client = ADKClient(config)
        >>> response = await client.create_agent("my-agent")
    """
    
    def __init__(
        self,
        config: ADKConfig,
        credentials: Optional[AuthCredentials] = None,
        telemetry: Optional[AetherTelemetryHandler] = None
    ):
        """
        Initialize ADK Client.
        
        Args:
            config: ADK configuration
            credentials: Authentication credentials
            telemetry: Custom telemetry handler
        """
        self.config = config
        self.credentials = credentials
        
        # Initialize telemetry
        self._telemetry = telemetry or AetherTelemetryHandler(
            logger_name="adk_client",
            enable_telemetry=config.enable_telemetry,
            enable_logging=config.enable_logging
        )
        
        # Initialize HTTP client with connection pooling
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=config.connection_timeout,
                read=config.read_timeout
            ),
            limits=httpx.Limits(
                max_connections=config.max_connections,
                max_keepalive_connections=config.max_keepalive_connections
            )
        )
        
        # Initialize circuit breaker
        self._circuit_breaker: Optional[CircuitBreaker] = None
        if config.circuit_breaker_enabled:
            cb_config = CircuitBreakerConfig(
                failure_threshold=config.circuit_breaker_failure_threshold,
                timeout=config.circuit_breaker_recovery_timeout,
                half_open_max_calls=config.circuit_breaker_half_open_max_calls
            )
            self._circuit_breaker = get_circuit_breaker("adk_client", cb_config)
        
        # Initialize rate limiter
        self._rate_limiter: Optional[RateLimiter] = None
        if config.rate_limit_enabled:
            rl_config = RateLimitConfig(
                requests_per_minute=config.rate_limit_requests_per_minute,
                burst_limit=config.rate_limit_burst
            )
            self._rate_limiter = get_rate_limiter("adk_client", rl_config)
        
        # Initialize retry executor
        retry_config = RetryConfig(
            max_attempts=config.max_retries,
            initial_delay=config.retry_delay,
            backoff_factor=config.retry_backoff_factor,
            retry_on_status_codes=config.retry_on_status_codes
        )
        self._retry_executor = RetryExecutor(
            config=retry_config,
            strategy=RetryStrategy.EXPONENTIAL_WITH_JITTER,
            on_retry=self._on_retry
        )
        
        # Initialize interceptors
        self._request_interceptors = InterceptorChain[Dict[str, Any]]()
        self._response_interceptors = InterceptorChain[ADKResponse]()
        
        # Add default interceptors
        if config.enable_request_interceptors:
            self._add_default_request_interceptors()
        
        if config.enable_response_interceptors:
            self._add_default_response_interceptors()
        
        self._base_url = self._build_base_url()
        
        logger.info(f"ADK Client initialized for project: {config.project_id}")
    
    def _build_base_url(self) -> str:
        """Build base URL for API requests."""
        return f"https://{self.config.location}-aiplatform.googleapis.com/v1/"
    
    def _add_default_request_interceptors(self):
        """Add default request interceptors."""
        
        def add_auth_header(request: Dict[str, Any]) -> Dict[str, Any]:
            if self.credentials:
                if self.credentials.auth_type == AuthType.API_KEY:
                    request["params"] = request.get("params", {})
                    request["params"]["key"] = self.credentials.api_key
                elif self.credentials.auth_type == AuthType.BEARER:
                    request["headers"] = request.get("headers", {})
                    request["headers"]["Authorization"] = f"Bearer {self.credentials.oauth2_token}"
            return request
        
        self._request_interceptors.add(add_auth_header)
    
    def _add_default_response_interceptors(self):
        """Add default response interceptors."""
        
        def log_response(response: ADKResponse) -> ADKResponse:
            if not response.success:
                self._telemetry.warning(
                    f"ADK request failed: {response.error}",
                    error_code=response.error_code
                )
            return response
        
        self._response_interceptors.add(log_response)
    
    def _on_retry(self, attempt: int, error: Exception, delay: float):
        """Callback for retry events."""
        self._telemetry.warning(
            f"Retrying after {delay:.2f}s",
            attempt=attempt,
            error=str(error)
        )
    
    def add_request_interceptor(
        self,
        interceptor: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        """Add a request interceptor."""
        self._request_interceptors.add(interceptor)
    
    def add_response_interceptor(
        self,
        interceptor: Callable[[ADKResponse], ADKResponse]
    ):
        """Add a response interceptor."""
        self._response_interceptors.add(interceptor)
    
    async def _make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with all protections."""
        request_id = str(uuid.uuid4())
        
        # Build request
        request = {
            "method": method,
            "url": urljoin(self._base_url, path),
            "json": data,
            "params": params,
            "headers": headers or {}
        }
        
        # Apply request interceptors
        if self.config.enable_request_interceptors:
            request = self._request_interceptors.execute(request)
        
        # Track request
        with self._telemetry.track_request(
            operation=f"http_{method.lower()}",
            request_id=request_id,
            path=path
        ):
            # Rate limiting
            if self._rate_limiter:
                await self._rate_limiter.acquire_async()
            
            # Circuit breaker
            if self._circuit_breaker:
                await self._circuit_breaker.execute_async(self._execute_request, request)
            else:
                return await self._execute_request(request)
    
    async def _execute_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute HTTP request with retry logic."""
        return await self._retry_executor.execute_async(
            self._http_client.request,
            method=request["method"],
            url=request["url"],
            json=request.get("json"),
            params=request.get("params"),
            headers=request.get("headers", {})
        )
    
    def _build_response(
        self,
        request_id: str,
        http_response: httpx.Response,
        duration_ms: float
    ) -> ADKResponse:
        """Build ADK response from HTTP response."""
        
        try:
            response_data = http_response.json()
        except json.JSONDecodeError:
            response_data = {"data": http_response.text}
        
        # Check for errors
        if http_response.status_code >= 400:
            error_code = response_data.get("error", {}).get("code", "UNKNOWN")
            error_message = response_data.get("error", {}).get("message", "Unknown error")
            
            error = ADKErrorFactory.from_response(
                status_code=http_response.status_code,
                error_code=error_code,
                message=error_message
            )
            
            return ADKResponse(
                success=False,
                error=error_message,
                error_code=error_code,
                request_id=request_id,
                latency_ms=duration_ms,
                metadata={"status_code": http_response.status_code}
            )
        
        return ADKResponse(
            success=True,
            data=response_data,
            request_id=request_id,
            latency_ms=duration_ms
        )
    
    # ========================================================================
    # Public API Methods
    # ========================================================================
    
    async def create_agent(
        self,
        name: str,
        model: str = "gemini-2.0-flash",
        description: str = "",
        instructions: str = "",
        tools: Optional[List[str]] = None
    ) -> ADKResponse:
        """
        Create a new ADK agent.
        
        Args:
            name: Agent name
            model: Model to use
            description: Agent description
            instructions: System instructions
            tools: List of tool names
            
        Returns:
            ADKResponse with agent data
        """
        path = f"projects/{self.config.project_id}/agents"
        data = {
            "display_name": name,
            "model": model,
            "description": description,
            "instructions": instructions,
            "tools": tools or []
        }
        
        response = await self._make_request("POST", path, data=data)
        
        return self._build_response(
            request_id=str(uuid.uuid4()),
            http_response=response,
            duration_ms=0.0
        )
    
    async def list_agents(
        self,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> ADKResponse:
        """
        List all ADK agents.
        
        Args:
            page_size: Number of results per page
            page_token: Token for pagination
            
        Returns:
            ADKResponse with agent list
        """
        path = f"projects/{self.config.project_id}/agents"
        params = {"page_size": page_size}
        if page_token:
            params["page_token"] = page_token
        
        response = await self._make_request("GET", path, params=params)
        
        return self._build_response(
            request_id=str(uuid.uuid4()),
            http_response=response,
            duration_ms=0.0
        )
    
    async def get_agent(self, agent_id: str) -> ADKResponse:
        """
        Get agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            ADKResponse with agent data
        """
        path = f"projects/{self.config.project_id}/agents/{agent_id}"
        
        response = await self._make_request("GET", path)
        
        return self._build_response(
            request_id=str(uuid.uuid4()),
            http_response=response,
            duration_ms=0.0
        )
    
    async def delete_agent(self, agent_id: str) -> ADKResponse:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            ADKResponse with deletion status
        """
        path = f"projects/{self.config.project_id}/agents/{agent_id}"
        
        response = await self._make_request("DELETE", path)
        
        return self._build_response(
            request_id=str(uuid.uuid4()),
            http_response=response,
            duration_ms=0.0
        )
    
    async def create_session(
        self,
        agent_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ADKResponse:
        """
        Create a new session.
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            context: Initial context
            
        Returns:
            ADKResponse with session data
        """
        path = f"projects/{self.config.project_id}/agents/{agent_id}/sessions"
        data = {
            "user_id": user_id,
            "context": context or {}
        }
        
        response = await self._make_request("POST", path, data=data)
        
        return self._build_response(
            request_id=str(uuid.uuid4()),
            http_response=response,
            duration_ms=0.0
        )
    
    async def send_message(
        self,
        agent_id: str,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ADKResponse:
        """
        Send a message to an agent session.
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            message: Message content
            context: Additional context
            
        Returns:
            ADKResponse with agent reply
        """
        path = f"projects/{self.config.project_id}/agents/{agent_id}/sessions/{session_id}:sendMessage"
        data = {
            "message": {
                "content": message
            },
            "context": context or {}
        }
        
        response = await self._make_request("POST", path, data=data)
        
        return self._build_response(
            request_id=str(uuid.uuid4()),
            http_response=response,
            duration_ms=0.0
        )
    
    async def close(self):
        """Close the client and cleanup resources."""
        await self._http_client.aclose()
        self._telemetry.flush()
        logger.info("ADK Client closed")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        if self._circuit_breaker:
            return self._circuit_breaker.get_state_info()
        return {"enabled": False}
    
    def get_rate_limiter_status(self) -> Dict[str, Any]:
        """Get rate limiter status."""
        if self._rate_limiter:
            return self._rate_limiter.get_state_info()
        return {"enabled": False}
    
    def get_telemetry_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[TEvent]:
        """Get recent telemetry events."""
        return self._telemetry.get_telemetry_events(event_type, limit)


# ========================================================================
# Factory Functions
# ========================================================================

def create_client(
    project_id: str,
    api_key: str,
    location: str = "us-central1",
    **kwargs
) -> ADKClient:
    """
    Factory function to create ADK client with API key authentication.
    
    Example:
        >>> client = create_client(
        ...     project_id="my-project",
        ...     api_key="your-api-key"
        ... )
    """
    config = ADKConfig(
        project_id=project_id,
        location=location,
        **kwargs
    )
    credentials = AuthCredentials(
        auth_type=AuthType.API_KEY,
        api_key=api_key
    )
    return ADKClient(config, credentials)


async def create_client_async(
    project_id: str,
    api_key: str,
    location: str = "us-central1",
    **kwargs
) -> ADKClient:
    """Async factory function."""
    client = create_client(project_id, api_key, location, **kwargs)
    return client
