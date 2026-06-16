"""Yangi mentor paketi (leti_math_mentor) uchun testlar — tarmoq/DB talab qilmaydi."""
from __future__ import annotations

from leti_math_mentor.services.claude import is_hard_problem, parse_topic, parse_verdict
from leti_math_mentor.services.memory import ConversationMemory
from leti_math_mentor.services.ratelimit import RateLimiter
from leti_math_mentor.taxonomy import normalize_topic


# --- parse_topic ---
def test_parse_topic_extracts_and_normalizes():
    raw = "Yaxshi urinish!\n\n[TOPIC: kvadrat tenglamalar]"
    clean, topic = parse_topic(raw)
    assert "[TOPIC" not in clean
    assert clean == "Yaxshi urinish!"
    assert topic == "kvadrat_tenglama"  # sinonim -> kanonik


def test_parse_topic_missing_tag_is_umumiy():
    clean, topic = parse_topic("Hech qanday teg yo'q.")
    assert clean == "Hech qanday teg yo'q."
    assert topic == "umumiy"


# --- parse_verdict ---
def test_parse_verdict_correct():
    ok, fb = parse_verdict("VERDICT: correct\nJuda yaxshi, to'g'ri yeching!")
    assert ok is True
    assert "VERDICT" not in fb
    assert "Juda yaxshi" in fb


def test_parse_verdict_wrong():
    ok, fb = parse_verdict("VERDICT: wrong\nBu yerda adashding.")
    assert ok is False
    assert "VERDICT" not in fb


def test_parse_verdict_no_marker_defaults_false():
    ok, _ = parse_verdict("Umuman tushunarsiz javob")
    assert ok is False


# --- is_hard_problem ---
def test_is_hard_problem_marker():
    assert is_hard_problem("Bu integralni hisobla: ∫ x dx") is True
    assert is_hard_problem("teoremani isbotla") is True


def test_is_hard_problem_simple():
    assert is_hard_problem("2 + 2 nechi?") is False


def test_is_hard_problem_long():
    assert is_hard_problem("x " * 250) is True  # 400 belgidan uzun


# --- normalize_topic ---
def test_normalize_topic_synonyms():
    assert normalize_topic("sinuslar") == "trigonometriya"
    assert normalize_topic("logarifmik tenglama") == "logarifm"
    assert normalize_topic("uchburchak yuzasi") == "geometriya_yuza"
    assert normalize_topic(None) == "umumiy"
    assert normalize_topic("allambalo mavzu") == "umumiy"


# --- RateLimiter (RAM fallback, redis=None) ---
async def test_ratelimit_ram_allows_then_blocks():
    rl = RateLimiter(None, per_minute=3)
    assert await rl.allow(111) is True
    assert await rl.allow(111) is True
    assert await rl.allow(111) is True
    assert await rl.allow(111) is False  # 4-chi bloklanadi
    # boshqa foydalanuvchiga ta'sir qilmaydi
    assert await rl.allow(222) is True


async def test_ratelimit_disabled_when_zero():
    rl = RateLimiter(None, per_minute=0)
    for _ in range(50):
        assert await rl.allow(1) is True


# --- ConversationMemory (RAM fallback, redis_url=None) ---
async def test_memory_ram_roundtrip_and_limit():
    mem = ConversationMemory(redis_url=None, history_limit=4, ttl=3600)
    await mem.connect()  # Redis yo'q -> RAM
    for i in range(6):
        await mem.add_turn(7, "user", f"xabar {i}")
    hist = await mem.get_history(7)
    assert len(hist) == 4  # limit
    assert hist[0]["content"] == "xabar 2"  # eng eskilari kesilgan
    assert hist[-1]["content"] == "xabar 5"
    assert all(h["role"] == "user" for h in hist)


async def test_memory_reset():
    mem = ConversationMemory(redis_url=None, history_limit=10, ttl=3600)
    await mem.connect()
    await mem.add_turn(9, "user", "salom")
    assert len(await mem.get_history(9)) == 1
    await mem.reset(9)
    assert await mem.get_history(9) == []
