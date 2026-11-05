# [SYNTHETIC] Combined posterior and ranked search blocks

> **SYNTHETIC INPUTS - these numbers are NOT results about MH370.** They exist only to test the combiner.

Generated 2026-11-05 21:32 by `scripts/combine_run.py`. Inputs:

- satcom: `satcom_posterior_SYNTHETIC.nc` present=True (modified Thu Nov  5 21:30:20 2026)
- drift: `drift_loglik_SYNTHETIC.nc` present=True (modified Thu Nov  5 21:30:20 2026)
- acoustic: `acoustic_loglik_SYNTHETIC.nc` present=True (modified Thu Nov  5 21:30:20 2026)
- pod: `search_pod_SYNTHETIC.nc` present=True (modified Thu Nov  5 21:30:20 2026)

posterior ∝ satcom_p × exp(w·drift_loglik) × (1 − pod); POD_new for a future search = 0.9.

## Headline satcom scenario `p`: searched vs unsearched

| w | POD bound | prior mass in searched ground | P(past searches would have found it) | P(wreck in searched ground, missed) | P(wreck in unsearched ground) | drift prior mass in NaN cells |
|---|---|---|---|---|---|---|
| 0 | best | 0.347 | 0.312 | 0.050 | 0.950 | 0.0000 |
| 0 | low | 0.347 | 0.277 | 0.096 | 0.904 | 0.0000 |
| 0 | high | 0.347 | 0.329 | 0.026 | 0.974 | 0.0000 |
| 0.5 | best | 0.347 | 0.312 | 0.050 | 0.950 | 0.0000 |
| 0.5 | low | 0.347 | 0.277 | 0.096 | 0.904 | 0.0000 |
| 0.5 | high | 0.347 | 0.329 | 0.026 | 0.974 | 0.0000 |
| 1 | best | 0.347 | 0.312 | 0.050 | 0.950 | 0.0000 |
| 1 | low | 0.347 | 0.277 | 0.096 | 0.904 | 0.0000 |
| 1 | high | 0.347 | 0.329 | 0.026 | 0.974 | 0.0000 |

## Top blocks, 5,000 km², re-search of previously searched ground allowed (satcom `p`, POD best)


**w = 0**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 28.63S 99.28E | 28.13S-29.13S | 98.78-99.78E | -25 to +25 | 5,000 | 0.1026 | 0.0923 | 1% | 0.0711 |
| 5,000 | 2 | 31.35S 96.89E | 30.86S-31.84S | 96.35-97.42E | -25 to +25 | 5,000 | 0.1017 | 0.0916 | 1% | 0.0705 |
| 5,000 | 3 | 27.94S 99.82E | 27.47S-28.41S | 99.32-100.31E | -30 to +30 | 5,100 | 0.0714 | 0.0643 | 0% | 0.0491 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 5,000 km²: best free-form contiguous block captures 0.1052; highest-density cells (non-contiguous) 0.1146.


**w = 0.5**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 28.63S 99.28E | 28.13S-29.13S | 98.78-99.78E | -25 to +25 | 5,000 | 0.1026 | 0.0923 | 1% | 0.0711 |
| 5,000 | 2 | 31.35S 96.89E | 30.86S-31.84S | 96.35-97.42E | -25 to +25 | 5,000 | 0.1017 | 0.0916 | 1% | 0.0705 |
| 5,000 | 3 | 27.94S 99.82E | 27.47S-28.41S | 99.32-100.31E | -30 to +30 | 5,100 | 0.0714 | 0.0643 | 0% | 0.0491 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 5,000 km²: best free-form contiguous block captures 0.1052; highest-density cells (non-contiguous) 0.1146.


**w = 1**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 28.63S 99.28E | 28.13S-29.13S | 98.78-99.78E | -25 to +25 | 5,000 | 0.1026 | 0.0923 | 1% | 0.0711 |
| 5,000 | 2 | 31.35S 96.89E | 30.86S-31.84S | 96.35-97.42E | -25 to +25 | 5,000 | 0.1017 | 0.0916 | 1% | 0.0705 |
| 5,000 | 3 | 27.94S 99.82E | 27.47S-28.41S | 99.32-100.31E | -30 to +30 | 5,100 | 0.0714 | 0.0643 | 0% | 0.0491 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 5,000 km²: best free-form contiguous block captures 0.1052; highest-density cells (non-contiguous) 0.1146.


