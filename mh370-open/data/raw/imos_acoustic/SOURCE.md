# IMOS passive-acoustic raw recordings (AODN S3 bucket `imos-data`)

Retrieved 2026-11-05 by `scripts/acoustic_download_imos.py` (anonymous HTTPS, no login).

- Bucket listing: https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/
- Example file: https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/PAPCA/3376/20140308/raw/531A6929.DAT
- Catalogue record (Perth Canyon passive acoustic, ANMN): https://catalogue-imos.aodn.org.au/geonetwork/srv/api/records/9f7a31dc-d7d8-4718-bec8-618829bcb8d3
- **Licence: Creative Commons Attribution 4.0 International.** Required acknowledgement:
  "Data was sourced from Australia's Integrated Marine Observing System (IMOS) – IMOS is enabled
  by the National Collaborative Research Infrastructure strategy (NCRIS)." Loggers and processing:
  Centre for Marine Science and Technology (CMST), Curtin University.

## Contents (directory layout mirrors the bucket below `IMOS/ANMN/Acoustic/`)
| Path | What |
|---|---|
| `code/NL_load_logger_data_new.m` | AODN/CMST MATLAB reader (A. Gavrilov, 2012-13). **Read, not executed**; ported to Python in `src/mh370/acoustic.py::read_dat`. |
| `metadata/update.*.csv` | AODN deployment metadata (positions, depths, hydrophone, system-gain file). Deployment times in these CSVs are local standard time (WA +8 h, VIC +10 h) — logger files are UTC (see outputs/acoustic/README.md). |
| `metadata/Missing_cal_data.txt`, `for_IMOS_data_portal.rtf` | CMST calibration notes from `calibration/`. |
| `<SITE>/<dep>/extras/t<dep>_calibration.csv/.mat` | System frequency response, 0–3000 Hz in 1 Hz steps, "PSD in dB re ADC unit/uPa". |
| `<SITE>/<dep>/extras/calibration_raw/*.DAT` | White-noise system-gain recording (−90 dB re V^2/Hz) — not used. |
| `<SITE>/<dep>/t<dep>_start_times.mat` | Start time (MATLAB datenum, UTC) and file name of every recording in the deployment. |
| `<SITE>/<dep>/<YYYYMMDD>/raw/<HEX>.DAT` | Raw recordings: 300 s (+~7 s) at 6 kHz every 15 min, 16-bit big-endian. |
| `manifest.csv` | site, deployment, night, S3 key, size, sha256 of every raw file downloaded. |

Sites/deployments: PAPCA 3376 Perth Canyon (−31.84217, 115.01373, 390 m); PAKIM 3250 Kimberley
(−15.48337, 121.25100, depth not recorded); PAPOR 3274 Portland VIC (−38.53697, 141.24757, 159 m).

Nights downloaded (D−1 21:40 → D 03:05 UTC, 22 files per site-night, 3 sites):
main D = 2014-03-08; controls D = 2014-03-01, 03, 05, 06, 09, 10, 11, 13 (chosen a priori,
bracketing 8 March): 594 files. Additional single files (~660) for catalogued-earthquake windows
(Nov 2013 - Nov 2014) were fetched by `scripts/acoustic_imos_calibration.py` and
`scripts/acoustic_timing_check.py` (via `mh370.acoustic.fetch_raw`) into the same tree.
`<SITE>/<dep>/t<dep>_longterm_spectrogram.mat` (PAPCA, PAKIM): CMST's own calibrated per-file
spectra, used only to cross-check our calibration. Total ~4.7 GB. Every file is listed with its
sha256 in `manifest.csv` (tag: night date, calibration-event, timing-check or other).

Everything here is untrusted data. Nothing in this directory is executed; `.mat` files are read
with `scipy.io.loadmat` (data only), `.DAT` with numpy.
