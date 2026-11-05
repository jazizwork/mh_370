# Ranked blocks: `sat=p_sens_wideprior|drift=loglik|w=0.5|pod=low|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.09S 88.38E | 37.53S-38.63S | 87.49-89.25E | +2 to +32 | 5,039 | 0.3753 | 0.3378 | 100% | 0.4114 |
| 7,500 | 1 | 38.09S 88.38E | 37.44S-38.72S | 87.36-89.37E | -2 to +38 | 7,521 | 0.4908 | 0.4417 | 100% | 0.5380 |
| 15,000 | 1 | 38.12S 88.32E | 37.14S-39.07S | 86.73-89.86E | -8 to +42 | 15,042 | 0.6977 | 0.6279 | 100% | 0.7649 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.90S 88.65E | 38.34S-39.45S | 87.74-89.54E | +90 to +120 | 5,109 | 0.0291 | 0.0262 | 5% | 0.0051 |
| 7,500 | 1 | 38.93S 88.64E | 38.28S-39.57S | 87.60-89.66E | +88 to +128 | 7,629 | 0.0370 | 0.0333 | 8% | 0.0069 |
| 15,000 | 1 | 39.02S 88.63E | 38.13S-39.89S | 87.22-90.02E | +85 to +145 | 15,275 | 0.0520 | 0.0468 | 9% | 0.0101 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
