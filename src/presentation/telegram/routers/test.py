"""Test oqimi handler'lari (n8n: Test_Prompt/AI Agent + Tekshirish/AI Agent1)."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery

from ....domain.exceptions import (
    InvalidAnswerError,
    NoActiveTopicError,
    TestSessionNotFoundError,
)
from ....infrastructure.container import Container
from ..callbacks import AnswerAction, ExplanationAction
from ..formatters import format_answer_feedback, format_question, format_test_result
from ..keyboards import question_keyboard
from ..utils import reply_long, status_message

logger = logging.getLogger(__name__)


def build_test_router(container: Container) -> Router:
    router = Router(name="test")

    @router.callback_query(ExplanationAction.filter(F.action == "test"))
    async def on_start_test(query: CallbackQuery) -> None:
        await query.answer()  # tugmani darhol tasdiqlaymiz (callback eskirmasin)
        message = query.message
        if message is None:
            return
        try:
            async with status_message(message, "📝 Test tayyorlanmoqda, biroz kuting..."):
                question = await container.start_test.execute(chat_id=message.chat.id)
        except NoActiveTopicError:
            await message.answer("Avval biror mavzu yozing.")
            return
        except Exception:
            logger.exception("Test boshlashda xatolik")
            await message.answer("⚠️ Testni tayyorlashda xatolik. Qayta urining.")
            return
        await message.answer(
            format_question(question), reply_markup=question_keyboard(question)
        )

    @router.callback_query(AnswerAction.filter())
    async def on_answer(query: CallbackQuery, callback_data: AnswerAction) -> None:
        # Tugma bosilishini DARHOL tasdiqlaymiz. Aks holda oxirgi savolda
        # uzoq davom etadigan AI tahlili vaqtida callback "eskirib" ketadi
        # (Telegram: "query is too old") va handler yiqilib, natija ko'rsatilmaydi.
        await query.answer()
        message = query.message
        if message is None:
            return

        # Eski savol tugmalarini darhol olib tashlaymiz (qayta bosilmasin).
        try:
            await message.edit_reply_markup(reply_markup=None)
        except TelegramBadRequest:
            pass  # xabar eskirgan yoki tugma allaqachon yo'q — ahamiyatsiz

        # "Tekshirilmoqda" xabari ko'rsatiladi; oxirgi savolda AI tahlili davom
        # etayotganda ham ko'rinib turadi va natijadan oldin o'chadi.
        try:
            async with status_message(message, "⏳ Tekshirilmoqda..."):
                feedback = await container.submit_answer.execute(
                    chat_id=message.chat.id,
                    question_index=callback_data.question_index,
                    option=callback_data.option,
                )
        except InvalidAnswerError:
            await message.answer("Bu savolga allaqachon javob bergansiz.")
            return
        except TestSessionNotFoundError:
            await message.answer("Faol test topilmadi. /start bilan qayta boshlang.")
            return
        except Exception:
            logger.exception("Javobni tekshirishda xatolik")
            await message.answer("⚠️ Xatolik yuz berdi. /start bilan qayta boshlang.")
            return

        await message.answer(format_answer_feedback(feedback))

        if feedback.is_final and feedback.final_result is not None:
            await reply_long(message, format_test_result(feedback.final_result))
        else:
            nxt = feedback.next_question
            await message.answer(
                format_question(nxt), reply_markup=question_keyboard(nxt)
            )

    return router
