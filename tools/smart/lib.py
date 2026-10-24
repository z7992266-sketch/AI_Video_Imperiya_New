"""Core motion-graphics primitives for the Smart Sistem ads (1080x1920, 30fps)."""
import math, random, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H, FPS = 1080, 1920, 30
IN = '/usr/share/fonts/opentype/inter/'
POPPINS = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'

GOLD = (246, 200, 110)
GOLD2 = (255, 228, 160)
MAG = (255, 46, 196)
VIO = (128, 64, 255)
CYAN = (64, 200, 255)
WHITE = (255, 255, 255)
GREEN = (52, 211, 120)
RED = (244, 63, 94)
TG = (42, 171, 238)


@functools.lru_cache(maxsize=None)
def font(name, size):
    path = POPPINS if name == 'poppins' else IN + name + '.otf'
    return ImageFont.truetype(path, size)


@functools.lru_cache(maxsize=None)
def emoji(ch, size):
    f = ImageFont.truetype(EMOJI, 109)
    im = Image.new('RGBA', (140, 140), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4, 4), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x

def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)

def eo3(x):
    x = clamp(x); return 1 - (1 - x) ** 3

def eio(x):
    x = clamp(x); return 3 * x * x - 2 * x * x * x

def eback(x, s=1.7):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

def eexpo(x):
    x = clamp(x); return 1 if x >= 1 else 1 - 2 ** (-10 * x)

def lerp(a, b, x):
    return a + (b - a) * x

def lerpc(c1, c2, x):
    return tuple(int(lerp(c1[i], c2[i], x)) for i in range(len(c1)))


# ---------------------------------------------------------------- helpers
def rr(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)

def grad_img(w, h, c1, c2, horizontal=False, a1=255, a2=255):
    if horizontal:
        x = np.linspace(0, 1, w)[None, :, None]
    else:
        x = np.linspace(0, 1, h)[:, None, None]
    c1 = np.array(list(c1) + [a1], float); c2 = np.array(list(c2) + [a2], float)
    arr = c1 + (c2 - c1) * x
    arr = np.broadcast_to(arr, (h, w, 4)).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

def rounded_mask(w, h, r, scale=3):
    m = Image.new('L', (w * scale, h * scale), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * scale - 1, h * scale - 1), r * scale, fill=255)
    return m.resize((w, h), Image.LANCZOS)

def grad_rr(w, h, r, c1, c2, horizontal=True):
    g = grad_img(w, h, c1, c2, horizontal)
    g.putalpha(rounded_mask(w, h, r))
    return g

def glow(img, radius, strength=1.0):
    """Return a blurred copy of img (RGBA) for additive glow."""
    g = img.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        a = np.array(g); a[..., 3] = np.clip(a[..., 3] * strength, 0, 255); g = Image.fromarray(a)
    return g

def text_img(txt, fnt, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0)):
    b = fnt.getbbox(txt, stroke_width=stroke)
    w, h = b[2] - b[0] + 4, b[3] - b[1] + 4
    im = Image.new('RGBA', (max(1, w), max(1, h)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-b[0] + 2, -b[1] + 2), txt, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
    return im

def grad_text(txt, fnt, c1, c2):
    m = text_img(txt, fnt, (255, 255, 255))
    g = grad_img(m.width, m.height, c1, c2)
    g.putalpha(m.split()[3])
    return g

def with_alpha(img, a):
    if a >= 0.999:
        return img
    im = img.copy()
    al = im.split()[3].point(lambda v: int(v * clamp(a)))
    im.putalpha(al)
    return im

def paste(base, img, cx, cy, alpha=1.0, scale=1.0, anchor='c'):
    """Alpha-composite img onto base centred at (cx, cy)."""
    if alpha <= 0.003 or scale <= 0.01:
        return
    if abs(scale - 1) > 0.003:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    img = with_alpha(img, alpha)
    if anchor == 'c':
        x, y = int(cx - img.width / 2), int(cy - img.height / 2)
    elif anchor == 'l':
        x, y = int(cx), int(cy - img.height / 2)
    else:
        x, y = int(cx - img.width), int(cy - img.height / 2)
    base.alpha_composite(img, (x, y)) if (x >= 0 and y >= 0 and x + img.width <= base.width and y + img.height <= base.height) else _safe(base, img, x, y)

def _safe(base, img, x, y):
    bx0, by0 = max(0, x), max(0, y)
    bx1, by1 = min(base.width, x + img.width), min(base.height, y + img.height)
    if bx1 <= bx0 or by1 <= by0:
        return
    crop = img.crop((bx0 - x, by0 - y, bx1 - x, by1 - y))
    base.alpha_composite(crop, (bx0, by0))

def add_light(base, img, cx, cy, alpha=1.0, scale=1.0):
    """Additive (screen-like) blend of an RGBA glow sprite."""
    if alpha <= 0.003:
        return
    if abs(scale - 1) > 0.003:
        img = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BILINEAR)
    x, y = int(cx - img.width / 2), int(cy - img.height / 2)
    bx0, by0 = max(0, x), max(0, y)
    bx1, by1 = min(base.width, x + img.width), min(base.height, y + img.height)
    if bx1 <= bx0 or by1 <= by0:
        return
    src = np.asarray(img.crop((bx0 - x, by0 - y, bx1 - x, by1 - y)), dtype=np.float32)
    region = base.crop((bx0, by0, bx1, by1))
    dst = np.asarray(region, dtype=np.float32)
    a = src[..., 3:4] / 255.0 * alpha
    out = dst.copy()
    out[..., :3] = np.minimum(255, dst[..., :3] + src[..., :3] * a)
    base.paste(Image.fromarray(out.astype(np.uint8), 'RGBA'), (bx0, by0))

