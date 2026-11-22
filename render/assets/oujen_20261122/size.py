"""OUJ EN 20261122 — "5 size facts that sound fake" — frame renderer (silent mp4).
usage: python3 size.py out.mp4 | python3 size.py prev t1 t2 ..."""
import json, math, os, sys, random, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(D, '..', '..'))
FONTS = os.path.join(ROOT, 'fonts') + '/'
def F(name, s): return ImageFont.truetype(FONTS + name, s)
FB, FX, FI = 'InterDisplay-Black.otf', 'InterDisplay-ExtraBold.otf', 'Inter-Bold.otf'
GOLD = (233, 185, 73); CREAM = (255, 246, 228); BG = (6, 10, 26); MUTED = (170, 180, 205)
BLUE = (70, 150, 255); RED = (226, 76, 76); TEAL = (64, 214, 230); GREEN = (98, 200, 120); ORANGE = (240, 140, 60)
WATER = (16, 44, 86); LANDC = (44, 62, 104); AFR = (196, 140, 60)
OFF = 0.35; TEMPO = float(os.environ.get('TEMPO', '1.0'))
WORK = os.environ.get('OUJ_WORK', '/home/claude/ouj22')

# ---------- timing ----------
SEG = json.load(open(os.path.join(D, 'segs.json')))['segments']
for s in SEG: s['s'] = s['s'] / TEMPO + OFF; s['e'] = s['e'] / TEMPO + OFF
SIL = []
if os.path.exists(os.path.join(D, 'sil.txt')):
    for line in open(os.path.join(D, 'sil.txt')):
        a, b = line.split(); SIL.append((float(a) + OFF, float(b) + OFF))
WORDS = []
for s in SEG:
    sents = [x for x in re.split(r'(?<=[.?!])\s+', s['text']) if x]
    m = []
    for x in sents:
        if m and len(m[-1].split()) == 1: m[-1] = m[-1] + ' ' + x
        else: m.append(x)
    sents = m
    inner = [(a, b) for a, b in SIL if a > s['s'] + 0.15 and b < s['e'] - 0.15]
    if len(inner) >= len(sents) - 1 and len(sents) > 1:
        pick = sorted(sorted(inner, key=lambda g: -(g[1] - g[0]))[:len(sents) - 1])
        bounds = [s['s']] + [x for g in pick for x in g] + [s['e']]
        spans = [(bounds[2 * i], bounds[2 * i + 1]) for i in range(len(sents))]
    else:
        L = [len(x) for x in sents]; tot = sum(L); t = s['s']; spans = []
        for l in L:
            d = (s['e'] - s['s']) * l / tot; spans.append((t, t + d)); t += d
    for sent, (a, b) in zip(sents, spans):
        ws = sent.split(); L = [len(w) + 2 for w in ws]; tot = sum(L); t = a
        for w, l in zip(ws, L):
            d = (b - a) * l / tot; WORDS.append((w, t, t + d)); t += d
VOICE_END = SEG[-1]['e']
TOTAL = round(VOICE_END + 0.8, 2)
FS = [SEG[i]['s'] - 0.15 for i in range(1, 7)]
FACTS = [(FS[i], FS[i + 1]) for i in range(5)]
QA = (FS[5], VOICE_END + 0.05)
def wt(seg, word):
    """time of first word in segment seg containing `word`"""
    s = SEG[seg]
    for w, a, b in WORDS:
        if a >= s['s'] - 0.01 and a <= s['e'] and word.lower() in w.lower(): return a
    return s['s']

