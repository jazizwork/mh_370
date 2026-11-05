import sys, numpy as np, cv2
im=cv2.imread(sys.argv[1], cv2.IMREAD_COLOR)
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY).astype(np.float32)
# thin bright, low-saturation lines
bg=cv2.medianBlur(g.astype(np.uint8),7).astype(np.float32)
d=g-bg
low_sat=hsv[...,1]<90
H,W=g.shape
# column/row profiles of positive residual in low-sat pixels
m=((d>6)&low_sat).astype(np.float32)
colp=m.sum(0)/H; rowp=m.sum(1)/W
def peaks(p,thr):
    idx=[i for i in range(1,len(p)-1) if p[i]>=thr and p[i]>=p[i-1] and p[i]>=p[i+1]]
    return idx
thr=float(sys.argv[2]) if len(sys.argv)>2 else 0.25
print('cols',[(i,round(colp[i],2)) for i in peaks(colp,thr)])
print('rows',[(i,round(rowp[i],2)) for i in peaks(rowp,thr)])
cv2.imwrite('oi/gridmask.png',(m*255).astype(np.uint8))
