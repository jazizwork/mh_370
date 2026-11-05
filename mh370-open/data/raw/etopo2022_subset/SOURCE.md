# ETOPO 2022 bathymetry subset

Retrieved 2026-11-05 by `scripts/acoustic_download_bathy.py` via anonymous OPeNDAP (ASCII) from
NOAA NCEI THREDDS:
https://www.ngdc.noaa.gov/thredds/dodsC/global/ETOPO2022/60s/60s_bed_elev_netcdf/ETOPO_2022_v1_60s_N90W180_bed.nc

- Product: ETOPO 2022 v1, 60 arc-second, bedrock elevation (m, positive up).
  NOAA National Centers for Environmental Information (2022), doi:10.25921/fd45-gt74.
- Subset: 55°S–12°N, 50°E–150°E, decimated to every 2nd sample (2 arc-min, ~3.7 km).
- File: `etopo2022_2min_55S12N_50E150E.nc` (var `z`).
- Licence: US Government work, public domain / no restrictions (NOAA NCEI).
- Use: qualitative SOFAR-path blockage checks (workstream D). Decimation can miss narrow
  seamount summits; blockage results are indicative only.
