"""Claude API bilan ishlash — tushuntirish, rasm o'qish (vision), mashq tuzish/tekshirish.

Optimizatsiyalar:
- prompt caching: katta system prompt cache_control bilan yuboriladi (kirish token narxi kamayadi).
- Opus auto-routing: qiyin masala aniqlansa kuchliroq modelga (hard_model) yuboriladi.
Timeout + retry shu yerda. Parse funksiyalari modul darajasida (toza, testlanadi).
"""
from __future__ import annotations

import asyncio
import logging
import re

from anthropic import AsyncAnthropic
from anthropic import APIError, APITimeoutError, RateLimitError

from leti_math_mentor.config import Config
from leti_math_mentor import prompts
from leti_math_mentor.taxonomy import normalize_topic

logger = logging.getLogger(__name__)

_TOPIC_RE = re.compile(r"\[TOPIC:\s*([^\]]+)\]", re.IGNORECASE)
_VERDICT_RE = re.compile(r"VERDICT:\s*(correct|wrong)", re.IGNORECASE)

# retry qilinadigan vaqtinchalik xatolar
_RETRYABLE = (APITimeoutError, RateLimitError)

# Qiyin (Opus'ga arzigulik) masala belgilari — bo'lsa kuchliroq modelga yuboramiz.
_HARD_MARKERS = (
    "integral", "limit", "lim ", "isbot", "isbotla", "teorema", "matritsa",
    "determinant", "kompleks son", "differensial tenglama", "ekstremum",
    "sistema", "parametr", "induksiya", "kombinator", "ehtimol",
)


def parse_topic(raw: str) -> tuple[str, str]:
    """(toza_matn, normalizatsiyalangan_mavzu). Teg bo'lmasa mavzu 'umumiy'."""
    m = _TOPIC_RE.search(raw)
    topic = normalize_topic(m.group(1) if m else None)
    clean = _TOPIC_RE.sub("", raw).strip()
    return clean, topic


def parse_verdict(raw: str) -> tuple[bool, str]:
    """(to'g'rimi, izoh). VERDICT qatori o'quvchiga ko'rsatilmaydi."""
    m = _VERDICT_RE.search(raw)
    is_correct = bool(m) and m.group(1).lower() == "correct"
    feedback = _VERDICT_RE.sub("", raw, count=1).strip()
    return is_correct, feedback


def is_hard_problem(text: str) -> bool:
    """Oddiy evristika: qiyin mavzu belgilari yoki uzun ko'p qadamli masala."""
    low = (text or "").lower()
    if any(marker in low for marker in _HARD_MARKERS):
        return True
    # juda uzun (ko'p shartli) masala ham qiyin deb hisoblanadi
    return len(low) > 400


class ClaudeService:
    def __init__(self, cfg: Config) -> None:
        self._cfg = cfg
        self._client = AsyncAnthropic(
            api_key=cfg.anthropic_api_key,
            timeout=60.0,
            max_retries=0,  # retry'ni o'zimiz boshqaramiz
        )

    @staticmethod
    def _cached_system(text: str) -> list[dict]:
        """System promptni cache_control bilan blok ko'rinishida beradi (prompt caching)."""
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    async def _create(self, *, model: str, system, messages: list[dict], max_tokens: int) -> str:
        """Bitta chaqiruv — 2 marta qayta urinish, eksponensial kutish bilan."""
        last_exc: Exception | None = None
        for attempt in range(3):  # 1 asosiy + 2 retry
            try:
                resp = await self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                )
                parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
                return "".join(parts).strip()
            except _RETRYABLE as exc:
                last_exc = exc
                delay = 1.5 * (2**attempt)
                logger.warning("Claude vaqtinchalik xato (urinish %s): %s — %.1fs kutamiz", attempt + 1, exc, delay)
                await asyncio.sleep(delay)
            except APIError as exc:
                logger.error("Claude API xatosi: %s", exc)
                raise
        assert last_exc is not None
        raise last_exc

    # --- Funksiya 1: Sokratik savol-javob ---
    async def ask_mentor(
        self,
        history: list[dict],
        user_text: str,
        image_b64: str | None = None,
        hard: bool | None = None,
    ) -> tuple[str, str]:
        """Suhbat tarixi + yangi xabar → (javob_matni, normalizatsiyalangan_mavzu).

        hard=None bo'lsa masala qiyinligi avtomatik aniqlanadi (Opus auto-routing).
        """
        content: list[dict] | str
        if image_b64:
            content = [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64},
                },
                {"type": "text", "text": user_text or "Mana bu masalani tushunishga yordam ber."},
            ]
        else:
            content = user_text

        messages = [*history, {"role": "user", "content": content}]
        system = self._cached_system(prompts.MENTOR_SYSTEM + prompts.TOPIC_TAG_INSTRUCTION)

        if hard is None:
            # rasmli masala ham odatda qiyinroq (vision + tahlil)
            hard = is_hard_problem(user_text) or image_b64 is not None
        model = self._cfg.hard_model if hard else self._cfg.model

        raw = await self._create(
            model=model, system=system, messages=messages, max_tokens=self._cfg.max_tokens
        )
        return parse_topic(raw)

    # --- Funksiya 2: Mashq tuzish ---
    async def generate_practice(self, topic: str, level: str = "o'rta") -> str:
        prompt = f"Mavzu: {topic}\nDaraja: {level}\nShu mavzu va darajada bitta masala tuz."
        return await self._create(
            model=self._cfg.model,
            system=self._cached_system(prompts.PRACTICE_GENERATE_SYSTEM),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )

    # --- Funksiya 2: Javobni tekshirish ---
    async def check_answer(self, problem: str, answer: str) -> tuple[bool, str]:
        prompt = f"MASALA:\n{problem}\n\nO'QUVCHI JAVOBI:\n{answer}"
        raw = await self._create(
            model=self._cfg.model,
            system=self._cached_system(prompts.PRACTICE_CHECK_SYSTEM),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return parse_verdict(raw)
