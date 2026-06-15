"""Test javobini tekshirish use case'i (n8n: "Tekshirish_Prompt" + "AI Agent1").

Asosiy farq: javob to'g'riligi domenda (deterministik) aniqlanadi,
LLM faqat yakuniy tahlil uchun ishlatiladi.
"""
from __future__ import annotations

import logging

from ...domain.entities import AnalysisResult, TestSession
from ...domain.enums import QuestionKind
from ...domain.exceptions import TestSessionNotFoundError
from ...domain.ports import (
    Clock,
    PerformanceAnalyst,
    ReviewRepository,
    StudentRepository,
    TestSessionRepository,
)
from ...domain.services import SpacedRepetitionPolicy
from ..dto import AnswerFeedback, QuestionView, TestResultView

logger = logging.getLogger(__name__)


class SubmitAnswerUseCase:
    def __init__(
        self,
        students: StudentRepository,
        sessions: TestSessionRepository,
        analyst: PerformanceAnalyst,
        reviews: ReviewRepository,
        policy: SpacedRepetitionPolicy,
        clock: Clock,
    ) -> None:
        self._students = students
        self._sessions = sessions
        self._analyst = analyst
        self._reviews = reviews
        self._policy = policy
        self._clock = clock

    async def execute(
        self,
        chat_id: int,
        question_index: int,
        option: str,
    ) -> AnswerFeedback:
        session = await self._sessions.get_active(chat_id)
        if session is None:
            raise TestSessionNotFoundError("Faol test sessiyasi topilmadi.")

        answered = session.current_question  # joriy savol (izoh uchun)
        answer = session.submit(question_index, option)  # InvalidAnswerError mumkin

        if not session.is_finished:
            await self._sessions.save(session)
            nxt = session.current_question
            return AnswerFeedback(
                is_correct=answer.is_correct,
                correct_option=answered.correct_option,
                explanation=answered.explanation,
                score=session.score,
                total=session.total,
                next_question=QuestionView(
                    index=nxt.index,
                    text=nxt.text,
                    options=nxt.options,
                    number=session.current_index + 1,
                    total=session.total,
                ),
            )

        # Test yakunlandi. Avval deterministik natijani saqlaymiz — bu qadam
        # hech qachon LLM'ga bog'liq emas, shuning uchun har doim muvaffaqiyatli.
        await self._sessions.save(session)

        # AI tahlili "best-effort": u sekin ishlasa yoki xato bersa ham,
        # o'quvchi natijasini va deterministik xulosani ko'radi. Tahlil
        # sessiyani bloklamaydi (avvalgi xato shu yerda edi).
        summary = self._fallback_summary(session)
        weak_topics: list[str] = []
        mastered_topics: list[str] = []
        try:
            analysis = await self._analyst.analyze(
                topic=session.topic,
                score=session.score,
                total=session.total,
                transcript=self._build_transcript(session),
            )
            if analysis.summary.strip():
                summary = analysis.summary
            weak_topics = analysis.weak_topics
            mastered_topics = analysis.mastered_topics
            await self._update_profile(chat_id, analysis)
            await self._schedule_reviews(chat_id, analysis)
        except Exception:  # noqa: BLE001 — tahlil ixtiyoriy; natija baribir ko'rsatiladi
            logger.warning(
                "Test yakuniy AI tahlili bajarilmadi; deterministik xulosa ko'rsatiladi.",
                exc_info=True,
            )

        return AnswerFeedback(
            is_correct=answer.is_correct,
            correct_option=answered.correct_option,
            explanation=answered.explanation,
            score=session.score,
            total=session.total,
            final_result=self._build_result(
                session, summary, weak_topics, mastered_topics
            ),
        )

    @staticmethod
    def _build_result(
        session: TestSession,
        summary: str,
        weak_topics: list[str],
        mastered_topics: list[str],
    ) -> TestResultView:
        """Sessiyadan deterministik statistikani yig'ib, boy natija ko'rinishini quradi."""
        by_index = {a.question_index: a for a in session.answers}
        answers_correct: list[bool] = []
        simple_correct = simple_total = logical_correct = logical_total = 0
        for q in session.questions:
            ans = by_index.get(q.index)
            correct = bool(ans and ans.is_correct)
            answers_correct.append(correct)
            if q.kind is QuestionKind.SIMPLE:
                simple_total += 1
                simple_correct += int(correct)
            else:
                logical_total += 1
                logical_correct += int(correct)
        return TestResultView(
            topic=session.topic,
            score=session.score,
            total=session.total,
            simple_correct=simple_correct,
            simple_total=simple_total,
            logical_correct=logical_correct,
            logical_total=logical_total,
            answers_correct=answers_correct,
            summary=summary,
            weak_topics=list(weak_topics),
            mastered_topics=list(mastered_topics),
        )

    async def _update_profile(self, chat_id: int, analysis: AnalysisResult) -> None:
        """Tahlil natijasiga ko'ra o'quvchining zaif/o'zlashtirilgan mavzularini yangilash."""
        student = await self._students.get(chat_id)
        if student is None:
            return
        for topic in analysis.weak_topics:
            student.record_weakness(topic)
        for topic in analysis.mastered_topics:
            student.record_mastery(topic)
        await self._students.save(student)

    @staticmethod
    def _fallback_summary(session: TestSession) -> str:
        """AI tahlili mavjud bo'lmaganda ko'rsatiladigan deterministik rag'bat matni."""
        pct = round(session.score / session.total * 100) if session.total else 0
        if pct >= 80:
            return "Ajoyib natija! Mavzuni yaxshi o'zlashtirgansiz. 👏"
        if pct >= 50:
            return "Yaxshi! Ba'zi joylarni takrorlasangiz, bilimingiz mustahkamlanadi."
        return (
            "Bu mavzuni qayta ko'rib chiqish foydali bo'ladi. "
            "Shoshilmang — /review yordam beradi! 💪"
        )

    async def _schedule_reviews(self, chat_id: int, analysis: AnalysisResult) -> None:
        """Tahlil natijasiga ko'ra spaced-repetition jadvalini yangilash."""
        now = self._clock.now()
        for topic in analysis.weak_topics:
            existing = await self._reviews.get_by_topic(chat_id, topic)
            item = self._policy.on_weak(existing, chat_id, topic, now)
            await self._reviews.upsert(item)
        for topic in analysis.mastered_topics:
            existing = await self._reviews.get_by_topic(chat_id, topic)
            if existing is None:
                continue
            updated = self._policy.on_mastered(existing, now)
            if updated is None:
                await self._reviews.delete(existing.id)
            else:
                await self._reviews.upsert(updated)

    @staticmethod
    def _build_transcript(session) -> str:
        """Tahlil uchun savol-javob bayonnomasini tuzish."""
        lines: list[str] = [f"Mavzu: {session.topic}", ""]
        for q in session.questions:
            ans = next(
                (a for a in session.answers if a.question_index == q.index), None
            )
            chosen = ans.selected_option if ans else "—"
            mark = "to'g'ri" if (ans and ans.is_correct) else "noto'g'ri"
            lines.append(
                f"Savol {q.index + 1} ({q.kind.value}): {q.text}\n"
                f"  Tanlangan: {chosen} | To'g'ri javob: {q.correct_option} | {mark}"
            )
        return "\n".join(lines)
