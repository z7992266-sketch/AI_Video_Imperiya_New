#!/usr/bin/env python3
"""Taqqos #4: O'zbekiston vs Qirg'iziston — renders raw RGB frames to stdout (1080x1920, 30fps)."""
import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "smart"))
import lib as L
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
F = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(F + name, size)
BLACK = "InterDisplay-Black.otf"
XB = "Inter-ExtraBold.otf"
B = "Inter-Bold.otf"
SB = "Inter-SemiBold.otf"
MD = "Inter-Medium.otf"

NAVY = (11, 17, 32); NAVY2 = (20, 29, 52); CARD = (24, 34, 60)
GOLD = (243, 196, 72); GOLD_D = (120, 96, 40); WHITE = (245, 247, 252); GREY = (150, 160, 185)
UZC = (0, 153, 181); TRC = (232, 17, 45); KGRED = (232, 17, 45); KGGOLD = (255, 214, 0)

A = "‘"  # o‘ g‘
UZ_NAME = f"O{A}ZBEKISTON"; TR_NAME = f"QIRG{A}IZISTON"

ROUNDS = [
    dict(t="HUDUD", s="UMUMIY MAYDON, KM²", uz=447400, tr=199951, fmt="int", unit="km²",
         win="uz", fact="O‘zbekiston 2,2 barobar katta", src="Manba: CIA World Factbook"),
    dict(t="AHOLI", s="NECHA KISHI YASHAYDI", uz=39.5, tr=7.4, fmt="mln", unit="",
         win="uz", fact="O‘zbekistonda 5 barobar ko‘p odam",
         src="Milliy statistika qo‘mitasi (1.10.2026) · Qirg‘iziston Milliy statistika qo‘mitasi (1.02.2026)"),
    dict(t="IQTISODIYOT HAJMI", s="YAIM, 2025, MLRD $", uz=152.5, tr=22.8, fmt="bln", unit="",
         win="uz", fact="O‘zbekiston iqtisodi 6,7 barobar katta", src="Milliy statistika qo‘mitasi · Qirg‘iziston Vazirlar Mahkamasi, 2025"),
    dict(t="BOYLIK", s="AHOLI JON BOSHIGA YAIM, 2025", uz=3845, tr=3131, fmt="usd", unit="",
         win="uz", fact="O‘zbekiston oldinda: +23%", src="Milliy statistika qo‘mitasi · FocusEconomics, 2025"),
    dict(t="IQTISODIY O‘SISH", s="YAIM O‘SISHI, 2025", uz=7.7, tr=11.1, fmt="pct", unit="",
         win="tr", fact="Qirg‘iziston oldinda: +11,1%!", src="Milliy statistika qo‘mitasi · Qirg‘iziston Milliy statistika qo‘mitasi, 2025"),
    dict(t="TASHRIFLAR", s="XORIJIY TASHRIFLAR, 2025", uz=11.7, tr=21.0, fmt="mln", unit="",
         win="tr", fact="Qirg‘izistonga 21 mln xorijlik kirdi",
         src="Turizm qo‘mitasi · Qirg‘iziston DKNB Chegara xizmati, 2025"),
]

import json, os
INTRO, ROUND, OUTRO = 3.0, 6.2, 5.0
# Optional narration timing: TIMING_JSON -> {"intro": s, "rounds": [s,...], "outro": s}
_TJ = os.environ.get("TIMING_JSON")
if _TJ:
    _t = json.load(open(_TJ))
    INTRO, OUTRO = _t["intro"], _t["outro"]
    ROUND_LENS = _t["rounds"]
else:
    ROUND_LENS = [ROUND] * len(ROUNDS)
ROUND_STARTS = [INTRO + sum(ROUND_LENS[:i]) for i in range(len(ROUNDS))]
TOTAL = INTRO + sum(ROUND_LENS) + OUTRO

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def lerp(a, b, t): return a + (b - a) * t
def mix(c1, c2, t): return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

def fmt(v, kind):
    if kind == "int": return f"{int(round(v)):,}".replace(",", " ")
    if kind == "usd": return "$" + f"{int(round(v)):,}".replace(",", " ")
    if kind == "pct": return f"{v:.1f}%".replace(".", ",")
    if kind == "mln": return f"{v:.1f} mln".replace(".", ",")
    if kind == "bln": return f"${v:.1f} mlrd".replace(".", ",")

