"""asyncpg connection pool'ni boshqaruvchi yengil qatlam."""
from __future__ import annotations

from pathlib import Path

import asyncpg

_SCHEMA_FILE = Path(__file__).parent / "schema.sql"


class Database:
    """Postgres ulanishlar puli (connection pool) hayot siklini boshqaradi."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._pool: asyncpg.Pool | None = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database ulanmagan. Avval connect() chaqiring.")
        return self._pool

    async def connect(self) -> None:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                dsn=self._dsn,
                min_size=1,
                max_size=10,
                command_timeout=60,
                # Supabase transaction pooler (pgbouncer, 6543-port) prepared
                # statement'larni qo'llab-quvvatlamaydi — keshni o'chiramiz.
                statement_cache_size=0,
            )

    async def disconnect(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def migrate(self) -> None:
        """schema.sql ni ishga tushiradi (idempotent — CREATE IF NOT EXISTS)."""
        sql = _SCHEMA_FILE.read_text(encoding="utf-8")
        async with self.pool.acquire() as conn:
            await conn.execute(sql)