## Top blocks, 7,500 km², re-search of previously searched ground allowed (satcom `p`, POD best)


**w = 0**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 7,500 | 1 | 28.44S 99.43E | 27.76S-29.13S | 98.78-100.07E | -25 to +25 | 7,500 | 0.1421 | 0.1279 | 0% | 0.0982 |
| 7,500 | 2 | 31.52S 96.72E | 30.86S-32.18S | 96.00-97.42E | -25 to +25 | 7,500 | 0.1408 | 0.1267 | 0% | 0.0973 |
| 7,500 | 3 | 27.41S 100.21E | 26.79S-28.03S | 99.61-100.80E | -30 to +30 | 7,500 | 0.0744 | 0.0669 | 0% | 0.0512 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 7,500 km²: best free-form contiguous block captures 0.1455; highest-density cells (non-contiguous) 0.1640.


**w = 0.5**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 7,500 | 1 | 28.44S 99.43E | 27.76S-29.13S | 98.78-100.07E | -25 to +25 | 7,500 | 0.1421 | 0.1279 | 0% | 0.0982 |
| 7,500 | 2 | 31.52S 96.72E | 30.86S-32.18S | 96.00-97.42E | -25 to +25 | 7,500 | 0.1408 | 0.1267 | 0% | 0.0973 |
| 7,500 | 3 | 27.41S 100.21E | 26.79S-28.03S | 99.61-100.80E | -30 to +30 | 7,500 | 0.0744 | 0.0669 | 0% | 0.0512 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 7,500 km²: best free-form contiguous block captures 0.1455; highest-density cells (non-contiguous) 0.1640.


**w = 1**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 7,500 | 1 | 28.44S 99.43E | 27.76S-29.13S | 98.78-100.07E | -25 to +25 | 7,500 | 0.1421 | 0.1279 | 0% | 0.0982 |
| 7,500 | 2 | 31.52S 96.72E | 30.86S-32.18S | 96.00-97.42E | -25 to +25 | 7,500 | 0.1408 | 0.1267 | 0% | 0.0973 |
| 7,500 | 3 | 27.41S 100.21E | 26.79S-28.03S | 99.61-100.80E | -30 to +30 | 7,500 | 0.0744 | 0.0669 | 0% | 0.0512 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 7,500 km²: best free-form contiguous block captures 0.1455; highest-density cells (non-contiguous) 0.1640.


## Top blocks, 15,000 km², re-search of previously searched ground allowed (satcom `p`, POD best)


**w = 0**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 15,000 | 1 | 28.22S 99.60E | 27.24S-29.20S | 98.68-100.50E | -35 to +35 | 15,050 | 0.2307 | 0.2076 | 1% | 0.1608 |
| 15,000 | 2 | 31.75S 96.50E | 30.80S-32.69S | 95.47-97.51E | -35 to +35 | 15,050 | 0.2282 | 0.2054 | 0% | 0.1576 |
| 15,000 | 3 | 30.24S 98.51E | 27.40S-32.92S | 95.90-100.81E | +35 to +55 | 15,108 | 0.0947 | 0.0852 | 9% | 0.0771 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 15,000 km²: best free-form contiguous block captures 0.2356; highest-density cells (non-contiguous) 0.2892.


**w = 0.5**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 15,000 | 1 | 28.22S 99.60E | 27.24S-29.20S | 98.68-100.50E | -35 to +35 | 15,050 | 0.2307 | 0.2076 | 1% | 0.1608 |
| 15,000 | 2 | 31.75S 96.50E | 30.80S-32.69S | 95.47-97.51E | -35 to +35 | 15,050 | 0.2282 | 0.2054 | 0% | 0.1576 |
| 15,000 | 3 | 30.24S 98.51E | 27.40S-32.92S | 95.90-100.81E | +35 to +55 | 15,108 | 0.0947 | 0.0852 | 9% | 0.0771 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 15,000 km²: best free-form contiguous block captures 0.2356; highest-density cells (non-contiguous) 0.2892.


