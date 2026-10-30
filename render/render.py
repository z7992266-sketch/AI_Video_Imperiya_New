#!/usr/bin/env python3
"""Z7 Render — professional vertical video renderer (no watermark).

Usage: python3 render/render.py job.json out.mp4

Job JSON (all fields optional except scenes):
{
  "name": "demo",
  "width": 1080, "height": 1920, "fps": 30,
  "grade": "cinematic" | "clean" | "dark" | "none",
  "transition": "auto" | "fade" | "none",      # between scenes
  "scenes": [
    {"src": "https://.../clip.mp4", "type": "video", "dur": 3.5, "start": 0.4,
     "move": "in|out|left|right|up|down|none", "fit": "fill|blur"},
    {"src": "https://.../photo.jpg", "type": "image", "dur": 3, "move": "in"},
    {"type": "color", "color": "#0b0b10", "dur": 2}
  ],
  "hook": {"text": "SHE CALLED HERSELF", "dur": 2.6, "color": "#FFD54F"},
  "voice": {"src": "https://.../voice.mp3", "start": 0.3, "volume": 1.0},
  "music": {"src": "https://.../beat.mp3", "volume": 0.22, "duck": true},
  "native_audio": false,                         # keep the scene clips' own sound
  "captions": {"script": "full narration text", "lang": "uz",
               "words": [{"w": "Salom", "t0": 0.3, "t1": 0.7}],   # optional exact timing
               "style": "karaoke" | "plain" | "none", "pos": 0.66,
               "color": "#FFFFFF", "highlight": "#FFD54F", "size": 84, "max_words": 3},
  "badge": {"text": "Made by B2B SAS", "color": "#D4AF37", "pos": "top-left"},
  "endcard": {"image": "https://.../end.png", "dur": 3.5}
             or {"title": "...", "subtitle": "...", "small": "...", "dur": 3.5,
                 "bg": "#000000", "accent": "#D4AF37"},
  "fade_out": 0.6
}
"""
import json, math, os, re, subprocess, sys, hashlib, urllib.request, shutil, random

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, 'fonts')
FONT_MAIN = 'Inter Display Black'
FONT_SUB = 'Inter Display ExtraBold'
WORK = os.environ.get('RENDER_WORK', '/tmp/z7render')


def sh(cmd, quiet=True):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stderr.write('CMD FAILED: ' + ' '.join(cmd)[:3000] + '\n' + r.stderr[-4000:] + '\n')
        raise RuntimeError('ffmpeg failed')
    return r


def probe_dur(path):
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', path],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def has_audio(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index', '-of', 'csv=p=0', path],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return bool(r.stdout.strip())


def fetch(src):
    if not src:
        return None
    if os.path.exists(src):
        return src
    os.makedirs(os.path.join(WORK, 'dl'), exist_ok=True)
    ext = os.path.splitext(src.split('?')[0])[1][:6] or '.bin'
    p = os.path.join(WORK, 'dl', hashlib.md5(src.encode()).hexdigest() + ext)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36'
    if shutil.which('curl'):
        r = subprocess.run(['curl', '-L', '-sS', '--fail', '--retry', '3', '-A', ua, '-o', p, src])
        if r.returncode == 0 and os.path.getsize(p) > 1000:
            return p
    req = urllib.request.Request(src, headers={'User-Agent': ua})
    with urllib.request.urlopen(req, timeout=300) as r, open(p, 'wb') as f:
        shutil.copyfileobj(r, f)
    return p


def gen_sfx(cuts, total, hook):
    """Whoosh on every transition + low boom at the hook. Synthesised, copyright-free."""
    p = os.path.join(WORK, 'sfx.wav')
    parts, labels = [], []
    if hook:
        parts.append('sine=f=48:d=1.2,volume=1.6,afade=t=out:st=0.05:d=1.1,adelay=0|0[h]')
        parts.append('anoisesrc=color=brown:amplitude=0.8:d=0.35,lowpass=f=180,afade=t=out:st=0:d=0.35[h2]')
        labels += ['[h]', '[h2]']
    for i, t in enumerate(cuts):
        st = max(0, t - 0.18)
        ms = int(st * 1000)
        parts.append('anoisesrc=color=pink:amplitude=0.55:d=0.5,bandpass=f=1400:width_type=o:w=2,volume=9,'
                     'afade=t=in:st=0:d=0.22,afade=t=out:st=0.22:d=0.28,adelay=%d|%d[w%d]' % (ms, ms, i))
        labels.append('[w%d]' % i)
    if not labels:
        sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-t', '%.2f' % total, p])
        return p
    f = ';'.join(parts) + ';' + ''.join(labels) + 'amix=inputs=%d:normalize=0:duration=longest,apad,atrim=0:%.3f,aresample=48000[o]' % (len(labels), total)
    sh(['ffmpeg', '-y', '-filter_complex', f, '-map', '[o]', '-ac', '2', p])
    return p


