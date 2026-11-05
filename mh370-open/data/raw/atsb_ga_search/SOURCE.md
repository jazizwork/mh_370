# atsb_ga_search: area searched by the ATSB-led MH370 underwater search (2014–2017)

Retrieved: 2026-11-05. All downloads were anonymous, with no sign-up. No code from this directory has been run.
Products were built with `scripts/search_fetch_atsb_ga.py` (WMS rasters) and
`scripts/search_build_atsb_polygons.py`. Everything else was fetched by hand with curl.

## Licences
- Geoscience Australia (GA) and AusSeabed data and services: © Commonwealth of Australia
  (Geoscience Australia), **CC BY 4.0**. Source: the eCat records, the WFS feature attributes
  (`LEGAL_CONS`) and the ArcGIS Online item `licenseInfo`.
- ATSB report *The Operational Search for MH370* (AE-2014-054, 3 Oct 2017): © Commonwealth of
  Australia 2017, **CC BY 3.0 Australia**, except for the Coat of Arms, logos and third-party
  graphics. The ATSB asks to be attributed as "Source: Australian Transport Safety Bureau".

## Files

### `polygons_atsb.json` (MAIN DELIVERABLE, derived)
This file holds the best polygons as closed `[lon, lat]` rings (WGS84, exteriors
counter-clockwise). Each entry has the fields name, kind, source, method, est_error_km and notes.
- `kind=searched_area`: envelope of all Phase 2 sonar coverage, with interior gaps filled. It has 349 vertices and 120,608 km² (EPSG:6933).
- `kind=searched_area_coarse`: the same envelope with a 0.01° simplification (232 vertices).
- `kind=sensor_footprint_*`: one per sensor (Go Phoenix SAS, DHJ101 SAS, deep-tow SSS, AUV SSS).
- `kind=atsb_confidence_area_{red,orange,yellow,purple}`: reconstructions of the four areas in ATSB Figure 73, each carrying the ATSB coverage and confidence statistics.
- `kind=data_gap`: 19 interior holes of at least 0.1 km² in the union coverage.
- `kind=searched_area_2014_bluefin21`: the GA polygons of the 2014 Ocean Shield AUV search.
- `kind=context_wide_area_2014`: the June 2014 "Entire Search Area" (±100 NM). It was **not searched**.
- The top-level `summary` field holds all areas and validation numbers.

### `ga_ecat/` (GA eCat ISO-19139 metadata)
URL pattern: `https://ecat.ga.gov.au/geonetwork/srv/api/records/<uuid>/formatters/xml`
| file | record |
|---|---|
| ecat_7c59b965-…xml | *The Search for Flight MH370 – Phase 2 5 m resolution sonar images* (pid ga/120969, doi:10.4225/25/5b0cd3b139def) |
| ecat_11759ecd-…xml | *Phase 2 Raw and Processed Data* (pid ga/120962, doi:10.4225/25/5b0cd2b84a2dc) |
| ecat_19fc382c-…xml | *MH370 Search Phase 1 Raw and Processed datasets* (pid ga/111383) |
| ecat_0bf01609-…xml | *MH370 Phase 1 Optimal Bathymetry datasets (GA-4421, GA-4422 and GA-4430)* (pid ga/82625) |
| ecat_3c500a8b-…xml | *Multimedia products of the bathymetry data from the MH370 Search Area* |

GA-4421, GA-4422 and GA-4430 are GA's survey numbers for the **Phase 1 hull-mounted multibeam
bathymetry** surveys, not for the sonar search:
- GA-4421 is Fugro Equator (EM302, 5 Jun to 22 Dec 2014).
- GA-4422 is Zhu Kezhen (Reson 8150, 3 Jun to 31 Aug 2014).
- GA-4430 is not named in the records read here. By elimination it is probably Fugro Supporter, but this is unconfirmed.

### `agol/` (GA ArcGIS Online story map "The data behind the search for MH370")
- `item_<id>.json`: `https://www.arcgis.com/sharing/rest/content/items/<id>?f=json`
- `itemdata_<id>.json`: `https://www.arcgis.com/sharing/rest/content/items/<id>/data?f=json`
- Cascade story 038a72439bfa4d28b3dde81cc6ff3214, and its web maps 20c43997…, 30ab41af…, 405dadf0…,
  412ab187…, 5fe78110…, 8a3c293b…, c1454ed0… and ea45b31b…. Also feature-layer items a738c2c4…
  (Wide_Search_Area), 05f2dc1e… (Flight_recorder_search_area = Bluefin-21) and 4c94d33c… (The_7th_Arc).
  The owner is `geoscienceaustralia` and the licence is CC BY 4.0.

### `ga_featureservices/` (GA ArcGIS FeatureServer layers saved as GeoJSON)
Base URL: `https://services1.arcgis.com/wfNKYeHsOyaFyPw3/arcgis/rest/services/<name>/FeatureServer/0`.
Each file is a query with `where=1=1&outFields=*&outSR=4326&f=geojson`, and the matching
`*_layer0_info.json` is `?f=json`. `services_index.json` is the org's service list.
- `WideSearchArea.geojson`: the ATSB June 2014 "Entire Search Area", 100 NM either side of the 7th arc. Context only.
- `Bluefin_21_AreaSearched2014.geojson`: the Ocean Shield Artemis (Bluefin-21) AUV area, Apr–May 2014.
- `7thArc_SingleLine.geojson`: the GA/ATSB 7th arc. Its caption says "positioned 40,000 feet above sea level".
- `Search_And_Rescue_Search_Area2014.geojson`: the 2014 surface search area. Context only.
- `MH370_Phase_2_contacts.geojson`, `Contact_Locations.geojson`: sonar contacts and shipwrecks.
- `Generalised_Flight_Path_Probabilities.geojson`: context.

