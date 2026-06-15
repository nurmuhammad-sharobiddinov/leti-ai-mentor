"""ReviewRepository port'ining Postgres realizatsiyasi."""
from __future__ import annotations

from datetime import datetime

import asyncpg

from ...domain.entities import ReviewItem
from ...domain.ports import ReviewRepository
from .database import Database


class PgReviewRepository(ReviewRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def upsert(self, item: ReviewItem) -> ReviewItem:
        if item.id is not None:
            await self._db.pool.execute(
                """
                UPDATE review_items
                   SET box = $2, due_at = $3, last_reviewed = $4
                 WHERE id = $1
                """,
                item.id,
                item.box,
                item.due_at,
                item.last_reviewed,
            )
            return item

        row = await self._db.pool.fetchrow(
            """
            INSERT INTO review_items (chat_id, topic, box, due_at, last_reviewed)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (chat_id, topic) DO UPDATE
                SET box           = EXCLUDED.box,
                    due_at        = EXCLUDED.due_at,
                    last_reviewed = EXCLUDED.last_reviewed
            RETURNING *
            """,
            item.chat_id,
            item.topic,
            item.box,
            item.due_at,
            item.last_reviewed,
        )
        return self._to_entity(row)

    async def get(self, review_id: int) -> ReviewItem | None:
        row = await self._db.pool.fetchrow(
            "SELECT * FROM review_items WHERE id = $1", review_id
        )
        return self._to_entity(row) if row else None

    async def get_by_topic(self, chat_id: int, topic: str) -> ReviewItem | None:
        row = await self._db.pool.fetchrow(
            "SELECT * FROM review_items WHERE chat_id = $1 AND topic = $2",
            chat_id,
            topic,
        )
        return self._to_entity(row) if row else None

    async def list_for_student(self, chat_id: int) -> list[ReviewItem]:
        rows = await self._db.pool.fetch(
            "SELECT * FROM review_items WHERE chat_id = $1 ORDER BY due_at",
            chat_id,
        )
        return [self._to_entity(row) for row in rows]

    async def due_for_notification(
        self, now: datetime, notified_before: datetime
    ) -> list[ReviewItem]:
        rows = await self._db.pool.fetch(
            """
            SELECT * FROM review_items
             WHERE due_at <= $1
               AND (last_notified IS NULL OR last_notified < $2)
             ORDER BY due_at
             LIMIT 100
            """,
            now,
            notified_before,
        )
        return [self._to_entity(row) for row in rows]

    async def mark_notified(self, review_id: int, when: datetime) -> None:
        await self._db.pool.execute(
            "UPDATE review_items SET last_notified = $2 WHERE id = $1",
            review_id,
            when,
        )

    async def delete(self, review_id: int) -> None:
        await self._db.pool.execute(
            "DELETE FROM review_items WHERE id = $1", review_id
        )

    @staticmethod
    def _to_entity(row: asyncpg.Record) -> ReviewItem:
        return ReviewItem(
            id=row["id"],
            chat_id=row["chat_id"],
            topic=row["topic"],
            box=row["box"],
            due_at=row["due_at"],
            last_reviewed=row["last_reviewed"],
            last_notified=row["last_notified"],
        )
