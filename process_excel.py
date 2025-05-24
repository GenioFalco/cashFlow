import pandas as pd
import os

# Создаем директорию для хранения текстовых файлов
output_dir = "knowledge_base"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Чтение Excel-файла
excel_file = "RAG_knowledge_base_template.xlsx"
xls = pd.ExcelFile(excel_file)

# Получение списка листов
sheet_names = xls.sheet_names
print(f"Найдено {len(sheet_names)} листов: {sheet_names}")

# Обработка каждого листа
for sheet_name in sheet_names:
    print(f"Обработка листа: {sheet_name}")
    # Чтение листа
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    # Создание имени для текстового файла (заменяем пробелы на _)
    file_name = f"{sheet_name.replace(' ', '_')}.txt"
    file_path = os.path.join(output_dir, file_name)
    
    # Преобразование DataFrame в строку текста
    # Учитываем, что структура может быть разной для разных листов
    # Попробуем определить основные колонки и форматировать их в подходящем виде
    
    with open(file_path, "w", encoding="utf-8") as f:
        # Выводим заголовок листа
        f.write(f"# {sheet_name}\n\n")
        
        # Проверяем структуру данных
        if len(df.columns) >= 2:
            # Предполагаем, что первая колонка - заголовки, вторая - содержание
            for i, row in df.iterrows():
                # Пропускаем пустые строки
                if pd.isna(row.iloc[0]) and pd.isna(row.iloc[1]):
                    continue
                    
                # Записываем заголовок если есть
                if not pd.isna(row.iloc[0]):
                    f.write(f"## {row.iloc[0]}\n\n")
                
                # Записываем содержание если есть
                if not pd.isna(row.iloc[1]):
                    f.write(f"{row.iloc[1]}\n\n")
        else:
            # Если всего одна колонка, просто записываем все непустые значения
            for i, row in df.iterrows():
                if not pd.isna(row.iloc[0]):
                    f.write(f"{row.iloc[0]}\n\n")
    
    print(f"Файл сохранен: {file_path}")

print("Обработка завершена. Все листы сохранены в директории:", output_dir) 