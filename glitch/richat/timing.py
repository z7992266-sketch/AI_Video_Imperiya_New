import json,re,subprocess
d=json.load(open('richat.json')); segs={s['id']:s for s in d['segments']}
out=[];offset=0.0
for ci,ids in enumerate(d['groups'],1):
    grp=[segs[i] for i in ids]
    mp3=f'assets/gvr_vo{ci}.mp3'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',mp3]))
    log=subprocess.run(['ffmpeg','-i',mp3,'-af','silencedetect=noise=-38dB:d=0.3','-f','null','-'],capture_output=True,text=True).stderr
    st=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',log)]
    en=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',log)]
    sil=[(a+b)/2 for a,b in zip(st,en)]
    lens=[len(s['text']) for s in grp]; tot=sum(lens)
    bounds=[0.0]; acc=0
    for L in lens[:-1]:
        acc+=L; est=acc/tot*dur
        best=min(sil,key=lambda s:abs(s-est)) if sil else est
        if abs(best-est)>4: best=est
        bounds.append(best)
    bounds.append(dur)
    for s,a,b in zip(grp,bounds,bounds[1:]):
        out.append({'id':s['id'],'chapter':s['chapter'],'start':round(offset+a,2),'end':round(offset+b,2),'text':s['text']})
    offset+=dur
json.dump(out,open('timing.json','w'),indent=1)
for o in out: print(o['id'],o['start'],o['end'],round(o['end']-o['start'],1),o['text'][:50])
print('total',offset)
