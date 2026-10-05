from typing import Callable, Dict, Any, Awaitable, List
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from bot.config import settings

class RoleFilter:
    """Helper to check if user has allowed role."""
    @staticmethod
    def is_superadmin(user_id: int) -> bool:
        return user_id in settings.superadmin_list

    @staticmethod
    def is_admin(user_role: str, user_id: int) -> bool:
        return user_role in ("admin", "superadmin") or RoleFilter.is_superadmin(user_id)

    @staticmethod
    def is_teacher(user_role: str, user_id: int) -> bool:
        return user_role in ("teacher", "admin", "superadmin") or RoleFilter.is_superadmin(user_id)
