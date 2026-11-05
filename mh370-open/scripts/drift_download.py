"""Download the public data used by workstream B (drift).

All sources are anonymous, no sign-up:
  1. NOAA Global Drifter Program 6-hourly interpolated dataset (ragged-array zarr,
     May 2025 release) from the NOAA Open Data Dissemination bucket on AWS:
     https://noaa-oar-hourly-gdp-pds.s3.amazonaws.com/experimental/gdp6h_ragged_may25.zarr
     Only the variables we need are mirrored (raw zarr chunk files, unmodified).
  2. Natural Earth 1:10m land polygons + minor islands (public domain):
     https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip
     https://naciscdn.org/naturalearth/10m/physical/ne_10m_minor_islands.zip
  3. NCEP/NCAR Reanalysis 1 daily-mean 10 m winds (NOAA PSL, public):
     https://psl.noaa.gov/thredds/fileServer/Datasets/ncep.reanalysis/Dailies/surface_gauss/
     (downloads.psl.noaa.gov returned HTTP 403 to scripted requests; the THREDDS fileServer works)
     (used only for the leeway-augmented sensitivity variant).

Run: .venv/bin/python -I scripts/drift_download.py [--no-wind]
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

GDP_BASE = "https://noaa-oar-hourly-gdp-pds.s3.amazonaws.com/experimental/gdp6h_ragged_may25.zarr"
GDP_DIR = RAW / "gdp6h" / "gdp6h_ragged_may25.zarr"
GDP_VARS = ["lat", "lon", "time", "drogue_status", "ve", "vn",
            "id", "rowsize", "typedeath", "drogue_lost_date", "deploy_date", "end_date",
            "end_lat", "end_lon", "start_date", "start_lat", "start_lon", "typebuoy"]

NE_DIR = RAW / "naturalearth"
NE_URLS = ["https://naciscdn.org/naturalearth/10m/physical/ne_10m_land.zip",
           "https://naciscdn.org/naturalearth/10m/physical/ne_10m_minor_islands.zip"]

NCEP_DIR = RAW / "ncep_r1_daily"
NCEP_BASE = "https://psl.noaa.gov/thredds/fileServer/Datasets/ncep.reanalysis/Dailies/surface_gauss"


def fetch(url: str, dest: Path, retries: int = 12) -> int:
    """Streamed download with HTTP Range resume (the PSL THREDDS server drops long
    transfers) into dest.part, renamed to dest only when complete."""
    import time
    if dest.exists() and dest.stat().st_size > 0:
        return dest.stat().st_size
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    for k in range(retries):
        try:
            have = tmp.stat().st_size if tmp.exists() else 0
            hdr = {"Range": f"bytes={have}-"} if have else {}
            with requests.get(url, timeout=120, stream=True, headers=hdr) as r:
                if r.status_code == 404:
                    return -404
                if r.status_code == 416:  # already complete
                    tmp.rename(dest)
                    return dest.stat().st_size
                r.raise_for_status()
                mode = "ab" if (have and r.status_code == 206) else "wb"
                total = r.headers.get("Content-Length")
                total = int(total) + (have if mode == "ab" else 0) if total else None
                with open(tmp, mode) as f:
                    for chunk in r.iter_content(1 << 20):
                        f.write(chunk)
            if total is not None and tmp.stat().st_size != total:
                raise IOError(f"short read {tmp.stat().st_size} != {total}")
            tmp.rename(dest)
            return dest.stat().st_size
        except Exception as e:  # noqa: BLE001
            if k == retries - 1:
                print("FAILED", url, e, file=sys.stderr, flush=True)
                raise
            time.sleep(2 + 2 * k)
    return 0


def download_gdp():
    meta_names = [".zgroup", ".zattrs", ".zmetadata"]
    for m in meta_names:
        fetch(f"{GDP_BASE}/{m}", GDP_DIR / m)
    meta = json.loads((GDP_DIR / ".zmetadata").read_text())["metadata"]
    jobs = []
    for v in GDP_VARS:
        za = meta[f"{v}/.zarray"]
        nch = -(-za["shape"][0] // za["chunks"][0])
        for m in [".zarray", ".zattrs"]:
            jobs.append((f"{GDP_BASE}/{v}/{m}", GDP_DIR / v / m))
        for c in range(nch):
            jobs.append((f"{GDP_BASE}/{v}/{c}", GDP_DIR / v / str(c)))
    print(f"GDP: {len(jobs)} files")
    with ThreadPoolExecutor(16) as ex:
        sizes = list(ex.map(lambda a: fetch(*a), jobs))
    print(f"GDP: {sum(s for s in sizes if s > 0) / 1e9:.2f} GB on disk")


def download_ne():
    import zipfile
    for u in NE_URLS:
        z = NE_DIR / Path(u).name
        fetch(u, z)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(NE_DIR / z.stem)
    print("Natural Earth done")


def download_ncep(years):
    jobs = []
    for y in years:
        for v in ["uwnd", "vwnd"]:
            fn = f"{v}.10m.gauss.{y}.nc"
            jobs.append((f"{NCEP_BASE}/{fn}", NCEP_DIR / fn))
    with ThreadPoolExecutor(3) as ex:
        sizes = list(ex.map(lambda a: fetch(*a), jobs))
    print(f"NCEP: {sum(s for s in sizes if s > 0) / 1e9:.2f} GB")


def write_source_md():
    today = dt.date.today().isoformat()
    (RAW / "gdp6h" / "SOURCE.md").write_text(f"""# NOAA Global Drifter Program — 6-hourly interpolated dataset (ragged array, zarr)

