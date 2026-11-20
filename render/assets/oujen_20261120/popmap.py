"""OUJ EN 20261120 — "If the map was drawn by people" — frame renderer (silent mp4).
usage: python3 popmap.py segs.json out.mp4 [--frames t1,t2,...]"""
import json, math, sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DATA = '/home/claude/fm/fetch/out/'
FONTS = '/home/claude/rw/render/fonts/'
W, H, FPS, SS = 1080, 1920, 30, 2
NAVY0, NAVY1 = (7, 13, 34), (16, 30, 66)
GOLD = (242, 181, 61)
LAND = (52, 74, 128)
LAND_EDGE = (90, 118, 182)
RED = (231, 84, 84)
CYAN = (64, 214, 230)
GREEN = (98, 214, 120)
WHITE = (240, 244, 255)
MUTED = (150, 165, 205)

def F(name, size):
    return ImageFont.truetype(FONTS + name, size * SS)
FB = 'InterDisplay-Black.otf'; FX = 'InterDisplay-ExtraBold.otf'; FI = 'Inter-Bold.otf'

# ---------------- data ----------------
pop = {r['countryiso3code']: r['value'] for r in json.load(open(DATA + 'oujen_wbpop2023.json'))[1] if r['value']}
ne = json.load(open(DATA + 'oujen_ne110.geojson'))
FIX = {'France': 'FRA', 'Norway': 'NOR', 'Kosovo': 'XKX', 'Somaliland': None, 'N. Cyprus': None, 'Taiwan': None}

# projection: equirectangular, lon -180..180 -> map width MW, lat 84..-57
MW = 1060
PX = MW / 360.0
LAT0, LAT1 = 84.0, -57.0
MH = (LAT0 - LAT1) * PX
MAP_CY = 820  # center y of map box
MX0 = (W - MW) / 2
MY0 = MAP_CY - MH / 2

def proj(lon, lat):
    return MX0 + (lon + 180) * PX, MY0 + (LAT0 - lat) * PX

def ring_area_centroid(pts):
    x, y = pts[:, 0], pts[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    c = x * y1 - x1 * y
    a = c.sum() / 2
    if abs(a) < 1e-9:
        return 0.0, pts.mean(0)
    cx = ((x + x1) * c).sum() / (6 * a); cy = ((y + y1) * c).sum() / (6 * a)
    return abs(a), np.array([cx, cy])

countries = []
for f in ne['features']:
    p = f['properties']
    if p['ADMIN'] == 'Antarctica':
        continue
    iso = p['ISO_A3'] if p['ISO_A3'] not in ('-99', None) else p.get('ADM0_A3')
    if p['ADMIN'] in FIX: iso = FIX[p['ADMIN']] or p.get('ADM0_A3')
    g = f['geometry']
    polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    rings = []
    for poly in polys:
        outer = np.array(poly[0], float)
        pts = np.array([proj(lo, la) for lo, la in outer])
        rings.append(pts)
    # area in km2 approx (spherical, using lat cos) for density; centroid in px using largest-area-weighted
    A = 0; C = np.zeros(2); kmA = 0
    for poly in polys:
        o = np.array(poly[0], float)
        a_deg, c_deg = ring_area_centroid(o)
        km = a_deg * 111.32 ** 2 * math.cos(math.radians(c_deg[1]))
        kmA += km
        a, c = ring_area_centroid(np.array([proj(lo, la) for lo, la in o]))
        A += a; C += a * c
    C = C / A if A else rings[0].mean(0)
    countries.append(dict(name=p['NAME'], iso=iso, rings=rings, km2=kmA, c=C, pop=pop.get(iso)))

# per-ring centroids for multi-part countries: scale each part about the COUNTRY centroid for mainland,
# but far-away parts (e.g. Alaska, islands) about their own centroid so they don't fly across the map.
for c in countries:
    parts = []
    for r in c['rings']:
        a, cc = ring_area_centroid(r)
        far = np.linalg.norm(cc - c['c']) > 60
        parts.append((r, cc if far else c['c']))
    c['parts'] = parts

tot_pop = sum(c['pop'] for c in countries if c['pop'])
tot_km = sum(c['km2'] for c in countries if c['pop'])
dens_w = tot_pop / tot_km
REF = None
for c in countries:
    if c['pop']:
        c['dens'] = c['pop'] / c['km2']
REFD = [c for c in countries if c['iso'] == 'IND'][0]['dens'] * 0.5  # anchor: India grows ~1.4x
for c in countries:
    if c['pop']:
        k = math.sqrt(c['dens'] / REFD)
        c['k'] = min(k, 2.8)
    else:
        c['k'] = 0.35
BY = {c['iso']: c for c in countries}

# ---------------- timeline ----------------
segs = json.load(open(sys.argv[1]))['segments']
VO = 0.35  # voice start offset in the final mix
S = [(s['s'] + VO, s['e'] + VO) for s in segs]
END = S[-1][1] + 0.9
MORPH0, MORPH1 = S[1][1] - 0.15, S[1][1] + 1.6
BACK0, BACK1 = S[6][0] + 0.1, S[6][0] + 1.5

def ease(x):
    x = min(1, max(0, x)); return x * x * (3 - 2 * x)

def morph_amt(t):
    if t < MORPH0: return 0.0
    if t < MORPH1: return ease((t - MORPH0) / (MORPH1 - MORPH0))
    if t < BACK0: return 1.0
    return 1 - ease((t - BACK0) / (BACK1 - BACK0))

def mix(a, b, u):
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))

