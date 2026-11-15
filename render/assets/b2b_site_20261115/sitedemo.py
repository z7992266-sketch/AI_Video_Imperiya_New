"""B2B SAS website demo scenes (generic demo site, no real brand, no prices) as 1080x1920 clips.
Reuses the phone/background helpers of b2b_app_20261113/appdemo.py. Usage: python3 sitedemo.py outdir [site lead two]"""
import math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'b2b_app_20261113'))
from appdemo import *  # noqa  W,H,FPS,f,GOLD,GOLD2,WHITE,GREY,BG,CARD,GREEN,ease,back,bg,phone,label,demo_tag,status,pipe
from PIL import Image, ImageDraw

BLUE = (64, 156, 255)


def page(pw, s, theme, brand):
    """full-length mobile web page (taller than the screen) -> scrolled later"""
    ph = int(1110 * s)
    pg = Image.new('RGBA', (pw, ph), BG + (255,)); d = ImageDraw.Draw(pg)
    # header bar
    d.rectangle([0, 0, pw, 64 * s], fill=(20, 20, 26))
    d.rounded_rectangle([16 * s, 14 * s, 52 * s, 50 * s], 9 * s, fill=theme)
    d.text((23 * s, 21 * s), 'YB' if brand else 'B', font=f('Inter-Black.otf', 15 * s), fill=(15, 15, 20))
    d.text((62 * s, 20 * s), brand or 'Ваш бизнес', font=f('Inter-Bold.otf', 18 * s), fill=WHITE)
    for i in range(3):
        d.rounded_rectangle([pw - 50 * s, (24 + i * 8) * s, pw - 22 * s, (27 + i * 8) * s], 2, fill=WHITE)
    # hero
    for yy in range(int(64 * s), int(330 * s)):
        k = (yy - 64 * s) / (266 * s)
        c = tuple(int(a * (1 - k) + b * k) for a, b in zip((70, 52, 20) if theme == GOLD else (20, 50, 95), (16, 16, 20)))
        d.line([0, yy, pw, yy], fill=c)
    d.text((22 * s, 100 * s), 'Ваш сайт', font=f('Inter-Black.otf', 32 * s), fill=WHITE)
    d.text((22 * s, 140 * s), 'работает 24/7', font=f('Inter-Black.otf', 32 * s), fill=theme)
    d.text((22 * s, 190 * s), 'Услуги, контакты и заявка —', font=f('Inter-Regular.otf', 15 * s), fill=(210, 210, 215))
    d.text((22 * s, 212 * s), 'в одном месте', font=f('Inter-Regular.otf', 15 * s), fill=(210, 210, 215))
    d.rounded_rectangle([22 * s, 250 * s, 220 * s, 296 * s], 14 * s, fill=theme)
    d.text((40 * s, 262 * s), 'Оставить заявку', font=f('Inter-Bold.otf', 16 * s), fill=(20, 20, 20))
    # services
    d.text((22 * s, 352 * s), 'Услуги', font=f('Inter-Black.otf', 24 * s), fill=WHITE)
    for i, n in enumerate(['Консультация', 'Доставка', 'Онлайн-запись', 'Подарочные карты']):
        y = (395 + i * 74) * s
        d.rounded_rectangle([18 * s, y, pw - 18 * s, y + 62 * s], 14 * s, fill=CARD)
        d.rounded_rectangle([30 * s, y + 12 * s, 68 * s, y + 50 * s], 10 * s, fill=tuple(int(v * 0.55) for v in theme))
        d.text((82 * s, y + 19 * s), n, font=f('Inter-Bold.otf', 18 * s), fill=WHITE)
        d.text((pw - 44 * s, y + 16 * s), '›', font=f('Inter-Bold.otf', 24 * s), fill=theme)
    # contacts + map
    y = 720 * s
    d.text((22 * s, y), 'Контакты', font=f('Inter-Black.otf', 24 * s), fill=WHITE)
    d.rounded_rectangle([18 * s, y + 44 * s, pw - 18 * s, y + 224 * s], 16 * s, fill=(34, 40, 46))
    for k in range(7):
        d.line([18 * s + k * 50 * s, y + 44 * s, 18 * s + k * 50 * s + 60 * s, y + 224 * s], fill=(52, 60, 68), width=int(5 * s))
    d.line([18 * s, y + 140 * s, pw - 18 * s, y + 110 * s], fill=(70, 78, 88), width=int(9 * s))
    cx, cy = pw / 2, y + 120 * s
    d.ellipse([cx - 16 * s, cy - 40 * s, cx + 16 * s, cy - 8 * s], fill=theme)
    d.polygon([(cx - 12 * s, cy - 18 * s), (cx + 12 * s, cy - 18 * s), (cx, cy + 4 * s)], fill=theme)
    d.ellipse([cx - 6 * s, cy - 30 * s, cx + 6 * s, cy - 18 * s], fill=(20, 20, 20))
    y2 = y + 244 * s
    for i, (ic, tx) in enumerate([('✆', 'Позвонить'), ('✈', 'Написать в Telegram')]):
        yy = y2 + i * 62 * s
        d.rounded_rectangle([18 * s, yy, pw - 18 * s, yy + 50 * s], 14 * s, fill=CARD)
        d.ellipse([32 * s, yy + 15 * s, 52 * s, yy + 35 * s], fill=theme)
        d.text((66 * s, yy + 13 * s), tx, font=f('Inter-Bold.otf', 17 * s), fill=WHITE)
    return pg


