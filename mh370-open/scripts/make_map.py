"""Build an interactive HTML map (Leaflet) and a static PNG of the mh370-open results.

Default probability layer: the model-misspecification mixture at its recommended default (satellite
layer p_v2, broad "model is wrong" component broad_arc with prior weight eps = 0.1, drift weight w = 0.5,
POD best; outputs/combine/README.md "Model-misspecification mixture", RESULTS_mix.md). The satellite-only
layers and the old (v1, satellite p) combined layers are offered as alternatives in the HTML.
Ranked blocks: areas 1-3 = top-3 essentially unsearched 7,500 km² blocks at the default; satellite-only
pick = top unsearched block with the drift set aside (w = 0); re-search block = top block on any ground
at the default.

Inputs: data/derived/combined_posterior_mix.nc, combined_posterior.nc (old layers), satcom_posterior.nc,
outputs/search/search_polygons.geojson, outputs/combine/ranked_blocks_mix.csv,
data/raw/oi2025_search/polygons_oi2025.json, data/raw/naturalearth (coastline for the static PNG).
Outputs: outputs/map/mh370_results_map.html, outputs/map/mh370_results_map.png
Run: .venv/bin/python -I scripts/make_map.py
"""
from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import matplotlib
import matplotlib.patheffects
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from matplotlib import cm, colors
from shapely.geometry import mapping, shape

from mh370 import geo

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "map"
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------- data
MIX_SCEN = "sat=p_v2|broad=broad_arc|eps=0.1|w=0.5|pod=best"      # recommended default
SATONLY_SCEN = "sat=p_v2|broad=broad_arc|eps=0.1|w=0|pod=best"     # same, debris drift set aside
mix = xr.open_dataset(ROOT / "data/derived/combined_posterior_mix.nc", engine="h5netcdf")
assert mix.attrs["recommended"] == MIX_SCEN, mix.attrs["recommended"]
comb = xr.open_dataset(ROOT / "data/derived/combined_posterior.nc", engine="h5netcdf")
sat = xr.open_dataset(ROOT / "data/derived/satcom_posterior.nc", engine="h5netcdf")
LAT = mix.lat.values
LON = mix.lon.values
assert np.allclose(LAT, comb.lat.values) and np.allclose(LON, comb.lon.values)
satsum = json.load(open(ROOT / "outputs/satcom/summary_v2.json"))["arcprofile"]
SAT_MED = -satsum["p_v2"]["median"]                                 # 38.17
SAT_90 = sorted(-v for v in satsum["p_v2"]["i90"])                  # [36.46, 39.51]
DES_MED = -satsum["p_v2_sens_descent1840"]["median"]                # 35.82

HEAT_LAYERS = {
    "Default: satellite + 'model is wrong' alternative (1 in 10), drift weight 0.5, not yet searched":
        mix["post_mix"].values,
    "Same, debris drift set aside (basis of the satellite-only pick)": mix["post_mix_broad_arc_eps0p1_w0"].values,
    "If the satellite model is right: satellite × drift 0.5 × not yet searched": mix["post_sat_cond"].values,
    "Satellite data only (where it ended, before removing searched ground)": sat["p_v2"].values,
    "Satellite data only, descending at the 02:40 call (sensitivity)": sat["p_v2_sens_descent1840"].values,
    "Old v1: satellite data only (single autopilot setting)": sat["p"].values,
    "Old v1: combined, drift weight 0": comb["post_w0_best"].values,
    "Old v1: combined, drift weight 0.5": comb["post_w0p5_best"].values,
    "Old v1: combined, drift weight 1": comb["post_w1_best"].values,
}
DEFAULT_HEAT = next(iter(HEAT_LAYERS))

search = json.load(open(ROOT / "outputs/search/search_polygons.geojson"))
oi = json.load(open(ROOT / "data/raw/oi2025_search/polygons_oi2025.json"))
blocks = pd.read_csv(ROOT / "outputs/combine/ranked_blocks_mix.csv")

arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-44.0, -7.9, 0.05))


def arc_lon(lat):
    return float(geo.arc_lon_for_lat(lat, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0))


# ------------------------------------------------------------ ranked areas (mixture run)
def pick(scenario, mode, rank=1, budget=7500):
    r = blocks[(blocks.scenario == scenario) & (blocks["mode"] == mode) & (blocks.budget_km2 == budget)
               & (blocks["rank"] == rank)]
    assert len(r) == 1, (scenario, mode, budget, rank, len(r))
    return r.iloc[0]


