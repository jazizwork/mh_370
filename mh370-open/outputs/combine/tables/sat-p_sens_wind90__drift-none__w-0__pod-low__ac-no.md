# Ranked blocks: `sat=p_sens_wind90|drift=none|w=0|pod=low|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.28S 88.13E | 37.73S-38.82S | 87.24-89.01E | +8 to +38 | 5,043 | 0.1541 | 0.1387 | 100% | 0.2833 |
| 7,500 | 1 | 38.31S 88.07E | 37.54S-39.05S | 86.78-89.33E | +8 to +38 | 7,527 | 0.2088 | 0.1879 | 100% | 0.3837 |
| 15,000 | 1 | 38.87S 87.02E | 37.46S-40.16S | 84.44-89.47E | +8 to +38 | 15,054 | 0.3418 | 0.3076 | 80% | 0.5038 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 39.87S 84.97E | 39.43S-40.31S | 84.22-85.73E | +5 to +45 | 5,020 | 0.1075 | 0.0968 | 3% | 0.0314 |
| 7,500 | 1 | 39.91S 84.87E | 39.38S-40.44S | 83.96-85.78E | +0 to +50 | 7,530 | 0.1312 | 0.1181 | 4% | 0.0391 |
| 15,000 | 1 | 40.03S 84.72E | 39.27S-40.78S | 83.42-86.02E | -5 to +65 | 15,122 | 0.1669 | 0.1502 | 9% | 0.0565 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
