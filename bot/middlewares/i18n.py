import json
import os
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User
from bot.services.db import db
from bot.config import settings

logger = logging.getLogger(__name__)

class I18nMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.locales: Dict[str, Dict[str, str]] = {}
        self.load_locales()

    def load_locales(self):
        locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
        for lang in ["uz", "ru"]:
            path = os.path.join(locales_dir, f"{lang}.json")
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.locales[lang] = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading {lang}.json: {e}")
                    self.locales[lang] = {}
            else:
                self.locales[lang] = {}

    def get_text(self, lang: str, key: str, **kwargs) -> str:
        lang_dict = self.locales.get(lang) or self.locales.get(settings.DEFAULT_LANGUAGE, {})
        text = lang_dict.get(key)
        if text is None:
            # Fallback to default language
            default_dict = self.locales.get(settings.DEFAULT_LANGUAGE, {})
            text = default_dict.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user: User = data.get("event_from_user")
        lang = settings.DEFAULT_LANGUAGE

        if event_user:
            user_data = await db.fetch_one("SELECT language, role, is_blocked FROM users WHERE telegram_id = ?", (event_user.id,))
            if user_data:
                if user_data.get("is_blocked"):
                    # Blocked users are ignored
                    return
                lang = user_data.get("language") or settings.DEFAULT_LANGUAGE
                data["user_role"] = user_data.get("role", "user")
                data["db_user"] = user_data
            else:
                data["user_role"] = "user"
                data["db_user"] = None

        data["lang"] = lang
        data["_"] = lambda key, **kwargs: self.get_text(lang, key, **kwargs)
        return await handler(event, data)

i18n = I18nMiddleware()
