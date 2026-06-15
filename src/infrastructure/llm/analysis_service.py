"""PerformanceAnalyst port'ining Anthropic realizatsiyasi (tool-use orqali)."""
from __future__ import annotations

from typing import Any

from ...domain.entities import AnalysisResult
from ...domain.ports import PerformanceAnalyst
from .anthropic_client import AnthropicClient
from .prompts import ANALYST_SYSTEM

_ANALYSIS_TOOL: dict[str, Any] = {
    "name": "report_analysis",
    "description": "Test natijasi bo'yicha tahlil va xulosani qaytarish.",
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "O'quvchiga yuboriladigan to'liq tahlil matni.",
            },
            "weak_topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "O'quvchi qiynalgan kichik mavzular.",
            },
            "mastered_topics": {
                "type": "array",
                "items": {"type": "string"},
                "description": "O'quvchi yaxshi o'zlashtirgan kichik mavzular.",
            },
        },
        "required": ["summary", "weak_topics", "mastered_topics"],
    },
}


class LlmPerformanceAnalyst(PerformanceAnalyst):
    def __init__(self, client: AnthropicClient, model: str) -> None:
        self._client = client
        self._model = model

    async def analyze(
        self,
        topic: str,
        score: int,
        total: int,
        transcript: str,
    ) -> AnalysisResult:
        prompt = (
            f"Mavzu: {topic}\n"
            f"Natija: {score}/{total} to'g'ri.\n\n"
            f"Bayonnoma:\n{transcript}\n\n"
            "Shu natijaga ko'ra tahlil va xulosani ber."
        )
        data = await self._client.complete_tool(
            model=self._model,
            system=ANALYST_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            tool=_ANALYSIS_TOOL,
        )
        return AnalysisResult(
            summary=data.get("summary", ""),
            weak_topics=list(data.get("weak_topics", [])),
            mastered_topics=list(data.get("mastered_topics", [])),
        )
