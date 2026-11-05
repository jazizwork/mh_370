import numpy as np
d=np.load('oi/slide_uv.npz'); u=d['u']-661.3; vv=d['v']; orange=d['orange']
for side,sgn,bands in [('NW',-1,[(52,58),(60,66),(68,74),(74,79)]),('SE',1,[(68,74),(76,82),(84,90),(90,95)])]:
    for lo,hi in bands:
        m=orange&(sgn*vv>lo)&(sgn*vv<hi)
        print(side,f'v {lo}-{hi}: u min/max (0.5/99.5 pct)',np.percentile(u[m],[0.5,99.5]).round(1), m.sum())