# ---------- background (static) ----------
def make_bg():
    bg = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=mix((14, 22, 44), (7, 10, 20), t))
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse([-300, 300, 700, 1300], fill=(0, 70, 95)); g.ellipse([400, 700, 1400, 1700], fill=(95, 10, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    bg = Image.blend(bg, Image.eval(glow, lambda p: p), 0.35)
    d = ImageDraw.Draw(bg)
    for x in range(0, W, 60): d.line([(x, 0), (x, H)], fill=(18, 26, 46))
    for y in range(0, H, 60): d.line([(0, y), (W, y)], fill=(18, 26, 46))
    return bg
BG = make_bg()
_BGO = L.Background(seed=5, palette=[((0, 153, 181), 0.25, 0.30, 0.32, 0.55, 0.09, 0.0), ((0, 175, 202), 0.78, 0.62, 0.34, 0.55, 0.07, 1.9),
                                      ((243, 196, 72), 0.5, 0.95, 0.26, 0.30, 0.10, 3.0), ((30, 181, 58), 0.15, 0.85, 0.2, 0.18, 0.12, 4.0)])
_DARK = Image.new("RGBA", (W, H), (6, 10, 22, 120))
def _bg(t):
    im = _BGO.frame(t, grid=True)
    im.alpha_composite(_DARK)
    return im.convert("RGB")

# ---------- flags ----------
def star(d, cx, cy, r, fill, rot=-90, inner=0.382):
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36); rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)

def flag_uz(w):
    h = w // 2; S = 3; im = Image.new("RGB", (w * S, h * S)); d = ImageDraw.Draw(im)
    W2, H2 = w * S, h * S; band = H2 / 3; red = H2 * 0.02
    d.rectangle([0, 0, W2, band], fill=(0, 153, 181))
    d.rectangle([0, band, W2, 2 * band], fill=WHITE)
    d.rectangle([0, 2 * band, W2, H2], fill=(30, 181, 58))
    d.rectangle([0, band - red, W2, band + red], fill=(206, 17, 38))
    d.rectangle([0, 2 * band - red, W2, 2 * band + red], fill=(206, 17, 38))
    cx, cy, r = H2 * 0.27, band * 0.5, band * 0.36
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.ellipse([cx - r + r * 0.32, cy - r * 0.92, cx + r * 1.12, cy + r * 0.92], fill=(0, 153, 181))
    rows = [3, 4, 5]; sx0 = H2 * 0.48; step = band * 0.21
    for ri, n in enumerate(rows):
        y = band * 0.22 + ri * step * 1.35
        for k in range(n):
            x = sx0 + (5 - n) * step + k * step
            star(d, x, y, band * 0.06, WHITE)
    return im.resize((w, h), Image.LANCZOS)

def flag_tr(w):
    # Kyrgyzstan: red field, gold sun with 40 rays, red tunduk inside
    h = w // 2; S = 4; W2, H2 = w * S, h * S
    im = Image.new("RGB", (W2, H2), KGRED); d = ImageDraw.Draw(im)
    cx, cy = W2 / 2, H2 / 2; Ro = H2 * 0.40; Ri = H2 * 0.23
    for k in range(40):
        a0 = math.radians(k * 9); a1 = math.radians(k * 9 + 4.5)
        tip = math.radians(k * 9 + 2.25)
        d.polygon([(cx + Ri * math.cos(a0), cy + Ri * math.sin(a0)), (cx + Ro * math.cos(tip), cy + Ro * math.sin(tip)),
                   (cx + Ri * math.cos(a1), cy + Ri * math.sin(a1))], fill=KGGOLD)
    r = H2 * 0.25; d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=KGGOLD)
    r2 = H2 * 0.165; lw = max(2, int(H2 * 0.022))
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=KGRED, width=lw)
    # tunduk: two sets of three crossing arcs
    for sgn in (-1, 1):
        for off in (-0.55, 0, 0.55):
            R = r2 * 2.2; ox = cx + off * r2 * 1.1; oy = cy + sgn * R
            bb = [ox - R, oy - R, ox + R, oy + R]
            d.arc(bb, 0, 360, fill=KGRED, width=lw)
    # clip arcs to inner circle: repaint outside ring area
    m = Image.new("L", (W2, H2), 0); ImageDraw.Draw(m).ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=255)
    base = Image.new("RGB", (W2, H2), KGRED); bd = ImageDraw.Draw(base)
    for k in range(40):
        a0 = math.radians(k * 9); a1 = math.radians(k * 9 + 4.5); tip = math.radians(k * 9 + 2.25)
        bd.polygon([(cx + Ri * math.cos(a0), cy + Ri * math.sin(a0)), (cx + Ro * math.cos(tip), cy + Ro * math.sin(tip)),
                    (cx + Ri * math.cos(a1), cy + Ri * math.sin(a1))], fill=KGGOLD)
    bd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=KGGOLD)
    bd.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], outline=KGRED, width=lw)
    base.paste(im, (0, 0), m)
    return base.resize((w, h), Image.LANCZOS)

