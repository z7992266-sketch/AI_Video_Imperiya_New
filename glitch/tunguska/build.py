"""GLITCHVERSE — Tunguska event flagship (Mia's Glitch Diary #10). 1920x1080, 30 fps.
Usage: python3 build.py [--part i n] [--still t1,t2]"""
import sys
sys.path.insert(0, '/home/claude/gv')
from base import *

ENTRY = 10
LAST = 's21'
AMB = (255, 170, 80)
for k in ('tg10_s2_wide.jpg', 'tg10_s2_mid.jpg', 'tg10_s2_close.jpg', 'tg10_s2_cheko.jpg'): CRED[k] = EOX
def have(n): return os.path.exists(A + n)

# ---------- MAP (equirectangular crops, aspect corrected by cos(lat)) ----------
SRC = [('tg10_s2_close.jpg', 100.7, 103.1, 60.25, 61.35), ('tg10_s2_mid.jpg', 94, 110, 56, 65), ('tg10_s2_wide.jpg', 55, 145, 38, 76)]
EPI = (101.894, 60.886); CHEKO = (101.860, 60.964); VAN = (102.28, 60.34)
LABELS = [('RUSSIA', 88, 63.5, 'cty'), ('KAZAKHSTAN', 70, 48.5, 'cty'), ('MONGOLIA', 103, 47.3, 'cty'), ('CHINA', 112, 42.5, 'cty'),
          ('SIBERIA', 104, 65.0, 'des'), ('Lake Baikal', 108.2, 53.6, 'city'), ('Krasnoyarsk', 92.87, 56.01, 'city'), ('Irkutsk', 104.3, 52.29, 'city'),
          ('Vanavara', VAN[0], VAN[1], 'city'), ('PODKAMENNAYA TUNGUSKA', 98.6, 61.35, 'riv'), ('Lake Cheko', CHEKO[0], CHEKO[1], 'lake')]

def map_frame(cx, cy, wdeg, t, pin_alpha=1.0):
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
        if not (-300 < x < W + 300 and -100 < y < H + 100): continue
        if kind == 'cty' and wdeg < 14: continue
        if kind == 'des' and wdeg < 7: continue
        if kind == 'city' and txt in ('Krasnoyarsk', 'Irkutsk', 'Lake Baikal') and not (6 < wdeg < 45): continue
        if txt == 'Vanavara' and not (0.9 < wdeg < 9): continue
        if kind == 'riv' and not (2.5 < wdeg < 16): continue
        if kind == 'lake' and wdeg > 1.8: continue
        sz = {'cty': 40, 'des': 40, 'city': 30, 'riv': 28, 'lake': 30}[kind]
        col = {'cty': (255, 255, 255, 230), 'des': (255, 220, 170, 240), 'city': (255, 255, 255, 235), 'riv': (170, 225, 255, 235), 'lake': (170, 225, 255, 255)}[kind]
        f = font(XB if kind in ('cty', 'des') else BOLD, sz)
        if kind in ('city', 'lake'):
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=col[:3] + (230,), outline=(0, 0, 0, 160), width=2)
            dx = -18 if txt == 'Lake Cheko' else 18
            anc = 'rm' if dx < 0 else 'lm'
            d.text((x + dx + 2, y + 2), txt, font=f, fill=(0, 0, 0, 170), anchor=anc)
            d.text((x + dx, y), txt, font=f, fill=col, anchor=anc)
        else:
            d.text((x + 3, y + 3), txt, font=f, fill=(0, 0, 0, 150), anchor='mm')
            d.text((x, y), txt, font=f, fill=col, anchor='mm')
    x, y = sxy(*EPI)
    if pin_alpha > 0:
        a = int(255 * pin_alpha)
        r = 18 + 10 * (0.5 + 0.5 * math.sin(t * 6))
        d.ellipse((x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2), outline=AMB + (int(a * 0.7),), width=4)
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=MG + (a,), outline=(255, 255, 255, a), width=4)
        f = font(BLACK, 46)
        d.text((x + 52, y + 20), 'TUNGUSKA · 1908', font=f, fill=(0, 0, 0, int(a * 0.6)), anchor='lm')
        d.text((x + 48, y + 16), 'TUNGUSKA · 1908', font=f, fill=(255, 255, 255, a), anchor='lm')
        d.text((x + 50, y + 62), '60.89°N  101.89°E · epicenter', font=font(MONO, 26), fill=CY + (a,), anchor='lm')
    return fr.convert('RGB')

def lerp(a, b, e): return a + (b - a) * e
def log_lerp(a, b, e): return math.exp(math.log(a) + (math.log(b) - math.log(a)) * e)
def map_in(p, tl, dur):
    e = ease(min(1, p / 0.9))
    return map_frame(lerp(98.0, EPI[0], e), lerp(57.0, EPI[1], e), log_lerp(62.0, 1.25, e), tl, pin_alpha=min(1, max(0, (p - 0.35) / 0.15)))
def map_out(p, tl, dur):
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

# ---------- cards ----------
def dim_or(name, alt): return name if have(name) else alt

