"""
🧠 AetherOS ADK Client - Core Types & Interfaces
=================================================
Type-safe abstractions for Google ADK SDK integration.
Supports both Python and provides TypeScript definitions.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Protocol, TypeVar,
    Union, Awaitable, Type, Callable
)
from urllib.parse import urlparse
import threading

# ============================================================================
# Configuration Types
# ============================================================================

class Environment(str, Enum):
    """Supported runtime environments."""
    BROWSER = "browser"
    NODEJS = "nodejs"
    SERVERLESS = "serverless"


@dataclass(frozen=True)
class ADKConfig:
    """
    Immutable configuration for ADK Client.
    
    All fields are read-only after construction to ensure thread-safety.
    """
    project_id: str
    location: str = "us-central1"
    model: str = "gemini-2.0-flash"
    
    # Connection Settings
    max_connections: int = 100
    max_keepalive_connections: int = 20
    connection_timeout: float = 30.0
    read_timeout: float = 60.0
    
    # Retry Settings
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff_factor: float = 2.0
    retry_on_status_codes: List[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])
    
    # Circuit Breaker Settings
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0
    circuit_breaker_half_open_max_calls: int = 3
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Feature Flags
    enable_telemetry: bool = True
    enable_logging: bool = True
    enable_request_interceptors: bool = True
    enable_response_interceptors: bool = True
    
    # Environment
    environment: Environment = Environment.NODEJS
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        if not self.project_id:
            errors.append("project_id is required")
        
        if not self.location:
            errors.append("location is required")
            
        if self.max_connections < 1:
            errors.append("max_connections must be >= 1")
            
        if self.max_retries < 0:
            errors.append("max_retries must be >= 0")
            
        if self.retry_backoff_factor < 1.0:
            errors.append("retry_backoff_factor must be >= 1.0")
            
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_id": self.project_id,
            "location": self.location,
            "model": self.model,
            "max_connections": self.max_connections,
            "max_keepalive_connections": self.max_keepalive_connections,
            "connection_timeout": self.connection_timeout,
            "read_timeout": self.read_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "retry_backoff_factor": self.retry_backoff_factor,
            "retry_on_status_codes": self.retry_on_status_codes,
            "circuit_breaker_enabled": self.circuit_breaker_enabled,
            "circuit_breaker_failure_threshold": self.circuit_breaker_failure_threshold,
            "circuit_breaker_recovery_timeout": self.circuit_breaker_recovery_timeout,
            "circuit_breaker_half_open_max_calls": self.circuit_breaker_half_open_max_calls,
            "rate_limit_enabled": self.rate_limit_enabled,
            "rate_limit_requests_per_minute": self.rate_limit_requests_per_minute,
            "rate_limit_burst": self.rate_limit_burst,
            "enable_telemetry": self.enable_telemetry,
            "enable_logging": self.enable_logging,
            "enable_request_interceptors": self.enable_request_interceptors,
            "enable_response_interceptors": self.enable_response_interceptors,
            "environment": self.environment.value
        }


# ============================================================================
# Authentication Types
# ============================================================================

class AuthType(str, Enum):
    """Supported authentication methods."""
    API_KEY = "api_key"
    SERVICE_ACCOUNT = "service_account"
    OAUTH2 = "oauth2"
    Bearer = "bearer"


@dataclass
class AuthCredentials:
    """Authentication credentials container."""
    auth_type: AuthType
    api_key: Optional[str] = None
    service_account_path: Optional[str] = None
    service_account_json: Optional[Dict[str, Any]] = None
    oauth2_token: Optional[str] = None
    token_refresh_callback: Optional[Callable[[], Awaitable[str]]] = None
    
    def validate(self) -> List[str]:
        """Validate credentials."""
        errors = []
        
        if self.auth_type == AuthType.API_KEY and not self.api_key:
            errors.append("API key is required for API_KEY auth")
            
        if self.auth_type == AuthType.SERVICE_ACCOUNT:
            if not self.service_account_path and not self.service_account_json:
                errors.append("Service account path or JSON required for SERVICE_ACCOUNT auth")
                
        return errors


# ============================================================================
# Request/Response Types
# ============================================================================

@dataclass
class ADKRequest:
    """Base request container for ADK operations."""
    agent_id: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "message": self.message,
            "context": self.context,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ADKResponse:
    """Base response container for ADK operations."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    request_id: Optional[str] = None
    latency_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "request_id": self.request_id,
            "latency_ms": self.latency_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# Agent Types
# ============================================================================

@dataclass
class ADKAgent:
    """Represents an ADK agent."""
    agent_id: str
    name: str
    description: str = ""
    model: str = "gemini-2.0-flash"
    capabilities: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    instructions: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "instructions": self.instructions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class ADKSession:
    """Represents an ADK session."""
    session_id: str
    agent_id: str
    user_id: str
    status: str = "active"
    context: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "user_id": self.user_id,
            "status": self.status,
            "context": self.context,
            "messages": self.messages,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================================
# Interceptor Types
# ============================================================================

T = TypeVar('T')

InterceptorFunc = Callable[[Dict[str, Any]], Dict[str, Any]]
ResponseInterceptorFunc = Callable[[ADKResponse], ADKResponse]
ErrorInterceptorFunc = Callable[[Exception], Optional[ADKResponse]]


@dataclass
class InterceptorChain(Generic[T]):
    """Chain of interceptors for request/response processing."""
    interceptors: List[Callable[[T], T]] = field(default_factory=list)
    
    def add(self, interceptor: Callable[[T], T]) -> InterceptorChain[T]:
        """Add interceptor to chain (fluent interface)."""
        self.interceptors.append(interceptor)
        return self
    
    def execute(self, data: T) -> T:
        """Execute all interceptors in order."""
        result = data
        for interceptor in self.interceptors:
            result = interceptor(result)
        return result
    
    async def execute_async(self, data: T) -> T:
        """Execute all interceptors asynchronously."""
        result = data
        for interceptor in self.interceptors:
            if asyncio.iscoroutinefunction(interceptor):
                result = await interceptor(result)
            else:
                result = interceptor(result)
        return result


# ============================================================================
# Telemetry Types
# ============================================================================

@dataclass
class TelemetryEvent:
    """Telemetry event for monitoring."""
    event_type: str
    timestamp: datetime
    duration_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


TelemetryCallback = Callable[[TelemetryEvent], None]
AsyncTelemetryCallback = Callable[[TelemetryEvent], Awaitable[None]]


# ============================================================================
# Connection Pool Types
# ============================================================================

@dataclass
class PoolConfig:
    """Connection pool configuration."""
    max_size: int = 100
    min_size: int = 1
    max_idle_time: float = 300.0
    max_overflow: int = 10
    timeout: float = 30.0
    recycle_time: float = 3600.0
    
    def validate(self) -> List[str]:
        errors = []
        if self.max_size < self.min_size:
            errors.append("max_size must be >= min_size")
        if self.max_size < 1:
            errors.append("max_size must be >= 1")
        return errors


# Type aliases for clarity
JSON = Union[Dict[str, Any], List[Any], str, int, float, bool, None]
RequestHandler = Callable[[ADKRequest], Awaitable[ADKResponse]]
Middleware = Callable[[RequestHandler], RequestHandler]
