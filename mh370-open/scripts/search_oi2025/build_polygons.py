"""Build reconstructed polygons for the Ocean Infinity 2025-2026 MH370 search.

Run from the project root:
    .venv/bin/python -I scripts/search_oi2025/build_polygons.py

Inputs (see data/raw/oi2025_search/SOURCE.md):
  data/derived/oi2025_search/search_areas.json     CAPTION "Search areas.kmz" geometries (kmlgeoms.py)
  data/derived/oi2025_search/armada_tracks_hourly.csv  CAPTION Armada AIS tracks, hourly (tracks.py)
  data/derived/oi2025_search/hpsa_polys.json       HPSA digitised from Iannello Feb-2023 map (hpsa2.py)
  data/derived/oi2025_search/racetrack.json        Ulich-Iannello 70-NM-glide racetrack fit (race4.py)
  Edge measurements of the OI March-2024 slide (slide3/4/6/7.py) and of Iannello's
  georeferenced maps (red4.py, redsn.py, iannello_edges.py) are hard-coded below with comments.

Geometry is built in an arc-following frame (arcframe.py): s = along-arc distance (km, +NE,
0 at the latitude of the UGIB LEP, 34.2342 S) of the foot point on the sea-level 7th arc from
mh370.geo, n = signed normal distance (km, + = SE / outward side of the arc).

Outputs:
  data/raw/oi2025_search/polygons_oi2025.json
  outputs/search/qa/oi2025_overview_*.png
"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "measure"))
sys.path.insert(0, os.path.join(ROOT, "src"))
from arcframe import from_sn, to_sn  # noqa: E402
from pyproj import Geod, Transformer  # noqa: E402
from shapely.geometry import MultiPoint, Polygon  # noqa: E402
from scipy.optimize import brentq  # noqa: E402

G = Geod(ellps="WGS84")
T6933 = Transformer.from_crs("EPSG:4326", "EPSG:6933", always_xy=True)
TALB = Transformer.from_crs(
    "EPSG:4326",
    "+proj=aea +lat_1=-33 +lat_2=-36.5 +lat_0=-34.5 +lon_0=93.5 +datum=WGS84 +units=m",
    always_xy=True,
)
DER = os.path.join(ROOT, "data", "derived", "oi2025_search")
RAW = os.path.join(ROOT, "data", "raw", "oi2025_search")
OUT = os.path.join(ROOT, "outputs", "search", "qa")


# ----------------------------------------------------------------------------- helpers
def close(r):
    r = [[round(float(p[0]), 5), round(float(p[1]), 5)] for p in r]
    if r[0] != r[-1]:
        r.append(r[0])
    return r


def densify(ring, step_km=1.0):
    out = []
    for (lo1, la1), (lo2, la2) in zip(ring[:-1], ring[1:]):
        _, _, d = G.inv(lo1, la1, lo2, la2)
        n = max(1, int(np.ceil(d / 1000 / step_km)))
        out.append((lo1, la1))
        if n > 1:
            out += list(G.npts(lo1, la1, lo2, la2, n - 1))
    out.append(tuple(ring[-1]))
    return out


def ring_areas(ring):
    r = densify(ring)
    lon, lat = zip(*r)
    ag = abs(G.polygon_area_perimeter(lon, lat)[0]) / 1e6
    x, y = T6933.transform(lon, lat)
    a6 = Polygon(zip(x, y)).area / 1e6
    x, y = TALB.transform(lon, lat)
    aa = Polygon(zip(x, y)).area / 1e6
    return np.array([ag, a6, aa])


def areas(rings):
    a = sum(ring_areas(r) for r in rings)
    return {"geodesic_WGS84": round(a[0], 1), "EPSG6933": round(a[1], 1), "local_albers": round(a[2], 1)}


def strip(s0, s1, n_in, n_out, ds=1.0):
    """Closed ring in lon/lat for {s0<=s<=s1, n_in(s) <= n <= n_out(s)} (n_in, n_out callables)."""
    ss = np.r_[np.arange(s0, s1, ds), s1]
    a = np.array([n_in(s) for s in ss])
    b = np.array([n_out(s) for s in ss])
    lo1, la1 = from_sn(ss, a)
    lo2, la2 = from_sn(ss[::-1], b[::-1])
    return close(np.r_[np.c_[lo1, la1], np.c_[lo2, la2]])


def sn_summary(rings):
    lon = np.concatenate([np.array(r)[:, 0] for r in rings])
    lat = np.concatenate([np.array(r)[:, 1] for r in rings])
    if lat.max() > -31.5 or lat.min() < -38.5:  # outside the arc-frame table
        return {"s_km": None, "n_km": None,
                "lat": [round(float(lat.min()), 3), round(float(lat.max()), 3)],
                "lon": [round(float(lon.min()), 3), round(float(lon.max()), 3)]}
    s, n = to_sn(lon, lat)
    return {"s_km": [round(float(s.min()), 1), round(float(s.max()), 1)],
            "n_km": [round(float(n.min()), 1), round(float(n.max()), 1)],
            "lat": [round(float(lat.min()), 3), round(float(lat.max()), 3)],
            "lon": [round(float(lon.min()), 3), round(float(lon.max()), 3)]}


# ----------------------------------------------------------------------------- inputs
cap = json.load(open(os.path.join(DER, "search_areas.json")))
cap_prop = [o["coords"] for o in cap if o["name"] == "Ocean Infinity proposed 2024 area"]
cap_SE, cap_NW = close(cap_prop[0]), close(cap_prop[1])
cap_bm = close([o for o in cap if o["name"] == "Blelly/Marchand"][0]["coords"])
cap_ig = [close(o["coords"]) for o in cap if o["name"] == "Independent Group Hotspot"]
hpsa = json.load(open(os.path.join(DER, "hpsa_polys.json")))
race = json.load(open(os.path.join(DER, "racetrack.json")))
tr = pd.read_csv(os.path.join(DER, "armada_tracks_hourly.csv"), parse_dates=["time_utc"])

S_IG, _ = to_sn(93.7875, -34.2342)
S_IG = float(S_IG[0])  # ~ +3.0 km

# ----------------------------------------------------------------------------- OI March-2024 slide
# Measured on images/radiantphysics_2024_03_searcharea-1.png (OI slide, 1059x720 px), in a frame
# aligned with the slide's dotted 7th arc (RANSAC line through 48 dots, rms 0.9 px). u = px along
# arc from the "IG Hotspot" square, v = px normal to arc (+SE).
#   NW strip: u in [-193.0, +89.0]; inner edge (OI-2018 coverage edge) v = 57.5 (u<-55) / 51.2 (u>=-55)
#             outer edge v = 78.74 - 0.0162 u   (rms 0.4 px)
#   SE strip: u in [-200.7, +86.0]; inner edge v = 68.6 (u<-55) / 67.0 (u>=-55)
#             outer edge v = 95.48 - 0.0088 u   (rms 0.4 px)
#   Inner edges are the orange-overlay start; the coverage boundary (black line centre) is ~1.2 px inward.
# Scale K km/px from the width of OI-2018 coverage between the two inner edges (115.8 px NE part,
# 123.6 px SW part) vs the OI-supplied 2018 outline georeferenced from Iannello's map (111.3 / 119.9 km)
# -> 0.961 / 0.970; cross-check: total outer-to-outer width 173.8 px = "~45 nm" each side (166.7 km)
# -> 0.959.  Adopted K = 0.966 +/- 0.01.  Offset of the slide arc from our sea-level arc: +1.6 km
# (+/-1.1) from the IG-hotspot square (v=+1.4 px) and coverage-edge midpoints.
K, OFF, U_STEP = 0.966, 1.6, -55.0
s_u = lambda u: S_IG + u * K  # noqa: E731
u_s = lambda s: (s - S_IG) / K  # noqa: E731
slide = {
    "NW": dict(s0=s_u(-193.0), s1=s_u(89.0),
               n_in=lambda s: -((57.5 - 1.2) if s < s_u(U_STEP) else (51.2 - 1.2)) * K + OFF,
               n_out=lambda s: -(78.74 - 0.0162 * u_s(s)) * K + OFF),
    "SE": dict(s0=s_u(-200.7), s1=s_u(86.0),
               n_in=lambda s: ((68.6 - 1.2) if s < s_u(U_STEP) else (67.0 - 1.2)) * K + OFF,
               n_out=lambda s: (95.48 - 0.0088 * u_s(s)) * K + OFF),
}
sl_NW = strip(**slide["NW"])
sl_SE = strip(**slide["SE"])

# ----------------------------------------------------------------------------- Iannello's red outline
# Red "OI proposed search" outline digitised from 3 georeferenced Google-Earth maps (radiantphysics
# 2025-03 image-1, image-4, image-9; quadratic graticule fits, rms 0.15-1 km; validated against
# CAPTION AIS hourly positions shown as purple dots: median 0.8 km, mean offset 0.3 km).
ian = {
    "NW": dict(s0=-191.5, s1=95.4, n_in=lambda s: -52.2 if s < -55 else -46.7,
               n_out=lambda s: -79.95 + 0.0023 * s),
    "SE": dict(s0=-194.0, s1=91.5, n_in=lambda s: 67.8 if s < -55 else 63.7,
               n_out=lambda s: 93.61 - 0.0042 * s),
}
ia_NW = strip(**ian["NW"])
ia_SE = strip(**ian["SE"])

# ----------------------------------------------------------------------------- surveyed areas
SE = slide["SE"]


def area_of(s0, s1, n_in, n_out):
    return ring_areas(strip(s0, s1, n_in, n_out, ds=2.0))[0]


# Post-contract survey (MOT: 25-28 Mar 2025 + 31 Dec 2025-23 Jan 2026 = 7,571 km2 [7,571.46 implied by
# 15,000 - 7,428.54]). Along-arc start S1 = position of Armada 78 06 on 25 Mar 2025 (AIS s = -141..-112;
# OI daily-report count restarted at "Day 1" = 25 Mar), end S2 = NE end of SE strip (slide 86, Iannello
# 91.5, CAPTION 83; AIS reaches 97) -> 88.  Outer edge: constant n solved so that area = 7,571.46 km2.
S1, S2 = -135.0, 88.0
N_OUT_POST = brentq(lambda no: area_of(S1, S2, SE["n_in"], lambda s: no) - 7571.46, 85, 130, xtol=0.02)
post = strip(S1, S2, SE["n_in"], lambda s: N_OUT_POST)
# Variant constrained only by the AIS envelope (ship positions reach n = 100-103 km in every period)
post_ais = strip(S1, S2, SE["n_in"], lambda s: 101.0)

# Pre-contract survey 11-24 Mar 2025 (Armada 78 06, AIS s = -275..-125, n = 64..103)
pre_SW = strip(-278.0, S1, lambda s: SE["n_in"](s) if s >= SE["s0"] else 63.0, lambda s: 101.0)
all_SE = strip(-278.0, S2, lambda s: SE["n_in"](s) if s >= SE["s0"] else 63.0,
               lambda s: N_OUT_POST)

# Remaining (inner, NW) strip: slide geometry; plus variant with outer edge solved for 7,428.54 km2
NW = slide["NW"]
N_OUT_REM = brentq(lambda no: area_of(NW["s0"], NW["s1"], NW["n_in"], lambda s: no) - 7428.54,
                   -120, -60, xtol=0.02)
rem_cal = strip(NW["s0"], NW["s1"], NW["n_in"], lambda s: N_OUT_REM)

# Feb 2025 infill (pre-contract, Armada 78 06): region containing the infill sorties (convex hull of
# AIS hourly positions with SOG < 6 kn, 23 Feb 12:00 - 28 Feb 06:00 UTC).
m = (tr.leg.str.startswith("A7806_P1") & (tr.time_utc >= "2025-02-23T12:00") &
     (tr.time_utc < "2025-02-28T06:00") & (tr.sog_kts.fillna(0) < 6) & (tr.lat < -33.5))
hull = MultiPoint(list(zip(tr.lon[m], tr.lat[m]))).convex_hull
feb_hull = close(list(hull.exterior.coords))

# ----------------------------------------------------------------------------- assemble
E = []


def add(name, rings, source, method, est_error_km, notes, **extra):
    d = {"name": name, "source": source, "method": method, "est_error_km": est_error_km,
         "notes": notes, "rings": rings, "area_km2": areas(rings), "extent": sn_summary(rings)}
    d.update(extra)
    E.append(d)


SRC_SLIDE = ("Ocean Infinity slide '2024 Proposed Search Area ~15,000km2, Extending out ~45nm from 7th arc' "
             "(shown 3 Mar 2024; copy: mh370.radiantphysics.com/wp-content/uploads/2024/03/searcharea-1.png)")
add("OI_contract_area_best__slide_digitised", [sl_NW, sl_SE], SRC_SLIDE + "; digitised in this work",
    "digitised", 3.0,
    "BEST ESTIMATE of the ~15,000 km2 'no find, no fee' contract area (MOT: 'a new area estimated at "
    "15,000 km2'), assumed identical to OI's March-2024 proposal (two strips outside the ATSB+OI-2018 "
    "coverage, ~33-36 S). Slide has no graticule: registered to the slide's own dotted 7th arc, the "
    "IG-hotspot square and the OI-2018 coverage edges. Edge errors ~2-3 km (scale +/-1%, arc offset "
    "+/-1.1 km, 1 px ~1 km), strip ends ~5 km. Total 14,861 km2 vs nominal ~15,000. That the signed "
    "contract polygon equals this slide is an ASSUMPTION (no official map published).",
    parts=["NW (inner) strip", "SE (outer) strip"])
add("OI_contract_area_alt__CAPTION_kml", [cap_NW, cap_SE],
    "mh370-caption.net 'Search areas.kmz' (placemarks 'Ocean Infinity proposed 2024 area'); CAPTION "
    "states coordinates 'drawn from the presentation given at the 10th anniversary ceremony'",
    "machine-readable", 6.0,
    "Machine-readable but itself a hand digitisation of the same slide by CAPTION. Open linestrings closed "
    "here with a straight inner edge. Relative to the slide digitisation its SE outer edge is ~5-6 km "
    "further out (n~99 km) and its NW outer edge agrees (n~-74 km). Total 15,812 km2.",
    parts=["NW (inner) strip", "SE (outer) strip"])
add("OI_contract_area_alt__Iannello_map_digitised", [ia_NW, ia_SE],
    "Red 'OI proposed search' outline on V. Iannello maps of 4 Mar 2025 and 31 Mar 2025 "
    "(radiantphysics 2025/03 image-1, image-4, image-9)", "digitised", 6.0,
    "Georeferencing of the maps is good to ~1 km (validated with AIS), but the red outline is Iannello's own "
    "rendering of the OI proposal. NW outer edge ~6 km further out than slide/CAPTION (n~-80 km); SE outer "
    "edge agrees with slide (n~93.6 km). Total 16,863 km2.", parts=["NW (inner) strip", "SE (outer) strip"])

add("OI2025_26_surveyed_post_contract_best", [post],
    "Constructed: AIS tracks (CAPTION KMLs) + MOT/AAIB area figures + OI daily reports + slide inner edge",
    "assumed", 8.0,
    f"Best-estimate footprint of the ~7,571 km2 counted by MOT/AAIB for the two post-signing phases "
    f"(Phase 1: 25-28 Mar 2025, Armada 78 06; Phase 2: 31 Dec 2025-23 Jan 2026, Armada 86 05; 28 days). "
    f"SE (outer) side of the 7th arc only. s from {S1} to {S2} km; inner edge = previous-coverage edge "
    f"(slide); outer edge n = {N_OUT_POST:.1f} km CHOSEN so area = 7,571.46 km2 (AIS ship positions reach "
    f"n = 100-103 km, i.e. beyond the proposal's ~93-95 km outer edge, consistent with Iannello's remark that "
    f"the Mar-2025 work was 'wider than the area proposed'). Errors: ends +/-10 km, outer edge +/-5 km. "
    f"Note the official figure is a line-km x swath (~1.82 km) tally, not a polygon area.",
    n_out_km=round(N_OUT_POST, 2), s_range_km=[S1, S2])
add("OI2025_26_surveyed_post_contract_AIS_envelope", [post_ais],
    "Constructed from AIS envelope (CAPTION KMLs)", "assumed", 8.0,
    "Same as best estimate but outer edge fixed at n = 101 km from the AIS envelope instead of calibrated to "
    "the official area.")
add("OI2025_pre_contract_SW_survey_Mar11-24", [pre_SW],
    "Constructed from AIS track of Armada 78 06, 11-24 Mar 2025 (CAPTION KML) + Iannello 31 Mar 2025 post",
    "assumed", 8.0,
    "Pre-signing survey (MOT: 'additional survey activities were undertaken within the broader search "
    "area before the formal signing'). New ground SE of the arc, from the SW end of the proposal's SE strip "
    "(~35.6-36.1 S) to ~36.6 S, i.e. partly OUTSIDE the March-2024 proposal ('starting further southwest "
    "and wider than the area proposed' - Iannello). Envelope n = 63/66-101 km; area not published; "
    "AUV coverage inside the envelope may be incomplete.")
add("OI2025_26_all_new_ground_SE_of_arc", [all_SE], "Union of the two previous entries", "assumed", 8.0,
    "All 2025-26 new-ground coverage (pre- and post-contract) SE of the 7th arc, 11 Mar 2025-23 Jan 2026. "
    "Use this (not the contractual 7,571 km2 piece) for search-POD purposes.")
add("OI2025_pre_contract_infill_region_Feb23-28", [feb_hull],
    "Convex hull of Armada 78 06 hourly AIS positions (SOG<6 kn), 23 Feb 12:00-28 Feb 06:00 UTC 2025",
    "assumed", 10.0,
    "NOT a coverage polygon: region inside which infill sorties targeted ATSB/OI-2018 data holidays and "
    "low-quality data (incl. the High Priority Search Area). Actual infill patches unknown (likely a small "
    "fraction of the hull). Re-scan of previously searched ground, not new area.")
add("OI2025_26_remaining_unsearched_NW_strip_slide", [sl_NW], SRC_SLIDE + "; digitised in this work",
    "digitised", 3.0,
    "Inner (NW) strip of the proposal: no Armada AIS positions there in either post-contract phase; "
    "commenters describe the remaining area as 'the rectangle on the inside of the 7th arc'. Slide area "
    "6,902 km2 vs MOT 'remaining 7,428.54 km2' (which is simply 15,000 - 7,571.46).")
add("OI2025_26_remaining_NW_strip_calibrated_7428", [rem_cal], "Slide geometry with outer edge calibrated",
    "assumed", 5.0,
    f"NW strip with constant outer edge n = {N_OUT_REM:.1f} km solved so area = 7,428.54 km2 (slide outer "
    f"edge -73 to -77 km; CAPTION -74.5; Iannello -80).", n_out_km=round(N_OUT_REM, 2))

add("High_Priority_Search_Area_HPSA", [close(p) for p in hpsa["hpsa"]],
    "V. Iannello 11 Feb 2023 'A High Priority Area to Search for MH370' (Priority-Area-Zoom.png)",
    "digitised", 0.2,
    "Seabed missed by GO Phoenix (terrain avoidance) and NW of OI-2018 AUV boundary; published 30.5 km2 "
    "around 34.53 S 93.84 E; digitised parts sum to ~25 km2 (small NE patches not captured). Reportedly "
    "scanned by Armada 78 06 in the pre-contract infill phase 23-28 Feb 2025 (Iannello 4 & 31 Mar 2025).")
add("GO_Phoenix_terrain_gap_near_HPSA_CAPTION", cap_ig,
    "mh370-caption.net 'Search areas.kmz' placemarks 'Independent Group Hotspot'", "machine-readable", 0.5,
    "Four polygons (55.4 km2) = the whole slope area missed by GO Phoenix near 34.53 S 93.84 E "
    "(Iannello: 60.3 km2 of which ~half later scanned by OI in 2018).")
add("CAPTION_Blelly_Marchand_recommended_zone", [cap_bm],
    "mh370-caption.net 'Search areas.kmz' placemark 'Blelly/Marchand'; vertices 35.32S 93.45E, 35.90S "
    "93.45E, 35.90S 92.70E", "machine-readable", 0.5,
    "CAPTION recommended zone (centred ~35.7 S 93.0 E). Lies in the SE strip SW end / SW extension; covered "
    "mostly in the pre-contract Mar-2025 work and at the start of Phase 2 (CAPTION: Phase 3 'includes the "
    "recommended zone by CAPTION'). Part of the triangle beyond n~99 km (its SE corner at n~115 km) may not "
    "have been covered.")
add("Ulich_Iannello_2023_70NM_glide_racetrack", [close(race["ring"])],
    "Black outline 'Ulich-Iannello Search Area Based on 70-NM Glide' on Iannello maps (4 & 31 Mar 2025)",
    "digitised", 3.0,
    f"Stadium fitted to outline pixels in two georeferenced maps: radius {race['R_km']:.1f} km "
    f"(~77.5 NM), axis along the arc through ~LEP, half-length {race['half_length_km']:.0f} km (+/-6). "
    "A recommendation, not a searched area.")

# 2014 Bluefin-21 (Ocean Shield) search around the towed-pinger-locator detections: ~860 km2,
# 14 Apr-28 May 2014. NO public polygon retrieved; placeholder circle of equal area at the commonly
# quoted approximate position 21 S 104 E.
_lo, _la, _ = G.fwd(np.full(73, 104.0), np.full(73, -21.0), np.linspace(0, 360, 73),
                    np.full(73, np.sqrt(860 / np.pi) * 1000))
add("Bluefin21_2014_pinger_area_PLACEHOLDER", [close(np.c_[_lo, _la])],
    "JACC/ATSB 2014 statements via Wikipedia ('Search for Malaysia Airlines Flight 370'): 860 km2 sonar survey, "
    "14 Apr-28 May 2014; position only as 'approx. 21 S 104 E' (no coordinates retrieved)", "assumed", 30.0,
    "PLACEHOLDER only (equal-area circle, r=16.5 km, at an approximate position). ~1,500 km NNE of the 2025-26 "
    "area. Note: with the sea-level arc of mh370.geo, 21 S 104 E lies ~2 km from the 7th arc (arc at 104.02 E), "
    "so it is NOT clearly off-arc; it was chosen from the 2014 pinger detections (later judged not from MH370) "
    "and discounted by ATSB in May 2014. North of all later systematic searches (OI 2018 reached 24.84 S).")

doc = {
    "description": "Reconstructed extents of the Ocean Infinity 2025-2026 MH370 seabed search and related "
                   "areas. Public sources only; see SOURCE.md. NO official polygon or coordinates were published.",
    "format": "Each entry: rings = list of closed rings [[lon,lat],...] (WGS84, decimal degrees); multiple rings "
              "are separate parts (no holes). area_km2 computed after 1-km geodesic densification with "
              "pyproj Geod (WGS84), EPSG:6933 and a local Albers (lat_1=-33, lat_2=-36.5). extent.s_km/n_km are "
              "along-arc / normal (+SE) distances relative to the sea-level 7th arc of mh370.geo (s=0 at 34.2342 S).",
    "official_figures": {"contract_area_km2": 15000, "surveyed_post_contract_km2": 7571,
                          "surveyed_implied_exact_km2": 7571.46, "remaining_km2": 7428.54,
                          "interim_cumulative_2026-01-15_km2": 7236.40, "operational_days": 28,
                          "phase1": "2025-03-25..2025-03-28 (Armada 78 06)",
                          "phase2": "2025-12-31..2026-01-23 (Armada 86 05, 3 Hugin AUVs)",
                          "cumulative_km2_by_date": {"2026-01-01 (OI 'Day 6')": 2111.68, "2026-01-04": 2900.25,
                                                     "2026-01-06": 2930.88, "2026-01-07": 3220.42,
                                                     "2026-01-08": 3567.53, "2026-01-09": 4205.22,
                                                     "2026-01-10": 4627.28, "2026-01-11": 5323.07,
                                                     "2026-01-12": 5885.81, "2026-01-13": 6183.56,
                                                     "2026-01-14": 7054.47, "2026-01-15": 7236.40,
                                                     "2026-01-23 (final)": 7571.46},
                          "area_per_line_km_km": 1.82,
                          "note": "Day count restarts at signing: Days 1-4 = 25-28 Mar 2025, Day 5 = 31 Dec 2025; "
                                  "cumulative before 1 Jan 2026 = 1,655.58 km2 (Mar 2025 + 31 Dec). Areas are "
                                  "line-km x swath tallies, not polygon areas."},
    "generated_by": "scripts/search_oi2025/build_polygons.py",
    "retrieved": "2026-11-05",
    "polygons": E,
}
json.dump(doc, open(os.path.join(RAW, "polygons_oi2025.json"), "w"), indent=1)
for d in E:
    print(f"{d['name']:55s} {d['method']:17s} err {d['est_error_km']:5.1f} km  "
          f"area {d['area_km2']['geodesic_WGS84']:9.1f} (6933 {d['area_km2']['EPSG6933']:9.1f}, "
          f"albers {d['area_km2']['local_albers']:9.1f})  s {d['extent']['s_km']} n {d['extent']['n_km']}")
print("N_OUT_POST", round(N_OUT_POST, 2), "N_OUT_REM", round(N_OUT_REM, 2))

# ----------------------------------------------------------------------------- QA figures
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from mh370 import geo  # noqa: E402

os.makedirs(OUT, exist_ok=True)
arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-37.2, -32.0, 0.02))
sty = {"OI_contract_area_best__slide_digitised": ("r", 1.6, "-"),
       "OI_contract_area_alt__CAPTION_kml": ("k", 0.8, "--"),
       "OI_contract_area_alt__Iannello_map_digitised": ("m", 0.8, ":"),
       "OI2025_26_surveyed_post_contract_best": ("b", 1.6, "-"),
       "OI2025_pre_contract_SW_survey_Mar11-24": ("c", 1.4, "-"),
       "OI2025_pre_contract_infill_region_Feb23-28": ("purple", 1.0, "-."),
       "High_Priority_Search_Area_HPSA": ("orange", 1.2, "-"),
       "CAPTION_Blelly_Marchand_recommended_zone": ("gold", 1.2, "-"),
       "Ulich_Iannello_2023_70NM_glide_racetrack": ("gray", 1.0, "-")}
oi18 = np.array([o["coords"] for o in cap if o["name"] == "Ocean Infinity 2018 search"][0])
atsb = np.array([o["coords"] for o in cap if o["name"].startswith("Australia/China")][0])
for frame in ("lonlat", "arcframe"):
    fig, ax = plt.subplots(figsize=(13, 11) if frame == "lonlat" else (16, 7))

    def P(lon, lat):
        if frame == "lonlat":
            return np.asarray(lon), np.asarray(lat)
        lon = np.asarray(lon); lat = np.asarray(lat)
        k = (lat > -37.5) & (lat < -32.0) & (lon > 90) & (lon < 97)
        s, n = to_sn(lon[k], lat[k])
        return s, n
    x, y = P(arc[:, 1], arc[:, 0]); ax.plot(x, y, "-", color="navy", lw=0.8, label="7th arc (sea level)")
    for c, col, lab in [(oi18, "orange", "OI 2018 coverage outline (CAPTION)"),
                        (atsb, "saddlebrown", "ATSB 2014-17 coverage outline (CAPTION)")]:
        x, y = P(c[:, 0], c[:, 1]); ax.plot(x, y, "-", color=col, lw=0.6, label=lab)
    for d in E:
        if d["name"] not in sty:
            continue
        col, lw, ls = sty[d["name"]]
        for i, r in enumerate(d["rings"]):
            r = np.array(r); x, y = P(r[:, 0], r[:, 1])
            ax.plot(x, y, ls, color=col, lw=lw, label=d["name"] if i == 0 else None)
    for leg, col in [("A7806_P1", "violet"), ("A7806_P2", "green"), ("A8605", "teal")]:
        t = tr[tr.leg.str.startswith(leg)]
        x, y = P(t.lon.values, t.lat.values); ax.plot(x, y, ".", color=col, ms=1.5, label=f"AIS {leg}")
    if frame == "lonlat":
        ax.set_xlim(91.0, 96.3); ax.set_ylim(-37.0, -32.4); ax.set_aspect(1 / np.cos(np.radians(34.7)))
        ax.set_xlabel("lon"); ax.set_ylabel("lat")
    else:
        ax.set_xlim(-300, 130); ax.set_ylim(-150, 150)
        ax.set_xlabel("s: along-arc km (+NE, 0 at 34.2342 S)"); ax.set_ylabel("n: km from sea-level arc (+SE)")
    ax.grid(lw=0.3); ax.legend(fontsize=6, loc="lower right" if frame == "lonlat" else "upper left", markerscale=6)
    ax.set_title("OI 2025-26 search reconstruction (public sources; polygons are digitised/assumed)")
    fig.savefig(os.path.join(OUT, f"oi2025_overview_{frame}.png"), dpi=110, bbox_inches="tight")
