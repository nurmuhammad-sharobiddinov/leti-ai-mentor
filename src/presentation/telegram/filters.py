"""Maxsus aiogram filtrlari."""
from __future__ import annotations

from collections.abc import Iterable

from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class IsAdmin(BaseFilter):
    """Faqat ruxsat etilgan admin chat_id'lariga handler'ni ochadi."""

    def __init__(self, admin_ids: Iterable[int]) -> None:
        self._admin_ids = set(admin_ids)

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        return user is not None and user.id in self._admin_ids
