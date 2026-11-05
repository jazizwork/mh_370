# Workstream C, part 2: combining the evidence and ranking search blocks

This is an independent, public-data-only reanalysis. **It is not authoritative.**

`RESULTS.md` in this directory is regenerated on every run; this README describes the method and summarises the run of **2026-11-05 ~18:30**. That run used real inputs:

| input | file | last modified |
|---|---|---|
| satcom (workstream A) | `satcom_posterior.nc` | 17:45 |
| drift (workstream B) | `drift_loglik.nc` | 17:53 |
| search (part 1) | `search_pod.nc` | 17:54 |
| acoustic (workstream D) | `acoustic_loglik.nc` | **absent** (flagged) |

Upstream layers are still changing. **Re-run** `.venv/bin/python -I scripts/combine_run.py` (≈10 min) after any of them is updated, and quote `RESULTS.md`, not this summary.

## Method (`src/mh370/combine.py`, `scripts/combine_run.py`)

```
posterior ∝ satcom_p × exp(w · drift_loglik) [× exp(acoustic_loglik)] × (1 − pod)
```

**Inputs and scenarios**
- **satcom_p:** `p` and every `p_*` variable, each renormalised. That is 20 scenarios in this run: end-of-flight models, autopilot modes, equal mode weights and the `p_sens_*` runs.
- **drift_loglik:** `loglik`, plus `loglik_*` variants for the sensitivity runs. Per-item (`loglik_item_*`, `loglik_itemleeway_*`) and component (`loglik_wa_term`) fields are excluded.
- **Tempering:** w ∈ {0, 0.5, 1}.
- **POD bounds:** `pod`, `pod_low`, `pod_high`, from part 1 (`outputs/search/README.md`).

**NaN = uninformative.** After tempering, the layer is centred on its satcom-weighted log-mean-exp over the computed cells. Cells that were not computed (NaN) get 0, i.e. the average likelihood. Two consequences:
- the result does not depend on the additive constant of the log-likelihood (self-test T3);
- the satcom mass that falls in NaN cells is reported as a flag. It is 0.0000 in this run, because the drift layer covers ±300 km of the arc.

**Searched vs unsearched.** For each cell, with prior π (satcom × drift^w, before search) and searched fraction f:

| quantity | formula |
|---|---|
| P(past searches would have found it) | Σ π·pod |
| P(null search \| scenario) | 1 − Σ π·pod |
| P(in searched ground, missed \| not found) | Σ π·(f − pod) / (1 − Σ π·pod) |

The last line is checked against an analytic case in self-test T4.

**Ranking.** The posterior density is resampled (bilinear) onto a 2.5 km × 2.5 km raster in the 7th-arc frame:
- s = distance along the arc, 0 at 34.2342°S, positive towards the NE;
- n = signed distance across the arc, positive = farther from the satellite = SE.

Arc-aligned rectangles (cross-arc width 20–300 km in 10 km steps, length set by the budget) are scanned with 2-D prefix sums. The best box is chosen, excluded, and the scan repeated: top 5, disjoint, for budgets of 5,000, 7,500 (≈ the remaining OI contract area) and 15,000 km².

Two modes are reported:
- **any**: re-searching earlier ground is allowed. The posterior already discounts it by (1 − pod).
- **unsearched**: blocks may contain at most 10% previously searched area.

**Per block** the outputs give: the centre and mass-weighted centre (lat, lon), the lat/lon bounding box, the four corners, the area, the s/n ranges, the posterior mass, **P(success) = mass × POD_new (0.9)**, the pre-search prior mass, the fraction previously searched, and the mean prior POD.

Two benchmarks show how much the rectangle shape costs:
- a free-form contiguous block, grown greedily;
- the highest-density cells, without contiguity.

For the headline results these capture 1–7% more mass than the best rectangle at 5,000 and 7,500 km², and 2–10% more at 15,000 km². The exception is 15,000 km² at w = 0, where they capture 24–30% more because the mass is split between two separate lobes.

**Named areas.** The posterior mass is also integrated over:
- the OI contract area and its unsearched NW strip;
- the CAPTION zone;
- the Ulich–Iannello glide racetrack;
- 50 km discs around each published candidate point.

## Self-test (`scripts/combine_selftest.py`): **50/50 pass** (25 combiner checks + 25 mixture checks, see the mixture section)

The self-test uses **SYNTHETIC** placeholder inputs, written to `data/derived/selftest_SYNTHETIC/`:
- a Gaussian along the arc at 30°S as the satcom layer;
- flat, offset and gradient drift layers, with NaN beyond 300 km of the arc;
- a fake searched box at 31–29°S, |n| < 40 km, with POD 0.9;
- a fake acoustic patch.

