# mh370-open: findings (5–6 November 2026)

This is an independent reanalysis built only from freely downloadable data. It is not
authoritative. Each number comes from a module output, cited in brackets; read the module
READMEs for the method, the validation and the limitations.

## 1. Satellite data: where the flight ended ([outputs/satcom/README.md](outputs/satcom/README.md))

- **Forward model validation:**
  - The BFO model reproduces Ashton et al. (2015) Table 9 to within 1.2 Hz, and the ATSB sensitivity tables to within 1 Hz.
  - Gate, climb and cruise BFO calibration agrees to 3 Hz RMS or better.
  - In-flight BTO residuals have an SD of 19 µs.
  - Wind data come from public ARCO-ERA5, which needs no sign-up.
- **Recommended satellite layer: `p_v2`** (satcom README sections 0 and 13). It weights seven route families by their evidence: the five single autopilot settings after the final major turn (FMT) used in v1, plus two added in response to review:
  - a **waypoint family**: FMT → direct to a published waypoint → a new lateral mode;
  - a **generic two-leg family**: one true track, then a second one.
  - Family weights: LNAV 0.43, constant true track 0.25, waypoint 0.23, two-leg 0.08; the magnetic and heading modes ≈ 0.
  - Their evidence is comparable to the best single-mode family: Δlog Z = −0.6 (waypoint) and −1.7 (two-leg). The best waypoint route, FMT → MUTMI → about 184°T, scores +3.0.
- **Result:** impact latitude along the 7th arc, median **38.17°S**, 90% interval **36.46–39.51°S** (v1 single-mode `p`: 38.36°S, 37.40–39.61°S).
  - The new families hardly move the bulk of the posterior; the northern 90% bound moves about 0.9° north.
  - The best-fitting paths make the FMT at 18:32–18:40 UTC (02:32–02:40 Malaysian time) and cruise at about Mach 0.80 (single-mode fits: about 186–191°T, Mach 0.80–0.86).
  - The DSTG published peak is 37.8°S, and this result agrees with it. Nine v1 sensitivity runs kept the median between 37.9 and 38.3°S.
- **38°S or 34°S? The satellite data alone cannot decide.** UGIB 2020 (34.23°S 93.78°E): the earlier claim was too strong. v1 said "the UGIB hotspot needs a second, unrecorded turn". That was true only of the single-mode family. Corrected:
  - **BEDAX → 180°T at constant Mach and altitude, level at 18:40, fits badly** (Δlog Z = −18). It reaches BEDAX about 20 minutes too early, as UGIB themselves note.
  - **One extra turn fits 34.2°S as well as 38°S.** This holds for a generic second turn or a turn at a waypoint such as MUTMI.
  - **UGIB's own published route, replayed through this likelihood, fits as well as our best path** (log L −3.55 against −3.90). It does so by descending during the 18:40 call and flying slowly at FL100. **Flown level at that moment, the call's BFO misses by 39 Hz** (log L −20.3), against measurements good to a few hertz.
  - **The satellite data cannot tell a descent at 18:40 from level flight** (Bayes factor 1.1). Allowing a descent (`p_v2_sens_descent1840`) moves the median to **35.82°S** (90% 30.93–38.07°S).
  - **The ~38°S preference therefore comes from assumptions, not from a BTO/BFO misfit:** level flight at 18:40, and the prior over turns and speeds. UGIB resolved this with fuel, drift and aerial-search constraints, the DSTG with its dynamics prior; neither is satellite evidence.
- **Main caveat — family weighting and the 18:40 assumption:**
  - This model weights path families by their evidence.
  - With equal weight per family (7 families), the median moves to 37.0°S and the 90% tail reaches about 31°S.
  - With a free descent at 18:40, the median is 35.8°S.
  - No public fuel model was credible enough to use as a constraint.

## 2. Debris drift ([outputs/drift/README.md](outputs/drift/README.md))

- **Data:** NOAA Global Drifter Program records from undrogued buoys, which behave most like floating debris, turned into a Markov chain. The chain is validated against held-out drifters and corrected for a 20% transit-speed bias.
- **Evidence used:** 15 debris observations, plus the fact that no debris washed up in Western Australia.
- **Result:** the default likelihood peaks at **33.4°S**, with a 68% interval of 30.8–34.9°S. It is broad, and mainly rules out latitudes north of about 26°S and south of about 38°S.
- **Why published drift studies disagree:**
  - Uncorrected drifter chains run about 20% too slow, which moves the answer about 4° north. This explains the northern results from Miron and Godfrey.
  - CSIRO measured the flaperon's leeway in a sea trial. Including that leeway moves the flaperon's answer from about 30°S to about 38°S.

## 3. Open hydroacoustics and seismology ([outputs/acoustic/README.md](outputs/acoustic/README.md))

