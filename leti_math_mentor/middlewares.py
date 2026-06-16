"""Rate-limit middleware — spam va ortiqcha API xarajatining oldini oladi."""
from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from leti_math_mentor.services.ratelimit import RateLimiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, limiter: RateLimiter) -> None:
        self._limiter = limiter
        self._warned: dict[int, float] = {}  # ortiqcha ogohlantirmaslik uchun

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        if await self._limiter.allow(user.id):
            return await handler(event, data)

        # limit oshdi — handlerga o'tkazmaymiz
        now = time.monotonic()
        last = self._warned.get(user.id, 0.0)
        if now - last > 20:  # 20 soniyada bir marta ogohlantiramiz
            self._warned[user.id] = now
            msg = "⏳ Birozdan keyin urinib ko'r — juda tez yozyapsan. Men har bir savolingni diqqat bilan o'qiyman. 🙂"
            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=False)
        return None
