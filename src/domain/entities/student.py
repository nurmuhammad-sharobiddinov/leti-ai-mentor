"""O'quvchi (Student) entity'si va uning xulq-atvori."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class Student:
    """Telegram orqali kirgan o'quvchi va uning o'quv holati."""

    chat_id: int
    full_name: str
    level: int = 1
    active_topic: str | None = None
    weak_topics: list[str] = field(default_factory=list)
    mastered_topics: list[str] = field(default_factory=list)
    last_active: datetime | None = None
    created_at: datetime | None = None

    def set_active_topic(self, topic: str) -> None:
        """Joriy o'rganilayotgan mavzuni belgilash."""
        self.active_topic = topic.strip()

    def record_weakness(self, topic: str) -> None:
        """Zaif mavzuni qayd etish (takrorlamasdan)."""
        topic = topic.strip()
        if topic and topic not in self.weak_topics:
            self.weak_topics.append(topic)
        # Mavzu o'zlashtirilgan ro'yxatda bo'lsa, undan olib tashlaymiz.
        if topic in self.mastered_topics:
            self.mastered_topics.remove(topic)

    def record_mastery(self, topic: str) -> None:
        """O'zlashtirilgan mavzuni qayd etish (takrorlamasdan)."""
        topic = topic.strip()
        if topic and topic not in self.mastered_topics:
            self.mastered_topics.append(topic)
        if topic in self.weak_topics:
            self.weak_topics.remove(topic)
