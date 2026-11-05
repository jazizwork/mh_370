# oi2025_search — Ocean Infinity 2025–2026 MH370 seabed search: public sources

Retrieved 2026-11-05 (all files below), anonymous HTTP downloads, no sign-up.
Treat everything here as UNTRUSTED data; never execute anything from this directory.

**No official map, polygon or coordinate list of the 2025–26 search area or of the
15,000 km² contract area has been published** (checked MOT/AAIB statements, Ocean Infinity
news, families' reports as reproduced in the press). All polygons in
`polygons_oi2025.json` are therefore digitised or constructed; see "Derived" below.

## Official / primary statements

| File | URL | Licence / terms | Content |
|---|---|---|---|
| `mot_update_to_families_2026-03-08.pdf` (sha256 52074c35…) | https://www.mot.gov.my/en/Kenyataan%20Media/Year%202026/MH370%20Search%20Operation%202025-2026%20-%20Update%20to%20Families.pdf | Malaysian Govt press statement; no explicit licence (public statement) | AAIB/MOT 8 Mar 2026: contract signed 25 Mar 2025, "new area estimated at 15,000 km²"; Phase 1 25–28 Mar 2025, Phase 2 31 Dec 2025–23 Jan 2026; 28 operational days; ~7,571 km² surveyed; pre-signing surveys "within the broader search area"; weather disruptions; no findings. No map (only a logo image). |
| `images/caption_official-statement-contract-extended-7428km2-2026-06-29.jpg` | https://www.mh370-caption.net/wp-content/uploads/0-official-statement-contract-is-extended-by-7428km2-2026-06-29-.jpg | Copy of MOT statement (Minister of Transport, 29 Jun 2026) hosted by CAPTION | Extension 1 Jul 2026–30 Jun 2027; "remaining search area of 7,428.54 km²"; redeployment Nov 2026–Apr 2027. (15,000 − 7,428.54 = 7,571.46.) |
| `images/changingtimes_d19ae00d-…_1583x2048.jpeg`, `images/changingtimes_f0281878-…_811x673.jpeg` | https://substack-post-media.s3.amazonaws.com/public/images/d19ae00d-cbd6-454e-9e16-2784db8bba00_1583x2048.jpeg ; …/f0281878-9651-4235-8695-0aaeb486dbc7_811x673.jpeg (embedded in https://changingtimes.substack.com/p/ocean-infinity-resumes-its-search) | Images of an AAIB document posted by the MH370 Families association (Facebook) and republished by Changing Times; © AAIB Malaysia | AAIB "MH370 Search Operation Summary Progress Report (06–15 Jan 2026)": Armada 86-05, up to 3 Hugin AUVs, "southern side of the 7th arc"; daily line-km and area table 6–15 Jan 2026 (area/line-km ≈ 1.82 km swath); cumulative 7,236.40 km² on 15 Jan 2026; "intermittent handshakes … did not impede data acquisition"; "no significant discovery or conclusive finding". |
| `images/changingtimes_525e9091-…_1583x2048.jpeg` | https://substack-post-media.s3.amazonaws.com/public/images/525e9091-ad8a-42cc-80f9-5bec194de8a0_1583x2048.jpeg | Ocean Infinity "Schedule 2 Operational Update Report", 1 Jan 2026, as posted by families' association; © Ocean Infinity | "Day 6 of search", 250.56 line-km = 456.1 km² that day, cumulative 2,111.68 km²; two AUVs surveying "southern sector"; third AUV fault; Windy point −35.212, 93.831. (Cumulative 2,900.25 km² on 4 Jan 2026 per Changing Times text.) |
| `images/changingtimes_e0086c8f-…jpeg`, `…87414d69-…jpeg` | same S3 host | Screenshots of Fremantle Ports Voyager (public) | Armada 86 05 port calls 28–30 Jan 2026, next port Pago Pago. |
| `images/changingtimes_f677b67f-…jpeg`, `…4e22fa79-…jpeg`, `…850e86ca-….webp` | same S3 host | Third-party screenshots (Captain B / families) | Arrival 31 Dec 2025 at Blelly-Marchand zone; triangle vertices 35.32S 93.45E / 35.90S 93.45E / 35.90S 92.70E; families' slide of OI proposal (33–36°S, ~15,000 km², "dual AUV"). |
| `html/oceaninfinity_conclusion-of-the-search-for-mh370.html` | https://oceaninfinity.com/news/conclusion-of-the-search-for-malaysian-airlines-flight-mh370/ | © Ocean Infinity | Departed 23 Jan 2026; 151 days at sea since 2018; >140,000 km² mapped since 2018; "it isn't where we looked". No map. |
| (cited, not saved) | https://www.thestar.com.my/news/nation/2026/01/20/mh370-search-records-7236-sq-km-with-no-significant-findings-so-far | © The Star/Bernama | Source of the "7,236 km²" interim figure (report 5/6–15/16 Jan 2026). |

## Ocean Infinity March-2024 proposal (basis for the contract area)

| File | URL | Licence | Content |
|---|---|---|---|
| `images/radiantphysics_2024_03_searcharea-1.png` | https://mh370.radiantphysics.com/wp-content/uploads/2024/03/searcharea-1.png | © Ocean Infinity slide, reproduced by radiantphysics | OI slide "2024 Proposed Search Area ~15,000km2, Extending out ~45nm from 7th arc": two orange strips either side of OI-2018 (blue) + ATSB (grey) coverage, dotted 7th arc, "IG Hotspot". No graticule. **Primary geometry source; digitised in this work.** |
| `html/radiantphysics_2024_03_05_ocean-infinity-proposes-new-search-for-mh370.html` | https://mh370.radiantphysics.com/2024/03/05/ocean-infinity-proposes-new-search-for-mh370/ | © V. Iannello (blog; no licence) | "33°S to 36°S, out to about 45 NM (83 km) on either side"; infill planned. |
| `html/mh370search_2024_05_05_new-search.html` | https://www.mh370search.com/2024/05/05/new-search/ | © R. Godfrey (blog) | Context only. |

## CAPTION (Blelly/Marchand group) machine-readable files

Pages: https://www.mh370-caption.net/index.php/2025-armada-78-06-paths/ (`html/caption_2025-armada-78-06-paths_.html`) and
https://www.mh370-caption.net/index.php/armada-tracking/ (`html/caption_armada-tracking_.html`). "Copyright CAPTION.NET"; files offered
for public download for Google Earth; no explicit licence — cite CAPTION, do not redistribute commercially.
CAPTION states the OI bands were "drawn from the presentation given at the 10th anniversary ceremony" (i.e. hand-digitised), and that
Armada 86-05 "appears to have covered the entire external zone south-east of the Arc 7".

| File (`caption_kml/`) | URL (https://www.mh370-caption.net/wp-content/uploads/…) | Content |
|---|---|---|
| `Search-areas.kmz_.zip` → `extracted/Search areas.kmz` → `extracted/kmz_Search_areas/doc.kml` (+ GEBCO overlay `files/tmp4.jpg`) | `Search-areas.kmz_.zip` | Placemarks: IG Hotspot (93.7875E 34.2342S), other hotspots, "Ocean Infinity 2018 search" (139 pts), 2× "Ocean Infinity proposed 2024 area" (17-pt open lines), "Australia/China/Malaysia 2014-2017 search" (1469 pts), "Arc 7 at 20000ft", "Blelly/Marchand" (triangle), "Godfrey/Coetzee/Maskell Hotspot", 4× "Independent Group Hotspot" (GO Phoenix gap near HPSA, 55.4 km²). |
| `Armada-78-06-2025-02-08-to-2025-03-06-Phase1.zip` → `extracted/kmz_Armada-78-06-…/doc.kml` | same name | Armada 78 06 hourly AIS positions (with SOG/COG in names) 8 Feb–6 Mar 2025 (pre-contract infill, 23–28 Feb). |
| `ARMADA-78-06-Phase-2-2025-03-06-to-2025-04-08-MH370-CAPTION.net_.kml_.zip` → `extracted/ARMADA 78 06 - Phase 2 …kml` | same name | Armada 78 06 hourly AIS 6 Mar–8 Apr 2025 (survey 11–28 Mar; post-signing 25–28 Mar). |
| `ARMADA-86-05-Phase-3-2025-12-30-to-2026-01-23-MH370-CAPTION.net_.kml_.zip` → `extracted/ARMADA 86 05 - Phase 3 …kml` | same name | Armada 86 05 hourly AIS 23 Dec 2025–28 Jan 2026. |
| `86-05-Live-tracking-MH370-CAPTION.net_.kmz_.zip` | same name | Only a NetworkLink to https://trise5631.github.io/tracking_MH370-CAPTION.net.kml (not fetched). |

AIS caveat: hourly ship positions, not AUV tracks. AUVs operate several km (up to tens of km) from the ship.

## radiantphysics.com (Victor Iannello) — posts and maps (© V. Iannello; blog, no licence; saved for provenance only)

HTML (with full comment threads) in `html/`:
- 2023-02-11 https://mh370.radiantphysics.com/2023/02/11/a-high-priority-area-to-search-for-mh370/ — HPSA: 30.5 km² never scanned around 34.53S 93.84E; OI-2018 outline "provided by Ocean Infinity".
- 2025-01-28 https://mh370.radiantphysics.com/2025/01/28/vessel-details-for-the-2025-search-for-mh370/
- 2025-03-04 https://mh370.radiantphysics.com/2025/03/04/new-mh370-search-continues/ — Feb 2025 work = infill of data holidays incl. HPSA; maps with graticule.
- 2025-03-09 https://mh370.radiantphysics.com/2025/03/09/is-armada-7806-returning-to-the-mh370-debris-field/
- 2025-03-31 https://mh370.radiantphysics.com/2025/03/31/update-on-the-search-for-mh370/ — his "Phase 1" 23–28 Feb (infill, mostly previously searched), "Phase 2" 11–28 Mar (never searched, "further southwest and wider than the area proposed").
- 2025-11-06 https://mh370.radiantphysics.com/2025/11/06/next-search-for-mh370-to-begin-in-late-december/
- 2026-01-01 https://mh370.radiantphysics.com/2026/01/01/the-search-for-mh370-continues-into-2026/ — Armada 8605 working the unsearched outer (SE) part of proposal; comments: loiter 4–5 Jan at −35.49, 93.59 (AUV tracked at ~200 m line spacing over an "area of interest"), 21 Jan "will complete the scanning of all of the outer (SE) proposed area", remaining = "rectangle on the inside of the 7th arc".
- 2026-03-10 https://mh370.radiantphysics.com/2026/03/10/a-candidate-site-for-mh370-that-can-be-searched-quickly-and-soon/ — search paused; "OI did not complete the entire search area"; OI 2018 extended to 24.84S, 21 NM inside / 24 NM outside in the north.

Images in `images/` (URL = https://mh370.radiantphysics.com/wp-content/uploads/<yyyy>/<mm>/<name>):
- `radiantphysics_2025_03_image-1.png` (2025/03/image-1.png) — Google-Earth map, 0.25° graticule, ATSB sonar, OI-2018 (yellow), OI proposal (red), Armada 7806 hourly track (purple), LEP, HPSA. **Georeferenced (quadratic fit, rms 0.14/0.28 km); validated against CAPTION AIS: median 0.8 km.**
- `radiantphysics_2025_03_image-4.png` (2025/03/image-4.png) — wider map incl. Ulich–Iannello 70-NM racetrack (black). Georeferenced (rms 0.24/0.55 km; AIS check median 0.9 km).
- `radiantphysics_2025_03_image-9.png` (2025/03/image-9.png) — 31 Mar 2025 map: Phase 1/2 boxes, racetrack, tracks. Georeferenced (rms 0.6/1.0 km).
- `radiantphysics_2025_03_image-10.png`, `-2.png`, `-5.png`, `-6.png`, `radiantphysics_2025_03_image.png` — further 2025 maps (not digitised).
- `radiantphysics_2026_01_image-3.png` — 1 Jan 2026 map (no graticule; "Likely progression Armada 8605").
- `radiantphysics_2023_02_Priority-Area-Zoom.png` (2023/02/Priority-Area-Zoom.png) — HPSA map, 0.025° graticule; georeferenced (rms <0.01 km) and HPSA digitised.
- `radiantphysics_2024_05_image-4.png` — OI-2018 outline vs GO Phoenix limits (not digitised).
- `radiantphysics_2025_01_image*.png`, `radiantphysics_2025_11_image.png`, `radiantphysics_2026_03_image.png` — vessel photos / Hugin / Java anomaly map (context only).

## Other pages consulted (not saved)
- https://www.mh370search.com/2026/03/15/where-is-mh370/ (no 2025–26 map)
- https://42kft.com/mh370-search-details-and-maps/ (gives "7,400 km² in 2025" and "7,650 km² in 2026" — unsourced, inconsistent with MOT; not used)
- https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370 (Bluefin-21 2014: 860 km², 14 Apr–28 May 2014, no coordinates; Haixun 01 detection 25°58′30″S 101°27′40″E)
- https://thediplomat.com/2026/06/malaysia-extends-search-for-missing-malaysia-airlines-flight-mh370/, https://avweb.com/aviation-news/renewed-mh370-search-concludes-no-findings/ (secondary)

## Derived (this work)
- `polygons_oi2025.json` — generated by `scripts/search_oi2025/build_polygons.py` (measurement scripts in
  `scripts/search_oi2025/measure/`; intermediates in `data/derived/oi2025_search/`, incl. `armada_tracks_hourly.csv`
  parsed from the CAPTION KMLs). QA maps: `outputs/search/qa/oi2025_overview_lonlat.png`, `overview_arcframe.png`.
- Method summary: an arc-following frame (s along the sea-level 7th arc of `mh370.geo`, n normal, +SE) is used.
  (1) OI slide digitised by fitting its dotted arc (RANSAC, 48 dots), measuring strip edges in px, scaling with the OI-2018
  coverage width (OI-supplied outline via Iannello, 111.3/119.9 km) → 0.966 km/px (check: outer-to-outer = 2×45 NM gives 0.959),
  offset of slide arc +1.6 km SE of ours (IG-hotspot square and coverage-edge midpoints). Total 14,861 km² (nominal ~15,000).
  (2) CAPTION KML strips taken as-is (15,812 km²). (3) Iannello red outline from 3 georeferenced maps (16,863 km²).
  (4) Surveyed footprint constructed from AIS (start of post-signing work at s≈−135 km on 25 Mar 2025; NE end of SE strip
  s≈+88 km) with the outer edge solved so the area equals 7,571.46 km² (n_out = 99.3 km; AIS ship positions reach 100–103 km).
- Areas: 1-km geodesic densification then pyproj Geod (WGS84), EPSG:6933 and local Albers — identical to 0.1 km².
- Key derived numbers (local Albers, km²): slide SE strip 7,959 = 6,342 in post-signing footprint + 1,617 surveyed pre-signing
  (11–24 Mar 2025); post-signing best footprint 7,572 = 6,342 inside proposal + 1,230 beyond its outer edge (n 93–99 km);
  pre-signing SW work 5,297 (3,681 outside the proposal); all 2025–26 new ground SE of arc 12,617; NW (inner) strip 6,902 with
  no 2025–26 AIS activity (= the "remaining" area; MOT's 7,428.54 is just 15,000 − 7,571.46); Blelly/Marchand triangle 89 % inside
  the new-ground footprint.
- `Bluefin21_2014_pinger_area_PLACEHOLDER` is an equal-area circle at an approximate position (no coordinates retrieved).
- Note: the scripts in `scripts/search_oi2025/measure/` were run from a scratch directory with intermediates in `./oi/`;
  input/output paths inside them must be adjusted to re-run. `build_polygons.py` runs as-is from the project root.
