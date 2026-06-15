"""Matn formatlovchilar — DTO'larni o'quvchiga ko'rinadigan matnga aylantiradi."""
from __future__ import annotations

from ...application.dto import AnswerFeedback, QuestionView, TestResultView
from ...domain.entities import Statistics, StudentStats


def format_question(question: QuestionView) -> str:
    return f"❓ Savol {question.number}/{question.total}\n\n{question.text}"


def format_answer_feedback(feedback: AnswerFeedback) -> str:
    """Javobdan keyingi izoh matni (keyingi savoldan oldin yuboriladi)."""
    head = "✅ To'g'ri!" if feedback.is_correct else "❌ Noto'g'ri."
    parts = [head]
    if not feedback.is_correct:
        parts.append(f"To'g'ri javob: {feedback.correct_option}")
    if feedback.explanation:
        parts.append(f"\n💡 {feedback.explanation}")
    return "\n".join(parts)


def _progress_bar(pct: int, width: int = 10) -> str:
    """Foizni vizual progress-bar ko'rinishida qaytaradi (▰▰▰▱▱)."""
    filled = round(pct / 100 * width)
    filled = max(0, min(width, filled))
    return "▰" * filled + "▱" * (width - filled)


def _grade_label(pct: int) -> str:
    if pct >= 80:
        return "🏆 A'lo"
    if pct >= 60:
        return "👍 Yaxshi"
    if pct >= 40:
        return "🙂 O'rta"
    return "📚 Mashq kerak"


def format_test_result(result: TestResultView) -> str:
    """Test yakunidagi boy, statistik natija kartasi."""
    pct = result.percentage
    strip = " ".join("✅" if ok else "❌" for ok in result.answers_correct)

    lines = [
        "🏁 Test yakunlandi!",
        "━━━━━━━━━━━━━━━",
        f"📚 Mavzu: {result.topic}",
        f"🎯 Natija: {result.score}/{result.total} ({pct}%)",
        f"{_progress_bar(pct)} {pct}%",
        f"📈 Baho: {_grade_label(pct)}",
        "",
        "📊 Savollar bo'yicha:",
        f"   • Oddiy:    {result.simple_correct}/{result.simple_total}",
        f"   • Mantiqiy: {result.logical_correct}/{result.logical_total}",
        f"   • Javoblar: {strip}",
    ]

    if result.mastered_topics:
        lines.append("")
        lines.append("💪 Kuchli tomonlaringiz:")
        lines.extend(f"   • {t}" for t in result.mastered_topics)

    if result.weak_topics:
        lines.append("")
        lines.append("📉 Takrorlash kerak:")
        lines.extend(f"   • {t}" for t in result.weak_topics)

    if result.summary.strip():
        lines.append("")
        lines.append("📝 Xulosa:")
        lines.append(result.summary.strip())

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append("🔁 Takrorlash: /review   •   📊 Statistika: /me")
    return "\n".join(lines)


def format_statistics(stats: Statistics) -> str:
    """Admin statistikasi matni."""
    lines = [
        "📊 Statistika",
        "",
        f"👥 Jami o'quvchilar: {stats.total_students}",
        f"🟢 Bugun faol: {stats.active_today}",
        f"📝 Yakunlangan testlar: {stats.completed_tests}",
        f"🎯 O'rtacha natija: {stats.average_score_pct}%",
    ]
    if stats.top_weak_topics:
        lines.append("")
        lines.append("🔻 Eng ko'p zaif mavzular:")
        for i, tc in enumerate(stats.top_weak_topics, start=1):
            lines.append(f"  {i}. {tc.topic} — {tc.count} ta")
    return "\n".join(lines)


def format_student_profile(stats: StudentStats) -> str:
    """O'quvchining shaxsiy statistikasi matni (/me)."""
    lines = [
        f"👤 {stats.full_name}",
        f"📈 Daraja: {stats.level}",
        "",
        f"📝 Ishlangan testlar: {stats.completed_tests}",
        f"🎯 O'rtacha natija: {stats.average_score_pct}%",
        f"🔁 Takrorlash kutayotgan mavzular: {stats.due_reviews}",
    ]

    lines.append("")
    if stats.mastered_topics:
        lines.append("✅ O'zlashtirgan mavzular:")
        for topic in stats.mastered_topics:
            lines.append(f"  • {topic}")
    else:
        lines.append("✅ O'zlashtirgan mavzular: hali yo'q")

    lines.append("")
    if stats.weak_topics:
        lines.append("⚠️ Zaif mavzular:")
        for topic in stats.weak_topics:
            lines.append(f"  • {topic}")
    else:
        lines.append("⚠️ Zaif mavzular: yo'q — ofarin! 🎉")

    return "\n".join(lines)

