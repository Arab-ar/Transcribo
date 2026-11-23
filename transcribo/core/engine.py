import re
import sys
import json
from pathlib import Path
from transcribo.core.database import DatabaseStore
from transcribo.core.transcriber import Transcriber
from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic 

class TranscriptionEngine:
    def __init__(self, base_db_path: Path = None, user_db_path: Path = None):
        self._transcriber = Transcriber()
        self._vocabulary = {}

        # 1. Загружаем базовую базу (ваши 207 000 слов) - ОСТАВЛЯЕМ
        if base_db_path and base_db_path.exists():
            base_store = DatabaseStore(base_db_path)
            base_vocab = {k.lower(): v for k, v in base_store.as_vocabulary().items()}
            self._vocabulary.update(base_vocab)

        # 2. Загружаем внешние словари (бренды, имена из JSON) - ДОБАВЛЯЕМ
        self._load_external_dictionaries()

        # 3. Накладываем пользовательскую базу (ваши правки из интерфейса - самый высокий приоритет)
        if user_db_path and user_db_path.exists():
            user_store = DatabaseStore(user_db_path)
            user_vocab = {k.lower(): v for k, v in user_store.as_vocabulary().items()}
            self._vocabulary.update(user_vocab)

    def _load_external_dictionaries(self):
        """Сканирует папку resources/dictionaries и загружает все JSON-файлы"""
        # Определяем базовый путь (работает и в обычном запуске, и в собранном .exe)
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.parent
            
        dict_dir = base_path / "resources" / "dictionaries"
        
        # Если папки нет — просто выходим (программа будет работать только на базовой базе)
        if not dict_dir.exists():
            return

        for json_file in dict_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Приводим все ключи к нижнему регистру для единообразия
                    clean_data = {k.lower(): v for k, v in data.items()}
                    self._vocabulary.update(clean_data)
            except Exception as e:
                print(f"Ошибка загрузки словаря {json_file.name}: {e}")

    def _preprocess(self, text: str) -> str:
        return text.strip()

    def transcribe(self, text: str) -> str:
        if not text.strip():
            return ""
        
        clean_text = self._preprocess(text)
        words = clean_text.split()
        result_parts = []
        i = 0

        while i < len(words):
            matched = False
            # Ищем фразы до 5 слов (для "Louis Vuitton" и т.д.)
            for length in range(min(5, len(words) - i), 0, -1):
                phrase_words = words[i:i + length]
                
                # Очищаем фразу от знаков препинания и акцентов для поиска
                clean_phrase = " ".join(
                    self._transcriber._normalize(re.sub(r'[^\w\s\'-]', '', w)).lower() for w in phrase_words
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
                clean_word = self._transcriber._normalize(re.sub(r'[^\w\s\'-]', '', word)).lower()
                
                if not clean_word:
                    result_parts.append(word)
                elif clean_word in self._vocabulary:
                    transcription = self._vocabulary[clean_word]
                    if any(c in transcription for c in "ˈˌæɒŋθðʃʒɜː"):
                        result_parts.append(ipa_to_cyrillic(transcription))
                    else:
                        result_parts.append(transcription)
                else:
                    # Если слова нет ни в базе, ни в JSON, ни у пользователя — умный Transcriber
                    result_parts.append(self._transcriber.transcribe(word))
                
                i += 1

        return " ".join(result_parts)