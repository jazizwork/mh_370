# oi2018_search — Ocean Infinity 2018 MH370 seabed search: sources and provenance

Retrieved: 2026-11-05 (all files). Downloads are UNTRUSTED data: nothing in this directory is executed.
Processing scripts: `scripts/search_oi2018/` (run `sh scripts/search_oi2018/run_all.sh` from the project root).

No machine-readable (KML/shapefile/GeoJSON/coordinate table) outline of the 2018 OI coverage was found in
any public source. The polygons here were DIGITISED from the official Malaysian weekly
"MH370 Operational Search Update" maps, except the northern end (~26.3–25.0°S), which is INFERRED
(see "Polygons" below).

## 1. Official: Government of Malaysia "MH370 Operational Search Update" #1–#18 (`weekly_updates/`)

- Publisher: Government of Malaysia (MH370 Response Team / Ministry of Transport), originally on
  `http://mh370.gov.my/en/mh370-underwater-search-2018?download=<id>:<name>`. The originals are no longer
  online. Archived copies were fetched from the Internet Archive Wayback Machine with the `id_` (raw bytes)
  flag: `https://web.archive.org/web/<timestamp>id_/<original URL>`.
- Licence/terms: Government of Malaysia publication. No licence is stated. The pages are marked "FOR OFFICIAL USE
  ONLY", but they were publicly released on mh370.gov.my and also mirrored on oceaninfinity.com (OSU#1–#15).
  They are kept here for research and attribution only; redistribution rights are unclear.

| file | period covered | Wayback timestamp | download id |
|---|---|---|---|
| OSU01_2018-01-30.pdf | 21–28 Jan | 20201109043738 | 109:english-version |
| OSU02_2018-02-06.pdf | 29 Jan–4 Feb | 20201109021819 | 111:english-version |
| OSU03_2018-02-13.pdf | 4–10 Feb | 20190822113407 | 113:13-february-2018-english-version&start=20 |
| OSU04_2018-02-20.pdf | 11–18 Feb | 20201109033656 | 115:20-february-2018-english-version |
| OSU05_2018-02-27.pdf | 19–25 Feb | 20201109030049 | 117:27-february-2018-english-version |
| OSU06_2018-03-06.pdf | 26 Feb–4 Mar | 20201109004416 | 119:6-march-2018-english-version |
| OSU07_2018-03-13.pdf | 5–11 Mar | 20220221132330 | 127:13-march-2018-english-version |
| OSU08_2018-03-20.pdf | 12–18 Mar | 20190822115654 | 128:20-march-2018-english-version&start=20 |
| OSU09_2018-03-27.pdf | 19–25 Mar | 20220618170513 | 131:27-march-2018-english-version |
| OSU10_2018-04-03.pdf | 26 Mar–1 Apr | 20220618170453 | 132:3-april-2018-english-version |
| OSU11_2018-04-10.pdf | 2–8 Apr | 20220618170426 | 134:10-april-2018-english-version |
| OSU12_2018-04-17.pdf | 9–15 Apr | 20220618170404 | 136:17-april-english-version |
| OSU13_2018-04-24.pdf | 16–22 Apr | 20220618170344 | 139:24-april-2018-english-version |
| OSU14_2018-05-01.pdf | 23–29 Apr | 20220618170319 | 140:1-may-2018-english-version |
| OSU15_2018-05-08.pdf | 30 Apr–6 May | 20220618170259 | 144:8-may-2018-english-version |
| OSU16_2018-05-15.pdf | 7–13 May | 20220618170209 | 146:15-may-2018-english-version |
| OSU17_2018-05-22.pdf | 14–20 May | 20220618170150 | 148:22-may-2018-english-version |
| OSU18_2018-05-29.pdf | 21–27 May | 20190920215828 | 150:29-may-2018-english-version |

There is no #19. A 2019 snapshot of the listing page still shows #18 as the latest.
OSU#1–#15 were also mirrored at `https://oceaninfinity.com/wp-content/uploads/MH370-Search-Weekly-Report-<n>.pdf`
(Wayback CDX lists them). Those were not downloaded because they duplicate the files above.

