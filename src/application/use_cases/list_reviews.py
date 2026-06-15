"""O'quvchining takrorlash ro'yxatini olish use case'i (/review buyrug'i)."""
from __future__ import annotations

from ...domain.entities import ReviewItem
from ...domain.ports import ReviewRepository


class ListReviewsUseCase:
    def __init__(self, reviews: ReviewRepository) -> None:
        self._reviews = reviews

    async def execute(self, chat_id: int) -> list[ReviewItem]:
        return await self._reviews.list_for_student(chat_id)
