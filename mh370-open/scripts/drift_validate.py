"""Validate the drifter Markov chain (workstream B): 5-fold hold-out by drifter.
Writes outputs/drift/validation_*.csv and validation.json.
Run: .venv/bin/python -I scripts/drift_validate.py
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pandas as pd

from mh370 import drift_mc as mc
from mh370 import drift_validate as V
from mh370.drift_data import load_gdp

OUT = Path(__file__).resolve().parents[1] / "outputs" / "drift"
OUT.mkdir(parents=True, exist_ok=True)
K = 5
HORIZONS = [1, 6, 12, 24, 48]
T_GRID = np.arange(0, 1101, 10.0)
TARGETS = [75.0, 60.0]
SCALES = [1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35]


def main():
    g = load_gdp()
    ntraj = g["rowsize"].size
    fold = V.folds(ntraj, K)
    grid = mc.MCGrid()
    start_mask = V.arc_start_cells(grid)
    score_rows, transit = [], {lt: dict(km_t=[], km_e=[], chain={f: np.zeros(T_GRID.size) for f in SCALES}, n=0) for lt in TARGETS}
    for f in range(K):
        train = fold != f
        test = fold == f
        pairs = mc.transition_pairs(grid, 5.0, drogue=0, traj_keep=train)
        chains = {"miron3": mc.build_chain(pairs, grid, 5.0, "miron3"),
                  "annual": mc.build_chain(pairs, grid, 5.0, "annual")}
        starts = V.test_starts(grid, test, 5.0, HORIZONS)
        for name, ch in chains.items():
            res = V.predictive_scores(ch, starts)
            for n, r in res.items():
                score_rows.append(dict(fold=f, chain=name, horizon_steps=n, **r))
        ch = chains["miron3"]
        for lt in TARGETS:
            t, e, sc, st = V.drifter_transits(grid, test, start_mask, lt)
            transit[lt]["km_t"].append(t)
            transit[lt]["km_e"].append(e)
            for fsc in SCALES:
                chf = dataclasses.replace(ch, time_scale=fsc)
                transit[lt]["chain"][fsc] += V.chain_transit_cdf(chf, sc, st, lt, T_GRID) * sc.size
            transit[lt]["n"] += sc.size
        print("fold", f, "done", flush=True)
    sc = pd.DataFrame(score_rows)
    sc.to_csv(OUT / "validation_scores_by_fold.csv", index=False)
    agg = (sc.assign(w=sc.n_test)
             .groupby(["chain", "horizon_steps"])
             .apply(lambda d: pd.Series({
                 "days": d.days.iloc[0], "n_test": d.n_test.sum(),
                 "cover50": np.average(d.cover50, weights=d.w), "cover90": np.average(d.cover90, weights=d.w),
                 "logscore": np.average(d.logscore, weights=d.w),
                 "obs_dx_km": np.average(d.obs_dx_km, weights=d.w), "pred_dx_km": np.average(d.pred_dx_km, weights=d.w),
                 "obs_dy_km": np.average(d.obs_dy_km, weights=d.w), "pred_dy_km": np.average(d.pred_dy_km, weights=d.w)}),
                    include_groups=False)
             .reset_index())
    agg.to_csv(OUT / "validation_scores.csv", index=False, float_format="%.4f")
    print(agg.to_string(index=False))
    rows = []
    summ = {}
    # fit the transit-speed calibration factor (joint over both targets, t <= 900 d)
    Fkm = {}
    for lt in TARGETS:
        t = np.concatenate(transit[lt]["km_t"])
        e = np.concatenate(transit[lt]["km_e"])
        Fkm[lt] = V.kaplan_meier(t, e, T_GRID)[0]
    mt = T_GRID <= 900
    rmse = {f: float(np.sqrt(np.mean([np.mean((Fkm[lt][mt] - transit[lt]["chain"][f][mt] / transit[lt]["n"]) ** 2)
                                       for lt in TARGETS]))) for f in SCALES}
    fbest = min(rmse, key=rmse.get)
    summ["time_scale_rmse"] = rmse
    summ["time_scale_best"] = fbest
    for lt in TARGETS:
        t = np.concatenate(transit[lt]["km_t"])
        e = np.concatenate(transit[lt]["km_e"])
        F_km = Fkm[lt]
        F_ch = transit[lt]["chain"][1.0] / transit[lt]["n"]
        F_cal = transit[lt]["chain"][fbest] / transit[lt]["n"]
        for tg, a, b, c in zip(T_GRID, F_km, F_ch, F_cal):
            rows.append(dict(lon_target=lt, day=tg, F_drifters_KM=a, F_chain=b, F_chain_calibrated=c))
        def q(F, p):
            return float(np.interp(p, F, T_GRID)) if F.max() >= p else None
        summ[f"west_of_{int(lt)}E"] = dict(
            n_drifters=int(t.size), n_events=int(e.sum()),
            median_days_drifters=q(F_km, 0.5), median_days_chain=q(F_ch, 0.5),
            q25_days_drifters=q(F_km, 0.25), q25_days_chain=q(F_ch, 0.25),
            F365_drifters=float(np.interp(365, T_GRID, F_km)), F365_chain=float(np.interp(365, T_GRID, F_ch)),
            F508_drifters=float(np.interp(508, T_GRID, F_km)), F508_chain=float(np.interp(508, T_GRID, F_ch)),
            median_days_chain_calibrated=q(F_cal, 0.5), F508_chain_calibrated=float(np.interp(508, T_GRID, F_cal)))
    pd.DataFrame(rows).to_csv(OUT / "validation_transit.csv", index=False, float_format="%.4f")
    # mass budget with full chains
    budget = []
    for name, lee in (("undrogued", None), ("flaperon_leeway", "flaperon")):
        pairs = mc.transition_pairs(grid, 5.0, drogue=0, leeway=lee)
        ch = mc.build_chain(pairs, grid, 5.0, "miron3")
        for r in V.mass_budget(ch, [-25.0, -30.0, -35.0, -40.0]):
            budget.append(dict(chain=name, **r))
    pd.DataFrame(budget).to_csv(OUT / "validation_mass_budget.csv", index=False, float_format="%.4f")
    summ["mass_budget_max_abs_total_minus_1"] = float(np.max(np.abs(pd.DataFrame(budget).total - 1)))
    (OUT / "validation.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))
    print(pd.DataFrame(budget).to_string(index=False))


if __name__ == "__main__":
    main()
