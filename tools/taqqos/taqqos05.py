#!/usr/bin/env python3
"""Taqqos #5: O'zbekiston vs Rossiya — MOTION version (27 Oct 2026 update).
Every second moves: flag collision hook, counters, race bars, live scoreboard with flips,
moving background, whip-pan transitions with motion blur, full-screen winner + confetti,
loop-friendly last frame.  Raw RGB frames to stdout (1080x1920, 30 fps)."""
import math, sys, os, json, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "smart"))
import lib as L
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SAFE_B = int(H * 0.82)          # nothing below this (YouTube UI)
F = "/usr/share/fonts/opentype/inter/"
_fc = {}
def font(name, size):
    k = (name, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(F + name, max(8, int(size)))
    return _fc[k]
BLACK = "InterDisplay-Black.otf"; XB = "Inter-ExtraBold.otf"; B = "Inter-Bold.otf"; SB = "Inter-SemiBold.otf"; MD = "Inter-Medium.otf"

NAVY = (11, 17, 32); CARD = (22, 30, 54)
GOLD = (243, 196, 72); YEL = (255, 213, 79); WHITE = (245, 247, 252); GREY = (160, 170, 195); INK = (8, 8, 12)
UZC = (0, 153, 181); TRC = (213, 43, 30); RUBLUE = (0, 57, 166)

A = "‘"
UZ_NAME = f"O{A}ZBEKISTON"; TR_NAME = "ROSSIYA"; TR_CODE = "RU"

ROUNDS = [
    dict(t="HUDUD", s="UMUMIY MAYDON, KM²", uz=447400, tr=17098246, fmt="int", win="tr",
         fact="Rossiya 38 barobar katta", src="Manba: CIA World Factbook"),
    dict(t="AHOLI", s="MLN KISHI", uz=39.5, tr=146.1, fmt="mln", win="tr",
         fact=f"Rossiyada 3,7 barobar ko{A}p odam", src=f"O{A}zStat (1.10.2026) · Rosstat (1.01.2025)"),
    dict(t="IQTISODIYOT", s="YAIM HAJMI, 2025", uz=152.5, tr=2563, fmt="bln", win="tr",
         fact="Rossiya iqtisodi 17 barobar katta", src=f"O{A}zStat · Rosstat (213,5 trln rubl), MB kursi"),
    dict(t="BOYLIK", s="JON BOSHIGA YAIM, 2025", uz=3845, tr=17540, fmt="usd", win="tr",
         fact=f"Rossiya 4,6 barobar boyroq", src=f"O{A}zStat · Rosstat / Rossiya MB hisobi"),
    dict(t=f"O{A}SISH", s=f"YAIM O{A}SISHI, 2025", uz=7.7, tr=1.0, fmt="pct", win="uz",
         fact=f"O{A}zbekiston 7 barobar tez o{A}smoqda!", src=f"O{A}zStat · Rosstat, 2025"),
    dict(t="YOSHLIK", s=f"O{A}RTACHA YOSH (YOSHROQ G{A}OLIB)", uz=27.9, tr=41.4, fmt="yosh", win="uz",
         fact=f"O{A}zbeklar 13,5 yosh yoshroq!", src="Manba: BMT World Population Prospects, 2025"),
]
HOOK = [f"O{A}ZBEKISTON", "7 BAROBAR TEZ", f"O{A}SMOQDA?!"]

INTRO, ROUND, OUTRO = 3.3, 2.9, 8.1
_TJ = os.environ.get("TIMING_JSON")
if _TJ:
    _t = json.load(open(_TJ)); INTRO, OUTRO = _t["intro"], _t["outro"]; ROUND_LENS = _t["rounds"]
else:
    ROUND_LENS = [ROUND] * len(ROUNDS)
ROUND_STARTS = [INTRO + sum(ROUND_LENS[:i]) for i in range(len(ROUNDS))]
OUTRO_START = INTRO + sum(ROUND_LENS)
TOTAL = OUTRO_START + OUTRO
T_COLLIDE = 0.45
T_DECIDE = 1.05      # round-relative moment the round winner is revealed
COUNT0, COUNT_D = 0.22, 0.7

# ---------- easing ----------
def cl(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def ei(x): x = cl(x); return x ** 3
def eback(x, s=2.2): x = cl(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def eelastic(x):
    x = cl(x)
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - 0.75) * (2 * math.pi / 3)) + 1
def lerp(a, b, t): return a + (b - a) * t
def mix(c1, c2, t): t = cl(t); return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

def fmt(v, kind):
    if kind == "int": return f"{int(round(v)):,}".replace(",", " ")
    if kind == "usd": return "$" + f"{int(round(v)):,}".replace(",", " ")
    if kind == "pct": return f"{v:.1f}%".replace(".", ",")
    if kind == "mln": return f"{v:.1f} mln".replace(".", ",")
    if kind == "yosh": return f"{v:.1f} yosh".replace(".", ",")
    if kind == "bln":
        if v >= 1000: return f"${v / 1000:.2f} trln".replace(".", ",")
        return f"${v:.1f} mlrd".replace(".", ",")

# ---------- moving background ----------
_BGO = L.Background(seed=7, palette=[(UZC, 0.22, 0.30, 0.34, 0.60, 0.10, 0.0), (RUBLUE, 0.80, 0.55, 0.36, 0.60, 0.08, 1.9),
                                     (GOLD, 0.50, 0.95, 0.26, 0.32, 0.11, 3.0), (TRC, 0.85, 0.15, 0.22, 0.30, 0.12, 4.0)])
_DARK = Image.new("RGBA", (W, H), (6, 10, 22, 110))
_STREAK = Image.new("RGBA", (W * 2, 260), (0, 0, 0, 0))
_sd = ImageDraw.Draw(_STREAK)
for i in range(130):
    a = int(70 * math.sin(math.pi * i / 130) ** 2); _sd.line([(0, i * 2), (W * 2, i * 2)], fill=(255, 230, 160, a))
_STREAK = _STREAK.rotate(-18, expand=True, resample=Image.BICUBIC).filter(ImageFilter.GaussianBlur(30))
def bg(t):
    im = _BGO.frame(t, grid=True)
    im.alpha_composite(_DARK)
    # drifting light streak sweeping diagonally every ~6 s
    ph = (t / 6.0) % 1.0
    x = int(lerp(-_STREAK.width, W, ph)); y = int(lerp(1300, 100, ph))
    _safe_paste(im, _STREAK, x, y)
    return im

# ---------- flags ----------
def flag_uz(w):
    h = w // 2; S = 3; im = Image.new("RGB", (w * S, h * S)); d = ImageDraw.Draw(im)
    W2, H2 = w * S, h * S; band = H2 / 3; red = H2 * 0.02
    d.rectangle([0, 0, W2, band], fill=(0, 153, 181)); d.rectangle([0, band, W2, 2 * band], fill=WHITE)
    d.rectangle([0, 2 * band, W2, H2], fill=(30, 181, 58))
    d.rectangle([0, band - red, W2, band + red], fill=(206, 17, 38)); d.rectangle([0, 2 * band - red, W2, 2 * band + red], fill=(206, 17, 38))
    cx, cy, r = H2 * 0.27, band * 0.5, band * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.ellipse([cx - r + r * 0.32, cy - r * 0.92, cx + r * 1.12, cy + r * 0.92], fill=(0, 153, 181))
    def star(x, y, rr):
        pts = []
        for i in range(10):
            a = math.radians(-90 + i * 36); q = rr if i % 2 == 0 else rr * 0.382
            pts.append((x + q * math.cos(a), y + q * math.sin(a)))
        d.polygon(pts, fill=WHITE)
    step = band * 0.21
    for ri, n in enumerate([3, 4, 5]):
        y = band * 0.22 + ri * step * 1.35
        for k in range(n): star(H2 * 0.48 + (5 - n) * step + k * step, y, band * 0.06)
    return im.resize((w, h), Image.LANCZOS)

def flag_tr(w):
    # Russia: white / blue / red horizontal tricolour (2:3 shown at 1:2 like the UZ flag)
    h = w // 2; im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im); b = h / 3
    d.rectangle([0, 0, w, b], fill=(255, 255, 255)); d.rectangle([0, b, w, 2 * b], fill=RUBLUE); d.rectangle([0, 2 * b, w, h], fill=TRC)
    return im

def rflag(im, rad):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], rad, fill=255)
    o = im.convert("RGBA"); o.putalpha(m); return o
