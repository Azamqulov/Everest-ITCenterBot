# Everest IT Center Telegram Bot — Texnik Topshiriq (TZ)

**Versiya:** 1.0 (qoralama, tasdiqlashga) · **Sana:** 2026-10-05 · **Muallif:** Azamkulov Musurmon

---

## 1. Loyiha haqida

### 1.1. Maqsad

Everest IT Center uchun yagona Telegram bot yaratish. Bot to'rtta asosiy vazifani bajaradi:

1. **Konkurslar uchun referal tizimi** — foydalanuvchi do'stlarini taklif qilib ball yig'adi, admin hammasini nazorat qiladi.
2. **Test platformasi** — o'qituvchi test yaratadi, o'quvchi kod orqali kirib topshiradi, bot avtomatik tekshiradi.
3. **Kurslar katalogi va yozilish** — o'quv markaz kurslari, narx, jadval, ro'yxatdan o'tish; ariza tegishli o'qituvchiga boradi.
4. **AI yordamida kanal postlari** — admin mavzu beradi, AI 3–4 variant tayyorlaydi, admin tasdiqlaydi, bot kanalga joylaydi.

### 1.2. Muvaffaqiyat mezonlari (KPI)

| Ko'rsatkich | Maqsad (tavsiya) |
| --- | --- |
| Konkurs davomida yangi botga kirgan foydalanuvchilar | Admin belgilaydi (masalan 1 000+) |
| Referal "tasdiqlanish" darajasi (start → tasdiqlangan) | ≥ 60% |
| Soxta/shubhali referallar ulushi | \< 5% |
| Kursga ariza → o'qituvchi bog'lanishi (o'rtacha vaqt) | \< 24 soat |
| Post tayyorlash vaqti (mavzu → kanalga) | \< 3 daqiqa |
| Bot javob vaqti | \< 1 soniya (AI bundan mustasno) |

### 1.3. Maqsadli auditoriya

Everest IT Center o'quvchilari va potensial o'quvchilari (asosan o'zbekzabon, ruscha ham qo'llab-quvvatlanadi), o'qituvchilar, markaz ma'muriyati.

---

## 2. Rollar va huquqlar

| Imkoniyat | User | Teacher | Admin | Superadmin |
| --- | --- | --- | --- | --- |
| Referal link, ball, reyting ko'rish | ✅ | ✅ | ✅ | ✅ |
| Testga kod bilan kirish va topshirish | ✅ | ✅ | ✅ | ✅ |
| Kurslarni ko'rish, ariza topshirish | ✅ | ✅ | ✅ | ✅ |
| Test yaratish, natijalarini ko'rish | ❌ | ✅ (o'zining) | ✅ (hammasi) | ✅ |
| Kurs qo'shish/tahrirlash | ❌ | ✅ (o'zining) | ✅ (hammasi) | ✅ |
| O'z kursiga kelgan arizalarni ko'rish/statusini o'zgartirish | ❌ | ✅ | ✅ | ✅ |
| Kurs moderatsiyasi (tasdiqlash) | ❌ | ❌ | ✅ | ✅ |
| Konkurs yaratish/boshqarish, ballni qo'lda o'zgartirish | ❌ | ❌ | ✅ | ✅ |
| Statistika, foydalanuvchilar ro'yxati | ❌ | ❌ (faqat o'ziniki) | ✅ | ✅ |
| AI post generator, kanalga joylash | ❌ | ❌ | ✅ | ✅ |
| Broadcast (ommaviy xabar) | ❌ | ❌ | ✅ | ✅ |
| Admin/teacher qo'shish va olib tashlash | ❌ | ❌ | ❌ | ✅ |
| Sozlamalar, AI limitlari, audit log | ❌ | ❌ | ❌ | ✅ |

**Teacher/Admin qo'shish usuli:** Superadmin bir martalik taklif kodi yaratadi yoki Telegram ID kiritadi. Rol faqat shu orqali beriladi (foydalanuvchi o'zi rol so'ray olmaydi).

---

## 3. Texnik arxitektura

### 3.1. Stack

