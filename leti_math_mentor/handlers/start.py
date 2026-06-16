"""/start, /help — ro'yxatdan o'tkazish va yordam."""
from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from leti_math_mentor.keyboards import main_menu
from leti_math_mentor.services.db import Database

router = Router(name="start")

WELCOME = (
    "Assalomu alaykum, {name}! 👋\n\n"
    "Men <b>LETI EDU matematika mentoriman</b>. Men senga tayyor javob bermayman — "
    "savol va kichik maslahatlar bilan yo'naltiraman, javobni o'zing topasan. Shunda "
    "haqiqatan o'rganasan. 💪\n\n"
    "Nima qila olaman:\n"
    "📚 <b>Savol berish</b> — masalani matn yoki rasm qilib yubor, birga yechamiz\n"
    "✏️ <b>Mashq</b> — mavzu tanla, men masala beraman, sen yechasan\n"
    "📊 <b>Progress</b> — qaysi mavzularda kuchli/kuchsizsan ko'rsataman\n\n"
    "Quyidagi menyudan boshla yoki shunchaki savolingni yoz."
)

HELP = (
    "<b>Qanday foydalanish kerak:</b>\n\n"
    "📚 <b>Savol berish</b> — matematik masala yoki nazariy savolingni yoz. Rasm ham "
    "yuborishing mumkin (daftar/kitobdagi masala). Men qadam-baqadam yo'naltiraman.\n\n"
    "✏️ <b>Mashq</b> — mavzu tanlaysan, men masala tuzaman. Javobingni yozasan, tekshiraman.\n\n"
    "📊 <b>Progress</b> — natijalaringni mavzular bo'yicha ko'rsataman.\n\n"
    "<b>Buyruqlar:</b>\n"
    "/start — boshlash\n"
    "/help — yordam\n"
    "/reset — joriy suhbatni unutish (yangi mavzu boshlash)\n\n"
    "<i>Eslatma: men ataylab to'liq yechimni darrov bermayman — o'zing o'ylab topishing "
    "uchun. Bu seni kuchli qiladi.</i>"
)


@router.message(CommandStart())
async def cmd_start(message: Message, db: Database) -> None:
    user = message.from_user
    await db.ensure_user(user.id, user.username, user.full_name, force=True)
    await message.answer(
        WELCOME.format(name=user.first_name or "o'quvchi"),
        reply_markup=main_menu,
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP, reply_markup=main_menu)


@router.message(Command("reset"))
async def cmd_reset(message: Message, memory) -> None:
    await memory.reset(message.from_user.id)
    await message.answer("✅ Suhbat tozalandi. Yangi savol yoki mavzu bilan boshlasak bo'ladi.")
