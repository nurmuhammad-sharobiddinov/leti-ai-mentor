"""Webhook rejimi uchun aiohttp ilovasini sozlash."""
from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from ...infrastructure.config import Settings


def build_web_app(bot: Bot, dp: Dispatcher, settings: Settings) -> web.Application:
    """Telegram webhook so'rovlarini qabul qiluvchi aiohttp ilovasi."""
    app = web.Application()

    handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret or None,
    )
    handler.register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)
    return app


def webhook_url(settings: Settings) -> str:
    base = settings.webhook_base_url.rstrip("/")
    return f"{base}{settings.webhook_path}"
