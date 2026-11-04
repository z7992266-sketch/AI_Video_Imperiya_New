"""GLITCHVERSE — Darvaza flagship renderer (1920x1080, 30 fps).
Usage: python3 build.py [--preview START END] -> writes video-only mp4 (frames piped to ffmpeg)."""
import json, math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = '/tmp/claude-0/-home-claude/844ebc5a-648f-5142-9a2f-1a04ed1a7ee7/scratchpad/'
A = S + 'glitch/assets/'
OUT = S + 'dz/'
W, H, FPS = 1920, 1080, 30
F = '/usr/share/fonts/opentype/inter/'
BLACK = F + 'InterDisplay-Black.otf'; XB = F + 'InterDisplay-ExtraBold.otf'
BOLD = F + 'Inter-Bold.otf'; MED = F + 'Inter-Medium.otf'; SEMI = F + 'Inter-SemiBold.otf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
CY = (0, 229, 255); MG = (255, 0, 110); WH = (244, 248, 255); FIRE = (255, 150, 40); BG = (6, 8, 14)

_fc = {}
def font(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]

# ---------- credits ----------
CRED = {}
for e in json.load(open(S + 'glitch/credits.json')):
    a = e['artist'].split('\n')[0].replace('(original picture)', '').split(' from ')[0].split(' http')[0].strip()
    if 'Jrmski' in a: a = 'Jrmski'
    if 'Earth Science' in a: a = 'NASA / ISS crew'
    if 'CIRA' in a: a = 'CSU/CIRA & NOAA/NESDIS (JPSS)'
    lic = e['license']
    CRED[e['file']] = f"{a} · {lic}" + ('' if 'Public' in lic else ' · Wikimedia Commons')
CRED['kk_s2.jpg'] = CRED['ca_s2.jpg'] = 'Sentinel-2 cloudless 2016 by EOX · CC BY 4.0 · contains modified Copernicus data'

# ---------- image cache ----------
_ic = {}
def img(name):
    if name not in _ic:
        im = Image.open(A + name).convert('RGB')
        _ic[name] = im
    return _ic[name]

def ease(x): return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, x)))

