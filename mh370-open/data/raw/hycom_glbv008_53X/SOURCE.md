# HYCOM GLBv0.08 expt_53.X global reanalysis — surface currents subset

- URLs: https://tds.hycom.org/thredds/dodsC/GLBv0.08/expt_53.X/data/2014 and https://tds.hycom.org/thredds/dodsC/GLBv0.08/expt_53.X/data/2015 (OPeNDAP, anonymous, no sign-up)
- Product: HYCOM + NCODA Global 1/12 deg Reanalysis (GLBv0.08, experiment 53.X), 3-hourly
  snapshots; https://www.hycom.org/data/glbv0pt08/expt-53pt-x . HYCOM data are freely available
  (https://www.hycom.org/data); acknowledge the HYCOM consortium / NRL.
- Subset retrieved 2026-11-05 by scripts/drift_hycom_download.py: water_u,
  water_v at depth index 0 (0 m), the snapshot nearest 12:00 UTC each day, 2014-03-08 .. 2015-08-31,
  lat 50S-5N, lon 20-120E, every 3rd grid point. Values int16, scale 0.001 m/s,
  fill -30000, exactly as served.
- Used only for the 2014-15 particle-tracking cross-check of the flaperon arrival.