| Qatlam | Tanlov | Izoh |
| --- | --- | --- |
| Bot | **Python 3.12 + aiogram 3** | FSM murakkab dialoglar (test yaratish, ariza) uchun qulay; boshqa botlaringiz bilan bir xil |
| Ma'lumotlar bazasi | **Supabase (PostgreSQL)** | Jadval, RLS, backup, keyin web-dashboard uchun tayyor Auth |
| FSM saqlash | **Redis** (yoki Supabase) | Restartdan keyin dialoglar yo'qolmasligi uchun |
| Fon vazifalar | **APScheduler** | Rejalashtirilgan postlar, test taymeri, eslatmalar, broadcast |
| AI | **Claude API** (asosiy) + **Gemini** (fallback) | Alohida `ai_service` modul orqali |
| Rasm/sertifikat | **Pillow** | Keyingi fazada (sertifikat, post kartasi) |
| Deploy | **Docker + VPS**, webhook rejimi | Lokal developmentda polling |
| Monitoring | Sentry yoki Telegram orqali admin-alert | Xato va fallback hodisalari |

### 3.2. Qaror talab qiladigan nuqtalar (variantlar)

**A. Admin panel qayerda bo'ladi?**

| Variant | Afzallik | Kamchilik |
| --- | --- | --- |
| 1. Faqat bot ichida (inline menyu) | Eng tez, alohida hosting kerak emas | Grafik/katta jadval noqulay |
| 2. Alohida web-panel (Vue 3 + Tailwind + Supabase Auth) | Grafiklar, jadval, Excel, qulay | Qo'shimcha ish hajmi |
| 3. **Gibrid** (kundalik amallar botda, statistika/grafik webda) | Ikkisining yaxshi tomoni | Ikki qismni qo'llab-quvvatlash |

**Tavsiya:** 3-variant, lekin bosqichma-bosqich — MVPda bot ichidagi panel + Excel eksport, keyin web-dashboard.

**B. Ball tizimi:** (1) global ball balansi (bitta hamyon) yoki (2) har konkurs uchun alohida hisob. **Tavsiya:** (2) — har yozuv `contest_id` bilan saqlanadi, shunda yangi konkurs "nol"dan boshlanadi, tarix yo'qolmaydi.

**C. G'olibni aniqlash:** (1) eng ko'p ball to'plagan Top-N; (2) lotereya — har X ball = 1 chipta, tasodifiy tanlash; (3) ikkalasi aralash. **Tavsiya:** konkurs yaratishda admin tanlaydi (ikkalasi ham qo'llab-quvvatlanadi).

---

## 4. Funksional talablar

### 4.0. Umumiy: ishga tushirish va ro'yxatdan o'tish

