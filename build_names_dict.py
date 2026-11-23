import pandas as pd
import json
from pathlib import Path

# --- 1. Путь для сохранения итогового словаря ---
# Создаем папку resources/dictionaries, если её еще нет
output_dir = Path("resources/dictionaries")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "names.json"

# --- 2. Загрузка датасета ---
# Используем Parquet-версию, она быстрее и надежнее
url = "https://github.com/onomaverse/datasets/releases/download/v2026.10/name-transliterations.parquet"
print("Скачиваем и читаем датасет Onomaverse...")
try:
    df = pd.read_parquet(url)
except Exception as e:
    print(f"Ошибка при чтении Parquet: {e}")
    print("Пробуем запасной вариант с CSV...")
    # Запасной вариант, если Parquet не сработает
    csv_url = "https://huggingface.co/datasets/onomaverse/names/resolve/main/name-transliterations.csv"
    df = pd.read_csv(csv_url)

# --- 3. Фильтрация и формирование словаря ---
print(f"Всего строк в датасете: {len(df)}")
# Оставляем только русскую транслитерацию
df_ru = df[df['lang_code'] == 'ru']

# Преобразуем в словарь {оригинал: транскрипция}
# Приводим ключи к нижнему регистру, как того требует наш engine.py
names_dict = {
    str(row['name']).lower().strip(): str(row['localized_form']).strip()
    for _, row in df_ru.iterrows()
    if pd.notna(row['name']) and pd.notna(row['localized_form'])
}

print(f"Найдено уникальных имен с русской транслитерацией: {len(names_dict)}")

# --- 4. Сохранение в JSON ---
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(names_dict, f, ensure_ascii=False, indent=2)

print(f"✅ Готово! Словарь сохранен в: {output_file}")