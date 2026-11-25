"""OUJ EN 20261125 — "5 map facts that sound fake" — frame renderer (silent mp4).
usage: python3 mapfacts.py out.mp4 | python3 mapfacts.py prev t1 t2 ..."""
import json, math, os, sys, random, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
R = '/home/claude/rw/render/'
FONTS = R + 'fonts/'
def F(name, s): return ImageFont.truetype(FONTS + name, s)
FB, FX, FI = 'InterDisplay-Black.otf', 'InterDisplay-ExtraBold.otf', 'Inter-Bold.otf'
GOLD = (233, 185, 73); CREAM = (255, 246, 228); BG = (6, 10, 26); MUTED = (170, 180, 205)
BLUE = (70, 150, 255); RED = (226, 76, 76); TEAL = (64, 214, 230); GREEN = (98, 200, 120)
WATER = (18, 48, 92); LANDC = (44, 62, 104)
OFF = 0.35; TEMPO = float(os.environ.get('TEMPO', '1.1'))

# ---------- timing ----------
SEG = json.load(open(R + 'out/oujen_20261125_mapfacts_voice_segs.json'))['segments']
for s in SEG: s['s'] = s['s'] / TEMPO + OFF; s['e'] = s['e'] / TEMPO + OFF
SIL = []
for line in open(os.path.join(D, 'sil.txt')):
    a, b = line.split(); SIL.append((float(a) + OFF, float(b) + OFF))
WORDS = []  # (word, t0, t1)
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
QA = (FS[5], VOICE_END + 0.35)

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

def flag(d, kind, x, y, w, h):
    if kind == 'ESP':
        d.rectangle([x, y, x + w, y + h], fill=(170, 21, 27)); d.rectangle([x, y + h / 4, x + w, y + 3 * h / 4], fill=(241, 191, 0))
    elif kind == 'FRA':
        d.rectangle([x, y, x + w / 3, y + h], fill=(0, 35, 149)); d.rectangle([x + w / 3, y, x + 2 * w / 3, y + h], fill=(255, 255, 255))
        d.rectangle([x + 2 * w / 3, y, x + w, y + h], fill=(237, 41, 57))
    elif kind == 'DEU':
        for i, c in enumerate([(0, 0, 0), (221, 0, 0), (255, 206, 0)]): d.rectangle([x, y + i * h / 3, x + w, y + (i + 1) * h / 3], fill=c)
    elif kind == 'AUT':
        for i, c in enumerate([(200, 16, 46), (255, 255, 255), (200, 16, 46)]): d.rectangle([x, y + i * h / 3, x + w, y + (i + 1) * h / 3], fill=c)
    elif kind == 'NLD':
        for i, c in enumerate([(174, 28, 40), (255, 255, 255), (33, 70, 139)]): d.rectangle([x, y + i * h / 3, x + w, y + (i + 1) * h / 3], fill=c)
    elif kind == 'BEL':
        for i, c in enumerate([(0, 0, 0), (253, 218, 36), (239, 51, 64)]): d.rectangle([x + i * w / 3, y, x + (i + 1) * w / 3, y + h], fill=c)
    elif kind == 'CHE':
        s = h; x = x + (w - s) / 2; d.rectangle([x, y, x + s, y + s], fill=(218, 41, 28))
        a, b = s * 6 / 32, s * 26 / 32; c1, c2 = s * 13 / 32, s * 19 / 32
        d.rectangle([x + c1, y + a, x + c2, y + b], fill='white'); d.rectangle([x + a, y + c1, x + b, y + c2], fill='white')
    d.rectangle([x, y, x + w, y + h], outline=(255, 255, 255), width=2) if kind != 'CHE' else None

def flag_card(im, kind, x, y, w, alpha, label=None):
    if alpha <= 0.01: return
    s = eob(alpha) if alpha < 1 else 1; ww, hh = w * s, w * 2 / 3 * s
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    flag(d, kind, x - ww / 2, y - hh / 2, ww, hh)
    ov.putalpha(ov.getchannel('A').point(lambda v: int(v * min(1, alpha))))
    im.paste(ov, (0, 0), ov)
    if label: text_c(im, label, y + hh / 2 + 14, F(FI, 34), alpha=alpha, x=x, stroke=3)

