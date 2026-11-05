"""Download open FDSN seismic waveforms + response metadata for workstream D step 4.

Anonymous FDSN web services (no login): EarthScope (ex-IRIS), GEOFON, RESIF, AusPass.
Main night : 2014-03-07 20:00 -> 2014-03-08 03:00 UTC (all listed stations, BH?/HH?)
Controls   : D-1 22:00 -> D 03:00 for D in 2014-03-05, 03-10, 03-11 (Z only, subset)

Output: data/raw/fdsn_seismic/<night>/<NET.STA>.mseed and <NET.STA>.xml, plus log.csv.
Usage: .venv/bin/python -I scripts/acoustic_seismic_download.py
"""
from __future__ import annotations

import csv
import datetime as dt
from pathlib import Path

from obspy import UTCDateTime
from obspy.clients.fdsn import Client

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "fdsn_seismic"

SERVERS = {
    "EARTHSCOPE": "https://service.earthscope.org",
    "GEOFON": "https://geofon.gfz.de",
    "RESIF": "https://ws.resif.fr",
    "AUSPASS": "http://auspass.edu.au:8080",
}
# (net, sta, channels, servers in order of preference)
STATIONS = [
    ("II", "COCO", "BH?", ["EARTHSCOPE"]),
    ("AU", "XMIS", "BH?", ["EARTHSCOPE", "AUSPASS"]),
    ("AU", "XMI", "BH?", ["EARTHSCOPE"]),
    ("G", "AIS", "BH?,HH?", ["RESIF", "EARTHSCOPE"]),
    ("G", "RODM", "BH?,HH?", ["RESIF", "EARTHSCOPE"]),
    ("G", "ROCAM", "BH?,HH?", ["RESIF", "EARTHSCOPE"]),
    ("II", "DGAR", "BH?", ["EARTHSCOPE"]),
    ("IU", "NWAO", "BH?,HHZ", ["EARTHSCOPE"]),
    ("IU", "MBWA", "BHZ,HHZ", ["EARTHSCOPE"]),
    ("S1", "AUBUS", "HH?,BHZ", ["AUSPASS", "EARTHSCOPE"]),
    ("AU", "GIRL", "BH?", ["EARTHSCOPE"]),
    ("GE", "CISI", "BH?", ["GEOFON"]),
    ("GE", "JAGI", "BH?", ["GEOFON"]),
    ("GE", "SMRI", "BH?", ["GEOFON"]),
    ("GE", "UGM", "BH?", ["GEOFON"]),
    ("GE", "KAAM", "BH?", ["GEOFON"]),
    ("GE", "HMDM", "BH?", ["GEOFON"]),
    ("IN", "MNC", "BH?,HH?", ["EARTHSCOPE"]),
]
CONTROL_STATIONS = ["COCO", "XMIS", "AIS", "NWAO", "AUBUS", "GIRL"]
CONTROL_DAYS = [dt.date(2014, 3, 5), dt.date(2014, 3, 10), dt.date(2014, 3, 11)]


def get(net, sta, cha, servers, t0, t1, outdir: Path, log):
    outdir.mkdir(parents=True, exist_ok=True)
    ms, xml = outdir / f"{net}.{sta}.mseed", outdir / f"{net}.{sta}.xml"
    if ms.exists() and xml.exists():
        log.append((outdir.name, net, sta, cha, "cached", "", ms.stat().st_size))
        return
    for s in servers:
        try:
            c = Client(SERVERS[s], timeout=180)
            st = c.get_waveforms(net, sta, "*", cha, t0, t1)
            inv = c.get_stations(network=net, station=sta, channel=cha, starttime=t0,
                                 endtime=t1, level="response")
            st.write(str(ms), format="MSEED")
            inv.write(str(xml), format="STATIONXML")
            ids = sorted({f"{tr.id}@{tr.stats.sampling_rate:g}" for tr in st})
            print(f"{outdir.name} {net}.{sta} from {s}: {ids}", flush=True)
            log.append((outdir.name, net, sta, cha, s, " ".join(ids), ms.stat().st_size))
            return
        except Exception as e:  # noqa: BLE001
            print(f"{outdir.name} {net}.{sta} {s}: {type(e).__name__} {str(e)[:120]}", flush=True)
    log.append((outdir.name, net, sta, cha, "NO DATA", "", 0))


def main():
    log = []
    t0, t1 = UTCDateTime(2014, 3, 7, 20), UTCDateTime(2014, 3, 8, 3)
    for net, sta, cha, srv in STATIONS:
        get(net, sta, cha, srv, t0, t1, OUT / "night_20140308", log)
    for d in CONTROL_DAYS:
        a = UTCDateTime(d.year, d.month, d.day) - 2 * 3600
        b = UTCDateTime(d.year, d.month, d.day, 3)
        for net, sta, cha, srv in STATIONS:
            if sta in CONTROL_STATIONS:
                zcha = ",".join(c[:-1] + "Z" for c in cha.split(","))
                get(net, sta, zcha, srv, a, b, OUT / f"control_{d:%Y%m%d}", log)
    with open(OUT / "download_log.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["night", "net", "sta", "channels", "server", "trace_ids", "bytes"])
        w.writerows(log)


if __name__ == "__main__":
    main()
