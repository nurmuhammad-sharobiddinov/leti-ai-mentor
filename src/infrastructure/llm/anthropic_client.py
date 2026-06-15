"""Anthropic API ustidagi yupqa adapter.

Ikki rejim:
  * complete_text  — erkin matnli javob (tushuntirish uchun)
  * complete_tool  — majburiy tool-use orqali strukturali JSON (test/tahlil uchun)

tool-use n8n'dagi mo'rt "```json ... ```" parse qilishdan ko'ra ancha ishonchli.
"""
from __future__ import annotations

from typing import Any

from anthropic import AsyncAnthropic

from ...domain.entities import Message
from ...domain.enums import Role
from ...domain.exceptions import LLMResponseError
from .resilience import AsyncRetrier, Throttler


class AnthropicClient:
    """Anthropic API adapteri — retry va rate-limit bilan o'ralgan."""

    def __init__(
        self,
        api_key: str,
        max_tokens: int = 4096,
        retrier: AsyncRetrier | None = None,
        throttler: Throttler | None = None,
    ) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._max_tokens = max_tokens
        self._retrier = retrier
        self._throttler = throttler

    async def _create(self, **kwargs: Any):
        """messages.create chaqiruvini throttle + retry bilan bajaradi."""

        async def factory():
            if self._throttler is not None:
                async with self._throttler:
                    return await self._client.messages.create(**kwargs)
            return await self._client.messages.create(**kwargs)

        if self._retrier is not None:
            return await self._retrier.run(factory)
        return await factory()

    async def complete_text(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
    ) -> str:
        response = await self._create(
            model=model,
            max_tokens=self._max_tokens,
            system=system,
            messages=messages,
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        if not text:
            raise LLMResponseError("LLM bo'sh matn qaytardi.")
        return text

    async def complete_tool(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        tool: dict[str, Any],
    ) -> dict[str, Any]:
        """Modelni berilgan tool'ni chaqirishga majburlaydi va input'ini qaytaradi."""
        response = await self._create(
            model=model,
            max_tokens=self._max_tokens,
            system=system,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
        )
        for block in response.content:
            if block.type == "tool_use":
                return dict(block.input)
        raise LLMResponseError("LLM kutilgan tool-use bloki qaytarmadi.")

    @staticmethod
    def to_messages(
        history: list[Message],
        new_user_text: str | None = None,
    ) -> list[dict[str, str]]:
        """Domen xabarlarini Anthropic messages formatiga o'tkazish.

        Anthropic birinchi xabar 'user' bo'lishini talab qiladi, shuning uchun
        boshidagi 'assistant' xabarlar olib tashlanadi.
        """
        items = list(history)
        while items and items[0].role is Role.ASSISTANT:
            items.pop(0)

        messages = [{"role": m.role.value, "content": m.content} for m in items]
        if new_user_text is not None:
            messages.append({"role": "user", "content": new_user_text})
        return messages