# ---------- helpers ----------
def ease(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
def eob(t):
    t = min(max(t, 0), 1); c = 1.70158; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def win(t, a, b, fi=0.35, fo=0.35): return ease((t - a) / fi) * (1 - ease((t - b + fo) / fo))
def mix(c1, c2, k): return tuple(int(lerp(x, y, k)) for x, y in zip(c1, c2))

rng = random.Random(7)
STARS = [(rng.random() * W, rng.random() * H, rng.random()) for _ in range(200)]
_g = np.linspace(0, 1, H)[:, None, None]
_BG = Image.fromarray(np.broadcast_to(np.array(BG, np.float32) + _g * np.array([10, 18, 40], np.float32), (H, W, 3)).clip(0, 255).astype(np.uint8))
def background(t):
    im = _BG.copy(); d = ImageDraw.Draw(im)
    for x, y, b in STARS:
        y2 = (y + t * 14 * b) % H
        a = int(60 + 110 * b * (0.6 + 0.4 * math.sin(t * 2 + x)))
        d.point((x, y2), fill=(a, a, min(255, a + 25)))
    return im

def text_c(im, txt, y, font, fill=CREAM, alpha=1.0, spacing=10, x=None, scale=1.0, stroke=4):
    if alpha <= 0.01: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bb = d.multiline_textbbox((0, 0), txt, font=font, align='center', spacing=spacing)
    tw = bb[2] - bb[0]; cx = W / 2 if x is None else x; a = int(255 * min(1, alpha))
    d.multiline_text((cx - tw / 2 - bb[0] + 4, y + 6), txt, font=font, fill=(0, 0, 0, int(a * .6)), align='center', spacing=spacing)
    d.multiline_text((cx - tw / 2 - bb[0], y), txt, font=font, fill=fill + (a,), align='center', spacing=spacing,
                     stroke_width=stroke, stroke_fill=(0, 0, 0, int(a * .85)))
    if abs(scale - 1) > 0.002:
        cy = y + (bb[3] - bb[1]) / 2
        ov = ov.resize((int(W * scale), int(H * scale)), Image.BILINEAR)
        im.paste(ov, (int(cx - cx * scale), int(cy - cy * scale)), ov)
    else:
        im.paste(ov, (0, 0), ov)

def panel(im, box, alpha, r=32, col=(10, 16, 38), op=215, border=None, bw=3):
    if alpha <= 0.01: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, r, fill=col + (int(op * alpha),), outline=(border + (int(255 * alpha),)) if border else None, width=bw)
    im.paste(ov, (0, 0), ov)

def tag(im, txt, x, y, col, alpha, f=None, tc=(255, 255, 255)):
    if alpha <= 0.01: return
    f = f or F(FI, 40); s = eob(alpha) if alpha < 1 else 1
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bb = d.textbbox((0, 0), txt, font=f); w = (bb[2] - bb[0]); h = bb[3] - bb[1]
    pw, ph = (w / 2 + 22) * s, (h / 2 + 16) * s
    d.rounded_rectangle([x - pw, y - ph, x + pw, y + ph], int(18 * s) + 1, fill=col + (int(235 * alpha),))
    if s > 0.6: d.text((x - w / 2 - bb[0], y - h / 2 - bb[1]), txt, font=f, fill=tc + (int(255 * alpha),))
    im.paste(ov, (0, 0), ov)

def chip(im, txt, y, alpha, x=None):
    if alpha <= 0.01: return
    f = F(FI, 30); cx = W / 2 if x is None else x
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bb = d.textbbox((0, 0), txt, font=f); w = bb[2] - bb[0]
    d.rounded_rectangle([cx - w / 2 - 20, y, cx + w / 2 + 20, y + 50], 25, fill=(255, 255, 255, int(26 * alpha)), outline=(255, 255, 255, int(70 * alpha)))
    d.text((cx - w / 2 - bb[0], y + 8), txt, font=f, fill=(215, 222, 238, int(255 * alpha)))
    im.paste(ov, (0, 0), ov)

def headline(im, t, a, b, txt, y=250, size=84, fill=CREAM):
    al = win(t, a, b, 0.3, 0.3)
    if al > 0: text_c(im, txt, y, F(FB, size), fill=fill, alpha=al, spacing=12, scale=lerp(1.2, 1.0, eob((t - a) / 0.45)))

# ---------- geo ----------
GEO = {}
for f in json.load(open(os.path.join(D, 'geo.json'))):
    GEO.setdefault(f['a3'], []).append(f)
CONT = {}
for code, fl in GEO.items():
    for f in fl: CONT[code] = f['cont']
def rings(code, minpts=8, bbox=None):
    out = []
    for f in GEO[code]:
        polys = f['coordinates'] if f['type'] == 'MultiPolygon' else [f['coordinates']]
        for p in polys:
            r = np.array(p[0], float)
            if len(r) < minpts: continue
            if bbox and (r[:, 0].max() < bbox[0] or r[:, 0].min() > bbox[2] or r[:, 1].max() < bbox[1] or r[:, 1].min() > bbox[3]): continue
            out.append(r)
    return out
R = 6371.0
def laea(r, lon0, lat0):
    lam = np.radians(r[:, 0] - lon0); phi = np.radians(r[:, 1]); p0 = math.radians(lat0)
    k = np.sqrt(2 / (1 + math.sin(p0) * np.sin(phi) + math.cos(p0) * np.cos(phi) * np.cos(lam)))
    x = R * k * np.cos(phi) * np.sin(lam)
    y = R * k * (math.cos(p0) * np.sin(phi) - math.sin(p0) * np.cos(phi) * np.cos(lam))
    return np.stack([x, y], 1)
