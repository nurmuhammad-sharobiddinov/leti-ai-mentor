# Lux Leti AI Mentor 🧮

Leti maktabining AI matematika mentori — Telegram bot. n8n'dagi sodda
workflow'ning **Clean Architecture** asosidagi Python qayta qurilishi.

## Bot oqimi (n8n bilan bir xil mantiq)

1. O'quvchi tushunmagan matematik mavzusini yozadi.
2. **Mentor** (Claude Opus) mavzuni sodda tushuntiradi + 2 tugma chiqaradi:
   - 🔄 **Qayta tushuntirish** — boshqacha misollar bilan qayta izohlaydi.
   - ✅ **Tushundim, testni boshlash** — testga o'tadi.
3. **Test**: 5 ta savol (2 oddiy + 3 mantiqiy), bittadan, 4 variantli.
4. Har bir javob **domenda deterministik** tekshiriladi (LLM emas).
5. Test oxirida **AI tahlilchi** natijani tahlil qiladi, zaif/kuchli
   mavzular o'quvchi profiliga yoziladi.

## Arxitektura (qatlamlar)

```
src/
├── domain/            # Eng ichki — hech narsaga bog'liq emas
│   ├── entities/      #   Student, TestSession, Question, Message ...
│   ├── enums.py       #   Role, TestStatus, QuestionKind, AnswerOption
│   ├── exceptions.py  #   Domen xatoliklari
│   └── ports/         #   Interfeyslar (Repository / Service portlari)
├── application/       # Use case'lar — biznes ssenariylari
│   ├── dto.py         #   Qatlamlararo ma'lumot obyektlari
│   └── use_cases/     #   ExplainTopic, StartTest, SubmitAnswer ...
├── infrastructure/    # Tashqi dunyo realizatsiyalari
│   ├── config/        #   pydantic-settings
│   ├── persistence/   #   asyncpg repozitoriylari + schema.sql
│   ├── llm/           #   Anthropic adapterlari + promptlar
│   └── container.py   #   DI konteyner (Composition Root)
└── presentation/      # Telegram (aiogram)
    └── telegram/      #   router'lar, klaviaturalar, callback'lar, middleware
```

**Bog'liqlik yo'nalishi** har doim ichkariga: `presentation → application →
domain`, `infrastructure → domain`. Domen hech kimga bog'liq emas.

### Qo'llanilgan pattern va tamoyillar

- **Clean / Hexagonal Architecture** — portlar va adapterlar.
- **Dependency Inversion (SOLID-D)** — domen interfeyslarga bog'lanadi,
  konkret Postgres/Anthropic'ga emas.
- **Repository pattern** — ma'lumotlarga kirish abstraksiyasi.
- **Use Case (Interactor)** — har bir ssenariy alohida, bitta mas'uliyat (SRP).
- **DTO** — qatlamlar orasida toza shartnoma.
- **Factory** — klaviatura va router quruvchilari.
- **Middleware** — ko'ndalang mas'uliyat (o'quvchini ro'yxatga olish).
- **Strategy** — bir nechta AI xizmati bir portning turli realizatsiyasi.

### n8n'ga nisbatan yaxshilanishlar

- Test holati (savol raqami, ball) endi **LLM xotirasida emas**, balki
  `TestSession` entity'sida — ishonchli va testlanadigan.
- Javob to'g'riligi **kod tomonidan** aniqlanadi, AI'ning xato baholashiga
  bog'liq emas.
- LLM strukturali chiqishi **tool-use** orqali (mo'rt `​```json` parse o'rniga).
- Type-safe callback_data (`ans_A` literallar o'rniga).

## Ishga tushirish

```powershell
# 1. Virtual muhit
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Kutubxonalar
pip install -r requirements.txt

# 3. Konfiguratsiya
copy .env.example .env   # va .env ichini to'ldiring (token, api key, DB)

# 4. Ishga tushirish (schema avtomatik yaratiladi)
py main.py
```

PostgreSQL kerak. `AUTO_MIGRATE=true` bo'lsa, jadval sxemasi ishga tushganda
avtomatik yaratiladi (`src/infrastructure/persistence/schema.sql`).

## Testlar

```powershell
pip install -e ".[dev]"
pytest
```

Domen testlari DB yoki API talab qilmaydi.

## Qo'shimcha imkoniyatlar

### 1. Webhook rejimi
`.env` da `BOT_MODE=webhook` qiling va to'ldiring:
```
BOT_MODE=webhook
WEBHOOK_BASE_URL=https://sizning-domeningiz.uz
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=maxfiy-token
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8080
```
`py main.py` aiohttp serverini ko'taradi va webhook'ni Telegram'da o'rnatadi.
`polling` rejimi (default) hech qanday domen/HTTPS talab qilmaydi — lokal test uchun.

### 2. Admin statistika
`.env` da `ADMIN_IDS=123456789,987654321` (vergul bilan chat_id'lar). Admin
botda `/stats` yuborsa: jami o'quvchilar, bugun faollar, yakunlangan testlar,
o'rtacha natija (%), eng ko'p zaif mavzular ko'rsatiladi. Boshqalar uchun
buyruq ko'rinmaydi (`IsAdmin` filtri).

### 3. Spaced-repetition (takrorlash)
Test yakunidagi zaif mavzular Leitner tizimi bo'yicha jadvalga yoziladi
(oraliqlar: 1, 3, 7, 16, 35 kun). Vaqti kelganda bot avtomatik eslatma yuboradi
("🔁 Takrorlashni boshlash" tugmasi bilan). O'quvchi `/review` orqali ham
takrorlanadigan mavzularni ko'ra oladi. To'g'ri takror — mavzuni yuqori qutiga
ko'taradi; eng yuqoridan o'tsa "bitiriladi". Mantiq `domain/services/
spaced_repetition.py` da (sof, testlangan). Fon vazifasi:
`presentation/telegram/scheduler.py`.
```
REVIEW_ENABLED=true
REVIEW_POLL_INTERVAL_SECONDS=3600     # qancha tez-tez tekshirish
REVIEW_NOTIFY_COOLDOWN_HOURS=20       # bir eslatmadan keyingi tanaffus
```

### 4. LLM retry / rate-limit
Har bir Anthropic chaqiruvi `AsyncRetrier` (vaqtinchalik xatolarda eksponensial
backoff + jitter) va `Throttler` (bir vaqtdagi chaqiruvlar soni cheklovi) bilan
o'ralgan — `infrastructure/llm/resilience.py`.
```
LLM_MAX_RETRIES=3
LLM_RETRY_BASE_DELAY=1.0
LLM_MAX_CONCURRENCY=4
```

## Keyingi qadamlar (rejada)

- O'quvchi shaxsiy statistikasi (`/me`).
- Bir nechta fan/daraja (level) bo'yicha tarmoqlash.
- Webhook uchun Docker + reverse-proxy namunasi.
