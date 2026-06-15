"""Application qatlami DTO'lari — use case'lar bilan presentation o'rtasidagi shartnoma.

Domen entity'larini to'g'ridan-to'g'ri UI'ga oqizmaslik uchun sodda,
o'qishbop ko'rinishlar.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ExplanationResult:
    """Tushuntirish natijasi (o'quvchiga yuboriladigan matn)."""

    text: str


@dataclass(slots=True)
class ReviewDue:
    """Eslatma yuborilishi kerak bo'lgan takrorlash elementi."""

    review_id: int
    chat_id: int
    topic: str


@dataclass(slots=True)
class QuestionView:
    """Bitta savolning UI uchun ko'rinishi (to'g'ri javobsiz!)."""

    index: int
    text: str
    options: dict[str, str]
    number: int  # 1-asosli tartib raqami (1..total)
    total: int


@dataclass(slots=True)
class TestResultView:
    """Test yakunidagi to'liq natija — boy, statistik UI ko'rinishi.

    Barcha sonli statistika domenda deterministik hisoblanadi; `summary` va
    topiclar AI tahlilidan keladi (mavjud bo'lmasa bo'sh/fallback).
    """

    topic: str
    score: int
    total: int
    simple_correct: int
    simple_total: int
    logical_correct: int
    logical_total: int
    answers_correct: list[bool]  # har bir savol to'g'ri/noto'g'ri (savol tartibida)
    summary: str
    weak_topics: list[str] = field(default_factory=list)
    mastered_topics: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> int:
        return round(self.score / self.total * 100) if self.total else 0


@dataclass(slots=True)
class AnswerFeedback:
    """Javobdan keyingi natija: keyingi savol yoki yakuniy natija."""

    is_correct: bool
    correct_option: str
    explanation: str
    score: int
    total: int
    next_question: QuestionView | None = None
    final_result: TestResultView | None = None

    @property
    def is_final(self) -> bool:
        return self.next_question is None
