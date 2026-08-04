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
    ms_total = round(seconds * 1000)
    hours, ms_total = divmod(ms_total, 3_600_000)
    minutes, ms_total = divmod(ms_total, 60_000)
    secs, ms = divmod(ms_total, 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
