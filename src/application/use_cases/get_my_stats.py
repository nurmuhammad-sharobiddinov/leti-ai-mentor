"""O'quvchining shaxsiy statistikasini olish use case'i (/me buyrug'i)."""
from __future__ import annotations

from ...domain.entities import StudentStats
from ...domain.ports import StatisticsRepository


class GetMyStatsUseCase:
    def __init__(self, statistics: StatisticsRepository) -> None:
        self._statistics = statistics

    async def execute(self, chat_id: int) -> StudentStats | None:
        return await self._statistics.collect_for_student(chat_id)
