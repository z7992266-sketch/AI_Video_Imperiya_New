"""Kokoro TTS for fetch/tts/jobs/<name>.txt -> fetch/out/tts/<name>.mp3 + <name>.json (word timings [{w,s,e}]).
First line of the job may be: #voice=af_heart speed=0.95"""
import sys, os, json, subprocess, re
import numpy as np, soundfile as sf
from kokoro import KPipeline

def run(job):
    name = os.path.splitext(os.path.basename(job))[0]
    lines = open(job, encoding="utf-8").read().strip().splitlines()
    voice, speed = "af_heart", 1.0
    if lines and lines[0].startswith("#"):
        m = re.search(r"voice=(\S+)", lines[0]); voice = m.group(1) if m else voice
        m = re.search(r"speed=([\d.]+)", lines[0]); speed = float(m.group(1)) if m else speed
        lines = lines[1:]
    text = " ".join(l.strip() for l in lines if l.strip())
    pipe = KPipeline(lang_code=voice[0])
    audio, words, t = [], [], 0.0
    for res in pipe(text, voice=voice, speed=speed, split_pattern=r"(?<=[.!?])\s+"):
        a = res.audio.cpu().numpy() if hasattr(res.audio, "cpu") else np.asarray(res.audio)
        for tok in (res.tokens or []):
            if tok.start_ts is None or tok.end_ts is None:
                continue
            words.append({"w": tok.text, "s": round(t + tok.start_ts, 3), "e": round(t + tok.end_ts, 3)})
        audio.append(a); t += len(a) / 24000
        pad = np.zeros(int(0.25 * 24000), dtype=a.dtype); audio.append(pad); t += 0.25
    out = "fetch/out/tts"; os.makedirs(out, exist_ok=True)
    wav = f"/tmp/{name}.wav"; sf.write(wav, np.concatenate(audio), 24000)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "192k", f"{out}/{name}.mp3"], check=True)
    json.dump({"voice": voice, "speed": speed, "text": text, "duration": round(t, 3), "words": words},
              open(f"{out}/{name}.json", "w"), ensure_ascii=False, indent=1)
    print("ok", name, round(t, 2), "s", len(words), "words")

for j in sys.argv[1:]:
    run(j)
