"""Assemble the Ocean Infinity 2018 searched-area polygons from the digitised site maps.

Run (after the per-map digitisation, see run_all.sh):
    .venv/bin/python -I scripts/search_oi2018/assemble.py

Inputs : data/raw/oi2018_search/digitisation/*_georef_polys.json   (outputs of oigeo.py)
         data/derived/oi2018_search/seabed_constructor_track_2018.csv  (AIS track, for the figure)
Outputs: data/raw/oi2018_search/polygons_oi2018.json   (primary deliverable)
         data/raw/oi2018_search/polygons_oi2018.geojson
         data/raw/oi2018_search/digitisation/cross_arc_profile.csv
         outputs/search/qa/oi2018_polygons.png
"""
import json, sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, mapping, Point
from shapely.ops import unary_union, transform as shp_transform
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import arcframe as af  # noqa: E402

RAW = ROOT / 'data/raw/oi2018_search'
DIG = RAW / 'digitisation'
OUT = ROOT / 'outputs/search/qa'; OUT.mkdir(parents=True, exist_ok=True)
T6933 = Transformer.from_crs('EPSG:4326', 'EPSG:6933', always_xy=True)


def area_km2(g):
    return shp_transform(lambda x, y: T6933.transform(x, y), g).area / 1e6


def load(name):
    g = json.load(open(DIG / name))
    polys = [Polygon(p['outer'], p['holes']).buffer(0) for p in g['polygons']]
    return unary_union(polys), g


def simplify(g, tol_deg=0.002):
    return g.simplify(tol_deg, preserve_topology=True)


site1, g1 = load('site1_OSU11_2018-04-10_georef_polys.json')
site2, g2 = load('site2_OSU17_2018-05-22_georef_polys.json')
site3, g3 = load('site3_OSU17_2018-05-22_georef_polys.json')
site4p, g4 = load('site4_OSU18_2018-05-29_georef_polys.json')
site1_chk, _ = load('site1_OSU10_2018-04-03_check_georef_polys.json')

# Site 4 survey box (P04S04_v7), corners from straight-line fits to the box outline in the OSU18 Site-4 map
# (box_corners.py), converted with the OSU18 georeference; OSU17 map gives the same corners within 0.3 km.
S4_BOX = [(100.5492, -26.3150), (101.2444, -26.7033), (99.7730, -28.7168), (99.0872, -28.2961)]
site4_box = Polygon(S4_BOX)
site4_full = unary_union([site4p, site4_box])

# Inferred northern extension (not on any official map): continuation of the Site-4 corridor from the
# NE edge of the Site-4 box (arc-lat ~ -26.5) to arc-lat -25.0, with the Site-4 cross-arc limits at its NE end.
_, d_nw = af.cross_arc_signed(*S4_BOX[0]); _, d_se = af.cross_arc_signed(*S4_BOX[1])
d_nw, d_se = float(d_nw[0]), float(d_se[0])
lat_sw = float(af.cross_arc_signed(*S4_BOX[0])[0][0]); lat_ne = -25.0
lats = np.arange(lat_sw, lat_ne + 1e-9, 0.05)
nw = af.offset_point(lats, np.full_like(lats, d_nw)); se = af.offset_point(lats[::-1], np.full_like(lats, d_se))
ring = [S4_BOX[0]] + [tuple(p) for p in nw[1:]] + [tuple(p) for p in se[:-1]] + [S4_BOX[1]]
north_ext = Polygon(ring).buffer(0).difference(site4_box)

from shapely.geometry import LineString

def fill_junctions(g):
    """Sites abut on the official maps; close digitisation slivers (<~2 km) ONLY along the Site1/Site2 and Site3/Site4
    junction lines (elsewhere, notches may be real coverage gaps and are kept)."""
    zones = unary_union([LineString([(95.4830, -32.1138), (96.3368, -32.7710)]).buffer(0.04),   # Site 2 SW edge
                         LineString([(99.0872, -28.2961), (99.7730, -28.7168)]).buffer(0.04)])  # Site 4 SW edge
    closed = g.buffer(0.02, join_style=2).buffer(-0.02, join_style=2)
    return unary_union([g, closed.difference(g).intersection(zones)])

best = fill_junctions(unary_union([site1, site2, site3, site4_full, north_ext]))
documented = fill_junctions(unary_union([site1, site2, site3, site4p]))

def rings(g):
    out = []
    for p in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        out.append(dict(ring=[[round(x, 5), round(y, 5)] for x, y in p.exterior.coords],
                        holes=[[[round(x, 5), round(y, 5)] for x, y in h.coords] for h in p.interiors]))
    return out

