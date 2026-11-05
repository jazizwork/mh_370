import csv, sys, math, collections
rows=list(csv.DictReader(open(sys.argv[1])))
txc=collections.Counter(r['tx_sign'] for r in rows)
def pts(lat1,lon1,lat2,lon2,long=False,n=240):
    p1,l1,p2,l2=map(math.radians,(lat1,lon1,lat2,lon2))
    d=2*math.asin(math.sqrt(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin((l2-l1)/2)**2))
    if d<1e-6: return []
    f0,f1=(1,2*math.pi/d) if long else (0,1)
    out=[]
    for i in range(n+1):
        f=f0+(f1-f0)*i/n
        A=math.sin((1-f)*d)/math.sin(d); B=math.sin(f*d)/math.sin(d)
        x=A*math.cos(p1)*math.cos(l1)+B*math.cos(p2)*math.cos(l2)
        y=A*math.cos(p1)*math.sin(l1)+B*math.cos(p2)*math.sin(l2)
        z=A*math.sin(p1)+B*math.sin(p2)
        out.append((math.degrees(math.atan2(z,math.hypot(x,y))),math.degrees(math.atan2(y,x))))
    return out
box=(-40,-20,85,105)
inb=lambda p: box[0]<=p[0]<=box[1] and box[2]<=p[1]<=box[3]
cache={}; sp=collections.Counter(); lp=collections.Counter(); lpp=collections.Counter(); late=collections.Counter()
for r in rows:
    if txc[r['tx_sign']]<3: continue
    k=(r['tx_lat'],r['tx_lon'],r['rx_lat'],r['rx_lon'])
    if k not in cache:
        a=list(map(float,k))
        cache[k]=(any(map(inb,pts(*a))),any(map(inb,pts(*a,long=True))))
    s,l=cache[k]
    if s: sp[r['time'][:13]]+=1
    if l and int(r["distance"])>=int(sys.argv[2]):
        lp[r['time'][:13]]+=1; lpp[(r['tx_sign'],r['rx_sign'],r['band'],r['distance'])]+=1
    if (s or l) and r['time']>='2014-03-07 23:30:00': late[(r['time'],r['tx_sign'],r['rx_sign'],r['band'],'SP' if s else 'LP',r['snr'])]+=1
print("SIO box short-path by hour",dict(sorted(sp.items())),"total",sum(sp.values()))
print("SIO box long-path by hour",dict(sorted(lp.items())),"total",sum(lp.values()),"distinct links",len(lpp))
for p,n in lpp.most_common(12): print("  LP",n,p)
print("spots SP or LP crossing box 23:30-01:00:",len(late))
for k in sorted(late)[:40]: print("  ",k)
