import re
import unicodedata
import os

# ЖЕСТКО ПРОПИСЫВАЕМ ПУТЬ К ESPEAK ДЛЯ WINDOWS
espeak_path = r"C:\Program Files\eSpeak NG\libespeak-ng.dll"
if os.path.exists(espeak_path):
    os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = espeak_path

try:
    from phonemizer import phonemize
    PHONEMIZER_AVAILABLE = True
except ImportError:
    PHONEMIZER_AVAILABLE = False
    print("ВНИМАНИЕ: Phonemizer не установлен. Установите: pip install phonemizer")

from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic

class Transcriber:
    def __init__(self):
        self.fallback_rules = [
            ("sh", "ш"), ("ch", "ч"), ("th", "т"), ("ph", "ф"), ("kh", "х"),
            ("ya", "я"), ("yu", "ю"), ("yo", "ё"), ("ye", "е"),
            ("a", "а"), ("b", "б"), ("v", "в"), ("g", "г"), ("d", "д"),
            ("e", "е"), ("z", "з"), ("i", "и"), ("k", "к"), ("l", "л"),
            ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"), ("r", "р"),
            ("s", "с"), ("t", "т"), ("u", "у"), ("f", "ф"), ("h", "х"),
            ("c", "к"), ("w", "в"), ("y", "й"), ("x", "кс"), ("j", "дж"),
        ]
        self.espeak_lang_map = {
            'en': 'en-us',
            'fr': 'fr-fr',
            'de': 'de',
            'es': 'es'
        }

    def _normalize(self, text: str) -> str:
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

    def _detect_language(self, word: str) -> str:
        if any(c in word for c in "èéêàâîôûçœæ"): return 'fr'
        if any(c in word for c in "äöüß"): return 'de'
        if any(c in word for c in "ñ"): return 'es'
        return 'en'

    def _apply_fallback_rules(self, word: str) -> str:
        word = word.lower()
        result = ""
        i = 0
        while i < len(word):
            matched = False
            for length in [2, 1]:
                chunk = word[i:i+length]
                for eng, rus in self.fallback_rules:
                    if chunk == eng:
                        result += rus
                        i += length
                        matched = True
                        break
                if matched:
                    break
            if not matched:
                result += word[i]
                i += 1
        return result.capitalize()

    def transcribe(self, word: str) -> str:
        normalized_word = self._normalize(word)
        if not normalized_word.strip():
            return word

        lang = self._detect_language(word)
        
        if PHONEMIZER_AVAILABLE:
            try:
                espeak_lang = self.espeak_lang_map.get(lang, 'en-us')
                ipa_transcription = phonemize(
                    normalized_word,
                    language=espeak_lang,
                    backend='espeak',
                    strip=True,
                    preserve_punctuation=True
                )
                return ipa_to_cyrillic(ipa_transcription)
            except Exception as e:
                print(f"Phonemizer error for '{word}': {e}")

        if lang == 'en':
            try:
                import eng_to_ipa as ipa
                ipa_word = ipa.convert(normalized_word)
                if '*' not in ipa_word:
                    return ipa_to_cyrillic(ipa_word)
            except Exception:
                pass
        
        return self._apply_fallback_rules(normalized_word)