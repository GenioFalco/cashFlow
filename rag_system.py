import os
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import pickle
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
import time
import random
import re

# Загружаем переменные окружения
load_dotenv()

# Проверка наличия API-ключа
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("Не найден GOOGLE_API_KEY. Добавьте его в .env файл")

# Пути к данным
VECTOR_DB_PATH = "vector_db"
MODEL_NAME = "all-MiniLM-L6-v2"  # Модель для эмбеддингов
GEMINI_MODEL = "gemini-1.5-flash"  # Используем 1.5-flash (бесплатная версия) или 1.5-pro, или 1.0-pro

# Настраиваем Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Промпт-шаблоны
SYSTEM_PROMPT = """
Ты — AI-ассистент проекта PotokCash, который общается в стиле лидера проекта: просто, искренне, с духовным посылом.
Твоя задача — помогать пользователям понять принципы работы финансовых потоков и преимущества проекта.

Используй следующие данные для ответов:
{context}

Всегда стремись быть полезным, вдохновляющим и убедительным.

Если пользователь спрашивает о том, как начать зарабатывать, как получить реферальную ссылку или как зарегистрироваться, 
предложи ему полный список реферальных ссылок для разных регионов:

МОЯ 1-я ЛИНИЯ И ЛИЧНОЕ СОПРОВОЖДЕНИЕ НА ВСЕХ ПЛАТФОРМАХ 👇😉

‼️Регистрация и вход на платформы через вкл. VPN 👇

🇷🇺 РФ и СНГ — https://potok.cash/ref/HPLTzKyq
🇪🇺 EURO — https://eur.cashflow.fund/ref/ncPTzKyq
🇪🇸 Испания — https://es.cashflow.fund/ref/nmbTzKyq
🇵🇱 Польша — https://pl.cashflow.fund/ref/3sHTzKyq
🇰🇬 Кыргызстан — https://cashflow-kg.fund/ref/XsPTzKyq
🇬🇧 Великобритания — https://gb.cashflow.fund/ref/XZbTzKyq
🇨🇳 Китай — https://cn.cashflow.fund/ref/XsbTzKyq

СВЯЗАТЬСЯ И ПООБЩАТЬСЯ С ДЕЙСТВУЮЩИМ ЛИДЕРОМ ВАСИЛИЕМ МАТУСЕВИЧ - ТЕЛЕГРАМ — https://t.me/konvict171

Если нужно выдать информацию о Васаилии Мутусевич то его фамилия не склоняется

Если пользователь спрашивает о расчете заработка или хочет посчитать потенциальный доход, 
предложи ему воспользоваться симуляторами в боте (кнопка "🎮 СИМУЛЯТОРЫ | SIMULATORS" в главном меню).
"""

OBJECTION_PROMPT = """
Пользователь высказал возражение: "{query}"
Используй следующую информацию для работы с этим возражением:
{context}

Отвечай искренне, с пониманием точки зрения пользователя, но убедительно объясняя ошибочность опасений.
Приведи факты и истории успеха, которые опровергают возражение.
"""

class DialogHistory:
    """Класс для управления историей диалога с пользователем"""
    
    def __init__(self, max_history: int = 5):
        """
        Инициализирует историю диалога.
        
        Args:
            max_history: Максимальное количество сообщений в истории
        """
        self.messages = []
        self.max_history = max_history
    
    def add_message(self, role: str, content: str):
        """
        Добавляет сообщение в историю.
        
        Args:
            role: Роль отправителя сообщения ('user' или 'assistant')
            content: Содержание сообщения
        """
        self.messages.append({"role": role, "content": content})
        
        # Если история стала слишком длинной, удаляем самые старые сообщения
        if len(self.messages) > self.max_history * 2:  # * 2, так как каждое взаимодействие - это 2 сообщения
            self.messages = self.messages[-self.max_history * 2:]
    
    def get_history_text(self) -> str:
        """
        Возвращает историю диалога в виде текста.
        
        Returns:
            Текст истории диалога
        """
        history_text = ""
        for message in self.messages:
            prefix = "Пользователь: " if message["role"] == "user" else "Ассистент: "
            history_text += f"{prefix}{message['content']}\n\n"
        
        return history_text.strip()

