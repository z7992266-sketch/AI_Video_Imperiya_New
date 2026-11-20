import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, 'frames'); os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/opentype/inter/'
def F(w, s): return ImageFont.truetype(FONT + f'Inter-{w}.otf', s)
BG1 = np.array([10, 18, 38], np.float32); BG2 = np.array([4, 8, 20], np.float32)
WHITE = (240, 244, 255); GOLD = (255, 200, 70); MUTED = (150, 165, 200)

EV = json.load(open(os.path.join(D, 'events.json')))  # timing in seconds
TOTAL = EV['total']

world = json.load(open(os.path.join(D, 'world.json')))['features']
C = {  # a3: (name, area %, population %, colour)
    'KAZ': ("Qozog'iston", 68, 25, (64, 156, 255)),
    'UZB': ("O'zbekiston", 11, 45, (255, 190, 60)),
    'TKM': ("Turkmaniston", 12, 9, (80, 205, 160)),
    'KGZ': ("Qirg'iziston", 5, 9, (240, 100, 120)),
    'TJK': ("Tojikiston", 4, 13, (170, 120, 255)),
}
NEIGH = ['RUS', 'CHN', 'AFG', 'IRN', 'MNG', 'PAK', 'AZE']
KX = math.cos(math.radians(43))

def rings(g):
    if g['type'] == 'Polygon': return [np.array(g['coordinates'][0], float)]
    return [np.array(p[0], float) for p in g['coordinates']]
GEO = {}
for f in world:
    a3 = f['properties']['a3']
    if a3 in C or a3 in NEIGH:
        GEO[a3] = [r for r in rings(f['geometry']) if len(r) > 3]
        if a3 in C:  # drop tiny islands etc
            GEO[a3] = sorted(GEO[a3], key=len, reverse=True)[:3]

def proj(r): return np.stack([r[:, 0] * KX, r[:, 1]], 1)
P = {a: [proj(r) for r in rs] for a, rs in GEO.items()}
def poly_area(p):
    x, y = p[:, 0], p[:, 1]; return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
def pcen(p):
    x, y = p[:, 0], p[:, 1]; x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cr = x * y1 - x1 * y; A = cr.sum() / 2
    return np.array([((x + x1) * cr).sum() / (6 * A), ((y + y1) * cr).sum() / (6 * A)])
def centroid(ps):
    big = max(ps, key=poly_area); return pcen(big)
LABEL = {'KAZ': (67.5, 48.3), 'UZB': (63.6, 41.6), 'TKM': (58.8, 39.2), 'KGZ': (74.8, 41.6), 'TJK': (71.0, 38.7)}
CEN = {a: centroid(P[a]) for a in C}
AREA = {a: sum(poly_area(p) for p in P[a]) for a in C}
SC = {a: math.sqrt(C[a][2] / C[a][1]) for a in C}

# relax target centroids so scaled countries don't overlap
tgt = {a: CEN[a].copy() for a in C}
rad = {a: math.sqrt(AREA[a] * SC[a] ** 2 / math.pi) * 1.0 for a in C}
grp = np.mean([CEN[a] for a in C], 0)
for it in range(800):
    for a in C:
        for b in C:
            if a >= b: continue
            d = tgt[b] - tgt[a]; dist = np.linalg.norm(d) + 1e-6; need = rad[a] + rad[b]
            if dist < need:
                push = (need - dist) / 2 * d / dist
                wa = 1 if a != 'UZB' else 0.6; wb = 1 if b != 'UZB' else 0.6
                tgt[a] -= push * wa; tgt[b] += push * wb
    for a in C:
        tgt[a] += (CEN[a] - tgt[a]) * 0.002

# view: fit real map; cartogram view computed similarly
def bbox(points):
    p = np.vstack(points); return p[:, 0].min(), p[:, 1].min(), p[:, 0].max(), p[:, 1].max()
def view_for(bb, frac=0.92, cy=H * 0.47):
    cx0 = (bb[0] + bb[2]) / 2; cy0 = (bb[1] + bb[3]) / 2
    s = min(W * frac / (bb[2] - bb[0]), H * 0.42 / (bb[3] - bb[1]))
    return (cx0, cy0, s, cy)
