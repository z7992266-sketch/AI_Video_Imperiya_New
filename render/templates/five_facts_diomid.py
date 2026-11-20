import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, 'frames'); os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/opentype/inter/'
def F(w, s): return ImageFont.truetype(FONT + f'Inter-{w}.otf', s)
GOLD = (233, 185, 73); CREAM = (255, 246, 228); BG = (6, 10, 24)
RUS = (226, 76, 76); USA = (70, 150, 255); ICE = (200, 228, 245)

world = json.load(open(os.path.join(D, '..', 'bday', 'world.json')))['features']
def rings(g): return [g['coordinates'][0]] if g['type'] == 'Polygon' else [p[0] for p in g['coordinates']]
WR = [(f['properties']['a3'], [np.array(r) for r in rings(f['geometry'])]) for f in world]

def ease(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
def eob(t):  # ease out back
    t = min(max(t, 0), 1); c = 1.70158; return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
def lerp(a, b, t): return a + (b - a) * t
def win(t, a, b, fi=0.4, fo=0.4): return ease((t - a) / fi) * (1 - ease((t - b + fo) / fo))

rng = random.Random(3)
STARS = [(rng.random() * W, rng.random() * H, rng.random()) for _ in range(220)]
_g = np.linspace(0, 1, H)[:, None, None]
_BG = Image.fromarray(np.broadcast_to(np.array(BG, np.float32) + _g * np.array([10, 16, 36], np.float32), (H, W, 3)).clip(0, 255).astype(np.uint8))
def background(t):
    im = _BG.copy(); d = ImageDraw.Draw(im)
    for x, y, b in STARS:
        y2 = (y + t * 12 * b) % H
        a = int(70 + 120 * b * (0.6 + 0.4 * math.sin(t * 2 + x)))
        d.point((x, y2), fill=(a, a, min(255, a + 25)))
    return im

def ortho(pts, lon0, lat0):
    lon = np.radians(pts[:, 0] - lon0); lat = np.radians(pts[:, 1]); p0 = math.radians(lat0)
    x = np.cos(lat) * np.sin(lon)
    y = math.cos(p0) * np.sin(lat) - math.sin(p0) * np.cos(lat) * np.cos(lon)
    c = math.sin(p0) * np.sin(lat) + math.cos(p0) * np.cos(lat) * np.cos(lon)
    n = np.sqrt(x * x + y * y) + 1e-9; vis = c > 0
    return np.where(vis, x, x / n), np.where(vis, y, y / n), vis
def draw_globe(im, lon0, lat0, R, cx, cy, hi):
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for k in range(10, 0, -1):
        rr = R + k * 7; d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(60, 120, 255, 6))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(14, 40, 92, 255))
    for a3, rs in WR:
        col = (60, 120, 92)
        if a3 == 'RUS': col = tuple(int(lerp(c1, c2, hi)) for c1, c2 in zip(col, RUS))
        if a3 == 'USA': col = tuple(int(lerp(c1, c2, hi)) for c1, c2 in zip(col, USA))
        for r in rs:
            x, y, vis = ortho(r, lon0, lat0)
            if not vis.any(): continue
            P = list(zip(cx + x * R, cy - y * R))
            if len(P) > 2: d.polygon(P, fill=col + (255,), outline=(210, 230, 220, 110))
    im.paste(ov, (0, 0), ov)

def text_c(im, txt, y, font, fill=CREAM, alpha=1.0, spacing=10, x=None, scale=1.0):
    if alpha <= 0: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bb = d.multiline_textbbox((0, 0), txt, font=font, align='center', spacing=spacing)
    tw = bb[2] - bb[0]; cx = W / 2 if x is None else x
    a = int(255 * min(1, alpha))
    d.multiline_text((cx - tw / 2 - bb[0] + 4, y + 6), txt, font=font, fill=(0, 0, 0, int(a * .7)), align='center', spacing=spacing)
    d.multiline_text((cx - tw / 2 - bb[0], y), txt, font=font, fill=fill + (a,), align='center', spacing=spacing,
                     stroke_width=3, stroke_fill=(0, 0, 0, int(a * .8)))
    if scale != 1.0:
        sz = (int(W * scale), int(H * scale)); ov = ov.resize(sz, Image.BILINEAR)
        ox = int(cx - cx * scale); oy = int((y + 40) - (y + 40) * scale)
        im.paste(ov, (ox, oy), ov)
    else:
        im.paste(ov, (0, 0), ov)

