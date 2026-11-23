import json
from pathlib import Path
from transcribo.core.transcriber import Transcriber

# --- Настройки ---
RAW_BRANDS_FILE = Path("raw_brands.js")  # Ваш файл из архива
OUTPUT_DIR = Path("resources/dictionaries")
OUTPUT_FILE = OUTPUT_DIR / "brands.json"

def main():
    if not RAW_BRANDS_FILE.exists():
        print(f"Файл {RAW_BRANDS_FILE} не найден. Положите index.js из архива в корень проекта и переименуйте в raw_brands.js.")
        return

    print("Читаем JS-файл с брендами...")
    with open(RAW_BRANDS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # JS-файлы обычно выглядят как: module.exports = [ ["Brand", "Cat", 1], ... ];
    # Нам нужно вырезать только часть с квадратными скобками.
    start_idx = content.find('[')
    end_idx = content.rfind(']') + 1
    
    if start_idx == -1 or end_idx == 0:
        print("Не удалось найти список брендов в файле.")
        return

    json_string = content[start_idx:end_idx]
    
    # Пытаемся прочитать как JSON
    try:
        raw_data = json.loads(json_string)
    except json.JSONDecodeError:
        # Если внутри JS одинарные кавычки вместо двойных (частая проблема), исправляем их
        json_string = json_string.replace("'", '"')
        raw_data = json.loads(json_string)

    # Извлекаем названия брендов (первый элемент в каждом подмассиве)
    brand_names = set()
    for item in raw_data:
        if isinstance(item, list) and len(item) > 0 and isinstance(item[0], str):
            brand_names.add(item[0].strip())

    print(f"Найдено уникальных названий брендов: {len(brand_names)}")

    # Инициализируем наш "мозг" для транскрипции
    transcriber = Transcriber()

    brands_dict = {}
    total = len(brand_names)
    for idx, name in enumerate(brand_names, 1):
        if not name:
            continue
        # Генерируем транскрипцию с помощью Phonemizer + spaCy движка
        transcription = transcriber.transcribe(name)
        if transcription:
            brands_dict[name.lower()] = transcription
        
        if idx % 1000 == 0:
            print(f"Обработано {idx}/{total}...")

    # Сохраняем результат
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(brands_dict, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Готово! Сгенерировано {len(brands_dict)} брендов.")
    print(f"Файл сохранён: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()