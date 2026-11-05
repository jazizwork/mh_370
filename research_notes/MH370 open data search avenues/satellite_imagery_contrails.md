# Satellite imagery and contrail search for MH370 (7–8 March 2014) using free data

Conventions: "[own calc]" marks numbers I computed in this session. The scripts and raw outputs are in the scratchpad: `mh370-open/scripts/wspr/` (geom.py, era5_sac.py, era5_issr_map.py) and `.../scratchpad/cmr/`, `.../scratchpad/eum/`, `.../scratchpad/era5/`, `.../scratchpad/gibs/`. "[inference]" marks my own reasoning. Times are UTC. Takeoff was ~16:42 on 7 Mar, the 7th-arc event was ~00:19 on 8 Mar, and local solar time at ~95°E is about UTC+6h20m.

## Q1. What satellite and imagery analysis has already been done for MH370?

### Takeaway
Official imagery work found floating objects, not the aircraft. Satellite sightings in March 2014 (WorldView-2/AMSA, Gaofen-1, French Pleiades/SPOT, Thaichote, COSMO-SkyMed) produced candidate objects, and none was ever confirmed as MH370 debris. Geoscience Australia's 2017 analysis of four Pleiades-1A images from 23 March 2014 found 12 "probably man-made" objects out of 70, and it could not tie them to aircraft debris. Contrail claims came from independent analysts: Vasquez (Meteosat-7, 2014), Lockerby (MODIS, 2014), Ulich and Prostyakov (Elektro-L and IR, 2015), and Kristensen (arXiv). All are self-published and unconfirmed, and they were disputed on Metabunk. No official body is known to have run a systematic contrail search.

### Cited Findings
**2014 debris-oriented satellite sightings**
- AMSA announced on 20 March that images captured on 16 March showed two objects, the largest about 24 m and another about 5 m, some 2,500 km SW of Perth. Reports attributed the imagery to DigitalGlobe's WorldView-2. — [LiveScience](https://livescience.com/44227-satellite-images-possible-flight-mh370-debris.html); [Yahoo/Malaysia](https://malaysia.news.yahoo.com/satellite-caught-images-objects-indian-ocean-identified-031827445.html)
- Wikipedia's search article lists these sightings, none confirmed as MH370:
  - China's Gaofen-1: "large debris" reported 22 March, about 120 km SW of the earlier sighting.
  - French satellites (Pleiades and SPOT): 122 floating objects reported 26 March.
  - Thai Thaichote: about 300 objects reported 27 March, about 200 km from the French area.
  - On 9 March, a Chinese website showed images of three objects up to 24 × 22 m at 6°42′N 105°38′E (South China Sea). They were not found.
  - Source: [Wikipedia – Search for MH370](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370). Wikipedia is secondary; its underlying footnotes are press reports.
