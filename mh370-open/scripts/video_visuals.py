"""Render the stills for the YouTube explainer (video/script.md) as 1920x1080 PNGs.

Every number drawn comes from the project's outputs (outputs/*, data/derived/*), the shared
geometry (src/mh370/geo.py, satcom_paths.py), the reports/research notes named in video/visuals.md,
or video/script.md itself. The on-screen source line of each visual names public sources only; the
file-level provenance is in video/visuals.md. Schematic visuals are badged "ILLUSTRATION".
Results visuals (V20-V23, V26, thumbnail) use the model-misspecification mixture at its recommended
default (satellite p_v2, broad_arc, eps = 0.1, drift w = 0.5, POD best; outputs/combine/RESULTS_mix.md).

Outputs: video/visuals/<ID>.png, video/thumbnail.png (1280x720), video/visuals.md
Run:     .venv/bin/python -I scripts/video_visuals.py            # all visuals
         .venv/bin/python -I scripts/video_visuals.py V04 V21    # selected IDs (prefix match)

Visual system (validated with the dataviz skill's validator against the navy surface #0e1a2b):
  categorical slots (dark steps) blue #3987e5, orange #d95926, aqua #199e70, yellow #c98500,
  violet #9085e9; campaigns use slots 1-3 (pass all-pairs CVD/normal-vision checks).
"""
from __future__ import annotations

import csv
import gzip
import json
import math
import sys
from functools import lru_cache
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import colors as mcolors
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

from mh370 import geo

ROOT = Path(__file__).resolve().parents[1]
VID = ROOT / "video"
OUTV = VID / "visuals"
DATA = VID / "data"
OUTV.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)
WORK = ROOT.parent  # /Users/.../MH370 (reports/, research_notes/)

# ----------------------------------------------------------------------------- style
W, H, DPI = 1920, 1080, 100
BG = "#0e1a2b"          # navy chart surface
PANEL = "#13243a"       # card panel
LAND = "#273242"
COAST = "#46536a"
GRID = "#1c2d45"
INK = "#f0efec"
INK2 = "#c3c2b7"
MUTED = "#8d95a3"
BLUE, ORANGE, AQUA, YELLOW, VIOLET = "#3987e5", "#d95926", "#199e70", "#c98500", "#9085e9"
ARC = INK               # the 7th arc is always the white line
ARC_DIM = "#6f7f96"
AREA = "#ff7eb6"        # areas 1-3 accent (outline + number badge)
CAMP = {"ATSB_2014_17": (BLUE, "ATSB-led 2014–17"),
        "OI_2018": (ORANGE, "Ocean Infinity 2018"),
        "OI_2025_26": (AQUA, "Ocean Infinity 2025–26 (reconstructed)"),
        "Bluefin21_2014": (MUTED, "Bluefin-21 2014")}
FONT = "Helvetica Neue"
plt.rcParams.update({"font.family": [FONT, "Arial Unicode MS", "DejaVu Sans"], "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.edgecolor": GRID,
                     "svg.fonttype": "none"})
HALO = [pe.withStroke(linewidth=5, foreground=BG)]


def pt(px):
    """font size in points for a size given in pixels (dpi 100)."""
    return px * 72.0 / DPI


def fx(x):
    return x / W


def fy(y):
    return 1 - y / H


def new_fig(w=W, h=H):
    fig = plt.figure(figsize=(w / DPI, h / DPI), dpi=DPI, facecolor=BG)
    return fig


def title(fig, text, sub=None, x=80, y=58, size=50, w=W, h=H, box=False):
    kw = dict(color=INK, fontsize=pt(size), fontweight="bold", va="top", ha="left")
    if box:
        kw["bbox"] = dict(boxstyle="round,pad=0.35", fc=BG, ec="none", alpha=0.82)
    fig.text(x / w, 1 - y / h, text, **kw)
    if sub:
        kw2 = dict(color=INK2, fontsize=pt(30), va="top", ha="left")
        if box:
            kw2["bbox"] = dict(boxstyle="round,pad=0.3", fc=BG, ec="none", alpha=0.82)
        fig.text(x / w, 1 - (y + size * 1.32) / h, sub, **kw2)


def source(fig, text):
    """small source line at the very bottom (below the caption-safe zone)."""
    fig.text(fx(64), fy(1046), "Source: " + text, color=MUTED, fontsize=pt(17), va="bottom", ha="left",
             zorder=30, bbox=dict(boxstyle="square,pad=0.25", fc=BG, ec="none", alpha=0.75))


def badge(fig, text="ILLUSTRATION", x=1840, y=58):
    fig.text(x / W, 1 - y / H, text, color=BG, fontsize=pt(22), fontweight="bold", va="top", ha="right",
             bbox=dict(boxstyle="round,pad=0.4", fc=YELLOW, ec="none"))


def save(fig, name, path=None):
    p = path or (OUTV / f"{name}.png")
    fig.savefig(p, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("wrote", p.relative_to(ROOT))


def style_chart(ax, grid_axis="y"):
    ax.set_facecolor(BG)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#3a4a63")
        ax.spines[s].set_linewidth(1.2)
    ax.tick_params(colors=INK2, labelsize=pt(26), length=0, pad=10)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, lw=1.2, zorder=0)
    ax.set_axisbelow(True)


def chart_ax(fig, x=150, y=230, w=1650, h=640):
    return fig.add_axes([fx(x), fy(y + h), w / W, h / H])


def fmt_ll(lat, lon, nd=2):
    return f"{abs(lat):.{nd}f}°{'S' if lat < 0 else 'N'} {lon:.{nd}f}°E"


def utc_to_myt(h, m=0, s=0):
    """'HH:MM' Malaysian time for a UTC clock time."""
    t = (h * 3600 + m * 60 + s + 8 * 3600) % 86400
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}"


# ----------------------------------------------------------------------------- map helpers
@lru_cache(None)
def land_polys():
    import shapefile  # pyshp
    out = []
    for sub in ("ne_10m_land", "ne_10m_minor_islands"):
        d = ROOT / "data/raw/naturalearth" / sub
        shp = next(d.glob("*.shp"))
        for s in shapefile.Reader(str(shp)).shapes():
            pts = np.asarray(s.points)
            parts = list(s.parts) + [len(pts)]
            for i in range(len(parts) - 1):
                seg = pts[parts[i]:parts[i + 1]]
                if len(seg) > 2:
                    out.append((seg, seg[:, 0].min(), seg[:, 0].max(), seg[:, 1].min(), seg[:, 1].max()))
    return out


def map_ax(fig, box, lat0, lat1, lon_c=None, lon0=None, lon1=None):
    """Axes in pixel box (x, y_top, w, h); lon range from lat range and the box aspect
    (equirectangular with cos(mid-lat) scaling)."""
    x, y, w, h = box
    ax = fig.add_axes([fx(x), fy(y + h), w / W, h / H])
    k = 1 / np.cos(np.radians((lat0 + lat1) / 2))
    if lon0 is None:
        half = (lat1 - lat0) * (w / h) * k / 2
        lon0, lon1 = lon_c - half, lon_c + half
    else:  # fit lat range to lon range
        mid = (lat0 + lat1) / 2
        half = (lon1 - lon0) / k * (h / w) / 2
        lat0, lat1 = mid - half, mid + half
    ax.set_xlim(lon0, lon1)
    ax.set_ylim(lat0, lat1)
    ax.set_facecolor(BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax._ext = (lon0, lon1, lat0, lat1)
    return ax


def draw_land(ax, z=2, fc=LAND, ec=COAST, lw=0.9):
    lon0, lon1, lat0, lat1 = ax._ext
    sel = [p for p, a, b, c, d in land_polys() if b >= lon0 - 1 and a <= lon1 + 1 and d >= lat0 - 1 and c <= lat1 + 1]
    ax.add_collection(PolyCollection(sel, facecolors=fc, edgecolors=ec, linewidths=lw, zorder=z))


def graticule(ax, dlat=5, dlon=5, labels=True, lab_lat_x=None, lab_lon_y=None, size=20):
    lon0, lon1, lat0, lat1 = ax._ext
    for la in np.arange(np.ceil(lat0 / dlat) * dlat, lat1, dlat):
        ax.axhline(la, color=GRID, lw=1.0, zorder=1)
        if labels:
            ax.text(lab_lat_x if lab_lat_x is not None else lon1 - 0.01 * (lon1 - lon0), la,
                    f"{abs(la):.0f}°{'S' if la < 0 else ('N' if la > 0 else '')}", color=MUTED, fontsize=pt(size),
                    ha="right", va="bottom", zorder=9, path_effects=HALO)
    for lo in np.arange(np.ceil(lon0 / dlon) * dlon, lon1, dlon):
        ax.axvline(lo, color=GRID, lw=1.0, zorder=1)
        if labels:
            ax.text(lo, lab_lon_y if lab_lon_y is not None else lat1 - 0.012 * (lat1 - lat0), f" {lo:.0f}°E",
                    color=MUTED, fontsize=pt(size), ha="left", va="top", zorder=9, path_effects=HALO)


@lru_cache(None)
def arc7(lat_min=-44.0, lat_max=-7.9):
    return geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(lat_min, lat_max, 0.05))


def draw_arc7(ax, lw=3.0, z=8, label=None, label_lat=None, color=ARC, size=26, dx=0.4, ha="left"):
    a = arc7()
    ax.plot(a[:, 1], a[:, 0], color=color, lw=lw, zorder=z, solid_capstyle="round")
    if label and label_lat is not None:
        lo = float(geo.arc_lon_for_lat(label_lat, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0))
        ax.text(lo + dx, label_lat, label, color=INK, fontsize=pt(size), fontweight="bold", ha=ha,
                va="center", zorder=z + 1, path_effects=HALO)


def arc_lon(lat):
    return float(geo.arc_lon_for_lat(lat, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0))


def point(ax, lon, lat, label=None, color=INK, s=140, marker="o", dx=0.3, dy=0.0, ha="left", va="center",
          size=26, z=12, weight="normal", ring=True, lcolor=INK):
    ax.scatter([lon], [lat], s=s, c=color, marker=marker, edgecolors=BG if ring else "none",
               linewidths=2.0, zorder=z)
    if label:
        ax.text(lon + dx, lat + dy, label, color=lcolor, fontsize=pt(size), ha=ha, va=va, zorder=z + 1,
                fontweight=weight, path_effects=HALO)


def legend_box(fig, items, x, y, size=24, title_txt=None, w=None):
    """items: list of (kind, color, label); kind in line/patch/dot/dash/outline. Pixel position = top-left."""
    yy = y
    if title_txt:
        fig.text(fx(x), fy(yy), title_txt, color=INK2, fontsize=pt(size), fontweight="bold", va="top")
        yy += size * 1.6
    for kind, col, lab in items:
        cy = yy + size * 0.62
        if kind == "line":
            fig.add_artist(plt.Line2D([fx(x), fx(x + 44)], [fy(cy), fy(cy)], color=col, lw=4,
                                      transform=fig.transFigure))
        elif kind == "dash":
            fig.add_artist(plt.Line2D([fx(x), fx(x + 44)], [fy(cy), fy(cy)], color=col, lw=3, ls=(0, (4, 3)),
                                      transform=fig.transFigure))
        elif kind == "dot":
            fig.add_artist(plt.Line2D([fx(x + 22)], [fy(cy)], marker="o", ms=14, color=col, mec=BG, mew=2,
                                      transform=fig.transFigure))
        elif kind == "tri":
            fig.add_artist(plt.Line2D([fx(x + 22)], [fy(cy)], marker="^", ms=15, color=col, mec=BG, mew=2,
                                      transform=fig.transFigure))
        elif kind == "outline":
            fig.add_artist(Rectangle((fx(x), fy(cy + 11)), 44 / W, 22 / H, fc="none", ec=col, lw=3,
                                     transform=fig.transFigure))
        elif kind == "solid":
            fig.add_artist(Rectangle((fx(x), fy(cy + 11)), 44 / W, 22 / H, fc=col, ec="none",
                                     transform=fig.transFigure))
        else:  # patch
            fig.add_artist(Rectangle((fx(x), fy(cy + 11)), 44 / W, 22 / H, fc=col, ec=col, lw=2, alpha=0.55,
                                     transform=fig.transFigure))
        nl = lab.count("\n")
        fig.text(fx(x + 60), fy(cy - size * 0.72), lab, color=INK2, fontsize=pt(size), va="top", linespacing=1.15)
        yy += size * 1.55 + nl * size * 1.18
    return yy


def panel(fig, x, y, w, h, alpha=0.88):
    fig.add_artist(FancyBboxPatch((fx(x), fy(y + h)), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.008",
                                  fc=BG, ec="#22344f", lw=1.5, alpha=alpha, transform=fig.transFigure, zorder=20))


# ----------------------------------------------------------------------------- shared data
@lru_cache(None)
def search_geo():
    from shapely.geometry import shape
    s = json.load(open(ROOT / "outputs/search/search_polygons.geojson"))
    out = []
    for f in s["features"]:
        out.append((shape(f["geometry"]), f["properties"]))
    return out


@lru_cache(None)
def oi_remaining():
    oi = json.load(open(ROOT / "data/raw/oi2025_search/polygons_oi2025.json"))
    r = next(p for p in oi["polygons"] if p["name"] == "OI2025_26_remaining_NW_strip_calibrated_7428")
    return np.asarray(r["rings"][0]), oi["official_figures"]


def draw_search(ax, mode="campaign", z=4, alpha=0.30, lw=1.4, skip_gaps=True):
    for g, pr in search_geo():
        if skip_gaps and pr.get("pod", 1) == 0:
            continue
        col = CAMP.get(pr["campaign"], (MUTED,))[0] if mode == "campaign" else INK2
        fa = alpha if mode == "campaign" else 0.07
        for poly in getattr(g, "geoms", [g]):
            x, y = poly.exterior.xy
            ax.fill(x, y, color=col, alpha=fa, lw=0, zorder=z)
            ax.plot(x, y, color=col, lw=lw if mode == "campaign" else 1.0, alpha=0.95 if mode == "campaign" else 0.55,
                    zorder=z + 0.1)


# Recommended default of the model-misspecification mixture (outputs/combine/README.md, RESULTS_mix.md):
# satellite layer p_v2, broad component broad_arc, prior weight eps = 0.1, drift weight w = 0.5, POD best.
MIX_SCEN = "sat=p_v2|broad=broad_arc|eps=0.1|w=0.5|pod=best"
SATONLY_SCEN = "sat=p_v2|broad=broad_arc|eps=0.1|w=0|pod=best"   # same, debris drift set aside
# public-facing source line for every figure built on the combined analysis
SRC_COMBINED = ("mh370-open analysis of the public Inmarsat log, ERA5 winds, NOAA drifters, "
                "Geoscience Australia / Malaysian search records")
SATONLY = VIOLET        # satellite-only pick outline
RESEARCH = INK          # re-search block outline (dashed)


@lru_cache(None)
def mix_blocks():
    return pd.read_csv(ROOT / "outputs/combine/ranked_blocks_mix.csv")


@lru_cache(None)
def mix_info():
    return json.load(open(ROOT / "outputs/combine/run_info_mix.json"))


def pick_mix(scen, mode, rank=1, budget=7500):
    """one ranked 7,500 km² block of the mixture run (outputs/combine/ranked_blocks_mix.csv)"""
    b = mix_blocks()
    r = b[(b.scenario == scen) & (b["mode"] == mode) & (b.budget_km2 == budget) & (b["rank"] == rank)]
    assert len(r) == 1, (scen, mode, rank, len(r))
    return r.iloc[0]


