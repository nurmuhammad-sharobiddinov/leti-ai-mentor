"""Admin statistikasi uchun qiymat obyektlari (read-model)."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class TopicCount:
    topic: str
    count: int


@dataclass(slots=True)
class Statistics:
    """Yig'ma statistika — admin paneliga ko'rsatish uchun."""

    total_students: int = 0
    active_today: int = 0
    completed_tests: int = 0
    average_score_pct: float = 0.0
    top_weak_topics: list[TopicCount] = field(default_factory=list)


@dataclass(slots=True)
class StudentStats:
    """Bitta o'quvchining shaxsiy statistikasi (read-model, /me buyrug'i uchun)."""

    full_name: str
    level: int = 1
    completed_tests: int = 0
    average_score_pct: float = 0.0
    mastered_topics: list[str] = field(default_factory=list)
    weak_topics: list[str] = field(default_factory=list)
    due_reviews: int = 0
