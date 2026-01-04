"""
Resilience Module for OVN Store Chatbot
Handles retry logic, circuit breaker, and fault tolerance
"""
import time
import functools
import threading
from typing import Callable, Any, Optional, Tuple, TypeVar
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass


T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True


class RetryHandler:
    """
    Handles retry logic with exponential backoff.
    """

    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            import random
            delay = delay * (0.5 + random.random())

        return delay

    def execute_with_retry(
        self,
        func: Callable[..., T],
        *args,
        retryable_exceptions: tuple = (Exception,),
        on_retry: Callable[[int, Exception], None] = None,
        **kwargs
    ) -> Tuple[bool, Optional[T], Optional[Exception]]:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments for func
            retryable_exceptions: Exception types to retry on
            on_retry: Callback on each retry (attempt, exception)
            **kwargs: Keyword arguments for func

        Returns:
            Tuple of (success: bool, result: Optional[T], last_exception: Optional[Exception])
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                return True, result, None

            except retryable_exceptions as e:
                last_exception = e

                if attempt < self.config.max_retries:
                    delay = self._calculate_delay(attempt)

                    if on_retry:
                        on_retry(attempt + 1, e)

                    time.sleep(delay)
                else:
                    # Final attempt failed
                    break

        return False, None, last_exception


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    Prevents cascading failures by failing fast when service is down.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            half_open_max_calls: Max calls in half-open state before deciding
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            return self._check_state()

    def _check_state(self) -> CircuitState:
        """Check and potentially update state based on timeout"""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                elapsed = datetime.now() - self._last_failure_time
                if elapsed.total_seconds() >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
        return self._state

    def _record_success(self) -> None:
        """Record successful call"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    # Enough successes, close circuit
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = max(0, self._failure_count - 1)

    def _record_failure(self) -> None:
        """Record failed call"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._state = CircuitState.OPEN

            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN

    def is_available(self) -> bool:
        """Check if circuit allows calls"""
        state = self.state
        return state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def execute(
        self,
        func: Callable[..., T],
        *args,
        fallback: Callable[..., T] = None,
        **kwargs
    ) -> Tuple[bool, Optional[T], Optional[str]]:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            fallback: Fallback function if circuit is open
            **kwargs: Keyword arguments

        Returns:
            Tuple of (success: bool, result: Optional[T], error: Optional[str])
        """
        state = self.state

        if state == CircuitState.OPEN:
            if fallback:
                try:
                    result = fallback(*args, **kwargs)
                    return True, result, "Using fallback (circuit open)"
                except Exception as e:
                    return False, None, f"Fallback failed: {str(e)}"
            return False, None, "Service temporarily unavailable. Please try again later."

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return True, result, None

        except Exception as e:
            self._record_failure()
            if fallback:
                try:
                    result = fallback(*args, **kwargs)
                    return True, result, f"Using fallback: {str(e)}"
                except Exception as fe:
                    return False, None, f"Both main and fallback failed: {str(fe)}"
            return False, None, str(e)

    def reset(self) -> None:
        """Manually reset circuit to closed state"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0

    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        with self._lock:
            return {
                'state': self._state.value,
                'failure_count': self._failure_count,
                'last_failure': self._last_failure_time.isoformat() if self._last_failure_time else None,
                'failure_threshold': self.failure_threshold,
                'recovery_timeout': self.recovery_timeout
            }


class ResilientExecutor:
    """
    Combines retry logic and circuit breaker for resilient execution.
    """

    def __init__(
        self,
        retry_config: RetryConfig = None,
        failure_threshold: int = 5,
        recovery_timeout: int = 30
    ):
        self.retry_handler = RetryHandler(retry_config)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )

    def execute(
        self,
        func: Callable[..., T],
        *args,
        fallback: Callable[..., T] = None,
        retryable_exceptions: tuple = (Exception,),
        **kwargs
    ) -> Tuple[bool, Optional[T], Optional[str]]:
        """
        Execute function with both retry and circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments
            fallback: Fallback function
            retryable_exceptions: Exceptions to retry on
            **kwargs: Keyword arguments

        Returns:
            Tuple of (success: bool, result: Optional[T], error: Optional[str])
        """
        # Check circuit first
        if not self.circuit_breaker.is_available():
            if fallback:
                try:
                    result = fallback(*args, **kwargs)
                    return True, result, "Using fallback (circuit open)"
                except Exception as e:
                    return False, None, f"Fallback failed: {str(e)}"
            return False, None, "Service temporarily unavailable"

        # Execute with retry
        def on_retry(attempt, exc):
            print(f"Retry attempt {attempt}: {exc}")

        success, result, exception = self.retry_handler.execute_with_retry(
            func,
            *args,
            retryable_exceptions=retryable_exceptions,
            on_retry=on_retry,
            **kwargs
        )

        if success:
            self.circuit_breaker._record_success()
            return True, result, None
        else:
            self.circuit_breaker._record_failure()
            if fallback:
                try:
                    result = fallback(*args, **kwargs)
                    return True, result, f"Using fallback: {str(exception)}"
                except Exception as e:
                    return False, None, f"All attempts failed: {str(e)}"
            return False, None, str(exception) if exception else "Unknown error"


# Decorators for easy use

def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retryable_exceptions: tuple = (Exception,)
):
    """Decorator to add retry logic to a function"""
    config = RetryConfig(max_retries=max_retries, base_delay=base_delay)
    handler = RetryHandler(config)

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            success, result, exception = handler.execute_with_retry(
                func,
                *args,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
            if success:
                return result
            raise exception or Exception("Retry failed")
        return wrapper
    return decorator


def with_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    fallback: Callable = None
):
    """Decorator to add circuit breaker to a function"""
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout
    )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            success, result, error = breaker.execute(func, *args, fallback=fallback, **kwargs)
            if success:
                return result
            raise Exception(error)
        return wrapper
    return decorator


# Global instances for shared use
_executors: dict = {}


def get_executor(name: str = "default") -> ResilientExecutor:
    """Get or create a named resilient executor"""
    if name not in _executors:
        _executors[name] = ResilientExecutor()
    return _executors[name]


def execute_resilient(
    func: Callable[..., T],
    *args,
    executor_name: str = "default",
    fallback: Callable[..., T] = None,
    **kwargs
) -> Tuple[bool, Optional[T], Optional[str]]:
    """
    Convenience function for resilient execution.

    Example:
        success, result, error = execute_resilient(
            api_call,
            param1, param2,
            fallback=lambda p1, p2: default_response
        )
    """
    executor = get_executor(executor_name)
    return executor.execute(func, *args, fallback=fallback, **kwargs)