SFX_LIB = {
    'ring': ("sine=f=440:d=1.6,volume=0.5[a1];sine=f=480:d=1.6,volume=0.5[a2];[a1][a2]amix=inputs=2:normalize=0,"
             "volume='if(lt(mod(t,0.4),0.2),1,0)':eval=frame,afade=t=out:st=1.3:d=0.3,highpass=f=300,lowpass=f=3400"),
    'zap': ("anoisesrc=color=white:amplitude=0.9:d=0.35,acrusher=bits=4:mode=log:aa=1,bandpass=f=2500:width_type=o:w=3,"
            "volume='if(lt(mod(t,0.07),0.035),1.4,0.2)':eval=frame,afade=t=out:st=0.2:d=0.15"),
    'heartbeat': ("sine=f=55:d=0.9,volume='if(lt(t,0.12),1.8,if(between(t,0.28,0.4),1.4,0))':eval=frame,lowpass=f=150,"
                  "afade=t=out:st=0.5:d=0.4"),
    'tick': "sine=f=2400:d=0.05,afade=t=out:st=0:d=0.05,volume=0.8",
    'boom': ("sine=f=40:d=1.6,volume=2.2,afade=t=out:st=0.1:d=1.5[b1];anoisesrc=color=brown:amplitude=0.9:d=0.5,lowpass=f=200,"
             "afade=t=out:st=0:d=0.5[b2];[b1][b2]amix=inputs=2:normalize=0"),
    'rewind': ("anoisesrc=color=pink:amplitude=0.6:d=0.9,bandpass=f=1800:width_type=o:w=2,volume=6,vibrato=f=18:d=0.9,"
               "afade=t=in:st=0:d=0.2,afade=t=out:st=0.6:d=0.3[r1];sine=f=900:d=0.9,vibrato=f=24:d=1,volume=0.25,"
               "afade=t=out:st=0.3:d=0.6[r2];[r1][r2]amix=inputs=2:normalize=0"),
    'whoosh': ("anoisesrc=color=pink:amplitude=0.55:d=0.5,bandpass=f=1400:width_type=o:w=2,volume=9,"
               "afade=t=in:st=0:d=0.22,afade=t=out:st=0.22:d=0.28"),
    'riser': ("anoisesrc=color=white:amplitude=0.4:d=2,highpass=f=800,volume='t/2*2.5':eval=frame,afade=t=out:st=1.9:d=0.1"),
}


def gen_events(events, total):
    """[{"t": 0.0, "type": "ring"|"zap"|"heartbeat"|"tick"|"boom"|"rewind"|"whoosh"|"riser", "volume": 1}] -> wav"""
    p = os.path.join(WORK, 'events.wav')
    parts, labels = [], []
    for i, ev in enumerate(events):
        f = SFX_LIB.get(ev.get('type'))
        if not f:
            continue
        ms = int(max(0, float(ev.get('t', 0))) * 1000)
        parts.append('%s,volume=%.2f,aformat=channel_layouts=stereo,adelay=%d|%d[e%d]' % (f, float(ev.get('volume', 1)), ms, ms, i))
        labels.append('[e%d]' % i)
    if not labels:
        return None
    f = ';'.join(parts) + ';' + ''.join(labels) + 'amix=inputs=%d:normalize=0:duration=longest,apad,atrim=0:%.3f,aresample=48000[o]' % (len(labels), total)
    sh(['ffmpeg', '-y', '-filter_complex', f, '-map', '[o]', '-ac', '2', p])
    return p


