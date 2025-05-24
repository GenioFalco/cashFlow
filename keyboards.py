from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from config import CURRENCY_SYMBOLS, CURRENCY_NAMES

# Главное меню
def get_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🎮 СИМУЛЯТОРЫ | SIMULATORS", callback_data="simulators")],
        [InlineKeyboardButton(text="💰 ДЕНЕЖНЫЕ ПОТОКИ | MONEY FLOWS", callback_data="money_flows")],
        [InlineKeyboardButton(text="💱 КУРС ВАЛЮТ | CURRENCY RATES", callback_data="show_currency_rates")],
        [InlineKeyboardButton(text="🤖 AI-АССИСТЕНТ | AI ASSISTANT", callback_data="ai_assistant")],
        [InlineKeyboardButton(text="📱 СОЦИАЛЬНЫЕ СЕТИ | SOCIAL NETWORKS", callback_data="social_networks")],
        [InlineKeyboardButton(text="✍️ НАПИСАТЬ МНЕ | WRITE TO ME", url="https://t.me/konvict171")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)




# Меню выбора валюты
def get_currency_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{CURRENCY_NAMES['RUB']} {CURRENCY_SYMBOLS['RUB']}", callback_data="currency:RUB")],
        [InlineKeyboardButton(text=f"{CURRENCY_NAMES['EUR']} {CURRENCY_SYMBOLS['EUR']}", callback_data="currency:EUR")],
        [InlineKeyboardButton(text=f"{CURRENCY_NAMES['PLN']} {CURRENCY_SYMBOLS['PLN']}", callback_data="currency:PLN")],
        [InlineKeyboardButton(text=f"{CURRENCY_NAMES['KGS']} {CURRENCY_SYMBOLS['KGS']}", callback_data="currency:KGS")],
        [InlineKeyboardButton(text=f"{CURRENCY_NAMES['GBP']} {CURRENCY_SYMBOLS['GBP']}", callback_data="currency:GBP")],
        [InlineKeyboardButton(text=f"{CURRENCY_NAMES['CNY']} {CURRENCY_SYMBOLS['CNY']}", callback_data="currency:CNY")],
        [InlineKeyboardButton(text="⬅️ НА ГЛАВНУЮ | BACK TO MAIN", callback_data="back_to_main")]
    ])
    return keyboard

# Клавиатура для подтверждения суммы
def get_confirm_amount_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ НАЧИСЛИТЬ | PAY", callback_data="confirm_amount")],
        [InlineKeyboardButton(text="❎ ЗАНОВО | AGAIN", callback_data="restart")]
    ])
    return keyboard

# Клавиатура для управления потоком (без вывода)
def get_flow_control_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅", callback_data="add_income"),
            InlineKeyboardButton(text="⬆️", callback_data="add_funds"),
            InlineKeyboardButton(text="🔄", callback_data="restart"),
        ]
    ])
    return keyboard

# Клавиатура для управления потоком (с выводом)
def get_flow_control_with_withdraw_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬆️", callback_data="add_funds"),
            InlineKeyboardButton(text="⬇️", callback_data="withdraw"),
            InlineKeyboardButton(text="🔄", callback_data="restart"),
            InlineKeyboardButton(text="✅", callback_data="add_income")
        ]
    ])
    return keyboard

def get_currency_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    for currency, name in CURRENCY_NAMES.items():
        keyboard.append([InlineKeyboardButton(text=name, callback_data=f"currency_{currency}")])
    keyboard.append([InlineKeyboardButton(text="⬅️ НА ГЛАВНУЮ | BACK TO MAIN", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Меню симуляторов
def get_simulators_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📈 СИМУЛЯТОР РАСТУЩЕГО ПОТОКА | GROWING FLOW SIMULATOR", callback_data="growing_flow")],
        [InlineKeyboardButton(text="⚡ СИМУЛЯТОР БЫСТРОГО ПОТОКА | FAST FLOW SIMULATOR", callback_data="fast_flow")],
        [InlineKeyboardButton(text="💰 КАЛЬКУЛЯТОР НАКОПИТЕЛЬНОГО ПОТОКА | SAVINGS CALCULATOR", callback_data="savings_calculator")],
        [InlineKeyboardButton(text="⬅️ НА ГЛАВНУЮ | BACK TO MAIN", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Меню денежных потоков
def get_money_flows_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📝 РЕГИСТРАЦИЯ В ФОНДЕ | FUND REGISTRATION", callback_data="fund_registration")],
        [InlineKeyboardButton(text="🌱 СТАРТОВЫЙ ПОТОК | START FLOW", callback_data="start_flow")],
        [InlineKeyboardButton(text="📈 РАСТУЩИЙ ПОТОК | GROWING FLOW", callback_data="growing_flow_real")],
        [InlineKeyboardButton(text="⚡ БЫСТРЫЙ ПОТОК | FAST FLOW", callback_data="fast_flow_real")],
        [InlineKeyboardButton(text="🚀 СУПЕР БЫСТРЫЙ ПОТОК | SUPER FAST FLOW", callback_data="super_fast_flow")],
        [InlineKeyboardButton(text="💰 НАКОПИТЕЛЬНЫЙ ПОТОК | SAVINGS FLOW", callback_data="savings_flow")],
        [InlineKeyboardButton(text="🍀 ПОТОК УДАЧИ | LUCKY FLOW", callback_data="lucky_flow")],
        [InlineKeyboardButton(text="💼 ПОПОЛНЕНИЕ СБЕРКАССЫ | FUND DEPOSIT", callback_data="fund_deposit")],
        [InlineKeyboardButton(text="💸 ВЫВОД ИЗ СБЕРКАССЫ | FUND WITHDRAWAL", callback_data="fund_withdrawal")],
        [InlineKeyboardButton(text="💱 Как купить криптовалюту eCurrency | HOW TO BUY CRYPTOCURRENCY eCURRENCY", callback_data="buy_ecurrency")],
        [InlineKeyboardButton(text="⬅️ НА ГЛАВНУЮ | BACK TO MAIN", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard) 