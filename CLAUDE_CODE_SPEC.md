# Texnik Topshiriq — LETI EDU Matematika Mentor Bot

> Bu hujjat Claude Code uchun. Botning maqsadi, qanday ishlashi, hozirgi holati va
> qilinishi kerak bo'lgan ishlar shu yerda. Mavjud kod ustiga qurib davom ettiriladi.

---

## 1. Loyiha haqida

LETI EDU — o'zbek ta'lim platformasi (letischool.uz). Bu bot — platformaning
**Telegramdagi matematika mentori**. Vazifasi: o'quvchilarga tushunmagan matematik
mavzu/masalalarini o'rganishda yordam berish.

**Eng muhim tamoyil — bot tayyor javobni BERMAYDI.** U Sokratik uslubda ishlaydi:
o'quvchini savol va kichik maslahatlar bilan yo'naltiradi, javobni o'quvchi o'zi
topishiga harakat qiladi. Aks holda bot "ko'chirish mashinasi"ga aylanadi va o'quvchi
hech narsa o'rganmaydi. Bu butun loyihaning asosiy qarori — uni buzmang.

Til: o'zbek (lotin). Kod va texnik atamalar — inglizcha.

---

## 2. Bot qanday ishlashi kerak

### Funksiya 1 — Savol-javob (📚)
- O'quvchi matn yoki rasm (daftardagi/kitobdagi masala) yuboradi.
- Bot Claude orqali bosqichma-bosqich yo'naltiradi: avval "birinchi qadam nima?" deb
  so'raydi yoki hint beradi; o'quvchi javob bersa — to'g'ri/xato ekanini aytib,
  keyingi qadamga o'tkazadi.
- Agar savol nazariy bo'lsa ("hosila nima?") — to'liq tushuntiradi.
- Suhbat konteksti saqlanadi (davom-savollar ishlashi uchun, masalan "yana misol ber").
- Rasm uchun alohida OCR shart EMAS — Claude rasmni o'zi o'qiydi (vision).

### Funksiya 2 — Mashq (✏️)
- O'quvchi mavzu tanlaydi (inline tugmalar).
- Claude o'sha mavzuda bitta masala tuzadi (javobsiz).
- O'quvchi javobini yozadi → Claude tekshiradi → to'g'ri/xato natija bazaga yoziladi.
- Xato bo'lsa qayerda adashganini aytadi, lekin to'liq yechimni bermaydi.

### Funksiya 3 — Progress (📊)
- `interactions` jadvalidan har bir mavzu bo'yicha to'g'ri/jami hisoblanadi.
- O'quvchiga foiz va kuchsiz mavzular ro'yxati ko'rsatiladi.

### Umumiy oqim
`/start` → ro'yxatdan o'tkazish → menyu → (savol | mashq | progress).
Har bir savol/mashq natijasi `interactions` jadvaliga log qilinadi.

---

## 3. Texnologiyalar

- **aiogram 3.x** — Telegram (router'lar, FSM)
- **anthropic** (AsyncAnthropic) — Claude API (tushuntirish + rasm o'qish + mashq)
- **asyncpg** — PostgreSQL / Supabase
- **python-dotenv** — `.env`
- Model: `claude-sonnet-4-6` (config orqali o'zgartiriladi; qiyin matematikaga `opus`)

---

## 4. Hozirgi holat (mavjud kod)

Ishlaydigan MVP tayyor. Tuzilishi:

```
leti_math_mentor/
├── bot.py                  # kirish nuqtasi, router'larni ulaydi
├── config.py               # .env dan sozlamalar
├── prompts.py              # mentor system prompt (Sokratik uslub shu yerda)
├── keyboards.py            # menyu va mavzu tugmalari
├── requirements.txt
├── .env.example
├── services/
│   ├── claude.py           # ask_mentor / generate_practice / check_answer
│   ├── db.py               # init_db / ensure_user / log_interaction / get_progress
│   └── memory.py           # suhbat konteksti (HOZIR RAM'da — vaqtinchalik)
└── handlers/
    ├── start.py            # /start, ro'yxat
    ├── question.py         # matn + rasm savollar (Sokratik)
    ├── practice.py         # mashq tuzish + tekshirish (FSM)
    └── progress.py         # progress ko'rsatish
```

Uchchala funksiya ishlaydi. Jadvallar (`bot_users`, `interactions`) birinchi ishga
tushganda avtomatik yaratiladi.

---

## 5. Claude Code bajaradigan ishlar (muhimligi bo'yicha)

### Yuqori ustuvorlik
1. **Redis ulash.** `services/memory.py` hozir suhbatni RAM'da saqlaydi — bot qayta
   ishga tushsa yo'qoladi. Uni Redis bilan almashtir (interfeysni o'zgartirmay:
   `get_history`, `add_turn`, `reset` o'sha-o'sha qolsin). Sessiyaga TTL qo'y (masalan
   1 soat). `redis.asyncio` ishlat. `REDIS_URL` ni config/.env ga qo'sh.

2. **Xatolarni boshqarish (error handling).** Claude API yoki bazada xato bo'lsa, bot
   yiqilmasin — o'quvchiga "biroz kuting / qayta urinib ko'ring" desin, xatoni log
   qilsin. aiogram'da global error handler qo'sh. Claude chaqiruvlariga timeout va
   1-2 marta retry qo'sh.

3. **Rate-limit.** Bir o'quvchi juda tez-tez yuborsa cheklash (Redis counter orqali,
   masalan daqiqasiga N ta xabar). Spam va ortiqcha API xarajatining oldini oladi.

