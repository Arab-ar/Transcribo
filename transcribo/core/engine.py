"""Ядро приложения: обёртка над eng-to-ru-transcriber."""

from __future__ import annotations

import re
from eng_to_ru_transcriber import Transcriber


class TranscriptionEngine:
    """Изолирует логику транскрипции от интерфейса."""

    def __init__(self, custom_vocabulary: dict[str, str] | None = None) -> None:
        self._vocabulary: dict[str, str] = dict(custom_vocabulary or {})
        self._transcriber = Transcriber(custom_vocabulary=self._vocabulary)

    def _preprocess(self, text: str) -> str:
        """Готовит текст к транскрипции, обрабатывая спецсимволы."""
        # Заменяем амперсанд на слово "and" (движок прочитает его как "энд")
        text = text.replace("&", " and ")
        # Можно добавить другие замены: "+" на " plus ", "@" на " at " и т.д.
        # text = text.replace("+", " plus ")
        
        # Убираем лишние пробелы, которые могли возникнуть
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def transcribe(self, text: str) -> str:
        """Принимает английский текст, возвращает кириллическую транскрипцию."""
        if not text.strip():
            return ""
        
        # Предварительная обработка
        clean_text = self._preprocess(text)
        
        # Если в словаре пользователя есть слово "and" -> "энд", оно применится.
        # Если нет, библиотека сама прочитает "and" как "энд".
        return self._transcriber.transcribe(clean_text)

    def update_vocabulary(self, custom_vocabulary: dict[str, str]) -> None:
        """Пересоздаёт внутренний Transcriber с новым словарём."""
        self._vocabulary = dict(custom_vocabulary)
        self._transcriber = Transcriber(custom_vocabulary=self._vocabulary)

    @property
    def vocabulary(self) -> dict[str, str]:
        """Копия текущего словаря."""
        return dict(self._vocabulary)