"""StudentRepository port'ining Postgres realizatsiyasi."""
from __future__ import annotations

import asyncpg

from ...domain.entities import Student
from ...domain.ports import StudentRepository
from .database import Database


class PgStudentRepository(StudentRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def get(self, chat_id: int) -> Student | None:
        row = await self._db.pool.fetchrow(
            "SELECT * FROM students WHERE chat_id = $1", chat_id
        )
        return self._to_entity(row) if row else None

    async def upsert(self, student: Student) -> Student:
        row = await self._db.pool.fetchrow(
            """
            INSERT INTO students (chat_id, full_name, level, active_topic,
                                  weak_topics, mastered_topics)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (chat_id) DO UPDATE
                SET full_name   = EXCLUDED.full_name,
                    last_active = now()
            RETURNING *
            """,
            student.chat_id,
            student.full_name,
            student.level,
            student.active_topic,
            student.weak_topics,
            student.mastered_topics,
        )
        return self._to_entity(row)

    async def save(self, student: Student) -> None:
        await self._db.pool.execute(
            """
            UPDATE students
               SET full_name       = $2,
                   level           = $3,
                   active_topic    = $4,
                   weak_topics     = $5,
                   mastered_topics = $6,
                   last_active     = now()
             WHERE chat_id = $1
            """,
            student.chat_id,
            student.full_name,
            student.level,
            student.active_topic,
            student.weak_topics,
            student.mastered_topics,
        )

    @staticmethod
    def _to_entity(row: asyncpg.Record) -> Student:
        return Student(
            chat_id=row["chat_id"],
            full_name=row["full_name"],
            level=row["level"],
            active_topic=row["active_topic"],
            weak_topics=list(row["weak_topics"]),
            mastered_topics=list(row["mastered_topics"]),
            last_active=row["last_active"],
            created_at=row["created_at"],
        )