Reported cumulative areas, quoted from the PDFs:
- 4,500 km² (28 Jan); 7,500 (4 Feb); 8,200 (25 Feb); 16,000 (4 Mar); 24,000 (11 Mar); 29,500 (18 Mar); 33,000 (25 Mar); 37,000 (1 Apr).
- "Total area covered in Site 1 is 38,214 square kilometres" (#11, 10 Apr).
- Site 1+2: 53,000 (#12, 17 Apr). Site 3: +11,500 (#13), 20,000 (#14), 23,500 (#15), 33,000 (#16).
- "within Site 1, Site 2 and Site 3 is 88,200 square kilometres and 8,000 [#17] / 18,000 [#18] square kilometres within Site 4".
- OSU#1 note: "The Primary search area covers an area of 25,000 square kilometres, the total area including the Supplementary area would cover an area of 33,012 square kilometres."

`figures_extracted/`: the embedded raster images, extracted losslessly from the PDFs with PyMuPDF.
Name pattern: `OSU<nn>_p<page>_x<xref>_<w>x<h>.png`. Figures used:
- `OSU01_p1_x11_1400x944.png`: planning map, Sites 1–3 (Site 1 33,012 km²; Site 2 19,596 + 2,266 km²;
  Site 3 17,425 + 9,204 km²). Labelled graticule. Used for validation; the projection is UTM 46S.
- `OSU10_p2_x36_586x612.png`, `OSU11_p2_x31_451x465.png`: Site 1 coverage on 1 Apr and at completion.
- `OSU17_p2_x32_610x442.png`: Site 2 coverage (complete). `OSU17_p2_x37_538x564.png`: Site 3 coverage (complete).
- `OSU17_p3_x41_663x696.png`, `OSU18_p3_x40_499x521.png`: Site 4 box and coverage on 20 May and 27 May.
- `OSU17_p1_x19_696x493.png`, `OSU18_p1_x18_588x420.png`: overview of all four sites (P04S01_v11, P04S02_v18,
  P04S03_v16, P04S04_v7). These are low resolution and were not used for coordinates.

## 2. Official: Malaysian Ministry of Transport, 10 Jan 2018 (`mot_jan2018/`)

- `MOT_MH370_Search_Operation_by_OI_Map_2018-01-10.pdf`: slides showing the primary (5,000 km²),
  secondary (10,000), tertiary (10,000) and supplementary areas around "35.6°S 92.8°E".
  - Source: https://web.archive.org/web/20180127224153id_/http://www.mh370.gov.my:80/phocadownload/News/MH370%20Search%20Operation%20by%20OI%20Map.pdf
- `MOT_Talking_points_MH370_Search_Operation_OI_2018-01-10.pdf`: the minister's talking points, including the
  25,000 km² / 90-day agreement and the payment tiers.
  - Source: https://web.archive.org/web/20180305005521id_/http://www.mh370.gov.my:80/phocadownload/News/Talking%20points%20MH370%20Search%20Operation%20OI.pdf
- Licence: same as section 1 (Government of Malaysia, no licence stated).

## 3. Ocean Infinity statements (`oi_statements/`, `oi_images/`)

All are Wayback raw copies of oceaninfinity.com pages. © Ocean Infinity; no licence stated.
- `OI_continue_search_2018-01-10.html`: https://oceaninfinity.com/ocean-infinity-continue-search-missing-malaysian-airlines-flight-mh370/ (ts 20180110224406)
- `OI_update_2018-05-02.html`: "Update on search…", dated 30/04/2018. Says "nearly 80,000 km2, covering up to 1,300 km2 per day".
  - https://oceaninfinity.com/update-search-missing-malaysian-airlines-flight-mh370/ (ts 20180502153355)
- `OI_conclusion_2018-05-29.html`: "searched and collected high quality data from over 112,000 km2".
  - https://oceaninfinity.com/conclusion-current-search-malaysian-airlines-flight-mh370/ (ts 20180530035152)
- `OI_mh370_page_2018-05-27.html`: https://oceaninfinity.com/mh370/ (ts 20180527120208)
- `OI_weekly_report_10.html`, `OI_weekly_report_11.html`: HTML versions of OSU#10 and #11 (ts 20180412145307, 20180412145427).
- `oi_images/Site-1_Site-2_05.15.18-540x242.png`: thumbnail only, not used.
  - https://oceaninfinity.com/wp-content/uploads/Site-1_Site-2_05.15.18-540x242.png

## 4. Community data

### `community_kmz_labratsr/`: Google Earth KMZ files by Reddit user "LabratSR"

- Source: Dropbox folder https://www.dropbox.com/scl/fo/v9spd9uo8pwlrrspa1n64/AOHexlWeRf6ScReRAMmNlyM?rlkey=ky98n4uw6ize9s8hoc2ezbven&dl=1,
  linked from r/MH370 and r/ArmadaVessels, post "Google Earth KMZ/KML Files For the Search So Far", 1 Mar 2025.
  The post was read through Wayback, ts 20250510075400.
- Licence: none stated (community post). Use for research with attribution.
- The useful files are `Seabed Constructor Track {December 2017 … May 2018, 607 Final}.kmz`. These are AIS
  positions of the vessel exported with GPS Visualizer.
  - Timestamps are locale-mangled: for day ≤ 12 they read YYYY-DD-MM. `scripts/search_oi2018/parse_tracks.py`
    fixes this using each file's month.
  - Output: `data/derived/oi2018_search/seabed_constructor_track_2018.csv` (66,218 points, 1 Dec 2017 – 8 Jun 2018).
- These are VESSEL positions, not AUV coverage. They were used only to check the timing and northern extent of the
  final (unmapped) phase.
- The zip also contains 2025–26 Armada tracks, the 7th-arc lines, and the GA bathymetry/backscatter KMZs. Those
  were not used.

### `community_maps/`: community map images (© their authors; no licence stated)

- `radiantphysics_2026-01-01_image-3.png`: V. Iannello, "The Search for MH370 Continues into 2026" (1 Jan 2026).
  - https://mh370.radiantphysics.com/wp-content/uploads/2026/01/image-3.png
  - No graticule; not digitised.
- `iannello_2023-02-11_OI-outline-image-4.png`: V. Iannello, "A High Priority Area to Search for MH370" (11 Feb 2023).
  - https://mh370.radiantphysics.com/wp-content/uploads/2024/05/image-4.png
  - Shows the OI-SUPPLIED outline of the 2018 AUV coverage near 34.2°S, with a 0.1° graticule. It was used to
    VALIDATE the Site 1 digitisation (`scripts/search_oi2018/iannello_check.py`).
- `godfrey_2023-12-22_GE-Bathymetry-MH370-UWA-and-WSPR.jpg`: R. Godfrey, mh370search.com, 22 Dec 2023.
  - https://www.mh370search.com/wp-content/uploads/2023/12/GE-Bathymetry-MH370-UWA-and-WSPR-1-pdf.jpg
- `godfrey_2025-03-20_UWA-vs-WSPR-Search-Areas.png`: R. Godfrey, 20 Mar 2025.
  - https://www.dropbox.com/scl/fi/ksjx9e3mlm1m8gb1nv0e5/UWA-vs-WSPR-Search-Areas.png?rlkey=tjy09ia8mrbaegftvpstgvk2k&dl=0
  - This and the previous file are oblique Google Earth views with schematic OI-2018 lines (~27.5–34.5°S). Not digitised.

### Checked and rejected

- github.com/mkmyhre/mh370-analysis-tool, `src/constants.ts` `SEARCHED_2018`: a crude lon/lat bounding box
  (93.5–97°E, 36–24.7°S). Wrong and not used.
- AusSeabed/Geoscience Australia MH370 WMS coverage layers: these are ATSB-era (2014–17) data only, not OI 2018.

## 5. Digitisation products (`digitisation/`, created by this workstream, not downloaded)

- `*_georef_polys.json`: per-map control points (graticule crosses: lon, lat, px, py), residuals, the affine
  (projected CRS → pixel) parameters, and the extracted outline vertices (pixel and lon/lat).
  `*_overlay.png` and `*_mask.png` are the visual checks.
- Projections were identified from graticule geometry:
  - OSU#1 planning map: UTM 46S (EPSG:32746), 0.21 px rms over 4,473 dash pixels.
    For comparison: LCC gave 0.50 px, UTM 47S 0.84, Mercator 1.03, plate carrée 1.13.
  - Site 1 and Site 2 maps: UTM 46S. Site 3 and Site 4 maps: UTM 47S (meridian 99°E vertical).
- Georeference rms (km): Site 1 (OSU11) 0.22, Site 2 0.12, Site 3 0.22, Site 4 (OSU18) 0.07 (4 points only).
  Check maps: OSU10 0.87, OSU17 Site-4 map 0.18.
- `osu01_planning_map_georef_utm46s.json`: the graticule fit plus 48 intersection control points.
- `cross_arc_profile.csv`: covered segments, as signed distance from the sea-level 7th arc (d > 0 = SE), every 0.1° of arc latitude.
- Validation:
  - Site 4 box corners from the OSU17 and OSU18 maps agree within 0.3 km.
  - Site 3 NE corners match the Site 4 SW corners within 1 km.
  - Site 1 boundaries from OSU10 and OSU11 differ by a median of 0.7 km (p90 1.8 km).
  - Site 1 edges near 34.2°S match the OI-supplied outline in Iannello (2023):
    - OI outline: −45, −4, +35, +64 km from the arc.
    - Digitised: −44, −2, +36, +67 km.
  - Digitised areas vs reported areas (km²):

    | | digitised | reported |
    |---|---|---|
    | Site 1 | 39,379 | 38,214 |
    | Site 2 | 15,025 | 14,786 |
    | Site 3 | 34,848 | 35,200 |
    | Site 4 to 27 May | 18,249 | 18,000 |
    | union to 27 May | 107,384 | 106,200 |

- The OSU#1 map's own "7thArc" line deviates from the sea-level arc in `mh370.geo` by up to ~16 km (a chord-like bow).
  The coordinates here come from the graticule, not from that line.

## 6. Polygons (`polygons_oi2018.json`, `polygons_oi2018.geojson`)

Written by `scripts/search_oi2018/assemble.py`. Each entry has: name, source, method (digitised / inferred),
est_error_km, notes, reported_area_km2, area_km2_eqarea (EPSG:6933), and closed [lon, lat] rings.
`OI2018_North_extension_inferred` is NOT from any map. It continues the Site 4 corridor (−37..+44 km from the arc)
from 26.3°S to arc-latitude 25.0°S. The evidence is the AIS track (vessel at 24.76°S on 6 Jun 2018); Iannello,
8 Jun 2018 ("searched as far north as 25S and at a width of at least +/-22 NM",
https://mh370.radiantphysics.com/2018/06/08/an-mh370-flight-path-ending-further-north-on-7th-arc/); Godfrey's daily
comments at https://mh370.radiantphysics.com/2018/05/16/sixty-minutes-australia-story-on-mh370-is-a-sensation/;
and AirlineRatings, 31 May 2018 (https://www.airlineratings.com/articles/mh370-auvs-final-sweep-search-end).