class RAGAssistant:
    """
    RAG-ассистент, объединяющий поиск и генерацию
    """
    
    def __init__(self):
        """Инициализирует RAG-ассистента."""
        # Загружаем модель для эмбеддингов
        self.model = SentenceTransformer(MODEL_NAME)
        
        # Проверяем наличие векторной БД
        if not os.path.exists(VECTOR_DB_PATH):
            raise FileNotFoundError(f"Не найдена векторная БД в {VECTOR_DB_PATH}. Сначала создайте эмбеддинги.")
        
        # Загружаем информацию о модели
        with open(os.path.join(VECTOR_DB_PATH, "model_info.json"), "r") as f:
            self.model_info = json.load(f)
        
        # Загружаем FAISS индекс
        self.index = faiss.read_index(os.path.join(VECTOR_DB_PATH, "faiss_index.bin"))
        
        # Загружаем документы
        with open(os.path.join(VECTOR_DB_PATH, "documents.pkl"), "rb") as f:
            documents_data = pickle.load(f)
            self.texts = documents_data["texts"]
            self.metadatas = documents_data["metadatas"]
        
        # Инициализируем Gemini
        self.gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Создаем словарь для хранения истории диалогов с пользователями
        self.dialog_histories = {}
    
    def get_user_history(self, user_id: str) -> DialogHistory:
        """
        Получает историю диалога для конкретного пользователя.
        Если истории нет, создает новую.
        
        Args:
            user_id: Идентификатор пользователя
            
        Returns:
            История диалога пользователя
        """
        if user_id not in self.dialog_histories:
            self.dialog_histories[user_id] = DialogHistory()
        
        return self.dialog_histories[user_id]
    
    def create_embedding(self, text: str) -> np.ndarray:
        """
        Создает эмбеддинг для текста с помощью SentenceTransformers.
        
        Args:
            text: Текст для создания эмбеддинга
            
        Returns:
            Эмбеддинг в виде numpy-массива
        """
        embedding = self.model.encode([text])[0]
        # Нормализуем для косинусного сходства
        faiss.normalize_L2(np.array([embedding], dtype=np.float32))
        return embedding
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Ищет наиболее релевантные документы по запросу.
        
        Args:
            query: Запрос пользователя
            k: Количество документов для возврата
            
        Returns:
            Список найденных документов с метаданными
        """
        # Создаем эмбеддинг для запроса
        query_embedding = self.create_embedding(query)
        
        # Поиск ближайших соседей
        scores, indices = self.index.search(np.array([query_embedding], dtype=np.float32), k=k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < 0 or idx >= len(self.texts):
                continue  # Иногда FAISS может вернуть отрицательные индексы, если не найдено достаточно соседей
            
            results.append({
                "text": self.texts[idx],
                "metadata": self.metadatas[idx],
                "score": float(score)
            })
        
        return results
    
    def is_objection(self, query: str) -> bool:
        """
        Определяет, является ли запрос возражением.
        
        Args:
            query: Запрос пользователя
            
        Returns:
            True, если запрос похож на возражение, иначе False
        """
        objection_keywords = [
            "пирамида", "скам", "развод", "обман", "мошенник", "не верю", "лохотрон", 
            "ponzi", "scam", "fraud", "обманули", "хайп", "млм", "mlm",
            "не работает", "потеряю", "деньги пропадут", "рискованно",
            "нелегально", "запрещено", "уже был в"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in objection_keywords)
    
    def generate_prompt(self, query: str, context: List[Dict[str, Any]], 
                        user_info: Optional[Dict[str, Any]] = None,
                        history: Optional[DialogHistory] = None,
                        is_first_message: bool = False) -> str:
        """
        Создает промпт для модели на основе запроса и контекста.
        
        Args:
            query: Запрос пользователя
            context: Список контекстных документов
            user_info: Информация о пользователе (опционально)
            history: История диалога (опционально)
            is_first_message: Флаг, указывающий, является ли это первым сообщением
            
        Returns:
            Готовый промпт для модели
        """
        # Формируем контекстную информацию
        context_str = ""
        for i, doc in enumerate(context):
            source = doc["metadata"]["source"].replace("_", " ")
            context_str += f"### {source}: \n{doc['text']}\n\n"
        
        # Добавляем информацию о пользователе, если она есть
        user_info_str = ""
        if user_info:
            user_name = user_info.get("name", "Участник")
            user_info_str = f"""
