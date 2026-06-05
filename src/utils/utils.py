import shutil
from pathlib import Path


def delete_path(path: str):
    try:
        shutil.rmtree(path)
    except OSError as e:
        print(f"Error: {path} : {e}")


def create_path(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def format_time(seconds: float):
    hours: int = int(seconds // 3600)
    minutes: int = int((seconds % 3600) // 60)
    secs: int = int(seconds % 60)
    milliseconds: int = int((seconds % 1) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
