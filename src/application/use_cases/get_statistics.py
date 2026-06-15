"""Admin statistikasini olish use case'i."""
from __future__ import annotations

from ...domain.entities import Statistics
from ...domain.ports import StatisticsRepository


class GetStatisticsUseCase:
    def __init__(self, statistics: StatisticsRepository) -> None:
        self._statistics = statistics

    async def execute(self) -> Statistics:
        return await self._statistics.collect()
