import logging
import traceback
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from bot.config import settings

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Unhandled error in handler: {e}\n{traceback.format_exc()}")
            
            _ = data.get("_")
            err_msg = _("error_occurred") if _ else "⚠️ Kutilmagan xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."

            try:
                if hasattr(event, "message") and event.message:
                    await event.message.answer(err_msg)
                elif hasattr(event, "callback_query") and event.callback_query:
                    await event.callback_query.answer(err_msg, show_alert=True)
                elif isinstance(event, Message):
                    await event.answer(err_msg)
                elif isinstance(event, CallbackQuery):
                    await event.answer(err_msg, show_alert=True)
            except Exception as notify_err:
                logger.error(f"Failed to send error notification to user: {notify_err}")

            return None

