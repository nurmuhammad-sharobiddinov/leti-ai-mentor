"""Ma'lumotlar omborlari uchun portlar (interfeyslar).

Domen va application qatlamlari faqat shu abstraksiyalarga bog'lanadi,
konkret Postgres realizatsiyasiga emas (Dependency Inversion Principle).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from ..entities import (
    Message,
    ReviewItem,
    Statistics,
    Student,
    StudentStats,
    TestSession,
)


class StudentRepository(ABC):
    @abstractmethod
    async def get(self, chat_id: int) -> Student | None:
        """chat_id bo'yicha o'quvchini olish (yo'q bo'lsa None)."""

    @abstractmethod
    async def upsert(self, student: Student) -> Student:
        """O'quvchini yaratish yoki yangilash."""

    @abstractmethod
    async def save(self, student: Student) -> None:
        """Mavjud o'quvchining o'zgargan holatini saqlash."""


class ConversationRepository(ABC):
    @abstractmethod
    async def add(self, chat_id: int, message: Message) -> None:
        """Suhbatga yangi xabar qo'shish."""

    @abstractmethod
    async def history(self, chat_id: int, limit: int) -> list[Message]:
        """Oxirgi `limit` ta xabarni (eskidan yangiga) qaytarish."""

    @abstractmethod
    async def clear(self, chat_id: int) -> None:
        """Suhbat tarixini tozalash."""


class TestSessionRepository(ABC):
    @abstractmethod
    async def save(self, session: TestSession) -> TestSession:
        """Test sessiyasini saqlash (yangi bo'lsa id beradi)."""

    @abstractmethod
    async def get_active(self, chat_id: int) -> TestSession | None:
        """O'quvchining faol (yakunlanmagan) test sessiyasini olish."""


class ReviewRepository(ABC):
    @abstractmethod
    async def upsert(self, item: ReviewItem) -> ReviewItem:
        """Takrorlash elementini yaratish yoki yangilash (chat_id+topic unikal)."""

    @abstractmethod
    async def get(self, review_id: int) -> ReviewItem | None:
        """id bo'yicha olish."""

    @abstractmethod
    async def get_by_topic(self, chat_id: int, topic: str) -> ReviewItem | None:
        """O'quvchi + mavzu bo'yicha olish."""

    @abstractmethod
    async def list_for_student(self, chat_id: int) -> list[ReviewItem]:
        """O'quvchining barcha takrorlash elementlari (due_at bo'yicha)."""

    @abstractmethod
    async def due_for_notification(
        self, now: datetime, notified_before: datetime
    ) -> list[ReviewItem]:
        """Vaqti kelgan va yaqinda eslatilmagan elementlar."""

    @abstractmethod
    async def mark_notified(self, review_id: int, when: datetime) -> None:
        """Eslatma yuborilganini belgilash (spam oldini olish)."""

    @abstractmethod
    async def delete(self, review_id: int) -> None:
        """Bitirilgan elementni o'chirish."""


class StatisticsRepository(ABC):
    @abstractmethod
    async def collect(self) -> Statistics:
        """Yig'ma statistikani hisoblab qaytarish."""

    @abstractmethod
    async def collect_for_student(self, chat_id: int) -> StudentStats | None:
        """Bitta o'quvchining shaxsiy statistikasini hisoblash (yo'q bo'lsa None)."""
