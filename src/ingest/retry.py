from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from ingest.logger import get_logger

F = TypeVar("F", bound=Callable)


def with_retry(max_retries: int, delay_seconds: float) -> Callable[[F], F]:
    """Decorator: retry on any exception with exponential backoff."""

    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            log = get_logger()
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        sleep_time = delay_seconds * (2 ** (attempt - 1))
                        log.warning(
                            f"{fn.__name__}: retry {attempt}/{max_retries} "
                            f"after {sleep_time:.1f}s (cause: {last_exc})"
                        )
                        time.sleep(sleep_time)
                    else:
                        time.sleep(delay_seconds)
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
            log.error(f"{fn.__name__}: all {max_retries} retries exhausted — {last_exc}")
            return None

        return wrapper  # type: ignore[return-value]

    return decorator
