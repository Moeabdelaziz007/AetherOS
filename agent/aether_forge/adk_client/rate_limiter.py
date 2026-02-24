"""
🧠 AetherOS ADK Client - Rate Limiter
=====================================
Thread-safe rate limiter with token bucket algorithm.
Supports both synchronous and asynchronous operations.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, TypeVar

from .exceptions import ADKRateLimiterError

logger = logging.getLogger(__name__)

T = TypeVar('T')


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 60       # Token refill rate
    burst_limit: int = 10                 # Maximum bucket size
    initial_tokens: Optional[int] = None  # Initial tokens (defaults to burst_limit)
    refill_interval: float = 1.0          # Seconds between refills
    
    def __post_init__(self):
        if self.initial_tokens is None:
            self.initial_tokens = self.burst_limit
    
    def validate(self) -> list:
        errors = []
        if self.requests_per_minute < 1:
            errors.append("requests_per_minute must be >= 1")
        if self.burst_limit < 1:
            errors.append("burst_limit must be >= 1")
        if self.refill_interval <= 0:
            errors.append("refill_interval must be > 0")
        return errors


@dataclass
class RateLimitMetrics:
    """Metrics for rate limiting."""
    total_requests: int = 0
    allowed_requests: int = 0
    rejected_requests: int = 0
    total_wait_time: float = 0.0
    
    def record_allowed(self, wait_time: float = 0.0):
        self.allowed_requests += 1
        self.total_wait_time += wait_time
        self.total_requests += 1
    
    def record_rejected(self):
        self.rejected_requests += 1
        self.total_requests += 1
    
    @property
    def rejection_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.rejected_requests / self.total_requests
    
    @property
    def average_wait_time(self) -> float:
        if self.allowed_requests == 0:
            return 0.0
        return self.total_wait_time / self.allowed_requests
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "rejected_requests": self.rejected_requests,
            "rejection_rate": self.rejection_rate,
            "average_wait_time": self.average_wait_time
        }


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.
    
    The token bucket algorithm allows for burst traffic up to the bucket size
    while maintaining an average rate over time.
    
    Features:
    - Configurable rate and burst limit
    - Thread-safe for concurrent access
    - Async support with awaitable acquire
    - Blocking and non-blocking acquire modes
    - Comprehensive metrics tracking
    """
    
    def __init__(
        self,
        name: str = "default",
        config: Optional[RateLimitConfig] = None,
        on_limit: Optional[Callable[[float], None]] = None
    ):
        self.name = name
        self.config = config or RateLimitConfig()
        self.on_limit = on_limit
        
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Invalid rate limiter config: {errors}")
        
        self._tokens = float(self.config.initial_tokens)
        self._last_refill = time.time()
        self._lock = threading.RLock()
        
        self.metrics = RateLimitMetrics()
        
        logger.info(
            f"Rate limiter '{name}' initialized: "
            f"{self.config.requests_per_minute} req/min, burst={self.config.burst_limit}"
        )
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self._last_refill
        
        # Calculate tokens to add
        tokens_to_add = elapsed * (self.config.requests_per_minute / 60.0)
        
        self._tokens = min(
            self._tokens + tokens_to_add,
            float(self.config.burst_limit)
        )
        self._last_refill = now
    
    def _try_acquire(self, tokens: int = 1) -> float:
        """
        Try to acquire tokens without blocking.
        
        Returns:
            Wait time in seconds if tokens available, -1 if blocked
        """
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                self.metrics.record_allowed()
                return 0.0
            
            # Calculate wait time
            tokens_needed = tokens - self._tokens
            wait_time = tokens_needed / (self.config.requests_per_minute / 60.0)
            
            return wait_time
    
    def acquire(
        self,
        tokens: int = 1,
        blocking: bool = True,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Acquire tokens from the rate limiter.
        
        Args:
            tokens: Number of tokens to acquire
            blocking: Whether to block until tokens available
            timeout: Maximum seconds to wait (None = infinite)
            
        Returns:
            True if tokens acquired, False otherwise
            
        Raises:
            ADKRateLimiterError: If timeout exceeded in blocking mode
        """
        if tokens > self.config.burst_limit:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (max burst: {self.config.burst_limit})"
            )
        
        start_time = time.time()
        
        while True:
            wait_time = self._try_acquire(tokens)
            
            if wait_time == 0.0:
                # Success
                return True
            
            if not blocking:
                # Non-blocking mode - return immediately
                self.metrics.record_rejected()
                return False
            
            # Blocking mode - wait or timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self.metrics.record_rejected()
                    raise ADKRateLimiterError(
                        message=f"Rate limit timeout after {timeout}s",
                        available_in=wait_time
                    )
            
            # Wait for tokens
            logger.debug(f"Rate limiter '{self.name}': waiting {wait_time:.2f}s for tokens")
            time.sleep(min(wait_time, 0.1))  # Sleep in small increments
    
    async def acquire_async(
        self,
        tokens: int = 1,
        blocking: bool = True,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Async version of acquire.
        
        Args:
            tokens: Number of tokens to acquire
            blocking: Whether to block until tokens available
            timeout: Maximum seconds to wait (None = infinite)
            
        Returns:
            True if tokens acquired, False otherwise
            
        Raises:
            ADKRateLimiterError: If timeout exceeded in blocking mode
        """
        if tokens > self.config.burst_limit:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (max burst: {self.config.burst_limit})"
            )
        
        start_time = time.time()
        
        while True:
            wait_time = self._try_acquire(tokens)
            
            if wait_time == 0.0:
                # Success
                return True
            
            if not blocking:
                # Non-blocking mode
                self.metrics.record_rejected()
                return False
            
            # Blocking mode - wait or timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self.metrics.record_rejected()
                    raise ADKRateLimiterError(
                        message=f"Rate limit timeout after {timeout}s",
                        available_in=wait_time
                    )
            
            # Notify about limit
            if self.on_limit:
                self.on_limit(wait_time)
            
            # Async wait
            await asyncio.sleep(min(wait_time, 0.1))
    
    def get_available_tokens(self) -> float:
        """Get current available tokens."""
        with self._lock:
            self._refill()
            return self._tokens
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get wait time for specified tokens."""
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                return 0.0
            
            tokens_needed = tokens - self._tokens
            return tokens_needed / (self.config.requests_per_minute / 60.0)
    
    def reset(self):
        """Reset the rate limiter to initial state."""
        with self._lock:
            self._tokens = float(self.config.initial_tokens)
            self._last_refill = time.time()
            logger.info(f"Rate limiter '{self.name}' reset")
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get detailed state information."""
        with self._lock:
            return {
                "name": self.name,
                "available_tokens": self._tokens,
                "config": {
                    "requests_per_minute": self.config.requests_per_minute,
                    "burst_limit": self.config.burst_limit,
                    "refill_interval": self.config.refill_interval
                },
                "metrics": self.metrics.to_dict()
            }
    
    def __repr__(self) -> str:
        return f"RateLimiter(name='{self.name}', tokens={self._tokens:.1f})"


