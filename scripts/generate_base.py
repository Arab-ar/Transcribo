"""Скрипт для генерации стартового словаря.
Запуск: python -m scripts.generate_base
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь, чтобы работали импорты
sys.path.insert(0, str(Path(__file__).parent.parent))

from transcribo.core.database import DatabaseStore
from transcribo.core.engine import TranscriptionEngine

# Базовый список слов и брендов (в реальности можно скачать файл из интернета)
WORDS_TO_GENERATE = [
    "Nike", "Hermès", "Porsche", "Xiaomi", "Samsung", "Adidas",
    "Levi's", "Louis Vuitton", "Gucci", "H&M", "though", "through",
    "colonel", "queue", "choir", "pneumonia", "subtle", "island",
    "rhythm", "anemone", "docker", "linux", "github", "python"
]

def main():
    print("Запуск генерации базового словаря...")
    db_path = Path(__file__).parent.parent / "resources" / "base_vocabulary.db"
    store = DatabaseStore(db_path)
    engine = TranscriptionEngine()

    for word in WORDS_TO_GENERATE:
        # Сначала проверяем, есть ли слово в базе (чтобы не перезаписывать ручные правки)
        existing = store.get_all()
        if any(e.word == word and e.source == "user" for e in existing):
            continue

        # Если слова нет, генерируем транскрипцию с помощью движка
        # В реальности здесь можно использовать IPA-словарь для точности,
        # но для примера используем наш движок.
        transcription = engine.transcribe(word)
        
        # Сохраняем с пометкой "auto"
        store.add(word, transcription, source="auto")
        print(f"  {word} -> {transcription}")

    print(f"Готово! База данных сохранена в {db_path}")
    print(f"Всего слов в базе: {store.count()}")

if __name__ == "__main__":
    main()