def merc(r, lon0):
    x = R * np.radians(r[:, 0] - lon0); y = R * np.log(np.tan(np.pi / 4 + np.radians(np.clip(r[:, 1], -85, 85)) / 2))
    return np.stack([x, y], 1)
def area_km2(xy):
    x, y = xy[:, 0], xy[:, 1]; return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
def shape(code, lon0, lat0, minpts=8, bbox=None, minarea=2000):
    rs = [laea(r, lon0, lat0) for r in rings(code, minpts, bbox)]
    return [r for r in rs if area_km2(r) > minarea]
def centroid(rs):
    A = sum(area_km2(r) for r in rs)
    cx = sum(area_km2(r) * r[:, 0].mean() for r in rs) / A; cy = sum(area_km2(r) * r[:, 1].mean() for r in rs) / A
    return np.array([cx, cy])
def recenter(rs):
    c = centroid(rs); return [r - c for r in rs]

AFRICA_CODES = [c for c, k in CONT.items() if k == 'Africa']
AFR_S = recenter([r for c in AFRICA_CODES for r in shape(c, 20, 3)])
USA_S = recenter(shape('USA', -98, 39, bbox=(-125, 24, -66, 50)))        # contiguous 48
CHN_S = recenter(shape('CHN', 104, 35))
IND_S = recenter(shape('IND', 79, 22))
GRL_LAEA = recenter(shape('GRL', -42, 72))
AUS_S = recenter(shape('AUS', 134, -25, bbox=(112, -40, 155, -10)))     # mainland (no Tasmania)
AUS_W = max(r[:, 0].max() for r in AUS_S) - min(r[:, 0].min() for r in AUS_S)

def poly(d, rs, cx, cy, sc, fill, outline=None, width=2, flip=True):
    for r in rs:
        p = np.stack([cx + r[:, 0] * sc, cy - r[:, 1] * sc], 1) if flip else r
        pts = [tuple(x) for x in p]
        if len(pts) > 2: d.polygon(pts, fill=fill, outline=outline, width=width)

def layer(im, fn, alpha):
    if alpha <= 0.01: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); fn(d)
    if alpha < 0.999: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * alpha)))
    im.paste(ov, (0, 0), ov)

def reveal_outline(d, rs, cx, cy, sc, k, col, width=5):
    """stroke draws itself: each ring up to fraction k"""
    for r in rs:
        p = np.stack([cx + r[:, 0] * sc, cy - r[:, 1] * sc], 1)
        n = max(2, int(len(p) * k))
        if k > 0: d.line([tuple(x) for x in p[:n]], fill=col, width=width, joint='curve')

# placement of 3 countries inside Africa (km offsets from Africa centroid, picked to sit inside the outline)
PLACE = {'USA': np.array([-100, 1200]), 'CHN': np.array([700, -1800]), 'IND': np.array([1700, 800])}
ROT = {'USA': 0, 'CHN': 90, 'IND': 90}
def rot(rs, deg):
    c, s_ = math.cos(math.radians(deg)), math.sin(math.radians(deg)); M = np.array([[c, -s_], [s_, c]]); return [r @ M.T for r in rs]

def progress(im, t):
    if t < FACTS[0][0] or t > QA[0]: return
    k = min(1, (t - FACTS[0][0]) / (QA[0] - FACTS[0][0])); idx = sum(1 for a, b in FACTS if t >= a)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([50, 96, W - 50, 196], 26, fill=(6, 10, 26, 190))
    d.rounded_rectangle([70, 112, W - 70, 122], 5, fill=(255, 255, 255, 50))
    d.rounded_rectangle([70, 112, 70 + (W - 140) * k, 122], 5, fill=GOLD + (255,))
    d.text((72, 140), 'SIZE FACTS THAT SOUND FAKE', font=F(FI, 30), fill=(205, 212, 230, 255))
    s = f'{idx:02d} / 05'; f = F(FB, 42); bb = d.textbbox((0, 0), s, font=f)
    d.text((W - 72 - (bb[2] - bb[0]), 134), s, font=f, fill=GOLD + (255,))
    im.paste(ov, (0, 0), ov)

