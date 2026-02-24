"""
🧠 AetherOS ADK Client - Retry Logic
====================================
Exponential backoff retry mechanism with jitter.
Handles transient failures gracefully with configurable policies.
"""

from __future__ import annotations

import asyncio
import logging
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, TypeVar, Union

from .exceptions import ADKException, is_retryable_error

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy(str, Enum):
    """Retry strategy types."""
    FIXED = "fixed"                 # Fixed delay between retries
    LINEAR = "linear"               # Linear increase in delay
    EXPONENTIAL = "exponential"     # Exponential backoff
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"  # Recommended default


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3              # Maximum number of retry attempts
    initial_delay: float = 1.0         # Initial delay in seconds
    max_delay: float = 60.0            # Maximum delay cap
    backoff_factor: float = 2.0        # Multiplier for exponential backoff
    jitter: bool = True                # Add randomness to prevent thundering herd
    jitter_factor: float = 0.25        # Jitter as fraction of delay (0-1)
    retry_on_status_codes: List[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )                                  # HTTP status codes to retry on
    retry_on_exceptions: tuple = (
        ConnectionError,
        TimeoutError,
        ADKException
    )                                  # Exception types to retry on
    retryable_predicate: Optional[Callable[[Exception], bool]] = None  # Custom retry check
    
    def validate(self) -> List[str]:
        errors = []
        if self.max_attempts < 1:
            errors.append("max_attempts must be >= 1")
        if self.initial_delay < 0:
            errors.append("initial_delay must be >= 0")
        if self.max_delay < 0:
            errors.append("max_delay must be >= 0")
        if self.backoff_factor < 1.0:
            errors.append("backoff_factor must be >= 1.0")
        if not 0 <= self.jitter_factor <= 1:
            errors.append("jitter_factor must be between 0 and 1")
        return errors


@dataclass
class RetryState:
    """State tracking for retry operations."""
    attempt: int = 0
    total_delay: float = 0.0
    errors: List[Exception] = field(default_factory=list)
    last_attempt_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    
    def record_attempt(self, error: Optional[Exception] = None):
        self.attempt += 1
        self.last_attempt_time = datetime.utcnow()
        if self.started_at is None:
            self.started_at = self.last_attempt_time
        if error:
            self.errors.append(error)
    
    def add_delay(self, delay: float):
        self.total_delay += delay
    
    def reset(self):
        self.attempt = 0
        self.total_delay = 0.0
        self.errors.clear()
        self.last_attempt_time = None
        self.started_at = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt": self.attempt,
            "total_delay": self.total_delay,
            "error_count": len(self.errors),
            "last_attempt_time": self.last_attempt_time.isoformat() if self.last_attempt_time else None,
            "started_at": self.started_at.isoformat() if self.started_at else None
        }


class RetryPolicy:
    """
    Encapsulates retry logic with exponential backoff.
    
    Supports multiple strategies:
    - FIXED: Same delay between retries
    - LINEAR: Delay increases linearly
    - EXPONENTIAL: Delay increases exponentially (recommended)
    - EXPONENTIAL_WITH_JITTER: Adds randomness (recommended for production)
    """
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_WITH_JITTER
    ):
        self.config = config or RetryConfig()
        self.strategy = strategy
        
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Invalid retry config: {errors}")
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt number.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.config.initial_delay
            
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.config.initial_delay * attempt
            
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.initial_delay * (self.config.backoff_factor ** (attempt - 1))
            
        elif self.strategy == RetryStrategy.EXPONENTIAL_WITH_JITTER:
            base_delay = self.config.initial_delay * (self.config.backoff_factor ** (attempt - 1))
            jitter = base_delay * self.config.jitter_factor * random.random()
            delay = base_delay + jitter
            
        else:
            delay = self.config.initial_delay
        
        # Cap at max delay
        return min(delay, self.config.max_delay)
    
    def should_retry(
        self,
        attempt: int,
        error: Exception,
        status_code: Optional[int] = None
    ) -> bool:
        """
        Determine if operation should be retried.
        
        Args:
            attempt: Current attempt number
            error: The exception that occurred
            status_code: HTTP status code if applicable
            
        Returns:
            True if should retry, False otherwise
        """
        # Check max attempts
        if attempt >= self.config.max_attempts:
            return False
        
        # Check custom predicate first
        if self.config.retryable_predicate:
            return self.config.retryable_predicate(error)
        
        # Check if error is retryable by type
        if isinstance(error, self.config.retryable_exceptions):
            return True
        
        # Check if status code is retryable
        if status_code and status_code in self.config.retry_on_status_codes:
            return True
        
        # Use general retryable check
        return is_retryable_error(error)
    
    def get_state(self) -> RetryState:
        """Get current retry state (for monitoring)."""
        return self._state
    
    def __repr__(self) -> str:
        return f"RetryPolicy({self.strategy.value}, max_attempts={self.config.max_attempts})"


