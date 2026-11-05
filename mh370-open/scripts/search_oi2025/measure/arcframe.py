"""Arc-following coordinates: s = along-arc distance (km, +NE) of the foot point, n = signed normal distance (km, +SE/outward)."""
import sys, numpy as np
sys.path.insert(0,'src')
from mh370 import geo
from pyproj import Geod
G=Geod(ellps='WGS84')
_lats=np.arange(-39,-30,0.005)
ARC=geo.arc_polyline(geo.ARC7_BTO_US,geo.ARC7_TIME,0.0,lats=_lats)  # (lat,lon)
_az,_,_d=G.inv(ARC[:-1,1],ARC[:-1,0],ARC[1:,1],ARC[1:,0])
S=np.r_[0,np.cumsum(_d)]/1000.0
# reference s=0 at lat -34.2342 (LEP latitude)
S0=np.interp(-34.2342,ARC[::-1,0] if ARC[0,0]>ARC[-1,0] else ARC[:,0],S[::-1] if ARC[0,0]>ARC[-1,0] else S)
S=S-S0
AZ=np.r_[_az,_az[-1]]
def to_sn(lon,lat):
    lon=np.atleast_1d(np.asarray(lon,float)); lat=np.atleast_1d(np.asarray(lat,float))
    s=np.empty(lon.size); n=np.empty(lon.size)
    for k,(lo,la) in enumerate(zip(lon,lat)):
        # coarse nearest by equirectangular
        dx=(ARC[:,1]-lo)*np.cos(np.radians(la)); dy=ARC[:,0]-la
        i=np.argmin(dx*dx+dy*dy)
        j=slice(max(i-40,0),min(i+41,len(ARC)))
        _,_,dd=G.inv(np.full(ARC[j].shape[0],lo),np.full(ARC[j].shape[0],la),ARC[j,1],ARC[j,0])
        ii=j.start+np.argmin(dd)
        lon_arc=np.interp(la,ARC[:,0],ARC[:,1]) if ARC[0,0]<ARC[-1,0] else np.interp(la,ARC[::-1,0],ARC[::-1,1])
        s[k]=S[ii]; n[k]=(1 if lo>lon_arc else -1)*dd.min()/1000
    return s,n
def from_sn(s,n):
    s=np.atleast_1d(np.asarray(s,float)); n=np.atleast_1d(np.asarray(n,float))
    la=np.interp(s,S,ARC[:,0]); lo=np.interp(s,S,ARC[:,1]); az=np.interp(s,S,AZ)
    # normal direction to SE = az+90
    lo2,la2,_=G.fwd(lo,la,az+90.0,n*1000.0)
    return lo2,la2
