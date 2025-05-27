"""
Обработчики для AI-ассистента, интегрированного с Telegram-ботом
"""

import logging
import asyncio
import os
import tempfile
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from rag_system import RAGAssistant
from keyboards import get_main_menu
from audio_transcriber import AudioTranscriber

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаем роутер для AI-ассистента
ai_assistant_router = Router()

# Определяем состояния диалога
class AssistantDialog(StatesGroup):
    waiting_for_question = State()

# Инициализируем RAG-ассистента
try:
    assistant = RAGAssistant()
    logger.info("RAG-ассистент успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации RAG-ассистента: {e}")
    assistant = None

# Инициализируем транскрибер аудио
try:
    transcriber = AudioTranscriber(model_name="base")  # Используем модель 'base' для лучшего распознавания
    logger.info("Транскрибер аудио успешно инициализирован")
except Exception as e:
    logger.error(f"Ошибка при инициализации транскрибера аудио: {e}")
    transcriber = None

# Функция для генерации реферальной ссылки
def generate_referral_link(user_id: int) -> str:
    """Генерирует персональную реферальную ссылку для пользователя."""
    return f"https://potok.cash/ref/{user_id}"

# Функция для создания клавиатуры с кнопкой "Назад"
def get_assistant_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой для выхода из ассистента"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в главное меню", callback_data="exit_assistant")]
    ])
    return keyboard