def rounded_flag(im, rad=14):
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.size[0] - 1, im.size[1] - 1], rad, fill=255)
    return im, m

UZF_S, UZM_S = rounded_flag(flag_uz(200)); TRF_S, TRM_S = rounded_flag(flag_tr(200))
UZF_L, UZM_L = rounded_flag(flag_uz(380), 22); TRF_L, TRM_L = rounded_flag(flag_tr(380), 22)

def crown(d, cx, cy, s, fill):
    w, h = s, s * 0.72
    pts = [(cx - w / 2, cy + h / 2), (cx - w / 2, cy - h * 0.15), (cx - w / 4, cy + h * 0.1), (cx, cy - h / 2),
           (cx + w / 4, cy + h * 0.1), (cx + w / 2, cy - h * 0.15), (cx + w / 2, cy + h / 2)]
    d.polygon(pts, fill=fill)
    for px, py in [(cx - w / 2, cy - h * 0.15), (cx, cy - h / 2), (cx + w / 2, cy - h * 0.15)]:
        r = s * 0.07; d.ellipse([px - r, py - r, px + r, py + r], fill=fill)

def ctext(d, xy, text, f, fill, anchor="mm"): d.text(xy, text, font=f, fill=fill, anchor=anchor)

def fit_font(text, name, size, maxw):
    f = font(name, size)
    while f.getlength(text) > maxw and size > 20:
        size -= 2; f = font(name, size)
    return f

# ---------- scoreboard ----------
def scoreboard(d, score_uz, score_tr, pop_uz=0.0, pop_tr=0.0):
    for i, (code, sc, col, pop) in enumerate([("UZ", score_uz, UZC, pop_uz), ("KG", score_tr, TRC, pop_tr)]):
        x0 = 170 + i * 390; y0 = 300
        border = mix(col, GOLD, pop)
        d.rounded_rectangle([x0, y0, x0 + 350, y0 + 92], 46, fill=(12, 16, 28), outline=border, width=5)
        d.ellipse([x0 + 28, y0 + 34, x0 + 52, y0 + 58], fill=col)
        ctext(d, (x0 + 70, y0 + 46), code, font(XB, 46), WHITE, "lm")
        crown(d, x0 + 215, y0 + 46, 56 + 18 * pop, GOLD if sc > 0 else GOLD_D)
        ctext(d, (x0 + 300, y0 + 46), str(sc), font(XB, 54 + int(16 * pop)), WHITE, "mm")

# ---------- scenes ----------
def header(d, num, title, sub, a):
    y = int(lerp(60, 120, ease(a)))
    tf = fit_font(title, BLACK, 74, 620)
    d.rounded_rectangle([110, y, 970, y + 150], 30, fill=(26, 32, 50), outline=(60, 70, 100), width=2)
    d.ellipse([140, y + 25, 240, y + 125], fill=GOLD); ctext(d, (190, y + 75), str(num), font(BLACK, 62), (40, 30, 10))
    ctext(d, (275, y + 60), title, tf, WHITE, "lm")
    ctext(d, (278, y + 118), sub, font(B, 30), GOLD, "lm")