- URL: {GDP_BASE}
  (NOAA Open Data Dissemination / AWS open-data bucket `noaa-oar-hourly-gdp-pds`, prefix
  `experimental/gdp6h_ragged_may25.zarr`; anonymous HTTPS, no sign-up.)
- Dataset: Lumpkin, R.; Centurioni, L. (2019). NOAA Global Drifter Program quality-controlled
  6-hour interpolated data from ocean surface drifting buoys. NOAA NCEI.
  https://doi.org/10.25921/7ntx-z961 . Version "May 2025" (time coverage 1979-02-15 .. 2025-06-12,
  28,728 trajectories, 48,887,074 observations).
- Licence: "freely available" (dataset attribute); NOAA data, public domain in the US.
- Retrieved: {today} by scripts/drift_download.py.
- Mirrored variables (raw zarr chunks, not modified): {", ".join(GDP_VARS)}.
  `.zmetadata` is the full consolidated metadata of the remote store (lists variables not mirrored);
  open with `xr.open_zarr(path, consolidated=False)`.
- Drogue status per observation: 1 = drogued, 0 = undrogued (drogue lost), from GDP metadata.
- typedeath: 0 alive, 1 ran aground, 2 picked up, 3 stopped transmitting, 4 sporadic, 5 bad
  batteries, 6 inactive.
""")
    (NE_DIR / "SOURCE.md").write_text(f"""# Natural Earth 1:10m physical vectors

- URLs: {NE_URLS[0]} ; {NE_URLS[1]}
- Licence: public domain (https://www.naturalearthdata.com/about/terms-of-use/).
- Retrieved: {today} by scripts/drift_download.py. Used for the land mask / coastal cells and
  for coastline plotting. ne_10m_minor_islands adds small islands (e.g. parts of the Mascarenes).
""")
    if NCEP_DIR.exists():
        (NCEP_DIR / "SOURCE.md").write_text(f"""# NCEP/NCAR Reanalysis 1 — daily mean 10 m wind components (T62 Gaussian grid)

- URL: {NCEP_BASE}/ (files uwnd.10m.gauss.YYYY.nc, vwnd.10m.gauss.YYYY.nc)
- Kalnay et al. (1996), Bull. Amer. Meteor. Soc. 77, 437-471. Provided by NOAA PSL, Boulder,
  Colorado, USA, https://psl.noaa.gov . Public, no sign-up.
- Retrieved: {today} by scripts/drift_download.py. Used only for the leeway-augmented
  (extra-windage) sensitivity variant of the Markov chain.
""")


if __name__ == "__main__":
    download_gdp()
    download_ne()
    if "--no-wind" not in sys.argv:
        download_ncep(range(1985, 2026))
    write_source_md()
