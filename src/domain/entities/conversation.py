"""Suhbat xabari entity'si — LLM kontekst xotirasi uchun."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..enums import Role


@dataclass(slots=True)
class Message:
    """O'quvchi va mentor o'rtasidagi bitta xabar."""

    role: Role
    content: str
    created_at: datetime | None = None

    @classmethod
    def user(cls, content: str) -> Message:
        return cls(role=Role.USER, content=content)

    @classmethod
    def assistant(cls, content: str) -> Message:
        return cls(role=Role.ASSISTANT, content=content)
