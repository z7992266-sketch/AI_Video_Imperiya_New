#!/usr/bin/env python3
"""BILASIZMI? — animated "did you know" Shorts template (Taqqos, 1080x1920, 30 fps).

Usage: python3 render/bilasizmi.py job.json out.mp4      (prints one JSON info line, writes out.jpg thumb)

Every fact photo sits INSIDE a cartoon cloud (puffy white edge, drop shadow, thought-bubble tail,
gentle bob, Ken Burns inside) that pops in elastically and "poofs" into the next one. Around it:
sparkles, "?"/"!" bubbles, stars, a hand-drawn arrow, a light bulb / globe icon, rising particles,
rotating sunburst on a bright Taqqos gradient. Big bouncing "BILASIZMI?" hook title (then docks as a
header), small TAQQOS label top-right, rolling number counters, word-by-word captions with a yellow
highlight on the spoken word, small image credit per photo, 2 s+ end card (question + subscribe).
Text stays out of the top 12 % and bottom 18 % (Shorts UI). Audio: voice + generated soft music bed
(ducked) + SFX at the kit default (render.SFX_GAIN = 40 %), two-pass loudnorm to -14 LUFS.

Job JSON:
{
  "template": "bilasizmi",              # render.yml routes jobs with this field here
  "name": "taqqos_bil_20261110_landlocked",
  "title": "BILASIZMI?",                # hook title (bounces in during the first ~1.5 s)
  "brand": "TAQQOS",
  "voice": {"src": "render/assets/<job>/voice.mp3" | "https://...", "start": 0.25,
            "max_pause": 0.12, "fit": 32.5, "tempo": 1.0},   # optional pause compression / speed-up
  "words": [{"w": "Bilasizmi?", "t0": 0.14, "t1": 1.12}, ...],  # voice-file timing (ElevenLabs transcript)
  "facts": [
    {"text": "short label (optional)", "image": "https://upload.wikimedia.org/...jpg" | "render/assets/...jpg",
     "credit": "Foto: NASA / Apollo 17 (PD)",
     "at": 0 | "at_word": "Ulardan",        # fact start: seconds (voice-file timeline) or first matching word
     "focus": [0.5, 0.45],                  # optional Ken Burns focus point (0..1)
     "number": {"value": 447400, "from": 0, "suffix": " km²", "prefix": "", "label": "MAYDONI",
                "at_word": "to'rt", "dur": 1.1, "decimals": 0}       # or a list of such dicts
    }, ...
  ],
  "endcard": {"at_word": "Siz", "dur": 2.0, "title": "Siz bilarmidingiz?", "line": "Izohda yozing",
              "button": "Obuna bo‘ling"},
  "music": {"gen": "bright", "volume": 0.13} | {"src": "...mp3", "volume": 0.13} | false,
  "sfx": true,
  "captions": {"max_words": 3, "size": 74}
}
Words match "at_word" case-insensitively ignoring punctuation/apostrophes, searching forward from the
previous fact's start. Durations: total = end-card start + end-card dur (at least voice end + 0.4 s).
"""
import json, math, os, re, subprocess, sys, random, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render as R   # fetch, gen_events, compress_pauses, gen_music, probe_dur, sh, SFX_GAIN

try:
    import cv2
    cv2.setNumThreads(2)
except Exception:  # pragma: no cover
    cv2 = None

W, H, FPS = 1080, 1920, 30
SAFE_T, SAFE_B = int(H * 0.12), int(H * 0.82)          # 230 .. 1574
FONT_DIRS = [os.path.join(HERE, 'fonts'), '/usr/share/fonts/opentype/inter', '/usr/share/fonts/truetype/google-fonts']
_fc = {}


def font(name, size):
    k = (name, int(size))
    if k not in _fc:
        for d in FONT_DIRS:
            p = os.path.join(d, name)
            if os.path.exists(p):
                _fc[k] = ImageFont.truetype(p, int(size))
                break
        else:
            alt = {'InterDisplay-Black.otf': 'InterDisplay-ExtraBold.otf', 'Inter-SemiBold.otf': 'Inter-Bold.otf'}.get(name)
            _fc[k] = font(alt, size) if alt else ImageFont.load_default()
    return _fc[k]


BLACK, XB, BOLD, SEMI = 'InterDisplay-Black.otf', 'InterDisplay-ExtraBold.otf', 'Inter-Bold.otf', 'Inter-SemiBold.otf'
# Taqqos palette (navy / gold / yellow / teal) made bright for this template
NAVY = (14, 22, 52); INK = (18, 24, 48); GOLD = (243, 196, 72); YEL = (255, 213, 79); WHITE = (255, 255, 255)
TEAL = (0, 178, 206); CORAL = (255, 107, 107); PINK = (255, 92, 168); MINT = (64, 224, 170)
A = '‘'


