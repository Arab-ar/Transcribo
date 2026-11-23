"""Фоновый обработчик для транскрипции."""

from PySide6.QtCore import QThread, Signal
from transcribo.core.engine import TranscriptionEngine

class TranscriptionWorker(QThread):
    # Сигналы для связи с главным потоком (GUI)
    finished = Signal(str)  # Передает готовый текст
    error = Signal(str)     # Передает текст ошибки

    def __init__(self, engine: TranscriptionEngine, text: str):
        super().__init__()
        self.engine = engine
        self.text = text

    def run(self):
        try:
            # Вся тяжелая работа происходит здесь, в отдельном потоке
            result = self.engine.transcribe(self.text)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))