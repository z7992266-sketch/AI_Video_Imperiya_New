"""OUJ EN 20261124 — "If the map was drawn by money" (GDP 2024) — silent mp4 renderer.
usage: python3 gdpmap.py segs.json out.mp4 [--frames t1,t2,...]"""
import json, math, sys, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
FONTS = '/home/claude/rw/render/fonts/'
W, H, FPS, SS = 1080, 1920, 30, 2
NAVY0, NAVY1 = (7, 13, 34), (16, 30, 66)
GOLD = (242, 181, 61); LAND = (52, 74, 128); NODATA = (40, 52, 84)
RED = (231, 84, 84); CYAN = (64, 214, 230); GREEN = (98, 214, 120)
WHITE = (240, 244, 255); MUTED = (150, 165, 205)
def F(name, size): return ImageFont.truetype(FONTS + name, size * SS)
FB = 'InterDisplay-Black.otf'; FX = 'InterDisplay-ExtraBold.otf'; FI = 'Inter-Bold.otf'

# ---------------- data (World Bank 2024, IMF WEO 2024 fallback) ----------------
wb = json.load(open(os.path.join(D, 'oujen1124_wbgdp.json')))[1]
G = {r['countryiso3code']: r['value'] for r in wb if r['value'] and r['date'] == '2023'}
G.update({r['countryiso3code']: r['value'] for r in wb if r['value'] and r['date'] == '2024'})
imf = json.load(open(os.path.join(D, 'oujen1124_imfgdp.json')))['values']['NGDPD']
for k, v in imf.items():
    if k not in G and v.get('2024'): G[k] = v['2024'] * 1e9
ALIAS = {'SDS': 'SSD', 'KOS': 'XKX', 'PSX': 'PSE', 'SOL': 'SOM', 'SAH': None, 'CYN': None, 'KAS': None}
WORLD = G['WLD']

MW = 1060; PX = MW / 360.0; LAT0, LAT1 = 84.0, -57.0
MH = (LAT0 - LAT1) * PX; MAP_CY = 800; MX0 = (W - MW) / 2; MY0 = MAP_CY - MH / 2
def proj_arr(a): return np.stack([MX0 + (a[:, 0] + 180) * PX, MY0 + (LAT0 - a[:, 1]) * PX], 1)
def proj(lon, lat): return MX0 + (lon + 180) * PX, MY0 + (LAT0 - lat) * PX
def ring_ac(pts):
    x, y = pts[:, 0], pts[:, 1]; x1, y1 = np.roll(x, -1), np.roll(y, -1)
    c = x * y1 - x1 * y; a = c.sum() / 2
    if abs(a) < 1e-9: return 0.0, pts.mean(0)
    return abs(a), np.array([((x + x1) * c).sum() / (6 * a), ((y + y1) * c).sum() / (6 * a)])

countries = []
for f in json.load(open(os.path.join(D, 'geo.json'))):
    if f['cont'] in ('Antarctica',) or f['a3'] in ('ATA', 'ATF', 'HMD', 'SGS'): continue
    iso = ALIAS.get(f['a3'], f['a3'])
    polys = f['coordinates'] if f['type'] == 'MultiPolygon' else [f['coordinates']]
    rings = []; A = 0; C = np.zeros(2); km = 0
    for poly in polys:
        o = np.array(poly[0], float)
        if len(o) < 4: continue
        ad, cd = ring_ac(o)
        km += ad * 111.32 ** 2 * math.cos(math.radians(cd[1]))
        p = proj_arr(o)
        # simplify: drop points closer than 0.6 px
        keep = [0]
        for i in range(1, len(p)):
            if np.abs(p[i] - p[keep[-1]]).max() > 0.6: keep.append(i)
        p = p[keep]
        if len(p) < 3: continue
        a, c = ring_ac(p); A += a; C += a * c; rings.append(p)
    if not rings or km <= 0: continue
    C = C / A if A else rings[0].mean(0)
    countries.append(dict(name=f['name'], iso=iso or f['a3'], cont=f['cont'], rings=rings, km2=km, c=C,
                          gdp=G.get(iso) if iso else None))