def gen_music(kind, dur):
    """Copyright-free generated ambience: dark (drone + wind), tension (pulse), calm (pad)."""
    p = os.path.join(WORK, 'music_%s.wav' % kind)
    d = '%.2f' % (dur + 1)
    if kind == 'tension':
        f = ("anoisesrc=color=brown:amplitude=0.25:d={d},lowpass=f=300[n];"
             "sine=f=55:d={d},volume=0.6,tremolo=f=1.6:d=0.9[a];sine=f=110:d={d},volume=0.25,tremolo=f=3.2:d=0.7[b];"
             "sine=f=164.8:d={d},volume=0.12[c];[n][a][b][c]amix=inputs=4:normalize=0,aecho=0.8:0.7:180:0.35,highpass=f=35")
    elif kind == 'calm':
        f = ("sine=f=220:d={d},volume=0.18[a];sine=f=277.2:d={d},volume=0.12[b];sine=f=329.6:d={d},volume=0.12[c];"
             "anoisesrc=color=pink:amplitude=0.04:d={d},lowpass=f=1200[n];[a][b][c][n]amix=inputs=4:normalize=0,tremolo=f=0.2:d=0.4,aecho=0.8:0.8:400:0.4")
    else:  # dark
        f = ("anoisesrc=color=brown:amplitude=0.5:d={d},lowpass=f=500,tremolo=f=0.12:d=0.7[w];"
             "sine=f=41.2:d={d},volume=0.7[a];sine=f=61.7:d={d},volume=0.35,tremolo=f=0.3:d=0.5[b];"
             "sine=f=82.4:d={d},volume=0.15[c];[w][a][b][c]amix=inputs=4:normalize=0,aecho=0.8:0.6:250|500:0.4|0.25,highpass=f=30")
    sh(['ffmpeg', '-y', '-filter_complex', f.format(d=d) + ',afade=t=in:d=1.5,aresample=48000[o]', '-map', '[o]', '-t', d, p])
    return p


def hex2ass(h, alpha=0):
    h = h.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    r, g, b = h[0:2], h[2:4], h[4:6]
    return '&H%02X%s%s%s' % (alpha, b.upper(), g.upper(), r.upper())


def grade_filter(g):
    if g == 'none':
        return 'null'
    if g == 'clean':
        return 'eq=contrast=1.04:saturation=1.08,unsharp=5:5:0.4'
    if g == 'dark':
        return 'eq=contrast=1.12:brightness=-0.03:saturation=0.95,curves=preset=darker,vignette=PI/4.5,unsharp=5:5:0.5'
    # cinematic teal/orange-ish
    return ('eq=contrast=1.08:saturation=1.12:brightness=-0.01,'
            'colorbalance=rs=0.03:gs=-0.01:bs=-0.04:rh=0.04:bh=-0.03,'
            'vignette=PI/5,unsharp=5:5:0.5')


def fx_filter(sc, W, H):
    """Per-scene effects: flash, glitch, shake, punch (all in the first fraction of a second), grain."""
    fx = sc.get('fx') or []
    if isinstance(fx, str):
        fx = [fx]
    out = []
    if 'punch' in fx:
        out.append("zoompan=z='if(lt(on,6),1.16-0.16*on/6,1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d" % (W, H))
    if 'shake' in fx:
        out.append("pad=%d:%d:30:30,crop=%d:%d:x='30+18*sin(t*97)*lt(t,0.45)':y='30+18*cos(t*83)*lt(t,0.45)'" % (W + 60, H + 60, W, H))
    if 'glitch' in fx:
        out.append("rgbashift=rh=-14:bh=14:gv=6:enable='lt(mod(t,0.9),0.32)*lt(t,0.9)',noise=alls=45:allf=t:enable='lt(t,0.3)'")
    if 'glitch_end' in fx:
        out.append("rgbashift=rh=-16:bh=16:enable='gt(t,%f)'" % (float(sc.get('dur', 3)) - 0.3))
    if 'flash' in fx:
        out.append('fade=t=in:st=0:d=0.18:color=white')
    if 'grain' in fx or sc.get('grain'):
        out.append('noise=alls=10:allf=t')
    return (',' + ','.join(out)) if out else ''