def scr_site(t, pw=600, ph=1060, theme=GOLD, brand=None, scroll=True):
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph), BG + (255,))
    pg = page(pw, s, theme, brand)
    # scroll down (0.3-1.6 s), back up (1.9-2.5 s), tap the button (2.7 s), form sent (3.0 s)
    maxs = pg.height - ph + 40 * s
    if scroll:
        off = maxs * ease((t - 0.3) / 1.3) * (1 - ease((t - 1.9) / 0.6))
    else:
        off = 0
    sc.alpha_composite(pg.crop((0, int(off), pw, int(off) + ph - int(44 * s))), (0, int(44 * s)))
    d = ImageDraw.Draw(sc)
    d.rectangle([0, 0, pw, 44 * s], fill=(10, 10, 12))
    status(d, s, pw)
    # url bar
    d.rounded_rectangle([90 * s, 10 * s, pw - 90 * s, 36 * s], 10 * s, fill=(40, 40, 48))
    fo = f('Inter-SemiBold.otf', 12 * s); tx = 'ваш-сайт.uz'; tw = d.textlength(tx, font=fo)
    d.text(((pw - tw) / 2, 15 * s), tx, font=fo, fill=(200, 200, 205))
    if scroll and t > 2.65:
        bx, by = 22 * s + 99 * s, (250 + 44 + 23) * s
        r = ease((t - 2.65) / 0.4) * 70 * s; a = max(0, 1 - (t - 2.65) / 0.4)
        ov = Image.new('RGBA', (pw, ph)); ImageDraw.Draw(ov).ellipse([bx - r, by - r, bx + r, by + r], outline=(255, 255, 255, int(220 * a)), width=5)
        sc.alpha_composite(ov); d = ImageDraw.Draw(sc)
    if scroll and t > 3.0:
        k = ease((t - 3.0) / 0.35); y = ph - (150 - (1 - k) * -60) * s
        d.rounded_rectangle([30 * s, y, pw - 30 * s, y + 56 * s], 28 * s, fill=GREEN)
        fo = f('Inter-Bold.otf', 18 * s); tx = 'Заявка отправлена ✓'; tw = d.textlength(tx, font=fo)
        d.text(((pw - tw) / 2, y + 16 * s), tx, font=fo, fill=WHITE)
    return sc