# ---------------------------------------------------------------- easing
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def eio(x): x = cl(x); return 3 * x * x - 2 * x * x * x
def eback(x, s=2.0): x = cl(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def eelastic(x):
    x = cl(x)
    if x <= 0 or x >= 1: return x
    return 2 ** (-9 * x) * math.sin((x * 9 - 0.75) * (2 * math.pi / 3.2)) + 1
def lerp(a, b, t): return a + (b - a) * t
def epop(x):
    """Springy pop-in: 0 -> ~1.13 overshoot -> settles at 1 (x = 0..1)."""
    x = cl(x)
    return 1.0 if x >= 1 else 1 - math.exp(-7 * x) * math.cos(11 * x) * (1 - x) ** 0.5


# ---------------------------------------------------------------- numpy compositing
def blend(dst, rgba, x, y, alpha=1.0):
    """Alpha-blend an RGBA uint8 array onto dst (H,W,3 uint8) at integer top-left x,y (clipped)."""
    if alpha <= 0.004 or rgba is None:
        return
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = src[..., 3:4].astype(np.float32) * (alpha / 255.0)
    reg = dst[y0:y1, x0:x1]
    reg[..., :3] = (reg[..., :3].astype(np.float32) * (1 - a) + src[..., :3].astype(np.float32) * a).astype(np.uint8)
    if dst.shape[2] == 4:
        reg[..., 3] = np.maximum(reg[..., 3], (a[..., 0] * 255).astype(np.uint8))


def add_glow(dst, rgba, x, y, alpha=1.0):
    """Additive (screen-like) blend for glows/particles."""
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0 or alpha <= 0.004:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    a = src[..., 3:4].astype(np.float32) * (alpha / 255.0)
    reg = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = np.minimum(255, reg + src[..., :3].astype(np.float32) * a).astype(np.uint8)


def blend_c(dst, rgba, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    """Blend centred at (cx, cy) with optional scale / rotation (degrees)."""
    if rgba is None or scale <= 0.02 or alpha <= 0.004:
        return
    im = rgba
    if abs(scale - 1) > 0.003 or abs(rot) > 0.05:
        h, w = im.shape[:2]
        if cv2 is not None:
            if abs(rot) > 0.05:
                diag = int(math.hypot(w, h) * scale) + 4
                M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
                M[0, 2] += diag / 2 - w / 2; M[1, 2] += diag / 2 - h / 2
                im = cv2.warpAffine(im, M, (diag, diag), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
            else:
                im = cv2.resize(im, (max(1, int(w * scale)), max(1, int(h * scale))),
                                interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        else:
            p = Image.fromarray(im).resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
            if abs(rot) > 0.05:
                p = p.rotate(rot, expand=True, resample=Image.BILINEAR)
            im = np.asarray(p)
    h, w = im.shape[:2]
    blend(dst, im, int(round(cx - w / 2)), int(round(cy - h / 2)), alpha)


def pil2np(im): return np.asarray(im.convert('RGBA')).copy()


# ---------------------------------------------------------------- shapes
def cloud_mask(w, h, seed=1, ss=2):
    """Puffy cloud silhouette (L mask, w x h) made of a rounded body + perimeter puffs."""
    rnd = random.Random(seed)
    Wm, Hm = w * ss, h * ss
    m = Image.new('L', (Wm, Hm), 0)
    d = ImageDraw.Draw(m)
    pad = int(min(Wm, Hm) * 0.11)
    bx0, by0, bx1, by1 = pad, pad, Wm - pad, Hm - pad
    d.rounded_rectangle([bx0, by0, bx1, by1], int(min(Wm, Hm) * 0.16), fill=255)
    # puffs along the body perimeter
    per = 2 * ((bx1 - bx0) + (by1 - by0))
    n = 22
    for i in range(n):
        u = (i + rnd.uniform(-0.12, 0.12)) / n * per
        if u < bx1 - bx0:
            px, py = bx0 + u, by0
        elif u < (bx1 - bx0) + (by1 - by0):
            px, py = bx1, by0 + (u - (bx1 - bx0))
        elif u < 2 * (bx1 - bx0) + (by1 - by0):
            px, py = bx1 - (u - (bx1 - bx0) - (by1 - by0)), by1
        else:
            px, py = bx0, by1 - (u - 2 * (bx1 - bx0) - (by1 - by0))
        r = pad * rnd.uniform(0.95, 1.35)
        # pull puffs slightly inwards so they never touch the canvas edge
        cxm, cym = Wm / 2, Hm / 2
        px = cxm + (px - cxm) * 0.985; py = cym + (py - cym) * 0.985
        r = min(r, px - 2, py - 2, Wm - px - 2, Hm - py - 2)
        d.ellipse([px - r, py - r, px + r, py + r], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(ss * 1.2)).point(lambda v: 255 if v > 127 else 0)
    return m.resize((w, h), Image.LANCZOS)


def erode(mask, px):
    a = np.asarray(mask)
    if cv2 is not None:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px + 1, 2 * px + 1))
        return Image.fromarray(cv2.erode(a, k))
    return mask.filter(ImageFilter.MinFilter(2 * (px // 2) + 1))


def star_poly(cx, cy, r, points=5, inner=0.45, rot=-90):
    pts = []
    for i in range(points * 2):
        a = math.radians(rot + i * 180 / points)
        q = r if i % 2 == 0 else r * inner
        pts.append((cx + q * math.cos(a), cy + q * math.sin(a)))
    return pts


def sprite_sparkle(r, col=WHITE):
    s = int(r * 2.6); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = s / 2
    pts = []
    for i in range(8):
        a = math.radians(-90 + i * 45); q = r if i % 2 == 0 else r * 0.22
        pts.append((c + q * math.cos(a), c + q * math.sin(a)))
    g = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([c - r * 0.6, c - r * 0.6, c + r * 0.6, c + r * 0.6], fill=col + (110,))
    im = Image.alpha_composite(im, g.filter(ImageFilter.GaussianBlur(r * 0.35)))
    ImageDraw.Draw(im).polygon(pts, fill=col + (255,))
    return pil2np(im)


def sprite_star(r, col=YEL):
    s = int(r * 2.5); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = star_poly(s / 2, s / 2 + 2, r, 5, 0.48)
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon([(x, y + 4) for x, y in pts], fill=(10, 10, 40, 90))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(im); d.polygon(pts, fill=col + (255,), outline=(255, 255, 255, 255), width=max(2, int(r * 0.12)))
    return pil2np(im)


def sprite_badge(ch, r, bg, fg=WHITE):
    """Round flat bubble with a big glyph ("?" or "!") and a soft shadow."""
    s = int(r * 2.6); im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    c = s / 2
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([c - r, c - r + r * 0.16, c + r, c + r + r * 0.16], fill=(10, 10, 40, 110))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(r * 0.12)))
    d = ImageDraw.Draw(im)
    d.ellipse([c - r, c - r, c + r, c + r], fill=bg + (255,), outline=(255, 255, 255, 255), width=max(3, int(r * 0.1)))
    d.ellipse([c - r * 0.62, c - r * 0.78, c - r * 0.18, c - r * 0.46], fill=(255, 255, 255, 90))
    f = font(BLACK, int(r * 1.35))
    d.text((c, c + r * 0.04), ch, font=f, fill=fg + (255,), anchor='mm')
    return pil2np(im)


def sprite_bulb(r):
    s = int(r * 3.0); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c = s / 2
    glow = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([c - r * 1.25, c - r * 1.35, c + r * 1.25, c + r * 1.15], fill=YEL + (120,))
    im = Image.alpha_composite(im, glow.filter(ImageFilter.GaussianBlur(r * 0.35)))
    d = ImageDraw.Draw(im)
    lw = max(3, int(r * 0.09))
    d.ellipse([c - r * 0.8, c - r * 1.0, c + r * 0.8, c + r * 0.55], fill=YEL + (255,), outline=INK + (255,), width=lw)
    d.rounded_rectangle([c - r * 0.42, c + r * 0.45, c + r * 0.42, c + r * 0.95], int(r * 0.12), fill=(200, 205, 220, 255), outline=INK + (255,), width=lw)
    d.line([c - r * 0.34, c + r * 0.62, c + r * 0.34, c + r * 0.62], fill=INK + (255,), width=lw)
    d.line([c - r * 0.34, c + r * 0.78, c + r * 0.34, c + r * 0.78], fill=INK + (255,), width=lw)
    d.arc([c - r * 0.5, c - r * 0.75, c + r * 0.1, c - r * 0.05], 180, 260, fill=(255, 255, 255, 230), width=lw)
    for k in range(5):  # rays
        a = math.radians(-90 + (k - 2) * 38)
        d.line([c + r * 1.05 * math.cos(a), c - r * 0.25 + r * 1.05 * math.sin(a), c + r * 1.38 * math.cos(a), c - r * 0.25 + r * 1.38 * math.sin(a)], fill=YEL + (255,), width=lw + 1)
    return pil2np(im)


def sprite_globe(r):
    s = int(r * 2.6); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c = s / 2
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([c - r, c - r + 8, c + r, c + r + 8], fill=(10, 10, 40, 100))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(5)))
    d = ImageDraw.Draw(im); lw = max(3, int(r * 0.08))
    d.ellipse([c - r, c - r, c + r, c + r], fill=(66, 165, 245, 255), outline=INK + (255,), width=lw)
    # flat continents
    d.polygon([(c - r * 0.6, c - r * 0.5), (c - r * 0.1, c - r * 0.7), (c + r * 0.05, c - r * 0.3), (c - r * 0.25, c + r * 0.05), (c - r * 0.55, c - r * 0.05)], fill=MINT + (255,))
    d.polygon([(c + r * 0.15, c + r * 0.05), (c + r * 0.65, c - r * 0.15), (c + r * 0.7, c + r * 0.35), (c + r * 0.3, c + r * 0.75), (c + r * 0.05, c + r * 0.45)], fill=MINT + (255,))
    d.arc([c - r * 0.45, c - r, c + r * 0.45, c + r], 0, 360, fill=INK + (120,), width=max(2, lw // 2))
    d.line([c - r, c, c + r, c], fill=INK + (120,), width=max(2, lw // 2))
    d.ellipse([c - r, c - r, c + r, c + r], outline=INK + (255,), width=lw)
    return pil2np(im)


def sprite_arrow(length=210, curve=0.35, col=WHITE, width=12):
    """Hand-drawn curved arrow pointing right; returns list of points + head for draw-on animation."""
    pts = []
    for i in range(41):
        u = i / 40
        x = u * length
        y = -math.sin(u * math.pi) * length * curve
        pts.append((x, y))
    return pts


def dot_sprite(r, col):
    s = int(r * 4); im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse([s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r], fill=col + (255,))
    im = im.filter(ImageFilter.GaussianBlur(r * 0.6))
    return pil2np(im)


# ---------------------------------------------------------------- text sprites
_tcache = {}


def text_sprite(txt, fname, size, fill=WHITE, stroke=0, stroke_fill=INK, shadow=0, key=None):
    k = key or (txt, fname, size, fill, stroke, stroke_fill, shadow)
    if k in _tcache:
        return _tcache[k]
    f = font(fname, size)
    bb = f.getbbox(txt, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 8 + shadow * 2, bb[3] - bb[1] + 8 + shadow * 2
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((4 - bb[0] + shadow * 0.5, 4 - bb[1] + shadow * 1.2), txt, font=f, fill=(8, 10, 40, 150), stroke_width=stroke, stroke_fill=(8, 10, 40, 150))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(shadow * 0.6)))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), txt, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=stroke_fill + (255,))
    _tcache[k] = pil2np(im)
    return _tcache[k]


# ---------------------------------------------------------------- background
class Background:
    """Bright Taqqos gradient (teal -> royal blue -> violet) with drifting colour blobs and a slow sunburst."""
    def __init__(self, cx, cy):
        self.lw, self.lh = 270, 480
        y = np.linspace(0, 1, self.lh, dtype=np.float32)[:, None]
        x = np.linspace(0, 1, self.lw, dtype=np.float32)[None, :]
        self.X, self.Y = x, y
        top, mid, bot = np.array([0, 182, 214], np.float32), np.array([38, 92, 230], np.float32), np.array([112, 52, 206], np.float32)
        t1 = np.clip(y / 0.55, 0, 1)[..., None]; t2 = np.clip((y - 0.55) / 0.45, 0, 1)[..., None]
        base = top * (1 - t1) + mid * t1
        base = base * (1 - t2) + bot * t2
        self.base = np.broadcast_to(base, (self.lh, self.lw, 3)).copy()
        self.blobs = [((255, 120, 200), 0.85, 0.20, 0.30, 0.35, 0.10, 0.0), ((0, 230, 210), 0.12, 0.62, 0.30, 0.30, 0.08, 1.7),
                      ((255, 210, 90), 0.70, 0.88, 0.28, 0.30, 0.09, 3.1), ((120, 160, 255), 0.25, 0.15, 0.25, 0.30, 0.12, 4.2)]
        dx = (x - cx / W) * (W / H); dy = (y - cy / H)
        self.theta = np.arctan2(dy, dx).astype(np.float32)
        rr = np.sqrt(dx ** 2 + dy ** 2)
        self.ray_fall = (np.clip(1.0 - rr / 0.75, 0, 1) ** 1.2).astype(np.float32)
        vg = np.clip((np.sqrt(((x - 0.5) / 0.75) ** 2 + ((y - 0.5) / 0.62) ** 2) - 0.55) / 0.6, 0, 1) ** 1.6
        self.vig = (1 - 0.35 * vg)[..., None].astype(np.float32)
        rnd = random.Random(11)
        self.parts = [(rnd.random(), rnd.random(), rnd.uniform(0.4, 1.0), rnd.uniform(0, 6.28), rnd.choice([WHITE, WHITE, YEL, (180, 240, 255)])) for _ in range(46)]
        self.dots = {}

    def frame(self, t, energy=1.0):
        img = self.base.copy()
        for col, cx, cy, r, inten, sp, ph in self.blobs:
            px = cx + 0.12 * math.sin(t * sp * 2 + ph); py = cy + 0.08 * math.cos(t * sp * 1.6 + ph * 0.7)
            g = np.exp(-(((self.X - px)) ** 2 + ((self.Y - py) * 0.56) ** 2) / (r * r * 0.25))
            img += g[..., None] * (np.array(col, np.float32) - img) * inten * 0.55
        rays = 0.5 + 0.5 * np.cos(14 * self.theta - t * 0.35)
        rays = np.clip((rays - 0.45) * 4, 0, 1) * self.ray_fall * 0.13 * energy
        img = img * (1 - rays[..., None]) + 255 * rays[..., None]
        img = np.clip(img * self.vig, 0, 255).astype(np.uint8)
        if cv2 is not None:
            out = cv2.resize(img, (W, H), interpolation=cv2.INTER_LINEAR)
        else:
            out = np.asarray(Image.fromarray(img).resize((W, H), Image.BILINEAR)).copy()
        for (px, py, z, ph, col) in self.parts:  # rising particles
            yy = (py - t * 0.03 * z) % 1.0; xx = px + 0.012 * math.sin(t * 0.9 + ph)
            a = (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2.2 + ph))) * z * 0.85
            r = int(2 + 4 * z)
            k = (r, col)
            if k not in self.dots:
                self.dots[k] = dot_sprite(r, col)
            sp = self.dots[k]
            add_glow(out, sp, int(xx * W - sp.shape[1] / 2), int(yy * H - sp.shape[0] / 2), a)
        return out


