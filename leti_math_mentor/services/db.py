"""PostgreSQL / Supabase — asyncpg pool, jadvallar va so'rovlar.

Jadvallar birinchi ishga tushganda avtomatik yaratiladi (AUTO_MIGRATE).
Supabase transaction pooler (port 6543) uchun statement_cache_size=0 SHART.
"""
from __future__ import annotations

import logging

import asyncpg

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bot_users (
    tg_id       BIGINT PRIMARY KEY,
    username    TEXT,
    full_name   TEXT,
    leti_id     TEXT,              -- LETI EDU akkaunt bog'lash uchun (keyin)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS interactions (
    id          BIGSERIAL PRIMARY KEY,
    tg_id       BIGINT NOT NULL REFERENCES bot_users(tg_id),
    kind        TEXT NOT NULL,     -- 'question' yoki 'practice'
    topic       TEXT,              -- aniqlangan mavzu (teg)
    is_correct  BOOLEAN,           -- mashq uchun; savol-javobda NULL
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interactions_tg ON interactions(tg_id);
CREATE INDEX IF NOT EXISTS idx_interactions_topic ON interactions(tg_id, topic);
"""


class Database:
    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None
        self._known_users: set[int] = set()  # ensure_user keshi (har xabarda DB so'rovini kamaytiradi)

    async def connect(self, auto_migrate: bool = True) -> None:
        # statement_cache_size=0 — Supabase pooler (pgbouncer transaction mode) uchun shart
        self._pool = await asyncpg.create_pool(
            self._dsn, statement_cache_size=0, min_size=1, max_size=5
        )
        if auto_migrate:
            async with self._pool.acquire() as conn:
                await conn.execute(_SCHEMA)
        logger.info("DB ulandi (auto_migrate=%s)", auto_migrate)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("DB ulanmagan — avval connect() chaqir")
        return self._pool

    # --- foydalanuvchi ---
    async def ensure_user(
        self, tg_id: int, username: str | None, full_name: str | None, force: bool = False
    ) -> None:
        # Ma'lum foydalanuvchi bo'lsa, har xabarda qayta yozmaymiz (force=True — /start da yangilash).
        if not force and tg_id in self._known_users:
            return
        await self.pool.execute(
            """
            INSERT INTO bot_users (tg_id, username, full_name)
            VALUES ($1, $2, $3)
            ON CONFLICT (tg_id) DO UPDATE
                SET username = EXCLUDED.username,
                    full_name = EXCLUDED.full_name
            """,
            tg_id, username, full_name,
        )
        self._known_users.add(tg_id)

    # --- log ---
    async def log_interaction(
        self,
        tg_id: int,
        kind: str,
        topic: str | None = None,
        is_correct: bool | None = None,
    ) -> None:
        await self.pool.execute(
            """
            INSERT INTO interactions (tg_id, kind, topic, is_correct)
            VALUES ($1, $2, $3, $4)
            """,
            tg_id, kind, topic, is_correct,
        )

    # --- progress ---
    async def get_progress(self, tg_id: int) -> list[dict]:
        """Har bir mavzu bo'yicha: jami, to'g'ri, foiz. Mashqlardan + savol mavzularidan."""
        rows = await self.pool.fetch(
            """
            SELECT
                COALESCE(topic, 'umumiy') AS topic,
                COUNT(*)                  AS total,
                COUNT(*) FILTER (WHERE is_correct IS TRUE)  AS correct,
                COUNT(*) FILTER (WHERE is_correct IS NOT NULL) AS graded
            FROM interactions
            WHERE tg_id = $1
            GROUP BY COALESCE(topic, 'umumiy')
            ORDER BY total DESC
            """,
            tg_id,
        )
        return [dict(r) for r in rows]

    async def get_level_for_topic(self, tg_id: int, topic: str) -> str:
        """O'quvchining mavzudagi natijasiga qarab keyingi mashq darajasi."""
        row = await self.pool.fetchrow(
            """
            SELECT
                COUNT(*) FILTER (WHERE is_correct IS NOT NULL) AS graded,
                COUNT(*) FILTER (WHERE is_correct IS TRUE)     AS correct
            FROM interactions
            WHERE tg_id = $1 AND topic = $2 AND kind = 'practice'
            """,
            tg_id, topic,
        )
        graded = row["graded"] if row else 0
        correct = row["correct"] if row else 0
        if not graded or graded < 2:
            return "oson"
        ratio = correct / graded
        if ratio >= 0.75:
            return "qiyin"
        if ratio >= 0.4:
            return "o'rta"
        return "oson"
