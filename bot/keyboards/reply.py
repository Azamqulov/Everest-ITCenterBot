from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from typing import Callable

def get_phone_keyboard(_: Callable[[str], str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("btn_send_phone"), request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_main_menu_keyboard(_: Callable[[str], str], role: str = "user") -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text=_("menu_contest")),
            KeyboardButton(text=_("menu_referral"))
        ],
        [
            KeyboardButton(text=_("menu_tests")),
            KeyboardButton(text=_("menu_courses"))
        ],
        [
            KeyboardButton(text=_("menu_about")),
            KeyboardButton(text=_("menu_contact"))
        ],
        [
            KeyboardButton(text=_("menu_language"))
        ]
    ]

    # Add role-specific buttons
    if role in ("teacher", "admin", "superadmin"):
        keyboard.append([KeyboardButton(text=_("menu_teacher"))])
    if role in ("admin", "superadmin"):
        keyboard.append([KeyboardButton(text=_("menu_admin"))])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_cancel_keyboard(_: Callable[[str], str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("btn_cancel"))]
        ],
        resize_keyboard=True
    )

def get_skip_cancel_keyboard(_: Callable[[str], str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("btn_skip")), KeyboardButton(text=_("btn_cancel"))]
        ],
        resize_keyboard=True
    )
