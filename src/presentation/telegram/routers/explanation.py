"""Tushuntirish oqimi handler'lari (n8n: Savolni tushuntiruvchi + Re Explain)."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from ....domain.exceptions import NoActiveTopicError
from ....infrastructure.container import Container
from ..callbacks import ExplanationAction
from ..keyboards import explanation_keyboard
from ..utils import reply_long, status_message

logger = logging.getLogger(__name__)


def build_explanation_router(container: Container) -> Router:
    router = Router(name="explanation")

    @router.message(F.text & ~F.text.startswith("/"))
    async def on_topic(message: Message) -> None:
        topic = (message.text or "").strip()
        if not topic:
            return
        try:
            async with status_message(message, "✍️ Javob tayyorlanmoqda, biroz kuting..."):
                result = await container.explain_topic.execute(
                    chat_id=message.chat.id, topic=topic
                )
        except Exception:
            logger.exception("Tushuntirishda xatolik")
            await message.answer(
                "⚠️ Kechirasiz, javob tayyorlashda xatolik yuz berdi. "
                "Birozdan so'ng qayta urinib ko'ring."
            )
            return
        await reply_long(message, result.text, explanation_keyboard())

    @router.callback_query(ExplanationAction.filter(F.action == "again"))
    async def on_explain_again(query: CallbackQuery) -> None:
        await query.answer()  # tugmani darhol tasdiqlaymiz (callback eskirmasin)
        message = query.message
        if message is None:
            return
        try:
            async with status_message(message, "✍️ Qayta tushuntirilmoqda, biroz kuting..."):
                result = await container.reexplain_topic.execute(
                    chat_id=message.chat.id
                )
        except NoActiveTopicError:
            await message.answer("Avval biror mavzu yozing.")
            return
        except Exception:
            logger.exception("Qayta tushuntirishda xatolik")
            await message.answer("⚠️ Xatolik yuz berdi. Qayta urinib ko'ring.")
            return
        await reply_long(message, result.text, explanation_keyboard())

    return router
