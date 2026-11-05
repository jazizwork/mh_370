"""Workstream C, part 1: reconstruction of the seafloor already searched for MH370 and the
resulting probability of detection (POD) on the common grid.

Inputs (all public; provenance in data/raw/<source>/SOURCE.md):
  * data/raw/atsb_ga_search/polygons_atsb.json  - ATSB 2014-17 sonar coverage from Geoscience
    Australia / AusSeabed machine-readable layers, ATSB Figure-73 confidence areas, interior
    data gaps, Bluefin-21 2014 area.
  * data/raw/oi2018_search/polygons_oi2018.json - Ocean Infinity 2018, digitised from the
    Malaysian "MH370 Operational Search Update" maps (+ an inferred final northern sweep).
  * data/raw/oi2025_search/polygons_oi2025.json - Ocean Infinity 2025-26, ASSUMED footprints
    from AIS tracks + official area tallies (no official map exists), plus the HPSA / GO Phoenix
    gap polygons.

Model
-----
Each campaign c is a list of "paint" items (geometry, detection probability d). Items are
painted in order inside a campaign (later items overwrite earlier ones), so a campaign
assigns a single d_c(x) to every point x. Campaigns are then combined:

  best / high bound : POD(x) = 1 - prod_c (1 - d_c(x))      (independent misses)
  low bound         : POD(x) = max_c d_c(x)                  (fully correlated misses)

Geometric uncertainty is folded into the bounds: for pod_low, items with d>0 are eroded by
their stated position error and gap items (d=0 overrides) are dilated; for pod_high the
reverse. A cell's POD is the mean of the point POD over a 10x10 sub-sample of the cell.

Signed cross-arc distance n is positive on the side of the 7th arc farther from the
satellite (south-east of the arc).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pyproj
import shapely
from shapely.geometry import MultiPolygon, Polygon, mapping
from shapely.ops import unary_union

from . import geo, grid

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
F_ATSB = RAW / "atsb_ga_search" / "polygons_atsb.json"
F_OI18 = RAW / "oi2018_search" / "polygons_oi2018.json"
F_OI25 = RAW / "oi2025_search" / "polygons_oi2025.json"
F_CAPTION_AREAS = ROOT / "data" / "derived" / "oi2025_search" / "search_areas.json"

GEOD = pyproj.Geod(ellps="WGS84")
_TO_EA = pyproj.Transformer.from_crs(4326, 6933, always_xy=True)
KM_PER_NM = 1.852

CAMPAIGNS = ["ATSB_2014_17", "OI_2018", "OI_2025_26", "Bluefin21_2014"]

# ---------------------------------------------------------------------------------------
# POD assignments (best, low, high) with justification. Referenced by the README.
# ---------------------------------------------------------------------------------------
POD_TABLE = {
    "ATSB_envelope": dict(
        pod=0.960, pod_low=0.84, pod_high=0.993,
        basis="ATSB 2017 (Operational Search, pp.95-96, Fig.73): combined 97.4% high-confidence "
              "coverage (>95% detection), 2.1% lower-POD (50-90%, nominal 70%), 0.5% gaps (0%). "
              "Mid = 0.974*0.975+0.021*0.7 = 0.96. Low additionally x0.9 for imagery-review / "
              "classification misses and holidays not captured by the 100 m metric; "
              "high = HC 100%, LC 90%. Applied only where no Fig.73 area polygon applies."),
    "ATSB_area": dict(
        basis="Per Fig.73 area: mid = HC*0.975 + LC*0.7; high = HC*1.0 + LC*0.9; "
              "low = (HC*0.95 + LC*0.5)*0.9 (extra x0.9 review/classification factor)."),
    "ATSB_gap": dict(
        pod=0.0, pod_low=0.0, pod_high=0.0,
        basis="Interior hole in the public GA sonar mosaics (no imagery) - ATSB rates data "
              "holidays at 0% detection."),
    "HPSA_gap": dict(
        pod=0.0, pod_low=0.0, pod_high=0.0,
        basis="Iannello (radiantphysics, 11 Feb 2023): ~30.5 km2 around 34.53S 93.84E 'never "
              "scanned' (steep slope missed by GO Phoenix, half-scanned by OI 2018). ATSB d=0."),
    "GoPhoenix_gap": dict(
        pod=0.0, pod_low=0.0, pod_high=0.5,
        basis="CAPTION KMZ: gap in GO Phoenix SAS coverage near the HPSA (55 km2). ATSB d=0 "
              "(high bound 0.5: deep-tow / AUV may have covered parts). OI 2018 coverage there "
              "is applied from the OI 2018 polygons where they overlap."),
    "OI2018_site": dict(
        pod=0.92, pod_low=0.80, pod_high=0.98,
        basis="OI 2018 Hugin AUVs (side-scan + MBES), 'high quality data in which we have full "
              "confidence' (OI 30 Apr 2018); OI reportedly estimated ~99% coverage (Godfrey, "
              "28 May 2018, unofficial); a second-hand 3.1% data-holiday figure exists. No "
              "official POD was published; Broken Ridge terrain is difficult. Best 0.92, low "
              "0.80, high 0.98."),
    "OI2018_intra_junction": dict(
        pod=0.92, pod_low=0.0, pod_high=0.98,
        basis="Gaps < ~3 km between adjacent digitised OI 2018 sites (e.g. Site 1/2 at 32.4S). The "
              "official maps show the sites abutting, so best/high treat them as covered with the "
              "site POD; the low bound treats them as real gaps."),
    "ATSB_OI_junction_sliver": dict(
        pod=0.46, pod_low=0.0, pod_high=0.92,
        basis="Slivers < ~3 km wide between the ATSB coverage edge (0.5 km accurate) and the "
              "digitised OI 2018 site edges (+/-1-2 km), mostly along the Site-1 legs at 34.7-36S. "
              "Could be digitising error (then covered, 0.92) or real unsearched slivers (0): "
              "best = 0.5 x 0.92."),
    "OI2018_site4_remainder": dict(
        pod=0.85, pod_low=0.50, pod_high=0.97,
        basis="Planned Site-4 box NE of the 27 May coverage; completion ~27-30 May inferred from "
              "the AIS track, not from an official map."),
    "OI2018_north_inferred": dict(
        pod=0.50, pod_low=0.15, pod_high=0.85,
        basis="30 May-7 Jun 2018 sweep to ~25S, no official map; 'gaps between AUV tracks "
              "opened out again' (R. Cole, AirlineRatings 31 May 2018); AUVs recovered early, "
              "one AUV swath 5.2 km vs 7.4 km (Godfrey). Geometry inferred from AIS; the "
              "CAPTION community outline independently reaches 24.73S."),
    "OI2025_post_contract": dict(
        pod=0.90, pod_low=0.70, pod_high=0.97,
        basis="Hugin AUVs (Armada 78 06 / 86 05). Official tally 7,571 km2, no map; footprint "
              "ASSUMED from AIS tracks + tally (+/-8 km). No POD published."),
    "OI2025_pre_contract_SW": dict(
        pod=0.60, pod_low=0.20, pod_high=0.92,
        basis="Pre-signing survey 11-24 Mar 2025 inferred only from the AIS envelope; OI never "
              "published its extent or area; AUV coverage within the envelope may be partial."),
    "OI2025_infill_HPSA": dict(
        pod=0.50, pod_low=0.0, pod_high=0.90,
        basis="Feb 2025 pre-contract infill reportedly targeted earlier gaps incl. the HPSA "
              "(Iannello); which patches were filled is unknown."),
    "Bluefin21": dict(
        pod=0.90, pod_low=0.70, pod_high=0.97,
        basis="Bluefin-21 AUV side-scan, Apr-May 2014, ~860 km2 around the Ocean Shield acoustic "
              "detections (GA feature service polygon). ATSB: no aircraft debris found. Lies "
              "~5 km from the sea-level 7th arc at 21.1S, so it is arc coverage."),
}


@dataclass
class SearchItem:
    campaign: str
    name: str
    geom: object  # shapely (Multi)Polygon in lon/lat
    pod: float
    pod_low: float
    pod_high: float
    err_km: float
    method: str
    pod_class: str
    source: str = ""
    notes: str = ""
    is_gap: bool = False
    _cache: dict = field(default_factory=dict, repr=False)

    def geometry_for(self, bound: str):
        """Geometry used for a bound: eroded/dilated by err_km for low/high. Coverage items
        are eroded only against the OUTER boundary of their campaign (set by
        _set_low_geometries), so shared edges between adjacent sites do not open fake gaps."""
        if bound == "best" or self.err_km <= 0:
            return self.geom
        if bound not in self._cache:
            grow = (bound == "high") != self.is_gap   # high: grow coverage, shrink gaps
            self._cache[bound] = buffer_km(self.geom, self.err_km if grow else -self.err_km)
        return self._cache[bound]

    def d(self, bound: str) -> float:
        return {"best": self.pod, "low": self.pod_low, "high": self.pod_high}[bound]


# ---------------------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------------------
def _poly_from_parts(parts):
    polys = []
    for p in parts:
        if isinstance(p, dict):
            polys.append(Polygon(p["ring"], p.get("holes") or []))
        else:
            polys.append(Polygon(p))
    g = unary_union([shapely.make_valid(q) for q in polys])
    return g


def area_km2(g) -> float:
    """Equal-area (EPSG:6933) area in km2."""
    if g.is_empty:
        return 0.0
    return shapely.transform(g, lambda xy: np.column_stack(_TO_EA.transform(xy[:, 0], xy[:, 1]))).area / 1e6


def geodesic_area_km2(g) -> float:
    if g.is_empty:
        return 0.0
    return abs(GEOD.geometry_area_perimeter(shapely.segmentize(g, 0.01))[0]) / 1e6


def buffer_km(g, d_km: float):
    """Buffer a lon/lat geometry by d_km (negative = erode) in a local azimuthal
    equidistant projection centred on the geometry."""
    if g.is_empty or d_km == 0:
        return g
    c = g.centroid
    aeqd = pyproj.CRS.from_proj4(f"+proj=aeqd +lat_0={c.y} +lon_0={c.x} +datum=WGS84 +units=m")
    fwd = pyproj.Transformer.from_crs(4326, aeqd, always_xy=True)
    inv = pyproj.Transformer.from_crs(aeqd, 4326, always_xy=True)
    gp = shapely.transform(g, lambda xy: np.column_stack(fwd.transform(xy[:, 0], xy[:, 1])))
    gb = gp.buffer(d_km * 1000.0, quad_segs=4)
    return shapely.transform(gb, lambda xy: np.column_stack(inv.transform(xy[:, 0], xy[:, 1])))


# ---------------------------------------------------------------------------------------
# build the search items
# ---------------------------------------------------------------------------------------
def build_items() -> list[SearchItem]:
    items: list[SearchItem] = []
    atsb = json.load(open(F_ATSB))["polygons"]
    oi18 = {p["name"]: p for p in json.load(open(F_OI18))["polygons"]}
    oi25 = {p["name"]: p for p in json.load(open(F_OI25))["polygons"]}

    def oi25geom(name):
        return _poly_from_parts(oi25[name]["rings"])

    # ---------------- ATSB 2014-17 ----------------
    env = [p for p in atsb if p["kind"] == "searched_area"][0]
    t = POD_TABLE["ATSB_envelope"]
    items.append(SearchItem("ATSB_2014_17", "ATSB sonar coverage envelope (GA, all sensors)",
                            Polygon(env["ring"]), t["pod"], t["pod_low"], t["pod_high"],
                            env["est_error_km"], env["method"], "ATSB_envelope", env["source"],
                            env["notes"]))
    for p in atsb:
        if p["kind"].startswith("atsb_confidence_area_"):
            col = p["kind"].split("_")[-1]
            hc = p["atsb_high_confidence_coverage_pct"] / 100
            lc = p["atsb_lower_confidence_coverage_pct"] / 100
            mid = hc * 0.975 + lc * 0.7
            hi = hc * 1.0 + lc * 0.9
            lo = (hc * 0.95 + lc * 0.5) * 0.9
            # clip to the envelope so that the colour areas never extend coverage
            g = _poly_from_parts(p["rings"]).intersection(items[0].geom)
            items.append(SearchItem("ATSB_2014_17", f"ATSB Fig.73 area '{col}'", g,
                                    round(mid, 4), round(lo, 4), round(hi, 4),
                                    0.5,  # outer edges = envelope (0.5 km); internal cuts ~3 km
                                    p["method"], "ATSB_area", p["source"] if "source" in p else
                                    "derived from GA coverage + ATSB Fig.73 statistics",
                                    p.get("atsb_definition", "")))
    t = POD_TABLE["ATSB_gap"]
    for p in atsb:
        if p["kind"] == "data_gap":
            items.append(SearchItem("ATSB_2014_17", p["name"], Polygon(p["ring"]), t["pod"],
                                    t["pod_low"], t["pod_high"], p["est_error_km"], p["method"],
                                    "ATSB_gap", "GA sonar mosaic interior hole", "", is_gap=True))
    t = POD_TABLE["GoPhoenix_gap"]
    items.append(SearchItem("ATSB_2014_17", "GO Phoenix terrain gap near HPSA (CAPTION KMZ)",
                            oi25geom("GO_Phoenix_terrain_gap_near_HPSA_CAPTION"), t["pod"],
                            t["pod_low"], t["pod_high"], 0.5, "machine-readable", "GoPhoenix_gap",
                            oi25["GO_Phoenix_terrain_gap_near_HPSA_CAPTION"].get("source", ""),
                            "", is_gap=True))
    t = POD_TABLE["HPSA_gap"]
    items.append(SearchItem("ATSB_2014_17", "High Priority Search Area (never scanned per Iannello 2023)",
                            oi25geom("High_Priority_Search_Area_HPSA"), t["pod"], t["pod_low"],
                            t["pod_high"], 0.2, "digitised", "HPSA_gap",
                            oi25["High_Priority_Search_Area_HPSA"].get("source", ""), "",
                            is_gap=True))

    # ---------------- Bluefin-21 2014 ----------------
    t = POD_TABLE["Bluefin21"]
    bf = unary_union([Polygon(p["ring"]) for p in atsb if p["kind"] == "searched_area_2014_bluefin21"])
    items.append(SearchItem("Bluefin21_2014", "Bluefin-21 AUV search area Apr-May 2014 (GA)", bf,
                            t["pod"], t["pod_low"], t["pod_high"], 0.5, "machine-readable",
                            "Bluefin21", "GA ArcGIS feature service Bluefin_21_AreaSearched2014", ""))

    # ---------------- Ocean Infinity 2018 ----------------
    def o18(name):
        p = oi18[name]
        return _poly_from_parts(p["parts"]), p
    # junction slivers (painted first inside OI_2018 so real site polygons win where they overlap)
    oi_parts = [o18(nm)[0] for nm in ["OI2018_Site1", "OI2018_Site2", "OI2018_Site3", "OI2018_Site4_to_27May",
                                       "OI2018_Site4_box", "OI2018_North_extension_inferred"]]
    oi_u = unary_union(oi_parts)
    intra = buffer_km(buffer_km(oi_u, 1.5), -1.5).difference(oi_u)
    intra = unary_union([g for g in getattr(intra, "geoms", [intra]) if area_km2(g) > 0.05]) if not intra.is_empty else intra
    t = POD_TABLE["OI2018_intra_junction"]
    items.append(SearchItem("OI_2018", "OI 2018 inter-site junction gaps (<3 km, closed)", intra, t["pod"],
                            t["pod_low"], t["pod_high"], 0.0, "derived", "OI2018_intra_junction",
                            "morphological closing (1.5 km) of the digitised OI 2018 union", ""))
    atsb_u = items[0].geom
    both = unary_union([atsb_u, oi_u])
    sl = buffer_km(buffer_km(both, 1.5), -1.5).difference(unary_union([both, intra]))
    sl = sl.intersection(buffer_km(atsb_u, 3.0)).intersection(buffer_km(oi_u, 3.0))
    sl = unary_union([g for g in getattr(sl, "geoms", [sl]) if g.geom_type == "Polygon" and area_km2(g) > 0.05]) \
        if not sl.is_empty else sl
    t = POD_TABLE["ATSB_OI_junction_sliver"]
    items.append(SearchItem("OI_2018", "ATSB / OI 2018 junction slivers (<3 km, uncertain)", sl, t["pod"],
                            t["pod_low"], t["pod_high"], 0.0, "derived", "ATSB_OI_junction_sliver",
                            "closing (1.5 km) of ATSB u OI 2018 minus both, within 3 km of each", ""))
    t = POD_TABLE["OI2018_north_inferred"]
    g, p = o18("OI2018_North_extension_inferred")
    # positional error used for erosion/dilation: ~5 km on the cross-arc edges; the along-arc
    # northern limit (-0.25/+0.3 deg) is covered by the low POD and by the dilation.
    items.append(SearchItem("OI_2018", "OI 2018 northern sweep 30 May-7 Jun (INFERRED)", g,
                            t["pod"], t["pod_low"], t["pod_high"], 5.0, p["method"],
                            "OI2018_north_inferred", p["source"], p["notes"]))
    t = POD_TABLE["OI2018_site4_remainder"]
    g, p = o18("OI2018_Site4_box")
    items.append(SearchItem("OI_2018", "OI 2018 Site 4 planned box (completion inferred)", g,
                            t["pod"], t["pod_low"], t["pod_high"], 1.5, p["method"],
                            "OI2018_site4_remainder", p["source"], p["notes"]))
    t = POD_TABLE["OI2018_site"]
    for nm in ["OI2018_Site1", "OI2018_Site2", "OI2018_Site3", "OI2018_Site4_to_27May"]:
        g, p = o18(nm)
        items.append(SearchItem("OI_2018", nm.replace("OI2018_", "OI 2018 "), g, t["pod"],
                                t["pod_low"], t["pod_high"], p["est_error_km"], p["method"],
                                "OI2018_site", p["source"], p["notes"]))

    # ---------------- Ocean Infinity 2025-26 ----------------
    t = POD_TABLE["OI2025_infill_HPSA"]
    items.append(SearchItem("OI_2025_26", "Feb 2025 infill of HPSA / GO Phoenix gap (uncertain)",
                            unary_union([oi25geom("High_Priority_Search_Area_HPSA"),
                                         oi25geom("GO_Phoenix_terrain_gap_near_HPSA_CAPTION")]),
                            t["pod"], t["pod_low"], t["pod_high"], 0.0, "assumed",
                            "OI2025_infill_HPSA", "Iannello (radiantphysics) via oi2025 SOURCE.md", ""))
    t = POD_TABLE["OI2025_pre_contract_SW"]
    nm = "OI2025_pre_contract_SW_survey_Mar11-24"
    items.append(SearchItem("OI_2025_26", "OI 2025 pre-contract SW survey 11-24 Mar 2025 (ASSUMED)",
                            oi25geom(nm), t["pod"], t["pod_low"], t["pod_high"],
                            oi25[nm]["est_error_km"], oi25[nm]["method"], "OI2025_pre_contract_SW",
                            oi25[nm]["source"], oi25[nm]["notes"]))
    t = POD_TABLE["OI2025_post_contract"]
    nm = "OI2025_26_surveyed_post_contract_best"
    items.append(SearchItem("OI_2025_26", "OI 2025-26 surveyed 7,571 km2 (ASSUMED footprint)",
                            oi25geom(nm), t["pod"], t["pod_low"], t["pod_high"],
                            oi25[nm]["est_error_km"], oi25[nm]["method"], "OI2025_post_contract",
                            oi25[nm]["source"], oi25[nm]["notes"]))
    _set_low_geometries(items)
    return items


def _set_low_geometries(items):
    """Low-bound geometry of a coverage item = item minus a band of width err_km inside the
    outer boundary of its campaign's coverage (instead of eroding each item separately)."""
    for camp in CAMPAIGNS:
        cov = [it for it in items if it.campaign == camp and not it.is_gap and it.pod > 0]
        if not cov:
            continue
        outer = unary_union([it.geom for it in cov])
        # morphological closing (1 km) first, so hairline digitising gaps between adjacent
        # sites are not widened into fake km-wide gaps by the erosion
        outer = buffer_km(buffer_km(outer, 1.0), -1.0)
        for it in cov:
            if it.err_km > 0:
                it._cache["low"] = it.geom.intersection(buffer_km(outer, -it.err_km))


