from typing import Any, Awaitable, Callable, Dict
import logging

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

# Настройка логирования
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):
    """Промежуточный обработчик для логирования всех обновлений. | Middleware for logging all updates."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Логирование входящих обновлений
        print(f"Received update: {event}")
        
        # Логируем входящие события
        if isinstance(event, Message) and event.from_user:
            logger.info(f"Получено сообщение от {event.from_user.id} ({event.from_user.username}): {event.text}")
        elif isinstance(event, CallbackQuery) and event.from_user:
            logger.info(f"Получен callback от {event.from_user.id} ({event.from_user.username}): {event.data}")
        
        # Продолжение обработки
        result = await handler(event, data)
        
        return result 

class UserSavingMiddleware(BaseMiddleware):
    """Промежуточный обработчик для сохранения пользователей в базу данных"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Сохраняем пользователя, если это сообщение или callback
        try:
            if isinstance(event, Message) and event.from_user:
                from broadcast_handlers import add_user_to_db
                add_user_to_db(
                    user_id=event.from_user.id,
                    username=event.from_user.username,
                    first_name=event.from_user.first_name,
                    last_name=event.from_user.last_name,
                    chat_id=event.chat.id
                )
            elif isinstance(event, CallbackQuery) and event.from_user and event.message:
                from broadcast_handlers import add_user_to_db
                add_user_to_db(
                    user_id=event.from_user.id,
                    username=event.from_user.username,
                    first_name=event.from_user.first_name,
                    last_name=event.from_user.last_name,
                    chat_id=event.message.chat.id
                )
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователя: {e}")
        
        # Вызываем следующий обработчик
        return await handler(event, data) 