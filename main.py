"""Ilova kirish nuqtasi (Composition Root).

Bu yagona joy barcha qatlamlarni ulaydi va botni ishga tushiradi.
Rejimlar: polling (default) yoki webhook — .env dagi BOT_MODE orqali.
Ishga tushirish:  py main.py
"""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiohttp import web

from src.infrastructure.config import Settings, get_settings
from src.infrastructure.container import Container
from src.infrastructure.persistence import Database
from src.presentation.telegram import (
    ReviewScheduler,
    build_dispatcher,
    build_web_app,
    webhook_url,
)

logger = logging.getLogger("lux-leti-ai-mentor")


def _start_scheduler(
    bot: Bot, container: Container, settings: Settings
) -> asyncio.Task | None:
    if not settings.review_enabled:
        return None
    scheduler = ReviewScheduler(
        bot=bot,
        process_due=container.process_due_reviews,
        interval_seconds=settings.review_poll_interval_seconds,
    )
    return asyncio.create_task(scheduler.run(), name="review-scheduler")


async def _run_polling(bot: Bot, dp: Dispatcher) -> None:
    await bot.delete_webhook(drop_pending_updates=False)
    me = await bot.get_me()
    logger.info("Bot polling rejimida ishga tushdi: @%s", me.username)
    await dp.start_polling(bot)


async def _run_webhook(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    url = webhook_url(settings)
    await bot.set_webhook(
        url=url,
        secret_token=settings.webhook_secret or None,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    app = build_web_app(bot, dp, settings)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webapp_host, port=settings.webapp_port)
    await site.start()
    me = await bot.get_me()
    logger.info(
        "Bot webhook rejimida ishga tushdi: @%s -> %s (%s:%d)",
        me.username,
        url,
        settings.webapp_host,
        settings.webapp_port,
    )
    try:
        await asyncio.Event().wait()  # to'xtatilmaguncha kutamiz
    finally:
        await runner.cleanup()


async def run() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    settings = get_settings()

    db = Database(settings.database_url)
    await db.connect()
    if settings.auto_migrate:
        await db.migrate()
        logger.info("Ma'lumotlar bazasi sxemasi tayyor.")

    container = Container(settings, db)
    bot = Bot(token=settings.telegram_bot_token)
    dp = build_dispatcher(container)

    scheduler_task = _start_scheduler(bot, container, settings)

    try:
        if settings.is_webhook:
            await _run_webhook(bot, dp, settings)
        else:
            await _run_polling(bot, dp)
    finally:
        if scheduler_task is not None:
            scheduler_task.cancel()
            try:
                await scheduler_task
            except asyncio.CancelledError:
                pass
        await bot.session.close()
        await db.disconnect()
        logger.info("Bot to'xtatildi.")


def main() -> None:
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    main()