class RetryExecutor:
    """
    Executes operations with retry logic.
    
    Provides both synchronous and asynchronous execution with
    configurable retry policies.
    """
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_WITH_JITTER,
        on_retry: Optional[Callable[[int, Exception, float], None]] = None
    ):
        self.policy = RetryPolicy(config, strategy)
        self.on_retry = on_retry
        self._state = RetryState()
    
    def execute(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Execute function with retry logic (synchronous).
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from successful execution
            
        Raises:
            Last exception if all retries exhausted
        """
        self._state.reset()
        last_error: Optional[Exception] = None
        
        while True:
            self._state.record_attempt(last_error)
            attempt = self._state.attempt
            
            try:
                result = func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"Operation succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_error = e
                
                if not self.policy.should_retry(attempt, e):
                    logger.warning(
                        f"Operation failed on attempt {attempt}, not retrying: {e}"
                    )
                    raise
                
                if attempt >= self.policy.config.max_attempts:
                    logger.error(
                        f"Operation failed after {attempt} attempts: {e}"
                    )
                    raise
                
                # Calculate and apply delay
                delay = self.policy.calculate_delay(attempt)
                self._state.add_delay(delay)
                
                logger.info(
                    f"Operation failed on attempt {attempt}, "
                    f"retrying in {delay:.2f}s: {e}"
                )
                
                if self.on_retry:
                    self.on_retry(attempt, e, delay)
                
                time.sleep(delay)
    
    async def execute_async(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any
    ) -> T:
        """
        Execute async function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from successful execution
            
        Raises:
            Last exception if all retries exhausted
        """
        self._state.reset()
        last_error: Optional[Exception] = None
        
        while True:
            self._state.record_attempt(last_error)
            attempt = self._state.attempt
            
            try:
                result = await func(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"Operation succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_error = e
                
                if not self.policy.should_retry(attempt, e):
                    logger.warning(
                        f"Operation failed on attempt {attempt}, not retrying: {e}"
                    )
                    raise
                
                if attempt >= self.policy.config.max_attempts:
                    logger.error(
                        f"Operation failed after {attempt} attempts: {e}"
                    )
                    raise
                
                # Calculate and apply delay
                delay = self.policy.calculate_delay(attempt)
                self._state.add_delay(delay)
                
                logger.info(
                    f"Operation failed on attempt {attempt}, "
                    f"retrying in {delay:.2f}s: {e}"
                )
                
                if self.on_retry:
                    self.on_retry(attempt, e, delay)
                
                await asyncio.sleep(delay)
    
    @property
    def state(self) -> RetryState:
        """Get current retry state."""
        return self._state
    
    def reset(self):
        """Reset retry state."""
        self._state.reset()


# Convenience function for creating retry executors
def create_retry_executor(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_WITH_JITTER,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None
) -> RetryExecutor:
    """Create a retry executor with common settings."""
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay
    )
    return RetryExecutor(config, strategy, on_retry)