The checks cover:
- normalisation;
- no effect from a flat drift layer, from an additive constant, or from NaN handling;
- the analytic missed-probability formula;
- exact tempering;
- recovery of a planted 7,500 km² block (overlap 0.95, area within 3%);
- disjointness of the ranked blocks, and the ≤ 10% constraint in unsearched mode;
- mass conservation in the arc-frame resampling;
- rejection of an input on the wrong grid;
- consistency of the real `search_pod.nc` (pod_low ≤ pod ≤ pod_high ≤ 1, pod ≤ searched_frac);
- an end-to-end run of the runner, including the acoustic branch;
- the model-misspecification mixture (TM1–TM9, listed in that section below).

Results are in `selftest_SYNTHETIC/README.md`. Every synthetic file and figure is stamped **SYNTHETIC** and says nothing about MH370.

## Results with the real inputs (run 2026-11-05)

### Searched vs unsearched (satcom `p` = evidence-weighted LNAV 0.63 / CTT 0.37 with 80% uncontrolled + 20% glide; drift `loglik`)

| w | prior mass in searched ground | P(null search \| model): pod best (low–high) | **P(wreck in searched ground, missed)**: pod best (low–high) | P(wreck in unsearched ground) |
|---|---|---|---|---|
| 0 | 0.85 | 0.18 (0.15–0.28) | **0.14** (0.02–0.46) | 0.86 |
| 0.5 | 0.98 | 0.05 (0.02–0.17) | **0.64** (0.16–0.90) | 0.36 |
| 1 | 1.00 | 0.03 (0.01–0.15) | **0.90** (0.49–0.98) | 0.10 |

How to read this table:
- **The satcom layer alone already places the end point in ground the ATSB searched.** Its 90% interval is 37.4–39.6°S on the arc, inside the ATSB area.
- **The drift layer moves mass further into that ground, not out of it.** Drift peaks near 33.4°S, but within the satcom support it only tilts mass northwards, from 39–40°S to 37.5–38.5°S, into ground the ATSB searched to POD ≈ 0.97.
- **The combined model is in clear tension with the fact that nothing was found.** Under it, the probability that every search would have missed is only 3–18%. Either the satcom/drift layers are over-confident or mis-specified (route mode, end-of-flight behaviour, drift physics), or the past POD is lower than assumed, or the wreck lies in the low-probability tails. The answer to "missed vs unsearched" therefore depends mainly on the POD bound and on w; see the ranges above.

### Top blocks, satcom `p`, POD best (full tables in `RESULTS.md` and `tables/`)

**Any ground**, 7,500 km², rank 1:

| w | centre | lat / lon range | n from arc (km) | area | mass | P(success) | previously searched |
|---|---|---|---|---|---|---|---|
| 0 | 39.94S 84.82E | 39.40–40.47S / 83.91–85.73E | 0 to +50 | 7,530 | 0.217 | **0.195** | 2% |
| 0.5 | 38.06S 88.46E | 37.42–38.70S / 87.45–89.46E | 0 to +40 | 7,524 | 0.350 | 0.315 | 100% (ATSB re-search) |
| 1 | 37.91S 88.68E | 37.27–38.55S / 87.67–89.67E | −2 to +38 | 7,521 | 0.537 | 0.484 | 100% (ATSB re-search) |

**Essentially unsearched ground (≤ 10% previously searched)**, 7,500 km², ranks 1–2:

| w | rank | centre | lat / lon range | n (km) | mass | P(success) |
|---|---|---|---|---|---|---|
| 0 | 1 | 39.94S 84.82E | 39.40–40.47S / 83.91–85.73E | 0 to +50 | 0.217 | **0.195** |
| 0 | 2 | 39.49S 87.80E | 38.92–40.06S / 86.89–88.69E | +92 to +142 | 0.133 | 0.120 |
| 0.5 | 1 | 38.90S 88.75E | 38.25–39.53S / 87.72–89.78E | +90 to +130 | 0.142 | 0.127 |
| 0.5 | 2 | 39.81S 84.93E | 39.29–40.33S / 84.12–85.74E | −12 to +48 | 0.064 | 0.058 |
| 1 | 1 | 38.70S 89.05E | 38.05–39.35S / 88.02–90.06E | +88 to +128 | 0.066 | 0.059 |

**Other budgets**, rank 1, unsearched mode:

| budget | w | centre | mass | P(success) |
|---|---|---|---|---|
| 5,000 km² | 0 | 39.86S 84.94E | 0.177 | 0.160 |
| 5,000 km² | 0.5 | 38.86S 88.72E | 0.111 | 0.100 |
| 5,000 km² | 1 | 38.70S 89.00E | 0.054 | 0.049 |
| 15,000 km² | 0 | 40.07S 84.70E | 0.275 | 0.248 |
| 15,000 km² | 0.5 | 38.98S 88.74E | 0.198 | 0.178 |
| 15,000 km² | 1 | 38.76S 89.15E | 0.082 | 0.074 |

