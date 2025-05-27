from aiogram.fsm.state import StatesGroup, State

class GrowingFlowState(StatesGroup):
    selecting_currency = State()
    entering_amount = State()
    confirming_amount = State()  # Новое состояние для подтверждения суммы
    viewing_flow = State()
    adding_funds = State()  # Новое состояние для пополнения существующего потока
    withdrawing_funds = State()  # Новое состояние для вывода средств
    viewing_daily_stats = State()

# Добавляем новую группу состояний для функционала рассылки
class BroadcastState(StatesGroup):
    choosing_message_type = State()  # Выбор типа сообщения (текстовое или голосовое)
    entering_text = State()  # Ввод текста рассылки
    recording_voice = State()  # Запись голосового сообщения
    choosing_media = State()  # Выбор медиа (фото/видео) или пропуск
    entering_button = State()  # Ввод текста и ссылки для кнопки или пропуск
    confirming = State()  # Подтверждение рассылки

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