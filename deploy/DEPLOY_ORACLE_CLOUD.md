# 🚀 Lux Leti AI Mentorini TEKINGA deploy qilish — Oracle Cloud (Always Free)

Bu yo'riqnoma botni Oracle Cloud'ning **abadiy tekin** (Always Free) Linux
serverida 24/7 ishlatib turishni o'rgatadi. Bot **polling** rejimida ishlaydi,
shuning uchun domen/HTTPS shart EMAS. Ma'lumotlar bazasi — allaqachon Supabase'da.

> ⚠️ Eng muhim qoida: bir vaqtning o'zida bot FAQAT BITTA joyda ishlasin.
> Server ishga tushgach, kompyuteringizdagi `py main.py` ni TO'XTATING
> (aks holda Telegram 409 "Conflict" xatosi beradi).

---

## 0. Nima kerak (oldindan)
- Bank kartasi (faqat shaxsni tasdiqlash uchun — pul YECHILMAYDI, Always Free
  resurslari uchun to'lov yo'q).
- `.env` faylingizdagi qiymatlar: `TELEGRAM_BOT_TOKEN`, `ANTHROPIC_API_KEY`,
  `DATABASE_URL`, `ADMIN_IDS`.
- SSH bilan ishlash (Windows'da PowerShell yoki PuTTY).

---

## 1-qadam. Oracle Cloud hisobini ochish
1. https://www.oracle.com/cloud/free/ ga kiring → **Start for free**.
2. Email, mamlakat (Uzbekistan), telefon raqamni kiriting va tasdiqlang.
3. Kartani kiriting (tasdiq uchun ~$1 bloklanib, qaytariladi).
4. Hisob tayyor bo'lgach, **Oracle Cloud Console** ga kiring.

💡 Maslahat: **Home Region** ni o'zingizga yaqin tanlang (masalan
*Singapore* yoki *South Korea — Seoul*). Supabase pooler ham `ap-northeast-2`
(Seoul) da — yaqin region kechikishni kamaytiradi.

---

## 2-qadam. Tekin serverni (VM) yaratish
1. Console'da: **Menu → Compute → Instances → Create Instance**.
2. **Name:** `lux-mentor`.
3. **Image and shape → Edit:**
   - **Image:** `Canonical Ubuntu 24.04`.
   - **Shape:** `Ampere` bo'limidan **VM.Standard.A1.Flex** (ARM, "Always Free
     eligible" yozuvi bo'lishi kerak). Masalan **1 OCPU + 6 GB RAM** — bot uchun
     ortig'i bilan yetadi va tekin.
     - 💡 Agar "Out of capacity" chiqsa: bir-ikki marta qayta urinib ko'ring yoki
       boshqa Availability Domain (AD-1/AD-2/AD-3) tanlang. ARM tekin shakl
       ba'zan band bo'ladi.
4. **Add SSH keys:**
   - **Generate a key pair for me** ni tanlab, **ikkala kalitni ham yuklab oling**
     (private va public). Private kalitni (`.key`) yo'qotmang!
   - (yoki o'zingizdagi mavjud public kalitni qo'ying).
5. **Create** bosing. 1-2 daqiqada server **Running** bo'ladi.
6. Instance sahifasidan **Public IP address** ni nusxalang (masalan `140.x.x.x`).

---

## 3-qadam. Serverga SSH bilan ulanish
Windows PowerShell'da (yuklab olingan private kalit yo'lini qo'ying):

```powershell
# Kalit fayliga ruxsatni to'g'rilash (bir marta)
icacls "C:\Users\user\Downloads\ssh-key-xxxx.key" /inheritance:r
icacls "C:\Users\user\Downloads\ssh-key-xxxx.key" /grant:r "$($env:USERNAME):(R)"

# Ulanish (IP ni o'zingiznikiga almashtiring)
ssh -i "C:\Users\user\Downloads\ssh-key-xxxx.key" ubuntu@140.x.x.x
```

Birinchi ulanishda "yes" deb tasdiqlang. Endi siz serverdasiz.

---

## 4-qadam. Serverni tayyorlash (Python, git)
Server ichida (Ubuntu) quyidagini bajaring:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip git
python3 --version   # 3.12.x bo'lishi kerak — bizning botga mos
```

---

## 5-qadam. Kodni serverga ko'chirish

**Variant A — Git orqali (tavsiya etiladi, keyin yangilash oson).**
Agar loyihani GitHub/GitLab'ga (private repo) qo'ygan bo'lsangiz:

```bash
cd ~
git clone https://github.com/SIZNING-USERNAME/lux-leti-ai-mentor.git
cd lux-leti-ai-mentor
```

**Variant B — To'g'ridan-to'g'ri nusxalash (git yo'q bo'lsa).**
Kompyuteringizdagi PowerShell'da (server ichida EMAS), `.venv` va `.env` siz
butun papkani yuklang. `scp` faqat kerakli narsalarni ko'chiramiz:

```powershell
# Loyiha papkasidan, .venv'siz arxiv qilib yuborgan qulay.
# Eng oddiy: papkani to'liq scp bilan (lekin .venv'ni qo'lda o'chiring — katta).
scp -i "C:\...\ssh-key-xxxx.key" -r `
  "D:\LUMEN\Coding\AI-Mentor-n8n\lux-leti-ai-mentor" `
  ubuntu@140.x.x.x:/home/ubuntu/
