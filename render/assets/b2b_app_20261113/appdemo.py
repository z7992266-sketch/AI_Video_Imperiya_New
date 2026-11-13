"""B2B SAS app demo scenes (generic demo UI, no real brand, no prices) as full 1080x1920 clips:
gold-framed phone(s) on black+gold background. Usage: python3 appdemo.py outdir"""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = '/usr/share/fonts/opentype/inter/'
f = lambda n, s: ImageFont.truetype(FD + n, int(s))
GOLD = (212, 175, 55); GOLD2 = (255, 214, 102); WHITE = (245, 245, 245); GREY = (150, 150, 160)
BG = (14, 14, 18); CARD = (30, 30, 38); GREEN = (46, 204, 113)
ease = lambda x: 1 - (1 - max(0.0, min(1.0, x))) ** 3
def back(x, s=1.6):
    x = max(0.0, min(1.0, x)); x -= 1
    return x * x * ((s + 1) * x + s) + 1
random.seed(5)
DUST = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4), random.uniform(20, 60), random.uniform(0, 6.3)) for _ in range(60)]


def bg(t):
    im = Image.new('RGBA', (W, H), (8, 8, 10, 255))
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([-150, 450, W + 150, 1500], fill=55)
    im.paste((48, 38, 10, 255), mask=g.filter(ImageFilter.GaussianBlur(170)))
    d = ImageDraw.Draw(im)
    for (px, py, r, sp, ph) in DUST:
        yy = (py - sp * t * 3) % H; a = 0.5 + 0.5 * math.sin(t * 2 + ph)
        d.ellipse([px - r, yy - r, px + r, yy + r], fill=tuple(int(v * (0.2 + 0.5 * a)) for v in GOLD) + (255,))
    return im


