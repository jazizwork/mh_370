"""Download an ERA5 subset (u, v, T on pressure levels) for the MH370 night from the
Google ARCO-ERA5 public Zarr store (anonymous access, no sign-up).

Store: gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3
Subset: 2014-03-07 16:00 .. 2014-03-08 01:00 UTC hourly, levels 150-350 hPa,
        lat 45S..15N, lon 75..115E (0.25 deg).
Output: data/raw/era5_arco/era5_mh370_uvT.nc  (+ SOURCE.md written by hand/below)

Run:  .venv/bin/python -I scripts/satcom_get_era5.py
"""
import datetime as dt
import pathlib
import sys

import gcsfs
import numpy as np
import xarray as xr

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "era5_arco"
STORE = "gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3"
VARS = ["u_component_of_wind", "v_component_of_wind", "temperature"]
LEVELS = [150, 175, 200, 225, 250, 300, 350]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fs = gcsfs.GCSFileSystem(token="anon")
    ds = xr.open_zarr(fs.get_mapper(STORE), consolidated=True, chunks=None)
    ds = ds[VARS].sel(time=slice("2014-03-07T16:00", "2014-03-08T01:00"),
                      level=LEVELS,
                      latitude=slice(15.0, -45.0), longitude=slice(75.0, 115.0))
    print(ds, flush=True)
    parts = []
    for i in range(ds.sizes["time"]):
        t0 = dt.datetime.now()
        parts.append(ds.isel(time=[i]).load())
        print(f"time {str(ds.time.values[i])[:16]} loaded in {(dt.datetime.now()-t0).total_seconds():.1f}s",
              flush=True)
    sub = xr.concat(parts, dim="time")
    sub.attrs.update(source="ARCO-ERA5 " + STORE, retrieved_utc=dt.datetime.utcnow().isoformat())
    enc = {v: {"compression": "gzip", "compression_opts": 4} for v in VARS}
    sub.to_netcdf(OUT / "era5_mh370_uvT.nc", engine="h5netcdf", encoding=enc)
    print("wrote", OUT / "era5_mh370_uvT.nc")


if __name__ == "__main__":
    sys.exit(main())
