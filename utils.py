from states import FlowData
from config import (
    CURRENCY_RATES,
    CURRENCY_SYMBOLS,
    INITIAL_PERCENT,
    CURRENCY_BONUS_RATES,
    ECR_SELL_RATE,
    ECR_BUY_RATE
)
import aiohttp
import logging
from typing import Dict

# Импортируем функции из currency_rates
try:
    from currency_rates import get_ecr_count_for_amount
except ImportError:
    # Заглушка
    def get_ecr_count_for_amount(amount_rub): return amount_rub / 4380

def convert_to_rub(amount: float, currency: str) -> float:
    """Конвертировать сумму в рубли | Convert amount to rubles"""
    return amount * CURRENCY_RATES[currency]

def convert_from_rub(amount_rub: float, currency: str) -> float:
    """Конвертировать сумму из рублей в указанную валюту | Convert amount from rubles to the specified currency"""
    return amount_rub / CURRENCY_RATES[currency]

def get_bonus_percent(amount: float, currency: str) -> float:
    """Получить процент бонуса для суммы в указанной валюте | Get bonus percentage for the amount in the specified currency"""
    bonus_rates = CURRENCY_BONUS_RATES.get(currency, [])
    
    # Сортируем от большой суммы к меньшей
    sorted_rates = sorted(bonus_rates, key=lambda x: x[0], reverse=True)
    
    for min_amount, bonus_percent in sorted_rates:
        if amount >= min_amount:
            # Для бонуса 150% множитель должен быть 2.5 (1 + 1.5)
            # Поскольку в CURRENCY_BONUS_RATES уже указан процент (например, 150),
            # то множитель равен 1 + (процент / 100)
            bonus_multiplier = 1 + (bonus_percent / 100)
            print(f"Для суммы {amount} найден бонус {bonus_percent}%, множитель: {bonus_multiplier}")
            print(f"For the sum of {amount} bonus found {bonus_percent}%, multiplier: {bonus_multiplier}")
            return bonus_multiplier
    
    return 1.0  # Базовый множитель, если нет бонуса

def calculate_ecr_costs(amount_rub: float) -> float:
    """Рассчитать затраты на ECR в рублях | Calculate the costs of ECR in rubles"""
    # Получаем количество ECR для суммы
    ecr_count = get_ecr_count_for_amount(amount_rub)
    
    # Стоимость покупки ECR по курсу продажи на бирже
    cost = ecr_count * ECR_SELL_RATE
    
    return cost

def calculate_flow_data(amount: float, currency: str) -> FlowData:
    """Рассчитать данные потока на основе суммы и валюты | Calculate the flow data based on the amount and currency"""
    # Создаем объект FlowData
    flow_data = FlowData(currency)
    flow_data.currency = currency
    flow_data.init_amount = amount
    flow_data.income_percent = INITIAL_PERCENT
    flow_data.day_counter = 1
    
    # Рассчитываем бонусный процент
    flow_data.bonus_percent = get_bonus_percent(amount, currency)
    
    # Рассчитываем итоговую сумму с учетом бонуса
    flow_data.total_amount = amount * flow_data.bonus_percent
    
    # Вычисляем сумму только бонуса (без начальной суммы)
    bonus_percent = (flow_data.bonus_percent - 1) * 100
    bonus_only = amount * (bonus_percent / 100)
    
    # Конвертируем сумму бонуса в рубли для расчетов
    bonus_rub = convert_to_rub(bonus_only, currency)
    
    # Рассчитываем количество ECR и затраты на ECR на основе суммы бонуса
    flow_data.ecr_amount = get_ecr_count_for_amount(bonus_rub)
    ecr_cost_rub = calculate_ecr_costs(bonus_rub)
    flow_data.ecr_cost = convert_from_rub(ecr_cost_rub, currency)
    
    # Рассчитываем ежедневный доход
    flow_data.daily_income = flow_data.total_amount * (flow_data.income_percent / 100)
    
    # Создаем первый депозит
    first_deposit = {
        "amount": amount,                     # Начальная сумма депозита
        "bonus_amount": flow_data.total_amount,  # Сумма с бонусом
        "percent": INITIAL_PERCENT,           # Начальный процент
        "daily_income": flow_data.daily_income # Ежедневное начисление
    }
    
    # Добавляем депозит в массив
    flow_data.deposits.append(first_deposit)
    
    print(f"Создан начальный депозит: {amount} с бонусом {flow_data.total_amount}, процент {INITIAL_PERCENT}, начисление {flow_data.daily_income}")
    
    return flow_data

