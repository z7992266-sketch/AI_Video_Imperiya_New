"""Motion-graphics layers for the B2B Laura ad: feature chips (alpha layer) and an animated end card."""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
FD = '/usr/share/fonts/opentype/inter/'
f = lambda n, s: ImageFont.truetype(FD + n, s)
GOLD = (212, 175, 55); GOLD2 = (255, 214, 102); WHITE = (250, 250, 250)
ease = lambda x: 1 - (1 - max(0.0, min(1.0, x))) ** 3
def back(x, s=1.7):
    x = max(0.0, min(1.0, x)); x -= 1
    return x * x * ((s + 1) * x + s) + 1


def pipe(out, alpha):
    if alpha:
        args = ['-c:v', 'qtrle', '-pix_fmt', 'argb']
        fmt = 'rgba'
    else:
        args = ['-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p']
        fmt = 'rgb24'
    return subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', fmt, '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-'] + args + [out],
                            stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)


def chip_img(text, check=True):
    ft = f('Inter-ExtraBold.otf', 44)
    tw = int(ImageDraw.Draw(Image.new('RGB', (1, 1))).textlength(text, font=ft))
    w, h = tw + (110 if check else 60), 92
    im = Image.new('RGBA', (w + 40, h + 40), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 26, 20 + w, 26 + h], 46, fill=(0, 0, 0, 150))
    im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], 46, fill=(12, 12, 16, 225), outline=GOLD, width=4)
    x = 50
    if check:
        d.ellipse([x, 20 + 22, x + 48, 20 + 70], fill=GOLD)
        d.line([x + 12, 20 + 47, x + 21, 20 + 57, x + 37, 20 + 35], fill=(20, 20, 20), width=6)
        x += 64
    d.text((x, 20 + 18), text, font=ft, fill=WHITE)
    return im


