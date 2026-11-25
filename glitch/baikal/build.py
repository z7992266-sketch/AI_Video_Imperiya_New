"""GLITCHVERSE — Lake Baikal ice rings flagship (Mia's Glitch Diary #14). 1920x1080, 30 fps.
Usage: python3 build.py [--part i n] [--still t1,t2]
Built from glitch/tunguska/build.py (same base.py helpers)."""
import sys
sys.path.insert(0, '/home/claude/gv')
from base import *

ENTRY = 14
LAST = 's17'
AMB = (255, 176, 72)      # warm accent (= warm water)
ICE = (150, 225, 255)     # ice accent
for k in ('gv14_s2_wide.jpg', 'gv14_s2_mid.jpg', 'gv14_s2_south.jpg'): CRED[k] = EOX
def have(n): return os.path.exists(A + n)

# ---------- MAP (equirectangular WMS crops, aspect corrected by cos(lat)) ----------
SRC = [('gv14_s2_south.jpg', 103.4, 105.4, 51.3, 52.1), ('gv14_s2_mid.jpg', 102, 111, 50.8, 56.4), ('gv14_s2_wide.jpg', 60, 140, 38, 72)]
RING = (103.95, 51.70)   # Kultuk Bay ring area (approximate; rings of 2009 & 2020 at the southern tip)
LABELS = [('RUSSIA', 92, 61.0, 'cty'), ('KAZAKHSTAN', 70, 48.5, 'cty'), ('MONGOLIA', 103, 46.8, 'cty'), ('CHINA', 112, 41.5, 'cty'),
          ('SIBERIA', 101, 65.0, 'des'), ('LAKE BAIKAL', 109.6, 54.6, 'lakebig'), ('Irkutsk', 104.30, 52.29, 'city'), ('Ulan-Ude', 107.60, 51.83, 'city'),
          ('Olkhon Island', 107.35, 53.15, 'city'), ('Kultuk', 103.70, 51.72, 'city'), ('Lake Hovsgol', 100.50, 51.0, 'lake'), ('Lake Teletskoye', 87.60, 51.60, 'lake')]

def map_frame(cx, cy, wdeg, t, pin_alpha=1.0, pin=RING, pin_text='RING ZONE · KULTUK BAY', pin_sub='rings seen in 2009 and 2020 (position approx.)', lakes=False):
    hdeg = wdeg * math.cos(math.radians(cy)) * H / W
    x0, x1, y0, y1 = cx - wdeg / 2, cx + wdeg / 2, cy - hdeg / 2, cy + hdeg / 2
    src = SRC[-1]
    for s in SRC:
        if s[1] <= x0 and x1 <= s[2] and s[3] <= y0 and y1 <= s[4]: src = s; break
    name, lo0, lo1, la0, la1 = src
    im = img(name); iw, ih = im.size
    ppx = iw / (lo1 - lo0); ppy = ih / (la1 - la0)
    box = ((x0 - lo0) * ppx, (la1 - y1) * ppy, (x1 - lo0) * ppx, (la1 - y0) * ppy)
    fr = im.transform((W, H), Image.EXTENT, box, Image.BICUBIC).convert('RGBA')
    fr = Image.blend(fr, Image.new('RGBA', (W, H), (0, 0, 0, 255)), 0.12)
    d = ImageDraw.Draw(fr)
    def sxy(lo, la): return ((lo - x0) / wdeg * W, (y1 - la) / hdeg * H)
    for txt, lo, la, kind in LABELS:
        x, y = sxy(lo, la)
        if not (60 < x < W - 60 and 60 < y < H - 60): continue
        if kind == 'cty' and wdeg < 14: continue
        if kind == 'des' and wdeg < 7: continue
        if kind == 'lakebig' and not (4 < wdeg < 40): continue
        if kind == 'lake' and not lakes: continue
        if txt in ('Irkutsk', 'Ulan-Ude', 'Olkhon Island') and not (2.5 < wdeg < 16): continue
        if txt == 'Kultuk' and not (0.4 < wdeg < 6): continue
        sz = {'cty': 40, 'des': 40, 'city': 30, 'lake': 32, 'lakebig': 40}[kind]
        col = {'cty': (255, 255, 255, 230), 'des': (255, 220, 170, 240), 'city': (255, 255, 255, 235), 'lake': ICE + (255,), 'lakebig': ICE + (250,)}[kind]
        f = font(XB if kind in ('cty', 'des', 'lakebig') else BOLD, sz)
        if kind in ('city', 'lake'):
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=col[:3] + (230,), outline=(0, 0, 0, 160), width=2)
            dx = -18 if txt in ('Kultuk', 'Irkutsk', 'Lake Teletskoye') else 18
            anc = 'rm' if dx < 0 else 'lm'
            d.text((x + dx + 2, y + 2), txt, font=f, fill=(0, 0, 0, 170), anchor=anc)
            d.text((x + dx, y), txt, font=f, fill=col, anchor=anc)
        else:
            d.text((x + 3, y + 3), txt, font=f, fill=(0, 0, 0, 150), anchor='mm')
            d.text((x, y), txt, font=f, fill=col, anchor='mm')
    if pin and pin_alpha > 0:
        x, y = sxy(*pin)
        a = int(255 * pin_alpha)
        r = 18 + 10 * (0.5 + 0.5 * math.sin(t * 6))
        d.ellipse((x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2), outline=ICE + (int(a * 0.8),), width=5)
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=MG + (a,), outline=(255, 255, 255, a), width=4)
        f = font(BLACK, 46)
        tx = x + 48 if x < W * 0.55 else x - 48
        anc = 'lm' if x < W * 0.55 else 'rm'
        d.text((tx + 4, y + 20), pin_text, font=f, fill=(0, 0, 0, int(a * 0.6)), anchor=anc)
        d.text((tx, y + 16), pin_text, font=f, fill=(255, 255, 255, a), anchor=anc)
        d.text((tx + 2, y + 62), pin_sub, font=font(MONO, 26), fill=CY + (a,), anchor=anc)
    return fr.convert('RGB')

def lerp(a, b, e): return a + (b - a) * e
def log_lerp(a, b, e): return math.exp(math.log(a) + (math.log(b) - math.log(a)) * e)
def _old_map_in(p, tl, dur):
    e = ease(min(1, p / 0.9))
    return map_frame(lerp(98.0, EPI[0], e), lerp(57.0, EPI[1], e), log_lerp(62.0, 1.25, e), tl, pin_alpha=min(1, max(0, (p - 0.35) / 0.15)))