def scene_clip(i, sc, W, H, FPS, grade, extra):
    """Render one scene to a normalized silent-or-native-audio mp4 of length dur+extra."""
    dur = float(sc.get('dur', 3)) + extra
    out = os.path.join(WORK, 'seg_%03d.mp4' % i)
    typ = sc.get('type') or ('image' if re.search(r'\.(png|jpe?g|webp)(\?|$)', str(sc.get('src', '')), re.I) else 'video')
    move = sc.get('move', 'auto')
    if move == 'auto':
        move = ['in', 'right', 'out', 'left', 'up'][i % 5] if typ == 'image' else ['in', 'none', 'right', 'in', 'left'][i % 5]
    frames = int(round(dur * FPS))
    g = grade_filter(sc.get('grade', grade))
    fit = sc.get('fit', 'fill')
    try:
        if typ == 'color':
            raise ValueError('color')
        src = fetch(sc['src'])
        if typ == 'image':
            # Ken Burns on a 2x canvas for smooth sub-pixel motion
            z0, z1 = (1.0, 1.14) if move in ('in', 'left', 'right', 'up', 'down', 'none') else (1.14, 1.0)
            if move == 'none':
                z1 = 1.04
            px = {'left': '(iw-iw/zoom)*(1-on/%d)' % frames, 'right': '(iw-iw/zoom)*(on/%d)' % frames}.get(move, 'iw/2-(iw/zoom/2)')
            py = {'up': '(ih-ih/zoom)*(1-on/%d)' % frames, 'down': '(ih-ih/zoom)*(on/%d)' % frames}.get(move, 'ih/2-(ih/zoom/2)')
            zexpr = '%f+(%f)*on/%d' % (z0, z1 - z0, frames)
            if fit == 'blur':
                base = ('[0:v]split[a][b];[a]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,boxblur=30:3,eq=brightness=-0.08[bg];'
                        '[b]scale=%d:%d:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,scale=%d:%d' % (W * 2, H * 2, W * 2, H * 2, W * 2, H * 2, W * 2, H * 2))
            else:
                base = '[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d' % (W * 2, H * 2, W * 2, H * 2)
            vf = (base + ",zoompan=z='%s':x='%s':y='%s':d=%d:s=%dx%d:fps=%d,%s%s,format=yuv420p[v]" % (zexpr, px, py, frames, W, H, FPS, g, fx_filter(sc, W, H)))
            sh(['ffmpeg', '-y', '-loop', '1', '-i', src, '-filter_complex', vf, '-map', '[v]', '-t', '%.3f' % dur,
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-r', str(FPS), '-an', out])
            return out, False
        # video
        start = float(sc.get('start', 0))
        sdur = probe_dur(src)
        speed = 1.0
        if sdur and sdur - start < dur:
            if sdur - start > dur * 0.6:
                speed = (sdur - start) / dur  # gentle slow-down to fit
            else:
                start = 0
        nfr = max(1, int(round(dur * FPS)))
        if move in ('in', 'out'):
            z = "1+0.10*on/%d" % nfr if move == 'in' else "1.10-0.10*on/%d" % nfr
            cw, ch = W * 2, H * 2
            crop = ("crop=%d:%d,zoompan=z='%s':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=%dx%d:fps=%d"
                    % (cw, ch, z, W, H, FPS))
        elif move in ('left', 'right'):
            cw, ch = int(W * 1.12) // 2 * 2, int(H * 1.12) // 2 * 2
            sgn = '' if move == 'right' else '1-'
            crop = "crop=%d:%d:x='(iw-ow)*(%st/%f)':y='(ih-oh)/2'" % (W, H, sgn, dur)
        else:
            cw, ch = W, H
            crop = 'crop=%d:%d' % (W, H)
        pts = 'setpts=%f*PTS,' % (1.0 / speed) if abs(speed - 1) > 0.02 else ''
        if fit == 'blur':
            vf = ('[0:v]%sfps=%d,split[a][b];[a]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,boxblur=30:3,eq=brightness=-0.08[bg];'
                  '[b]scale=%d:%d:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,%s,scale=%d:%d,setsar=1,%s,format=yuv420p[v]'
                  % (pts, FPS, W, H, W, H, W, H, 'null', W, H, g))
        else:
            vf = ('[0:v]%s%sfps=%d,scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,%s,scale=%d:%d,setsar=1,%s%s,format=yuv420p[v]'
                  % ('reverse,' if sc.get('reverse') else '', pts, FPS, cw, ch, cw, ch, crop, W, H, g, fx_filter(sc, W, H)))
        cmd = ['ffmpeg', '-y', '-ss', '%.3f' % start] + (['-t', '%.3f' % (dur * speed + 0.2)] if sc.get('reverse') else []) + ['-i', src, '-filter_complex', vf, '-map', '[v]']
        native = bool(sc.get('native_audio')) and has_audio(src)
        if native:
            atempo = 'atempo=%f,' % speed if abs(speed - 1) > 0.02 and 0.5 <= speed <= 2 else ''
            cmd += ['-map', '0:a:0', '-af', atempo + 'aresample=48000', '-c:a', 'aac', '-b:a', '192k']
        else:
            cmd += ['-an']
        cmd += ['-t', '%.3f' % dur, '-c:v', 'libx264', '-preset', 'medium', '-crf', '16', '-r', str(FPS), out]
        sh(cmd)
        return out, native
    except Exception as e:
        if str(e) != 'color':
            sys.stderr.write('scene %d fallback (%s)\n' % (i, e))
        col = sc.get('color', '#0b0b12').lstrip('#')
        sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=0x%s:s=%dx%d:r=%d:d=%.3f' % (col, W, H, FPS, dur),
            '-f', 'lavfi', '-i', 'color=c=0x%s:s=%dx%d:r=%d:d=%.3f' % ('1a1030', W, H, FPS, dur),
            '-filter_complex', '[0:v][1:v]blend=all_expr=A*(1-Y/H)+B*(Y/H),format=yuv420p[v]', '-map', '[v]',
            '-c:v', 'libx264', '-crf', '16', '-an', out])
        return out, False


