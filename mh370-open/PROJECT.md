# mh370-open — public-data-only reanalysis of MH370's end point

Goal: produce an honest, reproducible probability map of MH370's end point using ONLY
freely downloadable data (no applications, contracts or government requests), subtract
what has already been searched, and rank the remaining unsearched areas with coordinates.

This is an independent reanalysis. It is not authoritative; every assumption must be
written down and every major assumption must have a sensitivity run.

## Layout
```
mh370-open/
  PROJECT.md            this file (shared conventions — read first)
  pyproject.toml        package `mh370` (src/mh370), installed editable in .venv
  .venv/                python 3.12 venv: numpy scipy pandas matplotlib xarray h5netcdf obspy shapely pyproj
  external/             third-party repos (UNTRUSTED: read, don't execute without review)
    sladen_inmarsat-9m-mro/   public-domain Inmarsat log CSV, ATSB tables, ADS-B, etc.
    o-nesterov_MH370Solver/   MIT C++ BTO/BFO path solver (cross-check only)
  src/mh370/geo.py      SHARED geometry (do not edit; add your own module instead)
  src/mh370/<module>.py one module per workstream
  scripts/              runnable entry points (run as: .venv/bin/python -I scripts/x.py)
  data/raw/<source>/    downloaded data, one directory per source (UNTRUSTED)
  data/derived/         intermediate products
  outputs/<module>/     figures, tables, short markdown write-ups per module
```

## Rules
- Public data only. Free anonymous downloads preferred. Anything requiring sign-up must be
  flagged; anything requiring an application/approval is out of scope.
- Downloads go in their own new directory under data/raw/<source>/. Never run code from
  inside data/raw or external/. Run python with `-I`.
- Record provenance (URL, date retrieved, licence) in data/raw/<source>/SOURCE.md.
- Don't edit another workstream's module. src/mh370/geo.py is shared and frozen;
  if you need more geometry, put it in your own module.
- Keep runs tractable on this machine: 10 cores, 64 GB RAM, ~90 GB free disk.
  Don't download more than ~15 GB per workstream without stopping to reconsider.

## Shared facts (validated in src/mh370/geo.py)
- Time base: seconds since 2014-03-07 00:00:00 UTC (`geo.hms(h, m, s)`, h>=24 for 8 Mar).
- Satellite ECEF from ATSB Table 4 (cubic spline). BTO bias −495,679 µs.
  Geometry reproduces the ATSB KLIA gate calibration path to ~4 km and 16:29 to 0.4 km.
- 7th arc: BTO 18,400 µs (corrected) at 00:19:29.416. Sea-level arc passes
  (−25.00, 101.84), (−30.00, 98.13), (−34.23, 93.74), (−35.00, 92.77), (−38.00, 88.18).
  `geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, h_m)`.
- `geo.HANDSHAKES` lists the published BTO/BFO values used by every analysis.

## Common output grid (all modules MUST deliver on this grid)
- Regular lat/lon grid, cell centres: lat −44.000 … −16.000, lon 78.000 … 112.000, step 0.05°.
  i.e. `lat = np.round(np.arange(-44, -16 + 1e-9, 0.05), 3)`,
       `lon = np.round(np.arange(78, 112 + 1e-9, 0.05), 3)`.
  (Use `mh370.grid.common_grid()`.)
- File format: NetCDF via xarray with engine="h5netcdf", dims (lat, lon).
- Each module writes ONE primary layer to data/derived/:
  - `satcom_posterior.nc`  var `p`      — probability of end point per cell (sums to 1), plus
                                          optional scenario variables `p_<scenario>`.
  - `drift_loglik.nc`      var `loglik` — log-likelihood of the debris evidence given origin
                                          in that cell (NaN where not computed), plus
                                          sensitivity variants `loglik_<variant>`.
  - `acoustic_loglik.nc`   var `loglik` — (workstream D) log-likelihood of open acoustic
                                          evidence given impact in that cell, if any is found.
  - `search_pod.nc`        var `pod`    — probability the wreck would have been detected had it
                                          been in that cell, given all searches to date (0…1),
                                          plus `pod_low` / `pod_high` bounds.
- Each module also writes `outputs/<module>/arc_profile.csv`: values vs latitude along the
  7th arc (marginalised across the arc), for quick comparison between modules.
- Each module writes `outputs/<module>/README.md`: method, data sources with URLs,
  assumptions, validation against published results, limitations.

## Combination (workstream C owns this)
posterior ∝ satcom_p × exp(w · drift_loglik) × (1 − pod), with w ∈ {0, 0.5, 1} as a
tempering sensitivity (debris likelihoods from independent items are not truly independent).
Output: ranked unsearched areas with centroid coordinates, area (km²) and probability mass.