def campaign_union(items, campaign, bound="best", positive_only=True):
    """Union of a campaign's geometry (d>0 items) after applying gap overrides."""
    gs = [it.geometry_for(bound) for it in items if it.campaign == campaign
          and (it.d(bound) > 0 or not positive_only) and not it.is_gap]
    u = unary_union(gs) if gs else Polygon()
    gaps = [it.geometry_for(bound) for it in items if it.campaign == campaign and it.is_gap
            and it.d(bound) == 0]
    if gaps:
        u = u.difference(unary_union(gaps))
    return u


# ---------------------------------------------------------------------------------------
# POD evaluation at arbitrary points and on the common grid
# ---------------------------------------------------------------------------------------
def campaign_d_at(items, campaign, lon, lat, bound="best"):
    """Detection probability of one campaign at points (paint semantics). NaN = not covered."""
    d = np.full(lon.shape, np.nan)
    for it in items:
        if it.campaign != campaign:
            continue
        g = it.geometry_for(bound)
        if g.is_empty:
            continue
        x0, y0, x1, y1 = g.bounds
        sel = (lon >= x0) & (lon <= x1) & (lat >= y0) & (lat <= y1)
        if not sel.any():
            continue
        shapely.prepare(g)
        inside = shapely.contains_xy(g, lon[sel], lat[sel])
        idx = np.flatnonzero(sel)[inside]
        d.flat[idx] = it.d(bound)
    return d


