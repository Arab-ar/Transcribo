import re
import unicodedata
import eng_to_ipa as ipa
from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic

class Transcriber:
    def __init__(self):
        # Правила транслитерации для разных языков (если нет в словаре и IPA)
        self.lang_rules = {
            'fr': [
                ("eau", "о"), ("au", "о"), ("ou", "у"), ("oi", "уа"), ("ai", "э"), ("ei", "э"),
                ("ch", "ш"), ("gn", "нь"), ("qu", "к"), ("ph", "ф"),
                ("é", "э"), ("è", "э"), ("ê", "э"), ("à", "а"), ("â", "а"), ("î", "и"), ("ô", "о"), ("û", "у"), ("ç", "с"),
                ("s$", ""), ("t$", ""), ("x$", ""), ("e$", "") # Немые буквы на конце
            ],
            'de': [
                ("sch", "ш"), ("ch", "х"), ("ei", "ай"), ("ie", "и"), ("eu", "ой"), ("äu", "ой"),
                ("sp", "шп"), ("st", "шт"), ("ü", "ю"), ("ö", "ё"), ("ä", "э"), ("ß", "с")
            ],
            'es': [
                ("ll", "й"), ("ñ", "нь"), ("ch", "ч"), ("j", "х"), ("v", "б"), ("z", "с")
            ]
        }

    def _normalize(self, text: str) -> str:
        """Убирает акценты для поиска в базе (Hermès -> Hermes)"""
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

    def _detect_language(self, word: str) -> str:
        """Определяет язык по спецсимволам"""
        if any(c in word for c in "èéêàâîôûçœæ"): return 'fr'
        if any(c in word for c in "äöüß"): return 'de'
        if any(c in word for c in "ñ"): return 'es'
        return 'en'

    def _apply_rules(self, word: str, lang: str) -> str:
        """Применяет правила транслитерации для конкретного языка"""
        word = word.lower()
        for pattern, replacement in self.lang_rules.get(lang, []):
            if pattern.endswith('$'):
                # Обработка немых букв в конце
                word = re.sub(pattern, replacement, word)
            else:
                word = word.replace(pattern, replacement)
        return word.capitalize()

    def transcribe(self, word: str) -> str:
        # 1. Определяем язык
        lang = self._detect_language(word)
        
        # 2. Пробуем найти в IPA (только для английского или если слово без спецсимволов)
        normalized_word = self._normalize(word)
        
        if lang == 'en':
            try:
                ipa_word = ipa.convert(normalized_word)
                if '*' not in ipa_word:
                    return ipa_to_cyrillic(ipa_word)
            except Exception:
                pass

        # 3. Если английский движок не справился или язык не английский, используем правила
        return self._apply_rules(normalized_word, lang)