# Workstream C, part 1: reconstruction of the seafloor already searched, and its probability of detection (POD)

Independent, public-data-only reconstruction (mh370-open). **Not authoritative.** The ATSB part comes from
official machine-readable data. The Ocean Infinity 2018 part is digitised from official maps. The Ocean
Infinity 2025–26 part is **assumed** (no official map exists) and must be treated as such.

## Outputs

| file | content |
|---|---|
| `data/derived/search_pod.nc` | Common grid, all variables (lat, lon) float32: <br>• `pod` (best), `pod_low`, `pod_high`: probability that the wreck would have been detected had it been in the cell, cell mean; <br>• `searched_frac`, `searched_frac_low`, `searched_frac_high`: fraction of the cell inside any searched polygon; <br>• `cov_<campaign>`: per-campaign covered fraction. |
| `search_polygons.geojson` | All 38 reconstructed polygons (CRS84). Each has `campaign`, `pod`, `pod_low`, `pod_high`, `pod_basis`, `method` (machine-readable / digitised / inferred / assumed / derived), `est_error_km`, `area_km2_eqarea` and `source`. |
| `arc_profile.csv` | Searched cross-arc width vs latitude of the sea-level 7th arc. Transects run perpendicular to the arc over ±250 km at 0.25 km spacing; n > 0 is south-east of the arc (farther from the satellite). Columns: <br>• `searched_width_km` and `width_<campaign>_km`; <br>• `nw_edge_km`, `se_edge_km` and `contig_*` (the contiguous covered interval around the arc); <br>• `eff_width_km` (∫POD dn, best) with `_low`/`_high`; <br>• `mean_pod_25nm` and `frac_searched_25nm` / `frac_searched_70nm` (within ±25 NM and ±70 NM). |
| `area_summary.csv/.json` | Reconstructed areas vs published totals, overlaps, raster checks, the POD table. |
| `candidates_pod.csv` | POD at the published candidate points. |
| `fig_search_coverage.png` | Overview and hotspot zoom: campaigns, 7th arc, candidate points, documented gaps, the unsearched part of the OI contract area. |
| `fig_search_pod.png` | Maps of `pod_low`, `pod` and `pod_high`. |
| `fig_arc_profile.png` | Searched and POD-weighted width vs latitude. |
| `qa/` | QA maps from the polygon reconstruction (OI 2018 and OI 2025–26 overlays). |

Reproduce with:
- `.venv/bin/python -I scripts/search_build.py` (about 10 s)
- `.venv/bin/python -I scripts/search_plot.py`

The polygon inputs are rebuilt by these scripts, all of which read from `data/raw/`:
- `scripts/search_fetch_atsb_ga.py` and `scripts/search_build_atsb_polygons.py`
- `sh scripts/search_oi2018/run_all.sh`
- `scripts/search_oi2025/build_polygons.py`

Module: `src/mh370/search.py`.

## Sources by campaign

