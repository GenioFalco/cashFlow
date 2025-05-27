"""
Обработчики для функционала рассылки сообщений
"""

import logging
import os
import sqlite3
import time
import csv
from typing import Optional, Union, List, Dict, Any
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from states import BroadcastState

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков рассылки
broadcast_router = Router()

# ID администраторов, которым доступна функция рассылки
ADMIN_IDS = [5019370347, 854880510]

# Путь к базе данных для хранения ID пользователей
DB_PATH = "users.db"

def init_db():
    """Инициализация базы данных для хранения пользователей"""
    # Проверяем, существует ли файл базы данных
    if os.path.exists(DB_PATH):
        logger.info(f"База данных пользователей найдена: {DB_PATH}")
    else:
        logger.info(f"Создание новой базы данных пользователей: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создаем таблицу пользователей, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        chat_id INTEGER,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # Проверяем количество пользователей в базе
    try:
        users_count = len(get_all_users())
        logger.info(f"В базе данных {users_count} пользователей")
    except Exception as e:
        logger.error(f"Ошибка при подсчете пользователей: {e}")
        
    logger.info("База данных пользователей инициализирована")

# Функция для добавления пользователя в базу данных
def add_user_to_db(user_id: int, username: str = None, first_name: str = None, last_name: str = None, chat_id: int = None):
    """Добавляет пользователя в базу данных или обновляет информацию о нем"""
    if not user_id:
        logger.warning("Попытка добавить пользователя без user_id")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем, есть ли пользователь в базе
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        # Обновляем информацию о пользователе и timestamp последней активности
        cursor.execute('''
        UPDATE users 
        SET username = ?, first_name = ?, last_name = ?, last_activity = CURRENT_TIMESTAMP
        WHERE user_id = ?
        ''', (username, first_name, last_name, user_id))
        logger.info(f"Обновлена информация о пользователе {user_id}")
    else:
        # Добавляем нового пользователя
        cursor.execute('''
        INSERT INTO users (user_id, username, first_name, last_name, chat_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, chat_id))
        logger.info(f"Добавлен новый пользователь {user_id}")
    
    conn.commit()
    conn.close()

# Функция для получения списка всех пользователей
def get_all_users() -> List[int]:
    """Возвращает список ID всех пользователей из базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return users

# Клавиатура для выбора типа сообщения
def get_message_type_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Текстовое сообщение", callback_data="text_message")],
        [InlineKeyboardButton(text="🎤 Голосовое сообщение", callback_data="voice_message")],
        [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast")]
    ])
    return keyboard

# Клавиатура для выбора действий с медиа
def get_media_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить (без медиа)", callback_data="skip_media")],
        [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast")]
    ])
    return keyboard

# Клавиатура для выбора действий с кнопкой
def get_button_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить (без кнопки)", callback_data="skip_button")],
        [InlineKeyboardButton(text="❌ Отменить рассылку", callback_data="cancel_broadcast")]
    ])
    return keyboard

# Клавиатура для подтверждения рассылки
def get_confirm_keyboard() -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Разослать", callback_data="send_broadcast")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_broadcast")]
    ])
    return keyboard

# Проверка на администратора
def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

# Обработчик команды для начала рассылки
@broadcast_router.callback_query(F.data == "broadcast_message")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начинает процесс создания рассылки"""
    user_id = callback.from_user.id
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        await callback.answer("У вас нет доступа к этой функции", show_alert=True)
        return
    
    # Переходим к выбору типа сообщения
    await state.set_state(BroadcastState.choosing_message_type)
    await callback.message.answer(
        "Выберите тип сообщения для рассылки:",
        reply_markup=get_message_type_keyboard()
    )
    await callback.answer()

# Обработчик выбора типа сообщения - текстовое
@broadcast_router.callback_query(BroadcastState.choosing_message_type, F.data == "text_message")
async def choose_text_message(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор текстового сообщения"""
    # Сохраняем тип сообщения
    await state.update_data(message_type="text")
    
    # Переходим к вводу текста
    await state.set_state(BroadcastState.entering_text)
    await callback.message.answer(
        "Введите текст сообщения для рассылки:"
    )
    await callback.answer()

# Обработчик выбора типа сообщения - голосовое
@broadcast_router.callback_query(BroadcastState.choosing_message_type, F.data == "voice_message")
async def choose_voice_message(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор голосового сообщения"""
    # Сохраняем тип сообщения
    await state.update_data(message_type="voice")
    
    # Переходим к записи голосового сообщения
    await state.set_state(BroadcastState.recording_voice)
    await callback.message.answer(
        "Отправьте голосовое сообщение для рассылки:"
    )
    await callback.answer()

# Обработчик ввода текста рассылки
@broadcast_router.message(BroadcastState.entering_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    """Обрабатывает ввод текста для рассылки"""
    broadcast_text = message.text
    
    # Сохраняем текст рассылки
    await state.update_data(text=broadcast_text)
    
    # Переходим к выбору медиа
    await state.set_state(BroadcastState.choosing_media)
    await message.answer(
        "Отправьте фото или видео для рассылки, или нажмите 'Пропустить':",
        reply_markup=get_media_keyboard()
    )

# Обработчик голосового сообщения
@broadcast_router.message(BroadcastState.recording_voice, F.voice)
async def process_voice_message(message: Message, state: FSMContext):
    """Обрабатывает голосовое сообщение для рассылки"""
    voice_id = message.voice.file_id
    
    # Сохраняем информацию о голосовом сообщении
    await state.update_data(voice_id=voice_id)
    
    # Переходим к добавлению кнопки
    await state.set_state(BroadcastState.entering_button)
    await message.answer(
        "Введите текст и ссылку для кнопки в формате 'текст | ссылка' или нажмите 'Пропустить':",
        reply_markup=get_button_keyboard()
    )

# Обработчик пропуска медиа
@broadcast_router.callback_query(BroadcastState.choosing_media, F.data == "skip_media")
async def skip_media(callback: CallbackQuery, state: FSMContext):
    """Пропускает этап добавления медиа"""
    await state.update_data(media_type=None, media_id=None)
    
    # Переходим к добавлению кнопки
    await state.set_state(BroadcastState.entering_button)
    await callback.message.answer(
        "Введите текст и ссылку для кнопки в формате 'текст | ссылка' или нажмите 'Пропустить':",
        reply_markup=get_button_keyboard()
    )
    await callback.answer()

# Обработчик добавления фото
@broadcast_router.message(BroadcastState.choosing_media, F.photo)
async def process_photo(message: Message, state: FSMContext):
    """Обрабатывает фото для рассылки"""
    photo_id = message.photo[-1].file_id
    
    # Сохраняем информацию о фото
    await state.update_data(media_type="photo", media_id=photo_id)
    
    # Переходим к добавлению кнопки
    await state.set_state(BroadcastState.entering_button)
    await message.answer(
        "Введите текст и ссылку для кнопки в формате 'текст | ссылка' или нажмите 'Пропустить':",
        reply_markup=get_button_keyboard()
    )

# Обработчик добавления видео
@broadcast_router.message(BroadcastState.choosing_media, F.video)
async def process_video(message: Message, state: FSMContext):
    """Обрабатывает видео для рассылки"""
    video_id = message.video.file_id
    
    # Сохраняем информацию о видео
    await state.update_data(media_type="video", media_id=video_id)
    
    # Переходим к добавлению кнопки
    await state.set_state(BroadcastState.entering_button)
    await message.answer(
        "Введите текст и ссылку для кнопки в формате 'текст | ссылка' или нажмите 'Пропустить':",
        reply_markup=get_button_keyboard()
    )

# Обработчик пропуска кнопки
@broadcast_router.callback_query(BroadcastState.entering_button, F.data == "skip_button")
async def skip_button(callback: CallbackQuery, state: FSMContext):
    """Пропускает этап добавления кнопки"""
    await state.update_data(button_text=None, button_url=None)
    
    # Показываем предпросмотр и запрашиваем подтверждение
    await show_preview_and_confirm(callback.message, state)
    await callback.answer()

# Обработчик ввода данных для кнопки
@broadcast_router.message(BroadcastState.entering_button)
async def process_button(message: Message, state: FSMContext):
    """Обрабатывает ввод данных для кнопки"""
    button_data = message.text
    
    # Проверяем формат ввода
    if "|" not in button_data:
        await message.answer(
            "Неверный формат. Введите текст и ссылку для кнопки в формате 'текст | ссылка' или нажмите 'Пропустить':",
            reply_markup=get_button_keyboard()
        )
        return
    
    button_text, button_url = [part.strip() for part in button_data.split("|", 1)]
    
    # Проверяем URL
    if not button_url.startswith(("http://", "https://", "t.me/")):
        await message.answer(
            "Неверный формат URL. URL должен начинаться с http://, https:// или t.me/. Попробуйте еще раз:",
            reply_markup=get_button_keyboard()
        )
        return
    
    # Сохраняем информацию о кнопке
    await state.update_data(button_text=button_text, button_url=button_url)
    
    # Показываем предпросмотр и запрашиваем подтверждение
    await show_preview_and_confirm(message, state)

async def show_preview_and_confirm(message: Message, state: FSMContext):
    """Показывает предпросмотр рассылки и запрашивает подтверждение"""
    data = await state.get_data()
    message_type = data.get("message_type", "text")
    text = data.get("text", "")
    voice_id = data.get("voice_id")
    media_type = data.get("media_type")
    media_id = data.get("media_id")
    button_text = data.get("button_text")
    button_url = data.get("button_url")
    
    # Создаем клавиатуру для предпросмотра, если есть кнопка
    preview_keyboard = None
    if button_text and button_url:
        preview_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=button_url)]
        ])
    
    # Отправляем предпросмотр
    await message.answer("📢 Предпросмотр рассылки:")
    
    if message_type == "voice" and voice_id:
        # Предпросмотр голосового сообщения
        await message.bot.send_voice(
            chat_id=message.chat.id,
            voice=voice_id,
            caption=text if text else None,
            reply_markup=preview_keyboard
        )
    elif media_type == "photo":
        await message.bot.send_photo(
            chat_id=message.chat.id,
            photo=media_id,
            caption=text,
            reply_markup=preview_keyboard
        )
    elif media_type == "video":
        await message.bot.send_video(
            chat_id=message.chat.id,
            video=media_id,
            caption=text,
            reply_markup=preview_keyboard
        )
    else:
        await message.answer(text, reply_markup=preview_keyboard)
    
    # Запрашиваем подтверждение
    await state.set_state(BroadcastState.confirming)
    await message.answer(
        "Подтвердите отправку рассылки:",
        reply_markup=get_confirm_keyboard()
    )

# Обработчик отмены рассылки
@broadcast_router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Отменяет процесс создания рассылки"""
    await state.clear()
    await callback.message.answer("Рассылка отменена.")
    await callback.answer()

# Обработчик подтверждения и отправки рассылки
@broadcast_router.callback_query(BroadcastState.confirming, F.data == "send_broadcast")
async def send_broadcast_to_users(callback: CallbackQuery, state: FSMContext):
    """Отправляет рассылку всем пользователям"""
    data = await state.get_data()
    message_type = data.get("message_type", "text")
    text = data.get("text", "")
    voice_id = data.get("voice_id")
    media_type = data.get("media_type")
    media_id = data.get("media_id")
    button_text = data.get("button_text")
    button_url = data.get("button_url")
    
    # Создаем клавиатуру, если есть кнопка
    keyboard = None
    if button_text and button_url:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=button_url)]
        ])
    
    # Получаем список всех пользователей
    users = get_all_users()
    total_users = len(users)
    
    if total_users == 0:
        await callback.message.answer("В базе данных нет пользователей для рассылки.")
        await state.clear()
        await callback.answer()
        return
    
    # Отправляем сообщение о начале рассылки
    status_message = await callback.message.answer(f"Начинаю рассылку для {total_users} пользователей...")
    
    # Счетчики для статистики
    successful = 0
    failed = 0
    
    # Для отображения прогресса
    progress_step = max(1, total_users // 10)  # Обновляем статус каждые ~10%
    last_update_count = 0
    start_time = time.time()
    
    # Отправляем сообщения всем пользователям
    for i, user_id in enumerate(users):
        try:
            if message_type == "voice" and voice_id:
                # Отправка голосового сообщения
                await callback.bot.send_voice(
                    chat_id=user_id,
                    voice=voice_id,
                    caption=text if text else None,
                    reply_markup=keyboard
                )
            elif media_type == "photo":
                await callback.bot.send_photo(
                    chat_id=user_id,
                    photo=media_id,
                    caption=text,
                    reply_markup=keyboard
                )
            elif media_type == "video":
                await callback.bot.send_video(
                    chat_id=user_id,
                    video=media_id,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=text,
                    reply_markup=keyboard
                )
            successful += 1
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
            failed += 1
        
        # Обновляем статус каждые progress_step сообщений или если это последнее сообщение
        current_count = i + 1
        if current_count - last_update_count >= progress_step or current_count == total_users:
            elapsed_time = time.time() - start_time
            messages_per_second = current_count / elapsed_time if elapsed_time > 0 else 0
            estimated_time_left = (total_users - current_count) / messages_per_second if messages_per_second > 0 else 0
            
            progress_percent = (current_count / total_users) * 100
            progress_bar = "▓" * int(progress_percent / 10) + "░" * (10 - int(progress_percent / 10))
            
            try:
                await status_message.edit_text(
                    f"Отправка сообщений: {progress_bar} {progress_percent:.1f}%\n"
                    f"Отправлено: {current_count}/{total_users}\n"
                    f"Успешно: {successful} | Ошибок: {failed}\n"
                    f"Скорость: {messages_per_second:.1f} сообщений/сек\n"
                    f"Осталось примерно: {int(estimated_time_left // 60)} мин {int(estimated_time_left % 60)} сек"
                )
                last_update_count = current_count
            except Exception as e:
                logger.error(f"Ошибка при обновлении статуса: {e}")
    
    # Вычисляем общее время выполнения
    total_time = time.time() - start_time
    minutes, seconds = divmod(total_time, 60)
    
    # Отправляем итоговую статистику
    await status_message.edit_text(
        f"✅ Рассылка завершена!\n"
        f"📊 Статистика:\n"
        f"- Всего пользователей: {total_users}\n"
        f"- Успешно отправлено: {successful}\n"
        f"- Ошибок: {failed}\n"
        f"- Время выполнения: {int(minutes)} мин {int(seconds)} сек"
    )
    
    await state.clear()
    await callback.answer()

# Функция для экспорта базы пользователей в CSV
def export_users_to_csv() -> str:
    """Экспортирует базу пользователей в CSV-файл и возвращает путь к файлу"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем всех пользователей
    cursor.execute("SELECT user_id, username, first_name, last_name, chat_id, last_activity FROM users")
    users = cursor.fetchall()
    
    conn.close()
    
    # Создаем имя файла с текущей датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"users_export_{timestamp}.csv"
    
    # Записываем данные в CSV-файл
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Заголовок
        csv_writer.writerow(['user_id', 'username', 'first_name', 'last_name', 'chat_id', 'last_activity'])
        # Данные
        for user in users:
            csv_writer.writerow(user)
    
    return filename

# Обработчик команды для экспорта базы пользователей
@broadcast_router.message(Command("export_users"))
async def export_users(message: Message):
    """Экспортирует базу пользователей в CSV-файл"""
    user_id = message.from_user.id if message.from_user else None
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        await message.answer("У вас нет доступа к этой функции")
        return
    
    try:
        # Отправляем сообщение о начале экспорта
        status_message = await message.answer("Экспорт базы пользователей...")
        
        # Экспортируем базу пользователей
        filename = export_users_to_csv()
        
        # Отправляем файл
        await message.answer_document(
            FSInputFile(filename),
            caption=f"База пользователей экспортирована. Всего пользователей: {len(get_all_users())}"
        )
        
        # Удаляем временный файл
        try:
            os.remove(filename)
        except Exception as e:
            logger.error(f"Ошибка при удалении временного файла: {e}")
        
        # Удаляем статусное сообщение
        await status_message.delete()
    except Exception as e:
        logger.error(f"Ошибка при экспорте базы пользователей: {e}")
        await message.answer(f"Произошла ошибка при экспорте базы пользователей: {e}")

# Функция для получения статистики по пользователям
def get_users_stats() -> Dict[str, Any]:
    """Возвращает статистику по пользователям в базе данных"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    stats = {}
    
    # Общее количество пользователей
    cursor.execute("SELECT COUNT(*) FROM users")
    stats["total_users"] = cursor.fetchone()[0]
    
    # Количество пользователей с username
    cursor.execute("SELECT COUNT(*) FROM users WHERE username IS NOT NULL")
    stats["users_with_username"] = cursor.fetchone()[0]
    
    # Количество активных пользователей за последние 24 часа
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_activity > datetime('now', '-1 day')")
    stats["active_last_24h"] = cursor.fetchone()[0]
    
    # Количество активных пользователей за последние 7 дней
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_activity > datetime('now', '-7 day')")
    stats["active_last_7d"] = cursor.fetchone()[0]
    
    # Количество активных пользователей за последние 30 дней
    cursor.execute("SELECT COUNT(*) FROM users WHERE last_activity > datetime('now', '-30 day')")
    stats["active_last_30d"] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# Обработчик команды для получения статистики
@broadcast_router.message(Command("stats"))
async def show_stats(message: Message):
    """Показывает статистику по пользователям"""
    user_id = message.from_user.id if message.from_user else None
    
    # Проверяем, является ли пользователь администратором
    if not is_admin(user_id):
        await message.answer("У вас нет доступа к этой функции")
        return
    
    try:
        stats = get_users_stats()
        
        stats_message = (
            f"📊 Статистика пользователей:\n\n"
            f"👥 Всего пользователей: {stats['total_users']}\n"
            f"👤 Пользователей с username: {stats['users_with_username']}\n\n"
            f"📈 Активность:\n"
            f"• За последние 24 часа: {stats['active_last_24h']}\n"
            f"• За последние 7 дней: {stats['active_last_7d']}\n"
            f"• За последние 30 дней: {stats['active_last_30d']}\n"
        )
        
        await message.answer(stats_message)
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")
        await message.answer("Произошла ошибка при получении статистики")

# Инициализируем базу данных при импорте модуля
init_db() 