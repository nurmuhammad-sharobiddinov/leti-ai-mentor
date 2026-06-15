"""Qayta tushuntirish use case'i (n8n: "Re Explain" + explain_again)."""
from __future__ import annotations

from ...domain.entities import Message
from ...domain.exceptions import NoActiveTopicError
from ...domain.ports import (
    ConversationRepository,
    ExplanationService,
    StudentRepository,
)
from ..dto import ExplanationResult


class ReexplainTopicUseCase:
    def __init__(
        self,
        students: StudentRepository,
        conversations: ConversationRepository,
        explainer: ExplanationService,
        history_limit: int,
    ) -> None:
        self._students = students
        self._conversations = conversations
        self._explainer = explainer
        self._history_limit = history_limit

    async def execute(self, chat_id: int) -> ExplanationResult:
        student = await self._students.get(chat_id)
        if student is None or not student.active_topic:
            raise NoActiveTopicError("Qayta tushuntirish uchun faol mavzu yo'q.")

        history = await self._conversations.history(chat_id, self._history_limit)
        text = await self._explainer.reexplain(student.active_topic, history)
        await self._conversations.add(chat_id, Message.assistant(text))

        return ExplanationResult(text=text)
