"""
Обработчики для работы с симулятором накопительного потока
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import CURRENCY_SYMBOLS
from accumulative_flow_states import AccumulativeFlowState, AccumulativeFlowData
from accumulative_flow_keyboards import (
    get_accumulative_flow_currency_keyboard,
    get_accumulative_flow_period_keyboard,
    get_accumulative_flow_control_keyboard
)
from accumulative_flow_utils import (
    calculate_accumulative_flow_data,
    format_accumulative_flow_result
)
from keyboards import get_simulators_menu

# Создаем роутер для накопительного потока
accumulative_flow_router = Router()

# Обработчик для запуска симулятора накопительного потока
@accumulative_flow_router.callback_query(F.data == "savings_calculator")
async def start_accumulative_flow(callback: CallbackQuery, state: FSMContext):
    """Запуск симулятора накопительного потока."""
    await state.clear()
    await state.set_state(AccumulativeFlowState.selecting_currency)
    
    await callback.message.answer(
        "*Выберите валюту для Накопительного Потока:*\n\n"
        "*Select the currency for the Accumulation Flow:*\n\n"
        "👇👇👇",
        reply_markup=get_accumulative_flow_currency_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик выбора валюты для накопительного потока
@accumulative_flow_router.callback_query(AccumulativeFlowState.selecting_currency, F.data.startswith("accflow_currency_"))
async def process_accumulative_flow_currency_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора валюты для накопительного потока."""
    currency = callback.data.split("_")[2]
    
    # Сохраняем выбранную валюту
    await state.update_data(currency=currency)
    await state.set_state(AccumulativeFlowState.entering_amount)
    
    await callback.message.answer(
        f"Введите сумму Накопительного Потока\n\n"
        f"*Цифрами без пробелов от 1000 до 100000*\n\n"
        f"👇👇👇",
        parse_mode="Markdown"

    )
    await callback.answer()

# Обработчик ввода суммы накопительного потока
@accumulative_flow_router.message(AccumulativeFlowState.entering_amount)
async def process_accumulative_flow_amount_input(message: Message, state: FSMContext):
    """Обработка ввода суммы накопительного потока."""
    try:
        # Пытаемся преобразовать ввод в число
        amount = float(message.text.strip())
        
        # Проверяем, что сумма в допустимом диапазоне
        if amount < 1000 or amount > 100000:
            await message.answer(
                f"*Сумма должна быть от 1000 до 100000. Пожалуйста, введите корректную сумму:*",
                parse_mode="Markdown"
            )
            return
        
        # Сохраняем введенную сумму
        await state.update_data(amount=amount)
        await state.set_state(AccumulativeFlowState.selecting_period)
        
        # Получаем данные пользователя
        data = await state.get_data()
        currency = data.get("currency")
        
        await message.answer(
            f"*Выберите период для Накопительного Потока {CURRENCY_SYMBOLS[currency]}*\n\n"
            f"*Select the period for the Accumulation Flow {CURRENCY_SYMBOLS[currency]}*\n\n"
            "👇👇👇",
            reply_markup=get_accumulative_flow_period_keyboard(),
            parse_mode="Markdown"
        )
    except ValueError:
        # Если введено не число
        await message.answer(
            f"*Пожалуйста, введите сумму цифрами без пробелов:*",
            parse_mode="Markdown"
        )

# Обработчик выбора периода накопительного потока
@accumulative_flow_router.callback_query(AccumulativeFlowState.selecting_period, F.data.startswith("accflow_period_"))
async def process_accumulative_flow_period_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора периода для накопительного потока."""
    # Парсим период из callback_data
    period_years = int(callback.data.split("_")[2])
    
    # Получаем данные пользователя
    data = await state.get_data()
    currency = data.get("currency")
    amount = data.get("amount")
    
    # Рассчитываем данные потока
    flow_data = calculate_accumulative_flow_data(currency, amount, period_years)
    if not flow_data:
        await callback.answer("Ошибка при расчете данных потока", show_alert=True)
        return
    
    # Переходим к просмотру результата
    await state.set_state(AccumulativeFlowState.viewing_result)
    
    # Формируем сообщение с результатом
    message_text = format_accumulative_flow_result(flow_data)
    
    await callback.message.answer(
        message_text,
        reply_markup=get_accumulative_flow_control_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия кнопки "Заново"
@accumulative_flow_router.callback_query(F.data == "accflow_restart")
async def restart_accumulative_flow(callback: CallbackQuery, state: FSMContext):
    """Перезапуск симулятора накопительного потока."""
    await state.clear()
    await state.set_state(AccumulativeFlowState.selecting_currency)
    
    await callback.message.answer(
        "*Выберите валюту для Накопительного Потока:*\n\n"
        "*Select the currency for the Accumulation Flow:*\n\n"
        "👇👇👇",
        reply_markup=get_accumulative_flow_currency_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик возврата к вводу суммы
@accumulative_flow_router.callback_query(AccumulativeFlowState.selecting_period, F.data == "accflow_back_to_amount")
async def back_to_amount_input(callback: CallbackQuery, state: FSMContext):
    """Возврат к вводу суммы. | Return to the amount input."""
    await state.set_state(AccumulativeFlowState.entering_amount)
    
    await callback.message.answer(
        f"Введите сумму Накопительного Потока\n\n"
        f"*Цифрами без пробелов от 1000 до 100000*\n\n"
        f"👇👇👇",
        parse_mode="Markdown"

        f"Enter the amount of the Accumulation Flow\n\n"
        f"Without spaces from 1000 to 100000\n\n"
        f"👇👇👇"
    )
    await callback.answer()

# Обработчик возврата в меню симуляторов
@accumulative_flow_router.callback_query(F.data == "back_to_simulators")
async def back_to_simulators(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню симуляторов. | Return to the simulators menu."""
    await state.clear()
    
    await callback.message.answer(
        "*Выберите симулятор:*\n\n"
        "*Choose the simulator:*\n\n"
        "👇👇👇",
        reply_markup=get_simulators_menu(),
        parse_mode="Markdown"
    )
    await callback.answer() 