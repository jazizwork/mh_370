import csv, sys, math, collections
fn = sys.argv[1]
rows = list(csv.DictReader(open(fn)))
print("total rows", len(rows))
R=6371.0
def gc_points(lat1,lon1,lat2,lon2,n=60):
    p1=math.radians(lat1); l1=math.radians(lon1); p2=math.radians(lat2); l2=math.radians(lon2)
    d=2*math.asin(math.sqrt(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin((l2-l1)/2)**2))
    if d==0: return [(lat1,lon1)]
    pts=[]
    for i in range(n+1):
        f=i/n
        A=math.sin((1-f)*d)/math.sin(d); B=math.sin(f*d)/math.sin(d)
        x=A*math.cos(p1)*math.cos(l1)+B*math.cos(p2)*math.cos(l2)
        y=A*math.cos(p1)*math.sin(l1)+B*math.cos(p2)*math.sin(l2)
        z=A*math.sin(p1)+B*math.sin(p2)
        pts.append((math.degrees(math.atan2(z,math.sqrt(x*x+y*y))),math.degrees(math.atan2(y,x))))
    return pts
boxes={
 "SIO_7th_arc (-40..-20S, 85..105E)":(-40,-20,85,105),
 "Broad_IO (-45..10, 70..115E)":(-45,10,70,115),
 "Malacca/Andaman (0..15N, 90..105E)":(0,15,90,105),
}
# false-decode filter: require tx_sign seen >=3 times in window
txcount=collections.Counter(r['tx_sign'] for r in rows)
res={b:collections.Counter() for b in boxes}
pairs={b:collections.Counter() for b in boxes}
hours={b:collections.Counter() for b in boxes}
cache={}
for r in rows:
    if txcount[r['tx_sign']]<3: continue
    key=(r['tx_lat'],r['tx_lon'],r['rx_lat'],r['rx_lon'])
    if key not in cache:
        pts=gc_points(float(r['tx_lat']),float(r['tx_lon']),float(r['rx_lat']),float(r['rx_lon']))
        cache[key]={b:any(la0<=la<=la1 and lo0<=lo<=lo1 for la,lo in pts) for b,(la0,la1,lo0,lo1) in boxes.items()}
    for b,hit in cache[key].items():
        if hit:
            res[b][r['band']]+=1
            pairs[b][(r['tx_sign'],r['tx_loc'],r['rx_sign'],r['rx_loc'],r['band'],r['distance'])]+=1
            hours[b][r['time'][:13]]+=1
for b in boxes:
    print("\n==",b,"spots crossing (tx seen>=3x):",sum(res[b].values()),"by band:",dict(sorted(res[b].items(),key=lambda x:int(x[0]))))
    print("  by hour:",dict(sorted(hours[b].items())))
    print("  distinct tx-rx-band paths:",len(pairs[b]))
    for p,n in pairs[b].most_common(25): print("   ",n,p)
print("\nsingle-occurrence tx signs (likely incl. false decodes):",sum(1 for s,c in txcount.items() if c==1))
