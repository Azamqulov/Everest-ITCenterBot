import io
import json
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.services.db import db
from bot.services.test_service import test_service
from bot.keyboards.inline import (
    get_tests_menu_keyboard,
    get_test_start_keyboard,
    get_test_question_keyboard,
    get_my_created_tests_keyboard,
    get_test_creator_keyboard
)
from bot.keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard, get_skip_cancel_keyboard
from bot.states import StudentTestStates, UserTestCreationStates

logger = logging.getLogger(__name__)
router = Router()

# =====================================================================
# 1. MAIN TESTS MENU & NAVIGATION
# =====================================================================
@router.message(F.text.in_(["📝 Testlar", "📝 Тесты"]))
async def handle_tests_menu(message: Message, state: FSMContext, _: Any):
    await state.clear()
    await message.answer(
        _("tests_title"),
        reply_markup=get_tests_menu_keyboard(_),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "test:menu_back")
async def handle_test_menu_back(callback: CallbackQuery, state: FSMContext, _: Any):
    await state.clear()
    await callback.message.edit_text(
        _("tests_title"),
        reply_markup=get_tests_menu_keyboard(_),
        parse_mode="HTML"
    )
    await callback.answer()

# =====================================================================
# 2. USER TEST CREATION FLOW (ALL USERS CAN CREATE TESTS)
# =====================================================================
@router.callback_query(F.data == "test:create")
async def handle_create_test_prompt(callback: CallbackQuery, state: FSMContext, _: Any):
    await state.set_state(UserTestCreationStates.waiting_title)
    await callback.message.answer(
        "📝 <b>Yangi test yaratish</b>\n\n"
        "Test nomini kiriting (masalan: <i>Matematika 1-variant</i> yoki <i>Python Asoslari</i>):",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(UserTestCreationStates.waiting_title)
async def handle_test_title_input(message: Message, state: FSMContext, _: Any, user_role: str = "user"):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "Bekor qilish", "Отмена", "/cancel"]:
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role=user_role))
        return

    title = message.text.strip()
    await state.update_data(title=title)
    await state.set_state(UserTestCreationStates.waiting_answers)

    await message.answer(
        "🔑 <b>To'g'ri javoblar kalitini kiriting:</b>\n\n"
        "Format: <code>1a2b3d...</code> yoki <code>1a 2b 3d</code>\n"
        "<i>(Savollar soni kiritilgan javoblardan avtomatik aniqlanadi)</i>\n\n"
        "Masalan: <code>1a2b3c4d5a</code>",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )

@router.message(UserTestCreationStates.waiting_answers)
async def handle_test_answers_input(message: Message, state: FSMContext, _: Any, user_role: str = "user"):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "Bekor qilish", "Отмена", "/cancel"]:
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role=user_role))
        return

    answer_key = test_service.parse_answer_key(message.text)
    if not answer_key:
        await message.answer(
            "⚠️ Javoblar aniqlanmadi!\n\n"
            "Iltimos, javoblarni to'g'ri formatda kiriting, masalan: <code>1a2b3d...</code> yoki <code>1a 2b 3d</code>",
            parse_mode="HTML"
        )
        return

    q_count = len(answer_key)
    await state.update_data(answer_key=answer_key, question_count=q_count)
    await state.set_state(UserTestCreationStates.waiting_file)

    await message.answer(
        f"✅ <b>{q_count} ta savol</b> uchun to'g'ri javoblar qabul qilindi!\n\n"
        "📎 Endi test savollari faylini yuklang (PDF yoki rasm)\n"
        "<i>(Agar fayl bo'lmasa, '⏭ O'tkazib yuborish' tugmasini bosing):</i>",
        reply_markup=get_skip_cancel_keyboard(_),
        parse_mode="HTML"
    )

@router.message(UserTestCreationStates.waiting_file)
async def handle_test_file_input(message: Message, state: FSMContext, _: Any, user_role: str = "user"):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "Bekor qilish", "Отмена", "/cancel"]:
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role=user_role))
        return

    file_id = None
    if message.document:
        file_id = message.document.file_id
    elif message.photo:
        file_id = message.photo[-1].file_id

    await state.update_data(file_id=file_id)
    await state.set_state(UserTestCreationStates.waiting_time_limit)

    await message.answer(
        "⏱ <b>Test uchun ajratiladigan vaqt</b> (daqiqalarda, masalan: <code>30</code>):\n"
        "<i>(Yoki '⏭ O'tkazib yuborish' ni bosing — standart 30 daqiqa):</i>",
        reply_markup=get_skip_cancel_keyboard(_),
        parse_mode="HTML"
    )