def counter(v, dec=0):
    return f'{v:,.{dec}f}'

# ---------- layout pieces ----------
def progress(im, t):
    if t < FACTS[0][0] or t > QA[0]: return
    k = min(1, (t - FACTS[0][0]) / (QA[0] - FACTS[0][0])); idx = sum(1 for a, b in FACTS if t >= a)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([50, 96, W - 50, 196], 26, fill=(6, 10, 26, 190))
    d.rounded_rectangle([70, 112, W - 70, 122], 5, fill=(255, 255, 255, 50))
    d.rounded_rectangle([70, 112, 70 + (W - 140) * k, 122], 5, fill=GOLD + (255,))
    d.text((72, 140), 'MAP FACTS THAT SOUND FAKE', font=F(FI, 30), fill=(205, 212, 230, 255))
    s = f'{idx:02d} / 05'; f = F(FB, 42); bb = d.textbbox((0, 0), s, font=f)
    d.text((W - 72 - (bb[2] - bb[0]), 134), s, font=f, fill=GOLD + (255,))
    im.paste(ov, (0, 0), ov)

def headline(im, t, a, b, txt, y=250, size=84, fill=CREAM):
    al = win(t, a, b, 0.3, 0.3)
    if al <= 0: return
    f = F(FB, size); dd = ImageDraw.Draw(im)
    while dd.multiline_textbbox((0, 0), txt, font=f, spacing=12)[2] > 680 and size > 50:
        size -= 2; f = F(FB, size)
    text_c(im, txt, y, f, fill=fill, alpha=al, spacing=12, scale=lerp(1.08, 1.0, eob((t - a) / 0.45)))

def captions(im, t):
    if t > VOICE_END + 0.2: return
    cur = [i for i, (w, a, b) in enumerate(WORDS) if a - 0.05 <= t]
    if not cur: return
    i = cur[-1]
    # chunks of up to 4 words, never across sentence ends
    chunks = []; c = []
    for j, (w, a, b) in enumerate(WORDS):
        c.append(j)
        if len(c) == 4 or w[-1] in '.?!,' or (j + 1 < len(WORDS) and WORDS[j + 1][1] - b > 0.25):
            chunks.append(c); c = []
    if c: chunks.append(c)
    ch = next(c for c in chunks if i in c)
    if t > WORDS[ch[-1]][2] + 0.35: return
    fs = 66; f = F(FB, fs); d0 = ImageDraw.Draw(im); sp = 22
    while True:
        widths = [d0.textbbox((0, 0), WORDS[j][0].upper(), font=f)[2] for j in ch]
        tot = sum(widths) + sp * (len(ch) - 1)
        if tot <= W - 100 or fs <= 40: break
        fs -= 4; f = F(FB, fs)
    x = (W - tot) / 2; y = 1430
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for j, wd in zip(ch, widths):
        w, a, b = WORDS[j]; act = a - 0.05 <= t
        col = GOLD if (act and t < b + 0.05) else (CREAM if act else (200, 205, 220))
        pop = 1 + 0.12 * (1 - ease((t - a) / 0.18)) if act and t < a + 0.18 else 1
        ff = F(FB, int(fs * pop)) if pop != 1 else f
        xo = x - (d.textbbox((0, 0), w.upper(), font=ff)[2] - wd) / 2
        d.text((xo + 3, y + 5 - (pop - 1) * 30), w.upper(), font=ff, fill=(0, 0, 0, 150))
        d.text((xo, y - (pop - 1) * 30), w.upper(), font=ff, fill=col + (255 if act else 150,), stroke_width=5, stroke_fill=(0, 0, 0, 230))
        x += wd + sp
    im.paste(ov, (0, 0), ov)


# ---------- geo ----------
GEO = {}
for e in json.load(open(R + 'out/oujen_20261122_geo_geo.json')):
    rs = [np.array(p[0]) for p in e['coordinates']] if e['type'] == 'MultiPolygon' else [np.array(e['coordinates'][0])]
    GEO.setdefault(e['a3'], []).extend(rs)