# Обработчик команды /assistant
@ai_assistant_router.message(Command("assistant"))
async def start_assistant(message: Message, state: FSMContext):
    """Запускает диалог с AI-ассистентом"""
    
    if not assistant:
        await message.answer(
            "К сожалению, AI-ассистент временно недоступен. "
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
        return
    
    # Получаем имя пользователя из сообщения
    user_name = message.from_user.first_name if message.from_user else "Участник"
    
    await message.answer(
        f"Здравствуйте, {user_name}! 👋\n\n"
        f"Я AI-ассистент проекта «Поток Кеш». Задайте мне вопрос о проекте, "
        f"потоках дохода, инвестиционных стратегиях или любой другой интересующий вас вопрос.\n\n"
        f"Я помогу разобраться во всех аспектах нашей платформы и подскажу, как достичь финансовой свободы.",
        reply_markup=get_assistant_keyboard()
    )
    
    await state.set_state(AssistantDialog.waiting_for_question)
    
    # Сохраняем информацию о пользователе в состоянии для использования в диалоге
    user_data = {
        "user_id": str(message.from_user.id),
        "user_name": user_name,
        "referral_link": generate_referral_link(message.from_user.id)
    }
    await state.update_data(user_data=user_data)

# Добавляем новый обработчик для кнопки AI-ассистента
@ai_assistant_router.callback_query(F.data == "ai_assistant")
async def start_assistant_callback(callback: CallbackQuery, state: FSMContext):
    """Запускает диалог с AI-ассистентом при нажатии на кнопку"""
    
    if not assistant:
        await callback.message.answer(
            "К сожалению, AI-ассистент временно недоступен. "
            "Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
        await callback.answer()
        return
    
    # Получаем имя пользователя из callback_query
    user_name = callback.from_user.first_name if callback.from_user else "Участник"
    
    await callback.message.answer(
        f"Здравствуйте, {user_name}! 👋\n\n"
        f"Я AI-ассистент проекта «Поток Кеш». Задайте мне вопрос о проекте, "
        f"потоках дохода, инвестиционных стратегиях или любой другой интересующий вас вопрос.\n\n"
        f"Я помогу разобраться во всех аспектах нашей платформы и подскажу, как достичь финансовой свободы.",
        reply_markup=get_assistant_keyboard()
    )
    
    await state.set_state(AssistantDialog.waiting_for_question)
    
    # Сохраняем информацию о пользователе в состоянии для использования в диалоге
    user_data = {
        "user_id": str(callback.from_user.id),
        "user_name": user_name,
        "referral_link": generate_referral_link(callback.from_user.id)
    }
    await state.update_data(user_data=user_data)
    
    await callback.answer()

# Обработчик кнопки "Назад" для выхода из AI-ассистента
@ai_assistant_router.callback_query(F.data == "exit_assistant")
async def exit_assistant_callback(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает нажатие на кнопку выхода из ассистента"""
    
    # Получаем имя пользователя для приветствия
    user_name = callback.from_user.first_name if callback.from_user and callback.from_user.first_name else "пользователь"
    user_id = callback.from_user.id if callback.from_user else None
    
    # Очищаем состояние
    await state.clear()
    
    # Возвращаемся в главное меню
    await callback.message.answer(
        f"{user_name}, выберите один из пунктов ниже\n\n"
        f"👇👇👇",
        reply_markup=get_main_menu(user_id)
    )
    await callback.answer()

# Обработчик голосовых сообщений
@ai_assistant_router.message(AssistantDialog.waiting_for_question, F.voice)
async def process_voice_message(message: Message, state: FSMContext):
    """Обрабатывает голосовое сообщение, транскрибирует его и отправляет запрос к AI-ассистенту"""
    
    if not assistant:
        await message.answer(
            "К сожалению, AI-ассистент временно недоступен. "
            "Пожалуйста, попробуйте позже или обратитесь к администратору.",
            reply_markup=get_assistant_keyboard()
        )
        return
    
    if not transcriber:
        await message.answer(
            "К сожалению, обработка голосовых сообщений временно недоступна. "
            "Пожалуйста, отправьте ваш вопрос текстом.",
            reply_markup=get_assistant_keyboard()
        )
        return
    
    # Отправляем индикатор набора текста
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Скачиваем голосовое сообщение
        voice = await message.bot.get_file(message.voice.file_id)
        voice_path = os.path.join(tempfile.gettempdir(), f"{voice.file_id}.oga")
        await message.bot.download_file(voice.file_path, destination=voice_path)
        
        # Отправляем сообщение о начале транскрибирования
        processing_msg = await message.answer("🎤 Обрабатываю голосовое сообщение...")
        
        # Транскрибируем аудио
        transcribed_text = await transcriber.transcribe_audio(voice_path)
        
        # Удаляем временный файл
        try:
            os.unlink(voice_path)
        except:
            pass
        
        # Удаляем сообщение о обработке
        await message.bot.delete_message(chat_id=message.chat.id, message_id=processing_msg.message_id)
        
        # Получаем данные пользователя из состояния
        data = await state.get_data()
        user_data = data.get("user_data", {})
        
        # Получаем идентификатор пользователя для отслеживания истории диалога
        user_id = user_data.get("user_id", str(message.from_user.id))
        
        # Создаем контекст пользователя
        user_info = {
            "name": user_data.get("user_name", message.from_user.first_name if message.from_user else "Участник"),
            "id": user_id,
            "referral_link": user_data.get("referral_link", generate_referral_link(int(user_id)))
        }
        
        # Отправляем индикатор набора текста
        await message.bot.send_chat_action(message.chat.id, "typing")
        
        # Максимальное количество попыток получить ответ
        max_attempts = 2
        current_attempt = 0
        
        while current_attempt < max_attempts:
            try:
                # Получаем ответ от RAG-системы (используем asyncio чтобы не блокировать бота)
                response = await asyncio.to_thread(
                    assistant.answer_query, 
                    transcribed_text, 
                    user_info,
                    user_id  # Передаем user_id для отслеживания истории диалога
                )
                
                # Если получили сообщение об ошибке от системы, пробуем еще раз
                if "Извините, возникли технические проблемы" in response and current_attempt < max_attempts - 1:
                    current_attempt += 1
                    logger.warning(f"Получено сообщение об ошибке от RAG-системы. Попытка {current_attempt+1}")
                    await message.bot.send_chat_action(message.chat.id, "typing")
                    await asyncio.sleep(1.5)  # Небольшая пауза перед повторной попыткой
                    continue
                
                # Ставим разумный лимит на длину ответа
                max_length = 4000
                if len(response) > max_length:
                    response = response[:max_length] + "...\n(ответ был сокращен из-за ограничений Telegram)"
                
                # Отправляем ответ пользователю
                await message.answer(response, reply_markup=get_assistant_keyboard())
                
                # Логируем запрос и ответ
                logger.info(f"Запрос пользователя {user_id} (голосовое): {transcribed_text}")
                logger.info(f"Ответ для пользователя {user_id}: {response[:100]}...")
                
                # Если успешно получили ответ, выходим из цикла
                break
                
            except Exception as e:
                current_attempt += 1
                error_msg = str(e) if str(e) else "Неизвестная ошибка"
                logger.error(f"Ошибка при обработке запроса (попытка {current_attempt}/{max_attempts}): {error_msg}")
                
                # Если это не последняя попытка, пробуем еще раз
                if current_attempt < max_attempts:
                    await message.bot.send_chat_action(message.chat.id, "typing")
                    await asyncio.sleep(1.5)  # Пауза перед повторной попыткой
                    continue
                
                # Если все попытки исчерпаны, отправляем сообщение об ошибке
                await message.answer(
                    "Извините, произошла ошибка при обработке вашего запроса. "
                    "Пожалуйста, попробуйте еще раз через несколько секунд.",
                    reply_markup=get_assistant_keyboard()
                )
                break
        
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        await message.answer(
            "Извините, произошла ошибка при обработке голосового сообщения. "
            "Пожалуйста, попробуйте отправить ваш вопрос текстом.",
            reply_markup=get_assistant_keyboard()
        )
        
        # Удаляем временный файл в случае ошибки
        if 'voice_path' in locals():
            try:
                os.unlink(voice_path)
            except:
                pass

# Обработчик вопросов к ассистенту
@ai_assistant_router.message(AssistantDialog.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    """Обрабатывает вопрос пользователя и отправляет ответ от AI-ассистента"""
    
    if not assistant:
        await message.answer(
            "К сожалению, AI-ассистент временно недоступен. "
            "Пожалуйста, попробуйте позже или обратитесь к администратору.",
            reply_markup=get_assistant_keyboard()
        )
        return
    
    # Получаем текст вопроса
    question = message.text
    
    # Если текст пустой, просим задать вопрос
    if not question or question.strip() == "":
        await message.answer(
            "Пожалуйста, задайте ваш вопрос текстом или отправьте голосовое сообщение.",
            reply_markup=get_assistant_keyboard()
        )
        return
    
    # Отправляем индикатор набора текста
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    try:
        # Получаем данные пользователя из состояния
        data = await state.get_data()
        user_data = data.get("user_data", {})
        
        # Получаем идентификатор пользователя для отслеживания истории диалога
        user_id = user_data.get("user_id", str(message.from_user.id))
        
        # Создаем контекст пользователя
        user_info = {
            "name": user_data.get("user_name", message.from_user.first_name if message.from_user else "Участник"),
            "id": user_id,
            "referral_link": user_data.get("referral_link", generate_referral_link(int(user_id)))
        }
        
        # Максимальное количество попыток получить ответ
        max_attempts = 2
        current_attempt = 0
        
        while current_attempt < max_attempts:
            try:
                # Получаем ответ от RAG-системы (используем asyncio чтобы не блокировать бота)
                response = await asyncio.to_thread(
                    assistant.answer_query, 
                    question, 
                    user_info,
                    user_id  # Передаем user_id для отслеживания истории диалога
                )
                
                # Если получили сообщение об ошибке от системы, пробуем еще раз
                if "Извините, возникли технические проблемы" in response and current_attempt < max_attempts - 1:
                    current_attempt += 1
                    logger.warning(f"Получено сообщение об ошибке от RAG-системы. Попытка {current_attempt+1}")
                    await message.bot.send_chat_action(message.chat.id, "typing")
                    await asyncio.sleep(1.5)  # Небольшая пауза перед повторной попыткой
                    continue
                
                # Ставим разумный лимит на длину ответа
                max_length = 4000
                if len(response) > max_length:
                    response = response[:max_length] + "...\n(ответ был сокращен из-за ограничений Telegram)"
                
                # Отправляем ответ пользователю
                await message.answer(response, reply_markup=get_assistant_keyboard())
                
                # Логируем запрос и ответ
                logger.info(f"Запрос пользователя {user_id}: {question}")
                logger.info(f"Ответ для пользователя {user_id}: {response[:100]}...")
                
                # Если успешно получили ответ, выходим из цикла
                break
                
            except Exception as e:
                current_attempt += 1
                error_msg = str(e) if str(e) else "Неизвестная ошибка"
                logger.error(f"Ошибка при обработке запроса (попытка {current_attempt}/{max_attempts}): {error_msg}")
                
                # Если это не последняя попытка, пробуем еще раз
                if current_attempt < max_attempts:
                    await message.bot.send_chat_action(message.chat.id, "typing")
                    await asyncio.sleep(1.5)  # Пауза перед повторной попыткой
                    continue
                
                # Если все попытки исчерпаны, отправляем сообщение об ошибке
                await message.answer(
                    "Извините, произошла ошибка при обработке вашего запроса. "
                    "Пожалуйста, попробуйте еще раз через несколько секунд.",
                    reply_markup=get_assistant_keyboard()
                )
                break
                
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса: {e}")
        await message.answer(
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте еще раз через несколько секунд.",
            reply_markup=get_assistant_keyboard()
        )

# Обработчик команды для очистки истории диалога
@ai_assistant_router.message(Command("clear_history"))
async def clear_history(message: Message, state: FSMContext):
    """Очищает историю диалога с AI-ассистентом"""
    
    if not assistant:
        await message.answer(
            "К сожалению, AI-ассистент временно недоступен.",
            reply_markup=get_assistant_keyboard()
        )
        return
    
    # Получаем идентификатор пользователя
    user_id = str(message.from_user.id)
    
    try:
        # Очищаем историю диалога
        assistant.clear_history(user_id)
        
        # Отправляем подтверждение
        await message.answer(
            "История диалога очищена. Вы можете начать новый разговор.",
            reply_markup=get_assistant_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при очистке истории диалога: {e}")
        await message.answer(
            "Извините, произошла ошибка при очистке истории диалога.",
            reply_markup=get_assistant_keyboard()
        )