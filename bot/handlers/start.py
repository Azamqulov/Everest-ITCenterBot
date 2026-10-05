import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ChatMemberOwner, ChatMemberAdministrator, ChatMemberMember
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext

from bot.services.db import db
from bot.services.referral_service import referral_service
from bot.keyboards.inline import get_language_keyboard, get_consent_keyboard, get_channel_sub_keyboard
from bot.keyboards.reply import get_phone_keyboard, get_main_menu_keyboard
from bot.states import RegistrationStates
from bot.config import settings

logger = logging.getLogger(__name__)
router = Router()

async def check_channel_subscription(bot: Bot, user_id: int) -> bool:
    """Check if user is a member of all active required channels."""
    channels = await db.fetch_all("SELECT * FROM required_channels WHERE is_active = 1")
    if not channels:
        return True

    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status not in ("creator", "administrator", "member", "restricted"):
                return False
        except Exception as e:
            logger.warning(f"Error checking channel sub for chat_id={ch['chat_id']}, user={user_id}: {e}")
            # If bot is not in channel or error, allow through or handle gracefully
            continue
    return True

@router.message(CommandStart())
async def handle_start(message: Message, command: CommandObject, state: FSMContext, _: Any, lang: str):
    await state.clear()
    user_id = message.from_user.id
    full_name = message.from_user.full_name or "Foydalanuvchi"
    username = message.from_user.username

    # Parse deep-link referral code
    ref_code = None
    if command.args and command.args.startswith("ref_"):
        ref_code = command.args.replace("ref_", "").strip()

    # Get or create user
    user = await referral_service.get_or_create_user(
        telegram_id=user_id,
        full_name=full_name,
        username=username,
        referred_by_code=ref_code
    )

    # Check language
    if not user.get("language"):
        await state.set_state(RegistrationStates.choosing_language)
        await message.answer(
            _("welcome", name=full_name),
            reply_markup=get_language_keyboard(),
            parse_mode="HTML"
        )
        return

    # Check privacy consent
    # If phone is not verified yet, continue registration flow
    if not user.get("phone"):
        await state.set_state(RegistrationStates.privacy_consent)
        await message.answer(
            _("privacy_consent"),
            reply_markup=get_consent_keyboard(_),
            parse_mode="HTML"
        )
        return

    # Verified user -> show main menu
    await message.answer(
        _("main_menu_title"),
        reply_markup=get_main_menu_keyboard(_, role=user.get("role", "user")),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("set_lang:"))
async def handle_set_language(callback: CallbackQuery, state: FSMContext, _: Any):
    lang_code = callback.data.split(":")[1]
    user_id = callback.from_user.id

    await db.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (lang_code, user_id))
    data = await state.get_data()

    # If in registration, proceed to privacy consent
    current_state = await state.get_state()
    user = await db.fetch_one("SELECT * FROM users WHERE telegram_id = ?", (user_id,))

    await callback.message.delete()

    if not user or not user.get("phone"):
        await state.set_state(RegistrationStates.privacy_consent)
        msg_text = (
            "Hurmatli foydalanuvchi!\n\nBotdan to'liq foydalanish uchun O'zbekiston Respublikasining <i>\"Shaxsga doir ma'lumotlar to'g'risida\"</i>gi qonuniga muvofiq, ma'lumotlaringiz (Telegram ID, ism, telefon raqami) qayta ishlanishiga rozilik bildirasizmi?"
            if lang_code == "uz" else
            "Уважаемый пользователь!\n\nДля использования бота, в соответствии с Законом Республики Узбекистан <i>«О персональных данных»</i>, даете ли вы согласие на обработку ваших данных (Telegram ID, имя, номер телефона)?"
        )
        # Custom consent inline keyboard for selected language
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Roziman" if lang_code == "uz" else "✅ Согласен", callback_data="consent:yes"),
                InlineKeyboardButton(text="❌ Rozi emasman" if lang_code == "uz" else "❌ Не согласен", callback_data="consent:no")
            ]
        ])
        await callback.message.answer(msg_text, reply_markup=kb, parse_mode="HTML")
    else:
        await callback.message.answer(
            _("main_menu_title"),
            reply_markup=get_main_menu_keyboard(_, role=user.get("role", "user"))
        )

