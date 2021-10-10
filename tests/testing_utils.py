from pathlib import Path


def get_file(name: str) -> Path:
    return Path(__file__).resolve().parent / "files" / name