@lru_cache(None)
def _published_centres():
    """all 'dd.ddS ddd.ddE' centres printed in outputs/combine/RESULTS_mix.md (rounded from full precision;
    the CSV stores 5 significant digits, so re-rounding it can differ in the last digit)"""
    import re
    txt = (ROOT / "outputs/combine/RESULTS_mix.md").read_text()
    return sorted({(-float(a), float(b)) for a, b in re.findall(r"(\d+\.\d\d)S (\d+\.\d\d)E", txt)})


def centre_txt(row):
    """centre of a block as printed in RESULTS_mix.md (falls back to the CSV value)"""
    c = [(la, lo) for la, lo in _published_centres()
         if abs(la - row.centre_lat) <= 0.0051 and abs(lo - row.centre_lon) <= 0.0051]
    la, lo = min(c, key=lambda q: abs(q[0] - row.centre_lat) + abs(q[1] - row.centre_lon)) if c else \
        (row.centre_lat, row.centre_lon)
    return f"{abs(la):.2f}°S {lo:.2f}°E"


def ranges_txt(row):
    """(lat range, lon range) of a block as printed in RESULTS_mix.md, e.g. ('38.10–39.39°S', '87.98–90.03°E');
    falls back to rounding the CSV values"""
    import re
    c = centre_txt(row).replace("°", "")
    txt = (ROOT / "outputs/combine/RESULTS_mix.md").read_text()
    m = (re.search(re.escape(c) + r" \| (\d+\.\d\d)S-(\d+\.\d\d)S \| (\d+\.\d\d)-(\d+\.\d\d)E \|", txt)
         or re.search("centre " + re.escape(c) + r", (\d+\.\d\d)S-(\d+\.\d\d)S / (\d+\.\d\d)-(\d+\.\d\d)E", txt))
    if m:
        la0, la1, lo0, lo1 = (float(v) for v in m.groups())
        assert abs(la0 - abs(row.lat_max)) < 0.006 and abs(la1 - abs(row.lat_min)) < 0.006
        assert abs(lo0 - row.lon_min) < 0.006 and abs(lo1 - row.lon_max) < 0.006
    else:
        la0, la1, lo0, lo1 = abs(row.lat_max), abs(row.lat_min), row.lon_min, row.lon_max
    return f"{la0:.2f}–{la1:.2f}°S", f"{lo0:.2f}–{lo1:.2f}°E"


def corners(row):
    pts = []
    for tok in row.corners.split(";"):
        la, lo = tok.strip("() ").split(",")
        pts.append((float(la), float(lo)))
    return np.array(pts)


@lru_cache(None)
def areas():
    """Areas 1-3 (top unsearched blocks, default mixture), the satellite-only pick (drift set aside) and
    the re-search block (top block on any ground, default mixture)."""
    return {
        "1": dict(row=pick_mix(MIX_SCEN, "unsearched", 1), heat="mix", colour=AREA, dashed=False,
                  status="Essentially unsearched",
                  title="A long strip on the outer edge\nof the 2018 search",
                  why="Its probability comes almost entirely from the 'model is wrong somewhere' alternative. "
                      "Small changes to the assumptions can swap areas 1 and 2."),
        "2": dict(row=pick_mix(MIX_SCEN, "unsearched", 2), heat="mix", colour=AREA, dashed=False,
                  status="Essentially unsearched",
                  title="Glide zone beyond the south-east\nedge of the 2014–17 search",
                  why="Where a piloted glide after fuel exhaustion would end. The top unsearched area if "
                      "the satellite model is right."),
        "3": dict(row=pick_mix(MIX_SCEN, "unsearched", 3), heat="mix", colour=AREA, dashed=False,
                  status="Essentially unsearched",
                  title="Beside area 1, a little further\nbeyond the arc",
                  why="Shares area 1's logic: just outside the width the 2018 search covered."),
        "S": dict(row=pick_mix(SATONLY_SCEN, "unsearched", 1), heat="mix_w0", colour=SATONLY, dashed=False,
                  status="Essentially unsearched",
                  title="On the arc, just past the southern\nend of the 2014–17 search",
                  why="The top pick if the debris drift is set aside and only the satellite data are trusted. "
                      "With the drift (default settings) it holds about 2%."),
        "R": dict(row=pick_mix(MIX_SCEN, "any", 1), heat="mix", colour=RESEARCH, dashed=True,
                  status="Inside the 2014–17 search",
                  title="Re-search block",
                  why="Only worth it if the 2014–17 search was less thorough than reported."),
    }


def draw_areas(ax, which="123", lw=3.5, label=True, coords=False, size=30, z=14, offsets=None):
    offsets = offsets or {}
    for L in which:
        a = areas()[L]
        r, col = a["row"], a["colour"]
        c = corners(r)
        xs = list(c[:, 1]) + [c[0, 1]]
        ys = list(c[:, 0]) + [c[0, 0]]
        ax.fill(xs, ys, color=col, alpha=0.06 if a["dashed"] else 0.14, zorder=z, lw=0)
        ax.plot(xs, ys, color=col, lw=lw, zorder=z + 0.1, solid_joinstyle="round",
                ls=(0, (4, 2.5)) if a["dashed"] else "-")
        if label:
            dx, dy = offsets.get(L, (0, 0))
            lx, ly = r.centre_lon + dx, r.centre_lat + dy
            ax.text(lx, ly, L, color=BG, fontsize=pt(size), fontweight="bold", ha="center", va="center", zorder=z + 2,
                    bbox=dict(boxstyle="circle,pad=0.25", fc=col, ec=BG, lw=2))


@lru_cache(None)
def posterior(kind):
    if kind in ("mix", "mix_w0", "sat_cond"):
        mix = xr.open_dataset(ROOT / "data/derived/combined_posterior_mix.nc", engine="h5netcdf")
        assert mix.attrs["recommended"] == MIX_SCEN, mix.attrs["recommended"]
        var = {"mix": "post_mix", "mix_w0": "post_mix_broad_arc_eps0p1_w0", "sat_cond": "post_sat_cond"}[kind]
        return mix.lat.values, mix.lon.values, np.nan_to_num(np.asarray(mix[var].values, float))
    comb = xr.open_dataset(ROOT / "data/derived/combined_posterior.nc", engine="h5netcdf")
    lat, lon = comb.lat.values, comb.lon.values
    if kind == "w0":
        p = comb["post_w0_best"].values
    elif kind == "w0p5":
        p = comb["post_w0p5_best"].values
    elif kind == "sat":
        p = xr.open_dataset(ROOT / "data/derived/satcom_posterior.nc", engine="h5netcdf")["p"].values
    elif kind == "eq":  # equal-mode satcom x drift^0.5 x (1-pod), as in scripts/combine_run.py
        from mh370 import combine
        sat = xr.open_dataset(ROOT / "data/derived/satcom_posterior.nc", engine="h5netcdf")
        dr = xr.open_dataset(ROOT / "data/derived/drift_loglik.nc", engine="h5netcdf")
        pod = xr.open_dataset(ROOT / "data/derived/search_pod.nc", engine="h5netcdf")
        p = combine.combine(sat["p_equal_modes"].values, dr["loglik"].values, 0.5, pod["pod"].values)["post"]
    else:
        raise KeyError(kind)
    return lat, lon, np.nan_to_num(np.asarray(p, float))


HEAT_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "heat_navy", ["#5c210c", "#a63d17", "#d95926", "#f0913a", "#ffd27a", "#fff3d1"])


def heat_rgba(p, decades=3.0, mass_keep=0.995):
    p = p / p.sum()
    flat = np.sort(p.ravel())[::-1]
    cut = flat[np.searchsorted(np.cumsum(flat), mass_keep)]
    t = np.clip((np.log10(np.clip(p / flat[0], 1e-12, 1)) + decades) / decades, 0, 1)
    rgba = HEAT_CMAP(t)
    rgba[..., 3] = np.where(p >= cut, 0.30 + 0.65 * t, 0.0)
    return rgba


def draw_heat(ax, kind, z=3, decades=3.0):
    lat, lon, p = posterior(kind)
    ax.imshow(heat_rgba(p, decades), origin="lower", interpolation="bilinear", zorder=z,
              extent=[lon[0] - .025, lon[-1] + .025, lat[0] - .025, lat[-1] + .025], aspect="auto")
    ax.set_xlim(ax._ext[0], ax._ext[1])
    ax.set_ylim(ax._ext[2], ax._ext[3])


def heat_legend(fig, x, y, w=320, label="Probability left (log scale)", size=22):
    g = np.linspace(0, 1, 256)[None, :]
    a = fig.add_axes([fx(x), fy(y + 22), w / W, 22 / H])
    a.imshow(HEAT_CMAP(g), aspect="auto")
    a.set_xticks([])
    a.set_yticks([])
    for s in a.spines.values():
        s.set_visible(False)
    fig.text(fx(x), fy(y - 8), label, color=INK2, fontsize=pt(size), va="bottom")
    fig.text(fx(x), fy(y + 30), "0.1% of peak", color=MUTED, fontsize=pt(size - 2), va="top")
    fig.text(fx(x + w), fy(y + 30), "peak", color=MUTED, fontsize=pt(size - 2), va="top", ha="right")


# ============================================================================= visuals
DESCR: dict[str, str] = {}


def describe(vid, text):
    DESCR[vid] = text


# ---------------------------------------------------------------- V01 title
def v01():
    fig = new_fig()
    ax = map_ax(fig, (0, 0, W, H), -50, 12, lon_c=92)
    draw_land(ax, fc="#18263a", ec="#22344f")
    a = arc7(-44, 5)
    ax.plot(a[:, 1], a[:, 0], color=ARC, lw=2.0, alpha=0.35, zorder=3)
    fig.add_artist(Rectangle((0, 0), 1, 1, fc=BG, alpha=0.45, transform=fig.transFigure, zorder=5))
    fig.text(0.5, 0.56, "Could a plane's sound\nfind MH370?", color=INK, fontsize=pt(120), fontweight="bold",
             ha="center", va="center", linespacing=1.05, zorder=10)
    fig.text(0.5, 0.33, "A public-data reanalysis · November 2026", color=INK2, fontsize=pt(48), ha="center",
             va="center", zorder=10)
    fig.text(0.5, 0.06, "Background: the 7th satellite arc and coastlines (Natural Earth)", color=MUTED,
             fontsize=pt(18), ha="center", zorder=10)
    save(fig, "V01_title")
    describe("V01_title", "Title card over a faint map of the 7th arc. Arc: src/mh370/geo.py; coastlines: Natural Earth.")


# ---------------------------------------------------------------- V02 doppler concept
def v02():
    f0, v, d, c = 100.0, 70.0, 500.0, 343.0
    te = np.linspace(-80, 80, 4001)
    x = v * te
    R = np.hypot(x, d)
    tr = te + R / c
    cos_th = -x / R
    M = v / c
    f = f0 / (1 - M * cos_th)
    t_cpa = d / c  # reception time of the closest-approach emission
    t = tr - t_cpa
    k = (t >= -30) & (t <= 30)
    fig = new_fig()
    title(fig, "The plane-sound trick: a pitch that bends",
          "A steady propeller tone heard by one microphone as the plane flies past")
    badge(fig)
    ax = chart_ax(fig, 170, 250, 1560, 610)
    style_chart(ax)
    ax.plot(t[k], f[k], color=BLUE, lw=5, solid_capstyle="round", zorder=3)
    ax.axvline(0, color="#3a4a63", lw=1.2, zorder=1)
    ax.set_xlim(-30, 30)
    ax.set_ylim(75, 135)
    ax.set_xlabel("Time relative to closest approach (s)", fontsize=pt(28), labelpad=12)
    ax.set_ylabel("Heard pitch (Hz)", fontsize=pt(28), labelpad=12)
    fp, fm = f0 / (1 - M), f0 / (1 + M)
    ax.text(-29, fp - 1.5, f"Approaching: higher\n(→ {fp:.0f} Hz)", color=INK, fontsize=pt(28), va="top")
    ax.text(29, fm + 1.5, f"Moving away: lower\n(→ {fm:.0f} Hz)", color=INK, fontsize=pt(28), va="bottom", ha="right")
    ax.annotate("Pitch falls as\nthe plane passes", xy=(0, f0), xytext=(6, 118), color=INK, fontsize=pt(34),
                fontweight="bold", arrowprops=dict(arrowstyle="-|>", color=INK, lw=2, mutation_scale=24))
    ax.scatter([0], [f0], s=160, color=BLUE, edgecolors=BG, linewidths=2.5, zorder=5)
    ax.text(-1, f0 - 3, "true tone 100 Hz\nat closest approach", color=INK2, fontsize=pt(24), ha="right", va="top")
    fig.text(fx(1730), fy(215), "f = f₀ / (1 − M cos θ)", color=INK2, fontsize=pt(30), ha="right", va="bottom")
    source(fig, "illustration — synthetic 100 Hz tone, 70 m/s, 500 m closest approach, sound speed 343 m/s; "
                "standard moving-source Doppler formula")
    save(fig, "V02_doppler_concept")
    describe("V02_doppler_concept", "ILLUSTRATION: synthetic Doppler S-curve, f = f0/(1 - M cos theta) with retarded time; "
             "f0 = 100 Hz, v = 70 m/s, 500 m closest approach, c = 343 m/s (formula: reports/Aircraft Doppler audio geolocation.md).")


# ---------------------------------------------------------------- V03 flight path
def v03():
    from mh370 import satcom_paths as sp
    KLIA = (2.7456, 101.7099)
    IGARI = (6.9367, 103.585)
    PEN = (5.30, 100.27)
    VAMPI, MEKAR = sp.WPT["VAMPI"], sp.WPT["MEKAR"]
    RAD = tuple(float(v) for v in sp.RADAR_POS)
    fig = new_fig()
    ax = map_ax(fig, (0, 0, W, H), -1.0, 10.6, lon_c=98.7)
    graticule(ax, 2, 2)
    draw_land(ax)
    # transponder leg
    ax.plot([KLIA[1], IGARI[1]], [KLIA[0], IGARI[0]], color=BLUE, lw=5, zorder=6, solid_capstyle="round")
    pts = [IGARI, PEN, VAMPI, MEKAR, RAD]
    ax.plot([p[1] for p in pts], [p[0] for p in pts], color=ORANGE, lw=5, zorder=6, solid_capstyle="round",
            solid_joinstyle="round")
    ax.add_patch(FancyArrowPatch((RAD[1], RAD[0]), (RAD[1] - 0.4, RAD[0] - 5.8), arrowstyle="-|>",
                                 mutation_scale=40, color=INK, lw=3.5, ls=(0, (6, 5)), zorder=7,
                                 connectionstyle="arc3,rad=0.25"))
    ax.text(RAD[1] - 0.3, RAD[0] - 3.4, "?", color=INK, fontsize=pt(110), fontweight="bold", ha="right",
            va="center", zorder=8, path_effects=HALO)
    point(ax, KLIA[1], KLIA[0], "Kuala Lumpur (KLIA)\nDeparted 00:42", dx=0.25, dy=-0.15, va="top", size=28)
    point(ax, IGARI[1], IGARI[0], "IGARI\n01:19 last words\n01:21 transponder off", dx=0.25, va="center",
          size=28, weight="bold")
    point(ax, PEN[1], PEN[0], "Penang", dx=0.25, dy=0.05, size=28)
    point(ax, VAMPI[1], VAMPI[0], "VAMPI", dx=0.0, dy=-0.32, ha="center", va="top", size=26)
    point(ax, MEKAR[1], MEKAR[0], "MEKAR", dx=0.2, dy=0.28, ha="left", va="bottom", size=26)
    point(ax, RAD[1], RAD[0], "Last radar contact\n02:22", color=ORANGE, s=320, dx=-0.3, dy=0.35, ha="right",
          va="bottom", size=30, weight="bold")
    for nm, la, lo in (("Malay\nPeninsula", 4.6, 101.9), ("Sumatra", 2.3, 98.6), ("Andaman Sea", 8.5, 97.0),
                       ("Strait of\nMalacca", 3.6, 99.6)):
        ax.text(lo, la, nm, color="#7f8ca0" if nm != "Andaman Sea" else MUTED, fontsize=pt(26), ha="center",
                va="center", style="italic", zorder=5)
    title(fig, "8 March 2014: the turn back", "Times are Malaysian local time (UTC+8)", box=True)
    legend_box(fig, [("line", BLUE, "Transponder on (civil radar)"),
                     ("line", ORANGE, "Military radar only"),
                     ("dash", INK, "After 02:22: no radar")], 80, 210, size=26)
    source(fig, "Malaysian AIP waypoints; last radar point from ATSB (2017); "
                "route drawn as straight lines between published points (simplified)")
    save(fig, "V03_flight_path")
    describe("V03_flight_path", "Map: KLIA -> IGARI (transponder) -> Penang -> VAMPI -> MEKAR -> last radar 02:22 MYT, dashed '?' arrow south. "
             "Waypoints and radar point from src/mh370/satcom_paths.py; KLIA/IGARI/Penang coordinates from the brief; route simplified to straight segments.")


