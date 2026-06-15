"""LLM chaqiruvlari uchun barqarorlik vositalari: retry va rate-limit.

- AsyncRetrier — vaqtinchalik xatolarda eksponensial backoff bilan qayta urinish.
- Throttler — bir vaqtdagi chaqiruvlar sonini cheklash (semaphore).
"""
from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

import anthropic

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Qayta urinishga arziydigan (vaqtinchalik) xatolar.
_RETRYABLE_ERRORS = (
    anthropic.RateLimitError,
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.InternalServerError,
)


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, _RETRYABLE_ERRORS):
        return True
    if isinstance(exc, anthropic.APIStatusError):
        return exc.status_code in (408, 409, 429) or exc.status_code >= 500
    return False


class AsyncRetrier:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def run(self, factory: Callable[[], Awaitable[T]]) -> T:
        attempt = 0
        while True:
            try:
                return await factory()
            except Exception as exc:  # noqa: BLE001 — qayta urinish uchun ushlanadi
                if not _is_retryable(exc) or attempt >= self._max_retries:
                    raise
                attempt += 1
                delay = self._base_delay * (2 ** (attempt - 1))
                delay += random.uniform(0, self._base_delay)  # jitter
                logger.warning(
                    "LLM chaqiruvi xato (%s). %.1f s dan so'ng qayta urinish %d/%d.",
                    type(exc).__name__,
                    delay,
                    attempt,
                    self._max_retries,
                )
                await asyncio.sleep(delay)


class Throttler:
    """Bir vaqtda ishlaydigan chaqiruvlar sonini cheklaydi."""

    def __init__(self, max_concurrency: int) -> None:
        self._sem = asyncio.Semaphore(max_concurrency)

    async def __aenter__(self) -> Throttler:
        await self._sem.acquire()
        return self

    async def __aexit__(self, *exc_info: object) -> bool:
        self._sem.release()
        return False
