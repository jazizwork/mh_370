# Open FDSN seismic waveforms and event catalogues (workstream D, step 4)

Retrieved 2026-11-05 by `scripts/acoustic_seismic_download.py` and
`scripts/acoustic_seismic_calibration_ext.py` (ObsPy 1.5.1 FDSN client). Anonymous access,
no login or application needed. Total about 170 MB.

## Waveforms
| Directory | Content |
|---|---|
| `night_20140308/` | 2014-03-07 20:00 to 2014-03-08 03:00 UTC, BH?/HH? (all components where offered) plus StationXML with responses for II.COCO, AU.XMIS, AU.XMI, G.AIS, G.RODM, G.ROCAM, II.DGAR, IU.NWAO, IU.MBWA, S1.AUBUS, AU.GIRL, GE.CISI, GE.JAGI, GE.SMRI, GE.UGM, GE.KAAM, IN.MNC. GE.HMDM returned no data (HTTP 204). |
| `control_201403{05,10,11}/` | Vertical channels only, D−1 22:00 to D 03:00 UTC, for COCO, XMIS, AIS, NWAO, AUBUS and GIRL. |
| `calib_ext/` | 216 short Z windows, from origin −15 min to T(1.46 km/s) + 4 min, for USGS shallow oceanic events between 2014-02-01 and 2014-05-01 at COCO, XMIS, GIRL, DGAR, AIS, RODM and AUBUS. |

`download_log.csv` lists the server and trace IDs for each request.

Data centres (FDSN web services):
- EarthScope (formerly IRIS DMC): https://service.earthscope.org/fdsnws/ for the II, IU, AU and IN networks.
- GFZ GEOFON: https://geofon.gfz.de/fdsnws/ for the GE network.
- RESIF / EPOS-France: https://ws.resif.fr/fdsnws/ for the G network (GEOSCOPE).
- AusPass (ANU): http://auspass.edu.au:8080/fdsnws/ for the S1 network.

Terms: these are open FDSN data. Cite the networks by their DOIs:
- II: 10.7914/SN/II
- IU: 10.7914/SN/IU
- G: 10.18715/GEOSCOPE.G
- GE: 10.14470/TR560404
- AU: Geoscience Australia
- S1: 10.7914/SN/S1
- IN: India Meteorological Department

We have not checked each network's licence individually. Most are CC BY 4.0 or "open, cite DOI".

## Catalogues
- `catalog_usgs.csv`: USGS ComCat, 2014-03-07 18:00 to 03-08 03:00, 65°S–25°N, 30–160°E, M≥2.
  https://earthquake.usgs.gov/fdsnws/event/1/
- `catalog_isc.txt`: ISC Bulletin (FDSN text), same window. http://www.isc.ac.uk/fdsnws/event/1/
- `catalog_usgs_201402_201404_region.csv`: USGS, 2014-02-01 to 05-01, 60°S–5°N, 55–135°E, M≥3.5, depth ≤70 km. Used for T-phase detectability calibration.
- `catalog_usgs_global_M4.5.csv`: USGS global, M≥4.5, 2014-03-07 22:00 to 03-08 02:00. Used for the teleseism check.

Everything in this directory is untrusted data. It is read only with ObsPy and pandas, and nothing in it is executed.