# ---------------------------------------------------------------- V04 arcs map
def sat_subpoint(t):
    s = geo.sat_pos(t)
    lon = math.degrees(math.atan2(s[1], s[0]))
    lat = math.degrees(math.atan2(s[2], math.hypot(s[0], s[1])))
    return lat, lon


def v04():
    rings = [(lab, t, b) for lab, t, b, _ in geo.HANDSHAKES if np.isfinite(b)]
    fig = new_fig()
    ax = map_ax(fig, (620, 0, 1300, H), -47, 14, lon_c=93)
    graticule(ax, 10, 10)
    draw_land(ax)
    lon0, lon1, lat0, lat1 = ax._ext
    LA, LO = np.meshgrid(np.arange(lat0 - 1, 12.01, 0.1), np.arange(lon0 - 1, lon1 + 1, 0.1), indexing="ij")
    slat, slon = sat_subpoint(geo.ARC7_TIME)
    LX = 72.0  # rings drawn east of this meridian; labelled where they end
    lab_pts = []
    for lab, t, b in rings:
        last = (b == geo.ARC7_BTO_US)
        bto = np.where(LO >= LX, geo.predicted_bto(LA, LO, 0.0, t), np.nan)
        ax.contour(LO, LA, bto, levels=[b], colors=[ARC if last else ARC_DIM], linewidths=4.5 if last else 2.2,
                   zorder=8 if last else 6)
        la_g = np.arange(-60, 0, 0.01)
        v = geo.predicted_bto(la_g, np.full_like(la_g, LX), 0.0, t) - b
        i = np.where(np.sign(v[:-1]) != np.sign(v[1:]))[0]
        hh, mm = divmod(int(((t + 8 * 3600) % 86400) // 60), 60)
        if not last and i.size:
            lab_pts.append((f"{hh:02d}:{mm:02d}", float(la_g[i[0]])))
    # spread labels vertically (>= 1.75 deg apart) around their true crossings
    lab_pts.sort(key=lambda r: -r[1])
    ys = [r[1] for r in lab_pts]
    for _ in range(200):
        for j in range(1, len(ys)):
            if ys[j - 1] - ys[j] < 1.75:
                d = (1.75 - (ys[j - 1] - ys[j])) / 2
                ys[j - 1] += d
                ys[j] -= d
    for (txt, la), yl in zip(lab_pts, ys):
        ax.plot([LX - 2.2, LX - 0.8, LX - 0.1], [yl, yl, la], color=ARC_DIM, lw=1.4, zorder=7)
        ax.text(LX - 2.5, yl, txt, color=INK2, fontsize=pt(26), ha="right", va="center", zorder=12, path_effects=HALO)
    lo7 = arc_lon(-31.0)
    ax.text(lo7 + 1.6, -31.0, "08:19\n7th arc", color=INK, fontsize=pt(36), fontweight="bold", va="center",
            zorder=12, path_effects=HALO)
    ax.scatter([slon], [slat], marker="*", s=900, c=YELLOW, edgecolors=BG, linewidths=2, zorder=12)
    ax.text(slon + 1.5, slat + 1.2, "Satellite overhead\n(Inmarsat-3 F1, ~64.5°E)", color=INK, fontsize=pt(26),
            va="bottom", zorder=12, path_effects=HALO)
    ax.text(121, -26, "Australia", color="#7f8ca0", fontsize=pt(28), ha="center", style="italic", zorder=5)
    # left panel
    title(fig, "Seven pings,\nseven rings", None, size=60)
    fig.text(fx(80), fy(270), "Each hourly reply carried a timing\nvalue: the distance to the satellite.\nThat puts the plane on a ring.",
             color=INK2, fontsize=pt(32), va="top", linespacing=1.35)
    fig.text(fx(80), fy(470), "Ring times (Malaysian time)", color=INK2, fontsize=pt(26), fontweight="bold", va="top")
    fig.text(fx(80), fy(515), "02:25 · 03:41 · 04:41\n05:41 · 06:41 · 08:10\n08:19 (the 7th arc)", color=INK,
             fontsize=pt(32), va="top", linespacing=1.4)
    fig.text(fx(80), fy(760), "Only the Indian Ocean side of each\nring is drawn. Rings at sea level.", color=MUTED,
             fontsize=pt(24), va="top", linespacing=1.35)
    source(fig, "mh370-open analysis of the public Inmarsat log (timing values); rings computed at sea level")
    save(fig, "V04_arcs_map")
    describe("V04_arcs_map", "Map of the seven BTO rings (18:25, 19:41, 20:41, 21:41, 22:41, 00:10:58, 00:19:29 UTC = 02:25-08:19 MYT), "
             "south of 12N only, 7th arc emphasised, satellite sub-point at 00:19:29. Contours of geo.predicted_bto at sea level for the BTO values in geo.HANDSHAKES.")


# ---------------------------------------------------------------- V05 BFO chart
def bestfit_bfo_curve(mode="LNAV"):
    from mh370 import satcom
    from mh370 import satcom_paths as sp
    z = np.load(ROOT / f"data/derived/satcom_smc/baseline_{mode}.npz", allow_pickle=False)
    i = int(np.argmax(z["ll"]))
    names = list(z["names"])
    P = {k: z["x"][i:i + 1, j] for j, k in enumerate(names)}
    tt = np.unique(np.r_[np.arange(geo.hms(18, 26), geo.ARC7_TIME, 60.0), z["bfo_t"], geo.ARC7_TIME])
    meas = pd.DataFrame({"t": tt})
    o = sp.PathModel(mode, meas).run(P)
    pred = satcom.bfo(tt[None, :], o["lat"], o["lon"], o["h"][:, None], o["vn"], o["ve"], 0.0, bias=0.0)[0]
    pred = pred + float(z["bias"][i])
    # check against stored residuals at the fitted times
    sel = np.searchsorted(tt, z["bfo_t"])
    m = sp.build_measurements()
    zf = m[m.kind == "BFO"].z.to_numpy()
    res = zf - pred[sel]
    assert np.allclose(res, z["bfo_res"][i], atol=0.05), (res, z["bfo_res"][i])
    t_fmt = float(P["t_fmt"][0])
    return tt, pred, m[m.kind == "BFO"], t_fmt


def t_to_myt_hours(t):
    return (np.asarray(t) - geo.hms(16)) / 3600.0 + 0.0  # hours after 16:00 UTC = 00:00 MYT


def v05():
    tt, pred, mf, t_fmt = bestfit_bfo_curve("LNAV")
    fig = new_fig()
    title(fig, "The frequency data pointed south",
          "Measured frequency offset (BFO) vs this project's best-fit southern path")
    ax = chart_ax(fig, 170, 230, 1560, 640)
    style_chart(ax)
    x = t_to_myt_hours(tt)
    ax.plot(x, pred, color=BLUE, lw=4, zorder=3, solid_capstyle="round")
    ax.scatter(t_to_myt_hours(mf.t), mf.z, s=260, c=INK, edgecolors=BG, linewidths=2.5, zorder=5)
    excl = [(lab, t, f) for lab, t, b, f in geo.HANDSHAKES if lab.startswith("18:25:27") or lab.startswith("00:19:29")]
    ax.scatter(t_to_myt_hours([e[1] for e in excl]), [e[2] for e in excl], s=240, facecolors="none", edgecolors=INK,
               linewidths=2.5, zorder=5)
    ax.annotate("not used: power-up log-on", xy=(t_to_myt_hours(excl[0][1]), excl[0][2]),
                xytext=(t_to_myt_hours(excl[0][1]) + 0.25, 232), color=INK2, fontsize=pt(24),
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.5))
    ax.annotate("not used: final descent", xy=(t_to_myt_hours(excl[1][1]), excl[1][2]),
                xytext=(t_to_myt_hours(excl[1][1]) - 1.45, 150), color=INK2, fontsize=pt(24),
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.5))
    hf = t_to_myt_hours(t_fmt)
    ax.annotate("turn south\n(best fit)", xy=(hf, float(np.interp(t_fmt, tt, pred))), xytext=(hf + 0.35, 75),
                color=INK2, fontsize=pt(24), arrowprops=dict(arrowstyle="-", color=MUTED, lw=1.5))
    ticks = np.arange(2, 9)
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{h:02d}:00" for h in ticks])
    ax.set_xlim(2.2, 8.55)
    ax.set_ylim(60, 270)
    ax.set_xlabel("8 March 2014, Malaysian time", fontsize=pt(28), labelpad=12)
    ax.set_ylabel("Frequency offset, BFO (Hz)", fontsize=pt(28), labelpad=12)
    legend_box(fig, [("dot", INK, "Measured (public Inmarsat log)"),
                     ("line", BLUE, "Best-fit southern path (model)")], 760, 250, size=26)
    source(fig, "public Inmarsat log (Sladen transcription); best-fit path from the mh370-open satellite model "
                "with ERA5 winds")
    save(fig, "V05_bfo_chart")
    describe("V05_bfo_chart", "Chart: measured BFO (8 values used in the fit from the public log; hollow = 18:25:27 log-on and 00:19:29 descent values "
             "from geo.HANDSHAKES, not used) vs the BFO predicted along the maximum-likelihood LNAV path (baseline SMC run), "
             "fitted bias included; residuals checked against the stored best-fit residuals. No northern-route curve (not computed credibly).")


# ---------------------------------------------------------------- V06 search timeline
def v06():
    import datetime as dt
    D = lambda y, m, d: dt.date(y, m, d).toordinal()
    fig = new_fig()
    title(fig, "Twelve years of searching", "Searches for MH370 and the seabed area each covered")
    ax = chart_ax(fig, 560, 220, 1300, 640)
    ax.set_facecolor(BG)
    for sp_ in ax.spines.values():
        sp_.set_visible(False)
    x0, x1 = D(2014, 1, 1), D(2027, 12, 31)
    rows = [  # row, name, [(start, end)], value text, value side, colour, kind, sub
        (5, "Surface & pinger search", [(D(2014, 3, 8), D(2014, 4, 28))], "ocean surface only", "right", MUTED, "fill",
         "Mar–Apr 2014"),
        (4, "ATSB-led sonar search", [(D(2014, 10, 6), D(2017, 1, 17))], "~120,000 km²", "right", BLUE, "fill",
         "Oct 2014 – suspended 17 Jan 2017"),
        (3, "Ocean Infinity 2018", [(D(2018, 1, 22), D(2018, 5, 29))], ">112,000 km²", "right", ORANGE, "fill",
         "22 Jan – 29 May 2018"),
        (2, "Ocean Infinity 2025–26", [(D(2025, 3, 25), D(2025, 3, 28)), (D(2025, 12, 31), D(2026, 1, 23))],
         "7,571 km² in 28 days", "left", AQUA, "fill", "Mar 2025 + Dec 2025 – Jan 2026"),
        (1, "Contract extended", [(D(2026, 6, 29), D(2027, 6, 30))], "7,428.54 km² still to search", "left", AQUA,
         "outline", "to 30 Jun 2027 · no restart announced"),
    ]
    for yr in range(2014, 2028):
        ax.axvline(D(yr, 1, 1), color=GRID, lw=1.2, zorder=0)
        ax.text(D(yr, 7, 2), 0.3, f"’{yr % 100:02d}" if yr not in (2014, 2027) else str(yr), color=INK2,
                fontsize=pt(24), ha="center")
    for y, name, spans, val, side, col, kind, sub in rows:
        for a_, b_ in spans:
            bw = max(b_ - a_, 20)
            if kind == "fill":
                ax.add_patch(Rectangle((a_, y - 0.15), bw, 0.30, fc=col, ec="none", zorder=3))
            else:
                ax.add_patch(Rectangle((a_, y - 0.15), bw, 0.30, fc="none", ec=col, lw=3, ls=(0, (5, 4)), zorder=3))
        if side == "right":
            ax.text(spans[-1][1] + 60, y, val, color=INK, fontsize=pt(32), fontweight="bold", va="center", ha="left")
        else:
            ax.text(spans[0][0] - 60, y, val, color=INK, fontsize=pt(32), fontweight="bold", va="center", ha="right")
        ty = fy(220 + 640 * (1 - (y - 0.0) / 5.8))
        fig.text(fx(520), ty + 14 / H, name, color=INK, fontsize=pt(30), ha="right", va="center", fontweight="bold")
        fig.text(fx(520), ty - 22 / H, sub, color=MUTED, fontsize=pt(22), ha="right", va="center")
    today = D(2026, 11, 5)
    ax.axvline(today, color=INK, lw=2, zorder=4)
    ax.text(today, 5.75, "today", color=INK, fontsize=pt(24), ha="center", va="bottom")
    ax.set_xlim(x0, x1)
    ax.set_ylim(0.0, 5.8)
    ax.set_xticks([])
    ax.set_yticks([])
    source(fig, "ATSB (2017); Malaysian Ministry of Transport / AAIB updates; Malaysian Cabinet extension (29 Jun 2026); "
                "Ocean Infinity statements")
    save(fig, "V06_search_timeline")
    describe("V06_search_timeline", "Timeline 2014-2027: surface/pinger search (8 Mar-28 Apr 2014), ATSB sonar search (Oct 2014-17 Jan 2017, ~120,000 km2), "
             "OI 2018 (22 Jan-29 May 2018, >112,000 km2), OI 2025-26 (25-28 Mar 2025 + 31 Dec 2025-23 Jan 2026, 7,571 km2 in 28 days), "
             "extension to 30 Jun 2027 with 7,428.54 km2 remaining. Sources: outputs/search/README.md, reports/MH370 open data search avenues.md, "
             "research_notes (official_investigation_and_search.md).")