def _published(row):
    """centre and ranges of a block as printed in outputs/combine/RESULTS_mix.md (the CSV keeps 5 significant
    digits, so re-rounding it can differ from the report in the last digit); falls back to the CSV values"""
    import re
    txt = (ROOT / "outputs/combine/RESULTS_mix.md").read_text()
    cands = [(-float(a), float(b)) for a, b in re.findall(r"(\d+\.\d\d)S (\d+\.\d\d)E", txt)]
    cands = [c for c in cands if abs(c[0] - row.centre_lat) <= 0.0051 and abs(c[1] - row.centre_lon) <= 0.0051]
    la, lo = min(cands, key=lambda c: abs(c[0] - row.centre_lat) + abs(c[1] - row.centre_lon)) if cands else \
        (row.centre_lat, row.centre_lon)
    centre = f"{abs(la):.2f}S {lo:.2f}E"
    m = (re.search(re.escape(centre) + r" \| (\d+\.\d\d)S-(\d+\.\d\d)S \| (\d+\.\d\d)-(\d+\.\d\d)E \|", txt)
         or re.search("centre " + re.escape(centre) + r", (\d+\.\d\d)S-(\d+\.\d\d)S / (\d+\.\d\d)-(\d+\.\d\d)E", txt))
    rg = tuple(float(v) for v in m.groups()) if m else (abs(row.lat_max), abs(row.lat_min), row.lon_min, row.lon_max)
    return la, lo, rg


def corners(row):
    pts = []
    for tok in row.corners.split(";"):
        la, lo = tok.strip("() ").split(",")
        pts.append((float(la), float(lo)))
    return pts


# (label, title, row, colour, note, dashed)
HYP = [
    ("1", "Area 1: strip on the outer edge of the 2018 search", pick(MIX_SCEN, "unsearched", 1), "#e41a1c",
     "Top essentially unsearched block at the default settings. Its probability comes almost entirely from the "
     "'model is wrong somewhere' alternative; areas 1 and 2 swap places if the prior weight on that alternative is "
     "below about 0.06, or with the broad_arc_lnavctt start geometry.", False),
    ("2", "Area 2: glide zone beyond the ATSB south-east edge", pick(MIX_SCEN, "unsearched", 2), "#ff7f00",
     "Second unsearched block at the default; 90-130 km beyond the arc, where a piloted glide would end. The top "
     "unsearched block if the satellite model is right.", False),
    ("3", "Area 3: beside area 1, further beyond the arc", pick(MIX_SCEN, "unsearched", 3), "#4daf4a",
     "Third unsearched block at the default; 60-80 km beyond the arc, next to area 1.", False),
    ("S", "Satellite-only pick: just past the south end of the ATSB search, drift set aside",
     pick(SATONLY_SCEN, "unsearched", 1),
     "#377eb8", "Top unsearched block with the debris drift set aside (drift weight 0). Under the default settings "
     "this box holds about 2%.", False),
    ("R", "Re-search block inside the ATSB area", pick(MIX_SCEN, "any", 1), "#984ea3",
     "Highest-probability block at the default if re-searching old ground is allowed; only worth it if the "
     "2014-17 search was less thorough than reported.", True),
]