SRC_OSU = ('Government of Malaysia, "MH370 Operational Search Update" #{n} ({d}), {fig}; archived PDF '
           'via web.archive.org of http://mh370.gov.my/en/mh370-underwater-search-2018?download=... '
           '(file weekly_updates/OSU{n:02d}_{d}.pdf, figure figures_extracted/{img})')
items = [
    dict(name='OI2018_Site1', geom=site1,
         source=SRC_OSU.format(n=11, d='2018-04-10', fig='page 2 Diagram 2 (Site 1 Areas 01-03 completed)', img='OSU11_p2_x31_451x465.png'),
         method='digitised', est_error_km=2.0, reported_area_km2=38214,
         notes=('Site 1 = ATSB/FPR priority area (planned 25,000 km2 primary + supplementary = 33,012 km2) plus the '
                '"additional areas along the Northern Leg of Site 1/Area 1 and the Southern Leg of Site 1/Area 1". '
                'Searched 22 Jan - ~5 Apr 2018 (OSU#11: Site 1 complete, 38,214 km2). U-shaped: the concavity between '
                'the two legs (~33-35.5S) is the strip already searched by the ATSB/GO Phoenix and was NOT part of '
                'Site 1. Georef: 8 graticule crosses (2 deg), UTM 46S affine, rms 0.22 km; outline = non-background '
                'pixels (includes outline line and grey extra-coverage halo), so boundary is biased ~0.5-1 km outward; '
                'area +3% vs reported. Validated against OSU#10 map (median boundary diff 0.7 km, p90 1.8 km) and '
                'against the OI-supplied outline published by V. Iannello (11 Feb 2023) near 34.2S: edges agree to 1-3 km.')),
    dict(name='OI2018_Site2', geom=site2,
         source=SRC_OSU.format(n=17, d='2018-05-22', fig='page 2, Site 2 progress map (Areas 1-3 incl. Broken Ridge, P04S02_v18)', img='OSU17_p2_x32_610x442.png'),
         method='digitised', est_error_km=1.0, reported_area_km2=14786,
         notes=('Searched ~5-15 Apr 2018 (OSU#11-#12). Reported area derived as 53,000 (Sites 1+2, OSU#12) - 38,214 (Site 1). '
                'Georef: 10 crosses at 0.5 deg, UTM 46S affine, rms 0.12 km. Width ~108 km (-45..+63 km from the sea-level arc).')),
    dict(name='OI2018_Site3', geom=site3,
         source=SRC_OSU.format(n=17, d='2018-05-22', fig='page 2, Site 3 progress map (P04S03_v16, complete)', img='OSU17_p2_x37_538x564.png'),
         method='digitised', est_error_km=1.5, reported_area_km2=35200,
         notes=('Searched ~15 Apr - ~14 May 2018 (port call 28 Apr - 7 May). Reported area derived as 88,200 (Sites 1-3, OSU#17) - 53,000. '
                'Georef: 9 crosses at 1 deg (lat labels cropped off the figure; latitudes assigned from consistency with the '
                'overview map and with the Site-4 box, whose SW corners match Site 3 NE corners within 1 km), UTM 47S affine, '
                'rms 0.22 km. NW edge may include up to ~2 km of pale shallow seabed between 28.3S and 29.2S.')),
    dict(name='OI2018_Site4_to_27May', geom=site4p,
         source=SRC_OSU.format(n=18, d='2018-05-29', fig='page 3 Diagram 3 (Site 4 coverage as of 27 May 2018)', img='OSU18_p3_x40_499x521.png'),
         method='digitised', est_error_km=1.0, reported_area_km2=18000,
         notes='Searched 14-27 May 2018. Georef: 4 crosses at 1 deg, UTM 47S affine, rms 0.07 km (only 4 control points).'),
    dict(name='OI2018_Site4_box', geom=site4_box,
         source=SRC_OSU.format(n=18, d='2018-05-29', fig='page 3 Diagram 3, Site 4 survey box outline (P04S04_v7)', img='OSU18_p3_x40_499x521.png'),
         method='digitised', est_error_km=1.0, reported_area_km2=None,
         notes=('Planned Site 4 survey box, ~81 km wide (-38..+44 km from the sea-level arc, i.e. ~+/-22 NM), 28.7S-26.3S. '
                'Its NE part (~26.3-26.9S) was not yet covered on 27 May; completion ~27-30 May is INFERRED from the AIS track '
                '(vessel reached 26.30S on 28 May, 26.13S on 29 May) and community daily reports, not from an official map.')),
    dict(name='OI2018_North_extension_inferred', geom=north_ext,
         source=('Inferred: no official map. Evidence: Seabed Constructor AIS track (community KMZ, LabratSR Dropbox, '
                 'data/derived/oi2018_search/seabed_constructor_track_2018.csv) reaching 25.80S (31 May), 25.10S (4 Jun), '
                 '24.76S (6 Jun); V. Iannello 8 Jun 2018 "searched as far north as 25S and at a width of at least +/-22 NM"; '
                 'R. Godfrey daily comments on radiantphysics.com (31 May - 7 Jun 2018); AirlineRatings 31 May 2018 (OI spokesman: '
                 'vessel to remain a few days to sweep the area of the 2014 Chinese ping near 25S 101E).'),
         method='inferred', est_error_km=25.0, reported_area_km2=None,
         notes=('~30 May - 7 Jun 2018, after the official end of the search (29 May). Corridor continued with the Site-4 '
                f'cross-arc limits ({d_nw:+.1f} to {d_se:+.1f} km from the sea-level arc) up to arc-latitude 25.0S. The northern '
                'limit is uncertain by roughly -0.25/+0.3 deg (vessel reached 24.76S; last AUVs were recovered early). Coverage '
                'quality likely lower: Richard Cole (quoted by AirlineRatings 31 May 2018) "the gaps between AUV tracks have been '
                'opened out again"; Godfrey 4 Jun 2018: AUV54 recovered early, AUV55 swath 5.2 km instead of 7.4 km. Treat with '
                'reduced POD and as a sensitivity case.')),
]
total_items = [
    dict(name='OI2018_best_estimate_total', geom=best,
         source='Union of OI2018_Site1, Site2, Site3, Site4_to_27May, Site4_box and North_extension_inferred',
         method='digitised+inferred', est_error_km=2.0,
         reported_area_km2=None,
         notes=('Best estimate of all seabed searched by OI in 2018 (22 Jan - 7 Jun 2018). Boundary error ~1-2 km except the '
                'northern end (inferred, ~25 km along-arc). Official total ">112,000 km2" (OI/Malaysia, 29 May 2018) refers to '
                'coverage up to ~29 May; community estimates of the final total are ~115,000-120,000 km2.')),
    dict(name='OI2018_documented_to_27May', geom=documented,
         source='Union of OI2018_Site1, Site2, Site3, Site4_to_27May (official maps only)',
         method='digitised', est_error_km=2.0, reported_area_km2=106200,
         notes='Conservative: only coverage shown on official maps (OSU#18 reports 88,200 + 18,000 = 106,200 km2 as of 27 May 2018).'),
]

