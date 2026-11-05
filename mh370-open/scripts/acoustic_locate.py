"""Workstream D: bearing + time-difference (HA01 published pick vs IMOS arrival) location.

For a source on the HA01 ray (bearing az +/- daz) at range r, the IMOS-minus-HA01 arrival
difference is TDOA(r) = (d_site(r) - r) / c. Given an observed IMOS arrival time, solve for r
(hyperbola/bearing intersection). Reported for c = 1.47/1.48/1.49 km/s, bearing +/- daz and an
arrival-time uncertainty (dt_obs). Also reports how sensitive r is to timing (dr/dTDOA).

Cases (observed IMOS times from outputs/acoustic/kimberley_picks.csv / tests):
  * Curtin 301.6 deg (HA01 01:34:40) with PAKIM arrivals: Curtin's 01:32:49, and our picks
  * Kadri 306.18 / Stead 246.9 with PAPCA: only if an arrival is detected; otherwise the
    curve shows where a PAPCA arrival would have had to be.

Outputs: outputs/acoustic/locate_tdoa.csv, fig_tdoa_curves.png, fig_curtin_location.png
Run: .venv/bin/python -I scripts/acoustic_locate.py
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"
R = np.arange(200.0, 8000.0, 10.0)


def tdoa_curve(site, az, c):
    la, lo = A.ray_points("HA01", az, R)
    d, _ = A.rdist_az(site, la, lo)
    return (np.asarray(d) - R) / c, la, lo


def solve(site, t_ha01, az, daz, t_obs, dt_obs):
    """Ranges r on the HA01 ray consistent with an IMOS arrival t_obs +/- dt_obs.
    Returns list of (az, c, r_lo, r_hi, r_best) over the bearing/speed grid."""
    out = []
    for a in (az - daz, az, az + daz):
        for c in (1.47, 1.48, 1.49):
            T, la, lo = tdoa_curve(site, a, c)
            obs = t_obs - t_ha01
            ok = np.abs(T - obs) <= dt_obs
            k = int(np.argmin(np.abs(T - obs)))
            rb = R[k] if abs(T[k] - obs) <= dt_obs else np.nan
            out.append(dict(az=a, c=c, r_lo=R[ok].min() if ok.any() else np.nan,
                            r_hi=R[ok].max() if ok.any() else np.nan, r_best=rb,
                            lat_best=float(la[k]) if np.isfinite(rb) else np.nan,
                            lon_best=float(lo[k]) if np.isfinite(rb) else np.nan,
                            origin_best=A.fmt(t_ha01 - rb / c) if np.isfinite(rb) else "",
                            tdoa_obs=obs, tdoa_min=T.min(), tdoa_max=T.max(),
                            dr_dtdoa_km_per_s=float(np.gradient(R, T)[k]) if np.isfinite(rb) else np.nan))
    return out


def main(picks=None):
    rows = []
    # Curtin event at PAKIM
    cur = A.HA01_CANDIDATES["Curtin301"]
    pk = picks if picks is not None else {}
    cases = [("Curtin 'Scott Reef' 01:32:49 (published)", "PAKIM", A.hms8(1, 32, 49), 5.0)]
    for lab, t in pk.items():
        if "masked" in lab:
            continue
        cases.append((lab, "PAKIM", t, 5.0))
    for lab, site, t, dt in cases:
        for r in solve(site, cur["t"], cur["az"], cur["daz"], t, dt):
            rows.append(dict(case=lab, site=site, t_obs=A.fmt(t), ha01=f"{A.fmt(cur['t'])} {cur['az']}", **r))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "locate_tdoa.csv", index=False, float_format="%.3f")
    with pd.option_context("display.width", 250):
        print(df.groupby("case")[["r_lo", "r_hi", "r_best", "lat_best", "lon_best", "tdoa_obs"]]
              .agg(["min", "max"]).round(1).to_string())

    # TDOA curves figure
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.8))
    for ax, key, site in ((axs[0], "Kadri306", "PAPCA"), (axs[1], "Stead247", "PAPCA"),
                          (axs[2], "Curtin301", "PAKIM")):
        c0 = A.HA01_CANDIDATES[key]
        for da, ls in ((-c0["daz"], ":"), (0, "-"), (c0["daz"], ":")):
            for c, col in ((1.47, "tab:blue"), (1.48, "k"), (1.49, "tab:red")):
                T, _, _ = tdoa_curve(site, c0["az"] + da, c)
                ax.plot(R, T, ls, color=col, lw=0.9,
                        label=f"c={c}" if da == 0 else None)
        Rx, _, _ = A.arc_crossing("HA01", c0["az"])
        if np.isfinite(Rx):
            ax.axvline(Rx, color="m", ls="--", lw=0.8, label="7th-arc crossing")
        ax.set_xlabel(f"range from HA01 along {c0['az']} deg (km)")
        ax.set_ylabel(f"{site} - HA01 arrival (s)")
        ax.set_title(f"{key}: HA01 {A.fmt(c0['t'])}", fontsize=9)
        ax.grid(alpha=0.3)
        if key == "Curtin301":
            ax.axhline(A.hms8(1, 32, 49) - c0["t"], color="g", label="Curtin 01:32:49")
            for lab, t in [(k, v) for k, v in pk.items() if "masked" not in k]:
                ax.axhline(t - c0["t"], color="orange", ls="-.", lw=0.9)
                ax.text(R[5], t - c0["t"] + 2, lab, fontsize=6)
            car = A.SOURCES["Carlsberg_Curtin"]
            dH, _ = A.rdist_az("HA01", car["lat"], car["lon"])
            ax.axvline(float(dH), color="c", ls="--", lw=0.8, label="Carlsberg (Curtin)")
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig_tdoa_curves.png", dpi=130)
    plt.close(fig)
    return df


if __name__ == "__main__":
    import sys
    import json
    picks = {}
    pf = OUT / "kimberley_picks.json"
    if pf.exists():
        picks = {k: A.parse_hms8(v) for k, v in json.loads(pf.read_text()).items()}
    main(picks)
