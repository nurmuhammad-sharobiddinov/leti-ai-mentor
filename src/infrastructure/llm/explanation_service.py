"""ExplanationService port'ining Anthropic realizatsiyasi."""
from __future__ import annotations

from ...domain.entities import Message
from ...domain.ports import ExplanationService
from .anthropic_client import AnthropicClient
from .prompts import EXPLAINER_SYSTEM, REEXPLAIN_USER_TEMPLATE


class LlmExplanationService(ExplanationService):
    def __init__(
        self,
        client: AnthropicClient,
        model: str,
        admin_username: str,
    ) -> None:
        self._client = client
        self._model = model
        self._system = EXPLAINER_SYSTEM.format(admin=admin_username)

    async def explain(self, topic: str, history: list[Message]) -> str:
        messages = self._client.to_messages(history, new_user_text=topic)
        return await self._client.complete_text(
            model=self._model, system=self._system, messages=messages
        )

    async def reexplain(self, topic: str, history: list[Message]) -> str:
        prompt = REEXPLAIN_USER_TEMPLATE.format(topic=topic)
        messages = self._client.to_messages(history, new_user_text=prompt)
        return await self._client.complete_text(
            model=self._model, system=self._system, messages=messages
        )
