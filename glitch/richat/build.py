"""GLITCHVERSE — Richat Structure flagship (Mia's Glitch Diary #5). 1920x1080, 30 fps.
Usage: python3 build.py [--part i n] [--still t1,t2] [--preview a b]"""
import sys
sys.path.insert(0, '/home/claude/gv')
from base import *

ENTRY = 5
SAND = (255, 196, 120)

# ---------- MAP ----------
SRC = [('gvr_s2_close.jpg', -12.4, -10.4, 20.5, 22.0), ('gvr_s2_mid.jpg', -16, -6, 16.5, 24),
       ('gvr_s2_wide.jpg', -22, 6, 10, 31)]
RICH = (-11.40, 21.12)
LABELS = [('ATLANTIC OCEAN', -19.0, 21.5, 'sea'), ('MAURITANIA', -9.6, 19.0, 'cty'), ('MALI', -3.5, 17.8, 'cty'),
          ('ALGERIA', -2.5, 27.5, 'cty'), ('WESTERN SAHARA', -13.4, 24.6, 'cty'), ('SENEGAL', -14.6, 14.6, 'cty'),
          ('ADRAR PLATEAU', -12.55, 21.25, 'des'), ('Nouakchott', -15.98, 18.09, 'city'), ('Ouadane', -11.62, 20.93, 'city'),
          ('Chinguetti', -12.36, 20.46, 'city'), ('SAHARA', -7.0, 22.6, 'des')]

def map_frame(cx, cy, wdeg, t, pin_alpha=1.0):
    hdeg = wdeg * H / W
    x0, x1, y0, y1 = cx - wdeg / 2, cx + wdeg / 2, cy - hdeg / 2, cy + hdeg / 2
    src = SRC[-1]
    for s in SRC:
        if s[1] <= x0 and x1 <= s[2] and s[3] <= y0 and y1 <= s[4]: src = s; break
    name, lo0, lo1, la0, la1 = src
    im = img(name); iw, ih = im.size
    ppx = iw / (lo1 - lo0); ppy = ih / (la1 - la0)
    box = ((x0 - lo0) * ppx, (la1 - y1) * ppy, (x1 - lo0) * ppx, (la1 - y0) * ppy)
    fr = im.transform((W, H), Image.EXTENT, box, Image.BICUBIC).convert('RGBA')
    d = ImageDraw.Draw(fr)
    def sxy(lo, la): return ((lo - x0) / wdeg * W, (y1 - la) / hdeg * H)
    for txt, lo, la, kind in LABELS:
        x, y = sxy(lo, la)
        if not (-200 < x < W + 200 and -100 < y < H + 100): continue
        if kind in ('cty', 'sea') and wdeg < 7: continue
        if kind == 'des' and txt == 'SAHARA' and wdeg < 9: continue
        if kind == 'des' and txt != 'SAHARA' and not (1.0 < wdeg < 6): continue
        if kind == 'city' and wdeg > 14: continue
        if kind == 'city' and txt != 'Ouadane' and wdeg < 1.6: continue
        if txt == 'Ouadane' and wdeg > 3: continue
        sz = {'cty': 40, 'sea': 34, 'des': 36, 'city': 30}[kind]
        col = {'cty': (255, 255, 255, 230), 'sea': (170, 225, 255, 230), 'des': (255, 230, 170, 240), 'city': (255, 255, 255, 235)}[kind]
        f = font(XB if kind != 'city' else BOLD, sz)
        if kind == 'city':
            d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(255, 255, 255, 230), outline=(0, 0, 0, 160), width=2)
            d.text((x + 18, y + 2), txt, font=f, fill=(0, 0, 0, 150), anchor='lm')
            d.text((x + 16, y), txt, font=f, fill=col, anchor='lm')
        else:
            d.text((x + 3, y + 3), txt, font=f, fill=(0, 0, 0, 150), anchor='mm')
            d.text((x, y), txt, font=f, fill=col, anchor='mm')
    x, y = sxy(*RICH)
    if pin_alpha > 0:
        a = int(255 * pin_alpha)
        r = 18 + 10 * (0.5 + 0.5 * math.sin(t * 6))
        d.ellipse((x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2), outline=CY + (int(a * 0.6),), width=4)
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=MG + (a,), outline=(255, 255, 255, a), width=4)
        f = font(BLACK, 46)
        d.text((x + 52, y - 6), 'RICHAT STRUCTURE', font=f, fill=(0, 0, 0, int(a * 0.6)), anchor='lm')
        d.text((x + 48, y - 10), 'RICHAT STRUCTURE', font=f, fill=(255, 255, 255, a), anchor='lm')
        d.text((x + 50, y + 34), '21.12°N  11.40°W', font=font(MONO, 26), fill=CY + (a,), anchor='lm')
    return fr.convert('RGB')

