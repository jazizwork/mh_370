# SYNTHETIC self-test of the combiner - NOT MH370 RESULTS

> Every input in this directory and in `data/derived/selftest_SYNTHETIC/` is a synthetic placeholder (Gaussian along the 7th arc for satcom, flat/gradient drift, a rectangular fake search, a fake acoustic patch). The maps and tables here demonstrate that the combiner runs; they say nothing about where MH370 is.

Run 2026-11-05 21:33, 50/50 checks passed, 198s.

| check | result | detail |
|---|---|---|
| T1 posterior normalised | PASS |  |
| T2 flat drift (NaN outside band) leaves posterior unchanged, w=0.5 | PASS | max diff 0.0e+00 |
| T3 additive constant in loglik is irrelevant, w=0.5 | PASS | max diff 0.0e+00 |
| T2 flat drift (NaN outside band) leaves posterior unchanged, w=1.0 | PASS | max diff 0.0e+00 |
| T3 additive constant in loglik is irrelevant, w=1.0 | PASS | max diff 0.0e+00 |
| T3b NaN-mass flag reported | PASS | prior mass in NaN drift cells = 1.52e-23 |
| T4 P(missed in searched ground) matches analytic m(1-d)/(1-dm) | PASS | 0.050360 vs 0.050360 (prior mass in box 0.3465) |
| T4b missed fraction equals posterior mass in searched cells | PASS | 0.050359743 |
| T5 gradient drift moves posterior monotonically with w | PASS | mean s: 626 / 470 / 314 km |
| T5b exact tempering: log(p1/p0) - 2 log(p.5/p0) is constant | PASS | ptp 3.6e-15 |
| T6 best 7,500 km2 box recovers the planted 100x75 km block | PASS | overlap 0.95, box s 142..238, n 18..98, area 7670 |
| T6b area of box within 3% of budget | PASS | 7670 km2 |
| T6c second box is disjoint and smaller | PASS |  |
| T6d unsearched-only ranking: block <= 10% previously searched and avoids the searched block | PASS | searched fraction 0.100, nominal overlap 0.110 |
| T7 benchmarks: HDR >= blob-ish >= box (within resampling error) | PASS | hdr 0.873, blob 0.873, box 0.833 |
| T7b arc-raster resampling conserves mass within 1% | PASS | 0.9226 |
| T8 wrong grid rejected | PASS |  |
| T9 real search_pod.nc: values in [0,1] | PASS |  |
| T9b real search_pod.nc: pod_low <= pod <= pod_high (cells violating by >1e-3) | PASS | 0.0e+00 / 0.0e+00 |
| T9c real search_pod.nc: pod <= searched_frac | PASS |  |
| T10 end-to-end runner (synthetic, with acoustic) completes | PASS | rc=0 missing=[] |
| T10b item-level drift variables excluded | PASS |  |
| T10c acoustic scenarios produced | PASS |  |
| T10d top block avoids the fully searched synthetic box | PASS |  |
| T10e acoustic patch attracts a block when included | PASS | centres [-27.28, -27.28, -27.2, -27.2, -27.02, -27.02] |
| TM1 broad_arc: finite, non-negative, sums to 1 | PASS | sum 1.00000000 |
| TM1b broad_arc: uniform in 7th-arc latitude (1-deg bins 41-21 S within 5%) | PASS | max dev 0.010 |
| TM1 broad_wide: finite, non-negative, sums to 1 | PASS | sum 1.00000000 |
| TM1b broad_wide: uniform in 7th-arc latitude (1-deg bins 41-21 S within 5%) | PASS | max dev 0.005 |
| TM1 broad_arc_lnavctt: finite, non-negative, sums to 1 | PASS | sum 1.00000000 |
| TM1b broad_arc_lnavctt: uniform in 7th-arc latitude (1-deg bins 41-21 S within 5%) | PASS | max dev 0.012 |
| TM1c broad_wide flat within +/-125 km of the arc and ~0 beyond 175 km | PASS | max dev 0.005, mass beyond 0.0000 |
| TM2 eps=0 == satellite-only combiner, eps=1 == broad-only (w=0.0) | PASS | max diff 2.7e-20 |
| TM2 eps=0 == satellite-only combiner, eps=1 == broad-only (w=0.5) | PASS | max diff 2.2e-19 |
| TM3 sat on searched ground: eps 0.05 -> analytic posterior weight | PASS | eps_post 0.3333 (analytic 0.3333); P(null|sat) 0.100, P(null|broad) 0.950, BF 0.105 |
| TM3 sat on searched ground: eps 0.1 -> analytic posterior weight | PASS | eps_post 0.5135 (analytic 0.5135); P(null|sat) 0.100, P(null|broad) 0.950, BF 0.105 |
| TM3 sat on searched ground: eps 0.3 -> analytic posterior weight | PASS | eps_post 0.8028 (analytic 0.8028); P(null|sat) 0.100, P(null|broad) 0.950, BF 0.105 |
| TM3b posterior broad weight rises monotonically with past POD (0.5 / 0.9 / 0.99) | PASS | 0.178 / 0.514 / 0.913 |
| TM4 sat on unsearched ground: null result lowers the broad weight | PASS | eps_post 0.0955, P(null|broad) 0.950 |
| TM5 mixture prior/posterior and component posteriors each sum to 1 | PASS | 1.0000000000 1.0000000000 1.0000000000 1.0000000000 1.0000000000 1.0000000000 |
| TM5b posterior == normalise(((1-eps) p_sat + eps p_broad) exp(w ll) (1-pod)) and == weighted components | PASS | max diff 2.2e-19 |
| TM5c P(unsearched | mixture) == weighted component values | PASS |  |
| TM6 weight after drift = eps Z_b / ((1-eps) Z_s + eps Z_b); additive constant in loglik irrelevant | PASS | eps_drift 0.22756 (direct 0.22756); BF drift 0.377 |
| TM7 block mass decomposes into sat-conditional and broad-conditional parts; box_mass reproduces it | PASS | max dev 9.7e-17 / 9.7e-17 |
| TM8 broad_arc kernel constants == scripts/satcom_posterior.py | PASS | {'w_glide': 0.2, 'unc': (5.0, 7.0), 'glide': (120.0, 15.0), 'smooth': 1.0} |
| TM9 end-to-end mixture runner (synthetic) completes | PASS | rc=0 missing=[] |
| TM9b p_v2 auto-detected and run alongside p | PASS |  |
| TM9c runner: weight rises when sat is on searched ground (p), falls when unsearched (p_v2) | PASS | p: [0.514, 0.803], p_v2: [0.095, 0.289] |
| TM9d every ranked block: mixture mass = weighted conditional masses | PASS | max dev 8.1e-06 |
| TM9e requesting a missing satellite variable fails cleanly (exit 3) | PASS | rc=3 |