| campaign | how obtained | position error | main sources |
|---|---|---|---|
| **ATSB 2014–17** underwater search | **Machine-readable** (official). Union of the Geoscience Australia / AusSeabed Phase-2 sonar coverage: <br>• deep-tow SSS from the WFS vector layer; <br>• AUV SSS, GO Phoenix SAS and Dong Hai Jiu 101 SAS from WMS alpha masks at 0.002°. <br>Largest piece kept, interior holes ≥ 0.1 km² kept as data gaps. | ~0.5 km | AusSeabed geoserver `https://warehouse.ausseabed.gov.au/geoserver/ows`; GA eCat 120969 (doi:10.4225/25/5b0cd3b139def), CC BY 4.0; ATSB *The Operational Search for MH370* (3 Oct 2017) pp. 45–96 incl. Fig. 73 (Wayback copy in `data/raw/atsb_ga_search/atsb_reports/`). |
| ATSB Fig. 73 confidence areas (red / orange / yellow / purple) | **Derived**: the envelope split by the ATSB's stated widths around GA's own 7th arc. | outer edges 0.5 km; internal boundaries ~3–7 km | same |
| **Bluefin-21 2014** (pinger-detection area) | **Machine-readable**: GA ArcGIS feature service `Bluefin_21_AreaSearched2014`. | ~0.5 km | `services1.arcgis.com/wfNKYeHsOyaFyPw3/...` (see `data/raw/atsb_ga_search/SOURCE.md`) |
| **Ocean Infinity 2018** (Seabed Constructor, Hugin AUVs) | **Digitised** from the 18 Malaysian "MH370 Operational Search Update" weekly PDFs (30 Jan – 29 May 2018; Wayback copies of mh370.gov.my). Each map was tied to its own graticule crosses with a projected (UTM 46S/47S) affine fit, residuals 0.07–0.22 km; outlines extracted by pixel colour. <br>Site 1 (36.5–32.1°S), Site 2 (32.8–31.2°S, Broken Ridge), Site 3 (31.7–28.3°S), Site 4 to 27 May. Remainder of the Site-4 box inferred. Final sweep 30 May – 7 Jun to ~25°S **inferred** from the AIS track plus contemporaneous reports. | 1–2 km (sites); inferred north end ±25 km along the arc | `data/raw/oi2018_search/SOURCE.md`; Ocean Infinity statements (10 Jan, 30 Apr, 29 May 2018); AirlineRatings 31 May 2018; radiantphysics.com (Iannello, Godfrey comments). |
| **Ocean Infinity 2025–26** | **Assumed**: no official map or coordinates exist. Footprints were built from the AIS tracks of Armada 78 06 and 86 05 (CAPTION KMLs), the official 7,571.46 km² tally (AAIB 8 Mar 2026), the OI daily and AAIB progress reports, and the inner edge of OI's March 2024 proposal slide. <br>Post-contract strip lies SE of the arc, 35.7–34.1°S, n ≈ +65…+99 km. A pre-contract SW survey (11–24 Mar 2025, to 36.6°S) is inferred from AIS only. | ±8 km (ends ±10 km) | MOT/AAIB update 8 Mar 2026; Ocean Infinity 8 Mar 2026; mh370-caption.net KMLs; radiantphysics.com posts 2024–26 (full list in `data/raw/oi2025_search/SOURCE.md`). |
| Documented gaps | HPSA (~25 km² digitised vs 30.5 km² published, 34.53°S 93.84°E, "never scanned" per Iannello 2023) and the GO Phoenix terrain gap (55 km², CAPTION KMZ). | 0.2–0.5 km | radiantphysics.com 11 Feb 2023; mh370-caption.net "Search areas.kmz" |
| Junction slivers (derived) | Gaps under ~3 km wide: <br>• between adjacent digitised OI 2018 sites (233 km²; official maps show the sites abutting); <br>• between the ATSB edge and the OI 2018 edges (457 km², mostly beside the Site-1 legs at 34.7–36°S). | – | morphological closing, see `search.build_items()` |

Excluded:
- **The 2014 surface and aerial search.** It was not a seafloor search.
- **The Phase-1 bathymetry survey** (GA-4421 Fugro Equator, GA-4422 Zhu Kezhen, GA-4430). Its 150 m multibeam cannot detect a debris field.
- **The Feb 2025 pre-contract "infill" region (~5,800 km² hull).** It is not a coverage polygon. Only the HPSA and GO Phoenix gap inside it are credited, with an uncertain POD.

Bluefin-21 (2014) was not excluded: it lies ~5 km from our sea-level 7th arc at 21.1°S, so it counts as arc coverage.

## Reconstructed vs published areas (km², equal-area EPSG:6933; geodesic agrees to <0.01%)

| campaign | best geometry | eroded (low) | dilated (high) | published |
|---|---|---|---|---|
| ATSB 2014–17 | **120,553** | 118,636 | 122,654 | "in excess of 120,000" (ATSB 2017) |
| OI 2018 (sites 1–4 + inferred north sweep + slivers) | **126,626** | 117,013 | 135,854 | ">112,000" on 29 May 2018 |
| OI 2025–26 (post-contract 7,572 + pre-contract SW 5,297 + HPSA infill 58) | **12,927** | 6,595 | 19,657 | 7,571 post-contract; the pre-contract area was never published |
| Bluefin-21 2014 | **769** | – | – | ~860 |
| **All campaigns (union)** | **255,609** | 241,164 | 266,708 | sum of published figures ≈ 240,000 before overlaps |

Notes on the totals:
- **Overlaps.** ATSB ∩ OI 2018 = 3,909 km², OI 2018 ∩ OI 2025–26 = 1,357 km², ATSB ∩ OI 2025–26 = 325 km².
- **OI 2018 up to 27 May** (official maps only) is 107,384 km², against 106,200 reported (+1.1%). Sites 1–4 with the full Site-4 box come to 110,923 km², which matches ">112,000". The extra ~15,000 km² is the inferred 30 May – 7 Jun sweep to ~25°S.
- **Cross-check on the OI total.** Ocean Infinity says it has mapped ">140,000 km² since 2018" (8 Mar 2026). Our OI 2018 plus OI 2025–26 comes to 139,553 km², consistent.
- **POD-weighted area** (∫ POD dA): best 232,334 km², low 186,458 km², high 260,514 km².

## POD model