```
> ⚠️ Yuborishdan oldin kompyuterda `.venv` papkasini vaqtincha boshqa joyga
> ko'chiring yoki o'chiring (u juda katta va serverda kerak emas — serverda
> yangidan yaratamiz).

---

## 6-qadam. Virtual muhit va kutubxonalar
Server ichida:

```bash
cd ~/lux-leti-ai-mentor
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 7-qadam. `.env` faylini serverda yaratish
`.env` maxfiy, shuning uchun uni serverda qo'lda yozamiz:

```bash
nano ~/lux-leti-ai-mentor/.env
```

Ichiga (o'zingizdagi qiymatlar bilan) yozing:

```
TELEGRAM_BOT_TOKEN=8xxxx:AAxxxx
ANTHROPIC_API_KEY=sk-ant-xxxx
DATABASE_URL=postgresql://postgres.xxxx:PAROL@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres
ADMIN_IDS=123456789

# Polling rejimi (default) — domen kerak emas
BOT_MODE=polling
AUTO_MIGRATE=true
REVIEW_ENABLED=true
```

Saqlash: `Ctrl+O` → `Enter` → `Ctrl+X`.

> ℹ️ Supabase pooler (port **6543**) uchun kod ichida `statement_cache_size=0`
> allaqachon sozlangan — qo'shimcha narsa shart emas.

### Qo'lda bir marta sinab ko'rish (ixtiyoriy lekin tavsiya):
```bash
cd ~/lux-leti-ai-mentor
source .venv/bin/activate
python main.py
```
Telegram'da botga `/start` yozing — javob bersa, ishlayapti. `Ctrl+C` bilan
to'xtating va keyingi qadamga o'ting (doimiy service qilish uchun).

---

## 8-qadam. systemd service — botni 24/7 ishlatish
Tayyor service fayli loyihada bor: `deploy/lux-mentor.service`. Uni o'rnatamiz:

```bash
sudo cp ~/lux-leti-ai-mentor/deploy/lux-mentor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable lux-mentor      # server qayta yuklansa ham avtomatik ishga tushadi
sudo systemctl start lux-mentor       # hozir ishga tushiramiz
sudo systemctl status lux-mentor      # holatini ko'rish (active/running bo'lishi kerak)
```

> Agar foydalanuvchi nomi `ubuntu` emas yoki papka boshqa joyda bo'lsa,
> service faylidagi `User=` va yo'llarni mos ravishda tahrirlang.

---

## 9-qadam. Loglarni ko'rish va boshqarish
```bash
# Jonli loglar (real vaqtda)
journalctl -u lux-mentor -f

# Oxirgi 100 qator
journalctl -u lux-mentor -n 100 --no-pager

# Boshqaruv
sudo systemctl restart lux-mentor   # qayta ishga tushirish
sudo systemctl stop lux-mentor      # to'xtatish
sudo systemctl start lux-mentor     # yoqish
```

✅ Tayyor! Bot endi serverda doimiy ishlaydi. Kompyuteringizni o'chirsangiz ham,
server uzilsa ham (Restart=always) bot ishlayveradi.

---

## 🔄 Kodni yangilash (keyinroq o'zgartirish kiritsangiz)

**Git ishlatgan bo'lsangiz:**
```bash
cd ~/lux-leti-ai-mentor
git pull
source .venv/bin/activate
pip install -r requirements.txt   # yangi kutubxona qo'shilgan bo'lsa
sudo systemctl restart lux-mentor
```

**Git ishlatmagan bo'lsangiz:** o'zgargan fayllarni qaytadan `scp` qiling, so'ng
`sudo systemctl restart lux-mentor`.

---

## ❗ Tez-tez uchraydigan muammolar

| Belgi | Sabab | Yechim |
|------|-------|--------|
| Telegram `409 Conflict` | Bot 2 joyda ishlayapti | Kompyuterdagi `py main.py` ni to'xtating |
| `status` da `failed` | `.env` to'liq emas / DB ulanmadi | `journalctl -u lux-mentor -n 50` ga qarang |
| DB `statement cache` xatosi | Pooler port 6543 | `DATABASE_URL` to'g'ri pooler manzilini ishlatayotganini tekshiring |
| ARM "Out of capacity" | Tekin shakl band | Boshqa AD tanlang yoki keyinroq urinib ko'ring |
| SSH `Permission denied` | Kalit ruxsati noto'g'ri | 3-qadamdagi `icacls` buyruqlarini bajaring |

---

## 🔐 Kichik xavfsizlik tavsiyalari (ixtiyoriy)
- Serverda firewall: `sudo ufw allow OpenSSH && sudo ufw enable`
  (polling uchun boshqa port ochish shart emas).
- `.env` faylini hech kim bilan ulashmang, GitHub'ga PUSH QILMANG
  (`.gitignore` da allaqachon bor).
- Vaqti-vaqti bilan `sudo apt update && sudo apt upgrade -y`.