def _old_map_out(p, tl, dur):
    e = ease(p)
    return map_frame(lerp(EPI[0], 98.0, e), lerp(EPI[1], 57.0, e), log_lerp(1.25, 62.0, e), tl, pin_alpha=1.0)
def lower(text, sub=None):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    f1 = font(XB, 58); f2 = font(SEMI, 34)
    w1 = d.textlength(text, font=f1); w2 = d.textlength(sub, font=f2) if sub else 0
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.rounded_rectangle((70, 780, 160 + max(w1, w2) + 40, 950 if sub else 900), 18, fill=(0, 0, 0, 150))
    L.alpha_composite(g.filter(ImageFilter.GaussianBlur(14))); d = ImageDraw.Draw(L)
    shadow_text(d, (120, 860), text, f1, WH, 'ls', 3)
    if sub: shadow_text(d, (122, 912), sub, f2, CY, 'ls', 2)
    d.rectangle((96, 800, 104, 920 if sub else 870), fill=AMB + (255,))
    return L

def credit_layer(name):
    c = CRED.get(name)
    if not c: return None
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    f = font(MED, 20)
    tw = d.textlength(c, font=f)
    d.rounded_rectangle((W - 52 - tw, H - 56, W - 28, H - 22), 8, fill=(0, 0, 0, 120))
    d.text((W - 40, H - 30), c, font=f, fill=(255, 255, 255, 200), anchor='rs')
    return L

# ---------- shot helpers ----------
TIM = {s['id']: s for s in json.load(open(S + 'timing.json'))}
END_EXTRA = 8.0
TOTAL = TIM[LAST]['end'] + END_EXTRA

def img_shot(name, move='in', text=None, amt=0.12, focus=(0.5, 0.5), darken=0.0, glitch=True, w=1.0):
    return {'kind': 'img', 'name': name, 'move': move, 'text': text, 'amt': amt, 'focus': focus, 'darken': darken, 'glitch': glitch, 'w': w}
def card(fn, glitch=True, w=1.6, credit=None, grade=False):
    return {'kind': 'card', 'fn': fn, 'glitch': glitch, 'w': w, 'credit': credit, 'grade': grade}

def dimbg(name, p, move='in', amt=0.08, k=0.55, focus=(0.5, 0.5)):
    return Image.blend(kenburns(name, p, move, amt, focus), Image.new('RGB', (W, H), (0, 0, 0)), k).convert('RGBA')