# ---------------------------------------------------------------- photo cloud card
class CloudCard:
    def __init__(self, img_path, cw, ch, seed, focus=(0.5, 0.5), credit=None, plain=False, zoom=(1.0, 1.12)):
        self.zoom = zoom
        self.cw, self.ch = cw, ch
        self.tail_side = 1 if seed % 2 else -1
        pad = 60   # room for the shadow
        self.pad = pad
        mask = cloud_mask(cw, ch, seed=seed)
        inner = erode(mask, 20)
        self.inner = np.asarray(inner, np.float32)[..., None] / 255.0
        ring = erode(mask, 12)
        # base layer: shadow + white cloud + faint inner ring
        base = Image.new('RGBA', (cw + 2 * pad, ch + 2 * pad), (0, 0, 0, 0))
        shadow = Image.new('RGBA', base.size, (0, 0, 0, 0))
        shadow.paste(Image.new('RGBA', (cw, ch), (10, 14, 60, 120)), (pad, pad + 26), mask)
        base = Image.alpha_composite(base, shadow.filter(ImageFilter.GaussianBlur(18)))
        white = Image.new('RGBA', base.size, (0, 0, 0, 0))
        white.paste(Image.new('RGBA', (cw, ch), (255, 255, 255, 255)), (pad, pad), mask)
        # soft blue-ish inner shading of the cloud rim (gives it volume)
        shade = Image.new('RGBA', base.size, (0, 0, 0, 0))
        shade.paste(Image.new('RGBA', (cw, ch), (205, 220, 245, 255)), (pad, pad + 8), ring)
        white = Image.alpha_composite(white, Image.composite(shade, Image.new('RGBA', base.size, (0, 0, 0, 0)), white.split()[3]))
        base = Image.alpha_composite(base, white)
        if plain:
            wi = Image.new('RGBA', base.size, (0, 0, 0, 0))
            wi.paste(Image.new('RGBA', (cw, ch), (255, 255, 255, 255)), (pad, pad), erode(mask, 22).filter(ImageFilter.GaussianBlur(6)))
            base = Image.alpha_composite(base, wi)
        if not plain:
            rim = Image.new('RGBA', base.size, (0, 0, 0, 0))
            rim.paste(Image.new('RGBA', (cw, ch), (150, 170, 210, 255)), (pad, pad), erode(mask, 17))
            base = Image.alpha_composite(base, rim)
        self.base = pil2np(base)
        self.ix0, self.iy0 = pad, pad
        self.plain = plain
        self.src = None
        if img_path and not plain:
            im = Image.open(img_path).convert('RGB')
            # cover-fit to 1.22x the cloud box, so Ken Burns has room
            k = max(cw * 1.22 / im.width, ch * 1.22 / im.height)
            im = im.resize((max(cw, int(im.width * k)), max(ch, int(im.height * k))), Image.LANCZOS)
            # gentle "clean" grade: a touch of contrast/saturation
            a = np.asarray(im).astype(np.float32)
            mean = a.mean(axis=(0, 1), keepdims=True)
            a = (a - mean) * 1.06 + mean
            gray = a.mean(axis=2, keepdims=True)
            a = gray + (a - gray) * 1.12
            self.src = np.clip(a, 0, 255).astype(np.uint8)
        self.focus = focus
        self.credit = credit

    def render(self, u):
        """u = 0..1 progress through the fact (Ken Burns). Returns RGBA array."""
        out = self.base.copy()
        if self.src is None:
            return out
        sh_, sw_ = self.src.shape[:2]
        z = lerp(self.zoom[0], self.zoom[1], eio(u))
        vw, vh = sw_ / 1.0, sh_ / 1.0
        # visible window (in src pixels) = cloud box * (src_scale / z)
        scale = min(sw_ / (self.cw * 1.0), sh_ / (self.ch * 1.0)) / 1.0
        ww, hh = self.cw * scale / z / 1.0, self.ch * scale / z / 1.0
        ww, hh = min(ww, sw_), min(hh, sh_)
        fx, fy = self.focus
        cx = lerp(sw_ / 2, fx * sw_, eio(u)); cy = lerp(sh_ / 2, fy * sh_, eio(u))
        x0 = cl(cx - ww / 2, 0, sw_ - ww); y0 = cl(cy - hh / 2, 0, sh_ - hh)
        sx = self.cw / ww
        M = np.array([[sx, 0, -x0 * sx], [0, sx, -y0 * sx]], np.float32)
        if cv2 is not None:
            ph = cv2.warpAffine(self.src, M, (self.cw, self.ch), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        else:
            ph = np.asarray(Image.fromarray(self.src).transform((self.cw, self.ch), Image.AFFINE,
                            (1 / sx, 0, x0, 0, 1 / sx, y0), Image.BILINEAR))
        p, m = self.pad, self.inner
        reg = out[p:p + self.ch, p:p + self.cw]
        rgb = reg[..., :3].astype(np.float32) * (1 - m) + ph.astype(np.float32) * m
        reg[..., :3] = rgb.astype(np.uint8)
        reg[..., 3] = np.maximum(reg[..., 3], (m[..., 0] * 255).astype(np.uint8))
        return out


def tail_bubbles(cloud_cx, cloud_bottom, side):
    """Thought-bubble tail: three shrinking puffs leaving the cloud's lower corner."""
    bx = cloud_cx + side * 330
    return [(bx, cloud_bottom + 34, 34), (bx + side * 52, cloud_bottom + 92, 22), (bx + side * 86, cloud_bottom + 134, 13)]


_bubble_cache = {}


def bubble_sprite(r):
    if r not in _bubble_cache:
        s = int(r * 2 + 40); im = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c = s / 2
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([c - r, c - r + 10, c + r, c + r + 10], fill=(10, 14, 60, 110))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(7)))
        d = ImageDraw.Draw(im); d.ellipse([c - r, c - r, c + r, c + r], fill=(255, 255, 255, 255))
        d.ellipse([c - r * 0.75, c - r * 0.55 + 4, c + r * 0.75, c + r * 0.85], fill=(222, 232, 248, 255))
        d.ellipse([c - r * 0.82, c - r * 0.82, c + r * 0.6, c + r * 0.6], fill=(255, 255, 255, 255))
        _bubble_cache[r] = pil2np(im)
    return _bubble_cache[r]


