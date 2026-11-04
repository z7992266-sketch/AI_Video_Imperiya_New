import json,re,subprocess
G='/tmp/claude-0/-home-claude/844ebc5a-648f-5142-9a2f-1a04ed1a7ee7/scratchpad/glitch/'
d=json.load(open(G+'darvaza_v2.json'))
segs=d['segments']
groups=[segs[0:9],segs[9:15],segs[15:23]]
out=[];offset=0.0
for ci,grp in enumerate(groups,1):
    mp3=G+f'assets/gv_vo{ci}.mp3'
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',mp3]))
    log=subprocess.run(['ffmpeg','-i',mp3,'-af','silencedetect=noise=-38dB:d=0.35','-f','null','-'],capture_output=True,text=True).stderr
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
for o in out: print(o['id'],o['start'],o['end'],round(o['end']-o['start'],1),o['chapter'])
print('total',offset)
