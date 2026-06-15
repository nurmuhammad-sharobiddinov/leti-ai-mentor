"""Takrorlash (spaced-repetition) handler'lari: /review va eslatma tugmasi."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ....infrastructure.container import Container
from ..callbacks import ReviewAction
from ..keyboards import explanation_keyboard, review_list_keyboard
from ..utils import reply_long, status_message

logger = logging.getLogger(__name__)


def build_review_router(container: Container) -> Router:
    router = Router(name="review")

    @router.message(Command("review"))
    async def on_review_list(message: Message) -> None:
        items = await container.list_reviews.execute(message.chat.id)
        if not items:
            await message.answer(
                "Hozircha takrorlanadigan mavzu yo'q. 👍\n"
                "Avval biror mavzuni o'rganib, test ishlang."
            )
            return
        await message.answer(
            "🔁 Takrorlash uchun mavzular:",
            reply_markup=review_list_keyboard(items),
        )

    @router.callback_query(ReviewAction.filter())
    async def on_start_review(query: CallbackQuery, callback_data: ReviewAction) -> None:
        await query.answer()  # tugmani darhol tasdiqlaymiz (callback eskirmasin)
        message = query.message
        if message is None:
            return
        try:
            async with status_message(message, "✍️ Takrorlash tayyorlanmoqda, biroz kuting..."):
                result = await container.start_review.execute(
                    chat_id=message.chat.id, review_id=callback_data.review_id
                )
        except Exception:
            logger.exception("Takrorlashni boshlashda xatolik")
            await message.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko'ring.")
            return

        if result is None:
            await message.answer("Bu takrorlash topilmadi yoki eskirgan.")
            return
        await reply_long(message, result.text, explanation_keyboard())

    return router