POINTS = [
    # name, lat, lon, kind, note
    ("This project: satellite median", -SAT_MED, arc_lon(-SAT_MED), "ours",
     f"Median end point of the satellite-data layer (v2, all route families) along the 7th arc "
     f"(90%: {SAT_90[0]:.2f}-{SAT_90[1]:.2f} S)."),
    ("Satellite median if descending at 02:40", -DES_MED, arc_lon(-DES_MED), "ours",
     "Same satellite data, but allowing a descent during the 18:40 UTC (02:40 Malaysian time) call. The data "
     "cannot tell this from level flight."),
    ("This project: debris drift peak", -33.4, arc_lon(-33.4), "ours",
     "Peak of the default drift likelihood on the arc (68%: 30.8-34.9 S)."),
    ("DSTG (Australian Defence) peak", -37.8, arc_lon(-37.8), "pub", "DSTG Bayesian analysis, Fig. 10.3 peak."),
    ("UGIB 2020 hotspot", -34.23, 93.78, "pub", "Ulich, Godfrey, Iannello, Banks (2020). Their route fits the "
     "satellite data as well as ours, but only with a descent during the 02:40 call. Searched (ATSB / OI)."),
    ("CSIRO drift 2017", -35.6, 92.8, "pub", "CSIRO (Griffin) drift study. Searched."),
    ("WSPR claim (Godfrey et al.)", -29.128, 99.934, "pub", "Unsearched, but the method is judged unsound."),
    ("Kadri 306 deg bearing x arc", -25.73, 101.37, "acoustic", "Arrival 11.5-17 min too late for an arc impact."),
    ("Stead/LANL 246.9 deg timing-consistent point", -40.97, 81.57, "acoustic",
     "Timing fits; nothing on open sensors; untestable with open data."),
    ("Anderson 01:15 'Java' event", -8.36, 107.92, "acoustic", "A natural ~M4.1 earthquake, not MH370."),
]

# ------------------------------------------------------------------ raster helpers
def colourise(p, vmin_log=-3.0, mass_keep=0.995):
    """RGBA image (lat ascending) of a probability field: log colour, cells outside
    the top `mass_keep` probability mass are transparent."""
    p = np.nan_to_num(np.asarray(p, float), nan=0.0)
    if p.sum() <= 0:
        return np.zeros(p.shape + (4,), np.uint8)
    p = p / p.sum()
    flat = np.sort(p.ravel())[::-1]
    cut = flat[np.searchsorted(np.cumsum(flat), mass_keep)]
    pmax = flat[0]
    lg = np.log10(np.clip(p / pmax, 1e-12, 1))
    t = np.clip((lg - vmin_log) / -vmin_log, 0, 1)
    rgba = cm.inferno(0.15 + 0.85 * t)
    rgba[..., 3] = np.where(p >= cut, 0.35 + 0.6 * t, 0.0)
    return (rgba * 255).astype(np.uint8)


def merc_y(lat):
    return np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def to_mercator(img, lat, n_rows=1200):
    """Resample rows (lat ascending) to be uniform in Web-Mercator y; return top-down image."""
    lat_edges = (lat[0] - 0.025, lat[-1] + 0.025)
    y = np.linspace(merc_y(lat_edges[1]), merc_y(lat_edges[0]), n_rows)  # top -> bottom
    lat_rows = np.degrees(2 * np.arctan(np.exp(y)) - np.pi / 2)
    idx = np.clip(np.round((lat_rows - lat[0]) / 0.05).astype(int), 0, lat.size - 1)
    return img[idx], lat_edges


def png_b64(img):
    buf = io.BytesIO()
    plt.imsave(buf, img, format="png")
    return base64.b64encode(buf.getvalue()).decode()


# ------------------------------------------------------------------- HTML layers
heat_payload = {}
for name, p in HEAT_LAYERS.items():
    rgba = colourise(p)
    merc, (s, n) = to_mercator(rgba, LAT)
    heat_payload[name] = png_b64(merc)
heat_bounds = [[float(LAT[0] - 0.025), float(LON[0] - 0.025)], [float(LAT[-1] + 0.025), float(LON[-1] + 0.025)]]

CAMPAIGN_STYLE = {
    "ATSB_2014_17": ("#4a90d9", "ATSB 2014-17 search (Geoscience Australia data)"),
    "Bluefin21_2014": ("#666666", "Bluefin-21 2014 pinger-area search"),
    "OI_2018": ("#f08a5d", "Ocean Infinity 2018 search (digitised from official maps)"),
    "OI_2025_26": ("#2ca58d", "Ocean Infinity 2025-26 search (ASSUMED footprint)"),
}
search_feats = []
for f in search["features"]:
    g = shape(f["geometry"]).simplify(0.01, preserve_topology=True)
    pr = f["properties"]
    search_feats.append({"type": "Feature", "geometry": mapping(g), "properties": {
        "campaign": pr["campaign"], "name": pr["name"], "pod": pr["pod"], "pod_low": pr["pod_low"],
        "pod_high": pr["pod_high"], "method": pr["method"], "area_km2": round(pr["area_km2_eqarea"], 1)}})

