"""Template "kokoro_tts": free Kokoro TTS on GitHub Actions.
Job: {"template":"kokoro_tts","voice":"am_michael","speed":1.0,"gap":0.25,"segments":["line 1","line 2",...]}
Output: <out>.mp4 (black 1080x1920 + voice), render/out/<name>_voice.wav, render/out/<name>_segs.json
(segment start/end seconds). Last stdout line = JSON info."""
import json, os, subprocess, sys
job_path, out_mp4 = sys.argv[1], sys.argv[2]
name = os.path.splitext(os.path.basename(job_path))[0]
job = json.load(open(job_path))
def sh(*a): subprocess.run(a, check=True)
try:
    sh(sys.executable, '-m', 'pip', 'install', '-q', 'kokoro-onnx', 'soundfile')
except Exception:
    sh(sys.executable, '-m', 'pip', 'install', '-q', '--break-system-packages', 'kokoro-onnx', 'soundfile')
W = os.environ.get('RENDER_WORK', '/tmp/kok'); os.makedirs(W, exist_ok=True)
base = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
for f in ('kokoro-v1.0.onnx', 'voices-v1.0.bin'):
    p = os.path.join(W, f)
    if not os.path.exists(p): sh('curl', '-fsSL', '-o', p, base + f)
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro(os.path.join(W, 'kokoro-v1.0.onnx'), os.path.join(W, 'voices-v1.0.bin'))
voice, speed, gap = job.get('voice', 'am_michael'), float(job.get('speed', 1.0)), float(job.get('gap', 0.25))
parts, segs, t, sr = [], [], 0.0, 24000
for i, text in enumerate(job['segments']):
    s, sr = k.create(text, voice=voice, speed=speed, lang=job.get('lang', 'en-us'))
    s = np.asarray(s, dtype=np.float32)
    nz = np.where(np.abs(s) > 0.01)[0]
    if len(nz): s = s[max(0, nz[0] - 600): nz[-1] + 1200]
    d = len(s) / sr
    segs.append({'i': i, 'text': text, 's': round(t, 3), 'e': round(t + d, 3)})
    parts.append(s); t += d
    if i < len(job['segments']) - 1:
        parts.append(np.zeros(int(gap * sr), np.float32)); t += gap
audio = np.concatenate(parts)
os.makedirs('render/out', exist_ok=True)
wav = 'render/out/%s_voice.wav' % name
sf.write(wav, audio, sr)
json.dump({'voice': voice, 'speed': speed, 'sr': sr, 'duration': round(t, 3), 'segments': segs},
          open('render/out/%s_segs.json' % name, 'w'), indent=1)
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=1080x1920:r=30', '-i', wav,
   '-shortest', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', out_mp4)
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=1080x1920', '-frames:v', '1',
   os.path.splitext(out_mp4)[0] + '.jpg')
print(json.dumps({'duration': round(t, 3), 'segments': len(segs)}))
