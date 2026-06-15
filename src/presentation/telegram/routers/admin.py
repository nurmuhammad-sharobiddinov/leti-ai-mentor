"""Admin handler'lari — /stats (faqat ruxsat etilgan adminlar uchun)."""
from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from ....infrastructure.container import Container
from ..filters import IsAdmin
from ..formatters import format_statistics

logger = logging.getLogger(__name__)


def build_admin_router(container: Container) -> Router:
    router = Router(name="admin")
    is_admin = IsAdmin(container.settings.admin_ids)

    @router.message(Command("stats"), is_admin)
    async def on_stats(message: Message) -> None:
        try:
            stats = await container.get_statistics.execute()
        except Exception:
            logger.exception("Statistika olishda xatolik")
            await message.answer("⚠️ Statistikani olishda xatolik yuz berdi.")
            return
        await message.answer(format_statistics(stats))

    return router