def scr_lead(t, pw=600, ph=1060):
    """lock screen: new lead from the site arrives in Telegram"""
    s = pw / 360.0
    sc = Image.new('RGBA', (pw, ph)); d = ImageDraw.Draw(sc)
    for yy in range(ph):
        c = int(18 + 28 * yy / ph); d.line([0, yy, pw, yy], fill=(c, c // 2 + 12, c + 34))
    fo = f('Inter-Bold.otf', 64 * s); tx = '9:41'; tw = d.textlength(tx, font=fo)
    d.text(((pw - tw) / 2, 60 * s), tx, font=fo, fill=WHITE)
    notes = [('Telegram · Бот сайта', 'Новая заявка с сайта', 'Услуга: Онлайн-запись'),
             ('Telegram · Бот сайта', 'Новая заявка с сайта', 'Услуга: Консультация')]
    for i, (a, b, c) in enumerate(notes):
        k = ease((t - 0.3 - 1.0 * i) / 0.35)
        if k <= 0:
            continue
        y = (220 + i * 112) * s - (1 - k) * 40 * s
        ov = Image.new('RGBA', (pw, ph)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle([14 * s, y, pw - 14 * s, y + 98 * s], 18 * s, fill=(245, 245, 245, int(238 * k)))
        od.ellipse([26 * s, y + 14 * s, 58 * s, y + 46 * s], fill=(42, 171, 238, int(255 * k)))
        od.polygon([(34 * s, y + 31 * s), (51 * s, y + 23 * s), (46 * s, y + 39 * s)], fill=(255, 255, 255, int(255 * k)))
        od.text((70 * s, y + 12 * s), a, font=f('Inter-SemiBold.otf', 13 * s), fill=(90, 90, 95, int(255 * k)))
        od.text((70 * s, y + 34 * s), b, font=f('Inter-Bold.otf', 16 * s), fill=(25, 25, 30, int(255 * k)))
        od.text((70 * s, y + 60 * s), c, font=f('Inter-Regular.otf', 14 * s), fill=(60, 60, 66, int(255 * k)))
        sc.alpha_composite(ov)
    return sc


def two_sites(out, dur):
    p = pipe(out)
    pw, ph = 440, 777
    lf = f('Inter-ExtraBold.otf', 44)
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = bg(t)
        label(im, 'ДВА ВАРИАНТА', 255, 66, GOLD2, (t - 0.05) / 0.35)
        phone(im, scr_site(t, pw, ph, GOLD, None, False), 70, 420, GOLD, t / 0.35)
        d = ImageDraw.Draw(im); a = ease((t - 0.3) / 0.3)
        if a > 0:
            tx = 'ГОТОВОЕ'; tw = d.textlength(tx, font=lf)
            d.text((70 + (pw - tw) / 2, 1225), tx, font=lf, fill=tuple(int(v * a) for v in GOLD2) + (255,))
        k2 = (t - 0.9) / 0.4
        if k2 > 0:
            phone(im, scr_site(t, pw, ph, BLUE, 'YOUR BRAND', False), 570, 420, BLUE, k2)
            a = ease((t - 1.2) / 0.3); d = ImageDraw.Draw(im)
            tx = 'ВАШ БРЕНД'; tw = d.textlength(tx, font=lf)
            d.text((570 + (pw - tw) / 2, 1225), tx, font=lf, fill=tuple(int(v * a) for v in (150, 200, 255)) + (255,))
        ImageDraw.Draw(im).text((W - 200, 1285), 'демо', font=f('Inter-SemiBold.otf', 30), fill=(170, 170, 170, 255))
        p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    o = sys.argv[1]
    which = sys.argv[2:] or ['site', 'lead', 'two']
    if 'site' in which: one_phone(os.path.join(o, 'site.mp4'), 3.8, scr_site, 'САЙТ ДЛЯ ТЕЛЕФОНА')
    if 'lead' in which: one_phone(os.path.join(o, 'lead.mp4'), 2.8, scr_lead, 'ЗАЯВКА — В TELEGRAM')
    if 'two' in which: two_sites(os.path.join(o, 'two.mp4'), 5.6)
