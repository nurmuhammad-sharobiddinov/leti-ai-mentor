"""Ilova konfiguratsiyasi — .env fayldan o'qiladi (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Majburiy maxfiy qiymatlar ---
    telegram_bot_token: str
    anthropic_api_key: str
    database_url: str

    # --- LLM modellari ---
    explainer_model: str = "claude-opus-4-8"
    test_model: str = "claude-sonnet-4-6"
    analysis_model: str = "claude-sonnet-4-6"

    # --- Umumiy sozlamalar ---
    max_tokens: int = 4096
    history_limit: int = 50
    questions_per_test: int = 5
    admin_username: str = "mrleti"
    auto_migrate: bool = True

    # --- Bot rejimi ---
    bot_mode: str = "polling"  # "polling" | "webhook"
    webhook_base_url: str = ""
    webhook_path: str = "/webhook"
    webhook_secret: str = ""
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8080

    # --- LLM barqarorligi (retry + rate-limit) ---
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0
    llm_max_concurrency: int = 4

    # --- Spaced-repetition ---
    review_enabled: bool = True
    review_poll_interval_seconds: int = 3600
    review_notify_cooldown_hours: int = 20

    # --- Admin (vergul bilan ajratilgan chat_id'lar) ---
    admin_ids_raw: str = Field(
        default="",
        validation_alias=AliasChoices("ADMIN_IDS", "admin_ids_raw"),
    )

    @property
    def admin_ids(self) -> set[int]:
        return {
            int(part)
            for part in self.admin_ids_raw.replace(" ", "").split(",")
            if part
        }

    @property
    def is_webhook(self) -> bool:
        return self.bot_mode.strip().lower() == "webhook"


@lru_cache
def get_settings() -> Settings:
    """Sozlamalarni bir marta yuklab, keshlab qaytaradi."""
    return Settings()  # type: ignore[call-arg]