def kenburns(name, p, move='in', amt=0.12, focus=(0.5, 0.5), darken=0.0):
    """Cover-crop with smooth zoom/pan. p in [0,1]."""
    im = img(name); iw, ih = im.size
    base = min(iw / W, ih / H)  # source px per output px at cover
    e = ease(p) * 0.35 + p * 0.65
    if move == 'in': z0, z1, dx, dy = 1.0, 1 + amt, 0, 0
    elif move == 'out': z0, z1, dx, dy = 1 + amt, 1.0, 0, 0
    elif move == 'right': z0 = z1 = 1 + amt; dx, dy = 1, 0
    elif move == 'left': z0 = z1 = 1 + amt; dx, dy = -1, 0
    elif move == 'down': z0 = z1 = 1 + amt; dx, dy = 0, 1
    else: z0 = z1 = 1 + amt; dx, dy = 0, -1
    z = z0 + (z1 - z0) * e
    cw, ch = W * base / z, H * base / z
    fx, fy = focus
    cx = fx * iw + dx * (e - 0.5) * (iw - cw) * 0.9
    cy = fy * ih + dy * (e - 0.5) * (ih - ch) * 0.9
    cx = min(max(cx, cw / 2), iw - cw / 2); cy = min(max(cy, ch / 2), ih - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    fr = im.transform((W, H), Image.EXTENT, box, Image.BILINEAR)
    if darken: fr = Image.blend(fr, Image.new('RGB', (W, H), (0, 0, 0)), darken)
    return fr

# ---------- grade / vignette / grain ----------
yy, xx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.55 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2).clip(0.45, 1)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GRAIN = [rng.normal(0, 3, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]

def finish(fr, k, grade=True):
    a = np.asarray(fr, dtype=np.float32)
    if grade:
        a = a * VIG
        a[..., 2] *= 1.03; a[..., 0] *= 1.02
        g = GRAIN[k % 6].repeat(2, 0).repeat(2, 1)
        a += g
    return a.clip(0, 255).astype(np.uint8)

def glitch_np(a, strength, seed):
    r = random.Random(seed)
    a = a.copy()
    off = int(18 * strength) + 2
    a[..., 0] = np.roll(a[..., 0], off, axis=1)
    a[..., 2] = np.roll(a[..., 2], -off, axis=1)
    for _ in range(int(10 * strength) + 2):
        y0 = r.randrange(0, H - 40); hh = r.randrange(6, 60)
        a[y0:y0 + hh] = np.roll(a[y0:y0 + hh], r.randrange(-120, 120), axis=1)
    return a

# ---------- text overlays ----------
def shadow_text(d, xy, t, f, fill=WH, anchor='la', sh=4):
    x, y = xy
    d.text((x + sh, y + sh), t, font=f, fill=(0, 0, 0, 170), anchor=anchor)
    d.text(xy, t, font=f, fill=fill, anchor=anchor)

def overlay(spec):
    """spec: list of dicts {t:text, size, font, pos:(x,y), anchor, color, box}"""
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    for s in spec:
        f = font(s.get('font', XB), s.get('size', 64))
        if s.get('box'):
            bb = d.textbbox(s['pos'], s['t'], font=f, anchor=s.get('anchor', 'la'))
            pad = s.get('pad', 22)
            d.rounded_rectangle((bb[0] - pad, bb[1] - pad * 0.7, bb[2] + pad, bb[3] + pad * 0.7), 10, fill=s['box'])
            d.text(s['pos'], s['t'], font=f, fill=s.get('color', WH), anchor=s.get('anchor', 'la'))
        else:
            shadow_text(d, s['pos'], s['t'], f, s.get('color', WH), s.get('anchor', 'la'), s.get('sh', 4))
    return L

def lower(text, sub=None):
    """Lower-third caption, bottom-left inside safe area."""
    sp = [{'t': text, 'size': 58, 'font': XB, 'pos': (120, 860), 'anchor': 'ls'}]
    if sub: sp.append({'t': sub, 'size': 34, 'font': SEMI, 'pos': (122, 912), 'anchor': 'ls', 'color': CY})
    L = overlay(sp)
    d = ImageDraw.Draw(L); d.rectangle((96, 800, 104, 920 if sub else 870), fill=FIRE + (255,))
    return L

def center(text, size=96, sub=None, color=WH):
    sp = [{'t': text, 'size': size, 'font': BLACK, 'pos': (W // 2, H // 2 - (30 if sub else 0)), 'anchor': 'mm', 'color': color}]
    if sub: sp.append({'t': sub, 'size': 40, 'font': SEMI, 'pos': (W // 2, H // 2 + size * 0.55), 'anchor': 'mm', 'color': CY})
    return overlay(sp)

def credit_layer(name):
    c = CRED.get(name)
    if not c: return None
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    f = font(MED, 20)
    d.text((W - 40, H - 30), c, font=f, fill=(255, 255, 255, 150), anchor='rs')
    return L

def chapter_layer(n, title):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    f1 = font(MONO, 28); f2 = font(XB, 44)
    d.rectangle((96, 96, 104, 186), fill=CY + (255,))
    shadow_text(d, (124, 100), f'CHAPTER {n:02d}', f1, CY, sh=2)
    shadow_text(d, (122, 136), title.upper(), f2, WH, sh=3)
    return L

def brand_bug():
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.text((W - 60, 70), 'GLITCHVERSE', font=font(XB, 26), fill=(255, 255, 255, 120), anchor='rs')
    return L
BUG = brand_bug()

# ---------- cards (full-frame graphics) ----------
def card_bg(t):
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    for x in range(0, W, 48): d.line((x, 0, x, H), fill=(13, 20, 32))
    for y in range(0, H, 48): d.line((0, y, W, y), fill=(13, 20, 32))
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse((W * .2, H * .05, W * .8, H * .95), fill=70)
    g = g.filter(ImageFilter.GaussianBlur(220))
    return Image.composite(Image.new('RGB', (W, H), (16, 34, 58)), im, g)
CARD_BG = card_bg(0)

def type_on(d, xy, text, f, p, fill=WH, anchor='la'):
    n = int(len(text) * min(1, p)); s = text[:n]
    d.text(xy, s, font=f, fill=fill, anchor=anchor)

# ---------- MAP ----------
CA = ('ca_s2.jpg', 46, 76, 34, 50)
KK = ('kk_s2.jpg', 56, 61, 38, 42)
DARV = (58.44, 40.25)
LABELS = [('CASPIAN SEA', 50.6, 42.0, 'sea'), ('ARAL SEA', 59.6, 45.2, 'sea'), ('KAZAKHSTAN', 66.5, 47.5, 'cty'),
          ('UZBEKISTAN', 63.5, 41.8, 'cty'), ('TURKMENISTAN', 60.2, 38.6, 'cty'), ('IRAN', 56.5, 35.4, 'cty'),
          ('KARAKUM DESERT', 60.3, 39.6, 'des'), ('Ashgabat', 58.38, 37.95, 'city')]

def map_frame(cx, cy, wdeg, t, pin_alpha=1.0, show_labels=True):
    hdeg = wdeg * H / W
    src = KK if (wdeg < 4.6 and KK[1] < cx - wdeg / 2 and cx + wdeg / 2 < KK[2] and KK[3] < cy - hdeg / 2 and cy + hdeg / 2 < KK[4]) else CA
    name, lo0, lo1, la0, la1 = src
    im = img(name); iw, ih = im.size
    ppx = iw / (lo1 - lo0); ppy = ih / (la1 - la0)
    box = ((cx - wdeg / 2 - lo0) * ppx, (la1 - (cy + hdeg / 2)) * ppy, (cx + wdeg / 2 - lo0) * ppx, (la1 - (cy - hdeg / 2)) * ppy)
    fr = im.transform((W, H), Image.EXTENT, box, Image.BICUBIC).convert('RGBA')
    d = ImageDraw.Draw(fr)
    def sxy(lo, la): return ((lo - (cx - wdeg / 2)) / wdeg * W, ((cy + hdeg / 2) - la) / hdeg * H)
    if show_labels:
        for txt, lo, la, kind in LABELS:
            x, y = sxy(lo, la)
            if not (-200 < x < W + 200 and -100 < y < H + 100): continue
            if kind == 'cty' and wdeg < 9: continue
            if kind == 'sea' and wdeg < 6: continue
            sz = {'cty': 40, 'sea': 32, 'des': 38, 'city': 30}[kind]
            col = {'cty': (255, 255, 255, 220), 'sea': (170, 225, 255, 220), 'des': (255, 214, 140, 235), 'city': (255, 255, 255, 230)}[kind]
            f = font(XB if kind != 'city' else BOLD, sz)
            if kind == 'city':
                d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 255, 255, 230))
                d.text((x + 16, y), txt, font=f, fill=col, anchor='lm')
            else:
                d.text((x + 3, y + 3), txt, font=f, fill=(0, 0, 0, 140), anchor='mm')
                d.text((x, y), txt, font=f, fill=col, anchor='mm')
    # pin
    x, y = sxy(*DARV)
    if pin_alpha > 0:
        a = int(255 * pin_alpha)
        r = 18 + 10 * (0.5 + 0.5 * math.sin(t * 6))
        d.ellipse((x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2), outline=FIRE + (int(a * 0.5),), width=4)
        d.ellipse((x - 13, y - 13, x + 13, y + 13), fill=FIRE + (a,), outline=(255, 255, 255, a), width=4)
        f = font(BLACK, 46)
        d.text((x + 42, y - 6), 'DARVAZA', font=f, fill=(0, 0, 0, int(a * 0.6)), anchor='lm')
        d.text((x + 38, y - 10), 'DARVAZA', font=f, fill=(255, 255, 255, a), anchor='lm')
        d.text((x + 40, y + 34), '40.25°N  58.44°E', font=font(MONO, 26), fill=CY + (a,), anchor='lm')
    return fr.convert('RGB')

def lerp(a, b, e): return a + (b - a) * e
def log_lerp(a, b, e): return math.exp(math.log(a) + (math.log(b) - math.log(a)) * e)

# ---------- SHOT DEFINITIONS ----------
TIM = {s['id']: s for s in json.load(open(OUT + 'timing.json'))}
END_EXTRA = 8.0  # end-screen time
TOTAL = TIM['s18']['end'] + END_EXTRA

def img_shot(name, move='in', text=None, amt=0.12, focus=(0.5, 0.5), darken=0.0, glitch=True):
    return {'kind': 'img', 'name': name, 'move': move, 'text': text, 'amt': amt, 'focus': focus, 'darken': darken, 'glitch': glitch}

def card(fn, glitch=True): return {'kind': 'card', 'fn': fn, 'glitch': glitch}

# card functions: (p, t_local, dur) -> PIL RGB
def hook_card(name):
    def f(p, tl, dur):
        fr = kenburns(name, p, 'in', 0.18, (0.5, 0.6)).convert('RGBA')
        if tl < 3.4:
            sh_ = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh_)
            sd.rounded_rectangle((330, 260, 1590, 700), 40, fill=(0, 0, 0, int(150 * max(0, min(1, (3.4 - tl) / 0.4)))))
            fr.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(40)))
            L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
            ft = font(BLACK, 128)
            k = min(1, tl / 0.25)
            off = 10 if (int(tl * 30) % 7) in (0, 1) else 3
            for col, dx in ((MG, -off), (CY, off)):
                d.text((W // 2 + dx, 470), 'SATELLITES', font=ft, fill=col + (int(170 * k),), anchor='mm')
                d.text((W // 2 + dx, 610), 'DISAGREE.', font=ft, fill=col + (int(170 * k),), anchor='mm')
            d.text((W // 2, 470), 'SATELLITES', font=ft, fill=WH + (int(255 * k),), anchor='mm')
            d.text((W // 2, 610), 'DISAGREE.', font=ft, fill=WH + (int(255 * k),), anchor='mm')
            d.text((W // 2, 330), 'EVERYONE SAYS 1971', font=font(MONO, 40), fill=FIRE + (int(255 * k),), anchor='mm')
            if tl > 3.0: L.putalpha(L.split()[3].point(lambda v: int(v * max(0, (3.4 - tl) / 0.4))))
            fr.alpha_composite(L)
        return fr.convert('RGB')
    return f

def dates_card(p, tl, dur):
    fr = Image.blend(kenburns('gv_d18.jpg', p, 'in', 0.08), Image.new('RGB', (W, H), (0, 0, 0)), 0.55).convert('RGBA')
    d = ImageDraw.Draw(fr)
    rows = [('THE FAMOUS STORY', '1971', 'drilled, collapsed, set on fire', 0.0, FIRE),
            ('LOCAL GEOLOGISTS', '1960s', 'the crater collapses', 0.30, CY),
            ('LOCAL GEOLOGISTS', '1980s', 'only then set on fire', 0.55, CY)]
    for i, (lab, yr, txt, t0, col) in enumerate(rows):
        if p < t0: continue
        k = min(1, (p - t0) / 0.05)
        y = 260 + i * 220
        jit = random.Random(int(tl * 15) + i).randint(-6, 6) if (p - t0) < 0.06 else 0
        d.text((240 + jit, y), lab, font=font(MONO, 30), fill=col + (int(255 * k),))
        d.text((240 + jit, y + 40), yr, font=font(BLACK, 120), fill=WH + (int(255 * k),))
        d.text((720, y + 100), txt, font=font(SEMI, 40), fill=(220, 225, 235, int(255 * k)), anchor='ls')
        if i == 0 and p > 0.3:
            d.line((230, y + 105, 640, y + 105), fill=MG + (230,), width=10)
    return fr.convert('RGB')

def redacted_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 220), 'ORIGINAL SOVIET RECORDS', font=font(MONO, 44), fill=CY, anchor='mm')
    words = ['MISSING', 'CLASSIFIED', 'INACCESSIBLE']
    for i, w in enumerate(words):
        t0 = 0.12 + i * 0.22
        if p < t0: continue
        y = 400 + i * 170
        f = font(BLACK, 110)
        d.text((W // 2, y), w, font=f, fill=WH, anchor='mm')
        bb = d.textbbox((W // 2, y), w, font=f, anchor='mm')
        k = min(1, (p - t0) / 0.12)
        d.rectangle((bb[0] - 20, bb[3] + 14, bb[0] - 20 + (bb[2] - bb[0] + 40) * k, bb[3] + 24), fill=MG)
        d.text((bb[2] + 40, y), '[ REDACTED ]', font=font(MONO, 28), fill=MG + (int(255 * k),), anchor='lm')
    if p > 0.82:
        d.text((W // 2, 960), '"I don\'t know exactly what happened." — George Kourounis', font=font(SEMI, 34), fill=(210, 215, 225), anchor='mm')
    return fr.convert('RGB')

def landsat_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 170), 'LANDSAT ARCHIVE · FIRST SIGN OF FIRE', font=font(MONO, 40), fill=CY, anchor='mm')
    x0, x1, y = 200, 1720, 560
    d.line((x0, y, x1, y), fill=(90, 110, 140), width=6)
    years = list(range(1972, 1993, 2))
    for yr in years:
        x = x0 + (yr - 1972) / 20 * (x1 - x0)
        d.line((x, y - 18, x, y + 18), fill=(90, 110, 140), width=4)
        d.text((x, y + 50), str(yr), font=font(MONO, 26), fill=(150, 165, 190), anchor='mm')
    cur = 1972 + 20 * min(1, p / 0.7)
    xc = x0 + (cur - 1972) / 20 * (x1 - x0)
    d.line((x0, y, xc, y), fill=CY, width=8)
    d.ellipse((xc - 14, y - 14, xc + 14, y + 14), fill=CY)
    # 1971 crossed
    d.text((x0 - 10, y - 120), '1971 ?', font=font(BLACK, 64), fill=FIRE, anchor='mm')
    if p > 0.2: d.line((x0 - 110, y - 120, x0 + 90, y - 120), fill=MG, width=9)
    if cur >= 1987.8:
        xg = x0 + (1987.9 - 1972) / 20 * (x1 - x0)
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        gd.ellipse((xg - 60, y - 60, xg + 60, y + 60), fill=FIRE + (200,))
        fr.alpha_composite(g.filter(ImageFilter.GaussianBlur(24)))
        d = ImageDraw.Draw(fr)
        d.ellipse((xg - 16, y - 16, xg + 16, y + 16), fill=FIRE)
        d.text((xg, y - 150), 'LATE 1987 – EARLY 1988', font=font(BLACK, 66), fill=WH, anchor='mm')
        d.text((xg, y - 92), 'first glow in the satellite record', font=font(SEMI, 34), fill=(255, 210, 160), anchor='mm')
    if p > 0.82:
        d.text((W // 2, 860), 'NOT 1971 — OFF BY ALMOST 17 YEARS', font=font(BLACK, 64), fill=MG, anchor='mm')
    d.text((W // 2, 1010), 'Source: Valverde et al., Geophysical Research Letters (2026)', font=font(MED, 24), fill=(150, 160, 180), anchor='mm')
    return fr.convert('RGB')

def orders_card(p, tl, dur):
    fr = Image.blend(kenburns('gv_d06.jpg', p, 'right', 0.1), Image.new('RGB', (W, H), (0, 0, 0)), 0.5).convert('RGBA')
    d = ImageDraw.Draw(fr)
    items = [('2010', 'President calls for measures to limit the crater\'s impact on nearby gas fields', 0.18),
             ('JAN 2022', 'Order: find a way to extinguish it — health, environment, wasted gas', 0.55)]
    for i, (yr, txt, t0) in enumerate(items):
        if p < t0: continue
        k = min(1, (p - t0) / 0.06); y = 360 + i * 260
        d.rectangle((150, y - 10, 158, y + 150), fill=FIRE + (int(255 * k),))
        d.text((190, y), yr, font=font(BLACK, 96), fill=WH + (int(255 * k),))
        type_on(d, (194, y + 118), txt, font(SEMI, 38), (p - t0) / 0.2, fill=(225, 230, 240, int(255 * k)))
    return fr.convert('RGB')

def methane_card(p, tl, dur):
    fr = Image.blend(kenburns('gv_d07.jpg', p, 'in', 0.1), Image.new('RGB', (W, H), (0, 0, 0)), 0.6).convert('RGBA')
    d = ImageDraw.Draw(fr)
    if p < 0.18:
        d.text((W // 2, H // 2), 'HERE\'S THE TWIST', font=font(BLACK, 110), fill=WH, anchor='mm')
        return fr.convert('RGB')
    d.text((W // 2, 190), 'METHANE FROM THE CRATER · 2020–2025', font=font(MONO, 38), fill=CY, anchor='mm')
    stats = [('1–3 t', 'every hour', 0.25), ('44', 'methane plumes detected', 0.42), ('71 ± 21 kt', 'estimated total', 0.58)]
    for i, (big, small, t0) in enumerate(stats):
        if p < t0: continue
        k = min(1, (p - t0) / 0.06); x = 380 + i * 580
        d.text((x, 470), big, font=font(BLACK, 104), fill=WH + (int(255 * k),), anchor='mm')
        d.text((x, 560), small, font=font(SEMI, 34), fill=(210, 220, 235, int(255 * k)), anchor='mm')
    if p > 0.75:
        d.text((W // 2, 760), 'Flames: weaker.   Methane: no clear decline.', font=font(XB, 58), fill=FIRE, anchor='mm')
    d.text((W // 2, 1010), 'Source: Valverde et al., GRL (2026) — 5 hyperspectral satellites', font=font(MED, 24), fill=(150, 160, 180), anchor='mm')
    return fr.convert('RGB')

def gwp_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 190), 'WARMING POWER OVER 20 YEARS', font=font(MONO, 40), fill=CY, anchor='mm')
    k1 = min(1, p / 0.15); k2 = min(1, max(0, (p - 0.2) / 0.25))
    # CO2 bar
    d.text((300, 380), 'CO₂', font=font(BLACK, 80), fill=WH, anchor='mm')
    d.rectangle((420, 345, 420 + 18 * k1, 415), fill=(170, 180, 200))
    d.text((470, 380), '1×', font=font(XB, 46), fill=(200, 210, 225), anchor='lm')
    d.text((300, 560), 'CH₄', font=font(BLACK, 80), fill=WH, anchor='mm')
    d.rectangle((420, 525, 420 + 1350 * k2, 595), fill=FIRE)
    if k2 > 0.95: d.text((1720, 640), '≈ 80×', font=font(BLACK, 80), fill=FIRE, anchor='rm')
    if p > 0.55:
        d.text((W // 2, 800), 'Captured & used  →  a darker crater is a WIN', font=font(XB, 48), fill=(130, 255, 190), anchor='mm')
    if p > 0.75:
        d.text((W // 2, 885), 'Leaking unburned  →  a darker crater could be WORSE', font=font(XB, 48), fill=MG, anchor='mm')
    d.text((W // 2, 1010), 'IPCC AR6 WG1, Table 7.15: methane GWP-20 ≈ 81', font=font(MED, 24), fill=(150, 160, 180), anchor='mm')
    return fr.convert('RGB')

def baba_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 420), 'BABA GURGUR', font=font(BLACK, 120), fill=FIRE, anchor='mm')
    d.text((W // 2, 540), 'near Kirkuk, Iraq', font=font(SEMI, 48), fill=WH, anchor='mm')
    d.text((W // 2, 640), '"said to have burned for thousands of years"', font=font(MED, 38), fill=CY, anchor='mm')
    return fr.convert('RGB')

def mix_card(p, tl, dur):
    fr = Image.blend(kenburns('gv_d01.jpg', p, 'out', 0.1), Image.new('RGB', (W, H), (0, 0, 0)), 0.5).convert('RGBA')
    d = ImageDraw.Draw(fr)
    items = ['A giant open pit', 'A missing history', 'A satellite record that rewrote the story', 'A fire that might be helping by burning']
    d.text((160, 230), 'WHAT MAKES DARVAZA DIFFERENT', font=font(MONO, 38), fill=CY)
    for i, t in enumerate(items):
        t0 = 0.12 + i * 0.18
        if p < t0: continue
        y = 340 + i * 120
        d.text((160, y), '▸', font=font(XB, 60), fill=FIRE)
        d.text((230, y), t, font=font(XB, 60), fill=WH)
    return fr.convert('RGB')

def question_card(p, tl, dur):
    fr = Image.blend(kenburns('gv_d19.jpg', p, 'in', 0.14, (0.5, 0.6)), Image.new('RGB', (W, H), (0, 0, 0)), 0.45).convert('RGBA')
    d = ImageDraw.Draw(fr)
    if p > 0.1:
        d.text((W // 2, 380), 'PUT IT OUT FOR GOOD?', font=font(BLACK, 100), fill=WH, anchor='mm')
    if p > 0.3:
        d.text((W // 2, 520), 'or', font=font(SEMI, 50), fill=CY, anchor='mm')
    if p > 0.4:
        d.text((W // 2, 660), 'KEEP IT BURNING AS A MONUMENT?', font=font(BLACK, 90), fill=FIRE, anchor='mm')
    if p > 0.6:
        d.text((W // 2, 840), '↓  Tell me in the comments', font=font(XB, 52), fill=WH, anchor='mm')
    return fr.convert('RGB')

LOGO = Image.open(S + 'glitch/logo_800.png').convert('RGBA')
def endcard(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    lg = LOGO.resize((360, int(360 * LOGO.height / LOGO.width)))
    fr.alpha_composite(lg, (W // 2 - lg.width // 2, 120))
    d.text((W // 2, 140 + lg.height + 40), 'REAL PLACES. REAL GLITCHES.', font=font(BLACK, 72), fill=WH, anchor='mm')
    d.text((W // 2, 140 + lg.height + 120), 'Subscribe for a new glitch every week', font=font(SEMI, 40), fill=CY, anchor='mm')
    # end-screen slots (YouTube elements go here)
    for x in (360, 1560):
        d.rounded_rectangle((x - 300, 640, x + 300, 980), 24, outline=(60, 80, 110), width=3)
    return fr.convert('RGB')

def map_in(p, tl, dur):
    e = ease(min(1, p / 0.92))
    cx = lerp(61.0, DARV[0], e); cy = lerp(42.0, DARV[1], e); w = log_lerp(30.0, 2.2, e)
    fr = map_frame(cx, cy, w, tl, pin_alpha=min(1, max(0, (p - 0.35) / 0.15)))
    return fr

def map_out(p, tl, dur):
    e = ease(p)
    cx = lerp(DARV[0], 61.0, e); cy = lerp(DARV[1], 42.0, e); w = log_lerp(2.2, 30.0, e)
    return map_frame(cx, cy, w, tl, pin_alpha=1.0)

def nasa_card(p, tl, dur):
    fr = kenburns('gv_n01.jpg', p, 'in', 0.06).convert('RGBA')
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((60, 860, 1000, 1000), 14, fill=(0, 0, 0, 170))
    d.text((90, 880), 'FIRE REDUCED ~3×', font=font(BLACK, 58), fill=FIRE)
    d.text((92, 950), 'Turkmengaz, June 2025 · satellites agree: the flames are weaker', font=font(SEMI, 28), fill=WH)
    return fr.convert('RGB')

# ---------- SEGMENT -> SHOTS ----------
SEG = {
 's01': [card(hook_card('gv_d19.jpg'), glitch=False), img_shot('gv_d05.jpg', 'right'), img_shot('gv_d08.jpg', 'in', ('~70 m wide · 30 m deep', 'visible from kilometers away')), img_shot('gv_d17.jpg', 'in', ('THE DOOR TO HELL', 'Darvaza gas crater, Turkmenistan'))],
 's02': [img_shot('gv_d14.jpg', 'left', ('"Lit by Soviet engineers in 1971"', 'or so the story goes')), img_shot('gv_d02.jpg', 'in', None, focus=(0.6, 0.6), glitch=False), img_shot('gv_d18.jpg', 'in', ('The real problem?', 'something you can\'t see'))],
 's03': [card(map_in)],
 's04': [img_shot('gv_k02.jpg', 'right', ('KARAKUM', '"Black Sand" desert')), img_shot('gv_d09.jpg', 'in', ('"The Shining of Karakum"', 'official name')), img_shot('gv_k01.jpg', 'in', ('NATURAL GAS', 'Turkmenistan: some of the largest reserves on Earth')), img_shot('gv_d16.jpg', 'in')],
 's05': [img_shot('gv_d11.jpg', 'right', ('1971 · Soviet drilling', 'the version you\'ll find everywhere'), darken=0.15), img_shot('gv_d15.jpg', 'in', ('The ground gave way', 'equipment fell into the collapse'))],
 's06': [img_shot('gv_d04.jpg', 'in', ('"Set it on fire"', 'burn the gas off, wait a few weeks')), img_shot('gv_d13.jpg', 'down', None, amt=0.1), {'kind': 'text', 'bg': 'gv_d21.jpg', 'big': 'A PERFECT STORY.', 'sub': 'Maybe too perfect.'}],
 's07': [card(dates_card)],
 's08': [card(redacted_card)],
 's09': [card(landsat_card)],
 's10': [img_shot('gv_d04.jpg', 'down', ('2013 · George Kourounis', 'first person known to reach the bottom'), focus=(0.5, 0.7)), img_shot('gv_d13.jpg', 'down', ('Heat-reflective suit', 'own air supply · heat-resistant ropes')), img_shot('gv_d21.jpg', 'in')],
 's11': [img_shot('gv_d05.jpg', 'in', ('"Like a jet engine"', 'George Kourounis, National Geographic')), img_shot('gv_d19.jpg', 'left', ('"A coliseum of fire"', 'thousands of small flames')), img_shot('gv_d21.jpg', 'right', ('His mission:', 'collect soil'))],
 's12': [img_shot('gv_d03.jpg', 'right', ('LIFE AT THE BOTTOM', 'bacteria not found in the soil around the crater'), amt=0.2), img_shot('gv_d19.jpg', 'in')],
 's12b': [img_shot('gv_d11.jpg', 'in', ('Nature reserve since 2013', 'you can actually visit')), img_shot('gv_d12.jpg', 'right', ('Camps & yurts near the rim', 'hours across the desert on a rough track')), img_shot('gv_d15.jpg', 'in', ('No railings. No ticket booth.', None)), img_shot('gv_d10.jpg', 'up')],
 's12c': [img_shot('gv_d14.jpg', 'in', ('Heat on your face', 'cold desert night on your back')), img_shot('gv_d08.jpg', 'right', ('Best time: after sunset', None)), img_shot('gv_d17.jpg', 'in')],
 's13': [img_shot('gv_d16.jpg', 'in', ('A national problem', None)), card(orders_card)],
 's14': [card(nasa_card), img_shot('gv_n02.jpg', 'in', ('February 2022  →  May 2025', 'NASA / CIRA satellite view')), img_shot('gv_n03.jpg', 'in', ('Wells drilled nearby', 'to pull the gas away'))],
 's15': [card(methane_card)],
 's16': [card(gwp_card)],
 's16b': [img_shot('gv_c01.jpg', 'right', ('CENTRALIA, PENNSYLVANIA', 'coal-mine fire since 1962')), img_shot('gv_c04.jpg', 'in', None), img_shot('gv_c03.jpg', 'in', ('Almost the entire town was abandoned', None), glitch=False), img_shot('gv_c02.jpg', 'up', ('Smoke still rises from the ground', None))],
 's16c': [img_shot('gv_y01.jpg', 'right', ('YANAR DAG, AZERBAIJAN', '"the burning mountain" near Baku')), img_shot('gv_y03.jpg', 'in'), card(baba_card), img_shot('gv_o01.jpg', 'in', ('CHIMAERA, TÜRKIYE', 'flames escaping the rocks')), img_shot('gv_o01.jpg', 'left', ('"Ancient sailors used them like a lighthouse"', 'as the legend goes'))],
 's16d': [card(mix_card)],
 's17': [card(map_out), img_shot('gv_d18.jpg', 'in', ('A glitch in the desert', 'for almost forty years')), card(question_card)],
 's18': [card(endcard, glitch=False)],
}
CHAPTERS = {'s03': (1, 'Where is this?'), 's05': (2, 'The story everyone tells'), 's07': (3, 'The glitch in the story'),
            's10': (4, 'The man who went inside'), 's12b': (5, 'Can you go there?'), 's13': (6, 'Put it out'),
            's14': (7, 'It\'s working — and that\'s the problem'), 's16b': (8, 'Other doors to hell'), 's17': (9, 'Ending')}

def build_timeline():
    shots = []
    order = list(TIM.keys())
    for sid in order:
        seg = TIM[sid]; a, b = seg['start'], seg['end']
        if sid == 's18': b += END_EXTRA
        lst = SEG[sid]; n = len(lst)
        # weights: cards get more time
        wts = [1.6 if s['kind'] == 'card' and sid not in ('s01',) else 1.0 for s in lst]
        if sid == 's01': wts = [0.75, 1, 1, 1.3]
        tot = sum(wts); t = a
        for s, w in zip(lst, wts):
            d = (b - a) * w / tot
            shots.append(dict(s, start=t, end=t + d, seg=sid, chapter=CHAPTERS.get(sid) if s is lst[0] else None))
            t += d
    return shots

TEXT_CACHE = {}
def render_shot_frame(sh, tl, k):
    dur = sh['end'] - sh['start']; p = tl / dur
    if sh['kind'] == 'card':
        fr = sh['fn'](p, tl, dur).convert('RGBA')
    elif sh['kind'] == 'text':
        fr = Image.blend(kenburns(sh['bg'], p, 'in', 0.1), Image.new('RGB', (W, H), (0, 0, 0)), 0.55).convert('RGBA')
        key = ('ctr', sh['big'])
        if key not in TEXT_CACHE: TEXT_CACHE[key] = center(sh['big'], 110, sh['sub'])
        L = TEXT_CACHE[key]
        if p > 0.15: fr.alpha_composite(L)
    else:
        fr = kenburns(sh['name'], p, sh['move'], sh['amt'], sh['focus'], sh['darken']).convert('RGBA')
        if sh['text']:
            key = ('low',) + tuple(sh['text'])
            if key not in TEXT_CACHE: TEXT_CACHE[key] = lower(*sh['text'])
            L = TEXT_CACHE[key]
            a = min(1, max(0, (tl - 0.35) / 0.35)) * min(1, max(0, (dur - tl) / 0.3))
            if a > 0:
                if a < 1: L = L.copy(); L.putalpha(L.split()[3].point(lambda v: int(v * a)))
                fr.alpha_composite(L)
        key = ('cred', sh['name'])
        if key not in TEXT_CACHE: TEXT_CACHE[key] = credit_layer(sh['name'])
        if TEXT_CACHE[key]: fr.alpha_composite(TEXT_CACHE[key])
    if sh['seg'] in ('s03', 's17') and sh['kind'] == 'card' and sh['fn'] in (map_in, map_out):
        key = ('cred', 'kk_s2.jpg')
        if key not in TEXT_CACHE: TEXT_CACHE[key] = credit_layer('kk_s2.jpg')
        fr.alpha_composite(TEXT_CACHE[key])
    if sh['chapter'] and tl < 3.2:
        key = ('ch',) + sh['chapter']
        if key not in TEXT_CACHE: TEXT_CACHE[key] = chapter_layer(*sh['chapter'])
        L = TEXT_CACHE[key]; a = min(1, tl / 0.3) * min(1, (3.2 - tl) / 0.4)
        if a < 1: L = L.copy(); L.putalpha(L.split()[3].point(lambda v: int(v * a)))
        fr.alpha_composite(L)
    if sh['seg'] != 's18' and sh['start'] > 3.5:
        fr.alpha_composite(BUG)
    a = finish(fr.convert('RGB'), k, grade=sh['kind'] != 'card' or sh['seg'] in ('s01', 's17', 's14'))
    if sh.get('glitch', True) and tl < 0.2 and sh['start'] > 0:
        a = glitch_np(a, 1 - tl / 0.2, int(sh['start'] * 100) + int(tl * 30))
    if sh['start'] == 0 and tl < 0.12:  # flash-in from black on frame 1-3
        a = (a * (0.4 + 5 * tl)).clip(0, 255).astype(np.uint8)
    return a

def main():
    shots = build_timeline()
    json.dump([{k: v for k, v in s.items() if k not in ('fn',)} for s in shots], open(OUT + 'shots.json', 'w'), indent=1, default=str)
    t0, t1, out = 0.0, TOTAL, OUT + 'video.mp4'
    if '--preview' in sys.argv:
        i = sys.argv.index('--preview'); t0, t1 = float(sys.argv[i + 1]), float(sys.argv[i + 2]); out = OUT + 'preview_v.mp4'
    if '--still' in sys.argv:
        for ts in [float(x) for x in sys.argv[sys.argv.index('--still') + 1].split(',')]:
            sh = next(s for s in shots if s['start'] <= ts < s['end'])
            Image.fromarray(render_shot_frame(sh, ts - sh['start'], 0)).save(OUT + f'still_{ts:06.1f}.jpg', quality=85)
        return
    nf = int(round((t1 - t0) * FPS))
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-tune', 'film', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    si = 0
    for k in range(nf):
        t = t0 + k / FPS
        while si < len(shots) - 1 and t >= shots[si]['end']: si += 1
        while si > 0 and t < shots[si]['start']: si -= 1
        sh = shots[si]
        p.stdin.write(render_shot_frame(sh, t - sh['start'], k).tobytes())
        if k % 600 == 0: print(f'{k}/{nf}', flush=True)
    p.stdin.close(); p.wait()
    print('done', out)

if __name__ == '__main__':
    main()