UZF_L, TRF_L = rflag(flag_uz(420), 24), rflag(flag_tr(420), 24)
UZF_M, TRF_M = rflag(flag_uz(170), 12), rflag(flag_tr(170), 12)
UZF_S, TRF_S = rflag(flag_uz(96), 8), rflag(flag_tr(96), 8)
TR_BIG = flag_tr(W * 2).convert("RGBA")

def paste_c(base, im, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if scale <= 0.01 or alpha <= 0.01: return
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        a = im.split()[3].point(lambda p: int(p * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2))) if (0 <= int(cx - im.width / 2) and 0 <= int(cy - im.height / 2) and int(cx + im.width / 2) <= base.width and int(cy + im.height / 2) <= base.height) else _safe_paste(base, im, int(cx - im.width / 2), int(cy - im.height / 2))

def _safe_paste(base, im, x, y):
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(base.width, x + im.width), min(base.height, y + im.height)
    if x1 <= x0 or y1 <= y0: return
    base.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def text_im(txt, f, fill, stroke=0, sfill=INK, shadow=True):
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    pad = 30
    im = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 6, pad - t + 10), txt, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return im

def fit(txt, name, size, maxw, minsize=40):
    while font(name, size).getlength(txt) > maxw and size > minsize: size -= 2
    return font(name, size)

