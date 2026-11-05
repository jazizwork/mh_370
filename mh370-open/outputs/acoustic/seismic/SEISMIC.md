## Step 4: Open seismometer checks (FDSN, no login)

### Bottom line
- **Island and coastal seismometers cannot test a 7th-arc impact.** Calibrated on 195 catalogued oceanic earthquakes, a 50% T-phase detection needs about M4.6 at 500 km and M5.3 at 2,000 km. A 777 impact is at most "M3.2-equivalent", and only if all 4 GJ became seismic energy.
- **No candidate arrival appears in any 7th-arc window.** None of the 270 station × arc-point windows has an unexplained excess above the control-night rate.
- **The 01:15 Java event is real.** It is an uncatalogued earthquake of about M4.1, about 20 times more energetic than an impact could be.
- **The Curtin event fits the Carlsberg Ridge** location better than any other proposed location.

### Data and processing
- **Stations.** Waveforms for 2014-03-07 20:00 to 03-08 03:00 UTC from 17 stations:
  - COCO, XMIS, XMI, AIS, RODM, ROCAM (100 sps), DGAR, NWAO, AUBUS (100 sps), GIRL, CISI, JAGI, SMRI, UGM, KAAM (Maldives) and MNC (Minicoy, 100 sps);
  - MBWA was downloaded but is unusable: a periodic square-wave artefact on both channels;
  - GE.HMDM returned no data.
- **Control nights.** Three nights (2014-03-05, -10, -11; 22:00–03:00) for COCO, XMIS, AIS, NWAO, AUBUS and GIRL.
- **Processing.**
  - Instrument response removed to velocity (StationXML, pre-filter 0.2 Hz to 0.45·fs).
  - Band-pass filters of 2–8 Hz and 3–16/18 Hz.
  - SNR statistic: the maximum 2-s (P/S) or 5-s (T) RMS in the predicted window, over the median RMS of a pre-window noise segment.
  - p-values come from the same statistic at every window position of the same length, on the station's own record or on the control nights.
- **Predicted arrivals.** P and S use ak135 (`obspy.taup`). T uses geodesic distance / c, with c = 1.46–1.50 km/s (1.48 nominal).
- **Raw-data provenance:** `data/raw/fdsn_seismic/SOURCE.md`.

### Calibration (catalogued events)
**Same night** (`calibration_measurements.csv`, `fig_calibration_*.png`):
- **P waves.** P is detected (p<0.05) for the Java M4.1 at 23:52 on 6 stations, the New Guinea M5.1 on 5, and the deep Banda M4.7 on 6. Envelope-peak P residuals at the clear stations are 0 to +4 s, so station timing is consistent with ak135.
- **T phases detected.** Only two, both at about 300 km:
  - Java M4.1 → XMIS: 316 km, 10.7 dB, p=0.02, arriving 22 s after the 1.48 km/s prediction.
  - Mauritius–Réunion mb3.7 → RODM: 340 km, 10.6 dB, p=0.03.
- **T phases not detected:**
  - IAR M4.5 at AUBUS/NWAO (1,830–1,860 km) or AIS (3,850 km);
  - Java M4.1 at COCO (1,296 km: 8.6 dB, p=0.25).

**Extended set** (`tphase_detectability*.csv`, `fig_tphase_detectability.png`):
- 216 windows for USGS M3.8–5.8 shallow oceanic events, Feb–Apr 2014, at COCO, XMIS, GIRL, DGAR, AIS, RODM and AUBUS.
- We fitted a pooled logistic model at a 9 dB threshold with a false-alarm floor of 0.12, excluding AUBUS (its control false-alarm rate is 0.42, i.e. no skill).

| Distance | M50, true T detection (5–95% bootstrap) | P(detect) at M3.2 | P(detect) at M2.5 |
|---|---|---|---|
| 300 km | 4.3 (3.8–4.8) | 6% | 1% |
| 500 km | 4.6 (4.2–5.0) | 3% | 0.6% |
| 1,000 km | 4.9 (4.75–5.2) | 1.5% | 0.3% |
| 2,000 km | 5.3 (5.1–5.7) | 0.6% | 0.1% |

The M3.2 and M2.5 columns are extrapolated below the catalogue's minimum magnitude (M3.8).

**Conclusion: for an MH370 impact these stations had essentially no chance.** A non-detection there carries no information.

### Candidate (5): Anderson's 01:15:18 event, 8.36°S 107.92°E (`java_*.csv`, `fig_java_event.png`)
- **It is real.** Impulsive P and clear S arrivals appear at:
  - CISI (90 km), UGM, SMRI, XMIS, XMI (290–350 km);
  - GIRL (1,720 km) and COCO.

  Neither USGS nor ISC catalogues it.
