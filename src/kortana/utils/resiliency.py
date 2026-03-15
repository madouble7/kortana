import asyncio
import logging
import traceback
from collections.abc import Awaitable, Callable
from typing import Any

import requests

logger = logging.getLogger(__name__)


async def resilient_call(
    func: Callable[..., Awaitable[Any]],
    *args,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions_to_retry: tuple = (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        ConnectionResetError,
    ),
    **kwargs,
) -> Any:
    """
    Executes an async function with exponential backoff and retry logic.
    Designed to handle 'zombie server' issues and transient network errors.
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except exceptions_to_retry as e:
            last_exception = e
            logger.warning(
                f"⚠️ Attempt {attempt}/{max_retries} failed with {type(e).__name__}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            if attempt == max_retries:
                break
            await asyncio.sleep(delay)
            delay *= backoff_factor
        except Exception as e:
            # For non-retryable exceptions, log and re-raise immediately
            logger.error(f"❌ Permanent error in resilient_call: {e}")
            logger.debug(traceback.format_exc())
            raise

    logger.error(
        f"❌ resilient_call failed after {max_retries} attempts. Last error: {last_exception}"
    )
    raise last_exception
