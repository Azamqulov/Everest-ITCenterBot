import json
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.services.db import db
from bot.services.course_service import course_service
from bot.keyboards.inline import (
    get_courses_categories_keyboard,
    get_courses_list_keyboard,
    get_course_detail_keyboard,
    get_confirm_enroll_keyboard
)
from bot.keyboards.reply import get_skip_cancel_keyboard, get_main_menu_keyboard
from bot.states import CourseEnrollStates
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["📚 Kurslar", "📚 Курсы"]))
async def handle_courses_menu(message: Message, _: Any):
    categories = await course_service.get_categories()
    if not categories:
        await message.answer("Hozircha kurslar mavjud emas.")
        return

    await message.answer(
        _("courses_title"),
        reply_markup=get_courses_categories_keyboard(categories)
    )

@router.callback_query(F.data == "courses:all_cats")
async def handle_all_categories(callback: CallbackQuery, _: Any):
    categories = await course_service.get_categories()
    await callback.message.edit_text(
        _("courses_title"),
        reply_markup=get_courses_categories_keyboard(categories)
    )

@router.callback_query(F.data.startswith("cat:"))
async def handle_category_select(callback: CallbackQuery, _: Any):
    category = callback.data.split(":", 1)[1]
    courses = await course_service.get_courses_by_category(category)

    if not courses:
        await callback.answer("Ushbu kategoriyada hozircha kurslar yo'q.", show_alert=True)
        return

    await callback.message.edit_text(
        f"📂 <b>{category}</b> yo'nalishidagi kurslar:",
        reply_markup=get_courses_list_keyboard(courses),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("course:"))
async def handle_course_detail(callback: CallbackQuery, _: Any):
    course_id = int(callback.data.split(":")[1])
    c = await course_service.get_course_by_id(course_id)

    if not c:
        await callback.answer("Kurs topilmadi.", show_alert=True)
        return

    # Parse schedule
    schedule_data = c.get("schedule")
    sched_text = ""
    if isinstance(schedule_data, str):
        try:
            schedule_data = json.loads(schedule_data)
        except Exception:
            sched_text = schedule_data

    if isinstance(schedule_data, dict):
        days = ", ".join(schedule_data.get("days", []))
        time = schedule_data.get("time", "")
        sched_text = f"{days} ({time})" if days else time

    # Format price with thousands separator (Uzbekistan business convention)
    price_formatted = f"{c['price']:,}".replace(",", " ")

    msg = _(
        "course_details",
        title=c["title"],
        level=c["level"],
        description=c["description"],
        price=price_formatted,
        duration=c["duration"],
        schedule=sched_text or "Kelishiladi",
        format=c["format"],
        address=c["address"] or "Markaz binosida",
        teacher_name=c.get("teacher_name") or "Markaz mentori"
    )

    await callback.message.edit_text(
        msg,
        reply_markup=get_course_detail_keyboard(_, course_id=course_id),
        parse_mode="HTML"
    )

# Enrollment FSM flow
@router.callback_query(F.data.startswith("enroll:"))
async def handle_enroll_start(callback: CallbackQuery, state: FSMContext, _: Any):
    course_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    # Check if already active application exists
    has_active = await course_service.check_active_enrollment(course_id, user_id)
    if has_active:
        await callback.answer(_("enroll_already_exists"), show_alert=True)
        return

    user = await db.fetch_one("SELECT full_name, phone FROM users WHERE telegram_id = ?", (user_id,))
    await state.update_data(
        course_id=course_id,
        name=user.get("full_name") or callback.from_user.full_name or "",
        phone=user.get("phone") or ""
    )

    await state.set_state(CourseEnrollStates.waiting_name)
    await callback.message.answer(
        _("enroll_name_prompt"),
        reply_markup=get_skip_cancel_keyboard(_)
    )
    await callback.answer()

