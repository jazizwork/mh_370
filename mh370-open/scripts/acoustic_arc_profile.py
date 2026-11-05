"""Workstream D: outputs/acoustic/arc_profile.csv (values vs latitude along the 7th arc).

Columns per arc latitude (20-42 S, 0.5 deg; impact 00:19:30-00:25:00, c 1.47-1.49 km/s):
  lat, lon
  <SITE>_cov            fraction of the predicted T window recorded (IMOS duty cycle)
  <SITE>_path_max_elev  shallowest point on the source->receiver geodesic (m, ETOPO 2022,
                        ends excluded); > -1000 m means the SOFAR path is at least partly blocked
  <SITE>_pmin           min p-value of the two arrival-like statistics (5-40 Hz and 5-20 Hz,
                        8-s running median) in the recorded part of the window
  seis_min_p            smallest p over the open seismic stations' windows (fork, step 4),
                        seis_unexplained = windows with p<0.05 not explained by a known event
  loglik                0.0 everywhere: the open acoustic evidence is uninformative about the
                        impact latitude (see README "Why no likelihood layer"). 0 = no information,
                        not "not computed".
Run: .venv/bin/python -I scripts/acoustic_arc_profile.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"


def main():
    pr = pd.read_csv(OUT / "pred_arc_grid.csv")
    ta = pd.read_csv(OUT / "tests_arc_grid.csv")
    ta["lat"] = [float(t.split("_")[1]) for t in ta.test]
    sw = pd.read_csv(OUT / "seismic" / "arc_windows.csv")
    rows = []
    for _, r in pr.iterrows():
        o = dict(lat=r.lat, lon=r.lon)
        for s in A.IMOS_SITES:
            o[f"{s}_cov"] = round(r[f"{s}_cov"], 3)
            o[f"{s}_path_max_elev_m"] = round(r[f"{s}_maxelev_m"])
            t = ta[(np.isclose(ta.lat, r.lat)) & (ta.site == s)]
            o[f"{s}_pmin"] = float(np.nanmin([t.pm8.iloc[0], t.plf.iloc[0]])) if len(t) and np.isfinite(t.pm8.iloc[0]) else np.nan
        o["HA01_path_max_elev_m"] = round(r["HA01_maxelev_m"])
        s2 = sw[np.isclose(sw.arc_lat, r.lat)]
        o["seis_min_p"] = float(s2.p_null.min()) if len(s2) else np.nan
        o["seis_unexplained_p05"] = int(((s2.p_null < 0.05) & s2.explained_by.isna()).sum()) if len(s2) else 0
        o["imos_open_and_recorded"] = int(sum((r[f"{s}_cov"] > 0) and (r[f"{s}_maxelev_m"] < -1000)
                                              for s in A.IMOS_SITES))
        o["loglik"] = 0.0
        rows.append(o)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arc_profile.csv", index=False, float_format="%.4g")
    print(df.to_string())


if __name__ == "__main__":
    main()
