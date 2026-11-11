"""Telegram-bot chat demo (generic, no real brand) as a full 1080x1920 scene: gold-framed phone on black+gold bg."""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = '/usr/share/fonts/opentype/inter/'
f = lambda n, s: ImageFont.truetype(FD + n, s)
GOLD = (212, 175, 55); GOLD2 = (255, 214, 102); WHITE = (245, 245, 245); GREY = (150, 150, 160)
ease = lambda x: 1 - (1 - max(0.0, min(1.0, x))) ** 3
def back(x, s=1.6):
    x = max(0.0, min(1.0, x)); x -= 1
    return x * x * ((s + 1) * x + s) + 1

PX, PY, PW, PH = 230, 330, 620, 1220     # phone box (inside safe area 270..1536)
random.seed(3)
DUST = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4), random.uniform(20, 60), random.uniform(0, 6.3)) for _ in range(60)]


def wrap(d, text, font, maxw):
    out, line = [], ''
    for w in text.split(' '):
        t = (line + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw:
            line = t
        else:
            out.append(line); line = w
    out.append(line)
    return out


def bubble(scr, d, y, text, me, k, font):
    lines = wrap(d, text, font, PW - 200)
    lh = font.size + 10
    bw = max(d.textlength(l, font=font) for l in lines) + 44
    bh = lh * len(lines) + 28
    x = PW - 24 - bw if me else 24
    lay = Image.new('RGBA', (int(bw) + 4, int(bh) + 4), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([0, 0, bw, bh], 26, fill=(43, 82, 120) if me else (36, 36, 46))
    for i, l in enumerate(lines):
        ld.text((22, 14 + i * lh), l, font=font, fill=WHITE)
    sc = 0.6 + 0.4 * back(k)
    lay = lay.resize((max(1, int(lay.width * sc)), max(1, int(lay.height * sc))), Image.LANCZOS)
    al = lay.split()[3].point(lambda v: int(v * min(1, k * 2))); lay.putalpha(al)
    ox = int(x + (bw - lay.width) * (1 if me else 0))
    scr.alpha_composite(lay, (ox, int(y + (bh - lay.height) / 2)))
    return y + bh + 18


def frame(t, brand=False):
    im = Image.new('RGBA', (W, H), (8, 8, 10, 255)); d = ImageDraw.Draw(im)
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([-150, 450, W + 150, 1500], fill=55)
    im.paste((48, 38, 10, 255), mask=g.filter(ImageFilter.GaussianBlur(170)))
    d = ImageDraw.Draw(im)
    for (px, py, r, sp, ph) in DUST:
        yy = (py - sp * t * 3) % H; a = 0.5 + 0.5 * math.sin(t * 2 + ph)
        d.ellipse([px - r, yy - r, px + r, yy + r], fill=tuple(int(v * (0.2 + 0.5 * a)) for v in GOLD) + (255,))
    # phone screen
    scr = Image.new('RGBA', (PW, PH), (16, 16, 22, 255)); sd = ImageDraw.Draw(scr)
    sd.rectangle([0, 0, PW, 150], fill=(24, 24, 32))
    sd.text((30, 22), '02:14', font=f('Inter-Bold.otf', 28), fill=WHITE)
    # avatar + name
    if brand:
        sd.ellipse([30, 70, 100, 140], fill=GOLD)
        sd.text((44, 92), 'ВБ', font=f('Inter-Black.otf', 26), fill=(20, 20, 20))
        sd.text((120, 76), 'ВАШ БРЕНД', font=f('Inter-ExtraBold.otf', 32), fill=GOLD2)
    else:
        sd.ellipse([30, 70, 100, 140], fill=(60, 110, 160))
        sd.text((50, 88), 'B', font=f('Inter-Black.otf', 32), fill=WHITE)
        sd.text((120, 76), 'Ваш бот', font=f('Inter-ExtraBold.otf', 32), fill=WHITE)
    sd.text((120, 114), 'онлайн 24/7', font=f('Inter-Medium.otf', 22), fill=(110, 200, 140))
    fb = f('Inter-SemiBold.otf', 30)
    y = 190
    msgs = [(0.2, 'Здравствуйте! Вы работаете? Хочу заказать', True),
            (1.6, 'Здравствуйте! Да, мы на связи 24/7. Что вас интересует?', False)]
    if brand:
        msgs = [(0.1, 'Здравствуйте! Вы работаете? Хочу заказать', True),
                (0.5, 'Здравствуйте! Да, мы на связи 24/7. Что вас интересует?', False)]
    # typing dots before bot reply
    if not brand and 0.9 < t < 1.6:
        sd.rounded_rectangle([24, 330, 150, 390], 26, fill=(36, 36, 46))
        for i in range(3):
            a = 0.5 + 0.5 * math.sin(t * 12 - i)
            sd.ellipse([50 + i * 30, 352, 66 + i * 30, 368], fill=tuple(int(v * a) for v in WHITE))
    for (t0, txt, me) in msgs:
        if t >= t0:
            y = bubble(scr, sd, y, txt, me, (t - t0) / 0.35, fb)
    # buttons
    tb = 0.8 if brand else 2.4
    btns = ['Сайт', 'Приложение', 'AI-видео']
    if t >= tb:
        for i, b in enumerate(btns):
            k = ease((t - tb - 0.12 * i) / 0.3)
            if k <= 0: continue
            bx, by = 24, y + i * 78
            tap = (not brand) and i == 0 and t > 3.3
            sd.rounded_rectangle([bx, by, PW - 24, by + 64], 20, fill=(GOLD if tap else (30, 30, 40)), outline=GOLD, width=3)
            fbt = f('Inter-Bold.otf', 30); tw = sd.textlength(b, font=fbt)
            sd.text(((PW - tw) / 2, by + 14), b, font=fbt, fill=(20, 20, 20) if tap else GOLD2)
        y += 3 * 78 + 10
    if not brand:
        if t >= 3.6:
            y = bubble(scr, sd, y, 'Сайт', True, (t - 3.6) / 0.3, fb)
        if t >= 4.4:
            y = bubble(scr, sd, y, 'Отлично! Оставьте номер — менеджер свяжется с вами утром.', False, (t - 4.4) / 0.35, fb)
        if t >= 5.6:
            k = ease((t - 5.6) / 0.35)
            yy = PH - 120 + int(40 * (1 - k))
            sd.rounded_rectangle([60, yy, PW - 60, yy + 72], 36, fill=(46, 204, 113))
            tx = 'Заявка передана ✓'; ft = f('Inter-ExtraBold.otf', 30); tw = sd.textlength(tx, font=ft)
            sd.text(((PW - tw) / 2, yy + 18), tx, font=ft, fill=WHITE)
    # rounded mask + gold frame + glow
    m = Image.new('L', (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, PW, PH], 54, fill=255)
    glow = Image.new('L', (W, H), 0); ImageDraw.Draw(glow).rounded_rectangle([PX - 12, PY - 12, PX + PW + 12, PY + PH + 12], 64, fill=150)
    im.paste((212, 175, 55, 255), mask=glow.filter(ImageFilter.GaussianBlur(28)))
    sk = ease(t / 0.4)
    oy = int(80 * (1 - sk))
    im.paste(scr, (PX, PY + oy), m)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([PX - 6, PY - 6 + oy, PX + PW + 6, PY + PH + 6 + oy], 58, outline=GOLD, width=7)
    # demo label
    fl = f('Inter-SemiBold.otf', 26); lt = 'демо'; lw = d.textlength(lt, font=fl)
    d.text((PX + PW - lw - 10, PY + PH + 18), lt, font=fl, fill=GREY)
    return im.convert('RGB')


def render(out, dur, brand=False):
    p = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for i in range(int(dur * FPS)):
        p.stdin.write(frame(i / FPS, brand).tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    o = sys.argv[1]
    render(os.path.join(o, 'chat.mp4'), float(sys.argv[2]) if len(sys.argv) > 2 else 7.0)
    render(os.path.join(o, 'chat_brand.mp4'), float(sys.argv[3]) if len(sys.argv) > 3 else 3.2, brand=True)