**w = 1**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 15,000 | 1 | 28.22S 99.60E | 27.24S-29.20S | 98.68-100.50E | -35 to +35 | 15,050 | 0.2307 | 0.2076 | 1% | 0.1608 |
| 15,000 | 2 | 31.75S 96.50E | 30.80S-32.69S | 95.47-97.51E | -35 to +35 | 15,050 | 0.2282 | 0.2054 | 0% | 0.1576 |
| 15,000 | 3 | 30.24S 98.51E | 27.40S-32.92S | 95.90-100.81E | +35 to +55 | 15,108 | 0.0947 | 0.0852 | 9% | 0.0771 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

Benchmarks for 15,000 km²: best free-form contiguous block captures 0.2356; highest-density cells (non-contiguous) 0.2892.


## Top blocks, 5,000 km², essentially unsearched ground only (<= 10% previously searched) (satcom `p`, POD best)


**w = 0**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 28.63S 99.28E | 28.13S-29.13S | 98.78-99.78E | -25 to +25 | 5,000 | 0.1026 | 0.0923 | 1% | 0.0711 |
| 5,000 | 2 | 31.35S 96.89E | 30.86S-31.84S | 96.35-97.42E | -25 to +25 | 5,000 | 0.1017 | 0.0916 | 1% | 0.0705 |
| 5,000 | 3 | 27.94S 99.82E | 27.47S-28.41S | 99.32-100.31E | -30 to +30 | 5,100 | 0.0714 | 0.0643 | 0% | 0.0491 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


**w = 0.5**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 28.63S 99.28E | 28.13S-29.13S | 98.78-99.78E | -25 to +25 | 5,000 | 0.1026 | 0.0923 | 1% | 0.0711 |
| 5,000 | 2 | 31.35S 96.89E | 30.86S-31.84S | 96.35-97.42E | -25 to +25 | 5,000 | 0.1017 | 0.0916 | 1% | 0.0705 |
| 5,000 | 3 | 27.94S 99.82E | 27.47S-28.41S | 99.32-100.31E | -30 to +30 | 5,100 | 0.0714 | 0.0643 | 0% | 0.0491 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


**w = 1**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 28.63S 99.28E | 28.13S-29.13S | 98.78-99.78E | -25 to +25 | 5,000 | 0.1026 | 0.0923 | 1% | 0.0711 |
| 5,000 | 2 | 31.35S 96.89E | 30.86S-31.84S | 96.35-97.42E | -25 to +25 | 5,000 | 0.1017 | 0.0916 | 1% | 0.0705 |
| 5,000 | 3 | 27.94S 99.82E | 27.47S-28.41S | 99.32-100.31E | -30 to +30 | 5,100 | 0.0714 | 0.0643 | 0% | 0.0491 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


## Top blocks, 7,500 km², essentially unsearched ground only (<= 10% previously searched) (satcom `p`, POD best)


**w = 0**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 7,500 | 1 | 28.44S 99.43E | 27.76S-29.13S | 98.78-100.07E | -25 to +25 | 7,500 | 0.1421 | 0.1279 | 0% | 0.0982 |
| 7,500 | 2 | 31.52S 96.72E | 30.86S-32.18S | 96.00-97.42E | -25 to +25 | 7,500 | 0.1408 | 0.1267 | 0% | 0.0973 |
| 7,500 | 3 | 27.41S 100.21E | 26.79S-28.03S | 99.61-100.80E | -30 to +30 | 7,500 | 0.0744 | 0.0669 | 0% | 0.0512 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


**w = 0.5**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 7,500 | 1 | 28.44S 99.43E | 27.76S-29.13S | 98.78-100.07E | -25 to +25 | 7,500 | 0.1421 | 0.1279 | 0% | 0.0982 |
| 7,500 | 2 | 31.52S 96.72E | 30.86S-32.18S | 96.00-97.42E | -25 to +25 | 7,500 | 0.1408 | 0.1267 | 0% | 0.0973 |
| 7,500 | 3 | 27.41S 100.21E | 26.79S-28.03S | 99.61-100.80E | -30 to +30 | 7,500 | 0.0744 | 0.0669 | 0% | 0.0512 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


