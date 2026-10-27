"""Exclusive Vibe — long-form video renderer (runs in GitHub Actions).

job json:
{ "id": "ev001", "title": "Rain & Soft Piano for Deep Sleep", "subtitle": "1 Hour Relaxing Music",
  "minutes": 60, "mood": "rain", "seed": 11,
  "clips": [ {"id": 1234567, "place": "Forest, Norway"}, ... ],   # Pexels video ids (8-14)
  "slow": 1.6, "seg": 28 }
Outputs out/<id>.mp4 (1080p30) and out/<id>_thumb.jpg
"""
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_L = '/usr/share/fonts/opentype/inter/Inter-Light.otf'
FONT_B = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
if not os.path.exists(FONT_L):
    FONT_L = FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def sh(cmd):
    print('+', ' '.join(cmd)[:300], flush=True)
    subprocess.run(cmd, check=True)


def main(job_path):
    job = json.load(open(job_path))
    jid = job['id']
    os.makedirs('work', exist_ok=True)
    os.makedirs('out', exist_ok=True)
    minutes = float(job.get('minutes', 60))
    slow = float(job.get('slow', 1.6))
    seg = float(job.get('seg', 28))

    # 1) download + normalise clips (slow motion, 1080p, gentle colour)
    segs = []
    credits = []
    want = int(job.get('count', 10))
    for i, c in enumerate(job['clips']):
        if len(segs) >= want:
            break
        src = f'work/c{i}.mp4'
        try:
            if c.get('file'):
                src = c['file']
            else:
                url = c.get('url') or f"https://www.pexels.com/download/video/{c['id']}/"
                sh(['curl', '-sSL', '--fail', '--retry', '2', '--max-time', '300', '-A',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0', '-o', src, url])
        except subprocess.CalledProcessError:
            print('skip clip', c, flush=True)
            continue
        dst = f'work/s{i}.mp4'
        vf = (f'setpts={slow}*PTS,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,'
              f'fps=30,eq=saturation=1.08:contrast=1.03,format=yuv420p')
        try:
            sh(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-t', str(seg), '-vf', vf, '-an',
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', dst])
            d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                                               '-of', 'csv=p=0', dst]).decode().strip())
            if d >= 8:
                segs.append((dst, d))
                credits.append(f"{c.get('src', 'file')}:{c.get('id', '')}")
        except (subprocess.CalledProcessError, ValueError):
            print('bad clip', c, flush=True)
        if not c.get('file') and os.path.exists(src):
            os.remove(src)
    with open(f'out/{jid}_clips.txt', 'w') as f:
        f.write('\n'.join(credits) + '\n')
    if len(segs) < 4:
        sys.exit('not enough clips')

    # 2) crossfade chain -> base sequence (looped later)
    xf = 2.5
    inputs = []
    for p, _ in segs:
        inputs += ['-i', p]
    fc = []
    prev = '[0:v]'
    off = 0.0
    for k in range(1, len(segs)):
        off += segs[k - 1][1] - xf
        out = f'[v{k}]'
        fc.append(f'{prev}[{k}:v]xfade=transition=fade:duration={xf}:offset={off:.3f}{out}')
        prev = out
    # loop back to the first clip smoothly: append first clip again faded
    sh(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(fc), '-map', prev,
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', 'work/base.mp4'])

    # 3) original music
    sh([sys.executable, os.path.join(HERE, 'music.py'), '--minutes', str(minutes), '--mood', job.get('mood', 'rain'),
        '--seed', str(job.get('seed', 1)), '--out', 'work/music.wav'])

    # 4) title card PNG (first 8 s) + logo
    W, H = 1920, 1080
    t = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    f1 = ImageFont.truetype(FONT_L, 92)
    f2 = ImageFont.truetype(FONT_B, 40)
    sh_img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sh_img)
    ds.text((W // 2, H // 2 - 30), job['title'], font=f1, fill=(0, 0, 0, 200), anchor='mm')
    sh_img = sh_img.filter(ImageFilter.GaussianBlur(10))
    t.alpha_composite(sh_img)
    d.text((W // 2, H // 2 - 30), job['title'], font=f1, fill=(250, 240, 220, 255), anchor='mm')
    d.text((W // 2, H // 2 + 60), job.get('subtitle', '').upper(), font=f2, fill=(232, 196, 120, 255), anchor='mm')
    t.save('work/title.png')

    lg = Image.open(os.path.join(HERE, 'logo_800.png')).convert('RGBA')
    m = Image.new('L', lg.size, 0)
    ImageDraw.Draw(m).ellipse((40, 40, lg.size[0] - 40, lg.size[1] - 40), fill=255)
    lg.putalpha(m.filter(ImageFilter.GaussianBlur(3)))
    lg = lg.crop((30, 30, lg.size[0] - 30, lg.size[1] - 30))
    lg.save('work/logo_round.png')

    # 5) final render: looped base + particle overlay (screen) + logo + title fade, music
    dur = minutes * 60
    fc = (
        '[0:v]format=gbrp[a];[1:v]format=gbrp[b];[a][b]blend=all_mode=screen:all_opacity=0.85,format=yuv420p[bg];'
        '[2:v]scale=130:-1,format=rgba,colorchannelmixer=aa=0.6[lg];'
        '[bg][lg]overlay=W-w-40:H-h-36[v1];'
        '[3:v]format=rgba,fade=t=in:st=0.5:d=1.5:alpha=1,fade=t=out:st=6.5:d=1.5:alpha=1[tt];'
        '[v1][tt]overlay=0:0:enable=\'lt(t,8.5)\',fade=t=in:st=0:d=2,'
        f'fade=t=out:st={dur - 4:.2f}:d=4[v]'
    )
    sh(['ffmpeg', '-y', '-loglevel', 'error', '-stats', '-stats_period', '60',
        '-stream_loop', '-1', '-i', 'work/base.mp4',
        '-stream_loop', '-1', '-i', os.path.join(HERE, 'overlay_loop_1080p.mp4'),
        '-i', 'work/logo_round.png',
        '-loop', '1', '-t', '9', '-i', 'work/title.png',
        '-i', 'work/music.wav',
        '-filter_complex', fc, '-map', '[v]', '-map', '4:a',
        '-t', f'{dur:.2f}', '-r', '30',
        '-c:v', 'libx264', '-preset', job.get('preset', 'veryfast'), '-crf', '28',
        '-maxrate', '620k', '-bufsize', '1240k', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '112k', '-movflags', '+faststart', f'out/{jid}.mp4'])

    # 6) thumbnail from a nice frame
    sh(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '40', '-i', 'work/base.mp4', '-frames:v', '1', 'work/fr.png'])
    im = Image.open('work/fr.png').convert('RGB').resize((1280, 720))
    ov = Image.new('RGBA', (1280, 720), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for y in range(720):  # dark gradient at the bottom
        a = int(max(0, (y - 300) / 420) * 200)
        od.line((0, y, 1280, y), fill=(8, 10, 20, a))
    im = Image.alpha_composite(im.convert('RGBA'), ov)
    d = ImageDraw.Draw(im)
    big = job.get('thumb_big', job['title'].split(' for ')[0])
    fb = ImageFont.truetype(FONT_B, 96)
    while d.textlength(big, font=fb) > 1180 and fb.size > 50:
        fb = ImageFont.truetype(FONT_B, fb.size - 6)
    d.text((640, 520), big, font=fb, fill=(250, 240, 220), anchor='mm', stroke_width=3, stroke_fill=(0, 0, 0))
    d.text((640, 620), job.get('thumb_small', job.get('subtitle', '')).upper(), font=ImageFont.truetype(FONT_B, 44),
           fill=(232, 196, 120), anchor='mm', stroke_width=2, stroke_fill=(0, 0, 0))
    lg = Image.open('work/logo_round.png').convert('RGBA').resize((120, 120))
    im.alpha_composite(lg, (1140, 20))
    im.convert('RGB').save(f'out/{jid}_thumb.jpg', quality=92)
    print('DONE', jid, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
