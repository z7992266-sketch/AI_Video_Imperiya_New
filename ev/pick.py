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
    html = get(f'https://www.pexels.com/search/videos/{urllib.parse.quote(q)}/?orientation=landscape')
    ids = list(dict.fromkeys(re.findall(r'/video/[a-z0-9-]*?-?(\d{5,9})/', html)))
    print(f'pexels "{q}": {len(ids)} ids, html {len(html)}', flush=True)
    return [{'src': 'pexels', 'id': i, 'url': f'https://www.pexels.com/download/video/{i}/'} for i in ids]


def mixkit(q):
    slug = q.strip().lower().replace(' ', '-')
    html = get(f'https://mixkit.co/free-stock-video/{slug}/')
    ids = list(dict.fromkeys(re.findall(r'/free-stock-video/[a-z0-9-]+-(\d{3,6})/', html)))
    print(f'mixkit "{slug}": {len(ids)} ids, html {len(html)}', flush=True)
    return [{'src': 'mixkit', 'id': i, 'url': f'https://assets.mixkit.co/videos/{i}/{i}-1080.mp4'} for i in ids]


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
    job['clips'] = pool[: want * 2]  # extra in case some downloads fail
    json.dump(job, open(path, 'w'), indent=1)
    print('picked', len(job['clips']), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
