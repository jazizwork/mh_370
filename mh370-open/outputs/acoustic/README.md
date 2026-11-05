# Workstream D — open acoustic evidence for an MH370 impact on/near the 7th arc

Independent, public-data-only test. Not authoritative. All times UTC on 8 March 2014 unless stated.
Data: IMOS passive-acoustic recorders (AODN, CC BY 4.0), open FDSN seismometers, USGS/ISC
catalogues, ETOPO 2022 bathymetry, and **published** HA01 picks only (CTBTO HA01/HA08 waveforms
are not public and were not used).

## Bottom line

**No candidate acoustic event is both consistent with an MH370 impact on the 7th arc and
supported by open data. No likelihood layer is justified, so `data/derived/acoustic_loglik.nc` was
not written** (see "Why no likelihood layer"). `arc_profile.csv` carries `loglik = 0`, meaning
"no information".

| # | Candidate | Key numbers | Verdict |
|---|---|---|---|
| 1 | **Kadri 2024: HA01 00:54:30, 306.18°** | The bearing crosses the 7th arc 1,591 km from HA01 at 25.73°S 101.37°E (Kadri: 1,586 km). An on-arc impact at 00:19:30–00:25 would reach HA01 at 00:37:17–00:43:02, so the pick is **11.5–17.2 min late**; the implied on-arc origin is 00:36:34 (+17.1 min, reproducing Kadri's +17.10). **PAPCA recorded the whole predicted window** (source at the arc crossing: 00:53:12–00:53:33; source anywhere on the ray at 500–6,000 km: 00:52:52–00:54:33). It shows only a continuous 10.6–10.9 Hz tonal (00:50–00:54:40); arrival-like p = 0.18–0.59; no arrival above **0.21 Pa** (5–20 Hz band RMS, 95% detection level). PAKIM (01:02:54–01:03:21, recorded) and the open seismometers also show nothing. | **Inconsistent** with an on-arc impact (timing). The open data do not corroborate it. |
| 2 | **Stead 2014: HA01 ~00:52:02, 246.9°** | Arc crossing at 2,924 km, 40.97°S 81.57°E. Bearing ±2° moves it to 40.0–42.0°S. Implied on-arc origin 00:18:52–00:19:19 for c = 1.47–1.49 km/s, or 00:15:39–00:21:41 over ±2°, so the timing is consistent. PAPCA 00:54:19–00:54:41 (recorded): nothing, p = 0.63–0.86, upper limit 0.21 Pa. PAPOR 01:15:18–01:15:58 (recorded): nothing, p = 0.18–0.27, upper limit 0.17 Pa. AIS seismometer: p = 0.91. | **Untestable with open data.** Timing-consistent, but not corroborated, and the non-detections are expected whether or not an impact happened. |
| 3 | **Kadri 2024 Table 1 (19 HA01 picks from 00:36)** | Our Δt reproduces Kadri's to ≤0.3 min for 16 picks. 00:42:02/253.66° has a likely sign typo (ours −4.03, printed +3.93); for 00:39:02/268.24° we get −1.0 min where Kadri prints 0; 234.67° does not cross the arc. 5 picks imply an origin 1.0–4.4 min before the 00:19:29 log-on and 13 imply one 3.3–17.1 min after it. The only Δt≈0 pick (00:39:02, 268.24°, crossing 33.77°S 94.31°E) needs an origin 1.0 min before the log-on at 1.48 km/s, and its predicted PAPCA arrival (00:40:23) falls 15 s after the PAPCA recording ended. Of 21 recorded PAPCA windows, min p = 0.18. | **No pick corroborated.** Most are untestable. |
| 4 | **Curtin event: HA01 01:34:40, 301.6°; "Scott Reef" 01:32:49** | PAKIM (the IMOS Kimberley recorder) shows three features. **F1**, a whale-like 20–60 Hz burst at 01:32:56.5. **F2**, an impulsive broadband "knock" at 01:33:04.5. **F3**, an emergent 3–30 Hz T-phase reaching +15 dB at 01:33:39.0, with its energy centroid at 01:34:22.3. The Carlsberg-Ridge source predicts PAKIM at 01:32:42–01:32:44, and nothing T-phase-like is there. F3 fits the **Java 01:15 earthquake's T-phase** (predicted 01:33:39–01:34:22). Combining bearing and time difference with *any* PAKIM feature puts the source 4,500–6,500 km from HA01, **2,900–4,600 km from the 7th arc**. | **Inconsistent** with MH370 whichever feature is associated. PAKIM does not independently confirm a Carlsberg-origin arrival. |
| 5 | **Anderson: 01:15:18 at 8.36°S 107.92°E** | Open seismic data show a **real, uncatalogued M≈4.1±0.2 earthquake**: 8.12–8.30°S 107.82–107.92°E, origin 01:15:19–24, energy ~9×10¹⁰ J, about 20× the aircraft's kinetic energy, with earthquake-like S/P. It came 56 min after the 7th arc. Its T-phase appears at PAKIM (F3) at the predicted time. | **Inconsistent** with MH370: a natural earthquake. |
| — | Generic 7th-arc impact (20–42°S at 0.5°, impact 00:19:30–00:25) | 135 IMOS windows, 108 partly recorded: 1 at p<0.05 (≈5 expected by chance). 270 seismic windows: 0 unexplained. IMOS has **no recorded open-path coverage at 33.0–35.5°S**. | **Untestable** / no detection. No information on impact latitude. |

### Corrections to the background brief and notes
- The "table of 19 HA01 picks from 00:36" is **Kadri (2024) Table 1**, not Stead's.
- The +6 to +8 dB "excess at PAPCA 00:53:11–00:53:25" is a **continuous narrowband 10.6–10.9 Hz tonal** lasting more than 4 min. It is not an arrival. It happens to peak near the Kadri-306° prediction.
- The Java event is M≈4.1±0.2 (7-station amplitude ratio against the USGS M4.1 at 23:52), not ~4.3.
- The Kimberley "transient ~01:32:56–01:33:06" contains two short local or biological transients and a later T-phase. The T-phase matches the Java event; the transients do not match it.

---

## 1. Data (all anonymous HTTPS; provenance in each `data/raw/<source>/SOURCE.md`)
| Source | What | Where |
|---|---|---|
| IMOS/AODN S3 `imos-data` | Raw CMST `.DAT` files for PAPCA 3376, PAKIM 3250 and PAPOR 3274. Main night (7 Mar 21:40 → 8 Mar 03:05) plus 8 control nights (D = 1, 3, 5, 6, 9, 10, 11, 13 Mar, same hours, chosen a priori), 594 files. Also ~660 single files for catalogued-earthquake windows, the AODN MATLAB reader, calibration curves, start-time tables, metadata and CMST long-term spectrograms. ~4.7 GB, sha256 manifest. | `data/raw/imos_acoustic/` |
| FDSN (EarthScope, GEOFON, RESIF, AusPass) | 17 stations, 7 Mar 20:00 → 8 Mar 03:00, with responses; 3 control nights; 216 calibration windows. ~170 MB. | `data/raw/fdsn_seismic/` (step 4, see `seismic/SEISMIC.md`) |
| USGS ComCat / ISC | Catalogues for the night and for Nov 2013 – Nov 2014 (calibration). | `data/raw/usgs_catalog_acoustic/`, `data/raw/fdsn_seismic/` |
| NOAA ETOPO 2022 (60″) | Bathymetry subset 55°S–12°N, 50–150°E, decimated to 2′ via OPeNDAP. | `data/raw/etopo2022_subset/` |
| Kadri 2024 (Europe PMC, CC BY) | Full text, for Table 1 and the R7/c/Δt statements. | `data/raw/literature/` |

Recording windows on 8 March are UTC first-sample times from the file footers; each lasts 307.2 s:
- PAPCA: 00:05:02.6, 00:20:01.6, 00:35:01.4, **00:50:01.9**, 01:05:02.5, 01:20:00.8, 01:35:20.5, 01:50:01.5.
- PAKIM: 00:00:08.7, 00:15:00.9, 00:30:01.1, 00:45:00.6, 01:00:01.4, 01:15:00.9, **01:30:00.0**, 01:45:00.9.
- PAPOR: 00:00:01.8, 00:15:01.0, … every 15 min, including **01:15:01.8**.

Each recorder covers only about 34% of the time.

No extra Python packages were installed: the existing venv's obspy 1.5.1, scipy, pyproj and xarray were sufficient.

## 2. Reader port and validation (`src/mh370/acoustic.py::read_dat`, `scripts/acoustic_reader_validation.py`)
The AODN reader `NL_load_logger_data_new.m` (A. Gavrilov, CMST) was read and ported; it was not executed. The file format is:
- 5 ASCII header lines (LF-terminated), then big-endian `uint16` samples;
- the number of active channels comes from characters 13 and 18 of the two "Filter" lines;
- `volts = counts·5/65536 − mean`; the file is flagged as overloaded if any count exceeds 6×10⁴;
- the UTC of the first sample is in the footer `First Data-YYYY/MM/DD HH:MM:SS - FFFFF`, where FFFFF is in units of 1/65536 s.

Calibration divides the spectrum by 10^(cal_dB/20). The cal_dB values come from `t<dep>_calibration.csv`, the "PSD in dB re ADC unit/µPa", tabulated at 1 Hz.

Validation on all 594 night files:
- **Calibration matches CMST's own processing.** Our calibrated mean PSD minus CMST's independently computed `t<dep>_longterm_spectrogram.mat` over 8–100 Hz:
  - PAPCA: **median +0.03 dB** (IQR −0.16…+0.25);
  - PAKIM: **−0.03 dB** (IQR −0.63…+0.55).

  See `fig_reader_psd_vs_cmst.png`.
- **Timing (internal):**
  - The footer first-sample time minus the hex file-name Unix time is +15.7…+17.1 s (median 16.4 s).
  - Footer minus CMST's `start_times.mat` is 0.02–1.01 s (that table is in whole seconds), so the data producer uses the same clock.
  - Cadence is 900 ± 3 s.
  - "Finalised" minus "First Data" is 307.24–307.45 s.
- **Timing (absolute):**
  - AODN deployment metadata are exactly +8 h (WA) or +10 h (VIC) from the file times, so the metadata are in local standard time and the logger clock is UTC.
  - **Physical check:** open-path T-phases from 14 catalogued oceanic earthquakes peak −12…+30 s from d/1.48 km/s (PAPCA mean −1 s). This rules out gross clock errors and supports c ≈ 1.48 km/s.
  - A deep-event P-wave stack at PAKIM/PAPCA (64 events) was **inconclusive**: a step at +14.5 s, p = 0.03, 5–95% range −30…+21 s. The analog high-pass at 8 Hz removes most P energy, and P was detected in 0 of 118 catalogue P windows.
  - So absolute timing is physically verified only to about ±15 s. Sub-15-s claims, such as Curtin's 01:32:49 versus our F1/F2, cannot be settled physically.
- **Samples:**
  - 1,800,000 nominal samples plus 41,952–42,257 extra samples (~7 s) before the footer. These are continuous across the 300-s boundary (RMS ratio median 1.00), so we use all ~307 s.
  - 3 of 594 files carry the overload flag, all on control nights at PAKIM.
- **Noise floor (median 2-s band level, 22:00–03:00, 8 Mar / controls), dB re 1 µPa:**

  | Site | 8–16 Hz | 10–20 Hz | 20–40 Hz |
  |---|---|---|---|
  | PAPCA | 92.2 / 91.5 | 92.9 / 93.2 | 93.2 / 94.4 |
  | PAKIM | 85.2 / 91.6 | 85.7 / 90.0 | 94.9 / 94.3 |
  | PAPOR | 96.6 / 98.9 | 96.2 / 98.3 | 95.0 / 96.7 |

  PAPCA is dominated by whale chorus at 20–70 Hz. PAKIM has whale song at 20–40 Hz and frequent mechanical knocks. See `noise_floor.csv` and `fig_noise_floor.png`.
- Water depth from ETOPO: PAPCA 436 m (metadata 390 m), PAKIM 223 m (metadata missing), PAPOR 151 m. All three are shelf or slope sites; HA01 is near the SOFAR axis at about 1,055 m.

## 3. Predictions (`scripts/acoustic_predictions.py`)
- **7th arc:** `geo.arc_lon_for_lat` at sea level (BTO 18,400 µs at 00:19:29.416).
- **Receivers:** HA01 is the centroid of H01W1–3 (FDSN metadata). IMOS positions come from the AODN metadata.
- **Travel time:** WGS84 geodesic distance / c, with c = 1.48 km/s nominal, ±0.01 as the sensitivity range, and ±10 s padding. This is a pure-water path; no ocean model was run.
- **HA01 picks:** for each pick we compute:
  - the arc crossing along the bearing;
  - the origin time implied if the source were on the arc;
  - Δt after 00:19:29;
  - the IMOS arrival window, both for a source at the crossing and for a source anywhere on the ray at 500–6,000 km. In both cases the origin is tied to the HA01 pick through the time difference (TDOA).
- **Blockage:** shallowest point on the geodesic (ETOPO), excluding the first 30 km at the source and the last 60 km at the receiver. A path counts as "open" if it stays deeper than 1,000 m.

| Arc band | PAPCA | PAKIM | PAPOR |
|---|---|---|---|
| 20–32.5°S | 00:35 window, coverage 0.08–0.68; open | 20–29°S covered (00:45 window); path over the NW shelf at −480 to −290 m | covered ≤0.19; **path over SW Australia (land)** |
| **33.0–35.5°S** | **not recorded** (falls in the 00:40–00:50 gap) | covered 0.34–0.80; **path over shelf or land (−38 to −1 m)** | not recorded |
| 36–41°S | 00:50 window, coverage 0.06–0.82; open | partly; **path over land** | coverage 0.04–0.78; open |

Full detail is in `pred_arc_grid.csv`, `arc_profile.csv` and `fig_arc_timing.png`. Latitudes 33.0–35.5°S, which include the IG/UGIB point at 34.23°S, therefore have **no usable IMOS coverage at all**. Located sources are in `pred_sources.csv`; path profiles in `fig_blockage_profiles.png`; the map is `fig_map_candidates.png`.

## 4. What can the IMOS recorders hear? (`scripts/acoustic_imos_calibration.py`)
**Method.**
- We selected USGS events from Nov 2013 to Nov 2014 whose T window [t0+d/1.50−15 s, t0+d/1.46+30 s] fell inside a recording. Criteria: M≥4.0, depth ≤70 km, d ≤4,000 km, or ≤3,000 km for PAPOR.
- That gave 494 T windows, plus 118 P windows. We fetched each file.
- **Detection** means one of two "arrival-like" statistics has p<0.01 against control nights:
  - 5–40 Hz: an 8-s running median of 2-s band levels, as excess over the file median;
  - 5–20 Hz: the same statistic, in a window extended by 30 s.

| Site | Open-path T windows detected | Blocked-path T windows detected |
|---|---|---|
| PAPCA | **5/9**: M4.3–4.7 oceanic/ridge events at 860–3,400 km (SE Indian Ridge, Mid-Indian Ridge, west of Australia), **+21…+33 dB**, received 0.8–3.5 Pa | 0/135 |
| PAPOR | **9/11**: M4.0–5.0 Indian–Antarctic Ridge, SE Indian Ridge and Macquarie events at 1,600–2,930 km, +16…+31 dB | 2/11 |
| PAKIM | — (no open path: every path ends on the shelf) | 0/328, i.e. 10 at p<0.05 against 16 expected by chance |

**Caveat on PAKIM.** Visual inspection shows that PAKIM *does* record T-phases from earthquakes south of Java. Examples: M4.6 at 1,879 km, M4.5 at 1,801 km, M4.5 at 970 km, appearing as emergent 5–20 Hz arrivals 0 to +45 s after d/1.48. But they reach only about +14 dB, and PAKIM's control nights contain such low-frequency excursions about 3.5 times per hour. **PAKIM detections are therefore not statistically separable from its noise.** A first-pass 5–40 Hz-only statistic missed these T-phases; it was replaced, and both are reported.

Figures: `fig_imos_detectability.png`, `fig_imos_calibration_examples.png`. Tables: `imos_detectability_table.csv`, `calibration_received_levels.csv`.

## 5. Detection on 8 March vs control nights (`scripts/acoustic_detect.py`)
**Event detector.** We flagged segments where the 2-s band level is at least 6 dB above a 120-s running median for at least 2 s, in bands 5–10, 8–16, 10–20, 16–32, 20–40 and 40–80 Hz, and merged them across bands. Spectral peak, low-frequency fraction and kurtosis are computed for main-night events.

**False-alarm rates.** Events per recorded hour, as control median (range) versus 8 March:

| Site | ≥10 dB, any band | ≥15 dB, 5–40 Hz, ≥5 s |
|---|---|---|
| PAPCA | 29 (17–67) vs 32 | 7.0 (0.5–13) vs 8.1 |
| PAKIM | 127 (110–158) vs 133 | 46 (41–60) vs 48 |
| PAPOR | 7 (2–13) vs 9 | 0.5 (0–1.6) vs **3.2** |

**What drove the PAPOR excess.** It comes from a mechanical-knock cluster (23:01–23:03; 23:16 with kurtosis 127), a T-phase-like event at **00:17:11** (19 dB, 9 Hz, 12 s), and 00:31:15. No arc impact can reach PAPOR before about 01:04 (≥4,000 km), so these cannot be MH370. They are listed in `detections_20140308.csv`.

**Window tests.**
- 82 recorded candidate windows: 6 at p<0.05, about 4 expected by chance.
  - All 6 are at PAKIM, and none is below 0.01 in the arrival-like statistics.
  - On inspection they are a ~50 Pa ringing mooring knock (00:34:41), whale units or knocks (01:01:47, 01:04:23), and F2 (01:33:03).
- 108 arc windows: 1 at p<0.05, about 5 expected by chance.

**The 8 March data are statistically indistinguishable from noise in every predicted window.**

**Upper limits** (`upper_limits.csv`; 95% detection level for an arrival in 5–20 Hz band RMS):

| Window | Site | Upper limit |
|---|---|---|
| Kadri 306°, arc crossing | PAPCA | **0.21 Pa** |
| Kadri 306°, anywhere on the ray | PAPCA | 0.36 Pa |
| Stead 246.9° | PAPCA | 0.21 Pa |
| Stead 246.9° | PAPOR | **0.17 Pa** |
| Arc windows (median) | PAPCA | ~0.48 Pa |
| Arc windows (median) | PAPOR | ~0.19 Pa |

For comparison, Kadri expects about 0.5 Pa at HA01 for a 777 impact. The open-path earthquake T-phases above reached 0.8–3.5 Pa at PAPCA.

**STA/LTA** (2 s/30 s, threshold 3, 8–16 and 10–20 Hz) triggers for the main night are in `stalta_20140308.csv`. In 8–16 Hz they run at 71/h at PAKIM, 27/h at PAPCA and 12/h at PAPOR.
- None fall in the PAPCA Kadri-306° or Stead windows; one is at 00:51:42 (ratio 3.1), outside both. None fall in the PAPOR Stead window.
- At PAKIM, a weak trigger at 01:32:40.4–01:32:42.1 (ratio 3.2) ends just before the Carlsberg prediction. It is a 2-s, 0.05 Pa RMS (+5 dB) 8–16 Hz fluctuation, identical to others in the same minute (e.g. 01:32:30), and not an emergent T-phase. At 71 triggers/h, one within ±10 s of any given time has a ~33% chance.

**Figures with predicted windows marked:**
- `fig_spec_PAPCA_0050.png`: Kadri 306°, Stead 246.9° and several Kadri picks; the 10.7 Hz tonal is visible.
- `fig_spec_PAPCA_0035.png`
- `fig_spec_PAKIM_0045.png`
- `fig_spec_PAKIM_0100.png`
- `fig_spec_PAKIM_0130.png`
- `fig_kimberley_0130.png`
- `fig_spec_PAPOR_0115.png`
- `fig_arc_pvalues.png`
- `fig_far.png`

## 6. Candidate details
**(1) Kadri 306.18°.**
- The timing strike is robust. ±0.4° moves the crossing by only 1,589–1,594 km, and c = 1.47–1.49 moves the implied origin by only 00:36:27–00:36:42.
- A source at the arc crossing is about 99 km closer to PAPCA than to HA01, so the PAPCA arrival had to come about 67 s before the HA01 pick, near 00:53:23. For any range on the ray from 500 to 6,000 km the window is 00:52:52–00:54:33. The path is open (shallowest point −3,900 m).
- Nothing arrived above 0.21 Pa. The non-detection is **weak evidence against** an arrival of the ~0.5 Pa that Kadri expects at HA01. It is not decisive, because PAPCA (436 m, canyon slope) and HA01 (SOFAR axis, 3-element array) couple differently, and Kadri gives no measured amplitude for this pick.

**(2) Stead 246.9°.**
- Stead described a weak arrival, manually aligned and incoherent across the HA01 elements.
- Both PAPCA (3,140 km) and PAPOR (5,020 km, open southern path) recorded the predicted windows and saw nothing.
- At 5,000 km a weak HA01 arrival would be far below the 0.17–0.21 Pa limits. **Untestable.**

**(3) Kadri Table 1.** Full table in `pred_ha01_picks.csv`: crossings, implied origins, Δt with Kadri's own values, predicted IMOS times, coverage and blockage. Test results are in `tests_candidates.csv`.
- **None of the 18 picks that cross the arc has a corroborating IMOS detection.**
- The faint Δt≈0 pick at 268.24° falls in a duty-cycle gap at all three IMOS sites. It also implies a source 62 s before the 00:19:29 log-on unless c ≳ 1.52 km/s.

**(4) Curtin.**
- **Carlsberg prediction.** For the Carlsberg point (2.11°N 69.31°E), HA01 01:34:40 implies an origin of 00:24:14–00:25:11. PAKIM is then predicted at **01:32:42.0–01:32:43.6**, almost independent of c.
- **What PAKIM shows near that time** (`kimberley_analysis.csv`, `fig_kimberley_0130.png`):

  | Feature | Time | Description | Chance coincidence on control nights |
  |---|---|---|---|
  | F1 | 01:32:56.5 | 20–60 Hz, ~5 s, 2.6 Pa peak; looks like a whale unit | 10/h at ≥26 dB, so 8% within ±15 s |
  | F2 | 01:33:04.5 | impulsive, broadband to >300 Hz with strong 2–10 Hz content, 9.4 Pa peak; the same type as the many mooring knocks at this site | 38/h at ≥15.7 dB, so 27% within ±15 s |
  | F3 | onset masked by F2; +15 dB at 01:33:39.0; centroid 01:34:22.3; plateau +20–24 dB to ~01:34:55 | emergent 3–30 Hz T-phase | — |

- **F1 and F2 do not look like a 6,000-km T-phase.** They are short, impulsive or tonal-burst signals of locally common types, arriving 13–21 s after the Carlsberg prediction.
- **F3 matches the Java event's T-phase.** It sits within 0–13 s of the T window for Anderson's location (01:33:38.8–01:34:08.9) and within 0.6 s of the window for the relocated source (01:33:51–01:34:22). It also looks like the PAKIM T-phases of other south-of-Java earthquakes.
- **The record does not independently support a Carlsberg arrival at 01:32:4x.**
  - If Curtin's "Scott Reef" logger is PAKIM, their 01:32:49 most likely refers to F1/F2.
  - Curtin's record has not been seen. If timed by the hex file-name clock (16.0 s earlier for this file), F2 would read 01:32:48.5, but CMST's own start-time table uses the footer clock.
  - We cannot settle this.
- **Location** (`locate_tdoa.csv`, `fig_tdoa_curves.png`). Bearing 301.6±0.75° plus the PAKIM−HA01 time difference puts the source:
  - with Curtin's time, 5,790–6,420 km from HA01 (Carlsberg Ridge region);
  - with F1/F2, 5,570–6,300 km;
  - with F3 (if F3 were associated), 4,540–5,650 km.

  Every case is **≥2,900 km from the 7th arc**.
- Open seismic data weakly favour a Carlsberg origin at ~00:25: a T-phase at KAAM at 00:30:02 (p=0.04), as described in `seismic/SEISMIC.md`.

**(5) Java 01:15:18.** See `seismic/SEISMIC.md`. The IMOS contribution is the PAKIM T-phase (F3) at the predicted time. PAPCA's predicted arrival (01:45:19–01:46:08) is not recorded, and the path runs along the WA shelf, so it is blocked.

## 7. Open seismometers (step 4; summary of `seismic/SEISMIC.md`)
- **Data and calibration.** 17 stations, including KAAM (Maldives) and MNC (Minicoy). We calibrated on 195 catalogued oceanic earthquakes. A 50% T-phase detection needs about **M4.6 at 500 km and M5.3 at 2,000 km**. For a 777 impact, at most "M3.2-equivalent" (Kadri), the chance of detection is ≤3% at AIS and ≤1.5% elsewhere.
- **Windows.** 270 station × arc-point windows: 0 unexplained detections. The one exceedance is the Java event at XMIS.
- **Java event.** Recorded at CISI, UGM, SMRI, XMIS, XMI, GIRL and COCO. Location and magnitude are as in the table above.
- **Curtin.** Weak T at KAAM 00:30:02 and DGAR 00:37:47 (marginal), consistent with a Carlsberg origin at about 00:25. No P or S was seen, so the source was probably smaller than M4.5.

## 8. Why no likelihood layer
1. **No detection.** No candidate or arc window contains an arrival above the control-night false-alarm rate at any IMOS site or open seismometer.
2. **A non-detection needs a calibrated probability of detection (Pd) to become a likelihood, and Pd cannot be calibrated from open data.**
   - What is known: IMOS PAPCA and PAPOR reliably hear open-path earthquake T-phases of M≥4.3 at 1,600–3,400 km (0.4–4.6 Pa), and limit any 8-March arrival to below roughly 0.2–0.5 Pa.
   - What is not known: the received level of a 777 impact at a shelf or slope recorder. The only published guide is Kadri's ~0.5 Pa expectation at HA01, from IMS crash detections.
   - The result is that Pd for an impact lies somewhere between ~0 and ~0.8.
3. **The duty cycle dominates the spatial pattern.**
   - The fraction of each predicted window that was recorded varies from 0 to 0.82 with latitude, and from 0 at 33–35.5°S.
   - A "non-detection likelihood" 1 − Pd·coverage(lat) would therefore mostly encode *when the recorders happened to be off*.
   - For example, with Pd = 0.5 it would up-weight 33–35.5°S by a factor of about 1.5 relative to 25°S and about 2.3 relative to 39°S, purely as a duty-cycle artefact.
4. **Seismometers:** Pd ≤3%. This is uninformative.

`arc_profile.csv` provides coverage, path blockage and test p-values per arc latitude, so the conditional what-if (L = Π_sites[1 − Pd·cov·open]) can be explored if ever wanted. We do **not** recommend feeding it into the combined posterior.

## 9. Assumptions and limitations
- **Sound speed and geometry.**
  - Constant c = 1.48 ± 0.01 km/s (±0.02 checked), on straight geodesics.
  - No range-dependent ocean model, and no modelling of slope conversion at the source or receiver; T-phase timing at shelf sites is uncertain by tens of seconds.
  - Blockage is judged qualitatively from 2′ ETOPO, which can miss narrow seamount summits.
- **Impact window.** Impact is assumed between 00:19:30 and 00:25:00 at the sea-level 7th arc. A glide of tens of nautical miles off the arc would change arrival times by about ±1 min, which is still inside our window padding for most latitudes.
- **Published picks.** HA01 picks are used as published: Kadri to ±0.4°, Stead's DOA ±2° (our assumption), times to ±5–10 s. Kadri and Stead disagree about the 00:52 group, and the waveforms cannot be checked.
- **Statistics.**
  - The control-night null pools 8 nights of the same hours. The 8 March distribution differs from it (KS p<10⁻⁷ at all sites), with PAPCA quieter and PAKIM noisier, reflecting night-to-night biology and shipping.
  - p-values are therefore approximate. The first-pass 5–40 Hz-only statistic was revised after it missed visible PAKIM T-phases; both statistics are reported.
- **Absolute timing.** The logger clock is physically verified only to about ±15 s, as described in section 2.
- **Curtin's logger.** Curtin's "Scott Reef" logger is assumed to be IMOS PAKIM. This is not confirmed.

## 10. Reproduce
Run each with `.venv/bin/python -I`, in this order:
1. `scripts/acoustic_download_imos.py`
2. `scripts/acoustic_download_bathy.py`
3. `scripts/acoustic_predictions.py`
4. `scripts/acoustic_reader_validation.py`
5. `scripts/acoustic_imos_calibration.py`
6. `scripts/acoustic_timing_check.py`, then the same script with `--step`
7. `scripts/acoustic_detect.py`
8. `scripts/acoustic_kimberley.py`
9. `scripts/acoustic_locate.py`
10. `scripts/acoustic_upper_limits.py`
11. `scripts/acoustic_arc_profile.py`

Step 4 (seismic) has its own scripts: `scripts/acoustic_seismic_{download,calibration,calibration_ext,java,curtin,arc}.py`.

Code lives in `src/mh370/acoustic.py`, covering the reader, calibration, geometry, features and statistics, and in `src/mh370/acoustic_seismic.py`. Per-file band-level features are cached in `data/derived/acoustic_cache/`.

Acknowledgement: "Data was sourced from Australia's Integrated Marine Observing System (IMOS) – IMOS is enabled by the National Collaborative Research Infrastructure strategy (NCRIS)." Logger data and processing: CMST, Curtin University.