ALL = [(c, r) for c, rs in GEO.items() for r in rs]
def subset(box, codes=None):
    out = []
    for c, r in ALL:
        if codes and c not in codes: continue
        if r[:, 0].max() < box[0] or r[:, 0].min() > box[2] or r[:, 1].max() < box[1] or r[:, 1].min() > box[3]: continue
        out.append((c, r))
    return out
US_W = subset((-135, 20, -95, 55))
CANP = subset((-145, 40, -50, 85), ['CAN', 'USA', 'GRL'])

def proj(cam, cy0):
    lon0, lat0, sc = cam; k = math.cos(math.radians(lat0))
    return lambda r: np.stack([W / 2 + (np.asarray(r)[:, 0] - lon0) * sc * k, cy0 - (np.asarray(r)[:, 1] - lat0) * sc], 1)

def mapdraw(im, parts, cam, colors, alpha, cy0=820, water=WATER, edge=(220, 230, 245)):
    P = proj(cam, cy0)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, H], fill=water + (255,))
    for c, r in parts:
        p = P(r)
        if p[:, 0].max() < -50 or p[:, 0].min() > W + 50 or p[:, 1].max() < -50 or p[:, 1].min() > H + 50: continue
        pts = [tuple(x) for x in p]
        if len(pts) > 2: d.polygon(pts, fill=colors.get(c, LANDC) + (255,), outline=edge + (140,))
    ov.putalpha(ov.getchannel('A').point(lambda v: int(v * alpha)))
    im.paste(ov, (0, 0), ov)
    return P

def dashed(d, p1, p2, col, w=5, dash=26, gap=16, k=1.0):
    L = math.hypot(p2[0] - p1[0], p2[1] - p1[1]) * k; s = 0
    ux, uy = (p2[0] - p1[0]) / max(1e-6, math.hypot(p2[0] - p1[0], p2[1] - p1[1])), (p2[1] - p1[1]) / max(1e-6, math.hypot(p2[0] - p1[0], p2[1] - p1[1]))
    while s < L:
        e = min(L, s + dash)
        d.line([(p1[0] + ux * s, p1[1] + uy * s), (p1[0] + ux * e, p1[1] + uy * e)], fill=col, width=w); s += dash + gap

def pin(im, x, y, col, a, label=None, lab_dy=-70, f=None, pulse_t=None):
    if a <= 0.01: return
    s = eob(a) if a < 1 else 1; d = ImageDraw.Draw(im)
    if pulse_t is not None:
        ph = pulse_t % 1; rr = 16 + 50 * ph
        d.ellipse([x - rr, y - rr, x + rr, y + rr], outline=mix(col, (6, 10, 26), ph), width=4)
    r = 15 * s; d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline=(255, 255, 255), width=4)
    if label: tag(im, label, x, y + lab_dy, (16, 22, 46), a, f or F(FB, 36), col)

# ---------- calendar (hook + fact 5) ----------
def day_card(im, x, y, dow, num, col, a, scale=1.0, cross=0.0, squash=1.0):
    if a <= 0.01: return
    w, h = 270 * scale, 330 * scale * squash
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); A = int(255 * a)
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], int(26 * scale), fill=(240, 236, 226, A))
    d.rounded_rectangle([x - w / 2, y - h / 2, x + w / 2, y - h / 2 + 78 * scale * squash], int(26 * scale), fill=col + (A,))
    d.rectangle([x - w / 2, y - h / 2 + 40 * scale * squash, x + w / 2, y - h / 2 + 78 * scale * squash], fill=col + (A,))
    if squash > 0.35:
        f = F(FB, int(40 * scale)); bb = d.textbbox((0, 0), dow, font=f)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y - h / 2 + 14 * scale * squash), dow, font=f, fill=(255, 255, 255, A))
        f = F(FB, int(150 * scale * squash)); bb = d.textbbox((0, 0), num, font=f)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y + 40 * scale * squash - (bb[3] - bb[1]) / 2 - bb[1]), num, font=f, fill=(20, 24, 40, A))
        f = F(FI, int(30 * scale)); bb = d.textbbox((0, 0), 'DEC 2011', font=f)
        d.text((x - (bb[2] - bb[0]) / 2 - bb[0], y + h / 2 - 50 * scale * squash), 'DEC 2011', font=f, fill=(90, 96, 120, A))
    if cross > 0:
        c1 = ease(cross / 0.5); c2 = ease((cross - 0.5) / 0.5); m = 18 * scale
        x0, y0, x1, y1 = x - w / 2 + m, y - h / 2 + m, x + w / 2 - m, y + h / 2 - m
        d.line([(x0, y0), (lerp(x0, x1, c1), lerp(y0, y1, c1))], fill=(220, 30, 40, A), width=int(20 * scale))
        if c2 > 0: d.line([(x1, y0), (lerp(x1, x0, c2), lerp(y0, y1, c2))], fill=(220, 30, 40, A), width=int(20 * scale))
    im.paste(ov, (0, 0), ov)

