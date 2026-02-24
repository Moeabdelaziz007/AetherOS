"""
🧠 AetherOS ADK Client - Circuit Breaker Pattern
================================================
Thread-safe circuit breaker implementation for fault tolerance.
Prevents cascading failures by stopping requests to failing services.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from .exceptions import ADKCircuitBreakerError, is_retryable_error

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation, requests pass through
    OPEN = "open"          # Failure threshold exceeded, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5          # Failures before opening circuit
    success_threshold: int = 3           # Successes to close circuit from half-open
    timeout: float = 60.0                # Seconds before trying half-open
    half_open_max_calls: int = 3         # Max concurrent calls in half-open
    excluded_exceptions: tuple = ()       # Exceptions that don't count as failures
    
    def validate(self) -> list:
        errors = []
        if self.failure_threshold < 1:
            errors.append("failure_threshold must be >= 1")
        if self.success_threshold < 1:
            errors.append("success_threshold must be >= 1")
        if self.timeout < 0:
            errors.append("timeout must be >= 0")
        return errors


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_state_change: Optional[datetime] = None
    
    def record_success(self):
        self.successful_calls += 1
        self.last_success_time = datetime.utcnow()
    
    def record_failure(self):
        self.failed_calls += 1
        self.last_failure_time = datetime.utcnow()
    
    def record_rejection(self):
        self.rejected_calls += 1
    
    def record_call(self):
        self.total_calls += 1
    
    def record_state_change(self):
        self.state_changes += 1
        self.last_state_change = datetime.utcnow()
    
    @property
    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls
    
    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.successful_calls / self.total_calls
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "rejected_calls": self.rejected_calls,
            "state_changes": self.state_changes,
            "failure_rate": self.failure_rate,
            "success_rate": self.success_rate,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_state_change": self.last_state_change.isoformat() if self.last_state_change else None
        }


class CircuitBreaker:
    """
    Thread-safe circuit breaker implementation.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests are rejected immediately
    - HALF_OPEN: Testing recovery, limited requests allowed
    
    State transitions:
    - CLOSED -> OPEN: When failure threshold is exceeded
    - OPEN -> HALF_OPEN: When timeout expires
    - HALF_OPEN -> CLOSED: When success threshold is met
    - HALF_OPEN -> OPEN: When any call fails in half-open state
    """
    
    def __init__(
        self,
        name: str = "default",
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_state_change_time = time.time()
        self._half_open_calls = 0
        self._lock = threading.RLock()
        
        self.metrics = CircuitBreakerMetrics()
        
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Invalid circuit breaker config: {errors}")
        
        logger.info(f"Circuit breaker '{name}' initialized with state: {self._state.value}")
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            self._check_state_transition()
            return self._state
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open (requests blocked)."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN
    
    def _check_state_transition(self):
        """Check if state should transition based on timeout."""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change_time
            if elapsed >= self.config.timeout:
                self._transition_to(CircuitState.HALF_OPEN)
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        old_state = self._state
        
        if old_state == new_state:
            return
        
        self._state = new_state
        self._last_state_change_time = time.time()
        
        # Reset counters based on new state
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.OPEN:
            self._failure_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0
            self._half_open_calls = 0
        
        self.metrics.record_state_change()
        
        logger.info(
            f"Circuit breaker '{self.name}' state change: {old_state.value} -> {new_state.value}"
        )
        
        if self.on_state_change:
            try:
                self.on_state_change(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
    
    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            self.metrics.record_success()
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    def _record_failure(self):
        """Record a failed call."""
        with self._lock:
            self.metrics.record_failure()
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open opens the circuit
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
    
    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        with self._lock:
            state = self.state  # This triggers state transition check
            
            if state == CircuitState.OPEN:
                self.metrics.record_rejection()
                return False
            
            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.config.half_open_max_calls:
                    self.metrics.record_rejection()
                    return False
                self._half_open_calls += 1
            
            self.metrics.record_call()
            return True
    
    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Execute a function with circuit breaker protection (synchronous).
        
        Raises:
            ADKCircuitBreakerError: If circuit is open
        """
        if not self.can_execute():
            retry_after = self.config.timeout - (time.time() - self._last_state_change_time)
            raise ADKCircuitBreakerError(
                message=f"Circuit breaker '{self.name}' is open",
                state=self._state.value,
                retry_after=max(0, retry_after)
            )
        
        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            # Check if exception should be counted as failure
            if not self._is_excluded_exception(e):
                self._record_failure()
            raise
    
    async def execute_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Execute an async function with circuit breaker protection.
        
        Raises:
            ADKCircuitBreakerError: If circuit is open
        """
        if not self.can_execute():
            retry_after = self.config.timeout - (time.time() - self._last_state_change_time)
            raise ADKCircuitBreakerError(
                message=f"Circuit breaker '{self.name}' is open",
                state=self._state.value,
                retry_after=max(0, retry_after)
            )
        
        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            # Check if exception should be counted as failure
            if not self._is_excluded_exception(e):
                self._record_failure()
            raise
    
    def _is_excluded_exception(self, exception: Exception) -> bool:
        """Check if exception type is in excluded list."""
        return isinstance(exception, self.config.excluded_exceptions)
    
    def reset(self):
        """Manually reset the circuit breaker to closed state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            logger.info(f"Circuit breaker '{self.name}' manually reset")
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get detailed state information."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "half_open_calls": self._half_open_calls,
                "time_in_state": time.time() - self._last_state_change_time,
                "metrics": self.metrics.to_dict()
            }
    
    def __repr__(self) -> str:
        return f"CircuitBreaker(name='{self.name}', state={self._state.value})"


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
    
    def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config, on_state_change)
            return self._breakers[name]
    
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        with self._lock:
            return self._breakers.get(name)
    
    def remove(self, name: str) -> bool:
        """Remove circuit breaker by name."""
        with self._lock:
            if name in self._breakers:
                del self._breakers[name]
                return True
            return False
    
    def reset_all(self):
        """Reset all circuit breakers."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all circuit breakers."""
        with self._lock:
            return {
                name: breaker.get_state_info()
                for name, breaker in self._breakers.items()
            }
    
    def __len__(self) -> int:
        return len(self._breakers)


# Global registry instance
_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str = "default",
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker from the global registry."""
    return _registry.get_or_create(name, config)


def reset_all_circuit_breakers():
    """Reset all circuit breakers in the global registry."""
    _registry.reset_all()