- **Location.** We used automatic AIC picks.

  | Method | Position | Origin time (UTC) | RMS |
  |---|---|---|---|
  | Absolute ak135 grid search | 8.18–8.30°S, 107.82–107.90°E | 01:15:19.0–01:15:22.5 | 1.6–1.8 s |
  | Master-event relative (USGS M4.1 as master) | 8.12–8.26°S, 107.88–107.92°E | 01:15:22–01:15:24 | 0.2–0.3 s |

  - Depth was tried at 10, 20 and 35 km and trades off against the position.
  - Anderson's point fits as well as our solutions: rms 1.8 s with the origin left free at 01:15:20.
  - So the claim is consistent with open data to within about 10–25 km and 2–6 s.
- **Size.** M ≈ **4.1 ± 0.2**. This is the median of 7 similar-distance stations, using Wood-Anderson horizontal amplitude ratios against the M4.1 with a Hutton–Boore distance term.
  - Anderson's "4× stronger" holds only at CISI, which is 3 times closer to this event than to the M4.1.
  - The vertical S/P amplitude ratios are earthquake-like and similar to the catalogued M4.1 (median 1.1 vs 1.4).
- **Energy.** Using log E = 1.5M + 4.8, E ≈ 9×10¹⁰ J. That is about **20 times the entire kinetic energy of the aircraft** (4 GJ), before allowing for the small fraction of impact energy that radiates seismically.
- **T phase.** Observed at XMIS/XMI at 01:20:00, 45 s later than the 1.48 km/s prediction.
- **Predicted T arrivals elsewhere** (pure water path, c 1.50–1.47; claimed → relocated source):
  - PAKIM: 01:33:38–01:34:01 → 01:33:51–01:34:13;
  - HA01: 01:48:41–01:49:40;
  - HA08S: 01:58:42–01:59:39. Anderson's 01:59:20 is consistent with this.
- **Verdict: real event, inconsistent with an MH370 impact.** It comes 56 min after the 7th arc, it has the size and S/P character of an ordinary forearc earthquake, and its energy is far too large for an impact or an implosion.

### Candidate (4): the Curtin event (HA01 01:34:40, ~301.6°; Scott Reef/Kimberley 01:32:49) (`curtin_*.csv`, `fig_curtin_*.png`)
**Geometry and timing** (these only need the published HA01 and Scott Reef times plus the PAKIM position):
- **Carlsberg point (2.11°N 69.31°E).**
  - Distance from HA01 is 6,212 km, at a back-azimuth of 301.55° (the measured bearing is 301.6 ± 0.75).
  - Implied origin: 00:24:14 / 00:24:42 / 00:25:11 for c = 1.47 / 1.48 / 1.49 km/s.
  - Predicted PAKIM arrival: **01:32:42–01:32:43**, nearly independent of c because PAKIM is at 6,038 km. This is 6–7 s from Curtin's 01:32:49.
- **Comparing the predicted PAKIM-minus-HA01 time difference with the observed −111 s:**

  | Proposed source | Predicted PAKIM − HA01 | Verdict |
  |---|---|---|
  | Carlsberg (Curtin, Sep 2014) | −117 s | consistent |
  | Curtin June 2014 point (5.93°S 77.22°E) | −27 s | inconsistent |
  | Kadri ref-13 point (23.66°S 96.68°E) | +425 s | inconsistent |
  | Java 01:15 event | −915 s; it also cannot produce HA01 01:34:40 at all | inconsistent |

- **Bearing plus time difference.** Intersecting the time-difference hyperbola with the 301.6 ± 0.75° bearing puts the source **5,700–6,410 km from HA01** (0.8°S–3.0°N, 67.6–73.0°E), with origin 00:22–00:30. That is at least 4,000 km from the 7th arc.
- **Path caveat.** The Carlsberg-to-PAKIM geodesic grazes the Maldives: shallowest point −4 m at 0.65°N 73.13°E, with 75 km of the path shallower than 1,000 m. It needs a passage between atolls, so treat it as only qualitatively open. The path to HA01 is clear: its shallowest point is −1,680 m.

**Open seismic evidence:**
- **No P or S** above the null at KAAM (447 km), DGAR, RODM, ROCAM or COCO (p ≥ 0.13).
  - MNC shows an S-window excess (13.8 dB, p=0.01) at 00:28:27, close to Anderson's Minicoy pick of 00:28:40. It is 37 s after the predicted S, so it is ambiguous.
- **A weak T at KAAM: 00:30:02** (5.6 dB, p=0.04), matching Anderson's Maldives pick of 00:30:00.
  - For the Carlsberg point it implies an origin of 00:24:57, which agrees with the origin implied by HA01.
