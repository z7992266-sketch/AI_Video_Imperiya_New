"""Template "geofetch": downloads Natural Earth (public domain) countries geojson on Actions,
rounds coords, writes render/out/<name>_geo.json (committed with results). Dummy 1 s mp4/jpg output.
Job: {"template":"geofetch","url":"<geojson url>","dec":3}"""
import json, os, subprocess, sys, urllib.request
job_path, out_mp4 = sys.argv[1], sys.argv[2]
name = os.path.splitext(os.path.basename(job_path))[0]
job = json.load(open(job_path)); dec = int(job.get('dec', 3))
raw = json.loads(urllib.request.urlopen(job['url'], timeout=120).read())
def rnd(c):
    if isinstance(c[0], (int, float)): return [round(c[0], dec), round(c[1], dec)]
    return [rnd(x) for x in c]
feats = []
for f in raw['features']:
    p = f['properties']; g = f['geometry']
    if not g: continue
    feats.append({'a3': p.get('ADM0_A3'), 'name': p.get('NAME'), 'cont': p.get('CONTINENT'),
                  'type': g['type'], 'coordinates': rnd(g['coordinates'])})
os.makedirs('render/out', exist_ok=True)
json.dump(feats, open('render/out/%s_geo.json' % name, 'w'), separators=(',', ':'))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'color=c=black:s=320x568:r=30', '-t', '1',
                '-pix_fmt', 'yuv420p', out_mp4], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', out_mp4, '-frames:v', '1', out_mp4[:-4] + '.jpg'], check=True)
print(json.dumps({'features': len(feats), 'duration': 1}))
