"""Replay the UGIB 2020 published route through this model's BTO/BFO likelihood.

Source: Ulich, Godfrey, Iannello, Banks, "The Final Resting Place of MH370", 7 Mar 2020
(data/raw/ugib2020/2020-03-07-Final-Resting-Place-of-MH370.pdf), Figures 3 and 4 (pp. 4-5):
published aircraft states (position, flight level, rate of climb (ROC), ground speed, track) at
the radar point, the descent, the first call, and each arc.  Between published states the
position is interpolated (great-circle / along the 93.788 E meridian); the 18:23:48-18:27:43
15 NM right lateral offset (p. 31) is modelled as an instantaneous turn onto an offset leg at
27.7 deg to N571 (which completes the offset at 18:27:43 at the published ground speed) and an
instantaneous turn back.

The UGIB route is a hand-built route with a descent (FL385 -> FL100 from 18:29, ROC -1,840 fpm
at the 18:40 call), a holding-speed traverse at FL100, two FIR-boundary turns, BEDAX, and a
climb to FL390, i.e. it has altitude and speed changes that none of the families in this model
contains.  This replay therefore asks only: how well does UGIB's own path fit the same data under
the same noise model?  Vertical speed enters the BFO through the uplink Doppler (the AES
compensates horizontal velocity only), as in satcom.bfo.

Output: outputs/satcom/ugib_replay.csv, printed summary (also in outputs/satcom/ugib_replay.txt)
"""
import pathlib

import numpy as np
import pandas as pd

from mh370 import geo, satcom
from mh370 import satcom_paths as sp

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "satcom"
FPM = 0.3048 / 60
LON_SIO = 93.788          # published states print 93.788 E (BEDAX 93.7876 E)

# published states (UGIB 2020 Fig. 3 / Fig. 4): t, lat, lon, FL, ROC fpm, GS kt, TRK deg
STATES = [
    ("18:22:12 radar", geo.hms(18, 22, 12), 6.578, 96.341, 385, 0, 495, 296),
    ("18:29:00 start descent", geo.hms(18, 29, 0), 7.179, 95.684, 385, 0, 495, 296),
    ("18:35:27 direct to IGOGU", geo.hms(18, 35, 27), 7.505, 95.020, 250, -1840, 366, 271),
    ("18:39:55 call starts", geo.hms(18, 39, 55), 7.518, 94.583, 163, -1840, 337, 271),
    ("18:41:39 IGOGU (turn south)", geo.hms(18, 41, 39), 7.5169, 94.4167, 102, -1840, 330, 180),
    ("18:43:41 end descent", geo.hms(18, 43, 41), 7.329, 94.416, 100, 0, 292, 180),
    # Table E-1 (p. 130) waypoint passages at FL100, holding speed (no measurements in between;
    # used for plotting the route)
    ("18:46:21 ANOKO", geo.hms(18, 46, 21), 7.1361, 94.4161, 100, 0, 257, 180),
    ("18:53:52 NOPEK", geo.hms(18, 53, 52), 6.6039, 94.4167, 100, 0, 257, 180),
    ("19:02:16 6NFIR", geo.hms(19, 2, 16), 6.0, 94.4165, 100, 0, 257, 270),
    ("19:10:27 6NFIRWEST", geo.hms(19, 10, 27), 6.0, 93.7875, 100, 0, 257, 180),
    ("19:19:04 BEDAX", geo.hms(19, 19, 4), 5.3643, 93.7876, 100, 0, 257, 180),
    ("19:41:03 2nd arc", geo.hms(19, 41, 3), 2.930, LON_SIO, 389, 400, 480, 180),
    ("20:41:05 3rd arc", geo.hms(20, 41, 5), -5.183, LON_SIO, 390, 0, 485, 180),
    ("21:41:27 4th arc", geo.hms(21, 41, 27), -13.355, LON_SIO, 390, 0, 486, 180),
    ("22:41:22 5th arc", geo.hms(22, 41, 22), -21.420, LON_SIO, 390, 0, 478, 180),
    ("00:11:00 6th arc", geo.hms(24, 11, 0), -33.365, LON_SIO, 390, 0, 472, 180),
    ("00:19:29 7th arc", geo.hms(24, 19, 29), -34.234, LON_SIO, 192, -4304, 345, 180),
]


