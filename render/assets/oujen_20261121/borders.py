"""OUJ EN 20261121 — "5 border facts that sound fake" — frame renderer (silent mp4).
usage: python3 borders.py out.mp4 | python3 borders.py prev t1 t2 ..."""
import json, math, os, sys, random, subprocess, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from multiprocessing import Pool

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
FONTS = '/home/claude/rw/render/fonts/'
def F(name, s): return ImageFont.truetype(FONTS + name, s)
FB, FX, FI = 'InterDisplay-Black.otf', 'InterDisplay-ExtraBold.otf', 'Inter-Bold.otf'
GOLD = (233, 185, 73); CREAM = (255, 246, 228); BG = (6, 10, 26); MUTED = (170, 180, 205)
BLUE = (70, 150, 255); RED = (226, 76, 76); TEAL = (64, 214, 230); GREEN = (98, 200, 120)
WATER = (18, 48, 92); LANDC = (44, 62, 104)
OFF = 0.35; TEMPO = 1.15

# ---------- timing ----------
SEG = json.load(open('/home/claude/rw/render/out/oujen_20261121_borders_voice_segs.json'))['segments']
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
        # choose the longest gaps as sentence splits, keep order
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
FS = [SEG[i]['s'] - 0.15 for i in range(1, 7)]  # fact starts (5 facts) + question start
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

# ---------- geo ----------
GEO = json.load(open(os.path.join(D, 'c10.json')))
LAKE = json.load(open(os.path.join(D, 'constance.json')))
def rings(g): return [np.array(p[0]) for p in g['coordinates']] if g['type'] == 'MultiPolygon' else [np.array(g['coordinates'][0])]
def subset(codes, box):
    out = []
    for c in codes:
        for r in rings(GEO[c]):
            if r[:, 0].max() < box[0] or r[:, 0].min() > box[2] or r[:, 1].max() < box[1] or r[:, 1].min() > box[3]: continue
            out.append((c, r))
    return out
NA = subset(['USA', 'CAN'], (-140, 38, -100, 62))
# Tsawwassen / Point Roberts peninsula is missing at NE 10m scale -> simplified outline added by hand
NA.append(('CAN', np.array([(-123.0925, 49.0025), (-123.103, 49.02), (-123.095, 49.045), (-123.06, 49.062), (-123.02, 49.075),
                            (-122.99, 49.07), (-123.005, 49.04), (-123.0225, 49.0025)])))
NA.append(('USA', np.array([(-123.0925, 49.0025), (-123.0225, 49.0025), (-123.026, 48.985), (-123.037, 48.969), (-123.06, 48.964),
                            (-123.086, 48.974), (-123.097, 48.99)])))
AL = subset(['DEU', 'CHE', 'AUT', 'FRA', 'LIE'], (5, 45.5, 13, 49.5))
LAKER = rings(LAKE)

def mapdraw(im, parts, cam, colors, alpha, lake=None, lakecol=(40, 110, 190), edge=(220, 230, 245)):
    lon0, lat0, sc = cam; k = math.cos(math.radians(lat0)); cy0 = 820
    def P(r): return np.stack([W / 2 + (r[:, 0] - lon0) * sc * k, cy0 - (r[:, 1] - lat0) * sc], 1)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, H], fill=WATER + (255,))
    for c, r in parts:
        p = P(r)
        if p[:, 0].max() < -50 or p[:, 0].min() > W + 50 or p[:, 1].max() < -50 or p[:, 1].min() > H + 50: continue
        step = max(1, int(len(p) / 4000))
        pts = [tuple(x) for x in p[::step]]
        if len(pts) > 2: d.polygon(pts, fill=colors.get(c, LANDC) + (255,), outline=edge + (150,))
    if lake:
        for r in lake:
            pts = [tuple(x) for x in P(r)]; d.polygon(pts, fill=lakecol + (255,), outline=(170, 210, 255, 255))
    ov.putalpha(ov.getchannel('A').point(lambda v: int(v * alpha)))
    im.paste(ov, (0, 0), ov)
    return P