- A June 2014 report said investigators had no satellite image of the plane in flight, and that the first satellite images of the southern Indian Ocean came about a week after the loss. — [Malay Mail, 26 Jun 2014](https://www.malaymail.com/news/malaysia/2014/06/26/mh370-search-hampered-by-lack-of-satellite-images/694915). I saw this only via a search snippet and did not read the full article.
- **COSMO-SkyMed (Italian SAR), 21 March 2014:**
  - What was seen: three floating objects at 34.9519°S 91.6833°E, 34.5742°S 91.8689°E and 34.7469°S 92.1725°E.
  - Provenance: disclosed by an anonymous source to V. Iannello in 2021. The data were "never publicly released".
  - Quality: COSMO "only obtained a wide-angle, low-resolution capture", and a later high-resolution attempt failed.
  - Link to Pleiades: the Pleiades 23 March detections were "only 35 NM" away.
  - Source: [radiantphysics, 23 Jul 2021](https://mh370.radiantphysics.com/2021/07/23/italian-satellite-may-have-detected-mh370-floating-debris)
- **Disasters Charter:** it was activated on 11 March 2014, and Airbus products went to Malaysian and Chinese agencies. These archives might still hold imagery (blog commenter Don Thompson). — [same radiantphysics thread](https://mh370.radiantphysics.com/2021/07/23/italian-satellite-may-have-detected-mh370-floating-debris)

**Geoscience Australia 2017 (Pleiades 1A, 23 March 2014)**
- **Report:** GA Record 2017/13 (eCat 111041), Minchin, Mueller, Lewis, Byrne, Tran, "Summary of imagery analyses for non-natural objects in support of the search for Flight MH370".
- **Imagery:**
  - Four Airbus PLEIADES 1A scenes from 23 March 2014, centred near 35°S 91°E and about 100 km apart.
  - About 0.5 m pan-sharpened resolution, 12-bit.
- **Method:** manual visual interpretation plus PCA, using QGIS and ENVI.
- **Results:**
  - 70 objects were found; 12 were rated "probably man-made".
  - 36 of the 70 objects, and 9 of the 12 "probably man-made" ones, were in the NE image PHR_4.
  - Indicative object areas were 18–179 m².
- **Conclusion:** "a probable cluster of man-made objects in … PHR_4 … but cannot determine whether they are aircraft debris". The authors recommend comparing against control images where no debris is expected.
- Source: [GA report PDF via ATSB](https://www.atsb.gov.au/sites/default/files/media/5773373/mh370_satellite-imagery-geoscienceaust-report.pdf)
- Press counts "28 possibly man-made" — [Maritime Executive](https://maritime-executive.com/article/satellite-data-offers-new-estimate-of-mh370-location). The report tables, as extracted, list about 29 "possible man-made" rows, so treat 28–29 as approximate.
- CSIRO drift modelling released with GA's work found that the 8 March projected locations of the objects in most images were consistent with the First Principles Review area (Nov 2016). — [CSIRO, Aug 2017](https://www.csiro.au/en/news/all/articles/2017/august/satellite-images-add-to-weight-of-evidence-locating-missing-mh370); [ECOS](https://ecos.csiro.au/satellite-images-add-to-weight-of-evidence-locating-missing-mh370/). The ~35.6°S 92.8°E figure in the brief comes from this CSIRO work; I did not re-fetch the exact coordinate.

**Tomnod crowdsourcing (DigitalGlobe)**
- More than 2 million users and more than 645,000 tagged features by 12–13 March 2014, then "largest Tomnod campaign". — [Malay Mail 13 Mar 2014](https://www.malaymail.com/news/malaysia/2014/03/13/satellite-crowdsourcing-adds-2-million-searchers-for-mh370/634203)
- 2.3 million and later about 3 million participants were reported. — [Yahoo](https://my.news.yahoo.com/2-3-million-join-search-missing-mh370-003007408.html); [SCMP](https://amp.scmp.com/news/asia/article/1451444/three-million-people-join-crowdsourcing-satellite-hunt-missing-malaysia)
- Initial imagery was about 3,200 km² (South China Sea and Gulf of Thailand), growing to about 24,000 km². — [CTV](https://www.ctvnews.ca/sci-tech/satellite-firm-turns-to-crowdsourcing-in-search-for-missing-malaysia-plane-1.1723749). I got this from a search summary and did not read the article in full.
- A later retrospective claims 8 million volunteers and 340,000 km². This is an outlier against contemporaneous reports. No evidence of the plane was found. — [GPS World](https://www.gpsworld.com/post-mortem-on-flight-mh370-crowdsource-search/)

**Contrail claims by independent researchers**
- **Tim Vasquez (Weather Graphics), 18–19 Mar 2014:**
  - Imagery: METEOSAT-7 visible, frame 00:30–01:00 UTC 8 March; the feature was likely sensed at about 00:50.
  - The feature: a 39 km line from (−46.197, 87.283) to (−46.495, 87.548), oriented 148.5°T. He read it as a contrail shadow on altostratus or altocumulus.
  - IR check: "does not show any cold anomaly".
  - His conclusion: "inconclusive" and "most likely either a contrail or a spurious artifact".
  - The lead came from PPRuNe.
  - Sources: [weathergraphics.com/malaysia/contrail.shtml](https://www.weathergraphics.com/malaysia/contrail.shtml); press: [The Aviationist](https://theaviationist.com/2014/03/24/meteosat-mh370-contrails/)
- **Patrick Lockerby (Science 2.0), 15 Mar 2014:**
  - Imagery: a MODIS Rapid Response 250 m image, file A2014067043000 (04:30–04:35 UTC 8 Mar). He saw a "faint trace" that "could well be remnants of a single contrail" heading away from the Andamans.
  - No coordinates were given. He wrote: "Expert analysis is needed."
  - Source: [Science 2.0](https://science20.com/the_chatter_box/blog/malaysia_airlines_mh370_a_faint_trace-131788)
  - [inference] The CMR granule list shows Terra's 04:30–04:35 granule covering about 3–24°N, 79–104°E. That suggests the image was Terra, about 6 h after MH370 left the area, which makes attribution implausible.
- **Bobby Ulich with Kirill Prostyakov ("MH370 Addendum 4 – Contrails", April 2015):**
  - Claimed LWIR night contrails of the 18:22–18:40 manoeuvres, including three turns and a climb to about FL390.
  - Claimed a third contrail, a "slightly curved dark line" running SSW from 31°S to 38°S, in five visible images at 00:00–01:00 UTC. The imagery is attributed to Elektro-L.
  - Implied 7th-arc crossing: about 39.6–39.9°S, 84.5–85.0°E.
  - Rebuttal by "Trailspotter":
    - The dark line is likely a natural cloud gap, not a shadow, because its position relative to the cloud did not shift over an hour.
    - Aged contrails drift tens of miles.
    - GFS forecast RH at 250 hPa was about 45% at 18:00, which is unfavourable for persistence.
  - Herman Aven warned of cherry-picking without a blind hit/miss rate.
  - Sources: [Metabunk thread](https://www.metabunk.org/threads/claim-mh370-contrails-have-been-identified.6068/); [PDF attachment](https://metabunk.org/attachments/dr-bobby-ulich-mh370-addendum-4-contrails-pdf.12347)
- **Martin Kristensen, "How to find MH370?":** arXiv 1811.09315, v4 April 2024. A least-squares route fit claims agreement with "contrail" and other evidence for a non-Inmarsat location. It is not peer-reviewed and has no independent verification. — [arXiv](https://arxiv.org/abs/1811.09315)

### Inferences
- [inference] No contrail claim has been reproduced with raw radiances, a blind detection protocol, or a check against other air traffic. All rely on browse-quality images and prior knowledge of the expected track.
- [inference] Vasquez's feature at about 46°S lies well south of all three modern candidate end points (29–36°S). Ulich/Prostyakov's 39.6–39.9°S also lies south of them.
- [inference] Both the Vasquez and Ulich claims depend on dawn-shadow interpretation. At 00:00–00:20 the sun was only about 3–13° high at the candidate points (Q3). A contrail shadow from about 10.7 km would then fall about 50–200 km from the contrail itself (h/tan(elev)), which makes geometric attribution very sensitive.

### Gaps
- I could not retrieve the original ATSB/AMSA 2014 satellite-sighting coordinates or the Gaofen-1 (~44–45°S 90°E) and Thaichote coordinates from a primary source. ATSB pages timed out.
- The Ulich PDF was not read directly; its content above comes via the Metabunk quotes.
- I could not verify whether Elektro-L N1 archive imagery is publicly obtainable.

## Q2. Contrail physics: can ERA5 tell whether contrails would form or persist along candidate paths at FL350 on 7–8 March 2014?

### Takeaway
Yes, ERA5 can screen for contrail formation and persistence, and it is free. My ERA5 check says:
- **Malacca/Andaman segment, about 18:00–19:00:** formation was unlikely at FL340–FL360, because it was too warm and dry. Contrails could form at about FL385 (200 hPa) but would be short-lived (RHi below 60%).
- **7th-arc end points, 23:00–00:00:** formation was possible near the IG and CSIRO points at 250–200 hPa. But RHi was 13–77%, so contrails there would be non-persistent. Near WSPR, the Schmidt–Appleman criterion (SAC) failed at 250 and 225 hPa.
- **ISSR patches:** ice-supersaturated patches existed nearby at about 38–40°S and about 28–30°S near 105°E.

ERA5 has a documented dry bias and weak point-level skill for ISSRs (ETS about 0.2–0.4), so this is indicative, not conclusive.

### Cited Findings
- **Formation (SAC) and persistence:** formation needs the SAC (a mixing-line criterion based on ambient T, humidity, pressure and propulsion efficiency). Persistence needs ambient ice supersaturation (RHi ≥ 100%). The open-source pycontrails library implements "SAC, ISSR & PCC" (persistent contrail regions) and the CoCiP contrail model. It reads ERA5 from the Copernicus CDS (free account and credentials file) or from ARCO-ERA5 on Google Cloud. — [pycontrails API](https://py.contrails.org/api.html); [CoCiP on a flight](https://py.contrails.org/notebooks/run-cocip-on-flight.html); [ARCO-ERA5 notebook](https://py.contrails.org/notebooks/ARCO-ERA5.html)
- **ERA5 humidity can exceed 100% at upper levels.** The IFS allows ice supersaturation; see the ECMWF forum pointing to IFS doc CY41R2 Part IV ch. 7. — [ECMWF forum](https://forum.ecmwf.int/t/relative-humidity-data-exceeds-100/1579)
- **ERA5 RH is relative to ice below 250.16 K (−23°C)**, relative to water above 273.16 K, and mixed in between. This is from an author response in a preprint discussion, not official documentation. — [egusphere-2024-2012 AR2](https://egusphere.copernicus.org/preprints/2024/egusphere-2024-2012/egusphere-2024-2012-AR2.pdf)
- **ERA5 underestimates ISSR occurrence (dry bias) against IAGOS.** ETS is 0.2–0.4, i.e. weak to mediocre skill. Lowering the RHi threshold to 85–95% helps. — [Hildebrandt et al., ACP 2026](https://acp.copernicus.org/articles/26/6449/2026/)
- **ERA5 RHi is nonetheless the strongest available predictor of ISSRs.** Earlier literature likened ISSR forecasts for routing to "tossing a coin". — [Hofer, Gierens & Rohs, ACP 2024](https://acp.copernicus.org/articles/24/7911/2024/)
- **A neural-network correction** reduces ERA5 UT RHi mean absolute error from 15.8% to 5.7%. — per search summary of [Reading/ACP 2025 ML paper](https://centaur.reading.ac.uk/121823)
- **Free ERA5 access without any login:** the ARCO-ERA5 Zarr store at `https://storage.googleapis.com/gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3`. It is hourly, 0.25°, 37 pressure levels, with T, q, u, v, cloud fraction, and cloud ice water. Each variable chunk covers the whole globe for one hour (about 85 MB for T and 104 MB for q, compressed). [own calc: queried `.zmetadata`, downloaded 4 hours]
- **Contrails need not lie on the flight path.** Contrails drift with the wind; at about 100 mph winds the contrail direction deviates about 5°, and an hour-old contrail can be tens of miles from the aircraft. — Trailspotter in the [Metabunk thread](https://www.metabunk.org/threads/claim-mh370-contrails-have-been-identified.6068/)

**[own calc] ERA5 point check (ARCO-ERA5; SAC per the Schumann-1996 approximation with η = 0.31, EI_H2O = 1.23, Q = 43.2 MJ/kg; Murphy–Koop saturation pressures).** Reference flight levels: 250 hPa ≈ FL340, 225 hPa ≈ FL360, 200 hPa ≈ FL385. FL350 ≈ 238 hPa in the ISA.

*Pre-turn and post-turn tropical segment:*
- At 18:00 and 19:00, box 2–9°N, 93–101°E:
  - 250 hPa: T −41 to −43°C; SAC satisfied in 0% of the box.
  - 225 hPa: T −47 to −49°C; SAC 0%.
  - 200 hPa: T −52 to −55°C; SAC 89–92%, but RHi ≥ 100% in only 0–0.3% of the box.
- At the points (5.5°N 99.5°E, 6.3°N 97.8°E, 6.8°N 96.8°E, 6.5°N 95.5°E, 3°N 94°E), RHi was 24–60% at all three levels.
- ERA5 high-cloud cover at those points ranged 0–0.88.
- [own calc] This implies no contrail at about FL340–360. At FL380+ a contrail would be short-lived and non-persistent.

*7th-arc candidates at 00:00 UTC 8 Mar (23:00 values similar):*

| Point | 250 hPa | 225 hPa | 200 hPa |
|---|---|---|---|
| IG 34.23°S 93.78°E | T −50.6°C, RHi 58%, SAC yes | RHi 36%, SAC yes | RHi 14%, SAC yes |
| CSIRO 35.6°S 92.8°E | RHi 77%, SAC yes | RHi 44%, SAC yes | RHi 13%, SAC yes |
| WSPR 29.13°S 99.93°E | T −44.3°C, RHi 45%, SAC **no** | T −49.7°C, RHi 56%, SAC **no** | RHi 43%, SAC yes |

- ERA5 high-cloud cover at 00:00 was 0.00 at IG and CSIRO and 0.09 at WSPR.
- Box 25–40°S, 85–105°E at 00:00:
  - 250 hPa: SAC satisfied in 36% of the box; RHi ≥ 100% in 1.4%; RHi ≥ 90% in 8.5%.
  - 225 hPa: RHi ≥ 100% in 0%.
  - 200 hPa: RHi ≥ 100% in 0%.
- Maximum RHi (250/225/200 hPa) in 2° × 5° cells at 00:00:
  - Near IG (34–36°S, 90–95°E): ≤ 79–95%.
  - About 38–40°S, 85–105°E: up to 100–112% (ISSR).
  - About 28–30°S, 105–110°E: 114%.
  - 42–46°S, 80–90°E: up to 116%.
- Vasquez feature (46.3°S 87.4°E) at 00:00: 250 hPa T −54.0°C, RHi 67% (SAC yes, non-persistent).
- Ulich/Prostyakov's "18:22–18:40 night contrail" region was too warm and dry for SAC at about FL340–FL360. [own calc]

### Inferences
- [inference] Under ERA5 as given, a persistent, satellite-detectable contrail from MH370 was unlikely in both the Malacca/Andaman segment and at the three candidate end points. Short-lived contrails, lasting seconds to minutes and spanning a few km, would not be resolvable by 1–5 km imagers.
- [inference] The dry bias (Hildebrandt 2026) means ISSRs could have existed where ERA5 shows 80–95%. The CSIRO point (77%) and the 36–40°S band are the most plausible places for a persistent contrail. A trajectory reaching the 7th arc at 38–40°S would have crossed ERA5 ISSR.
- [inference] The final segment's altitude is unknown. The SAC answer changes with flight level: WSPR is SAC-negative at FL340–360 and positive at FL385. So any screening must cover FL330–FL410.

### Gaps
- I did not run full pycontrails/CoCiP with wind advection or RHi bias correction, nor model levels (137 levels, better vertical resolution near FL350).
- I did not cross-check with radiosondes (e.g., Cocos Island, 12.2°S 96.8°E) or with AIRS/IASI humidity retrievals.
- I did not verify the exact ECMWF statement on the RH ice/water switch from IFS documentation itself.

## Q3. Which free satellite data covered the region and time, and is night IR (12 − 11 µm BTD) usable before dawn?

### Takeaway
Polar orbiters:
- The best free polar-orbiter coverage of MH370's actual path is a night pass over the Andaman Sea/Malacca/northern Sumatra region at about 18:54–19:15. Suomi-NPP VIIRS (18:54–19:00) and Aqua MODIS (19:05–19:15) both had split-window IR, and the CALIPSO lidar track passed through the same region.
- No MODIS or VIIRS pass covered the 7th-arc zone between about 19:25 and about 03:00. Terra MODIS imaged all three candidate end points at about 03:00–03:07, about 2.7 h after the end.

Geostationary coverage at the end:
- At the end time, 00:00–00:30, the end points were in early daylight (sun 3–13° high). The geostationary options were:
  - Meteosat-7 (57.5°E): 30-min, VIS 2.5 km and one broad IR window, so no split-window BTD.
  - FY-2D (86.5°E) and FY-2E (105°E): VIS 1.25 km and split-window IR at 5 km.
  - INSAT-3D (82°E): VIS 1 km and split-window IR at 4 km.
- View zenith angles at the candidates were about 34–43° for FY-2D/2E and INSAT-3D, versus about 55–57° for Meteosat-7 and 59–68° for MTSAT-2.
- Night split-window BTD works without sunlight, but only on 4–5 km geostationary pixels or the passes above.

### Cited Findings
**Polar orbiters: granule times and footprints from NASA CMR** (no login needed to search; [CMR granule search](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=MYD021KM&temporal=2014-03-07T15:00:00Z,2014-03-08T05:00:00Z&bounding_box=80,-42,108,12&page_size=200)). [own calc: queried MOD021KM, MYD021KM, VNP02MOD, CALIPSO, AVHRR L2P]

*Terra MODIS (night, ascending):*
- 16:00–16:20 on 7 Mar: swath about 54°S–20°N, 83–115°E. This was before the 16:42 takeoff, so it is a reference image.
- 17:40–17:55: about 50°S–6°N, 57–97°E. Its east edge is west of the aircraft's position then (over the peninsula and Malacca at about 17:52).

*S-NPP VIIRS (night):*
- Granule 18:54–19:00: polygon (7.95N, 113.98E), (12.24N, 86.36E), (8.37S, 81.68E), (12.70S, 109.47E). It covers the entire Malacca–Andaman–N. Sumatra region.
- Granules 19:00–19:12 cover 13–54°S, 62–110°E, i.e. the SIO before the aircraft arrived.
- Passes at 20:36–20:48 lie at about 48–88°E, west of the path.

*Aqua MODIS (night, descending):*
- Granule 19:05–19:10: 3.4–24°N, 87–112°E, including Penang and Malacca.
- Granule 19:10–19:15: 14.5°S–6.5°N, 83–108°E.
- The nadir was near 5°N 97.2°E at about 19:10. [own calc from granule polygons]
- Granules 19:15–19:25 cover the 7th-arc zone (aircraft not yet there).
- The 20:45–20:55 pass lies at about 57–86°E, a miss.

*Terra MODIS (day, 8 Mar):*
- 03:00–03:10: 25–46°S, 87–119°E. The west edge is near 91°E at 34°S, so IG, CSIRO and WSPR are all inside, about 2.7 h after fuel exhaustion.
- 04:30–04:50: about 60–96°E. IG and CSIRO are near its east edge.

*CALIPSO (CALIOP lidar) L1 V4-51, night granule 18:49:13–19:35:40:*
- Its ground-track polyline passes 21.43°N 102.72°E → 17.95°S 94.18°E. [own calc]
- Linear interpolation puts the track at about 99.2°E at 5°N at about 19:08–19:10 [inference]. That would cross MH370's Penang→N571 segment (flown about 17:52–18:22) about 50–75 min after the aircraft.
- Downloads need Earthdata Login (free). — [CMR CALIPSO](https://cmr.earthdata.nasa.gov/search/granules.json?short_name=CAL_LID_L1-Standard-V4-51&temporal=2014-03-07T16:00:00Z,2014-03-08T02:00:00Z)

*NOAA-19 AVHRR:*
- The GHRSST NAVO L2P orbit polygon for 18:19–20:14 shows a descending swath edge-to-edge of about 85–112°E near the equator and about 72–106°E at 34°S. [own calc; CMR short_name AVHRR19_G-NAVO-L2P-v1.0]
- [inference] This implies a night pass over the path at roughly 19:30–20:00. NOAA-15/18 pass times were not resolvable from public metadata.
- MetOp-A L2P granules over the region were at 16:28–16:40 (before takeoff). MetOp equator times (09:30/21:30 local) give no pass during 16:42–00:19 at 95°E. [inference]

*Data access:*
- MODIS/VIIRS L1B (MOD021KM/MYD021KM with MOD03/MYD03; VNP02MOD/VNP02IMG with VNP03): LAADS DAAC, free Earthdata Login. — [LAADS](https://ladsweb.modaps.eosdis.nasa.gov/)
- NASA GIBS/Worldview serves browse layers without login:
  - `MODIS_Aqua_Brightness_Temp_Band31_Night` (2002-09-14 to 2022-04-01)
  - `VIIRS_SNPP_Brightness_Temp_BandI5_Night` (interval 2012-03-26 to 2015-04-18 includes the date)
  - `VIIRS_SNPP_DayNightBand` (2012-03-01 onward)
  - `MODIS_Terra_CorrectedReflectance_TrueColor`
  - [own calc: GIBS WMTS capabilities]
  - Source: [Worldview](https://worldview.earthdata.nasa.gov)
  - I fetched the VIIRS I5 night tile for 2014-03-07, 0–10°N 92–102°E, through [GIBS WMS](https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?SERVICE=WMS&REQUEST=GetMap&VERSION=1.3.0&LAYERS=VIIRS_SNPP_Brightness_Temp_BandI5_Night&CRS=EPSG:4326&BBOX=0,92,10,102&WIDTH=1000&HEIGHT=1000&FORMAT=image/png&TIME=2014-03-07). Lake Toba geolocated correctly.

**Geostationary imagers**
- **Meteosat-7 (IODC, about 57.5°E):**
  - MVIRI: VIS 2.5 km and WV/TIR 5 km at nadir, images every 30 min. It moved to the Indian Ocean in 2006 and served until February 2017. — [eoPortal MFG](https://eoportal.org/satellite-missions/meteosat-first-generation); [WMO OSCAR Meteosat-7 IODC](https://space.oscar.wmo.int/satellites/view/meteosat_7_iodc)
  - MVIRI has a single broad thermal IR channel (no 12 µm split), so no classic BTD. [inference from the band set]
  - The "MVIRI Level 1.5 Climate Data Record Release 2 – MFG – 57 degree" (EO:EUM:DAT:0881, 2006-11-01 to 2017-04-04) is in the EUMETSAT Data Store. It is netCDF4, licence "GeneralLicense", and download needs a free EUMETSAT account. — [collection metadata](https://api.eumetsat.int/data/browse/1.0.0/collections/EO%3AEUM%3ADAT%3A0881?format=json)
  - [own calc] A catalogue query for 16:00 7 Mar to 01:55 8 Mar returned 15 products:
    - 16:00, 16:30, 17:00, 17:30, 18:00, 18:30
    - 21:30, 22:00, 22:30, 23:00, 23:30 (ID string oddly dated 20140306), 00:00, 00:30, 01:00, 01:30
    - There is no CDR product for 19:00–21:25 UTC. Whether the raw archive has them is unknown.
- **INSAT-3D (82°E, launched 2013):**
  - Imager: TIR1 10.3–11.3 µm and TIR2 11.5–12.5 µm at 4 km, plus VIS, SWIR, MIR and WV. — [WMO OSCAR INSAT imager](https://space.oscar.wmo.int/instruments/view/imager_insat)
  - Archive at MOSDAC (login and sign-up). I did not verify eligibility or terms. — [MOSDAC](https://www.mosdac.gov.in/node/890)
- **FY-2 series:**
  - FY-2E was at 105°E before 2015-06-03; FY-2D at 86.5°E until end of service on 2015-06-30. — [NSMC FY-2E](https://nsmc.org.cn/nsmc/en/satellite/FY2E.html); [NSMC FY-2D](https://nsmc.org.cn/nsmc/en/satellite/FY2D.html)
  - VISSR-II: 1.25 km VIS and 5 km IR, including 10.8 and 12.0 µm split-window bands. — [NSMC VISSR-II](https://www.nsmc.org.cn/nsmc/en/instrument/VISSR-2.html); [McIDAS guide](https://www.ssec.wisc.edu/mcidas/doc/users_guide/2012.2/app_d-9.html)
  - Near-real-time full-resolution S-VISSR distribution via HRIT/CMACast and the CMA portal. — [WMO OSCAR FY-2E](https://space.oscar.wmo.int/satellites/view/fy_2e)
- **GridSat-B1 (NOAA NCEI CDR):** gridded ISCCP-B1 geostationary IR on a 0.07° grid, 3-hourly, 1980 onward. No registration required; THREDDS subsetting. Too coarse for contrails but useful as cloud context. — [NCEI GridSat-B1](https://www.ncei.noaa.gov/products/gridded-geostationary-brightness-temperature)

**[own calc] Geometry, from PyEphem plus a spherical-earth GEO view-zenith model**

*View zenith angles at the candidates (IG / CSIRO / WSPR):*

| Satellite | IG | CSIRO | WSPR |
|---|---|---|---|
| Meteosat-7 | 55.4° | 55.6° | 57.2° |
| INSAT-3D | 41.7° | 42.9° | 39.3° |
| FY-2D | 40.5° | 41.9° | 37.1° |
| FY-2E | 41.6° | 43.3° | 34.4° |
| MTSAT-2 | 66.8° | 68.2° | 59.4° |

- Over the Andaman Sea (6.8°N 97°E): FY-2E 12.3°, FY-2D 14.7°, INSAT-3D 19.3°, Meteosat-7 46.3°.

*Sun elevation at 00:19:*

| Point | Sun elevation |
|---|---|
| IG | 7.6° |
| CSIRO | 6.8° |
| WSPR | 12.9° |

*Sunrise and civil dawn (sea level):*

| Point | Sunrise | Civil dawn |
|---|---|---|
| IG | 23:38 | 23:13 |
| CSIRO | 23:41 | — |
| WSPR | 23:16 | — |

- At FL350 the sun rises about 14 min earlier, accounting for horizon dip: IG 23:23.
- So the last approximately 40–55 min of flight was in sunlit air.

*Moon:*
- About 42–45% illuminated, but it set by about 17:02 at 6.8°N 97°E and about 16:11 at IG.
- Moon altitude was below −20° for 18:30–00:00 across the path, so the VIIRS Day/Night Band was moonless.

**Night IR usability**
- Thermal BTD detection uses the emissivity difference of small ice crystals between 10.8 and 12.0 µm. It was developed for night and day AVHRR use, with line filtering on the channel-5 BT and BTD images. — [Mannstein et al. 1999 (IJRS 20:1641) via DLR elib](https://elib.dlr.de/32485/1/97-mannA.pdf); search summary of the method
- [inference] Night BTD is usable for MODIS bands 31/32, VIIRS M15/M16, AVHRR ch4/5, and FY-2/INSAT-3D TIR1/2. Meteosat-7 is the exception. Over warm, humid tropical ocean, the clear-sky BTD background is elevated, which reduces contrast.

### Inferences
- [inference] The aircraft's likely location at about 18:54–19:15 (post-FMT, roughly 2–6°N, 93–96°E) and its prior track were inside both the VIIRS and the Aqua MODIS swaths. This is the single best free, high-resolution (375 m–1 km) look at the path. But Q2 suggests no contrail formed there at FL340–360.
- [inference] For the end-of-flight window (23:00–00:30), only geostationary data exist. FY-2D/2E and INSAT-3D are geometrically best and have split windows; Meteosat-7 has an open archive but no BTD and a high view angle. Dawn VIS frames (00:00, 00:30) are usable but low-sun.

### Gaps
- I did not obtain exact NOAA-15/18 AVHRR pass times; NOAA CLASS or the EUMETSAT AVHRR FDR (EO:EUM:DAT:0862, which lists NOAA-15/18/19 GAC orbits for these hours) would resolve them after download.
- I did not confirm the 2014 FY-2D/2E scan schedule (hourly or half-hourly), INSAT-3D cadence and archive availability for March 2014, Elektro-L N1 data access, or the CALIPSO track's exact crossing point with the N571 segment. Those need L1/L2 lat-lon arrays behind Earthdata Login.

## Q4. Contrail detection literature: detectability at about 1–4 km, single-contrail lifetime and spreading, and whether 2014-era imagers could see it

### Takeaway
Modern ML detection is tuned to GOES-16 ABI: 2 km, 10-min, multiple IR bands (OpenContrails). Even there, only about 46% of contrail segments are observable in idealized clear-ocean conditions. Detection comes a median 21 min after formation. Contrails with optical depth below about 0.05 are invisible. Mean satellite-tracked contrail lifetime is about 1 h, and only longer-lived, persistent contrails become detectable. The 2014 Indian Ocean imagers had coarser pixels (4–5 km) and coarser cadence (30–60 min), and Meteosat-7 had no split window. So a single young contrail is unlikely to be detected unless it was persistent and spreading. Polar-orbiter MODIS/VIIRS at 0.375–1 km could see a contrail if one existed at their overpass time.

### Cited Findings
- **Driver, Stettler & Gryspeerdt (AMT 2025), synthetic study:**
  - At 2 km (GOES-ABI-like), only (46 ± 2)% of modelled contrail segments are observable, even with clear sky over homogeneous ocean. These segments carry about 72% of instantaneous LW forcing.
  - About 57% of segments are observable at least once at 2 km and 64% at 0.5 km.
  - Optical depth below about 0.05 is undetectable; detection needs an effective width above about half a pixel.
  - Median time from formation to first detection is 21 min at 2 km (IQR 10–94) and 9 min at 0.5 km.
  - At 7 km, observability is "only modestly lower".
  - With background cirrus (τ ≈ 3), under 2% of segments are detectable.
  - Source: [AMT 18, 1115 (2025)](https://amt.copernicus.org/articles/18/1115/2025/)
- **OpenContrails:** a human-labelled GOES-16 ABI contrail dataset (gs://goes_contrails_dataset) with a temporal-context detection model, Ng et al. 2023. — [arXiv 2304.02122](https://arxiv.org/abs/2304.02122); [Google Research](https://research.google/pubs/contrail-detection-on-goes-16-abi-with-the-opencontrails-dataset/)
- **Gryspeerdt et al. (ERL 2024):** more than 64,000 GOES-16 ABI contrails matched to the aircraft that produced them. Higher-flying, more fuel-efficient aircraft and business jets produce longer-lived, satellite-detectable contrails, primarily because of altitude. — [Gryspeerdt 2024 ERL 19 084059](https://elib.dlr.de/206112/1/Gryspeerdt_2024_Environ._Res._Lett._19_084059.pdf)
- **Vázquez-Navarro, Mannstein & Kox (ACP 2015):** one year of MSG/SEVIRI 5-min rapid-scan tracking (ACTA). Mean contrail lifetime about 1 h, length about 130 km, width about 8 km, optical thickness 0.34, altitude 11.7 km. Initial detection relied on Terra/MODIS resolution. — [ACP 15, 8739](https://acp.copernicus.org/articles/15/8739/2015/)
- **Mannstein et al. (1999):** a fully automated AVHRR IR contrail detection (BTD 10.8–12.0 µm plus 16-direction line filters), later adapted to MSG/SEVIRI. — [DLR elib](https://elib.dlr.de/32485/1/97-mannA.pdf); search-result summaries
- **Metabunk counter-example:** a contrail of about 200 km casting a shadow, from SIA12 at FL390 off California, is visible in MODIS Terra (23 Jun 2014, 18:55). It illustrates that MODIS can show long persistent contrails and their shadows. — [Metabunk](https://www.metabunk.org/threads/claim-mh370-contrails-have-been-identified.6068/)

### Inferences
- [inference] 2014 geostationary (4–5 km IR, 30–60 min) could, at best, detect an MH370 contrail if it persisted and spread for at least about 30–60 min to widths of 2–3 km or more with τ ≳ 0.1. Driver's result that 7 km is only modestly worse than 2 km helps here. Because of cadence, one frame might catch the contrail only after it has drifted and spread.
- [inference] OpenContrails-trained models expect ABI band combinations (e.g., 8.4/10.3/11.2/12.3 µm). FY-2, INSAT-3D and Meteosat-7 lack several of these, so transfer would be poor without retraining. A classical BTD and line-filter approach (Mannstein-style) is the realistic choice for 2014 data.
- [inference] Attribution of a single contrail in a low-traffic region needs:
  - geometric consistency with a time-stamped trajectory plus ERA5 wind advection;
  - exclusion of other flights (no free 2014 ADS-B over the SIO);
  - a false-positive rate measured on control dates.

### Gaps
- I found no published study that quantifies detection efficiency for FY-2/INSAT-3D/Meteosat-7-class imagers or for MODIS/VIIRS night BTD over tropical ocean.
- I found no study quantifying lifetime and spreading for a single B777 contrail in the SIO.

## Q5. Imagery of the "pre-turn" portion (Strait of Malacca/Andaman Sea, about 18:00–19:00, night)

### Takeaway
The pre-turn and early post-turn path has unusually good free night coverage:
- VIIRS at about 18:54–19:00 (375–750 m IR).
- Aqua MODIS at about 19:05–19:15 (1 km, bands 31/32).
- The CALIPSO lidar track at about 19:08–19:10.
- Meteosat-7 30-min frames until 18:30 (CDR gap after that).
- FY-2E and FY-2D (near-nadir) and INSAT-3D split-window.

But ERA5 indicates the SAC was not met at FL340–360 and air was strongly ice-subsaturated (RHi 25–55%), so a contrail is not expected. Ulich/Prostyakov's claimed "18:22–18:40 manoeuvre contrails" are therefore physically doubtful unless the aircraft was at FL385 or above, and even then non-persistent.

### Cited Findings
- **Last radar data:** Malaysian military radar ends with a position at 18:01:49, then a single capture at 18:22:12, about 10 NM past waypoint MEKAR on N571. Analysts cite the ATSB's latest considered turn time as 18:40. — summarised from [Duncan Steel, radar questions](https://duncansteel.com/archives/1987) and [radiantphysics](https://mh370.radiantphysics.com/?p=124) search excerpts; ATSB primary not fetched (timeouts)
- **Malaysian ICAO timeline document:** [ICAO APSARTF/3 Flimsy 1 MH370 Timeline](https://www.icao.int:443/APAC/Meetings/2015%20APSARTF3/Flimsy%201%20MH370%20Timeline.pdf) (not fetched)
- **GFS 250 hPa at 18:00:** forecast winds were under 10 km/h and RH about 45% at the claimed manoeuvre area, which is "unfavourable for long-lived contrails". — Trailspotter, [Metabunk](https://www.metabunk.org/threads/claim-mh370-contrails-have-been-identified.6068/)
- **[own calc] Polar coverage:** VIIRS granule 18:54–19:00 and Aqua MODIS granules 19:05–19:15 cover all of 0–8°N, 93–101°E (polygons in Q3). The CALIPSO 18:49–19:35 night track runs through about 99°E near 5°N.
- **[own calc] ERA5, box 2–9°N 93–101°E, 18:00–19:00:**
  - SAC satisfied in 0% of the box at 250 and 225 hPa.
  - SAC satisfied in 89–92% at 200 hPa, with RHi ≥ 100% in 0–0.3%.
- **[own calc / observation] GIBS VIIRS I5 night browse for 2014-03-07** shows thin cirrus streaks over the Andaman Sea and northern Malacca Strait (about 5–9°N) plus isolated convective cells near Sumatra. No obvious isolated linear contrail is evident in this single-band browse rendering. This is a visual glance, not a BTD analysis or a rigorous search.

### Inferences
- [inference] Any MH370 contrail here would be short-lived. So a null result from MODIS/VIIRS/CALIPSO would be expected and would not constrain altitude much. A positive detection would be surprising and would itself argue for flight at FL380 or above in a moister layer than ERA5 shows.
- [inference] The pre-existing thin cirrus at about 5–9°N complicates any linear-feature search: contrails embedded in cirrus are rarely detectable (Driver 2025: under 2% with background cirrus).

### Gaps
- Exact FMT time and location remain uncertain (about 18:28–18:41), so the aircraft position at the 18:55–19:12 overpasses is known only to roughly ±150 km. [inference]
- I did not analyse full-resolution MODIS/VIIRS L1B BTD fields or CALIPSO profiles; these require free Earthdata Login and downloads of hundreds of MB.

## Q6. Verdict: is a contrail search plausible, and what would a concrete free-data workflow look like?

### Takeaway
A public-data contrail search is technically possible and cheap, but physically low-probability:
- ERA5 shows the Andaman pre-turn segment too warm and dry for contrail formation at typical cruise levels.
- ERA5 shows the candidate end-point regions mostly ice-subsaturated at FL340–FL390 at 23:00–00:00, with ISSR patches nearby at about 38–40°S and about 28–30°S near 105°E.
- 2014 geostationary sensors (4–5 km, 30–60 min) could only catch a persistent, spreading contrail.
- No MODIS/VIIRS pass covered the 7th arc at 22:00–02:00.

It is worth doing only as a pre-registered, blind hypothesis test, focused on:
- (a) trajectories that cross ERA5 ISSRs or near-ISSRs (RHi ≥ 85–90%);
- (b) FY-2D/2E and INSAT-3D split-window plus dawn VIS frames from about 22:30 to 01:00;
- (c) a Terra MODIS check at 03:00 for any surviving contrail-cirrus.

Prior claims (Vasquez, Ulich/Prostyakov) do not survive the ERA5 humidity check well and remain unconfirmed.

### Cited Findings
- Detection limits and timing: [Driver et al. 2025](https://amt.copernicus.org/articles/18/1115/2025/). Lifetimes: [Vázquez-Navarro et al. 2015](https://acp.copernicus.org/articles/15/8739/2015/). ERA5 ISSR skill and bias: [Hildebrandt et al. 2026](https://acp.copernicus.org/articles/26/6449/2026/); [Hofer et al. 2024](https://acp.copernicus.org/articles/24/7911/2024/).
- Tooling: [pycontrails](https://py.contrails.org/api.html) (SAC, ISSR, CoCiP; reads CDS or ARCO-ERA5).
- Data: [EUMETSAT Data Store MVIRI CDR 57°E](https://api.eumetsat.int/data/browse/1.0.0/collections/EO%3AEUM%3ADAT%3A0881?format=json); [LAADS DAAC](https://ladsweb.modaps.eosdis.nasa.gov/); [NSMC FY-2](https://www.nsmc.org.cn/nsmc/en/instrument/VISSR-2.html); [MOSDAC INSAT-3D](https://www.mosdac.gov.in/node/890); [NCEI GridSat-B1](https://www.ncei.noaa.gov/products/gridded-geostationary-brightness-temperature).
- A prior critique applies to any such search: the analyst knew the expected route, risking cherry-picking. Report hit/miss rates on cases where the trajectory is not known in advance. — Herman Aven, [Metabunk](https://www.metabunk.org/threads/claim-mh370-contrails-have-been-identified.6068/)

### Inferences: concrete workflow (all free; registration needs flagged)
1. **Trajectories.** Take time-stamped candidate paths to IG (34.2°S 93.8°E), WSPR (29.1°S 99.9°E), CSIRO (35.6°S 92.8°E), and a 38–40°S variant. Use FL330–FL410 altitude hypotheses and Mach/LRC speed models. The positions at each satellite timestamp (22:30–00:30) are what matter.
2. **Meteorology screen (no login).**
   - Pull ARCO-ERA5 T, q, u, v at 300–175 hPa, hourly 17:00–01:00, from `gs://gcp-public-data-arco-era5` (HTTP, no login). Alternatively use CDS `reanalysis-era5-pressure-levels` (free ECMWF account plus licence acceptance) or model levels via CDS/MARS.
   - Run pycontrails SAC/ISSR and CoCiP along each path, with an RHi bias correction (e.g., test thresholds at 85/90/95%).
   - Output: segments where a persistent contrail is plausible, plus CoCiP-advected contrail positions, widths and τ at each imaging time.
   - Kill criterion: if no segment is plausible, stop.
3. **Imagery pull.**
   - (i) **EUMETSAT Data Store, free account:** Meteosat-7 MVIRI CDR (EO:EUM:DAT:0881), 21:30–01:30 frames. VIS for 23:30–01:00 (dawn and low sun), IR for context.
   - (ii) **NSMC portal, registration:** FY-2E (105°E) and FY-2D (86.5°E) S-VISSR L1, 22:00–01:00, TIR1 and TIR2 plus VIS 1.25 km.
   - (iii) **MOSDAC, registration:** INSAT-3D Imager L1B, 22:00–01:00, TIR1/TIR2 plus VIS 1 km.
   - (iv) **LAADS, Earthdata Login:** MYD021KM/MYD03 granules 2014-03-07 19:05–19:25; VNP02MOD/VNP02IMG/VNP03 granules 18:54–19:12; MOD021KM/MOD03 granules 2014-03-08 03:00–03:10 and 04:40–04:50.
   - (v) **EUMETSAT AVHRR FDR (EO:EUM:DAT:0862) or NOAA CLASS:** NOAA-15/18/19 GAC orbits around 19:00–01:00. Check whether any NOAA-15/18 pass hit 25–40°S around 22:00–00:30.
   - (vi) **ASDC, Earthdata Login:** CALIPSO L1/L2 05kmCLay for the 18:49 night granule (Andaman crossing).
   - (vii) **NCEI GridSat-B1 (no login):** for cloud context.
4. **Detection.**
   - Compute BT11 and BTD (BT11 − BT12) on native geostationary/LEO grids.
   - Apply Mannstein-style 16-direction line filters, or a Hough/Radon search restricted to orientations and positions predicted by CoCiP (±wind-advection uncertainty).
   - For dawn VIS, model shadow offset = (h_contrail − h_cloud)/tan(sun elevation). At 7–13° sun elevation this is about 50–90 km for a 10.7 km contrail over a 0–2 km cloud deck. [own calc]
5. **Blind control and false-positive rate.** Run the identical pipeline on the same region and hours for, e.g., ±10 days, on random synthetic trajectories, and on real known flights in similar regions. Pre-register thresholds before looking at 7–8 March.
6. **Attribution.** Check other traffic. The SIO was "a region with virtually no air traffic" (Vasquez), but Australia–Middle East/Africa routes exist (TWCobra; Gunson disputes N–S routes). Use public 2014 schedules; ADS-B archives for 2014 are not free.
7. **Output.** Any candidate must match trajectory timing, ERA5 winds, an ISSR location and multi-sensor consistency (e.g., FY-2D and FY-2E stereo or parallax from 86.5°E and 105°E) before being taken seriously. [inference: dual-FY-2 parallax could constrain contrail altitude]

### Gaps
- Effort estimate:
  - The ERA5 screen is hours of work, and I already did a 4-hour subset.
  - The geostationary pull depends on NSMC/MOSDAC access, which I did not verify for foreign users or for March 2014.
  - The LEO and CALIPSO pull is moderate effort.
- I found no record that the ATSB, DSTG, IG or Ocean Infinity ever ran a systematic contrail search. Absence of evidence here is not proof none was done (e.g., classified military imagery).
