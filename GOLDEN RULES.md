# 📌 PROJECT DASHBOARD & STATE — Everest IT Center Telegram Bot

> Bu fayl Everest IT Center Telegram Bot loyihasining yagona haqiqat manbai (Source of Truth) hisoblanadi.
> Umumiy texnik qoidalar (kod xavfsizligi, xatolarni ushlash, git, validatsiya va h.k.) global `AGENTS.md` va `skills/` papkasida yashaydi. Bu fayl faqat loyiha holati, arxitekturasi va vazifalariga tegishli.

## 🎯 Overall Objective & Current Phase
- **Loyiha:** Everest IT Center ko'p funksiyali Telegram boti (Referal & Konkurs tizimi, Test platformasi, Kurslar katalogi va yozilish, AI post generator).
- **Hozirgi Bosqich:** Phase 1 (MVP To'liq Implementatsiya va Sinovdan O'tdi)
- **Status:** 🟢 Live & Active (Bot Telegramda `@Everest_ITCenterbot` orqali ishga tushirildi va xabarlarni qabul qilmoqda).

## 🧠 Architecture Decision Log (ADR)
- **Stack:** Python 3.12+ (aiogram 3.31.0), PostgreSQL / Supabase, Redis / MemoryStorage (FSM), APScheduler, Claude 3.5 Sonnet / Gemini 1.5 Pro (Fallback), openpyxl (Excel tahlil va eksport), pytest.
- **Core Protocol:** Global `AGENTS.md` va `skills/` papkasidagi barcha qoidalarga 100% amal qilindi.
- **Data Model:**
  - Jadvallar: `users`, `required_channels`, `contests`, `contest_prizes`, `referrals`, `points_ledger`, `teachers`, `courses`, `course_enrollments`, `tests`, `test_attempts`, `test_answers`, `post_drafts`, `channel_posts`, `ai_logs`, `broadcasts`, `settings`, `audit_logs`, `faq`.
  - Har bir ball harakati o'zgarmas `points_ledger` jadvaliga yoziladi (audit log va anti-fraud bilan).
  - Test javoblari bosqichma-bosqich DBga saqlanadi (`test_answers`), taymer APScheduler orqali nazorat qilinadi.
  - Kurs arizalari to'g'ridan-to'g'ri tegishli o'qituvchiga va adminga yuboriladi.
- **Loyihaga xos maxsus qoidalar:**
  - Ko'p tillilik: O'zbek tili (🇺🇿 asosiy / standart) va Rus tili (🇷🇺 qo'shimcha), i18n JSON fayllari orqali boshqariladi, xabarlarda qat'iy `uz-ux-copywriting` va `uzbekistan-business-context` qoidalariga rioya qilingan.
  - Soxta referalga qarshi qat'iy himoya (Anti-fraud): kanal a'zoligi tekshiruvi, telefon raqami (`contact.user_id == from_user.id`), o'zini o'zi taklif qilishni taqiqlash, tezlik chegarasi va shubhali holatlarda ballni muzlatish.
  - AI bilan ishlashda: Har qanday fakt (kurs narxi, dars vaqti) sun'iy intellekt tomonidan to'qilmaydi, faqat DBdan olinadi va inson (admin) tasdig'isiz kanalga joylanmaydi.

## 🤖 AI Developers & Team Protocol
- To'liq pipeline (dev → qa-tester → team-lead → senior-qa → PM) — global `ai-development-team-protocol` skilida.

## 🔄 Active Task (In Progress)
- [x] TZ to'liq tahlil qilindi va arxitektura rejasi ishlab chiqildi.
- [x] [Faza 0] Infratuzilma, PostgreSQL/Supabase sxemasi, aiogram 3 konfiguratsiyasi, i18n locales (uz/ru), middlewarelar.
- [x] [Faza 1] Referal va Konkurs moduli (Anti-fraud, `points_ledger`, Top-10 reyting, maxfiylik).
- [x] [Faza 2] Kurslar va ariza moduli (Katalog, FSM ariza, o'qituvchi va adminga xabarnoma).
- [x] [Faza 3] Test platformasi (O'qituvchi test yaratishi, `EV-XXXX` kodi, o'quvchi topshirishi, real-time draft, Excel eksport).
- [x] [Faza 4] AI Kanal Post Generator (`ai_service` Claude + Gemini fallback, inson tasdig'i).
- [x] [Faza 5 & Admin] Admin boshqaruv paneli (Statistika, broadcast, ball audit logi).
- [x] Unit va integratsiya testlar (9/9 passed).
- [x] [UX & Feature Upgrade] Universal Bekor qilish va FSM qotib qolish xatosi bartaraf etildi.
- [x] [Test Upgrade] Umumiy barcha foydalanuvchilar uchun test yaratish (avtomatik kod, `1a2b3d...` javoblar kiritish), matnli javob yuborish, ishtirokchilar ballari va reyting o'rinlarini test yaratuvchisiga yuborish, testni yopish va Excel hisobot.

## ✅ Completed Checklist (History)
- [x] 2026-10-05: Loyiha `GOLDEN RULES.md` yaratildi, texnik topshiriq talablari va bosqichlar tasdiqlandi.
- [x] 2026-10-05: Barcha modullar (Faza 0 - 5) to'liq dasturlandi va testlardan o'tkazildi.
- [x] 2026-10-09: Universal Bekor qilish mexanizmi, umumiy userlar test yaratishi va real-time reyting bildirishnomalari ishlab chiqildi va sinovdan o'tkazildi.

## 📋 Roadmap & Upcoming Tasks (Backlog)
- [ ] Foydalanuvchi tomonidan haqiqiy Telegram Bot Token kiritilishi va serverga deploy qilish.
- [ ] Mini App (TMA) va onlayn to'lov (Payme/Click) integratsiyasi (kelgusidagi 2-bosqich).

## 🐛 Known Bugs & UX Defects (Issue Tracker)
- [x] [HAL QILINDI] Bekor qilish bosilganda bot qotib qolishi muammosi (FSM state tiqilishi va universal handler yo'qligi) to'liq tuzatildi.
- [Barcha sinovlar muvaffaqiyatli yakunlandi, kritik xatolar mavjud emas]

