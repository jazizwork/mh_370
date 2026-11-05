import numpy as np
d=np.load('oi/slide_uv.npz'); u=d['u']-661.3; vv=d['v']; orange=d['orange']
res={}
for side,sgn,vlo,vhi in [('NW',-1,40,90),('SE',1,55,105)]:
    m=orange&(sgn*vv>vlo)&(sgn*vv<vhi)
    U=u[m]; V=sgn*vv[m]
    umin,umax=np.percentile(U,[0.3,99.7])
    bins=np.arange(np.floor(umin),np.ceil(umax),5.0)
    rows=[]
    for a in bins:
        k=(U>=a)&(U<a+5)
        if k.sum()<15: continue
        rows.append((a+2.5,np.percentile(V[k],2),np.percentile(V[k],98)))
    rows=np.array(rows)
    # outer edge linear fit (robust: middle 90% of bins)
    sel=(rows[:,0]>umin+10)&(rows[:,0]<umax-10)
    po=np.polyfit(rows[sel,0],rows[sel,2],1)
    ro=rows[sel,2]-np.polyval(po,rows[sel,0])
    print(side,'u range',round(umin,1),round(umax,1),'outer fit v = %.4f u + %.2f  rms %.2f px'%(po[0],po[1],ro.std()))
    for a,lo,hi in rows[::3]: print(f'   u {a:7.1f} inner {lo:6.1f} outer {hi:6.1f}')
    res[side]=dict(umin=umin,umax=umax,po=po,rows=rows)
np.save('oi/slide_strips.npy',res,allow_pickle=True)
