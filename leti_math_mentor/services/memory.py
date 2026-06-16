"""Suhbat konteksti — Redis bilan saqlanadi (TTL bilan).

REDIS_URL berilmasa yoki Redis'ga ulanib bo'lmasa, avtomatik RAM fallback'ga o'tadi
(bot baribir ishlaydi, lekin qayta ishga tushganda kontekst yo'qoladi).
Interfeys o'zgarmas: get_history / add_turn / reset.
"""
from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ConversationMemory:
    def __init__(self, redis_url: str | None, history_limit: int, ttl: int) -> None:
        self._redis_url = redis_url
        self._limit = history_limit
        self._ttl = ttl
        self._redis = None  # redis.asyncio.Redis
        # RAM fallback: {tg_id: deque[(role, content)]} + oxirgi faollik vaqti
        self._mem: dict[int, deque] = defaultdict(lambda: deque(maxlen=history_limit))
        self._mem_seen: dict[int, float] = {}

    async def connect(self) -> None:
        if not self._redis_url:
            logger.info("REDIS_URL yo'q — suhbat konteksti RAM'da saqlanadi (fallback)")
            return
        try:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Redis ulandi — suhbat konteksti Redis'da")
        except Exception as exc:  # noqa: BLE001 — har qanday ulanish xatosida fallback
            logger.warning("Redis'ga ulanib bo'lmadi (%s) — RAM fallback'ga o'tildi", exc)
            self._redis = None

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.aclose()

    def _key(self, tg_id: int) -> str:
        return f"conv:{tg_id}"

    async def get_history(self, tg_id: int) -> list[dict]:
        """[{"role": ..., "content": ...}, ...] — Claude messages formatida."""
        if self._redis is not None:
            raw = await self._redis.lrange(self._key(tg_id), 0, -1)
            return [json.loads(x) for x in raw]
        self._expire_ram(tg_id)
        return [{"role": r, "content": c} for r, c in self._mem.get(tg_id, ())]

    async def add_turn(self, tg_id: int, role: str, content: str) -> None:
        """Bir turni qo'shadi (faqat matn saqlanadi — rasm tarixga yozilmaydi)."""
        if self._redis is not None:
            key = self._key(tg_id)
            await self._redis.rpush(key, json.dumps({"role": role, "content": content}))
            # limitdan oshganini kesib tashlash (oxirgi N ta qoladi)
            await self._redis.ltrim(key, -self._limit, -1)
            await self._redis.expire(key, self._ttl)
            return
        self._mem[tg_id].append((role, content))
        self._mem_seen[tg_id] = time.monotonic()

    async def reset(self, tg_id: int) -> None:
        if self._redis is not None:
            await self._redis.delete(self._key(tg_id))
            return
        self._mem.pop(tg_id, None)
        self._mem_seen.pop(tg_id, None)

    def _expire_ram(self, tg_id: int) -> None:
        seen = self._mem_seen.get(tg_id)
        if seen is not None and (time.monotonic() - seen) > self._ttl:
            self._mem.pop(tg_id, None)
            self._mem_seen.pop(tg_id, None)
