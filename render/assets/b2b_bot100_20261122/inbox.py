"""Inbox flood -> bot answers everyone (generic demo, no real brand). 1080x1920 scenes, gold-framed phone."""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
FD = '/usr/share/fonts/opentype/inter/'
f = lambda n, s: ImageFont.truetype(FD + n, s)
GOLD = (212, 175, 55); GOLD2 = (255, 214, 102); WHITE = (245, 245, 245); GREY = (150, 150, 160); RED = (231, 76, 60); GREEN = (46, 204, 113)
ease = lambda x: 1 - (1 - max(0.0, min(1.0, x))) ** 3
def back(x, s=1.6):
    x = max(0.0, min(1.0, x)); x -= 1
    return x * x * ((s + 1) * x + s) + 1
PX, PY, PW, PH = 240, 420, 600, 1110
random.seed(5)
DUST = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4), random.uniform(20, 60), random.uniform(0, 6.3)) for _ in range(60)]
MSG = ['Вы работаете?', 'Есть доставка?', 'Можно записаться?', 'Хочу заказать', 'Ответьте, пожалуйста', 'Где вы находитесь?', 'Есть в наличии?', 'До скольки открыты?', 'Хочу оформить заявку']
COLS = [(60, 110, 160), (150, 80, 120), (70, 140, 90), (170, 110, 50), (90, 90, 170), (140, 60, 60), (60, 140, 140), (120, 120, 60), (100, 70, 150)]
LET = 'АМДСКНЗЛТ'

def bg(t):
    im = Image.new('RGBA', (W, H), (8, 8, 10, 255))
    g = Image.new('L', (W, H), 0); ImageDraw.Draw(g).ellipse([-150, 450, W + 150, 1500], fill=55)
    im.paste((48, 38, 10, 255), mask=g.filter(ImageFilter.GaussianBlur(170)))
    d = ImageDraw.Draw(im)
    for (px, py, r, sp, ph) in DUST:
        yy = (py - sp * t * 3) % H; a = 0.5 + 0.5 * math.sin(t * 2 + ph)
        d.ellipse([px - r, yy - r, px + r, yy + r], fill=tuple(int(v * (0.2 + 0.5 * a)) for v in GOLD) + (255,))
    return im

def phone(im, scr, t, slide=True):
    m = Image.new('L', (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, PW, PH], 54, fill=255)
    glow = Image.new('L', (W, H), 0); ImageDraw.Draw(glow).rounded_rectangle([PX - 12, PY - 12, PX + PW + 12, PY + PH + 12], 64, fill=150)
    im.paste((212, 175, 55, 255), mask=glow.filter(ImageFilter.GaussianBlur(28)))
    oy = int(80 * (1 - ease(t / 0.35))) if slide else 0
    im.paste(scr, (PX, PY + oy), m)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([PX - 6, PY - 6 + oy, PX + PW + 6, PY + PH + 6 + oy], 58, outline=GOLD, width=7)
    fl = f('Inter-SemiBold.otf', 26); lt = 'демо'; lw = d.textlength(lt, font=fl)
    d.text((PX + PW - lw - 10, PY + PH + 18), lt, font=fl, fill=GREY)

def header(sd, title, sub, subc, brand=False):
    sd.rectangle([0, 0, PW, 160], fill=(24, 24, 32))
    sd.text((30, 22), '14:05', font=f('Inter-Bold.otf', 28), fill=WHITE)
    if brand:
        sd.ellipse([30, 74, 98, 142], fill=GOLD); sd.text((44, 94), 'ВБ', font=f('Inter-Black.otf', 26), fill=(20, 20, 20))
        sd.text((116, 76), 'ВАШ БРЕНД', font=f('Inter-ExtraBold.otf', 32), fill=GOLD2)
    else:
        sd.text((30, 72), title, font=f('Inter-ExtraBold.otf', 38), fill=WHITE)
    sd.text((116 if brand else 30, 120), sub, font=f('Inter-SemiBold.otf', 24), fill=subc)

