"""Spaced-repetition siyosati testlari — sof domen, IO yo'q."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.domain.entities import ReviewItem
from src.domain.services import DEFAULT_INTERVALS_DAYS, SpacedRepetitionPolicy

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _policy() -> SpacedRepetitionPolicy:
    return SpacedRepetitionPolicy()


def test_new_weak_topic_scheduled_soon() -> None:
    item = _policy().on_weak(None, chat_id=1, topic="kasrlar", now=NOW)
    assert item.box == 0
    assert item.due_at == NOW + timedelta(days=DEFAULT_INTERVALS_DAYS[0])


def test_weak_again_lowers_box() -> None:
    existing = ReviewItem(chat_id=1, topic="kasrlar", box=3)
    item = _policy().on_weak(existing, chat_id=1, topic="kasrlar", now=NOW)
    assert item.box == 2


def test_mastered_unknown_topic_is_ignored() -> None:
    assert _policy().on_mastered(None, NOW) is None


def test_mastered_advances_box() -> None:
    existing = ReviewItem(chat_id=1, topic="kasrlar", box=1)
    item = _policy().on_mastered(existing, NOW)
    assert item is not None
    assert item.box == 2
    assert item.due_at == NOW + timedelta(days=DEFAULT_INTERVALS_DAYS[2])


def test_graduation_returns_none() -> None:
    last_box = len(DEFAULT_INTERVALS_DAYS) - 1
    existing = ReviewItem(chat_id=1, topic="kasrlar", box=last_box)
    assert _policy().on_reviewed(existing, NOW) is None
