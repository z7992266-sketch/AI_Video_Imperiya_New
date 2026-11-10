import numpy as np, wave, subprocess, sys
SR=44100
def track(name,BPM,root,mode,seed,T=40.0):
    beat=60/BPM; n=int(T*SR); out=np.zeros(n); rng=np.random.default_rng(seed)
    def add(sig,t,g=1.0):
        i=int(t*SR)
        if i>=n: return
        j=min(n,i+len(sig)); out[i:j]+=sig[:j-i]*g
    def kick():
        m=int(0.35*SR); t=np.arange(m)/SR; return np.sin(2*np.pi*(45+90*np.exp(-t*25))*t)*np.exp(-t*9)
    def hat():
        m=int(0.05*SR); x=rng.standard_normal(m); x=x-np.convolve(x,np.ones(4)/4,'same'); return x*np.exp(-np.arange(m)/SR*80)*0.25
    def clap():
        m=int(0.15*SR); x=rng.standard_normal(m); return x*np.exp(-np.arange(m)/SR*30)*0.25
    def note(f,d,v=0.18,wf='saw'):
        m=int(d*SR); t=np.arange(m)/SR
        s=sum(np.sin(2*np.pi*f*k*t)/k for k in range(1,6)) if wf=='saw' else np.sin(2*np.pi*f*t)
        e=np.minimum(1,t/0.01)*np.exp(-t*2.2); return s*e*v
    def pad(fs,d,v=0.05):
        m=int(d*SR); t=np.arange(m)/SR; s=sum(np.sin(2*np.pi*f*t)+0.5*np.sin(2*np.pi*f*2.005*t) for f in fs)
        e=np.minimum(1,t/0.4)*np.minimum(1,(d-t)/0.4); return s*e*v
    st=lambda s: root*2**(s/12)
    degs={'minor':[[0,3,7],[-4,0,3],[-2,2,5],[-5,-1,2]],'major':[[0,4,7],[-3,0,4],[-7,-3,0],[-5,-1,2]]}[mode]
    prog=[[st(x) for x in c] for c in degs]
    t=0;k=0
    while t<T-0.01:
        bar=int(t/(4*beat))%4
        if k%4==0: add(pad(prog[bar],4*beat),t)
        add(kick(),t,0.9); add(hat(),t+beat/2)
        if k%2==1: add(clap(),t,0.8)
        add(note(prog[bar][0]/4,beat*0.9,0.22,'sine'),t)
        if k%2==1 or (seed%2 and k%4==0): add(note(prog[bar][k%3]*2,beat*0.4,0.06),t+beat/2)
        t+=beat;k+=1
    f=int(1.5*SR); out[-f:]*=np.linspace(1,0,f); out[:int(0.05*SR)]*=np.linspace(0,1,int(0.05*SR))
    out=out/np.max(np.abs(out))*0.8
    with wave.open(name+'.wav','wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out*32767).astype(np.int16).tobytes())
    subprocess.run(['ffmpeg','-loglevel','error','-y','-i',name+'.wav','-ac','2','-b:a','160k',name+'.mp3']); 
for i,(b,r,m) in enumerate([(118,220,'minor'),(124,196,'major'),(110,233.1,'minor'),(128,261.6,'major'),(100,174.6,'minor'),(120,246.9,'major')],1):
    track(f'b2b_beat_{i:02d}',b,r,m,i)
