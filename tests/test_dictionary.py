"""Тесты базы данных SQLite."""

from pathlib import Path
from transcribo.core.database import DatabaseStore

def test_add_and_get(tmp_path: Path):
    db_path = tmp_path / "test.db"
    store = DatabaseStore(db_path)
    
    store.add("docker", "докер", source="user")
    vocab = store.as_vocabulary()
    assert vocab["docker"] == "докер"
    assert store.count() == 1

def test_remove(tmp_path: Path):
    db_path = tmp_path / "test.db"
    store = DatabaseStore(db_path)
    store.add("docker", "докер")
    store.remove("docker")
    assert store.count() == 0

def test_source_priority(tmp_path: Path):
    db_path = tmp_path / "test.db"
    store = DatabaseStore(db_path)
    
    # Добавляем авто-слово
    store.add("apple", "эппл", source="auto")
    # Перезаписываем его как пользовательское
    store.add("apple", "эппл (яблоко)", source="user")
    
    entries = store.get_all()
    assert len(entries) == 1
    assert entries[0].transcription == "эппл (яблоко)"
    assert entries[0].source == "user"