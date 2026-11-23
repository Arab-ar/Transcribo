import urllib.request
from pathlib import Path

def download_openepd():
    # URL к файлу данных в репозитории GitHub
    url = "https://raw.githubusercontent.com/JackDanger/open-english-pronouncing-dictionary/main/data/openepd.json"
    
    # Путь для сохранения (в папку resources)
    resources_dir = Path(__file__).parent.parent / "resources"
    resources_dir.mkdir(exist_ok=True)
    output_path = resources_dir / "openepd.json"
    
    if output_path.exists():
        print(f"Файл уже существует: {output_path}")
        return
    
    print(f"Скачивание OpenEPD с {url}...")
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"Готово! Файл сохранен: {output_path}")
        print(f"Размер файла: {output_path.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")

if __name__ == "__main__":
    download_openepd()