def crown(d, cx, cy, s, fill):
    w, h = s, s * 0.72
    d.polygon([(cx - w / 2, cy + h / 2), (cx - w / 2, cy - h * 0.15), (cx - w / 4, cy + h * 0.1), (cx, cy - h / 2),
               (cx + w / 4, cy + h * 0.1), (cx + w / 2, cy - h * 0.15), (cx + w / 2, cy + h / 2)], fill=fill)
    for px, py in [(cx - w / 2, cy - h * 0.15), (cx, cy - h / 2), (cx + w / 2, cy - h * 0.15)]:
        r = s * 0.07; d.ellipse([px - r, py - r, px + r, py + r], fill=fill)

# ---------- scoreboard (fixed on top, flips on every win) ----------
def scores_at(t):
    su = st = 0; last = None
    for i, R in enumerate(ROUNDS):
        td = ROUND_STARTS[i] + T_DECIDE
        if t >= td:
            if R["win"] == "uz": su += 1
            else: st += 1
            last = (i, td)
    return su, st, last

def digit_roll(base, cx, cy, old, new, p, size):
    """old number rolls up and out, new number rolls in from below (p 0..1)."""
    f = font(BLACK, size)
    box = Image.new("RGBA", (int(size * 1.2), int(size * 1.3)), (0, 0, 0, 0))
    d = ImageDraw.Draw(box); bw, bh = box.size
    off = eo(p) * bh
    if p < 1: d.text((bw / 2, bh / 2 - off), str(old), font=f, fill=WHITE, anchor="mm")
    d.text((bw / 2, bh / 2 + bh - off), str(new), font=f, fill=YEL if p < 1 else WHITE, anchor="mm")
    base.alpha_composite(box, (int(cx - bw / 2), int(cy - bh / 2)))

def scoreboard(img, t, alpha=1.0):
    if alpha <= 0: return
    layer = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    su, st, last = scores_at(t)
    pulse_side = None; pf = 0.0
    if last is not None and t - last[1] < 0.6:
        pf = (t - last[1]) / 0.6; pulse_side = ROUNDS[last[0]]["win"]
    x0, x1, y0, y1 = 150, 930, 60, 190
    glowc = mix((60, 72, 110), GOLD, math.sin(math.pi * pf) if pulse_side else 0)
    d.rounded_rectangle([x0, y0, x1, y1], 65, fill=(10, 14, 26, 235), outline=glowc, width=5)
    layer.alpha_composite(UZF_S, (x0 + 30, 101)); layer.alpha_composite(TRF_S, (x1 - 30 - 96, 101))
    d.text((x0 + 140, 125), "UZ", font=font(XB, 44), fill=WHITE, anchor="lm")
    d.text((x1 - 140, 125), TR_CODE, font=font(XB, 44), fill=WHITE, anchor="rm")
    d.text((540, 120), ":", font=font(BLACK, 86), fill=GREY, anchor="mm")
    for side, val, cx in (("uz", su, 450), ("tr", st, 630)):
        if pulse_side == side and pf < 0.5:
            digit_roll(layer, cx, 124, val - 1, val, pf / 0.5, 96)
        else:
            sc = 1 + 0.25 * math.sin(math.pi * cl((pf - 0.5) / 0.5)) if pulse_side == side else 1
            d.text((cx, 124), str(val), font=font(BLACK, int(96 * sc)), fill=WHITE, anchor="mm")
    # round progress dots
    cur = sum(1 for s in ROUND_STARTS if t >= s) - 1
    for i in range(len(ROUNDS)):
        cx = 540 + (i - 2.5) * 56; cy = 238
        decided = t >= ROUND_STARTS[i] + T_DECIDE
        if decided:
            col = UZC if ROUNDS[i]["win"] == "uz" else TRC
            d.ellipse([cx - 15, cy - 15, cx + 15, cy + 15], fill=col, outline=WHITE, width=3)
        elif i == cur and t < OUTRO_START:
            r = 15 + 4 * math.sin(t * 10)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=YEL, width=5)
        else:
            d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], outline=(110, 120, 150), width=4)
    if alpha < 1:
        a = layer.split()[3].point(lambda p: int(p * alpha)); layer.putalpha(a)
    img.alpha_composite(layer, (0, 0))

