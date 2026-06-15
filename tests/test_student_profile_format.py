"""`/me` shaxsiy statistika formatlash testlari — sof funksiya, IO yo'q."""
from __future__ import annotations

from src.domain.entities import StudentStats
from src.presentation.telegram.formatters import format_student_profile


def test_profile_with_topics_lists_them() -> None:
    stats = StudentStats(
        full_name="Ali Valiyev",
        level=2,
        completed_tests=4,
        average_score_pct=72.5,
        mastered_topics=["kasrlar", "foizlar"],
        weak_topics=["logarifmlar"],
        due_reviews=3,
    )
    text = format_student_profile(stats)

    assert "Ali Valiyev" in text
    assert "Daraja: 2" in text
    assert "Ishlangan testlar: 4" in text
    assert "72.5%" in text
    assert "Takrorlash kutayotgan mavzular: 3" in text
    assert "kasrlar" in text
    assert "foizlar" in text
    assert "logarifmlar" in text


def test_profile_empty_topics_shows_placeholders() -> None:
    stats = StudentStats(full_name="Yangi O'quvchi")
    text = format_student_profile(stats)

    assert "O'zlashtirgan mavzular: hali yo'q" in text
    assert "Zaif mavzular: yo'q" in text
    assert "Ishlangan testlar: 0" in text
    assert "0.0%" in text