def captions(im, t):
    if t > VOICE_END + 0.2: return
    cur = [i for i, (w, a, b) in enumerate(WORDS) if a - 0.05 <= t]
    if not cur: return
    i = cur[-1]
    chunks = []; c = []
    for j, (w, a, b) in enumerate(WORDS):
        c.append(j)
        if len(c) == 4 or w[-1] in '.?!,' or (j + 1 < len(WORDS) and WORDS[j + 1][1] - b > 0.25):
            chunks.append(c); c = []
    if c: chunks.append(c)
    ch = next(c for c in chunks if i in c)
    if t > WORDS[ch[-1]][2] + 0.35: return
    f = F(FB, 66); d0 = ImageDraw.Draw(im)
    widths = [d0.textbbox((0, 0), WORDS[j][0].upper(), font=f)[2] for j in ch]; sp = 22
    tot = sum(widths) + sp * (len(ch) - 1)
    if tot > W - 80:
        f = F(FB, 54); widths = [d0.textbbox((0, 0), WORDS[j][0].upper(), font=f)[2] for j in ch]; tot = sum(widths) + sp * (len(ch) - 1)
    x = (W - tot) / 2; y = 1430; fs = f.size
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for j, wd in zip(ch, widths):
        w, a, b = WORDS[j]; act = a - 0.05 <= t
        col = GOLD if (act and t < b + 0.05) else (CREAM if act else (200, 205, 220))
        pop = 1 + 0.12 * (1 - ease((t - a) / 0.18)) if act and t < a + 0.18 else 1
        ff = F(FB, int(fs * pop)) if pop != 1 else f
        d.text((x + 3, y + 5 - (pop - 1) * 30), w.upper(), font=ff, fill=(0, 0, 0, 150))
        d.text((x, y - (pop - 1) * 30), w.upper(), font=ff, fill=col + (255 if act else 150,), stroke_width=5, stroke_fill=(0, 0, 0, 230))
        x += wd + sp
    im.paste(ov, (0, 0), ov)

# ---------- scenes ----------
CY = 820
def africa_three(im, t, t0, a, sc=0.0405, cy=CY, show_counter=False, draw_k=1.0, fly=None):
    """Africa + USA/CHN/IND dropping in. fly: list of start times for each country."""
    cx = W / 2
    def base(d):
        if draw_k >= 1: poly(d, AFR_S, cx, cy, sc, AFR + (255,), (255, 225, 160, 255), 2)
        else:
            poly(d, AFR_S, cx, cy, sc, AFR + (int(255 * ease((draw_k - 0.6) / 0.4)),))
            reveal_outline(d, AFR_S, cx, cy, sc, min(1, draw_k / 0.75), (255, 225, 160, 255), 5)
    layer(im, base, a)
    cols = {'USA': BLUE, 'CHN': RED, 'IND': GREEN}; sh = {'USA': USA_S, 'CHN': CHN_S, 'IND': IND_S}
    shake = 0
    for i, code in enumerate(['USA', 'CHN', 'IND']):
        ts = fly[i] if fly else t0
        k = (t - ts) / 0.55
        if k <= 0: continue
        p = eob(k); off = PLACE[code]
        dy = (1 - ease(k)) * 900
        s = lerp(1.6, 1.0, p)
        rs = [(r * s) + off + np.array([0, dy / sc]) for r in rot(sh[code], ROT[code] * ease(k))]
        al = min(1, k * 2)
        layer(im, lambda d, rs=rs, code=code: poly(d, rs, cx, cy, sc, cols[code] + (235,), (255, 255, 255, 255), 3), a * al)
        if 0 < t - ts - 0.45 < 0.25: shake = max(shake, 1 - (t - ts - 0.45) / 0.25)
        lab = {'USA': 'USA', 'CHN': 'CHINA', 'IND': 'INDIA'}[code]
        lx, ly = cx + off[0] * sc, cy - off[1] * sc
        if k > 0.9: tag(im, lab, lx, ly, (12, 18, 40), a * win(t, ts + 0.5, 1e9), F(FB, 36), cols[code])
    return shake

def hook(im, t, a, t0):
    lt = t - t0
    sh = africa_three(im, t, t0, a, sc=0.083, cy=870, fly=[t0 + 0.35, t0 + 0.75, t0 + 1.15])
    text_c(im, 'THESE 3 GIANTS\nFIT INSIDE AFRICA', 215, F(FB, 92), fill=GOLD, alpha=a, spacing=14,
           scale=lerp(1.06, 1, eob(lt / 0.5)) if lt < 0.6 else 1)
    chip(im, '5 size facts that sound fake · #5 is the strangest', 1330, a)
    return sh