# ---------------------------------------------------------------- V07 searched map
def v07():
    fig = new_fig()
    ax = map_ax(fig, (0, 0, W, H), -41.6, -23.4, lon_c=94.0)
    graticule(ax, 5, 5)
    draw_land(ax)
    draw_search(ax, alpha=0.40)
    draw_arc7(ax, lw=2.6, label="7th arc", label_lat=-24.4, dx=0.5)
    ring, _ = oi_remaining()
    ax.plot(ring[:, 0], ring[:, 1], color=INK, lw=2.6, ls=(0, (5, 3)), zorder=10)
    cl = ring.mean(0)
    ax.annotate("Still to search under the\ncurrent contract (~7,400 km²)", xy=(cl[0] - 0.2, cl[1]),
                xytext=(cl[0] - 7.6, cl[1] + 2.4), color=INK, fontsize=pt(26), zorder=12,
                arrowprops=dict(arrowstyle="-", color=INK, lw=1.8), path_effects=HALO)
    ax.text(86.4, -36.9, "ATSB-led\n2014–17", color=INK, fontsize=pt(30), fontweight="bold", zorder=12,
            path_effects=HALO, ha="right")
    ax.text(103.3, -27.8, "Ocean Infinity\n2018", color=INK, fontsize=pt(30), fontweight="bold", zorder=12,
            path_effects=HALO)
    ax.annotate("Ocean Infinity\n2025–26", xy=(94.6, -35.1), xytext=(98.0, -38.6), color=INK, fontsize=pt(30),
                fontweight="bold", zorder=12, path_effects=HALO,
                arrowprops=dict(arrowstyle="-", color=INK, lw=1.8))
    ax.text(116.0, -30.5, "Australia", color="#7f8ca0", fontsize=pt(30), style="italic", ha="center", zorder=5)
    title(fig, "Where the seabed has been searched", "About a quarter of a million km² mapped since 2014", box=True)
    legend_box(fig, [("patch", BLUE, "ATSB-led 2014–17 (Geoscience Australia)"),
                     ("patch", ORANGE, "Ocean Infinity 2018 (digitised maps)"),
                     ("patch", AQUA, "Ocean Infinity 2025–26 (reconstructed from ship tracks)"),
                     ("dash", INK, "Contract area not yet searched")], 80, 215, size=24)
    source(fig, "Geoscience Australia / AusSeabed (CC BY 4.0); Malaysian search updates; AIS ship tracks; "
                "Ocean Infinity; mh370-open reconstruction")
    save(fig, "V07_searched_map")
    describe("V07_searched_map", "Map of all reconstructed search polygons by campaign (outputs/search/search_polygons.geojson), 7th arc, and "
             "the OI contract's remaining NW strip ('OI2025_26_remaining_NW_strip_calibrated_7428'). Union = 255,609 km2 per outputs/search/README.md.")


# ---------------------------------------------------------------- V08 debris map
def v08():
    deb = pd.read_csv(ROOT / "outputs/drift/debris_items.csv")
    fig = new_fig()
    ax = map_ax(fig, (0, 0, W, H), -44.5, 3.0, lon0=16.5, lon1=118.5)
    graticule(ax, 10, 10)
    draw_land(ax)
    draw_arc7(ax, lw=3, label="7th arc", label_lat=-14.0, dx=0.8)
    for _, r in deb.iterrows():
        big = r.key == "flaperon"
        ax.scatter(r.lon, r.lat, s=520 if big else 200, c=ORANGE if not big else YELLOW, edgecolors=INK if big else BG,
                   linewidths=3 if big else 2, zorder=12 if big else 11)
    fl = deb[deb.key == "flaperon"].iloc[0]
    ax.annotate("Flaperon · Réunion\n29 July 2015", xy=(fl.lon, fl.lat), xytext=(fl.lon + 5.5, fl.lat + 5.5),
                color=INK, fontsize=pt(32), fontweight="bold", zorder=13, path_effects=HALO,
                arrowprops=dict(arrowstyle="-", color=INK, lw=2))
    for nm, la, lo in (("Mozambique", -18.5, 36.0), ("South\nAfrica", -29.5, 24.5), ("Madagascar", -20.0, 46.6),
                       ("Tanzania", -6.5, 34.0)):
        ax.text(lo, la, nm, color="#8592a6", fontsize=pt(26), style="italic", ha="center", zorder=5)
    ax.annotate("Western Australia:\nnone found", xy=(114.2, -29.5), xytext=(117.8, -37.0), color=INK,
                fontsize=pt(32), fontweight="bold", ha="right", va="center", zorder=12, path_effects=HALO,
                arrowprops=dict(arrowstyle="-", color=INK, lw=2))
    title(fig, "The ocean gave pieces back", None, box=True)
    legend_box(fig, [("dot", YELLOW, "Flaperon (first find)"),
                     ("dot", ORANGE, "Other finds, Dec 2015 – Jan 2017")], 860, 730, size=26)
    fig.text(fx(860), fy(845), "15 find sites (18 items) rated confirmed,\nalmost certain or highly likely",
             color=INK2, fontsize=pt(24), va="top", linespacing=1.3)
    source(fig, "Malaysia Safety Investigation Report (2018), Table 1.12A; ATSB debris updates; coastlines Natural Earth")
    save(fig, "V08_debris_map")
    describe("V08_debris_map", "Map of the 15 debris find sites (18 items; SIR confirmed/almost certain/highly likely, Jul 2015-Jan 2017) "
             "from outputs/drift/debris_items.csv, flaperon highlighted, 7th arc, 'none found in Western Australia'.")


# ---------------------------------------------------------------- V09 leads map
def v09():
    from mh370 import acoustic as A
    fig = new_fig()
    ax = map_ax(fig, (600, 0, 1320, H), -47.4, -7.0, lon_c=103.2)
    graticule(ax, 5, 5)
    draw_land(ax)
    draw_arc7(ax, lw=3, label="7th arc", label_lat=-17.0, dx=0.6)
    ha = A.RECEIVERS["HA01"]
    for az, crossing in ((306.18, (-25.73, 101.37)), (246.9, (-40.97, 81.57))):
        d_km = geo.haversine_km(ha["lat"], ha["lon"], *crossing)
        r = np.linspace(0, float(d_km), 200)
        la, lo = A.forward(np.full_like(r, ha["lat"]), np.full_like(r, ha["lon"]), np.full_like(r, az), r)
        ax.plot(lo, la, color=AQUA, lw=2.2, ls=(0, (6, 4)), zorder=7)
    pts = [
        ("Kadri 2024 sound\n(bearing × arc)", -25.73, 101.37, AQUA, (0.6, 0.0), "left"),
        ("Stead / LANL 2014 sound", -40.97, 81.57, AQUA, (0.7, 0.75), "left"),
        ("Anderson 'Java' sound", -8.36, 107.92, AQUA, (-0.6, 0.0), "right"),
        ("WSPR claim\n29.1°S 99.9°E", -29.128, 99.934, VIOLET, (0.6, -0.3), "left"),
        ("UGIB 2020 hotspot", -34.23, 93.78, ORANGE, (-0.7, 0.5), "right"),
        ("CSIRO drift 2017", -35.6, 92.8, ORANGE, (-0.7, -0.5), "right"),
    ]
    for lab, la, lo, col, (dx, dy), al in pts:
        point(ax, lo, la, lab, color=col, s=330, dx=dx, dy=dy, ha=al, size=27, weight="bold")
    for key, lab, dx, dy, al in (("HA01", "Cape Leeuwin hydrophone\n(test-ban network)", 0.5, -1.4, "left"),
                                 ("PAPCA", "IMOS Perth Canyon", 0.6, 0.0, "left"),
                                 ("PAKIM", "IMOS Kimberley", -0.6, 0.0, "right")):
        r = A.RECEIVERS[key]
        point(ax, r["lon"], r["lat"], lab, color=INK, marker="^", s=300, dx=dx, dy=dy, ha=al, size=24, lcolor=INK2)
    pr = A.RECEIVERS["PAPOR"]
    ax.annotate(f"IMOS Portland, Vic.\n({fmt_ll(pr['lat'], pr['lon'], 1)}) →", xy=(ax._ext[1] - 0.2, -38.5),
                xytext=(ax._ext[1] - 0.4, -38.5), ha="right", va="center", color=INK2, fontsize=pt(22), zorder=12,
                path_effects=HALO)
    ax.text(122.5, -25.0, "Australia", color="#7f8ca0", fontsize=pt(30), style="italic", ha="center", zorder=5)
    title(fig, "The other leads", None, size=56)
    fig.text(fx(80), fy(160), "Sounds, radio and drift claims\nnear the 7th arc", color=INK2, fontsize=pt(30), va="top",
             linespacing=1.3)
    legend_box(fig, [("dot", AQUA, "Hydrophone / seismic\ncandidates"),
                     ("dot", VIOLET, "WSPR radio claim"),
                     ("dot", ORANGE, "Published drift /\nsatellite hotspots"),
                     ("tri", INK, "Recorders"),
                     ("dash", AQUA, "Bearings from\nCape Leeuwin")], 80, 330, size=27)
    source(fig, "Kadri (2024); Curtin University / LANL (2014); Anderson; Godfrey et al. (WSPR); UGIB (2020); CSIRO (2017); "
                "recorder positions IMOS / AODN and FDSN")
    save(fig, "V09_leads_map")
    describe("V09_leads_map", "Map of candidate points (Kadri crossing 25.73S 101.37E, Stead/LANL 40.97S 81.57E, Anderson 8.36S 107.92E, "
             "WSPR 29.128S 99.934E, UGIB 34.23S 93.78E, CSIRO 35.6S 92.8E), HA01 bearings 306.18 and 246.9 deg, HA01/IMOS recorder "
             "positions from src/mh370/acoustic.py, 7th arc.")


# ---------------------------------------------------------------- V10 sound footprint
def v10():
    H_src = 10.7e3
    c_g = 331.3 * math.sqrt(1 + 28 / 273.15)
    c_s = 331.3 * math.sqrt(1 + (-54) / 273.15)
    g = (c_s - c_g) / H_src  # 1/s (negative)
    z = np.linspace(H_src, 0, 4000)
    cz = c_g + g * z
    th_lim = math.degrees(math.acos(c_s / c_g))
    fig = new_fig()
    title(fig, "Why a jet's sound stays near its track",
          "Sound from cruise height bends upwards; only steep rays reach the sea")
    badge(fig)
    ax = chart_ax(fig, 160, 240, 1600, 620)
    style_chart(ax, grid_axis=None)
    ax.set_facecolor(BG)

    def ray(theta_deg, side):
        cos0 = math.cos(math.radians(theta_deg))
        xs, zs, x = [0.0], [H_src], 0.0
        for i in range(1, z.size):
            cth = cos0 * cz[i] / c_s
            if cth >= 1:  # turning point: ray bends back up
                return np.array(xs), np.array(zs), False
            dz = z[i - 1] - z[i]
            x += dz * cth / math.sqrt(1 - cth ** 2)
            xs.append(x)
            zs.append(z[i])
        return np.array(xs), np.array(zs), True

    def ray_up(theta_deg):
        # shallow ray: down to the turning height, then mirror back up (linear-gradient circular arc)
        xs, zs, hit = ray(theta_deg, 1)
        if hit:
            return xs, zs
        x2 = xs[-1] + (xs[-1] - xs[::-1])
        z2 = zs[::-1]
        return np.r_[xs, x2], np.r_[zs, z2]

    reach = []
    for th in (35, 45, 60, 75, 90):
        xs, zs, hit = ray(th, 1)
        for sgn in (1, -1):
            ax.plot(sgn * xs / 1e3, zs / 1e3, color=BLUE, lw=3, zorder=3)
        reach.append(xs[-1] / 1e3)
    xs, zs, hit = ray(th_lim + 0.05, 1)
    x_lim = xs[-1] / 1e3
    for sgn in (1, -1):
        ax.plot(sgn * xs / 1e3, zs / 1e3, color=BLUE, lw=3, zorder=3)
    for th in (5, 15, 25):
        xs, zs = ray_up(th)
        k = xs / 1e3 < 75
        for sgn in (1, -1):
            ax.plot(sgn * xs[k] / 1e3, zs[k] / 1e3, color="#5a6b85", lw=2.4, zorder=2)
    ax.fill_between([-x_lim, x_lim], -0.55, 0.0, color=AQUA, alpha=0.85, zorder=4, lw=0)
    ax.fill_between([-75, 75], -1.2, -0.55, color="#10304d", zorder=1, lw=0)
    ax.text(0, -0.9, "Audible strip: roughly 25–40 km each side (estimate)", color=INK,
            fontsize=pt(30), fontweight="bold", ha="center", va="center", zorder=6)
    ax.scatter([0], [H_src / 1e3], marker="o", s=420, c=INK, edgecolors=BG, linewidths=3, zorder=6)
    ax.text(2.5, H_src / 1e3 + 0.3, "Boeing 777 at ~35,000 ft (10.7 km),\nflying into the screen", color=INK,
            fontsize=pt(28), va="bottom", zorder=6)
    ax.text(-74, 4.2, "Shallow rays curve\nback upwards", color=INK2, fontsize=pt(26), zorder=6)
    ax.text(74, 4.2, f"Only rays leaving more than\n~{th_lim:.0f}° below horizontal\nreach the surface", color=INK2,
            fontsize=pt(26), ha="right", zorder=6)
    ax.text(74, -0.9, "shadow zone", color=MUTED, fontsize=pt(24), ha="right", va="center", zorder=6)
    ax.text(-74, -0.9, "shadow zone", color=MUTED, fontsize=pt(24), ha="left", va="center", zorder=6)
    ax.set_xlim(-75, 75)
    ax.set_ylim(-1.2, 12.2)
    ax.set_xlabel("Distance across the flight track (km)", fontsize=pt(28), labelpad=12)
    ax.set_ylabel("Height (km)", fontsize=pt(28), labelpad=12)
    ax.set_yticks([0, 2, 4, 6, 8, 10, 12])
    source(fig, "illustration — idealised ray trace: +28 °C at sea level, −54 °C at 10.7 km, linear profile, no wind; "
                "~25–40 km each side is an estimate, not a measurement")
    save(fig, "V10_sound_footprint")
    describe("V10_sound_footprint", f"ILLUSTRATION: cross-section ray trace for a source at 10.7 km in a linear sound-speed profile "
             f"(+28 C surface, -54 C aloft, no wind, from reports/MH370 acoustic tracking feasibility.md). Limiting depression angle "
             f"{th_lim:.0f} deg; audible strip +/-{x_lim:.0f} km (report: ~25-40 km each side, an inference).")
    return x_lim, th_lim


# ---------------------------------------------------------------- V11 approach diagram
def v11():
    fig = new_fig()
    title(fig, "What we did: layers, not a single guess", "Public data only · every layer checked against published results")

    def box(x, y, w, h, head, body, col, dashed=False):
        fig.add_artist(FancyBboxPatch((fx(x), fy(y + h)), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.012",
                                      fc=PANEL, ec=col, lw=3, ls=(0, (6, 4)) if dashed else "-",
                                      transform=fig.transFigure))
        fig.add_artist(Rectangle((fx(x), fy(y + h)), 12 / W, h / H, fc=col, ec="none", transform=fig.transFigure))
        fig.text(fx(x + 36), fy(y + 26), head, color=INK, fontsize=pt(32), fontweight="bold", va="top")
        fig.text(fx(x + 36), fy(y + 76 + 44 * head.count("\n")), body, color=INK2, fontsize=pt(24), va="top",
                 linespacing=1.3)

    def arrow(x0, y0, x1, y1, dashed=False, col=INK2):
        fig.add_artist(FancyArrowPatch((fx(x0), fy(y0)), (fx(x1), fy(y1)), transform=fig.transFigure,
                                       arrowstyle="-|>", mutation_scale=30, color=col, lw=3,
                                       ls=(0, (6, 4)) if dashed else "-"))

    rows = [("Satellite", "Inmarsat log + ERA5 winds", BLUE, False),
            ("Debris drift", "NOAA drifters + 15 debris finds", ORANGE, False),
            ("Sound", "IMOS hydrophones + seismometers\ntested: nothing above chance → no layer", AQUA, True),
            ("Searched seabed", "Geoscience Australia, Malaysian\nupdates, ship tracking (AIS)", YELLOW, False)]
    y = 210
    for head, body, col, dsh in rows:
        box(80, y, 640, 150, head, body, col, dsh)
        arrow(730, y + 75, 975, 540, dashed=dsh)
        y += 175
    box(990, 420, 400, 240, "Combined\nprobability", "satellite × drift\n× (1 − chance already found)\n+ a 'model is wrong' option",
        INK)
    arrow(1400, 540, 1490, 540)
    box(1500, 420, 340, 240, "Ranked\nareas", "unsearched first,\nwith coordinates", AREA)
    source(fig, "mh370-open method; the sound recordings were tested but no acoustic layer was built")
    save(fig, "V11_approach_diagram")
    describe("V11_approach_diagram", "Flow diagram: satellite / drift / sound / searched seabed -> combined probability (incl. the broad "
             "'model is wrong' mixture component, outputs/combine/README.md 'Model-misspecification mixture') -> ranked areas. "
             "Sound arrow dashed: the acoustic module found nothing above chance and no acoustic layer entered the combination "
             "(outputs/acoustic/README.md, outputs/combine/README.md).")


