"""
Клавиатуры для работы с накопительным потоком
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CURRENCY_NAMES
from accumulative_flow_config import AVAILABLE_PERIODS

def get_accumulative_flow_currency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора валюты накопительного потока. | Keyboard for selecting the accumulative flow currency."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Российский рубль", callback_data="accflow_currency_RUB")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад | Back", callback_data="back_to_simulators")
        ]
    ])
    return keyboard

def get_accumulative_flow_period_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора периода накопительного потока. | Keyboard for selecting the accumulative flow period."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Создаем ряд кнопок с периодами
    row = []
    for period in AVAILABLE_PERIODS:
        period_text = f"{period} {'год | year' if period == 1 else 'года | years' if 2 <= period <= 4 else 'лет | years'}"
        row.append(InlineKeyboardButton(text=period_text, callback_data=f"accflow_period_{period}"))
        
        # По 3 кнопки в ряд
        if len(row) == 3:
            keyboard.inline_keyboard.append(row)
            row = []
    
    # Добавляем оставшиеся кнопки
    if row:
        keyboard.inline_keyboard.append(row)
    
    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад | Back", callback_data="accflow_back_to_amount")
    ])
    
    return keyboard

def get_accumulative_flow_control_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для управления накопительным потоком после расчета. | Keyboard for managing the accumulative flow after calculation."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Заново | Restart", callback_data="accflow_restart")
        ],
        [
            InlineKeyboardButton(text="◀️ К симуляторам | Back to simulators", callback_data="back_to_simulators")
        ]
    ])
    return keyboard 