def bars(im, t, t0, a, rows, y0, vmax, unit, dec=1):
    """rows: (label, value, color). bars grow + counters."""
    for i, (lab, v, col) in enumerate(rows):
        k = ease((t - t0 - i * 0.25) / 1.1)
        y = y0 + i * 96
        panel(im, [60, y, W - 60, y + 80], a, r=22, col=(10, 16, 38), op=200)
        bw = (W - 640) * (v / vmax) * k
        layer(im, lambda d, y=y, bw=bw, col=col: d.rounded_rectangle([420, y + 16, 420 + max(bw, 4), y + 64], 14, fill=col + (255,)), a)
        ImageDraw.Draw(im).text((84, y + 24), lab, font=F(FB, 28 if len(lab) > 8 else 36), fill=CREAM)
        txt = f'{v * k:,.{dec}f}{unit}'
        f = F(FB, 38); bb = ImageDraw.Draw(im).textbbox((0, 0), txt, font=f)
        ImageDraw.Draw(im).text((min(420 + bw + 16, W - 80 - (bb[2] - bb[0])), y + 18), txt, font=f, fill=GOLD if i == 0 else CREAM,
                                stroke_width=3, stroke_fill=(0, 0, 0))

def fact1(im, t):
    a0, b0 = FACTS[0]; lt = t - a0; a = win(t, a0, b0)
    ta = wt(1, 'USA'); tc = wt(1, 'China'); ti = wt(1, 'India')
    sh = africa_three(im, t, a0, a, sc=0.068, cy=730, draw_k=ease(lt / 1.2), fly=[ta, tc, ti])
    tr = wt(1, 'room')
    if t > tr - 0.2:
        k = ease((t - tr + 0.2) / 0.8)
        left = 30.37 - 22.72
        tag(im, f'{left * k:.1f}M km² left over', W / 2, 1060, (20, 26, 50), win(t, tr - 0.2, b0), F(FB, 44), GOLD)
    bars(im, t, a0 + 0.6, a, [('AFRICA', 30.37, AFR), ('USA+CHINA+INDIA', 22.72, BLUE)], 1130, 31, 'M km²')
    headline(im, t, a0 + 0.1, b0, 'Africa > USA + China\n+ India combined', 225, 70)
    return sh

def fact2(im, t):
    a0, b0 = FACTS[1]; lt = t - a0; a = win(t, a0, b0)
    tm = wt(2, 'real')  # morph moment
    k = ease((t - tm + 0.1) / 1.4)
    # Mercator shapes (same scale for both) vs true-size LAEA (same scale)
    gm = [merc(r, -42) for r in rings('GRL')]; gm = [r for r in gm if area_km2(r) > 30000]
    am = [merc(r, 20) for c in AFRICA_CODES for r in rings(c)]; am = [r for r in am if area_km2(r) > 30000]
    cg = centroid(gm); ca = centroid(am)
    sc = 0.058
    gx, gy = W / 2 - 250, 790; ax, ay = W / 2 + 200, 820
    # simple morph: scale greenland from mercator size to true size (area ratio), keep its shape
    ratio = math.sqrt(sum(area_km2(r) for r in GRL_LAEA) / sum(area_km2(r) for r in gm))
    gs = lerp(1.0, ratio, k)
    ga = [(r - cg) * gs for r in gm]; aa = [(r - ca) for r in am]
    afr_true = AFR_S
    def draw(d):
        # Africa: morph Mercator -> LAEA is near-identical near equator; show the mercator version then true
        poly(d, aa if k < 0.5 else afr_true, ax, ay, sc * 0.9, AFR + (255,), (255, 225, 160, 255), 2)
        poly(d, ga, gx + 60 * k, gy - 160 * k, sc * 0.9, (230, 240, 255, 255), (140, 180, 230, 255), 2)
    layer(im, draw, a)
    tag(im, 'GREENLAND', gx + 60 * k, gy - 160 * k - lerp(330, 90, k), (40, 80, 160), win(t, a0 + 0.5, b0), F(FB, 38))
    tag(im, 'AFRICA', ax, ay - 300, (150, 95, 30), win(t, a0 + 0.7, b0), F(FB, 40))
    if k < 0.05:
        chip(im, 'Mercator map (most world maps)', 1265, a * win(t, a0 + 0.4, tm, 0.3, 0.2))
    if k > 0.3:
        n = 14 * ease((t - tm - 0.2) / 1.0)
        panel(im, [300, 1190, 780, 1320], win(t, tm + 0.3, b0), border=GOLD)
        text_c(im, f'{n:.0f}× bigger', 1200, F(FB, 84), fill=GOLD, alpha=win(t, tm + 0.3, b0))
    headline(im, t, a0 + 0.1, tm + 0.25, 'On the map:\nthe same size?', 225, 80)
    headline(im, t, tm + 0.1, b0, 'Real size:\nAfrica is 14× bigger', 225, 76, GOLD)
    chip(im, 'Africa 30.4M km² · Greenland 2.17M km²', 1340, a)

