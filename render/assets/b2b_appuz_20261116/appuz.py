"""B2B SAS mobile-app demo scenes, Uzbek UI (generic demo, no prices, no real brand). Usage: python3 appuz.py outdir"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b2b_app_20261113'))
import appdemo as A
from appdemo import f, ease, Image, ImageDraw, GOLD, GOLD2, WHITE, GREY, BG, CARD, GREEN, W, H, FPS, BLUE


def tag(im, y=1470):
    ImageDraw.Draw(im).text((W - 200, y), 'demo', font=f('Inter-SemiBold.otf', 30), fill=(170, 170, 170, 255))


def scr_shop(t, pw=600, ph=1060, theme=GOLD, brand=None):
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph), BG + (255,)); d = ImageDraw.Draw(sc)
    A.status(d, s, pw)
    if brand:
        d.rounded_rectangle([22 * s, 52 * s, 62 * s, 92 * s], 10 * s, fill=theme)
        d.text((31 * s, 61 * s), 'YB', font=f('Inter-Black.otf', 15 * s), fill=(15, 15, 20))
        d.text((72 * s, 50 * s), brand, font=f('Inter-Black.otf', 19 * s), fill=WHITE)
        d.text((72 * s, 74 * s), 'SIZNING BRENDINGIZ', font=f('Inter-SemiBold.otf', 11 * s), fill=theme)
    else:
        d.text((22 * s, 50 * s), 'Katalog', font=f('Inter-Black.otf', 26 * s), fill=WHITE)
        d.text((22 * s, 84 * s), 'Sizning do\'koningiz', font=f('Inter-SemiBold.otf', 14 * s), fill=theme)
    items = ['Kofe', 'Tort', 'Gul guldastasi', "Sovg'a to'plami"]
    for i, n in enumerate(items):
        k = ease((t - 0.1 * i) / 0.4)
        y = (112 + i * 82) * s + (1 - k) * 30 * s
        d.rounded_rectangle([18 * s, y, pw - 18 * s, y + 68 * s], 16 * s, fill=CARD)
        d.rounded_rectangle([30 * s, y + 10 * s, 78 * s, y + 58 * s], 12 * s, fill=(70 + i * 30, 55 + i * 12, 40 + i * 20))
        d.text((92 * s, y + 13 * s), n, font=f('Inter-Bold.otf', 19 * s), fill=WHITE)
        d.text((92 * s, y + 40 * s), '★ 4.%d' % (9 - i % 3), font=f('Inter-Regular.otf', 14 * s), fill=theme)
        sel = (i == 1 and t > 0.9)
        d.ellipse([pw - 58 * s, y + 20 * s, pw - 30 * s, y + 48 * s], fill=theme if sel else (70, 70, 80))
    press = 1.0 - 0.06 * math.exp(-((t - 1.5) / 0.12) ** 2)
    bw, bh = (pw - 44 * s) * press, 64 * s * press
    bx, by = (pw - bw) / 2, 470 * s + (64 * s - bh) / 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], 20 * s, fill=theme)
    tx = 'Bir bosishda buyurtma'; fo = f('Inter-Bold.otf', 20 * s); tw = d.textlength(tx, font=fo)
    d.text(((pw - tw) / 2, by + bh / 2 - 13 * s), tx, font=fo, fill=(20, 20, 20))
    if t > 1.5:
        r = ease((t - 1.5) / 0.5) * 70 * s; a = max(0, 1 - (t - 1.5) / 0.5)
        ov = Image.new('RGBA', (pw, ph)); ImageDraw.Draw(ov).ellipse([pw / 2 - r, 502 * s - r, pw / 2 + r, 502 * s + r], outline=(255, 255, 255, int(200 * a)), width=5)
        sc.alpha_composite(ov); d = ImageDraw.Draw(sc)
    if t > 1.9:
        k = ease((t - 1.9) / 0.35); y = (560 + (1 - k) * 60) * s
        d.rounded_rectangle([30 * s, y, pw - 30 * s, y + 50 * s], 25 * s, fill=GREEN)
        fo = f('Inter-Bold.otf', 17 * s); tx = 'Buyurtma qabul qilindi ✓'; tw = d.textlength(tx, font=fo)
        d.text(((pw - tw) / 2, y + 13 * s), tx, font=fo, fill=WHITE)
    return sc


def scr_push(t, pw=600, ph=1060):
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph)); d = ImageDraw.Draw(sc)
    for yy in range(ph):
        c = int(20 + 30 * yy / ph); d.line([0, yy, pw, yy], fill=(c, c // 2 + 10, c + 30))
    fo = f('Inter-Bold.otf', 64 * s); tx = '9:41'; tw = d.textlength(tx, font=fo)
    d.text(((pw - tw) / 2, 60 * s), tx, font=fo, fill=WHITE)
    notes = [('Sizning ilovangiz', 'Bugun maxsus aksiya — ilovada'), ('Sizning ilovangiz', 'Yangi mahsulotlar keldi'),
             ('Sizning ilovangiz', 'Buyurtmangiz tayyor ✓')]
    for i, (a, b) in enumerate(notes):
        k = ease((t - 0.25 - 0.7 * i) / 0.35)
        if k <= 0:
            continue
        y = (220 + i * 96) * s - (1 - k) * 40 * s
        ov = Image.new('RGBA', (pw, ph)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle([14 * s, y, pw - 14 * s, y + 82 * s], 18 * s, fill=(245, 245, 245, int(235 * k)))
        od.rounded_rectangle([26 * s, y + 14 * s, 56 * s, y + 44 * s], 8 * s, fill=GOLD + (int(255 * k),))
        od.text((68 * s, y + 12 * s), a, font=f('Inter-Bold.otf', 15 * s), fill=(30, 30, 30, int(255 * k)))
        od.text((68 * s, y + 38 * s), b, font=f('Inter-Regular.otf', 14 * s), fill=(60, 60, 60, int(255 * k)))
        sc.alpha_composite(ov)
    return sc


def scr_panel(t, pw=600, ph=1060):
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph), (18, 18, 22, 255)); d = ImageDraw.Draw(sc)
    A.status(d, s, pw)
    d.text((22 * s, 50 * s), 'Boshqaruv paneli', font=f('Inter-Black.otf', 24 * s), fill=WHITE)
    d.text((22 * s, 84 * s), 'Barcha buyurtmalar', font=f('Inter-SemiBold.otf', 14 * s), fill=GOLD)
    rows = [('Buyurtma #A12', 'Tort × 1', 'YANGI', GOLD), ('Buyurtma #A11', 'Kofe × 2', 'YO\'LDA', (90, 90, 100)),
            ('Buyurtma #A10', 'Gul guldastasi', 'YETKAZILDI ✓', GREEN), ('Buyurtma #A09', "Sovg'a to'plami", 'YETKAZILDI ✓', GREEN)]
    for i, (a, b, st, col) in enumerate(rows):
        k = ease((t - 0.15 - 0.4 * i) / 0.35)
        if k <= 0:
            continue
        y = (118 + i * 104) * s - (1 - k) * 40 * s
        ov = Image.new('RGBA', (pw, ph)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle([18 * s, y, pw - 18 * s, y + 90 * s], 16 * s, fill=CARD + (int(255 * k),), outline=col + (int(255 * k),), width=int(3 * s))
        od.text((34 * s, y + 14 * s), a, font=f('Inter-ExtraBold.otf', 18 * s), fill=WHITE + (int(255 * k),))
        od.text((34 * s, y + 50 * s), b, font=f('Inter-SemiBold.otf', 15 * s), fill=(210, 210, 210, int(255 * k)))
        fo = f('Inter-Bold.otf', 11 * s); tw = od.textlength(st, font=fo)
        od.rounded_rectangle([pw - 34 * s - tw - 20 * s, y + 14 * s, pw - 34 * s, y + 38 * s], 12 * s, fill=col + (int(255 * k),))
        od.text((pw - 34 * s - tw - 10 * s, y + 19 * s), st, font=fo, fill=(15, 15, 15, int(255 * k)))
        sc.alpha_composite(ov)
    return sc


def one(out, dur, fn, top):
    p = A.pipe(out)
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = A.bg(t)
        A.label(im, top, 255, 66, GOLD2, (t - 0.05) / 0.35)
        A.phone(im, fn(t), 240, 380, GOLD, t / 0.35)
        tag(im)
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait()


def two(out, dur):
    p = A.pipe(out)
    pw, ph = 440, 777
    lf = f('Inter-ExtraBold.otf', 44)
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = A.bg(t)
        A.label(im, 'IKKI VARIANT', 255, 66, GOLD2, (t - 0.05) / 0.35)
        A.phone(im, scr_shop(t + 1.0, pw, ph), 70, 420, GOLD, t / 0.35)
        d = ImageDraw.Draw(im); a = ease((t - 0.3) / 0.3)
        if a > 0:
            tx = 'TAYYOR'; tw = d.textlength(tx, font=lf)
            d.text((70 + (pw - tw) / 2, 1225), tx, font=lf, fill=tuple(int(v * a) for v in GOLD2) + (255,))
        k2 = (t - 0.9) / 0.4
        if k2 > 0:
            A.phone(im, scr_shop(t + 0.2, pw, ph, BLUE, 'YOUR BRAND'), 570, 420, BLUE, k2)
            a = ease((t - 1.2) / 0.3); d = ImageDraw.Draw(im)
            tx = "O'Z BRENDINGIZ"; tw = d.textlength(tx, font=lf)
            d.text((570 + (pw - tw) / 2, 1225), tx, font=lf, fill=tuple(int(v * a) for v in (150, 200, 255)) + (255,))
        tag(im, 1285)
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    o = sys.argv[1]
    w = sys.argv[2:] or ['shop', 'push', 'panel', 'two', 'end']
    if 'shop' in w: one(os.path.join(o, 'shop.mp4'), 3.0, scr_shop, 'BIR BOSISHDA BUYURTMA')
    if 'push' in w: one(os.path.join(o, 'push.mp4'), 3.0, scr_push, 'AKSIYA — DARHOL TELEFONGA')
    if 'panel' in w: one(os.path.join(o, 'panel.mp4'), 3.2, scr_panel, 'HAMMASI BITTA PANELDA')
    if 'two' in w: two(os.path.join(o, 'two.mp4'), 7.4)
    if 'end' in w:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
        import motion
        motion.endcard(os.path.join(o, 'endcard.mp4'), 4.4, ('Sizga ham', 'shunday ilova', 'kerakmi?'), ("Direct'ga «INFO»", 'yozing'))