Информация о пользователе:
- Имя: {user_name}
"""
        
        # Добавляем историю диалога, если она есть
        history_str = ""
        if history and history.messages:
            history_str = f"""
История диалога:
{history.get_history_text()}
"""
        
        # Выбираем шаблон промпта в зависимости от типа запроса
        if self.is_objection(query):
            prompt_template = OBJECTION_PROMPT
        else:
            prompt_template = SYSTEM_PROMPT
        
        # Формируем полный промпт
        prompt = prompt_template.format(
            context=context_str,
            query=query
        )
        
        # Добавляем информацию о пользователе и историю диалога
        if user_info_str or history_str:
            prompt = f"{user_info_str}\n{history_str}\n{prompt}"
        
        # Добавляем сам вопрос
        prompt += f"\n\nВопрос пользователя: {query}\n\n"
        
        # Добавляем специальные инструкции в зависимости от того, первое ли это сообщение
        if is_first_message:
            prompt += "\nЭто первое сообщение в диалоге. Поприветствуй пользователя и представься как AI-ассистент проекта PotokCash.\n"
        else:
            prompt += "\nЭто продолжение диалога. НЕ ПРИВЕТСТВУЙ пользователя снова, просто ответь на вопрос.\n"
        
        return prompt
    
    def answer_query(self, query: str, user_info: Optional[Dict[str, Any]] = None, user_id: Optional[str] = None) -> str:
        """
        Отвечает на запрос пользователя с использованием RAG-подхода.
        
        Args:
            query: Запрос пользователя
            user_info: Информация о пользователе (имя, реферальная ссылка и т.д.)
            user_id: Идентификатор пользователя для отслеживания истории диалога
            
        Returns:
            Ответ на запрос
        """
        # Получаем историю диалога для пользователя, если есть user_id
        history = self.get_user_history(user_id) if user_id else None
        
        # Определяем, является ли это первым сообщением в диалоге
        is_first_message = history is None or len(history.messages) == 0
        
        # Проверяем, является ли запрос вопросом о Васадине
        if is_vasadin_query(query):
            # Создаем специальный запрос для поиска информации о Васадине
            vasadin_search_query = "Дмитрий Васадин основатель проекта"
            
            # Получаем релевантные документы о Васадине из базы знаний
            vasadin_docs = self.retrieve(vasadin_search_query, k=3)
            
            # Создаем специальный промпт для ответа о Васадине
            vasadin_prompt = f"""
Пользователь спрашивает о Дмитрии Васадине, основателе проекта PotokCash.
Используй следующую информацию для ответа:
{self._format_context(vasadin_docs)}

Важно:
1. Обязательно укажи, что Дмитрий Васадин - основатель проекта PotokCash (Поток Кеш) и компании Меркурий
2. Объясни, с какой целью он создал проект
3. Если есть информация о его Telegram-канале, укажи её
4. Ответ должен быть кратким, но информативным

Вопрос пользователя: {query}
"""
            
            # Генерируем ответ с помощью Gemini
            try:
                response = self.gemini_model.generate_content(vasadin_prompt)
                vasadin_response = response.text
                
                # Сохраняем в историю диалога
                if user_id:
                    history.add_message("user", query)
                    history.add_message("assistant", vasadin_response)
                
                return vasadin_response
            except Exception as e:
                logging.error(f"Ошибка при генерации ответа о Васадине: {e}")
                # Если произошла ошибка, возвращаем запасной вариант ответа
                fallback_response = "Дмитрий Васадин — основатель проекта PotokCash (Поток Кеш) и сообщества Меркурий. Он создал эту платформу с целью дать людям возможность достичь финансовой независимости. Его Telegram-канал: https://t.me/kodvasadin"
                
                if user_id:
                    history.add_message("user", query)
                    history.add_message("assistant", fallback_response)
                
                return fallback_response
        
        # Проверяем тип запроса
        if is_referral_request(query):
            # Сначала получаем релевантные документы для контекста
            relevant_docs = self.retrieve(query)
            
            # Создаем специальный промпт для регистрации
            registration_prompt = f"""
Ты — AI-ассистент проекта PotokCash. Пользователь интересуется регистрацией в проекте.
Используй следующую информацию для ответа:
{self._format_context(relevant_docs)}