for c in countries:
    c['parts'] = []
    for r in c['rings']:
        a, cc = ring_ac(r)
        c['parts'].append((r, cc if np.linalg.norm(cc - c['c']) > 60 else c['c']))
BY = {c['iso']: c for c in countries}
REFD = (BY['USA']['gdp'] / BY['USA']['km2']) / 1.6 ** 2   # anchor: USA grows 1.6x in width
for c in countries:
    c['k'] = min(math.sqrt(c['gdp'] / c['km2'] / REFD), 2.4) if c['gdp'] else 0.45
    c['k'] = max(c['k'], 0.22)
AFRICA = sum({c['iso']: c['gdp'] or 0 for c in countries if c['cont'] == 'Africa'}.values())
print('AFRICA', AFRICA / 1e12, 'USA share', BY['USA']['gdp'] / WORLD, 'US+CN', (BY['USA']['gdp'] + BY['CHN']['gdp']) / WORLD, file=sys.stderr)

# ---------------- timeline ----------------
segs = json.load(open(sys.argv[1]))['segments']
VO = 0.35
S = [(s['s'] + VO, s['e'] + VO) for s in segs]
END = S[-1][1] + 0.9
MORPH0, MORPH1 = S[1][0] + 0.9, S[1][1] + 1.0
BACK0, BACK1 = S[6][0] + 0.1, S[6][0] + 1.5
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)
def back_out(x):
    x = min(1, max(0, x)); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def morph_amt(t):
    if t < MORPH0: return 0.0
    if t < MORPH1: return ease((t - MORPH0) / (MORPH1 - MORPH0))
    if t < BACK0: return 1.0
    return 1 - ease((t - BACK0) / (BACK1 - BACK0))
def mix(a, b, u): return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
def fade(t, t0, d=0.35): return ease((t - t0) / d)
def win(t, a, b, d=0.3): return fade(t, a, d) * (1 - fade(t, b - d, d))

def make_bg():
    y = np.linspace(0, 1, H)[:, None]; bg = np.zeros((H, W, 3), np.float32)
    for i in range(3): bg[:, :, i] = NAVY1[i] * (1 - y) * 0.9 + NAVY0[i] * (0.4 + 0.6 * y)
    yy, xx = np.mgrid[0:H, 0:W]
    g = np.exp(-(((xx - W / 2) / 620.0) ** 2 + ((yy - MAP_CY) / 420.0) ** 2))
    bg += g[:, :, None] * np.array([18, 30, 60], np.float32)
    img = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).resize((W * SS, H * SS))
    d = ImageDraw.Draw(img)
    for lon in range(-180, 181, 30):
        x, _ = proj(lon, 0)
        for lat in np.arange(LAT1, LAT0, 2.0): d.point((x * SS, proj(0, lat)[1] * SS), fill=(40, 60, 110))
    for lat in range(-30, 90, 30):
        yv = proj(0, lat)[1]
        for lon in np.arange(-180, 180, 2.0): d.point((proj(lon, 0)[0] * SS, yv * SS), fill=(40, 60, 110))
    return img
BG = make_bg()

def country_color(c, t):
    iso = c['iso']; col = LAND if c['gdp'] else NODATA
    if c['cont'] == 'Africa':
        if t < S[1][0] + 0.4: col = mix(col, RED, fade(t, -0.1, 0.01) * (0.75 + 0.25 * math.sin(t * 5)) * (1 - fade(t, S[1][0], 0.4)))
        if S[4][0] - 0.2 < t < S[5][0]: col = mix(col, RED, win(t, S[4][0] - 0.2, S[5][0]))
        if t > END - 0.8: col = mix(col, RED, fade(t, END - 0.8, 0.4))
    if iso == 'USA' and S[2][0] - 0.2 < t < BACK0: col = mix(col, GOLD, fade(t, S[2][0] - 0.2))
    if iso == 'CHN' and S[3][0] - 0.2 < t < BACK0: col = mix(col, GOLD, fade(t, S[3][0] - 0.2))
    if iso == 'JPN' and S[4][0] - 0.2 < t < BACK0: col = mix(col, CYAN, fade(t, S[4][0] - 0.2))
    if iso == 'RUS' and S[5][0] - 0.2 < t < S[6][0] + 0.2: col = mix(col, RED, win(t, S[5][0] - 0.2, S[6][0] + 0.2))
    if iso == 'ITA' and S[5][0] - 0.2 < t < S[6][0] + 0.2: col = mix(col, GREEN, win(t, S[5][0] - 0.2, S[6][0] + 0.2))
    return col