# ---------- round card ----------
BAR_X0, BAR_X1 = 70, 1010
def round_layer(i, rt):
    R = ROUNDS[i]
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # header
    hy = 300
    d.rounded_rectangle([70, hy, 330, hy + 70], 35, fill=GOLD)
    d.text((200, hy + 35), f"{i + 1}-RAUND", font=font(BLACK, 44), fill=(35, 25, 5), anchor="mm")
    d.text((356, hy + 35), R["t"], font=fit(R["t"], BLACK, 84, 650), fill=WHITE, anchor="lm")
    d.text((72, hy + 112), R["s"], font=fit(R["s"], B, 34, 930, 22), fill=GOLD, anchor="lm")
    g = eo((rt - COUNT0) / COUNT_D)                 # counter / bar progress
    wa = eo((rt - T_DECIDE) / 0.25)                 # winner reveal
    mx = max(R["uz"], R["tr"])
    for k, (side, name, val, col, fl) in enumerate((("uz", UZ_NAME, R["uz"], UZC, UZF_M), ("tr", TR_NAME, R["tr"], TRC, TRF_M))):
        y = 500 + k * 330
        win = R["win"] == side
        # slide in from alternating sides
        sl = eback(cl((rt - 0.02 - k * 0.06) / 0.35), 1.6)
        dx = int((1 - sl) * (-700 if k == 0 else 700))
        # flag pulse on win
        ps = 1.0
        if win and rt > T_DECIDE: ps = 1 + 0.15 * math.sin(math.pi * cl((rt - T_DECIDE) / 0.45))
        paste_c(lay, fl, 70 + 85 + dx, y + 45, scale=ps)
        d.text((270 + dx, y + 45), name, font=font(XB, 52), fill=WHITE, anchor="lm")
        if win and wa > 0:
            crown(d, 975 + dx, y + 40, 80 * eback(wa, 2.5), GOLD)
        # big counter number (yellow, black stroke, >=110 px)
        txt = fmt(val * g, R["fmt"])
        nf = fit(txt, BLACK, 132, 900, 110)
        numc = YEL if (not win or wa < 0.5) else mix(YEL, (255, 236, 150), math.sin(math.pi * cl((rt - T_DECIDE) / 0.5)))
        ti = text_im(txt, nf, numc, stroke=8)
        nsc = 1 + (0.12 * math.sin(math.pi * cl((rt - T_DECIDE) / 0.4)) if win else 0)
        paste_c(lay, ti, 70 + ti.width * nsc / 2 - 30 + dx, y + 160, scale=nsc)
        # race bar
        by = y + 245; bx1 = BAR_X0 + (BAR_X1 - BAR_X0) * max(0.012, val / mx * g)
        d.rounded_rectangle([BAR_X0 + dx, by, BAR_X1 + dx, by + 46], 23, fill=(14, 20, 38, 230))
        if win and wa > 0:
            gl = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
            ImageDraw.Draw(gl).rounded_rectangle([BAR_X0 - 10 + dx, 40, bx1 + 10 + dx, 100], 30, fill=GOLD + (int(200 * wa),))
            gl = gl.filter(ImageFilter.GaussianBlur(16)); lay.alpha_composite(gl, (0, by - 47)); d = ImageDraw.Draw(lay)
        d.rounded_rectangle([BAR_X0 + dx, by, bx1 + dx, by + 46], 23, fill=mix(col, GOLD, wa * 0.85 if win else 0))
        # shine running along the bar while it grows
        if 0 < g < 1:
            sx = bx1 - 60 + dx
            d.rounded_rectangle([max(BAR_X0 + dx, sx), by + 6, bx1 - 8 + dx, by + 18], 6, fill=(255, 255, 255, 120))
        # "+1" pops at the winner's bar end, then flies into the scoreboard
        if win and rt > T_DECIDE:
            p = cl((rt - T_DECIDE) / 0.75)
            pi = text_im("+1", font(BLACK, 96), YEL, stroke=6)
            sx, sy = min(bx1 + dx, 900), by - 40
            tx, ty = (450 if side == "uz" else 630), 124
            q = ei(cl((p - 0.35) / 0.65))
            paste_c(lay, pi, lerp(sx, tx, q), lerp(sy, ty, q) - 60 * math.sin(math.pi * q), scale=(0.5 + 0.7 * eback(cl(p * 3), 2)) * (1 - 0.5 * q), alpha=1 - ei(cl((p - 0.85) / 0.15)))
    # fact box
    fa = eo((rt - T_DECIDE - 0.25) / 0.3)
    if fa > 0:
        fy = int(lerp(1260, 1190, eback(fa, 1.5)))
        d.rounded_rectangle([70, fy, 1010, fy + 150], 30, fill=(24, 32, 58, int(235 * fa)), outline=GOLD + (int(255 * fa),), width=4)
        d.text((540, fy + 58), R["fact"], font=fit(R["fact"], XB, 52, 880), fill=WHITE + (int(255 * fa),), anchor="mm")
        d.text((540, fy + 118), R["src"], font=fit(R["src"], MD, 26, 880, 18), fill=GREY + (int(255 * fa),), anchor="mm")
    return lay