@router.message(CourseEnrollStates.waiting_name)
async def handle_enroll_name(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Ariza bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    name = message.text if message.text != _("btn_skip") else (await state.get_data()).get("name")
    await state.update_data(name=name)

    await state.set_state(CourseEnrollStates.waiting_age)
    await message.answer(_("enroll_age_prompt"), reply_markup=get_skip_cancel_keyboard(_))

@router.message(CourseEnrollStates.waiting_age)
async def handle_enroll_age(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Ariza bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    age = None
    if message.text != _("btn_skip") and message.text.isdigit():
        age = int(message.text)
    await state.update_data(age=age)

    await state.set_state(CourseEnrollStates.waiting_time)
    await message.answer(_("enroll_time_prompt"), reply_markup=get_skip_cancel_keyboard(_))

@router.message(CourseEnrollStates.waiting_time)
async def handle_enroll_time(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Ariza bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    pref_time = message.text if message.text != _("btn_skip") else "Ixtiyoriy"
    await state.update_data(preferred_time=pref_time)

    await state.set_state(CourseEnrollStates.waiting_note)
    await message.answer(_("enroll_note_prompt"), reply_markup=get_skip_cancel_keyboard(_))

@router.message(CourseEnrollStates.waiting_note)
async def handle_enroll_note(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Ariza bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
        return

    note = message.text if message.text != _("btn_skip") else ""
    await state.update_data(note=note)

    data = await state.get_data()
    await state.set_state(CourseEnrollStates.confirm_enroll)

    confirm_msg = _(
        "enroll_confirm",
        name=data.get("name") or "—",
        phone=data.get("phone") or "—",
        age=data.get("age") or "Ko'rsatilmadi",
        time=data.get("preferred_time") or "Ixtiyoriy",
        note=data.get("note") or "Mavjud emas"
    )

    await message.answer(
        confirm_msg,
        reply_markup=get_confirm_enroll_keyboard(_),
        parse_mode="HTML"
    )

@router.callback_query(CourseEnrollStates.confirm_enroll, F.data.startswith("enroll_action:"))
async def handle_enroll_decision(callback: CallbackQuery, state: FSMContext, bot: Bot, _: Any):
    decision = callback.data.split(":")[1]
    if decision == "cancel":
        await state.clear()
        await callback.message.edit_text("Ariza bekor qilindi.")
        return

    data = await state.get_data()
    course_id = data["course_id"]
    user_id = callback.from_user.id

    enrollment = await course_service.create_enrollment(
        course_id=course_id,
        user_id=user_id,
        name=data.get("name") or callback.from_user.full_name,
        phone=data.get("phone") or "",
        age=data.get("age"),
        preferred_time=data.get("preferred_time"),
        note=data.get("note")
    )
    await state.clear()

    await callback.message.edit_text(_("enroll_success"), parse_mode="HTML")

    # Send notification to teacher and admin
    teacher_id = enrollment.get("teacher_id")
    notification_text = (
        f"📩 <b>Yangi kurs arizasi!</b>\n\n"
        f"📚 Kurs: <b>{enrollment.get('course_title')}</b>\n"
        f"👤 O'quvchi: <b>{data.get('name')}</b>\n"
        f"📞 Telefon: <code>{data.get('phone')}</code>\n"
        f"🌐 Telegram: @{callback.from_user.username or 'yo\'q'}\n"
        f"🎂 Yosh: {data.get('age') or '—'}\n"
        f"⏰ Qulay vaqt: {data.get('preferred_time') or '—'}\n"
        f"📝 Izoh: {data.get('note') or '—'}\n\n"
        f"Iltimos, 24 soat ichida o'quvchi bilan bog'laning."
    )

    targets = set()
    if teacher_id:
        targets.add(teacher_id)
    for sa in settings.superadmin_list:
        targets.add(sa)

    for target_id in targets:
        try:
            await bot.send_message(chat_id=target_id, text=notification_text, parse_mode="HTML")
        except Exception as e:
            logger.warning(f"Could not notify target {target_id} about enrollment: {e}")
