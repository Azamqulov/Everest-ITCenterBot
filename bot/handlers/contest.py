from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from typing import Any

from bot.services.db import db
from bot.services.referral_service import referral_service
from bot.keyboards.inline import get_contest_keyboard

router = Router()

@router.message(F.text.in_(["🎁 Konkurs", "🎁 Конкурс"]))
async def handle_contest_menu(message: Message, _: Any):
    user_id = message.from_user.id
    contest = await db.fetch_one("SELECT * FROM contests WHERE status = 'active' ORDER BY id DESC LIMIT 1")

    if not contest:
        await message.answer(_("contest_none"))
        return

    contest_id = contest["id"]
    prizes = await db.fetch_all("SELECT * FROM contest_prizes WHERE contest_id = ? ORDER BY place ASC", (contest_id,))

    prizes_text = "\n".join([f"• {p['place']}-o'rin: <b>{p['description']}</b>" for p in prizes]) or "Tez orada e'lon qilinadi."
    winner_mode = "Top ball to'plaganlar" if contest["winner_mode"] == "top_n" else "Tasodifiy lotereya"

    stats = await referral_service.get_user_stats(user_id, contest_id=contest_id)
    rank = await referral_service.get_user_rank(user_id, contest_id=contest_id)

    msg_text = _(
        "contest_details",
        title=contest["title"],
        description=contest["description"] or "",
        starts_at=str(contest["starts_at"])[:10],
        ends_at=str(contest["ends_at"])[:10],
        winner_mode=winner_mode,
        prizes=prizes_text,
        rules=contest["rules"] or "",
        points=stats["points"],
        rank=f"#{rank}"
    )

    await message.answer(
        msg_text,
        reply_markup=get_contest_keyboard(_),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "contest:leaderboard")
async def handle_contest_leaderboard(callback: CallbackQuery, _: Any):
    user_id = callback.from_user.id
    contest = await db.fetch_one("SELECT id FROM contests WHERE status = 'active' ORDER BY id DESC LIMIT 1")
    contest_id = contest["id"] if contest else None

    leaders = await referral_service.get_leaderboard(contest_id=contest_id, limit=10)
    stats = await referral_service.get_user_stats(user_id, contest_id=contest_id)
    rank = await referral_service.get_user_rank(user_id, contest_id=contest_id)

    if not leaders:
        await callback.answer("Hozircha ishtirokchilar reytingi shakllanmagan.", show_alert=True)
        return

    items = []
    medals = ["🥇", "🥈", "🥉"]
    for idx, l in enumerate(leaders, start=1):
        icon = medals[idx - 1] if idx <= 3 else f"{idx}."
        items.append(f"{icon} <b>{l['name']}</b> — {l['points']} ball")

    list_text = "\n".join(items)
    await callback.message.answer(
        _("leaderboard_title", list=list_text, rank=f"#{rank}", points=stats["points"]),
        parse_mode="HTML"
    )
    await callback.answer()
