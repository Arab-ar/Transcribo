import re
import unicodedata
import os

# Импортируем Phonemizer. Оборачиваем в try-except, чтобы программа работала даже если он не установлен.
try:
    from phonemizer import phonemize
    from phonemizer.backend import EspeakBackend
    PHONEMIZER_AVAILABLE = True
except ImportError:
    PHONEMIZER_AVAILABLE = False
    print("ВНИМАНИЕ: Phonemizer не установлен. Сложные имена могут обрабатываться некорректно.")
    print("Установите: pip install phonemizer, а также eSpeak-NG.")

from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic

class Transcriber:
    def __init__(self):
        # Правила транслитерации (используются как запасной вариант)
        self.fallback_rules = [
            ("sh", "ш"), ("ch", "ч"), ("th", "т"), ("ph", "ф"), ("kh", "х"),
            ("ya", "я"), ("yu", "ю"), ("yo", "ё"), ("ye", "е"),
            ("a", "а"), ("b", "б"), ("v", "в"), ("g", "г"), ("d", "д"),
            ("e", "е"), ("z", "з"), ("i", "и"), ("k", "к"), ("l", "л"),
            ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"), ("r", "р"),
            ("s", "с"), ("t", "т"), ("u", "у"), ("f", "ф"), ("h", "х"),
            ("c", "к"), ("w", "в"), ("y", "й"), ("x", "кс"), ("j", "дж"),
        ]
        # Соответствие наших внутренних кодов языков для eSpeak-NG
        self.espeak_lang_map = {
            'en': 'en-us',
            'fr': 'fr-fr',
            'de': 'de',
            'es': 'es'
        }

    def _normalize(self, text: str) -> str:
        """Убирает акценты и спецсимволы для поиска в базе (Hermès -> Hermes)"""
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

    def _detect_language(self, word: str) -> str:
        """Определяет язык по спецсимволам (диакритике)"""
        if any(c in word for c in "èéêàâîôûçœæ"): return 'fr'
        if any(c in word for c in "äöüß"): return 'de'
        if any(c in word for c in "ñ"): return 'es'
        return 'en'

    def _apply_fallback_rules(self, word: str) -> str:
        """Транслитерация, если Phonemizer недоступен или не справился"""
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
        # 1. Нормализуем слово (убираем акценты для возможного поиска)
        normalized_word = self._normalize(word)
        if not normalized_word.strip():
            return word

        # 2. Определяем язык
        lang = self._detect_language(word)
        
        # 3. Если Phonemizer доступен, пробуем использовать его
        if PHONEMIZER_AVAILABLE:
            try:
                espeak_lang = self.espeak_lang_map.get(lang, 'en-us')
                # Получаем IPA-транскрипцию с помощью Phonemizer
                ipa_transcription = phonemize(
                    normalized_word,
                    language=espeak_lang,
                    backend='espeak',
                    strip=True,
                    preserve_punctuation=True
                )
                # Конвертируем IPA в кириллицу
                return ipa_to_cyrillic(ipa_transcription)
            except Exception as e:
                # Если Phonemizer выдал ошибку, переходим к запасному варианту
                print(f"Phonemizer error for '{word}': {e}")

        # 4. Запасной вариант (если Phonemizer недоступен или не справился)
        # Для английского сначала пробуем старый добрый eng_to_ipa
        if lang == 'en':
            try:
                import eng_to_ipa as ipa
                ipa_word = ipa.convert(normalized_word)
                if '*' not in ipa_word:
                    return ipa_to_cyrillic(ipa_word)
            except Exception:
                pass
        
        # Если ничего не помогло, используем простую транслитерацию
        return self._apply_fallback_rules(normalized_word)