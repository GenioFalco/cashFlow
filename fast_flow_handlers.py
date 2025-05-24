"""
Обработчики для работы с симулятором быстрого потока
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from config import CURRENCY_SYMBOLS, ECR_SELL_RATE
from fast_flow_states import FastFlowState, FastFlowData
from fast_flow_config import FAST_FLOW_IMAGES, get_fast_flow_option
from fast_flow_keyboards import (
    get_fast_flow_currency_keyboard,
    get_fast_flow_amount_keyboard,
    get_fast_flow_confirmation_keyboard,
    get_fast_flow_control_keyboard
)
from fast_flow_utils import (
    calculate_fast_flow_data,
    process_day,
    format_fast_flow_confirmation,
    format_fast_flow_stats
)
from keyboards import get_simulators_menu

# Создаем роутер для быстрого потока
fast_flow_router = Router()

# Обработчик для запуска симулятора быстрого потока
@fast_flow_router.callback_query(F.data == "fast_flow")
async def start_fast_flow(callback: CallbackQuery, state: FSMContext):
    """Запуск симулятора быстрого потока. | Start the fast flow simulator."""
    await state.clear()
    await state.set_state(FastFlowState.selecting_currency)
    
    await callback.message.answer(
        "*Выберите валюту для Быстрого Потока:*\n\n"
        "*Select the currency for the fast flow:*\n\n"
        "👇👇👇",
        reply_markup=get_fast_flow_currency_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик выбора валюты для быстрого потока
@fast_flow_router.callback_query(FastFlowState.selecting_currency, F.data.startswith("fastflow_currency_"))
async def process_fast_flow_currency_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора валюты для быстрого потока. | Processing the selection of the currency for the fast flow."""
    currency = callback.data.split("_")[2]
    
    # Сохраняем выбранную валюту
    await state.update_data(currency=currency)
    await state.set_state(FastFlowState.selecting_amount)
    
    # Отправляем изображение валюты, если оно есть
    image_path = FAST_FLOW_IMAGES.get(currency)
    if image_path:
        try:
            import os
            from aiogram.types import FSInputFile
            
            # Прямой путь к файлу изображения
            current_dir = os.path.dirname(os.path.abspath(__file__))
            full_image_path = os.path.join(current_dir, "..", image_path)
            print(f"Current directory: {current_dir}")
            print(f"Image path from config: {image_path}")
            print(f"Full image path: {full_image_path}")
            print(f"File exists: {os.path.exists(full_image_path)}")
            
            if os.path.exists(full_image_path):
                photo = FSInputFile(full_image_path)
                await callback.message.answer_photo(
                    photo=photo,
                    caption=f"*Выберите номинал Быстрого Потока | Select the fast flow amount:  {CURRENCY_SYMBOLS[currency]}*\n\n"
                    "👇👇👇",
                    reply_markup=get_fast_flow_amount_keyboard(currency),
                    parse_mode="Markdown"
                )
                print("Photo sent successfully")
                await callback.answer()
                return
            else:
                print(f"Image file not found at: {full_image_path}")
                # Попробуем найти файл в текущей директории
                alt_path = os.path.join(current_dir, "images", f"fast_flow_{currency.lower()}.jpg")
                print(f"Trying alternative path: {alt_path}")
                if os.path.exists(alt_path):
                    photo = FSInputFile(alt_path)
                    await callback.message.answer_photo(
                        photo=photo,
                        caption=f"*Выберите номинал Быстрого Потока | Select the fast flow amount:  {CURRENCY_SYMBOLS[currency]}*\n\n"
                        "👇👇👇",
                        reply_markup=get_fast_flow_amount_keyboard(currency),
                        parse_mode="Markdown"
                    )
                    print("Photo sent successfully from alternative path")
                    await callback.answer()
                    return
        except Exception as e:
            print(f"Ошибка при отправке фото: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    # Если не удалось отправить фото, просто отправляем текст
    print("Falling back to text-only message")
    await callback.message.answer(
        f"*Выберите номинал Быстрого Потока | Select the fast flow amount:  {CURRENCY_SYMBOLS[currency]}*\n\n"
        "👇👇👇",
        reply_markup=get_fast_flow_amount_keyboard(currency),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик выбора номинала быстрого потока
@fast_flow_router.callback_query(FastFlowState.selecting_amount, F.data.startswith("fastflow_amount_"))
async def process_fast_flow_amount_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора номинала для быстрого потока. | Processing the selection of the fast flow amount."""
    # Парсим данные из callback_data
    _, _, currency, amount_str = callback.data.split("_")
    amount = float(amount_str)
    
    # Получаем данные потока
    flow_data = calculate_fast_flow_data(currency, amount)
    if not flow_data:
        await callback.answer("Ошибка при расчете данных потока", show_alert=True)
        return
    
    # Сохраняем данные потока
    await state.update_data(flow_data=flow_data)
    await state.set_state(FastFlowState.confirming_amount)
    
    # Формируем сообщение подтверждения
    message_text = format_fast_flow_confirmation(flow_data)
    
    await callback.message.answer(
        message_text,
        reply_markup=get_fast_flow_confirmation_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик подтверждения номинала быстрого потока
@fast_flow_router.callback_query(FastFlowState.confirming_amount, F.data == "fastflow_confirm")
async def confirm_fast_flow(callback: CallbackQuery, state: FSMContext):
    """Подтверждение номинала и запуск симуляции быстрого потока. | Confirmation of the amount and start of the fast flow simulation."""
    # Получаем данные из состояния
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    # Переходим к первому дню симуляции
    flow_data = process_day(flow_data)
    
    # Сохраняем обновленные данные
    await state.update_data(flow_data=flow_data)
    await state.set_state(FastFlowState.viewing_flow)
    
    # Отправляем информацию о текущем дне
    message_text = format_fast_flow_stats(flow_data)
    
    await callback.message.answer(
        message_text,
        reply_markup=get_fast_flow_control_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия кнопки "Начислить" в быстром потоке
@fast_flow_router.callback_query(FastFlowState.viewing_flow, F.data == "fastflow_next_day")
async def process_fast_flow_next_day(callback: CallbackQuery, state: FSMContext):
    """Переход к следующему дню симуляции быстрого потока. | Transition to the next day of the fast flow simulation."""
    # Получаем данные из состояния
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    # Если поток завершен, показываем сообщение
    if flow_data.completed:
        await callback.answer("Быстрый поток уже завершен! | The fast flow is already completed!", show_alert=True)
        return
    
    # Переходим к следующему дню симуляции
    flow_data = process_day(flow_data)
    
    # Сохраняем обновленные данные
    await state.update_data(flow_data=flow_data)
    
    # Отправляем информацию о текущем дне
    message_text = format_fast_flow_stats(flow_data)
    
    # Если поток завершен, добавляем сообщение
    if flow_data.completed:
        message_text += "\n\n✅ Быстрый поток завершен! | The fast flow is completed!"
    
    await callback.message.answer(
        message_text,
        reply_markup=get_fast_flow_control_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик возврата к выбору валюты
@fast_flow_router.callback_query(F.data == "fastflow_back_to_currency")
async def back_to_currency_selection(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору валюты. | Return to the currency selection."""
    current_state = await state.get_state()
    print(f"Текущее состояние | Current state: {current_state}, callback_data: {callback.data}")
    
    await state.set_state(FastFlowState.selecting_currency)
    
    # Проверяем, есть ли у сообщения текст
    if callback.message.text:
        await callback.message.answer(
            "*Выберите валюту для Быстрого Потока:*\n\n"
            "*Select the currency for the fast flow:*\n\n"
            "👇👇👇",
            reply_markup=get_fast_flow_currency_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # Если сообщение содержит изображение, отправляем новое текстовое сообщение
        await callback.message.answer(
            "*Выберите валюту для Быстрого Потока:*\n\n"
            "*Select the currency for the fast flow:*\n\n"
            "👇👇👇",
            reply_markup=get_fast_flow_currency_keyboard(),
            parse_mode="Markdown"
        )
    
    await callback.answer()

# Обработчик возврата к выбору номинала
@fast_flow_router.callback_query(FastFlowState.confirming_amount, F.data == "fastflow_back_to_amount")
async def back_to_amount_selection(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору номинала. | Return to the amount selection."""
    # Получаем выбранную валюту из состояния
    data = await state.get_data()
    currency = data.get("currency")
    
    await state.set_state(FastFlowState.selecting_amount)
    
    await callback.message.answer(
        f"*Выберите номинал Быстрого Потока | Select the fast flow amount:  {CURRENCY_SYMBOLS[currency]}*\n\n"
        "👇👇👇",
        reply_markup=get_fast_flow_amount_keyboard(currency),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия кнопки "Заново"
@fast_flow_router.callback_query(F.data == "fastflow_restart")
async def restart_fast_flow(callback: CallbackQuery, state: FSMContext):
    """Перезапуск симулятора быстрого потока. | Restart the fast flow simulator."""
    await state.clear()
    await state.set_state(FastFlowState.selecting_currency)
    
    await callback.message.answer(
        "*Выберите валюту для Быстрого Потока:*\n\n"
        "*Select the currency for the fast flow:*\n\n"
        "👇👇👇",
        reply_markup=get_fast_flow_currency_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик возврата в меню симуляторов
@fast_flow_router.callback_query(F.data == "back_to_simulators")
async def back_to_simulators(callback: CallbackQuery, state: FSMContext):
    """Возврат в меню симуляторов. | Return to the simulators menu."""
    await state.clear()
    
    await callback.message.answer(
        "*Выберите симулятор:*\n\n"
        "*Select the simulator:*\n\n"
        "👇👇👇",
        reply_markup=get_simulators_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик возврата к выбору валюты из экрана выбора номинала
@fast_flow_router.callback_query(FastFlowState.selecting_amount, F.data == "fastflow_back_to_currency")
async def back_to_currency_from_amount(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору валюты из экрана выбора номинала. | Return to the currency selection from the amount selection screen."""
    await state.set_state(FastFlowState.selecting_currency)
    
    await callback.message.answer(
        "*Выберите валюту для Быстрого Потока:*\n\n"
        "*Select the currency for the fast flow:*\n\n"
        "👇👇👇",
        reply_markup=get_fast_flow_currency_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer() 