"""
Клавиатуры для работы с быстрым потоком
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fast_flow_config import get_fast_flow_options
from config import CURRENCY_NAMES

def get_fast_flow_currency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора валюты быстрого потока. | Keyboard for selecting the fast flow currency."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Российский рубль", callback_data="fastflow_currency_RUB")
        ],
        [
            InlineKeyboardButton(text="🇪🇺 Евро", callback_data="fastflow_currency_EUR")
        ],
        [
            InlineKeyboardButton(text="🇵🇱 Польский злотый", callback_data="fastflow_currency_PLN")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад | Back", callback_data="back_to_simulators")
        ]
    ])
    return keyboard

def get_fast_flow_amount_keyboard(currency: str) -> InlineKeyboardMarkup:
    """Клавиатура для выбора номинала быстрого потока. | Keyboard for selecting the fast flow amount."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Получаем все опции для выбранной валюты
    options = get_fast_flow_options(currency)
    
    # Группируем по 4 кнопки в ряд
    current_row = []
    for option in options:
        amount = option["amount"]
        if len(current_row) < 4:
            current_row.append(
                InlineKeyboardButton(
                    text=f"{amount}", 
                    callback_data=f"fastflow_amount_{currency}_{amount}"
                )
            )
        else:
            keyboard.inline_keyboard.append(current_row)
            current_row = [
                InlineKeyboardButton(
                    text=f"{amount}", 
                    callback_data=f"fastflow_amount_{currency}_{amount}"
                )
            ]
    
    # Добавляем последний ряд, если остались кнопки
    if current_row:
        keyboard.inline_keyboard.append(current_row)
    
    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад | Back", callback_data="fastflow_back_to_currency")
    ])
    
    return keyboard

def get_fast_flow_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения номинала быстрого потока. | Keyboard for confirming the fast flow amount."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить | Confirm", callback_data="fastflow_confirm")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад к выбору номинала | Back to amount selection", callback_data="fastflow_back_to_amount")
        ]
    ])
    return keyboard

def get_fast_flow_control_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для управления быстрым потоком. | Keyboard for managing the fast flow."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Начислить | Accrue", callback_data="fastflow_next_day")
        ],
        [
            InlineKeyboardButton(text="🔄 Заново | Restart", callback_data="fastflow_restart")
        ],
        [
            InlineKeyboardButton(text="◀️ К симуляторам | Back to simulators", callback_data="back_to_simulators")
        ]
    ])
    return keyboard 