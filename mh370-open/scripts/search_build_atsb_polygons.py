"""Build polygons of the seafloor searched by the ATSB-led underwater search (2014-2017).

Inputs (all downloaded by hand / scripts/search_fetch_atsb_ga.py, see
data/raw/atsb_ga_search/SOURCE.md):
  * AusSeabed WFS vector coverage of the Phase 2 deep-tow side-scan mosaic (GA, CC BY 4.0)
  * AusSeabed WMS renderings (alpha mask) of the four Phase 2 sonar mosaics:
    deep-tow SSS, AUV SSS, Go Phoenix SAS, Dong Hai Jiu 101 SAS (GA, CC BY 4.0)
  * GA ArcGIS Online feature services (Bluefin-21 2014 area, 2014 wide search area)
  * GA MH370 tile cache (combined Phase 2 mosaic, zoom 8) -- used only as a cross-check

Outputs (data/raw/atsb_ga_search/):
  polygons_atsb.json                    best polygons as [lon, lat] closed rings + metadata
  derived/coverage_union_detailed.geojson  vectorised union coverage (0.002 deg raster) w/ holes
  derived/coverage_by_sensor.geojson    vectorised per-sensor coverage
  derived/coverage_frac_common_grid.nc  fraction of each 0.05 deg common-grid cell covered
  derived/cross_arc_widths.csv          searched extent either side of the sea-level 7th arc
  derived/summary.json                  areas, validation numbers
  derived/coverage_qa.png               QA map

Run: .venv/bin/python -I scripts/search_build_atsb_polygons.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import contourpy
import matplotlib
import numpy as np
import shapely
import xarray as xr
from PIL import Image
from pyproj import Geod, Transformer
from scipy import ndimage as ndi
from shapely.geometry import MultiPolygon, Polygon, mapping, shape

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from mh370 import geo  # noqa: E402
from mh370.grid import common_grid  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "atsb_ga_search"
OUT = RAW / "derived"
RES = 0.002
LON0, LAT1 = 85.0, -32.5
NX, NY = 6000, 4000
R_KM = 6371.0088
NM = 1.852
EA = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
GEOD = Geod(ellps="WGS84")

LON_C = LON0 + (np.arange(NX) + 0.5) * RES
LAT_C = LAT1 - (np.arange(NY) + 0.5) * RES
PIX_KM2 = (np.radians(RES) * R_KM) ** 2 * np.cos(np.radians(LAT_C))


def area_px(m: np.ndarray) -> float:
    return float((m.sum(1) * PIX_KM2).sum())


def area_ea(g) -> float:
    """Area in km^2 in EPSG:6933 (WGS84 equal-area cylindrical)."""
    return shapely.transform(g, lambda xy: np.column_stack(EA.transform(xy[:, 0], xy[:, 1]))).area / 1e6


def area_geod(g) -> float:
    return abs(GEOD.geometry_area_perimeter(g)[0]) / 1e6


def load_wms_masks() -> dict[str, np.ndarray]:
    idx = json.loads((RAW / "ausseabed_wms" / "index.json").read_text())
    assert abs(idx["res_deg"] - RES) < 1e-12
    masks = {}
    for short, layer in idx["layers"].items():
        m = np.zeros((NY, NX), bool)
        for t in layer["tiles"]:
            a = np.array(Image.open(RAW / "ausseabed_wms" / t["file"]).convert("RGBA"))
            r, c = t["row"], t["col"]
            # genuine data pixels are opaque; GeoServer draws semi-transparent black
            # outlines along granule bounding boxes for the SAS layers -> alpha < 255
            m[r * 1000:(r + 1) * 1000, c * 1000:(c + 1) * 1000] = a[..., 3] == 255
        masks[short] = m
    return masks


def rasterise(g) -> np.ndarray:
    shapely.prepare(g)
    X, Y = np.meshgrid(LON_C, LAT_C)
    out = np.zeros((NY, NX), bool)
    for i in range(0, NY, 250):
        out[i:i + 250] = shapely.contains_xy(g, X[i:i + 250], Y[i:i + 250])
    return out


def vectorise(m: np.ndarray):
    """Binary mask -> shapely (Multi)Polygon via marching squares at level 0.5."""
    z = np.zeros((NY + 2, NX + 2))
    z[1:-1, 1:-1] = m
    x = np.concatenate([[LON_C[0] - RES], LON_C, [LON_C[-1] + RES]])
    y = np.concatenate([[LAT_C[0] + RES], LAT_C, [LAT_C[-1] - RES]])
    cg = contourpy.contour_generator(x, y, z, name="serial", fill_type="OuterOffset")
    pts, offs = cg.filled(0.5, 1.5)
    polys = []
    for p, o in zip(pts, offs):
        rings = [p[o[i]:o[i + 1]] for i in range(len(o) - 1)]
        polys.append(Polygon(rings[0], rings[1:]))
    return shapely.make_valid(MultiPolygon(polys)) if len(polys) > 1 else polys[0]


def ring_list(r) -> list:
    c = [[round(x, 5), round(y, 5)] for x, y in r.coords]
    if c[0] != c[-1]:
        c.append(c[0])
    return c


def orient_ccw(p: Polygon) -> Polygon:
    return shapely.geometry.polygon.orient(p, 1.0)


def tile_cache_mask() -> np.ndarray:
    """Combined Phase 2 tile cache (zoom 8, Web Mercator) sampled at our pixel centres."""
    d = RAW / "ga_tiles_phase2_sonar" / "L8"
    z = 8
    n = 2 ** z
    X, Y = np.meshgrid(LON_C, LAT_C)
    gx = (X + 180) / 360 * n * 256
    gy = (1 - np.arcsinh(np.tan(np.radians(Y))) / np.pi) / 2 * n * 256
    tx, ty = (gx // 256).astype(int), (gy // 256).astype(int)
    px, py = (gx % 256).astype(int), (gy % 256).astype(int)
    out = np.zeros((NY, NX), bool)
    for (c, r) in set(zip(tx.ravel().tolist(), ty.ravel().tolist())):
        f = d / f"L{z}R{r}C{c}.png"
        if not f.exists():
            continue
        a = np.array(Image.open(f).convert("RGBA"))[..., 3]
        sel = (tx == c) & (ty == r)
        out[sel] = a[py[sel], px[sel]] > 0
    return out


def cross_arc_widths(env: np.ndarray, union: np.ndarray, lats, arc: np.ndarray) -> list[dict]:
    """Extent of the searched envelope along the local normal to `arc` ((N,2) lat, lon,
    ascending lat, ~0.01 deg spacing), NW and SE of the arc."""
    rows = []
    for la in lats:
        i = np.argmin(abs(arc[:, 0] - la))
        lat0, lon0 = arc[i]
        # local tangent in km (east, north)
        j0, j1 = max(i - 5, 0), min(i + 5, len(arc) - 1)
        de = (arc[j1, 1] - arc[j0, 1]) * 111.195 * math.cos(math.radians(lat0))
        dn = (arc[j1, 0] - arc[j0, 0]) * 111.195
        t = np.array([de, dn]) / math.hypot(de, dn)
        nw = np.array([-t[1], t[0]])
        if nw[1] < 0:  # make it point north-west-ish
            nw = -nw
        res = {"lat_arc": round(float(lat0), 3), "lon_arc": round(float(lon0), 4)}
        for side, vec in (("NW", nw), ("SE", -nw)):
            s = np.arange(0, 150.0, 0.1)
            la_s = lat0 + s * vec[1] / 111.195
            lo_s = lon0 + s * vec[0] / (111.195 * np.cos(np.radians(la_s)))
            r = np.floor((LAT1 - la_s) / RES).astype(int)
            c = np.floor((lo_s - LON0) / RES).astype(int)
            ok = (r >= 0) & (r < NY) & (c >= 0) & (c < NX)
            inside = np.zeros_like(s, bool)
            inside[ok] = env[r[ok], c[ok]]
            cov = np.zeros_like(s, bool)
            cov[ok] = union[r[ok], c[ok]]
            if not inside[0]:
                cont = 0.0
            else:
                first_out = np.argmax(~inside) if (~inside).any() else len(s) - 1
                cont = float(s[first_out])
            far = float(s[np.where(inside)[0][-1]]) if inside.any() else 0.0
            res[f"{side}_contiguous_km"] = round(cont, 1)
            res[f"{side}_contiguous_nm"] = round(cont / NM, 1)
            res[f"{side}_max_extent_km"] = round(far, 1)
            res[f"{side}_frac_covered_0_25nm"] = round(float(cov[s <= 25 * NM].mean()), 4)
        res["arc_point_inside"] = bool(env[int((LAT1 - lat0) // RES), int((lon0 - LON0) // RES)])
        rows.append(res)
    return rows


def coverage_fraction_common_grid(masks: dict[str, np.ndarray]) -> xr.Dataset:
    """Fraction of each 0.05 deg common-grid cell covered (area-weighted, exact ties split)."""
    glat, glon = common_grid()

    def weights(centres, gcentres, step=0.05):
        W = np.zeros((gcentres.size, centres.size))
        lo = gcentres[0] - step / 2
        f = (centres - lo) / step
        k = np.floor(f + 1e-9).astype(int)
        frac = f - k
        tie = np.isclose(frac, 0.0, atol=1e-6)
        for idx, (kk, tt) in enumerate(zip(k, tie)):
            if tt:
                if 0 <= kk < gcentres.size:
                    W[kk, idx] += 0.5
                if 0 <= kk - 1 < gcentres.size:
                    W[kk - 1, idx] += 0.5
            elif 0 <= kk < gcentres.size:
                W[kk, idx] = 1.0
        return W

    order = np.argsort(glat)
    Wlat = weights(LAT_C[::-1], glat[order])  # ascending lat
    Wlon = weights(LON_C, glon)
    pix = PIX_KM2[::-1]
    denom = (Wlat * pix[None, :]).sum(1)[:, None] * Wlon.sum(1)[None, :]
    ds = xr.Dataset(coords={"lat": glat, "lon": glon})
    inside_box = denom > 0
    full_denom = (np.radians(0.05) * R_KM) ** 2 * np.cos(np.radians(glat))[:, None] * np.ones(glon.size)[None, :]
    for k, m in masks.items():
        num = (Wlat * pix[None, :]) @ m[::-1].astype(float) @ Wlon.T
        # fraction of the full 0.05 deg cell (cells partly outside the raster box have no data
        # outside the box anyway because the box contains all coverage)
        frac = np.where(inside_box, num, 0.0) / full_denom
        da = np.zeros((glat.size, glon.size))
        da[order] = frac
        ds[f"frac_{k}"] = (("lat", "lon"), np.clip(da, 0, 1))
    return ds


# ATSB 'Confidence in the search results' areas (ATSB 2017 pp.95-96, Figure 73). The four
# areas are defined in the text by widths about the ATSB's 7th arc; the along-arc limits are
# taken where the public coverage width changes (see derived/cross_arc_widths_ga40kft_arc.csv):
# wide southern block ends at GA-arc latitude ~36.09 S; narrow SAS strip begins ~34.64 S.
CUT_RED_ORANGE = -36.09
CUT_ORANGE_YELLOW = -34.64
ATSB_AREAS = {
    # name: (HC %, LC %, gaps %, definition text)
    "red": (98.7, 1.1, 0.2, "'Indicative Search Area' out to 27.5 NM NW and 25 NM SE of the 7th arc; deep-tow SSS, SAS and AUV infill"),
    "orange": (91.5, 7.8, 0.7, "North of the Indicative Search Area out to 23 NM NW and 17 NM SE; mainly deep-tow SSS and AUV infill"),
    "yellow": (97.8, 1.1, 1.1, "Furthest north, out to 10 NM NW and 13 NM SE; mainly SAS (Go Phoenix) and AUV infill"),
    "purple": (97.9, 1.5, 0.6, "Outside 27.5-36 NM NW and 25-41 NM SE of the 7th arc; mainly deep-tow SSS"),
}


def atsb_regions(env: np.ndarray, arc: np.ndarray) -> dict[str, np.ndarray]:
    """Split the envelope into the four ATSB Figure-73 areas using foot-point latitude on, and
    signed perpendicular distance from, the ATSB/GA reference arc (40,000 ft)."""
    from scipy.spatial import cKDTree
    aeqd = Transformer.from_crs("EPSG:4326", "+proj=aeqd +lat_0=-36.5 +lon_0=90.5 +datum=WGS84 +units=km",
                                always_xy=True)
    lat_d = np.arange(-41.0, -31.9, 0.002)
    lon_d = np.interp(lat_d, arc[:, 0], arc[:, 1])
    ax_, ay_ = aeqd.transform(lon_d, lat_d)
    A = np.column_stack([ax_, ay_])
    T = np.gradient(A, axis=0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    rr, cc = np.where(env)
    px, py = aeqd.transform(LON_C[cc], LAT_C[rr])
    _, k = cKDTree(A).query(np.column_stack([px, py]))
    v = np.column_stack([px, py]) - A[k]
    d = T[k, 0] * v[:, 1] - T[k, 1] * v[:, 0]  # >0: left of north-going tangent = NW side
    foot = lat_d[k]
    d_nm = d / NM
    cls = np.full(rr.size, "", dtype=object)
    south = foot <= CUT_RED_ORANGE
    mid = (foot > CUT_RED_ORANGE) & (foot <= CUT_ORANGE_YELLOW)
    north = foot > CUT_ORANGE_YELLOW
    red_band = (d_nm <= 27.5) & (d_nm >= -25.0)
    cls[south & red_band] = "red"
    cls[south & ~red_band] = "purple"
    orange_band = (d_nm <= 23.5) & (d_nm >= -18.0)
    cls[mid & orange_band] = "orange"
    cls[mid & ~orange_band] = "purple"
    cls[north] = "yellow"
    out = {}
    for name in ATSB_AREAS:
        m = np.zeros((NY, NX), bool)
        sel = cls == name
        m[rr[sel], cc[sel]] = True
        out[name] = m
    return out


def main() -> None:
    OUT.mkdir(exist_ok=True)
    summary: dict = {}

    # ---- 1. masks -----------------------------------------------------------------
    wms = load_wms_masks()
    wfs_path = RAW / "ausseabed_wfs" / "MH370_Phase_2_Sonar_Imagery_Backscatter_Inverse_Deep_Tow__SSS__5m_2018_L0_Coverage.geojson"
    dt_geom = shape(json.loads(wfs_path.read_text())["features"][0]["geometry"]).buffer(0)
    dt_wfs = rasterise(dt_geom)
    masks = {
        "deeptow_sss": dt_wfs,
        "auv_sss": wms["auv_sss"],
        "gophoenix_sas": wms["gophoenix_sas"],
        "dhj_sas": wms["dhj_sas"],
    }
    union = np.zeros((NY, NX), bool)
    for m in masks.values():
        union |= m
    summary["area_km2_raster"] = {k: round(area_px(m)) for k, m in masks.items()}
    summary["area_km2_raster"]["union_all_sensors"] = round(area_px(union))
    summary["area_km2_raster"]["deeptow_sss_wms_render"] = round(area_px(wms["deeptow_sss"]))
    summary["area_km2_raster"]["union_with_wms_deeptow"] = round(
        area_px(wms["deeptow_sss"] | wms["auv_sss"] | wms["gophoenix_sas"] | wms["dhj_sas"]))
    summary["deeptow_wfs_vector_area_km2_epsg6933"] = round(area_ea(dt_geom))
    summary["deeptow_wfs_vector_area_km2_geodesic"] = round(area_geod(dt_geom))
    summary["deeptow_wfs_attribute_area_km2"] = 130961
    summary["validation_wms_vs_wfs_deeptow_km2"] = {
        "both": round(area_px(wms["deeptow_sss"] & dt_wfs)),
        "wms_only": round(area_px(wms["deeptow_sss"] & ~dt_wfs)),
        "wfs_only": round(area_px(dt_wfs & ~wms["deeptow_sss"])),
    }
    unique = {}
    others = {k: v for k, v in masks.items()}
    for k, m in masks.items():
        rest = np.zeros_like(m)
        for k2, m2 in others.items():
            if k2 != k:
                rest |= m2
        unique[k] = round(area_px(m & ~rest))
    summary["area_km2_unique_to_sensor"] = unique

    tc = tile_cache_mask()
    summary["validation_tilecache_z8_vs_union_km2"] = {
        "tilecache_total": round(area_px(tc)),
        "both": round(area_px(tc & union)),
        "tilecache_only": round(area_px(tc & ~union)),
        "union_only": round(area_px(union & ~tc)),
        "note": "zoom-8 tiles have ~0.5 km pixels, so edges are inflated/deflated by ~1 tile pixel",
    }

    # ---- 2. envelope (main connected area, interior holes filled) -------------------
    lab, n = ndi.label(union, structure=np.ones((3, 3)))
    sizes = ndi.sum(union, lab, range(1, n + 1))
    main = lab == (int(np.argmax(sizes)) + 1)
    env = ndi.binary_fill_holes(main)
    holes = env & ~union
    outliers = union & ~main
    summary["components"] = int(n)
    summary["area_km2_main_component"] = round(area_px(main))
    summary["area_km2_outlying_components"] = round(area_px(outliers), 2)
    summary["area_km2_envelope_holes_filled"] = round(area_px(env))
    summary["area_km2_interior_gaps"] = round(area_px(holes), 2)

    hl, hn = ndi.label(holes, structure=[[0, 1, 0], [1, 1, 1], [0, 1, 0]])
    hareas = ndi.sum(holes * PIX_KM2[:, None], hl, range(1, hn + 1))
    summary["interior_gap_count"] = int(hn)
    summary["interior_gap_area_by_threshold_km2"] = {
        f">={th}": [int((hareas >= th).sum()), round(float(hareas[hareas >= th].sum()), 2)]
        for th in (0.04, 0.1, 0.25, 1.0)}

    # ---- 3. vectorise ---------------------------------------------------------------
    env_poly = vectorise(env)
    if env_poly.geom_type != "Polygon":
        env_poly = max(env_poly.geoms, key=lambda g: g.area)
    env_poly = orient_ccw(Polygon(env_poly.exterior))
    union_vec = vectorise(union)
    per_sensor = {k: vectorise(m) for k, m in masks.items()}
    simp = {}
    for tol in (0.002, 0.005, 0.01):
        s = orient_ccw(env_poly.simplify(tol, preserve_topology=True))
        simp[tol] = s
    summary["envelope_vector_area_km2"] = {
        "unsimplified_epsg6933": round(area_ea(env_poly)),
        "unsimplified_geodesic": round(area_geod(env_poly)),
        **{f"simplified_{tol}deg_epsg6933": round(area_ea(s)) for tol, s in simp.items()},
        **{f"simplified_{tol}deg_nvert": len(s.exterior.coords) for tol, s in simp.items()},
        **{f"simplified_{tol}deg_hausdorff_km": round(env_poly.hausdorff_distance(s) * 111.195 * math.cos(math.radians(36)), 3)
           for tol, s in simp.items()},
    }
    summary["union_vector_area_km2_epsg6933"] = round(area_ea(union_vec))
    summary["per_sensor_vector_area_km2_epsg6933"] = {k: round(area_ea(g)) for k, g in per_sensor.items()}

    # gaps >= 0.1 km^2 as polygons
    gap_polys = []
    for i in np.where(hareas >= 0.1)[0]:
        gm = hl == (i + 1)
        rr, cc = np.where(gm)
        sub = np.zeros((NY, NX), bool)
        sub[rr, cc] = True
        gp = vectorise(sub)
        if gp.geom_type != "Polygon":
            gp = max(gp.geoms, key=lambda g: g.area)
        gap_polys.append((float(hareas[i]), orient_ccw(Polygon(gp.exterior))))
    gap_polys.sort(key=lambda t: -t[0])

    # ---- 4. arc sanity check ----------------------------------------------------------
    ref = [(-25.00, 101.84), (-30.00, 98.13), (-34.23, 93.74), (-35.00, 92.77), (-38.00, 88.18)]
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-41.0, -31.9, 0.01))
    summary["arc_reference_check"] = [
        {"lat": la, "lon_ref": lo, "lon_geo": round(float(geo.arc_lon_for_lat(la, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)), 3),
         "inside_envelope": bool(env_poly.contains(shapely.Point(lo, la)))} for la, lo in ref]
    arc_line = shapely.LineString(arc[:, ::-1])
    inside = arc_line.intersection(env_poly)
    lat_in = []
    for g in getattr(inside, "geoms", [inside]):
        ys = np.array(g.coords)[:, 1]
        lat_in.append([round(float(ys.min()), 3), round(float(ys.max()), 3)])
    summary["arc_latitude_ranges_inside_envelope"] = sorted(lat_in)
    import csv
    # GA/ATSB reference 7th arc used in the GA story map (caption: "positioned 40,000 feet above
    # sea level"); resampled to 0.01 deg latitude for the width computation.
    ga_arc_geom = shape(json.loads((RAW / "ga_featureservices" / "7thArc_SingleLine.geojson").read_text())
                        ["features"][0]["geometry"])
    ga_xy = np.array(ga_arc_geom.coords)
    ga_xy = ga_xy[np.argsort(ga_xy[:, 1])]
    gl = np.arange(-41.0, -31.9, 0.01)
    ga_arc = np.column_stack([gl, np.interp(gl, ga_xy[:, 1], ga_xy[:, 0])])
    offs = []
    for la in (-33.0, -34.0, -35.0, -36.0, -37.0, -38.0, -39.0):
        lo_sl = geo.arc_lon_for_lat(la, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
        lo_ga = float(np.interp(la, gl, ga_arc[:, 1]))
        i = np.argmin(abs(arc[:, 0] - la))
        de = (arc[i + 5, 1] - arc[i - 5, 1]) * 111.195 * math.cos(math.radians(la))
        dn = (arc[i + 5, 0] - arc[i - 5, 0]) * 111.195
        perp = (lo_ga - lo_sl) * 111.195 * math.cos(math.radians(la)) * dn / math.hypot(de, dn)
        offs.append({"lat": la, "lon_sea_level_arc": round(lo_sl, 3), "lon_ga_40kft_arc": round(lo_ga, 3),
                     "perp_offset_km_SE": round(perp, 1), "perp_offset_nm_SE": round(perp / NM, 1)})
    summary["ga_40kft_arc_vs_sea_level_arc"] = offs
    for fname, a in (("cross_arc_widths.csv", arc), ("cross_arc_widths_ga40kft_arc.csv", ga_arc)):
        widths = cross_arc_widths(env, union, np.round(np.arange(-40.2, -32.5, 0.1), 2), a)
        with open(OUT / fname, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(widths[0].keys()))
            w.writeheader()
            w.writerows(widths)
    summary["latitude_extent_envelope"] = [round(env_poly.bounds[1], 3), round(env_poly.bounds[3], 3)]
    summary["longitude_extent_envelope"] = [round(env_poly.bounds[0], 3), round(env_poly.bounds[2], 3)]

    regions = atsb_regions(env, ga_arc)
    reg_area = {k: area_px(m) for k, m in regions.items()}
    tot = sum(reg_area.values())
    summary["atsb_fig73_regions_area_km2"] = {k: round(v) for k, v in reg_area.items()}
    summary["atsb_fig73_regions_weighted_check"] = {
        "HC_pct": round(sum(reg_area[k] * ATSB_AREAS[k][0] for k in regions) / tot, 2),
        "LC_pct": round(sum(reg_area[k] * ATSB_AREAS[k][1] for k in regions) / tot, 2),
        "gap_pct": round(sum(reg_area[k] * ATSB_AREAS[k][2] for k in regions) / tot, 2),
        "atsb_combined": [97.4, 2.1, 0.5],
    }

    # ---- 5. context polygons from GA ArcGIS Online -------------------------------------
    fs = RAW / "ga_featureservices"
    bluefin = json.loads((fs / "Bluefin_21_AreaSearched2014.geojson").read_text())["features"]
    wide = json.loads((fs / "WideSearchArea.geojson").read_text())["features"][0]

    # ---- 6. polygons_atsb.json -----------------------------------------------------------
    src_ga = ("Geoscience Australia / AusSeabed, 'The Search for Flight MH370 - Phase 2 5 m resolution "
              "sonar images' (GA eCat 120969, doi:10.4225/25/5b0cd3b139def), CC BY 4.0; WFS layer "
              "ausseabed:MH370_Phase_2_Sonar_Imagery_Backscatter_Inverse_Deep_Tow__SSS__5m_2018_L0_Coverage "
              "and WMS layers for AUV SSS, Go Phoenix SAS, Dong Hai Jiu 101 SAS at "
              "https://warehouse.ausseabed.gov.au/geoserver/ows (retrieved 2026-11-05)")
    polys = []
    s = simp[0.005]
    polys.append({
        "name": "ATSB underwater search 2014-2017: sonar coverage envelope (all sensors, interior gaps filled)",
        "kind": "searched_area",
        "source": src_ga,
        "method": "machine-readable",
        "method_detail": ("Union of GA per-sensor Phase 2 sonar coverage (deep-tow SSS from GA WFS vector "
                          "coverage; AUV SSS, Go Phoenix SAS, DHJ101 SAS from GA WMS alpha masks rendered at "
                          "0.002 deg), largest connected component, interior holes filled, vectorised by "
                          "marching squares and Douglas-Peucker simplified with 0.005 deg tolerance."),
        "est_error_km": 0.5,
        "area_km2_epsg6933": round(area_ea(s)),
        "area_km2_geodesic": round(area_geod(s)),
        "n_vertices": len(s.exterior.coords),
        "notes": ("Represents seafloor imaged by sonar, which is what the ATSB counted as 'searched' "
                  "(~120,000 km2). Interior data holidays visible at 0.2 km resolution total only "
                  f"{summary['area_km2_interior_gaps']} km2 and are listed separately (kind=data_gap). "
                  "ATSB states 0.5% data gaps (0% detection) and 2.1% lower-probability-of-detection "
                  "areas (50-90%, nominal 70%) by a 100 m x 100 m metric; most are smaller than "
                  "200 m x 200 m and cannot be located from public rasters. Error budget: "
                  "simplification Hausdorff <= "
                  f"{summary['envelope_vector_area_km2']['simplified_0.005deg_hausdorff_km']} km, raster "
                  "pixel 0.18 x 0.22 km, sonar positioning ~0.05 km (ATSB p.55). Thin outlying "
                  f"strips not connected to the main area ({summary['area_km2_outlying_components']} km2) "
                  "are excluded."),
        "ring": ring_list(s.exterior),
    })
    s2 = simp[0.01]
    polys.append({
        "name": "ATSB underwater search 2014-2017: sonar coverage envelope, coarse (0.01 deg simplification)",
        "kind": "searched_area_coarse",
        "source": src_ga,
        "method": "machine-readable",
        "method_detail": "As above, simplified with 0.01 deg tolerance (for quick plotting / rasterising).",
        "est_error_km": 1.0,
        "area_km2_epsg6933": round(area_ea(s2)),
        "n_vertices": len(s2.exterior.coords),
        "notes": "Same envelope as the first entry; lower vertex count.",
        "ring": ring_list(s2.exterior),
    })
    for k, label in (("gophoenix_sas", "Go Phoenix ProSAS synthetic aperture sonar (Oct 2014 - Jun 2015)"),
                     ("dhj_sas", "Dong Hai Jiu 101 ProSAS synthetic aperture sonar (Feb - Aug 2016)"),
                     ("deeptow_sss", "Fugro Discovery / Fugro Equator Edgetech deep-tow side-scan sonar (Oct 2014 - Oct 2016)"),
                     ("auv_sss", "Fugro Supporter / Havila Harmony / Fugro Equator HUGIN 1000 AUV side-scan (Jan 2015 - Jan 2017)")):
        g = per_sensor[k]
        parts = sorted(getattr(g, "geoms", [g]), key=lambda p: -p.area)
        keep = [orient_ccw(Polygon(p.exterior).simplify(0.003, preserve_topology=True))
                for p in parts if area_ea(p) >= 5.0]
        polys.append({
            "name": f"Sensor footprint: {label}",
            "kind": f"sensor_footprint_{k}",
            "source": src_ga,
            "method": "machine-readable",
            "method_detail": ("Per-sensor coverage mask vectorised; parts >= 5 km2 kept; holes filled; "
                              "0.003 deg simplification. Full-detail geometry incl. holes and small parts "
                              "in derived/coverage_by_sensor.geojson."),
            "est_error_km": 0.4,
            "area_km2_epsg6933_unsimplified_with_holes": round(area_ea(g)),
            "area_km2_epsg6933_parts_kept_holes_filled": round(sum(area_ea(p) for p in keep)),
            "notes": ("Overlaps other sensors (AUV and SAS were used to infill deep-tow data holidays "
                      "and difficult terrain). AUV footprint is a network of thin swaths; the filled "
                      "outer rings overstate AUV-only area -- use the GeoJSON for detail." if k == "auv_sss"
                      else "Overlaps other sensors."),
            "rings": [ring_list(p.exterior) for p in keep],
        })
    for name, (hc, lc, gp_pct, desc) in ATSB_AREAS.items():
        g = vectorise(regions[name])
        parts = sorted(getattr(g, "geoms", [g]), key=lambda q: -q.area)
        keep = [orient_ccw(Polygon(q.exterior).simplify(0.005, preserve_topology=True))
                for q in parts if area_ea(q) >= 2.0]
        polys.append({
            "name": f"ATSB confidence area '{name}' (Figure 73) within the searched envelope",
            "kind": f"atsb_confidence_area_{name}",
            "source": src_ga + "; area definitions and statistics: ATSB, The Operational Search for MH370 (2017), pp. 95-96, Figure 73",
            "method": "machine-readable",
            "method_detail": ("Envelope pixels classified by foot-point latitude on, and signed perpendicular "
                              "distance from, the GA/ATSB 7th arc drawn at 40,000 ft (GA feature service "
                              "7thArc_SingleLine). Along-arc cuts at " f"{CUT_RED_ORANGE} S and {CUT_ORANGE_YELLOW} S "
                              "where the public coverage width changes; across-arc split of the southern block "
                              "at 27.5 NM NW / 25 NM SE (ATSB text). Parts >= 2 km2, 0.005 deg simplification."),
            "est_error_km": 0.5 if name in ("yellow",) else 3.0,
            "area_km2_raster": round(reg_area[name]),
            "atsb_definition": desc,
            "atsb_high_confidence_coverage_pct": hc,
            "atsb_lower_confidence_coverage_pct": lc,
            "atsb_data_gaps_pct": gp_pct,
            "implied_mean_detection_prob": {
                "low": round((hc * 0.95 + lc * 0.50) / 100, 4),
                "mid": round((hc * 0.975 + lc * 0.70) / 100, 4),
                "high": round((hc * 1.00 + lc * 0.90) / 100, 4),
                "formula": "HC*{0.95,0.975,1.0} + LC*{0.5,0.7,0.9} + gaps*0 (ATSB: HC >95%, LC 50-90% nominal 70%, gaps 0%)",
            },
            "notes": ("Boundaries between areas are inferred (along-arc cut uncertainty ~+/-0.06 deg latitude, "
                      "~5-7 km; the outer edges are the coverage envelope, error ~0.5 km). The ATSB figure "
                      "shows these areas as outlined polygons; our reconstruction reproduces the ATSB combined "
                      "statistics when area-weighted (see summary.atsb_fig73_regions_weighted_check)."),
            "rings": [ring_list(q.exterior) for q in keep],
        })
    for area_km2, gp in gap_polys:
        polys.append({
            "name": f"Interior data gap ({area_km2:.2f} km2) inside searched envelope",
            "kind": "data_gap",
            "source": src_ga,
            "method": "machine-readable",
            "method_detail": "Hole in the union of all four Phase 2 sonar coverage masks (0.002 deg raster).",
            "est_error_km": 0.3,
            "area_km2": round(area_km2, 2),
            "notes": "No sonar data in any public Phase 2 mosaic; ATSB assigned 0% detection to data gaps.",
            "ring": ring_list(gp.exterior),
        })
    for ft in bluefin:
        g = shape(ft["geometry"])
        polys.append({
            "name": f"Bluefin-21 AUV search area, Apr-May 2014 (ADV Ocean Shield acoustic detections), part {ft['properties']['FID']}",
            "kind": "searched_area_2014_bluefin21",
            "source": ("Geoscience Australia ArcGIS Online feature service "
                       "https://services1.arcgis.com/wfNKYeHsOyaFyPw3/arcgis/rest/services/Bluefin_21_AreaSearched2014/FeatureServer/0 "
                       "(used in GA story map 'The data behind the search for MH370'), retrieved 2026-11-05"),
            "method": "machine-readable",
            "est_error_km": 0.5,
            "area_km2_epsg6933": round(area_ea(g)),
            "notes": ("ATSB (2017, pp. 41-42) reports the Phoenix International Artemis (Bluefin-21) AUV search, "
                      "14 Apr - 28 May 2014, covered 860 km2 around the Ocean Shield TPL acoustic detections with "
                      "no debris found (GA polygons total " f"{sum(area_ea(shape(f['geometry'])) for f in bluefin):.0f}"
                      " km2). Far north of the 7th-arc search (~21 S, 104 E); not part of the ~120,000 km2."),
            "ring": ring_list(orient_ccw(g).exterior),
        })
    gw = shape(wide["geometry"])
    polys.append({
        "name": "Context only (NOT searched): ATSB June 2014 'Entire Search Area' (wide area, +/-100 NM of 7th arc)",
        "kind": "context_wide_area_2014",
        "source": ("Geoscience Australia ArcGIS Online feature service "
                   "https://services1.arcgis.com/wfNKYeHsOyaFyPw3/arcgis/rest/services/WideSearchArea/FeatureServer/0, "
                   "retrieved 2026-11-05"),
        "method": "machine-readable",
        "est_error_km": None,
        "area_km2_epsg6933": round(area_ea(gw)),
        "notes": wide["properties"].get("Caption_ENG"),
        "ring": ring_list(orient_ccw(gw).exterior),
    })
    meta = {
        "description": ("Polygons of the seafloor searched by the ATSB-led MH370 underwater search "
                        "(Oct 2014 - Jan 2017) derived from Geoscience Australia public data; plus "
                        "the 2014 Bluefin-21 area and the 2014 wide area for context. Coordinates are "
                        "[lon, lat] WGS84, closed rings, counter-clockwise exteriors."),
        "built_by": "scripts/search_build_atsb_polygons.py",
        "built": "2026-11-05",
        "atsb_published_area_km2": "'in excess of 120,000' (ATSB 2017 p. i); 'more than 120,000 ... searched and eliminated with a high degree of confidence' (p. ii); 'in the order of 120,000' (p. 63)",
        "atsb_detection_confidence": {
            "high_confidence_coverage": ">95% confidence of detection; 97.4% of combined area",
            "lower_probability_of_detection": "50-90% (nominal 70%); 2.1% of combined area",
            "data_gaps": "0%; 0.5% of combined area",
            "source": "ATSB, The Operational Search for MH370, 3 Oct 2017, pp. 95-96 (Figure 73)",
        },
        "summary": summary,
        "polygons": polys,
    }
    (RAW / "polygons_atsb.json").write_text(json.dumps(meta, indent=1))

    # ---- 7. GeoJSON + NetCDF ---------------------------------------------------------------
    def fc(feats):
        return {"type": "FeatureCollection", "features": feats}

    (OUT / "coverage_union_detailed.geojson").write_text(json.dumps(fc([{
        "type": "Feature", "properties": {"name": "union of all Phase 2 sonar coverage (0.002 deg raster, vectorised)",
                                          "area_km2_epsg6933": round(area_ea(union_vec))},
        "geometry": mapping(shapely.set_precision(union_vec, 1e-5))}])))
    (OUT / "coverage_by_sensor.geojson").write_text(json.dumps(fc([{
        "type": "Feature", "properties": {"sensor": k, "area_km2_epsg6933": round(area_ea(g))},
        "geometry": mapping(shapely.set_precision(g, 1e-5))} for k, g in per_sensor.items()])))
    ds = coverage_fraction_common_grid({**masks, "any": union, **{f"atsb_area_{k}": m for k, m in regions.items()}})
    ds.attrs.update({
        "title": "Fraction of each 0.05 deg common-grid cell covered by ATSB 2014-2017 Phase 2 sonar data",
        "source": "Geoscience Australia / AusSeabed MH370 Phase 2 sonar coverage (CC BY 4.0)",
        "note": ("Coverage = sonar imagery present; not a probability of detection. ATSB: >95% detection "
                 "in good data, 50-90% in LPD areas (2.1%), 0% in data gaps (0.5%). frac_atsb_area_* = "
                 "fraction of cell inside each reconstructed ATSB Figure-73 confidence area (red: HC 98.7/LC 1.1/"
                 "gap 0.2 %; orange: 91.5/7.8/0.7; yellow: 97.8/1.1/1.1; purple: 97.9/1.5/0.6)."),
        "built_by": "scripts/search_build_atsb_polygons.py",
    })
    ds.to_netcdf(OUT / "coverage_frac_common_grid.nc", engine="h5netcdf")
    cell = (np.radians(0.05) * R_KM) ** 2 * np.cos(np.radians(ds.lat.values))[:, None]
    summary["common_grid_any_area_km2"] = round(float((ds["frac_any"].values * cell).sum()))
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))

    # ---- 8. QA figure ------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 10))
    rgb = np.ones((NY, NX, 3))
    cols = {"deeptow_sss": (0.72, 0.72, 0.72), "gophoenix_sas": (0.35, 0.6, 0.9),
            "dhj_sas": (0.2, 0.7, 0.4), "auv_sss": (0.85, 0.3, 0.2)}
    for k in ("deeptow_sss", "gophoenix_sas", "dhj_sas", "auv_sss"):
        rgb[masks[k]] = cols[k]
    rgb[holes] = (0, 0, 0)
    ax.imshow(rgb, extent=[LON0, LON0 + NX * RES, LAT1 - NY * RES, LAT1], interpolation="nearest")
    x, y = s.exterior.xy
    ax.plot(x, y, "b-", lw=0.6, label="envelope (0.005 deg simplified)")
    ax.plot(arc[:, 1], arc[:, 0], "k-", lw=0.8, label="7th arc (sea level, mh370.geo)")
    ax.plot(ga_arc[:, 1], ga_arc[:, 0], "k--", lw=0.8, label="GA/ATSB 7th arc (40,000 ft)")
    rcol = {"red": "red", "orange": "darkorange", "yellow": "gold", "purple": "purple"}
    for name in ("purple", "orange", "yellow", "red"):
        g = vectorise(regions[name])
        for q in getattr(g, "geoms", [g]):
            if area_ea(q) >= 2.0:
                xx, yy = q.exterior.xy
                ax.plot(xx, yy, "-", color=rcol[name], lw=1.2)
        ax.plot([], [], "-", color=rcol[name], label=f"ATSB Fig.73 area '{name}' (reconstructed)")
    for la, lo in ref:
        ax.plot(lo, la, "k+", ms=8)
    for k, c in cols.items():
        ax.plot([], [], "s", color=c, label=k)
    ax.set_xlim(84.8, 96.4)
    ax.set_ylim(-40.4, -32.4)
    ax.set_aspect(1 / math.cos(math.radians(36.5)))
    ax.grid(True, lw=0.3)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(f"ATSB 2014-17 sonar coverage from GA public data: union {summary['area_km2_raster']['union_all_sensors']:,} km2")
    fig.savefig(OUT / "coverage_qa.png", dpi=120, bbox_inches="tight")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
