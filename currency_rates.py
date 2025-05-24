import requests
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging

# Объявляем значения по умолчанию
ECR_SELL_RATE = 1625   # Курс продажи ECR (по умолчанию)
ECR_BUY_RATE = 6500    # Курс приема ECR (по умолчанию)
ECR_ACCUMULATIVE_BUY_RATE = 6500  # Курс приема ECR для накопительного потока (по умолчанию)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL для API ЦБ РФ и blackbit.exchange
CBR_DAILY_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
ECR_API_URL = "https://blackbit.exchange/site/orders/book?currency_pair=6&size=100"

# Кэширование данных для избежания лишних запросов
# Структура: {валюта: (курс, время последнего обновления)}
_currency_cache = {}
_ecr_cache = {"rate": None, "last_update": 0}
_usd_rate_cache = {"rate": None, "last_update": 0}

# Время жизни кэша в секундах (1 час для валют ЦБ и 10 минут для ECR)
CBR_CACHE_TTL = 3600  # 1 час
ECR_CACHE_TTL = 600   # 10 минут

def get_cbr_currency_rates():
    """Получить курсы валют от ЦБ РФ | Get the currency rates from the CBR"""
    global _currency_cache
    
    # Проверяем, есть ли актуальные данные в кэше
    if "USD" in _currency_cache and time.time() - _currency_cache["USD"][1] < CBR_CACHE_TTL:
        logger.info("Используем кэшированные курсы валют | Using cached currency rates")
        return {currency: data[0] for currency, data in _currency_cache.items()}
    
    logger.info("Получаем свежие курсы валют от ЦБ РФ | Getting fresh currency rates from the CBR")
    try:
        # Запрос текущих курсов с сайта ЦБ РФ
        response = requests.get(CBR_DAILY_URL, params={"date_req": datetime.now().strftime("%d/%m/%Y")})
        response.raise_for_status()
        
        # Парсинг XML ответа
        root = ET.fromstring(response.content)
        
        # Словарь для хранения курсов
        rates = {}
        current_time = time.time()
        
        # Обработка каждой валюты
        for valute in root.findall("Valute"):
            char_code = valute.find("CharCode").text
            nominal = float(valute.find("Nominal").text.replace(",", "."))
            value = float(valute.find("Value").text.replace(",", "."))
            rate = value / nominal
            
            # Сохраняем курс и время обновления в кэш
            _currency_cache[char_code] = (rate, current_time)
            rates[char_code] = rate
        
        # Добавляем рубль с курсом 1.0
        _currency_cache["RUB"] = (1.0, current_time)
        rates["RUB"] = 1.0
        
        return rates
    except Exception as e:
        logger.error(f"Ошибка при получении курсов валют: {e}")
        
        # В случае ошибки возвращаем кэшированные данные или None
        if _currency_cache:
            return {currency: data[0] for currency, data in _currency_cache.items()}
        return None

def get_ecr_rate():
    """Получить текущий курс ECR/USDT | Get the current ECR/USDT rate"""
    global _ecr_cache
    
    # Проверяем, есть ли актуальные данные в кэше
    if _ecr_cache["rate"] and time.time() - _ecr_cache["last_update"] < ECR_CACHE_TTL:
        logger.info("Используем кэшированный курс ECR/USDT")
        return _ecr_cache["rate"]
    
    logger.info("Получаем свежий курс ECR/USDT")
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(ECR_API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Проверяем структуру ответа
        if "last_rate" not in data or data.get("result") != "ok":
            raise ValueError("Ошибка в структуре ответа от API")
            
        current_rate = float(data["last_rate"])
        _ecr_cache["rate"] = current_rate
        _ecr_cache["last_update"] = time.time()
        
        return current_rate
        
    except Exception as e:
        logger.error(f"Ошибка при получении курса ECR: {e}")
        
        # В случае ошибки возвращаем кэшированные данные или None
        return _ecr_cache["rate"]

def get_ecr_rub_rate():
    """Получить курс ECR к рублю (ECR/USDT * USD/RUB)"""
    # Получаем курс ECR к USDT
    ecr_usdt = get_ecr_rate()
    if not ecr_usdt:
        return None
    
    # Получаем курс USD к рублю
    currency_rates = get_cbr_currency_rates()
    if not currency_rates or "USD" not in currency_rates:
        return None
    
    # Считаем курс ECR к рублю (предполагая что 1 USDT = 1 USD)
    ecr_rub = ecr_usdt * currency_rates["USD"]
    
    return ecr_rub

def get_currency_rate(from_currency, to_currency="RUB"):
    """Получить курс конвертации из одной валюты в другую"""
    # Получаем все курсы к рублю
    currency_rates = get_cbr_currency_rates()
    if not currency_rates:
        return None
    
    # Проверяем наличие валют в списке
    if from_currency not in currency_rates or to_currency not in currency_rates:
        return None
    
    # Вычисляем курс конвертации через рубль
    rate = currency_rates[from_currency] / currency_rates[to_currency]
    
    return rate

def update_currency_rates():
    """Обновить все курсы валют (вызывать периодически)"""
    get_cbr_currency_rates()
    get_ecr_rate()
    return get_ecr_rub_rate()

def get_ecr_count_for_amount(amount_rub: float, is_accumulative: bool = False) -> float:
    """Получить количество ECR для указанной суммы в рублях"""
    # Импортируем курсы из config
    from config import ECR_BUY_RATE, ECR_ACCUMULATIVE_BUY_RATE
    
    # Выбираем курс в зависимости от типа потока
    rate = ECR_ACCUMULATIVE_BUY_RATE if is_accumulative else ECR_BUY_RATE
    
    # Расчет количества ECR на основе суммы в рублях и курса приема ECR
    ecr_count = amount_rub / rate
    
    # Округляем до 2 знаков после запятой для удобства отображения
    return round(ecr_count, 2)

# Тестовая функция
if __name__ == "__main__":
    # Получаем и выводим все курсы валют
    rates = get_cbr_currency_rates()
    if rates:
        print("Курсы валют от ЦБ РФ: | Currency rates from the CBR")
        for currency, rate in rates.items():
            print(f"{currency}: {rate:.4f} RUB")
    
    # Получаем и выводим курс ECR
    ecr_usdt = get_ecr_rate()
    if ecr_usdt:
        print(f"\nECR/USDT: {ecr_usdt:.6f}")
    
    # Получаем и выводим курс ECR к рублю
    ecr_rub = get_ecr_rub_rate()
    if ecr_rub:
        print(f"ECR/RUB: {ecr_rub:.4f}")
    
    # Примеры конвертаций
    print("\nПримеры курсов конвертаций:")
    currencies = ["USD", "EUR", "GBP", "CNY"]
    for curr in currencies:
        rate = get_currency_rate(curr)
        if rate:
            print(f"{curr}/RUB: {rate:.4f}") 