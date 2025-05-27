import json
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import MIN_AMOUNT, MAX_AMOUNT, CURRENCY_SYMBOLS, CURRENCY_RATES, CURRENCY_LIMITS, CURRENCY_NAMES, ECR_PURCHASE_RATE, CURRENCY_FLAGS, ECR_BUY_RATE, ECR_SELL_RATE, ECR_ACCUMULATIVE_BUY_RATE
from currency_rates import get_ecr_rub_rate, get_ecr_rate, get_cbr_currency_rates, get_ecr_count_for_amount
from keyboards import (
    get_main_menu,
    get_currency_menu,
    get_confirm_amount_keyboard,
    get_flow_control_keyboard,
    get_flow_control_with_withdraw_keyboard,
    get_simulators_menu,
    get_currency_keyboard,
    get_money_flows_menu
)
from fast_flow_keyboards import get_fast_flow_currency_keyboard
from states import GrowingFlowState, FlowData
from utils import (
    calculate_flow_data,
    add_income_to_savings,
    withdraw_savings,
    add_funds_to_flow,
    format_flow_message,
    format_confirmation_message,
    format_daily_stats,
    convert_to_rub,
    convert_from_rub,
    get_bonus_percent
)

router = Router()

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    # Получаем имя пользователя для приветствия
    user_name = message.from_user.first_name if message.from_user and message.from_user.first_name else "пользователь"
    user_id = message.from_user.id if message.from_user else None
    
    # Добавляем пользователя в базу данных
    try:
        from broadcast_handlers import add_user_to_db
        add_user_to_db(
            user_id=user_id,
            username=message.from_user.username if message.from_user else None,
            first_name=message.from_user.first_name if message.from_user else None,
            last_name=message.from_user.last_name if message.from_user else None,
            chat_id=message.chat.id
        )
    except ImportError:
        pass
    
    await message.answer(
        f"{user_name}, здравствуйте! 🤝 Меня зовут Василий. Я автоматическая система помощи\n\n"
        f"Сохраните меня в отдельную папку или закрепите вверху, что бы не потерять\n\n"
        f"Выберите один из пунктов ниже\n\n"
        f"👇👇👇",
        reply_markup=get_main_menu(user_id)
    )

# Обработчик нажатия на кнопку главного меню
@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    # Получаем имя пользователя для приветствия
    user_name = callback.from_user.first_name if callback.from_user and callback.from_user.first_name else "пользователь"
    user_id = callback.from_user.id if callback.from_user else None
    
    await state.clear()
    await callback.message.answer(
        f"{user_name}, выберите один из пунктов ниже\n\n"
        f"👇👇👇",
        reply_markup=get_main_menu(user_id)
    )
    await callback.answer()