### O'rta ustuvorlik
4. **Savollardan kuchsiz mavzuni aniqlash.** Hozir progress faqat mashqdan hisoblanadi.
   Savol-javobda Claude o'quvchi qaysi mavzuda qiynalayotganini aniqlasin (qisqa teg
   qaytarsin) va `interactions.topic` ga yozilsin. Shunda progress aniqroq bo'ladi.

5. **Mashq darajasini moslashtirish.** O'quvchining o'sha mavzudagi natijasiga qarab
   masala darajasini tanla (oson/o'rta/qiyin) — `generate_practice(topic, level)`
   allaqachon `level` qabul qiladi, uni progressga ulash kerak.

6. **/help va matematik formatlash.** `/help` komandasi; formulalarni Telegramda
   chiroyli ko'rsatish (oddiy matn yetarli, lekin uzun yechimlarni bo'lib yuborish).

### Past ustuvorlik (keyin)
7. **LETI EDU akkaunt bog'lash.** `bot_users.leti_id` ustuni tayyor. O'quvchining
   Telegram ID'sini platforma akkaunti bilan bog'lash (deep-link yoki kod orqali) va
   qiynalgan mavzu bo'yicha platformadagi tegishli darsga havola berish.

8. **Deploy.** Dockerfile + docker-compose (bot + postgres + redis). Log'lar,
   qayta ishga tushish (restart policy).

---

## 6. Kod qoidalari va muhim eslatmalar

- **Sokratik uslubni buzma.** Javob berish mantig'i `prompts.py` da. Tayyor yechim
  berib qo'yadigan tarzga o'zgartirma.
- **aiogram router tartibi muhim.** `bot.py` da `question.router` OXIRGI bo'lishi shart
  — u "fallback" (qolgan barcha matnni ushlaydi). Yangi handler qo'shsang, menyu
  matnlari/holatlar undan oldin ushlanishiga ishonch hosil qil.
- **PostgreSQL — har doim `$1, $2` placeholder + asyncpg parametrlari.** SQL ichiga
  qiymatni to'g'ridan-to'g'ri qo'shma (SQL injection xavfi). asyncpg parametrlari
  apostroflarni o'zi xavfsiz qiladi.
- **Telegram "chat not found"** = o'quvchi avval botga `/start` bosmagan. Xabar yuborish
  shu sababdan tushmasligi mumkin — buni xato sifatida emas, kutilgan holat sifatida
  qabul qil.
- **Rasm = Claude vision.** Telegram rasmlari JPEG; base64 qilib `media_type:
  "image/jpeg"` bilan yuboriladi (claude.py da bor). Alohida OCR kutubxonasi kerak emas.
- **Callback'larni sinash.** aiogram'da callback (inline tugma) "Execute Step" rejimida
  "query too old" beradi — faqat ishlab turgan (polling) botda, haqiqiy Telegram
  bosish orqali sinash kerak.
- **API kalitlari faqat `.env` da.** Hech qachon kodga yoki repoga yozma.

---

## 7. Qabul qilish mezonlari (bajarildi deb hisoblanadi, agar)

- [ ] Bot qayta ishga tushsa ham suhbat konteksti saqlanadi (Redis).
- [ ] Claude yoki baza xato bersa, bot yiqilmaydi va o'quvchi tushunarli xabar oladi.
- [ ] Bir o'quvchi spam qilsa, rate-limit ishlaydi.
- [ ] Savol-javob ham `interactions.topic` ga mavzu yozadi va progressda ko'rinadi.
- [ ] `python bot.py` (yoki docker-compose) bilan toza ishga tushadi.
- [ ] Sokratik uslub saqlangan — bot uy-vazifa masalasiga darrov tayyor javob bermaydi.
