"""Ядро приложения: оболочка над базой данных и движком."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from eng_to_ru_transcriber import Transcriber
from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic
from transcribo.core.database import DatabaseStore

class TranscriptionEngine:
    def __init__(self, base_db_path: Path | None = None, user_db_path: Path | None = None) -> None:
        self._vocabulary = {}
        
        # 1. Загружаем базовую базу (207 000 слов)
        if base_db_path and base_db_path.exists():
            base_store = DatabaseStore(base_db_path)
            self._vocabulary.update(base_store.as_vocabulary())
            
        # 2. Поверх неё накладываем пользовательскую (ваши правки имеют приоритет)
        if user_db_path and user_db_path.exists():
            user_store = DatabaseStore(user_db_path)
            self._vocabulary.update(user_store.as_vocabulary())
            
        self._transcriber = Transcriber(custom_vocabulary={})

    def _preprocess(self, text: str) -> str:
        text = text.replace("&", " and ")
        return re.sub(r'\s+', ' ', text).strip()

    def transcribe(self, text: str) -> str:
        if not text.strip():
            return ""
        
        clean_text = self._preprocess(text)
        words = clean_text.split()
        result_words = []
        
        for word in words:
            clean_word = re.sub(r'[^\w\s\'-]', '', word).lower()
            if not clean_word:
                result_words.append(word)
                continue
            
            if clean_word in self._vocabulary:
                transcription = self._vocabulary[clean_word]
                # Если это IPA — конвертируем
                if any(c in transcription for c in "ˈˌæɒŋθðʃʒɜː"):
                    result_words.append(ipa_to_cyrillic(transcription))
                else:
                    result_words.append(transcription)
            else:
                result_words.append(self._transcriber.transcribe(word))
                
        return " ".join(result_words)