# ---------- layout pieces ----------
def progress(im, t):
    if t < FACTS[0][0] or t > QA[0]: return
    k = min(1, (t - FACTS[0][0]) / (QA[0] - FACTS[0][0])); idx = sum(1 for a, b in FACTS if t >= a)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle([50, 96, W - 50, 196], 26, fill=(6, 10, 26, 190))
    d.rounded_rectangle([70, 112, W - 70, 122], 5, fill=(255, 255, 255, 50))
    d.rounded_rectangle([70, 112, 70 + (W - 140) * k, 122], 5, fill=GOLD + (255,))
    d.text((72, 140), 'BORDER FACTS THAT SOUND FAKE', font=F(FI, 30), fill=(205, 212, 230, 255))
    s = f'{idx:02d} / 05'; f = F(FB, 42); bb = d.textbbox((0, 0), s, font=f)
    d.text((W - 72 - (bb[2] - bb[0]), 134), s, font=f, fill=GOLD + (255,))
    im.paste(ov, (0, 0), ov)

def headline(im, t, a, b, txt, y=250, size=84, fill=CREAM):
    al = win(t, a, b, 0.3, 0.3)
    if al > 0: text_c(im, txt, y, F(FB, size), fill=fill, alpha=al, spacing=12, scale=lerp(1.2, 1.0, eob((t - a) / 0.45)))

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
    f = F(FB, 66); d0 = ImageDraw.Draw(im)
    widths = [d0.textbbox((0, 0), WORDS[j][0].upper(), font=f)[2] for j in ch]; sp = 22
    tot = sum(widths) + sp * (len(ch) - 1); x = (W - tot) / 2; y = 1430
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for j, wd in zip(ch, widths):
        w, a, b = WORDS[j]; act = a - 0.05 <= t
        col = GOLD if (act and t < b + 0.05) else (CREAM if act else (200, 205, 220))
        pop = 1 + 0.12 * (1 - ease((t - a) / 0.18)) if act and t < a + 0.18 else 1
        ff = F(FB, int(66 * pop)) if pop != 1 else f
        d.text((x + 3, y + 5 - (pop - 1) * 30), w.upper(), font=ff, fill=(0, 0, 0, 150))
        d.text((x, y - (pop - 1) * 30), w.upper(), font=ff, fill=col + (255 if act else 150,), stroke_width=5, stroke_fill=(0, 0, 0, 230))
        x += wd + sp
    im.paste(ov, (0, 0), ov)

# ---------- scenes ----------
def river_island(im, t, alpha, side_k, cy=900, zoom=1.0):
    """Pheasant Island schematic: Bidasoa river between Spain (south) and France (north)."""
    if alpha <= 0.01: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    s = zoom
    d.rectangle([0, cy - 430 * s, W, cy - 150 * s], fill=(40, 70, 110, 255))   # France bank
    d.rectangle([0, cy + 150 * s, W, cy + 390 * s], fill=(110, 60, 52, 255))   # Spain bank
    d.rectangle([0, cy - 150 * s, W, cy + 150 * s], fill=(22, 72, 128, 255))   # river
    for i in range(12):
        xx = (i * 137 + t * 60) % (W + 200) - 100; yy = cy - 120 * s + (i * 53) % int(240 * s)
        d.arc([xx, yy, xx + 120, yy + 26], 200, 340, fill=(255, 255, 255, 50), width=3)
    # island blob
    pts = []
    for i in range(120):
        a = i / 120 * 2 * math.pi
        k = 1 + 0.06 * math.sin(3 * a + 1) + 0.04 * math.sin(5 * a + 2)
        pts.append((W / 2 + 300 * s * k * math.cos(a), cy + 70 * s * k * math.sin(a)))
    d.polygon(pts, fill=(70, 120, 70, 255), outline=(200, 240, 200, 255))
    ov.putalpha(ov.getchannel('A').point(lambda v: int(v * alpha)))
    im.paste(ov, (0, 0), ov)
    # flag on island: flips Spain <-> France
    fk = 'ESP' if side_k < 0.5 else 'FRA'
    sq = abs(math.cos(side_k * math.pi))  # flip squash
    fw = 150 * s * max(0.05, sq)
    d2 = ImageDraw.Draw(im)
    d2.line([(W / 2, cy - 10 * s), (W / 2, cy - 190 * s)], fill=(230, 230, 230), width=6)
    ov2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d3 = ImageDraw.Draw(ov2)
    flag(d3, fk, W / 2 + 3, cy - 190 * s, fw, 100 * s)
    ov2.putalpha(ov2.getchannel('A').point(lambda v: int(v * alpha)))
    im.paste(ov2, (0, 0), ov2)
    text_c(im, 'FRANCE', cy - 250 * s, F(FB, 50), fill=(170, 200, 255), alpha=alpha)
    text_c(im, 'SPAIN', cy + 180 * s, F(FB, 50), fill=(255, 190, 170), alpha=alpha)

