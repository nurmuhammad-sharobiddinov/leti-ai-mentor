"""Takrorlash elementi (ReviewItem) — spaced-repetition uchun entity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ReviewItem:
    """O'quvchining zaif mavzusi va uni qayta ko'rish jadvali.

    `box` — Leitner qutisi (0 dan boshlanadi; yuqori qutilar uzoqroq oraliq).
    `due_at` — keyingi takrorlash vaqti.
    """

    chat_id: int
    topic: str
    box: int = 0
    due_at: datetime | None = None
    last_reviewed: datetime | None = None
    last_notified: datetime | None = None
    id: int | None = None
