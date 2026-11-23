"""Хранилище пользовательского словаря."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class DictionaryEntry:
    """Одна запись словаря."""
    word: str
    transcription: str
    comment: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> list[str]:
        problems: list[str] = []
        if not self.word.strip():
            problems.append("Слово не может быть пустым")
        elif not self.word.isascii():
            problems.append("Слово должно содержать только латиницу")
        if not self.transcription.strip():
            problems.append("Транскрипция не может быть пустой")
        return problems


class DictionaryStore:
    """Загружает и сохраняет словарь в JSON-файл."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, DictionaryEntry] = {}
        self.load()

    def all_entries(self) -> list[DictionaryEntry]:
        return list(self._entries.values())

    def as_vocabulary(self) -> dict[str, str]:
        return {e.word: e.transcription for e in self._entries.values()}

    def get(self, word: str) -> DictionaryEntry | None:
        return self._entries.get(word)

    def add(self, entry: DictionaryEntry) -> list[str]:
        problems = entry.validate()
        if problems:
            return problems
        if entry.word in self._entries:
            return [f"Слово '{entry.word}' уже есть в словаре"]
        self._entries[entry.word] = entry
        return []

    def update(self, original_word: str, entry: DictionaryEntry) -> list[str]:
        problems = entry.validate()
        if problems:
            return problems
        if original_word not in self._entries:
            return [f"Слова '{original_word}' нет в словаре"]
        if entry.word != original_word and entry.word in self._entries:
            return [f"Слово '{entry.word}' уже есть в словаре"]
        del self._entries[original_word]
        self._entries[entry.word] = entry
        return []

    def remove(self, word: str) -> bool:
        return self._entries.pop(word, None) is not None

    def load(self) -> None:
        if not self._path.exists():
            self._entries = {}
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._entries = {item["word"]: DictionaryEntry(**item) for item in raw.get("entries", [])}
        except (json.JSONDecodeError, OSError):
            self._entries = {}

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"entries": [asdict(e) for e in self._entries.values()]}
        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")