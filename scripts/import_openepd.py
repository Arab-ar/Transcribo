import json
import sqlite3
from pathlib import Path

def import_openepd_to_db():
    # Пути
    resources_dir = Path(__file__).parent.parent / "resources"
    json_path = resources_dir / "openepd.json"
    
    # ИСПРАВЛЕНИЕ: база должна лежать в корневой папке resources
    db_path = resources_dir / "base_vocabulary.db"
    
    if not json_path.exists():
        print("Ошибка: сначала скачайте OpenEPD (запустите download_openepd.py)")
        return

    # На всякий случай создаем папку, если её нет
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print("Загрузка JSON...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Записей в JSON: {len(data)}")
    
    # Подключаемся к базе
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Создаем таблицу, если её нет
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocabulary (
            word TEXT PRIMARY KEY,
            transcription TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'auto'
        )
    """)
    
    # Пакетная вставка (по 1000 записей) для скорости
    batch = []
    batch_size = 1000
    inserted = 0
    
    print("Начинаем импорт (это может занять 1-2 минуты)...")
    
    for word, entry in data.items():
        ipa_dict = entry.get("ipa", {})
        # Приоритет: misaki_gold -> cmu -> wikipron
        ipa = ipa_dict.get("misaki_gold") or ipa_dict.get("cmu") or ipa_dict.get("wikipron")
        
        if ipa:
            batch.append((word.lower(), ipa, "openepd_auto"))
            inserted += 1
        
        if len(batch) >= batch_size:
            cursor.executemany(
                "INSERT OR REPLACE INTO vocabulary (word, transcription, source) VALUES (?, ?, ?)",
                batch
            )
            conn.commit()
            if inserted % 50000 == 0:
                print(f"  Вставлено {inserted} слов...")
            batch = []
    
    # Вставляем остатки
    if batch:
        cursor.executemany(
            "INSERT OR REPLACE INTO vocabulary (word, transcription, source) VALUES (?, ?, ?)",
            batch
        )
        conn.commit()
    
    conn.close()
    print(f"Импорт завершен! Всего вставлено: {inserted} слов.")
    print(f"Файл базы данных: {db_path}")

if __name__ == "__main__":
    import_openepd_to_db()