**w = 1**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 7,500 | 1 | 28.44S 99.43E | 27.76S-29.13S | 98.78-100.07E | -25 to +25 | 7,500 | 0.1421 | 0.1279 | 0% | 0.0982 |
| 7,500 | 2 | 31.52S 96.72E | 30.86S-32.18S | 96.00-97.42E | -25 to +25 | 7,500 | 0.1408 | 0.1267 | 0% | 0.0973 |
| 7,500 | 3 | 27.41S 100.21E | 26.79S-28.03S | 99.61-100.80E | -30 to +30 | 7,500 | 0.0744 | 0.0669 | 0% | 0.0512 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


## Top blocks, 15,000 km², essentially unsearched ground only (<= 10% previously searched) (satcom `p`, POD best)


**w = 0**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 15,000 | 1 | 28.22S 99.60E | 27.24S-29.20S | 98.68-100.50E | -35 to +35 | 15,050 | 0.2307 | 0.2076 | 1% | 0.1608 |
| 15,000 | 2 | 31.75S 96.50E | 30.80S-32.69S | 95.47-97.51E | -35 to +35 | 15,050 | 0.2282 | 0.2054 | 0% | 0.1576 |
| 15,000 | 3 | 30.24S 98.51E | 27.40S-32.92S | 95.90-100.81E | +35 to +55 | 15,108 | 0.0947 | 0.0852 | 9% | 0.0771 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


**w = 0.5**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 15,000 | 1 | 28.22S 99.60E | 27.24S-29.20S | 98.68-100.50E | -35 to +35 | 15,050 | 0.2307 | 0.2076 | 1% | 0.1608 |
| 15,000 | 2 | 31.75S 96.50E | 30.80S-32.69S | 95.47-97.51E | -35 to +35 | 15,050 | 0.2282 | 0.2054 | 0% | 0.1576 |
| 15,000 | 3 | 30.24S 98.51E | 27.40S-32.92S | 95.90-100.81E | +35 to +55 | 15,108 | 0.0947 | 0.0852 | 9% | 0.0771 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


**w = 1**

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 15,000 | 1 | 28.22S 99.60E | 27.24S-29.20S | 98.68-100.50E | -35 to +35 | 15,050 | 0.2307 | 0.2076 | 1% | 0.1608 |
| 15,000 | 2 | 31.75S 96.50E | 30.80S-32.69S | 95.47-97.51E | -35 to +35 | 15,050 | 0.2282 | 0.2054 | 0% | 0.1576 |
| 15,000 | 3 | 30.24S 98.51E | 27.40S-32.92S | 95.90-100.81E | +35 to +55 | 15,108 | 0.0947 | 0.0852 | 9% | 0.0771 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.


## Posterior mass in named areas (satcom `p`, drift `loglik`)

