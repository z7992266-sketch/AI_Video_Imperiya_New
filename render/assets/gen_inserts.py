import math, os, subprocess, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS = 1080, 1920, 30
F = '/usr/share/fonts/opentype/inter/'
def font(n, s): return ImageFont.truetype(F + n, s)

def glow(img, r=18, k=1.6):
    g = img.filter(ImageFilter.GaussianBlur(r))
    return Image.blend(img, Image.eval(g, lambda v: min(255, int(v * k))), 0.5)

def clock_frame(t, sec_angle, min_angle, hr_angle, shake=0, rgb=0):
    im = Image.new('RGB', (W, H), (6, 4, 14))
    d = ImageDraw.Draw(im)
    cx, cy, R = W // 2 + shake, H // 2 - 60, 420
    for i in range(14, 0, -1):
        c = (int(10 + 3 * i), int(20 + 9 * i), int(40 + 12 * i))
        d.ellipse([cx - R - i * 5, cy - R - i * 5, cx + R + i * 5, cy + R + i * 5], outline=c, width=3)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(12, 10, 24), outline=(34, 211, 238), width=10)
    for k in range(60):
        a = math.radians(k * 6 - 90)
        L = 46 if k % 5 == 0 else 18
        w = 9 if k % 5 == 0 else 3
        x1, y1 = cx + (R - 24) * math.cos(a), cy + (R - 24) * math.sin(a)
        x2, y2 = cx + (R - 24 - L) * math.cos(a), cy + (R - 24 - L) * math.sin(a)
        d.line([x1, y1, x2, y2], fill=(230, 240, 255) if k % 5 == 0 else (120, 130, 160), width=w)
    fn = font('InterDisplay-Bold.otf', 62)
    for n in range(1, 13):
        a = math.radians(n * 30 - 90)
        x, y = cx + (R - 120) * math.cos(a), cy + (R - 120) * math.sin(a)
        d.text((x, y), str(n), font=fn, fill=(220, 230, 255), anchor='mm')
    def hand(ang, L, w, col):
        a = math.radians(ang - 90)
        d.line([cx - 40 * math.cos(a), cy - 40 * math.sin(a), cx + L * math.cos(a), cy + L * math.sin(a)], fill=col, width=w)
    hand(hr_angle, 230, 22, (240, 240, 255))
    hand(min_angle, 330, 14, (240, 240, 255))
    hand(sec_angle, 360, 6, (236, 72, 153))
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(236, 72, 153))
    im = glow(im)
    if rgb:
        r, g, b = im.split()
        r = r.transform(im.size, Image.AFFINE, (1, 0, -rgb, 0, 1, 0))
        b = b.transform(im.size, Image.AFFINE, (1, 0, rgb, 0, 1, 0))
        im = Image.merge('RGB', (r, g, b))
        d2 = ImageDraw.Draw(im)
        for _ in range(8):
            y = random.randint(0, H); h = random.randint(4, 30)
            d2.rectangle([0, y, W, y + h], fill=(random.randint(0, 80), random.randint(100, 255), 255))
    return im

def render(frames, name):
    os.makedirs('fr', exist_ok=True)
    for f in os.listdir('fr'): os.remove('fr/' + f)
    for i, im in enumerate(frames): im.save('fr/%05d.png' % i)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', str(FPS), '-i', 'fr/%05d.png', '-c:v', 'libx264', '-crf', '15', '-pix_fmt', 'yuv420p', name], check=True)

# CLOCK: 3:33:00 ticking forward 1.2 s, then glitch, seconds hand jumps BACK 3 s (with hands spinning backwards blur), settle
random.seed(7)
frames = []
base_sec = 0.0
def angles(s):  # s = seconds after 3:33:00
    sec = (s % 60) * 6
    mn = (33 + s / 60) * 6
    hr = (3 + (33 + s / 60) / 60) * 30
    return sec, mn, hr
total = int(4.2 * FPS)
for i in range(total):
    t = i / FPS
    if t < 1.6:          # normal ticking forward: 3:33:00 -> 3:33:01
        s = math.floor(t)
        sh, rgb = 0, 0
    elif t < 2.4:        # rewind: spin backwards fast, glitch
        p = (t - 1.6) / 0.8
        s = 1 - p * 4 - math.sin(p * math.pi) * 40   # whirl backwards
        sh, rgb = random.randint(-14, 14), random.randint(6, 22)
    else:                # settled at 3:32:57 and keeps ticking
        s = -3 + math.floor(t - 2.4)
        sh, rgb = 0, (8 if t < 2.55 else 0)
    frames.append(clock_frame(t, *angles(s), shake=sh, rgb=rgb))
render(frames, 'clock_rewind.mp4')

# PHONE: incoming call screen "MIA" 3:33, pulsing
frames = []
for i in range(int(3.0 * FPS)):
    t = i / FPS
    im = Image.new('RGB', (W, H), (4, 6, 14))
    d = ImageDraw.Draw(im)
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    for k in range(6):
        r = int(150 + k * 60 + pulse * 30)
        c = int(40 * (1 - k / 6) + 20 * pulse)
        d.ellipse([W / 2 - r, 720 - r, W / 2 + r, 720 + r], outline=(0, 120 + c, 160 + c), width=4)
    d.ellipse([W / 2 - 150, 570, W / 2 + 150, 870], fill=(20, 30, 60), outline=(34, 211, 238), width=6)
    d.text((W / 2, 720), 'M', font=font('InterDisplay-Black.otf', 170), fill=(230, 245, 255), anchor='mm')
    d.text((W / 2, 300), '3:33', font=font('InterDisplay-Bold.otf', 190), fill=(240, 245, 255), anchor='mm')
    d.text((W / 2, 1010), 'Mia', font=font('InterDisplay-Black.otf', 120), fill=(255, 255, 255), anchor='mm')
    d.text((W / 2, 1120), 'mobile · calling…', font=font('Inter-Medium.otf', 54), fill=(150, 170, 200), anchor='mm')
    d.ellipse([200, 1500, 360, 1660], fill=(220, 40, 70)); d.ellipse([720, 1500, 880, 1660], fill=(30, 200, 110))
    im = glow(im, 14, 1.4)
    frames.append(im)
render(frames, 'phone_call.mp4')
print('ok')
