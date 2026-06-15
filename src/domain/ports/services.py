"""Tashqi (AI) xizmatlar uchun portlar.

Konkret LLM provayderi (Anthropic) infrastructure qatlamida realizatsiya
qilinadi. Domen faqat bu interfeyslarni biladi.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..entities import AnalysisResult, Message, Question


class ExplanationService(ABC):
    """Mavzuni tushuntiruvchi AI mentor."""

    @abstractmethod
    async def explain(self, topic: str, history: list[Message]) -> str:
        """Mavzuni birinchi marta tushuntirish."""

    @abstractmethod
    async def reexplain(self, topic: str, history: list[Message]) -> str:
        """Mavzuni soddaroq, boshqacha misollar bilan qayta tushuntirish."""


class TestGenerator(ABC):
    """Mavzu bo'yicha test (5 savol) generatsiya qiluvchi AI."""

    @abstractmethod
    async def generate(self, topic: str, history: list[Message]) -> list[Question]:
        """Strukturalangan savollar ro'yxatini qaytarish."""


class PerformanceAnalyst(ABC):
    """Test natijasini tahlil qiluvchi AI."""

    @abstractmethod
    async def analyze(
        self,
        topic: str,
        score: int,
        total: int,
        transcript: str,
    ) -> AnalysisResult:
        """Natija bo'yicha xulosa, zaif va o'zlashtirilgan mavzularni qaytarish."""
