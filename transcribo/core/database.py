"""Хранилище словаря на базе SQLite."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from dataclasses import dataclass

@dataclass
class DictionaryEntry:
    word: str
    transcription: str
    source: str = "user"  # "user" (создано человеком) или "auto" (сгенерировано)

class DatabaseStore:
    """Управляет SQLite базой данных словаря."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Создает таблицу, если её нет."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    word TEXT PRIMARY KEY,
                    transcription TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'user'
                )
            """)
            conn.commit()

    def add(self, word: str, transcription: str, source: str = "user") -> bool:
        """Добавляет или обновляет слово."""
        with sqlite3.connect(self._db_path) as conn:
            try:
                conn.execute(
                    "INSERT OR REPLACE INTO vocabulary (word, transcription, source) VALUES (?, ?, ?)",
                    (word, transcription, source)
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    def remove(self, word: str) -> None:
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM vocabulary WHERE word = ?", (word,))
            conn.commit()

    def as_vocabulary(self) -> dict[str, str]:
        """Возвращает словарь в формате, который ждет TranscriptionEngine."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT word, transcription FROM vocabulary")
            return {row[0]: row[1] for row in cursor}

    def get_all(self) -> list[DictionaryEntry]:
        """Возвращает все записи для отображения в таблице."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute("SELECT word, transcription, source FROM vocabulary ORDER BY word")
            return [DictionaryEntry(row[0], row[1], row[2]) for row in cursor]

    def count(self) -> int:
        with sqlite3.connect(self._db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0]