V_REAL = view_for(bbox([p for a in C for p in P[a]]))
cart_pts = [ (p - CEN[a]) * SC[a] + tgt[a] for a in C for p in P[a] ]
V_CART = view_for(bbox(cart_pts), 0.88)

def ease(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t

_g = np.linspace(0, 1, H)[:, None, None]
BGIMG = Image.fromarray(np.broadcast_to(BG1 * (1 - _g) + BG2 * _g, (H, W, 3)).clip(0, 255).astype(np.uint8))
rng = np.random.default_rng(3); STARS = rng.random((140, 3))

def text_c(d, txt, y, font, fill, a=1.0, x=None, anchor='mm', stroke=3):
    if a <= 0: return
    al = int(255 * min(1, a))
    d.text((W / 2 if x is None else x, y), txt, font=font, fill=fill + (al,), anchor=anchor,
           stroke_width=stroke, stroke_fill=(0, 0, 0, int(al * 0.8)))

def morph_amount(t):
    m = ease((t - EV['morph0']) / 1.6)
    if t > EV['back0']: m *= 1 - ease((t - EV['back0']) / 1.2)
    return m

def frame(t):
    im = BGIMG.copy(); ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for x, y, b in STARS:
        a = int(40 + 60 * b * (0.6 + 0.4 * math.sin(t * 1.5 + x * 9)))
        d.point((x * W, y * H), fill=(200, 210, 255, a))
    m = morph_amount(t)
    zoom = 1 + 0.04 * math.sin(t * 0.35)
    v = tuple(lerp(V_REAL[i], V_CART[i], m) for i in range(4))
    cx0, cy0, s, cys = v; s *= zoom
    def scr(p): return list(zip(W / 2 + (p[:, 0] - cx0) * s, cys - (p[:, 1] - cy0) * s))
    # neighbours (context), fade out with morph
    na = int(70 * (1 - m))
    if na > 3:
        for a in NEIGH:
            for p in P.get(a, []):
                d.polygon(scr(p), fill=(30, 42, 70, na), outline=(70, 85, 120, na))
    hi = EV.get('hi', {})
    order = sorted(C, key=lambda a: -AREA[a] * lerp(1, SC[a] ** 2, m))
    for a in order:
        sc = lerp(1, SC[a], m); off = lerp(CEN[a], tgt[a], m)
        col = C[a][3]
        glow = 0
        for h0, h1, who in hi.values() if isinstance(hi, dict) else []:
            if who == a and h0 <= t <= h1: glow = min(ease((t - h0) / .4), ease((h1 - t) / .4))
        for p in P[a]:
            q = (p - CEN[a]) * sc + off
            pts = scr(q)
            fill = tuple(int(c * (0.78 + 0.22 * glow)) for c in col) + (235,)
            d.polygon(pts, fill=fill, outline=(255, 255, 255, 200))
            if glow > 0: d.line(pts + [pts[0]], fill=(255, 245, 200, int(255 * glow)), width=6)
    im.paste(ov, (0, 0), ov)
    d = ImageDraw.Draw(im, 'RGBA')
    # labels
    la = ease((t - EV['labels_area']) / .5)
    for a in C:
        sc = lerp(1, SC[a], m); off = lerp(CEN[a], tgt[a], m)
        lp = np.array([LABEL[a][0] * KX, LABEL[a][1]])
        cx, cy = scr(np.array([(lp - CEN[a]) * sc + off]))[0]
        pct = C[a][1] if m < 0.5 else C[a][2]
        big = a in ('UZB', 'KAZ')
        alpha = la * (1 - min(1, abs(m - 0.5) * 2) * 0 if True else 1)
        alpha = la * (abs(m - 0.5) * 2) if 0.05 < m < 0.95 else la
        if t > EV['back0']: alpha *= 1 - ease((t - EV['back0']) / .5)
        if a in ('KGZ', 'TJK') and m < 0.5: continue  # too small on the real map
        text_c(d, C[a][0], cy - (28 if big else 20), F('Bold', 40 if big else 30), WHITE, alpha, x=cx)
        text_c(d, f"{pct} %", cy + (26 if big else 18), F('Black', 58 if big else 40), GOLD if a == 'UZB' else WHITE, alpha, x=cx)
    # title
    title = "XARITANI\nODAMGA QARAB\nCHIZSAK?"
    ta = max(1 - ease((t - EV['title_out']) / .5), ease((t - (TOTAL - 1.0)) / .6))
    if ta > 0:
        d.multiline_text((W / 2, 300), title, font=F('Black', 96), fill=WHITE + (int(255 * ta),), anchor='mm',
                         align='center', spacing=6, stroke_width=4, stroke_fill=(0, 0, 0, int(200 * ta)))
    hdr_a = ease((t - EV['title_out']) / .5) * (1 - ease((t - (TOTAL - 1.0)) / .6))
    if hdr_a > 0:
        mode = 'ODAM SONI' if m >= 0.5 else 'YER MAYDONI'
        text_c(d, 'MARKAZIY OSIYO', 190, F('SemiBold', 40), MUTED, hdr_a)
        text_c(d, mode + ' BO‘YICHA', 265, F('Black', 82), GOLD if m >= .5 else (120, 190, 255), hdr_a)
    text_c(d, 'Aholi: milliy statistika, 2025 · Chegaralar: Natural Earth', 335 if hdr_a > 0 else 470,
           F('Medium', 28), MUTED, max(hdr_a, 0.0) * 0.9)
    # bottom card
    ca = ease((t - EV['card0']) / .5) * (1 - ease((t - EV['q0']) / .4))
    if ca > 0:
        y0 = 1390
        d.rounded_rectangle([70, y0, W - 70, y0 + 200], 32, fill=(12, 20, 44, int(225 * ca)), outline=(90, 110, 160, int(200 * ca)), width=2)
        for i, a in enumerate(['UZB', 'KAZ']):
            yy = y0 + 55 + i * 85
            text_c(d, C[a][0], yy, F('Bold', 38), WHITE, ca, x=110, anchor='lm', stroke=0)
            for j, (lab, val, colr) in enumerate([('YER', C[a][1], (120, 190, 255)), ('ODAM', C[a][2], GOLD)]):
                bx = 470 + j * 270; bw = 200
                text_c(d, lab, yy - 20, F('SemiBold', 22), MUTED, ca, x=bx, anchor='lm', stroke=0)
                d.rounded_rectangle([bx, yy, bx + bw, yy + 16], 8, fill=(40, 50, 80, int(255 * ca)))
                fillw = bw * min(1, val / 70) * ease((t - EV['card0'] - 0.3) / 1.0)
                d.rounded_rectangle([bx, yy, bx + max(16, fillw), yy + 16], 8, fill=colr + (int(255 * ca),))
                text_c(d, f'{val}%', yy + 8, F('Black', 30), colr, ca, x=bx + bw + 12, anchor='lm', stroke=0)
    # x4 pop
    if EV['x4'] <= t <= EV['x4'] + 2.6:
        k = ease((t - EV['x4']) / .35) * (1 - ease((t - EV['x4'] - 2.2) / .4))
        text_c(d, '×4', 1260, F('Black', int(120 + 30 * (1 - ease((t - EV['x4']) / .35)))), GOLD, k)
    # question
    qa = ease((t - EV['q0']) / .5)
    if qa > 0 and t < TOTAL - 0.3:
        d.rounded_rectangle([90, 1420, W - 90, 1560], 30, fill=(255, 200, 70, int(235 * qa)))
        text_c(d, '20 yildan keyin qanday bo‘ladi?', 1490, F('Black', 46), (20, 20, 30), qa, stroke=0)
    return im

if __name__ == '__main__':
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for i in range(a, b):
        frame(i / FPS).save(os.path.join(OUT, f'f{i:05d}.jpg'), quality=92)
