import pytest
import json
import os

from bot.middlewares.i18n import i18n
from bot.keyboards.reply import get_main_menu_keyboard, get_phone_keyboard
from bot.keyboards.inline import (
    get_language_keyboard,
    get_test_question_keyboard,
    get_courses_categories_keyboard
)
from bot.middlewares.role_auth import RoleFilter
from bot.config import settings

def test_i18n_files_structure():
    locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot", "locales")
    with open(os.path.join(locales_dir, "uz.json"), "r", encoding="utf-8") as f:
        uz_data = json.load(f)
    with open(os.path.join(locales_dir, "ru.json"), "r", encoding="utf-8") as f:
        ru_data = json.load(f)

    # All keys in uz should also exist in ru
    missing_in_ru = set(uz_data.keys()) - set(ru_data.keys())
    assert len(missing_in_ru) == 0, f"Missing keys in ru.json: {missing_in_ru}"

    # Check some critical keys
    assert "welcome" in uz_data
    assert "mandatory_sub_title" in uz_data
    assert "btn_send_phone" in uz_data
    assert "referral_title" in uz_data
    assert "tests_title" in uz_data

def test_keyboards_generation():
    _ = lambda k, **kw: k
    # Main menu for user
    kb_user = get_main_menu_keyboard(_, role="user")
    user_buttons = [b.text for row in kb_user.keyboard for b in row]
    assert "menu_contest" in user_buttons
    assert "menu_teacher" not in user_buttons
    assert "menu_admin" not in user_buttons

    # Main menu for teacher
    kb_teacher = get_main_menu_keyboard(_, role="teacher")
    teacher_buttons = [b.text for row in kb_teacher.keyboard for b in row]
    assert "menu_teacher" in teacher_buttons
    assert "menu_admin" not in teacher_buttons

    # Main menu for admin
    kb_admin = get_main_menu_keyboard(_, role="admin")
    admin_buttons = [b.text for row in kb_admin.keyboard for b in row]
    assert "menu_teacher" in admin_buttons
    assert "menu_admin" in admin_buttons

def test_test_question_pagination_keyboard():
    user_answers = {1: "A", 2: "C"}
    kb = get_test_question_keyboard(
        test_id=1,
        attempt_id=10,
        total_q=25,
        current_page=1,
        user_answers=user_answers,
        options_count=4
    )
    # Check that rows exist for questions 1 to 10
    assert len(kb.inline_keyboard) > 10

def test_role_filter():
    settings.SUPERADMIN_IDS = "999888,111222"
    assert RoleFilter.is_superadmin(999888) is True
    assert RoleFilter.is_superadmin(12345) is False
    assert RoleFilter.is_admin("admin", 12345) is True
    assert RoleFilter.is_admin("user", 12345) is False
    assert RoleFilter.is_admin("user", 999888) is True
    assert RoleFilter.is_teacher("teacher", 12345) is True
    assert RoleFilter.is_teacher("user", 12345) is False
