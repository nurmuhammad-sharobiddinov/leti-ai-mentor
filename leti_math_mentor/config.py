"""Sozlamalar — .env dan o'qiladi (python-dotenv)."""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    try:
        return int(raw) if raw else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Config:
    # Telegram
    bot_token: str

    # Anthropic
    anthropic_api_key: str
    model: str            # asosiy model (sonnet)
    hard_model: str       # qiyin matematika uchun (opus)
    max_tokens: int

    # Postgres / Supabase
    database_url: str

    # Redis (suhbat konteksti + rate-limit). Bo'sh bo'lsa — RAM fallback.
    redis_url: str | None

    # Sessiya / cheklovlar
    history_limit: int            # bir suhbatda saqlanadigan turlar soni
    session_ttl: int              # suhbat TTL (soniya)
    rate_limit_per_min: int       # daqiqasiga ruxsat etilgan xabarlar
    admin_username: str

    @classmethod
    def load(cls) -> "Config":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        db_url = os.getenv("DATABASE_URL", "").strip()
        if not token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN .env da yo'q")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY .env da yo'q")
        if not db_url:
            raise RuntimeError("DATABASE_URL .env da yo'q")

        return cls(
            bot_token=token,
            anthropic_api_key=api_key,
            model=os.getenv("MODEL", os.getenv("TEST_MODEL", "claude-sonnet-4-6")),
            hard_model=os.getenv("HARD_MODEL", os.getenv("EXPLAINER_MODEL", "claude-opus-4-8")),
            max_tokens=_int("MAX_TOKENS", 4096),
            database_url=db_url,
            redis_url=(os.getenv("REDIS_URL") or "").strip() or None,
            history_limit=_int("HISTORY_LIMIT", 20),
            session_ttl=_int("SESSION_TTL", 3600),
            rate_limit_per_min=_int("RATE_LIMIT_PER_MIN", 15),
            admin_username=os.getenv("ADMIN_USERNAME", "mrleti"),
        )