def fade(t, t0, d=0.35):
    return ease((t - t0) / d)

# ---------------- static background ----------------
def make_bg():
    y = np.linspace(0, 1, H)[:, None]
    bg = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        bg[:, :, i] = NAVY1[i] * (1 - y) * 0.9 + NAVY0[i] * (0.4 + 0.6 * y)
    # soft vignette glow behind the map
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - W / 2) / 620.0) ** 2 + ((yy - MAP_CY) / 420.0) ** 2))
    bg += g[:, :, None] * np.array([18, 30, 60], np.float32)
    # faint grid (graticule-like dots)
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).resize((W * SS, H * SS))
    d = ImageDraw.Draw(img)
    for lon in range(-180, 181, 30):
        x, _ = proj(lon, 0)
        for lat in np.arange(LAT1, LAT0, 2.0):
            _, yv = proj(0, lat)
            d.point((x * SS, yv * SS), fill=(40, 60, 110))
    for lat in range(-30, 90, 30):
        _, yv = proj(0, lat)
        for lon in np.arange(-180, 180, 2.0):
            x, _ = proj(lon, 0)
            d.point((x * SS, yv * SS), fill=(40, 60, 110))
    return img
BG = make_bg()

HL = {}  # iso -> color function of t

def country_color(c, t, m):
    iso = c['iso']
    col = LAND
    # Russia (hook) red pulse during seg0, Russia/Canada red during seg2
    if iso == 'RUS' and t < MORPH0:
        col = mix(LAND, RED, fade(t, 0.0, 0.01) * (0.75 + 0.25 * math.sin(t * 5)))
    if iso in ('RUS', 'CAN') and S[2][0] - 0.2 < t < S[3][0]:
        col = mix(LAND, RED, fade(t, S[2][0] - 0.2))
    if iso in ('IND', 'CHN') and S[3][0] - 0.2 < t < BACK0:
        col = mix(LAND, GOLD, fade(t, S[3][0] - 0.2))
    if iso == 'BGD' and S[4][0] - 0.2 < t < BACK0:
        col = mix(LAND, CYAN, fade(t, S[4][0] - 0.2))
    if iso == 'RUS' and S[4][0] - 0.2 < t < S[6][0]:
        col = mix(LAND, RED, fade(t, S[4][0] - 0.2))
    if iso == 'CAN' and S[5][0] - 0.2 < t < S[6][0]:
        col = mix(LAND, RED, fade(t, S[5][0] - 0.2))
    if iso == 'NGA' and S[5][0] - 0.2 < t < BACK0:
        col = mix(LAND, GREEN, fade(t, S[5][0] - 0.2))
    return col

ORDER = sorted(countries, key=lambda c: -c['km2'])  # big first, small on top
TOP = ['IND', 'CHN', 'BGD', 'NGA', 'RUS', 'CAN']

