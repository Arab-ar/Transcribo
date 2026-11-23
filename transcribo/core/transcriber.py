import eng_to_ipa as ipa
# Правильный импорт с указанием папки core
from transcribo.core.ipa_to_cyrillic import ipa_to_cyrillic

class Transcriber:
    def transcribe(self, word: str) -> str:
        try:
            # Получаем IPA транскрипцию английского слова
            ipa_word = ipa.convert(word)
            
            # Если слово не найдено, библиотека ставит звездочку '*'
            if '*' in ipa_word:
                return word
                
            # Конвертируем IPA в кириллицу
            return ipa_to_cyrillic(ipa_word)
        except Exception:
            return word