- **A marginal T at DGAR: 00:37:47** (7.4 dB, p=0.08); 00:37:12 was predicted.
- **No T at MNC, RODM or ROCAM.** RODM does record T phases from Carlsberg Ridge M4.5–5.6 events in Feb–Apr 2014, so the source was probably smaller than about M4.5.
- **A fit to all T times** (HA01, PAKIM, KAAM, DGAR plus the bearing) gives 0.5°N 71.2°E, origin 00:27:47, 276 km from Curtin's point. That fit leans on weak picks.

**Verdict: inconsistent with MH370.** The source is about 6,000 km from HA01, i.e. at least 4,000 km from the arc. Its origin time of about 00:24–00:25 is a coincidence.
- The Kimberley 01:32:49 transient is consistent in timing (within about 10 s) with the Carlsberg solution.
- The alternative, that it is the Java T phase, needs an arrival 45–65 s *earlier* than pure-water speed allows. The same Java event's T phase at XMIS arrived 45 s *late*, so we judge Java the less likely source of the Kimberley transient. Final attribution rests on the IMOS pick in the main analysis.

### Candidates (1)–(3) and generic 7th-arc impacts (`arc_windows.csv`, `arc_candidates.csv`, `fig_arc_windows.png`)
- **Grid.** Arc points from 20 to 42°S every 0.5°, impact times 00:19:30–00:25:00, at COCO, XMIS, AIS, NWAO, AUBUS and GIRL; 270 windows in total.
  - p<0.05: 1 window. It is XMIS for 42°S at 01:16:11, which is the Java 01:15 event's P/S. That leaves **0 unexplained** detections.
- **HA01 bearing candidates.** We located where each bearing crosses the arc:

  | Candidate | Arc crossing | Range from HA01 | Implied origin (c=1.48) |
  |---|---|---|---|
  | Stead247 | 40.97°S 81.57°E | 2,924 km | 00:19:06 |
  | Kadri306 | 25.73°S 101.37°E | 1,591 km | 00:36:34, i.e. 17 min after the arc |
  | Kadri268 | 33.77°S 94.31°E | 1,827 km | 00:18:27, i.e. before 00:19:29 |

  Results at the open stations:
  - Stead247 at AIS (493 km, the closest open station to any hypothesis): 4.6 dB, p=0.91.
  - Kadri306, impact window: COCO 9.8 dB (p=0.38), XMIS 4.0 dB (p=0.66).
  - Kadri306, implied-origin window: COCO 10.2 dB (p=0.10), XMIS 1.3 dB (p=0.98).
  - Kadri268: every station has p ≥ 0.09.
  - Nothing exceeds the control false-alarm rate.
- **Verdict: untestable with open seismic data.** The non-detections are expected whether or not an impact occurred: P(detect) is at most about 3% at AIS and at most about 1.5% elsewhere, even for M3.2.

### Caveats
- T-phase timing at island stations is uncertain by tens of seconds (slope conversion, bathymetry). We used a constant c with no ocean model.
- Picks are automatic (AIC/STA-LTA), not analyst-reviewed.
- The magnitude is an amplitude ratio relative to a single master event. Its distance term comes from California.
- The detectability fit extrapolates below M3.8. The "M-equivalent" of an impact is itself very uncertain.
- AUBUS (school station) has frequent glitches and XMI frequent noise bursts. NWAO is inland, so it is not a T-phase station.
- KAAM/DGAR T picks for the Curtin event are weak (p≈0.04–0.08) and do not count as independent confirmation.
- **Code note:** `mh370.acoustic.forward` and `arc_crossing` fail in pyproj when given scalar lat/lon with an array of azimuths ("Array lengths are not the same"). This module uses a broadcast-safe copy, `acoustic_seismic.fwd` / `arc_crossing`.

### Files
- **Code:** `src/mh370/acoustic_seismic.py`, `scripts/acoustic_seismic_{download,calibration,calibration_ext,java,curtin,arc}.py`.
- **Outputs** (all in `outputs/acoustic/seismic/`):
  - Calibration: `calibration_events.csv`, `calibration_measurements.csv`, `tphase_detectability.csv`, `tphase_detectability_fit.csv`.
  - Java event: `java_picks.csv`, `java_summary.csv`, `java_magnitude.csv`.
  - Curtin event: `curtin_predictions.csv`, `curtin_triggers.csv`, `curtin_association.csv`.
  - 7th arc: `arc_windows.csv`, `arc_candidates.csv`.
  - Figures: `fig_calibration_{Java_M4.1,IAR_M4.5,MauritiusReunion_mb3.7,Macquarie_M4.2}.png`, `fig_tphase_detectability.png`, `fig_java_event.png`, `fig_curtin_record_section.png`, `fig_curtin_association.png`, `fig_arc_windows.png`.