ORDER = sorted(countries, key=lambda c: -c['km2'])
TOP = ['USA', 'CHN', 'JPN', 'ITA', 'RUS', 'DEU', 'GBR', 'FRA']
def camera(t):
    keys = [(0, 1.0, 0, 13.5), (S[5][0] - 0.3, 1.0, 0, 13.5), (S[5][0] + 0.7, 1.55, 45, 48),
            (S[6][0] - 0.1, 1.55, 45, 48), (S[6][0] + 0.8, 1.0, 0, 13.5), (999, 1.0, 0, 13.5)]
    for (t0, z0, lo0, la0), (t1, z1, lo1, la1) in zip(keys, keys[1:]):
        if t0 <= t <= t1:
            u = ease((t - t0) / max(1e-6, t1 - t0)) if (z0, lo0, la0) != (z1, lo1, la1) else 0
            return z0 + (z1 - z0) * u, np.array(proj(lo0 + (lo1 - lo0) * u, la0 + (la1 - la0) * u))
    return 1.0, np.array(proj(0, 13.5))

def draw_map(d, t, zoom, m):
    cz, cc = camera(t); zoom *= cz; zc = np.array([W / 2, MAP_CY])
    def tf(pts, center, k): return (zc + (center + (pts - center) * k - cc) * zoom) * SS
    # USA overshoot "explode" pop
    for c in [c for c in ORDER if c['iso'] not in TOP] + [c for c in ORDER if c['iso'] in TOP]:
        k = 1 + (c['k'] - 1) * m
        if c['iso'] == 'USA' and S[2][0] - 0.2 < t < S[2][0] + 0.8:
            k *= 1 + 0.10 * math.sin(math.pi * ease((t - S[2][0] + 0.2) / 1.0))
        col = country_color(c, t); edge = mix(col, WHITE, 0.22)
        for r, cen in c['parts']:
            p = tf(r, cen, k)
            if (p[:, 0].max() - p[:, 0].min()) < 1.5 and (p[:, 1].max() - p[:, 1].min()) < 1.5: continue
            d.polygon([tuple(q) for q in p], fill=col, outline=edge, width=max(1, int(1.1 * SS)))
    def pos(iso, lon=None, lat=None):
        base = BY[iso]['c'] if lon is None else np.array(proj(lon, lat))
        return tuple(zc + (base - cc) * zoom)
    return pos

def pill(d, cx, cy, s, font, fg, bg, alpha=1.0, pad=(18, 10), scale=1.0):
    if alpha <= 0: return
    bb = d.textbbox((0, 0), s, font=font, anchor='lt'); w, h = (bb[2] - bb[0]) / SS, (bb[3] - bb[1]) / SS
    x0, y0 = cx - w / 2 - pad[0], cy - h / 2 - pad[1]
    d.rounded_rectangle([x0 * SS, y0 * SS, (cx + w / 2 + pad[0]) * SS, (cy + h / 2 + pad[1]) * SS],
                        radius=14 * SS, fill=bg + (int(235 * alpha),))
    d.text((cx * SS, cy * SS), s, font=font, fill=fg + (int(255 * alpha),), anchor='mm')

def label(ov, cxy, s, col, a, dy=0, dx=0):
    if a <= 0: return
    d = ImageDraw.Draw(ov); x, y = cxy[0] + dx, cxy[1] + dy
    if dx or dy:
        d.line([cxy[0] * SS, cxy[1] * SS, x * SS, y * SS], fill=col + (int(255 * a),), width=3 * SS)
        d.ellipse([(cxy[0] - 6) * SS, (cxy[1] - 6) * SS, (cxy[0] + 6) * SS, (cxy[1] + 6) * SS], fill=col + (int(255 * a),))
    pill(d, x, y, s, F(FX, 30), (10, 16, 36), col, a)