def panel(im, box, alpha, r=36, col=(10, 16, 36), op=210, border=None):
    if alpha <= 0: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rounded_rectangle(box, r, fill=col + (int(op * alpha),), outline=(border + (int(255 * alpha),)) if border else None, width=3)
    im.paste(ov, (0, 0), ov)

# ---------- schematic islands (screen space, west = left) ----------
def blob(cx, cy, rx, ry, seed, n=90):
    r = random.Random(seed); ph = [r.random() * 6.28 for _ in range(4)]
    pts = []
    for i in range(n):
        a = i / n * 2 * math.pi
        k = 1 + 0.08 * math.sin(3 * a + ph[0]) + 0.05 * math.sin(5 * a + ph[1]) + 0.03 * math.sin(9 * a + ph[2])
        pts.append((cx + rx * k * math.cos(a), cy + ry * k * math.sin(a)))
    return pts
def islands(im, t, alpha, zoom=1.0, ice=0.0, dateline=0.0, ruler=0.0, cy=880):
    if alpha <= 0: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    a = int(255 * alpha)
    # sea
    sea = (16, 52, 96) if ice < 0.5 else tuple(int(lerp(c1, c2, ice)) for c1, c2 in zip((16, 52, 96), (150, 185, 210)))
    d.rounded_rectangle([60, cy - 430, W - 60, cy + 430], 44, fill=sea + (int(235 * alpha),), outline=(120, 170, 220, int(160 * alpha)), width=3)
    # waves / ice cracks
    for i in range(14):
        yy = cy - 380 + i * 58 + (t * 18) % 58
        if yy > cy + 400: continue
        c = (255, 255, 255, int(28 * alpha * (1 - ice)))
        d.arc([100 + (i * 97) % 700, yy, 220 + (i * 97) % 700, yy + 30], 200, 340, fill=c, width=2)
    s = zoom
    big = blob(W / 2 - 230 * s, cy, 190 * s, 300 * s, 1)
    lit = blob(W / 2 + 230 * s, cy + 40 * s, 95 * s, 140 * s, 2)
    d.polygon(big, fill=(150, 72, 66, a), outline=(255, 190, 180, a))
    d.polygon(lit, fill=(64, 112, 176, a), outline=(190, 220, 255, a))
    im.paste(ov, (0, 0), ov)
    d = ImageDraw.Draw(im)
    if dateline > 0:
        y0 = cy - 430; y1 = lerp(y0, cy + 430, ease(dateline))
        y = y0
        while y < y1:
            d.line([(W / 2, y), (W / 2, min(y + 26, y1))], fill=GOLD, width=7); y += 44
    if ruler > 0:
        xa = W / 2 - 230 * s + 175 * s; xb = W / 2 + 230 * s - 88 * s
        xr = lerp(xa, xb, ease(ruler)); yr = cy + 260 * s
        d.line([(xa, yr), (xr, yr)], fill=GOLD, width=8)
        d.line([(xa, yr - 22), (xa, yr + 22)], fill=GOLD, width=8)
        if ruler >= 1: d.line([(xb, yr - 22), (xb, yr + 22)], fill=GOLD, width=8)

def tag(im, txt, x, y, col, alpha, f=None):
    if alpha <= 0: return
    f = f or F('Bold', 40)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bb = d.textbbox((0, 0), txt, font=f); w = bb[2] - bb[0]; h = bb[3] - bb[1]
    d.rounded_rectangle([x - w / 2 - 22, y - 12, x + w / 2 + 22, y + h + 22], 20, fill=col + (int(235 * alpha),))
    d.text((x - w / 2 - bb[0], y - bb[1] + 4), txt, font=f, fill=(255, 255, 255, int(255 * alpha)))
    im.paste(ov, (0, 0), ov)

def clock_card(im, x, y, label, day, hour, col, alpha):
    panel(im, [x - 210, y, x + 210, y + 300], alpha, col=(12, 18, 40), op=235, border=col)
    text_c(im, label, y + 22, F('Bold', 40), fill=col, alpha=alpha, x=x)
    text_c(im, hour, y + 82, F('Black', 104), fill=CREAM, alpha=alpha, x=x)
    text_c(im, day, y + 215, F('ExtraBold', 46), fill=GOLD, alpha=alpha, x=x)

def chip(im, txt, y, alpha):
    if alpha <= 0: return
    f = F('SemiBold', 32)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bb = d.textbbox((0, 0), txt, font=f); w = bb[2] - bb[0]
    d.rounded_rectangle([W / 2 - w / 2 - 20, y, W / 2 + w / 2 + 20, y + 54], 27, fill=(255, 255, 255, int(28 * alpha)), outline=(255, 255, 255, int(70 * alpha)))
    d.text((W / 2 - w / 2 - bb[0], y + 8), txt, font=f, fill=(220, 225, 235, int(255 * alpha)))
    im.paste(ov, (0, 0), ov)