@functools.lru_cache(maxsize=None)
def glow_dot(r, color):
    s = r * 6
    im = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((s / 2 - r, s / 2 - r, s / 2 + r, s / 2 + r), fill=color + (255,))
    im = im.filter(ImageFilter.GaussianBlur(r * 1.1))
    d = ImageDraw.Draw(im)
    rr_ = max(1, r // 3)
    d.ellipse((s / 2 - rr_, s / 2 - rr_, s / 2 + rr_, s / 2 + rr_), fill=(255, 255, 255, 255))
    return im


# ---------------------------------------------------------------- background
class Background:
    def __init__(self, seed=3, palette=None):
        self.lw, self.lh = 216, 384
        y = np.linspace(0, 1, self.lh)[:, None]
        x = np.linspace(0, 1, self.lw)[None, :]
        self.X, self.Y = x, y
        top = np.array([10, 4, 22.0]); bot = np.array([4, 2, 10.0])
        self.base = top + (bot - top) * y[..., None] + 0 * x[..., None]
        self.blobs = palette or [
            (MAG, 0.30, 0.25, 0.30, 0.55, 0.11, 0.0),
            (VIO, 0.75, 0.40, 0.35, 0.65, 0.07, 1.7),
            (GOLD, 0.50, 0.85, 0.28, 0.32, 0.09, 3.1),
            (CYAN, 0.15, 0.70, 0.22, 0.22, 0.13, 4.2),
        ]
        rnd = random.Random(seed)
        self.parts = [(rnd.random(), rnd.random(), rnd.uniform(0.3, 1.0), rnd.uniform(0, 6.28), rnd.choice([GOLD, GOLD, WHITE, MAG, CYAN])) for _ in range(70)]
        yy, xx = np.mgrid[0:H, 0:W]
        d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        v = np.clip((d - 0.55) / 0.6, 0, 1) ** 1.6
        vig = np.zeros((H, W, 4), np.uint8); vig[..., 3] = (v * 200).astype(np.uint8)
        self.vignette = Image.fromarray(vig, 'RGBA')
        self.energy = 1.0

    def frame(self, t, tint=1.0, grid=True):
        img = self.base.copy()
        for col, cx, cy, r, inten, sp, ph in self.blobs:
            px = cx + 0.12 * math.sin(t * sp * 2 + ph)
            py = cy + 0.08 * math.cos(t * sp * 1.6 + ph * 0.7)
            g = np.exp(-(((self.X - px) * 1.0) ** 2 + ((self.Y - py) * 0.56) ** 2) / (r * r * 0.25))
            img += g[..., None] * np.array(col) * inten * tint * self.energy * 0.55
        img = np.clip(img, 0, 255).astype(np.uint8)
        im = Image.fromarray(img, 'RGB').resize((W, H), Image.BILINEAR).convert('RGBA')
        if grid:
            self._grid(im, t)
        for (px, py, z, ph, col) in self.parts:
            yy = (py - t * 0.018 * z) % 1.0
            xx = px + 0.01 * math.sin(t * 0.8 + ph)
            a = (0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2 + ph))) * z * 0.8
            add_light(im, glow_dot(int(2 + 3 * z), col), xx * W, yy * H, a)
        return im

    def _grid(self, im, t):
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        hy = int(H * 0.70)
        for i in range(14):
            z = ((i + (t * 0.6) % 1.0) / 14.0)
            y = hy + (H - hy) * (z ** 2.2)
            a = int(70 * z)
            d.line((0, y, W, y), fill=(160, 90, 255, a), width=2)
        for i in range(-12, 13):
            x0 = W / 2 + i * 40
            x1 = W / 2 + i * 260
            d.line((x0, hy, x1, H), fill=(160, 90, 255, 38), width=2)
        im.alpha_composite(layer)

    def finish(self, im):
        im.alpha_composite(self.vignette)
        return im


