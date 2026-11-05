import csv, sys, collections, statistics, datetime
fn=sys.argv[1]
rows=list(csv.DictReader(open(fn)))
by=collections.defaultdict(list)
for r in rows:
    if r['band'] not in ('3','7','10','14','18','21','28'): continue
    t=datetime.datetime.strptime(r['time'],"%Y-%m-%d %H:%M:%S")
    by[(r['tx_sign'],r['rx_sign'],r['band'])].append((t,int(r['snr']),int(r['drift']),int(r['distance'])))
diffs=collections.defaultdict(list); dd=collections.defaultdict(list)
win_sd=[]; win_sd_long=[]
drift_all=collections.Counter()
for k,v in by.items():
    v.sort()
    # dedupe same time
    seen={}
    for t,s,d,dist in v: seen[t]=(s,d,dist)
    ts=sorted(seen)
    for t in ts: drift_all[seen[t][1]]+=1
    for i in range(1,len(ts)):
        lag=int((ts[i]-ts[i-1]).total_seconds()/60)
        if lag in (2,4,6,8,10,12,20,30):
            diffs[lag].append(seen[ts[i]][0]-seen[ts[i-1]][0])
            if seen[ts[i]][2]>1000: dd[lag].append(seen[ts[i]][0]-seen[ts[i-1]][0])
    # 30-min windows with >=5 spots: SD of snr
    if len(ts)>=5:
        start=ts[0]; bucket=collections.defaultdict(list)
        for t in ts: bucket[int((t-start).total_seconds()//1800)].append(seen[t][0])
        for b,s in bucket.items():
            if len(s)>=5:
                (win_sd_long if seen[ts[0]][2]>1000 else win_sd).append(statistics.pstdev(s))
def summ(x):
    x=sorted(x); n=len(x)
    if n<5: return f"n={n}"
    sd=statistics.pstdev(x); mad=statistics.median([abs(a) for a in x])
    p=lambda q:x[int(q*(n-1))]
    big=sum(1 for a in x if abs(a)>=3)/n
    return f"n={n} sd={sd:.2f} medAbs={mad} p05={p(.05)} p95={p(.95)} frac|d|>=3dB={big:.2f}"
print("file",fn,"rows",len(rows),"pairs",len(by))
for lag in sorted(diffs): print(f"lag {lag:2d} min  all: {summ(diffs[lag])} | dist>1000km: {summ(dd[lag])}")
print("30-min-window SNR SD (>=5 spots) dist>1000km: n=%d median=%.2f p90=%.2f"%(len(win_sd_long),statistics.median(win_sd_long),sorted(win_sd_long)[int(.9*len(win_sd_long))]))
print("30-min-window SNR SD (>=5 spots) dist<=1000km: n=%d median=%.2f"%(len(win_sd),statistics.median(win_sd)) if win_sd else "")
tot=sum(drift_all.values()); print("drift distribution:",{k:round(v/tot,4) for k,v in sorted(drift_all.items())})