# ---------------------------------------------------------------- V12 satcom profile
def v12():
    prof = pd.read_csv(ROOT / "outputs/satcom/arc_profile_v2.csv")
    dstg = pd.read_csv(ROOT / "outputs/satcom/dstg_fig10_3_digitised.csv")
    summ = json.load(open(ROOT / "outputs/satcom/summary_v2.json"))["arcprofile"]
    lat = -prof.lat.to_numpy()
    dlat = abs(float(np.median(np.diff(prof.lat))))

    def pdf_of(col):
        p = prof[col].to_numpy()
        return np.convolve(p / p.sum() / dlat, np.ones(3) / 3, mode="same")  # display smoothing over 0.3 deg

    pv2, pdes, pold = pdf_of("p_v2"), pdf_of("p_v2_sens_descent1840"), pdf_of("p")
    med = -summ["p_v2"]["median"]
    hi90, lo90 = (-v for v in summ["p_v2"]["i90"])           # i90 = [south, north]
    med_d = -summ["p_v2_sens_descent1840"]["median"]
    assert abs(med - 38.17) < 0.01 and abs(lo90 - 36.46) < 0.01 and abs(hi90 - 39.51) < 0.01 and abs(med_d - 35.82) < 0.01
    dl = -dstg.lat.to_numpy()
    dp = dstg.pdf_per_deg.to_numpy()
    top = max(pv2.max(), pold.max())
    fig = new_fig()
    title(fig, "Finding one: the satellite data points to the high thirties",
          "Where the flight ended, by latitude along the 7th arc (probability per degree)")
    ax = chart_ax(fig, 170, 240, 1560, 620)
    style_chart(ax)
    k = (lat >= lo90) & (lat <= hi90)
    ax.fill_between(lat[k], 0, pv2[k], color=BLUE, alpha=0.25, lw=0, zorder=2)
    ax.plot(lat, pold, color=MUTED, lw=2.4, ls=(0, (5, 3)), zorder=3)
    ax.plot(dl, dp, color=ORANGE, lw=3.0, zorder=3, solid_capstyle="round")
    ax.plot(lat, pdes, color=AQUA, lw=3.4, zorder=3.5, solid_capstyle="round")
    ax.plot(lat, pv2, color=BLUE, lw=4.5, zorder=4, solid_capstyle="round")
    ax.axvline(med, color=INK, lw=2, zorder=5)
    ax.text(med + 0.12, top * 1.04, f"Median {med:.1f}°S", color=INK, fontsize=pt(30), fontweight="bold", va="bottom")
    ax.annotate("", xy=(lo90, top * 0.05), xytext=(hi90, top * 0.05),
                arrowprops=dict(arrowstyle="<->", color=INK, lw=2, mutation_scale=22), zorder=6)
    ax.text(hi90 + 0.75, top * 0.16, f"90% range:\n{lo90:.1f}–{hi90:.1f}°S", color=INK, fontsize=pt(28), ha="left",
            va="bottom", zorder=6, fontweight="bold")
    # descent variant: direct label at its peak
    ipk = int(np.argmax(np.where(lat < 37.5, pdes, 0)))
    ax.annotate(f"If the plane was descending\nduring the 02:40 call:\nmedian {med_d:.1f}°S",
                xy=(lat[ipk] - 0.1, pdes[ipk] * 1.03), xytext=(34.45, top * 0.74), color=INK, fontsize=pt(26),
                fontweight="bold", ha="left", va="center", zorder=7, linespacing=1.2,
                arrowprops=dict(arrowstyle="-", color=AQUA, lw=2))
    ax.axvline(34.23, color=INK2, lw=2.2, ls=(0, (2, 3)), zorder=5)
    ax.text(34.12, top * 0.30, "34.2°S: UGIB hotspot,\nthe 2025–26 search", color=INK2, fontsize=pt(25), ha="right",
            va="bottom", linespacing=1.15)
    ax.set_xlim(30, 42.5)
    ax.set_ylim(0, top * 1.24)
    ax.set_xticks(range(30, 43, 2))
    ax.set_xticklabels([f"{v}°S" for v in range(30, 43, 2)])
    ax.set_xlabel("Latitude along the 7th arc  (further south →)", fontsize=pt(28), labelpad=12)
    ax.set_ylabel("Probability per degree", fontsize=pt(28), labelpad=12)
    legend_box(fig, [("line", BLUE, "This analysis (recommended)"),
                     ("line", AQUA, "Same, descending at 02:40"),
                     ("dash", MUTED, "Earlier version (one autopilot setting)"),
                     ("line", ORANGE, "DSTG 2016 (Australian defence)")], 200, 262, size=24)
    source(fig, "mh370-open analysis of the public Inmarsat log with ERA5 winds; DSTG (Davey et al. 2016) Fig. 10.3, digitised; "
                "curves smoothed over 0.3°")
    save(fig, "V12_satcom_profile")
    describe("V12_satcom_profile", "Chart: end-point latitude along the 7th arc (outputs/satcom/arc_profile_v2.csv; shown smoothed over 0.3 deg): "
             "recommended p_v2 (median 38.17S, 90% 36.46-39.51S, shaded; outputs/satcom/summary_v2.json), the descent-at-18:40 variant "
             "p_v2_sens_descent1840 (median 35.82S), the v1 layer p (dashed) and DSTG Fig 10.3 digitised (a 00:19:29 crossing pdf); "
             "34.23S UGIB hotspot / 2025-26 search marked. outputs/satcom/README.md section 13.")


# ---------------------------------------------------------------- V13 satcom paths
def _load_script(name):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def v13():
    from mh370 import satcom_paths as sp
    from mh370 import satcom_routes as sr
    meas = sp.build_measurements()
    atm = sp.Atmos()
    rng = np.random.default_rng(5)
    summ = json.load(open(ROOT / "outputs/satcom/summary_v2.json"))["arcprofile"]["p_v2"]
    med = -summ["median"]
    hi90, lo90 = (-v for v in summ["i90"])
    fig = new_fig()
    ax = map_ax(fig, (700, 0, 1220, H), -49.5, 12.0, lon_c=93.0)
    graticule(ax, 10, 10)
    draw_land(ax)
    draw_arc7(ax, lw=3.4, z=8)
    # single-mode families: best fit + 25 posterior paths each (baseline SMC samples re-run with ERA5)
    cols = {"LNAV": BLUE, "CTT": ORANGE}
    for m in ("LNAV", "CTT"):
        z = dict(np.load(ROOT / f"data/derived/satcom_smc/baseline_{m}.npz", allow_pickle=False))
        names = list(z["names"])
        pick = np.r_[np.argmax(z["ll"]), rng.choice(z["x"].shape[0], 25, replace=False)]
        P = {k: z["x"][pick, i] for i, k in enumerate(names)}
        o = sp.PathModel(m, meas, atm=atm).run(P, record_track=True)
        for j in range(1, pick.size):
            ax.plot(o["track_lon"][j], o["track_lat"][j], color=cols[m], lw=1.0, alpha=0.25, zorder=5)
        ax.plot(o["track_lon"][0], o["track_lat"][0], color=cols[m], lw=4, zorder=7, solid_capstyle="round")
    # waypoint family: best fit of its highest-evidence component, FMT -> MUTMI -> constant true track
    wruns = [np.load(f, allow_pickle=False) for f in
             sorted((ROOT / "data/derived/satcom_smc/routes").glob("baseline_WPT_MUTMI_CTT_n20000_s*.npz"))]
    assert wruns, "MUTMI/CTT waypoint runs missing"
    best = max(wruns, key=lambda r: float(np.max(r["ll"])))
    i = int(np.argmax(best["ll"]))
    P = {k: best["x"][i:i + 1, j] for j, k in enumerate(list(best["names"]))}
    o = sr.RouteModel("WPT", meas, mode2="CTT", wpt="MUTMI", atm=atm).run(P, record_track=True)
    ax.plot(o["track_lon"][0], o["track_lat"][0], color=AQUA, lw=4, zorder=7.5, solid_capstyle="round")
    wp = sr.load_waypoints(published_only=False)
    mlat, mlon = float(wp.loc["MUTMI", "lat_deg"]), float(wp.loc["MUTMI", "lon_deg"])
    point(ax, mlon, mlat, "waypoint\nMUTMI", color=AQUA, marker="^", s=260, dx=-1.3, ha="right", size=24, lcolor=INK2)
    # UGIB 2020 published route (descends during the 18:40 UTC = 02:40 MYT call)
    UR = _load_script("satcom_ugib_replay")
    ts = np.arange(geo.hms(18, 22, 12), geo.hms(24, 19, 29), 30.0)
    st = np.array([UR.state_at(t)[:2] for t in ts])
    ax.plot(st[:, 1], st[:, 0], color=INK, lw=3.2, ls=(0, (2.5, 1.6)), zorder=7.6)
    rad = sp.RADAR_POS
    point(ax, float(rad[1]), float(rad[0]), "Last radar\n02:22", color=INK, marker="^", s=380, dx=-1.6, ha="right", size=26)
    point(ax, 93.78, -34.23, "UGIB 2020 route → 34.2°S: fits only\nif descending at 02:40 (level: 39 Hz off)",
          color=YELLOW, s=320, dx=1.0, dy=-0.3, va="top", size=25)
    lo = arc_lon(-med)
    point(ax, lo, -med, f"Median crossing\n{med:.1f}°S", color=INK, s=320, dx=-1.1, dy=0.9, ha="right", size=26,
          weight="bold")
    ax.text(arc_lon(-25.0) + 0.8, -25.0, "7th arc", color=INK, fontsize=pt(28), fontweight="bold", zorder=12,
            path_effects=HALO)
    title(fig, "Best-fitting\npaths", None, size=58)
    fig.text(fx(80), fy(240), "One autopilot setting after the final\nturn, or a route via a published\n"
             "waypoint. Real winds.", color=INK2, fontsize=pt(28), va="top", linespacing=1.3)
    rows = [((80, 400), "Final turn", "02:32–02:40"), ((350, 400), "Speed", "~Mach 0.80"),
            ((80, 488), "7th-arc crossing", f"median {med:.1f}°S"), ((350, 488), "90% range", f"{lo90:.1f}–{hi90:.1f}°S"),
            ((80, 576), "34.2°S route", "only with a descent at 02:40")]
    for (x_, y_), a, b in rows:
        fig.text(fx(x_), fy(y_), a, color=MUTED, fontsize=pt(25), va="top")
        fig.text(fx(x_), fy(y_ + 33), b, color=INK, fontsize=pt(31), fontweight="bold", va="top")
    legend_box(fig, [("line", BLUE, "Great-circle autopilot (LNAV)"),
                     ("line", ORANGE, "Constant true track"),
                     ("line", AQUA, "Via waypoint MUTMI, then new course"),
                     ("dash", INK, "UGIB 2020 published route")], 80, 690, size=23)
    source(fig, "mh370-open analysis of the public Inmarsat log with ERA5 winds; waypoint coordinates from published "
                "aeronautical data; UGIB (2020) route")
    save(fig, "V13_satcom_paths")
    describe("V13_satcom_paths", "Map: best fit + 25 posterior paths for the LNAV and constant-true-track modes (baseline SMC samples re-run "
             "through PathModel with ERA5), the best fit of the top waypoint component FMT -> MUTMI -> constant true track "
             "(routes/baseline_WPT_MUTMI_CTT_n20000_s4*.npz re-run through satcom_routes.RouteModel), and UGIB's published route "
             "(scripts/satcom_ugib_replay.state_at). Median crossing and 90% range = p_v2 impact median 38.17S, 36.46-39.51S "
             "(outputs/satcom/summary_v2.json); FMT 18:32-18:40 UTC = 02:32-02:40 MYT; UGIB route fits only with its descent at the "
             "18:40 call (level: -39 Hz, outputs/satcom/README.md section 13.5).")


# ---------------------------------------------------------------- V14 drift profiles
def v14():
    d = pd.read_csv(ROOT / "outputs/drift/arc_profile.csv")
    ps = pd.read_csv(ROOT / "outputs/drift/profile_summary.csv")
    peaks = {r.variant: -r.peak for r in ps[ps.w == 1.0].itertuples()}
    lat = -d.arc_lat.to_numpy()
    series = [("loglik_uncalibrated", "Drifter model, uncorrected", BLUE),
              ("loglik", "Speed-corrected (default)", ORANGE),
              ("loglik_flaperon_only", "Flaperon as generic debris", AQUA),
              ("loglik_flaperon_only_leeway", "Flaperon, measured leeway", YELLOW)]
    fig = new_fig()
    title(fig, "Finding two: the drift studies disagreed for a reason",
          "Likelihood of the debris finds vs starting latitude on the arc (each scaled to its own peak)")
    ax = chart_ax(fig, 170, 250, 1560, 610)
    style_chart(ax)
    lab_y = {"loglik_uncalibrated": 1.13, "loglik": 1.13, "loglik_flaperon_only": 1.25, "loglik_flaperon_only_leeway": 1.13}
    for key, lab, col in series:
        y = np.exp(d[key].to_numpy() - np.nanmax(d[key].to_numpy()))
        ax.plot(lat, y, color=col, lw=4 if key in ("loglik", "loglik_flaperon_only_leeway") else 3, zorder=3,
                solid_capstyle="round")
        pk = peaks[key]
        ax.plot([pk, pk], [1.0, lab_y[key] - 0.03], color=col, lw=2, zorder=2)
        ax.text(pk, lab_y[key], f"{pk:.1f}°S", color=INK, fontsize=pt(28), fontweight="bold", ha="center", va="bottom")
        assert abs(lat[np.nanargmax(y)] - pk) <= 0.3, (key, lat[np.nanargmax(y)], pk)
    ax.set_xlim(20, 42)
    ax.set_ylim(0, 1.42)
    ax.set_yticks([0, 0.5, 1.0])
    ax.set_yticklabels(["0", "½", "peak"])
    ax.set_xticks(range(20, 43, 4))
    ax.set_xticklabels([f"{v}°S" for v in range(20, 43, 4)])
    ax.set_xlabel("Starting latitude on the 7th arc  (further south →)", fontsize=pt(28), labelpad=12)
    ax.set_ylabel("Relative likelihood", fontsize=pt(28), labelpad=12)
    legend_box(fig, [("line", c, l) for _, l, c in series], 200, 280, size=24)
    source(fig, "mh370-open analysis of NOAA Global Drifter Program data and the public debris finds; "
                "CSIRO flaperon leeway trials")
    save(fig, "V14_drift_profiles")
    describe("V14_drift_profiles", "Chart: four drift likelihood profiles along the arc, each exp(loglik - max): uncorrected (peak 29.4S), default "
             "speed-corrected (33.4S), flaperon-only generic (30.1S), flaperon with CSIRO leeway (38.1S). outputs/drift/arc_profile.csv, profile_summary.csv.")


