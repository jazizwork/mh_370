import numpy as np, numcodecs, sys, os, math, datetime
D=sys.argv[1]
blosc=numcodecs.Blosc()
def load(name, shape, dtype='<f4'):
    raw=open(os.path.join(D,name),'rb').read()
    return np.frombuffer(blosc.decode(raw),dtype=dtype).reshape(shape)
lev=load('level.0',(37,),'<i8'); lat=load('latitude.0',(721,)); lon=load('longitude.0',(1440,))
tchunk=load('time.14',(67706,),'<i8'); 
def tstr(idx): return (datetime.datetime(1900,1,1)+datetime.timedelta(hours=int(tchunk[idx-14*67706]))).isoformat()
# saturation vapour pressures (Murphy & Koop 2005)
def esi(T): return np.exp(9.550426-5723.265/T+3.53068*np.log(T)-0.00728332*T)
def esw(T): return np.exp(54.842763-6763.22/T-4.21*np.log(T)+0.000367*T+np.tanh(0.0415*(T-218.8))*(53.878-1331.22/T-9.44523*np.log(T)+0.014025*T))
def sac(T,e,p,eta):
    EI=1.23; cp=1004.0; eps=0.622; Q=43.2e6
    G=EI*cp*p/(eps*Q*(1-eta))
    x=np.log(G-0.053); TLM=273.15-46.46+9.43*x+0.72*x*x
    ok=(T<TLM)&(e>=esw(TLM)-G*(TLM-T))
    return ok,TLM,G
pts={'Malacca 5.5N 99.5E':(5.5,99.5),'N571 6.3N 97.8E':(6.3,97.8),'MEKAR-ish 6.8N 96.8E':(6.8,96.8),'Andaman 6.5N 95.5E':(6.5,95.5),'post-FMT 3N 94E':(3.0,94.0),'0N 93.5E':(0.0,93.5),
     'mid 20S 94E':(-20,94.0),'25S 95E':(-25,95.0),'WSPR 29.13S 99.93E':(-29.128,99.934),'30S 95E':(-30,95.0),'IG 34.23S 93.78E':(-34.23,93.78),'CSIRO 35.6S 92.8E':(-35.6,92.8),'38S 90E':(-38,90.0)}
li={int(l):i for i,l in enumerate(lev)}
for t in [1000890,1000891,1000895,1000896]:
    try:
        T=load(f'temperature.{t}',(37,721,1440)); q=load(f'specific_humidity.{t}',(37,721,1440))
        hcc=load(f'high_cloud_cover.{t}',(721,1440))
    except Exception as ex:
        print('missing',t,ex); continue
    print(f'===== {tstr(t)} UTC (index {t}) =====')
    for name,(la,lo) in pts.items():
        i=int(round((90-la)/0.25)); j=int(round((lo%360)/0.25))
        row=[]
        for p in (250,225,200):
            k=li[p]; Tk=T[k,i,j]; qk=q[k,i,j]; e=qk*p*100/(0.622+0.378*qk)
            rhi=100*e/esi(Tk); rhw=100*e/esw(Tk)
            ok,TLM,G=sac(Tk,e,p*100,0.31)
            row.append(f"{p}hPa T={Tk-273.15:6.1f}C RHi={rhi:5.0f}% SAC={'Y' if ok else 'n'}")
        print(f"{name:22s} hcc={hcc[i,j]:.2f} | "+' | '.join(row))
    # box stats 25-40S 85-105E at 250 and 225 and 200
    i0=int((90+25)/0.25); i1=int((90+40)/0.25); j0=int(85/0.25); j1=int(105/0.25)
    for p in (250,225,200):
        k=li[p]; Tk=T[k,i0:i1+1,j0:j1+1]; qk=q[k,i0:i1+1,j0:j1+1]; e=qk*p*100/(0.622+0.378*qk)
        rhi=100*e/esi(Tk); ok,TLM,G=sac(Tk,e,p*100,0.31)
        print(f"  box 25-40S 85-105E {p}hPa: SAC-satisfied {100*ok.mean():.0f}% ; RHi>=100 {100*(rhi>=100).mean():.1f}% ; RHi>=90 {100*(rhi>=90).mean():.1f}% ; SAC&RHi>=100 {100*(ok&(rhi>=100)).mean():.1f}% ; T range {Tk.min()-273.15:.0f}..{Tk.max()-273.15:.0f}C ; TLM {TLM-273.15:.1f}C")
    i0=int((90-9)/0.25); i1=int((90-2)/0.25); j0=int(93/0.25); j1=int(101/0.25)
    for p in (250,225,200):
        k=li[p]; Tk=T[k,i0:i1+1,j0:j1+1]; qk=q[k,i0:i1+1,j0:j1+1]; e=qk*p*100/(0.622+0.378*qk)
        rhi=100*e/esi(Tk); ok,TLM,G=sac(Tk,e,p*100,0.31)
        print(f"  box 2-9N 93-101E {p}hPa: SAC {100*ok.mean():.0f}% ; RHi>=100 {100*(rhi>=100).mean():.1f}% ; RHi>=90 {100*(rhi>=90).mean():.1f}% ; SAC&ISS {100*(ok&(rhi>=100)).mean():.1f}% ; T {Tk.min()-273.15:.0f}..{Tk.max()-273.15:.0f}C")
