"""Ball arena "kim oxirgi qoladi?" — our own physics simulation (generic format, own code & graphics).
Each ball bounces inside a circle; every wall hit adds a string from the ball to the hit point.
If another ball crosses a string, the string is cut. A ball that has had strings and drops to 0 is out.
Usage: python3 arena.py config.json out.mp4
config: {"title": "...", "subtitle": "...", "seed": 7, "teams": [{"name": "NAVBAHOR", "short": "NAV", "color": [40,170,90]}, ...]}
"""
import sys, json, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
CX, CY, R = 540, 1000, 470
BR = 62
FT = '/usr/share/fonts/opentype/inter/Inter-%s.otf'
def F(w, s): return ImageFont.truetype(FT % w, int(s))
cfg = json.load(open(sys.argv[1])); out = sys.argv[2]
rng = random.Random(cfg.get('seed', 7))
teams = cfg['teams']
balls = []
HITS = []; FR = [0]
for i, t in enumerate(teams):
    a = 2 * math.pi * i / len(teams) + rng.random() * 0.5
    sp = 8.0
    d = rng.random() * 2 * math.pi
    balls.append(dict(t=t, x=CX + 200 * math.cos(a), y=CY + 200 * math.sin(a), vx=sp * math.cos(d), vy=sp * math.sin(d),
                      strings=[], alive=True, had=False, out_at=None))
MAXT = cfg.get('max_seconds', 55)
GRACE = cfg.get('grace', 10)

def seg_point_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay; L = dx * dx + dy * dy or 1
    u = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + u * dx), py - (ay + u * dy))

def step():
    al = [b for b in balls if b['alive']]
    for b in al:
        b['x'] += b['vx']; b['y'] += b['vy']
        dx, dy = b['x'] - CX, b['y'] - CY; dist = math.hypot(dx, dy)
        if dist > R - BR:
            nx, ny = dx / dist, dy / dist
            dot = b['vx'] * nx + b['vy'] * ny
            b['vx'] -= 2 * dot * nx; b['vy'] -= 2 * dot * ny
            ang = rng.uniform(-0.25, 0.25); c, s = math.cos(ang), math.sin(ang)
            b['vx'], b['vy'] = b['vx'] * c - b['vy'] * s, b['vx'] * s + b['vy'] * c
            b['x'], b['y'] = CX + nx * (R - BR), CY + ny * (R - BR)
            base = math.atan2(ny, nx)
            for k in range(-3, 4):
                aa = base + k * 0.035
                b['strings'].append((CX + math.cos(aa) * R, CY + math.sin(aa) * R))
            b['had'] = True; HITS.append(FR[0])
            del b['strings'][:-260]
    # ball-ball collisions
    for i in range(len(al)):
        for j in range(i + 1, len(al)):
            a, b = al[i], al[j]
            dx, dy = b['x'] - a['x'], b['y'] - a['y']; d = math.hypot(dx, dy)
            if 0 < d < 2 * BR:
                nx, ny = dx / d, dy / d
                p = (a['vx'] - b['vx']) * nx + (a['vy'] - b['vy']) * ny
                if p > 0:
                    a['vx'] -= p * nx; a['vy'] -= p * ny; b['vx'] += p * nx; b['vy'] += p * ny
                ov = (2 * BR - d) / 2
                a['x'] -= nx * ov; a['y'] -= ny * ov; b['x'] += nx * ov; b['y'] += ny * ov
    # cut strings crossed by other balls
    for b in al:
        keep = []
        for (sx, sy) in b['strings']:
            cut = any(o is not b and seg_point_dist(o['x'], o['y'], b['x'], b['y'], sx, sy) < BR * 0.55 for o in al)
            if not cut: keep.append((sx, sy))
        b['strings'] = keep

