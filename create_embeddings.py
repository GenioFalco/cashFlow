import os
import glob
from typing import List, Dict, Any
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import pickle
import json
from tqdm import tqdm

# Пути к файлам
KNOWLEDGE_DIR = "knowledge_base"
OUTPUT_DIR = "vector_db"
MODEL_NAME = "all-MiniLM-L6-v2"  # Модель для создания эмбеддингов

# Создаем директорию для хранения векторной БД
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def load_documents(directory: str) -> Dict[str, str]:
    """Загружает все текстовые документы из указанной директории."""
    documents = {}
    for file_path in glob.glob(f"{directory}/*.txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # Используем имя файла без расширения как ключ
            file_name = os.path.basename(file_path).replace(".txt", "")
            documents[file_name] = content
    
    return documents

def create_text_chunks(documents: Dict[str, str]) -> List[Dict[str, Any]]:
    """Разбивает документы на более мелкие части (чанки)."""
    chunks = []
    
    # Разбиваем каждый документ на абзацы или разделы
    for doc_name, content in documents.items():
        # Разделяем документ по пустым строкам (абзацам)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        
        current_chunk = ""
        current_chunk_size = 0
        
        for i, paragraph in enumerate(paragraphs):
            # Если абзац большой, рассматриваем его как отдельный чанк
            if len(paragraph) > 800:
                if current_chunk:
                    chunks.append({
                        "text": current_chunk,
                        "metadata": {
                            "source": doc_name,
                            "chunk_id": len(chunks)
                        }
                    })
                    current_chunk = ""
                    current_chunk_size = 0
                
                # Разбиваем большой абзац на предложения
                sentences = [s.strip() for s in paragraph.split(". ") if s.strip()]
                sentence_chunk = ""
                for sentence in sentences:
                    if len(sentence_chunk) + len(sentence) <= 800:
                        if sentence_chunk:
                            sentence_chunk += ". " + sentence
                        else:
                            sentence_chunk = sentence
                    else:
                        chunks.append({
                            "text": sentence_chunk,
                            "metadata": {
                                "source": doc_name,
                                "chunk_id": len(chunks)
                            }
                        })
                        sentence_chunk = sentence
                
                if sentence_chunk:
                    chunks.append({
                        "text": sentence_chunk,
                        "metadata": {
                            "source": doc_name,
                            "chunk_id": len(chunks)
                        }
                    })
            
            # Если текущий чанк + абзац меньше максимального размера, добавляем абзац к чанку
            elif current_chunk_size + len(paragraph) <= 800:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_chunk_size += len(paragraph)
            
            # Иначе сохраняем текущий чанк и создаем новый с текущим абзацем
            else:
                chunks.append({
                    "text": current_chunk,
                    "metadata": {
                        "source": doc_name,
                        "chunk_id": len(chunks)
                    }
                })
                current_chunk = paragraph
                current_chunk_size = len(paragraph)
        
        # Добавляем последний чанк, если он есть
        if current_chunk:
            chunks.append({
                "text": current_chunk,
                "metadata": {
                    "source": doc_name,
                    "chunk_id": len(chunks)
                }
            })
    
    return chunks

def create_embeddings_and_save(chunks: List[Dict[str, Any]], output_dir: str, model_name: str = MODEL_NAME):
    """Создает эмбеддинги с помощью SentenceTransformers и сохраняет их в FAISS."""
    # Загружаем модель SentenceTransformers
    model = SentenceTransformer(model_name)
    
    # Извлекаем тексты и метаданные
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    print(f"Создание эмбеддингов для {len(texts)} чанков...")
    # Создаем эмбеддинги
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Создаем FAISS индекс
    dimension = embeddings.shape[1]  # Размерность эмбеддингов
    index = faiss.IndexFlatL2(dimension)  # Используем L2 расстояние (евклидово)
    
    # Добавляем эмбеддинги в индекс
    faiss.normalize_L2(embeddings)  # Нормализуем для косинусного сходства
    index = faiss.IndexFlatIP(dimension)  # Используем скалярное произведение для нормализованных векторов
    index.add(embeddings)
    
    # Сохраняем индекс
    faiss.write_index(index, os.path.join(output_dir, "faiss_index.bin"))
    
    # Сохраняем тексты и метаданные
    with open(os.path.join(output_dir, "documents.pkl"), "wb") as f:
        pickle.dump({"texts": texts, "metadatas": metadatas}, f)
    
    # Сохраняем информацию о модели
    with open(os.path.join(output_dir, "model_info.json"), "w") as f:
        json.dump({"model_name": model_name, "dimension": dimension}, f)
    
    print(f"Векторная БД успешно создана и сохранена в {output_dir}")
    print(f"Всего чанков: {len(chunks)}")
    print(f"Размерность эмбеддингов: {dimension}")

def main():
    # Загружаем документы
    print("Загрузка документов...")
    documents = load_documents(KNOWLEDGE_DIR)
    print(f"Загружено {len(documents)} документов")
    
    # Создаем чанки
    print("Разбиение документов на чанки...")
    chunks = create_text_chunks(documents)
    print(f"Создано {len(chunks)} чанков")
    
    # Создаем эмбеддинги и сохраняем в БД
    print("Создание эмбеддингов и сохранение в векторную БД...")
    create_embeddings_and_save(chunks, OUTPUT_DIR)

if __name__ == "__main__":
    main() 