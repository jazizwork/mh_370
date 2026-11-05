"""Workstream D: received-level upper limits for undetected arrivals in key predicted windows.

For a window [t1, t2] at an IMOS site, an arrival would have been 'detected' (p < 0.05) if its
arrival-like level (8-s running median of 2-s band levels) in some 5-20 Hz band exceeded
  UL_band = (file median band level) + (95th percentile of the control-night Slf statistic
            for windows of the same width at that site).
We report UL (dB re 1 uPa and Pa RMS) for 8-16 Hz and 10-20 Hz, and the observed maximum.
For comparison we list the absolute received levels of the catalogued earthquakes detected
by the same statistic (outputs/acoustic/imos_calibration_events.csv).

Outputs: outputs/acoustic/upper_limits.csv, calibration_received_levels.csv
Run: .venv/bin/python -I scripts/acoustic_upper_limits.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"


def pa(db):
    return 10 ** (np.asarray(db) / 20.0) / 1e6


def ctrl_feats(site):
    return [A.file_features(p, site) for d in A.CONTROL_DAYS for p in A.night_files(site, d)]


def main():
    tc = pd.read_csv(OUT / "tests_candidates.csv")
    ta = pd.read_csv(OUT / "tests_arc_grid.csv")
    keys = ["Kadri_00:54:30_306.18|arc", "Kadri_00:54:30_306.18|ray", "Stead_246.9|arc", "Stead_246.9|ray",
            "Kadri_00:40:34_303.28|arc", "Kadri_00:39:02_268.24|ray", "Java_0115|T", "Carlsberg|T"]
    sel = pd.concat([tc[tc.test.isin(keys) & (tc.coverage > 0)],
                     ta[ta.coverage > 0]], ignore_index=True)
    ctrl = {s: ctrl_feats(s) for s in A.IMOS_SITES}
    nulls = {}
    rows = []
    for _, r in sel.iterrows():
        a, b = A.parse_hms8(r.t1), A.parse_hms8(r.t2)
        files = [A.file_features(p, r.site) for tn, p in A.list_files(r.site, a - 400, b + 400)]
        files = [f for f in files if f["t"][-1] >= a and f["t"][0] <= b and A.MAIN_DAY == A.dt_of(f["t"][0] + 3 * 3600).date()]
        if not files:
            continue
        w = int(max(10, round(min(r.covered_s, 290) / 10) * 10))
        key = (r.site, w)
        if key not in nulls:
            nulls[key] = np.percentile(A.null_window_stats(ctrl[r.site], w, bands=A.LF_BANDS, smooth_s=-8.0,
                                                           step_s=5.0), 95)
        o = dict(test=r.test, site=r.site, t1=r.t1, t2=r.t2, coverage=r.coverage, null95_db=nulls[key])
        for band in ("8-16", "10-20"):
            med = np.median(np.concatenate([f[f"L_{band}"] for f in files]))
            ul = med + nulls[key]
            o[f"median_{band}_db"] = med
            o[f"UL_{band}_db"] = ul
            o[f"UL_{band}_Pa"] = float(pa(ul))
        rows.append(o)
    ul = pd.DataFrame(rows)
    ul.to_csv(OUT / "upper_limits.csv", index=False, float_format="%.4g")
    with pd.option_context("display.width", 220):
        print(ul[~ul.test.str.startswith("arc_")].to_string())
        g = ul[ul.test.str.startswith("arc_")].groupby("site")[["UL_8-16_Pa", "UL_10-20_Pa"]].describe()
        print(g.T.to_string())

    # absolute received level of detected calibration T phases
    ce = pd.read_csv(OUT / "imos_calibration_events.csv")
    ce = ce[(ce.phase == "T") & ((ce.p_lf < 0.01) | (ce.p_sm8 < 0.01))].copy()
    out = []
    for _, r in ce.iterrows():
        p = [pp for tn, pp in A.list_files(r.site) if pp.stem == r.file]
        if not p:
            continue
        f = A.file_features(p[0], r.site)
        band = r.band_lf if isinstance(r.band_lf, str) else "8-16"
        med = float(np.median(f[f"L_{band}"]))
        out.append(dict(site=r.site, time=r.time, mag=r.mag, d_km=r.d_km, place=r.place, band=band,
                        median_db=med, excess_db=r.stat_lf, received_db=med + r.stat_lf,
                        received_Pa=float(pa(med + r.stat_lf)), open_path=r.open_path))
    cl = pd.DataFrame(out)
    cl.to_csv(OUT / "calibration_received_levels.csv", index=False, float_format="%.4g")
    print(cl.to_string())


if __name__ == "__main__":
    main()
