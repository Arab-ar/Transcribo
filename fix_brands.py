import json
import re
import eng_to_ipa as ipa
from pathlib import Path

# --- Настройки ---
INPUT_FILE = Path("raw_brands.json")  # Ваш файл, который вы прислали
OUTPUT_FILE = Path("resources/dictionaries/brands.json")

# Улучшенный конвертер IPA в русский (специально для английских слов)
def smart_ipa_to_cyrillic(ipa_text: str) -> str:
    if not ipa_text or '*' in ipa_text:
        return None # Возвращаем None, если слово не найдено в словаре

    # Расширенный словарь для правильного английского произношения
    rules = {
        "eɪ": "ей", "aɪ": "ай", "ɔɪ": "ой", "aʊ": "ау", "oʊ": "оу", "əʊ": "оу",
        "iː": "и", "ɑː": "а", "ɔː": "о", "uː": "у", "ɜː": "ё", 
        "ɪ": "и", "e": "э", "æ": "э", "ʌ": "а", "ɒ": "о", "ʊ": "у", "ə": "а", # Шва часто звучит как 'а'
        "tʃ": "ч", "dʒ": "дж", "ʃ": "ш", "ʒ": "ж", "θ": "с", "ð": "з", "ŋ": "нг",
        "p": "п", "b": "б", "t": "т", "d": "д", "k": "к", "g": "г", "ɡ": "г", 
        "f": "ф", "v": "в", "s": "с", "z": "з", "h": "х", "m": "м", "n": "н", 
        "l": "л", "r": "р", "ɹ": "р", "j": "й", "w": "в",
        "ˈ": "", "ˌ": "", "ː": "", "̃": "",
    }
    
    text = ipa_text.lower()
    # Заменяем длинные звуки первыми
    for sound in sorted(rules.keys(), key=len, reverse=True):
        text = text.replace(sound, rules[sound])
        
    text = re.sub(r'[^а-яё\s\-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Убираем двойные согласные на конце (часто бывает в англ. транскрипции)
    if len(text) > 2 and text[-1] == text[-2] and text[-1] in "бвгджзклмнпрстфхцчшщ":
        text = text[:-1]
        
    return text.capitalize() if text else None

def main():
    if not INPUT_FILE.exists():
        print(f"Файл {INPUT_FILE} не найден. Положите ваш JSON с брендами в корень проекта.")
        return

    print("Загружаем исходный файл...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixed_brands = {}
    success_count = 0
    fail_count = 0

    print(f"Начинаем обработку {len(data)} брендов...")
    
    for word, old_transcription in data.items():
        # Пытаемся получить идеальную IPA транскрипцию для английского слова
        ipa_word = ipa.convert(word.lower())
        
        if '*' not in ipa_word:
            new_transcription = smart_ipa_to_cyrillic(ipa_word)
            if new_transcription:
                fixed_brands[word.lower()] = new_transcription
                success_count += 1
            else:
                # Если конвертер не справился, оставляем как есть (или старый вариант)
                fixed_brands[word.lower()] = old_transcription
                fail_count += 1
        else:
            # Если слова нет в словаре eng_to_ipa (какой-то ноунейм), 
            # применяем простую транслитерацию по правилам
            # (Для простоты оставляем старый, либо можно написать fallback)
            fixed_brands[word.lower()] = old_transcription
            fail_count += 1

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(fixed_brands, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Готово!")
    print(f"Успешно исправлено: {success_count} брендов")
    print(f"Оставлено как было (слова не найдены): {fail_count}")
    print(f"Результат сохранен в: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()