def phone(im, scr, x, y, col=GOLD, k=1.0):
    """paste screen with gold rounded frame + glow; k = slide-in progress"""
    pw, ph = scr.size
    yy = int(y + (1 - ease(k)) * 120)
    gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.rounded_rectangle([x - 18, yy - 18, x + pw + 18, yy + ph + 18], 70, fill=col + (110,))
    gl = gl.filter(ImageFilter.GaussianBlur(22))
    a = min(1.0, k * 2)
    if a < 1:
        gl.putalpha(gl.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(gl)
    fr = Image.new('RGBA', (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fr)
    fd.rounded_rectangle([x - 10, yy - 10, x + pw + 10, yy + ph + 10], 62, fill=col + (255,))
    m = Image.new('L', (pw, ph), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, pw - 1, ph - 1], 52, fill=255)
    fr.paste(scr, (x, yy), m)
    if a < 1:
        fr.putalpha(fr.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(fr)


def label(im, text, y, size=64, col=GOLD2, k=1.0):
    if k <= 0:
        return
    d = ImageDraw.Draw(im); fo = f('Inter-ExtraBold.otf', size)
    lay = Image.new('RGBA', (W, size + 40), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    tw = ld.textlength(text, font=fo)
    ld.text(((W - tw) / 2 + 3, 13), text, font=fo, fill=(0, 0, 0, 200))
    ld.text(((W - tw) / 2, 10), text, font=fo, fill=col + (255,))
    sc = 0.75 + 0.25 * back(k)
    lay = lay.resize((int(W * sc), int((size + 40) * sc)), Image.LANCZOS)
    lay.putalpha(lay.split()[3].point(lambda v: int(v * min(1, k * 2))))
    im.alpha_composite(lay, (int((W - lay.width) / 2), int(y)))


def demo_tag(im):
    d = ImageDraw.Draw(im); fo = f('Inter-SemiBold.otf', 30)
    d.text((W - 200, 1470), 'демо', font=fo, fill=(170, 170, 170, 255))


# ---------- phone screens (S = scale) ----------
def status(d, s, pw, theme=GOLD):
    d.text((26 * s, 18 * s), '9:41', font=f('Inter-Bold.otf', 15 * s), fill=WHITE)
    d.rounded_rectangle([pw - 60 * s, 22 * s, pw - 26 * s, 33 * s], 4, outline=WHITE, width=2)


def scr_order(t, pw=600, ph=1060, theme=GOLD, brand=None):
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph), BG + (255,)); d = ImageDraw.Draw(sc)
    status(d, s, pw)
    if brand:
        d.rounded_rectangle([22 * s, 52 * s, 62 * s, 92 * s], 10 * s, fill=theme)
        d.text((31 * s, 61 * s), 'YB', font=f('Inter-Black.otf', 15 * s), fill=(15, 15, 20))
        d.text((72 * s, 50 * s), brand, font=f('Inter-Black.otf', 19 * s), fill=WHITE)
        d.text((72 * s, 74 * s), 'ВАШ БРЕНД', font=f('Inter-SemiBold.otf', 11 * s), fill=theme)
    else:
        d.text((22 * s, 54 * s), 'Ваше меню', font=f('Inter-Black.otf', 26 * s), fill=WHITE)
    items = ['Капучино', 'Круассан', 'Салат Цезарь', 'Лимонад']
    for i, n in enumerate(items):
        k = ease((t - 0.1 * i) / 0.4)
        y = (110 + i * 82) * s + (1 - k) * 30 * s
        d.rounded_rectangle([18 * s, y, pw - 18 * s, y + 68 * s], 16 * s, fill=CARD)
        d.rounded_rectangle([30 * s, y + 10 * s, 78 * s, y + 58 * s], 12 * s, fill=(70 + i * 28, 52, 40))
        d.text((92 * s, y + 13 * s), n, font=f('Inter-Bold.otf', 19 * s), fill=WHITE)
        d.text((92 * s, y + 40 * s), '★ 4.%d' % (9 - i % 3), font=f('Inter-Regular.otf', 14 * s), fill=theme)
        sel = t > 1.1 and i == 0
        d.ellipse([pw - 58 * s, y + 20 * s, pw - 30 * s, y + 48 * s], fill=theme if sel else (70, 70, 80))
    press = 1.0 - 0.06 * math.exp(-((t - 1.6) / 0.12) ** 2)
    bw, bh = (pw - 44 * s) * press, 64 * s * press
    bx, by = (pw - bw) / 2, 470 * s + (64 * s - bh) / 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], 20 * s, fill=theme)
    tx = 'Заказать в 1 клик'; fo = f('Inter-Bold.otf', 22 * s); tw = d.textlength(tx, font=fo)
    d.text(((pw - tw) / 2, by + bh / 2 - 14 * s), tx, font=fo, fill=(20, 20, 20))
    if t > 1.6:
        r = ease((t - 1.6) / 0.5) * 70 * s; a = max(0, 1 - (t - 1.6) / 0.5)
        ov = Image.new('RGBA', (pw, ph)); ImageDraw.Draw(ov).ellipse([pw / 2 - r, 502 * s - r, pw / 2 + r, 502 * s + r], outline=(255, 255, 255, int(200 * a)), width=5)
        sc.alpha_composite(ov); d = ImageDraw.Draw(sc)
    if t > 2.0:
        k = ease((t - 2.0) / 0.35); y = (560 + (1 - k) * 60) * s
        d.rounded_rectangle([40 * s, y, pw - 40 * s, y + 50 * s], 25 * s, fill=GREEN)
        fo = f('Inter-Bold.otf', 18 * s); tx = 'Заказ принят ✓'; tw = d.textlength(tx, font=fo)
        d.text(((pw - tw) / 2, y + 13 * s), tx, font=fo, fill=WHITE)
    return sc


