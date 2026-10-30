#!/usr/bin/env python3
"""Z7 PiP — put a rounded "side screen" with clips over a base video (presenter talks, screen shows the product).

Usage: python3 render/pip.py spec.json out.mp4
spec = {
  "base": "presenter.mp4",            # full-frame 9:16 video (its audio is kept)
  "width": 1080, "height": 1920, "fps": 30,
  "box": [40, 900, 360, 640],         # x, y, w, h of the side screen
  "radius": 34, "border": 6, "border_color": "#D4AF37",
  "t0": 8.6, "t1": 24.4,              # when the side screen is visible (slides in / out)
  "clips": [{"src": "a.mp4", "start": 0.5, "dur": 2.6}, ...]   # played back to back inside the box
}
"""
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter


def sh(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr[-3000:])
        raise SystemExit('ffmpeg failed')


def main(spec_path, out):
    s = json.load(open(spec_path))
    W, H, FPS = s.get('width', 1080), s.get('height', 1920), s.get('fps', 30)
    x, y, w, h = s['box']
    R, B = s.get('radius', 34), s.get('border', 6)
    col = s.get('border_color', '#D4AF37')
    t0, t1 = float(s['t0']), float(s['t1'])
    work = os.environ.get('RENDER_WORK', '/tmp/z7pip')
    os.makedirs(work, exist_ok=True)
    # frame (border + shadow) and inner mask
    fw, fh = w + 2 * B, h + 2 * B
    pad = 40
    frame = Image.new('RGBA', (fw + 2 * pad, fh + 2 * pad), (0, 0, 0, 0))
    sh_ = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh_).rounded_rectangle([pad, pad + 10, pad + fw, pad + fh + 10], R + B, fill=(0, 0, 0, 170))
    frame = Image.alpha_composite(frame, sh_.filter(ImageFilter.GaussianBlur(16)))
    ImageDraw.Draw(frame).rounded_rectangle([pad, pad, pad + fw, pad + fh], R + B, fill=col)
    ImageDraw.Draw(frame).rounded_rectangle([pad + B, pad + B, pad + B + w, pad + B + h], R, fill=(0, 0, 0, 0))
    fpath = os.path.join(work, 'frame.png'); frame.save(fpath)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], R, fill=255)
    mpath = os.path.join(work, 'mask.png'); mask.save(mpath)
    # inner clip track
    parts = []
    for i, c in enumerate(s['clips']):
        p = os.path.join(work, 'c%d.mp4' % i)
        sh(['ffmpeg', '-y', '-ss', str(c.get('start', 0)), '-t', str(c['dur']), '-i', c['src'], '-an', '-vf',
            'scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,setsar=1,eq=saturation=1.08:contrast=1.04' % (w, h, w, h, FPS),
            '-c:v', 'libx264', '-crf', '14', '-preset', 'fast', p])
        parts.append(p)
    lst = os.path.join(work, 'list.txt')
    open(lst, 'w').write(''.join("file '%s'\n" % p for p in parts))
    track = os.path.join(work, 'track.mp4')
    sh(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', track])
    slide = 0.32
    # x position: slide in from the left edge, slide out at t1
    xe = "if(lt(t,{a}),{x0}+({x}-{x0})*(t-{t0})/{d},if(gt(t,{b}),{x}+({x0}-{x})*(t-{b})/{d},{x}))".format(
        a=t0 + slide, b=t1 - slide, t0=t0, d=slide, x=x - B - pad, x0=-(fw + 2 * pad))
    xi = "if(lt(t,{a}),{x0}+({x}-{x0})*(t-{t0})/{d},if(gt(t,{b}),{x}+({x0}-{x})*(t-{b})/{d},{x}))".format(
        a=t0 + slide, b=t1 - slide, t0=t0, d=slide, x=x, x0=-(fw + 2 * pad) + B + pad)
    en = "between(t,%.3f,%.3f)" % (t0, t1)
    fc = ('[0:v]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%d,setsar=1[base];'
          '[2:v][3:v]alphamerge,setpts=PTS+%.3f/TB[clip];'
          '[base][1:v]overlay=x=\'%s\':y=%d:enable=\'%s\'[b1];'
          '[b1][clip]overlay=x=\'%s\':y=%d:enable=\'%s\':eof_action=pass,format=yuv420p[v]') % (
        W, H, W, H, FPS, t0, xe, y - B - pad, en, xi, y, en)
    sh(['ffmpeg', '-y', '-i', s['base'], '-loop', '1', '-i', fpath, '-i', track, '-loop', '1', '-i', mpath,
        '-filter_complex', fc, '-map', '[v]', '-map', '0:a?', '-t', str(float(subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', s['base']],
            stdout=subprocess.PIPE, text=True).stdout.strip())),
        '-c:v', 'libx264', '-crf', '14', '-preset', 'medium', '-c:a', 'aac', '-b:a', '192k', out])
    print(json.dumps({'ok': True, 'out': out}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
