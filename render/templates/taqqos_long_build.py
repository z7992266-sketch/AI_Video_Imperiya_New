"""Taqqos long 25 Nov 2026 — Navbahor finalda! 1920x1080 30fps documentary renderer (own graphics + CC photos).
Usage: python3 build.py timeline            -> writes timeline.json + final narration wav
       python3 build.py render A B out.mp4  -> renders frames [A,B) seconds (video only)
       python3 build.py still t1,t2,...     -> writes prev_<t>.jpg"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = os.path.dirname(os.path.abspath(__file__)) + '/'
A = S + 'a/'
W, H, FPS = 1920, 1080, 30
F = '/usr/share/fonts/opentype/inter/'
BLK = F + 'InterDisplay-Black.otf'; XB = F + 'InterDisplay-ExtraBold.otf'; BD = F + 'Inter-Bold.otf'; SB = F + 'Inter-SemiBold.otf'; MD = F + 'Inter-Medium.otf'
BG = (9, 13, 26); BG2 = (18, 26, 48); YEL = (255, 204, 0); WH = (245, 247, 252); GR = (150, 160, 180)
TEAM = {'NAV': ('NAVBAHOR', (34, 168, 92)), 'LOK': ('LOKOMOTIV', (214, 52, 64)), 'OKMK': ('OKMK', (232, 128, 30)),
        'AND': ('ANDIJON', (52, 120, 220)), 'NAS': ('NASAF', (40, 170, 200)), 'GAZ': ("G'AZALKENT", (140, 90, 200)),
        'NEF': ('NEFTCHI', (230, 190, 40)), 'PAX': ('PAXTAKOR', (60, 140, 90)), 'BUN': ('BUNYODKOR', (200, 160, 60))}

_fc = {}
def font(p, s):
    k = (p, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, int(s))
    return _fc[k]

def cl(x, a=0, b=1): return max(a, min(b, x))
def ease(x): x = cl(x); return 0.5 - 0.5 * math.cos(math.pi * x)
def eout(x): x = cl(x); return 1 - (1 - x) ** 3
def back(x):
    x = cl(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def ramp(t, t0, d=0.5): return cl((t - t0) / d)

# ---------- credits ----------
CRED = {}
for e in json.load(open(S + 'credits.json')):
    a = e['artist'].split('\n')[0].strip()
    if len(a) > 40: a = a[:40]
    CRED[e['k']] = '%s / %s / Wikimedia Commons' % (a or 'Wikimedia', e['license'])

_ic = {}
def img(k):
    if k not in _ic: _ic[k] = Image.open(A + 'lg_%s.jpg' % k).convert('RGB')
    return _ic[k]

def kb(k, p, move='in', amt=0.12, focus=(0.5, 0.5)):
    im = img(k); iw, ih = im.size
    base = min(iw / W, ih / H); e = ease(p) * 0.4 + p * 0.6
    if move == 'in': z0, z1, dx, dy = 1.0, 1 + amt, 0, 0
    elif move == 'out': z0, z1, dx, dy = 1 + amt, 1.0, 0, 0
    elif move == 'right': z0 = z1 = 1 + amt; dx, dy = 1, 0
    elif move == 'left': z0 = z1 = 1 + amt; dx, dy = -1, 0
    else: z0 = z1 = 1 + amt; dx, dy = 0, -1
    z = z0 + (z1 - z0) * e; cw, ch = W * base / z, H * base / z
    cx = focus[0] * iw + dx * (e - 0.5) * (iw - cw) * 0.9; cy = focus[1] * ih + dy * (e - 0.5) * (ih - ch) * 0.9
    cx = min(max(cx, cw / 2), iw - cw / 2); cy = min(max(cy, ch / 2), ih - ch / 2)
    return im.transform((W, H), Image.EXTENT, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), Image.BILINEAR)

def darken(im, a): return Image.blend(im, Image.new('RGB', (W, H), (0, 0, 0)), a)

# background gradient + pitch graphic
_bgc = {}
def grad_bg(kind='dark'):
    if kind in _bgc: return _bgc[kind].copy()
    y = np.linspace(0, 1, H)[:, None]; x = np.linspace(0, 1, W)[None, :]
    if kind == 'pitch':
        base = np.zeros((H, W, 3), np.float32)
        stripes = ((np.floor(x * 12) % 2) * 0.06 + 0.94)
        g = np.stack([18 + 0 * y * x, 92 - 30 * y + 0 * x, 52 - 10 * y + 0 * x], -1) * stripes[..., None]
        vig = 1 - 0.55 * (((x - 0.5) * 2) ** 2 + ((y - 0.5) * 2) ** 2) / 2
        base = (g * vig[..., None]).clip(0, 255).astype(np.uint8)
        im = Image.fromarray(base); d = ImageDraw.Draw(im)
        lc = (120, 190, 140)
        d.rectangle((80, 80, W - 80, H - 80), outline=lc, width=4); d.line((W // 2, 80, W // 2, H - 80), fill=lc, width=4)
        d.ellipse((W // 2 - 170, H // 2 - 170, W // 2 + 170, H // 2 + 170), outline=lc, width=4)
        d.rectangle((80, H // 2 - 260, 360, H // 2 + 260), outline=lc, width=4); d.rectangle((W - 360, H // 2 - 260, W - 80, H // 2 + 260), outline=lc, width=4)
        im = darken(im, 0.45)
    else:
        c0 = np.array(BG2, np.float32); c1 = np.array(BG, np.float32)
        r = np.sqrt(((x - 0.5) * 1.6) ** 2 + ((y - 0.45) * 1.2) ** 2).clip(0, 1)[..., None]
        arr = c0 * (1 - r) + c1 * r
        # subtle diagonal lines
        arr += (((x * W + y * H) % 60) < 2)[..., None] * 6
        im = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    _bgc[kind] = im
    return im.copy()

# ---------- drawing helpers ----------
def txt(d, xy, s, f, fill=WH, anchor='mm', sh=4, alpha=255):
    if sh: d.text((xy[0] + sh, xy[1] + sh), s, font=f, fill=(0, 0, 0, int(150 * alpha / 255)), anchor=anchor)
    fl = fill if len(fill) == 4 else fill + (alpha,)
    d.text(xy, s, font=f, fill=fl, anchor=anchor)

def pill(d, xy, s, f, bg=YEL, fg=BG, anchor='mm', pad=22, alpha=255):
    bb = d.textbbox(xy, s, font=f, anchor=anchor)
    d.rounded_rectangle((bb[0] - pad, bb[1] - pad * 0.6, bb[2] + pad, bb[3] + pad * 0.6), 14, fill=bg + (alpha,))
    d.text(xy, s, font=f, fill=fg + (alpha,), anchor=anchor)

def badge(d, cx, cy, code, r=110, alpha=255, label=True, sc=1.0):
    name, col = TEAM[code]; r = int(r * sc)
    if r < 3: return
    d.ellipse((cx - r - 8, cy - r - 8, cx + r + 8, cy + r + 8), fill=(255, 255, 255, alpha))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (alpha,))
    d.ellipse((cx - r + 14, cy - r + 14, cx + r - 14, cy + r - 14), outline=(255, 255, 255, int(alpha * 0.55)), width=4)
    short = code
    txt(d, (cx, cy), short, font(BLK, r * 0.62 if len(short) <= 3 else r * 0.5), alpha=alpha, sh=0)
    if label: txt(d, (cx, cy + r + 52), name, font(XB, 44), alpha=alpha)

def trophy(d, cx, cy, s=1.0, col=(255, 200, 40), alpha=255):
    c = col + (alpha,); dk = tuple(int(v * 0.7) for v in col) + (alpha,)
    w = 70 * s; h = 90 * s
    d.ellipse((cx - w - 28 * s, cy - h * 0.9, cx - w + 22 * s, cy - h * 0.2), outline=c, width=max(2, int(9 * s)))
    d.ellipse((cx + w - 22 * s, cy - h * 0.9, cx + w + 28 * s, cy - h * 0.2), outline=c, width=max(2, int(9 * s)))
    d.chord((cx - w, cy - h * 1.6, cx + w, cy + h * 0.25), 0, 180, fill=c)
    d.rectangle((cx - w, cy - h * 1.0, cx + w, cy - h * 0.66), fill=c)
    d.rectangle((cx - 12 * s, cy + h * 0.2, cx + 12 * s, cy + h * 0.65), fill=dk)
    d.rounded_rectangle((cx - 48 * s, cy + h * 0.62, cx + 48 * s, cy + h * 0.85), 6, fill=c)
    d.rectangle((cx - 60 * s, cy + h * 0.85, cx + 60 * s, cy + h * 1.05), fill=dk)
    d.ellipse((cx - w * 0.5, cy - h * 0.95, cx - w * 0.1, cy - h * 0.2), fill=(255, 255, 255, int(alpha * 0.25)))

def ball(d, cx, cy, r, alpha=255):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(250, 250, 250, alpha), outline=(30, 30, 30, alpha), width=3)
    pts = [(cx + r * 0.42 * math.cos(math.radians(a - 90)), cy + r * 0.42 * math.sin(math.radians(a - 90))) for a in range(0, 360, 72)]
    d.polygon(pts, fill=(25, 25, 25, alpha))

def countnum(v0, v1, p, fmt='{:.0f}'):
    v = v0 + (v1 - v0) * eout(p)
    s = fmt.format(v)
    return s.replace(',', ' ')

# ---------- scene renderers: f(t, D, P) -> RGBA overlay on base ----------
class Ctx:
    def __init__(self, t, D): self.t, self.D = t, D; self.p = t / max(D, 0.01)

def base_photo(c, P):
    k = P['photo']; im = kb(k, c.p, P.get('move', 'in'), P.get('amt', 0.14), P.get('focus', (0.5, 0.5)))
    return darken(im, P.get('dark', 0.45)), k

def sc_hook28(c, P, d):
    t = c.t
    n = countnum(0, 28, ramp(t, 0.1, 2.2))
    sc = 1 + 0.06 * math.sin(t * 3) * (t > 2.3)
    txt(d, (W // 2, 430), n, font(BLK, 360 * sc), fill=YEL, sh=8)
    txt(d, (W // 2, 640), 'YIL', font(BLK, 120), sh=6)
    a = int(255 * ramp(t, 1.6, 0.6))
    if a: pill(d, (W // 2, 790), 'Oxirgi kubok: 1998', font(XB, 54), bg=(0, 0, 0), fg=WH, alpha=a)
    a = ramp(t, c.D - 3.2, 0.5)
    if a:
        s = back(a); pill(d, (W // 2, 160), 'NAVBAHOR FINALDA!', font(BLK, int(80 * max(s, 0.05))), alpha=int(255 * min(1, a * 2)))

def sc_vs(c, P, d, a_code='NAV', b_code='LOK', title='FINAL', sub=None, q=True):
    t = c.t
    pa = eout(ramp(t, 0.0, 0.8)); pb = eout(ramp(t, 0.25, 0.8))
    badge(d, int(-200 + (W // 2 - 420 + 200) * pa), 520, a_code, 150)
    badge(d, int(W + 200 - (W + 200 - (W // 2 + 420)) * pb), 520, b_code, 150)
    s = back(ramp(t, 0.8, 0.6))
    if s > 0.02: txt(d, (W // 2, 520), 'VS', font(BLK, int(120 * s)), fill=YEL, sh=6)
    a = int(255 * ramp(t, 1.0, 0.5))
    if a: pill(d, (W // 2, 190), title, font(BLK, 86), alpha=a)
    if sub:
        a = int(255 * ramp(t, 1.6, 0.6))
        if a: txt(d, (W // 2, 820), sub, font(SB, 46), alpha=a)
    if P.get('bottom'):
        a = int(255 * ramp(t, P.get('bottom_t', 3.0), 0.6))
        if a: pill(d, (W // 2, 905), P['bottom'], font(XB, 48), bg=(0, 0, 0), fg=YEL, alpha=a)

def sc_list(c, P, d):
    t = c.t; items = P['items']
    txt(d, (W // 2, 140), P.get('title', 'BUGUN VIDEODA'), font(BLK, 74), fill=YEL)
    n = len(items); dt = (c.D - 1.0) / n
    for i, s in enumerate(items):
        a = ramp(t, 0.4 + i * dt, 0.4)
        if a <= 0: continue
        y = 270 + i * 112; x = 330 + int(60 * (1 - eout(a)))
        d.rounded_rectangle((x, y - 44, x + 1260, y + 44), 16, fill=(255, 255, 255, int(28 * a)))
        txt(d, (x + 60, y), str(i + 1), font(BLK, 56), fill=YEL, alpha=int(255 * a))
        txt(d, (x + 120, y), s, font(XB, 48), anchor='lm', alpha=int(255 * a))

def sc_title(c, P, d):
    t = c.t; a = eout(ramp(t, 0.1, 0.7))
    txt(d, (W // 2, 400 - int(40 * (1 - a))), P['num'], font(XB, 60), fill=YEL, alpha=int(255 * a))
    s = back(ramp(t, 0.35, 0.7))
    if s > 0.02: txt(d, (W // 2, 540), P['title'], font(BLK, int(104 * s)), sh=6)
    w = int(700 * eout(ramp(t, 0.6, 0.8)))
    if w: d.rectangle((W // 2 - w // 2, 640, W // 2 + w // 2, 648), fill=YEL + (255,))
    if P.get('sub'):
        a2 = int(255 * ramp(t, 1.0, 0.6))
        if a2: txt(d, (W // 2, 720), P['sub'], font(SB, 46), alpha=a2)

def scoreboard(d, A_, B_, sa, sb, y=150, info=None, alpha=255, tag=None, flash=0):
    cx = W // 2
    d.rounded_rectangle((cx - 640, y - 70, cx + 640, y + 70), 22, fill=(8, 10, 20, int(alpha * 0.85)))
    for code, x, anc in ((A_, cx - 610, 'lm'), (B_, cx + 610, 'rm')):
        name, col = TEAM[code]
        bx = x + 50 if anc == 'lm' else x - 50
        d.ellipse((bx - 40, y - 40, bx + 40, y + 40), fill=col + (alpha,))
        txt(d, (bx, y), code, font(BLK, 30 if len(code) <= 3 else 22), alpha=alpha, sh=0)
        txt(d, (x + 110 if anc == 'lm' else x - 110, y), name, font(XB, 50), anchor=anc, alpha=alpha, sh=0)
    fc = YEL if not flash else tuple(int(YEL[i] * (1 - flash) + 255 * flash) for i in range(3))
    d.rounded_rectangle((cx - 120, y - 58, cx + 120, y + 58), 14, fill=fc + (alpha,))
    txt(d, (cx, y + 2), '%s : %s' % (sa, sb), font(BLK, 76), fill=BG, alpha=alpha, sh=0)
    if tag: pill(d, (cx, y + 105), tag, font(XB, 34), bg=(214, 52, 64), fg=WH, alpha=alpha, pad=16)
    if info: txt(d, (cx, y + (170 if tag else 115)), info, font(SB, 40), alpha=alpha)

def timeline(d, t, x0, x1, y, total, events, prog, show_upto=None):
    """events: list of (minute, label, side ('top'/'bot'), color, pos_override)"""
    d.rounded_rectangle((x0, y - 10, x1, y + 10), 10, fill=(255, 255, 255, 50))
    xp = x0 + (x1 - x0) * prog
    d.rounded_rectangle((x0, y - 10, xp, y + 10), 10, fill=YEL + (255,))
    for m in (0, 45, 90) + ((105, 120) if total > 90 else ()):
        xm = x0 + (x1 - x0) * m / total
        d.line((xm, y + 18, xm, y + 34), fill=(255, 255, 255, 140), width=3)
        txt(d, (xm, y + 62), "%d'" % m, font(SB, 30), fill=GR, sh=0)
    if total > 90:
        xm = x0 + (x1 - x0) * 90 / total
        txt(d, ((xm + x1) / 2, y + 105), "QO'SHIMCHA VAQT", font(XB, 30), fill=(255, 120, 120), sh=0)
    for ei, (m, label, col, pos) in enumerate(events):
        frac = (pos if pos is not None else m) / total
        if prog < frac: continue
        lift = 0 if ei % 2 == 0 else 70
        xm = x0 + (x1 - x0) * frac; k = cl((prog - frac) * total / 6)
        s = back(k)
        r = int(26 * max(s, 0.05)); ball(d, xm, y, r)
        d.line((xm, y - 30, xm, y - 70 - lift), fill=col + (255,), width=4)
        if label: txt(d, (xm, y - 98 - lift), label, font(XB, 36), fill=WH, alpha=int(255 * min(1, k * 2)))
    ball(d, xp, y, 16)

def sc_match(c, P, d):
    """scoreboard + timeline progressing; P: a,b, info, total, events[(min,label,teamcode)], prog range, tag"""
    t = c.t
    total = P.get('total', 90)
    p0, p1 = P.get('prog', (0, 1))
    prog = (p0 + (p1 - p0) * ease(ramp(t, 0.6, c.D - 1.4))) if P.get('events') is not None else None
    if P.get('kf'):
        kf = P['kf']; prog = kf[0][1]
        for (ta, pa), (tb, pb) in zip(kf, kf[1:]):
            if t >= ta: prog = pa + (pb - pa) * ease(ramp(t, ta, max(tb - ta, 0.01)))
    sa, sb = 0, 0; flash = 0
    evs = []
    for (m, label, code, *rest) in P.get('events', []):
        pos = rest[0] if rest else None
        evs.append((m, label, TEAM[code][1], pos))
        if prog is not None and prog >= (pos if pos is not None else m) / total:
            if code == P['a']: sa += 1
            else: sb += 1
            fl = cl(1 - (prog - (pos if pos is not None else m) / total) * total / 4); flash = max(flash, fl)
    if 'score' in P: sa, sb = P['score']
    a = int(255 * ramp(t, 0, 0.5))
    scoreboard(d, P['a'], P['b'], sa, sb, y=170, info=P.get('info'), alpha=a, tag=P.get('tag'), flash=flash)
    if prog is not None:
        timeline(d, t, 220, W - 220, 700, total, evs, prog)
    if P.get('big'):
        bt, s = P['big']
        k = back(ramp(t, bt, 0.6))
        if k > 0.02: pill(d, (W // 2, 520), s, font(BLK, int(70 * k)), alpha=255)

def sc_clock(c, P, d):
    t = c.t; m = 22 + (90 - 22) * ease(ramp(t, 0.5, c.D - 2.0))
    scoreboard(d, 'OKMK', 'NAV', 0, 1, y=170, info="Yarim final · Toshkent")
    txt(d, (W // 2, 520), "%d'" % int(m), font(BLK, 300), fill=YEL, sh=8)
    a = int(255 * ramp(t, 1.0, 0.5))
    if a: txt(d, (W // 2, 760), 'OKMK tenglashtirishga urindi...', font(SB, 50), alpha=a)
    if m >= 89.9:
        k = back(ramp(t, c.D - 1.4, 0.5))
        if k > 0.02: pill(d, (W // 2, 880), 'YAKUN: NAVBAHOR FINALDA', font(BLK, int(60 * k)), bg=TEAM['NAV'][1], fg=WH)

def sc_question(c, P, d):
    t = c.t
    s = back(ramp(t, 0.1, 0.6))
    if s > 0.02: txt(d, (W // 2, 300), '?', font(BLK, int(300 * s)), fill=YEL, sh=8)
    a = int(255 * ramp(t, 0.5, 0.5))
    lines = P['q'].split('\n')
    for i, l in enumerate(lines):
        if a: txt(d, (W // 2, 560 + i * 90), l, font(BLK, 74), alpha=a)
    if P.get('opts'):
        for i, o in enumerate(P['opts']):
            ao = int(255 * ramp(t, 1.0 + i * 0.4, 0.5))
            if ao: pill(d, (W // 2 + (i - (len(P['opts']) - 1) / 2) * 560, 820), o, font(XB, 50), bg=TEAM[P['oc'][i]][1] if P.get('oc') else YEL, fg=WH if P.get('oc') else BG, alpha=ao)
    # 2-s think bar at end
    hold = P.get('hold', 2.0)
    pr = ramp(t, c.D - hold - 0.2, hold)
    if pr > 0:
        d.rounded_rectangle((W // 2 - 400, 940, W // 2 + 400, 956), 8, fill=(255, 255, 255, 50))
        d.rounded_rectangle((W // 2 - 400, 940, W // 2 - 400 + 800 * pr, 956), 8, fill=YEL + (255,))

def road_node(d, x, y, rnd, a_code, b_code, score, alpha, sub=None, hi=False):
    w = 470
    d.rounded_rectangle((x - w // 2, y - 120, x + w // 2, y + 120), 24, fill=(10, 14, 28, int(alpha * 0.9)), outline=(YEL + (alpha,)) if hi else (255, 255, 255, int(alpha * 0.25)), width=5 if hi else 2)
    txt(d, (x, y - 80), rnd, font(XB, 38), fill=YEL, alpha=alpha, sh=0)
    for code, xx in ((a_code, x - 150), (b_code, x + 150)):
        d.ellipse((xx - 46, y - 36, xx + 46, y + 56), fill=TEAM[code][1] + (alpha,))
        txt(d, (xx, y + 10), code, font(BLK, 32 if len(code) <= 3 else 24), alpha=alpha, sh=0)
    txt(d, (x, y + 10), score, font(BLK, 60), alpha=alpha, sh=0)
    if sub: txt(d, (x, y + 88), sub, font(SB, 30), fill=GR, alpha=alpha, sh=0)

def sc_road(c, P, d):
    """P: title, nodes [(rnd,a,b,score,sub)], show (n visible at start), reveal index list with times, hi"""
    t = c.t
    txt(d, (W // 2, 120), P['title'], font(BLK, 66), fill=YEL)
    nodes = P['nodes']; n = len(nodes); xs = [W // 2 + (i - (n - 1) / 2) * 560 for i in range(n)]
    for i in range(n - 1):
        d.line((xs[i] + 240, 520, xs[i + 1] - 240, 520), fill=(255, 255, 255, 90), width=6)
    for i, (rnd, a_, b_, sc, sub) in enumerate(nodes):
        t0 = P.get('times', [0.2 + 0.3 * j for j in range(n)])[i]
        al = ramp(t, t0, 0.5)
        if al <= 0: continue
        ys = 520 + int(50 * (1 - eout(al)))
        road_node(d, xs[i], ys, rnd, a_, b_, sc, int(255 * al), sub, hi=(i == P.get('hi')))
    if P.get('bottom'):
        a = int(255 * ramp(t, P.get('bottom_t', 2.0), 0.5))
        if a: pill(d, (W // 2, 860), P['bottom'], font(XB, 50), alpha=a)

def sc_stats(c, P, d):
    """P: title, items [(value, label, fmt)], photo optional"""
    t = c.t
    txt(d, (W // 2, 150), P['title'], font(BLK, 66), fill=YEL)
    it = P['items']; n = len(it); xs = [W // 2 + (i - (n - 1) / 2) * (1600 / n) for i in range(n)]
    for i, (v, lab, *rest) in enumerate(it):
        t0 = 0.4 + i * P.get('dt', 0.6); a = ramp(t, t0, 0.4)
        if a <= 0: continue
        col = rest[0] if rest else WH
        d.rounded_rectangle((xs[i] - 1600 / n / 2 + 20, 330, xs[i] + 1600 / n / 2 - 20, 760), 28, fill=(6, 10, 22, int(170 * a)), outline=(255, 255, 255, int(40 * a)), width=2)
        if isinstance(v, (int, float)): s = countnum(0, v, ramp(t, t0, 1.2), '{:,.0f}' if v >= 1000 else '{:.0f}')
        else: s = v
        txt(d, (xs[i], 500), s, font(BLK, P.get('size', 170)), fill=col, alpha=int(255 * a))
        txt(d, (xs[i], 670), lab, font(XB, 44), alpha=int(255 * a))
    if P.get('bottom'):
        a = int(255 * ramp(t, P.get('bottom_t', 2.5), 0.5))
        if a: pill(d, (W // 2, 870), P['bottom'], font(XB, 48), alpha=a)

def sc_bigtext(c, P, d):
    t = c.t
    if P.get('trophy'):
        s = back(ramp(t, 0.1, 0.8))
        if s > 0.02: trophy(d, W // 2, 330, 1.5 * s)
    k = back(ramp(t, P.get('t0', 0.3), 0.7))
    if k > 0.02: txt(d, (W // 2, P.get('y', 560)), P['big'], font(BLK, int(P.get('size', 200) * k)), fill=P.get('col', YEL), sh=8)
    for i, (s, tt) in enumerate(P.get('lines', [])):
        a = int(255 * ramp(t, tt, 0.5))
        if a: txt(d, (W // 2, P.get('y', 560) + 170 + i * 80), s, font(XB, 56), alpha=a)
    if P.get('pill'):
        s, tt = P['pill']; a = int(255 * ramp(t, tt, 0.5))
        if a: pill(d, (W // 2, 930), s, font(BLK, 54), alpha=a)

def sc_trophies(c, P, d):
    t = c.t
    txt(d, (W // 2, 140), P['title'], font(BLK, 70), fill=YEL)
    ys = P['years']; n = len(ys)
    for i, (y, col) in enumerate(ys):
        t0 = P.get('times', [0.3 + 0.5 * j for j in range(n)])[i]
        s = back(ramp(t, t0, 0.6))
        if s <= 0.02: continue
        x = W // 2 + (i - (n - 1) / 2) * 380
        trophy(d, x, 470, 1.5 * s, col=col)
        txt(d, (x, 700), str(y), font(BLK, 80), alpha=int(255 * min(1, s)))
    if P.get('bottom'):
        a = int(255 * ramp(t, P.get('bottom_t', 2.0), 0.5))
        if a: pill(d, (W // 2, 870), P['bottom'], font(BLK, 56), alpha=a)

def sc_bars(c, P, d):
    """horizontal bars: rows [(label, value, color)], max"""
    t = c.t
    txt(d, (W // 2, 110), P['title'], font(BLK, 64), fill=YEL)
    rows = P['rows']; mx = P['max']; y0 = 210; rh = min(84, 690 // len(rows))
    for i, (lab, v, col, *rest) in enumerate(rows):
        tr = P['rt'][i] if P.get('rt') else 0.3 + i * 0.15
        a = ramp(t, tr, 0.4)
        if a <= 0: continue
        y = y0 + i * rh
        txt(d, (560, y), lab, font(XB, 42), anchor='rm', alpha=int(255 * a))
        g = eout(ramp(t, tr + 0.1, 1.4)); L = 1050 * v / mx * g
        d.rounded_rectangle((590, y - rh * 0.36, 590 + max(L, 8), y + rh * 0.36), 10, fill=col + (int(255 * a),))
        txt(d, (610 + L, y), countnum(0, v, g), font(BLK, 44), anchor='lm', alpha=int(255 * a))
        if rest and rest[0]:
            gp = ramp(t, P.get('ghost_t', 2.0), 0.8)
            if gp > 0:
                L2 = 1050 * (v + 1) / mx
                d.rounded_rectangle((590 + L, y - rh * 0.36, 590 + L + (L2 - L) * eout(gp), y + rh * 0.36), 10, outline=YEL + (255,), width=4)
                txt(d, (640 + L2, y), '4?', font(BLK, 44), fill=YEL, anchor='lm', alpha=int(255 * gp))
    if P.get('bottom'):
        a = int(255 * ramp(t, P.get('bottom_t', 2.5), 0.5))
        if a: pill(d, (W // 2, 925), P['bottom'], font(XB, 44), alpha=a)

def sc_compare(c, P, d):
    """two columns NAV vs LOK: P: cat, left, right, sub_l, sub_r, verdict, trophies (nl, nr)"""
    t = c.t
    pill(d, (W // 2, 120), P['cat'], font(BLK, 56), alpha=int(255 * ramp(t, 0, 0.4)))
    cl_, cr_ = P.get('codes', ('NAV', 'LOK'))
    for code, x, val, sub, t0 in ((cl_, W // 2 - 450, P['left'], P.get('sub_l'), P.get('t_l', 0.4)), (cr_, W // 2 + 450, P['right'], P.get('sub_r'), P.get('t_r', 0.9))):
        a = ramp(t, t0, 0.5)
        if a <= 0: continue
        badge(d, x, 330, code, 90, alpha=int(255 * a), label=False)
        txt(d, (x, 460), TEAM[code][0], font(XB, 46), alpha=int(255 * a))
        if P.get('trophies'):
            n = P['trophies'][0 if code == cl_ else 1]
            for j in range(n):
                s = back(ramp(t, t0 + 0.4 + j * 0.3, 0.5))
                if s > 0.02: trophy(d, x + (j - (n - 1) / 2) * 150, 610, 0.75 * s)
            y_val = 760
        else: y_val = 640
        k = back(ramp(t, t0 + 0.3, 0.6))
        if k > 0.02: txt(d, (x, y_val), val, font(BLK, int(P.get('size', 130) * k)), fill=YEL, sh=6)
        if sub:
            a2 = int(255 * ramp(t, t0 + 0.7, 0.5))
            if a2: txt(d, (x, y_val + 110), sub, font(SB, 40), alpha=a2)
    d.line((W // 2, 260, W // 2, 900), fill=(255, 255, 255, 60), width=3)
    if P.get('verdict'):
        a = int(255 * ramp(t, P.get('verdict_t', 3.0), 0.5))
        if a: pill(d, (W // 2, 925), P['verdict'], font(BLK, 48), alpha=a)

def sc_record(c, P, d):
    """dots for final records: rows [(code, [W/L...])]"""
    t = c.t
    txt(d, (W // 2, 130), P['title'], font(BLK, 64), fill=YEL)
    for r, (code, res, lab, t0) in enumerate(P['rows']):
        y = 380 + r * 300; a = ramp(t, t0, 0.5)
        if a <= 0: continue
        badge(d, 330, y, code, 85, alpha=int(255 * a), label=False)
        txt(d, (460, y - 95), TEAM[code][0], font(XB, 44), anchor='lm', alpha=int(255 * a))
        for j, rr in enumerate(res):
            s = back(ramp(t, t0 + 0.4 + j * 0.35, 0.5))
            if s <= 0.02: continue
            x = 520 + j * 170; col = (40, 190, 100) if rr[0] == 'G' else (220, 60, 70)
            d.ellipse((x - 60 * s, y - 60 * s + 20, x + 60 * s, y + 60 * s + 20), fill=col + (255,))
            txt(d, (x, y + 20), rr[0], font(BLK, int(56 * s)), sh=0)
            txt(d, (x, y + 110), rr[1:], font(SB, 30), fill=GR, sh=0, alpha=int(255 * min(1, s)))
        a2 = int(255 * ramp(t, t0 + 0.6 + len(res) * 0.35, 0.5))
        if a2: txt(d, (1560, y + 20), lab, font(BLK, 90), fill=YEL, alpha=a2)
    if P.get('bottom'):
        a = int(255 * ramp(t, P.get('bottom_t', 3.0), 0.5))
        if a: pill(d, (W // 2, 900), P['bottom'], font(XB, 46), alpha=a)

def sc_years(c, P, d):
    t = c.t
    y0, y1 = P['range']
    yv = y0 + (y1 - y0) * ease(ramp(t, 0.6, c.D - 2.0))
    txt(d, (W // 2, 420), str(int(yv)), font(BLK, 260), fill=YEL, sh=8)
    x0, x1 = 300, W - 300; d.rounded_rectangle((x0, 640, x1, 656), 8, fill=(255, 255, 255, 60))
    xp = x0 + (x1 - x0) * (yv - y0) / (y1 - y0); d.rounded_rectangle((x0, 640, xp, 656), 8, fill=YEL + (255,))
    txt(d, (x0, 700), str(y0), font(XB, 40), sh=0); txt(d, (x1, 700), str(y1), font(XB, 40), sh=0)
    trophy(d, x0, 560, 0.5)
    a = int(255 * ramp(t, 1.2, 0.5))
    if a: txt(d, (W // 2, 820), P['line'], font(XB, 52), alpha=a)
    if yv >= y1 - 0.01:
        k = back(ramp(t, c.D - 1.2, 0.5))
        if k > 0.02: pill(d, (W // 2, 180), P['pill'], font(BLK, int(64 * k)))

def sc_photo(c, P, d):
    t = c.t
    if P.get('head'):
        a = eout(ramp(t, 0.2, 0.6))
        pill(d, (W // 2, 160), P['head'], font(BLK, 64), alpha=int(255 * a))
    for i, (s, tt) in enumerate(P.get('lines', [])):
        a = ramp(t, tt, 0.5)
        if a > 0:
            y = 420 + i * 120 + int(30 * (1 - eout(a)))
            txt(d, (W // 2, y), s, font(BLK if i == 0 else XB, 92 if i == 0 else 56), fill=YEL if i == 0 else WH, alpha=int(255 * a), sh=6)

def sc_twofinals(c, P, d):
    t = c.t
    txt(d, (W // 2, 130), 'IKKI ALAMLI FINAL', font(BLK, 70), fill=YEL)
    for i, (yr, a_, b_, sc, sub) in enumerate((('2022', 'NAV', 'NAS', '1 : 2', "q.v. · Buxoro"), ('2024', 'NAV', 'AND', '2 : 3', "q.v. · Farg'ona"))):
        x = W // 2 + (i - 0.5) * 760; al = ramp(t, 0.4 + i * 0.6, 0.5)
        if al <= 0: continue
        d.rounded_rectangle((x - 330, 260, x + 330, 760), 30, fill=(10, 14, 28, int(230 * al)), outline=(255, 255, 255, int(70 * al)), width=2)
        txt(d, (x, 330), yr, font(BLK, 80), fill=YEL, alpha=int(255 * al), sh=0)
        for code, xx in ((a_, x - 190), (b_, x + 190)):
            d.ellipse((xx - 70, 450, xx + 70, 590), fill=TEAM[code][1] + (int(255 * al),))
            txt(d, (xx, 520), code, font(BLK, 44), alpha=int(255 * al), sh=0)
        txt(d, (x, 520), sc, font(BLK, 86), alpha=int(255 * al), sh=0)
        txt(d, (x, 680), sub, font(SB, 40), fill=GR, alpha=int(255 * al), sh=0)
    a = int(255 * ramp(t, 2.2, 0.5))
    if a: pill(d, (W // 2, 880), 'Ikkalasi ham qo\'shimcha vaqtda · farq 1 gol', font(XB, 50), alpha=a)

def sc_end(c, P, d):
    t = c.t
    txt(d, (W // 2, 200), 'SIZNINGCHA KUBOK KIMDA?', font(BLK, 76), fill=YEL)
    badge(d, W // 2 - 420, 500, 'NAV', 130); badge(d, W // 2 + 420, 500, 'LOK', 130)
    txt(d, (W // 2 - 420, 330), '1', font(BLK, 90), fill=YEL); txt(d, (W // 2 + 420, 330), '2', font(BLK, 90), fill=YEL)
    trophy(d, W // 2, 520, 1.1)
    a = int(255 * ramp(t, 0.6, 0.5))
    if a: pill(d, (W // 2, 820), "Izohda yozing: 1 yoki 2 + hisob", font(XB, 50), alpha=a)
    if P.get('sub'):
        k = back(ramp(t, 1.5, 0.6))
        if k > 0.02: pill(d, (W // 2, 925), 'OBUNA BO\'LING · TAQQOS', font(BLK, int(54 * k)), bg=(214, 52, 64), fg=WH)

SCENES = {
 'hook28': (('photo', 'nam9', 'in', 0.6), sc_hook28, {}),
 'hookfinal': (('pitch',), lambda c, P, d: sc_vs(c, P, d, 'NAV', 'LOK', 'FINAL', "10-dekabr · Toshkent (rejaga ko'ra)"), {'bottom': 'Eng hayratlanarlisi — videoning oxirida', 'bottom_t': 3.5}),
 'chapters': (('dark',), sc_list, {'items': ["Kechagi g'alaba", 'Finalgacha yo\'l', 'Oltin davr: 1992–1998', 'Ikki alamli final', 'Navbahor va Lokomotiv: raqamlarda', 'Sizningcha kubok kimda?']}),
 'title1': (('photo', 'stad1', 'in', 0.55), sc_title, {'num': '1-BO\'LIM', 'title': "KECHAGI G'ALABA", 'sub': 'Yarim final · 24-noyabr 2026'}),
 'semi_score': (('pitch',), sc_match, {'a': 'OKMK', 'b': 'NAV', 'info': "Yarim final · 24.11.2026 · Toshkent, Lokomotiv stadioni", 'score': (0, 0), 'big': (1.5, "O'zbekiston kubogi · 1/2 final")}),
 'goal22': (('pitch',), sc_match, {'a': 'OKMK', 'b': 'NAV', 'info': "Yarim final · Toshkent", 'events': [(22, "22' Kodjo", 'NAV')], 'kf': [(0.3, 0), (3.3, 22 / 90), (10, 0.36)]}),
 'clock': (('pitch',), sc_clock, {}),
 'semi2': (('pitch',), sc_match, {'a': 'AND', 'b': 'LOK', 'info': 'Yarim final · Olmaliq', 'events': [], 'total': 120, 'kf': [(0.3, 0), (7.0, 0.75)]}),
 'extra': (('pitch',), sc_match, {'a': 'AND', 'b': 'LOK', 'info': 'Yarim final · Olmaliq', 'tag': "QO'SHIMCHA VAQT", 'events': [(98, "98' Reimov", 'LOK'), (109, "109' Abduxoliqov", 'LOK')], 'total': 120, 'kf': [(0, 0.75), (5.5, 98 / 120), (8.3, 109 / 120), (10.5, 1.0)]}),
 'final_card': (('photo', 'pak1', 'in', 0.55), lambda c, P, d: sc_vs(c, P, d, 'NAV', 'LOK', 'FINAL', "10-dekabr · Paxtakor stadioni · rejaga ko'ra"), {}),
 'question1': (('dark',), sc_question, {'q': "Qaysi jamoaning yo'li\nqiyinroq bo'lgan?", 'opts': ['NAVBAHOR', 'LOKOMOTIV'], 'oc': ['NAV', 'LOK']}),
 'title2': (('photo', 'net2', 'in', 0.5), sc_title, {'num': '2-BO\'LIM', 'title': "FINALGACHA YO'L"}),
 'path_nasaf': (('dark',), sc_road, {'title': "NAVBAHORNING YO'LI", 'nodes': [('1/8 FINAL', 'NAV', 'NAS', '? : ?', None)], 'hi': 0, 'bottom': "Raqib: 4 karra kubok sohibi Nasaf", 'bottom_t': 2.0}),
 'path_nasaf2': (('dark',), sc_road, {'title': "NAVBAHORNING YO'LI", 'nodes': [('1/8 FINAL', 'NAV', 'NAS', '1 : 0', "so'nggi daqiqalarda")], 'times': [0.0], 'hi': 0, 'bottom': 'Nasaf turnirni tark etdi', 'bottom_t': 1.5}),
 'path_gaz': (('dark',), sc_road, {'title': "NAVBAHORNING YO'LI", 'nodes': [('1/8 FINAL', 'NAV', 'NAS', '1 : 0', "so'nggi daqiqalarda"), ('1/4 FINAL', 'NAV', 'GAZ', '3 : 1', '21-oktyabr')], 'times': [0.0, 0.4], 'hi': 1}),
 'path_okmk': (('dark',), sc_road, {'title': "NAVBAHORNING YO'LI", 'nodes': [('1/8 FINAL', 'NAV', 'NAS', '1 : 0', "so'nggi daqiqalarda"), ('1/4 FINAL', 'NAV', 'GAZ', '3 : 1', '21-oktyabr'), ('1/2 FINAL', 'OKMK', 'NAV', '0 : 1', "24-noyabr · 22' Kodjo")], 'times': [0.0, 0.0, 0.4], 'hi': 2}),
 'path_sum': (('dark',), sc_stats, {'title': 'OXIRGI 3 BOSQICH', 'items': [(3, "o'yin"), (3, "g'alaba", (60, 200, 110)), (5, 'urilgan gol', YEL), (1, "o'tkazilgan gol", (230, 90, 90))]}),
 'loko_path': (('photo', 'fer2', 'right', 0.62), sc_road, {'title': "LOKOMOTIVNING YO'LI", 'nodes': [('1/4 FINAL', 'NEF', 'LOK', '2 : 4', "20-oktyabr · Farg'ona")], 'hi': 0, 'bottom': '6 gol — hammasi birinchi bo\'limda', 'bottom_t': 3.0}),
 'loko_path2': (('dark',), sc_road, {'title': "LOKOMOTIVNING YO'LI", 'nodes': [('1/4 FINAL', 'NEF', 'LOK', '2 : 4', "20-oktyabr · Farg'ona"), ('1/2 FINAL', 'AND', 'LOK', '0 : 2', "qo'shimcha vaqtda")], 'times': [0.0, 0.4], 'hi': 1, 'bottom': 'Ikkala jamoa ham kuchli raqiblarni chetlatdi', 'bottom_t': 3.5}),
 'question2': (('dark',), sc_question, {'q': 'Kim kuchliroq raqiblarni yengdi?', 'opts': ['Nasaf + OKMK', 'Neftchi + Andijon'], 'oc': ['NAV', 'LOK']}),
 'title3': (('photo', 'nam1', 'in', 0.55), sc_title, {'num': '3-BO\'LIM', 'title': 'OLTIN DAVR', 'sub': '1992 – 1998'}),
 'founded': (('photo', 'nam5', 'in', 0.55), sc_photo, {'head': 'NAMANGAN', 'lines': [('1978', 0.6), ('Tekstilshchik nomi bilan tashkil topgan', 1.4), ('1980-yildan — NAVBAHOR', 3.2)]}),
 'stadium': (('pitch',), sc_stats, {'title': 'NAMANGAN MARKAZIY STADIONI', 'items': [('1956', 'ochilgan yil'), (22000, "o'rin", YEL)], 'size': 150}),
 'cup1992': (('dark',), sc_bigtext, {'trophy': True, 'big': '1992', 'y': 600, 'size': 190, 'lines': [("O'zbekiston kubogining birinchi sohibi", 5.0)], 'pill': ('NAVBAHOR', 7.9)}),
 'cup95_98': (('dark',), sc_trophies, {'title': 'NAVBAHORNING KUBOKLARI', 'years': [(1992, (255, 200, 40)), (1995, (255, 200, 40)), (1998, (255, 200, 40))], 'times': [0.0, 0.5, 1.9], 'bottom': '6 yilda 3 kubok', 'bottom_t': 3.8}),
 'champ1996': (('photo', 'fans2', 'right', 0.6), sc_stats, {'title': '1996: NAVBAHOR — CHEMPION', 'items': [(30, "o'yin"), (23, "g'alaba", (60, 200, 110)), (5, 'durang', (200, 200, 210)), (2, "mag'lubiyat", (230, 90, 90))], 'dt': 0.9}),
 'champ1996b': (('photo', 'fans3', 'in', 0.62), sc_compare, {'cat': '1996 · YAKUNIY JADVAL', 'left': '74', 'right': '72', 'sub_l': 'ochko · 88 gol', 'sub_r': 'ochko', 'verdict': 'Farq atigi 2 ochko', 'codes': ('NAV', 'NEF'), 't_l': 0.5, 't_r': 3.5, 'verdict_t': 4.5}),
 'supercup': (('dark',), sc_bigtext, {'trophy': True, 'big': '1999', 'y': 600, 'size': 190, 'lines': [('SUPERKUBOK', 1.2)]}),
 'gap28': (('photo', 'nam11', 'in', 0.6), sc_years, {'range': (1998, 2026), 'line': 'Yangi kubok kutilmoqda...', 'pill': '28 YIL'}),
 'title4': (('photo', 'flood2', 'in', 0.55), sc_title, {'num': '4-BO\'LIM', 'title': 'IKKI ALAMLI FINAL', 'sub': '2022 va 2024'}),
 'f2022': (('pitch',), sc_match, {'a': 'NAV', 'b': 'NAS', 'info': 'Final · 30.10.2022 · Buxoro Arena · 11 127 tomoshabin', 'score': (0, 0), 'big': (2.0, 'FINAL 2022')}),
 'f2022b': (('pitch',), sc_match, {'a': 'NAV', 'b': 'NAS', 'info': 'Final 2022 · Buxoro Arena', 'events': [(29, "29' Nasaf", 'NAS'), (57, "57' Abdumannopov", 'NAV')], 'total': 120, 'kf': [(0.2, 0), (2.0, 29 / 120), (6.5, 57 / 120), (11.0, 0.75)]}),
 'f2022c': (('pitch',), sc_match, {'a': 'NAV', 'b': 'NAS', 'info': 'Final 2022 · Buxoro Arena', 'tag': "QO'SHIMCHA VAQT", 'events': [(29, "29'", 'NAS'), (57, "57'", 'NAV'), (100, "100' Mateus Lima", 'NAS')], 'total': 120, 'kf': [(0, 0.75), (1.5, 100 / 120), (6.0, 0.9)], 'big': (4.7, 'Kubok: NASAF')}),
 'f2024': (('photo', 'fer3', 'in', 0.5), sc_photo, {'head': "FINAL 2024 · FARG'ONA", 'lines': [('20 000', 0.8), ('tomoshabin · Istiqlol stadioni · 5-oktyabr', 1.6), ('Navbahor — Andijon: vodiy derbisi', 3.6)]}),
 'f2024b': (('pitch',), sc_match, {'a': 'NAV', 'b': 'AND', 'info': "Final 2024 · Farg'ona", 'events': [(40, 'Navbahor', 'NAV'), (82, "82' Andijon", 'AND'), (116, "116'", 'AND'), (118, 'Navbahor!', 'NAV', 117.6)], 'total': 124, 'kf': [(0.2, 0), (1.2, 40 / 124), (4.2, 82 / 124), (7.6, 116 / 124), (11.0, 117.6 / 124), (12.5, 0.955)]}),
 'f2024c': (('pitch',), sc_match, {'a': 'NAV', 'b': 'AND', 'info': "Final 2024 · Farg'ona", 'tag': "QO'SHIMCHA VAQT", 'events': [(40, '', 'NAV'), (82, '', 'AND'), (116, '', 'AND'), (118, '', 'NAV', 117.6), (122, "120+' Andijon", 'AND', 122.5)], 'total': 124, 'kf': [(0, 0.955), (8.6, 122.5 / 124), (10.5, 1.0)], 'big': (10.3, 'YAKUN: 2 : 3')}),
 'f2024d': (('photo', 'fer1', 'right', 0.55), sc_photo, {'head': 'ANDIJON — ILK KUBOK', 'lines': [('2 : 3', 0.6), ("Navbahor yana qo'shimcha vaqtda yutqazdi", 1.6)]}),
 'twofinals': (('dark',), sc_twofinals, {}),
 'title5': (('photo', 'pak2', 'in', 0.55), sc_title, {'num': '5-BO\'LIM', 'title': 'NAVBAHOR vs LOKOMOTIV', 'sub': 'raqamlarda'}),
 'cmp_cups': (('dark',), sc_compare, {'cat': '1-TAQQOS · KUBOKLAR', 'left': '3', 'right': '3', 'sub_l': '1992 · 1995 · 1998', 'sub_r': '2014 · 2016 · 2017', 'trophies': (3, 3), 'size': 110, 'verdict': 'TENG', 'verdict_t': 9.9, 't_l': 2.9, 't_r': 5.2}),
 'cmp_last': (('dark',), sc_compare, {'cat': '2-TAQQOS · OXIRGI KUBOK', 'left': '1998', 'right': '2017', 'sub_l': '28 yil oldin', 'sub_r': '9 yil oldin', 'verdict': 'Lokomotiv yaqinroq', 'verdict_t': 12.6, 't_l': 2.9, 't_r': 8.5}),
 'cmp_finals': (('dark',), sc_compare, {'cat': '3-TAQQOS · FINALLAR', 'left': '6-final', 'right': '4-final', 'sub_l': 'tarixida', 'sub_r': 'tarixida', 'size': 110, 't_l': 2.0, 't_r': 4.5}),
 'cmp_asia': (('photo', 'stad1', 'right', 0.62), sc_photo, {'head': '4-TAQQOS · OSIYO TAJRIBASI', 'lines': [('AFC 2023/24', 0.5), ('Navbahor: Chempionlar ligasi, 1/8 final', 1.6)]}),
 'cmp_table': (('dark',), sc_bars, {'title': "O'ZBEKISTON KUBOGI: KIMDA NECHTA?", 'max': 15, 'rows': [('Paxtakor', 14, (90, 150, 110)), ('Bunyodkor', 4, (200, 160, 60)), ('Nasaf', 4, TEAM['NAS'][1]), ('Navbahor', 3, TEAM['NAV'][1]), ('Lokomotiv', 3, TEAM['LOK'][1]), ('Neftchi', 2, TEAM['NEF'][1]), ('AGMK (OKMK)', 1, TEAM['OKMK'][1]), ("Do'stlik", 1, (150, 150, 170)), ('Andijon', 1, TEAM['AND'][1])], 'rt': [3.5, 6.3, 6.6, 9.3, 9.6, 10.4, 10.5, 10.6, 10.7], 'bottom': 'Manba: Wikipedia · 1992–2025', 'bottom_t': 1.0}),
 'cmp_table2': (('dark',), sc_bars, {'title': "G'OLIB 4-KUBOKNI OLADI", 'max': 15, 'ghost_t': 2.4, 'rows': [('Paxtakor', 14, (90, 150, 110)), ('Bunyodkor', 4, (200, 160, 60)), ('Nasaf', 4, TEAM['NAS'][1]), ('Navbahor', 3, TEAM['NAV'][1], True), ('Lokomotiv', 3, TEAM['LOK'][1], True)], 'bottom': 'Bunyodkor va Nasaf bilan teng bo\'ladi', 'bottom_t': 3.0}),
 'question5': (('dark',), sc_question, {'q': 'Tajriba yoki\n28 yillik sog\'inch?', 'opts': ['SOG\'INCH', 'TAJRIBA'], 'oc': ['NAV', 'LOK']}),
 'reveal': (('dark',), sc_bigtext, {'big': '100%', 'y': 430, 'size': 300, 't0': 10.0, 'col': TEAM['LOK'][1], 'lines': [('Lokomotiv kubok finalida hech qachon yutqazmagan', 3.6), ("3 final — 3 g'alaba", 7.9)]}),
 'reveal2': (('dark',), sc_record, {'title': 'FINALLARDA', 'rows': [('NAV', ['G1992', 'G1995', 'G1998', "M2022", "M2024"], '3/5', 0.1), ('LOK', ['G2014', 'G2016', 'G2017'], '3/3', 4.0)], 'bottom': 'Bitta seriya albatta uziladi', 'bottom_t': 5.6}),
 'title6': (('photo', 'pak4', 'in', 0.55), sc_title, {'num': '6-BO\'LIM', 'title': 'KUBOK KIMDA?'}),
 'final_info': (('photo', 'pak3', 'in', 0.6), lambda c, P, d: sc_vs(c, P, d, 'NAV', 'LOK', 'FINAL · 10-DEKABR', "Paxtakor stadioni · rejaga ko'ra"), {'bottom': '3 kubok  vs  3 kubok', 'bottom_t': 3.5}),
 'vote': (('dark',), sc_end, {}),
 'outro': (('dark',), sc_end, {'sub': True}),
}
CHAP = {'hook': None, 'ch1': "1 · Kechagi g'alaba", 'ch2': "2 · Finalgacha yo'l", 'ch3': '3 · Oltin davr', 'ch4': '4 · Alamli finallar', 'ch5': '5 · Raqamlarda', 'ch6': '6 · Kubok kimda?'}
HOLD = {'question1': 2.0, 'question2': 2.0, 'question5': 2.2, 'vote': 1.5, 'hookfinal': 0.3}
END_EXTRA = 8.0

def load_tl():
    return json.load(open(S + 'timeline.json'))

def build_timeline():
    sys.path.insert(0, S); from script import SEG
    segs = json.load(open(S + 'segs.json'))
    assert len(segs) == len(SEG)
    # decode voice
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', S + 'voice.mp3', '-f', 'f32le', '-ac', '1', '-ar', '48000', '-'])
    v = np.frombuffer(raw, np.float32); sr = 48000
    out = []; scenes = []; words = []; t = 0.6  # lead-in
    out.append(np.zeros(int(0.6 * sr), np.float32))
    for i, (seg, (ch, typ, text)) in enumerate(zip(segs, SEG)):
        a = int(seg['s'] * sr); b = int(segs[i + 1]['s'] * sr) if i + 1 < len(segs) else len(v)
        chunk = v[a:b]; extra = HOLD.get(typ, 0.0)
        if i + 1 == len(segs): extra += END_EXTRA
        out.append(chunk); out.append(np.zeros(int(extra * sr), np.float32))
        D = len(chunk) / sr + extra
        scenes.append({'i': i, 'type': typ, 'ch': ch, 't0': round(t, 3), 'dur': round(D, 3), 'text': text})
        for w in seg['words']:
            words.append({'w': w['w'], 't0': round(t + w['t0'] - seg['s'], 3), 't1': round(t + w['t1'] - seg['s'], 3), 'scene': i})
        t += D
    audio = np.concatenate(out)
    import wave
    pcm = (audio.clip(-1, 1) * 32767).astype(np.int16)
    with wave.open(S + 'narr.wav', 'wb') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())
    json.dump({'scenes': scenes, 'words': words, 'total': round(t, 3)}, open(S + 'timeline.json', 'w'), ensure_ascii=False, indent=0)
    print('total', round(t, 2), 'scenes', len(scenes))

# captions: phrase chunks
def caption_chunks(words):
    chunks = []; cur = []
    for w in words:
        if cur and (len(cur) >= 7 or w['scene'] != cur[-1]['scene'] or w['t0'] - cur[-1]['t1'] > 0.5):
            chunks.append(cur); cur = []
        cur.append(w)
        if w['w'][-1:] in '.!?,' and len(cur) >= 3: chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

def draw_caption(d, chunk, t):
    f = font(BD, 40)
    ws = [w['w'] for w in chunk]
    total = sum(d.textlength(x + ' ', font=f) for x in ws)
    x = W // 2 - total / 2; y = 1018
    d.rounded_rectangle((x - 24, y - 34, x + total + 10, y + 30), 14, fill=(0, 0, 0, 150))
    act = None
    for j, w in enumerate(chunk):
        if w['t0'] - 0.05 <= t: act = j
    for j, w in enumerate(chunk):
        col = YEL if j == act else WH
        d.text((x, y), w['w'], font=f, fill=col + (255,), anchor='lm')
        x += d.textlength(w['w'] + ' ', font=f)

def frame(T, TL, CH):
    sc = None
    for s in TL['scenes']:
        if s['t0'] <= T < s['t0'] + s['dur']: sc = s; break
    if sc is None: sc = TL['scenes'][-1]
    typ = sc['type']; bgspec, fn, P = SCENES[typ]
    c = Ctx(T - sc['t0'], sc['dur'])
    credit = None
    if bgspec[0] == 'photo':
        im = kb(bgspec[1], c.p, bgspec[2], 0.14); im = darken(im, bgspec[3]); credit = CRED.get(bgspec[1])
    else:
        im = grad_bg(bgspec[0])
        # slow drift on graphic backgrounds
    im = im.convert('RGBA')
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    fn(c, P, d)
    # chrome
    txt(d, (60, 58), 'TAQQOS', font(BLK, 40), fill=YEL, anchor='lm', sh=2)
    if CHAP.get(sc['ch']): txt(d, (240, 58), '| ' + CHAP[sc['ch']], font(SB, 30), fill=WH, anchor='lm', sh=2)
    if credit: txt(d, (W - 40, H - 22), 'Foto: ' + credit, font(MD, 20), fill=(220, 220, 220), anchor='rs', sh=1)
    # captions
    for ch in CH:
        if ch[0]['t0'] - 0.15 <= T < ch[-1]['t1'] + 0.25:
            draw_caption(d, ch, T); break
    im.alpha_composite(L)
    # transitions: fade from black at scene start (short) for title cards, dip for others
    k = T - sc['t0']
    out = im.convert('RGB')
    if k < 0.25:
        out = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), out, 0.35 + 0.65 * (k / 0.25))
    if T < 0.6: out = Image.blend(Image.new('RGB', (W, H), (0, 0, 0)), out, max(0.0, T / 0.6))
    end = TL['total']
    if T > end - 0.8: out = Image.blend(out, Image.new('RGB', (W, H), (0, 0, 0)), cl((T - (end - 0.8)) / 0.8))
    return out

def render(a, b, path):
    TL = load_tl(); CH = caption_chunks(TL['words'])
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', path], stdin=subprocess.PIPE)
    n0, n1 = int(round(a * FPS)), int(round(min(b, TL['total']) * FPS))
    for n in range(n0, n1):
        p.stdin.write(frame(n / FPS, TL, CH).tobytes())
        if n % 300 == 0: print(path, n, '/', n1, flush=True)
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'timeline': build_timeline()
    elif cmd == 'render': render(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
    elif cmd == 'still':
        TL = load_tl(); CH = caption_chunks(TL['words'])
        for t in sys.argv[2].split(','):
            frame(float(t), TL, CH).save(S + 'prev/prev_%s.jpg' % t, quality=85)
