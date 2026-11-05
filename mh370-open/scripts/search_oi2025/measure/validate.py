import sys, numpy as np, cv2, pandas as pd
sys.path.insert(0,'.')
from grapply import load
from scipy.spatial import cKDTree
img, gr, legs = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
f=load(gr)
im=cv2.imread(img); b,g,r=[im[...,i].astype(int) for i in range(3)]
# purple dots: R~90-130, G<40, B~90-140
pm=((r>70)&(r<150)&(g<50)&(b>70)&(b<160)).astype(np.uint8)
pm=cv2.morphologyEx(pm,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))  # keep blobs (dots), remove thin lines
n,lab,st,cen=cv2.connectedComponentsWithStats(pm)
ok=[(i) for i in range(1,n) if 25<st[i,4]<200 and abs(st[i,2]-st[i,3])<=3]
c=cen[ok]
lon,lat=f(c[:,0],c[:,1])
tr=pd.read_csv('oi/tracks_hourly.csv'); tr=tr[tr.leg.isin(legs)]
T=np.c_[tr.lon*np.cos(np.radians(34.7))*111.32, tr.lat*110.95]
Q=np.c_[lon*np.cos(np.radians(34.7))*111.32, lat*110.95]
d,i=cKDTree(T).query(Q)
print('dots',len(c),'NN dist km pct 25/50/75/90:',np.percentile(d,[25,50,75,90]).round(2))
dx=(Q-T[i]); good=d<3
print('mean offset (E,N) km of good matches:',dx[good].mean(0).round(2),'n',good.sum())