# Обработчик нажатия на кнопку "СИМУЛЯТОРЫ"
@router.callback_query(F.data == "simulators")
async def show_simulators(callback: CallbackQuery):
    await callback.message.answer(
        "*Выберите симулятор:*\n\n"
        "*Select a simulator:*\n\n"
        "👇👇👇",
        reply_markup=get_simulators_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия на кнопку "СИМУЛЯТОР РАСТУЩЕГО ПОТОКА"
@router.callback_query(F.data == "growing_flow")
async def start_growing_flow(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GrowingFlowState.selecting_currency)
    await callback.message.answer(
        "*Выберите валюту для симулятора растущего потока:*\n\n"
        "*Select the currency for the growing flow simulator:*\n\n"
        "👇👇👇",
        reply_markup=get_currency_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия на кнопку "СИМУЛЯТОР БЫСТРОГО ПОТОКА"
@router.callback_query(F.data == "fast_flow")
async def start_fast_flow(callback: CallbackQuery, state: FSMContext):
    # Перенаправляем к обработчику в fast_flow_handlers
    from fast_flow_handlers import start_fast_flow as fast_flow_start
    await fast_flow_start(callback, state)


# Обработчик выбора валюты
@router.callback_query(F.data.startswith("currency_"))
async def process_currency_selection(callback: CallbackQuery, state: FSMContext):
    currency = callback.data.split("_")[1]
    currency_name = CURRENCY_NAMES.get(currency, "неизвестная валюта | unknown currency")
    currency_limits = CURRENCY_LIMITS[currency]
    min_amount = currency_limits["min"]
    max_amount = currency_limits["max"]
    currency_symbol = CURRENCY_SYMBOLS[currency]
    
    await state.update_data(currency=currency)
    await state.set_state(GrowingFlowState.entering_amount)
    
    await callback.message.answer(
        f"Вы выбрали: {currency_name}. Введите начальную сумму.\n"
        f"*Цифрами без пробелов от: {min_amount} до: {max_amount}{currency_symbol}*\n\n"
        f"You selected: {currency_name}. Enter the initial amount.\n"
        f"*In numbers without spaces from: {min_amount} to: {max_amount}{currency_symbol}*\n\n"
        f"👇👇👇",
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик ввода суммы
@router.message(GrowingFlowState.entering_amount)
async def process_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    currency = data.get("currency")
    currency_limits = CURRENCY_LIMITS[currency]
    min_amount = currency_limits["min"]
    max_amount = currency_limits["max"]
    currency_symbol = CURRENCY_SYMBOLS[currency]
    
    try:
        amount = float(message.text.strip().replace(" ", ""))
    except ValueError:
        await message.answer(
            f"*Пожалуйста, введите корректное число без пробелов от {min_amount} до {max_amount}{currency_symbol}*\n\n"
            f"*Please enter a valid number without spaces from: {min_amount} to: {max_amount}{currency_symbol}*\n\n"
            f"👇👇👇",
            parse_mode="Markdown"
        )
        return
    
    if amount < min_amount or amount > max_amount:
        await message.answer(
            f"*Сумма должна быть от {min_amount} до {max_amount}{currency_symbol}*\n\n"
            f"*The amount must be from: {min_amount} to: {max_amount}{currency_symbol}*\n\n"
            f"👇👇👇",
            parse_mode="Markdown"
        )
        return
    
    flow_data = calculate_flow_data(amount, currency)
    await state.update_data(flow_data=flow_data)
    await state.set_state(GrowingFlowState.confirming_amount)
    
    message_text = format_confirmation_message(flow_data)
    await message.answer(
        message_text,
        reply_markup=get_confirm_amount_keyboard(),
        parse_mode="Markdown"
    )

# Обработчик подтверждения суммы
@router.callback_query(GrowingFlowState.confirming_amount, F.data == "confirm_amount")
async def confirm_amount(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    print(f"\n[ПОДТВЕРЖДЕНИЕ] День: {flow_data.day_counter}")
    print(f"Сумма в потоке до начисления: {flow_data.total_amount:.2f}")
    print(f"Ежедневное начисление: {flow_data.daily_income:.2f}")
    
    # Сохраняем начисление в копилку
    flow_data.savings = flow_data.daily_income
    
    # Уменьшаем сумму в потоке
    flow_data.total_amount -= flow_data.daily_income
    
    # Важно: обрабатываем каждый депозит отдельно
    # Мы должны уменьшить каждый депозит на его ежедневное начисление
    for i, deposit in enumerate(flow_data.deposits):
        daily_income = deposit["daily_income"]
        
        # Уменьшаем бонусную сумму депозита на его начисление
        deposit["bonus_amount"] -= daily_income
        
        # Увеличиваем процент
        deposit["percent"] += 0.01
        
        # Рассчитываем новое начисление для этого депозита
        deposit["daily_income"] = deposit["bonus_amount"] * (deposit["percent"] / 100)
    
    # Пересчитываем общее начисление как сумму начислений всех депозитов
    new_total_income = 0
    for deposit in flow_data.deposits:
        new_total_income += deposit["daily_income"]
    
    # Обновляем общее ежедневное начисление с округлением до 2 знаков только для отображения
    flow_data.daily_income = round(new_total_income * 100) / 100
    
    # В первый день процент устанавливается на 0.31%
    flow_data.income_percent = 0.31
    
    # Логируем результат для отладки
    print(f"[ПОСЛЕ ПОДТВЕРЖДЕНИЯ] День: {flow_data.day_counter}")
    print(f"Сумма в потоке: {flow_data.total_amount:.2f}")
    print(f"Новое ежедневное начисление: {flow_data.daily_income:.2f}")
    print(f"Копилка: {flow_data.savings:.2f}")
    
    await state.update_data(flow_data=flow_data)
    await state.set_state(GrowingFlowState.viewing_flow)
    
    message_text = format_daily_stats(flow_data)
    keyboard = get_flow_control_with_withdraw_keyboard() if flow_data.savings > 0 else get_flow_control_keyboard()
    
    await callback.message.answer(
        message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия на кнопку "НАЧИСЛИТЬ"
@router.callback_query(GrowingFlowState.viewing_flow, F.data == "add_income")
async def add_income(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    print(f"\n[НАЧИСЛЕНИЕ] День: {flow_data.day_counter}")
    print(f"Сумма в потоке до начисления: {flow_data.total_amount:.2f}")
    print(f"Ежедневное начисление: {flow_data.daily_income:.2f}")
    print(f"Копилка до: {flow_data.savings:.2f}")
    
    # Добавляем начисление в копилку
    flow_data.savings += flow_data.daily_income
    
    # Уменьшаем сумму в потоке
    flow_data.total_amount -= flow_data.daily_income
    
    # Важно: обрабатываем каждый депозит отдельно
    # Мы должны уменьшить каждый депозит на его ежедневное начисление
    for i, deposit in enumerate(flow_data.deposits):
        daily_income = deposit["daily_income"]
        
        # Уменьшаем бонусную сумму депозита на его начисление
        deposit["bonus_amount"] -= daily_income
        
        # Увеличиваем процент
        deposit["percent"] += 0.01
        
        # Рассчитываем новое начисление для этого депозита
        deposit["daily_income"] = deposit["bonus_amount"] * (deposit["percent"] / 100)
    
    # Увеличиваем счетчик дней
    flow_data.day_counter += 1
    
    # Пересчитываем общее ежедневное начисление как сумму начислений всех депозитов
    new_total_income = 0
    for deposit in flow_data.deposits:
        new_total_income += deposit["daily_income"]
    
    # Обновляем общее ежедневное начисление с округлением до 2 знаков только для отображения
    flow_data.daily_income = round(new_total_income * 100) / 100
    
    # Рассчитываем средневзвешенный процент для отображения (для наглядности)
    if flow_data.total_amount > 0:
        avg_percent = 0
        deposit_count = len(flow_data.deposits)
        if deposit_count > 0:
            avg_percent = sum(deposit["percent"] for deposit in flow_data.deposits) / deposit_count
        flow_data.income_percent = avg_percent
    
    # Логируем результат для отладки
    print(f"[ПОСЛЕ НАЧИСЛЕНИЯ] День: {flow_data.day_counter}")
    print(f"Сумма в потоке: {flow_data.total_amount:.2f}")
    print(f"Новое ежедневное начисление: {flow_data.daily_income:.2f}")
    print(f"Копилка после: {flow_data.savings:.2f}")
    print(f"Средневзвешенный процент: {flow_data.income_percent:.2f}%")
    
    await state.update_data(flow_data=flow_data)
    
    message_text = format_daily_stats(flow_data)
    keyboard = get_flow_control_with_withdraw_keyboard() if flow_data.savings > 0 else get_flow_control_keyboard()
    
    await callback.message.answer(
        message_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия на кнопку "ВЫВЕСТИ"
@router.callback_query(GrowingFlowState.viewing_flow, F.data == "withdraw")
async def prompt_withdraw(callback: CallbackQuery, state: FSMContext):
    # Получаем данные потока
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    if flow_data.savings <= 0:
        await callback.answer("В копилке нет средств для вывода | There are no funds in the savings for withdrawal")
        return
    
    # Создаем клавиатуру с кнопкой "Вывести все"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вывести все | Withdraw all", callback_data="withdraw_all")],
        [InlineKeyboardButton(text="Отмена | Cancel", callback_data="cancel_withdraw")]
    ])
    
    currency_symbol = CURRENCY_SYMBOLS[flow_data.currency]
    await callback.message.answer(
        f"*В копилке доступно: {flow_data.savings:.2f}{currency_symbol}*\n"
        f"Введите сумму для вывода или нажмите 'Вывести все'\n\n"
        f"*Available in the savings: {flow_data.savings:.2f}{currency_symbol}*\n"
        f"*Enter the amount to withdraw or click 'Withdraw all'*\n\n"
        f"👇👇👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await state.set_state(GrowingFlowState.withdrawing_funds)
    await callback.answer()

# Обработчик нажатия на кнопку "Вывести все"
@router.callback_query(GrowingFlowState.withdrawing_funds, F.data == "withdraw_all")
async def handle_withdraw_all(callback: CallbackQuery, state: FSMContext):
    # Получаем данные потока
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    # Выводим все средства
    all_savings = flow_data.savings
    flow_data = withdraw_savings(flow_data, all_savings)
    
    # Сохраняем обновленные данные
    await state.update_data(flow_data=flow_data)
    
    # Возвращаемся к просмотру потока
    await state.set_state(GrowingFlowState.viewing_flow)
    
    # Показываем обновленную статистику
    message_text = format_daily_stats(flow_data)
    keyboard = get_flow_control_keyboard()
    
    await callback.message.answer(
        f"*Средства успешно выведены!*\n\n{message_text}\n\n"
        f"*Funds successfully withdrawn!*\n\n{message_text}\n\n"
        f"👇👇👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик нажатия на кнопку "Отмена"
@router.callback_query(GrowingFlowState.withdrawing_funds, F.data == "cancel_withdraw")
async def handle_cancel_withdraw(callback: CallbackQuery, state: FSMContext):
    # Получаем данные потока
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    # Возвращаемся к просмотру потока
    await state.set_state(GrowingFlowState.viewing_flow)
    
    # Показываем текущую статистику
    message_text = format_daily_stats(flow_data)
    keyboard = get_flow_control_with_withdraw_keyboard() if flow_data.savings > 0 else get_flow_control_keyboard()
    
    await callback.message.answer(message_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# Обработчик ввода суммы для вывода
@router.message(GrowingFlowState.withdrawing_funds)
async def handle_withdraw_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.strip().replace(" ", ""))
    except ValueError:
        await message.answer("*Пожалуйста, введите корректное число | Please enter a valid number*\n\n"
        f"👇👇👇",
        parse_mode="Markdown"
        )
        return
    
    # Получаем данные потока
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    try:
        # Пытаемся вывести указанную сумму
        flow_data = withdraw_savings(flow_data, amount)
    except ValueError as e:
        await message.answer(str(e))
        return
    
    # Сохраняем обновленные данные
    await state.update_data(flow_data=flow_data)
    
    # Возвращаемся к просмотру потока
    await state.set_state(GrowingFlowState.viewing_flow)
    
    # Показываем обновленную статистику
    message_text = format_daily_stats(flow_data)
    keyboard = get_flow_control_with_withdraw_keyboard() if flow_data.savings > 0 else get_flow_control_keyboard()
    
    await message.answer(
        f"*Средства успешно выведены!*\n\n{message_text}\n\n"
        f"*Funds successfully withdrawn!*\n\n{message_text}\n\n"
        f"👇👇👇",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Обработчик нажатия на кнопку "ПОПОЛНИТЬ"
@router.callback_query(GrowingFlowState.viewing_flow, F.data == "add_funds")
async def prompt_add_funds(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GrowingFlowState.adding_funds)  # Новое состояние для пополнения
    
    await callback.message.answer(
        f"Введите сумму пополнения Растущего Потока.\n"
        f"*Цифрами без пробелов от: {MIN_AMOUNT} до: {MAX_AMOUNT}*\n\n"
        f"Enter the amount to replenish the Growing Flow.\n"
        f"*In numbers without spaces from: {MIN_AMOUNT} to: {MAX_AMOUNT}*\n\n"
        f"👇👇👇",
        parse_mode="Markdown"
    )
    await callback.answer()

# Обработчик ввода суммы для пополнения существующего потока
@router.message(GrowingFlowState.adding_funds)
async def handle_additional_amount(message: Message, state: FSMContext):
    # Получаем текущие данные потока для определения валюты
    data = await state.get_data()
    flow_data = data.get("flow_data")
    
    # Получаем лимиты для текущей валюты
    currency = flow_data.currency
    currency_limits = CURRENCY_LIMITS[currency]
    min_amount = currency_limits["min"]
    max_amount = currency_limits["max"]
    currency_symbol = CURRENCY_SYMBOLS[currency]
    
    try:
        amount = float(message.text.strip().replace(" ", ""))
        if amount < min_amount or amount > max_amount:
            await message.answer(
                f"*Сумма должна быть от {min_amount} до {max_amount}{currency_symbol}*\n\n"
                f"*The amount must be from: {min_amount} to: {max_amount}{currency_symbol}*\n\n"
                f"👇👇👇",
                parse_mode="Markdown"
            )
            return
    except ValueError:
        await message.answer(
            f"*Пожалуйста, введите корректное число без пробелов от {min_amount} до {max_amount}{currency_symbol}*\n\n"
            f"*Please enter a valid number without spaces from: {min_amount} to: {max_amount}{currency_symbol}*\n\n"
            f"👇👇👇",
            parse_mode="Markdown"
        )
        return
    
    # Сохраняем текущую сумму в потоке для информирования пользователя
    current_total = flow_data.total_amount
    
    # Рассчитываем бонусный процент для новой суммы
    bonus_percent = get_bonus_percent(amount, currency)
    display_percent = (bonus_percent - 1) * 100
    
    # Рассчитываем количество ECR для новой суммы
    bonus_amount = amount * (display_percent / 100)
    bonus_rub = convert_to_rub(bonus_amount, currency)
    ecr_count = get_ecr_count_for_amount(bonus_rub)
    
    # Добавляем средства к потоку
    flow_data = add_funds_to_flow(flow_data, amount)
    
    # Сохраняем обновленные данные
    await state.update_data(flow_data=flow_data)
    
    # Формируем сообщение с подтверждением пополнения
    confirmation_message = (
        f"💰 Пополнение успешно! | Deposit successful! 💰\n\n"
        f"Пополнено на сумму: | Deposit amount: *{amount:.2f}*{currency_symbol}\n"
        f"Процент умножения: | Multiplication percentage: *{display_percent:.0f}*%\n"
        f"Кол-во ECR: | ECR amount: *{ecr_count:.2f}* ECR\n"
        f"Сумма с бонусом: | Amount with bonus: *{amount * bonus_percent:.2f}*{currency_symbol}\n"
    )
    
    # Отправляем сообщение с информацией о пополнении
    await message.answer(
        confirmation_message,
        parse_mode="Markdown"
    )
    
    # Форматируем сообщение с дневной статистикой
    message_text = format_daily_stats(flow_data)
    
    # Отправляем сообщение с обновленными данными
    await message.answer(
        message_text,
        reply_markup=get_flow_control_with_withdraw_keyboard() if flow_data.savings > 0 else get_flow_control_keyboard(),
        parse_mode="Markdown"
    )
    
    # Возвращаемся в состояние управления потоком
    await state.set_state(GrowingFlowState.viewing_flow)

# Обработчик нажатия на кнопку "ЗАНОВО"
@router.callback_query(F.data == "restart")
async def restart_simulator(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(GrowingFlowState.selecting_currency)
    
    await callback.message.answer(
        "*Выберите валюту:*\n\n"
        "*Select the currency:*\n\n"
        "👇👇👇",
        reply_markup=get_currency_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "money_flows")
async def show_money_flows(callback: CallbackQuery):
    await callback.message.answer(
        "*Выберите тип денежного потока:*\n\n"
        "*Select the type of money flow:*\n\n"
        "👇👇👇",
        reply_markup=get_money_flows_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "lucky_flow")
async def lucky_flow(callback: CallbackQuery):
    lucky_flow_text = (
       "https://t.me/potokcashi/18"
    )
    
    # Отправляем текстовое сообщение
    await callback.message.answer(lucky_flow_text)
    await callback.answer()

@router.callback_query(F.data == "savings_flow")
async def savings_flow(callback: CallbackQuery):
    savings_flow_text = (
        "Накопительный Поток (НП) - это поток без требования активности, который необходимо пополнять на фиксированную сумму ежемесячно на протяжении выбранного периода (от 3 до 25 лет). По истечении периода накопления начинается период выплат - ежемесячное получение средств увеличенных во много раз благодаря подтяжке eCurrency.\n\n"
        "Сумма вознаграждения в Накопительный Поток зависит от периода накопления и суммы создания потока: чем больше и то и другое, тем больше приумножение средств.\n\n"
    )
    
    # Отправляем основное текстовое сообщение
    await callback.message.answer(savings_flow_text)
    
    # Отправляем картинку с текстом в подписи
    try:
        from aiogram.types import FSInputFile
        image_path = "images/accumulative_flow.jpg"
        photo = FSInputFile(image_path)
        
        # Отправляем фото
        await callback.message.answer_photo(
            photo=photo,
            caption="Схема работы Накопительного Потока | Scheme of work of the Savings Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке изображения: {e}")
    
    # Отправляем первое видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/17",
            caption="Подробнее о Накопительном Потоке | More about the Savings Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке первого видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Видео о Накопительном Потоке: https://t.me/potokcashi/17\n\n"
            "📹 More about the Savings Flow: https://t.me/potokcashi/17"
        )
    
    # Отправляем второе видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/48",
            caption="Еще одно видео о Накопительном Потоке | Another video about the Savings Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке второго видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Еще одно видео о Накопительном Потоке: https://t.me/potokcashi/48\n\n"
            "📹 Another video about the Savings Flow: https://t.me/potokcashi/48"
        )
    
    await callback.answer()

@router.callback_query(F.data == "super_fast_flow")
async def super_fast_flow(callback: CallbackQuery):
    super_fast_flow_text = (
        "Супер Быстрый Поток (СБП) - это финансовая программа для тех, кто ориентирован на максимально быстрый результат, позволяющая получить прибыль уже через 15 дней.\n\n"
        "Поток можно создать на фиксированную сумму. Внесенная сумма увеличивается за счет подтяжки криптовалюты ECR и выплачивается через 15 дней начислений целиком, вне зависимости от обычного дня вывода.\n\n"
        "5000 — +10.1%\n"
        "10 000 — +7.1%\n"
        "25 000 — +5.9%\n"
        "45 000 — +5.6%\n"
        "50 000 — +5.6%\n"
        "55 000 — +5.3%\n"
        "70 000 — +5%\n"
        "75 000 — +5%\n"
        "100 000 — +4.4%\n"
        "110 000 — +4.4%\n"
        "130 000 — +4.4%\n"
        "140 000 — +4.4%\n"
        "170 000 — +4.1%\n"
        "250 000 — +4.1%\n"
        "500 000 — +3.5%\n"
        "750 000 — +3%\n"
        "1 000 000 — +2.6%\n\n"
    )
    
    # Отправляем текстовое сообщение
    await callback.message.answer(super_fast_flow_text)
    await callback.answer()

@router.callback_query(F.data == "fast_flow_real")
async def fast_flow_real(callback: CallbackQuery):
    fast_flow_text = (
        "Быстрый Поток (БП) - это особенная финансовая программа для тех, кто ориентирован на быстрый результат, позволяющая получить прибыль менее, чем через месяц с начала участия.\n\n"
        "Поток можно создать на фиксированную сумму. Внесенная сумма увеличивается за счет подтяжки криптовалюты ECR и выплачивается в течение 30 дней ежедневно равными частями.\n\n"
        "Эти выплаты доступны к выводу ежедневно!"
    )
    
    # Отправляем основное текстовое сообщение
    await callback.message.answer(fast_flow_text)
    
    # Отправляем первое видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/4",
            caption="Видео о Быстром Потоке"
        )
    except Exception as e:
        print(f"Ошибка при отправке первого видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Видео о Быстром Потоке: https://t.me/potokcashi/4"
        )
    
    # Отправляем второе видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/45",
            caption="Еще одно видео о Быстром Потоке | Another video about the Fast Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке второго видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Еще одно видео о Быстром Потоке: https://t.me/potokcashi/45\n\n"
            "📹 Another video about the Fast Flow: https://t.me/potokcashi/45"
        )
    
    await callback.answer()

@router.callback_query(F.data == "growing_flow_real")
async def growing_flow_real(callback: CallbackQuery):
    growing_flow_text = (
        "Растущий Поток (РП) - это инновационная финансовая программа, прибыльность которой возрастает со временем.\n\n"
        "Сделанный взнос можно значительно увеличить за счет подтяжки криптовалюты ECR, причём по курсу, который многократно превышает рыночный. В первый день на внесенную сумму начисляется 0.3% премии, и в дальнейшем премия ежедневно растет на 0.01%.\n\n"
        "Также Растущий Поток можно бесконечно увеличивать за счет добавления новых средств.\n\n"
        "При разумном соотношении снятия премии и реинвестирования Растущий Поток обеспечит постоянный рост Вашего благосостояния!\n\n"
        "Сумма криптовалюты ECR, за счет подтяжки которой можно увеличить взнос, зависит от суммы пополнения:\n\n"
        "от 1000 — +50%\n"
        "от 5000 — +75%\n"
        "от 10 000 — +100%\n"
        "от 50 000 — +125%\n"
        "от 100 000 — +150%\n"
        "от 500 000 — +175%\n"
        "от 1 000 000 — +200%"
    )
    
    # Отправляем основное текстовое сообщение
    await callback.message.answer(growing_flow_text)
    
    # Отправляем первое видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/16",
            caption="Подробнее о Растущем Потоке | More about the Growing Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке первого видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Видео о Растущем Потоке: https://t.me/potokcashi/16\n\n"
            "📹 More about the Growing Flow: https://t.me/potokcashi/16"
        )
    
    # Отправляем второе видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/47",
            caption="Еще одно видео о Растущем Потоке | Another video about the Growing Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке второго видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Еще одно видео о Растущем Потоке: https://t.me/potokcashi/47\n\n"
            "📹 Another video about the Growing Flow: https://t.me/potokcashi/47"
        )
    
    await callback.answer()

@router.callback_query(F.data == "start_flow")
async def start_flow(callback: CallbackQuery):
    start_flow_text = (
        "Стартовый Поток (СП) - это не имеющая аналогов, инновационная финансовая программа, которая разработана специально для новичков проекта и призвана обеспечить им легкий, быстрый и максимально выгодный старт, на практике обучая всем нюансам работы системы ПотокCash.\n\n"
        "Стартовый Поток может быть создан на произвольную сумму.\n\n"
        "Потоки любого номинала работают на общем принципе: это потоки с обязательным пополнением на фиксированную сумму дважды в месяц.\n\n"
        "Доходность потока за 20 периодов (10 месяцев) реализуется за счет подтяжки криптовалюты eCurrency (ECR) по льготному курсу (СУЩЕСТВЕННО выше рыночного).\n\n"
        "В зависимости от номинала Стартовый Поток, eCurrency принимаются по разному курсу, чем больше номинал потока, тем более выгодный курс.\n\n"
        "По прошествии нескольких недель вознаграждение в Стартовый Поток начинает превышать сумму регулярного пополнения\n\n"
        "Ускоренный Стартовый Поток (УСП) - это подвид Стартовый Поток - более быстрый и ещё более выгодный.\n\n"
        "Главной особенностью Ускоренный Стартовый Поток является то, что вы одномоментно вносите сумму его номинала в 4-х кратном размере и уже с первой выплаты получаете больше, чем номинал потока, как будто начался не 1-й а 6-й период, а 5 вы проскочили.\n\n"
        "В дальнейшем вы дважды в месяц пополняете его на одну и ту же сумму, и каждая последующая выплата будет больше предыдущей, так же как и в стандартных Стартовый Поток."
    )
    
    # Отправляем основное текстовое сообщение
    await callback.message.answer(start_flow_text)
    
    # Отправляем первое видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/5",
            caption="Дополнительная информация о Стартовом Потоке | Additional information about the Start Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке первого видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Видео о Стартовом Потоке: https://t.me/potokcashi/5\n\n"
            "📹 Additional information about the Start Flow: https://t.me/potokcashi/5"
        )
    
    # Отправляем второе видео напрямую
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/46",
            caption="Еще одно видео о Стартовом Потоке | Another video about the Start Flow"
        )
    except Exception as e:
        print(f"Ошибка при отправке второго видео: {e}")
        # Если не удалось отправить видео напрямую, отправляем ссылку
        await callback.message.answer(
            "📹 Еще одно видео о Стартовом Потоке: https://t.me/potokcashi/46\n\n"
            "📹 Another video about the Start Flow: https://t.me/potokcashi/46"
        )
    
    await callback.answer()

@router.callback_query(F.data == "fund_registration")
async def fund_registration(callback: CallbackQuery):
    registration_text = (
        "МОЯ 1-я ЛИНИЯ И ЛИЧНОЕ СОПРОВОЖДЕНИЕ НА ВСЕХ ПЛАТФОРМАХ 👇😉\n\n"
        "‼️Регистрация и вход на платформы через вкл. VPN 👇\n\n"
        "🇷🇺 РФ и СНГ — https://potok.cash/ref/HPLTzKyq\n"
        "🇪🇺 EURO — https://eur.cashflow.fund/ref/ncPTzKyq\n"
        "🇪🇸 Испания — https://es.cashflow.fund/ref/nmbTzKyq\n"
        "🇵🇱 Польша — https://pl.cashflow.fund/ref/3sHTzKyq\n"
        "🇰🇬 Кыргызстан — https://cashflow-kg.fund/ref/XsPTzKyq\n"
        "🇬🇧 Великобритания — https://gb.cashflow.fund/ref/XZbTzKyq\n"
        "🇨🇳 Китай — https://cn.cashflow.fund/ref/XsbTzKyq\n\n"
        "‼️Узнать подробнее или написать в личку 🤝😎👇\n\n"
        "Мой телеграм — https://t.me/konvict171\n"
        "Гостевой чат — https://t.me/potokcashchat\n\n"
        "Философия Дмитрия Васадина — https://t.me/kodvasadin"
    )
    
    # Отправляем текстовое сообщение
    await callback.message.answer(registration_text)
    await callback.answer()

@router.callback_query(F.data == "fund_deposit")
async def fund_deposit(callback: CallbackQuery):
    deposit_text = (
        "Пополнение Сберкассы & Money Storage через 📱 CryptoBot (https://t.me/send?start=r-yfe2e)\n\n"
        "❌ Без верификаций и блокировок\n\n"
        "✅Быстро и легко\n\n"
        "✅От 1000₽\n\n"
        "✅С банковской карты любой страны\n\n"
        "🇸🇧 ✅ 👽 💧 🇸🇧🔄 💲\n\n"
        "Ссылка на 👉 P2P Маркет (https://t.me/send?start=r-yfe2e-market) 👈 жми сюда"

        "Deposit to Sberbank & Money Storage through 📱 CryptoBot (https://t.me/send?start=r-yfe2e)\n\n"
        "❌ No verifications and blockages\n\n"
        "✅ Fast and easy\n\n"
        "✅ From 1000₽\n\n"
        "✅ From any country's bank card\n\n"
        "🇸🇧 ✅ 👽 💧 🇸🇧🔄 💲\n\n"
        "Link to 👉 P2P Market (https://t.me/send?start=r-yfe2e-market) 👈 click here"
    )
    
    # Отправляем текстовое сообщение
    await callback.message.answer(deposit_text)
    
    # Отправляем видео
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/131",
            caption="Инструкция по пополнению | Deposit instructions"
        )
    except Exception as e:
        print(f"Ошибка при отправке видео: {e}")
        await callback.message.answer(
            "📹 Видео-инструкция: https://t.me/potokcashi/131\n\n"
            "📹 Video instructions: https://t.me/potokcashi/131"
        )
    
    await callback.answer()

