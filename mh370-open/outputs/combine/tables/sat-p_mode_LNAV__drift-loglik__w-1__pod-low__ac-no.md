# Ranked blocks: `sat=p_mode_LNAV|drift=loglik|w=1|pod=low|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.10S 88.35E | 37.55S-38.64S | 87.47-89.23E | +2 to +32 | 5,039 | 0.4700 | 0.4230 | 100% | 0.4776 |
| 7,500 | 1 | 38.07S 88.40E | 37.43S-38.70S | 87.39-89.40E | -2 to +38 | 7,521 | 0.6057 | 0.5451 | 100% | 0.6155 |
| 15,000 | 1 | 38.02S 88.44E | 37.14S-38.89S | 87.07-89.79E | -15 to +45 | 15,036 | 0.8246 | 0.7421 | 100% | 0.8380 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.83S 88.82E | 38.35S-39.31S | 88.09-89.55E | +88 to +128 | 5,086 | 0.0094 | 0.0084 | 8% | 0.0017 |
| 7,500 | 1 | 38.81S 88.86E | 38.16S-39.45S | 87.82-89.88E | +88 to +128 | 7,629 | 0.0113 | 0.0102 | 8% | 0.0020 |
| 15,000 | 1 | 38.86S 88.92E | 37.96S-39.74S | 87.51-90.30E | +85 to +145 | 15,275 | 0.0141 | 0.0127 | 9% | 0.0028 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
