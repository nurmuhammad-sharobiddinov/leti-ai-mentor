"""Test yakuniy natija kartasi formatlash testlari — sof funksiya, IO yo'q."""
from __future__ import annotations

from src.application.dto import TestResultView
from src.presentation.telegram.formatters import format_test_result


def _result(**over) -> TestResultView:
    base = dict(
        topic="Logarifmlar",
        score=4,
        total=5,
        simple_correct=2,
        simple_total=2,
        logical_correct=2,
        logical_total=3,
        answers_correct=[True, True, False, True, True],
        summary="Yaxshi natija, davom eting.",
        weak_topics=["logarifm xossalari"],
        mastered_topics=["asosiy logarifm"],
    )
    base.update(over)
    return TestResultView(**base)


def test_result_card_shows_core_stats() -> None:
    text = format_test_result(_result())

    assert "Logarifmlar" in text
    assert "4/5" in text
    assert "(80%)" in text
    assert "🏆 A'lo" in text  # 80% -> a'lo
    assert "Oddiy:    2/2" in text
    assert "Mantiqiy: 2/3" in text
    assert "✅ ✅ ❌ ✅ ✅" in text  # har bir savol ko'rinadi
    assert "logarifm xossalari" in text  # zaif mavzu
    assert "asosiy logarifm" in text  # kuchli mavzu
    assert "/review" in text and "/me" in text


def test_result_card_without_ai_topics() -> None:
    text = format_test_result(
        _result(weak_topics=[], mastered_topics=[], summary="")
    )

    assert "4/5" in text
    # AI topiclari bo'lmasa, ularning sarlavhalari chiqmasligi kerak.
    assert "Takrorlash kerak:" not in text
    assert "Kuchli tomonlaringiz:" not in text