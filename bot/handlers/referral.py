from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from typing import Any

from bot.services.db import db
from bot.services.referral_service import referral_service
from bot.keyboards.inline import get_referral_keyboard
from bot.config import settings

router = Router()

@router.message(F.text.in_(["👥 Referal", "👥 Реферал"]))
async def handle_referral_menu(message: Message, _: Any):
    user_id = message.from_user.id
    user = await db.fetch_one("SELECT referral_code FROM users WHERE telegram_id = ?", (user_id,))
    if not user:
        return

    code = user["referral_code"]
    ref_link = f"https://t.me/{settings.BOT_USERNAME}?start=ref_{code}"

    # Get points setting
    setting_val = await db.fetch_val("SELECT value FROM settings WHERE key = 'referral_points'")
    points_per_ref = int(setting_val) if setting_val and str(setting_val).isdigit() else settings.DEFAULT_REFERRAL_POINTS

    stats = await referral_service.get_user_stats(user_id)
    share_text = _("share_ref_text", link=ref_link)

    msg_text = _(
        "referral_title",
        points=points_per_ref,
        link=ref_link,
        total=stats["total_refs"],
        confirmed=stats["confirmed_refs"],
        pending=stats["pending_refs"],
        user_points=stats["points"]
    )

    await message.answer(
        msg_text,
        reply_markup=get_referral_keyboard(_, share_text=share_text),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "ref:my_friends")
async def handle_my_friends(callback: CallbackQuery, _: Any):
    user_id = callback.from_user.id
    rows = await db.fetch_all("""
        SELECT r.status, r.created_at, u.full_name
        FROM referrals r
        JOIN users u ON u.telegram_id = r.invitee_id
        WHERE r.inviter_id = ?
        ORDER BY r.created_at DESC
        LIMIT 30
    """, (user_id,))

    if not rows:
        await callback.answer(_("friends_empty"), show_alert=True)
        return

    items = []
    for idx, r in enumerate(rows, start=1):
        status_icon = "✅" if r["status"] == "confirmed" else "⏳"
        status_text = "tasdiqlangan" if r["status"] == "confirmed" else "kutilmoqda"
        items.append(f"{idx}. {r['full_name']} — {status_icon} <i>{status_text}</i>")

    list_text = "\n".join(items)
    await callback.message.answer(
        _("friends_list_title", list=list_text),
        parse_mode="HTML"
    )
    await callback.answer()
