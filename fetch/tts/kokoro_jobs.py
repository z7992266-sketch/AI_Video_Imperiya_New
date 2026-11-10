"""Free TTS for OUJ (owner 10 Nov 2026): every fetch/tts/jobs/<id>.txt without fetch/out/tts/<id>.mp3
is spoken with Kokoro (Apache-2.0) voice af_heart (female, English) -> fetch/out/tts/<id>.mp3 (+ <id>.json word timings when available).
Optional first line '#voice=<name> speed=<x>' overrides voice/speed."""
import os, json, subprocess, glob
import numpy as np, soundfile as sf
from kokoro import KPipeline
os.makedirs('fetch/out/tts', exist_ok=True)
pipe = KPipeline(lang_code='a')
for txt in sorted(glob.glob('fetch/tts/jobs/*.txt')):
    jid = os.path.basename(txt)[:-4]
    out = f'fetch/out/tts/{jid}.mp3'
    if os.path.exists(out):
        continue
    lines = open(txt, encoding='utf-8').read().strip().splitlines()
    voice, speed = 'af_heart', 0.95
    if lines and lines[0].startswith('#'):
        for kv in lines[0][1:].split():
            k, _, v = kv.partition('=')
            if k == 'voice': voice = v
            if k == 'speed': speed = float(v)
        lines = lines[1:]
    text = '\n'.join(lines)
    chunks, words, t0 = [], [], 0.0
    for r in pipe(text, voice=voice, speed=speed):
        a = r.audio.numpy() if hasattr(r.audio, 'numpy') else np.asarray(r.audio)
        for tk in (getattr(r, 'tokens', None) or []):
            if getattr(tk, 'start_ts', None) is not None:
                words.append({'w': tk.text, 's': round(t0 + tk.start_ts, 3), 'e': round(t0 + (tk.end_ts or tk.start_ts), 3)})
        chunks.append(a); t0 += len(a) / 24000
    wav = f'/tmp/{jid}.wav'
    sf.write(wav, np.concatenate(chunks), 24000)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-af', 'loudnorm=I=-16', '-ar', '44100', '-b:a', '160k', out], check=True)
    json.dump({'voice': voice, 'duration': round(t0, 3), 'words': words}, open(f'fetch/out/tts/{jid}.json', 'w'))
    print('done', jid, round(t0, 1), 's')
