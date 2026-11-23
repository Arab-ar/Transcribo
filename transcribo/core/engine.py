"""Ядро приложения: обёртка над eng-to-ru-transcriber."""

from __future__ import annotations

from eng_to_ru_transcriber import Transcriber


class TranscriptionEngine:
    """Изолирует логику транскрипции от интерфейса."""

    def __init__(self, custom_vocabulary: dict[str, str] | None = None) -> None:
        self._vocabulary: dict[str, str] = dict(custom_vocabulary or {})
        self._transcriber = Transcriber(custom_vocabulary=self._vocabulary)

    def transcribe(self, text: str) -> str:
        """Принимает английский текст, возвращает кириллическую транскрипцию."""
        if not text.strip():
            return ""
        return self._transcriber.transcribe(text)

    def update_vocabulary(self, custom_vocabulary: dict[str, str]) -> None:
        """Пересоздаёт внутренний Transcriber с новым словарём."""
        self._vocabulary = dict(custom_vocabulary)
        self._transcriber = Transcriber(custom_vocabulary=self._vocabulary)

    @property
    def vocabulary(self) -> dict[str, str]:
        """Копия текущего словаря."""
        return dict(self._vocabulary)