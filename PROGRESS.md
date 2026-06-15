# Loyiha holati va ish jurnali (PROGRESS)

> Bu fayl — sessiyalar orasidagi "handoff". Har kuni davom etishdan oldin shuni o'qing.
> Oxirgi yangilanish: 2026-06-10.

---

## ✅ Bajarilgan ishlar

### Faza 1 — Asosiy bot (Clean Architecture skeleti)
n8n workflow (`../Lux_Leti_AI_Mentor.json`) Python'ga ko'chirildi.

- **Domain**: `Student`, `TestSession`, `Question`, `Message` entity'lari; enum/exception'lar;
  Repository va Service port'lari (interfeyslar).
- **Application**: use case'lar — `ExplainTopic`, `ReexplainTopic`, `StartTest`,
  `SubmitAnswer`, `RegisterStudent`; DTO'lar.
- **Infrastructure**: Postgres repozitoriylari (asyncpg), Anthropic LLM adapterlari
  (tool-use bilan strukturali chiqish), `pydantic-settings`, DI `Container`.
- **Presentation**: aiogram router'lari (commands, explanation, test), klaviaturalar,
  callback'lar, o'quvchini ro'yxatga oluvchi middleware.
- Oqim: mavzu → tushuntirish + 2 tugma → 5 savol test → har javob **domenda
  deterministik** tekshiriladi → oxirida AI tahlil.

### Faza 2 — Qo'shimcha imkoniyatlar
1. **Webhook rejimi** — `BOT_MODE=polling|webhook` (`webhook.py`, `main.py`).
2. **Admin statistika** — `/stats` (`IsAdmin` filtri, `StatisticsRepository`).
3. **Spaced-repetition** — Leitner (1,3,7,16,35 kun); `review_items` jadvali;
   fon `ReviewScheduler` eslatma yuboradi; `/review` buyrug'i;
   `domain/services/spaced_repetition.py`.
4. **LLM retry/rate-limit** — `AsyncRetrier` + `Throttler` (`llm/resilience.py`).

### Faza 3 — `/me` o'quvchining shaxsiy statistikasi (2026-06-09)
O'quvchi `/me` yuborganda o'zining holatini ko'radi: ism, daraja, ishlangan testlar
soni, o'rtacha natija (%), takrorlash kutayotgan mavzular soni, o'zlashtirgan va
zaif mavzular ro'yxati. Mavjud arxitekturaga to'liq mos qo'shildi:
- **Domain**: `entities/statistics.py` → `StudentStats` read-model qo'shildi.
- **Port**: `StatisticsRepository.collect_for_student(chat_id) -> StudentStats | None`.
- **Application**: `use_cases/get_my_stats.py` → `GetMyStatsUseCase`.
- **Infrastructure**: `PgStatisticsRepository.collect_for_student` — `students` +
  `test_sessions` (completed, avg score) + `review_items` (due_at <= now()) SQL.
- **Presentation**: `routers/commands.py` ga `/me` handler; `formatters.py` ga
  `format_student_profile`; `/start` matniga `/me` qo'shildi.
- **DI**: `container.get_my_stats`.
- **Test**: `tests/test_student_profile_format.py` — 2 ta formatlash testi.

### Faza 4 — Test oqimi xato tuzatish + barqarorlik (2026-06-10)
**Muammo:** oxirgi (5-) savoldan keyin yakuniy xulosa ko'rsatilmas, "Faol test
topilmadi" deb chiqardi. **Asl sabab:** `on_answer` da `query.answer()` sekin AI
tahlilidan KEYIN va `try/except` dan TASHQARIDA chaqirilgan → callback eskirib
("query is too old") handler yiqilardi; sessiya esa `completed` bo'lib qolardi.
- **Presentation** (`routers/test.py`): callback DARHOL `query.answer()` bilan
  tasdiqlanadi; `edit_reply_markup` va `send_chat_action` (typing) `TelegramBadRequest`
  dan himoyalangan; barcha javoblar `message.answer` orqali (eskirmaydi).
- **Application** (`use_cases/submit_answer.py`): yakuniy AI tahlili endi
  "best-effort" — xato/sekin bo'lsa ham deterministik natija + `_fallback_summary`
  qaytadi, sessiya hech qachon bloklanmaydi. Profil/review yangilash ham shu blokda.
- **Infra eslatma:** bot IKKI nusxada polling qilayotgani aniqlandi (409 konflikt) —
  bittasi qoldirildi. Bir vaqtda faqat BITTA `main.py` ishlasin.