CAMS = None
def camera(t):
    # keyframes: (time, zoom, lon, lat)
    world = (1.0, None)
    keys = [(0, 1.0, 0, 13.5), (S[3][0] - 0.3, 1.0, 0, 13.5), (S[3][0] + 0.6, 1.9, 92, 32),
            (S[4][0] - 0.2, 1.9, 92, 32), (S[4][0] + 0.6, 1.6, 92, 42), (S[5][0] - 0.2, 1.6, 92, 42),
            (S[5][0] + 0.6, 1.0, 0, 13.5), (999, 1.0, 0, 13.5)]
    for (t0, z0, lo0, la0), (t1, z1, lo1, la1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = ease((t - t0) / max(1e-6, t1 - t0)) if (z0, lo0, la0) != (z1, lo1, la1) else 0
            return z0 + (z1 - z0) * u, np.array(proj(lo0 + (lo1 - lo0) * u, la0 + (la1 - la0) * u))
    return 1.0, np.array(proj(0, 13.5))

def draw_map(d, t, zoom, m):
    cz, cc = camera(t)
    zoom = zoom * cz
    zc = np.array([W / 2, MAP_CY])
    def tf(pts, center, k):
        p = center + (pts - center) * k
        return (zc + (p - cc) * zoom) * SS
    hl = [c for c in ORDER if c['iso'] in TOP]
    rest = [c for c in ORDER if c['iso'] not in TOP]
    for c in rest + hl:
        k = 1 + (c['k'] - 1) * m
        col = country_color(c, t, m)
        edge = mix(col, WHITE, 0.25)
        for r, cen in c['parts']:
            p = tf(r, cen, k)
            if len(p) < 3: continue
            d.polygon([tuple(q) for q in p], fill=col, outline=edge, width=max(1, int(1.2 * SS)))
    return lambda iso: tuple((zc + (BY[iso]['c'] - cc) * zoom))

def text_c(d, xy, s, font, fill, anchor='mm', stroke=0, sfill=(0, 0, 0)):
    d.text((xy[0] * SS, xy[1] * SS), s, font=font, fill=fill, anchor=anchor,
           stroke_width=stroke * SS, stroke_fill=sfill)

def pill(d, cx, cy, s, font, fg, bg, alpha=1.0, pad=(18, 10)):
    if alpha <= 0: return
    bb = d.textbbox((0, 0), s, font=font, anchor='lt')
    w, h = (bb[2] - bb[0]) / SS, (bb[3] - bb[1]) / SS
    x0, y0 = cx - w / 2 - pad[0], cy - h / 2 - pad[1]
    bgc = tuple(int(v * alpha) for v in bg)
    d.rounded_rectangle([x0 * SS, y0 * SS, (cx + w / 2 + pad[0]) * SS, (cy + h / 2 + pad[1]) * SS],
                        radius=14 * SS, fill=bgc + (int(235 * alpha),))
    d.text((cx * SS, cy * SS), s, font=font, fill=fg + (int(255 * alpha),), anchor='mm')

def label(ov, cxy, s, col, a, dy=0, dx=0):
    if a <= 0: return
    d = ImageDraw.Draw(ov)
    x, y = cxy[0] + dx, cxy[1] + dy
    if dx or dy:
        d.line([cxy[0] * SS, cxy[1] * SS, x * SS, y * SS], fill=col + (int(255 * a),), width=3 * SS)
        d.ellipse([(cxy[0] - 5) * SS, (cxy[1] - 5) * SS, (cxy[0] + 5) * SS, (cxy[1] + 5) * SS], fill=col + (int(255 * a),))
    pill(d, x, y, s, F(FX, 30), (10, 16, 36), col, a)

def bars(ov, t0, t, rows, title):
    """info card: rows = [(label, value, color, display)]"""
    a = fade(t, t0, 0.3)
    if a <= 0: return
    d = ImageDraw.Draw(ov)
    x0, x1, y0, y1 = 70, W - 70, 1250, 1520
    d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=28 * SS,
                        fill=(12, 22, 52, int(232 * a)), outline=GOLD + (int(255 * a),), width=3 * SS)
    d.text(((x0 + 34) * SS, (y0 + 44) * SS), title, font=F(FX, 34), fill=GOLD + (int(255 * a),), anchor='lm')
    vmax = max(r[1] for r in rows)
    grow = ease((t - t0 - 0.15) / 0.9)
    for i, (lab, v, col, disp) in enumerate(rows):
        yy = y0 + 112 + i * 92
        d.text(((x0 + 34) * SS, yy * SS), lab, font=F(FX, 28), fill=WHITE + (int(255 * a),), anchor='lm')
        bx0, bx1 = x0 + 340, x1 - 40
        bw = (bx1 - bx0) * v / vmax * grow
        d.rounded_rectangle([bx0 * SS, (yy - 24) * SS, bx1 * SS, (yy + 24) * SS], radius=12 * SS,
                            fill=(30, 44, 86, int(255 * a)))
        if bw > 4:
            d.rounded_rectangle([bx0 * SS, (yy - 24) * SS, (bx0 + bw) * SS, (yy + 24) * SS], radius=12 * SS,
                                fill=col + (int(255 * a),))
        d.text(((bx1 - 14) * SS, yy * SS), disp, font=F(FB, 34), fill=WHITE + (int(255 * a),), anchor='rm',
               stroke_width=2 * SS, stroke_fill=(8, 14, 34))

