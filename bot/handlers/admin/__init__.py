from aiogram import Router
from bot.handlers.admin.main import router as main_router
from bot.handlers.admin.posts import router as posts_router
from bot.handlers.admin.broadcast import router as broadcast_router
from bot.handlers.admin.settings_handler import router as settings_router

admin_router = Router()
admin_router.include_router(main_router)
admin_router.include_router(posts_router)
admin_router.include_router(broadcast_router)
admin_router.include_router(settings_router)
