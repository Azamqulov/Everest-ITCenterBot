import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from typing import Any

from bot.services.db import db
from bot.keyboards.admin_kb import get_admin_menu_keyboard
from bot.middlewares.role_auth import RoleFilter

logger = logging.getLogger(__name__)
router = Router()

@router.message(F.text.in_(["🛠 Admin panel", "🛠 Панель админа"]))
async def handle_admin_panel(message: Message, user_role: str, _: Any):
    if not RoleFilter.is_admin(user_role, message.from_user.id):
        await message.answer(_("access_denied"))
        return

    await message.answer(
        "🛠 <b>Everest IT Center — Bosh Administrator Paneli</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin:stats")
async def handle_admin_stats(callback: CallbackQuery, user_role: str, _: Any):
    if not RoleFilter.is_admin(user_role, callback.from_user.id):
        await callback.answer(_("access_denied"), show_alert=True)
        return

    total_users = await db.fetch_val("SELECT COUNT(*) FROM users") or 0
    today_users = await db.fetch_val("SELECT COUNT(*) FROM users WHERE created_at >= date('now')") or 0
    total_refs = await db.fetch_val("SELECT COUNT(*) FROM referrals") or 0
    confirmed_refs = await db.fetch_val("SELECT COUNT(*) FROM referrals WHERE status = 'confirmed'") or 0
    flagged_refs = await db.fetch_val("SELECT COUNT(*) FROM referrals WHERE status = 'flagged'") or 0

    conversion_rate = round((confirmed_refs / total_refs) * 100, 1) if total_refs > 0 else 0.0

    total_tests = await db.fetch_val("SELECT COUNT(*) FROM tests") or 0
    total_attempts = await db.fetch_val("SELECT COUNT(*) FROM test_attempts WHERE status = 'completed'") or 0
    total_enrollments = await db.fetch_val("SELECT COUNT(*) FROM course_enrollments") or 0
    total_points = await db.fetch_val("SELECT COALESCE(SUM(amount), 0) FROM points_ledger") or 0

    stats_msg = (
        "📊 <b>Everest IT Center — Jonli Tizim Statistikasi</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b>\n"
        f"• Jami a'zolar: <b>{total_users:,} nafar</b>\n"
        f"• Bugun qo'shilganlar: <b>+{today_users} nafar</b>\n\n"
        f"🔗 <b>Referal va Konkurs:</b>\n"
        f"• Jami takliflar: <b>{total_refs:,} ta</b>\n"
        f"• Tasdiqlangan: <b>{confirmed_refs:,} ta ({conversion_rate}%)</b>\n"
        f"• Shubhali (muzlatilgan): <b>{flagged_refs} ta</b>\n"
        f"• Jami hisoblangan ballar: <b>{total_points:,} ball</b>\n\n"
        f"📝 <b>Testlar va Ta'lim:</b>\n"
        f"• Yaratilgan testlar: <b>{total_tests} ta</b>\n"
        f"• Topshirilgan testlar: <b>{total_attempts} ta</b>\n"
        f"• Kurslarga kelgan arizalar: <b>{total_enrollments} ta</b>"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Admin menyu", callback_data="admin:menu_back")]
    ])

    await callback.message.edit_text(stats_msg, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "admin:suspicious_refs")
async def handle_suspicious_refs(callback: CallbackQuery, user_role: str, _: Any):
    if not RoleFilter.is_admin(user_role, callback.from_user.id):
        await callback.answer(_("access_denied"), show_alert=True)
        return

    flagged = await db.fetch_all("""
        SELECT r.*, u1.full_name as inviter_name, u2.full_name as invitee_name
        FROM referrals r
        JOIN users u1 ON u1.telegram_id = r.inviter_id
        JOIN users u2 ON u2.telegram_id = r.invitee_id
        WHERE r.status = 'flagged'
        ORDER BY r.created_at DESC
        LIMIT 10
    """)

    if not flagged:
        await callback.answer("Hozircha shubhali referallar aniqlanmagan ✅", show_alert=True)
        return

    items = []
    for f in flagged:
        items.append(
            f"🚩 Taklif qiluvchi: <b>{f['inviter_name']}</b>\n"
            f"👤 Qo'shilgan: <b>{f['invitee_name']}</b>\n"
            f"Sabab: <i>{f['flag_reason'] or 'Yuqori tezlik'}</i>\n"
        )

    await callback.message.answer(
        "🚩 <b>Shubhali referallar ro'yxati (Anti-fraud):</b>\n\n" + "\n---\n".join(items),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "admin:menu_back")
async def handle_admin_back(callback: CallbackQuery, _: Any):
    await callback.message.edit_text(
        "🛠 <b>Everest IT Center — Bosh Administrator Paneli</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=get_admin_menu_keyboard(),
        parse_mode="HTML"
    )
