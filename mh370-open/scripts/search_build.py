"""Build the search-coverage / POD layer (workstream C, part 1).

Run:  .venv/bin/python -I scripts/search_build.py
Writes:
  data/derived/search_pod.nc                 pod, pod_low, pod_high, searched_frac*, cov_<campaign>
  outputs/search/search_polygons.geojson     reconstructed polygons with POD attributes
  outputs/search/arc_profile.csv             searched cross-arc width vs latitude
  outputs/search/area_summary.csv / .json    areas vs published totals, overlaps
  outputs/search/candidates_pod.csv          POD at published candidate points
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mh370 import grid, search  # noqa: E402

OUT = ROOT / "outputs" / "search"
OUT.mkdir(parents=True, exist_ok=True)
DER = ROOT / "data" / "derived"

PUBLISHED = {
    "ATSB_2014_17": ("~120,000 (ATSB 2017: 'in excess of 120,000')", 120000),
    "OI_2018": (">112,000 (OI/Malaysia 29 May 2018); OI cumulative 2018-26 '>140,000'", 112000),
    "OI_2025_26": ("7,571 (AAIB 8 Mar 2026, post-contract only)", 7571),
    "Bluefin21_2014": ("~860 (ATSB)", 860),
}


def main():
    t0 = time.time()
    items = search.build_items()
    print(f"{len(items)} search items built ({time.time()-t0:.1f}s)")

    # ---------------- areas ----------------
    rows = []
    unions = {}
    for b in ["best", "low", "high"]:
        for c in search.CAMPAIGNS:
            unions[(c, b)] = search.campaign_union(items, c, b)
    for c in search.CAMPAIGNS:
        u = unions[(c, "best")]
        rows.append(dict(campaign=c, area_km2_best=round(search.area_km2(u)),
                         area_km2_geodesic=round(search.geodesic_area_km2(u)),
                         area_km2_low_geometry=round(search.area_km2(unions[(c, "low")])),
                         area_km2_high_geometry=round(search.area_km2(unions[(c, "high")])),
                         published=PUBLISHED[c][0]))
    allu = {b: unary_union([unions[(c, b)] for c in search.CAMPAIGNS]) for b in ["best", "low", "high"]}
    rows.append(dict(campaign="ALL (union)", area_km2_best=round(search.area_km2(allu["best"])),
                     area_km2_geodesic=round(search.geodesic_area_km2(allu["best"])),
                     area_km2_low_geometry=round(search.area_km2(allu["low"])),
                     area_km2_high_geometry=round(search.area_km2(allu["high"])),
                     published="sum of published ~240,000 (120k+112k+7.6k+0.9k), before overlap"))
    # sub-components
    for it in items:
        if it.campaign in ("OI_2018", "OI_2025_26") or it.pod_class in ("ATSB_area", "HPSA_gap", "GoPhoenix_gap"):
            rows.append(dict(campaign=f"  {it.campaign}: {it.name}", area_km2_best=round(search.area_km2(it.geom)),
                             area_km2_geodesic=round(search.geodesic_area_km2(it.geom)),
                             area_km2_low_geometry=round(search.area_km2(it.geometry_for("low"))),
                             area_km2_high_geometry=round(search.area_km2(it.geometry_for("high"))),
                             published=""))
    gaps = unary_union([it.geom for it in items if it.pod_class == "ATSB_gap"])
    rows.append(dict(campaign="  ATSB interior data gaps (19 holes)", area_km2_best=round(search.area_km2(gaps), 1),
                     area_km2_geodesic=round(search.geodesic_area_km2(gaps), 1), area_km2_low_geometry=np.nan,
                     area_km2_high_geometry=np.nan, published="ATSB: 0.5% gaps (~600 km2, mostly <200 m)"))
    overlaps = {}
    cs = search.CAMPAIGNS
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            a = search.area_km2(unions[(cs[i], "best")].intersection(unions[(cs[j], "best")]))
            if a > 0.5:
                overlaps[f"{cs[i]} & {cs[j]}"] = round(a)
    df_area = pd.DataFrame(rows)
    df_area.to_csv(OUT / "area_summary.csv", index=False)
    print(df_area.to_string())
    print("overlaps", overlaps)

    # ---------------- raster ----------------
    t1 = time.time()
    r = search.rasterise(items, sub=10)
    print(f"rasterised in {time.time()-t1:.0f}s")
    lat, lon = grid.common_grid()
    A = grid.cell_area_km2().values
    ds = xr.Dataset(coords={"lat": lat, "lon": lon})
    desc = {
        "pod": "probability the wreck would have been detected had it been in the cell (cell mean), best estimate",
        "pod_low": "pessimistic bound: low per-campaign POD, eroded geometry, max() combination (correlated misses)",
        "pod_high": "optimistic bound: high per-campaign POD, dilated geometry, independent combination",
        "searched_frac": "fraction of cell area inside any searched polygon (best geometry)",
        "searched_frac_low": "as searched_frac with eroded geometry",
        "searched_frac_high": "as searched_frac with dilated geometry",
    }
    for k, v in r.items():
        da = xr.DataArray(v.astype(np.float32), dims=("lat", "lon"))
        da.attrs["long_name"] = desc.get(k, f"fraction of cell covered by campaign {k[4:]} (best geometry, d>0)")
        da.attrs["units"] = "1"
        ds[k] = da
    ds.attrs = dict(
        title="MH370 seafloor search coverage: probability of detection (POD) on the common grid",
        workstream="C (search + combine)",
        method=("Paint-order POD per campaign from reconstructed polygons; campaigns combined as "
                "1-prod(1-d) (best/high) or max (low); 10x10 sub-sampling per 0.05 deg cell. "
                "See outputs/search/README.md."),
        campaigns=", ".join(search.CAMPAIGNS),
        created=time.strftime("%Y-%m-%d"),
        caveat=("OI 2025-26 footprints are ASSUMED (no official map); OI 2018 north of 26.3S is "
                "INFERRED; ATSB from GA machine-readable coverage."),
    )
    grid.save(ds, str(DER / "search_pod.nc"))
    for k in ["pod", "pod_low", "pod_high", "searched_frac"]:
        print(f"{k}: area-weighted sum = {np.sum(r[k]*A):,.0f} km2")

    # ---------------- GeoJSON ----------------
    gj = search.items_geojson(items)
    with open(OUT / "search_polygons.geojson", "w") as f:
        json.dump(gj, f)

    # ---------------- arc profile ----------------
    t1 = time.time()
    prof = search.cross_arc_profile(items)
    prof.to_csv(OUT / "arc_profile.csv", index=False, float_format="%.4g")
    print(f"arc profile in {time.time()-t1:.0f}s")
    pr = prof[(prof.lat >= -40.5) & (prof.lat <= -20.5)]
    print(pr.iloc[::20][["lat", "arc_lon", "searched_width_km", "contig_nw_km", "contig_se_km",
                         "eff_width_km", "mean_pod_25nm", "frac_searched_70nm"]].to_string())

    # ---------------- candidates ----------------
    crow = []
    for lab, la, lo, note in search.candidate_points():
        pb, parts = search.pod_at(items, np.array([lo]), np.array([la]), "best", return_parts=True)
        pl = search.pod_at(items, np.array([lo]), np.array([la]), "low")
        ph = search.pod_at(items, np.array([lo]), np.array([la]), "high")
        s_km, n_km = search.arc_coords(np.array([la]), np.array([lo]))
        covered = [c for c, d in parts.items() if np.isfinite(d[0]) and d[0] > 0]
        crow.append(dict(candidate=lab, lat=la, lon=round(lo, 4), note=note,
                         n_from_arc_km=round(float(n_km[0]), 1), s_along_arc_km=round(float(s_km[0]), 1),
                         pod=round(float(pb[0]), 3), pod_low=round(float(pl[0]), 3),
                         pod_high=round(float(ph[0]), 3), searched_by=";".join(covered) or "none"))
    dfc = pd.DataFrame(crow)
    dfc.to_csv(OUT / "candidates_pod.csv", index=False)
    print(dfc.to_string())

    # ---------------- CAPTION cross-check of OI 2018 ----------------
    xcheck = {}
    try:
        from pyproj import Geod
        from shapely.geometry import Point
        g = Geod(ellps="WGS84")
        areas = json.load(open(search.F_CAPTION_AREAS))
        for nm, camp in [("Ocean Infinity 2018 search", "OI_2018"),
                         ("Australia/China/Malaysia 2014-2017 search", "ATSB_2014_17")]:
            cs_ = [x for x in areas if x["name"].startswith(nm)][0]["coords"]
            # compare against the outer boundary of our union of ATSB+OI2018 (CAPTION outlines
            # are drawn as envelopes)
            U = unary_union([unions[("ATSB_2014_17", "best")], unions[("OI_2018", "best")]]) if camp == "OI_2018" else unions[(camp, "best")]
            B = U.boundary
            dd = []
            for lo_, la_ in cs_:
                p = Point(lo_, la_)
                q = B.interpolate(B.project(p))
                dd.append(g.inv(lo_, la_, q.x, q.y)[2] / 1000)
            dd = np.array(dd)
            xcheck[nm] = dict(n_vertices=len(dd), median_km=round(float(np.median(dd)), 2),
                              p90_km=round(float(np.percentile(dd, 90)), 2), max_km=round(float(dd.max()), 2),
                              caption_lat_range=[round(min(c[1] for c in cs_), 3), round(max(c[1] for c in cs_), 3)])
    except Exception as e:  # noqa: BLE001
        xcheck["error"] = repr(e)
    print("CAPTION cross-check:", xcheck)

    summary = dict(
        areas=df_area.to_dict(orient="records"), overlaps_km2=overlaps, caption_crosscheck=xcheck,
        raster_area_weighted_km2={k: round(float(np.sum(r[k] * A))) for k in
                                  ["pod", "pod_low", "pod_high", "searched_frac", "searched_frac_low",
                                   "searched_frac_high"] + [f"cov_{c}" for c in search.CAMPAIGNS]},
        pod_table=search.POD_TABLE,
    )
    with open(OUT / "area_summary.json", "w") as f:
        json.dump(summary, f, indent=1, default=float)
    print(f"done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