def calendar(im, t, a, lt, cy=820, mode='hook'):
    """3 day cards; Friday 30 gets crossed, then squeezed out (mode fact)."""
    if mode == 'hook':
        cr = 1.0 if lt > 0.25 else ease(lt / 0.25); sq = 1.0; gapk = 0
    else:
        cr = (lt - 0.9) / 0.6; sq = 1 - ease((lt - 1.9) / 0.6); gapk = ease((lt - 1.9) / 0.6)
    shake = 8 * math.sin(lt * 50) * (1 - ease((lt - (0.3 if mode == 'hook' else 1.5)) / 0.3)) if cr > 0.8 else 0
    sp = lerp(300, 160, gapk)
    day_card(im, W / 2 - sp, cy + 8 * math.sin(lt * 3 + 1), 'THU', '29', (60, 90, 160), a)
    day_card(im, W / 2 + sp, cy + 8 * math.sin(lt * 3 + 2.5), 'SAT', '31', (60, 90, 160), a)
    if sq > 0.02:
        day_card(im, W / 2 + shake, cy, 'FRI', '30', (200, 50, 60), a, scale=1.08 + 0.03 * math.sin(lt * 5), cross=max(0, cr) * 1.0, squash=sq)

# ---------- scenes ----------
def hook(im, t, a, t0):
    lt = t - t0
    calendar(im, t, a, lt, cy=900 + 10 * math.sin(lt * 2.4), mode='hook')
    text_c(im, 'THIS DAY\nNEVER\nHAPPENED', 215, F(FB, 108), fill=GOLD, alpha=a, spacing=12,
           scale=lerp(1.05, 1, eob(lt / 0.5)) if lt < 0.6 else 1)
    chip(im, '5 map facts that sound fake · #5 is the strangest', 1150, a)

