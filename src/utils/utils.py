import shutil
from pathlib import Path

def delete_path(path: str):
    try:
        shutil.rmtree(path)
    except OSError as e:
        print(f"Error: {path} : {e}")


def create_path(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)
    