out = dict(
    description='Ocean Infinity 2018 MH370 seabed search (Seabed Constructor, Hugin AUVs), reconstructed from public maps.',
    crs='EPSG:4326 (lon, lat), WGS84', ring_format='closed rings [[lon, lat], ...], first == last; holes listed separately',
    reference_arc='sea-level 7th arc from mh370.geo (BTO 18,400 us at 00:19:29.416); d>0 = SE (outside) of arc',
    area_method='EPSG:6933 (WGS84 equal-area cylindrical)',
    created='2026-11-05', generator='scripts/search_oi2018/assemble.py',
    polygons=[])
for it in items + total_items:
    g = it.pop('geom')
    gs = simplify(g)
    it['area_km2_eqarea'] = round(area_km2(g), 0)
    it['parts'] = rings(gs)
    it['n_vertices'] = sum(len(p['ring']) for p in it['parts'])
    out['polygons'].append(it)
    it['_g'] = g

# pairwise overlaps between site polygons (double counting check)
names = [i['name'] for i in items[:4]] + ['OI2018_North_extension_inferred']
geoms = {i['name']: i['_g'] for i in items}
ov = {}
for a in range(len(names)):
    for b in range(a + 1, len(names)):
        x = geoms[names[a]].intersection(geoms[names[b]])
        if not x.is_empty and area_km2(x) > 1: ov[f'{names[a]} & {names[b]}'] = round(area_km2(x), 0)
out['pairwise_overlaps_km2'] = ov
out['site1_check_OSU10_vs_OSU11'] = dict(area_OSU10=round(area_km2(site1_chk)), area_OSU11=round(area_km2(site1)),
                                          symmetric_difference_km2=round(area_km2(site1_chk.symmetric_difference(site1))))

# reference arc points: inside? and cross-arc coverage at that latitude
refpts = [(-25.00, 101.84), (-30.00, 98.13), (-34.23, 93.74), (-35.00, 92.77), (-38.00, 88.18)]