# ---------------------------------------------------------------- 3D
def _coeffs(src, dst):
    m = []
    for (x, y), (u, v) in zip(dst, src):
        m.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        m.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A = np.array(m, float); B = np.array(src, float).reshape(8)
    return np.linalg.solve(A, B).tolist()

def project(img, ry=0.0, rx=0.0, rz=0.0, f=2400.0):
    """Rotate a flat card in 3D (degrees) and return (image, offset_x, offset_y) relative to its centre."""
    w, h = img.size
    if abs(ry) < 0.05 and abs(rx) < 0.05 and abs(rz) < 0.05:
        return img, -w / 2, -h / 2
    ay, ax, az = math.radians(ry), math.radians(rx), math.radians(rz)
    pts = []
    for (x, y) in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]:
        x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
        x1, z1 = x * math.cos(ay), x * math.sin(ay)
        y1, z2 = y * math.cos(ax) - z1 * math.sin(ax), y * math.sin(ax) + z1 * math.cos(ax)
        s = f / (f + z2)
        pts.append((x1 * s, y1 * s))
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, miny = min(xs), min(ys)
    ow, oh = int(math.ceil(max(xs) - minx)) + 2, int(math.ceil(max(ys) - miny)) + 2
    dst = [(p[0] - minx, p[1] - miny) for p in pts]
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    out = img.transform((ow, oh), Image.PERSPECTIVE, _coeffs(src, dst), Image.BICUBIC)
    return out, minx, miny


# ---------------------------------------------------------------- phone
SW, SH = 600, 1300      # screen size
BZ = 20                 # bezel
PW, PH = SW + 2 * BZ, SH + 2 * BZ