def moon(d, cx, cy, r, alpha=255):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(196, 198, 206, alpha), outline=(255, 255, 255, alpha), width=3)
    rr = random.Random(5)
    for _ in range(22):
        ang = rr.random() * 6.28; dist = rr.random() ** 0.7 * r * 0.82; s = r * (0.04 + rr.random() * 0.1)
        x, y = cx + math.cos(ang) * dist, cy + math.sin(ang) * dist
        d.ellipse([x - s, y - s, x + s, y + s], fill=(160, 162, 172, alpha), outline=(140, 142, 150, alpha))

def fact3(im, t):
    a0, b0 = FACTS[2]; lt = t - a0; a = win(t, a0, b0)
    sc = 0.21  # px per km
    cx, cy = W / 2, 800
    mk = ease((t - wt(3, 'Moon') + 0.1) / 0.9)
    def draw(d):
        poly(d, AUS_S, cx, cy, sc, (200, 120, 60, 255), (255, 210, 170, 255), 3)
    layer(im, draw, a)
    # moon slides in on top of Australia, half transparent
    if mk > 0:
        mr = 3474.8 / 2 * sc
        mx = lerp(W + mr + 40, cx, mk)
        layer(im, lambda d: moon(d, mx, cy, mr, 200), a)
        tag(im, 'MOON', mx, cy - mr + 60, (60, 64, 80), a * mk, F(FB, 40))
    # rulers
    x0, x1 = cx - AUS_W / 2 * sc, cx + AUS_W / 2 * sc
    rk = ease((t - wt(3, 'thousand') + 0.2) / 1.0)
    d = ImageDraw.Draw(im); yr = cy + 320
    if rk > 0:
        d.line([(x0, yr), (lerp(x0, x1, rk), yr)], fill=GOLD, width=8); d.line([(x0, yr - 22), (x0, yr + 22)], fill=GOLD, width=8)
        if rk >= 1: d.line([(x1, yr - 22), (x1, yr + 22)], fill=GOLD, width=8)
        text_c(im, f'AUSTRALIA  ≈{4000 * rk:,.0f} km', yr + 30, F(FB, 50), fill=GOLD, alpha=a)
    mk2 = ease((t - wt(3, 'versus') + 0.1) / 1.0)
    if mk2 > 0:
        mr = 3474.8 / 2 * sc; yr2 = yr + 115
        d.line([(cx - mr, yr2), (lerp(cx - mr, cx + mr, mk2), yr2)], fill=(200, 205, 220), width=8)
        d.line([(cx - mr, yr2 - 20), (cx - mr, yr2 + 20)], fill=(200, 205, 220), width=8)
        if mk2 >= 1: d.line([(cx + mr, yr2 - 20), (cx + mr, yr2 + 20)], fill=(200, 205, 220), width=8)
        text_c(im, f'MOON  {3475 * mk2:,.0f} km', yr2 + 28, F(FB, 46), fill=CREAM, alpha=a)
    headline(im, t, a0 + 0.1, b0, 'Australia is wider\nthan the Moon', 225, 82)
    chip(im, 'Same scale · Moon: NASA · Australia mainland', 1360, a)