# ---------------------------------------------------------------- timing helpers
def norm_word(w):
    return re.sub(r"[^\w]", '', w.lower().replace('‘', '').replace("'", '').replace('’', '').replace('`', ''))


def find_word(words, target, start_idx=0):
    tn = norm_word(target)
    for i in range(start_idx, len(words)):
        if norm_word(words[i]['w']) == tn:
            return i
    for i in range(start_idx, len(words)):  # prefix fallback
        if norm_word(words[i]['w']).startswith(tn):
            return i
    return None


def caption_groups(words, maxw=3, maxc=17):
    groups, g = [], []
    SHORT = {'va', 'bu', 'u', 'ham', 'eng', 'bir'}
    for i, wt in enumerate(words):
        g.append(wt)
        nxt = words[i + 1] if i + 1 < len(words) else None
        pause = nxt is not None and nxt['t0'] - wt['t1'] > 0.25
        punct = re.search(r'[.!?,:;—]$', wt['w'])
        full = len(g) >= maxw or sum(len(x['w']) for x in g) + len(g) > maxc
        if punct or pause or nxt is None:
            groups.append(g); g = []
        elif full:
            if norm_word(wt['w']) in SHORT and len(g) > 1:
                last = g.pop(); groups.append(g); g = [last]
            else:
                groups.append(g); g = []
    if g:
        groups.append(g)
    return groups


def fmt_num(v, decimals=0):
    if decimals:
        s = ('%.' + str(decimals) + 'f') % v
        a, b = s.split('.')
    else:
        a, b = str(int(round(v))), None
    neg = a.startswith('-'); a = a.lstrip('-')
    grp = []
    while len(a) > 3:
        grp.insert(0, a[-3:]); a = a[:-3]
    grp.insert(0, a)
    s = ('−' if neg else '') + ' '.join(grp)
    return s + (',' + b if b else '')


