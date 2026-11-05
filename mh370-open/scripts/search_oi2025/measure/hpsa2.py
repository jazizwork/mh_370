import sys, json, numpy as np, cv2
sys.path.insert(0,'.')
from grapply import load
from pyproj import Geod
G=Geod(ellps='WGS84'); f=load('oi/gr_hpsa.json')
im=cv2.imread(sys.argv[1]); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=[hsv[...,i].astype(int) for i in range(3)]
b,g,r=[im[...,i].astype(int) for i in range(3)]
H,W=h.shape
olive=((h>=25)&(h<=45)&(s>=70)&(v>=60)&(v<=220)).astype(np.uint8)
olive[0:220,0:620]=0
olive=cv2.morphologyEx(olive,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8)); olive=cv2.morphologyEx(olive,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
yellow=((r>200)&(g>200)&(b<90)).astype(np.uint8)
n,lab,st,_=cv2.connectedComponentsWithStats(yellow)
for i in range(1,n):
    if st[i,4]>3000 and (st[i,2]>150 and st[i,3]>60) and st[i,4]>0.3*st[i,2]*st[i,3]: yellow[lab==i]=0
yellow=cv2.dilate(yellow,np.ones((3,3),np.uint8))
# crossings above each pixel: cumulative count of run starts (yellow pixel whose upper neighbour is not yellow)
starts=np.zeros_like(yellow,dtype=np.int32); starts[1:]=((yellow[1:]==1)&(yellow[:-1]==0)); starts[0]=yellow[0]
cum=np.cumsum(starts,axis=0)
above=(cum%2==0)&(yellow==0)
hp=((olive>0)&above).astype(np.uint8)
hp=cv2.morphologyEx(hp,cv2.MORPH_OPEN,np.ones((5,5),np.uint8))
cs,_=cv2.findContours(hp,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
out=[]
for c in cs:
    if cv2.contourArea(c)<1500: continue
    c=cv2.approxPolyDP(c,2.0,True)[:,0,:].astype(float); lon,lat=f(c[:,0],c[:,1]); p=np.c_[lon,lat]; out.append(p)
ar=[abs(G.polygon_area_perimeter(p[:,0],p[:,1])[0])/1e6 for p in out]
print('HPSA polys',len(out),[round(a,2) for a in ar],'sum',round(sum(ar),2))
d=json.load(open('oi/hpsa_polys.json')); d['hpsa']=[p.tolist() for p in out]; json.dump(d,open('oi/hpsa_polys.json','w'))
dbg=im.copy(); dbg[hp>0]=(0,0,255); cv2.imwrite('oi/hpsa_dbg.png',cv2.resize(dbg,None,fx=0.45,fy=0.45))