def country_card(img, d, y, code, name, val_text, frac, color, flagim, flagmask, winner_a, is_winner):
    x0, x1 = 70, 1010
    outline = mix((50, 62, 95), GOLD, winner_a if is_winner else 0)
    fill = mix(CARD, (46, 40, 22), (winner_a * 0.6) if is_winner else 0)
    d.rounded_rectangle([x0, y, x1, y + 290], 34, fill=fill, outline=outline, width=6 if is_winner and winner_a > 0 else 3)
    img.paste(flagim, (x0 + 34, y + 34), flagmask)
    fw = flagim.size[0]
    ctext(d, (x0 + 60 + fw, y + 62), name, font(XB, 46), WHITE, "lm")
    vf = fit_font(val_text, BLACK, 92, x1 - x0 - 90 - fw)
    ctext(d, (x0 + 60 + fw, y + 150), val_text, vf, WHITE if not (is_winner and winner_a > 0.5) else GOLD, "lm")
    bx0, bx1, by = x0 + 34, x1 - 34, y + 232
    d.rounded_rectangle([bx0, by, bx1, by + 30], 15, fill=(14, 20, 36))
    if frac > 0.01:
        d.rounded_rectangle([bx0, by, bx0 + (bx1 - bx0) * frac, by + 30], 15, fill=color)
    if is_winner and winner_a > 0:
        s = 70 * ease(min(1, winner_a * 1.6)); crown(d, x1 - 70, y + 62, s, GOLD)

def fact_box(d, text, src, a):
    if a <= 0: return
    y = int(lerp(1330, 1290, ease(a)))
    c = mix(NAVY, (30, 38, 62), a)
    d.rounded_rectangle([70, y, 1010, y + 150], 30, fill=c, outline=mix(NAVY, GOLD, a), width=3)
    tf = fit_font(text, XB, 50, 880)
    ctext(d, (540, y + 62), text, tf, mix(NAVY, WHITE, a))
    sf = fit_font(src, MD, 24, 880)
    ctext(d, (540, y + 120), src, sf, mix(NAVY, GREY, a))

