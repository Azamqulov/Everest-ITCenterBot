import time
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 0.5):
        super().__init__()
        self.rate_limit = rate_limit
        self.user_timestamps: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        event_user = data.get("event_from_user")
        if not event_user:
            return await handler(event, data)

        user_id = event_user.id
        current_time = time.time()
        last_time = self.user_timestamps.get(user_id, 0.0)

        if current_time - last_time < self.rate_limit:
            # Throttled - politely notify callback or ignore rapid spam
            if isinstance(event, CallbackQuery):
                await event.answer("⏳ Iltimos, biroz kuting...", show_alert=False)
            return None

        self.user_timestamps[user_id] = current_time
        return await handler(event, data)