remaining = next(p for p in oi["polygons"] if p["name"] == "OI2025_26_remaining_NW_strip_calibrated_7428")
remaining_feat = {"type": "Feature", "properties": {"name": "Ocean Infinity contract: remaining ~7,429 km2 (approx.)"},
                  "geometry": {"type": "Polygon", "coordinates": [remaining["rings"][0]]}}


def block_feature(row, letter=None, title=None, colour=None, note=None, dashed=False):
    cs = corners(row)
    ring = [[lo, la] for la, lo in cs] + [[cs[0][1], cs[0][0]]]
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]}, "properties": {
        "letter": letter, "title": title, "colour": colour, "note": note, "dashed": dashed,
        "scenario": f"{row.scenario.replace('|', ', ')}, {row['mode']} (posterior weight on 'model is wrong' "
                    f"{row.eps_post:.2f})",
        "mass_sat": float(row.mass_sat_cond),
        "rank": int(row["rank"]), "centre": f"{abs(_published(row)[0]):.2f}°S {_published(row)[1]:.2f}°E",
        "lat_range": f"{_published(row)[2][0]:.2f}°S – {_published(row)[2][1]:.2f}°S",
        "lon_range": f"{_published(row)[2][2]:.2f}°E – {_published(row)[2][3]:.2f}°E",
        "corners": "<br>".join(f"{abs(la):.3f}°S {lo:.3f}°E" for la, lo in cs),
        "across_arc": f"{row.n0_km:+.0f} to {row.n1_km:+.0f} km from the arc",
        "area_km2": float(row.area_km2), "mass": float(row.mass), "p_success": float(row.p_success),
        "prev_searched": float(row.frac_previously_searched)}}


hyp_feats = [block_feature(r, L, t, c, n, d) for L, t, r, c, n, d in HYP]
top5 = {}
for w in (0, 0.5, 1):
    rows = blocks[(blocks.scenario == f"sat=p_v2|broad=broad_arc|eps=0.1|w={w:g}|pod=best")
                  & (blocks["mode"] == "unsearched") & (blocks.budget_km2 == 7500)].sort_values("rank")
    assert len(rows) >= 5, w
    top5[f"w{w}"] = [block_feature(r) for _, r in rows.head(5).iterrows()]

arc_coords = [[float(a), float(b)] for a, b in arc]
sat90 = [[float(a), float(b)] for a, b in arc if -SAT_90[1] <= a <= -SAT_90[0]]

