from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict, Any

def get_teacher_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Yangi test yaratish", callback_data="teacher:create_test"),
                InlineKeyboardButton(text="📋 Testlarim va natijalar", callback_data="teacher:my_tests")
            ],
            [
                InlineKeyboardButton(text="📩 Kurs arizalari", callback_data="teacher:enrollments"),
                InlineKeyboardButton(text="📚 Kurs qo'shish", callback_data="teacher:add_course")
            ]
        ]
    )

def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Umumiy statistika", callback_data="admin:stats"),
                InlineKeyboardButton(text="🎁 Konkurslar", callback_data="admin:contests")
            ],
            [
                InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin:users"),
                InlineKeyboardButton(text="🚩 Shubhali referallar", callback_data="admin:suspicious_refs")
            ],
            [
                InlineKeyboardButton(text="📚 Kurslar moderatsiyasi", callback_data="admin:courses_mod"),
                InlineKeyboardButton(text="📝 AI Post Generator", callback_data="admin:ai_posts")
            ],
            [
                InlineKeyboardButton(text="📣 Broadcast", callback_data="admin:broadcast"),
                InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin:settings")
            ]
        ]
    )

def get_ai_post_variants_keyboard(variants_count: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i in range(1, variants_count + 1):
        row.append(InlineKeyboardButton(text=f"Variant #{i}", callback_data=f"ai_post:select:{i}"))
    buttons.append(row)
    buttons.append([
        InlineKeyboardButton(text="🔄 Qayta yaratish", callback_data="ai_post:regenerate"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="ai_post:cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_ai_post_actions_keyboard(variant_idx: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 Hozir kanalga joylash", callback_data=f"ai_post:publish:{variant_idx}"),
                InlineKeyboardButton(text="⏰ Rejalashtirish", callback_data=f"ai_post:schedule:{variant_idx}")
            ],
            [
                InlineKeyboardButton(text="✏️ Matnni tahrirlash", callback_data=f"ai_post:edit:{variant_idx}"),
                InlineKeyboardButton(text="🖼 Rasm biriktirish", callback_data=f"ai_post:media:{variant_idx}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Boshqa variantlar", callback_data="ai_post:back_to_variants"),
                InlineKeyboardButton(text="❌ Bekor qilish", callback_data="ai_post:cancel")
            ]
        ]
    )

def get_enrollment_status_keyboard(enrollment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📞 Bog'lanildi", callback_data=f"enroll_status:{enrollment_id}:boglanildi"),
                InlineKeyboardButton(text="✅ Yozildi", callback_data=f"enroll_status:{enrollment_id}:yozildi")
            ],
            [
                InlineKeyboardButton(text="⏳ Kutish ro'yxati", callback_data=f"enroll_status:{enrollment_id}:kutish_royxati"),
                InlineKeyboardButton(text="❌ Rad etildi", callback_data=f"enroll_status:{enrollment_id}:rad_etildi")
            ]
        ]
    )