def fade(p, t0, d=0.06): return max(0.0, min(1.0, (p - t0) / d))
def src_line(d, t): d.text((W // 2, 1012), t, font=font(MED, 24), fill=(150, 160, 180), anchor='mm')

def rgb_split_text(d, xy, t, f, k, tl, anchor='mm'):
    off = 9 if (int(tl * 30) % 7) in (0, 1) else 3
    x, y = xy
    for col, dx in ((MG, -off), (CY, off)):
        d.text((x + dx, y), t, font=f, fill=col + (int(170 * k),), anchor=anchor)
    d.text(xy, t, font=f, fill=WH + (int(255 * k),), anchor=anchor)

# ---------- MIA avatar card (abstract, no face) ----------
def avatar(size=150):
    L = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.ellipse((4, 4, size - 4, size - 4), fill=(10, 18, 32, 235), outline=CY + (255,), width=5)
    d.arc((14, 14, size - 14, size - 14), 200, 330, fill=MG + (255,), width=4)
    f = font(BLACK, int(size * 0.5))
    for col, dx in ((MG, -4), (CY, 4)): d.text((size // 2 + dx, size // 2 + 2), 'M', font=f, fill=col + (200,), anchor='mm')
    d.text((size // 2, size // 2 + 2), 'M', font=f, fill=WH + (255,), anchor='mm')
    for y in range(8, size - 8, 5): d.line((10, y, size - 10, y), fill=(0, 0, 0, 40))
    return L
AV = avatar(150)

def avatar_badge(fr, x, y, k=1.0, sub='AI HOST · FICTIONAL'):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle((x, y, x + 560, y + 190), 26, fill=(4, 8, 16, 200), outline=(40, 70, 100, 255), width=2)
    L.alpha_composite(AV, (x + 20, y + 20))
    d.text((x + 190, y + 58), 'DR. MIA STERLING', font=font(XB, 40), fill=WH + (255,), anchor='lm')
    d.text((x + 192, y + 110), sub, font=font(MONO, 26), fill=CY + (255,), anchor='lm')
    d.text((x + 192, y + 148), 'GLITCH DIARY', font=font(MONO, 22), fill=(150, 165, 190, 255), anchor='lm')
    if k < 1: L.putalpha(L.split()[3].point(lambda v: int(v * k)))
    fr.alpha_composite(L)

HOOK_IMG = 'gv14_r01.jpg'; HOOK_FOCUS = (0.47, 0.62)

def map_in(p, tl, dur):
    e = ease(min(1, p / 0.9))
    return map_frame(lerp(100.0, 104.4, e), lerp(54.0, 51.72, e), log_lerp(60.0, 3.2, e), tl, pin_alpha=min(1, max(0, (p - 0.45) / 0.15)))
def map_mid(p, tl, dur):
    e = ease(p)
    return map_frame(lerp(106.3, 106.6, e), lerp(53.6, 53.5, e), lerp(9.0, 8.2, e), tl, pin_alpha=0)
def map_out(p, tl, dur):
    e = ease(min(1, p / 0.85))
    return map_frame(lerp(104.4, 98.0, e), lerp(51.72, 53.0, e), log_lerp(1.9, 34.0, e), tl, pin_alpha=max(0, 1 - p * 3), lakes=p > 0.55)

# ---------- cards ----------
def hook_card(p, tl, dur):
    fr = kenburns(HOOK_IMG, p, 'in', 0.30, HOOK_FOCUS).convert('RGBA')
    sh_ = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh_)
    sd.rounded_rectangle((260, 60, 1660, 420), 40, fill=(0, 0, 0, 150))
    fr.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(40)))
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    k = min(1, tl / 0.15)
    d.text((W // 2, 125), 'LAKE BAIKAL · SEEN FROM SPACE', font=font(MONO, 38), fill=ICE + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 250), 'GIANT ICE RINGS', font(BLACK, 150), k, tl)
    if tl > 0.9: d.text((W // 2, 365), 'up to 7 km wide', font=font(XB, 60), fill=WH + (int(255 * min(1, (tl - 0.9) / 0.3)),), anchor='mm')
    if tl > dur - 0.25: L.putalpha(L.split()[3].point(lambda v: int(v * max(0, (dur - tl) / 0.25))))
    fr.alpha_composite(L)
    return fr.convert('RGB')

def title_card(p, tl, dur):
    fr = dimbg('gv14_i01.jpg', p, 'right', 0.25, 0.55, (0.5, 0.5))
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.25)
    rgb_split_text(d, (W // 2, 430), "MIA'S GLITCH DIARY", font(BLACK, 110), k, tl)
    d.text((W // 2, 545), f'ENTRY #{ENTRY}  ·  THE ICE RINGS OF BAIKAL', font=font(MONO, 44), fill=CY + (int(255 * k),), anchor='mm')
    avatar_badge(fr, W // 2 - 280, 650, k)
    return fr.convert('RGB')

def promise_card(p, tl, dur):
    fr = dimbg('gv14_i03.jpg', p, 'in', 0.1, 0.55)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 170), 'FOR YEARS, THE USUAL SUSPECT:', font=font(MONO, 40), fill=CY, anchor='mm')
    k = fade(p, 0.05)
    if k > 0: d.text((W // 2, 360), 'GAS FROM THE BOTTOM', font=font(BLACK, 110), fill=WH + (int(255 * k),), anchor='mm')
    k = fade(p, 0.25)
    if k > 0: d.text((W // 2, 480), 'of the deepest lake on Earth', font=font(XB, 56), fill=(210, 220, 235, int(255 * k)), anchor='mm')
    if p > 0.55: d.text((W // 2, 700), 'What really draws them…', font=font(XB, 56), fill=WH + (int(255 * fade(p, 0.55)),), anchor='mm')
    if p > 0.72: d.text((W // 2, 800), '…is stranger than the rumor', font=font(XB, 56), fill=AMB + (int(255 * fade(p, 0.72)),), anchor='mm')
    return fr.convert('RGB')

def stats_card(p, tl, dur):
    fr = dimbg('gv14_i04.jpg', p, 'in', 0.06, 0.66)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 130), 'LAKE BAIKAL · SOUTHERN SIBERIA', font=font(MONO, 44), fill=CY, anchor='mm')
    rows = [('636 KM', 'long', 0.02), ('1,642 M', 'deepest point: deepest lake on Earth', 0.18), ('25–30 MILLION', 'years old: the oldest lake', 0.36),
            ('> ALL GREAT LAKES', 'more fresh water than all five combined', 0.54), ('UNESCO 1996', 'World Heritage Site', 0.74)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 210 + i * 150
        d.rectangle((180, y + 8, 188, y + 118), fill=ICE + (int(255 * k),))
        d.text((220, y), a, font=font(BLACK, 76), fill=WH + (int(255 * k),))
        d.text((224, y + 88), b, font=font(SEMI, 36), fill=(210, 220, 235, int(255 * k)))
    src_line(d, 'Source: Wikipedia "Lake Baikal"; UNESCO World Heritage List')
    return fr.convert('RGB')

def icefacts_card(p, tl, dur):
    fr = dimbg('gv14_i14.jpg', p, 'in', 0.08, 0.6)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 170), 'EVERY WINTER', font=font(MONO, 46), fill=CY, anchor='mm')
    rows = [('FROZEN 4–5 MONTHS', 'from early January to May–June', 0.03), ('ICE 0.5–1.4 M THICK', 'strong enough to drive on', 0.35)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 330 + i * 250
        d.text((W // 2, y), a, font=font(BLACK, 100), fill=WH + (int(255 * k),), anchor='mm')
        d.text((W // 2, y + 100), b, font=font(XB, 48), fill=ICE + (int(255 * k),), anchor='mm')
    src_line(d, 'Source: Wikipedia "Lake Baikal"')
    return fr.convert('RGB')

def framed(fr, name, box, angle=0):
    x0, y0, x1, y1 = box
    im = img(name).copy(); im.thumbnail((x1 - x0, y1 - y0), Image.LANCZOS)
    w, h = im.size
    L = Image.new('RGBA', (w + 24, h + 24), (240, 236, 225, 255)); L.paste(im, (12, 12))
    if angle: L = L.rotate(angle, expand=True, resample=Image.BICUBIC)
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle((cx - L.width // 2 + 14, cy - L.height // 2 + 18, cx + L.width // 2 + 14, cy + L.height // 2 + 18), fill=(0, 0, 0, 150))
    fr.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    fr.alpha_composite(L, (cx - L.width // 2, cy - L.height // 2))

def iss_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA')
    framed(fr, 'gv14_r01.jpg', (820, 140, 1780, 900), angle=-1.5)
    d = ImageDraw.Draw(fr)
    d.text((150, 300), 'APRIL 2009', font=font(BLACK, 110), fill=WH)
    d.text((154, 430), 'International Space Station', font=font(XB, 52), fill=CY)
    if p > 0.3:
        k = fade(p, 0.3)
        d.text((154, 560), 'a dark circle of thin ice', font=font(XB, 52), fill=WH + (int(255 * k),))
        d.text((154, 630), '≈ 4.4 km across', font=font(BLACK, 74), fill=AMB + (int(255 * k),))
    if p > 0.6: d.text((154, 770), 'southern end of the lake', font=font(SEMI, 44), fill=(200, 210, 225, int(255 * fade(p, 0.6))))
    d.text((1300, 1010), 'Astronaut photo, NASA ISS Crew Earth Observations · public domain', font=font(MED, 22), fill=(170, 180, 200), anchor='mm')
    return fr.convert('RGB')

def shuttle_card(p, tl, dur):
    fr = dimbg('gv14_o04.jpg', p, 'in', 0.08, 0.62)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 160), 'THEN SCIENTISTS CHECKED OLDER PICTURES', font=font(MONO, 40), fill=CY, anchor='mm')
    x0, x1, y = 300, 1620, 560
    e = ease(min(1, p / 0.7))
    d.line((x0, y, x1, y), fill=(90, 110, 140), width=6)
    d.line((x0, y, x0 + (x1 - x0) * e, y), fill=ICE, width=10)
    for frac, yr, sub in ((0.0, '1985', 'Space Shuttle (STS-51B)'), (0.38, '1994', 'Space Shuttle (STS-59)'), (1.0, '2009', 'ISS: 2 rings')):
        if e + 0.001 < frac: continue
        x = x0 + (x1 - x0) * frac
        d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=WH)
        d.text((x, y - 90), yr, font=font(BLACK, 80), fill=WH, anchor='mm')
        d.text((x, y + 70), sub, font=font(SEMI, 36), fill=ICE, anchor='mm')
    if p > 0.75: d.text((W // 2, 820), 'similar circles, years apart', font=font(XB, 56), fill=AMB, anchor='mm')
    src_line(d, 'Source: NASA Earth Observatory, "Circles in Thin Ice, Lake Baikal, Russia" (2009)')
    return fr.convert('RGB')

def ring_layer(cx, cy, R, band, e, alpha=255):
    """top view: white thick ice, dark thin band of width band at radius R"""
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
    ro, ri = R * e, max(0, (R - band) * e)
    ld.ellipse((cx - ro, cy - ro, cx + ro, cy + ro), fill=(25, 45, 70, alpha))
    ld.ellipse((cx - ri, cy - ri, cx + ri, cy + ri), fill=(225, 238, 248, alpha))
    return L.filter(ImageFilter.GaussianBlur(6))

def anatomy_card(p, tl, dur):
    fr = Image.new('RGBA', (W, H), (205, 222, 236, 255))
    d = ImageDraw.Draw(fr)
    for i in range(0, W, 60): d.line((i, 0, i - 300, H), fill=(195, 212, 228), width=2)
    cx, cy = 640, 560
    e = ease(min(1, p / 0.45))
    fr.alpha_composite(ring_layer(cx, cy, 380, 95, e))
    d = ImageDraw.Draw(fr)
    if p > 0.35:
        k = fade(p, 0.35)
        d.line((cx - 380, 990, cx + 380, 990), fill=(10, 20, 35, int(255 * k)), width=4)
        d.text((cx, 1035), '~5–7 km across (typical)', font=font(XB, 40), fill=(10, 20, 35, int(255 * k)), anchor='mm')
    rows = [('DARK BAND', 'thin ice', (20, 40, 70), 0.3), ('WHITE CENTER', 'thick ice', (30, 60, 100), 0.5), ('WHITE OUTSIDE', 'thick ice', (30, 60, 100), 0.62),
            ('MARCH–APRIL', 'when most appear', MG, 0.78)]
    for i, (a, b, col, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 220 + i * 170
        d.text((1180, y), a, font=font(BLACK, 72), fill=col + (int(255 * k),))
        d.text((1184, y + 84), b, font=font(SEMI, 40), fill=(40, 60, 90, int(255 * k)))
    d.text((W // 2, 80), 'ANATOMY OF A BAIKAL ICE RING', font=font(MONO, 42), fill=(20, 40, 70), anchor='mm')
    d.text((1450, 1055), 'Schematic, not to scale · Sources: NASA EO (2020); Kouraev et al. 2021', font=font(MED, 22), fill=(60, 80, 110), anchor='mm')
    return fr.convert('RGB')

def kultuk_card(p, tl, dur):
    fr = Image.fromarray(np.asarray(map_frame(lerp(104.05, 104.0, ease(p)), 51.70, lerp(1.6, 1.35, ease(p)), tl, pin_alpha=0))).convert('RGBA')
    x, y = W * 0.52, H * 0.52
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
    e = ease(min(1, p / 0.3)); r = 120 * e
    ld.ellipse((x - r, y - r, x + r, y + r), outline=ICE + (255,), width=10)
    fr.alpha_composite(L)
    d = ImageDraw.Draw(fr)
    d.rounded_rectangle((90, 120, 900, 520), 24, fill=(4, 8, 16, 200))
    d.text((130, 160), 'APRIL 2020 · KULTUK BAY', font=font(MONO, 38), fill=CY)
    d.text((130, 230), '4.2 KM ACROSS', font=font(BLACK, 76), fill=WH)
    if p > 0.25: d.text((130, 330), 'dark band ~0.9 km wide', font=font(XB, 48), fill=ICE)
    if p > 0.5: d.text((130, 410), 'lasted ~15–17 days', font=font(XB, 48), fill=AMB)
    d.text((x, y + 160), 'ring position schematic', font=font(MONO, 24), fill=(220, 230, 240), anchor='mm')
    src_line(d, 'Source: Kouraev et al., The Cryosphere 15, 4501–4516 (2021)')
    return fr.convert('RGB')

def loop1_card(p, tl, dur):
    fr = dimbg(HOOK_IMG, p, 'in', 0.14, 0.55, HOOK_FOCUS)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    d.rounded_rectangle((300, 290, 1620, 790), 30, fill=(4, 8, 16, 190), outline=MG + (255,), width=4)
    d.text((W // 2, 360), 'OPEN FILE #1', font=font(MONO, 44), fill=MG + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 490), 'WHY IS THE CENTER', font(BLACK, 100), k, tl)
    rgb_split_text(d, (W // 2, 610), 'STILL THICK?', font(BLACK, 100), k, tl)
    d.text((W // 2, 725), 'the clue that explains everything', font=font(XB, 44), fill=AMB + (int(255 * k),), anchor='mm')
    return fr.convert('RGB')

def suspects_card(p, tl, dur):
    fr = dimbg('gv14_g01.jpg', p, 'in', 0.08, 0.7)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 130), 'WHAT DRAWS A CIRCLE ON A FROZEN LAKE?', font=font(MONO, 40), fill=CY, anchor='mm')
    rows = [('GAS HYDRATES', 'methane locked in the sediments: real, at Baikal', 'FACT', (130, 255, 190), 0.04),
            ('RISING GAS LIFTS DEEP WATER', 'and melts the ice from below', 'HYPOTHESIS', (255, 210, 120), 0.28),
            ('A GIANT METHANE BUBBLE', '"trapped under the ice, waiting to explode"', 'LEGEND', MG, 0.55)]
    for i, (a, b, tag, col, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 260 + i * 220
        d.text((170, y), a, font=font(BLACK, 76), fill=WH + (int(255 * k),))
        d.text((174, y + 92), b, font=font(SEMI, 38), fill=(205, 215, 230, int(255 * k)))
        tw = d.textlength(tag, font=font(BLACK, 46))
        d.rounded_rectangle((1750 - tw - 40, y + 14, 1750, y + 84), 12, outline=col + (int(255 * k),), width=5)
        d.text((1750 - 20, y + 49), tag, font=font(BLACK, 46), fill=col + (int(255 * k),), anchor='rm')
    src_line(d, 'Sources: Wikipedia "Lake Baikal"; Kouraev et al. 2021 (Granin et al. upwelling idea; media claims)')
    return fr.convert('RGB')

def archive_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 120), 'EVERY SATELLITE IMAGE THEY COULD FIND', font=font(MONO, 42), fill=CY, anchor='mm')
    x0, x1, y = 260, 1660, 430
    e = ease(min(1, p / 0.5))
    d.line((x0, y, x1, y), fill=(90, 110, 140), width=6)
    d.line((x0, y, x0 + (x1 - x0) * e, y), fill=ICE, width=10)
    for x, t in ((x0, '1969'), (x1, '2019')):
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=WH)
        d.text((x, y - 70), t, font=font(XB, 56), fill=WH, anchor='mm')
    r = random.Random(7)
    n = int(57 * e)
    for i in range(n):
        xx = x0 + 120 + (x1 - x0 - 140) * (0.15 + 0.85 * (i / 57) ** 0.6) + r.uniform(-20, 20)
        yy = y + 70 + r.uniform(0, 160)
        d.ellipse((xx - 14, yy - 14, xx + 14, yy + 14), outline=ICE, width=4)
    if p > 0.45:
        k = fade(p, 0.45)
        d.text((W // 2, 790), '57 RINGS ON BAIKAL', font=font(BLACK, 110), fill=WH + (int(255 * k),), anchor='mm')
    if p > 0.65:
        k = fade(p, 0.65)
        d.text((W // 2, 905), 'some over SHALLOW water: no place for gas hydrates', font=font(XB, 48), fill=AMB + (int(255 * k),), anchor='mm')
    src_line(d, 'Source: NASA Earth Observatory, "Baikal\'s Giant Ice Rings" (2020)')
    return fr.convert('RGB')

def loop2_card(p, tl, dur):
    fr = dimbg('gv14_v02.jpg', p, 'in', 0.1, 0.5)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    d.rounded_rectangle((330, 310, 1590, 770), 30, fill=(4, 8, 16, 190), outline=CY + (255,), width=4)
    d.text((W // 2, 380), 'OPEN FILE #2', font=font(MONO, 44), fill=CY + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 510), '2016: A VAN ON', font(BLACK, 100), k, tl)
    rgb_split_text(d, (W // 2, 630), 'THE EDGE OF A RING', font(BLACK, 100), k, tl)
    d.text((W // 2, 720), 'how did it end?', font=font(XB, 44), fill=AMB + (int(255 * k),), anchor='mm')
    return fr.convert('RGB')

def team_card(p, tl, dur):
    fr = dimbg('gv14_o06.jpg', p, 'in', 0.06, 0.68)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 150), 'THE ANSWER · 2016–2021', font=font(MONO, 44), fill=CY, anchor='mm')
    d.text((W // 2, 300), 'Alexei Kouraev & colleagues', font=font(BLACK, 86), fill=WH, anchor='mm')
    d.text((W // 2, 395), 'University of Toulouse (LEGOS) · with Russian scientists', font=font(SEMI, 42), fill=ICE, anchor='mm')
    rows = [('SATELLITES', 'optical + radar images of the ice', 0.25), ('MEASUREMENTS FROM THE ICE', 'water temperature down to 200 m', 0.45)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 540 + i * 170
        d.text((W // 2, y), a, font=font(BLACK, 70), fill=WH + (int(255 * k),), anchor='mm')
        d.text((W // 2, y + 74), b, font=font(XB, 44), fill=AMB + (int(255 * k),), anchor='mm')
    src_line(d, 'Kouraev et al., Limnology & Oceanography (2016, 2019); The Cryosphere (2021) · NASA Earth Observatory (2020)')
    return fr.convert('RGB')

def eddy_card(p, tl, dur):
    """top view of a clockwise eddy under ice + numbers"""
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 110), 'WHAT THEY FOUND UNDER THE RINGS', font=font(MONO, 42), fill=CY, anchor='mm')
    cx, cy, R = 600, 590, 330
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
    for i in range(10, 0, -1):
        rr = R * i / 10
        ld.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(255, 140 + 9 * (10 - i), 60, 26))
    fr.alpha_composite(L.filter(ImageFilter.GaussianBlur(10))); d = ImageDraw.Draw(fr)
    rot = -tl * 1.2  # clockwise on screen
    for ring in (0.45, 0.7, 0.95):
        rr = R * ring
        for j in range(6):
            a0 = rot * (0.6 + ring) + j * math.pi / 3
            pts = [(cx + rr * math.cos(a0 - s * 0.6), cy + rr * math.sin(a0 - s * 0.6)) for s in np.linspace(0, 1, 12)]
            d.line(pts, fill=WH, width=int(3 + 5 * ring))
            hx, hy = pts[0]; tx, ty = math.cos(a0 + math.pi / 2), math.sin(a0 + math.pi / 2)
            d.polygon([(hx + tx * 18, hy + ty * 18), (hx - ty * 9 - tx * 4, hy + tx * 9 - ty * 4), (hx + ty * 9 - tx * 4, hy - tx * 9 - ty * 4)], fill=WH)
    d.text((cx, cy + R + 60), 'warm eddy (top view)', font=font(XB, 40), fill=AMB, anchor='mm')
    rows = [('CLOCKWISE', 'one full turn in ~3 days', 0.08), ('+1–2 °C', 'warmer than the water around it', 0.3), ('~10–12 KM', 'across, where it is widest', 0.52), ('LENS-SHAPED', 'common in oceans, rare in lakes', 0.72)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 230 + i * 180
        d.text((1080, y), a, font=font(BLACK, 80), fill=WH + (int(255 * k),))
        d.text((1084, y + 92), b, font=font(SEMI, 40), fill=ICE + (int(255 * k),))
    d.text((W // 2, 1045), 'Schematic · Sources: NASA Earth Observatory (2020); Kouraev et al., The Cryosphere (2021)', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def melt_card(p, tl, dur):
    """cross-section: ice on top, lens eddy below, strong currents at rim melt the ice from below"""
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 100), 'WHY ONLY A RING MELTS', font=font(MONO, 44), fill=CY, anchor='mm')
    top, ice_h = 250, 70
    d.rectangle((0, top + ice_h, W, H), fill=(10, 32, 58))
    cx, cy, a, b = W // 2, 560, 620, 170
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
    ld.ellipse((cx - a, cy - b, cx + a, cy + b), fill=(255, 150, 60, 110))
    fr.alpha_composite(L.filter(ImageFilter.GaussianBlur(18))); d = ImageDraw.Draw(fr)
    e = ease(min(1, max(0, (p - 0.15) / 0.6)))
    # ice: thickness profile (thin near |x-cx| ~ 0.75a)
    poly = [(0, top)]
    bottom = []
    for x in range(0, W + 1, 8):
        u = abs(x - cx) / a
        thin = math.exp(-((u - 0.78) / 0.13) ** 2)
        hh = ice_h * (1 - 0.72 * thin * e)
        bottom.append((x, top + hh))
    d.polygon([(0, top), (W, top)] + bottom[::-1], fill=(228, 240, 250))
    # arrows: weak in center, strong at rims
    for side in (-1, 1):
        for j in range(3):
            y = 470 + j * 90
            x = cx + side * (a * 0.78)
            L2 = 70 + 40 * (1 - j * 0.2)
            d.line((x - side * 0 , y, x, y - L2 * 0.9), fill=AMB, width=10)
            d.polygon([(x - 16, y - L2 * 0.9), (x + 16, y - L2 * 0.9), (x, y - L2 * 0.9 - 26)], fill=AMB)
    d.line((cx - 40, 560, cx + 40, 560), fill=(255, 220, 180), width=4)
    d.text((cx, 600), 'center: weak currents', font=font(XB, 42), fill=WH, anchor='mm')
    d.text((cx, 650), 'warm water, but the ice holds', font=font(SEMI, 34), fill=(210, 220, 235), anchor='mm')
    if p > 0.45:
        k = fade(p, 0.45)
        for side in (-1, 1):
            d.text((cx + side * a * 0.78, 800), 'edge: strong currents', font=font(XB, 40), fill=AMB + (int(255 * k),), anchor='mm')
            d.text((cx + side * a * 0.78, 850), 'ice melts from below', font=font(SEMI, 34), fill=WH + (int(255 * k),), anchor='mm')
    d.text((150, top + 35), 'ICE', font=font(BLACK, 40), fill=(40, 70, 110), anchor='lm')
    if p > 0.75:
        k = fade(p, 0.75)
        d.text((W // 2, 960), 'THE RING = THE OUTLINE OF THE WHIRLPOOL', font=font(BLACK, 62), fill=WH + (int(255 * k),), anchor='mm')
    d.text((W // 2, 1045), 'Schematic cross-section, not to scale · after Kouraev (NASA Earth Observatory, 2020)', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def van_card(p, tl, dur):
    fr = dimbg('gv14_i07.jpg', p, 'in', 0.08, 0.62)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 150), '2016 · CAPE NIZHNEYE IZGOLOVYE', font=font(MONO, 42), fill=CY, anchor='mm')
    rows = [('THE VAN BROKE THROUGH', 'along the edge of the ring, and sank', WH, 0.03), ('EVERYONE ESCAPED', 'driver and passengers were rescued', (130, 255, 190), 0.3),
            ('13 OF 57 RINGS', 'formed in this one area', AMB, 0.55)]
    for i, (a, b, col, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 290 + i * 200
        d.text((W // 2, y), a, font=font(BLACK, 88), fill=col + (int(255 * k),), anchor='mm')
        d.text((W // 2, y + 88), b, font=font(XB, 44), fill=(215, 225, 240, int(255 * k)), anchor='mm')
    if p > 0.78: d.text((W // 2, 930), 'Kouraev: "take a more southerly route"', font=font(XB, 50), fill=ICE, anchor='mm')
    src_line(d, 'Source: NASA Earth Observatory, "Baikal\'s Giant Ice Rings" (2020) · photo: ice crack, for illustration')
    return fr.convert('RGB')

def twist_card(p, tl, dur):
    fr = dimbg('gv14_o05.jpg', p, 'in', 0.12, 0.55)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.2)
    d.text((W // 2, 250), 'THE TWIST', font=font(MONO, 50), fill=MG + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 440), 'THE RING IS DRAWN', font(BLACK, 120), k, tl)
    rgb_split_text(d, (W // 2, 580), 'BEFORE THE ICE EXISTS', font(BLACK, 120), k, tl)
    if p > 0.4: d.text((W // 2, 760), 'eddies usually start in autumn, on open water', font=font(SEMI, 44), fill=CY, anchor='mm')
    return fr.convert('RGB')

def season_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 120), 'ONE RING, THREE SEASONS', font=font(MONO, 44), fill=CY, anchor='mm')
    cols = [('AUTUMN', 'open water', 'winds + river inflow\nspin up a warm eddy', AMB, 0.02), ('WINTER', 'ice forms on top', 'the eddy keeps turning\nunderneath', ICE, 0.3),
            ('MARCH–APRIL', 'the ring appears', 'the pattern was there\nall along', MG, 0.58)]
    for i, (a, b, c, col, t0) in enumerate(cols):
        k = fade(p, t0)
        if k <= 0: continue
        x = 340 + i * 620
        d.rounded_rectangle((x - 270, 230, x + 270, 860), 26, outline=col + (int(255 * k),), width=5, fill=(8, 14, 26, int(200 * k)))
        d.text((x, 320), a, font=font(BLACK, 64), fill=col + (int(255 * k),), anchor='mm')
        d.text((x, 400), b, font=font(XB, 44), fill=WH + (int(255 * k),), anchor='mm')
        cy_ = 600
        if i == 0:
            d.ellipse((x - 120, cy_ - 50, x + 120, cy_ + 50), fill=(255, 150, 60, int(140 * k)))
        elif i == 1:
            d.rectangle((x - 200, cy_ - 90, x + 200, cy_ - 60), fill=(228, 240, 250, int(255 * k)))
            d.ellipse((x - 120, cy_ - 40, x + 120, cy_ + 60), fill=(255, 150, 60, int(140 * k)))
        else:
            fr.alpha_composite(ring_layer(x, cy_, 110, 32, 1.0, int(255 * k))); d = ImageDraw.Draw(fr)
        for j, ln in enumerate(c.split('\n')):
            d.text((x, 740 + j * 50), ln, font=font(SEMI, 38), fill=(210, 220, 235, int(255 * k)), anchor='mm')
    if p > 0.82: d.text((W // 2, 950), 'THE ICE IS JUST THE PAPER', font=font(BLACK, 70), fill=WH, anchor='mm')
    src_line(d, 'Sources: NASA Earth Observatory (2020); Kouraev et al., The Cryosphere (2021) · schematic')
    return fr.convert('RGB')

def lakes_card(p, tl, dur):
    return map_frame(lerp(97.0, 97.5, ease(p)), 52.6, 26.0, tl, pin_alpha=0, lakes=True)

def warn_card(p, tl, dur):
    fr = dimbg('gv14_i01.jpg', p, 'in', 0.1, 0.55)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    rgb_split_text(d, (W // 2, 400), 'THE MOST DANGEROUS ICE', font(BLACK, 104), k, tl)
    rgb_split_text(d, (W // 2, 530), 'CAN LOOK NORMAL', font(BLACK, 104), k, tl)
    if p > 0.4: d.text((W // 2, 700), 'some of the best warnings come from orbit', font=font(XB, 54), fill=ICE, anchor='mm')
    return fr.convert('RGB')

def question_card(p, tl, dur):
    fr = dimbg('gv14_i14.jpg', p, 'in', 0.14, 0.62)
    d = ImageDraw.Draw(fr)
    if p > 0.03: d.text((W // 2, 250), 'A WARM WHIRLPOOL COULD BE TURNING UNDER THE ICE…', font=font(MONO, 40), fill=CY, anchor='mm')
    if p > 0.14: d.text((W // 2, 430), 'WOULD YOU STILL DRIVE', font=font(BLACK, 104), fill=WH, anchor='mm')
    if p > 0.24: d.text((W // 2, 560), 'ACROSS FROZEN BAIKAL?', font=font(BLACK, 104), fill=AMB, anchor='mm')
    if p > 0.4: d.text((W // 2, 720), 'YES  or  NO', font=font(BLACK, 80), fill=ICE, anchor='mm')
    if p > 0.5: d.text((W // 2, 860), '↓  Tell me in the comments', font=font(XB, 54), fill=WH, anchor='mm')
    return fr.convert('RGB')

LOGO = Image.open(S + 'logo_800.png').convert('RGBA')
def endcard(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    lg = LOGO.resize((300, 300))
    fr.alpha_composite(lg, (W // 2 - 150, 70))
    d.text((W // 2, 440), 'SUBSCRIBE FOR THE NEXT ENTRY', font=font(BLACK, 68), fill=WH, anchor='mm')
    d.text((W // 2, 515), f"Mia's Glitch Diary · entry #{ENTRY} · real places, real glitches", font=font(SEMI, 36), fill=CY, anchor='mm')
    for x in (380, 1540):
        d.rounded_rectangle((x - 300, 620, x + 300, 960), 24, outline=(60, 80, 110), width=3)
    avatar_badge(fr, W // 2 - 280, 700, 1.0, 'AI HOST · FICTIONAL')
    return fr.convert('RGB')

SEG = {
 's01': [dict(card(hook_card, glitch=False, credit=HOOK_IMG), dur=3.0), dict(card(title_card, credit='gv14_i01.jpg'), dur=3.0),
         img_shot('gv14_r01.jpg', 'in', ('A DARK RING ON WHITE ICE', 'astronaut photo, April 2009'), amt=0.25, focus=(0.5, 0.5)),
         img_shot('gv14_i14.jpg', 'right', ('FROM THE ICE: NOTHING TO SEE', 'frozen Baikal, February'), amt=0.2)],
 's02': [img_shot('gv14_i02.jpg', 'right', ('THE ICE RINGS OF LAKE BAIKAL', 'Southern Siberia, Russia'), amt=0.25),
         card(promise_card, w=2.6, credit='gv14_i03.jpg'), img_shot('gv14_i06.jpg', 'in', ('GAS FROM THE BOTTOM?', 'air bubbles frozen in Baikal ice'), amt=0.15)],
 's03': [card(map_in, glitch=False, w=2.4, credit='gv14_s2_south.jpg', grade=True), card(stats_card, w=3.0, credit='gv14_i04.jpg'),
         img_shot('gv14_o01.jpg', 'in', ('THE DEEPEST LAKE ON EARTH', 'seen from the International Space Station'), amt=0.15)],
 's04': [img_shot('gv14_o06.jpg', 'in', ('FROZEN FROM END TO END', 'satellite view, January 2024'), amt=0.12), card(icefacts_card, w=2.0, credit='gv14_i14.jpg'),
         img_shot('gv14_i01.jpg', 'in', ('CLEAR ENOUGH TO SEE THE DARK WATER', 'black ice near Olkhon Island'), amt=0.2)],
 's05': [card(iss_card, w=2.6), img_shot('gv14_r02.jpg', 'in', ('THE SOUTHERN END OF THE LAKE', 'ISS Expedition 19, April 2009'), amt=0.2),
         img_shot('gv14_o03.jpg', 'right', ('A SECOND RING, MID-LAKE', 'above an underwater ridge, same spring'), amt=0.2), card(shuttle_card, w=2.2, credit='gv14_o04.jpg')],
 's06': [card(anatomy_card, w=2.6), img_shot('gv14_i10.jpg', 'in', ('SOME LAST A DAY OR TWO', 'others for weeks'), amt=0.18), card(kultuk_card, w=2.6, credit='gv14_s2_south.jpg', grade=True)],
 's07': [card(loop1_card, w=1.6, credit=HOOK_IMG), img_shot('gv14_r01.jpg', 'in', ('WARM WATER BELOW…', '…but the center stays thick and white'), amt=0.35, focus=(0.5, 0.5))],
 's08': [card(suspects_card, w=3.2, credit='gv14_g01.jpg'), img_shot('gv14_g01.jpg', 'in', ('GAS-HYDRATE RESEARCH ON THE ICE', 'Irkutsk Scientific Center, Baikal'), amt=0.12),
         img_shot('gv14_i05.jpg', 'in', ('A BUBBLE WAITING TO EXPLODE?', 'that one goes into my legend file'), amt=0.15)],
 's09': [card(archive_card, w=3.0), img_shot('gv14_o05.jpg', 'in', ('SHALLOW WATER, RINGS ANYWAY', 'satellite view of Baikal, MODIS'), amt=0.15)],
 's10': [card(loop2_card, w=1.6, credit='gv14_v02.jpg'), img_shot('gv14_i14.jpg', 'in', ('PEOPLE TRAVEL ON THIS ICE', 'every winter'), amt=0.3, focus=(0.55, 0.45))],
 's11': [card(team_card, w=2.4, credit='gv14_o06.jpg'), img_shot('gv14_e02.jpg', 'in', ('AN EDDY', 'ocean eddy seen by satellite, for illustration'), amt=0.15),
         img_shot('gv14_e01.jpg', 'right', ('A SLOW, GIANT WHIRLPOOL', 'Black Sea swirls, for illustration'), amt=0.2)],
 's12': [card(eddy_card, w=3.0), img_shot('gv14_e03.jpg', 'in', ('COMMON IN THE OCEAN', 'ice eddy off Labrador, for illustration'), amt=0.15)],
 's13': [card(melt_card, w=3.4), img_shot('gv14_r01.jpg', 'out', ('THE OUTLINE OF THE WHIRLPOOL', 'printed on the ice'), amt=0.3)],
 's14': [card(van_card, w=3.0, credit='gv14_i07.jpg'), img_shot('gv14_v01.jpg', 'in', ('HOVERCRAFT, CARS, TRUCKS', 'winter traffic on Baikal ice'), amt=0.15)],
 's15': [card(twist_card, w=1.5, credit='gv14_o05.jpg'), card(season_card, w=3.2), img_shot('gv14_i04.jpg', 'in', ('AUTUMN: THE FIRST ICE', 'the pattern is already in the water'), amt=0.15)],
 's16': [card(map_out, glitch=False, w=1.6, credit='gv14_s2_wide.jpg', grade=True), img_shot('gv14_o09.jpg', 'in', ('LAKE HOVSGOL, MONGOLIA', 'rings seen here too'), amt=0.15),
         card(warn_card, w=1.6, credit='gv14_i01.jpg'), img_shot('gv14_o08.jpg', 'in', ('WARNINGS FROM ORBIT', 'Baikal at night, from the ISS'), amt=0.12)],
 's17': [card(question_card, w=2.6, credit='gv14_i14.jpg', grade=True), img_shot('gv14_i02.jpg', 'out', ('SUBSCRIBE', 'for the next entry of my Glitch Diary'), amt=0.2)],
 'end': [card(endcard, glitch=False)],
}
CHAPTERS = {'s03': (1, 'The deepest lake on Earth'), 's05': (2, 'Rings seen from orbit'), 's08': (3, 'The methane suspect'),
            's11': (4, 'Whirlpools under the ice'), 's15': (5, 'The twist'), 's17': (6, 'Your turn')}
def build_timeline():
    shots = []
    order = list(TIM.keys()) + ['end']
    for sid in order:
        if sid == 'end': a, b = TIM[LAST]['end'], TOTAL
        else: a, b = TIM[sid]['start'], TIM[sid]['end']
        lst = SEG[sid]
        fixed = sum(s.get('dur', 0) for s in lst)
        tot = sum(s['w'] for s in lst if 'dur' not in s)
        t = a
        for s in lst:
            d = s['dur'] if 'dur' in s else (b - a - fixed) * s['w'] / tot
            shots.append(dict(s, start=t, end=t + d, seg=sid, chapter=CHAPTERS.get(sid) if s is lst[0] else None))
            t += d
    return shots

TEXT_CACHE = {}
def cached(key, fn):
    if key not in TEXT_CACHE: TEXT_CACHE[key] = fn()
    return TEXT_CACHE[key]

def render_shot_frame(sh, tl, k):
    dur = sh['end'] - sh['start']; p = tl / dur
    if sh['kind'] == 'card':
        fr = sh['fn'](p, tl, dur).convert('RGBA')
        if sh.get('credit'):
            L = cached(('cred', sh['credit']), lambda: credit_layer(sh['credit']))
            if L: fr.alpha_composite(L)
    else:
        fr = kenburns(sh['name'], p, sh['move'], sh['amt'], sh['focus'], sh['darken']).convert('RGBA')
        if sh['text']:
            L = cached(('low',) + tuple(sh['text']), lambda: lower(*sh['text']))
            a = min(1, max(0, (tl - 0.35) / 0.35)) * min(1, max(0, (dur - tl) / 0.3))
            if a > 0:
                if a < 1: L = L.copy(); L.putalpha(L.split()[3].point(lambda v: int(v * a)))
                fr.alpha_composite(L)
        L = cached(('cred', sh['name']), lambda: credit_layer(sh['name']))
        if L: fr.alpha_composite(L)
    if sh['chapter'] and tl < 3.2:
        L = cached(('ch',) + sh['chapter'], lambda: chapter_layer(*sh['chapter']))
        a = min(1, tl / 0.3) * min(1, (3.2 - tl) / 0.4)
        if a < 1: L = L.copy(); L.putalpha(L.split()[3].point(lambda v: int(v * a)))
        fr.alpha_composite(L)
    if sh['seg'] != 'end' and sh['start'] >= 6.0:
        fr.alpha_composite(BUG)
    a = finish(fr.convert('RGB'), k, grade=sh['kind'] != 'card' or sh.get('grade'))
    if sh.get('glitch', True) and tl < 0.2 and sh['start'] > 0:
        a = glitch_np(a, 1 - tl / 0.2, int(sh['start'] * 100) + int(tl * 30))
    return a

def main():
    shots = build_timeline()
    os.makedirs(OUT, exist_ok=True)
    json.dump([{k: v for k, v in s.items() if k not in ('fn',)} for s in shots], open(OUT + 'shots.json', 'w'), indent=1, default=str)
    if '--still' in sys.argv:
        for ts in [float(x) for x in sys.argv[sys.argv.index('--still') + 1].split(',')]:
            sh = next(s for s in shots if s['start'] <= ts < s['end'])
            Image.fromarray(render_shot_frame(sh, ts - sh['start'], 0)).save(OUT + f'still_{ts:06.1f}.jpg', quality=85)
        return
    nf_total = int(round(TOTAL * FPS))
    f0, f1, out = 0, nf_total, OUT + 'video.mp4'
    if '--part' in sys.argv:
        i = sys.argv.index('--part'); pi, pn = int(sys.argv[i + 1]), int(sys.argv[i + 2])
        f0 = nf_total * pi // pn; f1 = nf_total * (pi + 1) // pn; out = OUT + f'part{pi}.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-tune', 'film', '-pix_fmt', 'yuv420p', '-threads', '1', out], stdin=subprocess.PIPE)
    si = 0
    for k in range(f0, f1):
        t = k / FPS
        while si < len(shots) - 1 and t >= shots[si]['end']: si += 1
        sh = shots[si]
        p.stdin.write(render_shot_frame(sh, t - sh['start'], k).tobytes())
        if k % 900 == 0: print(f'{k}/{f1}', flush=True)
    p.stdin.close(); p.wait()
    print('done', out)

if __name__ == '__main__':
    main()
