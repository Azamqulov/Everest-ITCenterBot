import json
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.services.db import db
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu_keyboard
from bot.states import AdminPointsStates
from bot.middlewares.role_auth import RoleFilter

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "admin:settings")
async def handle_admin_settings_menu(callback: CallbackQuery, user_role: str, _: Any):
    if not RoleFilter.is_admin(user_role, callback.from_user.id):
        await callback.answer(_("access_denied"), show_alert=True)
        return

    ref_pts = await db.fetch_val("SELECT value FROM settings WHERE key = 'referral_points'") or "10"
    channels = await db.fetch_all("SELECT * FROM required_channels WHERE is_active = 1")
    ch_text = ", ".join([c["title"] for c in channels]) or "Mavjud emas"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Referal ballini o'zgartirish", callback_data="admin:change_ref_points")],
        [InlineKeyboardButton(text="💎 Foydalanuvchiga ball berish (Audit log)", callback_data="admin:adjust_points")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu_back")]
    ])

    await callback.message.edit_text(
        f"⚙️ <b>Tizim Sozlamalari</b>\n\n"
        f"• Har bir referal uchun ball: <b>{ref_pts} ball</b>\n"
        f"• Majburiy kanallar: <b>{ch_text}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

# --- Adjust User Points with Mandatory Reason & Audit Log ---
@router.callback_query(F.data == "admin:adjust_points")
async def handle_adjust_points_start(callback: CallbackQuery, state: FSMContext, user_role: str, _: Any):
    if not RoleFilter.is_admin(user_role, callback.from_user.id):
        await callback.answer(_("access_denied"), show_alert=True)
        return

    await state.set_state(AdminPointsStates.waiting_user_id)
    await callback.message.answer(
        "👤 Ball o'zgartiriladigan foydalanuvchining <b>Telegram ID</b> raqamini kiriting:",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AdminPointsStates.waiting_user_id)
async def handle_points_user_id(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role="admin"))
        return

    if not message.text.isdigit():
        await message.answer("Iltimos, to'g'ri Telegram ID (faqat raqam) kiriting:")
        return

    uid = int(message.text)
    user = await db.fetch_one("SELECT * FROM users WHERE telegram_id = ?", (uid,))
    if not user:
        await message.answer("Bunday foydalanuvchi botda topilmadi. Qaytadan kiriting:")
        return

    await state.update_data(target_user_id=uid, target_user_name=user["full_name"])
    await state.set_state(AdminPointsStates.waiting_amount)
    await message.answer(
        f"Foydalanuvchi: <b>{user['full_name']}</b>\nQo'shiladigan yoki ayiriladigan ball miqdorini kiriting (masalan: <code>50</code> yoki <code>-20</code>):",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )

@router.message(AdminPointsStates.waiting_amount)
async def handle_points_amount(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role="admin"))
        return

    text = message.text.replace("+", "").strip()
    try:
        amount = int(text)
    except ValueError:
        await message.answer("Iltimos, to'g'ri son kiriting:")
        return

    await state.update_data(amount=amount)
    await state.set_state(AdminPointsStates.waiting_reason)
    await message.answer(
        "📝 Ushbu ball o'zgarishining <b>majburiy sababini</b> kiriting (Audit log uchun):",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )

@router.message(AdminPointsStates.waiting_reason)
async def handle_points_reason(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role="admin"))
        return

    reason = message.text.strip()
    data = await state.get_data()
    uid = data["target_user_id"]
    amount = data["amount"]
    name = data["target_user_name"]
    admin_id = message.from_user.id
    await state.clear()

    # Get active contest if any
    active_contest = await db.fetch_one("SELECT id FROM contests WHERE status = 'active' ORDER BY id DESC LIMIT 1")
    contest_id = active_contest["id"] if active_contest else None

    # Write to points_ledger
    await db.execute("""
        INSERT INTO points_ledger (user_id, contest_id, amount, source, reason, created_by)
        VALUES (?, ?, ?, 'admin', ?, ?)
    """, (uid, contest_id, amount, f"Admin tomonidan: {reason}", admin_id))

    # Write to audit_logs
    await db.execute("""
        INSERT INTO audit_logs (actor_id, action, entity, entity_id, details)
        VALUES (?, 'adjust_points', 'points_ledger', ?, ?)
    """, (admin_id, str(uid), json.dumps({"amount": amount, "reason": reason})))

    await message.answer(
        f"✅ <b>Ball muvaffaqiyatli saqlandi!</b>\n\n"
        f"• Foydalanuvchi: <b>{name}</b> ({uid})\n"
        f"• O'zgarish: <b>{amount:+d} ball</b>\n"
        f"• Sabab: <i>{reason}</i>\n"
        f"• Audit logga qayd etildi.",
        reply_markup=get_main_menu_keyboard(_, role="admin"),
        parse_mode="HTML"
    )
