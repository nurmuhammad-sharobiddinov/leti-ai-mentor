"""Testni boshlash use case'i (n8n: "Test_Prompt" + "AI Agent")."""
from __future__ import annotations

from ...domain.entities import TestSession
from ...domain.exceptions import NoActiveTopicError
from ...domain.ports import (
    ConversationRepository,
    StudentRepository,
    TestGenerator,
    TestSessionRepository,
)
from ..dto import QuestionView


class StartTestUseCase:
    def __init__(
        self,
        students: StudentRepository,
        conversations: ConversationRepository,
        sessions: TestSessionRepository,
        test_generator: TestGenerator,
        history_limit: int,
    ) -> None:
        self._students = students
        self._conversations = conversations
        self._sessions = sessions
        self._test_generator = test_generator
        self._history_limit = history_limit

    async def execute(self, chat_id: int) -> QuestionView:
        student = await self._students.get(chat_id)
        if student is None or not student.active_topic:
            raise NoActiveTopicError("Test uchun faol mavzu yo'q.")

        history = await self._conversations.history(chat_id, self._history_limit)
        questions = await self._test_generator.generate(student.active_topic, history)

        session = TestSession(
            chat_id=chat_id,
            topic=student.active_topic,
            questions=questions,
        )
        session = await self._sessions.save(session)

        question = session.current_question
        return QuestionView(
            index=question.index,
            text=question.text,
            options=question.options,
            number=session.current_index + 1,
            total=session.total,
        )