TITLE_F = F(FB, 66)
def frame(t):
    m = morph_amt(t)
    zoom = 1.0 + 0.05 * (0.5 - 0.5 * math.cos(2 * math.pi * t / END))  # slow breathe, equal at 0 and END
    img = BG.copy()
    d = ImageDraw.Draw(img)
    cpos = draw_map(d, t, zoom, m)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    # title block (persistent)
    od.text((W / 2 * SS, 200 * SS), 'IF THE MAP WAS', font=TITLE_F, fill=WHITE, anchor='mm')
    od.text((W / 2 * SS, 278 * SS), 'DRAWN BY PEOPLE', font=TITLE_F, fill=GOLD, anchor='mm')
    od.text((W / 2 * SS, 340 * SS), 'Population: World Bank 2023  |  Map: Natural Earth', font=F(FI, 24), fill=MUTED, anchor='mm')
    # state chip
    chip = 'REAL MAP: LAND AREA' if m < 0.5 else 'SIZE = NUMBER OF PEOPLE'
    pill(od, W / 2, 440, chip, F(FX, 30), (10, 16, 36), (200, 210, 235) if m < 0.5 else GOLD, 1.0)
    # hook (start + loop end)
    ha = max(1 - fade(t, S[0][1] - 0.2, 0.4), fade(t, END - 0.75, 0.4))
    if ha > 0:
        pill(od, W / 2, 1180, 'BIGGEST COUNTRY?', F(FB, 54), (10, 16, 36), RED, ha, pad=(26, 16))
    # labels
    if t < MORPH0 + 0.2:
        label(ov, cpos('RUS'), 'RUSSIA  #1 BY AREA', RED, fade(t, 0, 0.01) * (1 - fade(t, MORPH0 - 0.2, 0.3)), dy=-150, dx=40)
    if S[2][0] - 0.2 < t < S[3][0] + 0.1:
        a = fade(t, S[2][0] - 0.2) * (1 - fade(t, S[3][0] - 0.2, 0.3))
        label(ov, cpos('RUS'), 'RUSSIA  144M', RED, a, dy=-150, dx=60)
        label(ov, cpos('CAN'), 'CANADA  40M', RED, a, dy=-150, dx=40)
    if S[3][0] - 0.2 < t < S[4][0] + 0.1:
        a = fade(t, S[3][0] - 0.2) * (1 - fade(t, S[4][0] - 0.2, 0.3))
        label(ov, cpos('CHN'), 'CHINA  1.41B', GOLD, a, dy=-170, dx=70)
        label(ov, cpos('IND'), 'INDIA  1.44B', GOLD, a, dy=150, dx=-60)
        bars(ov, S[3][0] + 1.2, t, [('INDIA + CHINA', 35.3, GOLD, '35%'), ('REST OF WORLD', 64.7, (110, 130, 180), '65%')],
             'SHARE OF ALL PEOPLE ON EARTH')
    if S[4][0] - 0.2 < t < S[5][0] + 0.1:
        a = fade(t, S[4][0] - 0.2) * (1 - fade(t, S[5][0] - 0.2, 0.3))
        label(ov, cpos('BGD'), 'BANGLADESH  171M', CYAN, a, dy=150, dx=90)
        label(ov, cpos('RUS'), 'RUSSIA  144M', RED, a, dy=-150, dx=60)
        if t < S[5][0] - 0.1:
            bars(ov, S[4][0] + 0.3, t, [('BANGLADESH', 171.5, CYAN, '171M'), ('RUSSIA', 143.8, RED, '144M')], 'PEOPLE  (2023)')
    if S[5][0] - 0.2 < t < S[6][0] + 0.1:
        a = fade(t, S[5][0] - 0.2) * (1 - fade(t, S[6][0] - 0.2, 0.3))
        label(ov, cpos('NGA'), 'NIGERIA  228M', GREEN, a, dy=160, dx=-40)
        if t < S[6][0] - 0.1:
            bars(ov, S[5][0] + 0.3, t, [('NIGERIA', 227.9, GREEN, '228M'), ('RUSSIA + CANADA', 183.9, RED, '184M')], 'PEOPLE  (2023)')
    if S[6][0] - 0.1 < t < END - 0.75:
        a = fade(t, S[6][0]) * (1 - fade(t, END - 0.95, 0.3))
        pill(od, W / 2, 1300, 'WHERE IS YOUR COUNTRY?', F(FB, 50), (10, 16, 36), GOLD, a, pad=(26, 16))
        pill(od, W / 2, 1400, 'TELL ME IN THE COMMENTS', F(FX, 34), WHITE, (30, 44, 86), a)
    img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
    return img.resize((W, H), Image.LANCZOS)

if __name__ == '__main__':
    out = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == '--frames':
        for ts in sys.argv[4].split(','):
            frame(float(ts)).save(out.replace('.mp4', '_%s.jpg' % ts), quality=90)
        print('END', END, 'S', S)
        sys.exit()
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print('done', out, n, END)
