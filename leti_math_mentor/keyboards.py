"""Menyu va mavzu tugmalari."""
from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# --- Asosiy menyu (reply keyboard) ---
BTN_QUESTION = "📚 Savol berish"
BTN_PRACTICE = "✏️ Mashq"
BTN_PROGRESS = "📊 Progress"

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_QUESTION), KeyboardButton(text=BTN_PRACTICE)],
        [KeyboardButton(text=BTN_PROGRESS)],
    ],
    resize_keyboard=True,
    input_field_placeholder="Mavzu yoki masala yozing...",
)

# --- Mashq uchun mavzular (inline) ---
# callback_data formati: "practice_topic:<topic_key>"
TOPICS: list[tuple[str, str]] = [
    ("Kvadrat tenglamalar", "kvadrat_tenglama"),
    ("Kasrlar", "kasrlar"),
    ("Foizlar", "foiz"),
    ("Hosila", "hosila"),
    ("Trigonometriya", "trigonometriya"),
    ("Logarifmlar", "logarifm"),
    ("Geometriya (yuza)", "geometriya_yuza"),
    ("Progressiyalar", "progressiya"),
]


def topics_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(TOPICS), 2):
        row = [
            InlineKeyboardButton(text=label, callback_data=f"practice_topic:{key}")
            for label, key in TOPICS[i : i + 2]
        ]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)
