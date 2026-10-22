"""3-agent: Rassom. pollinations.ai'dan bepul tasvir; ishlamasa gradient zaxira tasvir."""
import subprocess
import time
import urllib.parse
from pathlib import Path

import requests

from . import config

STYLE = ", cinematic, vertical composition, high detail, no text, no watermark"


def _fallback(out: Path, index: int) -> None:
    colors = ["0x1b2a49", "0x3a1c71", "0x0f4c5c", "0x5f0f40", "0x264653"]
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={colors[index % len(colors)]}:s={config.VIDEO_W}x{config.VIDEO_H}",
         "-frames:v", "1", str(out)],
        capture_output=True, check=True,
    )


def paint(scenes: list[dict], folder: Path, seed: int = 7) -> list[dict]:
    folder.mkdir(parents=True, exist_ok=True)
    for i, scene in enumerate(scenes):
        out = folder / f"img_{i}.jpg"
        prompt = urllib.parse.quote(scene["image_prompt"] + STYLE)
        url = (f"https://image.pollinations.ai/prompt/{prompt}"
               f"?width={config.VIDEO_W}&height={config.VIDEO_H}&nologo=true&seed={seed + i}")
        ok = False
        for attempt in range(3):
            try:
                r = requests.get(url, timeout=120)
                if r.ok and r.headers.get("content-type", "").startswith("image"):
                    out.write_bytes(r.content)
                    ok = True
                    break
            except requests.RequestException:
                pass
            time.sleep(3 * (attempt + 1))
        if not ok:
            _fallback(out, i)
        scene["image"] = out
    return scenes
