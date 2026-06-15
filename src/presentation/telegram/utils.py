"""Telegram yordamchi funksiyalari."""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardMarkup, Message

_TELEGRAM_LIMIT = 4096


@asynccontextmanager
async def status_message(message: Message, text: str) -> AsyncIterator[None]:
    """Vaqtinchalik "kutib turing" xabarini ko'rsatadi.

    Blok tugashi bilan (ya'ni haqiqiy javob yuborilishidan OLDIN) bu xabar
    o'chiriladi — foydalanuvchi avval "tayyorlanmoqda"ni, so'ng faqat natijani
    ko'radi. Xato bo'lsa ham xabar ishonchli o'chadi (finally).

        async with status_message(message, "✍️ Javob tayyorlanmoqda..."):
            result = await slow_llm_call()
        await message.answer(result)   # placeholder allaqachon o'chgan
    """
    status = await message.answer(text)
    try:
        yield
    finally:
        try:
            await status.delete()
        except TelegramBadRequest:
            pass  # xabar allaqachon o'chgan yoki eskirgan — ahamiyatsiz


async def reply_long(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    """Uzun matnni Telegram limiti (4096) bo'yicha bo'lib yuboradi.

    Klaviatura faqat oxirgi qismga biriktiriladi.
    """
    chunks = [text[i : i + _TELEGRAM_LIMIT] for i in range(0, len(text), _TELEGRAM_LIMIT)]
    if not chunks:
        chunks = [""]
    for chunk in chunks[:-1]:
        await message.answer(chunk)
    await message.answer(chunks[-1], reply_markup=reply_markup)