# ---------------------------------------------------------------- music bed
def gen_bright_music(dur, path, seed=5):
    """Soft, copyright-free 'curious' bed: plucked major arpeggio + warm pad + light shaker, ~104 bpm."""
    sr = 48000
    n = int((dur + 1.5) * sr)
    t = np.arange(n, dtype=np.float32) / sr
    out = np.zeros(n, np.float32)
    bpm = 104.0; step = 60.0 / bpm / 2   # eighth notes
    chords = [(60, 64, 67, 72), (55, 59, 62, 67), (57, 60, 64, 69), (53, 57, 60, 65)]  # C G Am F
    patt = [0, 2, 1, 3, 2, 1, 3, 2]
    mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12.0)
    nsteps = int(dur / step) + 2
    for k in range(nsteps):
        st = k * step
        ch = chords[(k // 8) % 4]
        note = ch[patt[k % 8]] + 12
        f = mtof(note)
        i0 = int(st * sr); L = int(min(0.9, step * 3) * sr)
        if i0 >= n:
            break
        L = min(L, n - i0)
        tt = np.arange(L, dtype=np.float32) / sr
        env = np.exp(-tt * 7.0) * np.minimum(1, tt / 0.004)
        tone = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt) + 0.12 * np.sin(2 * np.pi * 3 * f * tt)
        out[i0:i0 + L] += 0.16 * env * tone * (1.0 if k % 2 == 0 else 0.75)
    # pad (chord roots + fifths, slow attack)
    bar = step * 8
    for b in range(int(dur / bar) + 2):
        ch = chords[b % 4]
        i0 = int(b * bar * sr); L = min(int(bar * sr * 1.1), n - i0)
        if L <= 0:
            break
        tt = np.arange(L, dtype=np.float32) / sr
        env = np.minimum(1, tt / 0.5) * np.minimum(1, (bar * 1.1 - tt) / 0.4)
        for m in ch[:3]:
            f = mtof(m)
            out[i0:i0 + L] += 0.045 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 1.003 * tt))
        # soft bass on beat 1 and 3
        for off in (0, bar / 2):
            j0 = i0 + int(off * sr); Lb = min(int(0.5 * sr), n - j0)
            if Lb > 0:
                tb = np.arange(Lb, dtype=np.float32) / sr
                out[j0:j0 + Lb] += 0.18 * np.exp(-tb * 5) * np.sin(2 * np.pi * mtof(ch[0] - 24) * tb)
    # shaker on off-beats
    rng = np.random.default_rng(seed)
    for k in range(nsteps):
        if k % 2 == 1:
            i0 = int(k * step * sr); L = min(int(0.06 * sr), n - i0)
            if L > 0:
                tt = np.arange(L, dtype=np.float32) / sr
                nz = rng.standard_normal(L).astype(np.float32)
                nz = np.diff(np.concatenate([[0], nz]))   # crude high-pass
                out[i0:i0 + L] += 0.018 * nz * np.exp(-tt * 60)
    fade = np.minimum(1, t / 1.0)
    out *= fade
    out /= max(1e-6, np.abs(out).max()) / 0.5
    st = np.stack([out, np.roll(out, 240)], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype('<i2')
    import wave
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(pcm.tobytes())
    return path


# ---------------------------------------------------------------- main renderer
def main(job_path, out_path):
    job = json.load(open(job_path))
    R.WORK = os.environ.get('RENDER_WORK', R.WORK)
    os.makedirs(R.WORK, exist_ok=True)
    work = R.WORK

    # ---- voice + word timings (shifted to the absolute timeline, optional pause compression)
    v = dict(job.get('voice') or {})
    vstart = float(v.get('start', 0.25))
    words = [dict(w) for w in (job.get('words') or [])]
    for w in words:
        w['t0'] = float(w['t0']) + vstart; w['t1'] = float(w['t1']) + vstart
    vpath = None
    if v.get('src'):
        if v.get('max_pause') or v.get('fit'):
            shim = {'voice': dict(v, max_pause=v.get('max_pause', 9.0)), 'captions': {'words': words}}
            vpath = R.compress_pauses(shim, [], None, vstart)
        else:
            vpath = R.fetch(v['src'])
            if abs(float(v.get('tempo', 1)) - 1) > 0.005:
                tp = float(v['tempo'])
                vt = os.path.join(work, 'voice_tempo.wav')
                R.sh(['ffmpeg', '-y', '-i', vpath, '-af', 'atempo=%f' % tp, '-ar', '48000', vt])
                vpath = vt
                for w in words:
                    w['t0'] = vstart + (w['t0'] - vstart) / tp; w['t1'] = vstart + (w['t1'] - vstart) / tp
    vend = vstart + (R.probe_dur(vpath) if vpath else (words[-1]['t1'] - vstart if words else 25))
    words = [w for w in words if not re.fullmatch(r'\[.*\]|[—–-]', w['w'].strip())]

    # ---- facts timeline
    facts = job['facts']
    starts, idx = [], 0
    for i, f in enumerate(facts):
        if 'at' in f:
            # voice-file seconds -> timeline via nearest word mapping
            t = float(f['at'])
            st = 0.0 if t <= 0 else vstart + t
        elif f.get('at_word'):
            j = find_word(words, f['at_word'], idx)
            st = words[j]['t0'] - 0.12 if j is not None else (starts[-1] + 4 if starts else 0)
            f['_widx'] = j if j is not None else idx
            idx = (j or idx) + 1
        else:
            st = 0.0 if i == 0 else starts[-1] + 4
        starts.append(0.0 if i == 0 else st)
    ec = dict(job.get('endcard') or {})
    ec_dur = float(ec.get('dur', 2.0))
    ec_start = None
    if ec.get('at_word'):
        j = find_word(words, ec['at_word'], idx)
        if j is not None:
            ec_start = words[j]['t0'] - 0.1
    if ec_start is None:
        ec_start = vend + 0.2
    total = max(ec_start + ec_dur, vend + 0.45)
    ends = starts[1:] + [ec_start]
    nframes = int(math.ceil(total * FPS))

    # numbers
    for i, f in enumerate(facts):
        nums = f.get('number')
        nums = [] if not nums else (nums if isinstance(nums, list) else [nums])
        for nb in nums:
            if nb.get('at_word'):
                j = find_word(words, nb['at_word'], f.get('_widx', 0))
                nb['_t'] = words[j]['t0'] if j is not None else starts[i] + 0.6
            else:
                nb['_t'] = starts[i] + float(nb.get('delay', 0.7))
        f['_nums'] = nums

    # ---- layout
    CW, CH = int(job.get('cloud_w', 880)), int(job.get('cloud_h', 650))
    CX, CY = W // 2, int(job.get('cloud_y', 862))
    bg = Background(CX, CY)
    cards = []
    for i, f in enumerate(facts):
        p = R.fetch(f['image']) if f.get('image') else None
        cards.append(CloudCard(p, CW, CH, seed=3 + i, focus=tuple(f.get('focus', (0.5, 0.5))), zoom=tuple(f.get('zoom', (1.0, 1.12)))))
    ec_card = CloudCard(None, 900, 560, seed=21, plain=True)

    # sprites
    spark = sprite_sparkle(26); spark_y = sprite_sparkle(20, YEL); spark_s = sprite_sparkle(14)
    star = sprite_star(26); star_s = sprite_star(17, (255, 160, 90))
    qb = sprite_badge('?', 46, CORAL); eb = sprite_badge('!', 40, (255, 170, 30)); qb2 = sprite_badge('?', 36, (140, 90, 255))
    bulb = sprite_bulb(46); globe = sprite_globe(46)
    brand = text_sprite(job.get('brand', 'TAQQOS'), BLACK, 44, WHITE, stroke=0, shadow=6)
    title = job.get('title', 'BILASIZMI?')
    tsz = 170
    while font(BLACK, tsz).getlength(title) + 9 * 2 * len(title) * 0.5 > W - 110 and tsz > 60:
        tsz -= 4
    tf = font(BLACK, tsz)
    letters = [(ch, text_sprite(ch, BLACK, tsz, YEL if ch in '?!' else WHITE, stroke=9, stroke_fill=INK, shadow=10), tf.getlength(ch) + 9) for ch in title]
    lw_total = sum(l[2] for l in letters)
    cap = job.get('captions') or {}
    csize = int(cap.get('size', 74))
    groups = caption_groups([w for w in words if w['t0'] < ec_start - 0.05], int(cap.get('max_words', 3)))

    # decorations per fact: (sprite, rel_x, rel_y, phase, kind)
    deco_sets = [
        [(bulb, -455, -300, 0.0), (qb, 450, -290, 0.7), (eb, -470, 250, 1.4), (star, 455, 250, 2.1)],
        [(globe, 452, -300, 0.3), (qb2, -458, -270, 1.0), (star_s, -460, 270, 1.9), (eb, 462, 240, 2.4)],
        [(qb, -455, -300, 0.2), (star, 452, -310, 0.9), (bulb, 458, 248, 1.6), (qb2, -462, 262, 2.2)],
        [(eb, 450, -300, 0.4), (globe, -452, -290, 1.1), (qb, 462, 255, 1.8), (star_s, -462, 268, 2.6)],
    ]
    sparkle_pos = [(-380, -350), (390, -360), (-450, -110), (452, -120), (-300, 352), (320, 360), (0, -372)]

    # ---- SFX events
    ev = [{'t': 0.0, 'type': 'boom', 'volume': 0.8}, {'t': 0.05, 'type': 'riser', 'volume': 0.25}]
    for i, st in enumerate(starts):
        if i > 0:
            ev.append({'t': max(0, st - 0.22), 'type': 'whoosh', 'volume': 0.9})
        ev.append({'t': st + (0.0 if i == 0 else 0.05), 'type': 'pop', 'volume': 1.0})
        for nb in facts[i]['_nums']:
            d = float(nb.get('dur', 1.1))
            k = 0.0
            while k < d:
                ev.append({'t': nb['_t'] + k, 'type': 'tick', 'volume': 0.45}); k += 0.09
            ev.append({'t': nb['_t'] + d, 'type': 'ding', 'volume': 0.7})
    ev.append({'t': ec_start - 0.2, 'type': 'whoosh', 'volume': 0.9})
    ev.append({'t': ec_start + 0.05, 'type': 'pop', 'volume': 1.0})
    ev.append({'t': ec_start + 0.45, 'type': 'ding', 'volume': 0.6})

    # ---- frame loop -> ffmpeg
    vid_tmp = os.path.join(work, 'bil_video.mp4')
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                            '-c:v', 'libx264', '-preset', job.get('preset', 'medium'), '-crf', str(job.get('crf', 17)), '-pix_fmt', 'yuv420p', vid_tmp],
                           stdin=subprocess.PIPE)
    rnd = random.Random(7)
    confetti = [(rnd.uniform(-1, 1), rnd.uniform(-1.2, -0.3), rnd.choice([YEL, CORAL, MINT, PINK, WHITE, (120, 170, 255)]), rnd.uniform(0, 6.28), rnd.uniform(6, 12)) for _ in range(60)]
    conf_sprites = {}

    def confetti_burst(fr, t0, cx, cy, t, spread=520, n=60):
        dt = t - t0
        if dt < 0 or dt > 1.6:
            return
        for (vx, vy, col, ph, sz) in confetti[:n]:
            x = cx + vx * spread * eo(dt / 1.2)
            y = cy + vy * spread * 0.9 * eo(dt / 1.0) + 420 * dt * dt
            k = (col, int(sz))
            if k not in conf_sprites:
                im = Image.new('RGBA', (int(sz * 2.4), int(sz * 2.4)), (0, 0, 0, 0))
                ImageDraw.Draw(im).rounded_rectangle([sz * 0.4, sz * 0.8, sz * 2.0, sz * 1.6], 3, fill=col + (255,))
                conf_sprites[k] = pil2np(im)
            blend_c(fr, conf_sprites[k], x, y, 1.0, cl(1.6 - dt * 1.1), rot=math.degrees(ph + dt * 9))

    def poof(fr, t0, t, cx, cy):
        dt = t - t0
        if dt < 0 or dt > 0.55:
            return
        for k in range(14):
            a = k / 14 * 2 * math.pi
            rr = lerp(400, 560, eo(dt / 0.55))
            x = cx + math.cos(a) * rr * 1.02; y = cy + math.sin(a) * rr * 0.72
            blend_c(fr, bubble_sprite(26), x, y, lerp(1.0, 0.2, dt / 0.55), cl(1 - dt / 0.55))

    def draw_arrow(fr, t, t0, side):
        """Curvy hand-drawn arrow that draws itself towards the cloud's lower corner."""
        dt = t - t0
        if dt < 0:
            return
        prog = eo(dt / 0.45)
        L, n = 200, 30
        m = max(2, int(n * prog))
        ang = math.radians(-28)
        ca, sa = math.cos(ang), math.sin(ang)
        pts = []
        for i in range(m + 1):
            u = i / n
            x, y = u * L, -math.sin(u * math.pi) * L * 0.32
            pts.append((x * ca - y * sa, x * sa + y * ca))
        ox, oy = (CX - 488, CY + 150) if side < 0 else (CX + 488, CY + 150)
        tp = [(ox - side * x, oy + y) for x, y in pts]
        xs = [q[0] for q in tp]; ys = [q[1] for q in tp]
        x0, y0 = int(min(xs)) - 50, int(min(ys)) - 50
        im = Image.new('RGBA', (int(max(xs)) - x0 + 50, int(max(ys)) - y0 + 50), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        loc = [(x - x0, y - y0) for x, y in tp]
        segs = []
        if prog > 0.9:
            (xa, ya), (xb, yb) = loc[-4], loc[-1]
            a = math.atan2(yb - ya, xb - xa)
            for s_ in (1, -1):
                aa = a + math.pi - s_ * 0.55
                segs.append([(xb, yb), (xb + 40 * math.cos(aa), yb + 40 * math.sin(aa))])
        for col, wd in ((INK, 20), (YEL, 11)):
            for poly in [loc] + segs:
                d.line(poly, fill=col + (255,), width=wd, joint='curve')
                for q in (poly[0], poly[-1]):
                    d.ellipse([q[0] - wd / 2, q[1] - wd / 2, q[0] + wd / 2, q[1] + wd / 2], fill=col + (255,))
        blend(fr, pil2np(im), x0, y0, 1.0)

    cap_cache = {}

    def caption(fr, t):
        if t >= ec_start - 0.05:
            return
        for gi, grp in enumerate(groups):
            g0 = grp[0]['t0']
            g1 = grp[-1]['t1'] + 0.12
            if gi + 1 < len(groups):
                g1 = min(g1 + 0.25, groups[gi + 1][0]['t0'])
            if not (g0 <= t < g1):
                continue
            act = 0
            for wi, wt in enumerate(grp):
                if t >= wt['t0'] - 0.02:
                    act = wi
            key = (gi, act)
            if key not in cap_cache:
                f = font(BLACK, csize)
                toks = [w['w'].upper() for w in grp]
                sp = f.getlength(' ')
                widths = [f.getlength(tk) for tk in toks]
                tw = sum(widths) + sp * (len(toks) - 1)
                scale = min(1.0, (W - 120) / (tw + 40))
                fs = int(csize * scale); f = font(BLACK, fs); sp = f.getlength(' ')
                widths = [f.getlength(tk) for tk in toks]; tw = sum(widths) + sp * (len(toks) - 1)
                hh = int(fs * 1.55)
                im = Image.new('RGBA', (int(tw + 80), hh + 30), (0, 0, 0, 0))
                d = ImageDraw.Draw(im)
                x = 40; y = 15 + hh / 2
                for wi, tk in enumerate(toks):
                    if wi == act:
                        pad = 14
                        boxl = Image.new('RGBA', im.size, (0, 0, 0, 0))
                        ImageDraw.Draw(boxl).rounded_rectangle([x - pad, y - fs * 0.62 + 6, x + widths[wi] + pad, y + fs * 0.62 + 6], 16, fill=(10, 12, 40, 120))
                        im = Image.alpha_composite(im, boxl.filter(ImageFilter.GaussianBlur(6)))
                        d = ImageDraw.Draw(im)
                        d.rounded_rectangle([x - pad, y - fs * 0.62, x + widths[wi] + pad, y + fs * 0.62], 16, fill=YEL + (255,))
                        d.text((x, y), tk, font=f, fill=INK + (255,), anchor='lm')
                    else:
                        d.text((x, y), tk, font=f, fill=WHITE + (255,), anchor='lm', stroke_width=7, stroke_fill=INK + (255,))
                    x += widths[wi] + sp
                cap_cache[key] = pil2np(im)
            sc = 1.0
            if act == 0:
                sc = lerp(0.86, 1.0, eback((t - g0) / 0.14))
            blend_c(fr, cap_cache[key], W / 2, int(job.get('caption_y', 1452)), sc)
            return

    num_cache = {}

    def number_badge(fr, t, nb, y):
        t0 = nb['_t']
        if t < t0 - 0.05:
            return
        d = float(nb.get('dur', 1.1))
        u = cl((t - t0) / d)
        val = lerp(float(nb.get('from', 0)), float(nb['value']), eo(u))
        txt = (nb.get('prefix', '') + fmt_num(val, int(nb.get('decimals', 0))) + nb.get('suffix', ''))
        label = nb.get('label', '')
        key = (txt, label)
        if key not in num_cache:
            fn = font(BLACK, 84); fl = font(XB, 30)
            tw = fn.getlength(txt); lw_ = fl.getlength(label.upper()) if label else 0
            bw = int(max(tw, lw_) + 90); bh = 150 if label else 118
            im = Image.new('RGBA', (bw + 40, bh + 50), (0, 0, 0, 0))
            sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([20, 34, 20 + bw, 34 + bh], 40, fill=(10, 14, 60, 130))
            im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
            dd = ImageDraw.Draw(im)
            dd.rounded_rectangle([20, 20, 20 + bw, 20 + bh], 40, fill=YEL + (255,), outline=WHITE + (255,), width=6)
            if label:
                dd.text((20 + bw / 2, 20 + 34), label.upper(), font=fl, fill=(70, 60, 120, 255), anchor='mm')
                dd.text((20 + bw / 2, 20 + 98), txt, font=fn, fill=INK + (255,), anchor='mm')
            else:
                dd.text((20 + bw / 2, 20 + bh / 2), txt, font=fn, fill=INK + (255,), anchor='mm')
            num_cache[key] = pil2np(im)
        s = eelastic((t - t0) / 0.6) if t - t0 < 0.6 else 1.0 + 0.04 * math.sin((t - t0) * 6) * (1 if u < 1 else 0) + (0.06 * math.exp(-(t - t0 - d) * 8) if t > t0 + d else 0)
        blend_c(fr, num_cache[key], W / 2, y, max(0.02, s))

    credit_cache = {}

    preview = [float(x) for x in os.environ.get('BIL_PREVIEW', '').split(',') if x.strip()]
    frame_ids = [int(round(x * FPS)) for x in preview] if preview else range(nframes)
    if preview:
        enc.stdin.close(); enc.wait()
    for fi in frame_ids:
        t = fi / FPS
        fr = bg.frame(t, energy=1.0)

        # active fact
        k = 0
        for i, st in enumerate(starts):
            if t >= st:
                k = i
        in_ec = t >= ec_start
        bob = 10 * math.sin(2 * math.pi * t / 2.6)
        rot_bob = 0.8 * math.sin(2 * math.pi * t / 3.4)

        # ---- cloud (+ outgoing cloud pop)
        if not in_ec:
            st, en = starts[k], ends[k]
            t_in = st + (-0.12 if k == 0 else 0.04)
            u_in = (t - t_in) / 0.62
            s = 0.0 if u_in < 0 else epop(u_in)
            # anticipation before leaving
            pre = en - t
            if pre < 0.18:
                s *= lerp(1.0, 1.07, cl(1 - pre / 0.18))
            # outgoing previous cloud: quick shrink behind the new one (+ poof)
            if k > 0 and t - st < 0.2:
                pu = (t - st) / 0.2
                blend_c(fr, cards[k - 1].render(1.0), CX, CY + bob, lerp(1.07, 0.3, eo(pu)), cl(1 - pu))
            card = cards[k].render(cl((t - st) / max(0.5, en - st)))
            sy = CY + bob
            # tail bubbles (pop sequentially after the cloud)
            side = 1 if k % 2 == 0 else -1
            for bi, (bx, byy, br) in enumerate(tail_bubbles(CX, CY + CH / 2 - 40, side)):
                bs = eelastic((t - t_in - 0.25 - bi * 0.09) / 0.45)
                if bs > 0.02:
                    blend_c(fr, bubble_sprite(br), bx, byy + bob * (0.6 - bi * 0.15), bs * min(1, s + 0.2) if s > 0 else 0)
            if s > 0.01:
                blend_c(fr, card, CX, sy, s, rot=rot_bob * (1 if s > 0.98 else 0) + (1 - min(1, s)) * -6)
            if k > 0:
                poof(fr, st - 0.02, t, CX, CY)
            # credit line (small, bottom of photo scene)
            cr = facts[k].get('credit')
            if cr and s > 0.5:
                if cr not in credit_cache:
                    credit_cache[cr] = text_sprite(cr, SEMI, 25, (235, 240, 255), stroke=0, shadow=4)
                blend_c(fr, credit_cache[cr], W / 2, int(job.get('credit_y', 1540)), 1.0, cl((t - t_in) / 0.4) * 0.92)
            # numbers
            live = [nb for nb in facts[k]['_nums'] if nb['_t'] - 0.05 <= t]
            if live:   # only the most recent counter of this fact is shown
                number_badge(fr, t, live[-1], int(job.get('number_y', 1290)))
            # decorations around the cloud
            for di, (sp, rx, ry, ph) in enumerate(deco_sets[k % len(deco_sets)]):
                dt = t - (t_in + 0.15 + di * 0.08)
                if dt < 0:
                    continue
                sc = eelastic(dt / 0.55) * (1 + 0.05 * math.sin(t * 3 + ph))
                if en - t < 0.15:
                    sc *= cl((en - t) / 0.15)
                blend_c(fr, sp, CX + rx + 6 * math.sin(t * 1.3 + ph), CY + ry + 12 * math.sin(t * 2.1 + ph) + bob * 0.4, sc,
                        rot=10 * math.sin(t * 1.7 + ph))
            # sparkles twinkling around
            for si, (rx, ry) in enumerate(sparkle_pos):
                tw_ = 0.5 + 0.5 * math.sin(t * 4.2 + si * 1.9)
                spr = [spark, spark_y, spark_s][si % 3]
                blend_c(fr, spr, CX + rx, CY + ry + bob * 0.5, 0.45 + 0.65 * tw_ * cl((t - t_in) / 0.4), 0.9 * cl((t - t_in) / 0.3), rot=t * 40 + si * 20)
            # arrow drawing itself towards the cloud (on facts 1+)
            if k > 0 and en - t > 0.15:
                draw_arrow(fr, t, st + 0.55, 1 if k % 2 else -1)
        else:
            # ---- END CARD
            te = t - ec_start
            if te < 0.22:
                pc = cards[-1].render(1.0)
                blend_c(fr, pc, CX, CY + bob, lerp(1.07, 0.1, eo(te / 0.22)), cl(1.2 - te / 0.22))
            poof(fr, ec_start - 0.02, t, CX, CY)
            s = epop((te - 0.04) / 0.6)
            ecy = int(job.get('endcard_y', 800))
            if s > 0.01:
                card = ec_card.render(0).copy()
                # text inside the end-card cloud
                ttl = text_sprite(ec.get('title', 'Siz bilarmidingiz?'), BLACK, 88, INK)
                ln = text_sprite(ec.get('line', 'Izohda yozing'), XB, 74, (110, 60, 220))
                ch_, cw_ = card.shape[:2]
                blend(card, ttl, int(cw_ / 2 - ttl.shape[1] / 2), int(ch_ / 2 - 58 - ttl.shape[0] / 2))
                blend(card, ln, int(cw_ / 2 - ln.shape[1] / 2 - 50), int(ch_ / 2 + 62 - ln.shape[0] / 2))
                # bouncing "pointing down" marker (drawn, emoji-free)
                bob2 = 12 * abs(math.sin(te * 5))
                mx = int(cw_ / 2 + ln.shape[1] / 2 - 20); my = int(ch_ / 2 + 66 + bob2)
                mk = Image.new('RGBA', (90, 110), (0, 0, 0, 0)); dm = ImageDraw.Draw(mk)
                dm.ellipse([5, 5, 85, 85], fill=YEL + (255,), outline=INK + (255,), width=5)
                dm.polygon([(45, 70), (22, 40), (35, 40), (35, 18), (55, 18), (55, 40), (68, 40)], fill=INK + (255,))
                blend(card, pil2np(mk), mx, my - 50)
                blend_c(fr, card, CX, ecy + bob, s, rot=(1 - min(1, s)) * -6)
                # small "?" and "!" bubbles orbiting
                for oi, sp in enumerate([qb, eb, qb2, star]):
                    a = te * 1.2 + oi * math.pi / 2
                    blend_c(fr, sp, CX + math.cos(a) * 470, ecy + math.sin(a) * 360, eelastic((te - 0.2 - oi * 0.06) / 0.5) * 0.9, rot=12 * math.sin(te * 3 + oi))
            # subscribe button
            bs_ = epop((te - 0.35) / 0.6)
            if bs_ > 0.01:
                key = 'btn'
                if key not in num_cache:
                    fb = font(BLACK, 64); txt = ec.get('button', 'Obuna bo' + A + 'ling').upper()
                    tw = fb.getlength(txt); bw = int(tw + 200); bh = 128
                    im = Image.new('RGBA', (bw + 40, bh + 50), (0, 0, 0, 0))
                    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([20, 34, 20 + bw, 34 + bh], 64, fill=(10, 14, 60, 140))
                    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
                    dd = ImageDraw.Draw(im)
                    dd.rounded_rectangle([20, 20, 20 + bw, 20 + bh], 64, fill=(240, 40, 60, 255), outline=WHITE + (255,), width=6)
                    # bell icon
                    bx, by = 20 + 70, 20 + bh / 2
                    dd.pieslice([bx - 26, by - 34, bx + 26, by + 18], 180, 360, fill=WHITE + (255,))
                    dd.rectangle([bx - 26, by - 8, bx + 26, by + 14], fill=WHITE + (255,))
                    dd.rounded_rectangle([bx - 34, by + 10, bx + 34, by + 20], 5, fill=WHITE + (255,))
                    dd.ellipse([bx - 8, by + 18, bx + 8, by + 32], fill=WHITE + (255,))
                    dd.text((20 + 120 + tw / 2 + 10, 20 + bh / 2), txt, font=fb, fill=WHITE + (255,), anchor='mm')
                    num_cache[key] = pil2np(im)
                pulse = 1 + 0.045 * math.sin(te * 7) * cl((te - 0.9) / 0.2)
                blend_c(fr, num_cache[key], W / 2, int(job.get('button_y', 1330)), bs_ * pulse, rot=(-4 * math.sin(te * 14) * math.exp(-max(0, te - 1.0) * 3) if te > 1.0 else 0))
            confetti_burst(fr, ec_start + 0.1, t, W / 2, ecy - 100, n=60)

        # ---- hook title (big bounce) -> header dock
        DOCK0, DOCK1 = 1.75, 2.35
        if t < DOCK1:
            big = 1.0
            dock_u = eio((t - DOCK0) / (DOCK1 - DOCK0)) if t > DOCK0 else 0.0
        else:
            dock_u = 1.0
        hdr_scale = lerp(1.0, 0.40, dock_u)
        hx0 = lerp(W / 2, 62 + lw_total * 0.40 / 2, dock_u)
        hy = lerp(400, 284, dock_u)
        x = hx0 - lw_total * hdr_scale / 2
        for li, (ch, sp, adv) in enumerate(letters):
            lt = t + 0.12 - 0.035 * li
            wl = adv * hdr_scale
            if lt <= 0:
                x += wl
                continue
            if dock_u <= 0:
                drop = (1 - eelastic(lt / 0.55)) * -110
                sc = epop(lt / 0.45) * 1.0
                wob = 0
            else:
                drop = 0; sc = 1.0; wob = 0
            if ch in '?!':
                wob = 12 * math.sin(t * 6) * (1 if dock_u >= 1 else 0.6)
            yy = hy + drop + (6 * math.sin(t * 5 + li * 0.6) * (1 - dock_u) if lt > 0.6 else 0)
            if dock_u >= 1:
                yy += 3 * math.sin(t * 3 + li * 0.5)
            blend_c(fr, sp, x + wl / 2, yy, sc * hdr_scale, rot=wob)
            x += wl
        # brand label top-right
        if t > 0.2:
            blend_c(fr, brand, W - 62 - brand.shape[1] / 2, 284, 1.0, cl((t - 0.2) / 0.4))
        # hook confetti burst
        confetti_burst(fr, 0.55, t, W / 2, 420, spread=560, n=40)

        caption(fr, t)
        # final fade to keep the loop clean
        if t > total - 0.25:
            fr = (fr.astype(np.float32) * cl((total - t) / 0.25 * 0.6 + 0.4)).astype(np.uint8)
        if preview:
            Image.fromarray(fr).save(os.path.join(work, 'prev_%06.2f.jpg' % t), quality=90)
            continue
        enc.stdin.write(fr.tobytes())
        if fi % 150 == 0:
            sys.stderr.write('frame %d/%d\n' % (fi, nframes))
    if preview:
        return None
    enc.stdin.close(); enc.wait()

    # ---- audio
    a_in, parts, mix, idx = [], [], [], 1
    if vpath:
        a_in += ['-i', vpath]
        parts.append('[%d:a]aresample=48000,adelay=%d|%d,volume=%.2f,highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,apad[voice]'
                     % (idx, int(vstart * 1000), int(vstart * 1000), float(v.get('volume', 1.0))))
        idx += 1
    mus = job.get('music', {'gen': 'bright'})
    if mus:
        try:
            if mus.get('src'):
                mp = R.fetch(mus['src'])
            elif mus.get('gen', 'bright') == 'bright':
                mp = gen_bright_music(total, os.path.join(work, 'music_bright.wav'))
            else:
                mp = R.gen_music(mus['gen'], total)
            a_in += ['-stream_loop', '-1', '-i', mp]
            parts.append('[%d:a]aresample=48000,volume=%.3f,afade=t=in:st=0:d=0.5[mus]' % (idx, float(mus.get('volume', 0.13))))
            idx += 1
            if vpath:
                parts.append('[voice]asplit=2[voice][vsc]')
                parts.append('[mus][vsc]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=400:makeup=1[musd]')
                mix.append('[musd]')
            else:
                mix.append('[mus]')
        except Exception as e:
            sys.stderr.write('music skipped: %s\n' % e)
    if job.get('sfx', True):
        ep = R.gen_events(ev, total)     # SFX_GAIN (40 %) applied inside
        if ep:
            a_in += ['-i', ep]
            parts.append('[%d:a]aresample=48000,volume=%.2f[sfx]' % (idx, float(job.get('sfx_volume', 0.9))))
            mix.append('[sfx]'); idx += 1
    if vpath:
        mix.append('[voice]')
    mixed = os.path.join(work, 'bil_mix.wav')
    pre = ';'.join(parts) + (';' if parts else '') + '%samix=inputs=%d:duration=longest:normalize=0,atrim=0:%.3f,afade=t=out:st=%.3f:d=0.4' % (
        ''.join(mix), len(mix), total, max(0, total - 0.45))
    R.sh(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo'] + a_in + ['-filter_complex', pre + '[m]', '-map', '[m]', '-t', '%.3f' % total, '-ar', '48000', mixed])
    # two-pass loudnorm -> -14 LUFS
    r = subprocess.run(['ffmpeg', '-i', mixed, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.S)
    if m:
        L = json.loads(m.group(0))
        ln = ('loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true'
              % (L['input_i'], L['input_tp'], L['input_lra'], L['input_thresh'], L['target_offset']))
    else:
        ln = 'loudnorm=I=-14:TP=-1.5:LRA=11'
    R.sh(['ffmpeg', '-y', '-i', vid_tmp, '-i', mixed, '-filter_complex', '[1:a]%s,aresample=48000[a]' % ln, '-map', '0:v', '-map', '[a]',
          '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-t', '%.3f' % total, out_path])
    thumb = os.path.splitext(out_path)[0] + '.jpg'
    subprocess.run(['ffmpeg', '-y', '-ss', '%.2f' % min(2.6, total / 2), '-i', out_path, '-frames:v', '1', '-q:v', '2', thumb],
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    info = {'name': job.get('name', ''), 'template': 'bilasizmi', 'duration': round(total, 2), 'width': W, 'height': H, 'fps': FPS,
            'size_mb': round(os.path.getsize(out_path) / 1e6, 2), 'words': len(words), 'facts': len(facts),
            'fact_starts': [round(s, 2) for s in starts], 'endcard_start': round(ec_start, 2)}
    print(json.dumps(info))
    return info


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
