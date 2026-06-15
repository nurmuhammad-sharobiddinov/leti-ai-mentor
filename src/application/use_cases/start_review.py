"""Takrorlashni boshlash use case'i.

Foydalanuvchi eslatmadagi tugmani bossa: mavzu faollashtiriladi, qaytadan
tushuntiriladi (so'ng odatdagi test oqimi davom etadi) va jadval yangilanadi.
"""
from __future__ import annotations

from ...domain.entities import Message
from ...domain.ports import (
    Clock,
    ConversationRepository,
    ExplanationService,
    ReviewRepository,
    StudentRepository,
)
from ...domain.services import SpacedRepetitionPolicy
from ..dto import ExplanationResult


class StartReviewUseCase:
    def __init__(
        self,
        students: StudentRepository,
        conversations: ConversationRepository,
        reviews: ReviewRepository,
        explainer: ExplanationService,
        policy: SpacedRepetitionPolicy,
        clock: Clock,
        history_limit: int,
    ) -> None:
        self._students = students
        self._conversations = conversations
        self._reviews = reviews
        self._explainer = explainer
        self._policy = policy
        self._clock = clock
        self._history_limit = history_limit

    async def execute(self, chat_id: int, review_id: int) -> ExplanationResult | None:
        item = await self._reviews.get(review_id)
        if item is None or item.chat_id != chat_id:
            return None

        topic = item.topic

        student = await self._students.get(chat_id)
        if student is not None:
            student.set_active_topic(topic)
            await self._students.save(student)

        history = await self._conversations.history(chat_id, self._history_limit)
        text = await self._explainer.explain(topic, history)
        await self._conversations.add(chat_id, Message.user(topic))
        await self._conversations.add(chat_id, Message.assistant(text))

        # Mavzu qayta ko'rib chiqildi — jadvalni oldinga suramiz.
        updated = self._policy.on_reviewed(item, self._clock.now())
        if updated is None:
            await self._reviews.delete(review_id)
        else:
            await self._reviews.upsert(updated)

        return ExplanationResult(text=text)
