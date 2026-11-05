"""Refine graticule lines locally and fit quadratic (lon,lat)->(x,y) and inverse.
usage: georef.py image  'x1:lon1,x2:lon2,...'  'y1:lat1,...'  out.json"""
import sys, json, numpy as np, cv2
im=cv2.imread(sys.argv[1]); H,W=im.shape[:2]
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
bg=cv2.medianBlur(g,7).astype(np.float32)
m=(((g.astype(np.float32)-bg)>6)&(hsv[...,1]<90)).astype(np.float32)
cols=[(float(a),float(b)) for a,b in (s.split(':') for s in sys.argv[2].split(','))]
rows=[(float(a),float(b)) for a,b in (s.split(':') for s in sys.argv[3].split(','))]
band=60; win=6
obs=[]  # (x,y,lon,lat) for meridian samples (lon known) and parallel samples (lat known)
mer=[];par=[]
for x0,lon in cols:
    for yc in range(band//2,H-band//2,band):
        sub=m[yc-band//2:yc+band//2, int(x0)-win:int(x0)+win+1].sum(0)
        if sub.max()<band*0.5: continue
        xs=np.arange(int(x0)-win,int(x0)+win+1); w=sub**2
        mer.append((float((xs*w).sum()/w.sum()),float(yc),lon))
for y0,lat in rows:
    for xc in range(band//2,W-band//2,band):
        sub=m[int(y0)-win:int(y0)+win+1, xc-band//2:xc+band//2].sum(1)
        if sub.max()<band*0.5: continue
        ys=np.arange(int(y0)-win,int(y0)+win+1); w=sub**2
        par.append((float(xc),float((ys*w).sum()/w.sum()),lat))
mer=np.array(mer); par=np.array(par)
# Fit inverse model: lon = f(x,y), lat = h(x,y), quadratic. Meridian samples constrain f; parallel samples constrain h.
def A(x,y,deg):
    x=(x-W/2)/W; y=(y-H/2)/H
    t=[np.ones_like(x),x,y]
    if deg>=2: t+= [x*x,x*y,y*y]
    return np.c_[tuple(t)]
out={}
for deg in (1,2):
    cl,_,_,_=np.linalg.lstsq(A(mer[:,0],mer[:,1],deg),mer[:,2],rcond=None)
    ch,_,_,_=np.linalg.lstsq(A(par[:,0],par[:,1],deg),par[:,2],rcond=None)
    rl=mer[:,2]-A(mer[:,0],mer[:,1],deg)@cl; rh=par[:,2]-A(par[:,0],par[:,1],deg)@ch
    # residuals in km
    print(f'deg{deg}: n_mer={len(mer)} n_par={len(par)} lon resid RMS {np.sqrt((rl**2).mean())*111.32*0.82:.3f} km max {abs(rl).max()*111.32*0.82:.3f}; lat resid RMS {np.sqrt((rh**2).mean())*111:.3f} km max {abs(rh).max()*111:.3f}')
    out[f'deg{deg}']={'lon':cl.tolist(),'lat':ch.tolist()}
out['W']=W; out['H']=H
json.dump(out,open(sys.argv[4],'w'))
