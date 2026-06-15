"""Vaqt manbai porti — use case'larni vaqtdan ajratadi (testlanadigan qiladi)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    @abstractmethod
    def now(self) -> datetime:
        """Joriy vaqt (UTC, timezone-aware)."""
