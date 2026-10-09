from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Callable, List, Dict, Any

def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="set_lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang:ru")
            ]
        ]
    )

def get_consent_keyboard(_: Callable[[str], str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("btn_consent"), callback_data="consent:yes"),
                InlineKeyboardButton(text=_("btn_reject_consent"), callback_data="consent:no")
            ]
        ]
    )

def get_channel_sub_keyboard(_: Callable[[str], str], channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['title']}", url=ch['link'])])
    buttons.append([InlineKeyboardButton(text=_("btn_check_sub"), callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_referral_keyboard(_: Callable[[str], str], share_text: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("btn_share_ref"),
                    switch_inline_query=share_text
                )
            ],
            [
                InlineKeyboardButton(text=_("btn_my_friends"), callback_data="ref:my_friends")
            ]
        ]
    )

def get_contest_keyboard(_: Callable[[str], str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("btn_leaderboard"), callback_data="contest:leaderboard")
            ]
        ]
    )

def get_tests_menu_keyboard(_: Callable[[str], str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yangi test yaratish", callback_data="test:create"),
                InlineKeyboardButton(text=_("btn_enter_test_code"), callback_data="test:enter_code")
            ],
            [
                InlineKeyboardButton(text="📁 Mening testlarim", callback_data="test:my_created"),
                InlineKeyboardButton(text=_("btn_my_test_results"), callback_data="test:my_results")
            ]
        ]
    )

def get_my_created_tests_keyboard(tests: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = []
    for t in tests:
        status_icon = "🟢" if t.get("status") == "published" else "🔴"
        attempts_cnt = t.get("attempts_count", 0)
        btn_text = f"{status_icon} {t['title']} ({t['code']}) — {attempts_cnt} kishi"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"test_creator_view:{t['id']}")])
    rows.append([InlineKeyboardButton(text="➕ Yangi test yaratish", callback_data="test:create")])
    rows.append([InlineKeyboardButton(text="⬅️ Test menyusi", callback_data="test:menu_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_test_creator_keyboard(test_id: int, is_closed: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📊 Natijalar (Reyting)", callback_data=f"test_results:{test_id}"),
            InlineKeyboardButton(text="📥 Excel hisobot", callback_data=f"test_excel:{test_id}")
        ]
    ]
    if not is_closed:
        rows.append([
            InlineKeyboardButton(text="🏁 Testni yakunlash / yopish", callback_data=f"test_close:{test_id}")
        ])
    rows.append([
        InlineKeyboardButton(text="⬅️ Mening testlarim", callback_data="test:my_created")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_test_start_keyboard(_: Callable[[str], str], test_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("btn_start_test"), callback_data=f"test_start:{test_id}")
            ]
        ]
    )

def get_test_question_keyboard(
    test_id: int,
    attempt_id: int,
    total_q: int,
    current_page: int,
    user_answers: Dict[int, str],
    options_count: int = 4
) -> InlineKeyboardMarkup:
    """Build an interactive 10-questions per page answer pad."""
    page_size = 10
    start_q = (current_page - 1) * page_size + 1
    end_q = min(total_q, current_page * page_size)

    options_letters = ["A", "B", "C", "D", "E"][:options_count]
    rows = []

    for q in range(start_q, end_q + 1):
        chosen = user_answers.get(q)
        q_row = [InlineKeyboardButton(text=f"{q}.", callback_data="noop")]
        for opt in options_letters:
            is_selected = chosen == opt
            label = f"✅ {opt}" if is_selected else opt
            q_row.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"ans:{attempt_id}:{q}:{opt}:{current_page}"
                )
            )
        rows.append(q_row)

    # Pagination buttons
    nav_row = []
    total_pages = (total_q + page_size - 1) // page_size
    if current_page > 1:
        nav_row.append(
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"test_page:{attempt_id}:{current_page - 1}")
        )
    if current_page < total_pages:
        nav_row.append(
            InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"test_page:{attempt_id}:{current_page + 1}")
        )
    if nav_row:
        rows.append(nav_row)

    # Finish button
    rows.append([
        InlineKeyboardButton(text="✅ Testni yakunlash", callback_data=f"test_finish:{attempt_id}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_courses_categories_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for cat in categories:
        rows.append([InlineKeyboardButton(text=f"📂 {cat}", callback_data=f"cat:{cat}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_courses_list_keyboard(courses: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    rows = []
    for c in courses:
        rows.append([InlineKeyboardButton(text=f"📖 {c['title']}", callback_data=f"course:{c['id']}")])
    rows.append([InlineKeyboardButton(text="⬅️ Barcha kategoriyalar", callback_data="courses:all_cats")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def get_course_detail_keyboard(_: Callable[[str], str], course_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("btn_enroll"), callback_data=f"enroll:{course_id}")
            ],
            [
                InlineKeyboardButton(text=_("btn_back"), callback_data="courses:all_cats")
            ]
        ]
    )

def get_confirm_enroll_keyboard(_: Callable[[str], str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("btn_confirm_enroll"), callback_data="enroll_action:confirm"),
                InlineKeyboardButton(text=_("btn_cancel"), callback_data="enroll_action:cancel")
            ]
        ]
    )
