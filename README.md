# Everest-ITCenterBot

Everest IT Center o'quv markazi uchun professional, ko'p funksiyali Telegram boti.

## 🚀 Asosiy Imkoniyatlar

1. **👥 Referal va Konkurs Tizimi:**
   - Shaxsiy taklif havolalari (Deep-linking).
   - Soxta a'zolarga qarshi qat'iy himoya (Anti-fraud: kanal a'zoligi, telefon tasdiqlash, vaqt cheklovi).
   - O'zgarmas audit log (`points_ledger`).
   - Jonli Top-10 reyting (Maxfiylik himoyalangan: ism-familiyalar qisqartirilgan).

2. **📝 Test Platformasi:**
   - O'qituvchilar va umumiy foydalanuvchilar uchun test yaratish (`➕ Yangi test yaratish`).
   - Avtomatik noyob test kodi (`EV-XXXX`) generatsiyasi.
   - Tezkor javoblar kiritish (`1a2b3d...` yoki `1a 2b 3d`).
   - Savollar sonini avtomatik aniqlash.
   - Ishtirokchilar tomonidan testni tugmalar orqali yoki matnli xabarda topshirish.
   - Test yakunlanishi bilanoq yaratuvchiga real-time reyting, o'rinlar va ballar hisoboti.
   - Professional Excel (.xlsx) natijalar jadvalini yuklab olish.
   - Testni rasman yakunlash / yopish.

3. **📚 Kurslar Katalogi va Ro'yxatdan O'tish:**
   - Kategoriyalar va interaktiv kurslar ro'yxati.
   - FSM orqali ochiq darsga qulay yozilish.
   - O'qituvchi va administratorlarga bir zumda arizani yo'naltirish.

4. **🤖 AI Kanal Post Generator:**
   - Claude 3.5 Sonnet va Gemini 1.5 Pro (Fallback) integratsiyasi.
   - O'quv markaz kanali uchun post variantlarini generatsiya qilish va inson tasdig'i orqali chop etish.

5. **🛠 Boshqaruv va Xavfsizlik:**
   - Administrator boshqaruv paneli va real-time statistika.
   - Universal bekor qilish (`/cancel`, `❌ Bekor qilish`) va FSM xavfsizligi.
   - Rate-limiting (Throttling) va global xatoliklar middleware'i.

## 🛠 Texnologik Stack

- **Til:** Python 3.12+
- **Framework:** [aiogram 3](https://docs.aiogram.dev/)
- **Ma'lumotlar bazasi:** PostgreSQL / Supabase, SQLite (avtomatik fallback)
- **Vazifalar boshqaruvi:** APScheduler
- **Hisobotlar:** openpyxl (Excel export)
- **Testlash:** pytest, pytest-asyncio

## 📦 O'rnatish va Ishga tushirish

1. **Repozitoriyani klonlash:**
   ```bash
   git clone https://github.com/Azamqulov/Everest-ITCenterBot.git
   cd Everest-ITCenterBot
   ```

2. **Kutubxonalarni o'rnatish:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfiguratsiya (.env):**
   `.env.example` faylidan nusxa olib `.env` yarating va Telegram bot tokenini kiriting:
   ```env
   BOT_TOKEN=YOUR_BOT_TOKEN
   BOT_USERNAME=Everest_ITCenterbot
   SUPERADMIN_IDS=123456789
   ```

4. **Botni ishga tushirish:**
   ```bash
   python -m bot.main
   ```

## 🧪 Testlarni ishga tushirish

```bash
python -m pytest
```