def hook(im, t, a, t0):
    lt = t - t0
    flip = ((lt * 0.9) % 2)  # flips every ~1.1 s
    sk = ease(min(1, (flip % 1) / 0.35)) if flip < 1 else 1 - ease(min(1, ((flip - 1) % 1) / 0.35))
    river_island(im, t, a, sk, cy=930, zoom=1.0 + 0.04 * ease(lt / 3))
    text_c(im, 'THIS ISLAND\nCHANGES COUNTRY', 215, F(FB, 94), fill=GOLD, alpha=a, spacing=14, scale=lerp(1.06, 1, eob(lt / 0.5)) if lt < 0.6 else 1)
    chip(im, '5 border facts that sound fake · #5 is the strangest', 1330, a)

def fact1(im, t):
    a0, b0 = FACTS[0]; lt = t - a0; a = win(t, a0, b0)
    z = ease(lt / 2.6)
    cam = (lerp(-112, -122.92, ease(lt / 1.8)), lerp(52, 49.0, ease(lt / 1.8)), 40 * math.exp(math.log(3600 / 40) * z))
    P = mapdraw(im, NA, cam, {'USA': (54, 96, 170), 'CAN': (150, 66, 66)}, a)
    d = ImageDraw.Draw(im)
    # 49th parallel draws itself
    dl = ease((lt - 0.9) / 1.0)
    if dl > 0:
        xs = np.linspace(-123.4, lerp(-123.4, -122.2, dl), 60)
        pts = P(np.stack([xs, np.full_like(xs, 49.0)], 1))
        for i in range(0, len(pts) - 1, 2): d.line([tuple(pts[i]), tuple(pts[i + 1])], fill=GOLD, width=7)
        tag(im, f'{49 * ease((lt - 0.9) / 0.8):.0f}°N', 900, 760, (30, 30, 50), dl, F(FB, 40), GOLD)
    # route Blaine -> through Canada -> Point Roberts
    route = np.array([[-122.75, 48.99], [-122.76, 49.06], [-122.95, 49.08], [-123.04, 49.05], [-123.055, 48.985]])
    rk = ease((lt - 2.2) / 1.8)
    if rk > 0:
        seg = np.concatenate([np.linspace(route[i], route[i + 1], 30) for i in range(len(route) - 1)])
        n = max(2, int(len(seg) * rk)); pts = [tuple(p) for p in P(seg[:n])]
        d.line(pts, fill=(255, 255, 255), width=9, joint='curve'); d.line(pts, fill=TEAL, width=5, joint='curve')
        x, y = pts[-1]; d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=TEAL, outline='white', width=4)
        cr = sum(1 for th in (0.12, 0.92) if rk > th)
        panel(im, [610, 1110, 1010, 1290], a, border=TEAL)
        text_c(im, f'{cr}', 1118, F(FB, 110), fill=TEAL, alpha=a, x=810)
        text_c(im, 'border checks', 1238, F(FI, 32), fill=MUTED, alpha=a, x=810, stroke=2)
    pr = P(np.array([[-123.058, 48.982]]))[0]
    ph = (lt * 1.3) % 1
    if lt > 1.6:
        rr = 14 + 60 * ph; d.ellipse([pr[0] - rr, pr[1] - rr, pr[0] + rr, pr[1] + rr], outline=GOLD, width=5)
    tag(im, 'POINT ROBERTS (USA)', min(max(pr[0], 230), W - 230), pr[1] + 110, (40, 80, 160), win(t, a0 + 1.6, b0), F(FB, 36))
    tag(im, 'CANADA', 760, 520, RED, win(t, a0 + 1.0, b0), F(FB, 44))
    tag(im, 'USA', 800, 1000, BLUE, win(t, a0 + 1.2, b0), F(FB, 44))
    headline(im, t, a0 + 0.1, b0, 'A US town you reach\nonly through Canada', 245, 70)
    chip(im, 'Map: Natural Earth (simplified) · 49th parallel', 1330, a)

