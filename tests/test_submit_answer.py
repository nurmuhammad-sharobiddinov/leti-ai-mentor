"""SubmitAnswerUseCase robustligi — AI tahlili ishlamay qolsa ham natija qaytadi.

Bu avvalgi xatoning (oxirgi savoldan keyin sessiya bloklanishi) qaytmasligini
kafolatlaydi. Infratuzilmasiz: barcha tashqi bog'liqliklar soxta (fake).
"""
from __future__ import annotations

from datetime import UTC, datetime

from src.application.use_cases import SubmitAnswerUseCase
from src.domain.entities import Question, Student, TestSession
from src.domain.enums import QuestionKind
from src.domain.services import SpacedRepetitionPolicy


class _FakeSessions:
    def __init__(self, session: TestSession) -> None:
        self._session = session
        self.saved = False

    async def get_active(self, chat_id: int) -> TestSession | None:
        return self._session

    async def save(self, session: TestSession) -> TestSession:
        self.saved = True
        self._session = session
        return session


class _FakeStudents:
    def __init__(self, student: Student) -> None:
        self._student = student

    async def get(self, chat_id: int) -> Student | None:
        return self._student

    async def upsert(self, student: Student) -> Student:
        return student

    async def save(self, student: Student) -> None:
        return None


class _FakeReviews:
    async def upsert(self, item):
        return item

    async def get(self, review_id):
        return None

    async def get_by_topic(self, chat_id, topic):
        return None

    async def list_for_student(self, chat_id):
        return []

    async def due_for_notification(self, now, notified_before):
        return []

    async def mark_notified(self, review_id, when):
        return None

    async def delete(self, review_id):
        return None


class _BrokenAnalyst:
    """Har doim xato beradigan tahlilchi (LLM ishlamayotgan holatni simulyatsiya qiladi)."""

    async def analyze(self, topic, score, total, transcript):
        raise RuntimeError("LLM mavjud emas")


class _FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 1, 1, tzinfo=UTC)


def _single_question_session() -> TestSession:
    return TestSession(
        chat_id=1,
        topic="kasrlar",
        questions=[
            Question(
                index=0,
                kind=QuestionKind.SIMPLE,
                text="2 + 2 = ?",
                options={"A": "4", "B": "3", "C": "5", "D": "22"},
                correct_option="A",
                explanation="2 ga 2 qo'shilsa 4 bo'ladi.",
            )
        ],
        id=10,
    )


async def test_final_answer_returns_result_even_if_analysis_fails() -> None:
    sessions = _FakeSessions(_single_question_session())
    use_case = SubmitAnswerUseCase(
        students=_FakeStudents(Student(chat_id=1, full_name="Ali")),
        sessions=sessions,
        analyst=_BrokenAnalyst(),
        reviews=_FakeReviews(),
        policy=SpacedRepetitionPolicy(),
        clock=_FixedClock(),
    )

    feedback = await use_case.execute(chat_id=1, question_index=0, option="A")

    assert feedback.is_final is True
    assert feedback.is_correct is True
    assert feedback.score == 1
    assert feedback.total == 1
    # Sessiya yakunlangan deb saqlangan bo'lishi kerak.
    assert sessions.saved is True

    # AI yiqilgan bo'lsa-da, boy natija deterministik to'ldirilishi shart.
    result = feedback.final_result
    assert result is not None
    assert result.topic == "kasrlar"
    assert result.score == 1
    assert result.total == 1
    assert result.percentage == 100
    assert result.simple_correct == 1
    assert result.simple_total == 1
    assert result.answers_correct == [True]
    assert result.summary  # fallback xulosa bo'sh emas
    # AI yiqilgani uchun topiclar bo'sh bo'ladi.
    assert result.weak_topics == []
    assert result.mastered_topics == []