@router.callback_query(F.data == "fund_withdrawal")
async def fund_withdrawal(callback: CallbackQuery):
    withdrawal_text = (
        "ВЫВОД из Сберкассы на банковскую карту через 📱 CryptoBot (https://t.me/send?start=r-yfe2e)\n\n"
        "🛡️Безопасно\n\n"
        "💵 🔄 🇸🇧 ✅ 👽 💧 🇸🇧\n\n"
        "Ссылка на 👉 P2P Маркет (https://t.me/send?start=r-yfe2e-market) 👈 жми сюда"

        "Withdrawal from Sberbank to bank card through 📱 CryptoBot (https://t.me/send?start=r-yfe2e)\n\n"
        "🛡️Safe\n\n"
        "💵 🔄 🇸🇧 ✅ 👽 💧 🇸🇧\n\n"
        "Link to 👉 P2P Market (https://t.me/send?start=r-yfe2e-market) 👈 click here"
    )
    
    # Отправляем текстовое сообщение
    await callback.message.answer(withdrawal_text)
    
    # Отправляем видео
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/132",
            caption="Инструкция по выводу | Withdrawal instructions"
        )
    except Exception as e:
        print(f"Ошибка при отправке видео: {e}")
        await callback.message.answer(
            "📹 Видео-инструкция: https://t.me/potokcashi/132\n\n"
            "📹 Video instructions: https://t.me/potokcashi/132"
        )
    
    await callback.answer()

