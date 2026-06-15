"""Domen darajasidagi sanab o'tilgan turlar (enums)."""
from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    """Suhbat xabarining muallifi (LLM xotirasi uchun)."""

    USER = "user"
    ASSISTANT = "assistant"


class TestStatus(str, Enum):
    """Test sessiyasining holati."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuestionKind(str, Enum):
    """Savol turi: oddiy (tushunish) yoki mantiqiy (qo'llash)."""

    SIMPLE = "simple"
    LOGICAL = "logical"


class AnswerOption(str, Enum):
    """Test javob variantlari."""

    A = "A"
    B = "B"
    C = "C"
    D = "D"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]
