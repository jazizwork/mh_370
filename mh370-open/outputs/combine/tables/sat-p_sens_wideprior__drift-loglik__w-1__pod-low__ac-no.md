# Ranked blocks: `sat=p_sens_wideprior|drift=loglik|w=1|pod=low|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 37.95S 88.57E | 37.39S-38.50S | 87.69-89.44E | +0 to +30 | 5,037 | 0.4522 | 0.4070 | 100% | 0.4611 |
| 7,500 | 1 | 37.95S 88.57E | 37.30S-38.58S | 87.56-89.56E | -5 to +35 | 7,518 | 0.5889 | 0.5300 | 100% | 0.6005 |
| 15,000 | 1 | 37.94S 88.58E | 37.05S-38.81S | 87.21-89.92E | -15 to +45 | 15,036 | 0.8108 | 0.7297 | 100% | 0.8267 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.73S 88.96E | 38.16S-39.28S | 88.06-89.85E | +90 to +120 | 5,109 | 0.0110 | 0.0099 | 5% | 0.0018 |
| 7,500 | 1 | 38.73S 89.00E | 38.08S-39.37S | 87.97-90.01E | +88 to +128 | 7,629 | 0.0134 | 0.0121 | 8% | 0.0024 |
| 15,000 | 1 | 38.78S 89.06E | 37.88S-39.66S | 87.66-90.44E | +85 to +145 | 15,275 | 0.0168 | 0.0151 | 9% | 0.0033 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
