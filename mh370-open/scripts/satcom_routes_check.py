"""Forward-model sanity checks for the multi-leg route families (reviewer response).

1. TWO with u2 = 1 (second turn at 00:19:29) must equal the single-mode CTT model exactly.
2. TWO with theta2 = theta1 and random u2 must equal CTT up to integration error
   (the turn time only splits one 120 s midpoint step into two).
3. WPT with mode2 = LNAV and theta2 = the course of the same great circle at W must equal the
   single-mode LNAV model with theta = initial azimuth from the FMT point to W.
4. Timing: one likelihood evaluation, N = 5000 particles, per family.
(The evidence-level check -- TWO with theta2 tied to theta1 reproducing the CTT single-mode
log-evidence -- is an SMC run: satcom_run_routes.py --family TWO --tie.)

Output: outputs/satcom/routes_sanity_check.txt
"""
import pathlib
import time

import numpy as np

from mh370 import geo, satcom
from mh370 import satcom_paths as sp
from mh370 import satcom_routes as sr

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "satcom" / "routes_sanity_check.txt"


def prior_draw(n, rng):
    la, lo = sp.RADAR_POS
    s = sp.RADAR_SIGMA_NM / 60
    return dict(lat0=rng.normal(la, s, n), lon0=rng.normal(lo, s / np.cos(np.radians(la)), n),
                trk_pre=rng.uniform(280, 310, n), gs_pre=rng.uniform(400, 500, n),
                t_fmt=rng.uniform(sp.T_RADAR + 30, geo.hms(18, 40), n),
                theta=rng.uniform(170, 200, n), mach=rng.uniform(0.75, 0.86, n),
                fl=rng.uniform(300, 400, n))


def preds(o, lik, tm):
    bto, bfo = lik.predict(o, tm)
    return bto, bfo


