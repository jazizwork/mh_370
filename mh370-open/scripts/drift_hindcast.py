"""Workstream B cross-check: 2014-15 HYCOM hindcast of flaperon arrival at Reunion vs origin
latitude on the 7th arc (generic 1.2% windage vs CSIRO flaperon leeway), compared with the
climatological drifter Markov chain.

Run (after scripts/drift_hycom_download.py): .venv/bin/python -I scripts/drift_hindcast.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from mh370 import drift_debris as dd
from mh370 import geo
from mh370.drift_data import NcepDailyWind
from mh370.drift_hindcast import HycomDaily, run

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "drift"
N_PER_LAT = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
SIGMA_KM = 30.0
R_KM = 150.0
LATS = np.arange(-42.0, -19.9, 1.0)


def velocity_check(hy, wind):
    """Pointwise comparison of the hindcast velocity model (HYCOM 0 m + 1.2% NCEP wind) with
    GDP undrogued-drifter velocities (ve, vn) during the hindcast period, 50S-5S, 20-120E."""
    import json
    from mh370.drift_data import load_gdp
    g = load_gdp()
    t = g["time"]
    m = ((t >= hy.t_unix[0]) & (t <= hy.t_end) & (g["drogue"] == 0) & (g["lat"] > -50) & (g["lat"] < -5)
         & (g["lon"] > 20) & (g["lon"] < 120) & np.isfinite(g["ve"]))
    idx = np.flatnonzero(m)[::4]          # daily subsample
    out = {}
    U, V = wind(t[idx], g["lat"][idx], g["lon"][idx])
    u = np.empty(idx.size)
    v = np.empty(idx.size)
    for i, k in enumerate(idx):
        a, b = hy(t[k], g["lat"][k:k + 1], g["lon"][k:k + 1])
        u[i], v[i] = a[0], b[0]
    for name, wf in (("hycom_only", 0.0), ("hycom_plus_1.2pct_wind", 0.012)):
        um, vm = u + wf * U, v + wf * V
        ok = np.isfinite(um) & np.isfinite(vm)
        ve, vn = g["ve"][idx][ok], g["vn"][idx][ok]
        out[name] = dict(
            n=int(ok.sum()),
            bias_u=float(np.mean(um[ok] - ve)), bias_v=float(np.mean(vm[ok] - vn)),
            rmsd=float(np.sqrt(np.mean((um[ok] - ve) ** 2 + (vm[ok] - vn) ** 2))),
            corr_u=float(np.corrcoef(um[ok], ve)[0, 1]), corr_v=float(np.corrcoef(vm[ok], vn)[0, 1]),
            mean_model=[float(np.mean(um[ok])), float(np.mean(vm[ok]))],
            mean_drifters=[float(np.mean(ve)), float(np.mean(vn))],
            rms_model=float(np.sqrt(np.mean(um[ok] ** 2 + vm[ok] ** 2))),
            rms_drifters=float(np.sqrt(np.mean(ve ** 2 + vn ** 2))))
    (OUT / "hindcast_velocity_check.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1), flush=True)


def main():
    hy = HycomDaily()
    wind = NcepDailyWind([2014, 2015])
    velocity_check(hy, wind)
    t0 = (dd.RELEASE_TIME - np.datetime64("1970-01-01T00:00")).astype("timedelta64[s]").astype(float)
    n_days = min(545.0, (hy.t_end - t0) / 86400.0 - 1)
    print(f"HYCOM to {np.datetime64(int(hy.t_end), 's')}, running {n_days:.0f} days", flush=True)
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
    rng = np.random.default_rng(370)
    rl, rlo, grp = [], [], []
    for g, la in enumerate(LATS):
        lo = np.interp(la, arc[:, 0], arc[:, 1])
        dy = rng.normal(0, SIGMA_KM, N_PER_LAT) / 111.195
        dx = rng.normal(0, SIGMA_KM, N_PER_LAT) / (111.195 * np.cos(np.radians(la)))
        rl.append(la + dy)
        rlo.append(lo + dx)
        grp.append(np.full(N_PER_LAT, g))
    rl, rlo, grp = map(np.concatenate, (rl, rlo, grp))
    fl = dd.ITEM_BY_KEY["flaperon"]
    a, b = fl.window()
    rows = {}
    for name, lee in (("generic", None), ("flaperon", "flaperon")):
        res = run(rl, rlo, t0, n_days, lee, hycom=hy, wind=wind)
        days = res["record_days"]
        LA, LO, AL = res["lat"], res["lon"], res["alive"]
        d = geo.haversine_km(fl.lat, fl.lon, LA, LO)
        # stranding day (first record with alive False)
        dead_day = np.where(AL.all(0), np.inf, days[np.argmax(~AL, axis=0)])
        win = (days >= a) & (days <= b)
        if win.any():
            near_alive = ((d[win] <= R_KM) & AL[win]).any(0)
        else:
            near_alive = np.zeros(rl.size, bool)
        strand_near = (dead_day >= a) & (dead_day <= b) & (d[-1] <= R_KM)
        visit = near_alive | strand_near
        k508 = np.searchsorted(days, min(508.5, days[-1]))
        west60 = LO[: k508 + 1].min(0) < 60.0
        reach_reu = ((d[: k508 + 1] <= R_KM)).any(0)
        # WA stranding: stranded east of 108E between 36S and 20S, within 548 days
        wa = (~AL[-1]) & (LO[-1] > 108) & (LA[-1] > -36) & (LA[-1] < -20) & (dead_day <= 548)
        for g, la in enumerate(LATS):
            m = grp == g
            r = rows.setdefault(la, {"release_lat": la, "n": int(m.sum())})
            r[f"visit_window_{name}"] = float(visit[m].mean())
            r[f"n_visit_{name}"] = int(visit[m].sum())
            r[f"reach_reunion_by508_{name}"] = float(reach_reu[m].mean())
            r[f"west60_by508_{name}"] = float(west60[m].mean())
            r[f"strand_WA_{name}"] = float(wa[m].mean())
        print("done", name, flush=True)
    df = pd.DataFrame(list(rows.values()))
    # Markov-chain comparison (flaperon-only profiles, on-arc +/-100 km)
    prof = pd.read_csv(OUT / "arc_profile.csv")
    for col, src in (("mc_loglik_undrogued", "loglik_flaperon_only"),
                     ("mc_loglik_leeway", "loglik_flaperon_only_leeway")):
        df[col] = np.interp(df.release_lat, prof.arc_lat, prof[src])
    df.attrs["n_days"] = n_days
    df.to_csv(OUT / "hindcast_flaperon.csv", index=False, float_format="%.5f")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
