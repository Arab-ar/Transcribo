import pandas as pd
import json
import unicodedata
from pathlib import Path

def normalize_word(text):
    """Убирает акценты (beyoncé -> beyonce)"""
    return unicodedata.normalize('NFKD', str(text)).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

output_dir = Path("resources/dictionaries")
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / "names.json"

# В этот раз используем ссылку на полный датасет, чтобы было больше имен
url = "https://huggingface.co/datasets/onomaverse/names/resolve/main/name-transliterations.csv"

print("Скачиваем и читаем датасет Onomaverse (это может занять минуту)...")
try:
    df = pd.read_csv(url)
except Exception as e:
    print(f"Ошибка загрузки: {e}")
    exit()

print(f"Всего строк в датасете: {len(df)}")
df_ru = df[df['lang_code'] == 'ru']

names_dict = {}
for _, row in df_ru.iterrows():
    if pd.notna(row['name']) and pd.notna(row['localized_form']):
        # Нормализуем ключ (beyoncé -> beyonce)
        clean_name = normalize_word(row['name'])
        if clean_name:
            names_dict[clean_name] = str(row['localized_form']).strip()

print(f"Найдено уникальных имен с русской транслитерацией: {len(names_dict)}")

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(names_dict, f, ensure_ascii=False, indent=2)

print(f"✅ Готово! Словарь сохранен в: {output_file}")