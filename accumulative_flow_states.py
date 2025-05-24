"""
Состояния для работы с симулятором накопительного потока
"""

from aiogram.fsm.state import StatesGroup, State
from dataclasses import dataclass
from typing import Optional, Dict

class AccumulativeFlowState(StatesGroup):
    """Состояния для симулятора накопительного потока. | States for the accumulative flow simulator."""
    selecting_currency = State()  # Выбор валюты
    entering_amount = State()     # Ввод суммы
    selecting_period = State()    # Выбор периода
    viewing_result = State()      # Просмотр результата

@dataclass
class AccumulativeFlowData:
    """Данные симулятора накопительного потока. | Data for the accumulative flow simulator."""
    currency: str                  # Валюта
    amount: float                  # Сумма вклада
    period_years: int              # Период в годах
    multiplier: float              # Коэффициент умножения
    monthly_contribution: float    # Ежемесячный взнос
    ecr_monthly: int = 20          # Ежемесячно начисляемые ECR
    total_input: float = 0         # Общая сумма вложений
    total_output: float = 0        # Общая сумма выплат 