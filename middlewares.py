from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


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
        
        # Продолжение обработки
        result = await handler(event, data)
        
        return result 