In plain terms, the unsearched candidates under this satcom layer are:
- (a) **just south-west of the ATSB area's southern end**, on the arc at 39.4–40.5°S, 84–86°E;
- (b) **beyond the ATSB area's south-eastern edge**, +90 to +170 km from the arc at 38–40°S, 87–90°E. This is glide territory, which only the 20% piloted-glide component of `p` reaches.

### Named areas (posterior mass, satcom `p`)

All of the following get **≤ 0.0004** in every w and POD combination:
- the unsearched NW strip of the OI 2025 contract area (~7,400 km²) and the whole contract area;
- the CAPTION zone;
- 50 km discs around the UGIB LEP, CSIRO 35.6°S, WSPR, Kadri and Stead.

The Ulich–Iannello 70 NM glide racetrack gets ≤ 0.005.

The unsearched NW strip of the OI contract area is worth essentially nothing under this satcom layer, and ≤ 0.0001 under **every** satcom scenario. Other named areas pick up mass only under the poorly fitting modes:
- the whole contract area: up to 0.065, under `p_mode_CMT`;
- the UGIB disc: up to 0.10, under `p_mode_CMT`, w = 1;
- the CSIRO disc: up to 0.33, under `p_mode_CTH`, w = 1.

The near-zero value for the NW strip under the headline layer follows directly from workstream A placing the end point at 37–40°S. That result is the dominant, and still single-source, assumption.

### Sensitivity

**Satcom scenarios** (POD best; see `RESULTS.md`, section "All satcom scenarios"):

| satcom scenario | rank-1 7,500 km² block (any ground) | P(null search) | comment |
|---|---|---|---|
| `p_uncontrolled`, `p_arc0019`, `p_mode_LNAV`, `p_mode_CTT`, all `p_sens_*` | same picture as `p` | 0.03–0.21 | At w=0: 39.9S 84.8E, except `p_mode_CTT` and `p_sens_bfo4p3`, which give 39.2S 88.4E (SE glide zone). For w ≥ 0.5: ATSB re-search at 37.8–38.2S. |
| `p_glide` | 39.5S 87.8E at w=0, then 38.7–38.9S 88.8–89.0E; n +88…+143 km; mass 0.22–0.43; unsearched | 0.54 / 0.17 / 0.08 (w = 0 / 0.5 / 1) | |
| `p_dstg_kernel` | 37.2–37.7S 87.5–88.2E; n −92…−52 km, beyond the ATSB NW edge; mass 0.15–0.30; unsearched | 0.36–0.45 | |
| `p_mode_CMT` (33.6°S; evidence weight 2e-5) | w=0: 35.0S 95.0E, n +100…+180, unsearched. w ≥ 0.5: 33.9S 94.8E, n +8…+80, 91–92% previously searched. | 0.17 / 0.11 / 0.09 | |
| `p_mode_CTH` (35.7°S; evidence weight 1e-5) | w=0: 37.1S 92.0E, n +90…+160. w ≥ 0.5: 35.6–35.7S 92.3E, ATSB re-search. | 0.16 / 0.09 / 0.07 | |
| `p_mode_CMH` (31.2°S; evidence weight 1e-14) | 31.55S 97.55E, n +38…+88 km, straddling the SE edge of OI 2018 Sites 2/3 (22–23% previously searched); mass 0.69–0.71 | 0.58–0.61 | |
| `p_equal_modes` | 31.55S 97.55E, mass 0.33–0.58 (driven by CMH) | 0.25–0.27 | |

**Drift variants** (31 variants, w = 0.5 and 1, satcom `p`):
- The rank-1 any-ground block stays at 37.6–38.4°S, an ATSB re-search, for every variant except two groups:
  - the flaperon-only variants (5 variants) move it to 39.9°S 84.8°E, the same place as w = 0;
  - `loglik_windage3` at w = 1 moves it to 33.8°S 94.7°E (re-search; top unsearched block 34.7°S 96.0°E, mass 0.06).
- The top unsearched block stays at 38.5–39.0°S, n ≈ +90…+130 km, except for `loglik_drogued` and the flaperon-only variants, which give 39.9–40.3°S.

**Acoustic:** not used, because there is no `acoustic_loglik.nc`. The runner adds a with-acoustic scenario set automatically when the file appears.

## Model-misspecification mixture (reviewer response)

> **Update (6 Nov 2026):** the mixture was re-run with the new satellite layer `p_v2` (headline), the descent sensitivity `p_v2_sens_descent1840`, and the old `p`. Current headline figures (p_v2, broad_arc, ε = 0.1, w = 0.5, POD best): broad weight 0.1 → 0.175 after drift → **0.462** after the null searches; P(unsearched) **0.58**; top 7,500 km² unsearched block **30.46°S 98.41°E (0.085)**. The `p`-only numbers further down (0.59, 30.44°S 98.43°E, 0.105) are from the earlier run and are superseded. See `RESULTS_mix.md` for the full current tables.

