"""Тесты хранилища словаря."""

from pathlib import Path

from transcribo.core.dictionary import DictionaryEntry, DictionaryStore


def make_store(tmp_path: Path) -> DictionaryStore:
    return DictionaryStore(tmp_path / "vocab.json")


def test_add_valid_entry(tmp_path):
    store = make_store(tmp_path)
    problems = store.add(DictionaryEntry(word="docker", transcription="докер"))
    assert problems == []
    assert store.as_vocabulary() == {"docker": "докер"}


def test_reject_empty_word(tmp_path):
    store = make_store(tmp_path)
    problems = store.add(DictionaryEntry(word="  ", transcription="докер"))
    assert any("пустым" in p for p in problems)


def test_reject_cyrillic_word(tmp_path):
    store = make_store(tmp_path)
    problems = store.add(DictionaryEntry(word="докер", transcription="докер"))
    assert any("латиницу" in p for p in problems)


def test_reject_duplicate(tmp_path):
    store = make_store(tmp_path)
    store.add(DictionaryEntry(word="docker", transcription="докер"))
    problems = store.add(DictionaryEntry(word="docker", transcription="докер"))
    assert any("уже есть" in p for p in problems)


def test_save_and_reload(tmp_path):
    path = tmp_path / "vocab.json"
    store = DictionaryStore(path)
    store.add(DictionaryEntry(word="docker", transcription="докер", comment="тех."))
    store.save()

    reloaded = DictionaryStore(path)
    assert reloaded.as_vocabulary() == {"docker": "докер"}
    assert reloaded.get("docker").comment == "тех."


def test_broken_json_does_not_crash(tmp_path):
    path = tmp_path / "vocab.json"
    path.write_text("{это не json", encoding="utf-8")
    store = DictionaryStore(path)
    assert store.all_entries() == []