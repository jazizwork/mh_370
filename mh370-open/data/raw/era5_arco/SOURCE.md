# ERA5 subset (ARCO-ERA5, Google public dataset)

- File: `era5_mh370_uvT.nc` (u, v wind and temperature on pressure levels)
- Source store: `gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3`
  (Google Cloud public dataset "ARCO-ERA5", anonymous read access, no sign-up;
  https://github.com/google-research/arco-era5 ,
  https://console.cloud.google.com/marketplace/product/bigquery-public-data/arco-era5)
- Underlying data: ECMWF ERA5 reanalysis (Hersbach et al. 2020, QJRMS 146:1999-2049,
  doi:10.1002/qj.3803), Copernicus Climate Change Service.
- Licence: Copernicus licence / CC-BY 4.0 terms for ERA5. Attribution: "Contains modified
  Copernicus Climate Change Service information 2026. Neither the European Commission nor
  ECMWF is responsible for any use that may be made of the Copernicus information or data it
  contains."
- Retrieved: 2026-11-05 by `scripts/satcom_get_era5.py` (log in `download.log`).
- Subset: 2014-03-07 16:00 UTC .. 2014-03-08 01:00 UTC hourly; levels 150, 175, 200, 225,
  250, 300, 350 hPa; latitude 15N..45S, longitude 75E..115E, 0.25 deg grid.
  Download volume ~2.5 GB (whole-globe chunks, one per hour/variable); stored subset 24 MB.
