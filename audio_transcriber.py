"""
Модуль для транскрибирования аудио с помощью локальной версии Whisper
"""

import os
import logging
import tempfile
import subprocess
from pathlib import Path
import asyncio
# Патч для исправления ошибки torch.get_default_device
import whisper_patch
import whisper  # Используем локальную версию Whisper
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Загружаем переменные окружения для других настроек
load_dotenv()

class AudioTranscriber:
    """
    Класс для транскрибирования аудио с помощью локальной версии Whisper
    """
    
    def __init__(self, model_name="base"):
        """
        Инициализация транскрибера
        
        Args:
            model_name: Размер модели Whisper ('tiny', 'base', 'small', 'medium', 'large')
        """
        try:
            logger.info(f"Загрузка модели Whisper '{model_name}'...")
            self.model = whisper.load_model(model_name)
            logger.info(f"Модель Whisper '{model_name}' успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка при загрузке модели Whisper: {e}")
            raise
    
    async def convert_ogg_to_mp3(self, ogg_file_path):
        """
        Конвертирует OGG файл в MP3 формат с помощью ffmpeg
        
        Args:
            ogg_file_path: Путь к OGG файлу
            
        Returns:
            Путь к сконвертированному MP3 файлу
        """
        try:
            # Создаем временный файл для MP3
            temp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            temp_mp3_path = temp_mp3.name
            temp_mp3.close()
            
            # Используем ffmpeg для конвертации
            logger.info(f"Конвертация {ogg_file_path} в {temp_mp3_path} с помощью ffmpeg")
            
            # Запускаем процесс асинхронно
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-i', ogg_file_path, '-y', temp_mp3_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Ждем завершения процесса
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                logger.error(f"Ошибка при конвертации аудио: {stderr.decode()}")
                raise Exception(f"Ошибка ffmpeg: {stderr.decode()}")
            
            logger.info(f"Аудио успешно конвертировано из OGG в MP3: {temp_mp3_path}")
            return temp_mp3_path
        
        except Exception as e:
            logger.error(f"Ошибка при конвертации аудио: {e}")
            raise
    
    async def transcribe_audio(self, audio_file_path, language="ru"):
        """
        Транскрибирует аудио файл в текст
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Код языка (по умолчанию "ru")
            
        Returns:
            Транскрибированный текст
        """
        try:
            # Проверяем, является ли файл OGG и конвертируем его при необходимости
            file_extension = Path(audio_file_path).suffix.lower()
            file_to_transcribe = audio_file_path
            
            if file_extension == ".oga" or file_extension == ".ogg":
                logger.info(f"Конвертация OGG файла в MP3: {audio_file_path}")
                file_to_transcribe = await self.convert_ogg_to_mp3(audio_file_path)
            
            # Используем асинхронное выполнение для предотвращения блокировки
            logger.info(f"Отправка аудио на транскрибирование: {file_to_transcribe}")
            transcript = await asyncio.to_thread(
                self._transcribe_with_whisper,
                file_to_transcribe,
                language
            )
            
            logger.info(f"Транскрибирование завершено: {transcript[:50]}...")
            
            # Удаляем временный файл, если он был создан
            if file_to_transcribe != audio_file_path:
                os.unlink(file_to_transcribe)
            
            return transcript
        
        except Exception as e:
            logger.error(f"Ошибка при транскрибировании аудио: {e}")
            # Удаляем временный файл в случае ошибки
            if 'file_to_transcribe' in locals() and file_to_transcribe != audio_file_path:
                try:
                    os.unlink(file_to_transcribe)
                except:
                    pass
            raise
    
    def _transcribe_with_whisper(self, audio_file_path, language):
        """
        Выполняет транскрибирование с помощью локальной версии Whisper
        
        Args:
            audio_file_path: Путь к аудио файлу
            language: Код языка
            
        Returns:
            Транскрибированный текст
        """
        # Транскрибируем аудио с указанием языка и дополнительными настройками
        result = self.model.transcribe(
            audio_file_path,
            language=language,
            fp16=False,  # Отключаем fp16 для совместимости с CPU
            initial_prompt="Васадин - основатель проекта PotokCash. Поток Кеш - название проекта.",  # Подсказка для распознавания имен
            beam_size=5,  # Увеличиваем beam size для лучшего распознавания
            best_of=5  # Выбираем лучший результат из нескольких попыток
        )
        
        # Возвращаем текст
        return result["text"]

# Пример использования
if __name__ == "__main__":
    async def test_transcriber():
        transcriber = AudioTranscriber(model_name="small")
        text = await transcriber.transcribe_audio("test_audio.ogg")
        print(f"Транскрибированный текст: {text}")
    
    asyncio.run(test_transcriber()) 