def fact4(im, t):
    a0, b0 = FACTS[3]; lt = t - a0; a = win(t, a0, b0)
    sea = 1010; pxm = 0.05  # px per meter
    base_y = sea + 6000 * pxm  # sea floor y for Mauna Kea
    ek = ease((lt - 0.2) / 1.2)
    mkk = ease((t - wt(4, 'Measured') + 0.0) / 1.6)
    def draw(d):
        # water
        d.rectangle([0, sea, W, base_y + 30], fill=(20, 70, 130, 230))
        for i in range(10):
            xx = (i * 131 + t * 50) % (W + 200) - 100
            d.arc([xx, sea - 6, xx + 110, sea + 18], 200, 340, fill=(255, 255, 255, 90), width=3)
        d.rectangle([0, base_y + 30, W, base_y + 60], fill=(60, 50, 40, 255))
        # Everest (on land, at sea level baseline)
        eh = 8849 * pxm * ek; ex = 290
        d.polygon([(ex - 210, sea), (ex, sea - eh), (ex + 210, sea)], fill=(150, 150, 165, 255), outline=(240, 240, 255, 255))
        if eh > 120: d.polygon([(ex - 60, sea - eh + 120 * 1.0), (ex, sea - eh), (ex + 60, sea - eh + 120)], fill=(250, 250, 255, 255))
        # Mauna Kea from sea floor
        mh = 10210 * pxm * mkk; mx = 790
        if mh > 0:
            d.polygon([(mx - 260, base_y + 30), (mx, base_y + 30 - mh), (mx + 260, base_y + 30)], fill=(120, 72, 56, 255), outline=(255, 190, 160, 255))
    layer(im, draw, a)
    d = ImageDraw.Draw(im)
    text_c(im, 'sea level', sea - 50, F(FI, 30), fill=(170, 210, 255), alpha=a, x=W - 110, stroke=2)
    text_c(im, f'{8849 * ek:,.0f} m', 1080 - 8849 * pxm * ek - 0 if False else sea - 8849 * pxm * ek - 70, F(FB, 50), fill=CREAM, alpha=a, x=290)
    text_c(im, 'EVEREST', sea + 20, F(FB, 36), fill=CREAM, alpha=a, x=290)
    if mkk > 0:
        top = base_y + 30 - 10210 * pxm * mkk
        text_c(im, f'{10210 * mkk:,.0f} m', top - 75, F(FB, 56), fill=GOLD, alpha=a, x=790)
        text_c(im, 'MAUNA KEA', min(top + 90, base_y - 40), F(FB, 36), fill=CREAM, alpha=a * ease((mkk - 0.5) / 0.3), x=790)
        if mkk > 0.9: chip(im, '4,207 m above water · ~6,000 m below', 1250, a * ease((mkk - 0.9) / 0.1))
    headline(im, t, a0 + 0.1, b0, 'Everest is NOT\nthe tallest mountain', 225, 80)

def fact5(im, t):
    a0, b0 = FACTS[4]; lt = t - a0; a = win(t, a0, b0)
    # view centred on 180° meridian, longitudes shifted to [0,360)
    lon0, lat0 = 193, 61; sc = 0.2
    def shift(r):
        r = r.copy(); r[:, 0] = np.where(r[:, 0] < 0, r[:, 0] + 360, r[:, 0]); return r
    zk = ease(lt / 1.6)
    scz = lerp(0.1, sc, zk)
    def P(r):
        return laea(shift(r), lon0, lat0)
    def draw(d):
        d.rectangle([0, 0, W, H], fill=WATER + (255,))
        for code, col in (('RUS', (110, 60, 60)), ('CAN', (70, 80, 110)), ('USA', (54, 96, 170))):
            bbox = (-180, 45, 180, 80) if code != 'CAN' else (-145, 45, -100, 80)
            for r in rings(code, 4, bbox if code != 'RUS' else None):
                rr = shift(r)
                if code == 'RUS' and rr[:, 0].max() < 120: continue
                if code == 'USA' and not ((rr[:, 1] > 50).all()): continue
                p = P(r); p = np.stack([W / 2 + p[:, 0] * scz, 820 - p[:, 1] * scz], 1)
                if p[:, 0].max() < -50 or p[:, 0].min() > W + 50: continue
                d.polygon([tuple(x) for x in p], fill=col + (255,), outline=(220, 230, 245, 160))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); draw(ImageDraw.Draw(ov))
    m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rounded_rectangle([30, 360, W - 30, 1330], 40, fill=int(255 * a))
    al = Image.fromarray((np.array(ov.getchannel('A'), np.float32) * np.array(m, np.float32) / 255).astype(np.uint8)); ov.putalpha(al)
    im.paste(ov, (0, 0), ov)
    d = ImageDraw.Draw(im)
    # 180° line draws itself
    lk = ease((t - wt(5, 'eastern') + 0.6) / 0.9)
    if lk > 0:
        lats = np.linspace(48, lerp(48, 74, lk), 50)
        pp = laea(np.stack([np.full_like(lats, 180.0), lats], 1), lon0, lat0)
        pts = [(W / 2 + x * scz, 820 - y * scz) for x, y in pp]
        for i in range(0, len(pts) - 1, 2): d.line([pts[i], pts[i + 1]], fill=(255, 255, 255), width=6)
        pm = pts[len(pts) // 3]; tag(im, '180° LINE', pm[0] - 120, pm[1], (30, 30, 50), lk, F(FB, 34), GOLD)
    def pin(lon, lat, txt, col, ts, dy=-70, dx=0):
        k = (t - ts) / 0.4
        if k <= 0: return
        p = laea(np.array([[lon % 360, lat]]), lon0, lat0)[0]; x, y = W / 2 + p[0] * scz, 820 - p[1] * scz
        rr = 10 + 12 * eob(min(1, k)); d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col, outline='white', width=4)
        ph = ((t - ts) * 1.3) % 1; r2 = 20 + 50 * ph
        d.ellipse([x - r2, y - r2, x + r2, y + r2], outline=col, width=4)
        tag(im, txt, min(max(x + dx, 190), W - 190), y + dy, col, min(1, k) * a, F(FB, 34))
    pin(-156.79, 71.39, 'MOST NORTHERN', TEAL, wt(5, 'northern'))
    pin(-179.10, 51.25, 'MOST WESTERN', ORANGE, wt(5, 'western'), 90, 120)
    pin(179.77, 51.95, 'MOST EASTERN', GOLD, wt(5, 'eastern'), -90, -60)
    pa = laea(np.array([[208.0, 64.0]]), lon0, lat0)[0]
    tag(im, 'ALASKA (USA)', W / 2 + pa[0] * scz, 820 - pa[1] * scz, (40, 80, 160), win(t, a0 + 0.6, b0), F(FB, 40))
    tag(im, 'RUSSIA', 150, 640, (120, 50, 50), win(t, a0 + 0.9, b0), F(FB, 34))
    headline(im, t, a0 + 0.1, b0, 'North, West AND East\n— all in one state', 200, 68, GOLD)
    chip(im, 'The Aleutian Islands cross the 180° meridian', 1345, a)

