import json, os, sys, subprocess
S = '/tmp/claude-0/-home-claude/844ebc5a-648f-5142-9a2f-1a04ed1a7ee7/scratchpad/'
OUT = S + 'dz/'
sys.path.insert(0, S + 'rw/render')
import render as R
R.WORK = OUT
tim = json.load(open(OUT + 'timing.json'))
TOTAL = tim[-1]['end'] + 8.0
A = S + 'glitch/assets/'
def sh(c): subprocess.run(c, check=True, capture_output=True)
# voice
sh(['ffmpeg', '-y', '-i', A + 'gv_vo1.mp3', '-i', A + 'gv_vo2.mp3', '-i', A + 'gv_vo3.mp3', '-filter_complex',
    '[0][1][2]concat=n=3:v=0:a=1,aresample=48000,apad,atrim=0:%.3f[o]' % TOTAL, '-map', '[o]', '-ac', '2', OUT + 'voice.wav'])
music = R.gen_music('dark', TOTAL)
chap = [s['start'] for s in tim if s['id'] in ('s03', 's05', 's07', 's10', 's12b', 's13', 's14', 's16b', 's17', 's18')]
ev = [{'t': 0.0, 'type': 'boom', 'volume': 1.1}, {'t': 131.4, 'type': 'boom', 'volume': 0.9},
      {'t': 242.4, 'type': 'riser', 'volume': 0.6}, {'t': 244.3, 'type': 'boom', 'volume': 0.8}]
ev += [{'t': max(0, t - 0.2), 'type': 'whoosh', 'volume': 0.55} for t in chap]
ev += [{'t': 107.1 + 10.0 * (0.12 + i * 0.22), 'type': 'zap', 'volume': 0.35} for i in range(3)]
sfx = R.gen_events(ev, TOTAL)
f = ('[1]volume=0.20,afade=t=out:st=%.2f:d=4[m];[m][0]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=400[md];'
     '[0][md][2]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[o]') % (TOTAL - 4)
sh(['ffmpeg', '-y', '-i', OUT + 'voice.wav', '-i', music, '-i', sfx, '-filter_complex', f, '-map', '[o]', '-c:a', 'pcm_s16le', OUT + 'mix.wav'])
print('ok', TOTAL)
