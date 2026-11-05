# MH370: a public-data reanalysis

This is an independent reanalysis of where Malaysia Airlines flight MH370 ended. It uses **only data that
anyone can download for free**: no government data requests and no special access. It began with a question:
could the November 2026 "plane sound reveals your location" trick help find MH370? The answer is no, so the
project rebuilt the evidence that already exists:

- the public Inmarsat satellite log;
- debris drift;
- open underwater recordings;
- a map of every patch of seabed already searched.

It then asked where the remaining probability actually sits.

**This is not an official analysis, and it does not find MH370.** It shows how the probability spreads
once the failed searches are counted as evidence. Every assumption that matters gets a sensitivity run.
If you can show it's wrong, please open an issue.

The research, code and analysis were done with Claude (Anthropic) in Claude Code, directed by the
repository owner.

## Headline results (6 November 2026)

Full details are in [`mh370-open/FINDINGS.md`](mh370-open/FINDINGS.md).

- **Satellite data.** The forward model reproduces the Inmarsat team's published worked example to about 1 Hz.
  - Fitted autopilot paths, including routes via published waypoints, put the end point at a median of **38.2°S** (90%: 36.5–39.5°S).
  - The satellite data alone cannot separate 38°S from the independent researchers' 34.2°S hotspot. That route fits only if the plane was descending at the 18:40 UTC call. Flown level, it misses that reading by 39 Hz.
- **Debris drift.** The model is built from NOAA drifters and corrected for a 20% speed bias found against held-out drifters. Its peak is near **33.4°S**.
  - The north–south split in the published drift studies comes mainly from that speed bias and from how the flaperon's drift is modelled.
- **Underwater sound.** None of the published acoustic candidates holds up on open IMOS and seismometer data.
  - The "Java event" is a natural ~M4.1 earthquake.
- **WSPR amateur-radio tracking.** The largest signal change a 777 can physically cause is about 0.03 dB. WSPR reports in 1 dB steps, and its natural jitter is 3.5–5 dB.
  - A fully public blind test is specified in the reports.
- **Combined.** 86% of the satellite probability lies on seabed that has already been searched.
  - Counting the failed searches as evidence lifts a deliberately vague "model is wrong somewhere" alternative from 1 in 10 to nearly 1 in 2.
  - The best remaining areas lie 40–130 km beyond the 7th arc, on the side the plane was heading. No single 7,500 km² area holds more than about 1 chance in 10.

| Area (≈7,500 km²) | Centre | Share of remaining probability |
|---|---|---|
| 1 | 30.46°S 98.41°E (42–62 km beyond the arc, along the 2018 search edge) | ~8.5% |
| 2 | 38.75°S 89.02°E (90–130 km beyond the arc; glide zone) | ~5% |
| 3 | 32.36°S 96.89°E (62–82 km beyond the arc) | ~4% |
| Satellite-only pick | 39.94°S 84.82°E (on the arc, just south of the 2014–17 search) | top if drift is ignored |

Which of the top two comes first depends on the prior weight given to "model is wrong" (they swap at about
6%). See FINDINGS.md section 5 for what is robust and what is fragile.

## Repository layout

```
README.md                  this file
reports/                   three research reports, with citations:
                           the Doppler audio-geolocation technique, MH370 acoustic feasibility,
                           and the open-data avenues (including the WSPR audit)
research_notes/            source notes behind each report
mh370-open/
  FINDINGS.md              summary of results, start here
  PROJECT.md               shared conventions (grid, time base, output contract)
  src/mh370/               library code: geo, satcom*, drift*, acoustic*, search, combine*, grid
  scripts/                 runnable entry points (satcom_*, drift_*, acoustic_*, search_*, combine_*, make_map,
                           video_*, voiceover, research/)
  outputs/<module>/        README (method, validation, limitations), figures, tables
  outputs/map/             interactive results map (HTML) + static PNG
  data/derived/            the six result layers (NetCDF on a common 0.05° grid) + small tables
  data/raw/<source>/       SOURCE.md provenance notes and small hand-made tables only (raw data not included)
  video/                   YouTube script, voice-over text, visuals, render pipeline, description
```

## Reproduce

Requirements: Python 3.12 on macOS or Linux, roughly 15 GB of disk for raw data, and a few hours of CPU.

```bash
cd mh370-open
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .

# third-party inputs (not redistributed here)
mkdir -p external && cd external
git clone https://github.com/sladen/inmarsat-9m-mro.git sladen_inmarsat-9m-mro     # public-domain Inmarsat log transcription
git clone https://github.com/o-nesterov/MH370Solver.git o-nesterov_MH370Solver     # MIT; used for reference only
cd ..
```

Then follow the "Reproduce" section in each module README, in this order:

1. [`outputs/satcom/README.md`](mh370-open/outputs/satcom/README.md): ERA5 winds (anonymous ARCO-ERA5), then the path model.
2. [`outputs/drift/README.md`](mh370-open/outputs/drift/README.md): NOAA GDP drifters (AWS open data), then the debris likelihood.
3. [`outputs/search/README.md`](mh370-open/outputs/search/README.md): searched-area reconstruction.
4. [`outputs/combine/README.md`](mh370-open/outputs/combine/README.md): `combine_run.py`, then `combine_mix_run.py`.
5. [`outputs/acoustic/README.md`](mh370-open/outputs/acoustic/README.md): independent; IMOS recordings and FDSN seismometers.
6. `scripts/make_map.py` for the map, and `video/README.md` for the video pipeline.

Run every script from `mh370-open/` as `.venv/bin/python -I scripts/<name>.py`.

## Data sources and attribution

Each `data/raw/<source>/SOURCE.md` records the URL, retrieval date and licence. Main sources:

- **Inmarsat log:** Inmarsat/DCA Malaysia SU log (2014), via Paul Sladen's public-domain transcription.
- **Search records and debris:**
  - ATSB reports and Geoscience Australia / AusSeabed MH370 sonar coverage (CC BY 4.0).
  - Government of Malaysia weekly search updates (2018) and Ministry of Transport updates (2025–26).
- **Ocean and weather data:**
  - NOAA Global Drifter Program; HYCOM; NCEP/NCAR Reanalysis.
  - ERA5 (Copernicus Climate Change Service; contains modified Copernicus information).
- **Sound and seismic recordings:**
  - IMOS / AODN passive acoustic data (CC BY 4.0).
  - EarthScope/IRIS, GEOFON and AusPass FDSN waveforms; USGS earthquake catalogue.
- **Maps and radio:**
  - Natural Earth coastlines.
  - wspr.live (WSPR spots; **non-commercial use only**).
- **Comparison curves:** the DSTG book *Bayesian Methods in the Search for MH370* (Davey et al., Springer, 2016; **CC BY-NC 4.0**), digitised for comparison only.

Third-party papers and reports were downloaded for analysis but are not redistributed here.

## Licence

No licence has been chosen yet. Until one is added, the code is all rights reserved by the repository
owner. The data sources above keep their own licences.
