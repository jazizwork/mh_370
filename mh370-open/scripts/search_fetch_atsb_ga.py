"""Fetch Geoscience Australia / AusSeabed MH370 Phase 2 sonar-coverage rasters (WMS).

Downloads transparent PNG renderings of the four per-sensor MH370 Phase 2 5 m sonar
mosaics from the AusSeabed GeoServer WMS on a regular lon/lat grid (EPSG:4326), so that a
data/no-data coverage mask can be derived (alpha > 0 == sonar data present).

Output: data/raw/atsb_ga_search/ausseabed_wms/<short_name>/r{row}_c{col}.png + index.json

Run:  .venv/bin/python -I scripts/search_fetch_atsb_ga.py
Licence of the data: CC BY 4.0, (c) Commonwealth of Australia (Geoscience Australia).
"""
from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "atsb_ga_search" / "ausseabed_wms"
WMS = "https://warehouse.ausseabed.gov.au/geoserver/ows"

LAYERS = {
    "deeptow_sss": "ausseabed:MH370_Phase_2_Sonar_Imagery_Backscatter_Inverse_Deep_Tow__SSS__5m_2018",
    "auv_sss": "ausseabed:MH370_Phase_2_Sonar_Imagery_Backscatter_Inverse_Autonomous_Underwater_Vehicle__SSS__5m_2018",
    "gophoenix_sas": "ausseabed:MH370_Phase_2_Sonar_Imagery_Backscatter_Wide_GoPhoenix__SAS__5m_2018",
    "dhj_sas": "ausseabed:MH370_Phase_2_Sonar_Imagery_Backscatter_Wide_DHJ__SAS__5m_2018",
}

LON0, LON1 = 85.0, 97.0   # covers all four layer bboxes (85.09 .. 96.31 E)
LAT0, LAT1 = -40.5, -32.5  # (-40.09 .. -32.71)
TILE_DEG = 2.0
RES_DEG = 0.002            # ~0.18 km (lon) x 0.22 km (lat) per pixel at 36 S
NPIX = int(round(TILE_DEG / RES_DEG))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"wms": WMS, "crs": "EPSG:4326", "res_deg": RES_DEG, "tile_deg": TILE_DEG,
             "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
             "layers": {}}
    nrow = int(round((LAT1 - LAT0) / TILE_DEG))
    ncol = int(round((LON1 - LON0) / TILE_DEG))
    for short, layer in LAYERS.items():
        d = OUT / short
        d.mkdir(exist_ok=True)
        tiles = []
        for r in range(nrow):
            top = LAT1 - r * TILE_DEG
            bot = top - TILE_DEG
            for c in range(ncol):
                left = LON0 + c * TILE_DEG
                right = left + TILE_DEG
                fn = d / f"r{r}_c{c}.png"
                params = {
                    "service": "WMS", "version": "1.1.1", "request": "GetMap",
                    "layers": layer, "styles": "", "srs": "EPSG:4326",
                    "bbox": f"{left},{bot},{right},{top}",
                    "width": NPIX, "height": NPIX,
                    "format": "image/png", "transparent": "true",
                }
                url = WMS + "?" + urllib.parse.urlencode(params)
                if not fn.exists():
                    for attempt in range(4):
                        try:
                            with urllib.request.urlopen(url, timeout=180) as resp:
                                ctype = resp.headers.get("Content-Type", "")
                                data = resp.read()
                            if not ctype.startswith("image/png"):
                                raise RuntimeError(f"bad content type {ctype}: {data[:200]!r}")
                            fn.write_bytes(data)
                            break
                        except Exception as e:  # noqa: BLE001
                            print("retry", short, r, c, e)
                            time.sleep(5 * (attempt + 1))
                    else:
                        raise SystemExit(f"failed {url}")
                tiles.append({"file": f"{short}/{fn.name}", "row": r, "col": c,
                              "bbox": [left, bot, right, top], "url": url})
                print(short, r, c, fn.stat().st_size)
        index["layers"][short] = {"layer": layer, "tiles": tiles}
    (OUT / "index.json").write_text(json.dumps(index, indent=1))


if __name__ == "__main__":
    main()
