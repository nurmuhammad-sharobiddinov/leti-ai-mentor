"""Domen mantig'i testlari — hech qanday infratuzilma (DB/LLM) talab qilmaydi.

Bu Clean Architecture'ning asosiy yutug'i: biznes qoidalari mustaqil tekshiriladi.
"""
from __future__ import annotations

import pytest

from src.domain.entities import Question, TestSession
from src.domain.enums import QuestionKind, TestStatus
from src.domain.exceptions import InvalidAnswerError, TestAlreadyCompletedError


def _question(index: int, correct: str = "A") -> Question:
    return Question(
        index=index,
        kind=QuestionKind.SIMPLE,
        text=f"Savol {index}",
        options={"A": "1", "B": "2", "C": "3", "D": "4"},
        correct_option=correct,
        explanation="izoh",
    )


def _session(n: int = 3) -> TestSession:
    return TestSession(
        chat_id=1,
        topic="kasrlar",
        questions=[_question(i) for i in range(n)],
    )


def test_correct_answer_increments_score() -> None:
    session = _session()
    answer = session.submit(0, "A")
    assert answer.is_correct is True
    assert session.score == 1
    assert session.current_index == 1


def test_wrong_answer_does_not_increment_score() -> None:
    session = _session()
    answer = session.submit(0, "B")
    assert answer.is_correct is False
    assert session.score == 0


def test_completing_all_questions_marks_completed() -> None:
    session = _session(2)
    session.submit(0, "A")
    session.submit(1, "A")
    assert session.is_finished is True
    assert session.status is TestStatus.COMPLETED
    assert session.score == 2


def test_stale_question_index_is_rejected() -> None:
    session = _session()
    with pytest.raises(InvalidAnswerError):
        session.submit(2, "A")  # joriy index 0, eski tugma 2


def test_submitting_after_completion_raises() -> None:
    session = _session(1)
    session.submit(0, "A")
    with pytest.raises(TestAlreadyCompletedError):
        session.submit(0, "A")
