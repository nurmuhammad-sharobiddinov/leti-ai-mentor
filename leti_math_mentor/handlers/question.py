"""📚 Savol-javob — Sokratik yo'naltirish (matn + rasm/vision).

DIQQAT: bu router bot.py da OXIRGI ulanadi — u barcha qolgan matnni ushlaydi (fallback).
"""
from __future__ import annotations

import base64
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from leti_math_mentor.keyboards import BTN_QUESTION
from leti_math_mentor.services.claude import ClaudeService
from leti_math_mentor.services.db import Database
from leti_math_mentor.services.memory import ConversationMemory

logger = logging.getLogger(__name__)

router = Router(name="question")

ASK_PROMPT = (
    "📚 Mayli! Matematik masalangni yoki savolingni yoz. Daftar/kitobdagi masalani "
    "rasmga olib ham yuborishing mumkin.\n\n"
    "<i>Eslatma: men darrov javob bermayman — birga qadam-baqadam yechamiz.</i>"
)


@router.message(F.text == BTN_QUESTION)
async def ask_hint(message: Message) -> None:
    await message.answer(ASK_PROMPT)


@router.message(F.photo)
async def on_photo(
    message: Message,
    db: Database,
    claude: ClaudeService,
    memory: ConversationMemory,
) -> None:
    """Rasm = Claude vision. Eng katta o'lchamdagi rasmni yuklab base64 qilamiz."""
    await db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.bot.send_chat_action(message.chat.id, "typing")

    photo = message.photo[-1]  # eng katta o'lcham
    buf = await message.bot.download(photo.file_id)
    image_b64 = base64.b64encode(buf.read()).decode("ascii")
    caption = message.caption or ""

    history = await memory.get_history(message.from_user.id)
    answer, topic = await claude.ask_mentor(history, caption, image_b64=image_b64)

    # rasm tarixga yozilmaydi — faqat matnli xulosa
    await memory.add_turn(message.from_user.id, "user", caption or "[rasm: masala yubordi]")
    await memory.add_turn(message.from_user.id, "assistant", answer)
    await db.log_interaction(message.from_user.id, "question", topic=topic)

    await message.answer(answer)


@router.message(F.text)
async def on_text(
    message: Message,
    state: FSMContext,
    db: Database,
    claude: ClaudeService,
    memory: ConversationMemory,
) -> None:
    """Har qanday erkin matn — Sokratik savol-javob (fallback)."""
    await db.ensure_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.bot.send_chat_action(message.chat.id, "typing")

    history = await memory.get_history(message.from_user.id)
    answer, topic = await claude.ask_mentor(history, message.text)

    await memory.add_turn(message.from_user.id, "user", message.text)
    await memory.add_turn(message.from_user.id, "assistant", answer)
    await db.log_interaction(message.from_user.id, "question", topic=topic)

    await _send_long(message, answer)


async def _send_long(message: Message, text: str, limit: int = 4000) -> None:
    """Uzun javoblarni Telegram limiti (4096) bo'yicha bo'lib yuborish."""
    if len(text) <= limit:
        await message.answer(text)
        return
    # bo'sh qatordan (paragraf) bo'yicha bo'lishga harakat qilamiz
    chunk = ""
    for para in text.split("\n\n"):
        if len(chunk) + len(para) + 2 > limit:
            if chunk:
                await message.answer(chunk.strip())
            chunk = para
        else:
            chunk = f"{chunk}\n\n{para}" if chunk else para
    if chunk.strip():
        await message.answer(chunk.strip())


@router.message()
async def on_other(message: Message) -> None:
    """Ovoz, stiker, fayl va h.k. — qo'llab-quvvatlanmaydigan turlar (eng oxirgi fallback)."""
    await message.answer(
        "Hozircha men faqat <b>matn</b> va <b>rasm</b>ni tushunaman. 🙂\n"
        "Masalangni yozib yubor yoki daftaringdagi masalani rasmga olib jo'nat."
    )
