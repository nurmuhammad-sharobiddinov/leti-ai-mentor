"""Rate-limit — bir o'quvchi daqiqasiga N tadan ko'p xabar yubora olmaydi.

Redis counter (INCR + EXPIRE) orqali. Redis bo'lmasa — RAM fallback (sliding window).
"""
from __future__ import annotations

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, redis, per_minute: int) -> None:
        self._redis = redis  # redis.asyncio.Redis yoki None
        self._limit = per_minute
        self._win: dict[int, deque] = defaultdict(deque)  # RAM fallback

    async def allow(self, tg_id: int) -> bool:
        """True — ruxsat, False — limit oshib ketdi."""
        if self._limit <= 0:
            return True
        if self._redis is not None:
            key = f"rl:{tg_id}:{int(time.time()) // 60}"
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, 70)
            return count <= self._limit
        # RAM: oxirgi 60 soniyadagi xabarlarni sanaymiz
        now = time.monotonic()
        win = self._win[tg_id]
        while win and now - win[0] > 60:
            win.popleft()
        if len(win) >= self._limit:
            return False
        win.append(now)
        return True