def add_funds_to_flow(flow_data: FlowData, amount: float) -> FlowData:
    """Добавить средства в существующий поток | Add funds to an existing flow"""
    # Сохраняем текущий день и сумму в потоке
    current_day = flow_data.day_counter
    current_total_amount = flow_data.total_amount
    current_init_amount = flow_data.init_amount
    
    # Получаем бонусный процент для новой суммы
    new_bonus_percent = get_bonus_percent(amount, flow_data.currency)
    
    # Рассчитываем сумму с бонусом для новой суммы
    new_amount_with_bonus = amount * new_bonus_percent
    
    # Добавляем к начальной сумме
    flow_data.init_amount += amount
    
    # Добавляем новую сумму с бонусом к текущей сумме в потоке
    flow_data.total_amount = current_total_amount + new_amount_with_bonus
    
    # Рассчитываем средневзвешенный бонусный множитель
    flow_data.bonus_percent = flow_data.total_amount / flow_data.init_amount
    
    # Вычисляем сумму только бонуса для новой суммы
    display_percent_new = (new_bonus_percent - 1) * 100
    bonus_only_new = amount * (display_percent_new / 100)
    
    # Конвертируем сумму бонуса в рубли для расчетов
    bonus_rub_new = convert_to_rub(bonus_only_new, flow_data.currency)
    
    # Рассчитываем количество ECR и затраты на ECR на основе суммы бонуса
    new_ecr_amount = get_ecr_count_for_amount(bonus_rub_new)
    new_ecr_cost_rub = calculate_ecr_costs(bonus_rub_new)
    new_ecr_cost = convert_from_rub(new_ecr_cost_rub, flow_data.currency)
    
    # Добавляем новое количество ECR к текущему
    flow_data.ecr_amount += new_ecr_amount
    flow_data.ecr_cost += new_ecr_cost
    
    # Восстанавливаем текущий день
    flow_data.day_counter = current_day
    
    # Рассчитываем начисление для нового депозита
    new_deposit_daily_income = new_amount_with_bonus * (INITIAL_PERCENT / 100)
    
    # Создаем новый депозит
    new_deposit = {
        "amount": amount,                      # Сумма депозита
        "bonus_amount": new_amount_with_bonus, # Сумма с бонусом
        "percent": INITIAL_PERCENT,            # Начальный процент (0.3%)
        "daily_income": new_deposit_daily_income # Начисление
    }
    
    # Добавляем новый депозит в массив
    flow_data.deposits.append(new_deposit)
    
    # Пересчитываем общее ежедневное начисление как сумму начислений всех депозитов
    total_daily_income = sum(deposit["daily_income"] for deposit in flow_data.deposits)
    flow_data.daily_income = round(total_daily_income * 100) / 100
    
    # В интерфейсе показываем INITIAL_PERCENT для удобства при пополнении
    # Но рассчитываем точный процент как отношение начисления к сумме в потоке
    if flow_data.total_amount > 0:
        flow_data.income_percent = round((flow_data.daily_income / flow_data.total_amount * 100) * 100) / 100
    else:
        flow_data.income_percent = INITIAL_PERCENT
    
    print(f"Пополнение потока: старая сумма {current_init_amount}, новая сумма {amount}, старая сумма в потоке {current_total_amount}, новая сумма в потоке {flow_data.total_amount}")
    print(f"Создан новый депозит: {amount} с бонусом {new_amount_with_bonus}, процент {INITIAL_PERCENT}, начисление {new_deposit_daily_income}")
    print(f"Общее начисление после пополнения: {flow_data.daily_income}, процент: {flow_data.income_percent:.2f}%")
    
    return flow_data

def add_income_to_savings(flow_data: FlowData) -> FlowData:
    """Добавить ежедневный доход в копилку | Add daily income to the savings"""
    flow_data.savings += flow_data.daily_income
    return flow_data

