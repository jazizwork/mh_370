"""Figures for the search-coverage layer (run after scripts/search_build.py).

  outputs/search/fig_search_coverage.png   overview + hotspot zoom, campaign polygons, 7th arc,
                                           published candidate points
  outputs/search/fig_search_pod.png        cell POD best / low / high
  outputs/search/fig_arc_profile.png       searched cross-arc width vs latitude
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import xarray as xr  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mh370 import geo, search  # noqa: E402

OUT = ROOT / "outputs" / "search"


def main():
    items = search.build_items()
    oi25 = {p["name"]: p for p in json.load(open(search.F_OI25))["polygons"]}
    remaining = search._poly_from_parts(oi25["OI2025_26_remaining_unsearched_NW_strip_slide"]["rings"])
    contract = search._poly_from_parts(oi25["OI_contract_area_best__slide_digitised"]["rings"])
    cand = search.candidate_points()
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-44.0, -5.0, 0.05))

    # ------------------------------------------------------------------ coverage figure
    fig, axes = plt.subplots(1, 2, figsize=(15, 8.2), gridspec_kw=dict(width_ratios=[1.05, 1]))
    for k, ax in enumerate(axes):
        ext = (78, 112, -44, -6) if k == 0 else (91.3, 95.6, -36.9, -33.0)
        search.basemap(ax, ext)
        for camp in search.CAMPAIGNS:
            u = search.campaign_union(items, camp, "best")
            search.fill_geom(ax, u, search.CAMPAIGN_COLOR[camp], alpha=0.35, lw=0.8)
        # uncertain sub-areas hatched
        for it in items:
            if it.pod_class in ("OI2018_north_inferred", "OI2025_pre_contract_SW", "OI2025_post_contract",
                                "OI2018_site4_remainder"):
                search.fill_geom(ax, it.geom, "none", alpha=1.0, lw=0.0, hatch="////",
                                   edge=search.CAMPAIGN_COLOR[it.campaign])
            if it.is_gap and k == 1:
                search.fill_geom(ax, it.geom, "#d03b3b", alpha=0.9, lw=0.6)
        if k == 1:
            search.fill_geom(ax, remaining, "none", alpha=1.0, lw=1.4, edge="#0b0b0b", ls="--")
            ax.annotate("OI contract area not yet\nsearched (NW strip, ~7,400 km2,\ndigitised from OI slide)",
                        xy=(92.55, -34.35), xytext=(91.45, -33.35), fontsize=8.5, color="#0b0b0b",
                        arrowprops=dict(arrowstyle="-", color="#52514e", lw=0.8))
        ax.plot(arc[:, 1], arc[:, 0], color="#0b0b0b", lw=1.4, zorder=5)
        if k == 0:
            ax.plot(104.03, -21.09, "o", ms=5, mfc="#52514e", mec="#52514e", zorder=7)
            ax.add_patch(plt.Rectangle((78, -44), 34, 28, fill=False, ec="#52514e", lw=0.8, ls=":", zorder=4))
            ax.text(78.3, -16.6, "common grid", fontsize=8, color="#52514e")
            ax.add_patch(plt.Rectangle((91.3, -36.9), 4.3, 3.9, fill=False, ec="#0b0b0b", lw=0.9, zorder=6))
            ax.text(104.6, -21.0, "Bluefin-21 2014 area", fontsize=8, color="#0b0b0b", ha="left", va="center",
                    transform=ax.transData, zorder=7)
        for i, (lab, la, lo, note) in enumerate(cand):
            x0, x1, y0, y1 = ext
            if not (x0 <= lo <= x1 and y0 <= la <= y1):
                continue
            m = search.CAND_MARKERS[i % len(search.CAND_MARKERS)]
            ax.plot(lo, la, m, ms=8 if k == 0 else 10, mfc="white", mec="#0b0b0b", mew=1.4, zorder=8)
            short = lab.split(" (")[0]
            dx, dy = search.CAND_OFFSETS[k].get(i, (0.4, 0.2))
            ax.annotate(short, (lo, la), xytext=(lo + dx, la + dy), fontsize=8.5 if k == 0 else 9,
                        color="#0b0b0b", zorder=9,
                        arrowprops=dict(arrowstyle="-", color="#52514e", lw=0.6) if abs(dx) + abs(dy) > 0.6 else None)
        ax.set_title(["Seafloor already searched for MH370 (reconstruction)",
                      "Zoom: UGIB hotspot area (gaps in red)"][k], fontsize=11, loc="left")
    handles = [Patch(fc=search.CAMPAIGN_COLOR[c], alpha=0.5, ec=search.CAMPAIGN_COLOR[c],
                     label=search.CAMPAIGN_LABEL[c]) for c in search.CAMPAIGNS]
    handles += [Patch(fc="none", ec="#52514e", hatch="////", label="inferred / assumed footprint"),
                Patch(fc="#d03b3b", label="documented gap (ATSB d=0)"),
                Line2D([], [], color="#0b0b0b", lw=1.4, label="7th arc, sea level (geo.py)")]
    axes[0].legend(handles=handles, loc="upper left", fontsize=8.5, frameon=True, framealpha=0.9)
    fig.text(0.01, 0.01, "Polygons: ATSB = Geoscience Australia machine-readable sonar coverage; OI 2018 = digitised "
             "Malaysian weekly maps (+ inferred final sweep to ~25S);\nOI 2025-26 = ASSUMED from AIS tracks + official "
             "7,571 km2 tally. Candidate points are published claims, not results of this project.",
             fontsize=7.8, color="#52514e")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "fig_search_coverage.png", dpi=150)
    plt.close(fig)

    # ------------------------------------------------------------------ POD figure
    ds = xr.open_dataset(ROOT / "data" / "derived" / "search_pod.nc", engine="h5netcdf")
    cmap = search.seq_cmap()
    fig, axes = plt.subplots(1, 3, figsize=(16, 6.2), sharey=True)
    ext = (84, 104, -41, -20)
    for ax, var, ttl in zip(axes, ["pod_low", "pod", "pod_high"], ["pessimistic (pod_low)", "best (pod)", "optimistic (pod_high)"]):
        search.basemap(ax, ext)
        a = ds[var].where(ds[var] > 0)
        im = ax.pcolormesh(ds.lon, ds.lat, a, cmap=cmap, vmin=0, vmax=1, shading="nearest", zorder=2)
        ax.plot(arc[:, 1], arc[:, 0], color="#0b0b0b", lw=0.8, zorder=5)
        A = search.grid.cell_area_km2().values
        ax.set_title(f"POD {ttl}\nPOD-weighted area {float((ds[var].values*A).sum()):,.0f} km2", fontsize=10.5, loc="left")
    cb = fig.colorbar(im, ax=axes, shrink=0.8, pad=0.01)
    cb.set_label("probability of detection if the wreck were in the cell")
    fig.savefig(OUT / "fig_search_pod.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------------------------ arc profile
    pr = pd.read_csv(OUT / "arc_profile.csv")
    pr = pr[(pr.lat >= -41.5) & (pr.lat <= -19.5)]
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.fill_between(pr.lat, pr.eff_width_low_km, pr.eff_width_high_km, color="#86b6ef", alpha=0.6, lw=0,
                    label="POD-weighted width, low-high bound")
    ax.plot(pr.lat, pr.searched_width_km, color="#0b0b0b", lw=2, label="searched width (any campaign)")
    ax.plot(pr.lat, pr.eff_width_km, color="#2a78d6", lw=2, label="POD-weighted width (best)")
    ax.axhline(2 * 25 * 1.852, color="#52514e", lw=0.8, ls=":")
    ax.text(-41.4, 2 * 25 * 1.852 + 3, "+/-25 NM", fontsize=8, color="#52514e")
    ax.set_xlabel("latitude of the sea-level 7th arc (deg)")
    ax.set_ylabel("cross-arc width (km)")
    ax.set_xlim(-41.5, -19.5)
    ax.grid(axis="y", color="#e6e5e1", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper right", fontsize=8.5, frameon=False)
    ax.set_title("Searched cross-arc width vs latitude (transects perpendicular to the arc, +/-250 km)",
                 fontsize=10.5, loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "fig_arc_profile.png", dpi=140)
    plt.close(fig)
    print("figures written to", OUT)


if __name__ == "__main__":
    main()
