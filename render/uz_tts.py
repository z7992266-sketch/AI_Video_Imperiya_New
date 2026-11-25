"""Template "uz_tts": free Microsoft Edge neural TTS on GitHub Actions (e.g. Uzbek uz-UZ-SardorNeural).
Job: {"template":"uz_tts","voice":"uz-UZ-SardorNeural","rate":"+0%","gap":0.35,"segments":["line 1",...]}
Output: <out>.mp4 (black 1280x720 + voice), render/out/<name>_voice.mp3, render/out/<name>_segs.json
(segment start/end seconds + word timings). Last stdout line = JSON info."""
import json, os, subprocess, sys, asyncio
job_path, out_mp4 = sys.argv[1], sys.argv[2]
name = os.path.splitext(os.path.basename(job_path))[0]
job = json.load(open(job_path))
def sh(*a): subprocess.run(a, check=True)
try:
    sh(sys.executable, '-m', 'pip', 'install', '-q', 'edge-tts')
except Exception:
    sh(sys.executable, '-m', 'pip', 'install', '-q', '--break-system-packages', 'edge-tts')
import edge_tts
W = os.environ.get('RENDER_WORK', '/tmp/edge'); os.makedirs(W, exist_ok=True)
voice, rate, gap = job.get('voice', 'uz-UZ-SardorNeural'), job.get('rate', '+0%'), float(job.get('gap', 0.35))
pitch = job.get('pitch', '+0Hz')

async def one(i, text):
    p = os.path.join(W, 'seg%03d.mp3' % i); words = []
    for attempt in range(4):
        try:
            try:
                c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary='WordBoundary')
            except TypeError:
                c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            words = []
            with open(p, 'wb') as f:
                async for ch in c.stream():
                    if ch['type'] == 'audio': f.write(ch['data'])
                    elif ch['type'] == 'WordBoundary':
                        words.append({'w': ch['text'], 't0': ch['offset'] / 1e7, 't1': (ch['offset'] + ch['duration']) / 1e7})
            return p, words
        except Exception as e:
            print('retry', i, e, file=sys.stderr); await asyncio.sleep(3)
    raise RuntimeError('tts failed seg %d' % i)

def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', p]).decode().strip())

segs, files, t = [], [], 0.0
for i, text in enumerate(job['segments']):
    p, words = asyncio.run(one(i, text))
    w = os.path.join(W, 'seg%03d.wav' % i)
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', p, '-ar', '48000', '-ac', '1', w)
    d = dur(w)
    segs.append({'i': i, 'text': text, 's': round(t, 3), 'e': round(t + d, 3),
                 'words': [{'w': x['w'], 't0': round(t + x['t0'], 3), 't1': round(t + x['t1'], 3)} for x in words]})
    files.append(w); t += d
    if i < len(job['segments']) - 1:
        g = os.path.join(W, 'gap%03d.wav' % i)
        sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', str(gap), g)
        files.append(g); t += gap
lst = os.path.join(W, 'list.txt')
open(lst, 'w').write(''.join("file '%s'\n" % f for f in files))
os.makedirs('render/out', exist_ok=True)
voice_mp3 = 'render/out/%s_voice.mp3' % name
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c:a', 'libmp3lame', '-b:a', '160k', voice_mp3)
json.dump(segs, open('render/out/%s_segs.json' % name, 'w'), ensure_ascii=False, indent=0)
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=black:s=640x360:r=10', '-i', voice_mp3, '-shortest',
   '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac', out_mp4)
jpg = os.path.splitext(out_mp4)[0] + '.jpg'
sh('ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=black:s=640x360', '-frames:v', '1', jpg)
print(json.dumps({'duration': round(t, 2), 'segments': len(segs), 'voice': voice_mp3}))
