# Indian Ocean / Andaman waypoints used in MH370 route analyses

Compiled 2026-11-05 from public sources by web research. Coordinates are WGS-84 as published. Decimals were computed from DMS. **Not for operational use.**

## Columns in `waypoints.csv`
- `name`: ICAO 5-letter name-code, ARINC-424 lat/lon pseudo-waypoint (e.g. `0292S`), or a UGIB-defined pseudo-point (`6NFIR`, `6NFIRWEST`).
- `lat_deg`, `lon_deg`: decimal degrees, with S and W negative. Left blank when unknown.
- `lat_dms`, `lon_dms`: `DD MM SS.ss H`.
- `source_url`: one or more URLs separated by ` ; `.
- `verified`:
  - `Y`: coordinates confirmed in a primary source, i.e. the Malaysian AIP (pre-2014 amendments). The value in the lat/lon columns is that pre-2014 AIP value, which is closest to what a 2014 FMS database would have held. The current (AIRAC 2026-10-29) eAIP value is given in `notes`; differences are 0–4 arcsec.
  - `N`: secondary sources only. These are opennav.com, and for most points also Richard Godfrey's 2016 waypoint table (published on duncansteel.com) or the UGIB/Blowin' papers. All of these agree to the arcsecond where they overlap. For Indonesian points, AirNav Indonesia confirms the **name** but publishes no coordinates. The Indonesian, Indian, Sri Lankan and Australian AIPs were not reachable, so none of these coordinates are AIP-verified.
  - `derived`: a computed or pseudo point, not a published fix.
  - `unknown`: the name was mentioned but no coordinates were found.

## Primary and near-primary sources
- AIP Malaysia ENR 3.3 RNAV routes, pages dated AMDT 1/2010 to 3/2012: https://aip.caam.gov.my/aip%20pdf/ENR/ENR%203/ENR%203.3/Area%20Navigaton%20Routes%20(RNAV).pdf. A copy is in `../ugib2020/`.
- AIP Malaysia ENR 3.1 ATS routes, AMDT 4/2010 (B466 and ANOKO): https://aip.caam.gov.my/aip%20pdf/ENR/ENR%203/ENR%203.1/Lower%20And%20Upper%20ATS%20Routes.pdf. A copy is in `../ugib2020/`.
- Malaysia eAIP ENR 4.4, AIRAC 2026-10-29, the current values: https://aip.caam.gov.my/aip/eAIP/2026-10-29-AIRAC/html/eAIP/WM-ENR-4.4-en-MS.html. Not saved locally; the URL is versioned by AIRAC date.
- AirNav Indonesia, UPR Trial Procedure v2.2. Lists waypoint names only: https://www.airnavindonesia.co.id/wp-content/uploads/2024/11/upr-trial-procedure-within-indonesia-airspace-v.2.2-2.pdf. A copy is in `../ugib2020/`.

## Secondary sources
- opennav.com waypoint pages, `https://opennav.com/waypoint/<CC>/<NAME>`. They were fetched with curl on 2026-11-05 and the exact country-code URL is cited for each row. Some names exist under more than one country code with slightly different values; ANOKO under MY differs from the AIP.
- R. Godfrey, "Comparison of MH370 Flight Paths Based on Waypoints", 1–3 Feb 2016, https://www.duncansteel.com/archives/2189. Table 2 is an image at https://www.duncansteel.com/wp-content/uploads/2016/02/Waypoint-Table-2.png and gives decimal lat/lon for 25 waypoints.
- UGIB 2020 and Blowin' in the Wind 2019 (see `../ugib2020/SOURCE.md`) for the BEDAX coordinates and the waypoint-longitude comparison in UGIB Fig. G-5 (ISBIX, BEDAX, BEBIM, AGEGA, BULVA).

## Known issues
- **NILAM:** the 2010-era Malaysian AIP prints 0955836E on N571 but 0955835E on P627. The CSV uses 35″, which matches the current eAIP value of 0955835.04E.
- **ANOKO:** there are three values. The 2010 AIP gives 070810N 0942458E, and UGIB used this one. The current eAIP gives 070812.12N 0942500.12E. opennav/MY gives 070818.90N 0942448.56E.
- **No coordinates found:** PAKRA, OPOVI and ULAGO. ULAGO did not appear in any source checked.
