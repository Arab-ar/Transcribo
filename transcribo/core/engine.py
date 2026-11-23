import re
import sys
import json
import spacy
from pathlib import Path
from transcribo.core.database import DatabaseStore
from transcribo.core.transcriber import Transcriber
from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic 

class TranscriptionEngine:
    def __init__(self, base_db_path: Path = None, user_db_path: Path = None):
        self._transcriber = Transcriber()
        self._vocabulary = {} 
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            self.nlp = None

        if base_db_path and base_db_path.exists():
            base_store = DatabaseStore(base_db_path)
            for k, v in base_store.as_vocabulary().items():
                clean_k = self._transcriber._normalize(k).lower()
                self._vocabulary[clean_k] = {"transcription": v, "source": "base"}

        self._load_external_dictionaries()

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
                        clean_k = self._transcriber._normalize(k).lower()
                        self._vocabulary[clean_k] = {"transcription": v, "source": json_file.stem}
            except Exception as e:
                print(f"Ошибка загрузки {json_file.name}: {e}")

    def add_user_word(self, word: str, transcription: str):
        clean_k = self._transcriber._normalize(word).lower()
        self._vocabulary[clean_k] = {"transcription": transcription, "source": "user"}

    def transcribe(self, text: str) -> str:
        if not text.strip():
            return ""
        
        lines = text.split('\n')
        processed_lines = []

        for line in lines:
            clean_text = line.strip()
            if not clean_text:
                processed_lines.append("")
                continue

            if self.nlp:
                doc = self.nlp(clean_text)
                entities = {}
                for ent in doc.ents:
                    for token in ent:
                        entities[token.text.lower()] = ent.label_
            else:
                entities = {}

            words = clean_text.split()
            result_parts = []
            i = 0

            while i < len(words):
                matched = False
                
                # Ограничиваем поиск фраз до 3 слов (чтобы избежать багов с длинными именами)
                max_len = min(3, len(words) - i)
                for length in range(max_len, 0, -1):
                    phrase_words = words[i:i + length]
                    clean_phrase = " ".join(
                        self._transcriber._normalize(re.sub(r'[^\w\s\'-]', '', w)).lower() for w in phrase_words
                    )
                    
                    # Пропускаем пустые фразы
                    if not clean_phrase.strip():
                        continue
                        
                    if clean_phrase in self._vocabulary:
                        entry = self._vocabulary[clean_phrase]
                        trans = entry["transcription"]
                        if any(c in trans for c in "ˈˌæɒŋθðʃʒɜː"):
                            trans = ipa_to_cyrillic(trans)
                        
                        if trans:
                            trans = trans[0].upper() + trans[1:]
                            
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
                        
                        if trans:
                            trans = trans[0].upper() + trans[1:]
                            
                        result_parts.append(f"{trans} [{entry['source']}]")
                    else:
                        entity_type = entities.get(clean_word, None)
                        
                        if entity_type in ['PERSON', 'ORG', 'GPE', 'LOC', 'PRODUCT']:
                            trans = self._transcriber.transcribe(clean_word)
                            if trans:
                                trans = trans[0].upper() + trans[1:]
                            result_parts.append(f"{trans} [NER:{entity_type}]")
                        else:
                            trans = self._transcriber.transcribe(word)
                            if trans:
                                trans = trans[0].upper() + trans[1:]
                            result_parts.append(f"{trans} [transcriber]")
                    
                    i += 1

            processed_lines.append(" ".join(result_parts))

        return "\n".join(processed_lines)