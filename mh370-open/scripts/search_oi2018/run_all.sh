#!/bin/sh
# Reproduce the OI-2018 searched-area digitisation from the downloaded figures.
# Run from the project root:  sh scripts/search_oi2018/run_all.sh
set -e
PY=".venv/bin/python -I -W ignore"
D=scripts/search_oi2018
# 1. vessel AIS track (community KMZ) -> CSV
$PY $D/parse_tracks.py "data/raw/oi2018_search/community_kmz_labratsr/extracted/Ocean Infinity MH370 Search Google Earth KMZ Files" \
    data/derived/oi2018_search/seabed_constructor_track_2018.csv
# 2. planning map (OSU#1) graticule fit, used for validation only
$PY $D/georef_fit.py $D/configs/osu01_planning_map_graticule_fit.json data/raw/oi2018_search/digitisation/osu01_planning_map_georef_utm46s.json
# 3. per-site progress maps: georeference from graticule crosses + extract coverage outline
for c in $D/configs/site*.json; do $PY $D/oigeo.py "$c"; done
# 4. assemble polygons, areas, cross-arc profile, figure
$PY $D/assemble.py
