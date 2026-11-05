import sys, json, numpy as np, cv2
sys.path.insert(0,'.')
from grapply import load
from pyproj import Proj, Geod
from scipy.optimize import least_squares
G=Geod(ellps='WGS84')
I='data/raw/oi2025_search/images/'
aeqd=Proj(proj='aeqd',lat_0=-34.2342,lon_0=93.7875,datum='WGS84')
inv=lambda x,y: aeqd(np.asarray(x)*1000,np.asarray(y)*1000,inverse=True)
res_all={}
for img,gr in [('radiantphysics_2025_03_image-4.png','oi/gr_img4.json'),('radiantphysics_2025_03_image-9.png','oi/gr_img9.json')]:
    f=load(gr); im=cv2.imread(I+img); b,g,r=[im[...,i].astype(int) for i in range(3)]
    blk=((r<45)&(g<45)&(b<45)).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(blk)
    keep=np.zeros_like(blk)
    for i in range(1,n):
        x,y,w,hh,a=st[i]
        if a>=60 and a<0.25*w*hh: keep[lab==i]=1
    ys,xs=np.nonzero(keep); lon,lat=f(xs,ys); X,Y=aeqd(lon,lat); P=np.c_[X,Y]/1000
    th=np.radians(46.0); d=np.array([np.sin(th),np.cos(th)]); nv=np.array([d[1],-d[0]])
    def stad(q,P):
        c=q[0]*d+q[1]*nv; L=q[2]; R=q[3]
        a=c-L*d; b=c+L*d; ab=b-a; t=np.clip(((P-a)@ab)/(ab@ab),0,1)
        return np.hypot(*(P-(a+t[:,None]*ab)).T)-R
    best=None
    for L0 in (40,70,100):
        for R0 in (110,130,150):
            q0=np.array([0,0,L0,R0])
            for it in range(3):
                r=stad(q0,P); m=np.abs(r)<(15 if it==0 else 5 if it==1 else 3)
                if m.sum()<50: break
                q0=least_squares(lambda q: stad(q,P[m]),q0,loss='soft_l1',f_scale=2).x
            r=stad(q0,P); m=np.abs(r)<3
            score=m.sum()
            if best is None or score>best[0]: best=(score,q0,np.sqrt((r[m]**2).mean()))
    score,q,rms=best
    c=q[0]*d+q[1]*nv
    print(img,'inliers',score,'centre along/perp km',q[0].round(1),q[1].round(1),'half-length L km',q[2].round(1),'R km',q[3].round(1),'(%.1f NM)'%(q[3]/1.852),'rms km',rms.round(2),'centre lonlat',np.round(inv(*c),4))
    res_all[img]=q
q=np.mean(list(res_all.values()),axis=0)
th=np.radians(46.0); d=np.array([np.sin(th),np.cos(th)]); nv=np.array([d[1],-d[0]])
c=q[0]*d+q[1]*nv; L,R=q[2],q[3]; a=c-L*d; b=c+L*d
ang=np.arctan2(nv[1],nv[0]); ring=[]
for t in np.linspace(-np.pi/2,np.pi/2,91): ring.append(b+R*np.array([np.cos(np.arctan2(d[1],d[0])+t),np.sin(np.arctan2(d[1],d[0])+t)]))
for t in np.linspace(np.pi/2,3*np.pi/2,91): ring.append(a+R*np.array([np.cos(np.arctan2(d[1],d[0])+t),np.sin(np.arctan2(d[1],d[0])+t)]))
ring=np.array(ring); lon,lat=inv(ring[:,0],ring[:,1]); p=np.c_[lon,lat]; p=np.vstack([p,p[:1]])
A=abs(G.polygon_area_perimeter(p[:,0],p[:,1])[0])/1e6
print('mean: L',L.round(1),'R',R.round(1),'area',round(A),'lat range',lat.min().round(2),lat.max().round(2),'axis ends',np.round(inv(*a),3),np.round(inv(*b),3))
json.dump({'ring':p.tolist(),'R_km':float(R),'half_length_km':float(L),'axis_end_SW':list(map(float,inv(*a))),'axis_end_NE':list(map(float,inv(*b))),'fits':{k:list(map(float,v)) for k,v in res_all.items()}},open('oi/racetrack.json','w'))
