import re
from pathlib import Path
from transcribo.core.database import DatabaseStore
from transcribo.core.transcriber import Transcriber
# Правильный импорт с указанием папки core
from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic 

class TranscriptionEngine:
    def __init__(self, base_db_path: Path = None, user_db_path: Path = None):
        self._transcriber = Transcriber()
        self._vocabulary = {}

        # 1. Загружаем базовую базу (207 000 слов)
        if base_db_path and base_db_path.exists():
            base_store = DatabaseStore(base_db_path)
            # Приводим все ключи к нижнему регистру при загрузке
            base_vocab = {k.lower(): v for k, v in base_store.as_vocabulary().items()}
            self._vocabulary.update(base_vocab)

        # 2. Поверх неё накладываем пользовательскую (ваши правки имеют приоритет)
        if user_db_path and user_db_path.exists():
            user_store = DatabaseStore(user_db_path)
            # Приводим все ключи к нижнему регистру при загрузке
            user_vocab = {k.lower(): v for k, v in user_store.as_vocabulary().items()}
            self._vocabulary.update(user_vocab)

    def _preprocess(self, text: str) -> str:
        return text.strip()

    def transcribe(self, text: str) -> str:
        if not text.strip():
            return ""
        
        clean_text = self._preprocess(text)
        words = clean_text.split()
        result_parts = []
        i = 0

        # Поиск по фразам (от 5 слов до 1)
        while i < len(words):
            matched = False
            
            for length in range(min(5, len(words) - i), 0, -1):
                phrase_words = words[i:i + length]
                
                clean_phrase = " ".join(
                    re.sub(r'[^\w\s\'-]', '', w).lower() for w in phrase_words
                )
                
                if clean_phrase in self._vocabulary:
                    transcription = self._vocabulary[clean_phrase]
                    
                    if any(c in transcription for c in "ˈˌæɒŋθðʃʒɜː"):
                        result_parts.append(ipa_to_cyrillic(transcription))
                    else:
                        result_parts.append(transcription)
                    
                    i += length
                    matched = True
                    break
            
            # Если фраза не найдена, обрабатываем одно слово
            if not matched:
                word = words[i]
                clean_word = re.sub(r'[^\w\s\'-]', '', word).lower()
                
                if not clean_word:
                    result_parts.append(word)
                elif clean_word in self._vocabulary:
                    transcription = self._vocabulary[clean_word]
                    if any(c in transcription for c in "ˈˌæɒŋθðʃʒɜː"):
                        result_parts.append(ipa_to_cyrillic(transcription))
                    else:
                        result_parts.append(transcription)
                else:
                    result_parts.append(self._transcriber.transcribe(word))
                
                i += 1

        return " ".join(result_parts)