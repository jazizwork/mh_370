"""Profile likelihood of the 7th-arc latitude for the multi-leg route families (reviewer response).

Same method as scripts/satcom_profile.py: maximise log L(BTO, BFO) + log prior(radar point)
subject to the 00:19:29 latitude = target (quadratic penalty, sd 0.03 deg), with differential
evolution inside the baseline prior bounds; plus an unconstrained best fit (target = none).
Values are upper bounds on the true optimum (best of the seeds is kept).

Configurations (name: family, waypoint, mode2, fixed parameters):
  TWO           generic two-leg, constant true tracks theta1 -> theta2
  BEDAX-180     WPT, BEDAX, LNAV with theta2 fixed at 180 deg (UGIB-like: BEDAX -> South Pole)
  BEDAX-CTT     WPT, BEDAX, constant true track theta2 free
  plus any "--wpt NAME:MODE2" given on the command line.

Output: outputs/satcom/profile_likelihood_v2.csv (+ _allruns), printed summary
Run   : .venv/bin/python -I scripts/satcom_routes_profile.py [--wpt ISBIX:CTT ...]
"""
import argparse
import itertools
import multiprocessing as mp
import pathlib

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

from mh370 import geo
from mh370 import satcom_paths as sp
from mh370 import satcom_routes as sr

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "satcom"
TARGETS = [None, -40.0, -39.0, -38.0, -37.0, -36.0, -35.0, -34.2342, -33.0, -32.0, -31.0, -30.0,
           -29.0, -28.0]
BASE = {"TWO": ("TWO", None, "CTT", {}),
        "BEDAX-180": ("WPT", "BEDAX", "LNAV", {"theta2": 180.0}),
        "BEDAX-CTT": ("WPT", "BEDAX", "CTT", {})}
CONFIGS = dict(BASE)
_cache = {}


def _setup(name):
    if name not in _cache:
        fam, wpt, mode2, fix = CONFIGS[name]
        meas = sp.build_measurements()
        model = sr.RouteModel(fam, meas, mode2=mode2, wpt=wpt)
        lik = sp.Likelihood(meas)
        la, lo = sp.RADAR_POS
        s = sp.RADAR_SIGMA_NM / 60
        so = s / np.cos(np.radians(la))
        b = {"lat0": (la - 3 * s, la + 3 * s), "lon0": (lo - 3 * so, lo + 3 * so),
             "trk_pre": (270, 340), "gs_pre": (350, 520), "t_fmt": (sp.T_RADAR + 30, geo.hms(19, 40)),
             "theta1": (140, 230), "theta2": (140, 230), "u2": (0, 1), "mach": (0.70, 0.86),
             "fl": (300, 400)}
        names = [k for k in sr.PARAMS[fam] if k not in fix]
        bounds = [b[k] for k in names]
        iend = int(np.argmin(np.abs(model.t_meas - geo.ARC7_TIME)))
        _cache[name] = (model, lik, bounds, names, fix, iend, (la, lo, s, so))
    return _cache[name]


def solve(args):
    name, target, seed = args
    model, lik, bounds, names, fix, iend, (la, lo, s, so) = _setup(name)

    def f(X):
        X = np.atleast_2d(X.T if X.ndim == 2 else X[None, :])
        o = model.run(sr.make_params(X, names, fix))
        ll = lik(o, model.t_meas)
        lpr = -0.5 * (((X[:, 0] - la) / s) ** 2 + ((X[:, 1] - lo) / so) ** 2)
        pen = 0.0 if target is None else 0.5 * ((o["lat"][:, iend] - target) / 0.03) ** 2
        v = -(ll + lpr) + pen
        return np.where(np.isfinite(v), v, 1e9)

    r = differential_evolution(f, bounds, popsize=16, maxiter=500, tol=1e-8, seed=seed,
                               vectorized=True, updating="deferred", polish=False,
                               mutation=(0.5, 1.0), recombination=0.9)
    x = r.x
    o = model.run(sr.make_params(x[None, :], names, fix))
    ll, parts = lik(o, model.t_meas, return_parts=True)
    bl = list(lik.bfo.label)
    row = dict(config=name, target_lat=np.nan if target is None else target, seed=seed,
               end_lat=float(o["lat"][0, iend]), end_lon=float(o["lon"][0, iend]),
               loglik=float(ll[0]), bto_rms_us=float(np.sqrt(np.mean(parts["bto_res"][0] ** 2))),
               bfo_rms_hz=float(np.sqrt(np.mean(parts["bfo_res"][0] ** 2))),
               bfo_max_abs_hz=float(np.max(np.abs(parts["bfo_res"][0]))),
               bfo_res_1840=float(parts["bfo_res"][0][bl.index("C 18:40 mean")]),
               bfo_res_1828=float(parts["bfo_res"][0][bl.index("R1200 18:28:15")]),
               bias_hz=float(parts["bias"][0]), t_sw2=float(o["t_sw2"][0]))
    P = sr.make_params(x[None, :], names, fix)
    row.update({k: float(v[0]) for k, v in P.items()})
    return row


def hms(t):
    if not np.isfinite(t):
        return ""
    return f"{int(t // 3600) % 24:02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wpt", action="append", default=[], help="NAME:MODE2 extra WPT configs")
    ap.add_argument("--only", action="append", default=[])
    a = ap.parse_args()
    for w in a.wpt:
        nm, m2 = w.split(":")
        CONFIGS[f"{nm}-{m2}"] = ("WPT", nm, m2, {})
    names = a.only or list(CONFIGS)
    jobs = list(itertools.product(names, TARGETS, (1, 2)))
    with mp.get_context("fork").Pool(10) as pool:
        rows = pool.map(solve, jobs, chunksize=1)
    df = pd.DataFrame(rows)
    f_all = OUT / "profile_likelihood_v2_allruns.csv"
    if f_all.exists():
        old = pd.read_csv(f_all)
        old = old[~old.config.isin(names)]
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(f_all, index=False)
    df["tkey"] = df.target_lat.fillna(0.0)
    best = df.sort_values("loglik", ascending=False).groupby(["config", "tkey"]).head(1)
    best = best.sort_values(["config", "tkey"]).drop(columns="tkey").reset_index(drop=True)
    # reference: best fit of the existing single-mode profile (outputs/satcom/profile_likelihood.csv)
    ref = pd.read_csv(OUT / "profile_likelihood.csv").loglik.max()
    best["delta_m2ll_vs_single_mode_best"] = -2 * (best.loglik - ref)
    best["t_fmt_utc"] = [hms(t) for t in best.t_fmt]
    best["t_sw2_utc"] = [hms(t) for t in best.t_sw2]
    best.round(4).to_csv(OUT / "profile_likelihood_v2.csv", index=False)
    cols = ["config", "target_lat", "end_lat", "loglik", "delta_m2ll_vs_single_mode_best", "bto_rms_us",
            "bfo_rms_hz", "bfo_res_1840", "mach", "fl", "t_fmt_utc", "t_sw2_utc"] + \
           [c for c in ("theta1", "theta2", "u2") if c in best]
    print(f"reference best single-mode loglik {ref:.3f}")
    print(best[cols].round(2).to_string())


if __name__ == "__main__":
    main()
