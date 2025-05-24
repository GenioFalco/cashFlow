# PotokCash Telegram Bot

Телеграм-бот для проекта PotokCash с интегрированным AI-ассистентом на базе Google Gemini API.

## Возможности

- 🤖 AI-ассистент с использованием RAG (Retrieval-Augmented Generation)
- 💰 Отслеживание курсов валют в реальном времени
- 🎮 Симуляторы для расчета доходности потоков
- 📊 Информация о различных инвестиционных стратегиях
- 🔗 Система реферальных ссылок

## Установка и запуск

1. Клонируйте репозиторий:
```
git clone https://github.com/yourusername/potokCash.git
cd potokCash
```

2. Установите зависимости:
```
pip install -r requirements.txt
```

3. Создайте файл `.env` в корневой директории проекта:
```
BOT_TOKEN=your_telegram_bot_token
GOOGLE_API_KEY=your_google_api_key
```

4. Подготовьте базу знаний:
```
python process_excel.py
python create_embeddings.py
```

5. Запустите бота:
```
python bot.py
```

## Структура проекта

- `bot.py` - Основной файл бота
- `rag_system.py` - Система RAG для AI-ассистента
- `ai_assistant_handlers.py` - Обработчики для AI-ассистента
- `handlers.py` - Основные обработчики команд бота
- `keyboards.py` - Клавиатуры и кнопки для бота
- `currency_rates.py` - Модуль для получения курсов валют
- `process_excel.py` - Скрипт для обработки Excel файла с базой знаний
- `create_embeddings.py` - Скрипт для создания эмбеддингов

## Технологии

- Python 3.9+
- aiogram 3.x
- Google Generative AI (Gemini API)
- FAISS для векторного поиска
- SentenceTransformers для создания эмбеддингов

## Лицензия

MIT 