def frame(t):
    img = _bg(t); d = ImageDraw.Draw(img)
    # brand tag
    ctext(d, (540, 1540), "@Taqqos_Uzb", font(SB, 30), (90, 100, 130))
    if t < INTRO:
        # flags slide in from frame 0, big yellow claim already on screen
        off = int(lerp(-330, 0, ease(t / 0.45)))
        img.paste(UZF_L, (60 + off, 780), UZM_L)
        img.paste(TRF_L, (W - 60 - TRF_L.size[0] - off, 780), TRM_L)
        d = ImageDraw.Draw(img)
        vs = ease((t - 0.25) / 0.3)
        if vs > 0:
            r = int(95 * vs); d.ellipse([540 - r, 875 - r, 540 + r, 875 + r], fill=GOLD)
            ctext(d, (540, 875), "VS", font(BLACK, int(84 * vs) + 1), (30, 22, 5))
        sc = 1.0 + 0.25 * (1 - ease(t / 0.35))
        for k, (line, yy) in enumerate([(f"QIRG{A}IZISTON", 260), ("+11,1%", 410), (f"O{A}SDI?!", 560)]):
            f = fit_font(line, BLACK, int(150 * sc), 1000)
            ctext(d, (540 + 4, yy + 6), line, f, (20, 14, 0))
            ctext(d, (540, yy), line, f, GOLD)
        ctext(d, (250, 1110), UZ_NAME, fit_font(UZ_NAME, BLACK, 46, 400), WHITE)
        ctext(d, (W - 250, 1110), TR_NAME, fit_font(TR_NAME, BLACK, 46, 400), WHITE)
        kb = ease((t - 1.5) / 0.4)
        if kb > 0:
            d.rounded_rectangle([200, 1200, 880, 1330], 40, fill=mix(NAVY, (30, 38, 62), kb), outline=mix(NAVY, GOLD, kb), width=4)
            ctext(d, (540, 1265), "KIM KUCHLI? ⚔".replace(" ⚔", ""), font(BLACK, 84), mix(NAVY, WHITE, kb))
        return img
    ri = sum(1 for s in ROUND_STARTS if t >= s) - 1
    if t < INTRO + sum(ROUND_LENS):
        rt = t - ROUND_STARTS[ri]; R = ROUNDS[ri]
        su = sum(1 for r in ROUNDS[:ri] if r["win"] == "uz"); st = ri - su
        decided = rt >= 1.3
        pop = ease((rt - 1.3) / 0.25) * (1 - ease((rt - 1.8) / 0.4)) if decided else 0
        if decided:
            if R["win"] == "uz": su += 1
            else: st += 1
        header(d, ri + 1, R["t"], R["s"], rt / 0.25)
        scoreboard(d, su, st, pop if R["win"] == "uz" else 0, pop if R["win"] == "tr" else 0)
        g = ease((rt - 0.15) / 1.0)
        mx = max(R["uz"], R["tr"])
        wa = ease((rt - 1.3) / 0.3)
        country_card(img, d, 460, "UZ", UZ_NAME, fmt(R["uz"] * g, R["fmt"]), R["uz"] / mx * g, UZC, UZF_S, UZM_S, wa, R["win"] == "uz")
        country_card(img, d, 790, "KG", TR_NAME, fmt(R["tr"] * g, R["fmt"]), R["tr"] / mx * g, TRC, TRF_S, TRM_S, wa, R["win"] == "tr")
        d = ImageDraw.Draw(img)
        fact_box(d, R["fact"], R["src"], ease((rt - 1.6) / 0.35))
        return img
    # outro
    ot = t - INTRO - sum(ROUND_LENS)
    su = sum(1 for r in ROUNDS if r["win"] == "uz"); st = len(ROUNDS) - su
    a = ease(ot / 0.5)
    ctext(d, (540, 200), "NATIJA", font(BLACK, 96), mix(NAVY, GOLD, a))
    img.paste(UZF_S, (110, 360), UZM_S); img.paste(TRF_S, (W - 110 - TRF_S.size[0], 360), TRM_S)
    d = ImageDraw.Draw(img)
    ctext(d, (210, 560), UZ_NAME, font(XB, 36), WHITE); ctext(d, (W - 210, 560), TR_NAME, fit_font(TR_NAME, XB, 36, 360), WHITE)
    ctext(d, (540, 430), f"{su} : {st}", font(BLACK, 150), WHITE)
    crown(d, 210, 310, 90, GOLD)
    b = ease((ot - 0.6) / 0.5)
    if b > 0:
        sc = 0.6 + 0.4 * ease(b)
        d.rounded_rectangle([70, 680, 1010, 980], 34, fill=mix(NAVY, (30, 38, 62), b), outline=mix(NAVY, GOLD, b), width=4)
        ctext(d, (540, 790), f"O{A}ZBEKISTON G{A}OLIB!", fit_font(f"O{A}ZBEKISTON G{A}OLIB!", BLACK, int(96 * sc), 880), mix(NAVY, GOLD, b))
        ctext(d, (540, 905), f"Lekin Qirg{A}iziston tezroq o{A}smoqda!", fit_font(f"Lekin Qirg{A}iziston tezroq o{A}smoqda!", XB, 46, 860), mix(NAVY, WHITE, b))
    c = ease((ot - 1.6) / 0.5)
    if c > 0:
        ctext(d, (540, 1080), "Sizningcha, kim kuchliroq?", font(BLACK, 58), mix(NAVY, WHITE, c))
        ctext(d, (540, 1170), "Izohda yozing  ↓", font(XB, 56), mix(NAVY, GOLD, c))
        ctext(d, (540, 1300), "Keyingi jang kim bilan bo‘lsin?", font(SB, 40), mix(NAVY, GREY, c))
    return img

CAPS = None
_WJ = os.environ.get("WORDS_JSON")
if _WJ:
    _ws = json.load(open(_WJ))["words"]
    CAPS = L.Captions(_ws, {w["text"]: w["text"].replace("'", "‘").replace("’", "‘") for w in _ws}, y=1690, size=62, maxchars=18)
_frame_core = frame
def frame(t):
    img = _frame_core(t)
    if CAPS is not None:
        im = img.convert("RGBA"); CAPS.draw(im, t); _BGO.finish(im); img = im.convert("RGB")
    return img

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        for ts in [float(x) for x in sys.argv[2:]]:
            frame(ts).save(f"preview_{ts:05.1f}.png")
        sys.exit()
    n = int(TOTAL * FPS); out = sys.stdout.buffer
    for i in range(n):
        out.write(frame(i / FPS).tobytes())
