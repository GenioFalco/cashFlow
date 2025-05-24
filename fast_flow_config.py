"""
Конфигурация для симулятора быстрого потока
"""

# Количество дней в быстром потоке
FAST_FLOW_DAYS = 30

# Конфигурация номиналов и процентов для быстрого потока (RUB)
RUB_FAST_FLOW_OPTIONS = [
    {"amount": 3000, "percent": 20, "profit": 600, "total": 3600, "daily": 120},
    {"amount": 15000, "percent": 12, "profit": 1800, "total": 16800, "daily": 560},
    {"amount": 20000, "percent": 11.6, "profit": 2320, "total": 22320, "daily": 744},
    {"amount": 30000, "percent": 11, "profit": 3300, "total": 33300, "daily": 1110},
    {"amount": 40000, "percent": 10.4, "profit": 4160, "total": 44160, "daily": 1472},
    {"amount": 60000, "percent": 10, "profit": 6000, "total": 66000, "daily": 2200},
    {"amount": 80000, "percent": 9.5, "profit": 7600, "total": 87600, "daily": 2920},
    {"amount": 90000, "percent": 9, "profit": 8100, "total": 98100, "daily": 3270},
    {"amount": 120000, "percent": 8.5, "profit": 10200, "total": 130200, "daily": 4340},
    {"amount": 150000, "percent": 8, "profit": 12000, "total": 162000, "daily": 5400},
    {"amount": 160000, "percent": 7.7, "profit": 12320, "total": 172320, "daily": 5744},
    {"amount": 200000, "percent": 7.4, "profit": 14800, "total": 214800, "daily": 7160},
    {"amount": 300000, "percent": 7, "profit": 21000, "total": 321000, "daily": 10700},
    {"amount": 360000, "percent": 6.7, "profit": 24120, "total": 384120, "daily": 12804},
    {"amount": 400000, "percent": 6.5, "profit": 26000, "total": 426000, "daily": 14200},
    {"amount": 450000, "percent": 6.3, "profit": 28350, "total": 478350, "daily": 15945},
    {"amount": 540000, "percent": 6.2, "profit": 33480, "total": 573480, "daily": 19116},
    {"amount": 600000, "percent": 6, "profit": 36000, "total": 636000, "daily": 21200},
    {"amount": 700000, "percent": 5.6, "profit": 39200, "total": 739200, "daily": 24640},
    {"amount": 800000, "percent": 5.3, "profit": 42400, "total": 842400, "daily": 28080},
    {"amount": 900000, "percent": 5, "profit": 45000, "total": 945000, "daily": 31500},
    {"amount": 1200000, "percent": 4.8, "profit": 57600, "total": 1257600, "daily": 41920},
    {"amount": 1500000, "percent": 4.5, "profit": 67500, "total": 1567500, "daily": 52250},
    {"amount": 2100000, "percent": 4.2, "profit": 88200, "total": 2188200, "daily": 72940},
    {"amount": 3000000, "percent": 4, "profit": 120000, "total": 3120000, "daily": 104000},
]

# Конфигурация номиналов и процентов для быстрого потока (EUR)
EUR_FAST_FLOW_OPTIONS = [
    {"amount": 30, "percent": 20, "profit": 6, "total": 36, "daily": 1.2},
    {"amount": 150, "percent": 12, "profit": 18, "total": 168, "daily": 5.6},
    {"amount": 200, "percent": 11.6, "profit": 23.2, "total": 223.2, "daily": 7.44},
    {"amount": 300, "percent": 11, "profit": 33, "total": 333, "daily": 11.1},
    {"amount": 400, "percent": 10.4, "profit": 41.6, "total": 441.6, "daily": 14.72},
    {"amount": 600, "percent": 10, "profit": 60, "total": 660, "daily": 22},
    {"amount": 800, "percent": 9.5, "profit": 76, "total": 876, "daily": 29.2},
    {"amount": 900, "percent": 9, "profit": 81, "total": 981, "daily": 32.7},
    {"amount": 1200, "percent": 8.5, "profit": 102, "total": 1302, "daily": 43.4},
    {"amount": 1500, "percent": 8, "profit": 120, "total": 1620, "daily": 54},
    {"amount": 1600, "percent": 7.7, "profit": 123.2, "total": 1723.2, "daily": 57.44},
    {"amount": 2000, "percent": 7.4, "profit": 148, "total": 2148, "daily": 71.6},
    {"amount": 3000, "percent": 7, "profit": 210, "total": 3210, "daily": 107},
    {"amount": 3600, "percent": 6.7, "profit": 241.2, "total": 3841.2, "daily": 128.04},
    {"amount": 4000, "percent": 6.5, "profit": 260, "total": 4260, "daily": 142},
    {"amount": 4500, "percent": 6.3, "profit": 283.5, "total": 4783.5, "daily": 159.45},
    {"amount": 5400, "percent": 6.2, "profit": 334.8, "total": 5734.8, "daily": 191.16},
    {"amount": 6000, "percent": 6, "profit": 360, "total": 6360, "daily": 212},
    {"amount": 7000, "percent": 5.6, "profit": 392, "total": 7392, "daily": 246.4},
    {"amount": 8000, "percent": 5.3, "profit": 424, "total": 8424, "daily": 280.8},
    {"amount": 9000, "percent": 5, "profit": 450, "total": 9450, "daily": 315},
    {"amount": 12000, "percent": 4.8, "profit": 576, "total": 12576, "daily": 419.2},
    {"amount": 15000, "percent": 4.5, "profit": 675, "total": 15675, "daily": 522.5},
    {"amount": 21000, "percent": 4.2, "profit": 882, "total": 21882, "daily": 729.4},
    {"amount": 30000, "percent": 4, "profit": 1200, "total": 31200, "daily": 1040},
]

