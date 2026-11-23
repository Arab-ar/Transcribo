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
        self._vocabulary = {} # Теперь тут будет храниться: {"слово": {"transcription": "...", "source": "..."}}

        # 1. Базовая база
        if base_db_path and base_db_path.exists():
            base_store = DatabaseStore(base_db_path)
            for k, v in base_store.as_vocabulary().items():
                clean_k = self._transcriber._normalize(k).lower()
                self._vocabulary[clean_k] = {"transcription": v, "source": "base"}

        # 2. Внешние словари (имена, бренды)
        self._load_external_dictionaries()

        # 3. Пользовательская база (самый высокий приоритет)
        if user_db_path and user_db_path.exists():
            user_store = DatabaseStore(user_db_path)
            for k, v in user_store.as_vocabulary().items():
                clean_k = self._transcriber._normalize(k).lower()
                self._vocabulary[clean_k] = {"transcription": v, "source": "user"}

    def _load_external_dictionaries(self):
        if hasattr(sys, '_MEIPASS'):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).parent.parent.parent
            
        dict_dir = base_path / "resources" / "dictionaries"
        
        if not dict_dir.exists():
            return

        for json_file in dict_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        # Применяем нормализацию, чтобы "beyoncé" и "beyonce" были одинаковыми
                        clean_k = self._transcriber._normalize(k).lower()
                        # Имя файла (например, "names" или "brands") используем как источник
                        self._vocabulary[clean_k] = {"transcription": v, "source": json_file.stem}
            except Exception as e:
                print(f"Ошибка загрузки {json_file.name}: {e}")

    def _preprocess(self, text: str) -> str:
        return text.strip()

    def transcribe(self, text: str) -> str:
        if not text.strip():
            return ""
        
        # Разбиваем текст по переносам строк, чтобы сохранить структуру абзацев
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            clean_text = line.strip()
            if not clean_text:
                processed_lines.append("")
                continue

            words = clean_text.split()
            result_parts = []
            i = 0

            while i < len(words):
                matched = False
                for length in range(min(5, len(words) - i), 0, -1):
                    phrase_words = words[i:i + length]
                    clean_phrase = " ".join(
                        self._transcriber._normalize(re.sub(r'[^\w\s\'-]', '', w)).lower() for w in phrase_words
                    )
                    
                    if clean_phrase in self._vocabulary:
                        entry = self._vocabulary[clean_phrase]
                        trans = entry["transcription"]
                        if any(c in trans for c in "ˈˌæɒŋθðʃʒɜː"):
                            trans = ipa_to_cyrillic(trans)
                        
                        # Добавляем источник в квадратных скобках для наглядности
                        result_parts.append(f"{trans} [{entry['source']}]")
                        i += length
                        matched = True
                        break
                
                if not matched:
                    word = words[i]
                    clean_word = self._transcriber._normalize(re.sub(r'[^\w\s\'-]', '', word)).lower()
                    
                    if not clean_word:
                        result_parts.append(word)
                    elif clean_word in self._vocabulary:
                        entry = self._vocabulary[clean_word]
                        trans = entry["transcription"]
                        if any(c in trans for c in "ˈˌæɒŋθðʃʒɜː"):
                            trans = ipa_to_cyrillic(trans)
                        result_parts.append(f"{trans} [{entry['source']}]")
                    else:
                        trans = self._transcriber.transcribe(word)
                        result_parts.append(f"{trans} [transcriber]")
                    
                    i += 1

            processed_lines.append(" ".join(result_parts))

        return "\n".join(processed_lines)