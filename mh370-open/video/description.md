# YouTube description

Title (suggestion): MH370: could a plane's sound find it? A public-data reanalysis

Paste everything below the line into YouTube, leaving out the two `<!-- chapters -->` marker lines and the note under them (the markers let `scripts/video_render.py` rewrite the timestamps after each full render).

---

In early November 2026, a YouTuber showed that the faint drone of a propeller plane in a video can reveal where the video was filmed. Could the same idea find MH370?

Short answer: no. A cruising Boeing 777 over open ocean, at night, with no microphones underneath it, leaves nothing like that to work with. But the satellite data already contain a radio version of the same Doppler trick. So we rebuilt the whole analysis from scratch, using only data that anyone can download for free: the satellite data, the debris drift, the underwater sound recordings, and a map of every patch of seabed that has already been searched.

This is an independent analysis, not an official one. It does not find MH370. It turns "somewhere on the 7th arc" into a few specific boxes with coordinates, and says honestly how little of the remaining probability any single one holds.

Code, data sources and full reports: [LINK TO CODE]

## Chapters
<!-- chapters:start -->
(timestamps from the voiced render)

0:00 Cold open: can a plane's sound find MH370?
0:45 What happened on 8 March 2014
1:43 The satellite arcs
2:50 Where people have looked
4:22 The debris
5:05 The other leads
6:11 Can you reverse the sound trick?
7:21 What we did differently
8:53 Finding 1: the satellite data points to the high 30s south, but can't settle it alone
10:25 Finding 2: why the drift studies disagreed
11:41 Finding 3: the sound candidates
12:58 Finding 4: WSPR's physics problem
14:18 The uncomfortable part: is the model wrong somewhere?
15:27 Where the probability is now
17:50 How this explains the history
19:00 What could prove us wrong
19:45 Close
<!-- chapters:end -->

## Key findings
- **Satellite data:** our model of the Inmarsat data (validated against the published worked example to about 1 Hz) scores autopilot paths with one fixed setting after the final turn south, and routes through a published waypoint followed by a new course. It puts the end of the flight at a median of 38.2°S along the 7th arc (90% range 36.5–39.5°S), in line with the Australian defence scientists' (DSTG) analysis. The best fits turn south at 02:32–02:40 Malaysian time and cruise at about Mach 0.80.
- **38°S or 34°S?** The satellite data alone cannot settle it. The independent hotspot near 34.2°S, searched in 2025–26, fits as well as our best path, but only if the plane was descending during the 02:40 call attempt; flown level, the frequency recorded during that call is off by 39 Hz. The data cannot tell a descent from level flight; allowing one moves our median to 35.8°S.
- **Debris drift:** drift models built from ocean drifters run about 20% too slow (held-out drifters took 565 days to reach 60°E; the raw model took 696). Corrected, the debris points to about 31–35°S (peak 33.4°S). Using the flaperon's measured leeway moves the flaperon's own answer from about 30°S to about 38°S.
- **Sound:** 4.7 GB of public IMOS recordings plus eight control nights show nothing above chance along the arc. The 2024 hydrophone candidate arrives 11.5–17 minutes too late for an impact on the arc; the 2014 Curtin event looks like a whale call, a mooring knock and an earthquake's T-phase; the "Java" event is a natural magnitude ~4.1 earthquake. One 2014 Cape Leeuwin arrival (near 41°S) fits on timing but cannot be tested with open data.
- **WSPR:** the largest signal change a 777 could plausibly cause is about 0.03 dB, against 1 dB reporting steps and 3.5–5 dB of natural jitter. No direct WSPR link crossed the southern arc after 07:06 Malaysian time that morning. A blind test on modern flights would settle it; the data for that are public.
- **Searched vs unsearched:** 86% of the satellite-data probability lies on seabed that has since been searched, mostly by the 2014–17 search. If the satellite model were right, the chance that every search would have missed the plane is only about 6–17% (6% with the debris drift, 17% without).
- **Is the model wrong somewhere?** We added a deliberately vague alternative (the plane ended anywhere along the arc between 20°S and 42°S), gave it a 1-in-10 starting weight and let the evidence update it: 10% → 17.5% after the debris drift → 46% after the empty searches. Allowing for that, the chance the wreck is in ground never searched is about 58% (42% if the satellite model is right).

## Where the probability is now (blocks of about 7,500 km², one search season each)
No single search-sized area holds more than about 1 chance in 10. The best unsearched areas sit 40–130 km beyond the arc, just outside the width past searches covered.
- **Area 1 — 30.46°S 98.41°E** (29.03–31.85°S, 97.10–99.66°E; 42–62 km beyond the arc): a long strip along the outer edge of the 2018 search. About 8.5% of the remaining probability. Small changes to the assumptions can swap areas 1 and 2.
- **Area 2 — 38.75°S 89.02°E** (38.10–39.39°S, 87.98–90.03°E; 90–130 km beyond the arc): where a piloted glide after fuel exhaustion would end. About 5%. The top unsearched area if the satellite model is right.
- **Area 3 — 32.36°S 96.89°E** (30.98–33.70°S, 95.46–98.24°E; 62–82 km beyond the arc): beside area 1. About 4%.
- **Satellite-only pick — 39.94°S 84.82°E:** on the arc just past the southern end of the 2014–17 search; the top pick if the debris drift is set aside and only the satellite data are trusted.
- **Re-search block — 37.91°S 88.69°E:** inside the 2014–17 search area (about 11%); only worth it if that search was less thorough than reported.