FACTS = [(2.6, 7.4), (7.4, 11.8), (11.8, 16.6), (16.6, 21.0), (21.0, 25.6)]
TOTAL = 28.5
def progress(im, t):
    if t < 2.6 or t > 25.6: return
    k = min(1, (t - 2.6) / (25.6 - 2.6)); idx = sum(1 for a, b in FACTS if t >= a)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([60, 120, W - 60, 132], 6, fill=(255, 255, 255, 40))
    d.rounded_rectangle([60, 120, 60 + (W - 120) * k, 132], 6, fill=GOLD)
    d.text((60, 150), 'DIOMID OROLLARI', font=F('Bold', 34), fill=(200, 205, 220))
    s = f'{idx:02d} / 05'; f = F('Black', 44); bb = d.textbbox((0, 0), s, font=f)
    d.text((W - 60 - (bb[2] - bb[0]), 144), s, font=f, fill=GOLD)

def headline(im, t, a, b, txt, y=250, size=92, fill=CREAM):
    al = win(t, a, b, 0.35, 0.35)
    if al > 0: text_c(im, txt, y, F('Black', size), fill=fill, alpha=al, spacing=12, scale=lerp(1.25, 1.0, eob((t - a) / 0.45)))

def hook(im, t, a):
    # frame-1 composition (also used for loop end)
    islands(im, t, a, zoom=1.0 + 0.03 * t % 1 * 0, cy=980)
    tag(im, 'ROSSIYA', W / 2 - 230, 760, RUS, a); tag(im, 'AQSH', W / 2 + 230, 860, USA, a)
    text_c(im, 'ERTANGI KUN', 1170, F('Black', 52), fill=CREAM, alpha=a, x=W / 2 - 230)
    text_c(im, 'KECHAGI KUN', 1170, F('Black', 52), fill=CREAM, alpha=a, x=W / 2 + 230)
    text_c(im, 'ORASI 4 KM,\nFARQI — 1 KUN', 230, F('Black', 104), fill=GOLD, alpha=a, spacing=14)
    chip(im, '5-chisi eng g‘alati', 500, a)

