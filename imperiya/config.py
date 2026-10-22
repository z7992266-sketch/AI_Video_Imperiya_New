"""Sozlamalar: .env faylidan va muhit o'zgaruvchilaridan o'qiydi. Kalitlar kodga yozilmaydi."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "work"
OUTPUT = ROOT / "output"


def load_env(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


load_env()

VIDEO_W, VIDEO_H, FPS = 1080, 1920, 30
