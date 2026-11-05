import math
c=299792458.0
def db(x): return 10*math.log10(x)
print("== wavelengths / max bistatic Doppler (V=250 m/s ~ 486 kt)")
for f in (7.04e6,10.14e6,14.097e6,18.106e6,21.096e6,28.126e6):
    lam=c/f; print(f"f={f/1e6:.3f} MHz lam={lam:.2f} m  2V/lam={2*250/lam:.1f} Hz  L/lam(777 63.7m)={63.7/lam:.2f}  FS lobe ~lam/L={math.degrees(lam/63.7):.0f} deg")
lam=c/14.097e6
print("\n== forward-scatter RCS 4*pi*A^2/lam^2 at 14.097 MHz")
for A in (100,300,500,800):
    s=4*math.pi*A*A/lam**2; print(f"A={A} m2 -> sigma_FS={s:.0f} m2 = {db(s):.1f} dBsm")
print("\n== scattered/direct power ratio (free-space bistatic eq.) Ps/Pd = sigma*R^2/(4*pi*R1^2*R2^2)")
cases=[("4000 km link, a/c at midpoint",4000e3,2000e3,2000e3),
       ("4000 km link, a/c 40 km from TX (ray at 10 km alt)",4000e3,40e3,3960e3),
       ("4000 km link, a/c 10 km from TX",4000e3,10e3,3990e3),
       ("16527 km HB9CZF-VK1CH, a/c 9868/6660 km",16527e3,9868e3,6660e3),
       ("252 km W8AC-N8GA short link, a/c at midpoint",252e3,126e3,126e3),
       ("252 km link, a/c 20 km from TX",252e3,20e3,232e3)]
for name,R,R1,R2 in cases:
    out=[]
    for sdb in (20,30,40,42.7):
        s=10**(sdb/10); r=s*R*R/(4*math.pi*R1*R1*R2*R2)
        dmax=20*math.log10(1+math.sqrt(r))
        out.append(f"s={sdb}dBsm:{db(r):.0f}dB(maxdSNR {dmax:.2g} dB)")
    print(name,"|"," ; ".join(out))
print("\n== Fresnel-zone / shadow view: |Es/Ed| ~ A*R/(lam*R1*R2), A=400 m2")
A=400
for name,R,R1,R2 in cases:
    a=A*R/(lam*R1*R2); rF=math.sqrt(lam*R1*R2/R)
    print(f"{name}: |Es/Ed|={a:.2e} -> max dSNR={20*math.log10(1+a):.2g} dB ; 1st Fresnel radius={rF/1e3:.2f} km; crossing time at 250 m/s={2*rF/250:.0f} s")
print("\n== ratio needed for a given max SNR change (coherent, in-phase)")
for d in (0.5,1,2,3):
    a=10**(d/20)-1; print(f"dSNR={d} dB needs amplitude ratio {a:.3f} = power ratio {db(a*a):.1f} dB")
print("\n== power analysis n=((z_a+z_b)*s/delta)^2, s=SD of per-spot anomaly score")
from statistics import NormalDist
N=NormalDist()
for s in (2.5,3.3):
    for delta in (1,0.5,0.1,0.01):
        for alpha in (0.05,0.05/1000):
            n=((N.inv_cdf(1-alpha)+N.inv_cdf(0.8))*s/delta)**2
            print(f"s={s} delta={delta} dB alpha={alpha:.0e} power=0.8 -> n={n:,.0f}")
print("\n== AUC <-> effect size (equal-variance normal): AUC=Phi(d/sqrt2)")
for d in (0.003,0.03,0.1,0.358):
    print(f"d={d}: AUC={N.cdf(d/math.sqrt(2)):.4f}")
print("\n== Hanley-McNeil SE for AUC=0.6043")
A_=0.6043
for n1,n2 in ((35,35),(20,50),(50,20)):
    Q1=A_/(2-A_); Q2=2*A_*A_/(1+A_)
    se=math.sqrt((A_*(1-A_)+(n1-1)*(Q1-A_**2)+(n2-1)*(Q2-A_**2))/(n1*n2))
    print(f"n_pos={n1} n_neg={n2}: SE={se:.3f}  95%CI=({A_-1.96*se:.3f},{A_+1.96*se:.3f})")
print("\n== WSPR spectral constants")
print("tone spacing 12000/8192 =",12000/8192,"Hz; symbol T=",8192/12000,"s; 162 sym ->",162*8192/12000,"s")
print("2500 Hz vs 1.4648 Hz bandwidth ratio =",db(2500/1.4648),"dB")
print("\n== thermal/ambient: kTB 2500 Hz =", db(1.380649e-23*290*2500/1e-3), "dBm")