def frame(t):
    im = background(t)
    # HOOK 0-2.6
    if t < 2.9:
        a = win(t, -1, 2.9, 0.3, 0.35)
        hook(im, t, a)
    # 01: globe -> Bering strait, two countries
    if 2.6 <= t < 7.6:
        lt = t - 2.6; a = win(t, 2.6, 7.6, 0.35, 0.4)
        k = ease(lt / 3.2)
        lon0 = lerp(64, 191, k); lat0 = lerp(30, 64, k)
        R = lerp(420, 1250, ease((lt - 1.6) / 2.4))
        tmp = background(t); draw_globe(tmp, lon0, lat0, R, W / 2, H * 0.52, ease((lt - 1.4) / 1.0))
        pa = ease((lt - 2.6) / 0.5)
        if pa > 0:
            x, y, vis = ortho(np.array([[-169.0, 65.77]]), lon0, lat0)
            px, py = W / 2 + x[0] * R, H * 0.52 - y[0] * R
            dd = ImageDraw.Draw(tmp)
            ph = (lt * 1.2) % 1; rr = 20 + 110 * ph
            dd.ellipse([px - rr, py - rr, px + rr, py + rr], outline=GOLD, width=6)
            dd.ellipse([px - 18, py - 18, px + 18, py + 18], fill=GOLD)
        im = Image.blend(im, tmp, a)
        headline(im, t, 2.8, 7.6, 'Ikki orol —\nikki davlat', 240)
        tag(im, 'ROSSIYA', W / 2 - 250, 1450, RUS, win(t, 4.6, 7.6, .3, .4), F('Black', 46))
        tag(im, 'AQSH (Alyaska)', W / 2 + 230, 1450, USA, win(t, 4.9, 7.6, .3, .4), F('Black', 46))
        chip(im, 'Bering bo‘g‘ozi', 1530, win(t, 5.2, 7.6, .3, .4))
    # 02: distance ruler
    if 7.4 <= t < 12.0:
        a = win(t, 7.4, 12.0, 0.35, 0.4)
        r = ease((t - 8.2) / 1.6)
        islands(im, t, a, ruler=r, cy=960)
        tag(im, 'Katta Diomid', W / 2 - 230, 560, RUS, a); tag(im, 'Kichik Diomid', W / 2 + 230, 700, USA, a)
        km = 3.8 * r
        text_c(im, f'{km:.1f} km'.replace('.', ','), 1270, F('Black', 130), fill=GOLD, alpha=win(t, 8.2, 12.0, .3, .4))
        headline(im, t, 7.6, 12.0, 'Orasi atigi', 260)
        chip(im, 'Sxema · masofa: NOAA / USGS', 1530, a)
    # 03: date line + 21 hours
    if 11.8 <= t < 16.8:
        a = win(t, 11.8, 16.8, 0.35, 0.4)
        if t < 13.9:
            islands(im, t, a * (1 - ease((t - 13.4) / 0.5)), dateline=ease((t - 12.2) / 1.2), cy=960)
            headline(im, t, 12.0, 14.0, 'O‘rtasidan sana\nchizig‘i o‘tadi', 250)
        else:
            b = win(t, 13.6, 16.8, .35, .4)
            hrs = int(round(21 * ease((t - 14.0) / 1.0)))
            headline(im, t, 13.8, 16.8, 'Qishda soat farqi', 250, 80)
            text_c(im, f'{hrs} SOAT', 420, F('Black', 170), fill=GOLD, alpha=b)
            clock_card(im, W / 2 - 230, 780, 'ROSSIYA', 'PAYSHANBA', '12:00', RUS, b)
            clock_card(im, W / 2 + 230, 780, 'AQSH', 'CHORSHANBA', '15:00', USA, b)
            chip(im, 'UTC+12  vs  UTC−9  (yozda 20 soat)', 1160, b)
    # 04: ice bridge but banned
    if 16.6 <= t < 21.2:
        a = win(t, 16.6, 21.2, 0.35, 0.4)
        ice = ease((t - 17.0) / 1.2)
        islands(im, t, a, ice=ice, dateline=1.0, cy=960)
        headline(im, t, 16.8, 21.2, 'Qishda orasini\nmuz qoplaydi…', 240)
        if t > 18.8:
            b = win(t, 18.8, 21.2, .25, .4); p = eob((t - 18.8) / 0.5)
            panel(im, [110, 1430, W - 110, 1600], b, col=(150, 20, 30), op=225)
            text_c(im, 'Piyoda o‘tish TAQIQLANGAN', 1468, F('Black', 58), fill=CREAM, alpha=b, scale=lerp(1.3, 1, p))
    # 05: population
    if 21.0 <= t < 25.8:
        a = win(t, 21.0, 25.8, 0.35, 0.4)
        headline(im, t, 21.2, 25.8, 'Eng g‘alatisi:', 250, 84, GOLD)
        n = int(round(80 * ease((t - 21.8) / 1.2)))
        panel(im, [90, 480, W - 90, 860], a, border=USA)
        text_c(im, 'Kichik Diomid (AQSH)', 510, F('Bold', 48), fill=USA, alpha=a)
        text_c(im, f'~{n} kishi', 590, F('Black', 150), fill=CREAM, alpha=a)
        b = win(t, 22.8, 25.8, .35, .4)
        panel(im, [90, 920, W - 90, 1300], b, border=RUS)
        text_c(im, 'Katta Diomid (Rossiya)', 950, F('Bold', 48), fill=RUS, alpha=b)
        text_c(im, '0 aholi', 1030, F('Black', 150), fill=CREAM, alpha=b)
        text_c(im, 'faqat chegarachilar', 1200, F('SemiBold', 44), fill=(200, 205, 220), alpha=b)
        chip(im, 'US Census 2020', 1360, a)
    # question card
    if 25.6 <= t < 27.9:
        a = win(t, 25.6, 27.9, 0.35, 0.4)
        text_c(im, 'Siz qaysi biriga\nishonmadingiz?', 640, F('Black', 100), fill=GOLD, alpha=a, spacing=16, scale=lerp(1.2, 1, eob((t - 25.6) / .5)))
        text_c(im, 'Izohda yozing', 960, F('ExtraBold', 70), fill=CREAM, alpha=a)
        chip(im, '1 · 2 · 3 · 4 · 5', 1090, a)
    if t >= 27.6:
        hook(im, t, ease((t - 27.6) / 0.6))
    progress(im, t)
    return im

if __name__ == '__main__' and len(sys.argv)>1 and sys.argv[0].endswith('make.py'):
    if sys.argv[1] == 'prev':
        for tt in sys.argv[2:]:
            frame(float(tt)).convert('RGB').save(os.path.join(D, f'p_{tt}.jpg'), quality=85)
    else:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        for i in range(a, b):
            frame(i / FPS).convert('RGB').save(os.path.join(OUT, f'f{i:05d}.jpg'), quality=92)
