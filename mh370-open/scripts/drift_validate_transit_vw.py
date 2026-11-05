"""Robustness check of the transit-speed calibration (workstream B): same 5-fold hold-out as
drift_validate.py, but with VOLUME-weighted starts (a start every 30 days while a held-out
undrogued drifter is within 300 km of the arc, 20-40S) instead of one first-entry start per
drifter (flux-weighted). Writes outputs/drift/validation_transit_volume_weighted.csv/.json.
Run: .venv/bin/python -I scripts/drift_validate_transit_vw.py
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
K = 5
T_GRID = np.arange(0, 1101, 10.0)
TARGETS = [75.0, 60.0]
SCALES = [1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3]


def main():
    g = load_gdp()
    fold = V.folds(g["rowsize"].size, K)
    grid = mc.MCGrid()
    start_mask = V.arc_start_cells(grid)
    acc = {lt: dict(t=[], e=[], F={f: np.zeros(T_GRID.size) for f in SCALES}, n=0) for lt in TARGETS}
    for f in range(K):
        pairs = mc.transition_pairs(grid, 5.0, drogue=0, traj_keep=fold != f)
        ch = mc.build_chain(pairs, grid, 5.0, "miron3")
        for lt in TARGETS:
            t, e, sc, st = V.drifter_transits(grid, fold == f, start_mask, lt, every_days=30.0)
            acc[lt]["t"].append(t)
            acc[lt]["e"].append(e)
            acc[lt]["n"] += sc.size
            for s in SCALES:
                acc[lt]["F"][s] += V.chain_transit_cdf(dataclasses.replace(ch, time_scale=s), sc, st, lt, T_GRID) * sc.size
        print("fold", f, flush=True)
    mt = T_GRID <= 900
    Fkm = {lt: V.kaplan_meier(np.concatenate(acc[lt]["t"]), np.concatenate(acc[lt]["e"]), T_GRID)[0] for lt in TARGETS}
    rmse = {s: float(np.sqrt(np.mean([np.mean((Fkm[lt][mt] - acc[lt]["F"][s][mt] / acc[lt]["n"]) ** 2) for lt in TARGETS])))
            for s in SCALES}
    per_target = {lt: min(SCALES, key=lambda s: np.mean((Fkm[lt][mt] - acc[lt]["F"][s][mt] / acc[lt]["n"]) ** 2))
                  for lt in TARGETS}
    rows = []
    for lt in TARGETS:
        for i, d in enumerate(T_GRID):
            rows.append(dict(lon_target=lt, day=d, F_drifters_KM=Fkm[lt][i],
                             **{f"F_chain_x{s:.2f}": acc[lt]["F"][s][i] / acc[lt]["n"] for s in SCALES}))
    pd.DataFrame(rows).to_csv(OUT / "validation_transit_volume_weighted.csv", index=False, float_format="%.4f")
    out = dict(n_starts={str(lt): acc[lt]["n"] for lt in TARGETS},
               n_events={str(lt): int(np.concatenate(acc[lt]["e"]).sum()) for lt in TARGETS},
               rmse=rmse, best=min(rmse, key=rmse.get), best_per_target={str(k): v for k, v in per_target.items()})
    (OUT / "validation_transit_volume_weighted.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
