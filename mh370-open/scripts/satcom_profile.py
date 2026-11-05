"""Profile likelihood of the 7th-arc latitude for each autopilot mode.

For each mode and target latitude L, maximise  log L(BTO,BFO) + log prior(radar point)
subject to the 00:19:29 position being at latitude L (quadratic penalty, sd 0.03 deg), with
scipy's differential evolution (vectorised over the population).  Shows how much worse the best
achievable fit becomes away from the posterior peak, e.g. at the UGIB 2020 LEP (34.23 S).

Output: outputs/satcom/profile_likelihood.csv, outputs/satcom/fig_profile_likelihood.png
Run   : .venv/bin/python -I scripts/satcom_profile.py
"""
import itertools
import multiprocessing as mp
import pathlib

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

from mh370 import geo
from mh370 import satcom_paths as sp

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "satcom"
TARGETS = [-40.0, -39.0, -38.0, -37.0, -36.0, -35.0, -34.2342, -33.0, -32.0, -31.0, -30.0, -29.0, -28.0]
REFINE_TARGETS = [-38.0, -37.0, -36.0, -35.0, -34.2342, -33.0, -32.0, -30.0]
CONFIGS = [(m, False) for m in sp.MODES] + [("LNAV", True), ("CTT", True)]

_cache = {}


def _setup(mode, drift):
    key = (mode, drift)
    if key not in _cache:
        meas = sp.build_measurements()
        model = sp.PathModel(mode, meas)
        lik = sp.Likelihood(meas)
        la, lo = sp.RADAR_POS
        s = sp.RADAR_SIGMA_NM / 60
        so = s / np.cos(np.radians(la))
        bounds = [(la - 3 * s, la + 3 * s), (lo - 3 * so, lo + 3 * so), (270, 340), (350, 520),
                  (sp.T_RADAR + 30, geo.hms(19, 40)), (140, 230), (0.70, 0.86), (300, 400)]
        names = list(sp.PathModel.PARAMS)
        if drift:
            bounds.append((-0.012, 0.004)); names.append("dmach")
        iend = int(np.argmin(np.abs(model.t_meas - geo.ARC7_TIME)))
        _cache[key] = (model, lik, bounds, names, iend, (la, lo, s, so))
    return _cache[key]


def solve(args):
    mode, drift, target, seed = args[:4]
    early = len(args) > 4 and args[4]
    model, lik, bounds, names, iend, (la, lo, s, so) = _setup(mode, drift)
    if early:   # refinement: FMT restricted to before the end of the 18:40 call
        bounds = list(bounds)
        bounds[4] = (sp.T_RADAR + 30, geo.hms(18, 40, 30))

    def f(X):
        X = np.atleast_2d(X.T if X.ndim == 2 else X[None, :])
        P = {k: X[:, i] for i, k in enumerate(names)}
        o = model.run(P)
        ll = lik(o, model.t_meas)
        lpr = -0.5 * (((X[:, 0] - la) / s) ** 2 + ((X[:, 1] - lo) / so) ** 2)
        pen = 0.5 * ((o["lat"][:, iend] - target) / 0.03) ** 2
        v = -(ll + lpr) + pen
        return np.where(np.isfinite(v), v, 1e9)

    r = differential_evolution(f, bounds, popsize=16 if early else 14, maxiter=500 if early else 400,
                               tol=1e-8, seed=seed,
                               vectorized=True, updating="deferred", polish=False, mutation=(0.5, 1.0),
                               recombination=0.9)
    x = r.x
    P = {k: np.array([x[i]]) for i, k in enumerate(names)}
    o = model.run(P)
    ll, parts = lik(o, model.t_meas, return_parts=True)
    row = dict(mode=mode, mach_drift=drift, target_lat=target, seed=seed, fmt_restricted=bool(early),
               end_lat=float(o["lat"][0, iend]), end_lon=float(o["lon"][0, iend]),
               loglik=float(ll[0]), bto_rms_us=float(np.sqrt(np.mean(parts["bto_res"][0] ** 2))),
               bfo_rms_hz=float(np.sqrt(np.mean(parts["bfo_res"][0] ** 2))),
               bfo_max_abs_hz=float(np.max(np.abs(parts["bfo_res"][0]))),
               bias_hz=float(parts["bias"][0]))
    row.update({k: float(x[i]) for i, k in enumerate(names)})
    return row


def main():
    import sys
    jobs = []
    prev = []
    if "--refine-only" in sys.argv and (OUT / "profile_likelihood_pass1.csv").exists():
        prev = [pd.read_csv(OUT / "profile_likelihood_pass1.csv")]
    else:
        jobs += [(m, d, t, s) for (m, d), t, s in itertools.product(CONFIGS, TARGETS, (1, 2))]
    # refinement pass: FMT restricted to before the end of the 18:40 call (where unrestricted DE
    # sometimes converged to a late-FMT local optimum), 2 more seeds, larger population
    jobs += [(m, d, t, s, True) for (m, d), t, s in
             itertools.product(CONFIGS, REFINE_TARGETS, (11, 12))]
    with mp.get_context("fork").Pool(10) as pool:
        rows = pool.map(solve, jobs, chunksize=1)
    df = pd.concat(prev + [pd.DataFrame(rows)], ignore_index=True)
    df.to_csv(OUT / "profile_likelihood_allruns.csv", index=False)
    # keep the best of all seeds / both passes
    df = df.sort_values("loglik", ascending=False).groupby(["mode", "mach_drift", "target_lat"]).head(1)
    df = df.sort_values(["mach_drift", "mode", "target_lat"]).reset_index(drop=True)
    best = df.loglik.max()
    df["delta_m2ll_vs_best"] = -2 * (df.loglik - best)
    df["t_fmt_utc"] = [f"{int(t//3600)}:{int(t%3600//60):02d}:{int(t%60):02d}" for t in df.t_fmt]
    df.round(4).to_csv(OUT / "profile_likelihood.csv", index=False)
    print(df[["mode", "mach_drift", "target_lat", "loglik", "delta_m2ll_vs_best", "bto_rms_us",
              "bfo_rms_hz", "mach", "fl", "theta", "t_fmt_utc"] +
             (["dmach"] if "dmach" in df else [])].round(3).to_string())
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    col = {"LNAV": "#2a78d6", "CTT": "#eb6834", "CMT": "#1baf7a", "CTH": "#eda100", "CMH": "#e87ba4"}
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    for (m, d), g in df.groupby(["mode", "mach_drift"]):
        g = g.sort_values("target_lat")
        ax.plot(g.target_lat, g.delta_m2ll_vs_best, color=col[m], lw=1.6, ls="--" if d else "-",
                marker="o", ms=3, label=f"{m}{' + Mach drift' if d else ''}")
    ax.axvline(-34.2342, color="#8a8984", lw=0.8, ls="--")
    ax.text(-34.15, 1, "UGIB LEP", fontsize=7, color="#52514e")
    ax.set_ylim(0, 60)
    ax.set_xlabel("imposed 7th-arc latitude at 00:19:29 (deg)", fontsize=8, color="#52514e")
    ax.set_ylabel("-2 delta log-likelihood vs best overall fit", fontsize=8, color="#52514e")
    ax.legend(fontsize=7, frameon=False, ncol=2)
    for sname in ("top", "right"):
        ax.spines[sname].set_visible(False)
    ax.grid(color="#e4e3df", lw=0.6)
    ax.tick_params(labelsize=8, colors="#52514e")
    fig.tight_layout()
    fig.savefig(OUT / "fig_profile_likelihood.png", dpi=150)


if __name__ == "__main__":
    main()