data = {
    "heat": heat_payload, "heatBounds": heat_bounds, "defaultHeat": DEFAULT_HEAT,
    "arc": arc_coords, "sat90": sat90,
    "search": {"type": "FeatureCollection", "features": search_feats},
    "campaignStyle": {k: {"colour": v[0], "label": v[1]} for k, v in CAMPAIGN_STYLE.items()},
    "remaining": remaining_feat,
    "hyp": {"type": "FeatureCollection", "features": hyp_feats},
    "top5": {k: {"type": "FeatureCollection", "features": v} for k, v in top5.items()},
    "points": [{"name": n, "lat": la, "lon": lo, "kind": k, "note": t} for n, la, lo, k, t in POINTS],
    "sat90txt": f"{SAT_90[0]:.2f}–{SAT_90[1]:.2f}°S",
}

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>MH370 open-data reanalysis: results map</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
 html,body{margin:0;height:100%;font:13px/1.4 -apple-system,Segoe UI,Helvetica,Arial,sans-serif}
 #map{position:absolute;inset:0}
 .panel{background:rgba(255,255,255,.95);padding:10px 12px;border-radius:6px;box-shadow:0 1px 6px rgba(0,0,0,.25);max-width:340px}
 .panel h3{margin:0 0 6px;font-size:14px}
 .sw{display:inline-block;width:14px;height:10px;margin-right:6px;vertical-align:middle;border:1px solid #333}
 .tag{display:inline-block;width:18px;height:18px;border-radius:50%;color:#fff;font-weight:700;text-align:center;line-height:18px;margin-right:6px}
 .lbl{background:none;border:none;box-shadow:none;font-weight:700;font-size:15px;color:#fff;text-shadow:0 0 3px #000,0 0 3px #000}
 #coords{font-family:ui-monospace,Menlo,monospace}
 table.pp td{padding:1px 6px 1px 0;vertical-align:top}
 .grad{height:10px;width:200px;background:linear-gradient(to right,#2c0b4e,#8a226a,#e55c30,#fbd243)}
 .small{color:#555;font-size:11px}
</style></head><body><div id="map"></div>
<script>
const D = __DATA__;
const map = L.map('map', {worldCopyJump:true}).setView([-34, 94], 5);
const ocean = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}',
  {maxZoom: 13, attribution: 'Basemap &copy; Esri, GEBCO, NOAA, NGS'}).addTo(map);
const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 13, attribution: '&copy; OpenStreetMap'});

// heat layers
const heat = {};
for (const [name, b64] of Object.entries(D.heat)) {
  heat[name] = L.imageOverlay('data:image/png;base64,' + b64, D.heatBounds, {opacity: 0.85, interactive: false});
}
heat[D.defaultHeat].addTo(map);

// searched ground
const searchLayer = L.geoJSON(D.search, {
  style: f => { const c = (D.campaignStyle[f.properties.campaign] || {colour:'#999'}).colour;
    const gap = f.properties.pod === 0;
    return {color: gap ? '#d7191c' : c, weight: gap ? 1.5 : 1, fillColor: gap ? '#d7191c' : c,
            fillOpacity: gap ? 0.6 : 0.18, dashArray: f.properties.method === 'assumed' || f.properties.method === 'inferred' ? '4 4' : null}; },
  onEachFeature: (f, l) => l.bindPopup(`<b>${f.properties.name}</b><br>${(D.campaignStyle[f.properties.campaign]||{}).label||f.properties.campaign}
    <br>Detection probability (best / low / high): ${f.properties.pod} / ${f.properties.pod_low} / ${f.properties.pod_high}
    <br>Area: ${f.properties.area_km2.toLocaleString()} km² &nbsp; Source type: ${f.properties.method}`)
}).addTo(map);

const remaining = L.geoJSON(D.remaining, {style: {color:'#111', weight:2, dashArray:'6 4', fillOpacity:0}})
  .bindPopup('<b>Ocean Infinity contract: remaining area (approx.)</b><br>~7,429 km² left under the extension to 30 June 2027. '+
             'Reconstructed from an OI slide; no official coordinates. It lies on the near side of the arc; the default '+
             'mixture gives it about 0.001% of the probability (about 0.002% if the satellite model is right).').addTo(map);

// 7th arc
const arcLine = L.polyline(D.arc, {color:'#000', weight:2}).bindTooltip('7th arc (00:19:29 UTC), sea level').addTo(map);
const sat90 = L.polyline(D.sat90, {color:'#00e5ff', weight:7, opacity:0.8})
  .bindTooltip('Satellite-data 90% range along the arc: ' + D.sat90txt).addTo(map);

// hypothesis blocks
function popupBlock(p) {
  return `<b>${p.title ? p.title : 'Rank ' + p.rank + ' unsearched block'}</b>` +
    (p.note ? `<br><span class="small">${p.note}</span>` : '') +
    `<table class="pp"><tr><td>Centre</td><td><b>${p.centre}</b></td></tr>
     <tr><td>Latitude</td><td>${p.lat_range}</td></tr><tr><td>Longitude</td><td>${p.lon_range}</td></tr>
     <tr><td>Corners</td><td>${p.corners}</td></tr><tr><td>Position</td><td>${p.across_arc}</td></tr>
     <tr><td>Area</td><td>${Math.round(p.area_km2).toLocaleString()} km²</td></tr>
     <tr><td>Probability inside</td><td>${(100*p.mass).toFixed(1)}% (of this scenario; ${(100*p.mass_sat).toFixed(1)}% if the satellite model is right)</td></tr>
     <tr><td>Chance a new search finds it</td><td>${(100*p.p_success).toFixed(1)}% (at 90% detection)</td></tr>
     <tr><td>Already searched</td><td>${(100*p.prev_searched).toFixed(0)}%</td></tr></table>
     <span class="small">${p.scenario}</span>`;
}
const hyp = L.geoJSON(D.hyp, {
  style: f => ({color: f.properties.colour, weight: 3, fillColor: f.properties.colour, fillOpacity: 0.12,
                dashArray: f.properties.dashed ? '6 4' : null}),
  onEachFeature: (f, l) => { l.bindPopup(popupBlock(f.properties), {maxWidth: 360});
    const c = l.getBounds().getCenter();
    L.marker(c, {icon: L.divIcon({className:'lbl', html: f.properties.letter, iconSize:[16,16]})}).addTo(hypLabels); }
});
const hypLabels = L.layerGroup();
hyp.addTo(map); hypLabels.addTo(map);

const top5 = {};
for (const [k, fc] of Object.entries(D.top5)) {
  top5[k] = L.geoJSON(fc, {style: {color:'#ffd400', weight:1.5, dashArray:'3 3', fillOpacity:0.05},
    onEachFeature: (f, l) => l.bindPopup(popupBlock(f.properties), {maxWidth: 360})});
}

// points
const kindStyle = {ours: '#00e5ff', pub: '#ffffff', acoustic: '#b3de69'};
const pts = L.layerGroup();
for (const p of D.points) {
  L.circleMarker([p.lat, p.lon], {radius: 6, color: '#000', weight: 1.5, fillColor: kindStyle[p.kind], fillOpacity: 1})
   .bindPopup(`<b>${p.name}</b><br>${Math.abs(p.lat).toFixed(3)}°S ${p.lon.toFixed(3)}°E<br><span class="small">${p.note}</span>`)
   .bindTooltip(p.name).addTo(pts);
}
pts.addTo(map);

const overlays = {
  '<b>Areas 1–3, satellite-only pick, re-search block</b>': hyp, 'Area labels': hypLabels,
  'Searched ground (2014–2026)': searchLayer, 'OI contract: remaining strip': remaining,
  '7th arc': arcLine, 'Satellite 90% range on arc': sat90, 'Candidate points': pts,
  'Top-5 unsearched blocks, drift w=0 (mixture)': top5['w0'], 'Top-5 unsearched blocks, drift w=0.5 (mixture, default)': top5['w0.5'],
  'Top-5 unsearched blocks, drift w=1 (mixture)': top5['w1'],
};
L.control.layers(Object.assign({'Ocean basemap (Esri)': ocean, 'OpenStreetMap': osm}), overlays, {collapsed: true, position: 'topright'}).addTo(map);

// heat selector + legend + info
const info = L.control({position: 'topleft'});
info.onAdd = () => { const d = L.DomUtil.create('div', 'panel');
  let opts = Object.keys(heat).map(n => `<option ${n===D.defaultHeat?'selected':''}>${n}</option>`).join('');
  d.innerHTML = `<h3>MH370 open-data reanalysis: results</h3>
   <div class="small">Independent, public-data-only analysis (5–6 Nov 2026). Not authoritative. Click any shape or point for coordinates.
   Default layer: satellite data plus a deliberately vague 'model is wrong somewhere' alternative (prior weight 1 in 10; 0.46 after
   the debris drift and the empty searches), drift weight 0.5, minus what past searches would have found.</div>
   <p style="margin:6px 0 2px"><b>Probability layer</b></p><select id="heatSel" style="max-width:310px">${opts}<option>(none)</option></select>
   <div class="grad" style="margin-top:6px"></div><div class="small">0.1% → 100% of the peak probability (log scale); cells outside the top 99.5% hidden</div>
   <p style="margin:8px 0 2px"><b>Where the probability is now (7,500 km² blocks)</b></p>
   ${D.hyp.features.map(f => `<div><span class="tag" style="background:${f.properties.colour}">${f.properties.letter}</span>${f.properties.centre} – ${f.properties.title} (${(100*f.properties.mass).toFixed(1)}%)</div>`).join('')}
   <p style="margin:8px 0 2px"><b>Searched ground</b></p>
   ${Object.values(D.campaignStyle).map(s => `<div><span class="sw" style="background:${s.colour}"></span>${s.label}</div>`).join('')}
   <div><span class="sw" style="background:#d7191c"></span>Documented gaps inside searched areas</div>
   <div><span class="sw" style="border:2px dashed #111;background:none"></span>OI contract area still to search</div>
   <p style="margin:8px 0 0" class="small">Cursor: <span id="coords">–</span></p>`;
  L.DomEvent.disableClickPropagation(d); L.DomEvent.disableScrollPropagation(d); return d; };
info.addTo(map);
let current = heat[D.defaultHeat];
document.getElementById('heatSel').addEventListener('change', e => {
  if (current) map.removeLayer(current); current = heat[e.target.value] || null; if (current) current.addTo(map); });
map.on('mousemove', e => { const la = e.latlng.lat, lo = e.latlng.lng;
  document.getElementById('coords').textContent = `${Math.abs(la).toFixed(3)}°${la<0?'S':'N'} ${lo.toFixed(3)}°E`; });
L.control.scale({imperial: false}).addTo(map);
</script></body></html>
"""
(OUT / "mh370_results_map.html").write_text(HTML.replace("__DATA__", json.dumps(data)))

# ----------------------------------------------------------------- static PNG
import shapefile  # pyshp

fig, ax = plt.subplots(figsize=(13, 10.5), dpi=130)
ax.set_facecolor("#dfe9f3")
lon0, lon1, lat0, lat1 = 79.0, 106.0, -43.5, -21.0
rgba = colourise(HEAT_LAYERS[DEFAULT_HEAT])
ax.imshow(rgba, origin="lower", extent=[LON[0] - .025, LON[-1] + .025, LAT[0] - .025, LAT[-1] + .025],
          interpolation="nearest", zorder=2)
for f in search["features"]:
    g = shape(f["geometry"])
    pr = f["properties"]
    c = "#d7191c" if pr["pod"] == 0 else CAMPAIGN_STYLE.get(pr["campaign"], ("#999",))[0]
    ls = "--" if pr["method"] in ("assumed", "inferred") else "-"
    for poly in getattr(g, "geoms", [g]):
        x, y = poly.exterior.xy
        ax.fill(x, y, color=c, alpha=0.18 if pr["pod"] else 0.6, zorder=3, lw=0)
        ax.plot(x, y, color=c, lw=0.8, ls=ls, zorder=4)
rx, ry = zip(*remaining["rings"][0])
ax.plot(rx, ry, color="k", lw=1.6, ls=(0, (5, 3)), zorder=5)
ax.annotate("OI contract\nremaining strip\n(≈0% here)", (np.mean(rx), np.mean(ry)), (np.mean(rx) - 3.2, np.mean(ry) + 2.6),
            fontsize=8, ha="center", zorder=9, arrowprops=dict(arrowstyle="-", lw=0.6, color="#333"),
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
ax.plot(arc[:, 1], arc[:, 0], "k-", lw=1.4, zorder=6, label="7th arc (00:19:29 UTC)")
s90 = np.array(sat90)
ax.plot(s90[:, 1], s90[:, 0], color="#00b8d4", lw=6, alpha=0.8, zorder=5, solid_capstyle="round",
        label="Satellite-data 90% range on the arc")
LABEL_OFFS = {"1": (1.3, 0.35), "2": (1.2, -0.75), "3": (1.3, -0.35), "S": (-0.9, -0.85), "R": (-1.2, 0.85)}
for L_, title, row, col, _, dashed in HYP:
    cs = corners(row)
    xs = [c[1] for c in cs] + [cs[0][1]]
    ys = [c[0] for c in cs] + [cs[0][0]]
    ax.fill(xs, ys, color=col, alpha=0.15, zorder=7)
    ax.plot(xs, ys, color=col, lw=2.4, zorder=8, ls=(0, (4, 2)) if dashed else "-")
    dx, dy = LABEL_OFFS.get(L_, (0, 0))
    ax.plot([row.centre_lon, row.centre_lon + dx], [row.centre_lat, row.centre_lat + dy], color=col, lw=1.2, zorder=9)
    ax.text(row.centre_lon + dx, row.centre_lat + dy, L_, color="white", fontsize=14, fontweight="bold", ha="center",
            va="center", zorder=10, path_effects=[matplotlib.patheffects.withStroke(linewidth=3, foreground="black")])
kc = {"ours": "#00e5ff", "pub": "white", "acoustic": "#b3de69"}
offs = {"This project: satellite median": (-6.8, 1.6), "Satellite median if descending at 02:40": (-7.8, 2.6),
        "This project: debris drift peak": (-5.5, 3.0),
        "DSTG (Australian Defence) peak": (-6.6, 2.6), "UGIB 2020 hotspot": (-0.8, 0.85),
        "CSIRO drift 2017": (1.1, -0.35), "WSPR claim (Godfrey et al.)": (0.7, 0.3),
        "Kadri 306 deg bearing x arc": (-7.6, -2.4), "Stead/LANL 246.9 deg timing-consistent point": (0.5, -1.0)}
for n, la, lo, k, _ in POINTS:
    if not (lon0 <= lo <= lon1 and lat0 <= la <= lat1):
        continue
    ax.scatter(lo, la, s=55, c=kc[k], edgecolors="k", linewidths=1.2, zorder=11)
    dx, dy = offs.get(n, (0.4, 0.4))
    ax.annotate(f"{n}\n{abs(la):.2f}°S {lo:.2f}°E", (lo, la), (lo + dx, la + dy), fontsize=7.5, zorder=12,
                arrowprops=dict(arrowstyle="-", lw=0.6, color="#333"),
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))
# land
try:
    sf = shapefile.Reader(str(next((ROOT / "data/raw/naturalearth/ne_10m_land").glob("*.shp"))))
    for shp_ in sf.shapes():
        pts_ = np.array(shp_.points)
        parts = list(shp_.parts) + [len(pts_)]
        for i in range(len(parts) - 1):
            seg = pts_[parts[i]:parts[i + 1]]
            if seg[:, 0].max() < lon0 - 5 or seg[:, 0].min() > lon1 + 5 or seg[:, 1].max() < lat0 - 5 or seg[:, 1].min() > lat1 + 5:
                continue
            ax.fill(seg[:, 0], seg[:, 1], color="#cfc6b4", zorder=1, lw=0.3, ec="#8a8070")
except StopIteration:
    pass
ax.set_xlim(lon0, lon1)
ax.set_ylim(lat0, lat1)
ax.set_aspect(1 / np.cos(np.radians((lat0 + lat1) / 2)))
ax.set_xlabel("Longitude (°E)")
ax.set_ylabel("Latitude (°S shown as negative)")
ax.grid(alpha=0.3, zorder=0)
ax.set_title("MH370 public-data reanalysis: probability left after past searches (default: satellite data + a 1-in-10 "
             "'model is wrong'\nalternative, debris drift weight 0.5). Areas 1–3, satellite-only pick (S) and re-search "
             "block (R), 7,500 km² each", fontsize=10.5)
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
handles = [Line2D([], [], color="k", lw=1.4, label="7th arc"),
           Line2D([], [], color="#00b8d4", lw=6, alpha=0.8,
                  label=f"Satellite 90% range on arc ({SAT_90[0]:.1f}–{SAT_90[1]:.1f}°S)")]
handles += [Patch(fc=v[0], alpha=0.35, ec=v[0], label=v[1]) for v in CAMPAIGN_STYLE.values()]
handles += [Patch(fc="#d7191c", alpha=0.6, label="Documented gaps in searched areas"),
            Line2D([], [], color="k", ls=(0, (5, 3)), label="OI contract area still to search")]
handles += [Patch(fc=c, ec=c, alpha=0.4, ls="--" if d else "-",
                  label=f"{L_}: {abs(_published(r)[0]):.2f}°S {_published(r)[1]:.2f}°E – {t.split(': ', 1)[-1]} ({r.mass:.1%})")
            for L_, t, r, c, _, d in HYP]
ax.legend(handles=handles, loc="upper left", fontsize=7.5, framealpha=0.92)
sm = cm.ScalarMappable(norm=colors.Normalize(-3, 0), cmap=colors.ListedColormap(cm.inferno(np.linspace(0.15, 1, 256))))
cb = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.01)
cb.set_label("log10(probability / peak)")
fig.text(0.01, 0.005, "Independent public-data reanalysis (mh370-open, 5–6 Nov 2026); not authoritative. Percentages: share of the "
         "remaining probability (S: with the drift set aside; about 2% at the default).\nHow much to doubt the satellite model "
         "(the 1-in-10 prior) is a judgement call; below about 0.06, areas 1 and 2 swap places. OI 2025-26 footprint is assumed.\n"
         "Anderson's Java point (8.36°S 107.92°E, a natural earthquake) lies outside this view.",
         fontsize=7.5, color="#444")
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(OUT / "mh370_results_map.png")
print("wrote", OUT / "mh370_results_map.html", OUT / "mh370_results_map.png")
for L_, t, r, c, _, _ in HYP:
    print(L_, f"{abs(_published(r)[0]):.2f}S {_published(r)[1]:.2f}E", r.scenario, r["mode"], round(r.mass, 4),
          round(r.p_success, 4), round(r.frac_previously_searched, 3))