def offset_leg_state(t):
    """18:22:12-18:29:00: N571 (296.13 T) with a 15 NM right offset begun 18:23:48 and complete
    18:27:43 (UGIB p. 31), polyline through the published 18:22:12 and 18:29:00 points."""
    t0, t3 = geo.hms(18, 22, 12), geo.hms(18, 29, 0)
    p0, p3 = (6.578, 96.341), (7.179, 95.684)
    trk = 296.13
    t1, t2 = geo.hms(18, 23, 48), geo.hms(18, 27, 43)
    # vertices: P1 = P0 + 96 s along trk; P2 = P3 - 77 s along trk (GS fitted to the endpoints)
    d03 = geo.haversine_km(*p0, *p3) * 1000
    brg03 = float(sp.initial_bearing(*p0, *p3))
    along = d03 * np.cos(np.radians(brg03 - trk))
    cross = d03 * np.sin(np.radians(brg03 - trk))
    # solve the constant ground speed v so that v*(t1-t0) + v*(t3-t2) + sqrt((v*(t2-t1))^2 - c^2) = along
    c = cross
    f = lambda v: v * (t1 - t0) + v * (t3 - t2) + np.sqrt(max((v * (t2 - t1)) ** 2 - c ** 2, 0)) - along
    lo, hi = 150.0, 400.0
    for _ in range(80):
        m = 0.5 * (lo + hi)
        lo, hi = (m, hi) if f(m) < 0 else (lo, m)
    v = 0.5 * (lo + hi)
    P1 = sp.destination(*p0, trk, v * (t1 - t0))
    P2 = sp.destination(*p3, trk + 180, v * (t3 - t2))
    verts = [(t0, p0), (t1, P1), (t2, P2), (t3, p3)]
    for (ta, pa), (tb, pb) in zip(verts[:-1], verts[1:]):
        if ta <= t <= tb:
            d = geo.haversine_km(*pa, *pb) * 1000
            b = float(sp.initial_bearing(*pa, *pb))
            la, lo_ = sp.destination(*pa, b, d * (t - ta) / (tb - ta))
            return float(la), float(lo_), 385.0, 0.0, d / (tb - ta) / sp.KT, b, v / sp.KT, \
                float(np.degrees(np.arcsin(c / (v * (t2 - t1)))))
    raise ValueError(t)


def state_at(t, level_1840=False):
    """(lat, lon, FL, ROC fpm, GS kt, TRK deg) at time t from the published states."""
    if t <= geo.hms(18, 29, 0):
        return offset_leg_state(t)[:6]
    S = STATES
    if t >= S[-1][1]:                      # 00:19:29.416 (published state is for 00:19:29)
        z = S[-1]
        la, lo = sp.destination(z[2], z[3], z[7], z[6] * sp.KT * (t - z[1]))
        return float(la), float(lo), z[4], z[5], z[6], z[7]
    for a, b in zip(S[:-1], S[1:]):
        if a[1] <= t <= b[1]:
            break
    else:
        raise ValueError(t)
    if a[1] == geo.hms(18, 39, 55):
        # 18:39:55 -> 18:41:39: continue 271 T descending until the IGOGU turn (18:41:39)
        dt = t - a[1]
        la, lo = sp.destination(a[2], a[3], a[7], a[6] * sp.KT * dt)
        fl = a[4] + a[5] * dt / 60 / 100
        roc = 0.0 if level_1840 else a[5]
        return float(la), float(lo), fl, roc, a[6], a[7]
    # along the SIO meridian (or the 18:29-18:39 descent leg): interpolate linearly
    w = (t - a[1]) / (b[1] - a[1])
    la = a[2] + w * (b[2] - a[2])
    lo = a[3] + w * (b[3] - a[3])
    if a[1] >= geo.hms(19, 41, 3):
        roc = 0.0
        fl = 390.0 if b[1] < geo.hms(24, 19, 29) else a[4] + w * (b[4] - a[4])
    else:
        roc, fl = a[5], a[4] + w * (b[4] - a[4])
    # nearest published ROC/GS/TRK
    near = a if w < 0.5 else b
    if near[1] == geo.hms(19, 41, 3):
        roc = near[5]
    gs = a[6] + w * (b[6] - a[6])
    return la, lo, fl, roc, gs, near[7]


