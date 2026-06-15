"""Clock port'ining tizim realizatsiyasi."""
from __future__ import annotations

from datetime import UTC, datetime

from ..domain.ports import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
