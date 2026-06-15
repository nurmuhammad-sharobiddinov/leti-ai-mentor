"""Mavzuni tushuntirish use case'i (n8n: "Savolni tushuntiruvchi")."""
from __future__ import annotations

from ...domain.entities import Message
from ...domain.ports import (
    ConversationRepository,
    ExplanationService,
    StudentRepository,
)
from ..dto import ExplanationResult


class ExplainTopicUseCase:
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

    async def execute(self, chat_id: int, topic: str) -> ExplanationResult:
        history = await self._conversations.history(chat_id, self._history_limit)

        await self._conversations.add(chat_id, Message.user(topic))
        text = await self._explainer.explain(topic, history)
        await self._conversations.add(chat_id, Message.assistant(text))

        # Faol mavzuni saqlaymiz — test va qayta tushuntirish shunga tayanadi.
        student = await self._students.get(chat_id)
        if student is not None:
            student.set_active_topic(topic)
            await self._students.save(student)

        return ExplanationResult(text=text)