def withdraw_savings(flow_data: FlowData, amount: float) -> FlowData:
    """Вывести средства из копилки | Withdraw funds from the savings"""
    if amount > flow_data.savings:
        amount = flow_data.savings
    
    # Рассчитываем долю снятых средств
    withdrawal_ratio = amount / flow_data.savings
    
    # Сохраняем текущий процент до снятия
    current_percent = flow_data.income_percent
    
    # Обновляем данные копилки
    flow_data.savings -= amount
    flow_data.withdrawn += amount
    
    # Если сняли все средства из копилки, сбрасываем проценты до начального
    if flow_data.savings <= 0:
        # Сбрасываем процент для каждого депозита
        for deposit in flow_data.deposits:
            deposit["percent"] = INITIAL_PERCENT
            deposit["daily_income"] = deposit["bonus_amount"] * (deposit["percent"] / 100)
        
        # Устанавливаем начальный процент
        flow_data.income_percent = INITIAL_PERCENT
    else:
        # При частичном снятии пропорционально снижаем процент
        # Рассчитываем новый процент по формуле оригинального бота
        # Новый процент = текущий - (текущий - начальный) * доля_снятых_средств
        new_percent = current_percent - (current_percent - INITIAL_PERCENT) * withdrawal_ratio
        
        # Округляем новый процент до 2 знаков после запятой
        # Используем специальное округление для точного соответствия оригинальному боту
        new_percent = int(new_percent * 100 + 0.5) / 100
        
        # Устанавливаем этот процент как текущий
        flow_data.income_percent = new_percent
        
        # Рассчитываем новое начисление напрямую из процента и суммы в потоке
        # Это обеспечивает точное соответствие между процентом и начислением
        new_daily_income = (flow_data.total_amount * new_percent / 100)
        
        # Распределяем это начисление между депозитами пропорционально их бонусным суммам
        total_bonus_amount = sum(deposit["bonus_amount"] for deposit in flow_data.deposits)
        
        if total_bonus_amount > 0:
            for deposit in flow_data.deposits:
                deposit_ratio = deposit["bonus_amount"] / total_bonus_amount
                deposit["daily_income"] = new_daily_income * deposit_ratio
                
                # Обратно рассчитываем процент для депозита
                if deposit["bonus_amount"] > 0:
                    deposit["percent"] = (deposit["daily_income"] / deposit["bonus_amount"]) * 100
                else:
                    deposit["percent"] = INITIAL_PERCENT
        else:
            for deposit in flow_data.deposits:
                deposit["percent"] = INITIAL_PERCENT
                deposit["daily_income"] = 0
    
    # Пересчитываем общее ежедневное начисление как сумму начислений всех депозитов
    # и округляем его специальным образом для точного соответствия оригинальному боту
    total_daily_income = sum(deposit["daily_income"] for deposit in flow_data.deposits)
    
    # Специальное округление для соответствия оригинальному боту
    flow_data.daily_income = int((total_daily_income + 0.005) * 100) / 100
    
    print(f"Снятие из копилки: {amount:.2f}, новый процент: {flow_data.income_percent:.2f}%, новое начисление: {flow_data.daily_income:.2f}")
    
    return flow_data

def format_daily_stats(flow_data: FlowData) -> str:
    """Форматировать статистику за день | Format the daily statistics"""
    currency_symbol = CURRENCY_SYMBOLS[flow_data.currency]
    
    # Вычисляем процент для отображения (бонусный процент - 1) * 100
    display_percent = (flow_data.bonus_percent - 1) * 100
    
    # Вычисляем сумму только бонуса (без начальной суммы)
    bonus_only = flow_data.init_amount * (display_percent / 100)
    bonus_rub = convert_to_rub(bonus_only, flow_data.currency)
    
    # Рассчитываем количество ECR только на основе суммы бонуса
    ecr_count = get_ecr_count_for_amount(bonus_rub)
    
    print(f"Форматирование статистики: бонусный множитель {flow_data.bonus_percent}, отображаемый процент {display_percent}%, ECR: {ecr_count:.2f}")
    print(f"Formatting statistics: bonus multiplier {flow_data.bonus_percent}, displayed percentage {display_percent}%, ECR: {ecr_count:.2f}")
    print(f"Текущее начисление: {flow_data.daily_income:.2f}, процент: {flow_data.income_percent:.2f}%")
    
    # Специальное округление для соответствия оригинальному боту
    init_amount = int((flow_data.init_amount + 0.005) * 100) / 100
    total_amount = int((flow_data.total_amount + 0.005) * 100) / 100
    daily_income = int((flow_data.daily_income + 0.005) * 100) / 100
    savings = int((flow_data.savings + 0.005) * 100) / 100
    withdrawn = int((flow_data.withdrawn + 0.005) * 100) / 100

    message = (
        f"*День | Day: {flow_data.day_counter}*\n\n"
        f"Внесено | Added: *{init_amount:.2f}*{currency_symbol}\n"
        f"В потоке| Stream amount: *{total_amount:.2f}*{currency_symbol}\n"
        f"Начисление | Income: *{daily_income:.2f}*{currency_symbol} (*{flow_data.income_percent:.2f}*%)\n"
        f"Копилка | piggy bank: *{savings:.2f}*{currency_symbol}\n"
        f"Выведено | Withdrawn: *{withdrawn:.2f}*{currency_symbol}"
    )
    
    return message