@router.message(UserTestCreationStates.waiting_time_limit)
async def handle_test_time_limit_input(message: Message, state: FSMContext, _: Any, user_role: str = "user"):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "Bekor qilish", "Отмена", "/cancel"]:
        await state.clear()
        await message.answer("Amal bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role=user_role))
        return

    time_limit = 30
    if message.text and message.text != _("btn_skip") and message.text.isdigit():
        val = int(message.text)
        if val > 0:
            time_limit = val

    data = await state.get_data()
    await state.clear()

    # Create test in DB
    test = await test_service.create_test(
        teacher_id=message.from_user.id,
        title=data["title"],
        question_count=data["question_count"],
        answer_key=data["answer_key"],
        subject="Umumiy",
        options_count=4,
        time_limit=time_limit,
        max_attempts=1,
        file_id=data.get("file_id")
    )

    share_text = (
        f"📝 <b>{test['title']}</b> testiga taklif!\n"
        f"Botga kirib quyidagi kodni yuboring va testni topshiring:\n"
        f"<code>{test['code']}</code>"
    )

    success_msg = (
        f"🎉 <b>Test muvaffaqiyatli yaratildi!</b>\n\n"
        f"📋 Nomi: <b>{test['title']}</b>\n"
        f"🔑 Test kodi: <code>{test['code']}</code>\n"
        f"🔢 Savollar soni: <b>{test['question_count']} ta</b>\n"
        f"⏱ Vaqt: <b>{test['time_limit']} daqiqa</b>\n\n"
        f"📢 <b>Ushbu kodni ishtirokchilarga ulashing:</b>\n"
        f"<code>{test['code']}</code>\n\n"
        f"Ishtirokchilar testni yechib yakunlashi bilanoq, sizga kimlar qatnashgani, ballari va o'rinlari haqida hisobot boradi!"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="↗️ Do'stlarga ulashish", switch_inline_query=test['code']),
            InlineKeyboardButton(text="📊 Natijalar (Reyting)", callback_data=f"test_creator_view:{test['id']}")
        ],
        [
            InlineKeyboardButton(text="📁 Mening testlarim", callback_data="test:my_created"),
            InlineKeyboardButton(text="⬅️ Test menyusi", callback_data="test:menu_back")
        ]
    ])

    await message.answer(
        success_msg,
        reply_markup=get_main_menu_keyboard(_, role=user_role),
        parse_mode="HTML"
    )
    await message.answer("Testni boshqarish paneli:", reply_markup=kb)

# =====================================================================
# 3. MY CREATED TESTS DASHBOARD & LEADERBOARD
# =====================================================================
@router.callback_query(F.data == "test:my_created")
async def handle_my_created_tests(callback: CallbackQuery, _: Any):
    user_id = callback.from_user.id
    tests = await test_service.get_my_created_tests(user_id)

    if not tests:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi test yaratish", callback_data="test:create")],
            [InlineKeyboardButton(text="⬅️ Test menyusi", callback_data="test:menu_back")]
        ])
        await callback.message.edit_text(
            "📁 Siz hali birorta ham test yaratmadingiz.\n\n"
            "O'z do'stlaringiz yoki o'quvchilaringiz uchun test yaratish uchun quyidagi tugmani bosing:",
            reply_markup=kb
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "📁 <b>Siz yaratgan testlar ro'yxati:</b>\n\n"
        "Natijalar, reyting va Excel hisobotni ko'rish uchun testni tanlang:",
        reply_markup=get_my_created_tests_keyboard(tests),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("test_creator_view:"))
async def handle_creator_view_test(callback: CallbackQuery, _: Any):
    test_id = int(callback.data.split(":")[1])
    test = await test_service.get_test_by_id(test_id)
    if not test:
        await callback.answer("Test topilmadi.", show_alert=True)
        return

    leaderboard = await test_service.get_test_leaderboard(test_id)
    is_closed = test.get("status") == "closed"
    status_text = "🔴 Yakunlangan (yopilgan)" if is_closed else "🟢 Faol (topshirish mumkin)"

    text = (
        f"📋 <b>{test['title']}</b> (<code>{test['code']}</code>)\n\n"
        f"• Holati: <b>{status_text}</b>\n"
        f"• Savollar soni: <b>{test['question_count']} ta</b>\n"
        f"• Ajratilgan vaqt: <b>{test['time_limit']} daqiqa</b>\n"
        f"• Jami qatnashganlar: <b>{len(leaderboard)} nafar</b>\n\n"
        f"Quyidagi tugmalar orqali qatnashchilar reytingini ko'rishingiz yoki Excel yuklab olishingiz mumkin:"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_test_creator_keyboard(test_id, is_closed=is_closed),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("test_results:"))