def lerp(a, b, e): return a + (b - a) * e
def log_lerp(a, b, e): return math.exp(math.log(a) + (math.log(b) - math.log(a)) * e)

def map_in(p, tl, dur):
    e = ease(min(1, p / 0.9))
    cx = lerp(-9.0, RICH[0], e); cy = lerp(20.5, RICH[1], e); w = log_lerp(26.0, 1.15, e)
    return map_frame(cx, cy, w, tl, pin_alpha=min(1, max(0, (p - 0.3) / 0.15)))

def map_out(p, tl, dur):
    e = ease(p)
    cx = lerp(RICH[0], -9.0, e); cy = lerp(RICH[1], 20.5, e); w = log_lerp(1.15, 26.0, e)
    return map_frame(cx, cy, w, tl, pin_alpha=1.0)

def lower(text, sub=None):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    f1 = font(XB, 58); f2 = font(SEMI, 34)
    w1 = d.textlength(text, font=f1); w2 = d.textlength(sub, font=f2) if sub else 0
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    gd.rounded_rectangle((70, 780, 160 + max(w1, w2) + 40, 950 if sub else 900), 18, fill=(0, 0, 0, 150))
    L.alpha_composite(g.filter(ImageFilter.GaussianBlur(14))); d = ImageDraw.Draw(L)
    shadow_text(d, (120, 860), text, f1, WH, 'ls', 3)
    if sub: shadow_text(d, (122, 912), sub, f2, CY, 'ls', 2)
    d.rectangle((96, 800, 104, 920 if sub else 870), fill=SAND + (255,))
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
TOTAL = TIM['s23']['end'] + END_EXTRA

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
def hook_card(p, tl, dur):
    fr = kenburns('gvr_r02.jpg', p, 'in', 0.22, (0.5, 0.48)).convert('RGBA')
    sh_ = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh_)
    sd.rounded_rectangle((250, 330, 1670, 760), 40, fill=(0, 0, 0, 120))
    fr.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(40)))
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    k = min(1, tl / 0.2)
    rgb_split_text(d, (W // 2, 480), 'THE SAHARA', font(BLACK, 140), k, tl)
    rgb_split_text(d, (W // 2, 630), 'HAS AN EYE.', font(BLACK, 140), k, tl)
    d.text((W // 2, 360), '40 KM WIDE · VISIBLE FROM SPACE', font=font(MONO, 38), fill=SAND + (int(255 * k),), anchor='mm')
    if tl > dur - 0.25: L.putalpha(L.split()[3].point(lambda v: int(v * max(0, (dur - tl) / 0.25))))
    fr.alpha_composite(L)
    return fr.convert('RGB')

def title_card(p, tl, dur):
    fr = dimbg('gvr_r04.jpg', p, 'right', 0.1, 0.5)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.25)
    rgb_split_text(d, (W // 2, 430), "MIA'S GLITCH DIARY", font(BLACK, 110), k, tl)
    d.text((W // 2, 545), f'ENTRY #{ENTRY}  ·  THE EYE OF THE SAHARA', font=font(MONO, 44), fill=CY + (int(255 * k),), anchor='mm')
    avatar_badge(fr, W // 2 - 280, 650, k)
    return fr.convert('RGB')

def theories_card(p, tl, dur):
    fr = dimbg('gvr_r10.jpg', p, 'in', 0.1, 0.62)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 170), 'WHAT IS IT?  ·  THE INTERNET SAYS…', font=font(MONO, 40), fill=CY, anchor='mm')
    items = [('A METEOR CRATER?', 0.08), ('AN OLD VOLCANO?', 0.3), ('THE RUINS OF ATLANTIS?', 0.52)]
    for i, (t, t0) in enumerate(items):
        k = fade(p, t0)
        if k <= 0: continue
        jit = random.Random(int(tl * 15) + i).randint(-6, 6) if p - t0 < 0.05 else 0
        d.text((W // 2 + jit, 370 + i * 170), t, font=font(BLACK, 104), fill=WH + (int(255 * k),), anchor='mm')
    if p > 0.75:
        d.text((W // 2, 930), 'The real answer is stranger.', font=font(XB, 56), fill=SAND, anchor='mm')
    return fr.convert('RGB')

def gemini_card(p, tl, dur):
    fr = dimbg('gvr_r29.jpg', p, 'in', 0.08, 0.6)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 300), 'JUNE 1965', font=font(BLACK, 150), fill=WH, anchor='mm')
    if p > 0.15: d.text((W // 2, 450), 'GEMINI IV', font=font(XB, 90), fill=CY, anchor='mm')
    if p > 0.3: d.text((W // 2, 570), 'Astronauts Ed White & James McDivitt photograph the "eye"', font=font(SEMI, 44), fill=WH, anchor='mm')
    if p > 0.5: d.text((W // 2, 700), 'Since then: a landmark for crews in orbit', font=font(XB, 54), fill=SAND, anchor='mm')
    src_line(d, 'Source: NASA Earth Observatory, "Eyeing the Richat Structure" (2026) · background: ISS photo, not Gemini IV')
    return fr.convert('RGB')

def monod_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 150), "1952 · THÉODORE MONOD'S EXPEDITION", font=font(MONO, 42), fill=CY, anchor='mm')
    d.text((W // 2, 230), 'four "crater-like" circles in the region', font=font(SEMI, 44), fill=WH, anchor='mm')
    rows = [('AOUELLOUL', 'impact structure', True, 0.12), ('TENOUMER', 'impact structure', True, 0.28),
            ('TEMIMICHAT-GHALLAMAN', 'impact structure', True, 0.44), ('RICHAT', '???', False, 0.62)]
    for i, (n, s, ok, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 360 + i * 150
        cx = 330
        d.ellipse((cx - 50, y - 50, cx + 50, y + 50), outline=(SAND if ok else MG) + (int(255 * k),), width=8)
        d.text((430, y - 10), n, font=font(BLACK, 66), fill=WH + (int(255 * k),), anchor='lm')
        d.text((1640, y - 10), ('✓ ' if ok else '') + s, font=font(XB, 48), fill=((130, 255, 190) if ok else MG) + (int(255 * k),), anchor='rm')
    src_line(d, 'Sources: Wikipedia "Richat Structure" (Monod 1952 expedition); NASA Earth Observatory')
    return fr.convert('RGB')

def coesite_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 160), 'METEORITE FINGERPRINT?', font=font(MONO, 44), fill=CY, anchor='mm')
    d.text((W // 2, 390), 'COESITE', font=font(BLACK, 180), fill=WH, anchor='mm')
    d.text((W // 2, 520), 'quartz formed only under enormous pressure', font=font(SEMI, 44), fill=(210, 220, 235), anchor='mm')
    if p > 0.45:
        k = min(1, (p - 0.45) / 0.1)
        d.line((W // 2 - 420, 395, W // 2 - 420 + 840 * k, 395), fill=MG, width=16)
    if p > 0.6:
        d.text((W // 2, 700), '1969: IT WAS BARITE', font=font(BLACK, 110), fill=MG, anchor='mm')
        d.text((W // 2, 810), 'an ordinary mineral, misidentified', font=font(XB, 50), fill=WH, anchor='mm')
    src_line(d, 'Source: Wikipedia "Richat Structure" (1969 re-analysis)')
    return fr.convert('RGB')

def loop1_card(p, tl, dur):
    fr = dimbg('gvr_r17.jpg', p, 'in', 0.14, 0.55, (0.47, 0.42))
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    d.rounded_rectangle((360, 300, 1560, 780), 30, fill=(4, 8, 16, 190), outline=MG + (255,), width=4)
    d.text((W // 2, 370), 'OPEN FILE #1', font=font(MONO, 44), fill=MG + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 500), 'REMEMBER THE', font(BLACK, 100), k, tl)
    rgb_split_text(d, (W // 2, 620), 'TWO DARK RINGS', font(BLACK, 100), k, tl)
    d.text((W // 2, 725), '2024: older than the eye they draw?', font=font(XB, 44), fill=SAND + (int(255 * k),), anchor='mm')
    return fr.convert('RGB')

def loop2_card(p, tl, dur):
    fr = dimbg('gvr_r13.jpg', p, 'in', 0.1, 0.55)
    d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    d.rounded_rectangle((360, 330, 1560, 750), 30, fill=(4, 8, 16, 190), outline=CY + (255,), width=4)
    d.text((W // 2, 400), 'OPEN FILE #2', font=font(MONO, 44), fill=CY + (int(255 * k),), anchor='mm')
    rgb_split_text(d, (W // 2, 540), 'WHO WAS HERE', font(BLACK, 100), k, tl)
    rgb_split_text(d, (W // 2, 660), 'FIRST?', font(BLACK, 100), k, tl)
    return fr.convert('RGB')

# --- geology diagram ---
LAYER_COLS = [(214, 168, 110), (170, 110, 70), (230, 200, 150), (150, 95, 60), (205, 150, 95), (120, 80, 55), (196, 140, 90), (100, 70, 50)]
def geo_diagram(stage, q, title, sub, gab=False, cut=0.0, dome=0.0, magma=0.0, topview=0.0):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 120), title, font=font(MONO, 40), fill=CY, anchor='mm')
    if sub: d.text((W // 2, 180), sub, font=font(XB, 46), fill=WH, anchor='mm')
    x0, x1 = 160, 1280 if topview > 0 else 1760
    cx = (x0 + x1) / 2; sig = (x1 - x0) * 0.2
    xs = np.linspace(x0, x1, 240)
    bump = np.exp(-((xs - cx) ** 2) / (2 * sig ** 2)) * 190 * dome
    base_top = 480; th = 62
    ycut = 1000 - (1000 - (base_top + 40)) * 1 if cut <= 0 else None
    lines = [base_top + i * th - bump * (1 - 0.06 * i) for i in range(len(LAYER_COLS) + 1)]
    for i in range(len(LAYER_COLS)):
        top = lines[i]; bot = lines[i + 1]
        poly = list(zip(xs, top)) + list(zip(xs[::-1], bot[::-1]))
        d.polygon([(float(a), float(b)) for a, b in poly], fill=LAYER_COLS[i])
    if gab:
        for gi in (3, 5):
            yy = lines[gi] + th * 0.45
            pts = [(float(a), float(b)) for a, b in zip(xs, yy)]
            d.line(pts, fill=(25, 30, 40), width=14)
    if magma > 0:
        my = lines[-1][120] + 40 - 120 * magma
        d.ellipse((cx - 260, my - 70 * magma, cx + 260, my + 160), fill=(255, 90, 30))
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((cx - 300, my - 100, cx + 300, my + 190), fill=(255, 120, 40, 120))
        fr.alpha_composite(g.filter(ImageFilter.GaussianBlur(30))); d = ImageDraw.Draw(fr)
        d.text((cx, my + 60), 'MAGMA', font=font(BLACK, 44), fill=(60, 10, 0), anchor='mm')
    # bottom cover below last line
    d.rectangle((x0, float(lines[-1].max()) - 1, x1, 1080), fill=BG) if magma == 0 else None
    if cut > 0:
        ytop = float(lines[0].min()); yc = ytop + (base_top + 2 * th - ytop) * cut
        d.rectangle((x0 - 5, 230, x1 + 5, yc), fill=BG)
        d.line((x0 - 40, yc, x1 + 40, yc), fill=CY, width=4)
        d.text((x0 + 10, yc - 28), 'EROSION', font=font(MONO, 30), fill=CY, anchor='lm')
    d.rectangle((0, 230, x0 - 1, 1080), fill=BG); d.rectangle((x1 + 1, 230, x1 + 60, 1080), fill=BG) if topview > 0 else None
    if topview > 0:
        k = topview; ccx, ccy = 1580, 600; R = 270
        d.text((ccx, 300), 'SEEN FROM ABOVE', font=font(MONO, 32), fill=CY + (int(255 * k),), anchor='mm')
        for i in range(8, 0, -1):
            r = R * i / 8
            col = LAYER_COLS[(8 - i) % len(LAYER_COLS)]
            d.ellipse((ccx - r, ccy - r * 0.92, ccx + r, ccy + r * 0.92), fill=col + (int(255 * k),))
        if gab:
            for rr in (0.38, 0.7):
                r = R * rr; d.ellipse((ccx - r, ccy - r * 0.92, ccx + r, ccy + r * 0.92), outline=(25, 30, 40, int(255 * k)), width=10)
        d.text((ccx, 930), 'oldest rocks in the middle', font=font(SEMI, 32), fill=WH + (int(255 * k),), anchor='mm')
    d.text((W // 2, 1040), 'Simplified illustration (not to scale) · GLITCHVERSE', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr

def dome_card(p, tl, dur):
    dome = ease(min(1, max(0, (p - 0.15) / 0.55)))
    fr = geo_diagram('grow', p, '~100 MILLION YEARS AGO', 'Magma stalls underground and lifts a dome', dome=dome, magma=min(1, p / 0.4))
    d = ImageDraw.Draw(fr)
    if p > 0.75: d.text((W // 2, 960), 'like a blister rising under paint', font=font(XB, 48), fill=SAND, anchor='mm')
    return fr.convert('RGB')

def erode_card(p, tl, dur):
    cut = ease(min(1, p / 0.5))
    fr = geo_diagram('erode', p, 'TENS OF MILLIONS OF YEARS', 'Erosion slices the top off the dome', dome=1.0, cut=cut, topview=fade(p, 0.55, 0.15))
    return fr.convert('RGB')

def sill_card(p, tl, dur):
    if p < 0.3:
        fr = geo_diagram('s', p, 'STEP 1 · ~200 MILLION YEARS AGO', 'Flat sheets of magma (sills) between rock layers', gab=True)
    elif p < 0.62:
        q = (p - 0.3) / 0.32
        fr = geo_diagram('s', p, 'STEP 2 · ~100 MILLION YEARS LATER', 'A second magma bends everything into a dome', gab=True, dome=ease(q), magma=min(1, q * 2))
    else:
        q = (p - 0.62) / 0.38
        fr = geo_diagram('s', p, 'STEP 3 · EROSION', 'The bent sheets are cut into rings', gab=True, dome=1.0, cut=ease(min(1, q / 0.5)), topview=fade(q, 0.45, 0.2))
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 990), 'Model proposed by Abdeina et al., Lithos (2024)', font=font(MED, 26), fill=(170, 180, 200), anchor='mm')
    return fr.convert('RGB')

def dates_card(p, tl, dur):
    fr = dimbg('gvr_r15.jpg', p, 'in', 0.08, 0.62)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 170), 'DATING THE EYE', font=font(MONO, 44), fill=CY, anchor='mm')
    rows = [('~98 MILLION YEARS', 'hot-fluid breccia at the center (98.2 ± 2.6 Ma)', 0.1), ('~99 MILLION YEARS', 'kimberlite plug', 0.35), ('94–104 MILLION YEARS', 'carbonatite dikes', 0.6)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 330 + i * 210
        d.text((200, y), a, font=font(BLACK, 92), fill=WH + (int(255 * k),))
        d.text((204, y + 112), b, font=font(SEMI, 40), fill=SAND + (int(255 * k),))
    src_line(d, 'Sources: Matton et al. 2005 (via Wikipedia); Abdeina et al., Lithos 2024')
    return fr.convert('RGB')

def iugs_card(p, tl, dur):
    fr = dimbg('gvr_r08.jpg', p, 'in', 0.1, 0.6)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 300), 'OCTOBER 2022', font=font(MONO, 48), fill=CY, anchor='mm')
    d.text((W // 2, 440), 'IUGS: FIRST 100', font=font(BLACK, 130), fill=WH, anchor='mm')
    d.text((W // 2, 570), 'GEOLOGICAL HERITAGE SITES', font=font(BLACK, 80), fill=WH, anchor='mm')
    if p > 0.35: d.text((W // 2, 720), '"a spectacular example of a magmatic concentric alkaline complex"', font=font(SEMI, 40), fill=SAND, anchor='mm')
    src_line(d, 'Source: International Union of Geological Sciences (via Wikipedia)')
    return fr.convert('RGB')

def atlantis_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    k = min(1, tl / 0.3)
    rgb_split_text(d, (W // 2, 270), 'ATLANTIS?', font(BLACK, 170), k, tl)
    if p > 0.2: d.text((W // 2, 420), 'Plato · Timaeus & Critias · c. 360 BC', font=font(MONO, 40), fill=CY, anchor='mm')
    if p > 0.35:
        cx, cy = W // 2, 680
        for i, r in enumerate((230, 170, 110, 55)):
            d.ellipse((cx - r * 1.6, cy - r * 0.8, cx + r * 1.6, cy + r * 0.8), outline=((90, 170, 255) if i % 2 else SAND), width=14)
        d.text((cx, 940), 'rings of land and rings of sea · sank "in a single day and night"', font=font(SEMI, 38), fill=WH, anchor='mm')
    if p > 0.7:
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L)
        ld.rounded_rectangle((1340, 520, 1800, 640), 14, outline=MG + (255,), width=8)
        ld.text((1570, 580), 'LEGEND', font=font(BLACK, 76), fill=MG + (255,), anchor='mm')
        fr.alpha_composite(L.rotate(-12, center=(1570, 580)))
    return fr.convert('RGB')

def check_card(p, tl, dur):
    fr = dimbg('gvr_r25.jpg', p, 'in', 0.08, 0.68)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 150), "PLATO'S ATLANTIS  vs  RICHAT", font=font(MONO, 44), fill=CY, anchor='mm')
    rows = [('An island in the sea', 'hundreds of km inland, on a plateau', 0.08), ('Walls & canals', 'natural rock layers, no canals', 0.26),
            ('A city & harbor', 'no ruins, no harbor ever found', 0.44), ('Concentric rings', 'yes — but made by geology', 0.62)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 290 + i * 160; last = i == 3
        d.text((180, y), a, font=font(XB, 60), fill=WH + (int(255 * k),), anchor='lm')
        d.text((180, y + 58), b, font=font(SEMI, 36), fill=(200, 210, 225, int(255 * k)), anchor='lm')
        d.text((1740, y + 20), '≈' if last else '✗', font=font(BLACK, 90), fill=((255, 210, 120) if last else MG) + (int(255 * k),), anchor='rm')
    if p > 0.85: d.text((W // 2, 950), 'Most classicists: Atlantis was Plato\'s invention', font=font(XB, 48), fill=SAND, anchor='mm')
    src_line(d, 'Sources: Wikipedia "Richat Structure" (Rafferty; Novella); Plato, Critias')
    return fr.convert('RGB')

def humans_card(p, tl, dur):
    fr = dimbg('gvr_r23.jpg', p, 'in', 0.08, 0.62)
    d = ImageDraw.Draw(fr)
    d.text((W // 2, 150), 'PEOPLE INSIDE THE EYE', font=font(MONO, 44), fill=CY, anchor='mm')
    rows = [('ACHEULEAN', 'hand axes — a tool style made for over a million years', 0.05),
            ('145,000–29,000 YEARS AGO', 'Aterian tools made by modern humans', 0.32),
            ('15,000–8,000 YEARS AGO', 'African Humid Period: lakes in the desert', 0.62)]
    for i, (a, b, t0) in enumerate(rows):
        k = fade(p, t0)
        if k <= 0: continue
        y = 280 + i * 220
        d.rectangle((160, y + 6, 168, y + 150), fill=SAND + (int(255 * k),))
        d.text((200, y), a, font=font(BLACK, 84), fill=WH + (int(255 * k),))
        d.text((204, y + 106), b, font=font(SEMI, 40), fill=(220, 225, 235, int(255 * k)))
    src_line(d, 'Source: Wikipedia "Richat Structure" (archaeology section) · ages approximate')
    return fr.convert('RGB')

def lithos_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 210), 'LITHOS · 2024', font=font(MONO, 50), fill=CY, anchor='mm')
    d.text((W // 2, 360), '"How old is the Eye of Africa?"', font=font(BLACK, 86), fill=WH, anchor='mm')
    d.text((W // 2, 470), 'Abdeina, Jourdan, Chazot, Bertrand & Le Gall', font=font(SEMI, 44), fill=SAND, anchor='mm')
    if p > 0.35:
        d.text((W // 2, 640), 'New argon dating + chemistry', font=font(XB, 60), fill=WH, anchor='mm')
        d.text((W // 2, 720), 'of the two dark gabbro rings', font=font(XB, 60), fill=WH, anchor='mm')
    src_line(d, 'Abdeina et al., Lithos 482–483 (2024) 107698')
    return fr.convert('RGB')

def ages_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 140), 'TWO AGES, ONE EYE', font=font(MONO, 46), fill=CY, anchor='mm')
    x0, x1, y = 200, 1720, 560
    def X(ma): return x1 - (ma / 260) * (x1 - x0)
    d.line((x0, y, x1, y), fill=(90, 110, 140), width=6)
    for ma in range(0, 261, 50):
        d.line((X(ma), y - 14, X(ma), y + 14), fill=(90, 110, 140), width=4)
        d.text((X(ma), y + 50), ('today' if ma == 0 else f'{ma} Ma'), font=font(MONO, 26), fill=(150, 165, 190), anchor='mm')
    k1 = fade(p, 0.1, 0.1)
    if k1 > 0:
        d.rectangle((X(230), y - 26, X(200), y + 26), fill=(30, 36, 48, int(255 * k1)), outline=WH + (int(255 * k1),), width=3)
        d.text(((X(230) + X(200)) / 2, y - 120), 'GABBRO RINGS', font=font(BLACK, 56), fill=WH + (int(255 * k1),), anchor='mm')
        d.text(((X(230) + X(200)) / 2, y - 70), '~230–200 Ma (modelled)', font=font(SEMI, 34), fill=SAND + (int(255 * k1),), anchor='mm')
    k2 = fade(p, 0.4, 0.1)
    if k2 > 0:
        d.ellipse((X(99) - 22, y - 22, X(99) + 22, y + 22), fill=(255, 110, 40, int(255 * k2)))
        d.text((X(99), y + 140), 'DOME & HOT FLUIDS', font=font(BLACK, 56), fill=WH + (int(255 * k2),), anchor='mm')
        d.text((X(99), y + 192), '~100 Ma', font=font(SEMI, 34), fill=SAND + (int(255 * k2),), anchor='mm')
    if p > 0.7:
        d.text((W // 2, 900), '≈ 100 million years apart', font=font(BLACK, 72), fill=MG, anchor='mm')
    src_line(d, 'Source: Abdeina et al., Lithos (2024); Matton et al. (2005)')
    return fr.convert('RGB')

def camp_card(p, tl, dur):
    fr = CARD_BG.copy().convert('RGBA'); d = ImageDraw.Draw(fr)
    d.text((W // 2, 130), 'CENTRAL ATLANTIC MAGMATIC PROVINCE · ~201 Ma', font=font(MONO, 40), fill=CY, anchor='mm')
    sep = ease(min(1, p / 0.8)) * 220
    # schematic continents (not a real map)
    am = [(560, 300), (720, 260), (820, 380), (800, 560), (760, 760), (640, 900), (560, 760), (520, 560)]
    af = [(1000, 280), (1240, 260), (1360, 420), (1320, 640), (1200, 860), (1080, 820), (1020, 600), (960, 420)]
    d.polygon([(x - sep / 2, y) for x, y in am], fill=(120, 95, 70))
    d.polygon([(x + sep / 2, y) for x, y in af], fill=(150, 115, 80))
    if sep > 20:
        d.rectangle((830 - sep / 2 + 20, 300, 950 + sep / 2 - 30, 820), fill=(30, 70, 120))
        d.text((W // 2, 560), 'ATLANTIC', font=font(BLACK, 34 + int(sep / 10)), fill=(160, 210, 255), anchor='mm')
    d.text((560 - sep / 2, 960), 'AMERICAS', font=font(XB, 40), fill=WH, anchor='mm')
    d.text((1180 + sep / 2, 960), 'AFRICA', font=font(XB, 40), fill=WH, anchor='mm')
    rx, ry = 1060 + sep / 2, 420
    d.ellipse((rx - 14, ry - 14, rx + 14, ry + 14), fill=MG, outline=WH, width=3)
    d.text((rx + 26, ry), 'Richat', font=font(XB, 34), fill=WH, anchor='lm')
    d.text((W // 2, 210), 'Pangaea splits · the Atlantic begins to open', font=font(XB, 48), fill=WH, anchor='mm')
    d.text((W // 2, 1040), 'Schematic sketch, not a real map · GLITCHVERSE', font=font(MED, 22), fill=(130, 140, 160), anchor='mm')
    return fr.convert('RGB')

def question_card(p, tl, dur):
    fr = dimbg('gvr_r02.jpg', p, 'in', 0.14, 0.5)
    d = ImageDraw.Draw(fr)
    if p > 0.05: d.text((W // 2, 300), 'IN THE CENTER OF THE EYE…', font=font(MONO, 46), fill=CY, anchor='mm')
    if p > 0.15: d.text((W // 2, 440), 'DIG FOR THE PEOPLE?', font=font(BLACK, 104), fill=WH, anchor='mm')
    if p > 0.3: d.text((W // 2, 560), 'or', font=font(SEMI, 50), fill=CY, anchor='mm')
    if p > 0.38: d.text((W // 2, 680), 'DIG FOR THE MAGMA?', font=font(BLACK, 104), fill=SAND, anchor='mm')
    if p > 0.55: d.text((W // 2, 860), '↓  Tell me in the comments', font=font(XB, 54), fill=WH, anchor='mm')
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

# ---------- SEGMENTS ----------
SEG = {
 's01': [dict(card(hook_card, glitch=False), dur=3.0), dict(card(title_card), dur=3.0), img_shot('gvr_r04.jpg', 'in', ('THE EYE OF THE SAHARA', 'Richat Structure · Mauritania'))],
 's02': [card(theories_card, w=2.2, credit='gvr_r10.jpg'), img_shot('gvr_r06.jpg', 'right', ('THE RICHAT STRUCTURE', 'Adrar Plateau, Mauritania')), img_shot('gvr_r25.jpg', 'in', None), img_shot('gvr_r16.jpg', 'left', ('Meteor? Volcano? Atlantis?', 'let\'s check each one'))],
 's03': [card(map_in, glitch=False, w=2.6, credit='gvr_s2_close.jpg', grade=True), img_shot('gvr_r12.jpg', 'in', ('ADRAR PLATEAU', 'NASA MODIS view')), img_shot('gvr_r21.jpg', 'right', ('OUADANE', 'old caravan town nearby')), img_shot('gvr_r09.jpg', 'in', ('"GUELB ER RICHAT"', 'also called "tagense": the mouth of a water bag'))],
 's04': [img_shot('gvr_r20.jpg', 'right', ('FROM THE GROUND', 'low ridges, dry valleys — no circle in sight')), img_shot('gvr_r13.jpg', 'left', ('Inside the eye', 'the rings are hard to see up close')), card(gemini_card, w=2.0, credit='gvr_r29.jpg'), img_shot('gvr_r07.jpg', 'in', ('APOLLO 9 · 1969', 'an early view from orbit'), amt=0.3, focus=(0.42, 0.62)), img_shot('gvr_r05.jpg', 'right', ('A LANDMARK FOR CREWS IN ORBIT', None))],
 's05': [img_shot('gvr_r10.jpg', 'out', ('40 KM ACROSS', 'big enough to frame a whole city'), amt=0.2)],
 's06': [img_shot('gvr_r08.jpg', 'in', ('THEORY #1: A METEORITE', None)), card(monod_card, w=2.4), img_shot('gvr_r15.jpg', 'right', ('THE CENTRAL ZONE', 'Richat "ombilic", ground view'))],
 's07': [img_shot('gvr_r27.jpg', 'in', None, focus=(0.5, 0.42)), card(coesite_card, w=2.4), img_shot('gvr_r17.jpg', 'left', ('NO IMPACT FINGERPRINTS', 'no evidence of shock metamorphism'), focus=(0.5, 0.42))],
 's08': [img_shot('gvr_r31.jpg', 'in', ('STILL UNEXPLAINED:', 'the rings'), focus=(0.5, 0.42)), card(loop1_card, w=1.8, credit='gvr_r17.jpg'), img_shot('gvr_r02.jpg', 'in', None, darken=0.15)],
 's09': [card(dome_card, w=2.6), img_shot('gvr_r08.jpg', 'out', ('NOT A VOLCANO', 'the magma never reached the surface'))],
 's10': [img_shot('gvr_r15.jpg', 'in', ('CENTRAL BRECCIA', 'up to 40 m thick')), card(dates_card, w=2.2, credit='gvr_r15.jpg'), img_shot('gvr_r09.jpg', 'right', None)],
 's11': [card(erode_card, w=2.4), img_shot('gvr_r04.jpg', 'right', ('CUESTAS', 'hard quartzite stands up as rings')), img_shot('gvr_r16.jpg', 'in', ('OLDEST AT THE CENTER', 'younger rocks toward the edge'))],
 's12': [img_shot('gvr_r06.jpg', 'in', ('NASA EARTH OBSERVATORY:', '"a deeply eroded geologic dome"')), card(iugs_card, w=1.6, credit='gvr_r08.jpg')],
 's13': [card(loop2_card, w=1.4, credit='gvr_r13.jpg'), img_shot('gvr_r19.jpg', 'in', None)],
 's14': [card(atlantis_card, w=2.4), img_shot('gvr_r02.jpg', 'in', ('LEGEND, NOT HISTORY', 'Plato, Critias & Timaeus, c. 360 BC'), darken=0.2), img_shot('gvr_r25.jpg', 'right', None)],
 's15': [card(check_card, w=3.0, credit='gvr_r25.jpg'), img_shot('gvr_r18.jpg', 'in', ('HUNDREDS OF KM FROM THE SEA', None)), img_shot('gvr_r22.jpg', 'left', ('VERDICT: LEGEND FILE', None))],
 's16': [img_shot('gvr_r20.jpg', 'in', ('ACHEULEAN SITES', 'along the dry riverbeds of the outer ring')), img_shot('gvr_r23.jpg', 'right', ('STONE HAND AXES', 'first recorded here by Théodore Monod, 1974')), img_shot('gvr_r13.jpg', 'in', None)],
 's17': [card(humans_card, w=2.6, credit='gvr_r23.jpg'), img_shot('gvr_r30.jpg', 'in', ('AFRICAN HUMID PERIOD', 'lakes here ~15,000–8,000 years ago'))],
 's18': [img_shot('gvr_r24.jpg', 'in', ('ROCK ART · ADRAR REGION', 'Mauritania')), img_shot('gvr_r19.jpg', 'left', ('THOUSANDS OF BURIAL MOUNDS', 'still not excavated')), img_shot('gvr_r05.jpg', 'in', ('LIVING INSIDE THE EYE', None))],
 's19': [img_shot('gvr_r17.jpg', 'in', ('OPEN FILE #1', 'the two dark rings'), focus=(0.48, 0.42), amt=0.25), img_shot('gvr_r28.jpg', 'in', ('GABBRO RINGS', 'geologic map of Guelb er Richat'), focus=(0.5, 0.45), amt=0.2)],
 's20': [card(lithos_card, w=1.8), card(ages_card, w=2.6), card(camp_card, w=2.2)],
 's21': [card(sill_card, w=3.4), img_shot('gvr_r31.jpg', 'in', ('TWO EVENTS. ONE EYE.', '~200 million + ~100 million years ago'), focus=(0.5, 0.42)), img_shot('gvr_r10.jpg', 'out', ('A FOSSIL OF AN OPENING OCEAN?', 'if the 2024 study is right'))],
 's22': [card(map_out, glitch=False, w=1.6, credit='gvr_s2_close.jpg', grade=True), img_shot('gvr_r01.jpg', 'in', ('NOT A CITY.', 'the birth of an ocean'))],
 's23': [card(question_card, w=2.0, credit='gvr_r02.jpg', grade=True), img_shot('gvr_r02.jpg', 'out', ('SUBSCRIBE', 'for the next entry of my Glitch Diary'))],
 'end': [card(endcard, glitch=False)],
}
CHAPTERS = {'s03': (1, 'The eye from orbit'), 's06': (2, "The crater that wasn't"), 's09': (3, 'How to grow an eye'),
            's14': (4, 'Atlantis?'), 's16': (5, 'Who was here first'), 's19': (6, 'The eye has two ages'), 's23': (7, 'Your turn')}

def build_timeline():
    shots = []
    order = list(TIM.keys()) + ['end']
    for sid in order:
        if sid == 'end': a, b = TIM['s23']['end'], TOTAL
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
