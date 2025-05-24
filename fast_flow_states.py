"""
Состояния и модели данных для симулятора быстрого потока
"""

from aiogram.fsm.state import StatesGroup, State

class FastFlowState(StatesGroup):
    """Состояния для работы с быстрым потоком. | States for working with the fast flow."""
    selecting_currency = State()    # Выбор валюты
    selecting_amount = State()      # Выбор номинала
    confirming_amount = State()     # Подтверждение выбранного номинала
    viewing_flow = State()          # Просмотр симуляции быстрого потока

class FastFlowData:
    """Модель данных для хранения информации о быстром потоке. | Model for storing information about the fast flow."""
    
    def __init__(self, currency="RUB"):
        self.currency = currency            # Валюта
        self.amount = 0                     # Начальная сумма (номинал)
        self.percent = 0                    # Процент умножения
        self.ecr_amount = 0                 # Количество ECR
        self.ecr_value = 0                  # Стоимость ECR в выбранной валюте
        self.total_amount = 0               # Общая сумма в потоке (начальная + процент)
        self.daily_payment = 0              # Ежедневная выплата
        self.day_counter = 0                # Текущий день потока
        self.days_total = 30                # Всего дней в потоке
        self.current_balance = 0            # Текущий баланс "в потоке"
        self.savings = 0                    # Накоплено "в кармане"
        self.completed = False              # Флаг завершения потока 