### The critique

A reviewer pointed out that the block ranking above depends on a model that the failed searches already count against. Our own diagnostic says that, if the satellite model were right, there was only a 3–18% chance that every search would come up empty. So the 0.22 (A) and 0.14 (B) captured-probability figures hold **only if the model is right**, and the null result is itself evidence that it is not. The reviewer asked for a broad "model is wrong" component with a small prior weight, and for the null searches to update that weight.

This section does that. It is implemented alongside the original analysis; nothing above changes. The ε = 0 rows of the new run reproduce the old numbers exactly (self-test TM2; e.g. B = 0.1416 at w = 0.5).

### Method (`src/mh370/combine_mix.py`, `scripts/combine_mix_run.py`)

```
prior      π(x) = (1 − ε)·p_sat(x) + ε·p_broad(x)
posterior  ∝ π(x) × exp(w·drift_loglik(x)) × (1 − pod(x))
```

Both the drift evidence and the null searches re-weight the two components as well as the location. Write q_k for component k after the drift evidence and N_k for the probability that every past search misses, given that component:

| quantity | formula | meaning |
|---|---|---|
| Z_k | Σ p_k·exp(w·ll) | drift evidence for component k (common arbitrary constant) |
| q_k | p_k·exp(w·ll) / Z_k | component k after the drift evidence |
| N_k | 1 − Σ q_k·pod | P(every past search misses \| component k) |
| ε_drift | ε·Z_b / ((1−ε)·Z_s + ε·Z_b) | broad weight after the drift evidence |
| **ε_post** | ε_drift·N_b / ((1−ε_drift)·N_s + ε_drift·N_b) | broad weight after the null searches as well |
| BF_null | N_s / N_b | Bayes factor of the null search result, satellite model : broad (< 1 favours "model is wrong") |
| BF_drift | Z_s / Z_b | the same for the drift evidence |

The mixture posterior is (1 − ε_post)·post_sat + ε_post·post_broad. Each block therefore carries three numbers:
- the **mixture** captured probability: the planning figure, marginal over "satellite model right / wrong";
- the probability captured **if the satellite model is right**: the old, conditional figure;
- the probability captured if the broad component is right.

The drift layer is centred on the mixture-weighted mean likelihood, with NaN cells treated as neutral, as before. It has no NaN cells within ±300 km of the arc, which covers both broad components.

**Settings:**
- ε ∈ {0.05, 0.1, 0.2, 0.3}, plus a fixed-box sweep over 0–0.5. The sweep is exact and cheap, because the component posteriors do not depend on ε.
- w ∈ {0, 0.5, 1}.
- POD best, low and high.
- `broad_arc`, `broad_wide` and `broad_arc_lnavctt`.
- Satellite variable `p`, plus `p_v2` automatically if it appears in `satcom_posterior.nc` (see Reproduce).

### The broad components (`data/derived/combine_broad_components.nc`)

Both components are built by Monte Carlo: 8 million draws each, seeded. They are gridded exactly as the satellite layer is, with a 2-D histogram, a 1-cell Gaussian smoothing and normalisation.

- **`broad_arc`**: the 7th-arc crossing is **uniform in latitude of the sea-level 7th arc over 20°S–42°S**. From there it uses the **same end-of-flight kernel as the satellite layer's default `p`**, replicated from `scripts/satcom_posterior.py` (`sample_eof`, `to_grid`):
  - 0.8 × uncontrolled descent: +5 NM along the final track, Gaussian sd 7 NM per axis;
  - 0.2 × piloted glide: uniform 0–120 NM along the final track, direction sd 15°.

  Self-test TM8 parses the satcom script and fails if these constants ever diverge. The kernel needs a start state at 00:19:29, which has two parts:
  - the aircraft's cross-arc offset from the sea-level arc. It is at altitude, so it sits on the higher BTO arc;
  - the angle between its final track and the arc normal.

  Both are drawn jointly from the satcom SMC end states, **pooled over all five autopilot modes with equal weight**: offset 5/50/95% = +5 / +20 / +43 km, angle 29 / 40 / 44°. This local geometry is the only thing borrowed from the path model, not where along the arc it ends. The resulting cross-arc profile matches that of `p_equal_modes` to within 0.002 per 25 km bin. It is slightly wider and further out than `p`, because CMH/CMT end farther off the arc.
- **`broad_wide`**: the same crossing latitudes, with the cross-arc offset **uniform within ±150 km** of the sea-level arc. This represents an end-of-flight model that is also wrong.
- **`broad_arc_lnavctt`** (sensitivity): as `broad_arc`, but with the start geometry pooled over LNAV and CTT only. These are the modes that carry the satellite layer's weight, so the aircraft starts closer to the arc: offset +2 / +14 / +25 km, angle 42–44°. It was added because the top-ranked block turned out to be sensitive to this choice (see Results).