def main():
    lines = []

    def log(s):
        print(s, flush=True)
        lines.append(s)

    rng = np.random.default_rng(7)
    meas = sp.build_measurements()
    lik = sp.Likelihood(meas)
    atm = sp.Atmos()
    n = 400
    P = prior_draw(n, rng)
    ctt = sp.PathModel("CTT", meas, atm=atm)
    o_ref = ctt.run(P)
    b_ref, f_ref = preds(o_ref, lik, ctt.t_meas)
    ll_ref = lik(o_ref, ctt.t_meas)
    two = sr.RouteModel("TWO", meas, atm=atm)
    # --- 1. u2 = 1
    Q = dict(P, theta1=P["theta"], theta2=rng.uniform(140, 230, n), u2=np.ones(n))
    o = two.run(Q)
    b, f = preds(o, lik, two.t_meas)
    log("1. TWO(u2=1) vs CTT: max |dBTO| = %.2e us, max |dBFO| = %.2e Hz, max |dloglik| = %.2e"
        % (np.abs(b - b_ref).max(), np.abs(f - f_ref).max(), np.abs(lik(o, two.t_meas) - ll_ref).max()))
    # --- 2. theta2 = theta1, random u2
    Q = dict(P, theta1=P["theta"], theta2=P["theta"], u2=rng.uniform(0, 1, n))
    o = two.run(Q)
    b, f = preds(o, lik, two.t_meas)
    iend = int(np.argmin(np.abs(two.t_meas - geo.ARC7_TIME)))
    dkm = geo.haversine_km(o["lat"][:, iend], o["lon"][:, iend], o_ref["lat"][:, iend], o_ref["lon"][:, iend])
    log("2. TWO(theta2=theta1, u2~U(0,1)) vs CTT: max |dBTO| = %.3f us, max |dBFO| = %.4f Hz, "
        "max |dloglik| = %.4f, max 00:19:29 position difference = %.3f km"
        % (np.abs(b - b_ref).max(), np.abs(f - f_ref).max(),
           np.abs(lik(o, two.t_meas) - ll_ref).max(), dkm.max()))
    # --- 3. WPT continuing the same great circle vs LNAV
    # The single-mode LNAV course law (great circle fixed at the FMT, spherical course, ellipsoidal
    # integration) drifts 0.4-0.9 km cross-track over ~150 NM; the WPT direct-to leg converges on
    # W.  So agreement is expected only to that level.  Reported for near-fitting paths
    # (loglik > -30) as well as for all prior draws.
    good = ll_ref > -1e9
    for wname in ("BEDAX", "ISBIX", "RUNUT"):
        tf = P["t_fmt"]
        ex = {"t": np.unique(np.concatenate([meas.t.to_numpy(), np.unique(tf)]))}
        lnav = sp.PathModel("LNAV", ex, atm=atm)
        wpt_x = sr.RouteModel("WPT", ex, mode2="LNAV", wpt=wname, atm=atm)
        o0 = lnav.run(P)
        k = np.searchsorted(lnav.t_meas, tf)
        flat, flon = o0["lat"][np.arange(n), k], o0["lon"][np.arange(n), k]
        az = sp.initial_bearing(flat, flon, wpt_x.wlat, wpt_x.wlon)
        nv = np.cross(sr._unit(flat, flon), wpt_x.rW)
        nv /= np.linalg.norm(nv, axis=-1, keepdims=True)
        crs_w = sp.gc_course(nv, np.full(n, wpt_x.wlat), np.full(n, wpt_x.wlon))
        o_l = lnav.run(dict(P, theta=az))
        o_w = wpt_x.run(dict(P, theta2=np.mod(crs_w, 360)), record_track=True)
        # cross-track of the WPT leg-1 track from the great circle FMT -> W
        r = sr._unit(o_w["track_lat"], o_w["track_lon"])
        xt = np.abs(np.arcsin(np.sum(r * nv[:, None, :], -1))) * 6371.0
        leg1 = (o_w["track_t"][None, :] > tf[:, None]) & (o_w["track_t"][None, :] < o_w["t_sw2"][:, None])
        xt1 = np.where(leg1, xt, 0).max()
        iend = int(np.argmin(np.abs(lnav.t_meas - geo.ARC7_TIME)))
        dkm = geo.haversine_km(o_w["lat"][:, iend], o_w["lon"][:, iend], o_l["lat"][:, iend], o_l["lon"][:, iend])
        i_std = np.isin(lnav.t_meas, meas.t.to_numpy())
        sub = lambda o: {kk: (v[:, i_std] if np.ndim(v) == 2 and v.shape[1] == lnav.t_meas.size else v)
                         for kk, v in o.items()}
        ll_w = lik(sub(o_w), lnav.t_meas[i_std])
        ll_l = lik(sub(o_l), lnav.t_meas[i_std])
        g = ll_l > -30
        log(f"3. WPT({wname}) direct-to leg, then LNAV continuing the same great circle, vs single-mode "
            f"LNAV (theta = azimuth FMT->{wname}); n = {n} prior draws, W reached by "
            f"{np.isfinite(o_w['t_sw2']).mean():.0%}:\n"
            f"   snap distance at W: max {np.nanmax(o_w['snap_km'])*1000:.0f} m; max cross-track of the "
            f"direct-to leg from the FMT->W great circle: {xt1*1000:.0f} m\n"
            f"   00:19:29 position difference vs LNAV: median {np.median(dkm):.2f} km, max {dkm.max():.2f} km; "
            f"|dloglik| for near-fitting paths (n={g.sum()}): "
            f"{'max %.2f' % np.abs(ll_w - ll_l)[g].max() if g.any() else 'n/a'}; all draws: median "
            f"{np.median(np.abs(ll_w - ll_l)):.2f}")
    # --- 4. timing
    for fam, kw in (("CTT", None), ("TWO", {}), ("WPT", dict(mode2="CTT", wpt="BEDAX")),
                    ("WPT", dict(mode2="CMH", wpt="BEDAX"))):
        Pn = prior_draw(5000, rng)
        if fam == "CTT":
            m = sp.PathModel("CTT", meas, atm=atm)
        else:
            m = sr.RouteModel(fam, meas, atm=atm, **kw)
            Pn = dict(Pn, theta1=Pn["theta"], theta2=Pn["theta"], u2=rng.uniform(0, 1, 5000))
        t0 = time.time()
        o = m.run(Pn)
        lik(o, m.t_meas)
        log(f"4. timing {fam} {kw or ''}: {time.time()-t0:.2f} s per 5000-particle likelihood")
    OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
