"""4-agent: Montajchi. ffmpeg bilan tasvir + ovoz + subtitr -> vertikal .mp4"""
import subprocess
import textwrap
from pathlib import Path

from . import config


def _srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _run(cmd: list[str], cwd: Path) -> None:
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg xatosi:\n{res.stderr[-1500:]}")


def assemble(scenes: list[dict], work: Path, final: Path) -> Path:
    work = work.resolve()
    final = final.resolve()
    final.parent.mkdir(parents=True, exist_ok=True)
    W, H, FPS = config.VIDEO_W, config.VIDEO_H, config.FPS

    clips, srt_lines, t = [], [], 0.0
    for i, sc in enumerate(scenes):
        clip = work / f"clip_{i}.mp4"
        frames = int(sc["duration"] * FPS)
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='min(zoom+0.0012,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS},"
              f"format=yuv420p")
        _run(["ffmpeg", "-y", "-loop", "1", "-i", str(sc["image"]), "-i", str(sc["audio"]),
              "-vf", vf, "-t", f"{sc['duration']:.3f}", "-af", "apad", "-shortest",
              "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac", "-ar", "44100", "-ac", "2",
              str(clip)], work)
        clips.append(clip)
        text = "\n".join(textwrap.wrap(sc["text"], 28))
        srt_lines += [str(i + 1), f"{_srt_time(t)} --> {_srt_time(t + sc['duration'] - 0.1)}", text, ""]
        t += sc["duration"]

    (work / "subs.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    (work / "list.txt").write_text("".join(f"file '{c.name}'\n" for c in clips), encoding="utf-8")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "joined.mp4"], work)

    style = ("FontName=DejaVu Sans,FontSize=14,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
             "BorderStyle=1,Outline=2,Alignment=2,MarginV=40")  # libass: 288 birlikli koordinata
    _run(["ffmpeg", "-y", "-i", "joined.mp4", "-vf", f"subtitles=subs.srt:force_style='{style}'",
          "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "copy", "-movflags", "+faststart",
          str(final)], work)
    return final