**Why these ranges:**
- **20°S–42°S along the arc.**
  - The ATSB bounded the 7th arc by aircraft performance: the fuel remaining at the last ACARS report, across a range of speeds and altitudes ([ATSB, MH370 – Flight Path Analysis Update, 30 July 2015](https://www.atsb.gov.au/sites/default/files/media/5668327/ae2014054_mh370__search_areas_30jul2015.pdf), "Aircraft performance limitations", Fig. 20). It summarises that "based on all the independent analysis of satellite communications and aircraft performance, the total extent of the 7th arc reaches from latitude 20 degrees S to 40 degrees S" ([ATSB, "The Seventh Arc"](https://www.atsb.gov.au/node/813)). That page did not load during this work, so the quote is taken from a search-engine extract.
  - We extend the southern end by 2° to 42°S. 40°S would be a hard edge exactly where candidate A (39.4–40.5°S) and the tail of our satellite layer lie: the 95% bound is 39.6°S and the sensitivity runs reach 39.8°S, before any glide.
  - The range also covers everything else proposed: the northern drift family (25–30°S), the WSPR point (29.1°S), CSIRO (35.6°S), UGIB (34.2°S), and the full along-arc extent of every search (ATSB about 33–40°S, OI 2018 about 25–36°S).
  - **Uniform in latitude, as specified, is not uniform in arc length.** The arc runs 121 km per degree of latitude at 21°S but 266 km per degree at 41°S. Uniform in arc length would put 51% instead of 41% of the broad mass south of 33°S.
- **±150 km across the arc (`broad_wide`).**
  - It is about twice the ATSB's original priority width (+30/−20 NM, i.e. +56/−37 km; ATSB 2015, p. 35).
  - It covers the ±70 NM (±130 km) "Zone 2" glide band discussed in the literature (see `../reports/MH370 open data search avenues.md`; CAPTION argues for 50–70 NM).
  - It roughly matches how far the satcom glide kernel reaches across the arc: 120 NM × cos 40° ≈ 170 km.

**Recommended default: ε = 0.1, `broad_arc`, w = 0.5, POD best**
- **ε = 0.1** is deliberately small. It gives the satellite model 90% prior credibility, so any shift towards "model is wrong" is driven by the evidence, not by scepticism built in up front. No data fix ε, so 0.05–0.3 are all reported, and section 4b of `RESULTS_mix.md` gives the ε at which the ranking flips.
- **`broad_arc`** keeps the satellite layer's end-of-flight model. It therefore isolates the documented weak point of the satellite layer: where along the arc it ends, which depends on autopilot-mode weighting and the absence of a fuel model. It is also the conservative choice, because `broad_wide` always gains more weight.
- **w = 0.5 and POD best** are the existing headline settings.

### Results

Run of 2026-11-05 ~21:30 on the inputs listed at the top of this README. `p_v2` was not present, so only satellite variable `p` was run. Full tables are in `RESULTS_mix.md`; the figures are `fig_mix_vs_old.png` and `fig_mix_weights.png`.

**Which figures are which:**
- *Conditional*: holds only if the satellite model is right. This is what the sections above report.
- *Mixture*: marginal over "model right" and "model wrong". It is still conditional on the mixture assumptions: the form of the broad component and the prior ε.

**1. How far the evidence moves belief towards "model is wrong"**

Posterior broad weight ε_post at POD best, with the POD low–high range in brackets:

| broad component | w | ε = 0.05 | **ε = 0.1** | ε = 0.2 | ε = 0.3 |
|---|---|---|---|---|---|
| `broad_arc` | 0 | 0.14 (0.10–0.14) | **0.25** (0.20–0.26) | 0.43 (0.36–0.44) | 0.57 (0.49–0.58) |
| `broad_arc` | **0.5** | 0.41 (0.22–0.56) | **0.59** (0.38–0.73) | 0.77 (0.58–0.86) | 0.85 (0.70–0.91) |
| `broad_arc` | 1 | 0.77 (0.54–0.93) | **0.88** (0.71–0.96) | 0.94 (0.85–0.98) | 0.96 (0.90–0.99) |
| `broad_wide` | 0 / 0.5 / 1 | 0.19 / 0.68 / 0.93 | **0.33 / 0.82 / 0.96** | 0.52 / 0.91 / 0.98 | 0.65 / 0.94 / 0.99 |
| `broad_arc_lnavctt` | 0 / 0.5 / 1 | 0.13 / 0.35 / 0.73 | **0.24 / 0.53 / 0.85** | 0.41 / 0.72 / 0.93 | 0.55 / 0.81 / 0.96 |

Where the shift comes from (ε = 0.1, `broad_arc`, POD best):

| w | P(all searches miss \| sat. model) | P(all searches miss \| broad) | BF null (sat : broad) | BF drift (sat : broad) | ε → after drift → after null searches | P(wreck in unsearched ground): if sat. right / if broad / **mixture** |
|---|---|---|---|---|---|---|
| 0 | 0.177 | 0.538 | 0.33 (0.31–0.45) | 1 | 0.10 → 0.10 → **0.25** | 0.86 / 0.90 / **0.87** |
| 0.5 | 0.046 | 0.238 | 0.19 (0.10–0.46) | 0.40 | 0.10 → 0.22 → **0.59** | 0.36 / 0.76 / **0.60** |
| 1 | 0.033 | 0.211 | 0.16 (0.04–0.46) | 0.10 | 0.10 → 0.53 → **0.88** | 0.10 / 0.73 / **0.65** |

What this shows:
- **The null searches alone count about 3:1 against the satellite model** relative to `broad_arc`: BF 0.33, or 0.31–0.45 across the POD bounds. Against `broad_wide` the figure is 4.4:1 (BF 0.23). At w = 0 this raises a 10% prior on "model wrong" to 25%.
- **With the drift evidence the shift is larger, for two reasons.**
  - The drift layer itself prefers the broad component (BF 0.40 at w = 0.5, 0.10 at w = 1), because its peak (33.4°S) lies outside the satellite layer's support.
  - Once drift is included, the satellite model's prediction that the searches would succeed is sharper, so the null result counts more: P(miss) 0.05 against 0.24, BF ≈ 1:5.
- **At the recommended default the satellite model ends up with 41% credibility, against 90% before the evidence.**
- **The direction is robust:** every broad variant, ε, w and POD bound moves weight towards "model is wrong". **The size is not:** it depends on ε, w and the POD bound.

**2. Re-ranked blocks: recommended default (ε = 0.1, `broad_arc`, w = 0.5, POD best)**

Essentially unsearched ground (≤ 10% previously searched); captured probability is the mixture figure:

| budget | rank | centre | lat / lon range | n from arc | **captured (mixture)** | **P(success) @0.9** | if sat. right | if broad |
|---|---|---|---|---|---|---|---|---|
| 7,500 km² | **1 (U1)** | **30.44°S 98.43°E** | 29.02–31.83°S / 97.11–99.67°E | +42 to +62 km | **0.105** | **0.095** | 0.000 | 0.178 |
| 7,500 km² | 2 (U2 ≈ old B) | 38.88°S 88.78°E | 38.23–39.52°S / 87.74–89.80°E | +90 to +130 km | 0.059 | 0.053 | 0.142 | 0.002 |
| 7,500 km² | 3 (U3) | 31.66°S 97.58°E | 30.26–33.02°S / 96.19–98.89°E | +62 to +82 km | 0.041 | 0.037 | 0.000 | 0.069 |
| 7,500 km² | 5 (≈ old A) | 39.81°S 84.93°E | 39.29–40.33°S / 84.12–85.74°E | −12 to +48 km | 0.027 | 0.025 | 0.064 | 0.002 |
| 5,000 km² | 1 | 30.87°S 98.04°E | 29.92–31.81°S / 97.13–98.92°E | +42 to +62 km | 0.080 | 0.072 | 0.000 | 0.134 |
| 15,000 km² | 1 | 30.03°S 98.85°E | 28.10–31.91°S / 97.10–100.47°E | +42 to +72 km | 0.152 | 0.136 | 0.000 | 0.256 |

- **U1 is a long, narrow strip** along the south-east edge of the OI 2018 swath at 28–32°S. It holds the tail of an uncontrolled descent just beyond what OI 2018 imaged, at the latitudes the drift layer favours. The satellite model gives it nothing. All of its probability comes from the "model wrong" component.
- **If re-search is allowed**, the rank-1 7,500 km² block is still C, the ATSB re-search at 38.06°S 88.46°E, now at 0.144 (P(success) 0.130). U1 follows at 0.105.

**3. How much the old A–D figures shrink** (fixed boxes from `ranked_blocks_all.csv`, `broad_arc`, POD best)

| hypothesis (7,500 km² box) | old figure (conditional) | mixture, ε = 0.1 | shrink | mixture, ε = 0.05–0.3 |
|---|---|---|---|---|
| A, 39.94°S 84.82°E, w = 0 | 0.217 | **0.172** | ×0.79 | 0.192–0.116 |
| A, same box, w = 0.5 | 0.061 | 0.026 | ×0.43 | 0.037–0.011 |
| B, 38.90°S 88.75°E, w = 0.5 | 0.142 | **0.059** | ×0.41 | 0.085–0.023 |
| B, same box, w = 0 | 0.096 | 0.073 | ×0.76 | 0.083–0.044 |
| C, 38.06°S 88.46°E (re-search), w = 0.5 | 0.350 | 0.144 | ×0.41 | 0.208–0.055 |
| D, 31.50°S 97.69°E (box from `p_equal_modes`), w = 0.5 | 0 under `p` | 0.061 | – | 0.042–0.087 |

- With `broad_wide` the shrinkage is stronger: A (w = 0) falls to 0.148 and B (w = 0.5) to 0.027.
- **Restated honestly:** under the recommended mixture, A and B are worth about **0.17 and 0.06** (P(success) 0.15 and 0.05), not 0.22 and 0.14.

**4. How robust the top block is: not very**

- **ε (fixed boxes, `broad_arc`, POD best).**
  - At w = 0.5, U1 overtakes B only when the prior ε exceeds **0.058**, i.e. a posterior weight of 0.45. It overtakes C when ε exceeds 0.13.
  - At w = 0, A stays rank-1 for every ε (0.19 → 0.12 as ε goes from 0.05 to 0.3). U1 would overtake B only above ε = 0.50.
  - At w = 1, U1 is rank-1 for ε > 0.005.
- **The start geometry of the kernel.** With `broad_arc_lnavctt` the posterior weight hardly changes (0.53 against 0.59), but U1's broad-conditional mass drops from 0.178 to 0.109. At ε = 0.1 and w = 0.5 the rank-1 unsearched block is then B again (38.88°S 88.78°E, 0.067), with U1 at 0.058. U1 is rank-1 again for ε ≥ 0.2, and at w = 1.
- **The cross-arc kernel.** With `broad_wide` (w ≥ 0.5, ε ≥ 0.1) the rank-1 unsearched block moves to the north-west side of the arc, at 32.63°S 94.20°E, n −140 to −50 km. It captures only 0.035–0.064: a flat cross-arc prior concentrates nowhere.

**Bottom line:**
- The robust result of this analysis is that **belief in the satellite model should fall substantially**: from 0.9 to about 0.75 using the null searches alone (w = 0), and to about 0.4 with drift at w = 0.5.
- In consequence, the best essentially unsearched 7,500 km² block now captures only **0.105** at the recommended default (P(success) 0.095). Across ε = 0.05–0.3 and w = 0–1 with `broad_arc` and POD best, the best unsearched block captures 0.08–0.19.
- **Which block is first is not robust.**
  - At w = 0.5 it is either the old B glide zone (38.9°S 88.8°E) or the OI 2018 edge strip U1 (30.4°S 98.4°E). The two are within a factor of about 2 of each other, and which leads depends on ε and on the kernel's start geometry.
  - At w = 0, A still leads; at w = 1, U1 leads clearly.
  - A plan would have to weigh both candidates. The earlier single-number P(success) of 0.13–0.20 for A and B should not be quoted without the mixture caveat.

**Mixture self-tests** (in `scripts/combine_selftest.py`):
- **TM1:** each broad component is normalised and uniform in arc latitude to within 1.2%; `broad_wide` is flat to within 0.5% across ±125 km.
- **TM2:** ε = 0 reproduces the satellite-only combiner exactly, and ε = 1 reproduces the broad-only one.
- **TM3:** a satellite component placed on the synthetic searched box (POD 0.9) gives exactly the analytic two-hypothesis update. ε 0.1 → 0.51, BF = 0.105, and the posterior weight rises monotonically with past POD.
- **TM4:** a satellite component on unsearched ground makes the weight fall.
- **TM5:** every component and the mixture are normalised, and they match the direct formula.
- **TM6:** the drift-updated weight equals the direct Z ratio, and an additive constant in the log-likelihood has no effect.
- **TM7:** block mass = (1 − ε_post)·conditional + ε_post·broad.
- **TM8:** the kernel constants match `scripts/satcom_posterior.py`.
- **TM9:** an end-to-end synthetic run of the mixture runner, including `p_v2` auto-detection and a clean failure on a missing variable.

### Caveats specific to the mixture

- **ε is a judgement.** No data determine it. The ranking flips near ε ≈ 0.06 at w = 0.5. All ε values and the crossovers are reported so that a reader can substitute their own prior.
- **The broad component is a stand-in, not a model.** ε_post measures how badly the satellite layer is contradicted *relative to this particular diffuse alternative*. It is not an absolute probability that the model is wrong. A sharper alternative might gain or lose more weight, for example UGIB-style second-turn paths, a fuel-constrained mode mix, or the equal-mode layer. Its structure would also move the ranking.
- **The drift layer does much of the work when w > 0.** Its own uncertainties (w, leeway, transit-speed correction; see `outputs/drift/README.md`) carry straight into the weights. The w = 0 rows isolate the null-search evidence.
- **U1 hugs a search edge.** Its value depends on:
  - the exact south-east edge of the OI 2018 swath (digitised to 1–2 km) and the POD assumed there;
  - the cross-arc offset of the uncontrolled-descent kernel (see the `broad_arc_lnavctt` result).

  A 20 km × 375 km strip is also an unusual search shape. The box finder allows widths of 20–300 km, and the 15,000 km² version is 30 km wide.
- **P(all searches miss | broad) uses the same POD layer,** including the *assumed* OI 2025–26 footprint.
- **The along-arc prior is uniform in latitude, as specified.** Uniform in arc length would put more weight south of 33°S: 51% instead of 41%.
- **The past searches were placed using earlier versions of models like this one.** That does not bias the likelihood for a given location. It is, however, exactly why the null result is informative against this family of models.
- **Only `p` was run, because `p_v2` was absent at the time of the run.** Re-run with `--sat-vars p_v2 p` when it lands.

## Limitations

- **The outcome is dominated by the satcom layer**, specifically by which autopilot modes it admits and how they are weighted. Equal mode weights move the answer to ~31.5°S.
- **The drift layer is tempered but not independent of modelling choices** (w is the stated sensitivity). The search layer contains assumed polygons (OI 2025–26) and judgement-based POD values; see `outputs/search/README.md`.
- **The low P(null search | model) is the most important diagnostic.** The evidence layers as delivered are hard to reconcile with ~255,000 km² of unsuccessful searching. Blocks ranked under such a model inherit that problem: their P(success) is conditional on the model being right. The section 'Model-misspecification mixture' quantifies this and gives unconditional (mixture) figures.
- **Blocks are arc-aligned rectangles.** Free-form blocks gain at most a few percent of mass.
- **P(success) uses POD_new = 0.9 for every block**, with no account of terrain.

## Files

| file | content |
|---|---|
| `RESULTS.md` | auto-generated full results: headline split, blocks for every budget, w and mode, named areas, every satcom scenario, every drift variant |
| `scenario_summary.csv` | one row per scenario (satcom × drift × w × POD bound × acoustic): split probabilities, P(null search), rank-1 blocks, benchmarks, named-area masses |
| `ranked_blocks_all.csv` | every ranked block, with corners |
| `tables/<scenario>.csv/.md` | ranked tables per main scenario (both modes) |
| `blocks_headline.geojson` | box outlines for satcom `p`, POD best |
| `arc_profile.csv` | prior and posterior marginalised onto the latitude of the nearest point on the sea-level arc (satcom `p`) |
| `fig_posterior_w.png`, `fig_posterior_pod_bounds.png`, `fig_top_block_centres_{any,unsearched}.png`, `fig_arc_profile.png` | maps and profile |
| `data/derived/combined_posterior.nc` | `post_w{0,0p5,1}_{best,low,high}` and `prior_w*` for satcom `p` |
| `selftest_SYNTHETIC/` | SYNTHETIC self-test outputs (not MH370 results) |
| `run_info.json` | input paths and modification times, flags, scenario lists |
| **Mixture (reviewer response)** | |
| `RESULTS_mix.md` | auto-generated: broad-component weights (prior → after drift → after null searches), P(null \| component), Bayes factors, P(unsearched), recommended-default blocks, old ranking, old A–D under the mixture, ε sweep with crossovers, rank-1 blocks for every setting |
| `scenario_summary_mix.csv` | one row per setting (satellite var × broad × ε × w × POD bound); ε = 0 rows = old conditional analysis |
| `ranked_blocks_mix.csv` | every mixture-ranked block, with corners; `mass` = mixture, `mass_sat_cond` = if the satellite model is right, `mass_broad_cond` = if broad |
| `old_blocks_under_mix.csv` | the fixed old A–D boxes under every mixture setting |
| `eps_sweep_mix.csv` | fixed boxes (new U1–U3, old A–D) vs prior ε 0–0.5 (recommended broad and POD) |
| `fig_mix_vs_old.png` | old vs mixture posterior maps, with blocks, plus the arc profile |
| `fig_mix_weights.png` | posterior broad weight vs prior ε; captured probability of fixed boxes vs ε |
| `run_info_mix.json` | inputs, broad-component build info, settings |
| `data/derived/combined_posterior_mix.nc` | `post_mix`, `prior_mix`, `post_sat_cond`, `post_broad_cond` (recommended default), `post_mix_<broad>_eps*_w*` (POD best), and `p_broad_*` |
| `data/derived/combine_broad_components.nc` | the broad prior components (cache; rebuilt with `--rebuild-broad`) |

**Reproduce the mixture:** `.venv/bin/python -I scripts/combine_mix_run.py` (about 5 min; run `combine_run.py` first, because the old A–D boxes are read from `ranked_blocks_all.csv`). By default it runs satellite variable `p`, and `p_v2` as well if that variable exists in `satcom_posterior.nc`. The first variable listed is the headline. When `p_v2` lands, use `--sat-vars p_v2 p` to make it the headline with `p` alongside, or `--sat-vars p_v2` to run it alone.