class RateLimiterRegistry:
    """Registry for managing multiple rate limiters."""
    
    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
        self._lock = threading.RLock()
    
    def get_or_create(
        self,
        name: str,
        config: Optional[RateLimitConfig] = None,
        on_limit: Optional[Callable[[float], None]] = None
    ) -> RateLimiter:
        """Get existing rate limiter or create new one."""
        with self._lock:
            if name not in self._limiters:
                self._limiters[name] = RateLimiter(name, config, on_limit)
            return self._limiters[name]
    
    def get(self, name: str) -> Optional[RateLimiter]:
        """Get rate limiter by name."""
        with self._lock:
            return self._limiters.get(name)
    
    def remove(self, name: str) -> bool:
        """Remove rate limiter by name."""
        with self._lock:
            if name in self._limiters:
                del self._limiters[name]
                return True
            return False
    
    def reset_all(self):
        """Reset all rate limiters."""
        with self._lock:
            for limiter in self._limiters.values():
                limiter.reset()
    
    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get metrics for all rate limiters."""
        with self._lock:
            return {
                name: limiter.get_state_info()
                for name, limiter in self._limiters.items()
            }
    
    def __len__(self) -> int:
        return len(self._limiters)


# Global registry instance
_rate_limiter_registry = RateLimiterRegistry()


def get_rate_limiter(
    name: str = "default",
    config: Optional[RateLimitConfig] = None
) -> RateLimiter:
    """Get or create a rate limiter from the global registry."""
    return _rate_limiter_registry.get_or_create(name, config)


def reset_all_rate_limiters():
    """Reset all rate limiters in the global registry."""
    _rate_limiter_registry.reset_all()
