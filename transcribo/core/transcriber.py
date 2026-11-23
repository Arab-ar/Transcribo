import re
import unicodedata
import eng_to_ipa as ipa
from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic

class Transcriber:
    def __init__(self):
        self.lang_rules = {
            'fr': [
                ("eau", "о"), ("au", "о"), ("ou", "у"), ("oi", "уа"), ("ai", "э"), ("ei", "э"),
                ("ch", "ш"), ("gn", "нь"), ("qu", "к"), ("ph", "ф"),
                ("é", "э"), ("è", "э"), ("ê", "э"), ("à", "а"), ("â", "а"), ("î", "и"), ("ô", "о"), ("û", "у"), ("ç", "с"),
                ("s$", ""), ("t$", ""), ("x$", ""), ("e$", "")
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
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')

    def _detect_language(self, word: str) -> str:
        if any(c in word for c in "èéêàâîôûçœæ"): return 'fr'
        if any(c in word for c in "äöüß"): return 'de'
        if any(c in word for c in "ñ"): return 'es'
        return 'en'

    def _apply_rules(self, word: str, lang: str) -> str:
        word = word.lower()
        for pattern, replacement in self.lang_rules.get(lang, []):
            if pattern.endswith('$'):
                word = re.sub(pattern, replacement, word)
            else:
                word = word.replace(pattern, replacement)
        return word.capitalize()

    def _fallback_transliterate(self, word: str) -> str:
        """Транслитерация, если слово вообще нигде не найдено"""
        word = word.lower()
        rules = [
            ("sh", "ш"), ("ch", "ч"), ("th", "т"), ("ph", "ф"), ("kh", "х"),
            ("ya", "я"), ("yu", "ю"), ("yo", "ё"), ("ye", "е"),
            ("a", "а"), ("b", "б"), ("v", "в"), ("g", "г"), ("d", "д"),
            ("e", "е"), ("z", "з"), ("i", "и"), ("k", "к"), ("l", "л"),
            ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"), ("r", "р"),
            ("s", "с"), ("t", "т"), ("u", "у"), ("f", "ф"), ("h", "х"),
            ("c", "к"), ("w", "в"), ("y", "й"), ("x", "кс"), ("j", "дж"),
        ]
        result = ""
        i = 0
        while i < len(word):
            matched = False
            for length in [2, 1]:
                chunk = word[i:i+length]
                for eng, rus in rules:
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
        
        if lang == 'en':
            try:
                ipa_word = ipa.convert(normalized_word)
                if '*' not in ipa_word:
                    return ipa_to_cyrillic(ipa_word)
            except Exception:
                pass

        if lang != 'en':
            return self._apply_rules(normalized_word, lang)
            
        return self._fallback_transliterate(normalized_word)