- **Data:** 4.7 GB of public IMOS recordings from that night plus eight control nights, and 17 open seismometers.
- **Reader:** ported from the IMOS reader and validated against the producer's spectra to within ±0.03 dB.
- **Kadri 306° candidate:** arrives 11.5–17 minutes too late, and the Perth Canyon recorder shows no arrival for it.
- **Stead 246.9° candidate** (pointing near 41°S 81.6°E): the timing fits, but no open sensor corroborates it, so it is untestable with open data.
- **Curtin "01:32" event:** a whale call, a mooring knock, and then the T-phase from the Java earthquake.
- **Anderson's Java "01:15" event:** a natural magnitude-4.1 earthquake, about 20 times the aircraft's impact energy.
- **Generic search along the arc:** no detection above the rate expected by chance.
- **No acoustic layer was built.** Building one from non-detections would mostly encode which recorders happened to be switched off.

## 4. What has been searched ([outputs/search/README.md](outputs/search/README.md))

- **Total:** 255,609 km² reconstructed, against about 240,000 km² published once overlaps are removed.
- **ATSB 2014–17:** from Geoscience Australia's machine-readable coverage, accurate to about 0.5 km.
- **Ocean Infinity 2018:** digitised from the official Malaysian weekly maps, accurate to 1–2 km.
- **Ocean Infinity 2025–26:** this footprint is **assumed**, reconstructed from AIS tracks and the official tally. No public map exists.

## 5. Combined result: where the probability is now ([outputs/combine/README.md](outputs/combine/README.md), section "Model-misspecification mixture"; [outputs/combine/RESULTS_mix.md](outputs/combine/RESULTS_mix.md))

**The central tension.** The satellite layer `p_v2` puts **86%** of its probability on ground already searched with a detection probability (POD) above 0.5, mostly by the 2014–17 ATSB-led search. If the satellite model were right, the chance that every past search would have missed the wreck is only **0.166** (satellite and searches only, w = 0) or **0.059** (with the debris drift, w = 0.5). The empty searches are therefore evidence that the model is wrong somewhere.

**The model-misspecification mixture.** We gave the analysis a deliberately vague alternative and let the evidence weigh it:

```
prior      π = (1 − ε)·p_sat + ε·p_broad
posterior  ∝ π × exp(w·drift_loglik) × (1 − POD)
```

- `p_broad` (`broad_arc`): the 7th-arc crossing is uniform in latitude over 20–42°S, followed by the satellite layer's own end-of-flight kernel. It stands in for "the satellite path model is wrong about where along the arc the flight ended".
- ε is the prior weight on that alternative. The drift evidence and the null searches re-weight the two components as well as the location.
- **Recommended default:** satellite `p_v2`, `broad_arc`, **ε = 0.1**, drift weight **w = 0.5**, POD best. ε = 0.1 gives the satellite model 90% prior credibility, so any shift is driven by the evidence.

**How far the evidence moves belief towards "model is wrong" (default):** ε **0.1 → 0.175 after the drift → 0.462 after the null searches**.
- The null searches alone count about 3–4:1 against the satellite model relative to `broad_arc` (Bayes factor 0.31 at w = 0, where ε goes 0.1 → 0.264; 0.25 at w = 0.5).
- The drift layer also prefers the broad component (Bayes factor 0.52), because its 33.4°S peak lies outside the satellite layer's support.
- The direction is robust: every broad variant, ε, w and POD bound moves weight towards "model is wrong". The size is not.

**Is the wreck in unsearched ground?** **0.58** under the default mixture; **0.42** if the satellite model is right; 0.76 under the broad component. POD low–high bounds: 0.28–0.88 (mixture).

**Where the probability is now** (7,500 km² blocks, about one search season each; captured probability under the default mixture unless stated):

| | Centre | Bounds | From the arc | Captured (mixture) | if satellite model right | Previously searched |
|---|---|---|---|---|---|---|
| **Area 1** | **30.46°S 98.41°E** | 29.03–31.85°S, 97.10–99.66°E | +42 to +62 km | **0.085** | 0.005 | 10% |
| **Area 2** | **38.75°S 89.02°E** | 38.10–39.39°S, 87.98–90.03°E | +90 to +130 km | **0.051** | 0.093 | 4% |
| **Area 3** | **32.36°S 96.89°E** | 30.98–33.70°S, 95.46–98.24°E | +62 to +82 km | **0.040** | 0.018 | 10% |
| Satellite-only pick (drift set aside, w = 0) | 39.94°S 84.82°E | 39.40–40.47°S, 83.91–85.73°E | 0 to +50 km | 0.143 at w = 0 (0.016 at the default) | 0.180 at w = 0 | 2% |
| Re-search block (any ground) | 37.91°S 88.69°E | 37.12–38.67°S, 87.42–89.93°E | +2 to +32 km | 0.108 | 0.199 | 100% (2014–17) |

"From the arc": positive = beyond the sea-level 7th arc, away from the satellite. P(success) with a new search at POD 0.9 is 0.9 × the captured figure (e.g. 0.077 for area 1).

