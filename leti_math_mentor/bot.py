"""Kirish nuqtasi — servislarni sozlaydi, router'larni ulaydi, polling'ni boshlaydi.

Ishga tushirish:  python -m leti_math_mentor.bot   (yoki  python bot.py  paket ichidan)
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent

from leti_math_mentor.config import Config
from leti_math_mentor.handlers import practice, progress, question, start
from leti_math_mentor.middlewares import RateLimitMiddleware
from leti_math_mentor.services.claude import ClaudeService
from leti_math_mentor.services.db import Database
from leti_math_mentor.services.memory import ConversationMemory
from leti_math_mentor.services.ratelimit import RateLimiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("leti_math_mentor")


async def main() -> None:
    cfg = Config.load()

    bot = Bot(
        token=cfg.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    # FSM saqlash: Redis bo'lsa o'shanda (qayta ishga tushganda mashq holati saqlanadi), aks holda RAM
    if cfg.redis_url:
        storage = RedisStorage.from_url(cfg.redis_url)
    else:
        storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # --- servislar ---
    db = Database(cfg.database_url)
    await db.connect(auto_migrate=True)

    memory = ConversationMemory(cfg.redis_url, cfg.history_limit, cfg.session_ttl)
    await memory.connect()

    claude = ClaudeService(cfg)
    limiter = RateLimiter(memory._redis, cfg.rate_limit_per_min)  # Redis bo'lsa o'shani ishlatadi

    # handlerlarga dependency injection (aiogram nom bo'yicha kiritadi)
    dp["cfg"] = cfg
    dp["db"] = db
    dp["claude"] = claude
    dp["memory"] = memory

    # --- middleware (rate-limit) ---
    rl = RateLimitMiddleware(limiter)
    dp.message.middleware(rl)
    dp.callback_query.middleware(rl)

    # --- global error handler: bot yiqilmasin ---
    @dp.errors()
    async def on_error(event: ErrorEvent) -> bool:
        logger.exception("Handlerda xato: %s", event.exception)
        update = event.update
        try:
            if update.message:
                await update.message.answer(
                    "⚠️ Kechirasan, biroz muammo bo'ldi. Iltimos, qayta urinib ko'r — "
                    "yoki “/reset” bilan yangidan boshla."
                )
            elif update.callback_query:
                await update.callback_query.answer("⚠️ Muammo bo'ldi, qayta urinib ko'r.", show_alert=True)
        except Exception:  # noqa: BLE001 — xabar yuborish ham xato bersa, shunchaki log
            logger.warning("Xato haqida xabar yuborib bo'lmadi")
        return True  # xato hal qilindi deb belgilaymiz

    # --- router'larni ulash. TARTIB MUHIM: question OXIRGI (fallback). ---
    dp.include_router(start.router)
    dp.include_router(progress.router)
    dp.include_router(practice.router)
    dp.include_router(question.router)  # <-- doim oxirgi

    logger.info("Bot ishga tushdi (polling). Model=%s, hard=%s", cfg.model, cfg.hard_model)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await memory.close()
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
