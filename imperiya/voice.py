"""2-agent: Diktor. Edge TTS (bepul) orqali o'zbekcha ovoz."""
import asyncio
import subprocess
from pathlib import Path

import edge_tts

from . import config


async def _synth(text: str, voice: str, out: Path) -> None:
    await edge_tts.Communicate(text, voice).save(str(out))


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def narrate(scenes: list[dict], folder: Path) -> list[dict]:
    voice = config.get("TTS_VOICE", "uz-UZ-MadinaNeural")
    folder.mkdir(parents=True, exist_ok=True)
    for i, scene in enumerate(scenes):
        out = folder / f"voice_{i}.mp3"
        asyncio.run(_synth(scene["text"], voice, out))
        scene["audio"] = out
        scene["duration"] = duration(out) + 0.25  # sahnalar orasida qisqa pauza
    return scenes
