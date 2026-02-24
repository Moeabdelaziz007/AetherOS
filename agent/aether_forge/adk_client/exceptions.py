"""
🧠 AetherOS ADK Client - Custom Exceptions
==========================================
Comprehensive error handling with custom exception types.
Follows REST API error conventions and includes retry guidance.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Type
import traceback


class ADKException(Exception):
    """Base exception for all ADK client errors."""
    
    def __init__(
        self, 
        message: str, 
        code: str = "UNKNOWN_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.retryable = retryable
        self._cause: Optional[Exception] = None
    
    @property
    def is_retryable(self) -> bool:
        """Check if the error is retryable."""
        return self.retryable
    
    def with_cause(self, cause: Exception) -> ADKException:
        """Add cause information."""
        self._cause = cause
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "status_code": self.status_code,
            "details": self.details,
            "retryable": self.retryable,
            "cause": str(self._cause) if self._cause else None
        }
    
    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.retryable:
            parts.append("(retryable)")
        if self._cause:
            parts.append(f"Caused by: {self._cause}")
        return " ".join(parts)


# ============================================================================
# Authentication Errors
# ============================================================================

class ADKAuthenticationError(ADKException):
    """Raised when authentication fails."""
    
    def __init__(
        self, 
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details,
            retryable=False
        )


class ADKAuthorizationError(ADKException):
    """Raised when authorization fails (insufficient permissions)."""
    
    def __init__(
        self, 
        message: str = "Authorization failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details,
            retryable=False
        )


class ADKTokenExpiredError(ADKAuthenticationError):
    """Raised when the access token has expired."""
    
    def __init__(self, message: str = "Access token has expired"):
        super().__init__(
            message=message,
            details={"error_type": "token_expired"}
        )


class ADKInvalidCredentialsError(ADKAuthenticationError):
    """Raised when credentials are invalid."""
    
    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(
            message=message,
            details={"error_type": "invalid_credentials"}
        )


# ============================================================================
# Client Errors (4xx)
# ============================================================================

class ADKClientError(ADKException):
    """Base class for client-side errors (4xx)."""
    pass


class ADKNotFoundError(ADKClientError):
    """Raised when a resource is not found."""
    
    def __init__(
        self, 
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details,
            retryable=False
        )


class ADKBadRequestError(ADKClientError):
    """Raised when request is malformed or invalid."""
    
    def __init__(
        self, 
        message: str = "Bad request",
        validation_errors: Optional[List[Dict[str, Any]]] = None
    ):
        details = {}
        if validation_errors:
            details["validation_errors"] = validation_errors
            
        super().__init__(
            message=message,
            code="BAD_REQUEST",
            status_code=400,
            details=details,
            retryable=False
        )


class ADKValidationError(ADKBadRequestError):
    """Raised when request validation fails."""
    
    def __init__(
        self, 
        message: str = "Validation failed",
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None
    ):
        validation_errors = []
        error = {"message": message}
        if field:
            error["field"] = field
        if value is not None:
            error["value"] = str(value)
        if constraint:
            error["constraint"] = constraint
        validation_errors.append(error)
        
        super().__init__(
            message=message,
            validation_errors=validation_errors
        )


class ADKRateLimitError(ADKClientError):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
        if limit:
            details["limit"] = limit
            
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
            retryable=True
        )


class ADKQuotaExceededError(ADKClientError):
    """Raised when quota is exceeded."""
    
    def __init__(
        self, 
        message: str = "Quota exceeded",
        quota_type: Optional[str] = None,
        limit: Optional[int] = None
    ):
        details = {}
        if quota_type:
            details["quota_type"] = quota_type
        if limit:
            details["limit"] = limit
            
        super().__init__(
            message=message,
            code="QUOTA_EXCEEDED",
            status_code=402,
            details=details,
            retryable=True
        )


# ============================================================================
# Server Errors (5xx)
# ============================================================================

class ADKServerError(ADKException):
    """Base class for server-side errors (5xx)."""
    
    def __init__(
        self, 
        message: str = "Internal server error",
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            code=code,
            status_code=500,
            details=details,
            retryable=True
        )


class ADKServiceUnavailableError(ADKServerError):
    """Raised when service is temporarily unavailable."""
    
    def __init__(
        self, 
        message: str = "Service unavailable",
        retry_after: Optional[int] = None
    ):
        details = {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            code="SERVICE_UNAVAILABLE",
            details=details
        )


class ADKTimeoutError(ADKServerError):
    """Raised when request times out."""
    
    def __init__(self, message: str = "Request timed out"):
        super().__init__(
            message=message,
            code="TIMEOUT",
            status_code=504,
            retryable=True
        )


class ADKInternalError(ADKServerError):
    """Raised for internal server errors."""
    
    def __init__(self, message: str = "Internal error"):
        super().__init__(message=message, code="INTERNAL_ERROR")


class ADKBadGatewayError(ADKServerError):
    """Raised when upstream service fails."""
    
    def __init__(self, message: str = "Bad gateway"):
        super().__init__(
            message=message,
            code="BAD_GATEWAY",
            status_code=502,
            retryable=True
        )


# ============================================================================
# Connection & Network Errors
# ============================================================================

class ADKConnectionError(ADKException):
    """Raised when connection fails."""
    
    def __init__(
        self, 
        message: str = "Connection failed",
        host: Optional[str] = None
    ):
        details = {}
        if host:
            details["host"] = host
            
        super().__init__(
            message=message,
            code="CONNECTION_ERROR",
            status_code=503,
            details=details,
            retryable=True
        )


class ADKNetworkError(ADKConnectionError):
    """Raised for general network errors."""
    pass


class ADKSSLError(ADKConnectionError):
    """Raised for SSL/TLS errors."""
    
    def __init__(self, message: str = "SSL/TLS error"):
        super().__init__(
            message=message,
            details={"error_type": "ssl_error"}
        )


# ============================================================================
# Circuit Breaker Errors
# ============================================================================

class ADKCircuitBreakerError(ADKException):
    """Raised when circuit breaker is open."""
    
    def __init__(
        self, 
        message: str = "Circuit breaker is open",
        state: Optional[str] = None,
        retry_after: Optional[float] = None
    ):
        details = {}
        if state:
            details["state"] = state
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            code="CIRCUIT_BREAKER_OPEN",
            status_code=503,
            details=details,
            retryable=True
        )


# ============================================================================
# Agent & Session Errors
# ============================================================================

class ADKAgentError(ADKException):
    """Base class for agent-related errors."""
    pass


class ADKAgentNotFoundError(ADKAgentError, ADKNotFoundError):
    """Raised when agent is not found."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            message=f"Agent not found: {agent_id}",
            resource_type="agent",
            resource_id=agent_id
        )
        self.agent_id = agent_id


