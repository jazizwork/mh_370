# USGS ComCat catalogue extract (workstream D, IMOS calibration events)

Retrieved 2026-11-05 (anonymous HTTPS):
https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2013-12-01&endtime=2014-06-01&minlatitude=-70&maxlatitude=15&minlongitude=30&maxlongitude=180&minmagnitude=4.0&orderby=time-asc

File: `usgs_201312_201406_m4.csv`. US Government public-domain data (USGS).
Used by `scripts/acoustic_imos_calibration.py` to find earthquakes whose P / T-phase arrivals
fall inside IMOS PAPCA/PAKIM/PAPOR recording windows (timing and detectability calibration).

Additional extracts (same service, retrieved 2026-11-05), used to extend the PAPCA calibration over
the rest of deployment 3376 for sources west/south-west of Perth (the 7th-arc directions):
- `usgs_201406_201411_WSW_m4.csv`: starttime=2014-06-01, endtime=2014-11-05, lat -65..-5, lon 55..125, M>=4.0
- `usgs_201311_m4.csv`: starttime=2013-11-28, endtime=2013-12-01, same box, M>=4.0
