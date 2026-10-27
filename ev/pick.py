"""Pick free-licence stock clips for a job (runs on the GitHub runner).

Sources (both allow free commercial use incl. YouTube monetised videos):
  * Pexels  — pexels.com/license      (search page scrape -> /download/video/<id>/)
  * Mixkit  — mixkit.co/license       (category page scrape -> assets.mixkit.co/.../<id>-1080.mp4)
Already used ids are kept in ev/used.txt so videos don't repeat footage.
Usage: python pick.py job.json  -> writes job.json with "clips" filled.
"""
import json
import os
import random
import re
import subprocess
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
USED = os.path.join(HERE, 'used.txt')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'


def get(url):
    try:
        return subprocess.check_output(['curl', '-sSL', '--max-time', '40', '-A', UA, '-H',
                                        'Accept-Language: en-US,en;q=0.9', url]).decode('utf-8', 'ignore')
    except subprocess.CalledProcessError:
        return ''


def pexels(q):
    """Needs secret PEXELS_API_KEY (free key from pexels.com/api); skipped otherwise."""
    key = os.environ.get('PEXELS_API_KEY')
    if not key:
        return []
    try:
        raw = subprocess.check_output(['curl', '-sSL', '--max-time', '40', '-H', f'Authorization: {key}',
                                       f'https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}'
                                       '&orientation=landscape&size=large&per_page=40']).decode()
        vids = json.loads(raw).get('videos', [])
    except Exception as e:  # noqa
        print('pexels api error', e, flush=True)
        return []
    out = []
    for v in vids:
        fs = [f for f in v.get('video_files', []) if (f.get('width') or 0) >= 1920 and f.get('link')]
        fs.sort(key=lambda f: f.get('width') or 0)
        if fs and (v.get('duration') or 0) >= 8:
            out.append({'src': 'pexels', 'id': str(v['id']), 'url': fs[0]['link'], 'by': v.get('user', {}).get('name', '')})
    print(f'pexels "{q}": {len(out)} clips', flush=True)
    return out


def mixkit(q):
    slug = q.strip().lower().replace(' ', '-')
    html = get(f'https://mixkit.co/free-stock-video/{slug}/')
    pages = list(dict.fromkeys(re.findall(r'/free-stock-video/([a-z0-9-]+-(\d{3,6}))/', html)))
    print(f'mixkit "{slug}": {len(pages)} pages', flush=True)
    return [{'src': 'mixkit', 'id': i, 'page': f'https://mixkit.co/free-stock-video/{p}/'} for p, i in pages]


def mixkit_url(c):
    html = get(c['page'])
    urls = list(dict.fromkeys(re.findall(r'https://assets\.mixkit\.co/[^"\'\s]+?\.mp4', html)))
    best = [u for u in urls if '1080' in u] or [u for u in urls if '720' in u] or urls
    if not best:
        print('no mp4 on', c['page'], len(html), flush=True)
        return None
    return best[0]


def main(path):
    job = json.load(open(path))
    if job.get('clips'):
        return
    used = set(open(USED).read().split()) if os.path.exists(USED) else set()
    rnd = random.Random(job.get('seed', 1))
    want = int(job.get('count', 10))
    pool = []
    for q in job.get('queries', []):
        for src in job.get('sources', ['pexels', 'mixkit']):
            for c in (pexels(q) if src == 'pexels' else mixkit(q)):
                key = f"{c['src']}:{c['id']}"
                if key not in used and all(key != f"{p['src']}:{p['id']}" for p in pool):
                    pool.append(c)
    rnd.shuffle(pool)
    clips = []
    for c in pool:
        if len(clips) >= want * 2:  # extra in case some downloads fail
            break
        if c['src'] == 'mixkit':
            c['url'] = mixkit_url(c)
            if not c['url']:
                continue
            print('mixkit', c['id'], c['url'], flush=True)
        clips.append(c)
    job['clips'] = clips
    json.dump(job, open(path, 'w'), indent=1)
    print('picked', len(job['clips']), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