def fact2(im, t):
    a0, b0 = FACTS[1]; lt = t - a0; a = win(t, a0, b0)
    k = ease(lt / 2.0)
    cam = (lerp(8.6, 9.38, k), lerp(47.2, 47.58, k), lerp(240, 1300, k))
    cols = {'DEU': (70, 70, 80), 'CHE': (150, 50, 50), 'AUT': (160, 160, 170), 'FRA': LANDC, 'LIE': (60, 70, 120)}
    cols = {'DEU': (64, 72, 92), 'CHE': (140, 58, 58), 'AUT': (120, 120, 140), 'FRA': LANDC, 'LIE': (60, 70, 120)}
    P = mapdraw(im, AL, cam, cols, a, lake=LAKER)
    # flickering "possible borders" in the lake
    d = ImageDraw.Draw(im)
    if lt > 1.4:
        cands = [[[9.02, 47.69], [9.30, 47.60], [9.62, 47.52]], [[9.05, 47.71], [9.35, 47.63], [9.66, 47.56]],
                 [[9.00, 47.67], [9.28, 47.56], [9.58, 47.49]]]
        for j, c in enumerate(cands):
            on = 0.5 + 0.5 * math.sin((lt - 1.4) * 5 + j * 2.1)
            pts = [tuple(p) for p in P(np.array(c))]
            ln = ImageDraw.Draw(im)
            col = mix((40, 110, 190), (255, 255, 255), on)
            for i in range(len(pts) - 1):
                xs = np.linspace(0, 1, 14)
                for u in range(0, 13, 2):
                    p1 = (lerp(pts[i][0], pts[i + 1][0], xs[u]), lerp(pts[i][1], pts[i + 1][1], xs[u]))
                    p2 = (lerp(pts[i][0], pts[i + 1][0], xs[u + 1]), lerp(pts[i][1], pts[i + 1][1], xs[u + 1]))
                    ln.line([p1, p2], fill=col, width=6)
        tag(im, 'NO AGREED BORDER', W / 2, 860, (200, 40, 50), win(t, a0 + 1.8, b0), F(FB, 46))
    n = int(round(3 * ease((lt - 2.6) / 0.8)))
    for i, (kind, lab) in enumerate([('DEU', 'Germany'), ('CHE', 'Switzerland'), ('AUT', 'Austria')]):
        flag_card(im, kind, 240 + i * 300, 1150, 170, win(t, a0 + 2.6 + i * 0.25, b0) if i < max(n, 1) or lt > 2.6 + i * 0.25 else 0, lab)
    if lt > 2.6:
        tag(im, f'{n} countries', W / 2, 1010, (20, 26, 50), win(t, a0 + 2.6, b0), F(FB, 48), GOLD)
    tag(im, 'LAKE CONSTANCE', W / 2, 560, (20, 80, 150), win(t, a0 + 1.0, b0), F(FB, 40))
    headline(im, t, a0 + 0.1, b0, 'Nobody agrees\nwhere the border is', 245, 76)
    chip(im, 'Map: Natural Earth · swisstopo', 1330, a)

BAARLE = None
def baarle_cells():
    r = random.Random(11); cells = []
    for i in range(9):
        for j in range(9):
            cells.append((i, j))
    r.shuffle(cells)
    return cells[:22]
