from bot.handlers.start import router as start_router
from bot.handlers.referral import router as referral_router
from bot.handlers.contest import router as contest_router
from bot.handlers.courses import router as courses_router
from bot.handlers.test_taking import router as test_taking_router
from bot.handlers.teacher import router as teacher_router
from bot.handlers.admin import admin_router

__all__ = [
    "start_router",
    "referral_router",
    "contest_router",
    "courses_router",
    "test_taking_router",
    "teacher_router",
    "admin_router"
]