def pod_at(items, lon, lat, bound="best", campaigns=CAMPAIGNS, return_parts=False):
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    parts = {c: campaign_d_at(items, c, lon, lat, bound) for c in campaigns}
    if bound == "low":
        pod = np.zeros(lon.shape)
        for d in parts.values():
            pod = np.maximum(pod, np.nan_to_num(d, nan=0.0))
    else:
        surv = np.ones(lon.shape)
        for d in parts.values():
            surv *= 1.0 - np.nan_to_num(d, nan=0.0)
        pod = 1.0 - surv
    return (pod, parts) if return_parts else pod


def rasterise(items, sub=10, campaigns=CAMPAIGNS):
    """Cell-mean POD (best/low/high), searched fraction and per-campaign coverage fraction on
    the common grid using a sub x sub point sample per cell."""
    lat, lon = grid.common_grid()
    step = 0.05
    # region of interest: bounds of all (dilated) geometry + margin
    bb = np.array([it.geometry_for(b).bounds for it in items for b in ("best", "high")
                   if not it.geometry_for(b).is_empty])
    x0, y0 = np.nanmin(bb[:, 0]) - 0.1, np.nanmin(bb[:, 1]) - 0.1
    x1, y1 = np.nanmax(bb[:, 2]) + 0.1, np.nanmax(bb[:, 3]) + 0.1
    i0, i1 = np.searchsorted(lat, y0) - 1, np.searchsorted(lat, y1) + 1
    j0, j1 = np.searchsorted(lon, x0) - 1, np.searchsorted(lon, x1) + 1
    i0, j0 = max(i0, 0), max(j0, 0)
    i1, j1 = min(i1, lat.size), min(j1, lon.size)
    off = (np.arange(sub) + 0.5) / sub * step - step / 2
    out = {}
    shape = (lat.size, lon.size)
    for k in ["pod", "pod_low", "pod_high", "searched_frac", "searched_frac_low",
              "searched_frac_high"] + [f"cov_{c}" for c in campaigns]:
        out[k] = np.zeros(shape, dtype=np.float32)
    # process in latitude chunks to bound memory
    for ia in range(i0, i1, 40):
        ib = min(ia + 40, i1)
        la = (lat[ia:ib, None] + off[None, :]).ravel()
        lo = (lon[j0:j1, None] + off[None, :]).ravel()
        LO, LA = np.meshgrid(lo, la)
        nlat, nlon = ib - ia, j1 - j0

        def cellmean(a):
            return a.reshape(nlat, sub, nlon, sub).mean(axis=(1, 3))
        for bound, key in [("best", "pod"), ("low", "pod_low"), ("high", "pod_high")]:
            pod, parts = pod_at(items, LO, LA, bound, campaigns, return_parts=True)
            out[key][ia:ib, j0:j1] = cellmean(pod)
            sk = {"best": "searched_frac", "low": "searched_frac_low", "high": "searched_frac_high"}[bound]
            anyc = np.zeros(LO.shape, bool)
            for c, d in parts.items():
                cov = np.isfinite(d) & (d > 0)
                anyc |= cov
                if bound == "best":
                    out[f"cov_{c}"][ia:ib, j0:j1] = cellmean(cov.astype(np.float32))
            out[sk][ia:ib, j0:j1] = cellmean(anyc.astype(np.float32))
    return out


