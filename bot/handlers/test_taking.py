import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.services.db import db
from bot.services.test_service import test_service
from bot.keyboards.inline import (
    get_tests_menu_keyboard,
    get_test_start_keyboard,
    get_test_question_keyboard
)
from bot.keyboards.reply import get_main_menu_keyboard, get_cancel_keyboard
from bot.states import StudentTestStates

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["📝 Testlar", "📝 Тесты"]))
async def handle_tests_menu(message: Message, _: Any):
    await message.answer(
        _("tests_title"),
        reply_markup=get_tests_menu_keyboard(_),
        parse_mode="HTML"
    )

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
async def handle_test_code_input(message: Message, state: FSMContext, bot: Bot, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Test bekor qilindi.", reply_markup=get_main_menu_keyboard(_))
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

    await callback.message.edit_text(
        _(
            "test_started",
            time_limit=test["time_limit"]
        ),
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("ans:"))
async def handle_answer_option(callback: CallbackQuery, _: Any):
    # format: ans:attempt_id:q:opt:current_page
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

@router.callback_query(F.data.startswith("test_finish:"))
async def handle_test_finish(callback: CallbackQuery, state: FSMContext, _: Any):
    attempt_id = int(callback.data.split(":")[1])
    result = await test_service.finish_attempt(attempt_id)
    await state.clear()

    summary_text = _(
        "test_result_summary",
        title=result.get("test_title", "Test"),
        correct=result["correct_count"],
        total=result["total_questions"],
        percentage=result["percentage"],
        score=result["score"],
        answers_detail=""
    )

    await callback.message.edit_text(summary_text, parse_mode="HTML")
    await callback.answer("Test yakunlandi!", show_alert=True)

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

    await callback.message.answer(
        "📊 <b>Sizning so'nggi test natijalaringiz:</b>\n\n" + "\n\n".join(items),
        parse_mode="HTML"
    )
    await callback.answer()