def bars(ov, t0, t, rows, title, t1=None):
    a = fade(t, t0, 0.3) * (1 - fade(t, t1 - 0.3, 0.3) if t1 else 1)
    if a <= 0: return
    d = ImageDraw.Draw(ov)
    x0, x1, y0 = 70, W - 70, 1220
    y1 = y0 + 112 + len(rows) * 92 - 30
    sl = (1 - back_out((t - t0) / 0.5)) * 60
    y0 += sl; y1 += sl
    d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=28 * SS,
                        fill=(12, 22, 52, int(232 * a)), outline=GOLD + (int(255 * a),), width=3 * SS)
    d.text(((x0 + 34) * SS, (y0 + 44) * SS), title, font=F(FX, 32), fill=GOLD + (int(255 * a),), anchor='lm')
    vmax = max(r[1] for r in rows); grow = ease((t - t0 - 0.15) / 0.9)
    for i, (lab, v, col, fmt) in enumerate(rows):
        yy = y0 + 112 + i * 92
        d.text(((x0 + 34) * SS, yy * SS), lab, font=F(FX, 28), fill=WHITE + (int(255 * a),), anchor='lm')
        bx0, bx1 = x0 + 330, x1 - 40; bw = (bx1 - bx0) * v / vmax * grow
        d.rounded_rectangle([bx0 * SS, (yy - 24) * SS, bx1 * SS, (yy + 24) * SS], radius=12 * SS, fill=(30, 44, 86, int(255 * a)))
        if bw > 4:
            d.rounded_rectangle([bx0 * SS, (yy - 24) * SS, (bx0 + bw) * SS, (yy + 24) * SS], radius=12 * SS, fill=col + (int(255 * a),))
        d.text(((bx1 - 14) * SS, yy * SS), fmt(v * grow), font=F(FB, 34), fill=WHITE + (int(255 * a),), anchor='rm',
               stroke_width=2 * SS, stroke_fill=(8, 14, 34))

T = lambda v: '$%.1fT' % (v / 1e12)
T2 = lambda v: '$%.2fT' % (v / 1e12)
P = lambda v: '%d%%' % round(v)
US, CN, JP, RU, IT = (BY[i]['gdp'] for i in ('USA', 'CHN', 'JPN', 'RUS', 'ITA'))
USP = US / WORLD * 100; UCP = (US + CN) / WORLD * 100
TITLE_F = F(FB, 66)