| area | w=0 low | w=0 best | w=0 high | w=0.5 low | w=0.5 best | w=0.5 high | w=1 low | w=1 best | w=1 high |
|---|---|---|---|---|---|---|---|---|---|
| OI contract remainder: NW strip (slide, 6,902 km2) | 0.0010 | 0.0011 | 0.0011 | 0.0010 | 0.0011 | 0.0011 | 0.0010 | 0.0011 | 0.0011 |
| OI contract remainder: NW strip calibrated to 7,428 km2 | 0.0011 | 0.0011 | 0.0011 | 0.0011 | 0.0011 | 0.0011 | 0.0011 | 0.0011 | 0.0011 |
| OI 2025 contract area (both strips, slide) | 0.0013 | 0.0014 | 0.0014 | 0.0013 | 0.0014 | 0.0014 | 0.0013 | 0.0014 | 0.0014 |
| CAPTION Blelly/Marchand zone | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Ulich-Iannello 2023 70 NM glide racetrack | 0.0622 | 0.0653 | 0.0670 | 0.0622 | 0.0653 | 0.0670 | 0.0622 | 0.0653 | 0.0670 |
| 50 km radius around UGIB LEP (Ulich/Godfrey/Iannello/Banks 2020) | 0.0077 | 0.0081 | 0.0083 | 0.0077 | 0.0081 | 0.0083 | 0.0077 | 0.0081 | 0.0083 |
| 50 km radius around CSIRO drift 2017 | 0.0005 | 0.0006 | 0.0006 | 0.0005 | 0.0006 | 0.0006 | 0.0005 | 0.0006 | 0.0006 |
| 50 km radius around WSPR (Godfrey 2024) | 0.0130 | 0.0136 | 0.0140 | 0.0130 | 0.0136 | 0.0140 | 0.0130 | 0.0136 | 0.0140 |
| 50 km radius around Ulich & Iannello drift 2023 (34.0S on arc) | 0.0107 | 0.0112 | 0.0115 | 0.0107 | 0.0112 | 0.0115 | 0.0107 | 0.0112 | 0.0115 |
| 50 km radius around Kadri 306 deg bearing x 7th arc | 0.0122 | 0.0129 | 0.0132 | 0.0122 | 0.0129 | 0.0132 | 0.0122 | 0.0129 | 0.0132 |
| 50 km radius around Stead 246.9 deg timing-consistent | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## All satcom scenarios: rank-1 block, mode 'any' (drift `loglik`)

| satcom | w | POD | P(null search given scenario) | P(missed in searched) | top 5k centre | mass | P(succ) | top 7.5k centre | mass | P(succ) | top 15k centre | mass | P(succ) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p | 0 | best | 0.688 | 0.050 | 28.63S 99.28E | 0.1026 | 0.0923 | 28.44S 99.43E | 0.1421 | 0.1279 | 28.22S 99.60E | 0.2307 | 0.2076 |
| p | 0 | low | 0.723 | 0.096 | 28.63S 99.28E | 0.0977 | 0.0880 | 28.44S 99.43E | 0.1353 | 0.1218 | 28.22S 99.60E | 0.2199 | 0.1979 |
| p | 0 | high | 0.671 | 0.026 | 28.63S 99.28E | 0.1052 | 0.0947 | 28.44S 99.43E | 0.1457 | 0.1311 | 28.20S 99.62E | 0.2366 | 0.2129 |
| p | 0.5 | best | 0.688 | 0.050 | 28.63S 99.28E | 0.1026 | 0.0923 | 28.44S 99.43E | 0.1421 | 0.1279 | 28.22S 99.60E | 0.2307 | 0.2076 |
| p | 0.5 | low | 0.723 | 0.096 | 28.63S 99.28E | 0.0977 | 0.0880 | 28.44S 99.43E | 0.1353 | 0.1218 | 28.22S 99.60E | 0.2199 | 0.1979 |
| p | 0.5 | high | 0.671 | 0.026 | 28.63S 99.28E | 0.1052 | 0.0947 | 28.44S 99.43E | 0.1457 | 0.1311 | 28.20S 99.62E | 0.2366 | 0.2129 |
| p | 1 | best | 0.688 | 0.050 | 28.63S 99.28E | 0.1026 | 0.0923 | 28.44S 99.43E | 0.1421 | 0.1279 | 28.22S 99.60E | 0.2307 | 0.2076 |
| p | 1 | low | 0.723 | 0.096 | 28.63S 99.28E | 0.0977 | 0.0880 | 28.44S 99.43E | 0.1353 | 0.1218 | 28.22S 99.60E | 0.2199 | 0.1979 |
| p | 1 | high | 0.671 | 0.026 | 28.63S 99.28E | 0.1052 | 0.0947 | 28.44S 99.43E | 0.1457 | 0.1311 | 28.20S 99.62E | 0.2366 | 0.2129 |
| p_south | 0 | best | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0 | low | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0 | high | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0.5 | best | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0.5 | low | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0.5 | high | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 1 | best | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 1 | low | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 1 | high | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_glide | 0 | best | 0.881 | 0.015 | 30.32S 98.61E | 0.0303 | 0.0273 | 30.31S 98.62E | 0.0442 | 0.0398 | 30.32S 98.64E | 0.0817 | 0.0735 |
| p_glide | 0 | low | 0.895 | 0.029 | 30.32S 98.61E | 0.0298 | 0.0269 | 30.31S 98.62E | 0.0435 | 0.0392 | 30.32S 98.64E | 0.0806 | 0.0726 |
| p_glide | 0 | high | 0.875 | 0.008 | 30.32S 98.61E | 0.0305 | 0.0275 | 30.31S 98.62E | 0.0445 | 0.0400 | 30.33S 98.66E | 0.0823 | 0.0740 |
| p_glide | 0.5 | best | 0.881 | 0.015 | 30.32S 98.61E | 0.0303 | 0.0273 | 30.31S 98.62E | 0.0442 | 0.0398 | 30.32S 98.64E | 0.0817 | 0.0735 |
| p_glide | 0.5 | low | 0.895 | 0.029 | 30.32S 98.61E | 0.0298 | 0.0269 | 30.31S 98.62E | 0.0435 | 0.0392 | 30.32S 98.64E | 0.0806 | 0.0726 |
| p_glide | 0.5 | high | 0.875 | 0.008 | 30.32S 98.61E | 0.0305 | 0.0275 | 30.31S 98.62E | 0.0445 | 0.0400 | 30.33S 98.66E | 0.0823 | 0.0740 |
| p_glide | 1 | best | 0.881 | 0.015 | 30.32S 98.61E | 0.0303 | 0.0273 | 30.31S 98.62E | 0.0442 | 0.0398 | 30.32S 98.64E | 0.0817 | 0.0735 |
| p_glide | 1 | low | 0.895 | 0.029 | 30.32S 98.61E | 0.0298 | 0.0269 | 30.31S 98.62E | 0.0435 | 0.0392 | 30.32S 98.64E | 0.0806 | 0.0726 |
| p_glide | 1 | high | 0.875 | 0.008 | 30.32S 98.61E | 0.0305 | 0.0275 | 30.31S 98.62E | 0.0445 | 0.0400 | 30.33S 98.66E | 0.0823 | 0.0740 |

