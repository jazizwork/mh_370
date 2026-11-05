# Ranked blocks: `sat=p_mode_LNAV|drift=none|w=0|pod=low|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 39.85S 84.96E | 39.41S-40.29S | 84.21-85.71E | +2 to +42 | 5,018 | 0.1584 | 0.1425 | 3% | 0.0508 |
| 7,500 | 1 | 39.12S 86.51E | 38.11S-40.07S | 84.57-88.37E | +12 to +32 | 7,527 | 0.2156 | 0.1941 | 76% | 0.2994 |
| 15,000 | 1 | 39.14S 86.48E | 37.76S-40.40S | 83.88-88.96E | +8 to +38 | 15,054 | 0.3715 | 0.3343 | 69% | 0.5003 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 39.85S 84.96E | 39.41S-40.29S | 84.21-85.71E | +2 to +42 | 5,018 | 0.1584 | 0.1425 | 3% | 0.0508 |
| 7,500 | 1 | 39.93S 84.85E | 39.39S-40.45S | 83.94-85.76E | +0 to +50 | 7,530 | 0.1940 | 0.1746 | 3% | 0.0619 |
| 15,000 | 1 | 40.01S 84.71E | 39.25S-40.76S | 83.40-86.01E | -8 to +62 | 15,116 | 0.2512 | 0.2261 | 9% | 0.0931 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