# ---------------------------------------------------------------- V15 drift speed
def v15():
    v = json.load(open(ROOT / "outputs/drift/validation.json"))["west_of_60E"]
    rows = [("Real drifters (held out)", v["median_days_drifters"], INK),
            ("Drifter-based model, raw", v["median_days_chain"], ORANGE),
            ("Model after speed correction", v["median_days_chain_calibrated"], BLUE)]
    fig = new_fig()
    title(fig, "The drift model was too slow",
          "Median days for debris starting near the 7th arc to drift west of 60°E")
    ax = chart_ax(fig, 560, 250, 1180, 450)
    style_chart(ax, grid_axis="x")
    for i, (lab, val, col) in enumerate(rows):
        y = 2 - i
        ax.barh(y, val, height=0.32, color=col, zorder=3)
        ax.text(val + 12, y, f"{val:.0f} days", color=INK, fontsize=pt(34), fontweight="bold", va="center")
        fig.text(fx(530), fy(250 + 450 * (1 - (y + 0.6) / 3.2)), lab, color=INK2, fontsize=pt(30), ha="right",
                 va="center")
    ax.set_yticks([])
    ax.set_xlim(0, 820)
    ax.set_ylim(-0.6, 2.6)
    ax.set_xticks([0, 200, 400, 600, 800])
    ax.set_xlabel("Days", fontsize=pt(28), labelpad=10)
    ratio = v["median_days_chain"] / v["median_days_drifters"]
    fig.text(fx(560), fy(820), f"Raw model takes {ratio:.2f}× as long → about 20% too slow (fitted correction ×1.20)",
             color=INK, fontsize=pt(32), fontweight="bold", va="top")
    source(fig, "mh370-open analysis of NOAA Global Drifter Program data (416 held-out drifters, Kaplan–Meier medians)")
    save(fig, "V15_drift_speed")
    describe("V15_drift_speed", f"Bar chart: median transit arc->60E, held-out drifters {v['median_days_drifters']:.0f} d, raw chain "
             f"{v['median_days_chain']:.0f} d, calibrated {v['median_days_chain_calibrated']:.0f} d (outputs/drift/validation.json); ~20% too slow, f = 1.20.")


# ---------------------------------------------------------------- V16 acoustic timing
def v16():
    def s(h, m, sec=0):  # seconds after 00:00 UTC 8 Mar
        return h * 3600 + m * 60 + sec
    fig = new_fig()
    title(fig, "Finding three: the timing test",
          "If a sound came from an impact on the 7th arc, when did that impact happen?")
    ax = chart_ax(fig, 560, 260, 1260, 560)
    style_chart(ax, grid_axis="x")
    lo_w, hi_w = s(0, 19, 30), s(0, 25)
    ax.axvspan(lo_w, hi_w, color=AQUA, alpha=0.22, lw=0, zorder=1)
    ax.text((lo_w + hi_w) / 2, 2.62, "Possible impact\ntime", color=INK, fontsize=pt(26), ha="center", va="bottom")
    ax.axvline(s(0, 19, 29), color=INK2, lw=1.5, zorder=2)
    # Kadri 306 deg: implied on-arc origin 00:36:34 (c 1.47-1.49: 00:36:27-00:36:42)
    k0, k1, kc = s(0, 36, 27), s(0, 36, 42), s(0, 36, 34)
    ax.plot([k0, k1], [2, 2], color=INK, lw=6, solid_capstyle="round", zorder=4)
    ax.scatter([kc], [2], s=340, c=ORANGE, edgecolors=BG, linewidths=2.5, zorder=5)
    ax.annotate("", xy=(hi_w, 1.72), xytext=(kc, 1.72), arrowprops=dict(arrowstyle="<->", color=INK, lw=2,
                                                                         mutation_scale=22), zorder=5)
    ax.text((hi_w + kc) / 2, 1.62, "11.5–17 min too late", color=INK, fontsize=pt(30), fontweight="bold", ha="center",
            va="top")
    ax.text((hi_w + kc) / 2, 1.30, "heard at Cape Leeuwin 08:54:30; an arc impact\nwould arrive 08:37:17–08:43:02",
            color=INK2, fontsize=pt(24), ha="center", va="top", linespacing=1.25)
    ax.text(s(0, 19, 29) - 15, 2.62, "last satellite\nmessage 08:19", color=INK2, fontsize=pt(24), ha="right",
            va="bottom")
    # Stead 246.9: implied 00:18:52-00:19:19, +/-2 deg bearing 00:15:39-00:21:41
    ax.plot([s(0, 15, 39), s(0, 21, 41)], [1, 1], color=MUTED, lw=3, zorder=3, solid_capstyle="round")
    ax.plot([s(0, 18, 52), s(0, 19, 19)], [1, 1], color=INK, lw=8, zorder=4, solid_capstyle="round")
    ax.scatter([s(0, 19, 5)], [1], s=340, c=AQUA, edgecolors=BG, linewidths=2.5, zorder=5)
    ax.text(s(0, 21, 50), 0.62, "fits — but nothing on open\nsensors backs it up", color=INK, fontsize=pt(28),
            fontweight="bold", va="top", path_effects=HALO)
    fig.text(fx(530), fy(260 + 560 * (1 - (2 + 0.3) / 3.3)), "Kadri 2024\nbearing 306°", color=INK2,
             fontsize=pt(30), ha="right", va="center")
    fig.text(fx(530), fy(260 + 560 * (1 - (1 + 0.3) / 3.3)), "Stead / LANL 2014\nbearing 246.9°", color=INK2,
             fontsize=pt(30), ha="right", va="center")
    ax.set_ylim(-0.3, 3.0)
    ax.set_yticks([])
    ticks = [s(0, m) for m in range(10, 46, 5)]
    ax.set_xticks(ticks)
    ax.set_xticklabels([utc_to_myt(0, m) for m in range(10, 46, 5)])
    ax.set_xlim(s(0, 12), s(0, 43))
    ax.set_xlabel("Implied impact time, Malaysian time (8 March)", fontsize=pt(28), labelpad=12)
    source(fig, "mh370-open analysis of published Cape Leeuwin (CTBTO HA01) arrival picks; sound speed 1.47–1.49 km/s; "
                "Stead whisker = ±2° bearing")
    save(fig, "V16_acoustic_timing")
    describe("V16_acoustic_timing", "Chart: implied on-arc impact time for the Kadri 306.18 deg pick (00:36:34 UTC = 08:36 MYT, range 00:36:27-00:36:42) "
             "vs the assumed impact window 00:19:30-00:25 UTC -> 11.5-17 min late; Stead 246.9 deg implied 00:18:52-00:19:19 (+/-2 deg: 00:15:39-00:21:41) "
             "-> fits. Footer: HA01 arrival 00:54:30 vs predicted 00:37:17-00:43:02 UTC. All from outputs/acoustic/README.md, shown in MYT.")


# ---------------------------------------------------------------- V17 spectrogram
def v17():
    from scipy import signal
    from mh370 import acoustic as A
    w = A.recording_windows("PAKIM", A.hms8(1, 31), A.hms8(1, 33), full=True)[0]
    t0, fs, p, rec = A.read_pressure(w[2], "PAKIM", 1000.0, full=True)
    f, ts, Sg = signal.spectrogram(p, fs, nperseg=2000, noverlap=1800)
    Sg = 10 * np.log10(Sg + 1e-30)
    picks = json.load(open(ROOT / "outputs/acoustic/kimberley_picks.json"))
    tb = A.hms8(1, 30)
    x = (t0 + ts - tb)
    fig = new_fig()
    title(fig, "What the Kimberley recorder heard",
          "The 2014 Curtin event window, IMOS recorder off north-west Australia, 8 March 2014")
    ax = chart_ax(fig, 170, 290, 1580, 560)
    style_chart(ax, grid_axis=None)
    k = (f >= 2) & (f <= 100)
    vmin, vmax = np.percentile(Sg[k], 10), np.percentile(Sg[k], 99.8)
    ax.pcolormesh(x, f[k], Sg[k], shading="auto", cmap="cividis", vmin=vmin, vmax=vmax, rasterized=True, zorder=1)
    xl0, xl1 = 125, 300
    ax.set_xlim(xl0, xl1)
    ax.set_ylim(2, 100)

    def tsec(key):
        hh, mm, ss = picks[key].split(":")
        return A.hms8(int(hh), int(mm), float(ss)) - tb
    t1, t2, t3 = tsec("F1 20-60 Hz burst onset"), tsec("F2 broadband impulsive onset"), tsec("F3 reaches +15 dB after F2")
    t3_end = A.hms8(1, 34, 55) - tb   # plateau to ~01:34:55 (outputs/acoustic/README.md)
    for tx, lab, al, dx in ((t1, "Whale-like call", "right", 1.5), (t2, "Knock on the mooring", "left", -1.0)):
        ax.annotate(lab, xy=(tx + (2.0 if al == "right" else 0.3), 101), xytext=(tx + dx, 112), color=INK, fontsize=pt(28),
                    fontweight="bold", ha=al, va="bottom", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-|>", color=INK, lw=2, mutation_scale=20))
    ax.annotate("", xy=(t3, 104), xytext=(t3_end, 104), annotation_clip=False,
                arrowprops=dict(arrowstyle="|-|", color=INK, lw=2, mutation_scale=8))
    ax.text((t3 + t3_end) / 2, 108, "Earthquake sound (T-phase) from the Java quake", color=INK, fontsize=pt(28),
            fontweight="bold", ha="center", va="bottom")
    tick_s = np.arange(xl0 - xl0 % 15 + 15, xl1 + 1, 30)
    ax.set_xticks(tick_s)
    lbl = []
    for sec in tick_s:
        tt = 9 * 3600 + 30 * 60 + sec
        lbl.append(f"{int(tt // 3600):02d}:{int(tt % 3600 // 60):02d}:{int(tt % 60):02d}")
    ax.set_xticklabels(lbl)
    ax.set_xlabel("Malaysian time (UTC+8)", fontsize=pt(28), labelpad=12)
    ax.set_ylabel("Frequency (Hz)", fontsize=pt(28), labelpad=12)
    cax = fig.add_axes([fx(1770), fy(850), 18 / W, 560 / H])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=mcolors.Normalize(vmin, vmax), cmap="cividis"), cax=cax)
    cb.outline.set_visible(False)
    cb.set_ticks([])
    fig.text(fx(1800), fy(290), "louder", color=MUTED, fontsize=pt(20), va="top")
    fig.text(fx(1800), fy(850), "quieter", color=MUTED, fontsize=pt(20), va="bottom")
    source(fig, "IMOS passive acoustic data, Kimberley recorder (AODN, CC BY 4.0; IMOS is enabled by NCRIS); "
                "mh370-open analysis, 2-s spectrogram windows")
    save(fig, "V17_spectrogram")
    describe("V17_spectrogram", "Spectrogram (2-100 Hz, 2-s windows) of the IMOS PAKIM file starting 01:30 UTC (09:30 MYT), reread with "
             "src/mh370/acoustic.read_pressure; annotations at the picks in outputs/acoustic/kimberley_picks.json: whale-like burst "
             "01:32:56.5, mooring knock 01:33:04.5, Java-earthquake T-phase from +15 dB at 01:33:39 to the plateau end ~01:34:55 UTC.")


# ---------------------------------------------------------------- V18 WSPR physics
def v18():
    fig = new_fig()
    title(fig, "Finding four: WSPR has a physics problem", "Size of a signal change, in decibels (log scale)")
    ax = chart_ax(fig, 640, 240, 1120, 450)
    style_chart(ax, grid_axis="x")
    rows = [("Largest change a 777 can\nplausibly make", 0.03, None, ORANGE, "~0.03 dB"),
            ("Smallest step WSPR\nreports", 1.0, None, MUTED, "1 dB"),
            ("Natural jump between\nreadings on one link", 3.5, 5.0, MUTED, "3.5–5 dB")]
    base = 0.01
    for i, (lab, v0, v1, col, txt) in enumerate(rows):
        y = 2 - i
        ax.barh(y, v0 - base, left=base, height=0.34, color=col, zorder=3)
        if v1:
            ax.barh(y, v1 - v0, left=v0, height=0.34, color=col, alpha=0.45, zorder=3)
        ax.text((v1 or v0) * 1.18, y, txt, color=INK, fontsize=pt(36), fontweight="bold", va="center")
        fig.text(fx(610), fy(240 + 450 * (1 - (y + 0.6) / 3.2)), lab, color=INK2, fontsize=pt(30), ha="right",
                 va="center", linespacing=1.2)
    ax.set_xscale("log")
    ax.set_xlim(base, 30)
    ax.set_ylim(-0.6, 2.6)
    ax.set_yticks([])
    ax.set_xticks([0.01, 0.1, 1, 10])
    ax.set_xticklabels(["0.01", "0.1", "1", "10"])
    ax.set_xlabel("Decibels (log scale)", fontsize=pt(28), labelpad=10)
    fig.text(fx(640), fy(805), "The aircraft's effect is ~30× smaller than one reporting step\nand ~100× smaller than the natural noise.",
             color=INK, fontsize=pt(32), fontweight="bold", va="top", linespacing=1.3)
    source(fig, "mh370-open radar link-budget estimate; WSPR signal statistics from wspr.live (wsprnet.org data)")
    save(fig, "V18_wspr_physics")
    describe("V18_wspr_physics", "Log-scale bars: physics-max SNR change ~0.03 dB (777 near a transmitter), WSPR 1 dB reporting step, "
             "natural slot-to-slot variability 3.5-5 dB. research_notes/MH370 open data search avenues/wspr_physics_and_blind_test.md.")


# ---------------------------------------------------------------- V19 WSPR coverage
WSPR_SRC = DATA / "mh370_window.csv"  # optional uncompressed extract; the gzipped copy below is what ships
WSPR_GZ = DATA / "wspr_mh370_window_2014-03-07T16_2014-03-08T01.csv.gz"


def wspr_rows():
    if not WSPR_GZ.exists():
        with open(WSPR_SRC, "rb") as fi, gzip.open(WSPR_GZ, "wb") as fo:
            fo.write(fi.read())
    with gzip.open(WSPR_GZ, "rt") as fh:
        return list(csv.DictReader(fh))


def gc_points(lat1, lon1, lat2, lon2, n=60):
    p1, l1, p2, l2 = map(math.radians, (lat1, lon1, lat2, lon2))
    d = 2 * math.asin(math.sqrt(math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin((l2 - l1) / 2) ** 2))
    if d == 0:
        return [(lat1, lon1)]
    out = []
    for i in range(n + 1):
        f = i / n
        a, b = math.sin((1 - f) * d) / math.sin(d), math.sin(f * d) / math.sin(d)
        x = a * math.cos(p1) * math.cos(l1) + b * math.cos(p2) * math.cos(l2)
        y = a * math.cos(p1) * math.sin(l1) + b * math.cos(p2) * math.sin(l2)
        z = a * math.sin(p1) + b * math.sin(p2)
        out.append((math.degrees(math.atan2(z, math.hypot(x, y))), math.degrees(math.atan2(y, x))))
    return out


def wspr_hourly():
    import collections
    rows = wspr_rows()
    txc = collections.Counter(r["tx_sign"] for r in rows)
    box = (-40, -20, 85, 105)
    spots = collections.Counter(r["time"][:13] for r in rows)
    cross = collections.Counter()
    hits = []
    cache = {}
    for r in rows:
        if txc[r["tx_sign"]] < 3:
            continue
        key = (r["tx_lat"], r["tx_lon"], r["rx_lat"], r["rx_lon"])
        if key not in cache:
            pts = gc_points(float(r["tx_lat"]), float(r["tx_lon"]), float(r["rx_lat"]), float(r["rx_lon"]))
            cache[key] = any(box[0] <= la <= box[1] and box[2] <= lo <= box[3] for la, lo in pts)
        if cache[key]:
            cross[r["time"][:13]] += 1
            hits.append(r)
    hours = sorted(spots)
    tab = pd.DataFrame({"hour_utc": hours, "spots_worldwide": [spots[h] for h in hours],
                        "spots_short_path_crossing_box": [cross.get(h, 0) for h in hours]})
    tab.to_csv(DATA / "wspr_hourly.csv", index=False)
    pd.DataFrame(hits).to_csv(DATA / "wspr_box_crossings.csv", index=False)
    last = max(r["time"] for r in hits)
    return tab, last


