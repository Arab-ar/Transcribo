"""Конвертер IPA в русскую кириллицу."""
import re

IPA_TO_RU = {
    "eɪ": "ей", "aɪ": "ай", "ɔɪ": "ой", "aʊ": "ау", "əʊ": "оу", "oʊ": "оу",
    "ɪə": "иэ", "eə": "эа", "ʊə": "уа", "juː": "ью", "ju": "ю",
    "iː": "и", "ɑː": "а", "ɔː": "о", "uː": "у", "ɜː": "ё", 
    "ɪ": "и", "e": "э", "æ": "э", "ʌ": "а", "ɒ": "о", "ʊ": "у", "ə": "э",
    "tʃ": "ч", "dʒ": "дж", "ʃ": "ш", "ʒ": "ж", "θ": "с", "ð": "з", "ŋ": "нг",
    "p": "п", "b": "б", "t": "т", "d": "д", "k": "к", "g": "г", "ɡ": "г", 
    "f": "ф", "v": "в", "s": "с", "z": "з", "h": "х", "m": "м", "n": "н", 
    "l": "л", "r": "р", "j": "й", "w": "в",
    "ˈ": "", "ˌ": "", "ː": "",
}

def ipa_to_cyrillic(ipa_text: str) -> str:
    if not ipa_text:
        return ""
    
    text = ipa_text.lower()
    result = text
    
    sorted_keys = sorted(IPA_TO_RU.keys(), key=len, reverse=True)
    for ipa_sound in sorted_keys:
        result = result.replace(ipa_sound, IPA_TO_RU[ipa_sound])
    
    result = re.sub(r'[^а-яё\s\-]', '', result)
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result.capitalize()