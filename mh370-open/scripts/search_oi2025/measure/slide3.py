import cv2, numpy as np
im=cv2.imread('data/raw/oi2025_search/images/radiantphysics_2024_03_searcharea-1.png')
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=[hsv[...,i].astype(int) for i in range(3)]
dots=((h>=84)&(h<=94)&(s>110)&(v>140)).astype(np.uint8)
# keep components whose surrounding ring is gray/blue band (low-mid sat) -> compute mean sat in 7x7 neighbourhood excluding the dot
n,lab,st,cen=cv2.connectedComponentsWithStats(dots)
blur_s=cv2.blur(s.astype(np.float32),(9,9))
cand=[]
for i in range(1,n):
    if 2<=st[i,4]<=25 and st[i,2]<=6 and st[i,3]<=6:
        x,y=cen[i]
        if blur_s[int(y),int(x)]<130: cand.append((x,y))
c=np.array(cand); print('cands',len(c))
rng=np.random.default_rng(1); best=(0,None)
for _ in range(5000):
    i,j=rng.choice(len(c),2,replace=False); p,q=c[i],c[j]
    if np.hypot(*(q-p))<100: continue
    d=q-p; nrm=np.array([-d[1],d[0]])/np.hypot(*d)
    r=np.abs((c-p)@nrm); inl=r<1.5
    if inl.sum()>best[0]: best=(inl.sum(),inl)
inl=best[1]; ci=c[inl]
A=np.c_[ci[:,0],np.ones(len(ci))]; k,b=np.linalg.lstsq(A,ci[:,1],rcond=None)[0]
r=(ci[:,1]-(k*ci[:,0]+b))/np.hypot(1,k)
print('inliers',inl.sum(),'y=%.5f x + %.3f angle %.3f rms %.2f'%(k,b,np.degrees(np.arctan(-k)),np.sqrt((r**2).mean())),'x',ci[:,0].min().round(),ci[:,0].max().round())
# dot spacing
u=np.sort((ci[:,0]+k*ci[:,1])/np.hypot(1,k)); du=np.diff(u); print('spacing median',np.median(du).round(2))
q=np.polyfit(ci[:,0],ci[:,1],2); print('quad',q, 'max dev from line px', np.abs(np.polyval(q,ci[:,0])-(k*ci[:,0]+b)).max().round(2))
np.save('oi/slide_arcline.npy',np.array([k,b])); np.save('oi/slide_arcdots.npy',ci)
