import json, numpy as np
def load(fn, deg='deg2'):
    d=json.load(open(fn)); W,H=d['W'],d['H']; cl=np.array(d[deg]['lon']); ch=np.array(d[deg]['lat'])
    def f(x,y):
        x=np.asarray(x,float); y=np.asarray(y,float)
        u=(x-W/2)/W; v=(y-H/2)/H
        t=[np.ones_like(u),u,v]+([u*u,u*v,v*v] if len(cl)==6 else [])
        T=np.stack(t,-1); return T@cl, T@ch
    return f
