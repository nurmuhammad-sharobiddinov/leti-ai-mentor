"""Domen darajasidagi xatoliklar. Tashqi (infra/UI) xatolardan ajratilgan."""
from __future__ import annotations


class DomainError(Exception):
    """Barcha domen xatoliklarining bazaviy sinfi."""


class StudentNotFoundError(DomainError):
    """O'quvchi topilmadi."""


class NoActiveTopicError(DomainError):
    """O'quvchida hozircha faol (tushuntirilgan) mavzu yo'q."""


class TestSessionNotFoundError(DomainError):
    """Faol test sessiyasi topilmadi."""


class TestAlreadyCompletedError(DomainError):
    """Test allaqachon yakunlangan."""


class InvalidAnswerError(DomainError):
    """Javob joriy savolga mos kelmaydi (masalan, eski tugma bosildi)."""


class LLMResponseError(DomainError):
    """LLM kutilgan formatda javob qaytarmadi."""
