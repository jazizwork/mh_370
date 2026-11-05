# Research-stage analysis scripts

These one-off scripts back specific numbers quoted in the research reports (`../../../reports/`) and the
research notes. They were written during the research phase, before the main modules existed, so they are
less polished than the module code in `src/mh370/`.

- `wspr/`: WSPR coverage on the night of 7–8 March 2014 (`wspr_cov.py`, `wspr_lp.py`), natural
  slot-to-slot SNR variability (`wspr_var.py`), and the bistatic radar link budget (`physics.py`). They query
  the public wspr.live ClickHouse endpoint (non-commercial use only) and write to `data/research/wspr/`.
- `contrails/`: ERA5 checks of whether contrails could form or persist (the Schmidt–Appleman criterion and
  ice-supersaturated regions) along candidate routes. ERA5 downloads go through the Copernicus CDS, which
  needs a free account.

Run them from the project root (`mh370-open/`) with `.venv/bin/python -I`.