def fact1(im, t):
    a0, b0 = FACTS[0]; lt = t - a0; a = win(t, a0, b0)
    z = ease(lt / 1.2)
    cam = (lerp(-100, -119.0, z), lerp(39, 36.6, z), 14 * math.exp(math.log(130 / 14) * z))
    P = mapdraw(im, US_W, cam, {'USA': (54, 96, 170), 'MEX': (70, 80, 110), 'CAN': (70, 80, 110)}, a, cy0=900)
    d = ImageDraw.Draw(im)
    sl = ease((lt - 0.8) / 0.6)
    if sl > 0:  # CA/NV state line (schematic)
        pts = P(np.array([[-120.0, 42.0], [-120.0, 39.0], [-114.63, 35.0]]))
        L1 = math.dist(pts[0], pts[1]); L2 = math.dist(pts[1], pts[2]); tot = (L1 + L2) * sl
        dashed(d, pts[0], pts[1], (230, 235, 245), 4, 18, 12, min(1, tot / L1))
        if tot > L1: dashed(d, pts[1], pts[2], (230, 235, 245), 4, 18, 12, (tot - L1) / L2)
        tag(im, 'NEVADA', *P(np.array([[-117.0, 39.3]]))[0], (16, 22, 46), sl, F(FB, 34), CREAM)
        tag(im, 'CALIFORNIA', *P(np.array([[-119.6, 36.9]]))[0], (16, 22, 46), sl, F(FB, 34), CREAM)
    reno = P(np.array([[-119.8138, 39.5296]]))[0]; la = P(np.array([[-118.24, 34.05]]))[0]
    pa = ease((lt - 0.9) / 0.3); pb = ease((lt - 1.1) / 0.3)
    ml = ease((lt - 1.3) / 0.6)
    if ml > 0:  # meridians drawing themselves
        dashed(d, (reno[0], reno[1]), (reno[0], 1330), GOLD, 5, 22, 14, ml)
        dashed(d, (la[0], la[1]), (la[0], 420), TEAL, 5, 22, 14, ml)
        ar = ease((lt - 1.8) / 0.5)
        if ar > 0:
            y = 1060; x1 = la[0]; x0 = lerp(la[0], reno[0], ar)
            d.line([(x1, y), (x0, y)], fill=GOLD, width=9)
            d.polygon([(x0 - 6, y), (x0 + 26, y - 20), (x0 + 26, y + 20)], fill=GOLD)
            tag(im, 'FARTHER WEST', (reno[0] + la[0]) / 2 - 40, y - 58, (40, 30, 10), ar, F(FB, 34), GOLD)
    pin(im, reno[0], reno[1], GOLD, pa, None, pulse_t=lt * 1.2 if lt > 1.3 else None)
    tag(im, 'RENO', reno[0] - 110, reno[1] + 10, (16, 22, 46), pa, F(FB, 36), GOLD)
    pin(im, la[0], la[1], TEAL, pb, None)
    tag(im, 'LOS ANGELES', la[0] + 170, la[1] - 90, (16, 22, 46), pb, F(FB, 36), TEAL)
    lonr = lerp(0, 119.8, ease((lt - 1.5) / 0.9)); lonl = lerp(0, 118.2, ease((lt - 1.5) / 0.9))
    if lt > 1.5:
        panel(im, [60, 1240, W - 60, 1330], win(t, a0 + 1.5, b0), border=GOLD)
        text_c(im, f'Reno {lonr:.1f}°W   ·   L.A. {lonl:.1f}°W', 1256, F(FB, 46), fill=CREAM, alpha=win(t, a0 + 1.5, b0))
    headline(im, t, a0 + 0.1, b0, 'Reno is WEST\nof Los Angeles', 230, 84)
    chip(im, 'Map: Natural Earth · state line schematic', 1345, a)