class ADKSessionError(ADKAgentError):
    """Base class for session-related errors."""
    pass


class ADKSessionNotFoundError(ADKSessionError, ADKNotFoundError):
    """Raised when session is not found."""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session not found: {session_id}",
            resource_type="session",
            resource_id=session_id
        )
        self.session_id = session_id


class ADKSessionExpiredError(ADKSessionError):
    """Raised when session has expired."""
    
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session expired: {session_id}",
            details={"session_id": session_id}
        )
        self.session_id = session_id


# ============================================================================
# Rate Limiting Errors
# ============================================================================

class ADKRateLimiterError(ADKException):
    """Raised when rate limiter rejects a request."""
    
    def __init__(
        self, 
        message: str = "Rate limit exceeded",
        available_in: Optional[float] = None
    ):
        details = {}
        if available_in:
            details["available_in"] = available_in
            
        super().__init__(
            message=message,
            code="RATE_LIMITED",
            status_code=429,
            details=details,
            retryable=True
        )


# ============================================================================
# Configuration Errors
# ============================================================================

class ADKConfigError(ADKException):
    """Raised for configuration errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
            
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            status_code=500,
            details=details,
            retryable=False
        )


# ============================================================================
# Error Factory
# ============================================================================

class ADKErrorFactory:
    """Factory for creating appropriate exceptions from error responses."""
    
    # Mapping of status codes to exception classes
    STATUS_CODE_MAP: Dict[int, Type[ADKException]] = {
        400: ADKBadRequestError,
        401: ADKAuthenticationError,
        403: ADKAuthorizationError,
        404: ADKNotFoundError,
        429: ADKRateLimitError,
        500: ADKInternalError,
        502: ADKBadGatewayError,
        503: ADKServiceUnavailableError,
        504: ADKTimeoutError,
    }
    
    # Mapping of error codes to exception classes
    ERROR_CODE_MAP: Dict[str, Type[ADKException]] = {
        "AUTHENTICATION_ERROR": ADKAuthenticationError,
        "AUTHORIZATION_ERROR": ADKAuthorizationError,
        "NOT_FOUND": ADKNotFoundError,
        "BAD_REQUEST": ADKBadRequestError,
        "VALIDATION_ERROR": ADKValidationError,
        "RATE_LIMIT_EXCEEDED": ADKRateLimitError,
        "QUOTA_EXCEEDED": ADKQuotaExceededError,
        "INTERNAL_ERROR": ADKInternalError,
        "SERVICE_UNAVAILABLE": ADKServiceUnavailableError,
        "TIMEOUT": ADKTimeoutError,
        "BAD_GATEWAY": ADKBadGatewayError,
        "CONNECTION_ERROR": ADKConnectionError,
        "CIRCUIT_BREAKER_OPEN": ADKCircuitBreakerError,
    }
    
    @classmethod
    def from_response(
        cls,
        status_code: int,
        error_code: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> ADKException:
        """Create exception from HTTP response."""
        # Try error code first
        if error_code and error_code in cls.ERROR_CODE_MAP:
            error_class = cls.ERROR_CODE_MAP[error_code]
            return error_class(message or "Unknown error", details=details)
        
        # Fall back to status code
        if status_code in cls.STATUS_CODE_MAP:
            error_class = cls.STATUS_CODE_MAP[status_code]
            return error_class(message or "Unknown error", details=details)
        
        # Default to server error for unknown codes >= 500
        if status_code >= 500:
            return ADKServerError(message or "Server error", details=details)
        
        return ADKClientError(message or "Client error", details=details)
    
    @classmethod
    def from_exception(cls, exc: Exception) -> ADKException:
        """Convert standard exception to ADK exception."""
        if isinstance(exc, ADKException):
            return exc
        
        # Handle common exception types
        if isinstance(exc, TimeoutError):
            return ADKTimeoutError(str(exc)).with_cause(exc)
        
        if isinstance(exc, ConnectionError):
            return ADKConnectionError(str(exc)).with_cause(exc)
        
        if isinstance(exc, ValueError):
            return ADKValidationError(str(exc)).with_cause(exc)
        
        # Default to unknown error
        return ADKException(str(exc)).with_cause(exc)


# ============================================================================
# Exception Helpers
# ============================================================================

def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable."""
    if isinstance(error, ADKException):
        return error.is_retryable
    
    # Retry on network errors
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True
    
    return False


def get_error_message(error: Exception) -> str:
    """Get human-readable error message."""
    if isinstance(error, ADKException):
        return str(error)
    return str(error) or type(error).__name__
