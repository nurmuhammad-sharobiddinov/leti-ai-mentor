"""TestGenerator port'ining Anthropic realizatsiyasi (tool-use orqali)."""
from __future__ import annotations

from typing import Any

from ...domain.entities import Message, Question
from ...domain.enums import AnswerOption, QuestionKind
from ...domain.exceptions import LLMResponseError
from ...domain.ports import TestGenerator
from .anthropic_client import AnthropicClient
from .prompts import TEST_GENERATOR_SYSTEM


def _build_tool(question_count: int) -> dict[str, Any]:
    """Strukturali test uchun tool sxemasi (majburiy JSON formati)."""
    return {
        "name": "generate_test",
        "description": "Mavzu bo'yicha test savollarini strukturali tarzda qaytarish.",
        "input_schema": {
            "type": "object",
            "properties": {
                "questions": {
                    "type": "array",
                    "minItems": question_count,
                    "maxItems": question_count,
                    "items": {
                        "type": "object",
                        "properties": {
                            "kind": {
                                "type": "string",
                                "enum": [k.value for k in QuestionKind],
                            },
                            "text": {"type": "string"},
                            "options": {
                                "type": "object",
                                "properties": {
                                    opt.value: {"type": "string"}
                                    for opt in AnswerOption
                                },
                                "required": AnswerOption.values(),
                            },
                            "correct_option": {
                                "type": "string",
                                "enum": AnswerOption.values(),
                            },
                            "explanation": {"type": "string"},
                        },
                        "required": [
                            "kind",
                            "text",
                            "options",
                            "correct_option",
                            "explanation",
                        ],
                    },
                }
            },
            "required": ["questions"],
        },
    }


class LlmTestGenerator(TestGenerator):
    def __init__(
        self,
        client: AnthropicClient,
        model: str,
        question_count: int = 5,
    ) -> None:
        self._client = client
        self._model = model
        self._question_count = question_count
        self._tool = _build_tool(question_count)

    async def generate(self, topic: str, history: list[Message]) -> list[Question]:
        prompt = f'"{topic}" mavzusi bo\'yicha test savollarini tuzing.'
        messages = self._client.to_messages(history, new_user_text=prompt)

        data = await self._client.complete_tool(
            model=self._model,
            system=TEST_GENERATOR_SYSTEM,
            messages=messages,
            tool=self._tool,
        )

        raw_questions = data.get("questions")
        if not isinstance(raw_questions, list) or not raw_questions:
            raise LLMResponseError("Test savollari generatsiya qilinmadi.")

        return [
            Question(
                index=i,
                kind=QuestionKind(q["kind"]),
                text=q["text"],
                options=q["options"],
                correct_option=q["correct_option"],
                explanation=q.get("explanation", ""),
            )
            for i, q in enumerate(raw_questions)
        ]