- **Test:** `tests/test_submit_answer.py` — AI yiqilsa ham natija qaytishini tekshiradi.

### Faza 5 — "Kutib turing" UX (2026-06-10)
Sekin LLM chaqiruvlari paytida vaqtinchalik "⏳/✍️ tayyorlanmoqda" xabari
ko'rsatiladi va natija kelishidan OLDIN o'chiriladi (foydalanuvchi avval
"tayyorlanmoqda"ni, so'ng faqat natijani ko'radi).
- `utils.py` ga `status_message(message, text)` — `@asynccontextmanager`
  (xabar yuboradi, blok tugashi/xato bo'lishi bilan `finally` da o'chiradi).
- Qo'llangan joylar: tushuntirish (`on_topic`), qayta tushuntirish, test
  tayyorlash (`on_start_test`), javob tekshirish (`on_answer`), takrorlash
  (`on_start_review`). Barcha callback handlerlar endi DARHOL `query.answer()`
  bilan tasdiqlaydi (callback eskirmasligi uchun).

### Faza 6 — Boy yakuniy natija kartasi (2026-06-10)
Test oxiridagi oddiy "Natija: X/Y" o'rniga statistik, vizual karta:
- **DTO** (`dto.py`): `TestResultView` — topic, score/total/%, oddiy/mantiqiy
  bo'yicha to'g'ri/jami, har bir savol natijasi (`answers_correct`), AI'dan
  weak/mastered topiclar, summary. `final_summary` o'rniga `AnswerFeedback.final_result`.
- **Application** (`submit_answer.py`): `_build_result` deterministik statistikani
  sessiyadan yig'adi (savol turi bo'yicha QuestionKind orqali).
- **Presentation** (`formatters.py`): `format_test_result` — progress-bar (▰▱),
  baho yorlig'i (🏆/👍/🙂/📚), ✅/❌ javoblar chizig'i, kuchli/zaif mavzular,
  AI xulosa, /review va /me yo'naltmalari. Plain-text (HTML emas — LLM matni xavfsiz).
- **Test:** `tests/test_test_result_format.py` (2 ta). Jami **15/15**.

### Tekshiruv holati (hammasi yashil)
- `compileall` — sintaksis toza
- DI wiring — 5 router, barcha use case quriladi
- `pytest` — **13/13** (domen + spaced-repetition + /me + submit_answer robustlik)
- `ruff check` (F/B/ASYNC) — muammosiz
- Eslatma: `ruff` to'liq config (UP tanlangan) `enums.py` da 4 ta UP042 beradi
  (`class X(str, Enum)` → `StrEnum` taklifi) — bu **eski**, `/me` ga aloqasi yo'q.
  `StrEnum` ga ko'chirish `str()` xulqini o'zgartiradi (regress xavfi), shuning uchun
  ataylab tegilmadi.

---

## 📌 Keyingi ishlar (ertaga)

### Navbatdagilar (rejada, shoshilinch emas)
- Bir nechta fan/daraja (level) bo'yicha tarmoqlash.
- Webhook uchun Docker + reverse-proxy namunasi.
- O'quvchi javob vaqtini (response time) statistikaga qo'shish.

---

## 🚀 Davom etish uchun eslatma

```powershell
# Loyiha papkasi
cd D:\LUMEN\Coding\AI-Mentor-n8n\lux-leti-ai-mentor

# Muhit (venv allaqachon yaratilgan: .venv)
.\.venv\Scripts\Activate.ps1

# Testlar
.\.venv\Scripts\python.exe -m pytest -q

# Lint
.\.venv\Scripts\python.exe -m ruff check src main.py tests

# Ishga tushirish (avval .env to'ldirilishi shart)
py main.py
```

**Diqqat:**
- `python` PATH'da yo'q — `py` yoki `.venv\Scripts\python.exe` ishlating.
- `.env` to'ldirilishi shart: `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`,
  `DATABASE_URL` (PostgreSQL kerak). Admin uchun `ADMIN_IDS`.
- Arxitektura qoidasi: yangi imkoniyat har doim **to'g'ri qatlamga** —
  domen mantig'i `domain/`, IO `infrastructure/`, ssenariy `application/use_cases/`,
  Telegram `presentation/`. Port orqali ulang (DI `container.py`).
- Batafsil arxitektura: `README.md`.
