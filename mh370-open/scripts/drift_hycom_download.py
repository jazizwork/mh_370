"""Download HYCOM GLBv0.08 expt_53.X (global reanalysis, 1/12 deg) surface currents for the
2014-15 hindcast cross-check of workstream B (drift). Free OPeNDAP, no sign-up.

  https://tds.hycom.org/thredds/dodsC/GLBv0.08/expt_53.X/data/2014   (and .../2015)

Subset: depth level 0 (surface), daily at 12:00 UTC, 8 Mar 2014 .. 31 Aug 2015,
lon 20-120E, lat 50S-5N, every 3rd grid point (~0.24 deg). Stored as one .npz per month in
data/raw/hycom_glbv008_53X/ (int16 values as served, scale 0.001 m/s, fill -30000).

Run: .venv/bin/python -I scripts/drift_hycom_download.py
"""
from __future__ import annotations

import datetime as dt
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "hycom_glbv008_53X"
BASE = "https://tds.hycom.org/thredds/dodsC/GLBv0.08/expt_53.X/data/{year}"
STRIDE = 3
T0 = dt.date(2014, 3, 8)
T1 = dt.date(2015, 8, 31)


def open_year(year):
    from pydap.client import open_url
    for k in range(5):
        try:
            return open_url(BASE.format(year=year), protocol="dap2")
        except Exception:  # noqa: BLE001
            time.sleep(5 + 5 * k)
    raise RuntimeError(f"cannot open HYCOM {year}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {}
    for year in (2014, 2015):
        ds = open_year(year)
        lat = np.asarray(ds["lat"][:])
        lon = np.asarray(ds["lon"][:])
        t = np.asarray(ds["time"][:])
        i0, i1 = np.searchsorted(lat, -50.0), np.searchsorted(lat, 5.0) + 1
        j0, j1 = np.searchsorted(lon, 20.0), np.searchsorted(lon, 120.0) + 1
        meta[year] = (ds, lat[i0:i1:STRIDE], lon[j0:j1:STRIDE], t, (i0, i1, j0, j1))
    days = [T0 + dt.timedelta(d) for d in range((T1 - T0).days + 1)]
    months = sorted({(d.year, d.month) for d in days})

    def fetch_day(d):
        ds, la, lo, t, (i0, i1, j0, j1) = meta[d.year]
        target = (dt.datetime(d.year, d.month, d.day, 12) - dt.datetime(2000, 1, 1)).total_seconds() / 3600
        k = int(np.argmin(np.abs(t - target)))
        if abs(t[k] - target) > 6:
            return d, None, None, np.nan
        out = []
        for var in ("water_u", "water_v"):
            for attempt in range(6):
                try:
                    a = ds[var].array[k, 0, i0:i1:STRIDE, j0:j1:STRIDE]
                    a = np.asarray(getattr(a, "data", a)).reshape(la.size, lo.size).astype(np.int16)
                    out.append(a)
                    break
                except Exception as e:  # noqa: BLE001
                    if attempt == 5:
                        print("FAILED", d, var, e, file=sys.stderr, flush=True)
                        return d, None, None, np.nan
                    time.sleep(3 + 3 * attempt)
        return d, out[0], out[1], t[k]

    for (y, m) in months:
        f = OUT / f"hycom_sfc_{y}{m:02d}.npz"
        if f.exists():
            continue
        md = [d for d in days if (d.year, d.month) == (y, m)]
        with ThreadPoolExecutor(4) as ex:
            res = list(ex.map(fetch_day, md))
        ok = [r for r in res if r[1] is not None]
        _, la, lo, _, _ = meta[y]
        np.savez_compressed(
            f, u=np.stack([r[1] for r in ok]), v=np.stack([r[2] for r in ok]),
            time_hours_since_2000=np.array([r[3] for r in ok]),
            date=np.array([str(r[0]) for r in ok]), lat=la, lon=lo,
            scale_factor=0.001, fill_value=-30000)
        print(f"{y}-{m:02d}: {len(ok)}/{len(md)} days", flush=True)
    (OUT / "SOURCE.md").write_text(f"""# HYCOM GLBv0.08 expt_53.X global reanalysis — surface currents subset

- URLs: {BASE.format(year=2014)} and {BASE.format(year=2015)} (OPeNDAP, anonymous, no sign-up)
- Product: HYCOM + NCODA Global 1/12 deg Reanalysis (GLBv0.08, experiment 53.X), 3-hourly
  snapshots; https://www.hycom.org/data/glbv0pt08/expt-53pt-x . HYCOM data are freely available
  (https://www.hycom.org/data); acknowledge the HYCOM consortium / NRL.
- Subset retrieved {dt.date.today().isoformat()} by scripts/drift_hycom_download.py: water_u,
  water_v at depth index 0 (0 m), the snapshot nearest 12:00 UTC each day, {T0} .. {T1},
  lat 50S-5N, lon 20-120E, every {STRIDE}rd grid point. Values int16, scale 0.001 m/s,
  fill -30000, exactly as served.
- Used only for the 2014-15 particle-tracking cross-check of the flaperon arrival.
""")


if __name__ == "__main__":
    main()
