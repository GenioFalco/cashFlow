# Патч для исправления ошибки torch.get_default_device
import whisper_patch

import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from accumulative_flow_handlers import accumulative_flow_router
from config import BOT_TOKEN
from handlers import router
from fast_flow_handlers import fast_flow_router
from middlewares import LoggingMiddleware
from ai_assistant_handlers import ai_assistant_router  # Новый импорт для AI-ассистента

# Импортируем функцию обновления курсов
try:
    from currency_rates import update_currency_rates
    import config  # Для обновления констант
except ImportError:
    update_currency_rates = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Периодичность обновления курсов в секундах
CURRENCY_UPDATE_INTERVAL = 3600  # 1 час

async def update_currencies_periodically():
    """Периодическое обновление курсов валют"""
    if not update_currency_rates:
        logger.warning("Модуль currency_rates не найден, обновление курсов недоступно")
        return
        
    while True:
        try:
            logger.info("Обновление курсов валют...")
            # Обновляем курсы
            ecr_rate = update_currency_rates()
            
            # Обновляем константы в config
            if ecr_rate:
                config.ECR_PURCHASE_RATE = ecr_rate
                logger.info(f"Курс ECR обновлен: {ecr_rate:.2f} руб.")
            
            # Обновляем курсы валют
            rates = config.CURRENCY_RATES_DYNAMIC
            if rates:
                for currency, rate in rates.items():
                    if currency in config.CURRENCY_RATES:
                        config.CURRENCY_RATES[currency] = rate
                logger.info(f"Курсы валют обновлены: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении курсов: {e}")
        
        # Ждем до следующего обновления
        await asyncio.sleep(CURRENCY_UPDATE_INTERVAL)

async def main():
    # Используем хранилище в памяти
    storage = MemoryStorage()
    
    # Инициализируем бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Регистрируем промежуточные обработчики
    dp.update.middleware(LoggingMiddleware())
    
    # Регистрируем обработчики
    dp.include_router(router)
    dp.include_router(fast_flow_router)  # Добавляем роутер быстрого потока
    dp.include_router(accumulative_flow_router)  # Добавляем роутер накопительного потока
    dp.include_router(ai_assistant_router)  # Добавляем роутер AI-ассистента
    
    
    # Игнорируем старые обновления
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем периодическое обновление курсов в фоне
    if update_currency_rates:
        asyncio.create_task(update_currencies_periodically())
    
    # Запускаем бота
    logger.info("Starting bot")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 