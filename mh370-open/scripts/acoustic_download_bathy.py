"""Download a regional subset of NOAA ETOPO 2022 (60 arc-second bedrock elevation) via
anonymous OPeNDAP ASCII, decimated to 2 arc-minutes, and save as NetCDF.

Region: 55S-12N, 50E-150E (covers 7th arc, IMOS/IMS receivers, Carlsberg Ridge, Java).
Output: data/raw/etopo2022_subset/etopo2022_2min_55S12N_50E150E.nc  (var z, metres, +up)

Usage: .venv/bin/python -I scripts/acoustic_download_bathy.py
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "etopo2022_subset"
URL = ("https://www.ngdc.noaa.gov/thredds/dodsC/global/ETOPO2022/60s/60s_bed_elev_netcdf/"
       "ETOPO_2022_v1_60s_N90W180_bed.nc.ascii?z%5B{i0}:{s}:{i1}%5D%5B{j0}:{s}:{j1}%5D")
STRIDE = 2


def idx_lat(lat):
    return int(round((lat + 90) * 60 - 0.5))


def idx_lon(lon):
    return int(round((lon + 180) * 60 - 0.5))


def fetch_block(i0, i1, j0, j1):
    url = URL.format(i0=i0, i1=i1, j0=j0, j1=j1, s=STRIDE)
    with urllib.request.urlopen(url, timeout=600) as r:
        txt = r.read().decode()
    body = txt.split("---------------------------------------------", 1)[1]
    zpart, rest = body.split("z.lat[", 1)
    rows = []
    for line in zpart.strip().splitlines()[1:]:
        if line.startswith("["):
            rows.append([float(v) for v in line.split(",")[1:]])
    lat = np.array([float(v) for v in rest.split("\n", 1)[1].split("z.lon[")[0].strip().split(",")])
    lon = np.array([float(v) for v in rest.split("z.lon[", 1)[1].split("\n", 1)[1].strip().split(",")])
    return lat, lon, np.array(rows, dtype=np.float32)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    i0, i1 = idx_lat(-55.0), idx_lat(12.0)
    j0, j1 = idx_lon(50.0), idx_lon(150.0)
    lats, blocks = [], []
    step = 400  # rows per request (in native index units)
    lon = None
    for a in range(i0, i1 + 1, step):
        b = min(a + step - STRIDE, i1)
        la, lo, z = fetch_block(a, b, j0, j1)
        print(f"rows {a}-{b}: {z.shape}", flush=True)
        lats.append(la)
        blocks.append(z)
        lon = lo
    lat = np.concatenate(lats)
    z = np.concatenate(blocks, axis=0)
    ds = xr.Dataset({"z": (("lat", "lon"), z)}, coords={"lat": lat, "lon": lon})
    ds.z.attrs.update(units="m", long_name="bedrock elevation (+up), ETOPO 2022 v1 60s, decimated x2")
    ds.attrs.update(source="NOAA NCEI ETOPO 2022 v1 60 arc-second bedrock elevation, "
                    "https://www.ngdc.noaa.gov/thredds/dodsC/global/ETOPO2022/60s/60s_bed_elev_netcdf/"
                    "ETOPO_2022_v1_60s_N90W180_bed.nc", decimation="every 2nd sample (2 arc-min)")
    out = OUT / "etopo2022_2min_55S12N_50E150E.nc"
    ds.to_netcdf(out, engine="h5netcdf")
    print("saved", out, z.shape)


if __name__ == "__main__":
    main()