def endcard_clip(i, ec, W, H, FPS, ass_events):
    dur = float(ec.get('dur', 3.5))
    if ec.get('image'):
        return scene_clip(i, {'src': ec['image'], 'type': 'image', 'dur': dur, 'move': 'in', 'grade': 'none'}, W, H, FPS, 'none', 0)
    out = os.path.join(WORK, 'seg_%03d.mp4' % i)
    bg = ec.get('bg', '#07070a').lstrip('#')
    acc = ec.get('accent', '#D4AF37').lstrip('#')
    vf = ('[0:v]drawbox=x=90:y=%d:w=%d:h=6:color=0x%s@1:t=fill,drawbox=x=90:y=%d:w=%d:h=6:color=0x%s@1:t=fill,vignette=PI/4,format=yuv420p[v]'
          % (int(H * 0.30), W - 180, acc, int(H * 0.70), W - 180, acc))
    sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=0x%s:s=%dx%d:r=%d:d=%.3f' % (bg, W, H, FPS, dur),
        '-filter_complex', vf, '-map', '[v]', '-c:v', 'libx264', '-crf', '16', '-an', out])
    return out, False


def speech_spans(voice, offset, total):
    """Find speech segments in the voice track using silencedetect."""
    r = subprocess.run(['ffmpeg', '-i', voice, '-af', 'silencedetect=noise=-32dB:d=0.22', '-f', 'null', '-'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    vd = probe_dur(voice)
    sil = []
    st = None
    for line in r.stderr.splitlines():
        m = re.search(r'silence_start: ([\d.]+)', line)
        if m:
            st = float(m.group(1))
        m = re.search(r'silence_end: ([\d.]+)', line)
        if m and st is not None:
            sil.append((st, float(m.group(1))))
            st = None
    if st is not None:
        sil.append((st, vd))
    spans, cur = [], 0.0
    for a, b in sil:
        if a - cur > 0.12:
            spans.append((cur + offset, a + offset))
        cur = b
    if vd - cur > 0.12:
        spans.append((cur + offset, vd + offset))
    return spans or [(offset, offset + vd)]


def align_words(words, spans):
    weights = [len(w) + 2 for w in words]
    total_w = sum(weights)
    total_t = sum(b - a for a, b in spans)
    out, si = [], 0
    t = spans[0][0]
    for w, wt in zip(words, weights):
        d = total_t * wt / total_w
        if si < len(spans) and t >= spans[si][1] - 0.02 and si + 1 < len(spans):
            si += 1
            t = spans[si][0]
        out.append({'w': w, 't0': t, 't1': t + d})
        t += d
    return out


def ass_time(t):
    t = max(0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return '%d:%02d:%05.2f' % (h, m, s)


def esc(s):
    s = ''.join(ch for ch in s if ord(ch) <= 0xFFFF and not (0xFE00 <= ord(ch) <= 0xFE0F) and ch not in '\u200d')
    s = s.replace('\u261f', '').strip()
    return s.replace('\\', '').replace('{', '(').replace('}', ')').replace('\n', '\\N')


def build_ass(job, W, H, total, word_times):
    cap = job.get('captions') or {}
    size = int(cap.get('size', 84))
    col = hex2ass(cap.get('color', '#FFFFFF'))
    hi = hex2ass(cap.get('highlight', '#FFD54F'))
    hook = job.get('hook') or {}
    badge = job.get('badge') or {}
    ec = job.get('endcard') or {}
    L = ['[Script Info]', 'ScriptType: v4.00+', 'PlayResX: %d' % W, 'PlayResY: %d' % H, 'WrapStyle: 0', 'ScaledBorderAndShadow: yes', '',
         '[V4+ Styles]',
         'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
         'Style: Cap,%s,%d,%s,%s,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,7,3,5,60,60,0,1' % (FONT_MAIN, size, col, hi),
         'Style: Hook,%s,%d,%s,%s,&H00000000,&HA0000000,0,0,0,0,100,100,1,0,1,9,4,5,70,70,0,1' % (FONT_MAIN, int(hook.get('size', 112)), hex2ass(hook.get('color', '#FFFFFF')), hi),
         'Style: Badge,%s,44,%s,%s,&H00000000,&H64000000,0,0,0,0,100,100,1,0,1,3,1,7,40,40,60,1' % (FONT_SUB, hex2ass(badge.get('color', '#D4AF37')), hi),
         'Style: EndT,%s,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,80,80,0,1' % FONT_MAIN,
         'Style: EndS,%s,60,%s,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,80,80,0,1' % (FONT_SUB, hex2ass(ec.get('accent', '#D4AF37'))),
         'Style: EndM,%s,38,&H00C8C8C8,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,80,80,0,1' % FONT_SUB,
         '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text']
    cy = int(H * float(cap.get('pos', 0.66)))
    hook_end = 0.0
    if hook.get('text'):
        hook_end = float(hook.get('dur', 2.6))
        hy = int(H * float(hook.get('pos', 0.24)))
        txt = esc(hook['text'].upper() if hook.get('upper', True) else hook['text'])
        L.append('Dialogue: 2,%s,%s,Hook,,0,0,0,,{\\pos(%d,%d)\\fscx40\\fscy40\\t(0,180,\\fscx112\\fscy112)\\t(180,300,\\fscx100\\fscy100)\\fad(0,250)}%s'
                 % (ass_time(0.02), ass_time(hook_end), W // 2, hy, txt))
    if word_times and cap.get('style', 'karaoke') != 'none':
        maxw = int(cap.get('max_words', 3))
        groups, g = [], []
        for wt in word_times:
            g.append(wt)
            if len(g) >= maxw or sum(len(x['w']) for x in g) > 16 or re.search(r'[.!?,:;]$', wt['w']):
                groups.append(g); g = []
        if g:
            groups.append(g)
        for gi, grp in enumerate(groups):
            g_end = grp[-1]['t1'] + 0.08
            if gi + 1 < len(groups):
                g_end = min(g_end + 0.25, groups[gi + 1][0]['t0'])
            for wi, wt in enumerate(grp):
                parts = []
                for wj, w2 in enumerate(grp):
                    word = esc(w2['w'].upper() if cap.get('upper', True) else w2['w'])
                    if cap.get('style', 'karaoke') == 'karaoke' and wj == wi:
                        parts.append('{\\c%s\\fscx108\\fscy108}%s{\\c%s\\fscx100\\fscy100}' % (hi, word, col))
                    else:
                        parts.append(word)
                t0 = wt['t0']
                t1 = grp[wi + 1]['t0'] if wi + 1 < len(grp) else g_end
                pop = '\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)' if wi == 0 else ''
                L.append('Dialogue: 1,%s,%s,Cap,,0,0,0,,{\\pos(%d,%d)%s}%s' % (ass_time(t0), ass_time(t1), W // 2, cy, pop, ' '.join(parts)))
    for tx in job.get('texts') or []:
        st = 'Hook' if tx.get('style', 'hook') == 'hook' else 'Cap'
        size = int(tx.get('size', 96))
        colr = hex2ass(tx.get('color', '#FFFFFF'))
        y = int(H * float(tx.get('pos', 0.3)))
        anim = '\\fscx60\\fscy60\\t(0,140,\\fscx108\\fscy108)\\t(140,240,\\fscx100\\fscy100)' if tx.get('pop', True) else ''
        L.append('Dialogue: 2,%s,%s,%s,,0,0,0,,{\\pos(%d,%d)\\fs%d\\c%s%s\\fad(0,180)}%s' % (
            ass_time(float(tx['t0'])), ass_time(float(tx['t1'])), st, W // 2, y, size, colr, anim, esc(tx['text'])))
    if badge.get('text'):
        end_at = total - (float(ec.get('dur', 3.5)) if ec else 0)
        pos = badge.get('pos', 'top-left')
        x, y, an = (44, 150, 7) if pos == 'top-left' else (W - 44, 150, 9)
        L.append('Dialogue: 3,%s,%s,Badge,,0,0,0,,{\\an%d\\pos(%d,%d)\\fad(300,200)}%s' % (ass_time(0.3), ass_time(end_at), an, x, y, esc(badge['text'])))
    if ec and not ec.get('image'):
        t0 = total - float(ec.get('dur', 3.5))
        if ec.get('title'):
            L.append('Dialogue: 4,%s,%s,EndT,,0,0,0,,{\\pos(%d,%d)\\fad(250,0)\\fscx80\\fscy80\\t(0,220,\\fscx100\\fscy100)}%s' % (ass_time(t0 + 0.05), ass_time(total), W // 2, int(H * 0.42), esc(ec['title'])))
        if ec.get('subtitle'):
            L.append('Dialogue: 4,%s,%s,EndS,,0,0,0,,{\\pos(%d,%d)\\fad(350,0)}%s' % (ass_time(t0 + 0.35), ass_time(total), W // 2, int(H * 0.56), esc(ec['subtitle'])))
        if ec.get('small'):
            L.append('Dialogue: 4,%s,%s,EndM,,0,0,0,,{\\pos(%d,%d)\\fad(450,0)}%s' % (ass_time(t0 + 0.6), ass_time(total), W // 2, int(H * 0.66), esc(ec['small'])))
    return '\n'.join(L) + '\n'


TRANS = ['fade', 'smoothleft', 'circleopen', 'slideup', 'fadeblack', 'smoothright', 'zoomin', 'radial']


def main(job_path, out_path):
    job = json.load(open(job_path))
    os.makedirs(WORK, exist_ok=True)
    W, H, FPS = int(job.get('width', 1080)), int(job.get('height', 1920)), int(job.get('fps', 30))
    grade = job.get('grade', 'cinematic')
    tmode = job.get('transition', 'auto')
    TD = 0.0 if tmode == 'none' else float(job.get('transition_dur', 0.35))
    scenes = list(job['scenes'])
    ec = job.get('endcard')

    # voice-driven duration: stretch last content scene so narration fits before the end card
    vpath = None
    vstart = 0.0
    if job.get('voice', {}).get('src'):
        vpath = fetch(job['voice']['src'])
        vstart = float(job['voice'].get('start', 0.3))
        need = vstart + probe_dur(vpath) + 0.35
        have = sum(float(s.get('dur', 3)) for s in scenes) - TD * (len(scenes) - 1)
        if need > have:
            scenes[-1] = dict(scenes[-1], dur=float(scenes[-1].get('dur', 3)) + need - have)

    segs, natives = [], []
    n_all = len(scenes) + (1 if ec else 0)
    for i, sc in enumerate(scenes):
        extra = TD if i < n_all - 1 else 0
        p, nat = scene_clip(i, sc, W, H, FPS, grade, extra)
        segs.append((p, float(sc.get('dur', 3)) + extra)); natives.append(nat)
    if ec:
        p, nat = endcard_clip(len(scenes), ec, W, H, FPS, None)
        segs.append((p, float(ec.get('dur', 3.5)))); natives.append(False)

    # concat with xfade
    inputs = []
    for p, _ in segs:
        inputs += ['-i', p]
    fc, last, offset = [], '[0:v]', 0.0
    total = segs[0][1]
    cut_times = []
    for k in range(1, len(segs)):
        offset = total - TD
        tr = ('fade' if tmode in ('fade', 'auto') and k == len(segs) - 1 and ec else
              (TRANS[k % len(TRANS)] if tmode == 'auto' else 'fade'))
        if TD > 0:
            fc.append('%s[%d:v]xfade=transition=%s:duration=%.3f:offset=%.3f[x%d]' % (last, k, tr, TD, offset, k))
        else:
            fc.append('%s[%d:v]concat=n=2:v=1:a=0[x%d]' % (last, k, k))
        last = '[x%d]' % k
        cut_times.append(offset if TD > 0 else total)
        total = offset + segs[k][1] if TD > 0 else total + segs[k][1]

    # captions
    cap = job.get('captions') or {}
    word_times = cap.get('words')
    if not word_times and cap.get('script'):
        words = cap['script'].split()
        spans = speech_spans(vpath, vstart, total) if vpath else [(0.4, total - (float(ec.get('dur', 3.5)) if ec else 0) - 0.3)]
        word_times = align_words(words, spans)
    ass = os.path.join(WORK, 'subs.ass')
    open(ass, 'w', encoding='utf-8').write(build_ass(job, W, H, total, word_times))
    fo = float(job.get('fade_out', 0.5))
    fi = float(job.get('fade_in', 0 if (job.get('hook') or {}).get('text') else 0.2))
    fin = 'fade=t=in:st=0:d=%.3f,' % fi if fi > 0 else ''
    fout = 'fade=t=out:st=%.3f:d=%.3f,' % (max(0, total - fo), fo) if fo > 0 else ''
    fc.append("%sass='%s':fontsdir='%s',%s%sformat=yuv420p[vout]"
              % (last, ass.replace(':', '\\:'), FONTS, fin, fout))

    # audio
    a_inputs, a_parts, n = [], [], len(segs)
    mix = []
    if job.get('native_audio') and any(natives):
        # concat native audio with crossfades (silence for scenes without audio)
        for k, (p, d) in enumerate(segs):
            if natives[k]:
                a_parts.append('[%d:a]aresample=48000,apad=whole_dur=%.3f[na%d]' % (k, d, k))
            else:
                a_parts.append('anullsrc=r=48000:cl=stereo:d=%.3f[na%d]' % (d, k))
        prev = '[na0]'
        for k in range(1, n):
            if TD > 0:
                a_parts.append('%s[na%d]acrossfade=d=%.3f[ac%d]' % (prev, k, TD, k))
            else:
                a_parts.append('%s[na%d]concat=n=2:v=0:a=1[ac%d]' % (prev, k, k))
            prev = '[ac%d]' % k
        a_parts.append('%svolume=%.2f[nat]' % (prev, float(job.get('native_volume', 1.0))))
        mix.append('[nat]')
    idx = n
    if vpath:
        a_inputs += ['-i', vpath]
        vol = float(job['voice'].get('volume', 1.0))
        a_parts.append('[%d:a]aresample=48000,adelay=%d|%d,volume=%.2f,highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,apad[voice]'
                       % (idx, int(vstart * 1000), int(vstart * 1000), vol))
        idx += 1
    if job.get('music', {}).get('src') or job.get('music', {}).get('gen'):
        try:
            mpath = gen_music(job['music']['gen'], total) if job['music'].get('gen') else fetch(job['music']['src'])
            a_inputs += ['-stream_loop', '-1', '-i', mpath]
            mv = float(job['music'].get('volume', 0.22))
            a_parts.append('[%d:a]aresample=48000,volume=%.3f,afade=t=in:st=0:d=0.6[mus]' % (idx, mv))
            idx += 1
            if vpath and job['music'].get('duck', True):
                a_parts.append('[voice]asplit=2[voice][vsc]')
                a_parts.append('[mus][vsc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350:makeup=1[musd]')
                mix.append('[musd]')
            else:
                mix.append('[mus]')
        except Exception as e:
            sys.stderr.write('music skipped: %s\n' % e)
    for vi, xv in enumerate(job.get('voices') or []):
        try:
            xp = fetch(xv['src'])
        except Exception as e:
            sys.stderr.write('extra voice skipped: %s\n' % e)
            continue
        a_inputs += ['-i', xp]
        ms = int(float(xv.get('start', 0)) * 1000)
        fxs = {'phone': 'highpass=f=350,lowpass=f=3200,acrusher=bits=10:mix=0.25,aecho=0.8:0.5:60:0.3,',
               'echo': 'aecho=0.8:0.75:320|640:0.5|0.3,',
               'whisper': 'highpass=f=150,aecho=0.6:0.6:120:0.25,'}.get(xv.get('fx', ''), '')
        a_parts.append('[%d:a]aresample=48000,%svolume=%.2f,adelay=%d|%d,apad[xv%d]' % (idx, fxs, float(xv.get('volume', 1.0)), ms, ms, vi))
        mix.append('[xv%d]' % vi)
        idx += 1
    if job.get('sfx_events'):
        ep = gen_events(job['sfx_events'], total)
        if ep:
            a_inputs += ['-i', ep]
            a_parts.append('[%d:a]aresample=48000,volume=%.2f[evs]' % (idx, float(job.get('sfx_events_volume', 0.9))))
            mix.append('[evs]')
            idx += 1
    if job.get('sfx', True) and (vpath or job.get('music')):
        sfx = gen_sfx(cut_times, total, bool((job.get('hook') or {}).get('text')))
        a_inputs += ['-i', sfx]
        a_parts.append('[%d:a]aresample=48000,volume=%.2f[sfx]' % (idx, float(job.get('sfx_volume', 0.55))))
        idx += 1
        mix.append('[sfx]')
    if vpath:
        mix.append('[voice]')
    if mix:
        a_parts.append('%samix=inputs=%d:duration=longest:normalize=0,atrim=0:%.3f,afade=t=out:st=%.3f:d=%.3f,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]'
                       % (''.join(mix), len(mix), total, max(0, total - fo - 0.2), fo + 0.2))
    filt = ';'.join(fc + a_parts)
    cmd = ['ffmpeg', '-y'] + inputs + a_inputs + ['-filter_complex', filt, '-map', '[vout]']
    if mix:
        cmd += ['-map', '[aout]', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000']
    cmd += ['-t', '%.3f' % total, '-c:v', 'libx264', '-preset', job.get('preset', 'slow'), '-crf', str(job.get('crf', 18)),
            '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-r', str(FPS), '-movflags', '+faststart', out_path]
    sh(cmd)
    thumb = os.path.splitext(out_path)[0] + '.jpg'
    subprocess.run(['ffmpeg', '-y', '-ss', '%.2f' % min(1.2, total / 2), '-i', out_path, '-frames:v', '1', '-q:v', '2', thumb],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = {'name': job.get('name', ''), 'duration': round(total, 2), 'width': W, 'height': H, 'fps': FPS,
            'size_mb': round(os.path.getsize(out_path) / 1e6, 2), 'words': len(word_times or [])}
    print(json.dumps(info))
    return info


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