def zoom_layer(lay, z, cx=540, cy=900):
    if abs(z - 1) < 1e-3: return lay
    nw, nh = int(W * z), int(H * z)
    big = lay.resize((nw, nh), Image.BILINEAR)
    x = int(cx * z - cx); y = int(cy * z - cy)
    return big.crop((x, y, x + W, y + H))

def whip(lay, dx, blur):
    """horizontal slide with motion blur (blur in px)."""
    if blur > 2:
        k = max(1, int(blur / 4))
        lay = lay.resize((max(1, W // k), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0)); _safe_paste(out, lay, int(dx), 0); return out

# ---------- hook ----------
def hook_layer(t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    fy = 940
    if t < T_COLLIDE:
        p = ei(t / T_COLLIDE)
        ux = lerp(-260, 540 - 210, p); rx = lerp(W + 260, 540 + 210, p)
    else:
        p = eback(cl((t - T_COLLIDE) / 0.45), 2.6)
        ux = lerp(540 - 210, 280, p); rx = lerp(540 + 210, W - 280, p)
    tilt = 0 if t > T_COLLIDE + 0.5 else (8 * (1 - cl(t / T_COLLIDE)) if t < T_COLLIDE else 6 * math.sin((t - T_COLLIDE) * 25) * (1 - cl((t - T_COLLIDE) / 0.5)))
    paste_c(lay, UZF_L, ux, fy, rot=tilt); paste_c(lay, TRF_L, rx, fy, rot=-tilt)
    if t > T_COLLIDE:
        vs = eback(cl((t - T_COLLIDE - 0.05) / 0.3), 3)
        if vs > 0:
            r = int(100 * vs); d.ellipse([540 - r, fy - r, 540 + r, fy + r], fill=GOLD, outline=INK, width=6)
            d.text((540, fy), "VS", font=font(BLACK, max(10, int(90 * vs))), fill=(30, 22, 5), anchor="mm")
        na = eo((t - T_COLLIDE - 0.2) / 0.3)
        d.text((280, fy + 160), UZ_NAME, font=fit(UZ_NAME, BLACK, 50, 420), fill=WHITE + (int(255 * na),), anchor="mm")
        d.text((W - 280, fy + 160), TR_NAME, font=font(BLACK, 50), fill=WHITE + (int(255 * na),), anchor="mm")
    # claim text: pops 1.4 -> 1.0 with rotation wobble, every line staggered
    for k, line in enumerate(HOOK):
        lt = max(0.0, t - k * 0.06)
        sc = lerp(1.4, 1.0, eo(lt / 0.35)) if lt < 0.35 else 1 + 0.03 * math.sin(lt * 5 + k)
        rot = 7 * math.sin(lt * 22) * math.exp(-lt * 4.5) + 1.2 * math.sin(lt * 3 + k)
        f = fit(line, BLACK, 150, 740, 80)
        paste_c(lay, text_im(line, f, YEL, stroke=10), 540, 420 + k * 160, scale=sc, rot=rot)
    kb = eback(cl((t - 1.5) / 0.35), 2.2)
    if kb > 0:
        badge = Image.new("RGBA", (640, 130), (0, 0, 0, 0)); bd = ImageDraw.Draw(badge)
        bd.rounded_rectangle([0, 0, 639, 129], 50, fill=(24, 32, 58, 240), outline=GOLD, width=5)
        bd.text((320, 65), "KIM KUCHLI?", font=font(BLACK, 80), fill=WHITE, anchor="mm")
        paste_c(lay, badge, 540, 1300, scale=kb, rot=3 * math.sin(t * 4))
    return lay

# ---------- outro ----------
rng = random.Random(11)
CONF = [(rng.uniform(0, W), rng.uniform(-900, -20), rng.uniform(-80, 80), rng.uniform(380, 760), rng.uniform(0, 6.28), rng.uniform(4, 12),
         rng.choice([GOLD, YEL, WHITE, UZC, TRC, RUBLUE, (30, 181, 58)]), rng.uniform(10, 22)) for _ in range(170)]
def confetti(d, ct):
    for x0, y0, vx, vy, ph, spin, col, s in CONF:
        y = y0 + vy * ct; x = x0 + vx * ct + 30 * math.sin(ct * 3 + ph)
        if y < -30 or y > SAFE_B + 40: continue
        w = s * abs(math.cos(ct * spin + ph)) + 2
        d.polygon([(x - w, y - s * 0.4), (x + w, y - s * 0.2), (x + w * 0.8, y + s * 0.4), (x - w * 0.9, y + s * 0.3)], fill=col)

def outro_layer(ot):
    su = sum(1 for r in ROUNDS if r["win"] == "uz"); st = len(ROUNDS) - su
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    tie = su == st
    winner_flag = UZF_L if su > st else TRF_L
    g = eo(ot / 0.7)
    if not tie:
        # winner flag grows to full screen
        if ot < 0.7:
            sc = lerp(0.4, 1.0, g)
            fw = int(lerp(420, W * 1.15, g) )
        big = (flag_uz(W * 2).convert("RGBA") if su > st else TR_BIG)
        s = lerp(0.25, 1.0, g)
        fb = big.resize((int(big.width * s), int(big.height * s * 1.9)), Image.BILINEAR)
        alpha = 1.0
        paste_c(lay, fb, 540, 900 + 8 * math.sin(ot * 2), alpha=0.9)
        dk = Image.new("RGBA", (W, H), (5, 8, 18, int(165 * g))); lay.alpha_composite(dk)
    else:
        paste_c(lay, UZF_L, 280, 900, scale=eback(g)); paste_c(lay, TRF_L, W - 280, 900, scale=eback(g))
    d = ImageDraw.Draw(lay)
    confetti(d, max(0.0, ot - 0.5))
    # stamp
    sp = cl((ot - 0.55) / 0.3)
    if sp > 0:
        word = "DURRANG" if tie else f"G{A}OLIB!"
        st_im = Image.new("RGBA", (900, 280), (0, 0, 0, 0)); sd = ImageDraw.Draw(st_im)
        sd.rounded_rectangle([10, 10, 889, 269], 40, outline=GOLD, width=16)
        sd.text((450, 140), word, font=fit(word, BLACK, 190, 800), fill=GOLD, anchor="mm", stroke_width=6, stroke_fill=INK)
        paste_c(lay, st_im, 540, 760, scale=lerp(2.6, 1.0, eo(sp)), rot=-8, alpha=cl(sp * 3))
    ta = eo((ot - 1.1) / 0.4)
    if ta > 0:
        who = "DURRANG" if tie else (UZ_NAME if su > st else TR_NAME)
        line = f"{who}  {st if st > su else su} : {su if st > su else st}"
        paste_c(lay, text_im(line, fit(line, BLACK, 110, 960, 70), YEL, stroke=8), 540, 1010, scale=eback(ta, 1.8))
    qa = eo((ot - 2.4) / 0.4)
    if qa > 0:
        d.rounded_rectangle([70, 1130, 1010, 1420], 36, fill=(14, 20, 38, int(235 * qa)), outline=GOLD + (int(255 * qa),), width=4)
        q1 = "Lekin kelajak kimniki?"
        d.text((540, 1205), q1, font=fit(q1, BLACK, 72, 880), fill=WHITE + (int(255 * qa),), anchor="mm")
        d.text((540, 1300), f"Izohda yozing  ↓", font=font(BLACK, 66), fill=YEL + (int(255 * qa),), anchor="mm")
        d.text((540, 1378), f"7 barobar tez o{A}sish 10 yilda nima beradi?", font=fit(f"7 barobar tez o{A}sish 10 yilda nima beradi?", SB, 34, 880, 20), fill=GREY + (int(255 * qa),), anchor="mm")
    return lay

# ---------- captions (inside safe area) ----------
CAPS = None
_WJ = os.environ.get("WORDS_JSON")
if _WJ:
    _ws = json.load(open(_WJ))["words"]
    CAPS = L.Captions(_ws, {w["text"]: w["text"].replace("'", A).replace("’", A) for w in _ws}, y=1490, size=60, maxchars=18,
                      hide=((0, INTRO),))

def shake_at(t):
    """(dx, dy) camera shake: flag collision + every round win + final stamp."""
    hits = [T_COLLIDE] + [s + T_DECIDE for s in ROUND_STARTS] + [OUTRO_START + 0.75]
    amps = [8] + [6] * len(ROUND_STARTS) + [8]
    for h, a in zip(hits, amps):
        k = int(round((t - h) * FPS))
        if 0 <= k < 4:
            r = random.Random(int(h * 1000) + k)
            return r.choice([-1, 1]) * a * (1 - k / 5), r.choice([-1, 1]) * a * (1 - k / 5)
    return 0, 0

def compose(t):
    img = bg(t)
    if t < INTRO:
        lay = hook_layer(t)
        if t > INTRO - 0.18:      # whip out of the hook
            p = (t - (INTRO - 0.18)) / 0.18; lay = whip(lay, -W * ei(p), 60 * p)
        img.alpha_composite(lay)
        scoreboard(img, t, alpha=eo((t - 2.2) / 0.4))
    elif t < OUTRO_START:
        i = sum(1 for s in ROUND_STARTS if t >= s) - 1; rt = t - ROUND_STARTS[i]
        lay = round_layer(i, rt)
        lay = zoom_layer(lay, 1.0 + 0.04 * cl(rt / ROUND_LENS[i]))
        if rt < 0.18:              # whip in
            p = rt / 0.18; lay = whip(lay, W * (1 - eo(p)), 60 * (1 - p))
        elif rt > ROUND_LENS[i] - 0.18:   # whip out
            p = (rt - (ROUND_LENS[i] - 0.18)) / 0.18; lay = whip(lay, -W * ei(p), 60 * p)
        img.alpha_composite(lay)
        scoreboard(img, t)
    else:
        ot = t - OUTRO_START
        img.alpha_composite(outro_layer(ot))
        scoreboard(img, t, alpha=1 - eo((ot - 0.2) / 0.4) + eo((ot - 1.4) / 0.4) * 0)
    # brand
    ImageDraw.Draw(img).text((540, 1555), "@Taqqos_Uzb", font=font(SB, 28), fill=(130, 140, 170), anchor="mm")
    if CAPS is not None: CAPS.draw(img, t)
    _BGO.finish(img)
    # white flash on the collision
    fl = 1 - cl((t - T_COLLIDE) / 0.18) if t >= T_COLLIDE else 0
    if fl > 0: img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(230 * fl))))
    dx, dy = shake_at(t)
    if dx or dy:
        out = Image.new("RGBA", (W, H), (0, 0, 0, 255)); out.alpha_composite(img, (0, 0)) ; out = Image.new("RGBA", (W, H), NAVY + (255,)); _safe_paste(out, img, int(dx), int(dy)); img = out
    return img

FIRST = None
def frame(t):
    global FIRST
    img = compose(t)
    # loop-friendly ending: the last 0.4 s crossfades into frame 0
    if t > TOTAL - 0.4:
        if FIRST is None: FIRST = compose(0.0)
        img = Image.blend(img, FIRST, ei((t - (TOTAL - 0.4)) / 0.4))
    return img.convert("RGB")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for ts in [float(x) for x in sys.argv[2:]]:
            frame(ts).save(f"preview_{ts:05.2f}.png")
        sys.exit()
    n = int(TOTAL * FPS); out = sys.stdout.buffer
    for i in range(n): out.write(frame(i / FPS).tobytes())
