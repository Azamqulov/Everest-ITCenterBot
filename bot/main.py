import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import settings
from bot.services.db import db
from bot.middlewares.i18n import i18n
from bot.middlewares.error_handler import ErrorHandlerMiddleware
from bot.middlewares.throttling import ThrottlingMiddleware
from bot.handlers import (
    start_router,
    referral_router,
    contest_router,
    courses_router,
    test_taking_router,
    teacher_router,
    admin_router
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("everest_bot")

async def on_startup(bot: Bot):
    logger.info("Initializing Database...")
    await db.init()
    logger.info("Database initialized successfully.")

    # Alert superadmins that bot is started
    for admin_id in settings.superadmin_list:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text="🟢 <b>Everest IT Center Telegram Boti ishga tushirildi!</b>\nBarcha tizimlar soz holatda.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.warning(f"Could not alert superadmin {admin_id}: {e}")

async def main():
    if not settings.BOT_TOKEN or settings.BOT_TOKEN == "mock_bot_token":
        logger.warning("BOT_TOKEN is not set or using mock token. Please specify your Telegram BOT_TOKEN in .env")

    # Bot instance
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # FSM Storage (Redis or Memory)
    storage = MemoryStorage()
    if settings.REDIS_URL:
        try:
            from aiogram.fsm.storage.redis import RedisStorage
            storage = RedisStorage.from_url(settings.REDIS_URL)
            logger.info("Redis FSM storage initialized.")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Falling back to MemoryStorage.")

    dp = Dispatcher(storage=storage)

    # Middlewares registration (Outer & Inner)
    dp.update.outer_middleware(ErrorHandlerMiddleware())
    dp.message.outer_middleware(ThrottlingMiddleware(rate_limit=0.5))
    dp.callback_query.outer_middleware(ThrottlingMiddleware(rate_limit=0.3))

    dp.message.middleware(i18n)
    dp.callback_query.middleware(i18n)

    # Register all handlers
    dp.include_router(start_router)
    dp.include_router(referral_router)
    dp.include_router(contest_router)
    dp.include_router(courses_router)
    dp.include_router(test_taking_router)
    dp.include_router(teacher_router)
    dp.include_router(admin_router)

    # Background scheduler
    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("APScheduler started.")

    await on_startup(bot)

    # Polling mode (or Webhook)
    logger.info(f"Starting bot @{settings.BOT_USERNAME} in polling mode...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