- `/start` — til tanlash (🇺🇿 O'zbekcha — default, 🇷🇺 Русский). Matnlar i18n kalitlar orqali (`uz.json`, `ru.json`), hardcoded matn yo'q.
- **Majburiy obuna:** Everest IT Center kanali (va ixtiyoriy guruh) — obuna bo'lmasa bot asosiy menyuni ochmaydi. Obuna `getChatMember` orqali tekshiriladi, "✅ Tekshirish" tugmasi bor. Majburiy kanallar admin paneldan o'zgartiriladi.
- **Telefon raqamni tasdiqlash:** "📱 Raqamni yuborish" tugmasi (faqat o'zining kontakti qabul qilinadi — `contact.user_id == from_user.id`).
- **Rozilik:** shaxsiy ma'lumotlarni qayta ishlashga qisqa rozilik matni (O'zbekistonning shaxsga doir ma'lumotlar to'g'risidagi qonuniga muvofiq); foydalanuvchi "Ma'lumotlarimni o'chirish" so'rashi mumkin.
- **Asosiy menyu (user):** 🎁 Konkurs · 👥 Referal · 📝 Testlar · 📚 Kurslar · ℹ️ Markaz haqida · 🌐 Til · 💬 Aloqa.
- Rolga qarab menyuda qo'shimcha tugma chiqadi: 🧑‍🏫 *Teacher panel* / 🛠 *Admin panel*.

---

### 4.1. Modul 1 — Referal va ball tizimi (asosiy modul)

#### 4.1.1. Referal link

- Format: `https://t.me/<bot_username>?start=ref_<kod>`. `<kod>` — qisqa tasodifiy kod (8 belgi), Telegram ID ochiq ko'rinmaydi.
- Foydalanuvchi "👥 Referal" bo'limida: shaxsiy link, **Ulashish** tugmasi (`switch_inline_query`/share), tayyor taklif matni (admin tahrirlaydi).

#### 4.1.2. Referal hisoblash qoidasi

Taklif qilingan do'st quyidagi bosqichlardan o'tgach referal **"tasdiqlangan"** hisoblanadi:

1. Link orqali botga kirdi (`pending`)
2. Majburiy kanalga obuna bo'ldi
3. Telefon raqamini tasdiqladi

Shundan keyingina taklif qilgan odamga **N ball** (default 10, admin sozlaydi) beriladi va unga xabar boradi: *"Do'stingiz Ali qo'shildi, +10 ball!"*.

#### 4.1.3. Soxta referalga qarshi himoya (anti-fraud)

- O'zini o'zi taklif qila olmaydi.
- Har bir foydalanuvchi faqat **bitta** taklif qiluvchiga biriktiriladi (birinchi link kuchda).
- Eski foydalanuvchi (allaqachon botda bor) referal bo'la olmaydi.
- Telefon raqami takrorlanmasligi (bitta raqam = bitta akkaunt); ixtiyoriy: faqat `+998`.
- Kanaldan chiqib ketsa — ball **bekor qilinadi** (admin yoqib/o'chiradi), 24 soatlik tekshiruv.
- **Tezlik nazorati:** bir odamga qisqa vaqtda g'ayrioddiy ko'p referal kelsa — "shubhali" deb belgilanadi, ball vaqtincha muzlatiladi, admin ko'rib chiqadi.
- Ball tarixi **o'zgarmas jurnal** (`points_ledger`): har bir ball qo'shish/ayirish sababi va vaqti bilan saqlanadi; admin qo'lda o'zgartirsa — sabab majburiy va audit logga yoziladi.

#### 4.1.4. Konkurs boshqaruvi (admin)

- Konkurs yaratish: nomi, tavsifi, banner, boshlanish/tugash vaqti, qoidalar matni, sovrinlar (1-, 2-, 3-o'rin…), g'olib aniqlash usuli (Top-N / lotereya), ball qiymatlari.
- Holatlar: `draft → active → finished → archived`.
- Konkurs tugaganda: avtomatik yakuniy reyting, g'oliblar ro'yxati, g'oliblarga xabar, admin tasdiqlagach umumiy e'lon.
- Tugashiga 24 soat qolganda barcha ishtirokchilarga eslatma (ixtiyoriy).

#### 4.1.5. Foydalanuvchi kabineti ("🎁 Konkurs")

- Mening ballarim, taklif qilgan do'stlar soni: **jami / tasdiqlangan / kutilayotgan**.
- Mening o'rnim va **Top-10 reyting** (ismlar qisman yashiriladi: "Ali K.").
- Do'stlarim ro'yxati (ism, holati: ✅ tasdiqlangan / ⏳ kutilmoqda).
- Konkurs qoidalari, sovrinlar, qolgan vaqt.

#### 4.1.6. Ballni boshqa yo'llar bilan ham berish (qo'shimcha, sozlanadigan)

Test topshirgani, kursga yozilgani, kunlik tashrif (check-in) uchun admin belgilagan miqdorda ball. Har bir manba alohida yoqiladi/o'chiriladi.

---

### 4.2. Modul 2 — Testlar

#### 4.2.1. Teacher: test yaratish (FSM oqimi)

`🧑‍🏫 Teacher panel → ➕ Test yaratish`

1. Test nomi (va ixtiyoriy: fan / bog'langan kurs)
2. **Savollar soni** (N)
3. **Har bir savolda variantlar soni** (A–D yoki A–E) — hammasi uchun umumiy yoki alohida
4. **To'g'ri javoblar kaliti** — ikki usul:
   - bitta xabarda: `1a 2c 3b 4d ...`
   - yoki tugmalar orqali savol-savol
5. Test materiali: PDF/rasm biriktirish (ixtiyoriy) — o'quvchi kirganda yuboriladi
6. Sozlamalar: vaqt chegarasi (daqiqa), urinishlar soni (1 yoki ko'p), ochilish/yopilish vaqti, to'g'ri javoblarni ko'rsatish (darhol / test yopilgach / ko'rsatmaslik), natijani reytingda ko'rsatish (ha/yo'q)
7. Ko'rib chiqish → tasdiqlash → bot **test kodi** yaratadi (masalan `EV-4821`) va tayyor ulashish matnini beradi.

**Variantlar (test kiritish usuli):**

| Variant | Mazmuni | Baho |
| --- | --- | --- |
| A. Kalit + fayl | O'qituvchi PDF/rasm yuklaydi, faqat javob kalitini kiritadi | Tez, MVP uchun yetarli |
| B. Savol-savol | Har savol matni va variantlari botga kiritiladi | Ko'p mehnat, lekin bot ichida to'liq test |

**Tavsiya:** MVPda A, keyingi fazada B.

**Savol turlari:** MVP — yopiq (variantli). Keyingi faza — ochiq javob (son/qisqa matn), ko'p javobli savollar.

#### 4.2.2. O'quvchi: testni topshirish

`📝 Testlar → 🔑 Kod kiritish`

1. Kodni kiritadi → bot test ma'lumotini ko'rsatadi (nomi, savollar soni, vaqti, urinishlar) → "▶️ Boshlash".
2. Fayl (PDF/rasm) yuboriladi, **taymer** ishga tushadi.
3. Javob berish — ikki qulay usul:
   - **Tugmalar:** har sahifada 10 ta savol, har biri uchun `A B C D` qatori; belgilangan javob ✅ bo'ladi, o'zgartirish mumkin;
   - **Matn:** bitta xabarda `1a2b3c...` formati.
4. "✅ Yakunlash" yoki vaqt tugashi bilan avtomatik topshirish.
5. **Natija:** to'g'ri/noto'g'ri soni, foiz, xato qilingan savollar raqamlari (sozlamaga qarab to'g'ri javoblar bilan), reytingdagi o'rni.

#### 4.2.3. Teacher: natijalar

- Ishtirokchilar ro'yxati (ism, ball, vaqt), o'rtacha ball, eng yuqori/past natija.
- **Savol tahlili:** qaysi savollarga eng ko'p xato qilingan.
- **Excel (.xlsx) eksport.**
- Testni yopish / qayta ochish / nusxa ko'chirish / arxivlash.
- Yangi natija kelganda ixtiyoriy bildirishnoma.

#### 4.2.4. Himoya va chekka holatlar

- Kodni topishga urinishdan himoya: 5 ta noto'g'ri kod → 10 daqiqa blok.
- Javoblar har bosishda DBga saqlanadi (draft) — bot qayta ishga tushsa ham yo'qolmaydi.
- Foydalanuvchi testni yarmida tashlab ketsa — taymer tugagach fon vazifa avtomatik topshiradi.
- To'g'ri javoblar kaliti faqat test egasi va adminga ko'rinadi.
- Yopilgan/muddati o'tgan testga kirib bo'lmaydi.

---

### 4.3. Modul 3 — Kurslar va yozilish

#### 4.3.1. Kurs kartasi (maydonlar)

| Maydon | Izoh |
| --- | --- |
| Nomi, kategoriya | Masalan: Frontend, Python, Grafik dizayn… |
| Qisqa va batafsil tavsif | Kimlar uchun, nimani o'rganadi |
| Daraja | Boshlang'ich / O'rta / Yuqori |
| **Narx** | Oyiga yoki jami (so'm), chegirma bo'lsa alohida |
| **Davomiyligi** | Necha oy / necha dars |
| **Jadval** | Haftada necha kun, **qaysi kunlar** (Du/Chor/Ju), dars vaqti |
| Format va manzil | Offline / online, filial |
| O'rinlar soni, boshlanish sanasi | Guruh to'lganda "kutish ro'yxati" |
| O'qituvchi | Avtomatik biriktiriladi |
| Banner/rasm, dastur (syllabus) | Ixtiyoriy |
| Bepul sinov darsi | Bor/yo'q |
| Holat | `draft / pending / published / archived` |

#### 4.3.2. Kurs qo'shish (Teacher / Admin)

- Teacher o'z kursini FSM orqali qo'shadi → **admin tasdiqlaydi** (moderatsiya, nosoz ma'lumot chiqib ketmasligi uchun). Admin xohlasa teacherga to'g'ridan-to'g'ri e'lon qilish huquqini beradi (sozlama).
- Teacher faqat o'z kurslarini tahrirlaydi/arxivlaydi; admin hammasini.

#### 4.3.3. Foydalanuvchi: yozilish oqimi

`📚 Kurslar → kategoriya → kurs kartasi → ✍️ Ro'yxatdan o'tish`

1. Ism, telefon (tasdiqlangan raqam oldindan to'ldiriladi), yosh (ixtiyoriy), qulay vaqt (ixtiyoriy), izoh.
2. Tasdiqlash → foydalanuvchiga: *"Arizangiz qabul qilindi, o'qituvchi tez orada bog'lanadi"*.
3. **O'sha kurs o'qituvchisiga** va adminga bildirishnoma: ism, telefon, Telegram username, **ariza sanasi/vaqti**, kurs nomi.
4. Bir foydalanuvchi bitta kursga bir vaqtda bitta faol ariza yubora oladi.

#### 4.3.4. Arizalar boshqaruvi (Teacher / Admin)

- Holatlar: `yangi → bog'lanildi → yozildi → rad etildi / kutish ro'yxati`.
- Teacher o'z kursidagi arizalarni sana bo'yicha filtrlab ko'radi, statusini o'zgartiradi, izoh qo'shadi, Excelga eksport qiladi.
- 24 soat ichida "yangi" holatda qolgan ariza haqida o'qituvchiga va adminga eslatma.
- Statistika: kurs bo'yicha ko'rishlar → arizalar → yozilganlar (konversiya), teacher bo'yicha taqqoslash.

---

### 4.4. Modul 4 — AI bilan kanal postlari (Admin)

#### 4.4.1. Oqim

`🛠 Admin → 📝 Post yaratish`

1. Admin mavzu yozadi (masalan: *"bugun dasturlash haqida post"*).
2. Ixtiyoriy parametrlar: maqsad (ta'lim / kurs reklamasi / konkurs e'loni / motivatsiya), ohang (do'stona / rasmiy / motivatsion), uzunlik (qisqa / o'rta / uzun), til (uz / ru), emoji va hashtaglar.
3. AI **3–4 xil variant** tayyorlaydi (loading holati ko'rsatiladi).
4. Admin variantni tanlaydi → harakatlar:
   - 🔄 Qayta yaratish
   - ✏️ Tahrirlash (qo'lda yoki ko'rsatma bilan: *"qisqartir"*, *"ohangni jiddiyroq qil"*)
   - 🖼 Rasm qo'shish
   - 🔗 Tugma qo'shish (masalan "Kursga yozilish" → botga deep link)
5. **Preview** — post kanalda aynan qanday ko'rinishini ko'rsatadi.
6. ✅ Tasdiqlash → **hozir joylash** yoki **rejalashtirish** (sana/vaqt) → bot kanalga joylaydi, havolasini qaytaradi.

#### 4.4.2. Qo'shimcha imkoniyatlar

- **Kontent taqvimi:** rejalashtirilgan postlar ro'yxati, bekor qilish/o'zgartirish.
- **Postlar tarixi:** mavzu, tanlangan variant, joylangan vaqt.
- **Brend ovozi:** AI uchun "Everest IT Center" tavsifi (ohang, taqiqlangan so'zlar, doimiy hashtaglar) — superadmin paneldan tahrirlaydi.
- **Fakt xavfsizligi:** narx, sana, manzil kabi faktlarni AI o'ylab topmaydi — ular bazadan (kurs kartasidan) qo'yiladi; har post **inson tasdig'idan** o'tadi.
- Bir nechta kanalni ulash imkoni (har kanal uchun alohida sozlama).

#### 4.4.3. AI texnik talablari

- Barcha AI chaqiruvlari yagona `ai_service` moduli orqali; promptlar `prompts/` papkasida versiyalangan fayllarda (kod ichida emas).
- Fallback: rate-limit → qayta urinish (1s, 2s, 4s) → Gemini ga o'tish; content-filter bo'lsa qayta urinilmaydi, adminga mavzuni o'zgartirish taklif qilinadi.
- Xarajat nazorati: kunlik/oylik generatsiya limiti, har chaqiruv logi (token, vaqt, xato); bir xil so'rovga keshlash.
- Telegram cheklovlari hisobga olinadi: matn ≤ 4096, rasmli post izohi ≤ 1024 belgi; xavfsiz HTML teglar.
- API kalitlar faqat serverda `.env` da.

---

### 4.5. Admin panel

#### 4.5.1. Bo'limlar

| Bo'lim | Mazmuni |
| --- | --- |
| 📊 Statistika | Quyida 4.5.2 |
| 🎁 Konkurslar | Yaratish, tahrirlash, reyting, g'olibni aniqlash |
| 👥 Foydalanuvchilar | Qidiruv (ism/telefon/@username), profil, ball tarixi, **ballni qo'lda o'zgartirish (sabab bilan)**, bloklash/blokdan chiqarish |
| 🚩 Shubhali referallar | Muzlatilgan ballar: tasdiqlash yoki bekor qilish |
| 📚 Kurslar | Moderatsiya, barcha arizalar |
| 📝 Testlar | Barcha testlar va natijalar |
| 🧑‍🏫 Teacherlar | Qo'shish/olib tashlash, har birining statistikasi |
| 📝 Post generator | 4.4 |
| 📣 Broadcast | Ommaviy xabar |
| ⚙️ Sozlamalar | Ball qiymatlari, majburiy kanallar, matnlar, AI limitlari, brend ovozi |
| 🧾 Audit log | Kim, nima, qachon o'zgartirgani |

#### 4.5.2. Statistika

- **Foydalanuvchilar:** jami, bugungi yangi, faol (DAU/WAU/MAU), o'sish grafigi, til bo'yicha taqsimot, botni bloklaganlar.
- **Manba:** referal vs organik.
- **Referal voronkasi:** start → obuna → telefon → tasdiqlangan; Top-10 taklif qiluvchilar; shubhali referallar soni.
- **Konkurs:** ishtirokchilar, jami ball, kunlik dinamika.
- **Testlar:** testlar soni, ishtirokchilar, o'rtacha natija, eng faol teacherlar.
- **Kurslar:** ko'rishlar, arizalar, konversiya, kurs va teacher kesimida.
- **Kanal postlari:** soni, AI generatsiyalar, taxminiy xarajat.
- **Broadcast:** yuborildi / yetib bordi / bloklagan.
- Davr filtri (bugun / 7 kun / 30 kun / oraliq) va **Excel/CSV eksport**.

#### 4.5.3. Broadcast

- Matn/rasm/tugma, **segmentlar** (hamma, til, konkurs ishtirokchilari, ma'lum kursga ariza topshirganlar, ball oralig'i).
- Test yuborish (faqat o'ziga), rejalashtirish, Telegram limitiga mos tezlik (\~25 xabar/soniya), natija hisoboti, botni bloklaganlarni avtomatik belgilash.

---

### 4.6. Men qo'shgan qo'shimcha imkoniyatlar (tavsiya)

| # | Imkoniyat | Nima uchun kerak | Faza |
| --- | --- | --- | --- |
| 1 | Majburiy obuna tekshiruvi | Konkurs mantig'ining asosi, kanal o'sadi | MVP |
| 2 | Anti-fraud (soxta referallar) | Konkurs adolati, aks holda hamma "soxta akkaunt" ochadi | MVP |
| 3 | O'zgarmas ball jurnali + audit log | Nizo bo'lsa isbotlash mumkin | MVP |
| 4 | Uz/Ru ko'p tillilik | Auditoriya kengayadi | MVP |
| 5 | Shaxsiy ma'lumotga rozilik va o'chirish | Qonuniy talab | MVP |
| 6 | Kutish ro'yxati va "bepul sinov darsi" | Kursga yozilish konversiyasini oshiradi | 2 |
| 7 | Arizaga javob bermagan teacherga eslatma | Mijoz yo'qotilmaydi | 2 |
| 8 | Test natijalari tahlili, Excel eksport | O'qituvchiga katta qulaylik | 3 |
| 9 | Rejalashtirilgan postlar va kontent taqvimi | Muntazam kontent | 4 |
| 10 | Broadcast + segmentlar | Yangi kurs/konkurs e'lonlari | 5 |
| 11 | Sertifikat (test/konkurs g'olibi, PDF/rasm) | Motivatsiya, brend | 5 |
| 12 | Ball do'koni (ballni chegirma/sovg'aga almashtirish) | Konkursdan keyin ham foydalanuvchini ushlab turadi | 5 |
| 13 | Promo-kod | Chegirma va marketing | 5 |
| 14 | FAQ, Aloqa, Manzil (lokatsiya), ijtimoiy tarmoqlar | Markaz haqida ma'lumot | MVP |
| 15 | Fikr-mulohaza / shikoyat | Sifat nazorati | 5 |
| 16 | Web admin-dashboard | Grafik va katta jadval | 5 |
| 17 | Telegram Mini App (kelajak) | Boy interfeys (test, reyting) | Kelajak |
| 18 | Kurs uchun onlayn to'lov (Payme/Click) | Hozir TZga kirmagan — faqat ariza | Kelajak |

---

## 5. Ma'lumotlar bazasi (asosiy jadvallar)

| Jadval | Asosiy maydonlar |
| --- | --- |
| `users` | id, telegram_id (unique), full_name, username, phone, language, role, referral_code, referred_by, is_blocked, is_active, created_at |
| `required_channels` | id, chat_id, title, link, is_active |
| `contests` | id, title, description, starts_at, ends_at, status, winner_mode, rules, banner |
| `contest_prizes` | id, contest_id, place, description |
| `referrals` | id, inviter_id, invitee_id (unique), status (`pending/confirmed/rejected/flagged`), confirmed_at, flag_reason |
| `points_ledger` | id, user_id, contest_id, amount (+/−), source (`referral/test/course/bonus/admin`), reference_id, reason, created_by, created_at |
| `teachers` | user_id, bio, is_active |
| `courses` | id, teacher_id, title, category, description, level, price, duration, schedule (jsonb: days, time), format, address, seats, starts_at, trial_available, banner, status |
| `course_enrollments` | id, course_id, user_id, name, phone, note, status, created_at, updated_at, contacted_at |
| `tests` | id, teacher_id, course_id, title, code (unique), question_count, options_count, answer_key (jsonb), file_id, time_limit, max_attempts, opens_at, closes_at, show_answers_mode, status |
| `test_attempts` | id, test_id, user_id, started_at, finished_at, score, correct_count, status |
| `test_answers` | attempt_id, question_no, chosen, is_correct |
| `post_drafts` | id, admin_id, topic, params (jsonb), variants (jsonb), chosen_variant, final_text, media, status |
| `channel_posts` | id, channel_id, draft_id, message_id, scheduled_at, published_at, status |
| `ai_logs` | id, provider, model, prompt_version, tokens_in, tokens_out, cost, status, created_at |
| `broadcasts` | id, admin_id, content, segment (jsonb), scheduled_at, status, sent, failed |
| `settings` | key, value (jsonb) — ball qiymatlari, limitlar, matnlar |
| `audit_logs` | id, actor_id, action, entity, entity_id, details (jsonb), created_at |
| `feedback`, `faq` | foydalanuvchi murojaatlari, tez-tez so'raladigan savollar |

Barcha jadvallarda: `created_at`, kerak joyda `updated_at`; Supabase **RLS yoqilgan**, bot faqat service-role kaliti bilan serverdan ishlaydi.

---

## 6. Kod strukturasi

```
everest-bot/
├── bot/
│   ├── handlers/
│   │   ├── start.py          # til, majburiy obuna, telefon
│   │   ├── referral.py       # link, kabinet, reyting
│   │   ├── contest.py
│   │   ├── test_taking.py    # o'quvchi oqimi
│   │   ├── test_manage.py    # teacher: yaratish/natijalar
│   │   ├── courses.py        # katalog va ariza
│   │   ├── teacher.py        # teacher panel
│   │   └── admin/            # stats, users, posts, broadcast, settings
│   ├── keyboards/
│   ├── states/               # FSM guruhlari
│   ├── services/             # biznes-logika: referral, points, tests, courses, ai_service, broadcast
│   ├── middlewares/          # xato ushlash, throttling, rol tekshiruvi, til
│   └── locales/              # uz.json, ru.json
├── prompts/                  # AI promptlar (versiyalangan)
├── db/migrations/
├── tests/
├── docker-compose.yml
└── .env.example
```

Qoidalar: bitta handler fayli = bitta mantiqiy oqim; bot faqat interfeys, ma'lumot manbai — Supabase; markaziy xato middleware; har FSM holatidan "⬅️ Orqaga / ❌ Bekor qilish"; texnik nomlar inglizcha, izohlar o'zbekcha.

---

## 7. Nofunksional talablar

| Yo'nalish | Talab |
| --- | --- |
| Xavfsizlik | Rol tekshiruvi har handlerda (middleware); kalitlar `.env`da; RLS; teacher faqat o'z ma'lumotiga kira oladi; admin amallari audit logda |
| Ishlash | Bir vaqtda kamida 500 faol foydalanuvchi; og'ir ishlar (broadcast, taymer, AI) fon vazifada |
| Ishonchlilik | FSM Redisda; test javoblari darrov DBga; fon vazifalar qayta ishga tushganda tiklanadi |
| Spamdan himoya | Throttling middleware, kod tanlashga urinish limiti |
| Ko'p tillilik | uz (default) + ru; fallback — o'zbekcha; matn ohangi `uz-ux-copywriting` bo'yicha |
| Monitoring | Xatolar Sentry/adminga alert; AI chaqiruvlar soni, xato darajasi, vaqti |
| Backup | Supabase kunlik backup; sozlamalar va matnlar eksport qilinadi |
| Maxfiylik | Rozilik, ma'lumotni o'chirish, ommaviy reytingda ismlar qisman yashiriladi |
| Deploy | Docker, webhook (nginx + HTTPS), `.env` orqali konfiguratsiya, CI orqali yangilash |

---

## 8. Bosqichlar (Roadmap)

| Faza | Mazmuni | Natija | Taxminiy muddat |
| --- | --- | --- | --- |
| **0. Poydevor** | Repo, Supabase sxemasi, aiogram skeleti, i18n, middlewarelar, rollar, Docker | Ishlaydigan bo'sh bot | 3–4 kun |
| **1. Referal + Konkurs (MVP-1)** | Start, majburiy obuna, telefon, referal, ball jurnali, anti-fraud, reyting, konkurs boshqaruvi, bot ichida asosiy statistika | **Konkursni boshlash mumkin** | 1.5–2 hafta |
| **2. Kurslar** | Teacher roli, kurs qo'shish, moderatsiya, katalog, ariza, o'qituvchiga bildirishnoma, ariza statuslari | Kurslarga yozilish ishlaydi | 1–1.5 hafta |
| **3. Testlar** | Test yaratish (kalit+fayl), kod bilan kirish, taymer, avto-tekshirish, natijalar, Excel | Testlar ishlaydi | 1.5–2 hafta |
| **4. AI postlar** | `ai_service` (Claude+Gemini fallback), 3–4 variant, tahrirlash, preview, joylash, rejalashtirish | Kanal uchun post generator | 1–1.5 hafta |
| **5. Kengaytirish** | Broadcast, kengaytirilgan statistika, web-dashboard, sertifikat, ball do'koni, promo-kod | To'liq platforma | 2–3 hafta |
| **6. Sinov va ishga tushirish** | Yuklama testi, xavfsizlik tekshiruvi, hujjatlar, o'qituvchilarga o'rgatish | Productionga chiqish | 1 hafta |

*Muddatlar taxminiy (bitta dasturchi uchun); aniq baho qarorlar tasdiqlangach beriladi. Konkurs shoshilinch bo'lsa — Faza 0 va 1 birinchi chiqariladi.*

---

## 9. Qabul qilish mezonlari (qisqacha)

- **Referal:** yangi foydalanuvchi link orqali kirib, kanalga obuna bo'lib, raqamini tasdiqlasa — taklif qiluvchiga ball tushadi va xabar boradi; o'zini o'zi taklif qilish va takroriy referal ishlamaydi.
- **Konkurs:** admin konkurs yaratadi, reyting real vaqtda yangilanadi, tugaganda g'oliblar to'g'ri aniqlanadi.
- **Test:** teacher test yaratadi va kod oladi; o'quvchi kod bilan kirib topshiradi; natija to'g'ri hisoblanadi; teacher Excel oladi; vaqt tugaganda avtomatik topshiriladi.
- **Kurs:** teacher kurs qo'shadi, admin tasdiqlaydi; foydalanuvchi ariza yuboradi; aynan shu kurs o'qituvchisiga ism, telefon va sana bilan xabar boradi.
- **AI post:** admin mavzu beradi, 3–4 variant oladi, tahrirlab tasdiqlaydi, post kanalga joylanadi (hozir yoki rejalashtirilgan vaqtda); AI ishlamasa fallback yoki tushunarli xabar chiqadi.
- **Admin:** statistika to'g'ri, ball qo'lda o'zgartirilsa audit logga yoziladi, broadcast segmentga yetib boradi.

---

## 10. Ochiq savollar (tasdiqlash kerak)

1. **Admin panel:** bot ichida / web / gibrid? *(tavsiya: gibrid, bosqichma-bosqich)*
2. **Ball hisobi:** har konkurs uchun alohida yoki umumiy balans? *(tavsiya: konkurs bo'yicha)*
3. **G'olib aniqlash:** Top-N, lotereya yoki ikkalasi?
4. **Bitta referal uchun necha ball** va referal qaysi shartlarda "tasdiqlangan" (obuna + telefon yetarlimi)?
5. **Kanaldan chiqib ketsa** ball bekor qilinsinmi?
6. **Test kiritish:** MVPda kalit + fayl yetarlimi?
7. **Kurs moderatsiyasi:** teacher qo'shgan kurs admin tasdig'isiz chiqsinmi?
8. **Kurslarga onlayn to'lov** (Payme/Click) kerakmi yoki faqat ariza?
9. **Nechta kanal** ulanadi va botga kanal admin huquqi berilishi mumkinmi?
10. **Tillar:** faqat o'zbekcha yetadimi yoki ruscha ham kerakmi?
11. **Hosting:** o'z VPS yoki Railway/Render kabi servis?
12. **Everest IT Center ma'lumotlari:** logotip, brend ranglari, filiallar/manzillar, aloqa raqamlari, dastlabki kurs va o'qituvchilar ro'yxati.

---

*Hujjat tasdiqlangach, har bir faza alohida vazifa fayllariga (agent-ready markdown) bo'linadi va bosqichma-bosqich amalga oshiriladi.*