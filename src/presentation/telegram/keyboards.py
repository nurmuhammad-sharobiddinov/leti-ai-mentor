"""Inline klaviatura quruvchilari (Factory'lar).

UI tafsilotlari shu yerda jamlangan — handler'lar faqat tayyor klaviaturani
oladi (Single Responsibility).
"""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ...application.dto import QuestionView
from ...domain.entities import ReviewItem
from .callbacks import AnswerAction, ExplanationAction, ReviewAction


def explanation_keyboard() -> InlineKeyboardMarkup:
    """Tushuntirishdan keyingi 2 ta tugma."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔄 Qayta tushuntirish",
        callback_data=ExplanationAction(action="again"),
    )
    builder.button(
        text="✅ Tushundim, testni boshlash",
        callback_data=ExplanationAction(action="test"),
    )
    builder.adjust(1)  # har biri alohida qatorda
    return builder.as_markup()


def question_keyboard(question: QuestionView) -> InlineKeyboardMarkup:
    """Test savoli uchun 4 variant (A/B 1-qatorda, C/D 2-qatorda)."""
    buttons = [
        InlineKeyboardButton(
            text=f"{option}) {text}",
            callback_data=AnswerAction(
                question_index=question.index, option=option
            ).pack(),
        )
        for option, text in question.options.items()
    ]
    rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def review_start_keyboard(review_id: int) -> InlineKeyboardMarkup:
    """Eslatma xabaridagi 'Takrorlashni boshlash' tugmasi."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔁 Takrorlashni boshlash",
        callback_data=ReviewAction(review_id=review_id),
    )
    return builder.as_markup()


def review_list_keyboard(items: list[ReviewItem]) -> InlineKeyboardMarkup:
    """/review buyrug'i uchun — har bir mavzu alohida tugma."""
    builder = InlineKeyboardBuilder()
    for item in items:
        if item.id is None:
            continue
        builder.button(
            text=f"🔁 {item.topic}",
            callback_data=ReviewAction(review_id=item.id),
        )
    builder.adjust(1)
    return builder.as_markup()