def profile(g, arc_lat, dstep=0.5, dmax=120):
    ds = np.arange(-dmax, dmax + 1e-9, dstep)
    pts = af.offset_point(np.full_like(ds, arc_lat), ds)
    inside = np.array([g.contains(Point(p)) for p in pts])
    if not inside.any():
        return None
    idx = np.nonzero(inside)[0]
    segs = []
    start = idx[0]
    for k in range(1, len(idx)):
        if idx[k] != idx[k - 1] + 1:
            segs.append((ds[start], ds[idx[k - 1]])); start = idx[k]
    segs.append((ds[start], ds[idx[-1]]))
    return dict(d_min=float(ds[idx[0]]), d_max=float(ds[idx[-1]]), covered_km=float(inside.sum() * dstep),
                segments=[(float(a), float(b)) for a, b in segs])

out['reference_arc_points'] = []
for la, lo in refpts:
    pr = profile(best, la)
    out['reference_arc_points'].append(dict(lat=la, lon=lo, inside_best_estimate=bool(best.contains(Point(lo, la))),
                                            cross_arc_coverage_at_this_arc_lat=pr))

# cross-arc profile CSV
rows = ['arc_lat,d_min_km,d_max_km,covered_width_km,segments_km(d_from:d_to;...),n_segments']
for la in np.round(np.arange(-36.6, -24.7, 0.1), 2):
    pr = profile(best, la)
    if pr is None:
        rows.append(f'{la},,,0,,0'); continue
    segs = ';'.join(f'{a:+.1f}:{b:+.1f}' for a, b in pr['segments'])
    rows.append(f"{la},{pr['d_min']:.1f},{pr['d_max']:.1f},{pr['covered_km']:.1f},{segs},{len(pr['segments'])}")
(DIG / 'cross_arc_profile.csv').write_text('\n'.join(rows) + '\n')

for it in out['polygons']:
    it.pop('_g')
json.dump(out, open(RAW / 'polygons_oi2018.json', 'w'), indent=1)
fc = dict(type='FeatureCollection', features=[])
for it in out['polygons']:
    polys = [[p['ring']] + p['holes'] for p in it['parts']]
    geom = dict(type='MultiPolygon', coordinates=polys)
    props = {k: v for k, v in it.items() if k != 'parts'}
    fc['features'].append(dict(type='Feature', properties=props, geometry=geom))
json.dump(fc, open(RAW / 'polygons_oi2018.geojson', 'w'))

# summary
for it in out['polygons']:
    print(f"{it['name']:36s} area {it['area_km2_eqarea']:>9.0f} km2  reported {it['reported_area_km2']}  verts {it['n_vertices']}  err {it['est_error_km']} km")
print('overlaps', ov)
print('site1 check', out['site1_check_OSU10_vs_OSU11'])
for r in out['reference_arc_points']: print(r)

# figure
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
import pandas as pd
fig, ax = plt.subplots(figsize=(11, 12))
cols = dict(OI2018_Site1='tab:orange', OI2018_Site2='tab:pink', OI2018_Site3='tab:green', OI2018_Site4_to_27May='tab:blue',
            OI2018_Site4_box='navy', OI2018_North_extension_inferred='tab:red')
for it in out['polygons']:
    if it['name'] not in cols: continue
    for p in it['parts']:
        r = np.array(p['ring']); ax.fill(r[:, 0], r[:, 1], alpha=0.25 if 'box' not in it['name'] else 0.0, color=cols[it['name']])
        ax.plot(r[:, 0], r[:, 1], '-', color=cols[it['name']], lw=1.2 if 'box' not in it['name'] else 0.8,
                ls='--' if ('box' in it['name'] or 'inferred' in it['name']) else '-', label=it['name'])
arc = af._ARC; sel = (arc[:, 0] > -37) & (arc[:, 0] < -24)
ax.plot(arc[sel, 1], arc[sel, 0], 'k-', lw=0.8, label='7th arc (sea level, mh370.geo)')
trk = ROOT / 'data/derived/oi2018_search/seabed_constructor_track_2018.csv'
if trk.exists():
    t = pd.read_csv(trk); t = t[(t.lat > -37) & (t.lat < -24) & (t.lon > 89) & (t.lon < 103.5)]
    ax.plot(t.lon, t.lat, '.', ms=0.4, color='0.4', label='Seabed Constructor AIS (community KMZ)')
for la, lo in refpts:
    ax.plot(lo, la, 'k^', ms=5)
h, l = ax.get_legend_handles_labels(); seen = {}
for hh, ll in zip(h, l): seen.setdefault(ll, hh)
ax.legend(seen.values(), seen.keys(), loc='lower right', fontsize=8)
ax.set_xlim(89.5, 103.5); ax.set_ylim(-37, -24.3); ax.set_aspect(1 / np.cos(np.radians(30.5))); ax.grid(True, lw=0.3)
ax.set_title('Ocean Infinity 2018 searched area, reconstructed from public maps (digitised) + inferred N end')
plt.savefig(OUT / 'oi2018_polygons.png', dpi=110, bbox_inches='tight')