def frame(t):
    m = morph_amt(t)
    zoom = 1.0 + 0.05 * (0.5 - 0.5 * math.cos(2 * math.pi * t / END))
    img = BG.copy(); d = ImageDraw.Draw(img)
    pos = draw_map(d, t, zoom, m)
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    od.text((W / 2 * SS, 200 * SS), 'IF THE MAP WAS', font=TITLE_F, fill=WHITE, anchor='mm')
    od.text((W / 2 * SS, 278 * SS), 'DRAWN BY MONEY', font=TITLE_F, fill=GOLD, anchor='mm')
    od.text((W / 2 * SS, 340 * SS), 'GDP 2024: World Bank, IMF  |  Map: Natural Earth', font=F(FI, 24), fill=MUTED, anchor='mm')
    chip = 'REAL MAP: LAND AREA' if m < 0.5 else 'SIZE = ECONOMY (GDP)'
    pill(od, W / 2, 430, chip, F(FX, 30), (10, 16, 36), (200, 210, 235) if m < 0.5 else GOLD, 1.0)
    # hook (start + loop end)
    ha = max(1 - fade(t, S[0][1] - 0.1, 0.4), fade(t, END - 0.75, 0.4))
    if ha > 0:
        pill(od, W / 2, 1230, 'AFRICA IS HUGE...', F(FB, 54), (10, 16, 36), RED, ha, pad=(26, 16))
        if t < S[0][1] + 0.3 and t > 1.6:
            pill(od, W / 2, 1340, 'OR IS IT?', F(FB, 44), WHITE, (30, 44, 86), ha * fade(t, 1.6, 0.3))
    if t < S[1][0] + 0.5 or t > END - 0.8:
        a = (1 - fade(t, S[1][0], 0.4)) if t < S[1][0] + 0.5 else fade(t, END - 0.8, 0.4)
        label(ov, pos('NGA', 20, 2), 'AFRICA  30M KM²', RED, a, dy=-170, dx=150)
    if S[1][0] + 0.3 < t < S[2][0]:
        a = win(t, S[1][0] + 0.3, S[2][0])
        pill(od, W / 2, 1260, 'SIZE = HOW MUCH IT EARNS', F(FB, 44), (10, 16, 36), GOLD, a, pad=(24, 14))
    if S[2][0] - 0.2 < t < S[3][0] + 0.1:
        a = win(t, S[2][0] - 0.2, S[3][0] + 0.1)
        label(ov, pos('USA'), 'USA  ' + T(US), GOLD, a, dy=-190, dx=40)
        bars(ov, S[2][0] + 0.6, t, [('USA', USP, GOLD, P), ('REST OF WORLD', 100 - USP, (110, 130, 180), P)],
             'SHARE OF WORLD GDP  (2024)', S[3][0] + 0.1)
    if S[3][0] - 0.2 < t < S[4][0] + 0.1:
        a = win(t, S[3][0] - 0.2, S[4][0] + 0.1)
        label(ov, pos('CHN'), 'CHINA  ' + T(CN), GOLD, a, dy=-200, dx=-30)
        bars(ov, S[3][0] + 0.5, t, [('USA + CHINA', UCP, GOLD, P), ('REST OF WORLD', 100 - UCP, (110, 130, 180), P)],
             'SHARE OF WORLD GDP  (2024)', S[4][0] + 0.1)
    if S[4][0] - 0.2 < t < S[5][0] + 0.1:
        a = win(t, S[4][0] - 0.2, S[5][0] + 0.1)
        label(ov, pos('JPN'), 'JAPAN  ' + T(JP), CYAN, a, dy=-200, dx=-60)
        label(ov, pos('NGA', 20, 2), 'ALL OF AFRICA', RED, a, dy=150, dx=-60)
        bars(ov, S[4][0] + 0.4, t, [('JAPAN', JP, CYAN, T), ('ALL OF AFRICA', AFRICA, RED, T)],
             'GDP 2024  (US DOLLARS)', S[5][0] + 0.1)
    if S[5][0] - 0.2 < t < S[6][0] + 0.2:
        a = win(t, S[5][0] - 0.2, S[6][0] + 0.2)
        label(ov, pos('RUS'), 'RUSSIA  ' + T2(RU), RED, a, dy=-170, dx=20)
        label(ov, pos('ITA'), 'ITALY  ' + T2(IT), GREEN, a, dy=170, dx=-60)
        bars(ov, S[5][0] + 0.4, t, [('ITALY', IT, GREEN, T2), ('RUSSIA', RU, RED, T2)], 'GDP 2024  (US DOLLARS)', S[6][0] + 0.2)
    if S[6][0] + 0.1 < t < END - 0.75:
        a = win(t, S[6][0] + 0.1, END - 0.75)
        pill(od, W / 2, 1290, 'WHERE IS YOUR COUNTRY?', F(FB, 50), (10, 16, 36), GOLD, a, pad=(26, 16))
        pill(od, W / 2, 1390, 'TELL ME IN THE COMMENTS', F(FX, 34), WHITE, (30, 44, 86), a)
    img = Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
    return img.resize((W, H), Image.LANCZOS)

if __name__ == '__main__':
    out = sys.argv[2]
    if len(sys.argv) > 3 and sys.argv[3] == '--frames':
        for ts in sys.argv[4].split(','):
            frame(float(ts)).save(out.replace('.mp4', '_%s.jpg' % ts), quality=88)
        print('END', END, 'S', S); sys.exit()
    n = int(END * FPS)
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                         stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print('done', out, n, END)
