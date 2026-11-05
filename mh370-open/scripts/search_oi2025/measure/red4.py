import sys, json, numpy as np, cv2
sys.path.insert(0,'.')
from grapply import load
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.path.insert(0,'src')
from mh370 import geo
I='data/raw/oi2025_search/images/'
fig,ax=plt.subplots(figsize=(13,12))
for img,gr,col,lab in [('radiantphysics_2025_03_image-4.png','oi/gr_img4.json','m','Iannello img4 (4 Mar 2025)'),('radiantphysics_2025_03_image-1.png','oi/gr_img1.json','r','Iannello img1 (4 Mar 2025)'),('radiantphysics_2025_03_image-9.png','oi/gr_img9.json','g','Iannello img9 (31 Mar 2025)')]:
    f=load(gr); im=cv2.imread(I+img); b,g,r=[im[...,i].astype(int) for i in range(3)]
    red=(r>190)&(g<70)&(b<70); ys,xs=np.nonzero(red); lon,lat=f(xs,ys)
    np.save('oi/red_'+img.split('_')[-1].replace('.png','')+'.npy',np.c_[lon,lat])
    ax.plot(lon,lat,'.',color=col,ms=1,label=lab)
g_=json.load(open('oi/search_areas.json'))
for o in g_:
    c=np.array(o['coords'])
    if 'proposed' in o['name']: c=np.vstack([c,c[:1]]); ax.plot(c[:,0],c[:,1],'k-',lw=0.8)
    if o['name']=='Ocean Infinity 2018 search': ax.plot(c[:,0],c[:,1],'-',color='orange',lw=0.8)
arc=geo.arc_polyline(geo.ARC7_BTO_US,geo.ARC7_TIME,0.0,lats=np.arange(-37,-32.5,0.02)); ax.plot(arc[:,1],arc[:,0],'b-',lw=0.8)
ax.set_xlim(91.3,95.6); ax.set_ylim(-36.6,-32.9); ax.set_aspect(1/np.cos(np.radians(34.8))); ax.grid(lw=0.3); ax.legend(markerscale=8)
plt.savefig('oi/cmp_red_all.png',dpi=100,bbox_inches='tight')