def fact2(im, t):
    a0, b0 = FACTS[1]; lt = t - a0; a = win(t, a0, b0)
    PX = 300  # px per km
    sc = PX * math.sqrt(3.41); sm = PX * math.sqrt(2.08)
    g = eob((lt - 0.2) / 0.5); m = eob((lt - 0.6) / 0.5)
    cx_c, cy = 540, 820
    slide = ease((lt - 2.2) / 0.9)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); A = int(255 * a)
    # Central Park square (to scale), shifts left at start then back to centre for fit
    cpx = lerp(330, 540, slide); h = sc / 2 * g
    if h > 2:
        d.rounded_rectangle([cpx - h, cy - h, cpx + h, cy + h], 18, fill=(46, 140, 72, A), outline=(170, 240, 180, A), width=4)
        for i in range(14):  # tree dots
            rr = random.Random(i); tx = cpx - h + 30 + rr.random() * (2 * h - 60); ty = cy - h + 30 + rr.random() * (2 * h - 60)
            d.ellipse([tx - 12, ty - 12, tx + 12, ty + 12], fill=(30, 105, 52, A))
    # Monaco square, flag colours
    mx = lerp(800, 540, slide); my = lerp(cy + 120, cy, slide); hm = sm / 2 * m
    if hm > 2:
        d.rectangle([mx - hm, my - hm, mx + hm, my], fill=(206, 17, 38, A))
        d.rectangle([mx - hm, my, mx + hm, my + hm], fill=(250, 250, 250, A))
        d.rectangle([mx - hm, my - hm, mx + hm, my + hm], outline=(255, 255, 255, A), width=4)
    im.paste(ov, (0, 0), ov)
    if slide < 0.5:
        tag(im, 'CENTRAL PARK', cpx, cy - sc / 2 - 40, (30, 110, 60), win(t, a0 + 0.4, a0 + 2.6), F(FB, 34))
        tag(im, 'MONACO', mx, my - sm / 2 - 40, (200, 30, 50), win(t, a0 + 0.8, a0 + 2.6), F(FB, 34))
    ca = 3.41 * ease((lt - 0.4) / 1.2); ma = 2.08 * ease((lt - 0.8) / 1.2)
    panel(im, [60, 1170, 520, 1320], win(t, a0 + 0.4, b0), border=GREEN)
    text_c(im, f'{ca:.2f} km²', 1180, F(FB, 64), fill=(150, 235, 160), alpha=win(t, a0 + 0.4, b0), x=290)
    text_c(im, 'Central Park, NYC', 1262, F(FI, 30), fill=MUTED, alpha=win(t, a0 + 0.4, b0), x=290, stroke=2)
    panel(im, [560, 1170, 1020, 1320], win(t, a0 + 0.8, b0), border=RED)
    text_c(im, f'{ma:.2f} km²', 1180, F(FB, 64), fill=(255, 150, 150), alpha=win(t, a0 + 0.8, b0), x=790)
    text_c(im, 'Monaco (a country)', 1262, F(FI, 30), fill=MUTED, alpha=win(t, a0 + 0.8, b0), x=790, stroke=2)
    if slide > 0.95:
        tag(im, 'FITS INSIDE!', 540, cy - sc / 2 - 45, (40, 30, 10), win(t, a0 + 3.1, b0), F(FB, 44), GOLD)
    headline(im, t, a0 + 0.1, b0, 'A country smaller\nthan a park', 230, 84)
    chip(im, 'Areas to scale · CIA World Factbook · Central Park Conservancy', 1345, a)

def _canada_points(n=900):
    from matplotlib.path import Path
    rings = sorted(GEO['CAN'], key=lambda r: -len(r))[:12]
    paths = [Path(r) for r in rings]
    rr = random.Random(5); pts = []
    while len(pts) < n:
        x = rr.uniform(-140, -55); y = rr.uniform(43, 70)
        if any(p.contains_point((x, y)) for p in paths): pts.append((x, y, rr.random()))
    return pts
CPTS = _canada_points()

