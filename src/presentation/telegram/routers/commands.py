"""Buyruq (command) handler'lari — /start, /me."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from ....infrastructure.container import Container
from ..formatters import format_student_profile

logger = logging.getLogger(__name__)

_WELCOME = (
    "Assalomu alaykum! 👋\n\n"
    "Men Leti maktabining AI matematika mentoriman. "
    "Tushunmagan matematik mavzuyingizni yozing — men uni sodda qilib "
    "tushuntiraman, so'ng siz testda bilimingizni sinab ko'rasiz.\n\n"
    "✍️ Savolingizni yozib yuboring.\n"
    "📊 Shaxsiy statistikangiz: /me\n"
    "🔁 Takrorlash kerak mavzularni ko'rish: /review"
)


def build_command_router(container: Container) -> Router:
    router = Router(name="commands")

    @router.message(CommandStart())
    async def on_start(message: Message) -> None:
        await message.answer(_WELCOME)

    @router.message(Command("me"))
    async def on_me(message: Message) -> None:
        try:
            stats = await container.get_my_stats.execute(message.chat.id)
        except Exception:
            logger.exception("Shaxsiy statistikani olishda xatolik")
            await message.answer("⚠️ Statistikani olishda xatolik yuz berdi.")
            return
        if stats is None:
            await message.answer(
                "Hali statistika yo'q. Biror mavzuni o'rganib, test ishlab ko'ring. ✍️"
            )
            return
        await message.answer(format_student_profile(stats))

    return router
