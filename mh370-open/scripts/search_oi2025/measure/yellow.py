import sys, numpy as np, cv2, json
sys.path.insert(0,'.')
from grapply import load
from arcframe import to_sn
I='data/raw/oi2025_search/images/'
f=load('oi/gr_img1.json'); im=cv2.imread(I+'radiantphysics_2025_03_image-1.png')
b,g,r=[im[...,i].astype(int) for i in range(3)]
yel=(r>220)&(g>200)&(b<80)
ys,xs=np.nonzero(yel); lon,lat=f(xs,ys)
rng=np.random.default_rng(0); idx=rng.choice(len(xs),min(4000,len(xs)),replace=False)
s,n=to_sn(lon[idx],lat[idx])
for lo,hi in [(-200,-60),(-55,60)]:
    m=(s>lo)&(s<hi)
    for side,sel in [('NW',n<-30),('SE',n>50)]:
        mm=m&sel
        if mm.sum(): print(f's in [{lo},{hi}] {side}: n pct 5/50/95', np.percentile(n[mm],[5,50,95]).round(1), mm.sum())
