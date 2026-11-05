# Ranked blocks: `sat=p_mode_LNAV|drift=loglik|w=1|pod=high|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.10S 88.35E | 37.55S-38.64S | 87.47-89.23E | +2 to +32 | 5,039 | 0.2544 | 0.2290 | 100% | 0.4776 |
| 7,500 | 1 | 38.07S 88.40E | 37.43S-38.70S | 87.39-89.40E | -2 to +38 | 7,521 | 0.3279 | 0.2951 | 100% | 0.6155 |
| 15,000 | 1 | 38.46S 88.54E | 37.68S-39.25S | 87.56-89.53E | -5 to +125 | 15,421 | 0.4988 | 0.4489 | 74% | 0.5288 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.81S 88.82E | 38.25S-39.36S | 87.91-89.71E | +90 to +120 | 5,109 | 0.2333 | 0.2100 | 7% | 0.0015 |
| 7,500 | 1 | 38.83S 88.87E | 38.18S-39.47S | 87.84-89.89E | +90 to +130 | 7,632 | 0.2763 | 0.2486 | 5% | 0.0018 |
| 15,000 | 1 | 38.89S 88.91E | 37.99S-39.77S | 87.50-90.29E | +88 to +148 | 15,281 | 0.3398 | 0.3058 | 7% | 0.0024 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