# ---------------------------------------------------------------------------------------
# 7th-arc frame: along-arc s and signed cross-arc n (+ = farther from satellite = SE)
# ---------------------------------------------------------------------------------------
_ARC_CACHE = {}


def arc_dense(h_m=0.0, lat_min=-46.0, lat_max=-6.0, step=0.01):
    key = (h_m, lat_min, lat_max, step)
    if key not in _ARC_CACHE:
        lats = np.round(np.arange(lat_min, lat_max + 1e-9, step), 6)
        pl = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, h_m, lats=lats)
        la, lo = pl[:, 0], pl[:, 1]
        seg = GEOD.inv(lo[:-1], la[:-1], lo[1:], la[1:])[2] / 1000.0
        s = np.concatenate([[0.0], np.cumsum(seg)])
        # s = 0 at the UGIB LEP latitude 34.2342 S
        s -= np.interp(-34.2342, la, s)
        _ARC_CACHE[key] = (la, lo, s)
    return _ARC_CACHE[key]


def _range_to_sat_km(lat, lon):
    sp = geo.sat_pos(geo.ARC7_TIME)
    return np.linalg.norm(geo.llh_to_ecef(lat, lon, 0.0) - sp, axis=-1)


def arc_coords(lat, lon, h_m=0.0):
    """(s_km, n_km) of points: s = along-arc distance of the nearest arc point (0 at 34.2342S,
    positive towards the north-east), n = signed distance (+ farther from the satellite)."""
    from scipy.spatial import cKDTree
    la, lo, s = arc_dense(h_m)
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    xyz_arc = geo.llh_to_ecef(la, lo, 0.0)
    tree = cKDTree(xyz_arc)
    xyz = geo.llh_to_ecef(lat.ravel(), lon.ravel(), 0.0)
    _, k = tree.query(xyz)
    # refine along the local segment (linear projection in ECEF)
    k0 = np.clip(k - 1, 0, la.size - 2)
    best_s = np.empty(k.size)
    best_d = np.full(k.size, np.inf)
    for kk in (k0, np.clip(k, 0, la.size - 2)):
        a = xyz_arc[kk]
        b = xyz_arc[kk + 1]
        ab = b - a
        t = np.clip(np.einsum("ij,ij->i", xyz - a, ab) / np.einsum("ij,ij->i", ab, ab), 0, 1)
        foot = a + t[:, None] * ab
        dd = np.linalg.norm(xyz - foot, axis=1)
        better = dd < best_d
        best_d[better] = dd[better]
        best_s[better] = (s[kk] + t * (s[kk + 1] - s[kk]))[better]
    sign = np.sign(_range_to_sat_km(lat.ravel(), lon.ravel()) - geo.sat_to_aes_range_km(geo.ARC7_BTO_US, geo.ARC7_TIME))
    return best_s.reshape(lat.shape), (sign * best_d).reshape(lat.shape)


