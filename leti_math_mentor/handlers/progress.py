"""📊 Progress — mavzular bo'yicha natijalar."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from leti_math_mentor.keyboards import BTN_PROGRESS
from leti_math_mentor.services.db import Database

router = Router(name="progress")


def _bar(pct: int) -> str:
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)


@router.message(F.text == BTN_PROGRESS)
async def show_progress(message: Message, db: Database) -> None:
    rows = await db.get_progress(message.from_user.id)
    if not rows:
        await message.answer(
            "📊 Hali natija yo'q.\n\nBir nechta savol bering yoki mashq qiling — "
            "keyin bu yerda kuchli/kuchsiz mavzularingni ko'rsataman."
        )
        return

    lines = ["📊 <b>Sening progressing</b>\n"]
    weak: list[str] = []
    for r in rows:
        topic = r["topic"]
        graded = r["graded"] or 0
        correct = r["correct"] or 0
        total = r["total"] or 0
        if graded > 0:
            pct = round(correct / graded * 100)
            lines.append(f"<b>{topic}</b>  {_bar(pct)} {pct}%  ({correct}/{graded})")
            if pct < 50:
                weak.append(topic)
        else:
            # faqat savol-javob bo'lgan mavzu (baholanmagan)
            lines.append(f"<b>{topic}</b>  — {total} ta muloqot")

    if weak:
        lines.append("\n⚠️ <b>Ko'proq mashq kerak:</b> " + ", ".join(weak))
        lines.append("Bu mavzularda “✏️ Mashq” qil — men darajangga moslab masala beraman.")
    else:
        lines.append("\n✅ Yaxshi ketyapsan! Davom et. 💪")

    await message.answer("\n".join(lines))