BCELLS = baarle_cells()
def fact3(im, t):
    a0, b0 = FACTS[2]; lt = t - a0; a = win(t, a0, b0)
    mid = a0 + (b0 - a0) * 0.48
    if t < mid + 0.3:
        al = a * (1 - ease((t - mid) / 0.3))
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        x0, y0, cs = 189, 470, 78
        d.rounded_rectangle([x0 - 10, y0 - 10, x0 + 9 * cs + 10, y0 + 9 * cs + 10], 24, fill=(222, 110, 40, int(255 * al)))
        n = int(22 * ease((lt - 0.4) / 2.0))
        for q, (i, j) in enumerate(BCELLS[:n]):
            p = eob(min(1, (lt - 0.4 - q * 2.0 / 22) / 0.25))
            cx, cy = x0 + i * cs + cs / 2, y0 + j * cs + cs / 2; h = cs / 2 * p - 4
            if h > 0: d.rounded_rectangle([cx - h, cy - h, cx + h, cy + h], 10, fill=(253, 218, 36, int(255 * al)), outline=(0, 0, 0, int(200 * al)), width=3)
        im.paste(ov, (0, 0), ov)
        flag_card(im, 'NLD', 200, 1440 - 40, 0, 0)
        panel(im, [250, 1180, 830, 1310], al, border=GOLD)
        text_c(im, f'{n} pieces of Belgium', 1188, F(FB, 50), fill=GOLD, alpha=al)
        text_c(im, 'inside the Netherlands', 1256, F(FI, 36), fill=MUTED, alpha=al, stroke=2)
        headline(im, t, a0 + 0.1, mid + 0.3, 'Baarle: a border\nmaze', 245, 80)
        chip(im, 'Schematic · Baarle-Hertog has 22 Belgian exclaves', 1340, al)
    if t > mid:
        al = win(t, mid, b0); lt2 = t - mid
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        A = int(255 * al)
        # house
        hx, hy, hw, hh = 240, 600, 600, 470
        d.rectangle([hx, hy, hx + hw / 2, hy + hh], fill=(253, 218, 36, A))
        d.rectangle([hx + hw / 2, hy, hx + hw, hy + hh], fill=(222, 110, 40, A))
        d.polygon([(hx - 40, hy), (hx + hw / 2, hy - 240), (hx + hw + 40, hy)], fill=(120, 40, 40, A))
        for wx in (hx + 60, hx + hw - 180):
            d.rectangle([wx, hy + 80, wx + 120, hy + 200], fill=(180, 220, 255, A), outline=(0, 0, 0, A), width=4)
        # front door straddling? door on Belgian side
        dx = hx + hw / 2 - 150
        d.rectangle([dx, hy + 260, dx + 110, hy + hh], fill=(90, 50, 30, A), outline=(0, 0, 0, A), width=4)
        im.paste(ov, (0, 0), ov)
        dd = ImageDraw.Draw(im)
        # border line draws itself through the house (white cross marks like the real pavement)
        k = ease(lt2 / 0.9); y0, y1 = hy - 280, hy + hh + 120
        yy = y0
        while yy < lerp(y0, y1, k):
            dd.rectangle([W / 2 - 8, yy, W / 2 + 8, yy + 24], fill=(255, 255, 255)); dd.line([(W / 2 - 22, yy + 12), (W / 2 + 22, yy + 12)], fill=(255, 255, 255), width=5); yy += 44
        flag_card(im, 'BEL', 330, 1235, 120, win(t, mid + 0.4, b0)); flag_card(im, 'NLD', 750, 1235, 120, win(t, mid + 0.5, b0))
        if lt2 > 1.0:
            ph = (lt2 * 1.4) % 1; rr = 70 + 40 * ph; cx, cy = dx + 55, hy + 370
            dd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=GOLD, width=6)
            tag(im, 'FRONT DOOR = BELGIUM', dx + 55, hy + hh + 50, (30, 30, 50), win(t, mid + 1.0, b0), F(FB, 38), GOLD)
        headline(im, t, mid + 0.05, b0, 'Your front door\ndecides your country', 245, 76)
        chip(im, 'Schematic · Baarle-Hertog (BE) / Baarle-Nassau (NL)', 1330, al)

