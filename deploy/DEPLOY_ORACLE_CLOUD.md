# 🚀 LETI Matematika Mentorini TEKINGA deploy qilish — Oracle Cloud (Always Free) + Docker

Bu yo'riqnoma botni (yangi `leti_math_mentor` paketi) Oracle Cloud'ning **abadiy tekin**
serverida **Docker** orqali 24/7 ishlatishni o'rgatadi. Bot **polling** rejimida —
domen/HTTPS shart EMAS. Baza allaqachon **Supabase**'da. Docker Compose botni va
**Redis**ni (suhbat konteksti + mashq holati saqlanishi uchun) birga ishga tushiradi.

> ⚠️ Eng muhim qoida: bot bir vaqtda FAQAT BITTA joyda ishlasin. Server ishga tushgach,
> kompyuteringizdagi `run_mentor.py` ni TO'XTATING (aks holda Telegram `409 Conflict`).

---

## 0. Nima kerak
- Bank kartasi (faqat shaxsni tasdiqlash — Always Free uchun pul yechilmaydi; ~$1 vaqtincha bloklanib qaytadi).
- `.env` qiymatlari: `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`, `DATABASE_URL`.
- SSH (Windows PowerShell yetadi).

---

## 1-qadam. Oracle Cloud hisobini ochish
1. https://www.oracle.com/cloud/free/ → **Start for free**.
2. Email, mamlakat (Uzbekistan), telefon — tasdiqlang.
3. Kartani kiriting (~$1 bloklanib qaytadi).
4. **Home Region** ni yaqin tanlang (masalan *Singapore* yoki *Seoul*) — Supabase pooler ham Osiyoda.
5. Console'ga kiring.

---

## 2-qadam. Tekin serverni (VM) yaratish
1. **Menu → Compute → Instances → Create Instance**.
2. **Name:** `leti-mentor`.
3. **Image and shape → Edit:**
   - **Image:** `Canonical Ubuntu 24.04`.
   - **Shape:** `Ampere` → **VM.Standard.A1.Flex** (ARM, "Always Free eligible"). **1 OCPU + 6 GB RAM** yetib ortadi.
   - 💡 "Out of capacity" chiqsa: boshqa Availability Domain (AD-1/2/3) tanlang yoki keyin urinib ko'ring.
4. **Add SSH keys → Generate a key pair for me** → **ikkala kalitni yuklab oling** (private `.key` ni yo'qotmang!).
5. **Create** → 1-2 daqiqada **Running**.
6. **Public IP** ni nusxalang (masalan `140.x.x.x`).

---

## 3-qadam. SSH bilan ulanish
Windows PowerShell'da (kalit yo'lini o'zingiznikiga almashtiring):

```powershell
icacls "C:\Users\user\Downloads\ssh-key-xxxx.key" /inheritance:r
icacls "C:\Users\user\Downloads\ssh-key-xxxx.key" /grant:r "$($env:USERNAME):(R)"
ssh -i "C:\Users\user\Downloads\ssh-key-xxxx.key" ubuntu@140.x.x.x
```

Birinchi ulanishda `yes`. Endi serverdasiz.

---

## 4-qadam. Docker'ni o'rnatish (serverda, bir marta)
```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu        # docker'ni sudosiz ishlatish uchun
```
> ⚠️ `usermod` dan keyin SSH'dan **chiqib qayta kiring** (`exit`, so'ng yana `ssh ...`) —
> guruh o'zgarishi shundan keyin kuchga kiradi. Tekshirish: `docker run hello-world`.

---

## 5-qadam. Kodni serverga olish (Git orqali)
Yangi kod GitHub'da: **github.com/nurmuhammad-sharobiddinov/leti-ai-mentor**.

```bash
cd ~
git clone https://github.com/nurmuhammad-sharobiddinov/leti-ai-mentor.git
cd leti-ai-mentor
```
> Keyin yangilash: `git pull && docker compose up -d --build`.

---

## 6-qadam. `.env` faylini serverda yaratish
`.env` maxfiy — repoda yo'q, qo'lda yozamiz:

```bash
nano ~/leti-ai-mentor/.env
```

Ichiga (o'zingizdagi qiymatlar bilan):

```
TELEGRAM_BOT_TOKEN=5225570156:AA...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://postgres.xxxx:PAROL@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres

# Modellar (ixtiyoriy)
MODEL=claude-sonnet-4-6
HARD_MODEL=claude-opus-4-8

# REDIS_URL ni BU YERGA YOZMANG — docker-compose o'zi redis konteyneriga ulaydi.
RATE_LIMIT_PER_MIN=15
```

Saqlash: `Ctrl+O` → `Enter` → `Ctrl+X`.

> ℹ️ Supabase pooler (port **6543**) uchun `statement_cache_size=0` kod ichida bor — qo'shimcha sozlash shart emas.
> Jadvallar (`bot_users`, `interactions`) bot birinchi ishga tushganda avtomatik yaratiladi.

---

## 7-qadam. Ishga tushirish (Docker Compose)
```bash
cd ~/leti-ai-mentor
docker compose up -d --build
```

Bu bot + redis konteynerlarini quradi va fon rejimida ishga tushiradi.
`restart: unless-stopped` — server qayta yuklansa yoki bot yiqilsa avtomatik tiklanadi.

Tekshirish:
```bash
docker compose ps              # ikkala konteyner "Up" bo'lishi kerak
docker compose logs -f bot     # jonli log — "Run polling for bot @Gcvljyhbot" ko'rinsin
```

Telegram'da botga `/start` yozing — javob bersa, tayyor! ✅
(Kompyuteringizdagi mahalliy nusxani to'xtatishni unutmang.)

---

## 8-qadam. Boshqaruv
```bash
docker compose logs -f bot         # jonli loglar (Ctrl+C chiqish)
docker compose restart bot         # botni qayta ishga tushirish
docker compose down                # hammasini to'xtatish
docker compose up -d               # qayta yoqish
docker compose up -d --build       # kod o'zgargandan keyin qayta qurish
```

---

## 🔄 Kodni yangilash
```bash
cd ~/leti-ai-mentor
git pull
docker compose up -d --build       # faqat o'zgargan qatlamlar qayta quriladi
```

---

## ❗ Tez-tez uchraydigan muammolar

| Belgi | Sabab | Yechim |
|------|-------|--------|
| Telegram `409 Conflict` | Bot 2 joyda ishlayapti | Kompyuterdagi `run_mentor.py` ni to'xtating |
| `docker: permission denied` | `usermod` dan keyin qayta kirmagansiz | SSH'dan chiqib qayta kiring |
| `bot` konteyner qayta-qayta o'chadi | `.env` to'liq emas / DB ulanmadi | `docker compose logs bot` ga qarang |
| DB `statement cache` xatosi | Pooler port 6543 | `DATABASE_URL` to'g'ri pooler manzili ekanini tekshiring |
| ARM "Out of capacity" | Tekin shakl band | Boshqa AD tanlang yoki keyin urinib ko'ring |
| SSH `Permission denied` | Kalit ruxsati | 3-qadamdagi `icacls` buyruqlarini bajaring |

---

## 🔐 Xavfsizlik (ixtiyoriy)
- Firewall: `sudo ufw allow OpenSSH && sudo ufw enable` (polling uchun boshqa port shart emas).
- `.env` ni hech kimga bermang, GitHub'ga push QILMANG (`.gitignore` da bor).
- Vaqti-vaqti: `sudo apt update && sudo apt upgrade -y` va `docker compose pull` (redis yangilanishi uchun).