async def handle_view_test_leaderboard(callback: CallbackQuery, _: Any):
    test_id = int(callback.data.split(":")[1])
    test = await test_service.get_test_by_id(test_id)
    if not test:
        await callback.answer("Test topilmadi.", show_alert=True)
        return

    leaderboard = await test_service.get_test_leaderboard(test_id)
    ranking_text = test_service.format_leaderboard(test, leaderboard)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Excel hisobot yuklash", callback_data=f"test_excel:{test_id}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"test_creator_view:{test_id}")]
    ])

    await callback.message.edit_text(ranking_text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("test_excel:"))
async def handle_download_test_excel(callback: CallbackQuery, _: Any):
    test_id = int(callback.data.split(":")[1])
    test = await test_service.get_test_by_id(test_id)
    if not test:
        await callback.answer("Test topilmadi.", show_alert=True)
        return

    excel_bytes = await test_service.generate_excel_report(test_id)
    filename = f"Test_{test['code']}_Natijalari.xlsx"
    doc = BufferedInputFile(excel_bytes, filename=filename)

    await callback.message.answer_document(
        document=doc,
        caption=f"📊 <b>{test['title']}</b> ({test['code']}) testi ishtirokchilari hisoboti"
    )
    await callback.answer("Excel hisobot yuborildi!")

@router.callback_query(F.data.startswith("test_close:"))
async def handle_close_test(callback: CallbackQuery, _: Any):
    test_id = int(callback.data.split(":")[1])
    success = await test_service.close_test(test_id, callback.from_user.id)
    if not success:
        await callback.answer("Testni yopish huquqi faqat uning yaratuvchisida!", show_alert=True)
        return

    test = await test_service.get_test_by_id(test_id)
    leaderboard = await test_service.get_test_leaderboard(test_id)
    ranking_text = test_service.format_leaderboard(test, leaderboard)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Yakuniy Excel hisobot", callback_data=f"test_excel:{test_id}")],
        [InlineKeyboardButton(text="⬅️ Mening testlarim", callback_data="test:my_created")]
    ])

    msg = f"🏁 <b>Test rasman yakunlandi va yopildi!</b>\n\nYangi topshirishlar qabul qilinmaydi.\n\n{ranking_text}"
    await callback.message.edit_text(msg, reply_markup=kb, parse_mode="HTML")
    await callback.answer("Test yopildi!", show_alert=True)

