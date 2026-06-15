"""StatisticsRepository port'ining Postgres realizatsiyasi."""
from __future__ import annotations

from ...domain.entities import Statistics, StudentStats, TopicCount
from ...domain.ports import StatisticsRepository
from .database import Database


class PgStatisticsRepository(StatisticsRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def collect(self) -> Statistics:
        pool = self._db.pool

        total_students = await pool.fetchval("SELECT count(*) FROM students")
        active_today = await pool.fetchval(
            "SELECT count(*) FROM students WHERE last_active >= date_trunc('day', now())"
        )
        completed_tests = await pool.fetchval(
            "SELECT count(*) FROM test_sessions WHERE status = 'completed'"
        )
        avg_pct = await pool.fetchval(
            """
            SELECT coalesce(
                avg(score::float / nullif(total_questions, 0)) * 100, 0
            )
            FROM test_sessions
            WHERE status = 'completed' AND total_questions > 0
            """
        )
        weak_rows = await pool.fetch(
            """
            SELECT topic, count(*) AS cnt
              FROM students, unnest(weak_topics) AS topic
             GROUP BY topic
             ORDER BY cnt DESC
             LIMIT 5
            """
        )

        return Statistics(
            total_students=total_students or 0,
            active_today=active_today or 0,
            completed_tests=completed_tests or 0,
            average_score_pct=round(float(avg_pct or 0.0), 1),
            top_weak_topics=[
                TopicCount(topic=row["topic"], count=row["cnt"]) for row in weak_rows
            ],
        )

    async def collect_for_student(self, chat_id: int) -> StudentStats | None:
        pool = self._db.pool

        student = await pool.fetchrow(
            """
            SELECT full_name, level, weak_topics, mastered_topics
              FROM students
             WHERE chat_id = $1
            """,
            chat_id,
        )
        if student is None:
            return None

        completed_tests = await pool.fetchval(
            "SELECT count(*) FROM test_sessions "
            "WHERE chat_id = $1 AND status = 'completed'",
            chat_id,
        )
        avg_pct = await pool.fetchval(
            """
            SELECT coalesce(
                avg(score::float / nullif(total_questions, 0)) * 100, 0
            )
            FROM test_sessions
            WHERE chat_id = $1 AND status = 'completed' AND total_questions > 0
            """,
            chat_id,
        )
        due_reviews = await pool.fetchval(
            "SELECT count(*) FROM review_items "
            "WHERE chat_id = $1 AND due_at <= now()",
            chat_id,
        )

        return StudentStats(
            full_name=student["full_name"],
            level=student["level"],
            completed_tests=completed_tests or 0,
            average_score_pct=round(float(avg_pct or 0.0), 1),
            mastered_topics=list(student["mastered_topics"] or []),
            weak_topics=list(student["weak_topics"] or []),
            due_reviews=due_reviews or 0,
        )
