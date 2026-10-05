import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.services.db import db
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu_keyboard
from bot.states import AdminBroadcastStates
from bot.middlewares.role_auth import RoleFilter

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "admin:broadcast")
async def handle_broadcast_menu(callback: CallbackQuery, state: FSMContext, user_role: str, _: Any):
    if not RoleFilter.is_admin(user_role, callback.from_user.id):
        await callback.answer(_("access_denied"), show_alert=True)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Barcha foydalanuvchilarga", callback_data="broadcast_seg:all")],
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek tilidagilarga", callback_data="broadcast_seg:uz"),
            InlineKeyboardButton(text="🇷🇺 Rus tilidagilarga", callback_data="broadcast_seg:ru")
        ],
        [InlineKeyboardButton(text="⬅️ Bekor qilish", callback_data="admin:menu_back")]
    ])

    await callback.message.edit_text(
        "📣 <b>Ommaviy Xabarnoma (Broadcast)</b>\n\nQaysi auditoriyaga xabar yubormoqchisiz?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("broadcast_seg:"))
async def handle_broadcast_segment(callback: CallbackQuery, state: FSMContext, _: Any):
    seg = callback.data.split(":")[1]
    await state.update_data(segment=seg)
    await state.set_state(AdminBroadcastStates.waiting_content)

    await callback.message.answer(
        "📝 Yubormoqchi bo'lgan xabaringizni kiriting (matn yoki rasm bilan):",
        reply_markup=get_cancel_keyboard(_)
    )
    await callback.answer()

@router.message(AdminBroadcastStates.waiting_content)
async def handle_broadcast_content(message: Message, state: FSMContext, bot: Bot, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Xabarnoma bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role="admin"))
        return

    data = await state.get_data()
    seg = data.get("segment", "all")
    await state.clear()

    # Get target users
    if seg == "uz":
        users = await db.fetch_all("SELECT telegram_id FROM users WHERE language = 'uz' AND is_blocked = 0")
    elif seg == "ru":
        users = await db.fetch_all("SELECT telegram_id FROM users WHERE language = 'ru' AND is_blocked = 0")
    else:
        users = await db.fetch_all("SELECT telegram_id FROM users WHERE is_blocked = 0")

    total = len(users)
    status_msg = await message.answer(f"🚀 Xabarnoma yuborish boshlandi (Jami: {total} nafar)...")

    sent = 0
    failed = 0

    for u in users:
        uid = u["telegram_id"]
        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=uid,
                    photo=message.photo[-1].file_id,
                    caption=message.caption or "",
                    parse_mode="HTML"
                )
            else:
                await bot.send_message(chat_id=uid, text=message.text or "", parse_mode="HTML")
            sent += 1
        except Exception as e:
            failed += 1
            if "blocked" in str(e).lower():
                await db.execute("UPDATE users SET is_blocked = 1 WHERE telegram_id = ?", (uid,))
        # Rate limit compliance: ~25 msg per second
        await asyncio.sleep(0.04)

    await status_msg.edit_text(
        f"✅ <b>Xabarnoma yakunlandi!</b>\n\n"
        f"• Yuborildi: <b>{sent} ta</b>\n"
        f"• Yetib bormadi (bloklagan): <b>{failed} ta</b>",
        parse_mode="HTML"
    )