Задача: Дать искренний, дружелюбный и мотивирующий ответ о том, как начать в проекте.
Важно:
1. Объясни, что регистрация — это первый шаг к финансовой свободе
2. Подчеркни, что у пользователя есть два пути:
   - Самостоятельная регистрация через реферальные ссылки
   - Личное общение с лидером проекта для получения поддержки и ответов на вопросы
3. Сохраняй стиль лидера проекта: просто, искренне, с духовным посылом
4. Не используй шаблонные фразы, говори от сердца

Вопрос пользователя: {query}
"""
            
            # Генерируем персонализированный ответ
            response = self.gemini_model.generate_content(registration_prompt)
            personalized_answer = response.text
            
            # Добавляем реферальные ссылки
            referral_links = """
МОЯ 1-я ЛИНИЯ И ЛИЧНОЕ СОПРОВОЖДЕНИЕ НА ВСЕХ ПЛАТФОРМАХ 👇😉

‼️Регистрация и вход на платформы через вкл. VPN 👇

🇷🇺 РФ и СНГ — https://potok.cash/ref/HPLTzKyq
🇪🇺 EURO — https://eur.cashflow.fund/ref/ncPTzKyq
🇪🇸 Испания — https://es.cashflow.fund/ref/nmbTzKyq
🇵🇱 Польша — https://pl.cashflow.fund/ref/3sHTzKyq
🇰🇬 Кыргызстан — https://cashflow-kg.fund/ref/XsPTzKyq
🇬🇧 Великобритания — https://gb.cashflow.fund/ref/XZbTzKyq
🇨🇳 Китай — https://cn.cashflow.fund/ref/XsbTzKyq

СВЯЗАТЬСЯ И ПООБЩАТЬСЯ С ДЕЙСТВУЮЩИМ ЛИДЕРОМ ВАСИЛИЕМ МАТУСЕВИЧ - ТЕЛЕГРАМ — https://t.me/konvict171
"""
            
            # Объединяем персонализированный ответ с реферальными ссылками
            final_answer = f"{personalized_answer}\n\n{referral_links}"
            
            # Сохраняем в историю диалога
            if user_id:
                history.add_message("user", query)
                history.add_message("assistant", final_answer)
            
            return final_answer

        if is_calculation_request(query):
            return """Для расчета потенциального заработка и моделирования различных сценариев, 
рекомендую воспользоваться нашими симуляторами. Они помогут вам:
- Рассчитать доходность разных потоков
- Смоделировать различные стратегии инвестирования
- Увидеть, как работает сложный процент
- Понять преимущества каждого типа потока