Each campaign assigns one detection probability d_c(x) to each point, painted in order so that gaps override coverage. Campaigns are then combined:
- **best and high:** POD = 1 − Π(1 − d_c), i.e. misses are independent between campaigns;
- **low:** POD = max d_c, i.e. misses are fully correlated, for example because of terrain.

Geometric uncertainty is folded into the bounds:
- **`pod_low`:** coverage is eroded by its position error, measured only against each campaign's outer boundary after a 1 km closing, so the digitised edges between adjacent sites do not open fake gaps. Gaps are dilated.
- **`pod_high`:** the reverse — coverage dilated, gaps eroded.

The cell value is the mean over a 10×10 sub-sample of the cell (0.005°, about 0.5 km).

| class | pod / low / high | justification |
|---|---|---|
| ATSB Fig. 73 area (red / orange / yellow / purple) | 0.970/0.849/0.996; 0.947/0.817/0.985; 0.961/0.841/0.988; 0.965/0.844/0.992 | ATSB 2017 pp. 95–96: per-area shares of high-confidence coverage (HC, >95% detection), lower-POD coverage (LC, 50–90%, nominal 70%) and gaps (0%). <br>• mid = HC·0.975 + LC·0.7 <br>• high = HC + LC·0.9 <br>• low = (HC·0.95 + LC·0.5) × 0.9. The extra ×0.9 covers imagery-review and classification misses and data holidays smaller than the ATSB's 100 m metric. <br>Area-weighting our reconstruction reproduces the ATSB combined 97.4 / 2.1 / 0.5%. |
| ATSB envelope elsewhere | 0.960/0.84/0.993 | combined ATSB statistics |
| ATSB interior holes (19, 9.6 km²) | 0 | no imagery; the ATSB rates holidays at 0%. The ATSB's own 0.5% of gaps (~600 km²) are mostly under 200 m across and cannot be located from public data. They are carried inside the per-area mean instead. |
| HPSA / GO Phoenix gap (ATSB) | 0 / 0 / 0 (HPSA); 0 / 0 / 0.5 (GO Phoenix gap) | Iannello 2023; CAPTION KMZ |
| HPSA + GO Phoenix gap, Feb 2025 infill (OI 2025–26) | 0.5 / 0 / 0.9 | infill reportedly targeted earlier gaps, but which patches were filled is unknown |
| OI 2018 sites 1–4 | 0.92 / 0.80 / 0.98 | Hugin AUVs with SSS and MBES. Ocean Infinity reported "high quality data in which we have full confidence". It reportedly estimated ~99% coverage (Godfrey, 28 May 2018, unofficial); a second-hand figure of 3.1% data holidays also circulates. No official POD was published, and Broken Ridge is difficult terrain. |
| OI 2018 rest of the Site-4 box | 0.85 / 0.50 / 0.97 | completion inferred from the AIS track |
| OI 2018 northern sweep to ~25°S (inferred) | 0.50 / 0.15 / 0.85 | "gaps between AUV tracks opened out again" (R. Cole); AUVs recovered early; one swath 5.2 km instead of 7.4 km. The CAPTION outline independently reaches 24.73°S. |
| OI 2018 inter-site junction gaps | 0.92 / 0 / 0.98 | the official maps show the sites abutting |
| ATSB / OI 2018 junction slivers | 0.46 / 0 / 0.92 | could be digitising error (then covered) or real slivers (then 0) |
| OI 2025–26 post-contract (assumed) | 0.90 / 0.70 / 0.97 | modern Hugin AUVs, no published POD. The footprint is assumed (±8 km), and erosion in the low bound halves it. |
| OI 2025 pre-contract SW (assumed) | 0.60 / 0.20 / 0.92 | AIS envelope only; area never published |
| Bluefin-21 2014 | 0.90 / 0.70 / 0.97 | AUV side-scan; the ATSB found no debris |

All of these POD figures are judgements anchored on the published statements quoted above. None is a measured detection rate for an MH370-type debris field. The ATSB reports that a 200 m × 200 m low-lying debris field is detectable at altitudes of up to 200 m (p. 89).

## Validation

**Machine-readable ATSB data:**
- **GA layers agree with each other.** The WMS deep-tow mask matches the GA WFS vector coverage: 743 km² (0.7%) extra from edge pixels, 1 km² missing. The GA combined tile cache agrees with the union to within 0.6%.
- **CAPTION's ATSB outline agrees.** The "Australia/China/Malaysia 2014–2017 search" outline in the CAPTION KMZ lies within 0.10 km (median) and 0.54 km (p90) of our ATSB boundary.

