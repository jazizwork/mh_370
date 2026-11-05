# Ranked blocks: `sat=p_mode_LNAV|drift=loglik|w=0.5|pod=low|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.22S 88.14E | 37.67S-38.76S | 87.25-89.02E | +2 to +32 | 5,039 | 0.3891 | 0.3502 | 100% | 0.4272 |
| 7,500 | 1 | 38.22S 88.14E | 37.58S-38.84S | 87.12-89.15E | -2 to +38 | 7,521 | 0.5038 | 0.4534 | 100% | 0.5532 |
| 15,000 | 1 | 38.22S 88.13E | 37.24S-39.17S | 86.54-89.68E | -8 to +42 | 15,042 | 0.7040 | 0.6336 | 100% | 0.7729 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 39.75S 85.06E | 39.33S-40.17S | 84.41-85.71E | -8 to +42 | 5,014 | 0.0288 | 0.0259 | 5% | 0.0052 |
| 7,500 | 1 | 39.82S 84.91E | 39.29S-40.35S | 84.00-85.81E | -8 to +42 | 7,521 | 0.0338 | 0.0304 | 10% | 0.0070 |
| 15,000 | 1 | 39.18S 88.34E | 38.29S-40.04S | 86.92-89.74E | +85 to +145 | 15,275 | 0.0456 | 0.0410 | 10% | 0.0089 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