def scr_notify(t, pw=600, ph=1060):
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph)); d = ImageDraw.Draw(sc)
    for yy in range(ph):
        c = int(20 + 30 * yy / ph); d.line([0, yy, pw, yy], fill=(c, c // 2 + 10, c + 30))
    fo = f('Inter-Bold.otf', 64 * s); tx = '9:41'; tw = d.textlength(tx, font=fo)
    d.text(((pw - tw) / 2, 60 * s), tx, font=fo, fill=WHITE)
    notes = [('Ваше кафе', 'Ваш заказ готов! Заберите на кассе'), ('Ваше кафе', 'Подарок для постоянных клиентов'),
             ('Ваше кафе', 'Вам начислены бонусы ★')]
    for i, (a, b) in enumerate(notes):
        k = ease((t - 0.25 - 0.75 * i) / 0.35)
        if k <= 0:
            continue
        y = (220 + i * 96) * s - (1 - k) * 40 * s
        ov = Image.new('RGBA', (pw, ph)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle([14 * s, y, pw - 14 * s, y + 82 * s], 18 * s, fill=(245, 245, 245, int(235 * k)))
        od.rounded_rectangle([26 * s, y + 14 * s, 56 * s, y + 44 * s], 8 * s, fill=GOLD + (int(255 * k),))
        od.text((68 * s, y + 12 * s), a, font=f('Inter-Bold.otf', 15 * s), fill=(30, 30, 30, int(255 * k)))
        od.text((68 * s, y + 38 * s), b, font=f('Inter-Regular.otf', 13 * s), fill=(60, 60, 60, int(255 * k)))
        sc.alpha_composite(ov)
    return sc


def scr_turnkey(t, pw=600, ph=1060):
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph), BG + (255,)); d = ImageDraw.Draw(sc)
    status(d, s, pw)
    d.text((22 * s, 54 * s), 'Приложение', font=f('Inter-Black.otf', 26 * s), fill=WHITE)
    d.text((22 * s, 90 * s), 'под ключ', font=f('Inter-Bold.otf', 26 * s), fill=GOLD)
    rows = ['iOS + Android', 'Дизайн', 'Меню и заказы', 'Push-уведомления', 'Бонусы клиентам', 'Ваш логотип и цвета']
    for i, r in enumerate(rows):
        k = ease((t - 0.15 - 0.4 * i) / 0.3)
        y = (160 + i * 66) * s
        d.rounded_rectangle([18 * s, y, pw - 18 * s, y + 52 * s], 14 * s, fill=CARD)
        d.text((70 * s, y + 14 * s), r, font=f('Inter-Bold.otf', 18 * s), fill=WHITE if k > 0 else GREY)
        if k > 0:
            rr = 13 * s * k
            d.ellipse([40 * s - rr, y + 26 * s - rr, 40 * s + rr, y + 26 * s + rr], fill=GREEN)
            if k > 0.6:
                d.line([33 * s, y + 26 * s, 38 * s, y + 32 * s, 48 * s, y + 19 * s], fill=WHITE, width=int(3 * s))
        else:
            d.ellipse([27 * s, y + 13 * s, 53 * s, y + 39 * s], outline=GREY, width=2)
    d.text((22 * s, ph - 52 * s), 'B2B SAS', font=f('Inter-Bold.otf', 18 * s), fill=GOLD)
    return sc


def pipe(out):
    return subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                             '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)


def one_phone(out, dur, scrfn, top, sub=None):
    p = pipe(out)
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = bg(t)
        label(im, top, 255, 66, GOLD2, (t - 0.05) / 0.35)
        phone(im, scrfn(t), 240, 380, GOLD, t / 0.35)
        demo_tag(im)
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait()


BLUE = (64, 156, 255)
def two_options(out, dur):
    p = pipe(out)
    pw, ph = 440, 777
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = bg(t)
        label(im, 'ДВА ВАРИАНТА', 255, 66, GOLD2, (t - 0.05) / 0.35)
        # left: ready app (gold)
        phone(im, scr_order(t + 1.0, pw, ph), 70, 420, GOLD, t / 0.35)
        label_small = f('Inter-ExtraBold.otf', 44)
        d = ImageDraw.Draw(im)
        a = ease((t - 0.3) / 0.3)
        if a > 0:
            tx = 'ГОТОВОЕ'; tw = d.textlength(tx, font=label_small)
            d.text((70 + (pw - tw) / 2, 1225), tx, font=label_small, fill=tuple(int(v * a) for v in GOLD2) + (255,))
        # right: your brand (blue theme, placeholder logo)
        k2 = (t - 1.0) / 0.4
        if k2 > 0:
            phone(im, scr_order(t + 0.2, pw, ph, BLUE, 'YOUR BRAND'), 570, 420, BLUE, k2)
            a = ease((t - 1.3) / 0.3)
            d = ImageDraw.Draw(im)
            tx = 'ВАШ БРЕНД'; tw = d.textlength(tx, font=label_small)
            d.text((570 + (pw - tw) / 2, 1225), tx, font=label_small, fill=tuple(int(v * a) for v in (150, 200, 255)) + (255,))
        ImageDraw.Draw(im).text((W - 200, 1285), 'демо', font=f('Inter-SemiBold.otf', 30), fill=(170, 170, 170, 255))
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    o = sys.argv[1]
    which = sys.argv[2:] or ['order', 'notify', 'turnkey', 'two']
    if 'order' in which: one_phone(os.path.join(o, 'order.mp4'), 3.2, scr_order, 'ЗАКАЗ В 1 КЛИК')
    if 'notify' in which: one_phone(os.path.join(o, 'notify.mp4'), 3.0, scr_notify, 'УВЕДОМЛЕНИЯ И БОНУСЫ')
    if 'turnkey' in which: one_phone(os.path.join(o, 'turnkey.mp4'), 4.6, scr_turnkey, 'ПОД КЛЮЧ')  # 4.6 s
    if 'two' in which: two_options(os.path.join(o, 'two.mp4'), 5.2)