**Digitised OI 2018:**
- **Independent community outline.** CAPTION's "Ocean Infinity 2018 search" outline is within 2.2 km (median) and 4.4 km (p90) of our OI 2018 / ATSB envelope. It reaches 24.73°S, which supports the inferred final sweep to ~25°S.
- **Ocean Infinity's own outline.** The OI-supplied outline published by Iannello (Feb 2023) matches our Site-1 edges near 34.2°S to 1–3 km.
- **Two weekly maps of Site 1** agree to a median of 0.7 km (p90 1.8 km).

**Areas:**
- ATSB: 120,553 km² against "in excess of 120,000".
- OI 2018 to 27 May: 107,384 km² against 106,200 reported.
- OI cumulative: 139,553 km² against ">140,000".

**Arc reference.** GA's published 7th arc (described as drawn at 40,000 ft) is a uniform 13.4 km (7.2 NM) south-east of the project's sea-level arc. Measured from GA's arc, the searched widths match the ATSB text: yellow 10/13 NM, orange 23/17 NM, outer 36/41 NM. Measured from our arc, the ATSB strip north of ~34.5°S reaches only ~2–8 km north-west of the arc. That ground is covered by OI 2018 instead (its NW leg starts at about −1 to −4 km).

## Searched width along the arc (from `arc_profile.csv`; 10th–90th percentile within each band; POD-weighted width given as best / low / high, km)

| arc latitude | searched width | coverage | POD-weighted width |
|---|---|---|---|
| 39.4–36.1°S | ~135–143 km | ATSB only, n ≈ −52…+91 | 130–138 / 113–120 / 135–143 |
| 36.0–33.7°S | ~145 km | ATSB strip + OI 2018 legs + OI 2025–26 SE strip (n to +99) | 129–136 / 92–102 / 151–156 |
| 33.6–31.5°S | ~110 km | ATSB north end + OI Site 2 | 100–106 / 84–88 / 110–115. Dip at 32.4°S at the Site 1/2 junction. |
| 31.4–26.6°S | ~81–87 km (±~22 NM) | OI Site 3/4 | 74–80 / 62–67 / 82–88 |
| 26.5–25.0°S | ~81 km | inferred OI sweep | 41 / 11 / 78 |
| north of 25.0°S | 0 | except Bluefin-21 near 21.1°S (~26 km across) | – |
| south of 39.4°S | 0 | – | – |

## Candidate points (published claims; POD from this layer)

| candidate | lat, lon | n from arc (km) | POD best / low / high | searched by |
|---|---|---|---|---|
| UGIB LEP (2020) | 34.234°S 93.788°E | +3 | 0.961 / 0.841 / 0.988 | ATSB |
| CSIRO drift 2017 | 35.6°S 92.8°E | +51 | 0.920 / 0.800 / 0.980 | OI 2018 (SE leg of Site 1) |
| WSPR (Godfrey 2024) | 29.128°S 99.934°E | **+84** | **0** | **not searched**: OI 2018 reached only about +44 km at that latitude |
| Ulich & Iannello drift 2023 (34.0°S on the arc) | 34.0°S 94.03°E | 0 | 0.961 / 0.841 / 1.0 | ATSB |
| Kadri 306° bearing crossing | 25.7°S 101.4°E | +1 | 0.50 / 0.15 / 0.85 | only the inferred OI 2018 final sweep |
| Stead 246.9° timing-consistent point | 41.0°S 81.0°E | −17 | **0** | not searched; south-west of the ATSB area |
| Anderson Java event | 8.36°S 107.92°E | −0.5 | **0** | not searched; outside the common grid |

## Limitations

1. **OI 2025–26 is an assumption.** Neither the contract area nor the coverage has been published. The ±8 km error and the uncertainty about the pre-contract survey dominate the hotspot area. Treat the `pod_low` and `pod_high` spread there as real uncertainty.
2. **OI 2018 north of 26.3°S** has no official map, and the sweep quality was reduced.
3. **The ATSB's lower-POD areas (2.1%) and small holidays (0.5%) cannot be located.** They enter only through per-area mean POD values, which spreads a localised risk uniformly.
4. **Independence of misses between campaigns** is assumed in `pod` and `pod_high`. The low bound uses max() instead.
5. **The POD is for a debris field on the seabed.** It does not cover burial, extreme terrain shadow beyond the published holiday statistics, or a field that was imaged but misclassified, beyond the ×0.9 allowance in the low bound.
6. **The junction slivers (~690 km²)** may be either digitising artefacts or real unsearched strips. Their POD is set to straddle both.

Python packages used: `pyshp` (Natural Earth coastlines). The reconstruction scripts also installed `pymupdf` and `opencv-python-headless` into `.venv` for PDF and image extraction during digitising. No package requiring sign-up was used.