## All satcom scenarios: rank-1 block, mode 'unsearched' (drift `loglik`)

| satcom | w | POD | P(null search given scenario) | P(missed in searched) | top 5k centre | mass | P(succ) | top 7.5k centre | mass | P(succ) | top 15k centre | mass | P(succ) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| p | 0 | best | 0.688 | 0.050 | 28.63S 99.28E | 0.1026 | 0.0923 | 28.44S 99.43E | 0.1421 | 0.1279 | 28.22S 99.60E | 0.2307 | 0.2076 |
| p | 0 | low | 0.723 | 0.096 | 28.63S 99.28E | 0.0977 | 0.0880 | 28.44S 99.43E | 0.1353 | 0.1218 | 28.22S 99.60E | 0.2199 | 0.1979 |
| p | 0 | high | 0.671 | 0.026 | 28.63S 99.28E | 0.1052 | 0.0947 | 28.44S 99.43E | 0.1457 | 0.1311 | 28.20S 99.62E | 0.2366 | 0.2129 |
| p | 0.5 | best | 0.688 | 0.050 | 28.63S 99.28E | 0.1026 | 0.0923 | 28.44S 99.43E | 0.1421 | 0.1279 | 28.22S 99.60E | 0.2307 | 0.2076 |
| p | 0.5 | low | 0.723 | 0.096 | 28.63S 99.28E | 0.0977 | 0.0880 | 28.44S 99.43E | 0.1353 | 0.1218 | 28.22S 99.60E | 0.2199 | 0.1979 |
| p | 0.5 | high | 0.671 | 0.026 | 28.63S 99.28E | 0.1052 | 0.0947 | 28.44S 99.43E | 0.1457 | 0.1311 | 28.20S 99.62E | 0.2366 | 0.2129 |
| p | 1 | best | 0.688 | 0.050 | 28.63S 99.28E | 0.1026 | 0.0923 | 28.44S 99.43E | 0.1421 | 0.1279 | 28.22S 99.60E | 0.2307 | 0.2076 |
| p | 1 | low | 0.723 | 0.096 | 28.63S 99.28E | 0.0977 | 0.0880 | 28.44S 99.43E | 0.1353 | 0.1218 | 28.22S 99.60E | 0.2199 | 0.1979 |
| p | 1 | high | 0.671 | 0.026 | 28.63S 99.28E | 0.1052 | 0.0947 | 28.44S 99.43E | 0.1457 | 0.1311 | 28.20S 99.62E | 0.2366 | 0.2129 |
| p_south | 0 | best | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0 | low | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0 | high | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0.5 | best | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0.5 | low | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 0.5 | high | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 1 | best | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 1 | low | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_south | 1 | high | 1.000 | 0.000 | 36.01S 91.38E | 0.1241 | 0.1117 | 36.00S 91.40E | 0.1789 | 0.1610 | 36.00S 91.40E | 0.3250 | 0.2925 |
| p_glide | 0 | best | 0.881 | 0.015 | 30.32S 98.61E | 0.0303 | 0.0273 | 30.31S 98.62E | 0.0442 | 0.0398 | 30.32S 98.64E | 0.0817 | 0.0735 |
| p_glide | 0 | low | 0.895 | 0.029 | 30.32S 98.61E | 0.0298 | 0.0269 | 30.31S 98.62E | 0.0435 | 0.0392 | 30.32S 98.64E | 0.0806 | 0.0726 |
| p_glide | 0 | high | 0.875 | 0.008 | 30.32S 98.61E | 0.0305 | 0.0275 | 30.31S 98.62E | 0.0445 | 0.0400 | 30.33S 98.66E | 0.0823 | 0.0740 |
| p_glide | 0.5 | best | 0.881 | 0.015 | 30.32S 98.61E | 0.0303 | 0.0273 | 30.31S 98.62E | 0.0442 | 0.0398 | 30.32S 98.64E | 0.0817 | 0.0735 |
| p_glide | 0.5 | low | 0.895 | 0.029 | 30.32S 98.61E | 0.0298 | 0.0269 | 30.31S 98.62E | 0.0435 | 0.0392 | 30.32S 98.64E | 0.0806 | 0.0726 |
| p_glide | 0.5 | high | 0.875 | 0.008 | 30.32S 98.61E | 0.0305 | 0.0275 | 30.31S 98.62E | 0.0445 | 0.0400 | 30.33S 98.66E | 0.0823 | 0.0740 |
| p_glide | 1 | best | 0.881 | 0.015 | 30.32S 98.61E | 0.0303 | 0.0273 | 30.31S 98.62E | 0.0442 | 0.0398 | 30.32S 98.64E | 0.0817 | 0.0735 |
| p_glide | 1 | low | 0.895 | 0.029 | 30.32S 98.61E | 0.0298 | 0.0269 | 30.31S 98.62E | 0.0435 | 0.0392 | 30.32S 98.64E | 0.0806 | 0.0726 |
| p_glide | 1 | high | 0.875 | 0.008 | 30.32S 98.61E | 0.0305 | 0.0275 | 30.31S 98.62E | 0.0445 | 0.0400 | 30.33S 98.66E | 0.0823 | 0.0740 |

## Drift-variant sensitivity (satcom `p`, POD best, budget 7,500 km²)

| drift variant | w | P(null search) | P(missed in searched) | top block (any) | mass | top unsearched block | mass | P(success) |
|---|---|---|---|---|---|---|---|---|
| loglik_const | 0.5 | 0.688 | 0.050 | 28.44S 99.43E | 0.1421 | 28.44S 99.43E | 0.1421 | 0.1279 |
| loglik_gradient | 0.5 | 0.738 | 0.040 | 31.67S 96.57E | 0.1860 | 31.67S 96.57E | 0.1860 | 0.1674 |
| loglik_const | 1 | 0.688 | 0.050 | 28.44S 99.43E | 0.1421 | 28.44S 99.43E | 0.1421 | 0.1279 |
| loglik_gradient | 1 | 0.845 | 0.020 | 32.17S 96.06E | 0.1731 | 32.17S 96.06E | 0.1731 | 0.1558 |