def arc_normal_bearing(lat0, lon0, h_m=0.0):
    """Azimuth (deg) of the cross-arc direction pointing to +n (away from the satellite)."""
    la, lo, _ = arc_dense(h_m)
    k = int(np.argmin(np.abs(la - lat0)))
    k = min(max(k, 1), la.size - 2)
    az = GEOD.inv(lo[k - 1], la[k - 1], lo[k + 1], la[k + 1])[0]
    for cand in (az + 90.0, az - 90.0):
        lo2, la2, _ = GEOD.fwd(lon0, lat0, cand, 10_000.0)
        if _range_to_sat_km(la2, lo2) > _range_to_sat_km(lat0, lon0):
            return cand % 360.0
    raise RuntimeError("normal direction not found")


def sn_to_latlon(s_km, n_km, h_m=0.0):
    """Inverse of arc_coords (approximately: forward geodesic along the local normal)."""
    la, lo, s = arc_dense(h_m)
    s_km = np.atleast_1d(np.asarray(s_km, float))
    n_km = np.atleast_1d(np.asarray(n_km, float))
    out_lat = np.empty(s_km.shape)
    out_lon = np.empty(s_km.shape)
    for i, (si, ni) in enumerate(zip(s_km.ravel(), n_km.ravel())):
        lat0 = np.interp(si, s, la)
        lon0 = np.interp(si, s, lo)
        az = arc_normal_bearing(lat0, lon0, h_m)
        if ni >= 0:
            lo2, la2, _ = GEOD.fwd(lon0, lat0, az, ni * 1000.0)
        else:
            lo2, la2, _ = GEOD.fwd(lon0, lat0, (az + 180.0) % 360.0, -ni * 1000.0)
        out_lat.flat[i] = la2
        out_lon.flat[i] = lo2
    return out_lat, out_lon


