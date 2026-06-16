"""✏️ Mashq — mavzu tanlash, masala tuzish, javobni tekshirish (FSM)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from leti_math_mentor.keyboards import BTN_PRACTICE, topics_keyboard
from leti_math_mentor.services.claude import ClaudeService
from leti_math_mentor.services.db import Database

router = Router(name="practice")


class Practice(StatesGroup):
    waiting_answer = State()


@router.message(F.text == BTN_PRACTICE)
async def choose_topic(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Qaysi mavzuda mashq qilamiz? 👇", reply_markup=topics_keyboard())


@router.callback_query(F.data.startswith("practice_topic:"))
async def make_problem(
    call: CallbackQuery, state: FSMContext, db: Database, claude: ClaudeService
) -> None:
    await call.answer()  # darhol — "query too old" bo'lmasligi uchun
    topic = call.data.split(":", 1)[1]
    level = await db.get_level_for_topic(call.from_user.id, topic)

    await call.message.bot.send_chat_action(call.message.chat.id, "typing")
    problem = await claude.generate_practice(topic, level)

    await state.set_state(Practice.waiting_answer)
    await state.update_data(topic=topic, level=level, problem=problem)
    await call.message.answer(
        f"✏️ <b>Mashq</b> (mavzu: {topic}, daraja: {level})\n\n{problem}\n\n"
        "Javobingni yoz — tekshiraman. Yechib bo'lmasa “/reset” bilan to'xtatishing mumkin."
    )


@router.message(Practice.waiting_answer)
async def check(
    message: Message, state: FSMContext, db: Database, claude: ClaudeService
) -> None:
    data = await state.get_data()
    problem = data.get("problem", "")
    topic = data.get("topic")

    await message.bot.send_chat_action(message.chat.id, "typing")
    is_correct, feedback = await claude.check_answer(problem, message.text or "")
    await db.log_interaction(message.from_user.id, "practice", topic=topic, is_correct=is_correct)

    mark = "✅ To'g'ri!" if is_correct else "❌ Hali to'g'ri emas."
    await message.answer(f"{mark}\n\n{feedback}")

    if is_correct:
        await state.clear()
        await message.answer("Yana mashq qilasanmi? “✏️ Mashq” tugmasini bos.")
    # xato bo'lsa state'da qolamiz — o'quvchi qayta urinishi mumkin