def question(im, t):
    a0, b0 = QA; a = win(t, a0, b0 + 0.2, 0.3, 0.4)
    text_c(im, 'Which one did\nyou NOT believe?', 560, F(FB, 100), fill=GOLD, alpha=a, spacing=16, scale=lerp(1.2, 1, eob((t - a0) / .5)))
    text_c(im, 'Comment 1 · 2 · 3 · 4 · 5', 880, F(FX, 60), fill=CREAM, alpha=a)
    for i in range(5):
        p = eob(min(1, max(0, (t - a0 - 0.3 - i * 0.12) / 0.3)))
        if p > 0: tag(im, str(i + 1), 220 + i * 160, 1060, (30, 40, 80), a * min(1, p), F(FB, 60), GOLD)

def frame(t):
    im = background(t); sh = 0
    if t < FACTS[0][0] + 0.35:
        sh = hook(im, t, win(t, -1, FACTS[0][0] + 0.35, 0.3, 0.35), -0.2) or 0
    if FACTS[0][0] <= t < FACTS[0][1]: sh = fact1(im, t) or 0
    if FACTS[1][0] <= t < FACTS[1][1]: fact2(im, t)
    if FACTS[2][0] <= t < FACTS[2][1]: fact3(im, t)
    if FACTS[3][0] <= t < FACTS[3][1]: fact4(im, t)
    if FACTS[4][0] <= t < FACTS[4][1]: fact5(im, t)
    if QA[0] <= t < QA[1] + 0.2: question(im, t)
    if t >= TOTAL - 0.6:
        hook(im, t, ease((t - (TOTAL - 0.6)) / 0.45), TOTAL + 0.2)
    if sh > 0:
        dx, dy = int(10 * sh * math.sin(t * 90)), int(8 * sh * math.cos(t * 77))
        im = im.transform(im.size, Image.AFFINE, (1, 0, dx, 0, 1, dy), fillcolor=BG)
    progress(im, t)
    captions(im, t)
    return im.convert('RGB')

def rend(i):
    frame(i / FPS).save(f'{WORK}/frames/f{i:05d}.jpg', quality=92)

if __name__ == '__main__':
    os.makedirs(WORK, exist_ok=True)
    if sys.argv[1] == 'prev':
        for tt in sys.argv[2:]:
            frame(float(tt)).save(f'{WORK}/p_{tt}.jpg', quality=85)
    else:
        os.makedirs(f'{WORK}/frames', exist_ok=True)
        N = int(TOTAL * FPS)
        with Pool(os.cpu_count()) as p: p.map(rend, range(N), chunksize=8)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{WORK}/frames/f%05d.jpg',
                        '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', sys.argv[1]], check=True)
        print('TOTAL', TOTAL, 'frames', N)