def badge(t, r):
    im = Image.new('RGBA', (r * 4, r * 4), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = tuple(t['color'])
    d.ellipse((0, 0, r * 4 - 1, r * 4 - 1), fill=c + (255,), outline=(255, 255, 255, 255), width=10)
    if t.get('color2'):
        d.pieslice((0, 0, r * 4 - 1, r * 4 - 1), 200, 340, fill=tuple(t['color2']) + (255,))
        d.ellipse((0, 0, r * 4 - 1, r * 4 - 1), outline=(255, 255, 255, 255), width=10)
    txt = t['short']; f = F('Black', r * 1.25)
    d.text((r * 2, r * 2), txt, font=f, fill=(255, 255, 255, 255), anchor='mm', stroke_width=6, stroke_fill=(0, 0, 0, 200))
    return im.resize((r * 2, r * 2), Image.LANCZOS)
BADGES = [badge(b['t'], BR) for b in balls]

def render(t, winner=None):
    im = Image.new('RGB', (W, H), (4, 6, 12)); L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.ellipse((CX - R, CY - R, CX + R, CY + R), outline=(235, 235, 245, 255), width=6)
    for b in balls:
        if not b['alive']: continue
        c = tuple(b['t']['color'])
        for (sx, sy) in b['strings']:
            d.line((b['x'], b['y'], sx, sy), fill=c + (170,), width=2)
    glow = L.filter(ImageFilter.GaussianBlur(6))
    im.paste(glow, (0, 0), glow); im.paste(L, (0, 0), L)
    for b, bd in zip(balls, BADGES):
        if b['alive']: im.paste(bd, (int(b['x'] - BR), int(b['y'] - BR)), bd)
    d2 = ImageDraw.Draw(im)
    d2.text((W / 2, 230), cfg['title'], font=F('Black', 64), fill=(255, 246, 230), anchor='mm')
    if cfg.get('subtitle'): d2.text((W / 2, 310), cfg['subtitle'], font=F('Bold', 38), fill=(255, 196, 64), anchor='mm')
    # legend with string counts
    x0 = W / 2 - (len(balls) - 1) * 170
    for i, b in enumerate(balls):
        x = x0 + i * 340 / (1 if len(balls) < 4 else 1.4)
        c = tuple(b['t']['color']); a = 255 if b['alive'] else 90
        d2.text((x, 1560), b['t']['name'], font=F('ExtraBold', 34), fill=c if b['alive'] else (90, 90, 90), anchor='mm')
        d2.text((x, 1610), str(len(b['strings'])) if b['alive'] else 'X', font=F('Black', 50), fill=(255, 255, 255) if b['alive'] else (150, 60, 60), anchor='mm')
    if winner is not None:
        d2.rounded_rectangle((140, 1690, 940, 1810), 60, fill=(255, 196, 64))
        d2.text((W / 2, 1750), f"G'OLIB: {winner['t']['name']}", font=F('Black', 56), fill=(10, 16, 36), anchor='mm')
    d2.text((40, H - 40), cfg.get('note', 'Tasodifiy fizik simulyatsiya — haqiqiy natija emas'), font=F('Medium', 26), fill=(170, 170, 180), anchor='ls')
    return im

p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
f = 0; winner = None; end_f = None
while True:
    t = f / FPS
    if winner is None:
        step()
        for b in balls:
            if b['alive'] and b['had'] and t > GRACE and not b['strings']:
                b['alive'] = False; b['out_at'] = t
        alive = [b for b in balls if b['alive']]
        if len(alive) == 1 or t > MAXT:
            winner = max(alive, key=lambda b: len(b['strings'])); end_f = f + 3 * FPS
    else:
        step()
    FR[0] = f
    p.stdin.write(render(t, winner).tobytes()); f += 1
    if end_f and f >= end_f: break
p.stdin.close(); p.wait()
print('winner', winner['t']['name'], 'at', round(f / FPS, 1))
json.dump({'hits': [h / FPS for h in HITS], 'dur': f / FPS}, open(out + '.hits.json', 'w'))
