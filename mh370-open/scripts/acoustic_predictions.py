"""Workstream D step 2: predicted T-phase arrivals for candidate events and 7th-arc impacts.

Outputs (outputs/acoustic/):
  pred_ha01_picks.csv      every published HA01 pick (Kadri Table 1, Stead 246.9, Curtin 301.6):
                           arc crossing, implied origin, delta-t, predicted IMOS arrivals,
                           window coverage on 8 March, path blockage
  pred_arc_grid.csv        7th-arc points 20-42S (0.5 deg) x impact 00:19:30-00:25:00:
                           predicted arrival windows at PAPCA/PAKIM/PAPOR/HA01, IMOS coverage
  pred_sources.csv         located candidate sources (Java, Carlsberg, ...) -> receivers
  fig_map_candidates.png, fig_arc_timing.png, fig_blockage_profiles.png

Run: .venv/bin/python -I scripts/acoustic_predictions.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mh370 import acoustic as A
from mh370 import geo

OUT = A.ROOT / "outputs" / "acoustic"
OUT.mkdir(parents=True, exist_ok=True)
IMPACT = (geo.hms(24, 19, 30), geo.hms(24, 25, 0))
NIGHT = (A.hms8(0, 0) - 3 * 3600, A.hms8(3, 0))


def windows_8mar():
    return {s: [(a, b) for a, b, _ in A.recording_windows(s, *NIGHT, full=True)] for s in A.IMOS_SITES}


def coverage(t1, t2, wins):
    """Fraction of [t1, t2] inside recording windows, and the list of windows hit."""
    if t2 <= t1:
        t2 = t1 + 1e-6
    cov, hit = 0.0, []
    for a, b in wins:
        o = max(0.0, min(b, t2) - max(a, t1))
        if o > 0:
            cov += o
            hit.append(f"{A.fmt(a)}-{A.fmt(b)}")
    return cov / (t2 - t1), ";".join(hit)


def main():
    W = windows_8mar()
    rows = []
    picks = [(f"K{i+1:02d}_{az:.2f}", A.parse_hms8(t), az, 0.4, kdt, "Kadri2024 T1")
             for i, (t, az, kdt) in enumerate(A.KADRI_TABLE1)]
    picks += [("Stead247", A.HA01_CANDIDATES["Stead247"]["t"], 246.9, 2.0, np.nan, "Stead2014"),
              ("Curtin301.6", A.HA01_CANDIDATES["Curtin301"]["t"], 301.6, 0.75, np.nan, "ATSB/Curtin")]
    for name, t, az, daz, kdt, ref in picks:
        R, la, lo = A.arc_crossing("HA01", az)
        r = dict(pick=name, ref=ref, t_ha01=A.fmt(t), az=az, daz=daz, kadri_dt_min=kdt,
                 R_arc_km=R, arc_lat=la, arc_lon=lo)
        if np.isfinite(R):
            Rm, _, _ = A.arc_crossing("HA01", az - daz)
            Rp, _, _ = A.arc_crossing("HA01", az + daz)
            r["R_arc_range_km"] = f"{np.nanmin([Rm, Rp, R]):.0f}-{np.nanmax([Rm, Rp, R]):.0f}"
            for c in (1.47, 1.48, 1.49):
                r[f"origin_c{c}"] = A.fmt(t - R / c)
            r["dt_after_0019_29_min_c1.48"] = (t - R / 1.48 - geo.ARC7_TIME) / 60
            r["kadri_dt_check_c1.50_t2000"] = (t - R / 1.50 - A.hms8(0, 20, 0)) / 60
            # if the impact were on the arc at 00:19:30-00:25, HA01 arrival would be:
            r["ha01_if_impact_0019_30_to_0025"] = f"{A.fmt(IMPACT[0] + R / 1.49)}-{A.fmt(IMPACT[1] + R / 1.47)}"
            t0 = t - R / A.C_SOFAR
            for s in A.IMOS_SITES:
                d, _ = A.rdist_az(s, la, lo)
                # predicted window: source at arc crossing (origin from HA01 pick),
                # c 1.47-1.49 applied consistently to both legs
                tt = [t - R / c + d / c for c in (1.47, 1.49)]
                lo_t, hi_t = min(tt) - 10, max(tt) + 10
                cv, hit = coverage(lo_t, hi_t, W[s])
                r[f"{s}_pred"] = A.fmt(t0 + d / A.C_SOFAR)
                r[f"{s}_win"] = f"{A.fmt(lo_t)}-{A.fmt(hi_t)}"
                r[f"{s}_cov"] = round(cv, 2)
                b = A.blockage_summary(la, lo, s)
                r[f"{s}_maxelev_m"] = round(b["max_elev_m"])
                r[f"{s}_km_above1000"] = round(b["km_above_axis"])
            bh = A.blockage_summary(la, lo, "HA01", exclude_rcv_km=30)
            r["HA01_maxelev_m"] = round(bh["max_elev_m"])
            r["HA01_km_above1000"] = round(bh["km_above_axis"])
        rows.append(r)
    dfp = pd.DataFrame(rows)
    dfp.to_csv(OUT / "pred_ha01_picks.csv", index=False, float_format="%.3f")

    # ---------- TDOA along the bearing (source anywhere along the HA01 ray) ----------
    trows = []
    for key in ("Kadri306", "Stead247", "Kadri268"):
        c0 = A.HA01_CANDIDATES[key]
        for daz in (-c0["daz"], 0.0, c0["daz"]):
            for R in (500, 1000, 1500, 2000, 2500, 3000, 4000, 5000):
                la, lo = A.ray_points("HA01", c0["az"] + daz, np.array([R]))
                la, lo = float(la[0]), float(lo[0])
                for s in A.IMOS_SITES:
                    d, _ = A.rdist_az(s, la, lo)
                    trows.append(dict(cand=key, az=c0["az"] + daz, R_km=R, site=s, d_km=float(d),
                                      tdoa_s=(float(d) - R) / A.C_SOFAR,
                                      t_pred=A.fmt(c0["t"] + (float(d) - R) / A.C_SOFAR)))
    pd.DataFrame(trows).to_csv(OUT / "pred_tdoa_along_bearing.csv", index=False, float_format="%.2f")

    # ---------- 7th arc grid ----------
    lats, lons = A.arc7_points(-42.0, -20.0, 0.5)
    arows = []
    for la, lo in zip(lats, lons):
        r = dict(lat=la, lon=lo)
        for s in ("PAPCA", "PAKIM", "PAPOR", "HA01"):
            d, az = A.rdist_az(s, la, lo)
            d = float(d)
            lo_t = IMPACT[0] + d / C_HI - 10
            hi_t = IMPACT[1] + d / C_LO + 10
            r[f"{s}_d_km"] = d
            r[f"{s}_baz"] = float(A.dist_az(A.RECEIVERS[s]["lat"], A.RECEIVERS[s]["lon"], la, lo)[1])
            r[f"{s}_t_lo"] = lo_t
            r[f"{s}_t_hi"] = hi_t
            r[f"{s}_win"] = f"{A.fmt(lo_t)}-{A.fmt(hi_t)}"
            if s in A.IMOS_SITES:
                cv, hit = coverage(lo_t, hi_t, W[s])
                r[f"{s}_cov"] = cv
                r[f"{s}_hit"] = hit
            b = A.blockage_summary(la, lo, s, exclude_rcv_km=30 if s == "HA01" else 60)
            r[f"{s}_maxelev_m"] = b["max_elev_m"]
            r[f"{s}_km_above1000"] = b["km_above_axis"]
            r[f"{s}_km_above500"] = b["km_above_500"]
            r[f"{s}_block_at"] = f"{b['at_lat']:.1f},{b['at_lon']:.1f}"
        arows.append(r)
    dfa = pd.DataFrame(arows)
    dfa.to_csv(OUT / "pred_arc_grid.csv", index=False, float_format="%.3f")

    # ---------- located sources ----------
    srows = []
    for key, s0 in {**A.SOURCES, **{k: dict(lat=v["lat"], lon=v["lon"], t0=v["t0"], ref="USGS/ISC")
                                    for k, v in A.CAL_EVENTS.items()}}.items():
        for s in ("PAPCA", "PAKIM", "PAPOR", "HA01", "HA08S"):
            d, _ = A.rdist_az(s, s0["lat"], s0["lon"])
            d = float(d)
            b = A.blockage_summary(s0["lat"], s0["lon"], s, exclude_rcv_km=30 if s.startswith("HA") else 60)
            r = dict(source=key, lat=s0["lat"], lon=s0["lon"], site=s, d_km=d,
                     max_elev_m=b["max_elev_m"], block_at=f"{b['at_lat']:.2f},{b['at_lon']:.2f}",
                     km_above1000=b["km_above_axis"], km_land=b["km_land"])
            if s0["t0"] is not None:
                r["t_pred_c1.48"] = A.fmt(s0["t0"] + d / 1.48)
                r["t_pred_range"] = f"{A.fmt(s0['t0'] + d / 1.50)}-{A.fmt(s0['t0'] + d / 1.46)}"
            srows.append(r)
    # Carlsberg: origin implied by HA01 01:34:40
    car = A.SOURCES["Carlsberg_Curtin"]
    dH, _ = A.rdist_az("HA01", car["lat"], car["lon"])
    for c in (1.47, 1.48, 1.49):
        t0 = A.HA01_CANDIDATES["Curtin301"]["t"] - float(dH) / c
        for s in ("PAPCA", "PAKIM", "PAPOR"):
            d, _ = A.rdist_az(s, car["lat"], car["lon"])
            srows.append(dict(source=f"Carlsberg_from_HA01_c{c}", lat=car["lat"], lon=car["lon"], site=s,
                              d_km=float(d), **{"t_pred_c1.48": A.fmt(t0 + float(d) / c)},
                              origin=A.fmt(t0)))
    dfs = pd.DataFrame(srows)
    dfs.to_csv(OUT / "pred_sources.csv", index=False, float_format="%.2f")

    figures(dfp, dfa, W)
    print(dfp[["pick", "t_ha01", "az", "R_arc_km", "arc_lat", "arc_lon", "origin_c1.48",
               "dt_after_0019_29_min_c1.48", "kadri_dt_min", "PAPCA_pred", "PAPCA_cov",
               "PAKIM_pred", "PAKIM_cov", "PAPOR_pred", "PAPOR_cov"]].to_string())
    print(dfa[["lat", "lon", "PAPCA_win", "PAPCA_cov", "PAKIM_win", "PAKIM_cov", "PAPOR_win",
               "PAPOR_cov", "PAPCA_maxelev_m", "PAKIM_maxelev_m", "PAPOR_maxelev_m",
               "HA01_maxelev_m"]].to_string())
    print(dfs.to_string())


C_LO, C_HI = A.C_SENS


def figures(dfp, dfa, W):
    import xarray as xr
    ds = xr.open_dataset(A.BATHY, engine="h5netcdf")
    sub = ds.z.sel(lat=slice(-50, 8), lon=slice(60, 145))[::3, ::3]
    fig, ax = plt.subplots(figsize=(11, 7.5))
    ax.contourf(sub.lon, sub.lat, sub, levels=[-7000, -4000, -3000, -2000, -1000, -500, 0],
                colors=["#08306b", "#2171b5", "#4292c6", "#9ecae1", "#c6dbef", "#deebf7"], extend="neither")
    ax.contourf(sub.lon, sub.lat, sub, levels=[0, 9000], colors=["#d9d9d9"])
    ax.contour(sub.lon, sub.lat, sub, levels=[-1000], colors="k", linewidths=0.3)
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-44, -5, 0.25))
    ax.plot(arc[:, 1], arc[:, 0], "r-", lw=2, label="7th arc (sea level)")
    for s, r in A.RECEIVERS.items():
        ax.plot(r["lon"], r["lat"], "k^", ms=8)
        ax.annotate(s, (r["lon"], r["lat"]), xytext=(4, 4), textcoords="offset points", fontsize=8)
    for key, col in (("Kadri306", "m"), ("Stead247", "orange"), ("Kadri268", "y"), ("Curtin301", "c")):
        c0 = A.HA01_CANDIDATES[key]
        rr = np.linspace(0, 6500, 300)
        la, lo = A.ray_points("HA01", c0["az"], rr)
        ax.plot(lo, la, "--", color=col, lw=1.2, label=f"HA01 {c0['az']:.1f}° ({key})")
        R, a, b = A.arc_crossing("HA01", c0["az"])
        ax.plot(b, a, "o", color=col, mec="k")
    for key, s0 in A.SOURCES.items():
        ax.plot(s0["lon"], s0["lat"], "*", ms=12, mec="k", label=key)
    ax.set_xlim(60, 145)
    ax.set_ylim(-50, 8)
    ax.set_aspect(1 / np.cos(np.radians(22)))
    ax.legend(fontsize=7, loc="lower right")
    ax.set_title("Receivers, HA01 published bearings, candidate sources; shading = ETOPO 2022 depth "
                 "(contour = 1000 m)", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig_map_candidates.png", dpi=130)
    plt.close(fig)

    # timing diagram: predicted windows vs recording windows
    fig, axs = plt.subplots(1, 3, figsize=(14, 7), sharey=True)
    for ax, s in zip(axs, A.IMOS_SITES):
        for a, b in W[s]:
            ax.axvspan((a - A.hms8(0)) / 60, (b - A.hms8(0)) / 60, color="0.85")
        for _, r in dfa.iterrows():
            ax.plot([(r[f"{s}_t_lo"] - A.hms8(0)) / 60, (r[f"{s}_t_hi"] - A.hms8(0)) / 60],
                    [r["lat"], r["lat"]], "-", color="tab:blue" if r[f"{s}_cov"] > 0 else "tab:red", lw=3)
        ax.set_xlim(10, 90)
        ax.set_xlabel("minutes after 2014-03-08 00:00 UTC")
        ax.set_title(f"{s}: predicted T arrival (impact 00:19:30-00:25, c 1.47-1.49)\n"
                     "grey = recording windows; blue = overlaps, red = missed", fontsize=8)
    axs[0].set_ylabel("7th-arc latitude")
    fig.tight_layout()
    fig.savefig(OUT / "fig_arc_timing.png", dpi=130)
    plt.close(fig)

    # blockage profiles for key paths
    paths = [("Kadri306 crossing", -25.73, 101.37), ("Stead247 crossing", -40.97, 81.57),
             ("arc 35S", -35.0, geo.arc_lon_for_lat(-35.0, geo.ARC7_BTO_US, geo.ARC7_TIME)),
             ("Carlsberg", 2.11, 69.31), ("Java 01:15", -8.36, 107.92)]
    fig, axs = plt.subplots(len(paths), 1, figsize=(10, 2.1 * len(paths)))
    for ax, (nm, la, lo) in zip(axs, paths):
        for s, col in (("PAPCA", "k"), ("PAKIM", "tab:green"), ("PAPOR", "tab:purple"), ("HA01", "tab:red")):
            r = A.RECEIVERS[s]
            sd, _, _, z = A.path_profile(la, lo, r["lat"], r["lon"])
            ax.plot(sd, z, color=col, lw=0.8, label=s)
        ax.axhline(-1000, color="b", ls=":", lw=0.8)
        ax.set_ylim(-7000, 500)
        ax.set_ylabel("elev m")
        ax.set_title(f"source: {nm} ({la:.2f}, {lo:.2f}) -> receivers (dotted: ~SOFAR axis 1000 m)", fontsize=8)
        ax.legend(fontsize=6, ncol=4, loc="lower left")
    axs[-1].set_xlabel("distance from source along geodesic (km)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_blockage_profiles.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
