"""
Resilience utilities for handling API failures, timeouts, and retries.

Provides decorators and utilities for robust API calls with automatic
fallbacks and error recovery.
"""

import asyncio
import functools
from typing import Callable, Any, Optional
from loguru import logger


class APIError(Exception):
    """Base exception for API errors."""
    pass


class TimeoutError(APIError):
    """Timeout exception."""
    pass


class ProviderUnavailableError(APIError):
    """Provider unavailable exception."""
    pass


async def with_retry(
    func: Callable,
    max_retries: int = 3,
    timeout_seconds: float = 5.0,
    backoff_factor: float = 1.5,
    on_error: Optional[Callable] = None,
) -> Any:
    """
    Execute an async function with retry logic and timeout.
    
    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        timeout_seconds: Timeout for each attempt
        backoff_factor: Multiplier for backoff between retries
        on_error: Optional callback on each error
    
    Returns:
        Result from function
        
    Raises:
        APIError: If all retries exhausted
    """
    last_exception = None
    wait_time = 0.5  # Initial wait time
    
    for attempt in range(max_retries):
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(),
                timeout=timeout_seconds
            )
            return result
            
        except asyncio.TimeoutError as e:
            last_exception = TimeoutError(f"Timeout after {timeout_seconds}s")
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} timed out "
                f"after {timeout_seconds}s"
            )
            
        except Exception as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}"
            )
        
        # Call error handler if provided
        if on_error:
            try:
                await on_error(last_exception, attempt)
            except Exception as callback_error:
                logger.error(f"Error callback failed: {callback_error}")
        
        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            await asyncio.sleep(wait_time)
            wait_time *= backoff_factor
    
    # All retries exhausted
    error_msg = f"All {max_retries} attempts failed"
    if last_exception:
        error_msg += f": {last_exception}"
    
    raise ProviderUnavailableError(error_msg)


async def with_fallback(
    primary_func: Callable,
    fallback_func: Callable,
    timeout_seconds: float = 5.0,
) -> tuple[Any, str]:
    """
    Execute primary function with automatic fallback on failure.
    
    Args:
        primary_func: Primary async function to try
        fallback_func: Fallback async function if primary fails
        timeout_seconds: Timeout for primary attempt
    
    Returns:
        Tuple of (result, source) where source is "primary" or "fallback"
    """
    try:
        result = await asyncio.wait_for(
            primary_func(),
            timeout=timeout_seconds
        )
        return result, "primary"
        
    except Exception as e:
        logger.warning(f"Primary function failed: {e}, using fallback")
        
        try:
            result = await fallback_func()
            return result, "fallback"
            
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            raise ProviderUnavailableError(
                f"Both primary and fallback failed: {e}, {fallback_error}"
            )


async def cached_fallback_response(transcript: str) -> str:
    """
    Provide a cached fallback response when all APIs fail.
    
    Args:
        transcript: User's input transcript
    
    Returns:
        Generic fallback response
    """
    fallback_responses = [
        "Maaf kijiye, main abhi thoda slow ho raha hoon. Kya aap phir se keh sakte hain?",
        "Sorry, main temporarily unavailable hoon. Ek minute baad try karein.",
        "Kshama kijiye, technical issue hai. Thoda intezaar karein.",
    ]
    
    # Simple hash to pick consistent response for same input
    index = hash(transcript) % len(fallback_responses)
    return fallback_responses[index]


def retry_on_error(
    max_retries: int = 3,
    timeout_seconds: float = 5.0,
):
    """
    Decorator for adding retry logic to async functions.
    
    Usage:
        @retry_on_error(max_retries=3, timeout_seconds=5.0)
        async def my_api_call():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await with_retry(
                lambda: func(*args, **kwargs),
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
            )
        return wrapper
    return decorator