@router.callback_query(F.data.startswith("consent:"))
async def handle_consent(callback: CallbackQuery, state: FSMContext, bot: Bot, _: Any):
    decision = callback.data.split(":")[1]
    if decision == "no":
        await callback.message.edit_text(_("consent_rejected"))
        await state.clear()
        return

    # Check channels subscription
    channels = await db.fetch_all("SELECT * FROM required_channels WHERE is_active = 1")
    is_subbed = await check_channel_subscription(bot, callback.from_user.id)

    if not is_subbed and channels:
        await state.set_state(RegistrationStates.waiting_channel_sub)
        await callback.message.edit_text(
            _("mandatory_sub_title"),
            reply_markup=get_channel_sub_keyboard(_, channels),
            parse_mode="HTML"
        )
        return

    # Proceed to phone verification
    await callback.message.delete()
    await state.set_state(RegistrationStates.waiting_phone)
    await callback.message.answer(
        _("phone_request"),
        reply_markup=get_phone_keyboard(_),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "check_sub")
async def handle_check_subscription(callback: CallbackQuery, state: FSMContext, bot: Bot, _: Any):
    is_subbed = await check_channel_subscription(bot, callback.from_user.id)
    if not is_subbed:
        await callback.answer(_("sub_not_found"), show_alert=True)
        return

    await callback.answer("✅ Rahmat!", show_alert=False)
    await callback.message.delete()

    user = await db.fetch_one("SELECT phone FROM users WHERE telegram_id = ?", (callback.from_user.id,))
    if not user or not user.get("phone"):
        await state.set_state(RegistrationStates.waiting_phone)
        await callback.message.answer(
            _("phone_request"),
            reply_markup=get_phone_keyboard(_),
            parse_mode="HTML"
        )
    else:
        await state.clear()
        await callback.message.answer(
            _("main_menu_title"),
            reply_markup=get_main_menu_keyboard(_)
        )

@router.message(RegistrationStates.waiting_phone, F.contact)
async def handle_phone_contact(message: Message, state: FSMContext, bot: Bot, _: Any):
    contact = message.contact
    # Security: check contact belongs to user
    if contact.user_id != message.from_user.id:
        await message.answer(_("phone_invalid"))
        return

    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = f"+{phone}"

    user_id = message.from_user.id
    await db.execute("UPDATE users SET phone = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?", (phone, user_id))
    await state.clear()

    # Confirm referral points if eligible
    ref_result = await referral_service.confirm_referral_if_eligible(user_id)
    if ref_result:
        inviter_id = ref_result["inviter_id"]
        pts = ref_result["points"]
        friend = ref_result["friend_name"]
        try:
            await bot.send_message(
                chat_id=inviter_id,
                text=f"🎉 <b>Ajoyib yangilik!</b>\n\nDo'stingiz <b>{friend}</b> botimizga qo'shildi va telefon raqamini tasdiqladi.\nSizga <b>+{pts} ball</b> berildi!",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not notify inviter {inviter_id}: {e}")

    user = await db.fetch_one("SELECT * FROM users WHERE telegram_id = ?", (user_id,))
    await message.answer(
        _("phone_saved"),
        reply_markup=get_main_menu_keyboard(_, role=user.get("role", "user")),
        parse_mode="HTML"
    )

# Static navigation handlers
@router.message(F.text.in_(["ℹ️ Markaz haqida", "ℹ️ О центре"]))
async def handle_about(message: Message, _: Any):
    await message.answer(_("about_title"), parse_mode="HTML")

@router.message(F.text.in_(["💬 Aloqa", "💬 Контакты"]))
async def handle_contact(message: Message, _: Any):
    await message.answer(_("contact_title"), parse_mode="HTML")

@router.message(F.text.in_(["🌐 Til / Язык"]))
async def handle_change_language(message: Message, _: Any):
    await message.answer(
        "Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        reply_markup=get_language_keyboard()
    )