def fact3(im, t):
    a0, b0 = FACTS[2]; lt = t - a0; a = win(t, a0, b0)
    z = ease(lt / 1.4)
    cam = (lerp(-100, -96, z), lerp(55, 61, z), lerp(11, 17, z))
    P = mapdraw(im, CANP, cam, {'CAN': (150, 66, 66), 'USA': (50, 62, 96), 'GRL': (50, 62, 96)}, a, cy0=730)
    n = int(len(CPTS) * ease((lt - 0.6) / 2.2))
    if n:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        xy = P(np.array([(p[0], p[1]) for p in CPTS[:n]]))
        for i, (x, y) in enumerate(xy):
            age = (lt - 0.6) - i / len(CPTS) * 2.2; s = eob(min(1, age / 0.25)) if age < 0.25 else 1
            r = (3 + 4 * CPTS[i][2]) * s
            d.ellipse([x - r, y - r, x + r, y + r], fill=(110, 190, 255, int(230 * a)))
        im.paste(ov, (0, 0), ov)
    tag(im, 'CANADA', *P(np.array([[-105, 57]]))[0], (16, 22, 46), win(t, a0 + 0.5, b0), F(FB, 44), CREAM)
    # pie chart 62 %
    pa = win(t, a0 + 1.6, b0); k = ease((lt - 1.8) / 1.4)
    panel(im, [60, 1110, W - 60, 1330], pa, border=(110, 190, 255))
    if pa > 0.01:
        d = ImageDraw.Draw(im); cx, cy, r = 200, 1220, 85
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(60, 70, 100))
        if k > 0: d.pieslice([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * 0.62 * k, fill=(110, 190, 255))
        text_c(im, f'{62 * k:.0f}%', 1128, F(FB, 100), fill=(140, 205, 255), alpha=pa, x=470)
        text_c(im, 'of the world’s lakes', 1248, F(FI, 34), fill=MUTED, alpha=pa, x=470, stroke=2)
        nl = int(900 * ease((lt - 2.2) / 1.4)) * 1000
        text_c(im, f'{nl:,}', 1140, F(FB, 60), fill=GOLD, alpha=pa, x=850)
        text_c(im, 'lakes (almost)', 1220, F(FI, 32), fill=MUTED, alpha=pa, x=850, stroke=2)
    headline(im, t, a0 + 0.1, b0, 'Canada vs\nevery other country', 220, 84)
    chip(im, 'Lakes over 10 ha · HydroLAKES, Messager et al. 2016 · dots illustrative', 1345, a)

FR_ZONES = [(-176.2, -13.3, 'UTC+12', 'Wallis & Futuna'), (-149.4, -17.6, 'UTC−10', 'Tahiti'), (-140.0, -9.0, 'UTC−9:30', 'Marquesas'),
            (-134.9, -23.1, 'UTC−9', 'Gambier'), (-109.2, 10.3, 'UTC−8', 'Clipperton'), (-61.0, 14.6, 'UTC−4', 'Martinique'),
            (-53.0, 4.0, 'UTC−3', 'French Guiana'), (2.35, 48.85, 'UTC+1', 'Paris'), (45.1, -12.8, 'UTC+3', 'Mayotte'),
            (55.5, -21.1, 'UTC+4', 'Réunion'), (69.5, -49.3, 'UTC+5', 'Kerguelen'), (165.6, -21.3, 'UTC+11', 'New Caledonia')]
FR_CODES = {'FRA', 'PYF', 'NCL', 'WLF', 'SPM', 'ATF', 'BLM', 'MAF'}
_WM = None
def world_base():
    global _WM
    if _WM is None:
        im = Image.new('RGBA', (W, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, W - 1, 559], 30, fill=WATER + (255,))
        for c, r in ALL:
            if r[:, 1].max() < -60: continue
            pts = [(x * 3 + 540, 280 - y * 3) for x, y in r]
            if len(pts) > 2: d.polygon(pts, fill=((70, 120, 230) if c in FR_CODES else LANDC) + (255,))
        _WM = im
    return _WM

def fact4(im, t):
    a0, b0 = FACTS[3]; lt = t - a0; a = win(t, a0, b0)
    my = 470; mid = a0 + (b0 - a0) * 0.68
    wm = world_base().copy(); wm.putalpha(wm.getchannel('A').point(lambda v: int(v * a)))
    zoom = 1 + 0.04 * ease(lt / 4)
    if zoom != 1: wm = wm.resize((int(W * zoom), int(560 * zoom)), Image.BILINEAR)
    im.paste(wm, (int((W - wm.width) / 2), int(my - (wm.height - 560) / 2)), wm)
    def M(lon, lat): return (540 + (lon * 3) * zoom, my + 280 * zoom - lat * 3 * zoom + (0))
    n = 0
    for i, (lon, lat, z, nm) in enumerate(FR_ZONES):
        ti = 0.5 + i * 0.17; pa = ease((lt - ti) / 0.25)
        if pa > 0:
            n += 1; x, y = M(lon, lat)
            pin(im, x, y, GOLD if nm == 'Paris' else TEAL, pa * a, pulse_t=(lt * 1.5) if i == len([1 for q in range(12) if lt > 0.5 + q * 0.17]) - 1 else None)
    # clock labels ticker
    if n:
        lon, lat, z, nm = FR_ZONES[n - 1]
        tag(im, f'{z}  ·  {nm}', 540, my + 600, (16, 22, 46), a * (1 - win(t, mid - 0.2, b0 + 5, 0.25)), F(FB, 40), TEAL)
    text_c(im, f'{n}', 1100, F(FB, 150), fill=GOLD, alpha=a * (1 - win(t, mid, b0 + 5)), x=300)
    text_c(im, 'time zones', 1160, F(FX, 50), fill=CREAM, alpha=a * (1 - win(t, mid, b0 + 5)), x=640)
    if t > mid:  # bars France vs Russia
        al = win(t, mid, b0); k = ease((t - mid) / 0.8)
        for j, (nm, v, col) in enumerate([('FRANCE', 12, (70, 120, 230)), ('RUSSIA', 11, RED)]):
            y = 1080 + j * 110; ww = 600 * v / 12 * k
            panel(im, [300, y, 300 + max(ww, 30), y + 80], al, r=18, col=col, op=255)
            text_c(im, nm, y + 16, F(FB, 42), fill=CREAM, alpha=al, x=170)
            text_c(im, f'{v * k:.0f}', y + 6, F(FB, 56), fill=GOLD, alpha=al, x=300 + ww + 60)
    headline(im, t, a0 + 0.1, b0, 'The country with\nthe MOST time zones', 230, 80)
    chip(im, '12 zones incl. overseas territories · timeanddate · Guinness', 1345, a)

def fact5(im, t):
    a0, b0 = FACTS[4]; lt = t - a0; a = win(t, a0, b0)
    calendar(im, t, a, lt, cy=800, mode='fact')
    if lt > 2.4:
        tag(im, 'THU 29  →  SAT 31', 540, 1080, (40, 30, 10), win(t, a0 + 2.4, b0), F(FB, 50), GOLD)
    if lt > 3.2:
        chip(im, 'Samoa jumped across the Date Line', 1170, win(t, a0 + 3.2, b0))
    headline(im, t, a0 + 0.1, b0, 'A whole country\nskipped a day', 230, 86, GOLD)
    chip(im, 'Samoa, 2011 · Time in Samoa (Wikipedia) · Al Jazeera', 1345, a)

def question(im, t):
    a0, b0 = QA; a = win(t, a0, b0 + 0.2, 0.3, 0.4) * (1 - ease((t - (TOTAL - 0.95)) / 0.3))
    text_c(im, 'Which one did\nyou NOT believe?', 560, F(FB, 100), fill=GOLD, alpha=a, spacing=16, scale=lerp(1.2, 1, eob((t - a0) / .5)))
    text_c(im, 'Comment 1 · 2 · 3 · 4 · 5', 880, F(FX, 60), fill=CREAM, alpha=a)
    for i in range(5):
        p = eob(min(1, max(0, (t - a0 - 0.3 - i * 0.12) / 0.3)))
        if p > 0: tag(im, str(i + 1), 220 + i * 160, 1060, (30, 40, 80), a * min(1, p), F(FB, 60), GOLD)

def frame(t):
    im = background(t)
    if t < FACTS[0][0] + 0.35:
        hook(im, t, win(t, -1, FACTS[0][0] + 0.35, 0.3, 0.35), 0)
    if FACTS[0][0] <= t < FACTS[0][1]: fact1(im, t)
    if FACTS[1][0] <= t < FACTS[1][1]: fact2(im, t)
    if FACTS[2][0] <= t < FACTS[2][1]: fact3(im, t)
    if FACTS[3][0] <= t < FACTS[3][1]: fact4(im, t)
    if FACTS[4][0] <= t < FACTS[4][1]: fact5(im, t)
    if QA[0] <= t < QA[1] + 0.2: question(im, t)
    if t >= TOTAL - 0.7:
        hook(im, t, ease((t - (TOTAL - 0.7)) / 0.35), TOTAL - 0.7 - 0.3)
    progress(im, t)
    captions(im, t)
    return im.convert('RGB')

WD = '/home/claude/ouj25'
def rend(i):
    frame(i / FPS).save(f'{WD}/frames/f{i:05d}.jpg', quality=92)

if __name__ == '__main__':
    os.makedirs(WD + '/frames', exist_ok=True)
    if sys.argv[1] == 'prev':
        for tt in sys.argv[2:]:
            frame(float(tt)).save(f'{WD}/p_{tt}.jpg', quality=85)
    else:
        N = int(TOTAL * FPS)
        with Pool(os.cpu_count()) as p: p.map(rend, range(N), chunksize=8)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{WD}/frames/f%05d.jpg',
                        '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', sys.argv[1]], check=True)
        print('TOTAL', TOTAL, 'frames', N)
