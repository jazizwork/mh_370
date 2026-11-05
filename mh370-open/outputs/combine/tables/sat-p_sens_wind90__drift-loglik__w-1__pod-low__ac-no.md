# Ranked blocks: `sat=p_sens_wind90|drift=loglik|w=1|pod=low|ac=no`

## Any ground (re-search of previously searched seabed allowed)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 37.91S 88.68E | 37.36S-38.46S | 87.80-89.54E | +2 to +32 | 5,039 | 0.4424 | 0.3982 | 100% | 0.4518 |
| 7,500 | 1 | 37.91S 88.68E | 37.27S-38.55S | 87.67-89.67E | -2 to +38 | 7,521 | 0.5794 | 0.5215 | 100% | 0.5917 |
| 15,000 | 1 | 37.91S 88.69E | 37.02S-38.78S | 87.32-90.03E | -12 to +48 | 15,042 | 0.8042 | 0.7238 | 100% | 0.8212 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.

## Essentially unsearched ground (<= 10% of block previously searched)

| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | posterior mass | P(success) @POD 0.90 | previously searched | prior mass |
|---|---|---|---|---|---|---|---|---|---|---|
| 5,000 | 1 | 38.69S 89.03E | 38.12S-39.24S | 88.13-89.92E | +90 to +120 | 5,109 | 0.0125 | 0.0113 | 4% | 0.0021 |
| 7,500 | 1 | 38.69S 89.07E | 38.04S-39.34S | 88.04-90.08E | +88 to +128 | 7,629 | 0.0154 | 0.0138 | 8% | 0.0028 |
| 15,000 | 1 | 38.71S 89.18E | 37.81S-39.60S | 87.78-90.55E | +85 to +145 | 15,275 | 0.0196 | 0.0176 | 9% | 0.0038 |

n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.
