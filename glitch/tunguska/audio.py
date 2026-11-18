import json, os, sys, subprocess
sys.path.insert(0, '/home/claude/kit/render')
import render as R
OUT = '/home/claude/gv/out/'
R.WORK = OUT
tim = json.load(open('/home/claude/gv/timing.json')); T = {s['id']: s for s in tim}
shots = json.load(open(OUT + 'shots.json'))
TOTAL = tim[-1]['end'] + 8.0
A = '/home/claude/gv/assets/'
def sh(c): subprocess.run(c, check=True, capture_output=True)
sh(['ffmpeg', '-y', '-i', A + 'tg10_vo1.mp3', '-i', A + 'tg10_vo2.mp3', '-i', A + 'tg10_vo3.mp3', '-filter_complex',
    '[0][1][2]concat=n=3:v=0:a=1,aresample=48000,apad,atrim=0:%.3f[o]' % TOTAL, '-map', '[o]', '-ac', '2', OUT + 'voice.wav'])
music = R.gen_music('dark', TOTAL)
def first(seg, i=0): return [x for x in shots if x['seg'] == seg][i]
ev = [{'t': 0.0, 'type': 'boom', 'volume': 1.1}, {'t': 2.95, 'type': 'zap', 'volume': 0.5}]
loops = [first('s07')['start'], first('s12')['start']]
ev += [{'t': t, 'type': 'zap', 'volume': 0.45} for t in loops]
ab = first('s13'); tb = ab['start'] + 0.18 * (ab['end'] - ab['start'])
ev += [{'t': tb - 2.0, 'type': 'riser', 'volume': 0.4}, {'t': tb, 'type': 'boom', 'volume': 0.7}]
tw = T['s19']['start']
ev += [{'t': tw - 2.0, 'type': 'riser', 'volume': 0.5}, {'t': tw, 'type': 'boom', 'volume': 0.8}]
ev += [{'t': first('s09', 2)['start'], 'type': 'zap', 'volume': 0.35}]  # "there was none"
print('events', ev)
sfx = R.gen_events(ev, TOTAL)
f = ('[1]volume=0.17,afade=t=out:st=%.2f:d=5[m];[m][0]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=400[md];'
     '[0][md][2]amix=inputs=3:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[o]') % (TOTAL - 5)
sh(['ffmpeg', '-y', '-i', OUT + 'voice.wav', '-i', music, '-i', sfx, '-filter_complex', f, '-map', '[o]', '-c:a', 'pcm_s16le', OUT + 'mix.wav'])
print('ok', TOTAL)
