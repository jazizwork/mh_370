import numpy as np, numcodecs, sys, os
D=sys.argv[1]; b=numcodecs.Blosc()
def load(n,s,dt='<f4'): return np.frombuffer(b.decode(open(os.path.join(D,n),'rb').read()),dtype=dt).reshape(s)
lev=load('level.0',(37,),'<i8'); li={int(l):i for i,l in enumerate(lev)}
def esi(T): return np.exp(9.550426-5723.265/T+3.53068*np.log(T)-0.00728332*T)
for t,lab in [(1000896,'00:00 UTC 8 Mar')]:
    T=load(f'temperature.{t}',(37,721,1440)); q=load(f'specific_humidity.{t}',(37,721,1440))
    print('==',lab,'max RHi (%) per 1-deg lat band (rows) x 5-deg lon band (cols), 250/225/200 hPa max shown as a/b/c')
    print('lat   '+''.join(f'{lo:>13d}E' for lo in range(80,110,5)))
    for la in range(-24,-48,-2):
        row=[]
        for lo in range(80,110,5):
            i0=int((90-la)/0.25); i1=int((90-(la-2))/0.25); j0=int(lo/0.25); j1=int((lo+5)/0.25)
            vals=[]
            for p in (250,225,200):
                k=li[p]; Tk=T[k,i0:i1,j0:j1]; qk=q[k,i0:i1,j0:j1]; e=qk*p*100/(0.622+0.378*qk)
                vals.append(int((100*e/esi(Tk)).max()))
            row.append('/'.join(f'{v:3d}' for v in vals))
        print(f'{la:4d}S '+'  '.join(f'{r:>12s}' for r in row))
    # Vasquez feature
    for name,(la,lo) in {'Vasquez 46.3S 87.4E':(-46.3,87.4)}.items():
        i=int(round((90-la)/0.25)); j=int(round(lo/0.25))
        out=[]
        for p in (300,250,225,200):
            k=li[p]; Tk=T[k,i,j]; qk=q[k,i,j]; e=qk*p*100/(0.622+0.378*qk); out.append(f'{p}hPa T={Tk-273.15:.1f}C RHi={100*e/esi(Tk):.0f}%')
        print(name,' | '.join(out))