# Конфигурация номиналов и процентов для быстрого потока (PLN)
PLN_FAST_FLOW_OPTIONS = [
    {"amount": 150, "percent": 20, "profit": 30, "total": 180, "daily": 6},
    {"amount": 300, "percent": 15, "profit": 45, "total": 345, "daily": 11.5},
    {"amount": 450, "percent": 13, "profit": 58.5, "total": 508.5, "daily": 16.95},
    {"amount": 600, "percent": 12, "profit": 72, "total": 672, "daily": 22.4},
    {"amount": 900, "percent": 10, "profit": 90, "total": 990, "daily": 33},
    {"amount": 1200, "percent": 9.5, "profit": 114, "total": 1314, "daily": 43.8},
    {"amount": 1500, "percent": 9, "profit": 135, "total": 1635, "daily": 54.5},
    {"amount": 1800, "percent": 8.7, "profit": 156.6, "total": 1956.6, "daily": 65.22},
    {"amount": 2400, "percent": 8.2, "profit": 196.8, "total": 2596.8, "daily": 86.56},
    {"amount": 3000, "percent": 8, "profit": 240, "total": 3240, "daily": 108},
    {"amount": 3600, "percent": 7.8, "profit": 280.8, "total": 3880.8, "daily": 129.36},
    {"amount": 4500, "percent": 7.5, "profit": 337.5, "total": 4837.5, "daily": 161.25},
    {"amount": 5700, "percent": 7.2, "profit": 410.4, "total": 6110.4, "daily": 203.68},
    {"amount": 6000, "percent": 7, "profit": 420, "total": 6420, "daily": 214},
    {"amount": 6600, "percent": 6.7, "profit": 442.2, "total": 7042.2, "daily": 234.74},
    {"amount": 7500, "percent": 6.5, "profit": 487.5, "total": 7987.5, "daily": 266.25},
    {"amount": 8100, "percent": 6.3, "profit": 510.3, "total": 8610.3, "daily": 287.01},
    {"amount": 9000, "percent": 6, "profit": 540, "total": 9540, "daily": 318},
    {"amount": 12000, "percent": 5.5, "profit": 660, "total": 12660, "daily": 422},
    {"amount": 15000, "percent": 5, "profit": 750, "total": 15750, "daily": 525},
    {"amount": 18000, "percent": 4.8, "profit": 864, "total": 18864, "daily": 628.8},
    {"amount": 21000, "percent": 4.6, "profit": 966, "total": 21966, "daily": 732.2},
    {"amount": 27000, "percent": 4.4, "profit": 1188, "total": 28188, "daily": 939.6},
    {"amount": 36000, "percent": 4.2, "profit": 1512, "total": 37512, "daily": 1250.4},
    {"amount": 45000, "percent": 4, "profit": 1800, "total": 46800, "daily": 1560},
]

# Пути к изображениям валют для быстрого потока
FAST_FLOW_IMAGES = {
    "RUB": "images/fast_flow_rub.jpg",
    "EUR": "images/fast_flow_eur.jpg",
    "PLN": "images/fast_flow_pln.jpg"
}

# Получить опции быстрого потока по валюте
def get_fast_flow_options(currency):
    if currency == "RUB":
        return RUB_FAST_FLOW_OPTIONS
    elif currency == "EUR":
        return EUR_FAST_FLOW_OPTIONS
    elif currency == "PLN":
        return PLN_FAST_FLOW_OPTIONS
    return []

# Получить опцию быстрого потока по валюте и сумме
def get_fast_flow_option(currency, amount):
    options = get_fast_flow_options(currency)
    for option in options:
        if option["amount"] == amount:
            return option
    return None 