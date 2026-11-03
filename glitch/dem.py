import tifffile, zlib, numpy as np, glob, os, sys
def read(path):
    t=tifffile.TiffFile(path); p=t.pages[0]
    H,W=p.shape; tw,tl=p.tilewidth,p.tilelength
    out=np.zeros((H,W),np.float32)
    fh=t.filehandle; nx=(W+tw-1)//tw
    for i,(off,cnt) in enumerate(zip(p.dataoffsets,p.databytecounts)):
        fh.seek(off); raw=zlib.decompress(fh.read(cnt))
        b=np.frombuffer(raw,np.uint8).reshape(tl,tw*4)
        b=np.cumsum(b,axis=1,dtype=np.uint8)  # undo horizontal diff (mod 256)
        planes=b.reshape(tl,4,tw).transpose(0,2,1).copy()
        v=planes.view('>f4').reshape(tl,tw)
        r,c=divmod(i,nx); y,x=r*tl,c*tw
        h=min(tl,H-y); w=min(tw,W-x)
        out[y:y+h,x:x+w]=v[:h,:w]
    return out
if __name__=='__main__':
    d=sys.argv[1]
    rows=[]
    for la in range(47,41,-1):
        rows.append(np.hstack([read(f'{d}/dem_N{la}E{lo}.tif') for lo in range(57,63)]))
    m=np.vstack(rows); print(m.shape,np.nanmin(m),np.nanmax(m))
    np.save(sys.argv[2],m)
