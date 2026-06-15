"""Vaqti kelgan takrorlashlarni aniqlash use case'i (scheduler chaqiradi)."""
from __future__ import annotations

from datetime import timedelta

from ...domain.ports import Clock, ReviewRepository
from ..dto import ReviewDue


class ProcessDueReviewsUseCase:
    def __init__(
        self,
        reviews: ReviewRepository,
        clock: Clock,
        notify_cooldown_hours: int = 20,
    ) -> None:
        self._reviews = reviews
        self._clock = clock
        self._cooldown = timedelta(hours=notify_cooldown_hours)

    async def execute(self) -> list[ReviewDue]:
        now = self._clock.now()
        items = await self._reviews.due_for_notification(
            now=now, notified_before=now - self._cooldown
        )

        result: list[ReviewDue] = []
        for item in items:
            if item.id is None:
                continue
            await self._reviews.mark_notified(item.id, now)
            result.append(
                ReviewDue(review_id=item.id, chat_id=item.chat_id, topic=item.topic)
            )
        return result