def hook_card(p, tl, dur):
    fr = kenburns('tg10_h01.jpg', p, 'in', 0.22, (0.5, 0.45)).convert('RGBA')
    sh_ = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh_)
    sd.rounded_rectangle((300, 320, 1620, 780), 40, fill=(0, 0, 0, 150))
    fr.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(40)))
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    k = min(1, tl / 0.15)
    rgb_split_text(d, (W // 2, 545), 'NO CRATER.', font(BLACK, 190), k, tl)
    d.text((W // 2, 385), '1908 · SIBERIA · 2,150 KM² OF FOREST FLATTENED', font=font(MONO, 36), fill=AMB + (int(255 * k),), anchor='mm')
    if tl > 0.9: d.text((W // 2, 700), 'So what exploded?', font=font(XB, 58), fill=WH + (int(255 * min(1, (tl - 0.9) / 0.3)),), anchor='mm')
    if tl > dur - 0.25: L.putalpha(L.split()[3].point(lambda v: int(v * max(0, (dur - tl) / 0.25))))
    fr.alpha_composite(L)
    return fr.convert('RGB')

def title_card(p, tl, dur):
    fr = dimbg('tg10_p02.jpg', p, 'right', 0.25, 0.55, (0.45, 0.35))
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.25)
    rgb_split_text(d, (W // 2, 430), "MIA'S GLITCH DIARY", font(BLACK, 110), k, tl)
    d.text((W // 2, 545), f'ENTRY #{ENTRY}  ·  THE TUNGUSKA EVENT', font=font(MONO, 44), fill=CY + (int(255 * k),), anchor='mm')
    avatar_badge(fr, W // 2 - 280, 650, k)
    return fr.convert('RGB')

def whathit_card(p, tl, dur):
    fr = dimbg('tg10_a01.jpg', p, 'in', 0.1, 0.45)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 170), 'THE BIGGEST COSMIC BLAST IN RECORDED HISTORY', font=font(MONO, 38), fill=CY, anchor='mm')
    items = [('NO HOLE IN THE GROUND.', 0.05), ('NO ROCK TO SHOW FOR IT.', 0.25)]
    for i, (t, t0) in enumerate(items):
        k = fade(p, t0)
        if k > 0: d.text((W // 2, 380 + i * 150), t, font=font(BLACK, 96), fill=WH + (int(255 * k),), anchor='mm')
    if p > 0.55:
        k = fade(p, 0.55)
        d.text((W // 2, 720), 'What most scientists think happened…', font=font(XB, 52), fill=WH + (int(255 * k),), anchor='mm')
    if p > 0.72:
        k = fade(p, 0.72)
        d.text((W // 2, 820), '…and why one team says it flew away', font=font(XB, 52), fill=AMB + (int(255 * k),), anchor='mm')
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

def quote_card(p, tl, dur):
    fr = dimbg('tg10_p03.jpg', p, 'in', 0.08, 0.72)
    d = ImageDraw.Draw(fr)
    d.text((160, 170), 'SEMYON SEMYONOV · VANAVARA · ~60 KM AWAY', font=font(MONO, 36), fill=CY)
    lines = ['"…the sky was split in two,', 'and high above the forest the whole', 'northern part of the sky appeared', 'to be covered with fire…', 'I felt great heat, as if my shirt', 'had caught fire."']
    n = len(lines)
    for i, ln in enumerate(lines):
        t0 = 0.04 + i * 0.1
        if p < t0: break
        type_on(d, (160, 280 + i * 92), ln, font(XB, 64), (p - t0) / 0.1, WH if i < 4 else AMB)
    src_line(d, 'Letter written in 1930 (as quoted in Wikipedia, "Tunguska event")')
    return fr.convert('RGB')

def records_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 140), 'RECORDED FAR AWAY', font=font(MONO, 44), fill=CY, anchor='mm')
    rows = [('WINDOWS SHATTERED', 'up to ~200 km away', 0.05), ('SEISMOGRAPHS', 'Irkutsk · Tiflis · Jena · Tashkent', 0.25),
            ('BAROGRAPHS', 'pressure wave detected around the world', 0.5)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 270 + i * 230
        d.rectangle((180, y + 6, 188, y + 150), fill=AMB + (int(255 * k),))
        d.text((220, y), a, font=font(BLACK, 90), fill=WH + (int(255 * k),))
        d.text((224, y + 112), b, font=font(SEMI, 44), fill=(210, 220, 235, int(255 * k)))
    src_line(d, 'Source: Wikipedia "Tunguska event" (seismic & barometric records, published 1910–1930s)')
    return fr.convert('RGB')

def news_card(p, tl, dur):
    fr = dimbg('tg10_p09.jpg', p, 'in', 0.06, 0.7)
    framed(fr, 'tg10_h05.jpg', (220, 60, 520, 1020), angle=2)
    d = ImageDraw.Draw(fr)
    d.text((700, 330), 'SIBIRSKAYA ZHIZN · 1908', font=font(MONO, 40), fill=CY)
    d.text((700, 400), 'One of the first reports —', font=font(XB, 58), fill=WH)
    d.text((700, 470), 'written from rumors.', font=font(XB, 58), fill=WH)
    if p > 0.35:
        d.text((700, 620), 'At least 3 people reported dead.', font=font(SEMI, 46), fill=AMB)
        d.text((700, 685), 'Reindeer killed. Fires in the taiga.', font=font(SEMI, 46), fill=(220, 225, 235))
    return fr.convert('RGB')

def nineteen_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    rgb_split_text(d, (W // 2, 380), 'NO ONE CAME', font(BLACK, 130), k, tl)
    rgb_split_text(d, (W // 2, 530), 'FOR 19 YEARS', font(BLACK, 130), k, tl)
    x0, x1, y = 360, 1560, 760
    d.line((x0, y, x1, y), fill=(90, 110, 140), width=6)
    e = ease(min(1, p / 0.8))
    d.line((x0, y, x0 + (x1 - x0) * e, y), fill=AMB, width=10)
    for x, t in ((x0, '1908'), (x1, '1927')):
        d.ellipse((x - 14, y - 14, x + 14, y + 14), fill=WH)
        d.text((x, y + 60), t, font=font(XB, 52), fill=WH, anchor='mm')
    d.text((W // 2, y + 140), 'war · revolution · remoteness', font=font(SEMI, 40), fill=(170, 180, 200), anchor='mm')
    return fr.convert('RGB')

def loop1_card(p, tl, dur):
    fr = dimbg('tg10_h01.jpg', p, 'in', 0.14, 0.55, (0.6, 0.35))
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    d.rounded_rectangle((330, 290, 1590, 790), 30, fill=(4, 8, 16, 190), outline=MG + (255,), width=4)
    d.text((W // 2, 360), 'OPEN FILE #1', font=font(MONO, 44), fill=MG + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 490), 'THE TREES THAT', font(BLACK, 100), k, tl)
    rgb_split_text(d, (W // 2, 610), 'STAYED STANDING', font(BLACK, 100), k, tl)
    d.text((W // 2, 725), 'the clue that solves half the mystery', font=font(XB, 44), fill=AMB + (int(255 * k),), anchor='mm')
    return fr.convert('RGB')

def kulik_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA')
    framed(fr, 'tg10_h04.jpg', (180, 180, 640, 900))
    d = ImageDraw.Draw(fr)
    d.text((780, 300), 'LEONID KULIK', font=font(BLACK, 100), fill=WH)
    d.text((784, 420), 'mineralogist · Mineralogical Museum, St Petersburg', font=font(SEMI, 40), fill=CY)
    if p > 0.3:
        d.text((784, 560), '1921: first expedition', font=font(XB, 56), fill=WH)
        d.text((784, 630), 'never reached the center', font=font(SEMI, 44), fill=(200, 210, 225))
    if p > 0.6:
        d.text((784, 760), 'Convinced: a giant iron meteorite', font=font(XB, 52), fill=AMB)
    src_line(d, 'Photo: E. L. Krinov (Kulik expedition), public domain · Source: Wikipedia "Leonid Kulik"')
    return fr.convert('RGB')

def scheme_card(p, tl, dur):
    fr = dimbg('tg10_h02.jpg', p, 'in', 0.06, 0.65)
    framed(fr, 'tg10_h03.jpg', (1180, 60, 1720, 1010), angle=-2)
    d = ImageDraw.Draw(fr)
    d.text((160, 330), '1927', font=font(BLACK, 150), fill=WH)
    d.text((164, 500), 'Kulik reaches', font=font(XB, 64), fill=WH)
    d.text((164, 580), 'the blast zone', font=font(XB, 64), fill=WH)
    if p > 0.35: d.text((164, 720), 'Evenki hunters as guides', font=font(SEMI, 44), fill=CY)
    d.text((160, 960), 'Photo c.1930 & sketch map, published in "Vokrug Sveta", 1931', font=font(MED, 26), fill=(190, 200, 215))
    return fr.convert('RGB')

def crater_card(p, tl, dur):
    fr = dimbg('tg10_h02.jpg', p, 'out', 0.12, 0.55)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.2)
    d.text((W // 2, 330), 'HE EXPECTED A CRATER.', font=font(MONO, 50), fill=CY + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 520), 'THERE WAS NONE.', font(BLACK, 150), k, tl)
    return fr.convert('RGB')

def stump_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 160), "KULIK'S \"CRATERS\"", font=font(MONO, 44), fill=CY, anchor='mm')
    d.text((W // 2, 330), 'Drained: "Suslov\'s crater"', font=font(BLACK, 96), fill=WH, anchor='mm')
    d.text((W // 2, 440), 'a swampy pit ~32 m across', font=font(SEMI, 44), fill=(200, 210, 225), anchor='mm')
    if p > 0.4:
        k = fade(p, 0.4, 0.1)
        d.text((W // 2, 640), 'AT THE BOTTOM:', font=font(XB, 56), fill=WH + (int(255 * k),), anchor='mm')
        d.text((W // 2, 770), 'AN OLD TREE STUMP', font=font(BLACK, 120), fill=MG + (int(255 * k),), anchor='mm')
    src_line(d, 'Source: Wikipedia "Tunguska event" (Kulik expeditions, 1927–1930s)')
    return fr.convert('RGB')

def butterfly_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 120), 'THE FLATTENED FOREST · MAPPED IN THE 1960s', font=font(MONO, 40), fill=CY, anchor='mm')
    cx, cy = W // 2, 580
    e = ease(min(1, p / 0.6))
    pts = []
    for i in range(361):
        th = math.radians(i)
        r = (0.55 + 0.45 * abs(math.sin(th)) ** 0.8) * (1 - 0.18 * math.cos(2 * th) ** 2)
        pts.append((cx + 380 * r * math.cos(th) * e, cy - 300 * r * math.sin(th) * e * (1.0 if math.sin(th) > 0 else 0.85)))
    if e > 0.02:
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
        ld.polygon(pts, fill=(255, 120, 40, 110), outline=AMB + (255,))
        fr.alpha_composite(L); d = ImageDraw.Draw(fr)
        for a in range(0, 360, 15):
            th = math.radians(a); r1 = 70; r2 = 70 + 230 * e
            d.line((cx + r1 * math.cos(th), cy - r1 * math.sin(th), cx + r2 * math.cos(th), cy - r2 * math.sin(th) * 0.9), fill=(255, 210, 160), width=3)
        d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=MG, outline=WH, width=3)
    if p > 0.55:
        k = fade(p, 0.55, 0.1)
        d.line((cx - 380, 940, cx + 380, 940), fill=WH + (int(255 * k),), width=4)
        d.text((cx, 975), '~70 km wingtip to wingtip', font=font(XB, 40), fill=WH + (int(255 * k),), anchor='mm')
        d.text((1500, 420), '≈ 2,150 km²', font=font(BLACK, 80), fill=AMB + (int(255 * k),), anchor='mm')
        d.text((1500, 500), 'of forest', font=font(SEMI, 44), fill=WH + (int(255 * k),), anchor='mm')
        d.text((380, 420), '"butterfly"', font=font(BLACK, 70), fill=WH + (int(255 * k),), anchor='mm')
        d.text((380, 500), 'trees fall away from center', font=font(SEMI, 36), fill=WH + (int(255 * k),), anchor='mm')
    d.text((W // 2, 1040), 'Schematic shape, not an exact map · Source: Wikipedia "Tunguska event"', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def theories_card(p, tl, dur):
    fr = dimbg('tg10_k01.jpg', p, 'in', 0.08, 0.7)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 130), 'NO CRATER, NO ROCK → EVERY THEORY IMAGINABLE', font=font(MONO, 40), fill=CY, anchor='mm')
    rows = [('A COMET', 'ice and dust, vaporized in the air', 'HYPOTHESIS', (130, 255, 190), 0.04),
            ('GAS FROM THE GROUND', 'methane eruption', 'FRINGE', (255, 210, 120), 0.2),
            ('AN ALIEN SPACESHIP', 'from a 1946 science-fiction story', 'LEGEND', MG, 0.42),
            ('A TESLA "DEATH RAY"', 'from a 1994 fictionalized biography', 'LEGEND', MG, 0.64)]
    for i, (a, b, tag, col, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 250 + i * 190
        d.text((170, y), a, font=font(BLACK, 76), fill=WH + (int(255 * k),))
        d.text((174, y + 92), b, font=font(SEMI, 38), fill=(205, 215, 230, int(255 * k)))
        tw = d.textlength(tag, font=font(BLACK, 46))
        d.rounded_rectangle((1750 - tw - 40, y + 14, 1750, y + 84), 12, outline=col + (int(255 * k),), width=5)
        d.text((1750 - 20, y + 49), tag, font=font(BLACK, 46), fill=col + (int(255 * k),), anchor='rm')
    return fr.convert('RGB')

def loop2_card(p, tl, dur):
    fr = dimbg('tg10_s2_cheko.jpg', p, 'in', 0.1, 0.5)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    d.rounded_rectangle((360, 310, 1560, 770), 30, fill=(4, 8, 16, 190), outline=CY + (255,), width=4)
    d.text((W // 2, 380), 'OPEN FILE #2', font=font(MONO, 44), fill=CY + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 510), 'A LAKE 8 KM', font(BLACK, 100), k, tl)
    rgb_split_text(d, (W // 2, 630), 'FROM THE CENTER', font(BLACK, 100), k, tl)
    d.text((W // 2, 720), 'is a piece of it at the bottom?', font=font(XB, 44), fill=AMB + (int(255 * k),), anchor='mm')
    return fr.convert('RGB')

def tree(d, x, gy, ang, h=150, stripped=False, col=(120, 200, 140)):
    # ang: 0 = upright, +/-90 = flat (degrees, positive = falls right)
    a = math.radians(ang)
    tx, ty = x + h * math.sin(a), gy - h * math.cos(a)
    d.line((x, gy, tx, ty), fill=(150, 110, 80), width=8)
    if not stripped:
        for j in range(3):
            f = 0.45 + 0.2 * j; bx, by = x + h * f * math.sin(a), gy - h * f * math.cos(a)
            w = 46 - 12 * j
            nx, ny = math.cos(a), math.sin(a)
            d.line((bx - w * nx, by - w * ny, bx + w * nx, by + w * ny), fill=col, width=14)

def airburst_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 110), 'WHY THE TREES IN THE MIDDLE STOOD', font=font(MONO, 42), fill=CY, anchor='mm')
    gy = 900; bx, by = W // 2, 300
    d.rectangle((0, gy, W, H), fill=(40, 30, 22)); d.line((0, gy, W, gy), fill=(120, 95, 70), width=4)
    tb = 0.18  # blast time
    if p >= tb:
        q = (p - tb) / (1 - tb)
        R = 1500 * min(1, q / 0.55)
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
        fl = max(0, 1 - q / 0.25)
        ld.ellipse((bx - 90, by - 90, bx + 90, by + 90), fill=(255, 220, 140, int(255 * max(0.35, fl))))
        for rr in (R, R * 0.8):
            if rr > 10: ld.ellipse((bx - rr, by - rr, bx + rr, by + rr), outline=(255, 170, 80, int(200 * max(0.2, 1 - q))), width=6)
        fr.alpha_composite(L.filter(ImageFilter.GaussianBlur(2))); d = ImageDraw.Draw(fr)
        d.text((bx + 120, by), 'AIRBURST · kilometers up', font=font(XB, 44), fill=AMB, anchor='lm')
    else:
        f = p / tb
        sx, sy = -100 + (bx + 100) * f, -60 + (by + 60) * f
        d.line((sx - 160, sy - 90, sx, sy), fill=(255, 200, 120), width=8)
        d.ellipse((sx - 16, sy - 16, sx + 16, sy + 16), fill=WH)
    R = 1500 * min(1, max(0, (p - tb) / (1 - tb) / 0.55))
    for x in range(120, W - 100, 96):
        dx = x - bx; dist = math.hypot(dx, gy - by)
        hit = R >= dist
        if not hit: tree(d, x, gy, 0)
        elif abs(dx) < 170: tree(d, x, gy, 0, stripped=True)
        else:
            fall = min(1, (R - dist) / 160)
            tree(d, x, gy, (1 if dx > 0 else -1) * 85 * ease(fall), stripped=True)
    if p > 0.6:
        k = fade(p, 0.6, 0.1)
        d.text((bx, 980), 'directly below: stripped, but STANDING', font=font(XB, 40), fill=WH + (int(255 * k),), anchor='mm')
        d.text((300, 980), '← knocked flat', font=font(XB, 40), fill=AMB + (int(255 * k),), anchor='mm')
        d.text((W - 300, 980), 'knocked flat →', font=font(XB, 40), fill=AMB + (int(255 * k),), anchor='mm')
    d.text((W // 2, 1045), 'Simplified illustration (not to scale) · GLITCHVERSE', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def matches_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 130), 'SOVIET LAB TEST · 1960s', font=font(MONO, 44), fill=CY, anchor='mm')
    d.text((W // 2, 260), 'A model forest of matches', font=font(BLACK, 92), fill=WH, anchor='mm')
    d.text((W // 2, 360), '+ small explosive charges', font=font(XB, 56), fill=(200, 210, 225), anchor='mm')
    if p > 0.3:
        k = fade(p, 0.3)
        d.text((W // 2, 520), 'RESULT: THE SAME BUTTERFLY', font=font(BLACK, 80), fill=AMB + (int(255 * k),), anchor='mm')
    if p > 0.5:
        k = fade(p, 0.5)
        cx, cy = W // 2 - 300, 790
        d.line((cx - 200, cy + 80, cx + 200, cy + 80), fill=(120, 95, 70, int(255 * k)), width=6)
        d.line((cx - 180, cy - 80, cx + 30, cy + 40), fill=WH + (int(255 * k),), width=8)
        d.arc((cx - 60, cy + 20, cx + 60, cy + 140), 180, 210, fill=AMB + (int(255 * k),), width=5)
        d.text((cx + 60, cy + 40), '~30°', font=font(XB, 44), fill=AMB + (int(255 * k),), anchor='lm')
        d.text((W // 2 + 120, 760), 'came in at ~30°', font=font(XB, 52), fill=WH + (int(255 * k),), anchor='lm')
        d.text((W // 2 + 120, 830), 'exploded in midair', font=font(XB, 52), fill=WH + (int(255 * k),), anchor='lm')
    src_line(d, 'Source: Wikipedia "Tunguska event" (blast-pattern experiments, mid-1960s)')
    return fr.convert('RGB')

def numbers_card(p, tl, dur):
    fr = dimbg('tg10_a02.jpg', p, 'in', 0.06, 0.6)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 140), 'WHAT EXPLODED? · MOST MODELS', font=font(MONO, 44), fill=CY, anchor='mm')
    rows = [('~50–80 m', 'a space rock (NASA: 50–100 m)', 0.05), ('~5–14 km UP', 'where it blew apart', 0.3), ('~10–15 MEGATONS', 'usual estimate (range: 3–30 Mt)', 0.55)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 260 + i * 220
        d.text((200, y), a, font=font(BLACK, 96), fill=WH + (int(255 * k),))
        d.text((204, y + 118), b, font=font(SEMI, 42), fill=AMB + (int(255 * k),))
    src_line(d, 'Sources: Wikipedia "Tunguska event"; NASA Earth Observatory (2024)')
    return fr.convert('RGB')

def size_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 130), 'CHELYABINSK 2013  vs  TUNGUSKA 1908', font=font(MONO, 44), fill=CY, anchor='mm')
    e = ease(min(1, p / 0.5)); base = 860
    r1 = 50 * e; r2 = 165 * e
    d.ellipse((520 - r1, base - 2 * r1, 520 + r1, base), fill=(170, 160, 150))
    d.ellipse((1300 - r2, base - 2 * r2, 1300 + r2, base), fill=(150, 120, 95))
    d.text((520, 300), '~20 m', font=font(BLACK, 80), fill=WH, anchor='mm')
    d.text((520, 380), '~500 kilotons', font=font(XB, 46), fill=CY, anchor='mm')
    d.text((1300, 300), '~50–80 m', font=font(BLACK, 80), fill=WH, anchor='mm')
    d.text((1300, 380), '~10–15 megatons', font=font(XB, 46), fill=AMB, anchor='mm')
    if p > 0.6: d.text((W // 2, 960), 'roughly 20–30× the energy', font=font(BLACK, 64), fill=MG, anchor='mm')
    d.text((W // 2, 1040), 'Sizes approximate, schematic · Source: Wikipedia', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def cheko_map(p, tl, dur):
    lo0, lo1, la0, la1 = 101.70, 102.00, 60.88, 61.00
    e = ease(p)
    wdeg = lerp(0.28, 0.22, e); cx = lerp(101.85, 101.862, e); cy = lerp(60.945, 60.952, e)
    hdeg = wdeg * math.cos(math.radians(cy)) * H / W
    x0, x1, y0, y1 = cx - wdeg / 2, cx + wdeg / 2, cy - hdeg / 2, cy + hdeg / 2
    im = img('tg10_s2_cheko.jpg'); iw, ih = im.size
    ppx = iw / (lo1 - lo0); ppy = ih / (la1 - la0)
    fr = im.transform((W, H), Image.EXTENT, ((x0 - lo0) * ppx, (la1 - y1) * ppy, (x1 - lo0) * ppx, (la1 - y0) * ppy), Image.BICUBIC).convert('RGBA')
    fr = Image.blend(fr, Image.new('RGBA', (W, H), (0, 0, 0, 255)), 0.1)
    d = ImageDraw.Draw(fr)
    def sxy(lo, la): return ((lo - x0) / wdeg * W, (y1 - la) / hdeg * H)
    lx, ly = sxy(*CHEKO); ex, ey = sxy(*EPI)
    k = fade(p, 0.08, 0.1)
    if k > 0:
        r = 52 + 6 * math.sin(tl * 5)
        d.ellipse((lx - r, ly - r, lx + r, ly + r), outline=CY + (int(255 * k),), width=5)
        d.text((lx + 80, ly - 14), 'LAKE CHEKO', font=font(BLACK, 58), fill=WH + (int(255 * k),), anchor='lm')
        d.text((lx + 82, ly + 38), '~500 m long · ~50 m deep', font=font(MONO, 28), fill=CY + (int(255 * k),), anchor='lm')
    k2 = fade(p, 0.35, 0.1)
    if k2 > 0:
        ang = math.atan2(ey - ly, ex - lx); ux, uy = math.cos(ang), math.sin(ang)
        sx_, sy_ = lx + ux * 70, ly + uy * 70; tx, ty = lx + ux * 420, ly + uy * 420
        for i in range(0, 12, 2):
            a = i / 12; b = (i + 1) / 12
            d.line((sx_ + (tx - sx_) * a, sy_ + (ty - sy_) * a, sx_ + (tx - sx_) * b, sy_ + (ty - sy_) * b), fill=AMB + (int(255 * k2),), width=6)
        d.polygon([(tx + ux * 30, ty + uy * 30), (tx - uy * 18, ty + ux * 18), (tx + uy * 18, ty - ux * 18)], fill=AMB + (int(255 * k2),))
        d.text((tx + 50, ty), 'to the epicenter: ~8 km', font=font(BLACK, 50), fill=WH + (int(255 * k2),), anchor='lm')
        d.text((tx + 52, ty + 52), '(off-screen, south-southeast)', font=font(MONO, 26), fill=AMB + (int(255 * k2),), anchor='lm')
    return fr.convert('RGB')

def cheko_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 120), '2007 · UNIVERSITY OF BOLOGNA', font=font(MONO, 44), fill=CY, anchor='mm')
    d.text((W // 2, 220), 'An impact crater from a fragment?', font=font(BLACK, 76), fill=WH, anchor='mm')
    x0, x1, wl = 360, 1560, 420
    e = ease(min(1, p / 0.4))
    pts = [(x0 - 150, wl)] + [(x0 + (x1 - x0) * i / 60, wl + 280 * e * max(0, 1 - abs(i / 30 - 1)) ** 1.3) for i in range(61)] + [(x1 + 150, wl)]
    d.polygon(pts + [(x1 + 150, 800), (x0 - 150, 800)], fill=(70, 55, 40))
    d.polygon([(x0, wl)] + pts[1:-1] + [(x1, wl)], fill=(40, 90, 150))
    d.line((x0 - 150, wl, x1 + 150, wl), fill=(120, 190, 255), width=4)
    d.text((W // 2, wl + 150 * e), 'cone-shaped floor', font=font(XB, 44), fill=WH, anchor='mm')
    rows = [('points toward the blast', 0.45), ('magnetic anomaly under the deepest point', 0.62)]
    for i, (t, t0) in enumerate(rows):
        k = fade(p, t0)
        if k > 0: d.text((W // 2, 870 + i * 70), '+ ' + t, font=font(XB, 48), fill=AMB + (int(255 * k),), anchor='mm')
    d.text((W // 2, 1040), 'Schematic cross-section, not to scale · Source: Gasperini et al. 2007 (via Wikipedia)', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def debate_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 120), 'OTHER SCIENTISTS PUSHED BACK', font=font(MONO, 44), fill=CY, anchor='mm')
    rows = [('2008', 'trees around the lake older than 100 years', 0.05), ('2017', 'sediment layers: lake at least ~280 years old', 0.3),
            ('2023', 'two more cone-shaped lakes, 50–60 km away', 0.55)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 250 + i * 190
        d.text((180, y), a, font=font(BLACK, 96), fill=MG + (int(255 * k),))
        d.text((480, y + 30), b, font=font(XB, 50), fill=WH + (int(255 * k),))
    if p > 0.78: d.text((W // 2, 900), 'FOR NOW: THE LAKE LOOKS OLDER THAN THE BLAST', font=font(BLACK, 60), fill=AMB, anchor='mm')
    src_line(d, 'Sources: Collins et al. 2008 (Terra Nova); Rogozin et al. 2017, 2023 (via Live Science, 29 May 2023)')
    return fr.convert('RGB')

def twist_card(p, tl, dur):
    fr = dimbg('tg10_a01.jpg', p, 'in', 0.12, 0.55)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.2)
    d.text((W // 2, 250), 'THE TWIST · 2020', font=font(MONO, 50), fill=MG + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 440), 'WHAT IF NOTHING', font(BLACK, 130), k, tl)
    rgb_split_text(d, (W // 2, 590), 'FELL AT ALL?', font(BLACK, 130), k, tl)
    if p > 0.4: d.text((W // 2, 760), 'Khrennikov et al., Monthly Notices of the Royal Astronomical Society', font=font(SEMI, 40), fill=CY, anchor='mm')
    return fr.convert('RGB')

def graze_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 110), 'THE "GRAZING" HYPOTHESIS (2020)', font=font(MONO, 42), fill=CY, anchor='mm')
    ECX, ECY, ER = W // 2, 3300, 2500
    d.ellipse((ECX - ER - 160, ECY - ER - 160, ECX + ER + 160, ECY + ER + 160), fill=(20, 40, 70))
    d.ellipse((ECX - ER, ECY - ER, ECX + ER, ECY + ER), fill=(30, 70, 45))
    d.text((300, 860), 'ATMOSPHERE (exaggerated)', font=font(MONO, 26), fill=(140, 180, 230), anchor='mm')
    # path: hyperbola-like curve dipping close to the surface at x=W/2
    def path(s):
        x = -100 + (W + 200) * s
        surf = ECY - math.sqrt(max(0, ER ** 2 - (x - ECX) ** 2))
        dip = 70 + 0.0009 * (x - ECX) ** 2
        return x, surf - dip
    e = min(1, p / 0.75)
    trail = [path(i / 200) for i in range(int(200 * e) + 1)]
    if len(trail) > 1: d.line(trail, fill=(255, 190, 110), width=6)
    x, y = path(e)
    d.ellipse((x - 18, y - 18, x + 18, y + 18), fill=(200, 200, 210), outline=WH, width=3)
    mx, my = path(0.5)
    if e > 0.5:
        k = min(1, (e - 0.5) / 0.1)
        surf = ECY - ER
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
        ld.polygon([(mx, my), (mx - 260, surf + 20), (mx + 260, surf + 20)], fill=(255, 140, 60, int(120 * k)))
        fr.alpha_composite(L); d = ImageDraw.Draw(fr)
        d.text((mx, surf + 70), 'shock wave flattens the forest', font=font(XB, 40), fill=AMB + (int(255 * k),), anchor='mm')
        d.text((mx + 40, my - 40), 'lowest point ~10–15 km', font=font(XB, 38), fill=WH + (int(255 * k),), anchor='lm')
    if e >= 1:
        d.text((W - 160, 360), '→ back into orbit around the Sun', font=font(XB, 46), fill=WH, anchor='rm')
    d.text((160, 230), 'iron asteroid, up to ~200 m (model)', font=font(SEMI, 40), fill=(210, 220, 235))
    d.rounded_rectangle((1440, 200, 1780, 260), 12, outline=MG, width=4)
    d.text((1610, 230), 'MINORITY VIEW', font=font(BLACK, 34), fill=MG, anchor='mm')
    d.text((W // 2, 1045), 'Schematic, not to scale · Khrennikov et al., MNRAS (2020)', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def asteroid_day_card(p, tl, dur):
    fr = dimbg('tg10_k01.jpg', p, 'in', 0.08, 0.6)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 320), '30 JUNE', font=font(BLACK, 170), fill=WH, anchor='mm')
    d.text((W // 2, 470), 'INTERNATIONAL ASTEROID DAY', font=font(BLACK, 80), fill=AMB, anchor='mm')
    d.text((W // 2, 560), 'proclaimed by the United Nations in 2016', font=font(SEMI, 44), fill=CY, anchor='mm')
    if p > 0.45: d.text((W // 2, 740), 'Tunguska-sized events: rare — but not impossible', font=font(XB, 54), fill=WH, anchor='mm')
    return fr.convert('RGB')

def question_card(p, tl, dur):
    fr = dimbg('tg10_h01.jpg', p, 'in', 0.14, 0.62)
    d = ImageDraw.Draw(fr)
    if p > 0.03: d.text((W // 2, 260), 'WHAT DO YOU BELIEVE?', font=font(MONO, 50), fill=CY, anchor='mm')
    if p > 0.12: d.text((W // 2, 420), 'A ROCK THAT SHATTERED', font=font(BLACK, 100), fill=WH, anchor='mm')
    if p > 0.25: d.text((W // 2, 540), 'or', font=font(SEMI, 50), fill=CY, anchor='mm')
    if p > 0.32: d.text((W // 2, 660), 'A VISITOR THAT LEFT?', font=font(BLACK, 100), fill=AMB, anchor='mm')
    if p > 0.5: d.text((W // 2, 850), '↓  Tell me in the comments', font=font(XB, 54), fill=WH, anchor='mm')
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

def scale_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA')
    framed(fr, 'tg10_x03.jpg', (1060, 90, 1760, 990), angle=-1.5)
    d = ImageDraw.Draw(fr)
    d.text((160, 360), 'FOR SCALE', font=font(MONO, 46), fill=CY)
    d.text((160, 430), 'The blast zone', font=font(BLACK, 92), fill=WH)
    d.text((160, 540), 'over Washington, D.C.', font=font(XB, 60), fill=WH)
    if p > 0.3: d.text((160, 680), 'bigger than the whole city', font=font(XB, 52), fill=AMB)
    d.text((1410, 1050), 'Illustration: Lunar and Planetary Institute · CC BY 2.0', font=font(MED, 22), fill=(170, 180, 200), anchor='mm')
    return fr.convert('RGB')

N01 = 'tg10_n01.jpg'
SEG = {
 's01': [dict(card(hook_card, glitch=False, credit='tg10_h01.jpg'), dur=3.0), dict(card(title_card, credit='tg10_p02.jpg'), dur=3.0),
         img_shot('tg10_h01.jpg', 'right', ('2,150 KM² OF FOREST FLATTENED', 'Kulik expedition photo, 1929'), amt=0.2, focus=(0.5, 0.45)),
         img_shot(N01, 'in', ('THE BLAST ZONE TODAY', 'Landsat 8, 2024 · no crater anywhere'), amt=0.15)],
 's02': [img_shot('tg10_p02.jpg', 'right', ('THE TUNGUSKA EVENT', '30 June 1908 · Central Siberia'), amt=0.25, focus=(0.45, 0.35)),
         card(whathit_card, w=2.6, credit='tg10_a01.jpg'), img_shot('tg10_c02.jpg', 'in', ('A FIREBALL FROM SPACE?', 'photo: Chelyabinsk fireball trail, 2013'), amt=0.1)],
 's03': [card(map_in, glitch=False, w=2.6, credit='tg10_s2_close.jpg', grade=True),
         img_shot('tg10_p01.jpg', 'right', ('PODKAMENNAYA TUNGUSKA', 'Evenkiysky District, Krasnoyarsk Krai'), amt=0.3, focus=(0.5, 0.2))],
 's04': [img_shot('tg10_c01.jpg', 'in', ('7:14 AM · A FIREBALL', '"brighter than the Sun" · photo: Chelyabinsk 2013'), amt=0.1),
         img_shot('tg10_p03.jpg', 'right', ('VANAVARA', 'trading post ~60 km from the blast · photo 2022')),
         card(quote_card, w=3.2, credit='tg10_p03.jpg'), img_shot('tg10_p08.jpg', 'in', ('THROWN OFF HIS PORCH', 'several meters, by the blast'))],
 's05': [card(records_card, w=2.2), img_shot('tg10_b01.jpg', 'in', ('BRIGHT NIGHTS OVER EUROPE', 'today\'s noctilucent clouds, for illustration')),
         img_shot('tg10_b02.jpg', 'right', ('"READ A NEWSPAPER AT MIDNIGHT"', 'reports across Europe, 30 June – early July 1908'))],
 's06': [card(news_card, w=2.0, credit='tg10_h05.jpg'), card(nineteen_card, w=1.6)],
 's07': [card(loop1_card, w=1.6, credit='tg10_h01.jpg'), img_shot('tg10_h01.jpg', 'in', ('STRIPPED. SCORCHED. UPRIGHT.', 'like telegraph poles'), amt=0.3, focus=(0.62, 0.3)),
         img_shot('tg10_h02.jpg', 'left', ('EVERYTHING AROUND: FLAT', None), amt=0.15)],
 's08': [card(kulik_card, w=2.0), img_shot('tg10_m01.jpg', 'in', ('HE EXPECTED IRON', 'iron meteorite shown: Sikhote-Alin, 1947 fall'))],
 's09': [card(scheme_card, w=1.6, credit='tg10_h03.jpg'), img_shot('tg10_h01.jpg', 'left', ('TREES POINTING AWAY', 'from one central area'), amt=0.2), card(crater_card, w=1.3, credit='tg10_h02.jpg')],
 's10': [img_shot('tg10_h02.jpg', 'in', ('SWAMPY PITS', 'Kulik thought they were meteorite holes'), amt=0.2), card(stump_card, w=1.8),
         card(butterfly_card, w=2.4), card(scale_card, w=1.4)],
 's11': [card(theories_card, w=3.4, credit='tg10_k01.jpg'), img_shot('tg10_k01.jpg', 'in', ('THEORY: A COMET', 'comet Hale-Bopp, 1997, for illustration'), amt=0.2), img_shot('tg10_p11.jpg', 'right', ('LEGENDS GO TO THE LEGEND FILE', 'Evenkia today'))],
 's12': [card(loop2_card, w=1.8, credit='tg10_s2_cheko.jpg'), img_shot('tg10_p08.jpg', 'left', ('A SMALL, DEEP LAKE', 'taiga lake shore, for illustration'))],
 's13': [card(airburst_card, w=3.2), img_shot('tg10_h01.jpg', 'in', ('DIRECTLY BELOW: STANDING', 'farther away: flattened'), amt=0.25, focus=(0.6, 0.35))],
 's14': [card(matches_card, w=2.4), img_shot('tg10_p06.jpg', 'in', ('AIRBURST', 'an explosion in midair'))],
 's15': [card(numbers_card, w=2.6, credit='tg10_a02.jpg'), img_shot('tg10_a03.jpg', 'in', ('A SPACE ROCK', 'asteroid Eros shown, for illustration'), amt=0.15),
         img_shot(N01, 'out', ('NO GROUND IMPACT', 'so no crater'), amt=0.2)],
 's16': [img_shot('tg10_c04.jpg', 'in', ('CHELYABINSK · 2013', '~20 m rock · ~500 kilotons')), img_shot('tg10_c03.jpg', 'right', ('1,200+ INJURED', 'mostly by broken glass'), focus=(0.62, 0.4), amt=0.25),
         card(size_card, w=1.8)],
 's17': [card(cheko_map, glitch=False, w=2.2, credit='tg10_s2_cheko.jpg', grade=True), card(cheko_card, w=2.4)],
 's18': [card(debate_card, w=3.0), img_shot(N01, 'in', ('LAKE CHEKO (TOP LEFT)', 'Landsat 8, 2024'), amt=0.35, focus=(0.3, 0.2))],
 's19': [card(twist_card, w=1.5, credit='tg10_a01.jpg'), card(graze_card, w=3.4), img_shot('tg10_m02.jpg', 'in', ('AN IRON ASTEROID?', 'iron meteorite shown: Sikhote-Alin'), amt=0.15)],
 's20': [img_shot('tg10_a01.jpg', 'out', ('IT NEVER STAYED?', 'if the 2020 study is right'), amt=0.2), img_shot('tg10_h01.jpg', 'right', ('MOST SCIENTISTS: AIRBURST', 'the debate is still open'), amt=0.15),
         card(map_out, glitch=False, w=1.4, credit='tg10_s2_close.jpg', grade=True)],
 's21': [card(asteroid_day_card, w=1.8, credit='tg10_k01.jpg'), card(question_card, w=2.4, credit='tg10_h01.jpg', grade=True),
         img_shot('tg10_p02.jpg', 'out', ('SUBSCRIBE', 'for the next entry of my Glitch Diary'), amt=0.2, focus=(0.45, 0.35))],
 'end': [card(endcard, glitch=False)],
}
CHAPTERS = {'s03': (1, 'The morning the sky split'), 's08': (2, 'The search for a crater'), 's11': (3, 'Comets, gas & legends'),
            's13': (4, 'Why the trees stood'), 's17': (5, 'The lake'), 's19': (6, 'The twist'), 's21': (7, 'Your turn')}
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