### `ausseabed_wfs/` (AusSeabed GeoServer WFS, `https://warehouse.ausseabed.gov.au/geoserver/ows`)
- `ausseabed_wfs_caps.xml` is the response to `?service=WFS&version=2.0.0&request=GetCapabilities`.
- `<layer>.geojson` is the response to `?service=WFS&version=2.0.0&request=GetFeature&typeNames=ausseabed:<layer>&outputFormat=application/json&srsName=EPSG:4326`.
- `<layer>_describe.xml` is the response to DescribeFeatureType.

The layers:
- `MH370_Phase_2_Sonar_Imagery_Backscatter_Inverse_Deep_Tow__SSS__5m_2018_L0_Coverage`: the
  **detailed vector coverage of the deep-tow side-scan mosaic** (6.6 MB). It is invalid as
  delivered, and `buffer(0)` repairs it. The repaired area is 103,975 km² (EPSG:6933). Its
  attribute `area_km2` is 130,961, which is unexplained and possibly counts overlaps.
- `…GoPhoenix__SAS__…_L0_Coverage` and `…DHJ__SAS__…_L0_Coverage`: **bounding boxes only**.
  Not used as footprints.
- `Southern_Indian_Ocean__MH370__Bathymetry__150m_2017_L0_Coverage` (738,618 km²) and
  `…Backscatter__30m_2017_L0_Coverage` (224,248 km²): Phase 1 bathymetry and backscatter
  coverage. Context only; this is not the searched area.
- There is **no WFS coverage layer for the AUV mosaic.**

### `ausseabed_wms/` (AusSeabed GeoServer WMS GetMap renderings, written by `scripts/search_fetch_atsb_ga.py`)
- The fetch covers lon 85–97° and lat −40.5 to −32.5° at 0.002° per pixel. Each layer is 24
  tiles of 2°×2° at 1000×1000 px. They are transparent PNGs in EPSG:4326.
- Every exact URL is listed in `index.json`.
- Layers: `ausseabed:MH370_Phase_2_Sonar_Imagery_Backscatter_Inverse_Deep_Tow__SSS__5m_2018`,
  `…Inverse_Autonomous_Underwater_Vehicle__SSS__5m_2018`, `…Wide_GoPhoenix__SAS__5m_2018` and
  `…Wide_DHJ__SAS__5m_2018`.
- **Only opaque pixels (alpha = 255) count as data.** GeoServer draws semi-transparent black
  outlines of the granule bounding boxes on the SAS layers.

### `ga_tiles_phase2_sonar/` (GA static tile cache of the combined Phase 2 mosaic)
- URL pattern: `https://mh370-tiles.ausseabed.gov.au/MH370_Phase2_5m_WGS84/L{z}R{row}C{col}.png`.
  These are standard Web-Mercator XYZ tiles, as referenced by GA web map 405dadf0….
- Zoom 5 (2 tiles) and zoom 8 (72 tiles) are kept. Tiles that returned 404 are empty and were deleted.
- These tiles are used only as an independent cross-check.

### `atsb_reports/`
- `operational-search-for-mh370_final_3oct2017.pdf` (41,685,870 bytes, sha256
  `bb6ccea27d83d42caeaea2dfaad9c8b0b8e9e12c7e75c103fbf0e09628509bf3`).
  - It came from the Wayback Machine capture
    `https://web.archive.org/web/20200220230324id_/https://www.atsb.gov.au/media/5773565/operational-search-for-mh370_final_3oct2017.pdf`.
  - The canonical URL `https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf`
    timed out from this machine.
  - **PDF page = printed page + 9.**
- `operational-search-for-mh370_final_3oct2017_pp1-130_firecrawl.md`: a text extraction of PDF
  pages 1–130 made by the Firecrawl PDF parser. Printed page numbers appear as `› N ‹` at the
  **end** of each page.
- `page_images/pNN_pdfMM-MMM.png`: pdftoppm renders at 150 dpi of the pages with Figures 26, 49,
  50, 51, 52, 53, 56, 57, 58, 65 and 73. NN is the printed page and MM the PDF page.

### `derived/` (built by `scripts/search_build_atsb_polygons.py`; not raw data)
- `coverage_union_detailed.geojson`: the union of all four sensors, vectorised from the 0.002° masks, with holes.
- `coverage_by_sensor.geojson`: per-sensor coverage, vectorised.
- `coverage_frac_common_grid.nc`: the fraction of each 0.05° cell on the project common grid
  that is covered, by sensor (`frac_*`), for any sensor (`frac_any`), and for each
  reconstructed ATSB Figure-73 area (`frac_atsb_area_*`).
- `cross_arc_widths.csv`: searched extent NW and SE of the sea-level 7th arc (`mh370.geo`).
- `cross_arc_widths_ga40kft_arc.csv`: the same, measured from the GA/ATSB 40,000 ft arc.
- `summary.json`: areas and validation numbers. `coverage_qa.png`: the QA map.

## Not obtained / notes
- **ATSB weekly "Operational Search Updates" and ATSB KML/KMZ:** not retrieved. www.atsb.gov.au timed
  out, and archive.org rate-limited most requests.
- **ATSB's own sonar-coverage geodatabase:** not public as far as found. It holds the data-holiday
  and LPD polygons (ATSB p. 87).
- **Community KMZ:** a Reddit r/MH370 post "Google Earth KMZ/KML Files For the Search So Far"
  exists, but it returned 403 and was not retrieved. Its provenance is unknown, and the GA data above
  supersede it.
- **marine.ga.gov.au/geoserver:** this older GA marine WMS is defunct and does not resolve.
