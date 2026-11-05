"""Figures for workstream B (drift). Run after drift_build.py and drift_validate.py.
Run: .venv/bin/python -I scripts/drift_figures.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import pandas as pd
import xarray as xr

from mh370 import drift_debris as dd
from mh370 import drift_mc as mc
from mh370 import geo
from mh370.drift_data import land_geometry

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "drift"

# Reference categorical palette (fixed order) and neutral inks
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8984", "#e4e3df"
SURF = "#fcfcfb"
BLUES = LinearSegmentedColormap.from_list(
    "blues", ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "font.size": 9, "axes.titlesize": 10, "axes.titlecolor": INK,
    "legend.frameon": False, "lines.linewidth": 2.0,
})

PUBLISHED = [  # (label, lat, kind)
    ("CSIRO 2017: 35.6S", -35.6, "south"),
    ("Ulich & Iannello 2023: 34.0S", -34.0, "south"),
    ("Godfrey 2021: 34.1S", -34.13, "south"),
    ("Miron 2019 (Bayes): ~31S", -31.0, "north"),
    ("Miron 2019 (paths): ~25S", -25.0, "north"),
]
NESTEROV = (-30.5, -25.5)


def draw_land(ax, **kw):
    g = land_geometry()
    geoms = getattr(g, "geoms", [g])
    for p in geoms:
        if p.geom_type != "Polygon":
            continue
        x, y = p.exterior.xy
        ax.fill(x, y, color=kw.get("color", "#d9d7d0"), lw=0, zorder=kw.get("zorder", 3))


def published_marks(ax):
    """Published estimates as thin grey rules with short rotated labels inside the axes."""
    ax.axvspan(*NESTEROV, color=GRID, alpha=0.6, lw=0, zorder=0)
    ax.text(np.mean(NESTEROV), 0.02, "Nesterov 2018", ha="center", va="bottom", fontsize=7,
            color=INK2, transform=ax.get_xaxis_transform(), zorder=6)
    labels = {"CSIRO 2017: 35.6S": "CSIRO 35.6", "Ulich & Iannello 2023: 34.0S": "U&I 34.0 / Godfrey 34.1",
              "Miron 2019 (Bayes): ~31S": "Miron ~31", "Miron 2019 (paths): ~25S": "Miron ~25"}
    for lab, la, kind in PUBLISHED:
        ax.axvline(la, color=MUTED, lw=0.8, ls="--" if kind == "south" else ":", zorder=1)
        if lab in labels:
            ax.text(la + 0.15, 0.97, labels[lab], rotation=90, ha="left", va="top", fontsize=7,
                    color=INK2, transform=ax.get_xaxis_transform(), zorder=6,
                    bbox=dict(boxstyle="square,pad=0.1", fc=SURF, ec="none", alpha=0.8))


def rel(v):
    v = np.asarray(v, float)
    return np.exp(v - np.nanmax(v))


def fig_profiles():
    p = pd.read_csv(OUT / "arc_profile.csv")
    m = (p.arc_lat >= -44) & (p.arc_lat <= -16)
    p = p[m]
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    ax = axs[0]
    series = [("loglik", "Default: undrogued drifters, speed-calibrated (all items + WA)", C[0]),
              ("loglik_leeway", "CSIRO-like: flaperon leeway, others undrogued", C[1]),
              ("loglik_all_leeway", "All items with flaperon leeway", C[2]),
              ("loglik_uncalibrated", "Default without speed calibration", C[3])]
    for k, lab, col in series:
        ax.plot(p.arc_lat, rel(p[k]), color=col, label=lab)
    ax.set_title("All debris items: relative likelihood along the 7th arc", loc="left")
    ax.set_xlabel("7th-arc latitude (deg; marginalised across +/-100 km)")
    ax.set_ylabel("likelihood / max")
    published_marks(ax)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.22), fontsize=8, ncol=1)
    ax = axs[1]
    series = [("loglik_flaperon_only", "Undrogued-drifter chain (speed-calibrated)", C[0]),
              ("loglik_flaperon_only_leeway", "+0.10 m/s, 20 deg left of wind (CSIRO)", C[1]),
              ("loglik_flaperon_only_leeway10", "+0.10 m/s, 10 deg left of wind", C[2]),
              ("loglik_flaperon_only_uncalibrated", "Undrogued, no speed calibration", C[3])]
    for k, lab, col in series:
        ax.plot(p.arc_lat, rel(p[k]), color=col, label=lab)
    ax.set_title("Reunion flaperon only", loc="left")
    ax.set_xlabel("7th-arc latitude (deg)")
    published_marks(ax)
    ax.legend(loc="upper left", bbox_to_anchor=(0.0, -0.22), fontsize=8)
    for a in axs:
        a.set_xlim(-42.5, -16)
        a.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(OUT / "fig_arc_profiles.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_sensitivity():
    p = pd.read_csv(OUT / "arc_profile.csv")
    s = pd.read_csv(OUT / "profile_summary.csv")
    s = s[(s.w == 1.0) & ~s.variant.str.startswith("item:")].copy()
    order = s.sort_values("mean").variant.tolist()
    fig, ax = plt.subplots(figsize=(8, 7))
    y = np.arange(len(order))
    for i, v in enumerate(order):
        r = s[s.variant == v].iloc[0]
        col = (C[3] if "drogued" in v else C[1] if ("leeway" in v or "windage" in v)
               else C[2] if ("uncalibrated" in v or v in ("loglik_annual", "loglik_bin05", "loglik_T7")) else C[0])
        ax.plot([r.q025, r.q975], [i, i], color=col, lw=1, alpha=0.6)
        ax.plot([r.q16, r.q84], [i, i], color=col, lw=4, solid_capstyle="round")
        ax.plot(r.peak, i, "o", ms=6, color=SURF, mec=col, mew=2, zorder=5)
    ax.set_yticks(y)
    ax.set_yticklabels(order, fontsize=8)
    ax.set_xlabel("7th-arc latitude (deg)   [thick: 68%, thin: 95% interval; circle: peak; w=1, uniform prior 42-20S]")
    ax.axvspan(*NESTEROV, color=GRID, alpha=0.6, lw=0, zorder=0)
    for lab, la, kind in PUBLISHED:
        ax.axvline(la, color=MUTED, lw=0.8, ls="--" if kind == "south" else ":", zorder=0)
    ax.set_xlim(-42, -20)
    ax.set_title("Sensitivity (blue: default chain; orange: added leeway; aqua: uncalibrated chain structure; yellow: drogued)",
                 loc="left", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig_sensitivity.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_items():
    p = pd.read_csv(OUT / "arc_profile_items.csv")
    keys = [it.key for it in dd.ITEMS]
    n = len(keys) + 1
    fig, axs = plt.subplots(4, 4, figsize=(12, 10), sharex=True)
    for ax, k in zip(axs.ravel(), keys + ["wa_term"]):
        a, b = p[k], p[f"{k}__leeway"]
        mx = np.nanmax(np.r_[a, b])
        ax.plot(p.arc_lat, a - mx, color=C[0], lw=1.6, label="undrogued")
        ax.plot(p.arc_lat, b - mx, color=C[1], lw=1.6, label="+ flaperon leeway")
        if k == "wa_term":
            ax.set_title("WA non-detection term (lambda=20)", loc="left", fontsize=8)
        else:
            it = dd.ITEM_BY_KEY[k]
            ax.set_title(f"{it.region}: {it.date}\n{it.name[:38]}", loc="left", fontsize=8)
        ax.set_xlim(-42.5, -16)
        ax.axvline(-35.6, color=MUTED, lw=0.6, ls="--")
        ax.axvline(-25.0, color=MUTED, lw=0.6, ls=":")
    axs[0, 0].legend(fontsize=7, loc="lower left")
    for ax in axs[-1]:
        ax.set_xlabel("arc latitude")
    for ax in axs[:, 0]:
        ax.set_ylabel("log-lik (nats, rel.)")
    fig.suptitle("Per-item log-likelihood along the 7th arc (each panel relative to its own max; dashed 35.6S, dotted 25S)",
                 x=0.01, ha="left", fontsize=10, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "fig_items.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_maps():
    ds = xr.open_dataset(ROOT / "data" / "derived" / "drift_loglik.nc", engine="h5netcdf")
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
    fig, axs = plt.subplots(1, 3, figsize=(13, 5.2), sharey=True)
    for ax, k, t in zip(axs, ["loglik", "loglik_leeway", "loglik_all_leeway"],
                        ["Default (undrogued)", "CSIRO-like (flaperon leeway)", "All items with flaperon leeway"]):
        v = ds[k].values
        v = v - np.nanmax(v)
        im = ax.pcolormesh(ds.lon, ds.lat, v, cmap=BLUES, vmin=-15, vmax=0, shading="nearest", rasterized=True)
        ax.plot(arc[:, 1], arc[:, 0], color=INK, lw=1.0)
        ax.set_xlim(78, 112)
        ax.set_ylim(-44, -16)
        ax.set_aspect(1 / np.cos(np.radians(30)))
        ax.set_title(t, loc="left")
        ax.set_xlabel("lon")
    axs[0].set_ylabel("lat")
    cb = fig.colorbar(im, ax=axs, shrink=0.8, pad=0.01)
    cb.set_label("log-likelihood relative to max (nats)")
    fig.savefig(OUT / "fig_maps.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_forward():
    grid = mc.MCGrid()
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
    chains = {}
    for name, lee in (("undrogued drifters", None), ("+ flaperon leeway", "flaperon")):
        import dataclasses, json
        pairs = mc.transition_pairs(grid, 5.0, drogue=0, leeway=lee)
        f = json.loads((OUT / "validation.json").read_text()).get("time_scale_best", 1.2)
        chains[name] = dataclasses.replace(mc.build_chain(pairs, grid, 5.0, "miron3"), time_scale=f)
    day = dd.ITEM_BY_KEY["flaperon"].days
    fig, axs = plt.subplots(2, 3, figsize=(14, 6.6), sharex=True, sharey=True)
    for i, (name, ch) in enumerate(chains.items()):
        for j, alat in enumerate([-25.0, -30.0, -35.0]):
            ax = axs[i, j]
            alon = np.interp(alat, arc[:, 0], arc[:, 1])
            p0 = np.zeros((grid.nstate, 1))
            p0[grid.cell(alat, alon), 0] = 1
            n = int(round(day / ch.step_days))
            h = mc.forward(ch, p0, n, dd.RELEASE_TIME)[-1, :, 0]
            dens = (h[:grid.nc] + h[grid.nc:2 * grid.nc]).reshape(grid.nlat, grid.nlon)
            im = ax.pcolormesh(grid.lon_edges, grid.lat_edges, np.log10(np.maximum(dens, 1e-6)),
                               cmap=BLUES, vmin=-5, vmax=-1.5, rasterized=True)
            draw_land(ax)
            ax.plot(arc[:, 1], arc[:, 0], color=INK, lw=0.8, zorder=4)
            ax.plot(alon, alat, "o", ms=8, color=SURF, mec=C[1], mew=2, zorder=6)
            for it in dd.ITEMS:
                ax.plot(it.lon, it.lat, "o", ms=4, color=C[7] if it.key == "flaperon" else INK2, zorder=6)
            wsum = h[:2 * grid.nc].reshape(2, grid.nlat, grid.nlon).sum(0)[:, :int((70 - 20) / grid.d)].sum()
            ax.set_title(f"{name}: release {abs(alat):.0f}S, day {day:.0f}\nmass west of 70E: {wsum:.2f}",
                         loc="left", fontsize=8)
            ax.set_xlim(20, 120)
            ax.set_ylim(-50, 5)
            ax.set_aspect(1.0)
    cb = fig.colorbar(im, ax=axs, shrink=0.8, pad=0.01)
    cb.set_label("log10 probability per 1-deg cell (afloat + beached)")
    fig.suptitle("Forward Markov-chain distribution (speed-calibrated) on 29 Jul 2015 (flaperon find, red dot) for releases on the 7th arc",
                 x=0.01, ha="left", fontsize=10, color=INK)
    fig.savefig(OUT / "fig_forward_day508.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_validation():
    tr = pd.read_csv(OUT / "validation_transit.csv")
    sc = pd.read_csv(OUT / "validation_scores.csv")
    fig, axs = plt.subplots(1, 3, figsize=(14, 4))
    ax = axs[0]
    for i, lt in enumerate(sorted(tr.lon_target.unique(), reverse=True)):
        d = tr[tr.lon_target == lt]
        ax.plot(d.day, d.F_drifters_KM, color=C[i], lw=2, label=f"held-out drifters (KM), west of {lt:.0f}E")
        ax.plot(d.day, d.F_chain, color=C[i], lw=2, ls="--", label=f"chain (raw), west of {lt:.0f}E")
        if "F_chain_calibrated" in d:
            ax.plot(d.day, d.F_chain_calibrated, color=C[i], lw=1.4, ls=":",
                    label=f"chain (speed-calibrated), west of {lt:.0f}E")
    ax.axvline(508, color=MUTED, lw=0.8, ls=":")
    ax.text(508, 0.02, " flaperon\n find", fontsize=7, color=INK2)
    ax.set_xlabel("days after first undrogued fix within 300 km of the arc (20-40S)")
    ax.set_ylabel("cumulative fraction")
    ax.set_title("Transit time: 5-fold hold-out", loc="left")
    ax.legend(fontsize=7, loc="upper left")
    ax = axs[1]
    for i, ch in enumerate(["miron3", "annual"]):
        d = sc[sc.chain == ch]
        ax.plot(d.days, d.cover50, "o-", color=C[i], ms=5, lw=1.6, label=f"{ch}: 50% set")
        ax.plot(d.days, d.cover90, "s--", color=C[i], ms=5, lw=1.6, label=f"{ch}: 90% set")
    ax.axhline(0.5, color=MUTED, lw=0.8)
    ax.axhline(0.9, color=MUTED, lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("forecast horizon (days)")
    ax.set_ylabel("fraction of held-out positions inside")
    ax.set_title("Calibration of predictive HPD sets", loc="left")
    ax.legend(fontsize=7)
    ax = axs[2]
    d = sc[sc.chain == "miron3"]
    ax.plot(d.days, d.obs_dx_km, "o-", color=C[0], ms=5, lw=1.6, label="observed mean zonal displacement")
    ax.plot(d.days, d.pred_dx_km, "o--", color=C[1], ms=5, lw=1.6, label="chain mean zonal displacement")
    ax.plot(d.days, d.obs_dy_km, "s-", color=C[2], ms=5, lw=1.6, label="observed mean meridional")
    ax.plot(d.days, d.pred_dy_km, "s--", color=C[3], ms=5, lw=1.6, label="chain mean meridional")
    ax.set_xlabel("forecast horizon (days)")
    ax.set_ylabel("km (east/north positive)")
    ax.set_title("Mean displacement, held-out starts 18-42S, 70-110E", loc="left")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(OUT / "fig_validation.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_hindcast():
    h = pd.read_csv(OUT / "hindcast_flaperon.csv")
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.2))
    ax = axs[0]
    for k, lab, col in (("visit_window_generic", "HYCOM 2014-15 + 1.2% wind (generic)", C[0]),
                        ("visit_window_flaperon", "HYCOM 2014-15 + flaperon leeway", C[1])):
        n = h[k.replace("visit_window", "n_visit")]
        p = h[k]
        err = np.sqrt(np.maximum(p * (1 - p), 1e-12) / h.n)
        ax.errorbar(h.release_lat, p * 100, yerr=err * 100, color=col, lw=1.8, capsize=2, label=lab)
    ax.set_xlabel("release latitude on the 7th arc")
    ax.set_ylabel("% of particles within 150 km of Reunion\nduring 29 Jun - 29 Jul 2015")
    ax.set_title("Hindcast (HYCOM reanalysis) flaperon likelihood", loc="left")
    ax.legend(fontsize=7)
    ax = axs[1]
    p = pd.read_csv(OUT / "arc_profile.csv")
    for k, lab, col in (("loglik_flaperon_only", "Markov chain, undrogued (speed-cal.)", C[0]),
                        ("loglik_flaperon_only_leeway", "Markov chain, flaperon leeway (speed-cal.)", C[1]),
                        ("loglik_flaperon_only_uncalibrated", "Markov chain, undrogued, uncalibrated", C[2]),
                        ("loglik_flaperon_only_leeway_uncalibrated", "Markov chain, leeway, uncalibrated", C[3])):
        if k in p:
            ax.plot(p.arc_lat, rel(p[k]), color=col, label=lab)
    for k, col in (("visit_window_generic", C[0]), ("visit_window_flaperon", C[1])):
        ax.plot(h.release_lat, h[k] / h[k].max(), "o", ms=5, color=SURF, mec=col, mew=1.6)
    ax.set_xlabel("7th-arc latitude")
    ax.set_ylabel("likelihood / max")
    ax.set_title("Flaperon: climatological chain (lines) vs 2014-15 hindcast (circles)", loc="left")
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(0.0, -0.15), ncol=2)
    ax = axs[2]
    pit = pd.read_csv(OUT / "arc_profile_items.csv")
    ax.plot(h.release_lat, h.strand_WA_generic * 100, "o-", color=C[0], ms=4, lw=1.6,
            label="hindcast: stranded on WA coast <= 18 months (generic)")
    ax.plot(h.release_lat, h.strand_WA_flaperon * 100, "o-", color=C[1], ms=4, lw=1.6,
            label="hindcast: stranded on WA (flaperon leeway)")
    ax.plot(pit.arc_lat, pit.p_wa * 100, color=C[0], lw=1.4, ls="--",
            label="chain: P(reach WA coastal band) <= 18 months")
    ax.set_xlabel("7th-arc latitude")
    ax.set_ylabel("%")
    ax.set_title("Western Australia: negative-evidence ingredient", loc="left")
    ax.legend(fontsize=7)
    for a in axs:
        a.set_xlim(-42.5, -19.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_hindcast_flaperon.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def fig_density():
    grid = mc.MCGrid()
    pairs = mc.transition_pairs(grid, 5.0, drogue=0)
    cnt = np.bincount(pairs.start, minlength=grid.nc)[:grid.nc].reshape(grid.nlat, grid.nlon)
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.pcolormesh(grid.lon_edges, grid.lat_edges, np.log10(np.maximum(cnt, 0.5)), cmap=BLUES,
                       vmin=0, vmax=4, rasterized=True)
    draw_land(ax)
    ax.plot(arc[:, 1], arc[:, 0], color=INK, lw=1)
    for it in dd.ITEMS:
        ax.plot(it.lon, it.lat, "o", ms=4, color=C[7], zorder=6)
    ax.set_xlim(20, 120)
    ax.set_ylim(-50, 10)
    ax.set_aspect(1.0)
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("log10 (# undrogued 5-day transition pairs starting in cell)")
    ax.set_title("GDP undrogued-drifter data density (1 deg), 7th arc, debris find sites", loc="left")
    fig.savefig(OUT / "fig_data_density.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import sys
    which = sys.argv[1:] or ["profiles", "sensitivity", "items", "maps", "forward", "validation", "density"]
    for w in which:
        globals()[f"fig_{w}"]()
        print("done", w, flush=True)
