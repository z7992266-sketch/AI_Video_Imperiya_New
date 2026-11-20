import sys, os, numpy as np
sys.argv=[sys.argv[0]]+sys.argv[1:]
import make
O=[0,2.6,7.4,8.2,11.8,13.9,14.0,16.6,17.0,18.8,21.0,21.8,22.8,25.6,27.6,28.5]
N=[0,3.9,9.55,10.5,13.6,16.4,17.0,19.5,20.8,22.5,25.0,27.1,29.6,32.4,35.0,36.2]
def w(t): return float(np.interp(t,N,O))
a,b=int(sys.argv[1]),int(sys.argv[2])
os.makedirs('frames2',exist_ok=True)
for i in range(a,b):
    make.frame(w(i/30)).convert('RGB').save(f'frames2/f{i:05d}.jpg',quality=92)