Area 1 lies near the crash site proposed using WSPR (about 27 km away), but not on it; this analysis does not use WSPR. The strip still left in Ocean Infinity's current contract lies on the near side of the arc and gets almost no probability: the plane would have had to turn back after its final message.

## Caveats
- Independent, public-data-only reanalysis; not authoritative and not peer-reviewed.
- How much to doubt the satellite model in the first place is a judgement call. We started at 1 in 10; below about 0.06 the top two areas swap places, and a different form of the "model is wrong" alternative moves the ranking.
- No credible public fuel-burn model exists; fuel is what best separates the scenarios.
- The 2025–26 search footprint has never been published; we reconstructed it from ship-tracking (AIS) data and official totals.
- How thoroughly each past search covered its ground is partly our own estimate.
- The flaperon real-currents check uses an ocean model covering March 2014 – August 2015 only.
- The area percentages already allow for the possibility that the satellite model is wrong, but only through the deliberately vague alternative we chose; they are not absolute probabilities.
- Some visuals are illustrations (marked on screen): the Doppler curve and the sound-footprint diagram.

## Data, credits and licences
- **Inmarsat satellite log** (redacted SU log released 27 May 2014 by Inmarsat and Malaysia's DCA), via Paul Sladen's CSV transcription (github.com/sladen/inmarsat-9m-mro; the conversion is placed in the public domain). ATSB tables transcribed in the same repository.
- **ATSB reports** including *The Operational Search for MH370* (2017) and *MH370 – Definition of Underwater Search Areas* (2014): © Commonwealth of Australia, CC BY 3.0 AU. Source: Australian Transport Safety Bureau.
- **Geoscience Australia / AusSeabed** MH370 Phase 2 sonar coverage (eCat 120969, doi:10.4225/25/5b0cd3b139def) and Bluefin-21 2014 search area: © Commonwealth of Australia (Geoscience Australia), CC BY 4.0.
- **Malaysian Government** search updates: Ministry of Transport weekly "MH370 Operational Search Update" maps (2018) and the MOT/AAIB update to families (8 March 2026). No licence stated; used for research with attribution.
- **Ocean Infinity** public statements (2018, 2026); **CAPTION** (mh370-caption.net) AIS vessel-track files; **Radiant Physics** (V. Iannello) posts. Cited for research; no licence stated.
- **ERA5** winds via Google's public ARCO-ERA5 store: Hersbach et al. (2020). Contains modified Copernicus Climate Change Service information 2026. Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus information or data it contains.
- **NOAA Global Drifter Program**, 6-hourly interpolated data (Lumpkin & Centurioni 2019, doi:10.25921/7ntx-z961). Freely available.
- **NCEP/NCAR Reanalysis 1** daily winds (Kalnay et al. 1996), provided by NOAA PSL, Boulder, Colorado, USA. **HYCOM** GLBv0.08 expt 53.X reanalysis: HYCOM consortium / NRL.
- **IMOS passive acoustic data** (PAPCA, PAKIM, PAPOR) via the AODN, CC BY 4.0. Data was sourced from Australia's Integrated Marine Observing System (IMOS) – IMOS is enabled by the National Collaborative Research Infrastructure strategy (NCRIS). Loggers and processing: Centre for Marine Science and Technology (CMST), Curtin University.
- **Seismic data** via FDSN web services: EarthScope (formerly IRIS DMC; networks II doi:10.7914/SN/II, IU doi:10.7914/SN/IU, AU Geoscience Australia, IN India Meteorological Department), GFZ GEOFON (GE doi:10.14470/TR560404), RESIF/EPOS-France (G GEOSCOPE doi:10.18715/GEOSCOPE.G) and AusPass (S1 doi:10.7914/SN/S1).
- **Earthquake catalogues:** USGS ComCat (US Government, public domain) and the ISC Bulletin (International Seismological Centre).
- **Bathymetry:** NOAA NCEI ETOPO 2022 (public domain). **Coastlines:** Natural Earth (public domain).
- **Magnetic model:** NOAA NCEI WMM2010 (via pygeomag).
- **WSPR spots:** wspr.live (raw wsprnet.org data; free for own research and projects, not for commercial or profit-oriented use; no warranty). Note: if this video is monetised, check the wspr.live terms first.
- **Published work used or compared:** Ashton et al. (2015), *J. Navigation* 68:1–22 (open access, CC BY); Davey et al., *Bayesian Methods in the Search for MH370* (DSTG, Springer 2016, open access, CC BY-NC 4.0; Fig. 10.3 digitised for comparison — non-commercial licence, check before monetising); Kadri (2024), *Scientific Reports* (CC BY 4.0); Griffin, Oke & Jones, CSIRO drift reports (2016–17); Ulich & Iannello (2023); Godfrey (2021, 2024); Miron et al. (2019); Nesterov (2018); Iannello, Ulich, Godfrey & Banks (UGIB, 2020); Malaysia ICAO Annex 13 Safety Investigation Report (2018).
- **Inspiration:** colsto's November 2026 video on aircraft-Doppler audio geolocation.

Code, data sources and full reports: [LINK TO CODE]

If you can show any of this is wrong, please do: open an issue or leave a comment with the evidence.

In memory of the 239 people on board MH370.