def blob(cx, cy, rx, ry, seed, n=90):
    r = random.Random(seed); ph = [r.random() * 6.28 for _ in range(3)]; pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + 0.08 * math.sin(3 * a + ph[0]) + 0.05 * math.sin(5 * a + ph[1]) + 0.03 * math.sin(9 * a + ph[2])
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts
def clock_card(im, x, y, label, day, hour, col, alpha):
    panel(im, [x - 220, y, x + 220, y + 290], alpha, col=(12, 18, 40), op=235, border=col)
    text_c(im, label, y + 20, F(FI, 36), fill=col, alpha=alpha, x=x, stroke=2)
    text_c(im, hour, y + 70, F(FB, 100), fill=CREAM, alpha=alpha, x=x)
    text_c(im, day, y + 208, F(FX, 44), fill=GOLD, alpha=alpha, x=x)
def fact4(im, t):
    a0, b0 = FACTS[3]; lt = t - a0; a = win(t, a0, b0)
    mid = a0 + (b0 - a0) * 0.5
    cy = 860
    if t < mid + 0.3:
        al = a * (1 - ease((t - mid) / 0.3))
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); A = int(255 * al)
        d.rounded_rectangle([60, cy - 400, W - 60, cy + 400], 44, fill=(16, 52, 96, int(235 * al)), outline=(120, 170, 220, int(160 * al)), width=3)
        for i in range(12):
            yy = cy - 360 + i * 62 + (t * 20) % 62
            if yy < cy + 380: d.arc([100 + (i * 97) % 700, yy, 220 + (i * 97) % 700, yy + 30], 200, 340, fill=(255, 255, 255, int(30 * al)), width=2)
        s = 1 + 0.05 * ease(lt / 3)
        d.polygon(blob(W / 2 - 230 * s, cy, 180 * s, 280 * s, 1), fill=(150, 72, 66, A), outline=(255, 190, 180, A))
        d.polygon(blob(W / 2 + 230 * s, cy + 40, 90 * s, 130 * s, 2), fill=(64, 112, 176, A), outline=(190, 220, 255, A))
        im.paste(ov, (0, 0), ov); dd = ImageDraw.Draw(im)
        r = ease((lt - 0.6) / 1.4); xa, xb = W / 2 - 60, W / 2 + 145; yr = cy + 230
        if r > 0:
            dd.line([(xa, yr), (lerp(xa, xb, r), yr)], fill=GOLD, width=8); dd.line([(xa, yr - 22), (xa, yr + 22)], fill=GOLD, width=8)
            if r >= 1: dd.line([(xb, yr - 22), (xb, yr + 22)], fill=GOLD, width=8)
        # date line
        dl = ease((lt - 0.3) / 1.0); y0 = cy - 400; yy = y0
        while yy < lerp(y0, cy + 400, dl):
            dd.line([(W / 2 + 40, yy), (W / 2 + 40, min(yy + 26, cy + 400))], fill=(255, 255, 255), width=5); yy += 44
        tag(im, 'Big Diomede · RUSSIA', W / 2 - 230, cy - 330, RED, win(t, a0 + 0.4, mid + 0.3), F(FB, 34))
        tag(im, 'Little Diomede · USA', W / 2 + 240, cy - 200, BLUE, win(t, a0 + 0.6, mid + 0.3), F(FB, 34))
        text_c(im, f'{3.8 * r:.1f} km', cy + 270, F(FB, 96), fill=GOLD, alpha=win(t, a0 + 0.6, mid + 0.3), x=W / 2 + 60)
        headline(im, t, a0 + 0.1, mid + 0.3, 'Less than 4 km apart…', 260, 76)
        chip(im, 'Schematic · Bering Strait · NOAA / USGS', 1330, al)
    if t > mid:
        al = win(t, mid, b0); lt2 = t - mid
        hrs = int(round(21 * ease((lt2 - 0.2) / 1.2)))
        headline(im, t, mid, b0, '…but this far apart\nin time', 245, 76)
        text_c(im, f'{hrs} HOURS', 470, F(FB, 160), fill=GOLD, alpha=al, scale=1 + 0.05 * math.sin(lt2 * 6) * (1 - ease((lt2 - 1.4) / .4)))
        clock_card(im, W / 2 - 240, 760, 'RUSSIA · UTC+12', 'SUNDAY', '12:00', RED, win(t, mid + 0.3, b0))
        clock_card(im, W / 2 + 240, 760, 'USA · UTC−9', 'SATURDAY', '15:00', BLUE, win(t, mid + 0.5, b0))
        chip(im, 'Winter time · summer gap is 20 hours', 1120, al)

MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
def fact5(im, t):
    a0, b0 = FACTS[4]; lt = t - a0; a = win(t, a0, b0)
    mk = (lt - 0.6) / 3.0  # one full year in 3 s
    m = int((mk * 12)) % 12 if mk > 0 else 1
    m = (m + 1) % 12  # start at Feb
    spain = 1 <= m <= 6
    river_island(im, t, a, 0.0 if spain else 1.0, cy=690, zoom=0.6)
    # month strip
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    x0, y0, cw = 60, 1020, 80
    for i, mn in enumerate(MONTHS):
        sp = 1 <= i <= 6
        base = (170, 21, 27) if sp else (0, 35, 149)
        on = i == m and mk > 0
        A = int(255 * a)
        d.rounded_rectangle([x0 + i * cw + 3, y0, x0 + (i + 1) * cw - 3, y0 + 90], 12, fill=(mix(base, (255, 255, 255), 0.25 if on else 0)) + (A if (on or mk > 0) else int(A * .5),), outline=(GOLD + (A,)) if on else None, width=4)
        f = F(FI, 26); bb = d.textbbox((0, 0), mn, font=f)
        d.text((x0 + i * cw + cw / 2 - (bb[2] - bb[0]) / 2, y0 + 30), mn, font=f, fill=(255, 255, 255, A))
    im.paste(ov, (0, 0), ov)
    tag(im, 'SPAIN  1 Feb – 31 Jul', 300, 1165, (170, 21, 27), win(t, a0 + 0.6, b0), F(FB, 32))
    tag(im, 'FRANCE  1 Aug – 31 Jan', 790, 1165, (0, 35, 149), win(t, a0 + 0.9, b0), F(FB, 32))
    yr = int(round(lerp(1600, 1659, ease((lt - 2.4) / 1.4))))
    if lt > 2.4:
        panel(im, [300, 1215, 780, 1315], win(t, a0 + 2.4, b0), border=GOLD)
        text_c(im, f'since {yr}', 1222, F(FB, 64), fill=GOLD, alpha=win(t, a0 + 2.4, b0))
    headline(im, t, a0 + 0.1, b0, 'Spanish 6 months,\nFrench 6 months', 220, 80, GOLD)
    chip(im, 'Schematic · Treaty of the Pyrenees, 1659', 1345, a)

def question(im, t):
    a0, b0 = QA; a = win(t, a0, b0 + 0.2, 0.3, 0.4)
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
    if t >= TOTAL - 0.9:
        hook(im, t, ease((t - (TOTAL - 0.9)) / 0.5), TOTAL - 0.9)
    progress(im, t)
    captions(im, t)
    return im.convert('RGB')

def rend(i):
    frame(i / FPS).save(f'/home/claude/ouj/frames/f{i:05d}.jpg', quality=92)

if __name__ == '__main__':
    if sys.argv[1] == 'prev':
        for tt in sys.argv[2:]:
            frame(float(tt)).save(f'/home/claude/ouj/p_{tt}.jpg', quality=85)
    else:
        os.makedirs('/home/claude/ouj/frames', exist_ok=True)
        N = int(TOTAL * FPS)
        with Pool(os.cpu_count()) as p: p.map(rend, range(N), chunksize=8)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', '/home/claude/ouj/frames/f%05d.jpg',
                        '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', sys.argv[1]], check=True)
        print('TOTAL', TOTAL, 'frames', N)
