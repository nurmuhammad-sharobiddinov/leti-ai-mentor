"""Test sessiyasi — domenning yuragi.

n8n versiyasidan farqli o'laroq, test holati (nechanchi savol, ball)
LLM xotirasiga emas, shu entity'ga tayanadi. Ballash deterministik.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..enums import QuestionKind, TestStatus
from ..exceptions import InvalidAnswerError, TestAlreadyCompletedError


@dataclass(slots=True)
class Question:
    """Bitta test savoli, to'g'ri javobi va izohi bilan birga."""

    index: int
    kind: QuestionKind
    text: str
    options: dict[str, str]  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_option: str
    explanation: str


@dataclass(slots=True)
class SubmittedAnswer:
    """O'quvchi bergan javob va uning to'g'riligi."""

    question_index: int
    selected_option: str
    is_correct: bool


@dataclass(slots=True)
class AnalysisResult:
    """Test yakunidagi AI tahlili natijasi."""

    summary: str
    weak_topics: list[str] = field(default_factory=list)
    mastered_topics: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TestSession:
    """O'quvchining bitta test urinishi — holat mashinasi (state machine)."""

    chat_id: int
    topic: str
    questions: list[Question]
    answers: list[SubmittedAnswer] = field(default_factory=list)
    current_index: int = 0
    status: TestStatus = TestStatus.IN_PROGRESS
    id: int | None = None

    @property
    def total(self) -> int:
        return len(self.questions)

    @property
    def score(self) -> int:
        return sum(1 for a in self.answers if a.is_correct)

    @property
    def is_finished(self) -> bool:
        return self.current_index >= self.total

    @property
    def current_question(self) -> Question:
        if self.is_finished:
            raise TestAlreadyCompletedError("Barcha savollar yakunlangan.")
        return self.questions[self.current_index]

    def submit(self, question_index: int, option: str) -> SubmittedAnswer:
        """Joriy savolga javobni qabul qilish va keyingisiga o'tish.

        question_index — eski tugmalar bosilishidan himoya uchun tekshiriladi.
        """
        if self.status is TestStatus.COMPLETED:
            raise TestAlreadyCompletedError("Test allaqachon yakunlangan.")
        if question_index != self.current_index:
            raise InvalidAnswerError(
                f"Kutilgan savol {self.current_index}, kelgan {question_index}."
            )

        question = self.current_question
        answer = SubmittedAnswer(
            question_index=question.index,
            selected_option=option,
            is_correct=(option == question.correct_option),
        )
        self.answers.append(answer)
        self.current_index += 1
        if self.is_finished:
            self.status = TestStatus.COMPLETED
        return answer