def v19():
    tab, last = wspr_hourly()
    assert last.endswith("23:06:00"), last
    hrs = [int(h[11:13]) for h in tab.hour_utc]
    myt = [(h + 8) % 24 for h in hrs]
    x = np.arange(len(hrs))
    fig = new_fig()
    title(fig, "What the WSPR network could see that night", "Amateur-radio beacon reports per hour, 8 March 2014")
    a1 = chart_ax(fig, 170, 240, 1560, 260)
    style_chart(a1)
    a1.bar(x, tab.spots_worldwide / 1000, width=0.55, color=BLUE, zorder=3)
    a1.set_xticks(x)
    a1.set_xticklabels([])
    a1.set_ylim(0, 20)
    a1.set_yticks([0, 10, 20])
    a1.set_yticklabels(["0", "10k", "20k"])
    a1.set_ylabel("Reports\nworldwide", fontsize=pt(26), labelpad=12)
    a2 = chart_ax(fig, 170, 560, 1560, 300)
    style_chart(a2)
    vals = tab.spots_short_path_crossing_box.to_numpy()
    a2.bar(x, vals, width=0.55, color=ORANGE, zorder=3)
    for xi, v in zip(x, vals):
        a2.text(xi, v + 0.25, f"{v}", color=INK, fontsize=pt(28), fontweight="bold", ha="center", va="bottom")
    a2.set_ylim(0, 6.5)
    a2.set_yticks([0, 2, 4, 6])
    a2.set_ylabel("Reports on links\nover the southern arc", fontsize=pt(26), labelpad=12)
    a2.set_xticks(x)
    a2.set_xticklabels([f"{m:02d}:00" for m in myt])
    a2.set_xlabel("Hour starting, Malaysian time", fontsize=pt(28), labelpad=10)
    a2.axvline(x[-1] - 0.5, color=INK, lw=0)
    i7 = myt.index(7)
    a2.text(i7, 1.9, "last one\n07:06", color=INK, fontsize=pt(26), fontweight="bold", ha="center", va="bottom")
    i8 = myt.index(8)
    a2.text(i8, 0.95, "7th arc\n08:19:\nnone", color=INK, fontsize=pt(26), fontweight="bold", ha="center", va="bottom")
    source(fig, "wspr.live (raw wsprnet.org spots), queried 5 Nov 2026; mh370-open analysis of links crossing "
                "40–20°S, 85–105°E")
    save(fig, "V19_wspr_coverage")
    describe("V19_wspr_coverage", "Two-panel bars by hour (16:00-00:59 UTC = 00:00-08:59 MYT): worldwide WSPR spots, and spots on short-path links "
             "crossing the southern-arc box 40-20S 85-105E (TX seen >=3x). Last crossing 23:06 UTC (07:06 MYT). Recomputed from the wspr.live extract "
             "(copied to video/data/), tables video/data/wspr_hourly.csv and wspr_box_crossings.csv.")


# ---------------------------------------------------------------- V20 searched vs unsearched
@lru_cache(None)
def mix_summary():
    return pd.read_csv(ROOT / "outputs/combine/scenario_summary_mix.csv")


def mix_row(w=0.5, pod="best", eps=0.1, broad="broad_arc", sat="p_v2"):
    s = mix_summary()
    r = s[(s.sat_var == sat) & (s.broad == broad) & (s.eps == eps) & (s.w == w) & (s.pod_bound == pod)]
    assert len(r) == 1, (sat, broad, eps, w, pod, len(r))
    return r.iloc[0]


@lru_cache(None)
def sat_mass_on_searched_ground(var="p_v2", pod_cut=0.5):
    """share of the satellite layer (before any search subtraction) on cells with POD > pod_cut"""
    sat = xr.open_dataset(ROOT / "data/derived/satcom_posterior.nc", engine="h5netcdf")[var].values
    pod = xr.open_dataset(ROOT / "data/derived/search_pod.nc", engine="h5netcdf")["pod"].values
    p = np.nan_to_num(np.asarray(sat, float))
    return float((p * (np.nan_to_num(pod) > pod_cut)).sum() / p.sum())


def stat_tile(fig, x, y, w, h, big, text, accent=YELLOW):
    fig.add_artist(FancyBboxPatch((fx(x), fy(y + h)), w / W, h / H, boxstyle="round,pad=0,rounding_size=0.01",
                                  fc=PANEL, ec="none", transform=fig.transFigure))
    fig.add_artist(Rectangle((fx(x), fy(y + h)), 10 / W, h / H, fc=accent, ec="none", transform=fig.transFigure))
    t = fig.text(fx(x + 44), fy(y + h / 2), big, color=INK, fontsize=pt(92), fontweight="bold", va="center", ha="left")
    right = t.get_window_extent(renderer=fig.canvas.get_renderer()).x1   # display px (dpi 100 = pixels)
    fig.text(right / W + 36 / W, fy(y + h / 2), text, color=INK2, fontsize=pt(27), va="center", ha="left",
             linespacing=1.3)


def v20():
    on_searched = sat_mass_on_searched_ground()
    n0, n5 = mix_row(w=0).p_null_given_sat, mix_row(w=0.5).p_null_given_sat
    assert abs(on_searched - 0.86) < 0.005 and abs(n0 - 0.166) < 0.001 and abs(n5 - 0.059) < 0.001
    fig = new_fig()
    title(fig, "The uncomfortable part", "Every search so far came up empty. What does that say about the model?")
    stat_tile(fig, 80, 230, 850, 200, f"{on_searched:.0%}",
              "of the satellite-data probability\nsat on seabed that has since been\nsearched, mostly in 2014–17")
    stat_tile(fig, 990, 230, 850, 200, f"{n5 * 100:.0f}–{n0:.0%}",
              "chance every search misses,\nif the satellite model were right\n"
              f"({n0:.0%} satellite only, {n5:.0%} with drift)")
    # where is the wreck now: conditional on the satellite model vs the mixture (default settings)
    top, hh = 620, 250
    fig.text(fx(80), fy(505), "Where is the wreck now?\n(default settings)", color=INK, fontsize=pt(34), fontweight="bold",
             va="top", linespacing=1.15)
    ax = chart_ax(fig, 640, top, 1160, hh)
    ax.set_facecolor(BG)
    for sp_ in ax.spines.values():
        sp_.set_visible(False)
    rows = [("If the satellite model is right", "p_unsearched_given_sat"),
            ("Allowing that it may be wrong", "p_unsearched_mixture")]
    bh = 0.46
    for i, (lab, col) in enumerate(rows):
        r = {b_: mix_row(w=0.5, pod=b_) for b_ in ("best", "low", "high")}
        un = float(r["best"][col])
        y = 1 - i
        ax.barh(y, un, height=bh, color=BLUE, zorder=3)
        ax.barh(y, 1 - un - 0.004, left=un + 0.004, height=bh, color=ORANGE, zorder=3)
        lo_b, hi_b = float(r["low"][col]), float(r["high"][col])
        yy = y + bh / 2 + 0.11
        ax.plot([lo_b, hi_b], [yy, yy], color=INK, lw=2.5, zorder=5)
        for xb in (lo_b, hi_b):
            ax.plot([xb, xb], [yy - 0.06, yy + 0.06], color=INK, lw=2.5, zorder=5)
        ax.text(un / 2, y, f"{un:.0%}", color=INK, fontsize=pt(34), fontweight="bold", ha="center", va="center", zorder=6)
        ax.text(un + (1 - un) / 2, y, f"{1 - un:.0%}", color=INK, fontsize=pt(34), fontweight="bold", ha="center",
                va="center", zorder=6)
        fig.text(fx(610), fy(top + hh * (1 - (y + 0.5) / 2.0)), lab, color=INK2, fontsize=pt(30), ha="right", va="center")
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 1.5)
    ax.set_xticks([])
    ax.set_yticks([])
    legend_box(fig, [("solid", BLUE, "In ground never searched"),
                     ("solid", ORANGE, "In searched ground, but missed")], 900, 500, size=25)
    xw = 1360
    fig.add_artist(plt.Line2D([fx(xw), fx(xw + 44)], [fy(530), fy(530)], color=INK, lw=2.5, transform=fig.transFigure))
    for xb in (xw, xw + 44):
        fig.add_artist(plt.Line2D([fx(xb), fx(xb)], [fy(522), fy(538)], color=INK, lw=2.5, transform=fig.transFigure))
    fig.text(fx(xw + 60), fy(530), "range if past searches were\nless / more thorough", color=INK2, fontsize=pt(24),
             va="center", linespacing=1.15)
    source(fig, SRC_COMBINED)
    save(fig, "V20_searched_vs_unsearched")
    rb = mix_row(w=0.5)
    describe("V20_searched_vs_unsearched", f"Two stat tiles + two 100% stacked bars. Tiles: {on_searched:.3f} of satcom p_v2 lies on cells "
             f"with POD > 0.5 (data/derived/satcom_posterior.nc x search_pod.nc); P(all searches miss | satellite model) "
             f"{n0:.3f} (w=0) / {n5:.3f} (w=0.5), POD best. Bars at the recommended default ({MIX_SCEN}): P(wreck in unsearched "
             f"ground) {rb.p_unsearched_given_sat:.3f} if the satellite model is right vs {rb.p_unsearched_mixture:.3f} under the "
             "mixture; whiskers = POD low/high. outputs/combine/scenario_summary_mix.csv, RESULTS_mix.md section 1.")


# ---------------------------------------------------------------- V26 model wrong
def v26():
    r = mix_row(w=0.5)
    steps = [("Starting\nassumption", float(r.eps), "1 in 10"),
             ("After the\ndebris drift", float(r.eps_after_drift), "about 1 in 6"),
             ("After every search\ncame up empty", float(r.eps_post), "nearly 1 in 2")]
    assert abs(steps[0][1] - 0.1) < 1e-9 and abs(steps[1][1] - 0.175) < 0.001 and abs(steps[2][1] - 0.462) < 0.001
    fig = new_fig()
    fig.text(fx(80), fy(58), "How much the evidence moves belief toward\n‘the model is wrong somewhere’", color=INK,
             fontsize=pt(50), fontweight="bold", va="top", ha="left", linespacing=1.12)
    ax = chart_ax(fig, 260, 250, 1400, 500)
    style_chart(ax)
    x = np.arange(3)
    ax.bar(x, [s[1] for s in steps], width=0.5, color=YELLOW, zorder=3)
    for xi, (_, v, words) in zip(x, steps):
        ax.text(xi, v + 0.012, f"{v * 100:.3g}%", color=INK, fontsize=pt(44), fontweight="bold", ha="center", va="bottom")
        ax.text(xi, v + 0.088, words, color=INK2, fontsize=pt(27), ha="center", va="bottom")
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(0, 0.6)
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax.set_yticklabels(["0", "10%", "20%", "30%", "40%", "50%"])
    ax.set_xticks(x)
    ax.set_xticklabels([s[0] for s in steps], fontsize=pt(30), color=INK, linespacing=1.15)
    ax.set_ylabel("Weight on ‘model is wrong’", fontsize=pt(28), labelpad=14)
    fig.text(fx(260), fy(892), "The alternative: the plane ended anywhere along the 7th arc between 20°S and 42°S. "
             "Drift weight 0.5; best-estimate search thoroughness.", color=MUTED, fontsize=pt(22), va="bottom")
    source(fig, SRC_COMBINED)
    save(fig, "V26_model_wrong")
    describe("V26_model_wrong", f"Bar chart: posterior weight of the broad 'model is wrong' component (broad_arc, 7th-arc crossing uniform "
             f"20-42S with the satcom end-of-flight kernel) at the recommended default {MIX_SCEN}: prior eps 0.1 -> after drift "
             f"{r.eps_after_drift:.3f} -> after the null searches {r.eps_post:.3f}. outputs/combine/scenario_summary_mix.csv / "
             "RESULTS_mix.md section 2; outputs/combine/README.md 'Model-misspecification mixture'.")


# ---------------------------------------------------------------- V21 results map
def area_callouts(ax, spec, size=28, badge=28):
    """spec: {key: (dlon, dlat, ha, text)} -> badge + text at an offset, leader line to the block centre."""
    for L, (dx, dy, ha, text) in spec.items():
        a = areas()[L]
        r, col = a["row"], a["colour"]
        x, y = r.centre_lon + dx, r.centre_lat + dy
        ax.plot([r.centre_lon, x], [r.centre_lat, y], color=col, lw=1.8, zorder=15)
        ax.text(x, y, L, color=BG, fontsize=pt(badge), fontweight="bold", ha="center", va="center", zorder=17,
                bbox=dict(boxstyle="circle,pad=0.25", fc=col, ec=BG, lw=2))
        off = 0.62 * (1 if ha == "left" else -1)
        ax.text(x + off, y, text, color=INK, fontsize=pt(size), fontweight="bold", ha=ha, va="center", zorder=16,
                path_effects=HALO, linespacing=1.15)


def area_pct(L):
    return f"{areas()[L]['row'].mass:.1%}"


def draw_oi_remaining(ax, label=None, z=10, **kw):
    ring, _ = oi_remaining()
    ax.plot(ring[:, 0], ring[:, 1], color=INK2, lw=2.0, ls=(0, (2, 2)), zorder=z)
    if label:
        cl = ring.mean(0)
        ax.annotate(label, xy=(cl[0], cl[1]), zorder=z + 2, color=INK2, path_effects=HALO,
                    arrowprops=dict(arrowstyle="-", color=INK2, lw=1.5), **kw)


def v21():
    fig = new_fig()
    ax = map_ax(fig, (0, 0, W, H), -42.4, -27.4, lon_c=91.0)
    graticule(ax, 5, 5)
    draw_heat(ax, "mix")
    draw_land(ax)
    draw_search(ax, mode="mono")
    draw_arc7(ax, lw=2.6, label="7th arc", label_lat=-40.9, dx=-0.6, ha="right")
    draw_oi_remaining(ax, "Ocean Infinity contract strip\nstill to search: almost no probability",
                      xytext=(89.4, -30.9), fontsize=pt(23), ha="center", va="center")
    point(ax, 99.934, -29.128, "WSPR claim", color=INK2, s=110, dx=0.35, dy=0.25, size=22, lcolor=INK2)
    draw_areas(ax, which="RS123", label=False)

    def lab(L):
        r = areas()[L]["row"]
        return f"{centre_txt(r)}\nholds {area_pct(L)}"
    area_callouts(ax, {"1": (3.4, -0.55, "left", lab("1")),
                       "3": (4.1, -1.25, "left", lab("3")),
                       "2": (3.6, -0.75, "left", lab("2")),
                       "R": (-3.1, 2.3, "right", "Re-search block\n" + centre_txt(areas()["R"]["row"])),
                       "S": (-2.6, 1.4, "right", "Satellite-only pick\n" + centre_txt(areas()["S"]["row"]))}, size=27)
    title(fig, "Where the probability is now", "Top three unsearched areas, each ≈ 7,500 km²", box=True)
    heat_legend(fig, 80, 215, label="Probability left after past searches")
    legend_box(fig, [("outline", INK2, "Already searched (2014–2026)"),
                     ("outline", AREA, "Areas 1–3 (default settings)"),
                     ("outline", SATONLY, "Satellite-only pick (drift set aside)"),
                     ("outline", RESEARCH, "Re-search block (dashed)")], 80, 300, size=24)
    source(fig, SRC_COMBINED)
    save(fig, "V21_results_map")
    describe("V21_results_map", f"Results map: heat = post_mix (data/derived/combined_posterior_mix.nc, recommended default {MIX_SCEN}), "
             "searched polygons (outlines), 7th arc, OI contract remaining strip (post_mix mass ~1e-5), WSPR point; areas 1-3 = rank 1-3 "
             "unsearched 7,500 km2 blocks at the default (mixture mass 0.085 / 0.051 / 0.040), satellite-only pick = rank-1 unsearched "
             "block at w=0 (39.94S 84.82E), re-search block = rank-1 any-ground block at the default (37.91S 88.69E, 0.108). "
             "outputs/combine/ranked_blocks_mix.csv, RESULTS_mix.md section 2.")


