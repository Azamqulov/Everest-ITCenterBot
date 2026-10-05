import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from typing import Any

from bot.services.db import db
from bot.services.ai_service import ai_service
from bot.keyboards.admin_kb import get_ai_post_variants_keyboard, get_ai_post_actions_keyboard
from bot.keyboards.reply import get_cancel_keyboard, get_main_menu_keyboard
from bot.states import AIPostStates
from bot.middlewares.role_auth import RoleFilter
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "admin:ai_posts")
async def handle_ai_post_start(callback: CallbackQuery, state: FSMContext, user_role: str, _: Any):
    if not RoleFilter.is_admin(user_role, callback.from_user.id):
        await callback.answer(_("access_denied"), show_alert=True)
        return

    await state.set_state(AIPostStates.waiting_topic)
    await callback.message.answer(
        "📝 <b>AI Kanal Post Generator (Claude 3.5 + Gemini Fallback)</b>\n\n"
        "Kanal uchun post mavzusini kiriting:\n<i>(Masalan: Python nima uchun mashhur va bizning yangi kursimiz)</i>",
        reply_markup=get_cancel_keyboard(_),
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(AIPostStates.waiting_topic)
async def handle_ai_topic(message: Message, state: FSMContext, _: Any):
    if message.text == _("btn_cancel"):
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=get_main_menu_keyboard(_, role="admin"))
        return

    topic = message.text.strip()
    await state.update_data(topic=topic)

    wait_msg = await message.answer(
        "🧠 <b>Sun'iy intellekt post variantlarini tayyorlamoqda...</b>\n<i>Iltimos, bir necha soniya kuting...</i>",
        parse_mode="HTML"
    )

    try:
        variants = await ai_service.generate_channel_posts(topic=topic)
        await state.update_data(variants=variants)
        await state.set_state(AIPostStates.review_variants)

        # Show variants preview
        out_msg = "✨ <b>Tayyorlangan 3 ta variant:</b>\n\n"
        for idx, var in enumerate(variants, start=1):
            out_msg += f"<b>=== VARIANT #{idx} ===</b>\n{var}\n\n"

        await wait_msg.delete()
        await message.answer(
            out_msg,
            reply_markup=get_ai_post_variants_keyboard(len(variants)),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error generating AI posts: {e}")
        await wait_msg.delete()
        await message.answer("⚠️ Post generatsiyasida xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        await state.clear()

@router.callback_query(AIPostStates.review_variants, F.data.startswith("ai_post:select:"))
async def handle_select_variant(callback: CallbackQuery, state: FSMContext, _: Any):
    variant_idx = int(callback.data.split(":")[2]) - 1
    data = await state.get_data()
    variants = data.get("variants", [])

    if variant_idx >= len(variants):
        await callback.answer("Variant topilmadi.", show_alert=True)
        return

    chosen_text = variants[variant_idx]
    await state.update_data(chosen_variant=variant_idx, final_text=chosen_text)

    await callback.message.answer(
        f"✅ <b>Tanlangan variant #{variant_idx + 1}:</b>\n\n{chosen_text}\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_ai_post_actions_keyboard(variant_idx),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data.startswith("ai_post:publish:"))
async def handle_publish_post(callback: CallbackQuery, state: FSMContext, bot: Bot, _: Any):
    data = await state.get_data()
    final_text = data.get("final_text")
    media = data.get("media")

    channel_id = settings.DEFAULT_CHANNEL_ID
    try:
        if media:
            await bot.send_photo(chat_id=channel_id, photo=media, caption=final_text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id=channel_id, text=final_text, parse_mode="HTML")

        # Save to channel_posts table
        await db.execute("""
            INSERT INTO post_drafts (admin_id, topic, final_text, status)
            VALUES (?, ?, ?, 'published')
        """, (callback.from_user.id, data.get("topic", "AI Post"), final_text))

        await callback.message.edit_text("🚀 <b>Post muvaffaqiyatli kanalga joylandi!</b>", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to post to channel: {e}")
        await callback.message.answer(f"⚠️ Kanalga joylashda xatolik yuz berdi: {e}\n(Bot kanalda admin ekanligini tekshiring).")

    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "ai_post:cancel")
async def handle_ai_cancel(callback: CallbackQuery, state: FSMContext, _: Any):
    await state.clear()
    await callback.message.edit_text("Post yaratish bekor qilindi.")
    await callback.answer()