class Phone:
    def __init__(self):
        fr = grad_rr(PW, PH, 100, (70, 66, 80), (28, 26, 34), horizontal=True)
        d = ImageDraw.Draw(fr)
        d.rounded_rectangle((3, 3, PW - 4, PH - 4), 97, outline=(150, 145, 165, 255), width=2)
        d.rounded_rectangle((BZ - 6, BZ - 6, PW - BZ + 5, PH - BZ + 5), 86, fill=(4, 4, 6, 255))
        self.frame = fr
        self.mask = rounded_mask(SW, SH, 80)
        isl = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
        ImageDraw.Draw(isl).rounded_rectangle((PW / 2 - 95, BZ + 18, PW / 2 + 95, BZ + 72), 27, fill=(0, 0, 0, 255))
        self.island = isl
        sil = Image.new('RGBA', (PW + 240, PH + 240), (0, 0, 0, 0))
        ImageDraw.Draw(sil).rounded_rectangle((120, 120, 120 + PW, 120 + PH), 100, fill=(150, 70, 255, 255))
        self.halo = sil.filter(ImageFilter.GaussianBlur(60))
        sh = Image.new('RGBA', (PW + 300, 300), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((80, 110, PW + 220, 190), fill=(0, 0, 0, 200))
        self.shadow = sh.filter(ImageFilter.GaussianBlur(30))

    def render(self, screen, glare=None):
        im = self.frame.copy()
        im.paste(screen.convert('RGB'), (BZ, BZ), self.mask)
        im.alpha_composite(self.island)
        if glare is not None:
            g = Image.new('L', (PW, PH), 0)
            gd = ImageDraw.Draw(g)
            x = -PW + glare * (PW * 3)
            gd.polygon([(x, 0), (x + 160, 0), (x + 160 - PH * 0.5, PH), (x - PH * 0.5, PH)], fill=38)
            g = g.filter(ImageFilter.GaussianBlur(25))
            g = ImageChops.multiply(g, self.frame.split()[3])
            white = Image.new('RGBA', (PW, PH), (255, 255, 255, 0)); white.putalpha(g)
            im.alpha_composite(white)
        return im

    def draw(self, base, screen, cx, cy, scale=0.82, ry=0, rx=0, rz=0, alpha=1.0, glare=None, halo=0.55):
        if alpha <= 0.01:
            return
        im = self.render(screen, glare)
        if abs(scale - 1) > 0.002:
            im = im.resize((int(PW * scale), int(PH * scale)), Image.BICUBIC)
        pim, ox, oy = project(im, ry, rx, rz)
        if halo > 0:
            add_light(base, self.halo, cx, cy, halo * alpha, scale)
        paste(base, self.shadow, cx, cy + PH * scale * 0.5 + 10, 0.8 * alpha, scale)
        pim = with_alpha(pim, alpha)
        _safe(base, pim, int(cx + ox), int(cy + oy))


# ---------------------------------------------------------------- glass card
def glass(w, h, r=36, tint=(255, 255, 255), a=34, border=(255, 255, 255, 70)):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=tint + (a,), outline=border, width=2)
    hl = grad_img(w, h // 2, (255, 255, 255), (255, 255, 255), a1=26, a2=0)
    m = rounded_mask(w, h, r).crop((0, 0, w, h // 2))
    hl.putalpha(ImageChops.multiply(hl.split()[3], m))
    im.alpha_composite(hl)
    return im


# ---------------------------------------------------------------- captions
class Captions:
    """Kinetic word-by-word captions: chunk appears word by word, active word pops in gold."""

    def __init__(self, words, display=None, y=1640, size=70, maxchars=20, hide=()):
        self.y = y; self.size = size; self.hide = hide
        disp = display or {}
        ws = []
        for w in words:
            t = disp.get(w['text'], w['text'])
            if t == '':
                continue
            ws.append(dict(text=t, start=w['start'], end=w['end']))
        ws = [w for w in ws if w['text'] not in ('—', '-', '–')]
        chunks, cur = [], []
        for w in ws:
            cur.append(w)
            ln = sum(len(x['text']) + 1 for x in cur)
            if w['text'][-1] in '.,!?:' or len(cur) >= 3 or ln >= maxchars:
                chunks.append(cur); cur = []
        if cur:
            chunks.append(cur)
        self.chunks = []
        for i, c in enumerate(chunks):
            st = c[0]['start'] - 0.05
            en = chunks[i + 1][0]['start'] - 0.05 if i + 1 < len(chunks) else c[-1]['end'] + 0.6
            en = min(en, c[-1]['end'] + 0.9)
            self.chunks.append((st, en, c))
        self.f = font('Inter-Black', size)
        self.cache = {}

    def _word(self, txt, col):
        k = (txt, col)
        if k not in self.cache:
            if col == 'gold':
                im = grad_text(txt, self.f, GOLD2, (240, 160, 60))
            else:
                im = text_img(txt, self.f, (255, 255, 255))
            sh = text_img(txt, self.f, (0, 0, 0)).filter(ImageFilter.GaussianBlur(9))
            cv = Image.new('RGBA', (im.width + 40, im.height + 40), (0, 0, 0, 0))
            cv.alpha_composite(sh, (20, 26)); cv.alpha_composite(sh, (20, 26)); cv.alpha_composite(im, (20, 20))
            self.cache[k] = cv
        return self.cache[k]

    def draw(self, base, t):
        for (a, b) in self.hide:
            if a <= t < b:
                return
        for st, en, ws in self.chunks:
            if not (st <= t < en):
                continue
            fade = 1 - prog(t, en - 0.12, en)
            space = self.size * 0.40
            widths = [self._word(w['text'], 'w').width - 40 for w in ws]
            total = sum(widths) + space * (len(ws) - 1)
            x = W / 2 - total / 2
            for w, wd in zip(ws, widths):
                cx = x + wd / 2
                x += wd + space
                if t < w['start'] - 0.06:
                    continue
                k = prog(t, w['start'] - 0.06, w['start'] + 0.16)
                active = w['start'] - 0.06 <= t < w['end'] + 0.05
                sc = 0.7 + 0.3 * eback(k, 2.4)
                if active:
                    sc *= 1.0 + 0.10 * math.sin(math.pi * prog(t, w['start'], w['end'] + 0.05))
                img = self._word(w['text'], 'gold' if active else 'w')
                dy = (1 - eo3(k)) * 26
                paste(base, img, cx, self.y + dy, alpha=min(1, k * 1.6) * fade, scale=sc)
            return


def find_word(words, key, after=0.0, nth=1):
    def norm(s):
        return ''.join(ch for ch in s.lower() if ch.isalnum())
    n = 0
    for w in words:
        if w['start'] + 1e-6 < after:
            continue
        if norm(w['text']).startswith(norm(key)):
            n += 1
            if n == nth:
                return w['start']
    raise KeyError(key)
