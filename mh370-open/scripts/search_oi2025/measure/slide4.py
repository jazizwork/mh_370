import cv2, numpy as np
im=cv2.imread('data/raw/oi2025_search/images/radiantphysics_2024_03_searcharea-1.png')
hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV); h,s,v=[hsv[...,i].astype(int) for i in range(3)]
H,W=h.shape
k,b=np.load('oi/slide_arcline.npy')
L=np.hypot(1,k); dvec=np.array([1,k])/L  # along (x increasing -> NE since k<0 => y decreasing)
nvec=np.array([-k,1])/L  # normal: points to +y side for... check sign: SE = down-right
yy,xx=np.mgrid[0:H,0:W]
u=(xx*dvec[0]+(yy-b)*dvec[1]); vv=(xx*nvec[0]+(yy-b)*nvec[1])
# ensure SE positive: a point down-right of the line, e.g. (700,500)
if (700*nvec[0]+(500-b)*nvec[1])<0: nvec=-nvec; vv=-vv
print('normal',nvec)
orange=((h>=3)&(h<=35)&(s>40)&(v>60))
orange&=(yy>150)&(yy<540)&(xx>250)&(xx<640)
band=((s<40)&(v>120)&(v<215)) | ((h>=95)&(h<=112)&(s>=40)&(s<=140)&(v>=110)&(v<=210))
black=(v<70)
# IG hotspot red square
red=(((h<=6)|(h>=174))&(s>180)&(v>150))
ys,xs=np.nonzero(red&(yy<330)&(yy>280)&(xx>450)&(xx<500)); print('IG square centre px',xs.mean().round(1),ys.mean().round(1),'u',(xs.mean()*dvec[0]+(ys.mean()-b)*dvec[1]).round(1),'v',(xs.mean()*nvec[0]+(ys.mean()-b)*nvec[1]).round(1))
np.savez('oi/slide_uv.npz',u=u,v=vv,orange=orange,band=band,black=black)
# orange strip extents
for side,sel in [('NW',vv<0),('SE',vv>0)]:
    m=orange&sel
    print(side,'orange u range pct1/99',np.percentile(u[m],[0.5,99.5]).round(1),'v pct 1/99',np.percentile(vv[m],[0.5,99.5]).round(1))
# per u-bin: orange v-extent, and band edge (last band pixel moving outward from arc)
for u0 in range(-260,300,40):
    row=[]
    for side,sgn in [('NW',-1),('SE',1)]:
        m=orange&(np.abs(u-u0)<10)&(sgn*vv>0)
        o=(np.percentile(sgn*vv[m],[2,98]).round(1) if m.sum()>30 else None)
        mb=band&(np.abs(u-u0)<10)&(sgn*vv>0)&(sgn*vv<160)
        be=np.percentile(sgn*vv[mb],99).round(1) if mb.sum()>30 else None
        row.append(f'{side}: orange {o} bandedge {be}')
    print(u0,' | '.join(row))
