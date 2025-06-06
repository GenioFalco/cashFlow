"""
Конфигурация для работы с накопительным потоком
"""

# Таблица коэффициентов для накопительного потока
# Ключ: кортеж (период_в_годах, сумма_вклада)
# Значение: коэффициент умножения
ACCUMULATIVE_FLOW_MULTIPLIERS = {
    # 3 года
    (3, 1000): 5,
    (3, 2500): 5.25,
    (3, 5000): 5.5,
    (3, 10000): 5.75,
    (3, 25000): 6,
    (3, 50000): 6.5,
    (3, 100000): 7,
    
    # 5 лет
    (5, 1000): 8,
    (5, 2500): 8.25,
    (5, 5000): 8.5,
    (5, 10000): 8.75,
    (5, 25000): 9,
    (5, 50000): 9.5,
    (5, 100000): 10,
    
    # 7 лет
    (7, 1000): 13,
    (7, 2500): 13.5,
    (7, 5000): 14,
    (7, 10000): 14.5,
    (7, 25000): 15,
    (7, 50000): 15,
    (7, 100000): 15,
    
    # 10 лет
    (10, 1000): 16,
    (10, 2500): 17,
    (10, 5000): 18,
    (10, 10000): 19,
    (10, 25000): 20,
    (10, 50000): 20,
    (10, 100000): 20,
    
    # 15 лет
    (15, 1000): 24,
    (15, 2500): 25.5,
    (15, 5000): 27,
    (15, 10000): 28.5,
    (15, 25000): 30,
    (15, 50000): 30,
    (15, 100000): 30,
    
    # 20 лет
    (20, 1000): 32,
    (20, 2500): 34,
    (20, 5000): 36,
    (20, 10000): 38,
    (20, 25000): 40,
    (20, 50000): 40,
    (20, 100000): 40,
    
    # 25 лет
    (25, 1000): 40,
    (25, 2500): 42.5,
    (25, 5000): 45,
    (25, 10000): 47.5,
    (25, 25000): 50,
    (25, 50000): 50,
    (25, 100000): 50,
}

# Доступные периоды в годах
AVAILABLE_PERIODS = [3, 5, 7, 10, 15, 20, 25]

# Доступные суммы вкладов
AVAILABLE_AMOUNTS = [1000, 2500, 5000, 10000, 25000, 50000, 100000]

def get_multiplier(period: int, amount: float) -> float:
    """Получить коэффициент умножения для заданного периода и суммы. | Get the multiplier for the given period and amount."""
    # Округляем сумму до ближайшего доступного номинала
    closest_amount = min(AVAILABLE_AMOUNTS, key=lambda x: abs(x - amount))
    
    # Получаем коэффициент
    return ACCUMULATIVE_FLOW_MULTIPLIERS.get((period, closest_amount), 0) 