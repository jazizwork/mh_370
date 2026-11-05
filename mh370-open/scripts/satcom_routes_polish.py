"""Local polish (Nelder-Mead) of the best SMC particles of selected route components.

Used for the "best fit" of the UGIB-like configuration (BEDAX -> LNAV 180 T, constant Mach/FL),
where differential evolution (scripts/satcom_routes_profile.py) stalled in a worse local optimum
(late FMT, 18:40 BFO off by 40 Hz) than the best SMC particle (pre-FMT track ~335 T, FMT ~18:40).
Objective = log L + log prior(radar point), as in the profile scripts; bounds = prior bounds.

Output: outputs/satcom/bestfit_polished_v2.csv
Run   : .venv/bin/python -I scripts/satcom_routes_polish.py
"""
import json
import pathlib

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from mh370 import geo
from mh370 import satcom_paths as sp
from mh370 import satcom_routes as sr

ROOT = pathlib.Path(__file__).resolve().parents[1]
R = ROOT / "data" / "derived" / "satcom_smc" / "routes"
OUT = ROOT / "outputs" / "satcom"
BOUNDS = {"trk_pre": (270, 340), "gs_pre": (350, 520), "t_fmt": (sp.T_RADAR + 30, geo.hms(19, 40)),
          "theta1": (140, 230), "theta2": (140, 230), "u2": (0, 1), "mach": (0.70, 0.86), "fl": (300, 400)}
JOBS = [  # label, file glob, family, wpt, mode2
    ("UGIB-like BEDAX -> LNAV 180 T (constant Mach/FL)", "baseline_WPT_BEDAX_LNAV_ugib180_n20000_s*.npz", "WPT", "BEDAX", "LNAV"),
]


def hms(t):
    return f"{int(t // 3600) % 24:02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d}" if np.isfinite(t) else ""


def main():
    meas = sp.build_measurements()
    lik = sp.Likelihood(meas)
    atm = sp.Atmos()
    la0, lo0 = sp.RADAR_POS
    s = sp.RADAR_SIGMA_NM / 60
    so = s / np.cos(np.radians(la0))
    rows = []
    for label, pat, fam, wpt, m2 in JOBS:
        files = sorted(R.glob(pat))
        if not files:
            continue
        zs = [np.load(f) for f in files]
        names = list(zs[0]["names"])
        fixed = json.loads(str(zs[0]["fixed"]))
        free = [k for k in names if k not in fixed]
        model = sr.RouteModel(fam, meas, mode2=m2, wpt=wpt, atm=atm)
        iend = int(np.argmin(np.abs(model.t_meas - geo.ARC7_TIME)))

        def P_of(v):
            P = {k: np.array([v[i]]) for i, k in enumerate(free)}
            for k, val in fixed.items():
                P[k] = np.array([val])
            return P

        def f(v):
            for i, k in enumerate(free):
                if k in BOUNDS and not (BOUNDS[k][0] <= v[i] <= BOUNDS[k][1]):
                    return 1e9
            o = model.run(P_of(v))
            ll = lik(o, model.t_meas)[0]
            lpr = -0.5 * (((v[0] - la0) / s) ** 2 + ((v[1] - lo0) / so) ** 2)
            return -(ll + lpr) if np.isfinite(ll) else 1e9

        # start from the 5 best particles over all replicates
        X = np.concatenate([z["x"] for z in zs])
        LL = np.concatenate([z["ll"] for z in zs])
        best = None
        for i in np.argsort(-LL)[:2]:
            v0 = X[i, [names.index(k) for k in free]]
            r = minimize(f, v0, method="Nelder-Mead", options=dict(maxiter=1500, xatol=1e-3, fatol=1e-3))
            if best is None or r.fun < best.fun:
                best = r
        o = model.run(P_of(best.x))
        ll, parts = lik(o, model.t_meas, return_parts=True)
        bl = list(lik.bfo.label)
        from importlib.util import spec_from_file_location, module_from_spec
        spec = spec_from_file_location("spost", ROOT / "scripts" / "satcom_posterior.py")
        SP = module_from_spec(spec); spec.loader.exec_module(SP)
        alat = float(SP.arc_project(o["lat"][:, iend], o["lon"][:, iend])[0][0])
        row = dict(config=label, files=" ".join(f.name for f in files), smc_best_loglik=round(float(LL.max()), 3),
                   polished_loglik=round(float(ll[0]), 3),
                   bto_rms_us=round(float(np.sqrt(np.mean(parts["bto_res"][0] ** 2))), 1),
                   bfo_rms_hz=round(float(np.sqrt(np.mean(parts["bfo_res"][0] ** 2))), 1),
                   bfo_res_1828=round(float(parts["bfo_res"][0][bl.index("R1200 18:28:15")]), 1),
                   bfo_res_1840=round(float(parts["bfo_res"][0][bl.index("C 18:40 mean")]), 1),
                   bto_res=" ".join(f"{v:+.0f}" for v in parts["bto_res"][0]),
                   bfo_res=" ".join(f"{v:+.1f}" for v in parts["bfo_res"][0]),
                   end_lat=round(float(o["lat"][0, iend]), 3), end_lon=round(float(o["lon"][0, iend]), 3),
                   arc_lat_0019=round(alat, 3), t_fmt=hms(P_of(best.x)["t_fmt"][0]), t_wpt=hms(o["t_sw2"][0]))
        row.update({k: round(float(P_of(best.x)[k][0]), 4) for k in names})
        rows.append(row)
        print(row, flush=True)
    pd.DataFrame(rows).to_csv(OUT / "bestfit_polished_v2.csv", index=False)


if __name__ == "__main__":
    main()
