"""Spaced-repetition eslatma yuboruvchisi — fon vazifasi (background task).

Davriy ravishda vaqti kelgan takrorlashlarni tekshiradi va o'quvchilarga
eslatma yuboradi. Aiogram'dan tashqarida, mustaqil asyncio loop sifatida.
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from ...application.use_cases import ProcessDueReviewsUseCase
from .keyboards import review_start_keyboard

logger = logging.getLogger(__name__)


class ReviewScheduler:
    def __init__(
        self,
        bot: Bot,
        process_due: ProcessDueReviewsUseCase,
        interval_seconds: int,
    ) -> None:
        self._bot = bot
        self._process_due = process_due
        self._interval = interval_seconds

    async def run(self) -> None:
        """To'xtatilmaguncha (CancelledError) davriy ishlaydi."""
        logger.info("Takrorlash scheduleri ishga tushdi (%d s interval).", self._interval)
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                logger.info("Takrorlash scheduleri to'xtatildi.")
                raise
            except Exception:
                logger.exception("Scheduler tsiklida xatolik")
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        due = await self._process_due.execute()
        for item in due:
            text = (
                f"🔔 Eslatma! \"{item.topic}\" mavzusini takrorlash vaqti keldi.\n"
                "Keling, bilimingizni mustahkamlaymiz!"
            )
            try:
                await self._bot.send_message(
                    chat_id=item.chat_id,
                    text=text,
                    reply_markup=review_start_keyboard(item.review_id),
                )
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after)
            except TelegramForbiddenError:
                # Foydalanuvchi botni bloklagan — o'tkazib yuboramiz.
                logger.info("Foydalanuvchi %s botni bloklagan.", item.chat_id)
            except Exception:
                logger.exception("Eslatma yuborishda xatolik (chat %s)", item.chat_id)