def cross_arc_profile(items, lats=None, n_max_km=250.0, dn_km=0.25):
    """Searched cross-arc width vs latitude along the sea-level 7th arc."""
    import pandas as pd
    if lats is None:
        lats = np.round(np.arange(-44.0, -16.0 + 1e-9, 0.05), 3)
    # keep latitudes where the sea-level arc lies inside the common grid (lon >= 78E; the arc
    # turns west south of ~41.5S and leaves the grid)
    lon_arc = np.array([geo.arc_lon_for_lat(la, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0) for la in lats])
    lats = lats[np.isfinite(lon_arc) & (lon_arc >= grid.LON[0]) & (lon_arc <= grid.LON[-1])]
    n = np.arange(-n_max_km, n_max_km + 1e-9, dn_km)
    rows = []
    LAT = np.empty((lats.size, n.size))
    LON = np.empty((lats.size, n.size))
    arc_lon = np.empty(lats.size)
    for i, la in enumerate(lats):
        lo0 = geo.arc_lon_for_lat(la, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
        arc_lon[i] = lo0
        az = arc_normal_bearing(la, lo0)
        lo_p, la_p, _ = GEOD.fwd(np.full(n.size, lo0), np.full(n.size, la),
                                 np.where(n >= 0, az, (az + 180) % 360), np.abs(n) * 1000.0)
        LAT[i] = la_p
        LON[i] = lo_p
    res = {}
    for bound in ["best", "low", "high"]:
        res[bound] = pod_at(items, LON, LAT, bound, return_parts=True)
    pod_b, parts_b = res["best"]
    m25 = np.abs(n) <= 25 * KM_PER_NM
    m70 = np.abs(n) <= 70 * KM_PER_NM
    for i, la in enumerate(lats):
        cov = pod_b[i] > 0
        row = dict(lat=la, arc_lon=round(arc_lon[i], 4))
        row["searched_width_km"] = cov.sum() * dn_km
        for c in CAMPAIGNS:
            d = parts_b[c][i]
            row[f"width_{c}_km"] = (np.isfinite(d) & (d > 0)).sum() * dn_km
        row["nw_edge_km"] = n[cov].min() if cov.any() else np.nan
        row["se_edge_km"] = n[cov].max() if cov.any() else np.nan
        # contiguous covered interval around the arc (n=0)
        if cov[np.argmin(np.abs(n))]:
            k0 = np.argmin(np.abs(n))
            a = k0
            while a > 0 and cov[a - 1]:
                a -= 1
            b = k0
            while b < n.size - 1 and cov[b + 1]:
                b += 1
            row["contig_nw_km"], row["contig_se_km"] = n[a], n[b]
        else:
            row["contig_nw_km"], row["contig_se_km"] = np.nan, np.nan
        row["arc_point_pod"] = pod_b[i][np.argmin(np.abs(n))]
        row["frac_searched_25nm"] = cov[m25].mean()
        row["frac_searched_70nm"] = cov[m70].mean()
        for bound, key in [("best", "eff_width_km"), ("low", "eff_width_low_km"), ("high", "eff_width_high_km")]:
            row[key] = res[bound][0][i].sum() * dn_km
        row["mean_pod_25nm"] = pod_b[i][m25].mean()
        row["mean_pod_25nm_low"] = res["low"][0][i][m25].mean()
        row["mean_pod_25nm_high"] = res["high"][0][i][m25].mean()
        row["mean_pod_70nm"] = pod_b[i][m70].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def items_geojson(items) -> dict:
    feats = []
    for it in items:
        g = it.geom
        if g.is_empty:
            continue
        feats.append(dict(type="Feature", geometry=mapping(shapely.set_precision(g, 1e-5)), properties=dict(
            campaign=it.campaign, name=it.name, pod=it.pod, pod_low=it.pod_low,
            pod_high=it.pod_high, pod_class=it.pod_class, pod_basis=POD_TABLE[it.pod_class]["basis"],
            method=it.method, est_error_km=it.err_km, is_gap_override=it.is_gap,
            area_km2_eqarea=round(area_km2(g), 1), source=it.source)))
    return dict(type="FeatureCollection", name="mh370_search_coverage_reconstruction",
                crs=dict(type="name", properties=dict(name="urn:ogc:def:crs:OGC:1.3:CRS84")),
                features=feats)


CANDIDATES = [
    # label, lat, lon, note
    ("UGIB LEP (Ulich/Godfrey/Iannello/Banks 2020)", -34.2342, 93.7875, "IG hotspot"),
    ("CSIRO drift 2017", -35.6, 92.8, "Griffin et al."),
    ("WSPR (Godfrey 2024)", -29.128, 99.934, ""),
    ("Ulich & Iannello drift 2023 (34.0S on arc)", -34.0, None, "lon = sea-level arc"),
    ("Kadri 306 deg bearing x 7th arc", -25.7, 101.4, "acoustic; timing inconsistent"),
    ("Stead 246.9 deg timing-consistent", -41.0, 81.0, "acoustic"),
    ("Anderson Java acoustic event", -8.36, 107.92, "outside common grid"),
]


def candidate_points():
    out = []
    for lab, la, lo, note in CANDIDATES:
        if lo is None:
            lo = geo.arc_lon_for_lat(la, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
        out.append((lab, la, float(lo), note))
    return out


# ---------------------------------------------------------------------------------------
# plotting helpers (shared by scripts/search_plot.py and scripts/combine_run.py)
# ---------------------------------------------------------------------------------------
# categorical slots 1-3 of the reference palette (validated all-pairs); Bluefin-21 is tiny,
# isolated and directly labelled, so it is drawn in neutral ink.
CAMPAIGN_COLOR = {"ATSB_2014_17": "#2a78d6", "OI_2018": "#eb6834", "OI_2025_26": "#1baf7a",
                  "Bluefin21_2014": "#52514e"}
CAMPAIGN_LABEL = {"ATSB_2014_17": "ATSB 2014-17 (GA sonar coverage)",
                  "OI_2018": "Ocean Infinity 2018 (digitised)",
                  "OI_2025_26": "Ocean Infinity 2025-26 (assumed)",
                  "Bluefin21_2014": "Bluefin-21 2014 (GA)"}
CAND_MARKERS = ["o", "s", "D", "^", "v", "P", "X"]
CAND_OFFSETS = {
    0: {0: (-8.0, 1.2), 1: (-9.0, -2.0), 2: (1.2, 1.4), 3: (1.5, 3.2), 4: (1.0, 1.2), 5: (1.5, -1.5), 6: (-6.0, -1.2)},
    1: {0: (-1.15, 0.3), 1: (-1.2, -0.45), 3: (0.3, 0.45)},
}


def seq_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    steps = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
    return LinearSegmentedColormap.from_list("seq_blue", steps)


_LAND = None


def _land_polys():
    global _LAND
    if _LAND is None:
        import shapefile  # pyshp
        polys = []
        for nm in ["ne_10m_land/ne_10m_land.shp", "ne_10m_minor_islands/ne_10m_minor_islands.shp"]:
            f = RAW / "naturalearth" / nm
            if not f.exists():
                continue
            r = shapefile.Reader(str(f))
            for sh in r.shapes():
                x0, y0, x1, y1 = sh.bbox
                if x1 < 30 or x0 > 160 or y0 > 30 or y1 < -60:
                    continue
                pts = np.array(sh.points)
                parts = list(sh.parts) + [len(pts)]
                for a, b in zip(parts[:-1], parts[1:]):
                    polys.append(pts[a:b])
        _LAND = polys
    return _LAND


def basemap(ax, ext):
    """Plate-carree axes with Natural Earth land, aspect corrected for latitude."""
    from matplotlib.patches import Polygon as MPoly
    x0, x1, y0, y1 = ext
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect(1.0 / np.cos(np.radians(0.5 * (y0 + y1))))
    ax.set_facecolor("#fcfcfb")
    for p in _land_polys():
        if p[:, 0].max() < x0 - 1 or p[:, 0].min() > x1 + 1 or p[:, 1].max() < y0 - 1 or p[:, 1].min() > y1 + 1:
            continue
        ax.add_patch(MPoly(p, closed=True, fc="#e6e5e1", ec="#a9a8a2", lw=0.4, zorder=3))
    ax.grid(color="#e6e5e1", lw=0.5, zorder=0)
    ax.tick_params(labelsize=8, colors="#52514e")
    ax.set_xlabel("longitude (deg E)", fontsize=8.5, color="#52514e")
    ax.set_ylabel("latitude (deg)", fontsize=8.5, color="#52514e")
    for s in ax.spines.values():
        s.set_color("#a9a8a2")


def fill_geom(ax, g, fc, alpha=0.35, lw=0.8, edge=None, hatch=None, ls="-"):
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as MPath
    if g is None or g.is_empty:
        return
    geoms = getattr(g, "geoms", [g])
    for p in geoms:
        if p.geom_type != "Polygon":
            continue
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            xy = np.asarray(ring.coords)
            verts.append(xy)
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(xy) - 2) + [MPath.CLOSEPOLY]
        path = MPath(np.concatenate(verts), codes)
        ec = edge if edge is not None else fc
        if fc != "none":
            ax.add_patch(PathPatch(path, fc=fc, ec="none", alpha=alpha, zorder=3.5))
        ax.add_patch(PathPatch(path, fc="none", ec=ec, lw=lw if lw > 0 else 0.0, hatch=hatch, ls=ls,
                               alpha=1.0 if hatch or lw > 0 else 0, zorder=3.6))
