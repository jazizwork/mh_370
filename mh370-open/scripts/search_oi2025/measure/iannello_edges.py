import numpy as np
d=np.load('oi/red_sn.npy'); s=d[:,2]; n=d[:,3]
for side,sel_out,sel_in in [('NW',(n<-75)&(n>-90),(n>-56)&(n<-44)),('SE',(n>88)&(n<100),(n>60)&(n<70))]:
    so=s[sel_out]; no=n[sel_out]
    print(side,'outer: s range',np.percentile(so,[0.5,99.5]).round(1),'n median',np.median(no).round(2))
    p=np.polyfit(so,no,1); print('   outer fit n = %.4f s + %.2f'%tuple(p))
    si=s[sel_in]; ni=n[sel_in]
    for lo,hi in [(-200,-60),(-50,100)]:
        k=(si>lo)&(si<hi); 
        if k.sum(): print(f'   inner s[{lo},{hi}] n median',np.median(ni[k]).round(2),'n',k.sum())
    # end edges: s extremes of pixels with n between inner and outer
    mid=(n<-55)&(n>-75) if side=='NW' else (n>70)&(n<88)
    print('   end edges s (0.5/99.5 pct of mid pixels)',np.percentile(s[mid],[0.5,99.5]).round(1))