def format_confirmation_message(flow_data: FlowData) -> str:
    """Форматировать сообщение подтверждения | Format the confirmation message"""
    currency_symbol = CURRENCY_SYMBOLS[flow_data.currency]
    
    # Вычисляем процент для отображения (бонусный процент - 1) * 100
    display_percent = (flow_data.bonus_percent - 1) * 100
    
    # Вычисляем только сумму бонуса (без начальной суммы)
    bonus_only = flow_data.init_amount * (display_percent / 100)
    bonus_rub = convert_to_rub(bonus_only, flow_data.currency)
    
    # Рассчитываем количество ECR только на основе суммы бонуса
    ecr_count = get_ecr_count_for_amount(bonus_rub)
    
    # Рассчитываем затраты на ECR
    ecr_cost_rub = ecr_count * ECR_SELL_RATE
    ecr_cost = convert_from_rub(ecr_cost_rub, flow_data.currency)
    
    return (
        f"Начальная сумма: | Initial amount: *{flow_data.init_amount:.2f}*{currency_symbol}\n"
        f"Затраты на ECR: | ECR costs: *{ecr_cost:.2f}*{currency_symbol} (*{ecr_count:.2f}* ECR)\n"
        f"Бонусный процент: | Bonus percentage: *{display_percent:.0f}*%\n"
        f"Итоговая сумма в потоке: | Total stream amount: *{flow_data.total_amount:.2f}*{currency_symbol}\n"
        f"Начисление: | Income: *{flow_data.daily_income:.2f}*{currency_symbol}"
    )

def format_flow_message(flow_data: FlowData) -> str:
    """Форматировать сообщение о потоке | Format the flow message"""
    currency_symbol = CURRENCY_SYMBOLS[flow_data.currency]
    
    return (
        f"Сумма в потоке: | Stream amount: *{flow_data.total_amount:.2f}*{currency_symbol}\n"
        f"Процент начисления: | Income percentage: *{flow_data.income_percent:.2f}*%\n"
        f"Начисление: | Income: *{flow_data.daily_income:.2f}*{currency_symbol}\n"
        f"Копилка: | piggy bank: *{flow_data.savings:.2f}*{currency_symbol}\n"
        f"Выведено: | Withdrawn: *{flow_data.withdrawn:.2f}*{currency_symbol}"
    )

async def get_currency_rates() -> Dict[str, float]:
    """
    Получает актуальные курсы валют с внешнего API
    
    Возвращает:
        Dict[str, float]: Словарь с кодами валют и их курсами к рублю
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.cbr-xml-daily.ru/daily_json.js') as response:
                if response.status == 200:
                    data = await response.json()
                    rates = {}
                    
                    # Добавляем основные валюты
                    if 'Valute' in data:
                        valutes = data['Valute']
                        
                        if 'USD' in valutes:
                            rates['USD'] = valutes['USD']['Value']
                            
                        if 'EUR' in valutes:
                            rates['EUR'] = valutes['EUR']['Value']
                            
                        if 'CNY' in valutes:
                            rates['CNY'] = valutes['CNY']['Value']
                            
                        if 'TRY' in valutes:
                            rates['TRY'] = valutes['TRY']['Value']
                    
                    return rates
                else:
                    logging.error(f"Failed to fetch currency rates. Status: {response.status}")
                    return {
                        'USD': 92.50,
                        'EUR': 99.20,
                        'CNY': 12.80,
                        'TRY': 2.70
                    }
    except Exception as e:
        logging.error(f"Error fetching currency rates: {e}")
        # Возвращаем значения по умолчанию в случае ошибки
        return {
            'USD': 92.50,
            'EUR': 99.20,
            'CNY': 12.80,
            'TRY': 2.70
        } 