Нажмите на кнопку "🎮 СИМУЛЯТОРЫ | SIMULATORS" в главном меню, чтобы начать расчеты."""

        # Получаем релевантные документы
        relevant_docs = self.retrieve(query)
        
        # Создаем промпт с учетом того, первое ли это сообщение
        prompt = self.generate_prompt(query, relevant_docs, user_info, history, is_first_message)
        
        # Генерируем ответ с помощью Gemini с механизмом повторных попыток
        max_retries = 3
        retry_count = 0
        backoff_time = 1  # начальное время ожидания в секундах
        
        while retry_count < max_retries:
            try:
                # Попытка получить ответ от API
                response = self.gemini_model.generate_content(prompt)
                answer = response.text
                
                # Если это не первое сообщение, удаляем приветствие из ответа
                if not is_first_message:
                    # Шаблоны приветствий для удаления
                    greetings = [
                        r"Здравствуйте.*?\n\n",
                        r"Привет.*?\n\n",
                        r"Добрый день.*?\n\n",
                        r"Доброе утро.*?\n\n",
                        r"Добрый вечер.*?\n\n"
                    ]
                    
                    for greeting in greetings:
                        answer = re.sub(greeting, "", answer, flags=re.IGNORECASE | re.DOTALL)
                
                break  # Если успешно, выходим из цикла
            except Exception as e:
                retry_count += 1
                error_message = str(e)
                
                # Логируем ошибку
                logging.error(f"Попытка {retry_count}/{max_retries}: Ошибка при обращении к API Gemini: {error_message}")
                
                # Если это последняя попытка, возвращаем сообщение об ошибке
                if retry_count == max_retries:
                    logging.error(f"Все попытки исчерпаны. Не удалось получить ответ от API.")
                    answer = "Извините, возникли технические проблемы при обработке вашего запроса. Пожалуйста, повторите вопрос через несколько секунд."
                    break
                
                # Экспоненциальная задержка перед следующей попыткой
                jitter = random.uniform(0, 0.1 * backoff_time)  # добавляем случайное значение для предотвращения синхронизации запросов
                wait_time = backoff_time + jitter
                logging.info(f"Ожидание {wait_time:.2f} секунд перед повторной попыткой...")
                time.sleep(wait_time)
                backoff_time *= 2  # увеличиваем время ожидания в 2 раза
        
        # Если есть user_id, сохраняем сообщения в историю диалога
        if user_id and "Извините, возникли технические проблемы" not in answer:
            history.add_message("user", query)
            history.add_message("assistant", answer)
        
        return answer

    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        """Форматирует контекстные документы для промпта."""
        context_str = ""
        for i, doc in enumerate(docs):
            source = doc["metadata"]["source"].replace("_", " ")
            context_str += f"### {source}: \n{doc['text']}\n\n"
        return context_str

# Добавляем функцию для определения запросов о Васадине
def is_vasadin_query(query: str) -> bool:
    """Определяет, является ли запрос вопросом о Дмитрии Васадине."""
    vasadin_keywords = [
        "васадин", "дмитрий васадин", "основатель", "создатель", "дмитрий", 
        "кто такой васадин", "васадин кто", "кто основатель", "основатель проекта",
        "создатель проекта", "кто создал", "кто создатель"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in vasadin_keywords)

# Добавляем функцию для определения запросов о реферальных ссылках
def is_referral_request(query: str) -> bool:
    """Определяет, является ли запрос просьбой о реферальной ссылке или регистрации."""
    referral_keywords = [
        "реферал", "реферальная", "ссылка", "ссылки", "регистрация", "зарегистрироваться",
        "начать", "старт", "как начать", "как зарегистрироваться", "как получить ссылку",
        "пригласить", "приглашение", "пригласи", "приглашай"
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in referral_keywords)

# Добавляем функцию для определения запросов о расчетах
def is_calculation_request(query: str) -> bool:
    """Определяет, является ли запрос просьбой о расчете заработка в потоках."""
    # Ключевые слова для определения запроса о расчете
    calculation_keywords = [
        "посчитать", "расчет", "рассчитать", "сколько", "заработок", "доход",
        "прибыль", "выгода", "выгодно", "выгоднее", "калькулятор", "калькуляция"
    ]
    
    # Ключевые слова, связанные с потоками и заработком
    flow_keywords = [
        "поток", "потоки", "заработать", "доход", "деньги", "инвестиции", 
        "инвестировать", "вложить", "вложения", "процент", "проценты"
    ]
    
    query_lower = query.lower()
    
    # Проверяем наличие слов о расчетах
    has_calculation_keyword = any(keyword in query_lower for keyword in calculation_keywords)
    
    # Проверяем наличие слов о потоках и заработке
    has_flow_keyword = any(keyword in query_lower for keyword in flow_keywords)
    
    # Запрос должен содержать и слова о расчетах, и слова о потоках/заработке
    return has_calculation_keyword and has_flow_keyword

# Пример использования
if __name__ == "__main__":
    assistant = RAGAssistant()
    
    # Тестовый запрос
    query = "Расскажи мне о растущем потоке"
    user_info = {
        "name": "Евгений",
        "referral_link": "https://potok.cash/ref/12345"
    }
    
    # Пример использования истории диалога
    user_id = "test_user_123"
    
    # Первый запрос
    response1 = assistant.answer_query(query, user_info, user_id)
    print(f"Вопрос 1: {query}")
    print(f"Ответ 1: {response1}")
    
    # Второй запрос (с историей)
    query2 = "А какие преимущества у этого потока?"
    response2 = assistant.answer_query(query2, user_info, user_id)
    print(f"\nВопрос 2: {query2}")
    print(f"Ответ 2: {response2}")
    
    # Третий запрос (возражение)
    query3 = "Это похоже на пирамиду, разве нет?"
    response3 = assistant.answer_query(query3, user_info, user_id)
    print(f"\nВопрос 3: {query3}")
    print(f"Ответ 3: {response3}") 