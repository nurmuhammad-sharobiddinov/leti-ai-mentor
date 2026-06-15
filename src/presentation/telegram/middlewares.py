"""Cross-cutting middleware — har bir yangilanishda o'quvchini ro'yxatga oladi.

n8n'da bu har bir trigger'dan keyingi "upsert" node edi. Bu yerda u
ko'ndalang mas'uliyat sifatida bir joyga ajratilgan (DRY).
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject, User

from ...application.use_cases import RegisterStudentUseCase


class StudentRegistrationMiddleware(BaseMiddleware):
    def __init__(self, register_student: RegisterStudentUseCase) -> None:
        self._register_student = register_student

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user: User | None = data.get("event_from_user")
        if user is not None and not user.is_bot:
            full_name = " ".join(
                part for part in (user.first_name, user.last_name) if part
            )
            student = await self._register_student.execute(
                chat_id=user.id, full_name=full_name
            )
            data["student"] = student
        return await handler(event, data)


def chat_id_of(event: Message | CallbackQuery) -> int:
    """Message yoki CallbackQuery'dan chat_id ajratib olish."""
    if isinstance(event, CallbackQuery):
        if event.message is None:
            return event.from_user.id
        return event.message.chat.id
    return event.chat.id
