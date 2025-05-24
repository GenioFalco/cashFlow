"""
Утилиты для работы с быстрым потоком
"""

from fast_flow_states import FastFlowData
from fast_flow_config import get_fast_flow_option, FAST_FLOW_DAYS
from config import CURRENCY_SYMBOLS, ECR_BUY_RATE, CURRENCY_RATES

def calculate_ecr_count(amount_rub):
    """Расчет количества ECR для суммы в рублях. | Calculation of the number of ECR for the amount in rubles.   """
    # ECR рассчитывается в обратном порядке - нам нужно определить
    # какое количество ECR соответствует сумме в рублях по курсу BUY_RATE
    return amount_rub / ECR_BUY_RATE

def calculate_fast_flow_data(currency, amount):
    """Инициализация данных быстрого потока на основе валюты и суммы. | Initialization of fast flow data based on currency and amount."""
    # Получаем опцию быстрого потока по валюте и сумме
    option = get_fast_flow_option(currency, amount)
    if not option:
        return None
    
    # Создаем объект данных быстрого потока
    flow_data = FastFlowData(currency)
    flow_data.amount = amount
    flow_data.percent = option["percent"]
    flow_data.total_amount = option["total"]
    flow_data.daily_payment = option["daily"]
    flow_data.days_total = FAST_FLOW_DAYS
    flow_data.day_counter = 0
    flow_data.current_balance = flow_data.total_amount
    flow_data.savings = 0
    
    # Для быстрого потока profit уже известен из конфигурации
    profit = option["profit"]
    
    # Конвертируем сумму в рубли по текущему курсу для расчета ECR
    if currency == "RUB":
        profit_rub = profit
    else:
        profit_rub = profit * CURRENCY_RATES.get(currency, 1.0)
    
    # Вычисляем количество ECR на основе профита
    flow_data.ecr_amount = calculate_ecr_count(profit_rub)
    flow_data.ecr_value = profit
    
    return flow_data

def process_day(flow_data):
    """Обрабатывает один день в симуляции быстрого потока. | Processes one day in the fast flow simulation."""
    # Если поток завершен, ничего не делаем
    if flow_data.completed:
        return flow_data
    
    # Увеличиваем счетчик дней
    flow_data.day_counter += 1
    
    # Переводим ежедневную выплату из потока в копилку
    flow_data.current_balance -= flow_data.daily_payment
    flow_data.savings += flow_data.daily_payment
    
    # Проверяем, завершен ли поток
    if flow_data.day_counter >= flow_data.days_total:
        flow_data.completed = True
    
    return flow_data

def format_fast_flow_confirmation(flow_data):
    """Форматирует сообщение подтверждения быстрого потока. | Formats the fast flow confirmation message."""
    currency_symbol = CURRENCY_SYMBOLS[flow_data.currency]
    ecr_rate = ECR_BUY_RATE  # Курс приема ECR системой (в рублях)
    
    return (
        f"Номинал | Nominal: *{flow_data.amount}* {currency_symbol}\n"
        f"Процент умножения | Multiplication percentage: *{flow_data.percent}*%\n"
        f"Кол-во ECR | Number of ECR: *{flow_data.ecr_amount:.2f}* (соответствует *{flow_data.ecr_value:.2f}* {currency_symbol} "
        f"по курсу 1 ECR | at the rate of 1 ECR = *{ecr_rate:.2f}* ₽)\n\n"
        f"В потоке БП | In the fast flow: *{flow_data.total_amount:.2f}* {currency_symbol}"
    )

def format_fast_flow_stats(flow_data):
    """Форматирует статистику текущего дня быстрого потока. | Formats the current day's statistics of the fast flow."""
    currency_symbol = CURRENCY_SYMBOLS[flow_data.currency]
    
    return (
        f"*День | Day: {flow_data.day_counter} / {flow_data.days_total}*\n\n"
        f"В потоке | In the flow: *{flow_data.current_balance:.2f}* {currency_symbol}\n\n"
        f"Начисление | Accrual: *{flow_data.daily_payment:.2f}* {currency_symbol}\n\n"
        f"В кармане | In the pocket: *{flow_data.savings:.2f}* {currency_symbol}"
    ) 