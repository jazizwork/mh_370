# NOAA Global Drifter Program — 6-hourly interpolated dataset (ragged array, zarr)

- URL: https://noaa-oar-hourly-gdp-pds.s3.amazonaws.com/experimental/gdp6h_ragged_may25.zarr
  (NOAA Open Data Dissemination / AWS open-data bucket `noaa-oar-hourly-gdp-pds`, prefix
  `experimental/gdp6h_ragged_may25.zarr`; anonymous HTTPS, no sign-up.)
- Dataset: Lumpkin, R.; Centurioni, L. (2019). NOAA Global Drifter Program quality-controlled
  6-hour interpolated data from ocean surface drifting buoys. NOAA NCEI.
  https://doi.org/10.25921/7ntx-z961 . Version "May 2025" (time coverage 1979-02-15 .. 2025-06-12,
  28,728 trajectories, 48,887,074 observations).
- Licence: "freely available" (dataset attribute); NOAA data, public domain in the US.
- Retrieved: 2026-11-05 by scripts/drift_download.py.
- Mirrored variables (raw zarr chunks, not modified): lat, lon, time, drogue_status, ve, vn, id, rowsize, typedeath, drogue_lost_date, deploy_date, end_date, end_lat, end_lon, start_date, start_lat, start_lon, typebuoy.
  `.zmetadata` is the full consolidated metadata of the remote store (lists variables not mirrored);
  open with `xr.open_zarr(path, consolidated=False)`.
- Drogue status per observation: 1 = drogued, 0 = undrogued (drogue lost), from GDP metadata.
- typedeath: 0 alive, 1 ran aground, 2 picked up, 3 stopped transmitting, 4 sporadic, 5 bad
  batteries, 6 inactive.
