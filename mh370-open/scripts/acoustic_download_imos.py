"""Download IMOS passive-acoustic raw files (CMST .DAT) from the public AODN S3 bucket.

Anonymous HTTPS only. Files are selected by their hex file name, which is a Unix
time ~15 s before the first sample (verified against the footer by acoustic.read_dat).

Nights are defined as D-1 21:40 UTC -> D 03:05 UTC (covers 22:00-03:00 plus margin).
Main night: D = 2014-03-08. Control nights: see CONTROL_DAYS.

Usage: .venv/bin/python -I scripts/acoustic_download_imos.py [--sites PAPCA PAKIM PAPOR]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "imos_acoustic"
BASE = "https://imos-data.s3-ap-southeast-2.amazonaws.com"
PREFIX = "IMOS/ANMN/Acoustic"

SITES = {"PAPCA": "3376", "PAKIM": "3250", "PAPOR": "3274"}
MAIN_DAY = dt.date(2014, 3, 8)
# Control nights (date D = the UTC date of the 00:00-03:00 part). Chosen to bracket
# 8 March on both sides without looking at the data first.
CONTROL_DAYS = [dt.date(2014, 3, d) for d in (1, 3, 5, 6, 9, 10, 11, 13)]

NIGHT_START = dt.timedelta(hours=-2, minutes=-20)   # D-1 21:40
NIGHT_END = dt.timedelta(hours=3, minutes=5)         # D 03:05


def s3_list(prefix: str) -> list[tuple[str, int]]:
    out, token = [], None
    while True:
        url = f"{BASE}/?list-type=2&prefix={prefix}"
        if token:
            url += "&continuation-token=" + urllib.parse.quote(token)
        with urllib.request.urlopen(url, timeout=60) as r:
            t = r.read().decode()
        out += [(k, int(s)) for k, s in re.findall(r"<Key>(.*?)</Key>.*?<Size>(\d+)</Size>", t)]
        m = re.search(r"<NextContinuationToken>(.*?)</NextContinuationToken>", t)
        if "<IsTruncated>true</IsTruncated>" in t and m:
            token = m.group(1)
        else:
            return out


def fetch(key: str, size: int | None = None) -> Path:
    dest = OUT / key.replace(PREFIX + "/", "")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and (size is None or dest.stat().st_size == size):
        return dest
    url = f"{BASE}/{urllib.parse.quote(key)}"
    for attempt in range(4):
        try:
            tmp = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            tmp.rename(dest)
            if size is not None and dest.stat().st_size != size:
                raise IOError(f"size mismatch {dest}")
            return dest
        except Exception as e:  # noqa: BLE001
            print(f"  retry {attempt} {key}: {e}", file=sys.stderr)
            time.sleep(2 + 3 * attempt)
    raise RuntimeError(f"failed {key}")


def hex_time(name: str) -> dt.datetime:
    return dt.datetime.fromtimestamp(int(Path(name).stem, 16), dt.timezone.utc).replace(tzinfo=None)


def night_files(site: str, dep: str, day: dt.date):
    t0 = dt.datetime.combine(day, dt.time()) + NIGHT_START
    t1 = dt.datetime.combine(day, dt.time()) + NIGHT_END
    keys = []
    for d in {t0.date(), t1.date()}:
        keys += s3_list(f"{PREFIX}/{site}/{dep}/{d:%Y%m%d}/raw/")
    return sorted((k, s) for k, s in keys if t0 <= hex_time(k) <= t1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", nargs="+", default=list(SITES))
    ap.add_argument("--days", nargs="*", default=None, help="YYYY-MM-DD (default main+controls)")
    a = ap.parse_args()
    days = [dt.date.fromisoformat(d) for d in a.days] if a.days else [MAIN_DAY] + CONTROL_DAYS

    # code, metadata and calibration (small)
    fetch(f"{PREFIX}/code/NL_load_logger_data_new.m")
    for site in a.sites:
        dep = SITES[site]
        for k, s in s3_list(f"{PREFIX}/{site}/{dep}/extras/"):
            fetch(k, s)
        fetch(f"{PREFIX}/{site}/{dep}/t{dep}_start_times.mat")

    manifest = OUT / "manifest.csv"
    rows = []
    for site in a.sites:
        dep = SITES[site]
        for day in days:
            files = night_files(site, dep, day)
            print(f"{site} {day}: {len(files)} files", flush=True)
            for k, s in files:
                p = fetch(k, s)
                rows.append((site, dep, day.isoformat(), k, s, p))
    # manifest with sha256 (append/refresh)
    old = {}
    if manifest.exists():
        for line in manifest.read_text().splitlines()[1:]:
            f = line.split(",")
            old[f[3]] = line
    for site, dep, day, k, s, p in rows:
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        old[k] = f"{site},{dep},{day},{k},{s},{h}"
    manifest.write_text("site,deployment,night_day,key,size,sha256\n" + "\n".join(sorted(old.values())) + "\n")
    print("done; manifest:", manifest)


if __name__ == "__main__":
    import urllib.parse  # noqa: F401
    main()