@router.callback_query(F.data == "buy_ecurrency")
async def buy_ecurrency(callback: CallbackQuery):
    ecurrency_text = "Инструкция по покупке криптовалюты eCurrency: | Instruction for buying eCurrency:"
    
    # Отправляем текстовое сообщение
    await callback.message.answer(ecurrency_text)
    
    # Отправляем видео
    try:
        await callback.message.answer_video(
            video="https://t.me/potokcashi/102",
            caption="Видео-инструкция | Video instruction"
        )
    except Exception as e:
        print(f"Ошибка при отправке видео: {e}")
        await callback.message.answer(
            "📹 Видео-инструкция: https://t.me/potokcashi/102\n\n"
            "📹 Video instruction: https://t.me/potokcashi/102"
        )
    
    await callback.answer()

@router.callback_query(F.data == "social_networks")
async def show_social_networks(callback: CallbackQuery):
    social_networks_text = (
        "ПОДПИСЫВАЙТЕСЬ И ДОБАВЛЯЙТЕСЬ В ДРУЗЬЯ 😉\n\n"
        "👇👇👇\n\n"
        "Вконтакте (2000 + друзей) — https://vk.com/buisness25\n\n"
        "Гостевой чат — https://t.me/matusevich_vpotoke\n\n"
        "YouTube канал (10 000+ подписчиков) — https://www.youtube.com/@matusevich17\n\n"
        "Канал Код Васадина — https://t.me/kodvasadin\n\n"
    )
    
    await callback.message.answer(
        social_networks_text,
        reply_markup=get_main_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    await callback.message.answer(
        "Раздел помощи находится в разработке. Скоро будет доступен!\n\n"
        "The help section is under development. It will be available soon!",
        reply_markup=get_main_menu()
    )
    await callback.answer()

# Добавляем новый обработчик после других команд
@router.message(Command('rates'))
async def cmd_rates(message: Message):
    """Показать текущие курсы валют и ECR | Show the current exchange rates and ECR"""
    rates_text = "💱 Текущие курсы валют | Current exchange rates:\n\n"
    
    # Показываем только курс ECR в рублях
    try:
        # Получаем курс продажи ECR в рублях
        ecr_rub = get_ecr_rub_rate() or ECR_SELL_RATE
        rates_text += f"🔹 ECR (курс покупки пользователем) | ECR (user purchase rate): {ecr_rub:.2f}₽\n\n"
        
 
    except Exception as e:
        rates_text += f"🔹 ECR (курс покупки пользователем) | ECR (user purchase rate): {ECR_SELL_RATE:.2f}₽\n\n"
       
    # Получаем актуальные курсы валют
    currency_rates = get_cbr_currency_rates()
    if currency_rates and "USD" in currency_rates:
        rates_text += f"🇺🇸 USD: {currency_rates['USD']:.4f}₽ за 1$\n"
    
    # Добавляем курсы валют из конфига
    for currency, rate in CURRENCY_RATES.items():
        if currency not in ["RUB", "USD"]:  # Пропускаем рубль и USD (уже показан выше)
            symbol = CURRENCY_SYMBOLS[currency]
            rates_text += f"{CURRENCY_FLAGS.get(currency, '')} {currency}: {rate:.4f}₽ за 1{symbol}\n"
    
    await message.answer(rates_text)

# Заглушки для разделов денежных потоков, теперь это пустой список
@router.callback_query(F.data.in_([]))
async def money_flow_placeholder(callback: CallbackQuery):
    flow_names = {}
    
    flow_name = flow_names.get(callback.data, "Выбранный поток | Selected flow")
    
    try:
        # Пытаемся отредактировать текущее сообщение
        await callback.message.edit_text(
            f"Раздел «{flow_name}» находится в разработке. Скоро будет доступен!\n\n"
            f"The section «{flow_name}» is under development. It will be available soon!",
            reply_markup=get_money_flows_menu()
        )
    except Exception as e:
        # Если не получается отредактировать, то удаляем старое и отправляем новое
        try:
            await callback.message.delete()
        except Exception:
            pass
            
        await callback.message.answer(
            f"Раздел «{flow_name}» находится в разработке. Скоро будет доступен!\n\n"
            f"The section «{flow_name}» is under development. It will be available soon!",
            reply_markup=get_money_flows_menu()
        )
    
    await callback.answer()

# Обработчик кнопки "КУРС ВАЛЮТ"
@router.callback_query(F.data == "show_currency_rates")
async def show_currency_rates(callback: CallbackQuery):
    try:
        await cmd_rates(callback.message)
        await callback.answer()
    except Exception as e:
        logging.error(f"Error in show_currency_rates: {e}")
        await callback.message.answer("❌ Ошибка при получении курсов валют. Попробуйте позже.")
        await callback.answer() 