# ---------------------------------------------------------------- V22 area cards
CARDS = [("1", "V22a_area_1"), ("2", "V22b_area_2"), ("3", "V22c_area_3"), ("S", "V22d_satellite_only")]


def v22():
    for old in OUTV.glob("V22*.png"):          # drop cards from earlier versions (e.g. areas A-D)
        if old.stem not in {c[1] for c in CARDS}:
            old.unlink()
            print("removed", old.relative_to(ROOT))
    for L, name in CARDS:
        a = areas()[L]
        r = a["row"]
        fig = new_fig()
        span = 6.0
        ax = map_ax(fig, (0, 0, 1130, H), r.centre_lat - span / 2, r.centre_lat + span / 2, lon_c=r.centre_lon)
        graticule(ax, 1, 1, size=18)
        draw_heat(ax, a["heat"])
        draw_land(ax)
        draw_search(ax, mode="mono")
        draw_arc7(ax, lw=3)
        lo0, lo1, la0, la1 = ax._ext
        others = [k for k in "123SR" if k != L and lo0 + 0.5 < areas()[k]["row"].centre_lon < lo1 - 0.5
                  and la0 + 0.4 < areas()[k]["row"].centre_lat < la1 - 0.4]
        draw_areas(ax, which=others, lw=1.8, size=24, z=13)
        draw_areas(ax, which=L, lw=4.5, size=44)
        if L == "1":
            point(ax, 99.934, -29.128, "WSPR claim\n(not used here)", color=INK2, s=150, dx=0.18, dy=0.0, size=22,
                  lcolor=INK2)
        # arc label where the arc crosses the top or bottom of the view
        placed = False
        for la_lab in (la1 - 0.35, la0 + 0.35):
            lo_a = arc_lon(la_lab)
            if lo0 + 0.3 < lo_a < lo1 - 0.8:
                ax.text(lo_a + 0.12, la_lab, "7th arc", color=INK, fontsize=pt(26), fontweight="bold", va="center",
                        zorder=12, path_effects=HALO)
                placed = True
                break
        if not placed:  # label where the arc leaves the left edge
            a7 = arc7()
            lo_a = lo0 + 0.5
            la_a = float(np.interp(lo_a, a7[:, 1], a7[:, 0]))
            ax.text(lo_a, la_a + 0.18, "7th arc", color=INK, fontsize=pt(26), fontweight="bold", va="bottom",
                    zorder=12, path_effects=HALO)
        x0 = 1190
        head = f"Area {L}" if L in "123" else "Satellite-only pick"
        fig.text(fx(x0), fy(60), head, color=a["colour"], fontsize=pt(88 if L in "123" else 62), fontweight="bold",
                 va="top")
        fig.text(fx(x0), fy(185), a["title"], color=INK, fontsize=pt(29), fontweight="bold", va="top", linespacing=1.2)
        if L == "S":
            share = f"{r.mass:.0%} with drift set aside"
        else:
            share = f"{r.mass:.1%}"
        rows = [("Centre", centre_txt(r)),
                ("Latitude", ranges_txt(r)[0]),
                ("Longitude", ranges_txt(r)[1]),
                ("Beyond the arc", f"{r.n0_km:+.0f} to {r.n1_km:+.0f} km"),
                ("Previously searched", f"{r.frac_previously_searched:.0%} of the box"),
                ("Share of remaining probability", share)]
        yy = 272
        for k_, v_ in rows:
            fig.text(fx(x0), fy(yy), k_, color=MUTED, fontsize=pt(24), va="top")
            fig.text(fx(x0), fy(yy + 31), v_, color=INK, fontsize=pt(35), fontweight="bold", va="top")
            yy += 85
        import textwrap
        fig.text(fx(x0), fy(yy + 6), textwrap.fill(a["why"], 52), color=INK2, fontsize=pt(24), va="top", linespacing=1.22)
        source(fig, SRC_COMBINED)
        save(fig, name)
        scen = SATONLY_SCEN if L == "S" else MIX_SCEN
        describe(name, f"Card for {head}: zoomed map (heat {'post_mix_broad_arc_eps0p1_w0' if L == 'S' else 'post_mix'}, searched "
                 f"outlines, arc, block, neighbouring blocks thin) + centre {centre_txt(r)}, lat/lon range, "
                 f"n {r.n0_km:+.0f}..{r.n1_km:+.0f} km, previously searched {r.frac_previously_searched:.3f}, mixture mass {r.mass:.4f}"
                 + (f" (default-setting mass of this box 0.0162, RESULTS_mix.md section 4)" if L == "S" else "")
                 + f". outputs/combine/ranked_blocks_mix.csv ({scen}, unsearched, rank {1 if L == 'S' else L}).")


# ---------------------------------------------------------------- V23 history explained
def v23():
    summ = json.load(open(ROOT / "outputs/satcom/summary_v2.json"))["arcprofile"]["p_v2"]
    hi90, lo90 = (-v for v in summ["i90"])
    fig = new_fig()
    ax = map_ax(fig, (0, 0, W, H), -43.6, -24.4, lon_c=94.0)
    graticule(ax, 5, 5)
    draw_land(ax)
    draw_search(ax, alpha=0.38)
    draw_arc7(ax, lw=2.6)
    a = arc7()
    k = (a[:, 0] >= -hi90) & (a[:, 0] <= -lo90)
    ax.plot(a[k, 1], a[k, 0], color=INK, lw=12, alpha=0.45, zorder=7, solid_capstyle="round")
    draw_areas(ax, which="12", label=False)
    for L, (bx, by) in {"1": (102.6, -30.0), "2": (92.6, -39.8)}.items():
        r = areas()[L]["row"]
        ax.plot([r.centre_lon, bx], [r.centre_lat, by], color=AREA, lw=1.8, zorder=15)
        ax.text(bx, by, L, color=BG, fontsize=pt(30), fontweight="bold", ha="center", va="center", zorder=17,
                bbox=dict(boxstyle="circle,pad=0.25", fc=AREA, ec=BG, lw=2))
    ax.text(102.6 + 0.75, -30.0, "Area 1: on the 2018\nsearch's outer edge", color=INK, fontsize=pt(26), fontweight="bold",
            ha="left", va="center", zorder=16, path_effects=HALO)
    ax.text(92.6 + 0.75, -39.8, "Area 2: beyond the 2014–17\nsearch's south-east edge", color=INK, fontsize=pt(26),
            fontweight="bold", ha="left", va="center", zorder=16, path_effects=HALO)
    notes = [((84.9, -39.45), (75.6, -35.6), "2014–17: right latitudes,\nlimited width"),
             ((97.4, -29.9), (88.2, -28.3), "2018: further north,\nlimited width"),
             ((94.4, -34.6), (97.4, -36.4), "2025–26: the 34.2°S hotspot\ndepends on a descent at 02:40")]
    for xy, xyt, txt in notes:
        ax.annotate(txt, xy=xy, xytext=xyt, color=INK, fontsize=pt(28), fontweight="bold", zorder=15,
                    path_effects=HALO, arrowprops=dict(arrowstyle="-", color=INK, lw=2))
    title(fig, "Why the past searches came up empty", "The empty searches point past the edges", box=True)
    legend_box(fig, [("patch", BLUE, "ATSB-led 2014–17"), ("patch", ORANGE, "Ocean Infinity 2018"),
                     ("patch", AQUA, "Ocean Infinity 2025–26 (reconstructed)"), ("outline", AREA, "Areas 1 and 2"),
                     ("line", "#9aa3b1", f"Satellite 90% range on the arc ({lo90:.1f}–{hi90:.1f}°S)")], 80, 215, size=24)
    source(fig, "Geoscience Australia / AusSeabed; Malaysian search updates; AIS ship tracks; mh370-open analysis")
    save(fig, "V23_history_explained")
    describe("V23_history_explained", "Map of search campaigns with annotations (2014-17: right latitudes, limited width; 2018: further north, "
             "limited width, area 1 on its outer (south-east) edge; 2025-26: the 34.2S hotspot depends on a descent at the 18:40 UTC / "
             f"02:40 MYT call), satellite p_v2 90% band {lo90:.2f}-{hi90:.2f}S on the arc, areas 1 and 2 (default mixture, "
             "outputs/combine/ranked_blocks_mix.csv). Band width NOT labelled as +/-25 NM: the reconstructed ATSB band at 36-39.4S "
             "runs ~-52 to +91 km from the arc (outputs/search/arc_profile.csv).")


# ---------------------------------------------------------------- V24 limits
def v24():
    fig = new_fig()
    title(fig, "What could prove us wrong", "Five limits of this analysis")
    items = [("How much to doubt the model is a judgement call",
              "We started at 1 in 10 that the satellite model is wrong; change that and the top two areas can swap."),
             ("No public fuel model", "Fuel is what best separates our scenarios; no credible open model exists."),
             ("2025–26 search footprint reconstructed", "Never published; rebuilt from ship-tracking (AIS) data and official totals."),
             ("Search thoroughness partly estimated", "Detection chances of past searches are partly our own judgement."),
             ("Flaperon drift check: currents to mid-2015 only",
              "The flaperon's real-currents check (HYCOM) only spans March 2014 – August 2015.")]
    y = 210
    for i, (h, b) in enumerate(items):
        fig.add_artist(FancyBboxPatch((fx(80), fy(y + 120)), 1760 / W, 120 / H, boxstyle="round,pad=0,rounding_size=0.01",
                                      fc=PANEL, ec="none", transform=fig.transFigure))
        fig.text(fx(130), fy(y + 60), f"{i + 1}", color=YELLOW, fontsize=pt(60), fontweight="bold", va="center")
        fig.text(fx(240), fy(y + 40), h, color=INK, fontsize=pt(38), fontweight="bold", va="center")
        fig.text(fx(240), fy(y + 86), b, color=INK2, fontsize=pt(26), va="center")
        y += 132
    source(fig, "mh370-open findings (independent analysis, 5–6 Nov 2026)")
    save(fig, "V24_limits")
    describe("V24_limits", "Text card: the five limits listed in script S16 (prior weight eps of the 'model is wrong' component is a "
             "judgement - outputs/combine/README.md mixture caveats: U1/U2 order swaps for eps < ~0.06 at w = 0.5; fuel model; reconstructed "
             "2025-26 footprint; estimated POD; flaperon hindcast currents). Titles follow the script's ONSCREEN text; the hindcast line "
             "says March 2014 - August 2015 because that is the HYCOM span in outputs/drift/README.md. FINDINGS.md section 6.")


# ---------------------------------------------------------------- V25 close
def v25():
    fig = new_fig()
    ax = map_ax(fig, (0, 0, W, H), -50, 12, lon_c=92)
    draw_land(ax, fc="#16233a", ec="#1f3049")
    a = arc7(-44, 5)
    ax.plot(a[:, 1], a[:, 0], color=ARC, lw=2.0, alpha=0.25, zorder=3)
    fig.add_artist(Rectangle((0, 0), 1, 1, fc=BG, alpha=0.5, transform=fig.transFigure, zorder=5))
    fig.text(0.5, 0.60, "239 people", color=INK, fontsize=pt(150), fontweight="bold", ha="center", va="center", zorder=10)
    fig.text(0.5, 0.44, "were on board MH370", color=INK2, fontsize=pt(48), ha="center", va="center", zorder=10)
    fig.text(0.5, 0.20, "Code, data sources and full reports: link in description", color=INK, fontsize=pt(40),
             ha="center", va="center", zorder=10)
    save(fig, "V25_close")
    describe("V25_close", "Closing card: '239 people' + 'Code, data sources and full reports: link in description' over a faint 7th arc.")


# ---------------------------------------------------------------- thumbnail
def thumbnail():
    fig = new_fig(1280, 720)
    s = 1280 / W  # scale factor vs 1920 layout
    ax = fig.add_axes([0.42, 0, 0.58, 1])
    lat0, lat1 = -43.0, -28.0
    k = 1 / np.cos(np.radians((lat0 + lat1) / 2))
    half = (lat1 - lat0) * (0.58 * 1280 / 720) * k / 2
    ax.set_xlim(91.5 - half, 91.5 + half)
    ax.set_ylim(lat0, lat1)
    ax.set_facecolor(BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp_ in ax.spines.values():
        sp_.set_visible(False)
    ax._ext = (91.5 - half, 91.5 + half, lat0, lat1)
    draw_heat(ax, "mix")
    draw_land(ax)
    draw_search(ax, mode="mono")
    draw_arc7(ax, lw=2.5)
    draw_areas(ax, which="S123", lw=3, size=26)
    fig.add_artist(Rectangle((0, 0), 0.47, 1, fc=BG, alpha=0.92, transform=fig.transFigure, zorder=5))
    fig.text(0.04, 0.80, "MH370", color=AREA, fontsize=56, fontweight="bold", va="center", zorder=10)
    fig.text(0.04, 0.55, "Where's left\nto look?", color=INK, fontsize=52, fontweight="bold", va="center",
             linespacing=1.0, zorder=10)
    fig.text(0.04, 0.27, "Public-data reanalysis\nranked areas · honest odds", color=INK2, fontsize=22, va="center",
             linespacing=1.25, zorder=10)
    fig.savefig(VID / "thumbnail.png", dpi=DPI, facecolor=BG)
    plt.close(fig)
    print("wrote video/thumbnail.png")
    describe("thumbnail (video/thumbnail.png, 1280x720)", "'MH370 / Where's left to look?' over the V21 results map "
             "(mixture posterior post_mix at the recommended default, searched outlines, 7th arc, areas 1-3 and the satellite-only "
             "pick S). No claim of a find.")


# ============================================================================= main
ALL = [("V01", v01), ("V02", v02), ("V03", v03), ("V04", v04), ("V05", v05), ("V06", v06), ("V07", v07),
       ("V08", v08), ("V09", v09), ("V10", v10), ("V11", v11), ("V12", v12), ("V13", v13), ("V14", v14),
       ("V15", v15), ("V16", v16), ("V17", v17), ("V18", v18), ("V19", v19), ("V20", v20), ("V21", v21),
       ("V22", v22), ("V23", v23), ("V24", v24), ("V25", v25), ("V26", v26), ("thumb", thumbnail)]


def write_visuals_md():
    p = VID / "visuals.md"
    old = {}
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("- **"):
                k = line[4:line.index("**", 4)]
                old[k] = line
    for k, v in DESCR.items():
        old[k] = f"- **{k}** — {v}"
    old = {k: v for k, v in old.items() if k.startswith("thumbnail") or (OUTV / f"{k}.png").exists()}  # drop retired stills
    head = ("# Visuals for video/script.md\n\nOne line per still in `video/visuals/` (1920×1080 PNG): what it shows and where the "
            "numbers come from. Regenerate with `.venv/bin/python -I scripts/video_visuals.py`. All times on screen are Malaysian "
            "local time (UTC+8) unless marked UTC. Visuals marked ILLUSTRATION are schematic. On-screen source lines name public "
            "sources only; the file-level provenance is listed here.\n\n")
    p.write_text(head + "\n".join(old[k] for k in sorted(old)) + "\n")
    print("wrote video/visuals.md")


def main(argv):
    sel = argv or [k for k, _ in ALL]
    for k, fn in ALL:
        if any(k.startswith(s) or s.startswith(k) for s in sel):
            fn()
    write_visuals_md()


if __name__ == "__main__":
    main(sys.argv[1:])