# =====================================================================
# 4. TAKING TEST (STUDENT ENTER CODE & SOLVE)
# =====================================================================
@router.callback_query(F.data == "test:enter_code")
async def handle_enter_code_prompt(callback: CallbackQuery, state: FSMContext, _: Any):
    await state.set_state(StudentTestStates.entering_code)
    await callback.message.answer(
        _("prompt_enter_test_code"),
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(StudentTestStates.entering_code)
async def handle_test_code_input(message: Message, state: FSMContext, bot: Bot, _: Any, user_role: str = "user"):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "Bekor qilish", "Отмена", "/cancel"]:
        await state.clear()
        await message.answer("Test bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role=user_role))
        return

    code = message.text.strip().upper()
    test = await test_service.get_test_by_code(code)

    if not test:
        await message.answer(_("test_code_not_found"))
        return

    await state.clear()

    # Send attached file if exists
    if test.get("file_id"):
        try:
            await bot.send_document(
                chat_id=message.chat.id,
                document=test["file_id"],
                caption=f"📄 {test['title']} materiali"
            )
        except Exception as e:
            logger.warning(f"Could not send test document: {e}")

    info_text = _(
        "test_info",
        title=test["title"],
        subject=test.get("subject") or "Umumiy",
        count=test["question_count"],
        time_limit=test["time_limit"],
        max_attempts=test["max_attempts"]
    )

    await message.answer(
        info_text,
        reply_markup=get_test_start_keyboard(_, test_id=test["id"]),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("test_start:"))
async def handle_test_start(callback: CallbackQuery, state: FSMContext, _: Any):
    test_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    attempt, status_msg = await test_service.start_attempt(test_id, user_id)
    if not attempt:
        await callback.answer(status_msg, show_alert=True)
        return

    attempt_id = attempt["id"]
    test = await test_service.get_test_by_id(test_id)
    user_answers = await test_service.get_user_answers(attempt_id)

    await state.set_state(StudentTestStates.taking_test)
    await state.update_data(attempt_id=attempt_id, test_id=test_id)

    kb = get_test_question_keyboard(
        test_id=test_id,
        attempt_id=attempt_id,
        total_q=test["question_count"],
        current_page=1,
        user_answers=user_answers,
        options_count=test.get("options_count", 4)
    )

    instructions = (
        f"⏱ <b>{test['title']}</b> testi boshlandi!\n"
        f"Ajratilgan vaqt: <b>{test['time_limit']} daqiqa</b>.\n\n"
        "Javoblarni pastdagi tugmalar orqali belgilang <b>YOKI</b> to'g'ridan-to'g'ri bitta matn qilib yuboring:\n"
        "Format: <code>1a2b3d...</code> yoki <code>1a 2b 3d</code>"
    )

    await callback.message.edit_text(instructions, reply_markup=kb, parse_mode="HTML")

# Text-based bulk answer submission
@router.message(StudentTestStates.taking_test)
async def handle_student_text_answers(message: Message, state: FSMContext, _: Any, user_role: str = "user"):
    if message.text in ["❌ Bekor qilish", "❌ Отмена", "Bekor qilish", "Отмена", "/cancel"]:
        await state.clear()
        await message.answer("Test bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role=user_role))
        return

    data = await state.get_data()
    attempt_id = data.get("attempt_id")
    test_id = data.get("test_id")
    if not attempt_id or not test_id:
        await state.clear()
        return

    test = await test_service.get_test_by_id(test_id)
    if not test:
        await state.clear()
        return

    parsed = test_service.parse_answer_key(message.text, test["question_count"])
    if not parsed:
        await message.answer(
            "⚠️ Javoblar formati tushunarsiz.\n\n"
            "Iltimos, javoblarni <code>1a2b3c...</code> yoki <code>1a 2b 3c</code> formatida yuboring yoki variant tugmalaridan foydalaning.",
            parse_mode="HTML"
        )
        return

    for q_no, opt in parsed.items():
        await test_service.save_answer(attempt_id, q_no, opt)

    user_answers = await test_service.get_user_answers(attempt_id)
    kb = get_test_question_keyboard(
        test_id=test_id,
        attempt_id=attempt_id,
        total_q=test["question_count"],
        current_page=1,
        user_answers=user_answers,
        options_count=test.get("options_count", 4)
    )

    await message.answer(
        f"✅ <b>{len(parsed)} ta javob saqlandi!</b>\n\n"
        f"Jami belgilangan: <b>{len(user_answers)}/{test['question_count']} ta</b>.\n\n"
        f"Testni yakunlash uchun pastdagi <b>'✅ Testni yakunlash'</b> tugmasini bosing:",
        reply_markup=kb,
        parse_mode="HTML"
    )

# Button-based answer submission
@router.callback_query(F.data.startswith("ans:"))
async def handle_answer_option(callback: CallbackQuery, _: Any):
    parts = callback.data.split(":")
    attempt_id = int(parts[1])
    q_no = int(parts[2])
    opt = parts[3]
    current_page = int(parts[4])

    await test_service.save_answer(attempt_id, q_no, opt)

    attempt = await db.fetch_one("SELECT test_id FROM test_attempts WHERE id = ?", (attempt_id,))
    if not attempt:
        await callback.answer()
        return

    test = await test_service.get_test_by_id(attempt["test_id"])
    user_answers = await test_service.get_user_answers(attempt_id)

    kb = get_test_question_keyboard(
        test_id=test["id"],
        attempt_id=attempt_id,
        total_q=test["question_count"],
        current_page=current_page,
        user_answers=user_answers,
        options_count=test.get("options_count", 4)
    )

    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await callback.answer(f"{q_no}-savol: {opt} tanlandi")

@router.callback_query(F.data.startswith("test_page:"))
async def handle_test_page_navigation(callback: CallbackQuery, _: Any):
    parts = callback.data.split(":")
    attempt_id = int(parts[1])
    page = int(parts[2])

    attempt = await db.fetch_one("SELECT test_id FROM test_attempts WHERE id = ?", (attempt_id,))
    test = await test_service.get_test_by_id(attempt["test_id"])
    user_answers = await test_service.get_user_answers(attempt_id)

    kb = get_test_question_keyboard(
        test_id=test["id"],
        attempt_id=attempt_id,
        total_q=test["question_count"],
        current_page=page,
        user_answers=user_answers,
        options_count=test.get("options_count", 4)
    )

    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()

# Finish attempt & notify test creator
@router.callback_query(F.data.startswith("test_finish:"))
async def handle_test_finish(callback: CallbackQuery, state: FSMContext, bot: Bot, _: Any):
    attempt_id = int(callback.data.split(":")[1])
    result = await test_service.finish_attempt(attempt_id)
    await state.clear()

    test = await test_service.get_test_by_id(result["test_id"])
    user_answers = await test_service.get_user_answers(attempt_id)
    raw_key = test["answer_key"]
    key = json.loads(raw_key) if isinstance(raw_key, str) else raw_key

    detail_lines = []
    for q in range(1, test["question_count"] + 1):
        target = str(key.get(str(q)) or key.get(q) or "").upper()
        chosen = str(user_answers.get(q) or "—").upper()
        if chosen == target:
            detail_lines.append(f"{q}. {chosen} ✅")
        else:
            detail_lines.append(f"{q}. {chosen} ❌ (To'g'ri: {target})")

    answers_detail = "\n<b>Javoblar tahlili:</b>\n" + ", ".join(detail_lines) if test.get("show_answers_mode") == "immediate" else ""

    summary_text = _(
        "test_result_summary",
        title=result.get("test_title", "Test"),
        correct=result["correct_count"],
        total=result["total_questions"],
        percentage=result["percentage"],
        score=result["score"],
        answers_detail=answers_detail
    )

    await callback.message.edit_text(summary_text, parse_mode="HTML")
    await callback.answer("Test yakunlandi!", show_alert=True)

    # NOTIFY TEST CREATOR WITH PARTICIPANT RANK AND LEADERBOARD
    creator_id = test.get("teacher_id")
    if creator_id and creator_id != callback.from_user.id:
        try:
            leaderboard = await test_service.get_test_leaderboard(test["id"])
            student_rank = next((idx for idx, item in enumerate(leaderboard, 1) if item["user_id"] == callback.from_user.id), 1)

            # Build top 5
            top_lines = []
            medals = ["🥇", "🥈", "🥉"]
            for idx, item in enumerate(leaderboard[:5], 1):
                badge = medals[idx - 1] if idx <= 3 else f"{idx}."
                top_lines.append(f"{badge} <b>{item['full_name']}</b> — {item['correct_count']}/{item['total_questions']} ({item['score']} ball)")

            leaders_block = "\n".join(top_lines)

            creator_msg = (
                f"🔔 <b>Siz yaratgan testni yangi ishtirokchi yakunladi!</b>\n\n"
                f"📋 Test: <b>{test['title']}</b> (<code>{test['code']}</code>)\n"
                f"👤 Ishtirokchi: <b>{callback.from_user.full_name}</b>\n"
                f"📊 Natijasi: <b>{result['correct_count']}/{result['total_questions']} ({result['percentage']}%)</b> — <b>+{result['score']} ball</b>\n"
                f"🏅 O'rni: <b>{student_rank}-o'rin</b>\n\n"
                f"🏆 <b>Joriy Top reyting:</b>\n{leaders_block}\n\n"
                f"👥 Jami qatnashganlar: <b>{len(leaderboard)} nafar</b>"
            )

            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            creator_kb = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 To'liq reyting", callback_data=f"test_results:{test['id']}"),
                    InlineKeyboardButton(text="📥 Excel hisobot", callback_data=f"test_excel:{test['id']}")
                ],
                [
                    InlineKeyboardButton(text="🏁 Testni yakunlash / yopish", callback_data=f"test_close:{test['id']}")
                ]
            ])

            await bot.send_message(
                chat_id=creator_id,
                text=creator_msg,
                reply_markup=creator_kb,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify test creator {creator_id}: {e}")

@router.callback_query(F.data == "test:my_results")
async def handle_my_test_results(callback: CallbackQuery, _: Any):
    user_id = callback.from_user.id
    attempts = await db.fetch_all("""
        SELECT ta.*, t.title, t.code
        FROM test_attempts ta
        JOIN tests t ON t.id = ta.test_id
        WHERE ta.user_id = ? AND ta.status = 'completed'
        ORDER BY ta.finished_at DESC
        LIMIT 10
    """, (user_id,))

    if not attempts:
        await callback.answer("Siz hali birorta ham test topshirmagansiz.", show_alert=True)
        return

    items = []
    for idx, att in enumerate(attempts, start=1):
        items.append(
            f"{idx}. <b>{att['title']}</b> ({att['code']})\n"
            f"   Natija: {att['correct_count']}/{att['total_questions']} ({att['percentage']}%) — <b>+{att['score']} ball</b>"
        )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Test menyusi", callback_data="test:menu_back")]
    ])

    await callback.message.edit_text(
        "📊 <b>Sizning so'nggi test natijalaringiz:</b>\n\n" + "\n\n".join(items),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()