def loglik_from_pred(lik, bto_pred, bfo_pred):
    """Same likelihood as satcom_paths.Likelihood (analytic bias marginalisation)."""
    rb = (lik.bto.z.to_numpy() - bto_pred) / lik.bto.sigma.to_numpy()
    ll_bto = -0.5 * np.sum(rb ** 2)
    s2 = lik.bfo.sigma.to_numpy()[0] ** 2
    r = lik.bfo.z.to_numpy() - bfo_pred - lik.b0
    n = r.size
    sb2 = lik.sb ** 2
    q = np.sum(r ** 2) / s2 - (sb2 / (s2 * (s2 + n * sb2))) * np.sum(r) ** 2
    ll_bfo = -0.5 * q - 0.5 * np.log1p(n * sb2 / s2)
    b_post = sb2 * np.sum(r) / (s2 + n * sb2)
    return ll_bto + ll_bfo, ll_bto, ll_bfo, lik.bto.z.to_numpy() - bto_pred, r - b_post, lik.b0 + b_post


def replay(level_1840=False, label="as published"):
    meas = sp.build_measurements()
    lik = sp.Likelihood(meas)
    rows = []
    bto_p, bfo_p = [], []
    for kind, part in (("BTO", lik.bto), ("BFO", lik.bfo)):
        for _, m in part.iterrows():
            la, lo, fl, roc, gs, trk = state_at(m.t, level_1840)
            h = fl * 100 * sp.FT
            if kind == "BTO":
                p = float(satcom.bto(m.t, la, lo, h))
                bto_p.append(p)
            else:
                vn, ve = satcom.gs_track_to_vn_ve(gs, trk)
                p = float(satcom.bfo(m.t, la, lo, h, vn, ve, roc * FPM, bias=0.0))
                bfo_p.append(p)
            rows.append(dict(kind=kind, label=m.label, t=m.t, lat=la, lon=lo, fl=fl, roc_fpm=roc,
                             gs_kt=gs, trk=trk, measured=m.z, predicted_wo_bias=p))
    ll, llb, llf, rb, rf, bias = loglik_from_pred(lik, np.array(bto_p), np.array(bfo_p))
    df = pd.DataFrame(rows)
    df["residual"] = np.r_[rb, rf]
    df["variant"] = label
    return df, dict(variant=label, loglik=ll, ll_bto=llb, ll_bfo=llf, bias=bias,
                    bto_rms=float(np.sqrt(np.mean(rb ** 2))), bfo_rms=float(np.sqrt(np.mean(rf ** 2))),
                    bto_rms_1941_0011=float(np.sqrt(np.mean(rb[6:11] ** 2))),
                    bfo_1840=float(rf[1]), bfo_1828=float(rf[0]))


def main():
    out, summ = [], []
    for lvl, lab in ((False, "as published (descent -1840 fpm at 18:40)"),
                     (True, "same, but level flight at the 18:40 call")):
        df, s = replay(lvl, lab)
        out.append(df)
        summ.append(s)
    df = pd.concat(out)
    df.round(4).to_csv(OUT / "ugib_replay.csv", index=False)
    lines = []
    o = offset_leg_state(geo.hms(18, 25))
    lines.append(f"offset-leg model: ground speed {o[6]:.0f} kt, offset-leg angle {o[7]:.1f} deg to N571")
    for s in summ:
        lines.append(f"{s['variant']}: loglik {s['loglik']:.2f} (BTO {s['ll_bto']:.2f}, BFO {s['ll_bfo']:.2f}); "
                     f"BTO RMS {s['bto_rms']:.0f} us (19:41-00:11: {s['bto_rms_1941_0011']:.0f} us); "
                     f"BFO RMS {s['bfo_rms']:.1f} Hz; BFO residual 18:28:15 {s['bfo_1828']:+.1f} Hz, "
                     f"18:40 call {s['bfo_1840']:+.1f} Hz; fitted bias {s['bias']:.1f} Hz")
    d0 = out[0]
    lines.append("residuals (as published): " + "; ".join(
        f"{r.kind} {r.label}: {r.residual:+.1f}" for r in d0.itertuples()))
    txt = "\n".join(lines)
    print(txt)
    (OUT / "ugib_replay.txt").write_text(txt + "\n")


if __name__ == "__main__":
    main()
