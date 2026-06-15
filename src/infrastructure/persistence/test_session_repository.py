"""TestSessionRepository port'ining Postgres realizatsiyasi.

Savollar va javoblar JSONB sifatida saqlanadi. Bu mapping shu sinfning
yagona mas'uliyati (entity <-> qator).
"""
from __future__ import annotations

import json

import asyncpg

from ...domain.entities import Question, SubmittedAnswer, TestSession
from ...domain.enums import QuestionKind, TestStatus
from ...domain.ports import TestSessionRepository
from .database import Database


class PgTestSessionRepository(TestSessionRepository):
    def __init__(self, db: Database) -> None:
        self._db = db

    async def save(self, session: TestSession) -> TestSession:
        questions_json = json.dumps(
            [self._question_to_dict(q) for q in session.questions]
        )
        answers_json = json.dumps([self._answer_to_dict(a) for a in session.answers])

        if session.id is None:
            row = await self._db.pool.fetchrow(
                """
                INSERT INTO test_sessions
                    (chat_id, topic, questions, answers, current_index,
                     status, score, total_questions)
                VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6, $7, $8)
                RETURNING id
                """,
                session.chat_id,
                session.topic,
                questions_json,
                answers_json,
                session.current_index,
                session.status.value,
                session.score,
                session.total,
            )
            session.id = row["id"]
        else:
            await self._db.pool.execute(
                """
                UPDATE test_sessions
                   SET answers       = $2::jsonb,
                       current_index = $3,
                       status        = $4,
                       score         = $5,
                       updated_at    = now()
                 WHERE id = $1
                """,
                session.id,
                answers_json,
                session.current_index,
                session.status.value,
                session.score,
            )
        return session

    async def get_active(self, chat_id: int) -> TestSession | None:
        row = await self._db.pool.fetchrow(
            """
            SELECT * FROM test_sessions
             WHERE chat_id = $1 AND status = 'in_progress'
             ORDER BY id DESC
             LIMIT 1
            """,
            chat_id,
        )
        return self._to_entity(row) if row else None

    # --- mapping yordamchilari ---

    @staticmethod
    def _question_to_dict(q: Question) -> dict:
        return {
            "index": q.index,
            "kind": q.kind.value,
            "text": q.text,
            "options": q.options,
            "correct_option": q.correct_option,
            "explanation": q.explanation,
        }

    @staticmethod
    def _answer_to_dict(a: SubmittedAnswer) -> dict:
        return {
            "question_index": a.question_index,
            "selected_option": a.selected_option,
            "is_correct": a.is_correct,
        }

    @classmethod
    def _to_entity(cls, row: asyncpg.Record) -> TestSession:
        questions_raw = cls._load_json(row["questions"])
        answers_raw = cls._load_json(row["answers"])
        return TestSession(
            id=row["id"],
            chat_id=row["chat_id"],
            topic=row["topic"],
            questions=[
                Question(
                    index=q["index"],
                    kind=QuestionKind(q["kind"]),
                    text=q["text"],
                    options=q["options"],
                    correct_option=q["correct_option"],
                    explanation=q["explanation"],
                )
                for q in questions_raw
            ],
            answers=[
                SubmittedAnswer(
                    question_index=a["question_index"],
                    selected_option=a["selected_option"],
                    is_correct=a["is_correct"],
                )
                for a in answers_raw
            ],
            current_index=row["current_index"],
            status=TestStatus(row["status"]),
        )

    @staticmethod
    def _load_json(value) -> list:
        # asyncpg jsonb'ni str sifatida qaytarishi mumkin (codec o'rnatilmagan bo'lsa).
        if isinstance(value, str):
            return json.loads(value)
        return value or []
