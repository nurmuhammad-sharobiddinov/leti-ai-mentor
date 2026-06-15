"""Inline tugmalar uchun callback_data fabrikalari (type-safe).

aiogram'ning CallbackData mexanizmi n8n'dagi "explain_again" / "ans_A" kabi
qator literallarni o'rniga bosadi va parse qilishni avtomatlashtiradi.
"""
from __future__ import annotations

from aiogram.filters.callback_data import CallbackData


class ExplanationAction(CallbackData, prefix="exp"):
    """Tushuntirishdan keyingi amallar."""

    action: str  # "again" | "test"


class AnswerAction(CallbackData, prefix="ans"):
    """Test savoliga javob: qaysi savol va qaysi variant."""

    question_index: int
    option: str  # "A" | "B" | "C" | "D"


class ReviewAction(CallbackData, prefix="rev"):
    """Takrorlashni boshlash: qaysi review elementi (id orqali)."""

    review_id: int