def row(sd, y, i, k, answered, a2):
    x0 = int(-PW * (1 - k))
    sd.rectangle([x0, y, x0 + PW, y + 112], fill=(16, 16, 22))
    sd.ellipse([x0 + 24, y + 18, x0 + 100, y + 94], fill=COLS[i % 9])
    sd.text((x0 + 46, y + 34), LET[i % 9], font=f('Inter-Black.otf', 32), fill=WHITE)
    sd.text((x0 + 120, y + 20), 'Клиент', font=f('Inter-Bold.otf', 28), fill=WHITE)
    if answered:
        txt = 'Бот: Здравствуйте! Чем помочь?'
        sd.text((x0 + 120, y + 62), txt, font=f('Inter-Medium.otf', 23), fill=tuple(int(GREY[j] + (GREEN[j] - GREY[j]) * a2) for j in range(3)))
        r = 20; cx, cy = x0 + PW - 50, y + 56
        sd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
        sd.line([(cx - 9, cy), (cx - 2, cy + 8), (cx + 10, cy - 8)], fill=WHITE, width=5)
    else:
        sd.text((x0 + 120, y + 62), MSG[i % 9], font=f('Inter-Medium.otf', 24), fill=GREY)
        n = 1 + (i * 7 + int(k * 3)) % 4
        bx = x0 + PW - 70; sd.rounded_rectangle([bx, y + 38, bx + 46, y + 76], 19, fill=RED)
        s = str(n); fw = sd.textlength(s, font=f('Inter-Bold.otf', 24)); sd.text((bx + 23 - fw / 2, y + 43), s, font=f('Inter-Bold.otf', 24), fill=WHITE)
    sd.line([(x0 + 120, y + 111), (x0 + PW, y + 111)], fill=(34, 34, 42), width=2)

def flood(t):
    im = bg(t); scr = Image.new('RGBA', (PW, PH), (16, 16, 22, 255)); sd = ImageDraw.Draw(scr)
    n = int(min(100, 100 * ease(t / 2.6)))
    off = (t * 260) % 112  # list keeps scrolling down = new chats on top
    for j in range(-1, 10):
        i = j + int(t * 260 // 112)
        y = 170 + j * 112 + off
        if y > PH: continue
        row(sd, int(y), i, ease((t - 0.05 * max(0, j)) / 0.3), False, 0)
    header(sd, 'Сообщения', 'Без ответа: %d' % n, RED)
    s = str(n); fb = f('Inter-Black.otf', 40); tw = sd.textlength(s, font=fb)
    sd.rounded_rectangle([PW - 60 - tw, 66, PW - 24, 126], 30, fill=RED); sd.text((PW - 42 - tw, 72), s, font=fb, fill=WHITE)
    phone(im, scr, t)
    # big red counter pill above phone
    d = ImageDraw.Draw(im); fn = f('Inter-Black.otf', 64)
    return im.convert('RGB')

def bot(t, brand=False):
    im = bg(t); scr = Image.new('RGBA', (PW, PH), (16, 16, 22, 255)); sd = ImageDraw.Draw(scr)
    left = max(0, int(100 * (1 - ease((t - 0.3) / 2.6))))
    if brand:
        header(sd, '', 'бот · онлайн 24/7', (110, 200, 140), brand=True)
    else:
        header(sd, 'Бот отвечает', ('Без ответа: %d' % left) if left else 'Без ответа: 0 ✓', RED if left else GREEN)
    for j in range(9):
        y = 170 + j * 112
        ta = 0.3 + 0.28 * j
        ans = brand or t >= ta
        row(sd, y, j, 1.0, ans, 1.0 if brand else ease((t - ta) / 0.3))
    if t > (1.0 if brand else 3.4):
        k = ease((t - (1.0 if brand else 3.4)) / 0.35)
        yy = PH - 130 + int(40 * (1 - k))
        sd.rounded_rectangle([50, yy, PW - 50, yy + 76], 38, fill=GREEN if not brand else GOLD)
        tx = 'Заявки у менеджера ✓' if not brand else 'Ваше имя · логотип · цвета'
        ft = f('Inter-ExtraBold.otf', 30); tw = sd.textlength(tx, font=ft)
        sd.text(((PW - tw) / 2, yy + 20), tx, font=ft, fill=WHITE if not brand else (20, 20, 20))
    phone(im, scr, t, slide=not brand)
    return im.convert('RGB')

def render(out, dur, fn):
    p = subprocess.Popen(['ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '14', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    for i in range(int(dur * FPS)):
        p.stdin.write(fn(i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == '__main__':
    o = sys.argv[1]
    render(os.path.join(o, 'flood.mp4'), 3.2, flood)
    render(os.path.join(o, 'bot.mp4'), 5.0, bot)
    render(os.path.join(o, 'brand.mp4'), 3.4, lambda t: bot(t, True))