- **No single search-sized block holds more than about 0.11.** Almost all of the best unsearched blocks lie 40–130 km beyond the arc, just outside the width the searches covered.
- **Area 1** is a long, narrow strip (375 × 20 km) along the south-east edge of the 2018 Ocean Infinity swath. Its probability comes almost entirely from the broad component (0.178 if the model is wrong, 0.005 if it is right). It is rank 1 at the default for every satellite variant run (`p_v2`: 0.085; descent at 18:40: 0.070; v1 `p`: a near-identical strip at 30.44°S 98.43°E, 0.105). The WSPR crash point (29.13°S 99.93°E) lies about 27 km outside it; this analysis does not use WSPR.
- **Area 2** is the glide zone beyond the south-east edge of the 2014–17 search (≈ the old area B). It is the top unsearched block if the satellite model is right.
- **Satellite-only pick:** with the drift set aside (w = 0), the top unsearched block is on the arc just past the southern end of the 2014–17 search (≈ the old area A).
- **Re-search:** if re-searching old ground is allowed, the highest block is inside the 2014–17 area (≈ the old area C). It is only worth it if that search was less thorough than reported.
- The old A–D table (single-mode `p`, conditional on the satellite model) is superseded. Under the default mixture its boxes hold A 0.016, B 0.049, C 0.104, D 0.052 (RESULTS_mix.md section 4).

**Fragility (which block is first is not robust):**
- **Areas 1 and 2 swap places** at w = 0.5 if the prior weight ε is below about **0.06** (crossover ε = 0.060 for `p_v2`; 0.058 in the earlier `p` run), or with the `broad_arc_lnavctt` start geometry (area 2 0.056, area 1 0.047 at ε = 0.1).
- **`broad_wide`** (cross-arc offset uniform within ±150 km) **moves the top unsearched block** to the near side of the arc at 32.63°S 94.20°E (−140 to −50 km), capturing only 0.031: a flat cross-arc prior concentrates nowhere.
- With the drift set aside (w = 0) the satellite-only pick leads; at w = 1 a block next to area 1 (30.94°S 98.05°E) leads.
- Across ε = 0.05–0.3 and w = 0–1 (`broad_arc`, POD best) the best unsearched block captures 0.07–0.17.

Other results:
- **Ocean Infinity contract remainder:** the north-west strip (about 7,400 km²) lies on the near side of the arc. It holds about 0.00001 of the default mixture (0.00002 if the satellite model is right): essentially nothing. To end up there the aircraft would have had to turn back after its final message.
- **WSPR point (29.128°S 99.934°E):** unsearched; it lies near area 1 but not in it. The method is judged unsound; see the WSPR critique in [../reports/MH370 open data search avenues.md](../reports/MH370%20open%20data%20search%20avenues.md).
- **The superseded conditional analysis** (satellite `p`, no mixture) is still in [outputs/combine/RESULTS.md](outputs/combine/RESULTS.md); the ε = 0 rows of RESULTS_mix.md reproduce it.

## 6. What would change these conclusions most

1. **How much to doubt the satellite model (ε) is a judgement call.** No data fix the prior weight on "the model is wrong somewhere". We use ε = 0.1; below about 0.06 areas 1 and 2 swap places, and the size (not the direction) of the shift towards "model is wrong" depends on it. RESULTS_mix.md tabulates ε = 0.05–0.3 and the crossovers so that a reader can substitute their own prior. The broad component is a stand-in, not a model; a sharper alternative would move the ranking.
2. **A credible public fuel model.** This decides the speed and route mix, and with it whether the flight ended near 38°S or could have reached 34°S.
3. **Whether the aircraft was descending during the 18:40 call.** The satellite data cannot tell; it moves the satellite median from 38.2°S to 35.8°S.
4. **The real 2025–26 Ocean Infinity coverage map.** The footprint used here is assumed.
5. **Probability-of-detection data for the ATSB and Ocean Infinity 2018 searches.** These decide the re-search block against the unsearched areas, and set the strength of the null-search evidence. Area 1 also hugs the digitised south-east edge of the 2018 swath.
6. **A model that combines all debris items with flaperon-specific leeway in actual 2014–16 currents.** The HYCOM hindcast here covers March 2014 – August 2015 only.
7. **The CTBTO hydrophone records from Cape Leeuwin and Diego Garcia, plus calibration shots along the 7th arc.** This is the only acoustic route that could be decisive, and it needs institutional access.

## Reproduce
See each module's README "Reproduce" section. Run order: satcom (incl. `satcom_posterior_v2.py`) → drift → search → combine (`combine_run.py`, then `combine_mix_run.py --sat-vars p_v2 p_v2_sens_descent1840 p`) → `make_map.py`. The acoustic module is independent. Everything runs as `.venv/bin/python -I scripts/<name>.py`.
