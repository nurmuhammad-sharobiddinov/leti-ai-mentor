"""Spaced-repetition siyosati — sof domen mantig'i (IO yo'q, testlanadigan).

Leitner tizimi: har bir to'g'ri takrordan keyin mavzu yuqori "quti"ga o'tadi
va keyingi takrorlash oralig'i uzayadi. Xato (zaiflik) qutini pasaytiradi.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ..entities import ReviewItem

# Har bir quti uchun keyingi takrorlashgacha kunlar soni.
DEFAULT_INTERVALS_DAYS: tuple[int, ...] = (1, 3, 7, 16, 35)


class SpacedRepetitionPolicy:
    def __init__(self, intervals_days: tuple[int, ...] = DEFAULT_INTERVALS_DAYS) -> None:
        if not intervals_days:
            raise ValueError("Kamida bitta oraliq kerak.")
        self._intervals = intervals_days

    @property
    def _max_box(self) -> int:
        return len(self._intervals) - 1

    def _due(self, box: int, now: datetime) -> datetime:
        idx = max(0, min(box, self._max_box))
        return now + timedelta(days=self._intervals[idx])

    def on_weak(
        self,
        existing: ReviewItem | None,
        chat_id: int,
        topic: str,
        now: datetime,
    ) -> ReviewItem:
        """Mavzu zaif chiqdi — qutini pasaytirib, tez orada takror rejalashtiramiz."""
        if existing is None:
            return ReviewItem(
                chat_id=chat_id, topic=topic, box=0, due_at=self._due(0, now)
            )
        existing.box = max(0, existing.box - 1)
        existing.due_at = self._due(existing.box, now)
        return existing

    def on_mastered(self, existing: ReviewItem | None, now: datetime) -> ReviewItem | None:
        """Mavzu o'zlashtirildi.

        Jadvalda bo'lmasa — hech narsa qilmaymiz (allaqachon biladi).
        Bor bo'lsa — qutini oshiramiz; eng yuqori qutidan o'tsa "bitiradi" (None).
        """
        if existing is None:
            return None
        return self._advance(existing, now)

    def on_reviewed(self, existing: ReviewItem, now: datetime) -> ReviewItem | None:
        """Foydalanuvchi mavzuni qayta ko'rib chiqdi — qutini oshiramiz."""
        return self._advance(existing, now)

    def _advance(self, item: ReviewItem, now: datetime) -> ReviewItem | None:
        next_box = item.box + 1
        if next_box > self._max_box:
            return None  # bitirildi — jadvaldan o'chiriladi
        item.box = next_box
        item.due_at = self._due(next_box, now)
        item.last_reviewed = now
        return item
