import sys, numpy as np
sys.path.insert(0,'.')
from arcframe import to_sn
pts=np.vstack([np.load('oi/red_image-4.npy'),np.load('oi/red_image-1.npy'),np.load('oi/red_image-9.npy')])
pts=pts[(pts[:,1]>-36.6)&(pts[:,1]<-32.9)&(pts[:,0]>91.3)&(pts[:,0]<95.6)]
# subsample for speed
rng=np.random.default_rng(0); idx=rng.choice(len(pts),min(len(pts),12000),replace=False); pts=pts[idx]
s,n=to_sn(pts[:,0],pts[:,1])
np.save('oi/red_sn.npy',np.c_[pts,s,n])
h,e=np.histogram(n,bins=np.arange(-110,110,2.5))
for a,c in zip(e[:-1],h):
    if c>20: print(f'{a:7.1f} {c}')
