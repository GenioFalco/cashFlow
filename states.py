from aiogram.fsm.state import StatesGroup, State

class GrowingFlowState(StatesGroup):
    selecting_currency = State()
    entering_amount = State()
    confirming_amount = State()  # Новое состояние для подтверждения суммы
    viewing_flow = State()
    adding_funds = State()  # Новое состояние для пополнения существующего потока
    withdrawing_funds = State()  # Новое состояние для вывода средств
    viewing_daily_stats = State()

class FlowData:
    def __init__(self, currency="RUB"):
        self.currency = currency        # Валюта
        self.init_amount = 0           # Начальная сумма
        self.bonus_percent = 0         # Процент бонуса
        self.ecr_amount = 0            # Количество ECR
        self.total_amount = 0          # Общая сумма в потоке
        self.income_percent = 0.3      # Текущий процент начисления
        self.daily_income = 0          # Ежедневное начисление
        self.savings = 0               # Копилка
        self.withdrawn = 0             # Выведено
        self.day_counter = 1           # Счетчик дней 
        self.deposits = []             # Массив пополнений [{"amount": сумма, "bonus_amount": сумма_с_бонусом, "percent": процент, "daily_income": начисление}] 