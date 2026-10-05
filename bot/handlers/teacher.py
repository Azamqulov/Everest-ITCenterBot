import io
import json
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.services.db import db
from bot.services.test_service import test_service
from bot.services.course_service import course_service
from bot.keyboards.admin_kb import (
    get_teacher_menu_keyboard,
    get_enrollment_status_keyboard
)
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu_keyboard, get_skip_cancel_keyboard
from bot.states import TeacherTestStates, TeacherCourseStates
from bot.middlewares.role_auth import RoleFilter

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["🧑‍🏫 Teacher panel", "🧑‍🏫 Панель учителя"]))
async def handle_teacher_panel(message: Message, user_role: str, _: Any):
    if not RoleFilter.is_teacher(user_role, message.from_user.id):
        await message.answer(_("access_denied"))
        return

    await message.answer(
        "🧑‍🏫 <b>Everest IT Center — O'qituvchi boshqaruv paneli</b>\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_teacher_menu_keyboard(),
        parse_mode="HTML"
    )

# --- Test Creation FSM ---
@router.callback_query(F.data == "teacher:create_test")
async def handle_create_test_start(callback: CallbackQuery, state: FSMContext, user_role: str, _: Any):
    if not RoleFilter.is_teacher(user_role, callback.from_user.id):
        await callback.answer(_("access_denied"), show_alert=True)
        return

    await state.set_state(TeacherTestStates.waiting_title)
    await callback.message.answer(
        "📝 <b>Yangi test yaratish</b>\n\nTest nomini kiriting (masalan: <i>Python Asoslari 1-bosqich</i>):",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(TeacherTestStates.waiting_title)
async def handle_test_title(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    await state.update_data(title=message.text.strip())
    await state.set_state(TeacherTestStates.waiting_subject)
    await message.answer("Fan yoki yo'nalish nomini kiriting (masalan: <i>Backend</i>):", reply_markup=get_cancel_keyboard(_))

@router.message(TeacherTestStates.waiting_subject)
async def handle_test_subject(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    await state.update_data(subject=message.text.strip())
    await state.set_state(TeacherTestStates.waiting_question_count)
    await message.answer("Savollar sonini kiriting (masalan: <i>15</i>):", reply_markup=get_cancel_keyboard(_))

@router.message(TeacherTestStates.waiting_question_count)
async def handle_test_count(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("Iltimos, musbat butun son kiriting:")
        return

    count = int(message.text)
    await state.update_data(question_count=count)
    await state.set_state(TeacherTestStates.waiting_answer_key)
    await message.answer(
        f"🔑 <b>To'g'ri javoblar kalitini kiriting</b> ({count} ta savol uchun):\n\n"
        "Format: <code>1a 2c 3b 4d ...</code> yoki <code>1A2C3B4D</code>",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )

@router.message(TeacherTestStates.waiting_answer_key)
async def handle_test_key(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    data = await state.get_data()
    q_count = data["question_count"]
    key_dict = test_service.parse_answer_key(message.text, q_count)

    if len(key_dict) < q_count:
        await message.answer(
            f"⚠️ Siz {len(key_dict)} ta javob kiritdingiz, lekin savollar soni {q_count} ta bo'lishi kerak.\nIltimos, qaytadan to'liq kiriting:"
        )
        return

    await state.update_data(answer_key=key_dict)
    await state.set_state(TeacherTestStates.waiting_file)
    await message.answer(
        "📎 Test uchun PDF yoki rasm fayl yuklang (yoki 'O'tkazib yuborish' tugmasini bosing):",
        reply_markup=get_skip_cancel_keyboard(_)
    )

@router.message(TeacherTestStates.waiting_file)
async def handle_test_file(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id

    await state.update_data(file_id=file_id)
    await state.set_state(TeacherTestStates.waiting_time_limit)
    await message.answer(
        "⏱ Test uchun ajratiladigan vaqtni daqiqalarda kiriting (masalan: <i>30</i>):",
        reply_markup=get_cancel_keyboard(_)
    )

@router.message(TeacherTestStates.waiting_time_limit)
async def handle_test_time(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    time_limit = int(message.text) if message.text.isdigit() else 30
    data = await state.get_data()
    await state.clear()

    # Create test
    test = await test_service.create_test(
        teacher_id=message.from_user.id,
        title=data["title"],
        subject=data.get("subject"),
        question_count=data["question_count"],
        answer_key=data["answer_key"],
        file_id=data.get("file_id"),
        time_limit=time_limit
    )

    share_text = (
        f"📝 <b>Everest IT Center — Test e'lon qilindi!</b>\n\n"
        f"Fan: <b>{test['title']}</b>\n"
        f"Savollar soni: <b>{test['question_count']} ta</b>\n"
        f"Ajratilgan vaqt: <b>{test['time_limit']} daqiqa</b>\n\n"
        f"🔑 Test kodi: <code>{test['code']}</code>\n\n"
        f"Botga kiring: @{settings.BOT_USERNAME}\n"
        f"\"📝 Testlar\" bo'limini tanlab, yuqoridagi kodni kiriting va bilimingizni sinab ko'ring!"
    )

    await message.answer(
        f"🎉 <b>Test muvaffaqiyatli yaratildi!</b>\n\n"
        f"Test kodi: <code>{test['code']}</code>\n\n"
        f"O'quvchilar bilan ulashish uchun tayyor matn:\n\n{share_text}",
        reply_markup=get_main_menu_keyboard(_, role="teacher"),
        parse_mode="HTML"
    )

# --- Teacher: My Tests & Excel Export ---
@router.callback_query(F.data == "teacher:my_tests")
async def handle_teacher_my_tests(callback: CallbackQuery, _: Any):
    tests = await db.fetch_all("SELECT * FROM tests WHERE teacher_id = ? ORDER BY id DESC LIMIT 10", (callback.from_user.id,))
    if not tests:
        await callback.answer("Siz hali test yaratmagansiz.", show_alert=True)
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for t in tests:
        buttons.append([
            InlineKeyboardButton(text=f"📊 {t['title']} ({t['code']})", callback_data=f"teacher:test_stat:{t['id']}")
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="teacher:panel_back")])

    await callback.message.edit_text(
        "📋 <b>Siz yaratgan testlar:</b>\nStatistikani ko'rish va Excel eksport qilish uchun testni tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("teacher:test_stat:"))
async def handle_teacher_test_stat(callback: CallbackQuery, _: Any):
    test_id = int(callback.data.split(":")[2])
    test = await test_service.get_test_by_id(test_id)

    stats = await db.fetch_one("""
        SELECT 
            COUNT(*) as total_attempts,
            AVG(percentage) as avg_percent,
            MAX(score) as max_score
        FROM test_attempts 
        WHERE test_id = ? AND status = 'completed'
    """, (test_id,))

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 Excel natijalarni yuklash (.xlsx)", callback_data=f"teacher:export_excel:{test_id}")
        ],
        [
            InlineKeyboardButton(text="⬅️ Barcha testlarim", callback_data="teacher:my_tests")
        ]
    ])

    avg_p = round(stats["avg_percent"] or 0.0, 1)
    await callback.message.edit_text(
        f"📊 <b>{test['title']}</b> ({test['code']})\n\n"
        f"• Topshirganlar: <b>{stats['total_attempts']} nafar</b>\n"
        f"• O'rtacha natija: <b>{avg_p}%</b>\n"
        f"• Eng yuqori ball: <b>{stats['max_score'] or 0} ball</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("teacher:export_excel:"))
async def handle_export_excel(callback: CallbackQuery, _: Any):
    test_id = int(callback.data.split(":")[2])
    excel_bytes = await test_service.generate_excel_report(test_id)

    test = await test_service.get_test_by_id(test_id)
    doc = BufferedInputFile(excel_bytes, filename=f"test_{test['code']}_natijalar.xlsx")

    await callback.message.answer_document(
        document=doc,
        caption=f"📊 <b>{test['title']}</b> test natijalari jadvali."
    )
    await callback.answer()

# --- Teacher: Course Enrollments Management ---
@router.callback_query(F.data == "teacher:enrollments")
async def handle_teacher_enrollments(callback: CallbackQuery, _: Any):
    enrollments = await course_service.get_teacher_enrollments(callback.from_user.id)
    if not enrollments:
        await callback.answer("Kurslaringizga arizalar kelib tushmagan.", show_alert=True)
        return

    for e in enrollments[:5]:
        status_badges = {
            "yangi": "🟡 Yangi",
            "boglanildi": "🔵 Bog'lanildi",
            "yozildi": "🟢 Yozildi",
            "rad_etildi": "🔴 Rad etildi",
            "kutish_royxati": "🟠 Kutish ro'yxati"
        }
        badge = status_badges.get(e["status"], e["status"])

        text = (
            f"📩 <b>Ariza #{e['id']}</b> — {badge}\n"
            f"📚 Kurs: <b>{e['course_title']}</b>\n"
            f"👤 O'quvchi: <b>{e['name']}</b>\n"
            f"📞 Telefon: <code>{e['phone']}</code>\n"
            f"⏰ Vaqt: {e.get('preferred_time') or '—'}\n"
            f"📝 Izoh: {e.get('note') or '—'}\n"
            f"📅 Sana: {str(e['created_at'])[:16]}"
        )
        await callback.message.answer(
            text,
            reply_markup=get_enrollment_status_keyboard(e["id"]),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data.startswith("enroll_status:"))
async def handle_change_enroll_status(callback: CallbackQuery, _: Any):
    # format: enroll_status:id:status
    parts = callback.data.split(":")
    enrollment_id = int(parts[1])
    new_status = parts[2]

    await course_service.update_enrollment_status(enrollment_id, new_status)
    await callback.answer(f"Status yangilandi: {new_status}")
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

@router.callback_query(F.data == "teacher:panel_back")
async def handle_panel_back(callback: CallbackQuery, _: Any):
    await callback.message.edit_text(
        "🧑‍🏫 <b>Everest IT Center — O'qituvchi boshqaruv paneli</b>\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_teacher_menu_keyboard(),
        parse_mode="HTML"
    )