def chips(out, items, dur, x_right=1044):
    """items: [(t_in, text, y)] ; all chips leave together at dur-0.35"""
    imgs = [chip_img(t) for _, t, _ in items]
    p = pipe(out, True)
    for i in range(int(dur * FPS)):
        t = i / FPS
        fr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        out_k = ease((t - (dur - 0.35)) / 0.35)
        for (ti, _, y), im in zip(items, imgs):
            k = back((t - ti) / 0.38)
            if t < ti:
                continue
            sc = 0.6 + 0.4 * k
            a = min(1.0, (t - ti) / 0.15) * (1 - out_k)
            iw, ih = int(im.width * sc), int(im.height * sc)
            ci = im.resize((max(1, iw), max(1, ih)), Image.LANCZOS)
            if a < 1:
                al = ci.split()[3].point(lambda v: int(v * a)); ci.putalpha(al)
            x = x_right - iw + int(80 * (1 - ease((t - ti) / 0.3))) + int(160 * out_k)
            fr.alpha_composite(ci, (x, y - ih // 2))
        p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()


def endcard(out, dur=3.8, title=('Вам нужно', 'такое', 'приложение?'), cta=('Напишите «ИНФО»', 'в Директ')):
    random.seed(7)
    parts = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4.5), random.uniform(20, 70), random.uniform(0, 6.28)) for _ in range(70)]
    fT = f('Inter-Black.otf', 112); fC = f('Inter-ExtraBold.otf', 76); fL = f('Inter-ExtraBold.otf', 64); fS = f('Inter-SemiBold.otf', 40)
    p = pipe(out, False)
    for i in range(int(dur * FPS)):
        t = i / FPS
        im = Image.new('RGB', (W, H), (8, 8, 10))
        d = ImageDraw.Draw(im)
        # radial vignette glow
        g = Image.new('L', (W, H), 0); gd = ImageDraw.Draw(g)
        gd.ellipse([-200, 500, W + 200, 1500], fill=int(40 + 15 * math.sin(t * 3)))
        im.paste((40, 32, 10), mask=g.filter(ImageFilter.GaussianBlur(160)))
        d = ImageDraw.Draw(im)
        for (px, py, r, sp, ph) in parts:  # rising gold dust
            y = (py - sp * t * 3) % H
            a = 0.5 + 0.5 * math.sin(t * 2 + ph)
            c = tuple(int(v * (0.25 + 0.6 * a)) for v in GOLD)
            d.ellipse([px - r, y - r, px + r, y + r], fill=c)
        # frame lines draw in
        k = ease(t / 0.6)
        d.rectangle([40, 40, 40 + int((W - 80) * k), 42], fill=GOLD)
        d.rectangle([W - 40 - int((W - 80) * k), H - 42, W - 40, H - 40], fill=GOLD)
        # logo
        a = ease((t - 0.1) / 0.4)
        lo = 'B2B SAS'; lw = d.textlength(lo, font=fL)
        d.text(((W - lw) / 2, 150 - 20 * (1 - a)), lo, font=fL, fill=tuple(int(v * a) for v in GOLD))
        d.rectangle([W / 2 - 120 * a, 250, W / 2 + 120 * a, 254], fill=GOLD)
        # title words pop in
        y = 640
        for j, line in enumerate(title):
            k = back((t - 0.25 - 0.18 * j) / 0.4)
            if t > 0.25 + 0.18 * j:
                lay = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                lw = ld.textlength(line, font=fT); ld.text(((W - lw) / 2, 10), line, font=fT, fill=WHITE)
                sc = 0.7 + 0.3 * k
                lay = lay.resize((int(W * sc), int(160 * sc)), Image.LANCZOS)
                im.paste(lay, (int((W - lay.width) / 2), int(y + (160 - lay.height) / 2)), lay)
            y += 140
        # CTA with shimmer sweep
        y = 1120
        for j, line in enumerate(cta):
            a = ease((t - 0.9 - 0.12 * j) / 0.35)
            if a <= 0:
                y += 96; continue
            lay = Image.new('RGBA', (W, 110), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            lw = ld.textlength(line, font=fC); ld.text(((W - lw) / 2, 8), line, font=fC, fill=GOLD + (255,))
            sx = int(((t - 1.4) % 1.6) / 1.6 * (W + 600)) - 300
            sh = Image.new('L', (W, 110), 0); ImageDraw.Draw(sh).polygon([(sx, 0), (sx + 90, 0), (sx + 30, 110), (sx - 60, 110)], fill=200)
            shine = Image.new('RGBA', (W, 110), GOLD2 + (255,))
            mask = Image.composite(sh.filter(ImageFilter.GaussianBlur(12)), Image.new('L', (W, 110), 0), lay.split()[3])
            lay = Image.composite(shine, lay, mask)
            al = lay.split()[3].point(lambda v: int(v * a)); lay.putalpha(al)
            im.paste(lay, (0, int(y + 30 * (1 - a))), lay)
            y += 96
        # bouncing arrow
        if t > 1.2:
            by = 1350 + 18 * abs(math.sin((t - 1.2) * 5))
            d = ImageDraw.Draw(im)
            d.polygon([(W / 2 - 46, by), (W / 2 + 46, by), (W / 2, by + 60)], fill=GOLD)
        a = ease((t - 1.3) / 0.4)
        u = 'b2bsasagency.com  ·  @B2BSAS_bot'; d = ImageDraw.Draw(im); uw = d.textlength(u, font=fS)
        d.text(((W - uw) / 2, 1700), u, font=fS, fill=tuple(int(v * a) for v in (225, 225, 225)))
        p.stdin.write(im.tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    o = sys.argv[1]
    chips(os.path.join(o, 'chips.mov'), [(0.25, 'Заказ в 1 клик', 1110), (2.6, 'Уведомления', 1222), (3.8, 'Постоянные клиенты', 1334)], 6.2)
    endcard(os.path.join(o, 'endcard_anim.mp4'))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '2.6', '-i', os.path.join(o, 'endcard_anim.mp4'), '-frames:v', '1', os.path.join(o, 'ec.jpg')])
