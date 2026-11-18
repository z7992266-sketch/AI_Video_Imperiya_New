"""GLITCHVERSE — Darvaza flagship renderer (1920x1080, 30 fps).
Usage: python3 build.py [--preview START END] -> writes video-only mp4 (frames piped to ffmpeg)."""
import json, math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = '/home/claude/gv/'
A = S + 'assets/'
OUT = S + 'out/'
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
for e in json.load(open(S + 'credits.json')):
    lic = e['license']
    CRED[e['file']] = f"{e['credit']} · {lic}" + ('' if ('Public' in lic or lic=='CC0') else ' · Wikimedia Commons')
EOX = 'Sentinel-2 cloudless 2016 by EOX · CC BY 4.0 · contains modified Copernicus Sentinel data'
for k in ('gvr_s2_wide.jpg','gvr_s2_mid.jpg','gvr_s2_close.jpg'): CRED[k] = EOX

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

