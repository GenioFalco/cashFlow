"""
Вспомогательные функции для работы с накопительным потоком
"""

from typing import Dict, Optional, Tuple
from accumulative_flow_states import AccumulativeFlowData
from accumulative_flow_config import get_multiplier
from config import CURRENCY_SYMBOLS, ECR_BUY_RATE, CURRENCY_RATES, ECR_ACCUMULATIVE_BUY_RATE
from currency_rates import get_ecr_count_for_amount

def calculate_accumulative_flow_data(currency: str, amount: float, period_years: int) -> Optional[AccumulativeFlowData]:
    """Расчет данных накопительного потока. | Calculation of the accumulative flow data."""
    # Получаем коэффициент умножения
    multiplier = get_multiplier(period_years, amount)
    if not multiplier:
        return None
    
    # Конвертируем сумму в рубли для расчета ECR
    amount_rub = amount * CURRENCY_RATES.get(currency, 1.0)
    
    # Рассчитываем бонус (дополнительную сумму от умножения)
    bonus_amount = amount * (multiplier - 1)
    bonus_amount_rub = bonus_amount * CURRENCY_RATES.get(currency, 1.0)
    
    # Рассчитываем количество необходимых ECR на основе бонуса
    # Используем специальный курс для накопительного потока
    ecr_required = get_ecr_count_for_amount(bonus_amount_rub, is_accumulative=True)
    
    # Создаем данные потока
    flow_data = AccumulativeFlowData(
        currency=currency,
        amount=amount,
        period_years=period_years,
        multiplier=multiplier,
        monthly_contribution=amount,
        ecr_monthly=ecr_required  # Используем рассчитанное значение
    )
    
    # Рассчитываем общую сумму вложений
    # Ежемесячный взнос * количество месяцев
    flow_data.total_input = flow_data.monthly_contribution * (period_years * 12)
    
    # Рассчитываем общую сумму выплат
    # Начальная сумма * коэффициент умножения
    flow_data.total_output = flow_data.amount * flow_data.multiplier * (period_years * 12)
    
    print(f"Накопительный поток: сумма {amount} {currency}, множитель {multiplier}, необходимо ECR: {ecr_required:.2f}")
    
    return flow_data

def format_accumulative_flow_result(flow_data: AccumulativeFlowData) -> str:
    """Форматирование результата накопительного потока для вывода. | Formatting the accumulative flow result for output."""
    currency_symbol = CURRENCY_SYMBOLS[flow_data.currency]
    period_text = f"{flow_data.period_years} {'год | year' if flow_data.period_years == 1 else 'года | years' if 2 <= flow_data.period_years <= 4 else 'лет | years'}"
    
    # Рассчитываем ежемесячную выплату
    monthly_payment = flow_data.amount * flow_data.multiplier
    
    # Округление ECR до 2 знаков после запятой для отображения
    ecr_monthly_display = round(flow_data.ecr_monthly, 2)
    
    message = f"НАКОПИТЕЛЬНЫЙ ПОТОК НОМИНАЛОМ: *{flow_data.amount}*{currency_symbol} "
    message += f"на период *{period_text}* КФ *х{flow_data.multiplier}*\n\n"
    
    message += f"В период накопления необходимо пополнять на фиксированную сумму *{flow_data.amount}*{currency_symbol} "
    message += f"ежемесячно +*{ecr_monthly_display}* ECR по текущему курсу приема: 1 ECR = *{ECR_ACCUMULATIVE_BUY_RATE:.2f}*{currency_symbol}\n\n"
    
    message += f"В период получения фонд будет выплачивать вам *{monthly_payment}*{currency_symbol} "
    message += f"ежемесячно в течении *{period_text}*\n\n"
    
    message += f"Итого отдадите: *{int(flow_data.total_input)}*{currency_symbol}, "
    message += f"а получите: *{int(flow_data.total_output)}*{currency_symbol}"
    
    return message 