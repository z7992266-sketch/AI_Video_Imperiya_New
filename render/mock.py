"""Clean app-screen mockup clips (demo UI, no real brand) for the B2B side screen."""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 360, 640, 30
F = '/usr/share/fonts/opentype/inter/'
def font(sz, w='Bold'):
    for n in ('Inter-%s.otf' % w, 'Inter%s.otf' % w):
        p = os.path.join(F, n)
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.truetype('/tmp/claude-0/-home-claude/844ebc5a-648f-5142-9a2f-1a04ed1a7ee7/scratchpad/rw/render/fonts/' + os.listdir('/tmp/claude-0/-home-claude/844ebc5a-648f-5142-9a2f-1a04ed1a7ee7/scratchpad/rw/render/fonts')[0], sz)

GOLD = (212, 175, 55); BG = (14, 14, 18); CARD = (28, 28, 36); WHITE = (245, 245, 245); GREY = (150, 150, 160); GREEN = (46, 204, 113)
ease = lambda x: 1 - (1 - max(0, min(1, x))) ** 3


def base(d, title):
    d.rectangle([0, 0, W, H], fill=BG)
    d.text((22, 18), '9:41', font=font(16), fill=WHITE)
    d.rounded_rectangle([W - 60, 22, W - 24, 34], 4, outline=WHITE, width=2)
    d.text((22, 60), title, font=font(26, 'Black') if os.path.exists(F + 'Inter-Black.otf') else font(26), fill=WHITE)


def scene_order(t):  # menu + 1-click order button press
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    base(d, 'Ваше меню')
    items = [('Капучино', '★ 4.9'), ('Круассан', '★ 4.8'), ('Салат Цезарь', '★ 4.9'), ('Лимонад', '★ 4.7')]
    for i, (n, r) in enumerate(items):
        k = ease((t - 0.1 * i) / 0.4)
        y = 110 + i * 82 + int((1 - k) * 30)
        d.rounded_rectangle([18, y, W - 18, y + 68], 16, fill=CARD)
        d.rounded_rectangle([30, y + 10, 78, y + 58], 12, fill=(60 + i * 30, 50, 40))
        d.text((92, y + 14), n, font=font(19), fill=WHITE)
        d.text((92, y + 40), r, font=font(14, 'Regular'), fill=GOLD)
        sel = t > 1.2 and i == 0
        d.ellipse([W - 58, y + 20, W - 30, y + 48], fill=GOLD if sel else (70, 70, 80))
    # big button
    press = 1.0 - 0.06 * math.exp(-((t - 1.6) / 0.12) ** 2)
    bw, bh = int((W - 44) * press), int(64 * press)
    bx, by = (W - bw) // 2, 470 + (64 - bh) // 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], 20, fill=GOLD)
    tx = 'Заказать в 1 клик'
    f = font(22); tw = d.textlength(tx, font=f)
    d.text(((W - tw) / 2, by + bh / 2 - 14), tx, font=f, fill=(20, 20, 20))
    if t > 1.6:  # tap ripple
        r = int(ease((t - 1.6) / 0.5) * 70); a = max(0, 1 - (t - 1.6) / 0.5)
        ov = Image.new('RGBA', (W, H)); ImageDraw.Draw(ov).ellipse([W // 2 - r, 502 - r, W // 2 + r, 502 + r], outline=(255, 255, 255, int(200 * a)), width=4)
        im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB'); d = ImageDraw.Draw(im)
    if t > 2.0:  # success toast
        k = ease((t - 2.0) / 0.35)
        y = 560 + int((1 - k) * 60)
        d.rounded_rectangle([40, y, W - 40, y + 50], 25, fill=GREEN)
        f2 = font(18); tx = 'Заказ принят ✓'; tw = d.textlength(tx, font=f2)
        d.text(((W - tw) / 2, y + 14), tx, font=f2, fill=WHITE)
    return im


def scene_notify(t):  # lock screen + push notifications slide in
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    for yy in range(H):
        c = int(20 + 30 * yy / H); d.line([0, yy, W, yy], fill=(c, c // 2 + 10, c + 30))
    f = font(64); tx = '9:41'; tw = d.textlength(tx, font=f)
    d.text(((W - tw) / 2, 70), tx, font=f, fill=WHITE)
    tx = 'Уведомления'; f3 = font(16, 'Regular'); tw = d.textlength(tx, font=f3)
    d.text(((W - tw) / 2, 150), tx, font=f3, fill=WHITE)
    notes = [('Ваше кафе', 'Ваш заказ готов! Заберите на кассе'), ('Ваше кафе', 'Подарок для постоянных клиентов'),
             ('Ваше кафе', 'Вам начислены бонусы')]
    for i, (a, b) in enumerate(notes):
        k = ease((t - 0.3 - 0.9 * i) / 0.35)
        if k <= 0:
            continue
        y = 230 + i * 92 - int((1 - k) * 40)
        ov = Image.new('RGBA', (W, H)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle([14, y, W - 14, y + 80], 18, fill=(245, 245, 245, int(235 * k)))
        od.rounded_rectangle([26, y + 14, 56, y + 44], 8, fill=GOLD + (int(255 * k),))
        od.text((68, y + 12), a, font=font(15), fill=(30, 30, 30, int(255 * k)))
        od.text((68, y + 36), b, font=font(13, 'Regular'), fill=(60, 60, 60, int(255 * k)))
        im = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    return im


def scene_turnkey(t):  # "под ключ" checklist
    im = Image.new('RGB', (W, H)); d = ImageDraw.Draw(im)
    base(d, 'Приложение')
    d.text((22, 94), 'под ключ', font=font(26), fill=GOLD)
    rows = ['iOS + Android', 'Дизайн', 'Заказы и оплата', 'Push-уведомления', 'Бонусы клиентам', 'Публикация в сторах']
    for i, r in enumerate(rows):
        k = ease((t - 0.15 - 0.33 * i) / 0.3)
        y = 160 + i * 66
        d.rounded_rectangle([18, y, W - 18, y + 52], 14, fill=CARD)
        d.text((70, y + 15), r, font=font(18), fill=WHITE if k > 0 else GREY)
        if k > 0:
            rr = int(13 * k)
            d.ellipse([40 - rr, y + 26 - rr, 40 + rr, y + 26 + rr], fill=GREEN)
            if k > 0.6:
                d.line([33, y + 26, 38, y + 32, 48, y + 19], fill=WHITE, width=3)
        else:
            d.ellipse([27, y + 13, 53, y + 39], outline=GREY, width=2)
    d.text((22, H - 50), 'B2B SAS', font=font(18), fill=GOLD)
    return im


def render(fn, dur, out):
    p = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '12', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for i in range(int(dur * FPS)):
        p.stdin.write(fn(i / FPS).tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    o = sys.argv[1]
    render(scene_order, 3.7, os.path.join(o, 'm_order.mp4'))
    render(scene_notify, 3.5, os.path.join(o, 'm_notify.mp4'))
    render(scene_turnkey, 3.8, os.path.join(o, 'm_turnkey.mp4'))
    for n in ('order', 'notify', 'turnkey'):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', '2.6', '-i', os.path.join(o, 'm_%s.mp4' % n), '-frames:v', '1', os.path.join(o, 'm_%s.jpg' % n)])
