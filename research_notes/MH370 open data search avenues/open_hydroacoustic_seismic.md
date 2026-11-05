# Open hydroacoustic and seismic data for MH370's end point (8 March 2014, ~00:00–02:00 UTC)

Notes compiled 2026-11-05. The data checks are my own live queries of AODN S3 and the FDSN services, run 2026-11-05 with ObsPy 1.5.1. Anything marked "own analysis" is a quick look by me, not a published result. The term "Inference" marks my own reasoning.

**Three corrections to the background brief:**
1. **Stead 2014 (LANL) did not report a 306° bearing.** His candidate at HA01 at ~00:52 UTC has a direction of arrival of **246.9°**. The **306.18°** arrival is Kadri's, at **00:54:30 UTC** ([Stead LA-UR-14-24972](https://www.osti.gov/servlets/purl/1136454); [Kadri 2024, Table 1](https://www.nature.com/articles/s41598-024-60529-1.pdf)).
2. **The IMOS Perth Canyon recorder ran a fixed schedule in March 2014: 300 s of every 15 min at 6 kHz.** File headers give the exact windows (section 1).
3. **The "IMOS Scott Reef" recorder in the 2014 Curtin story is very probably the AODN "Kimberley" (PAKIM) recorder, and its 8 March data are open.** The open file contains a strong transient at ~01:32:56 UTC (sections 1 and 4).

---

## 1. IMOS passive-acoustic data on AODN: locations, formats, 8 March 2014 files, duty cycle, sample rate

### Takeaway
Three IMOS recorders have raw files for 2014-03-08 in the public AODN S3 bucket: Perth Canyon (PAPCA, deployment 3376), Kimberley (PAKIM 3250) and Portland, Victoria (PAPOR 3274). Each records 300 s every 15 min at 6 kHz in the CMST binary `.DAT` format, and AODN provides a MATLAB reader and per-deployment calibration curves. Across 00:00–02:00 UTC, the Perth Canyon windows happen to cover the predicted Perth Canyon arrival times of both the Kadri 306° and the Stead 246.9° HA01 candidates (00:50:01–00:55:01). The Kimberley window 01:30:00–01:35:08 contains a strong transient that matches the "Scott Reef 01:32:49" signal from the 2014 Curtin story.

### Cited Findings
**Where the data are**
- AODN bucket `imos-data` (HTTPS listing, no login): the prefix `IMOS/ANMN/Acoustic/` holds the site folders PAKAI (Kangaroo Island), PAKIM (Kimberley), PAPCA (Perth Canyon), PAPIL (Pilbara), PAPOR (Portland), PATUN (Tuncurry), plus `calibration/`, `code/` and `metadata/`. There is no separate Scott Reef folder. — [S3 listing](https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/&delimiter=/) (own query 2026-11-05)
- Folder layout is `<SITE>/<deployment_id>/<YYYYMMDD>/`:
  - `raw/<HEX>.DAT`: 96 files per day.
  - `recording_spec/<HEX>SP.png` and `recording_wave/...png`: 96 each.
  - `<id>_<date>SP.png`: one daily spectrogram.
  - The deployment level also holds `t<id>_longterm_spectrogram.mat`, `t<id>_start_times.mat`, `asfft/` and `extras/t<id>_calibration.csv`.
  - Source: [PAPCA 3376, 20140308 listing](https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/PAPCA/3376/20140308/) (own query)
- **Files exist for 2014-03-08** (96 raw `.DAT` files each, ~3.68 MB per file):
  - [PAPCA/3376/20140308](https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/PAPCA/3376/20140308/)
  - [PAKIM/3250/20140308](https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/PAKIM/3250/20140308/)
  - [PAPOR/3274/20140308](https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/PAPOR/3274/20140308/)
  - Direct download works, for example: `https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/PAPCA/3376/20140308/raw/531A6929.DAT` (own download)
- **Deployment metadata** (AODN metadata CSVs in [metadata/](https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/metadata/)):
  - PAPCA 3376 "Perth Canyon, WA 2013-2014": deployed 2013-11-28 17:05 to 2014-11-04 04:35. Position −31.84217, 115.01373; water and receiver depth 390 m; 6 kHz. Hydrophone "Massa TR1025C 500", sensitivity −196.0 dB.
  - PAKIM 3250 "Kimberley, WA 2013-2014": 2013-10-01 to 2014-07-10 (last wet sample 2014-06-02). Position −15.48337, 121.251; 6 kHz; hydrophone 454012, −197.7 dB. The depth field reads "1", which looks like a placeholder.
  - PAPOR 3274 "Portland, VIC 2014": 2013-12-01 to 2014-11-27. Position −38.53697, 141.24757; depth 159 m.
  - Other deployments do not cover March 2014: PAPCA 3318 starts 2014-11-28, PAPIL 3334 starts 2014-08-11, and PAKAI 3382 starts in Dec 2014.
- **Format** (from AODN's reader [NL_load_logger_data_new.m](https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/code/NL_load_logger_data_new.m), A. Gavrilov, CMST Curtin, 2012–13):
  - A 5-line ASCII header, then big-endian `uint16` samples. Counts convert to volts with full scale 5 V/65536 after removing the mean.
  - An ASCII footer ("Record Marker") gives the UTC start time to a fraction of a second.
  - The header of `531A6929.DAT` reads `Schedule 1 2014/03/08 00:50:01`, `Sample Rate 06000 Duration 0000000300`, `Filter 0 ... LF=008 HF=02800`.
  - Its footer reads `First Data-2014/03/08 00:50:01 - 55982` (the fraction is in units of 1/65536 s) and `Finalised -2014/03/08 00:55:09`. (Own inspection of the [file](https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/PAPCA/3376/20140308/raw/531A6929.DAT).)
  - The hex file name is a Unix time about 16 s before the first sample (0x531A6929 = 00:49:45 UTC).
- **Exact recording windows on 8 Mar 2014** (UTC, from the headers and footers of the S3 files; own HTTP range reads):
  - Perth Canyon: 00:05:02–00:10:09, 00:35:01–00:40:08, 00:50:01–00:55:09, 01:20:00–(+300 s), 01:35:20–01:40:27, 01:50:01–01:55:08. File names imply the remaining windows are about 00:20–00:25 and 01:05–01:10.
  - Kimberley: 01:15:00–01:20:08 and 01:30:00–01:35:08. File names imply the full sequence is 00:15, 00:30, 00:45, 01:00, 01:15, 01:30, 01:45 and 02:00, each 5 min long.
  - Portland: file names follow the same cycle as Kimberley (xx:14:45, xx:29:45 and so on).
- **Calibration:** `extras/t3376_calibration.csv` has 3,001 rows of (Hz, dB). Sample values: −176.94 at 0 Hz, −165.92 at 5 Hz, −161.01 at 10 Hz, −157.47 at 20 Hz, −155.86 at 40 Hz, −155.35 at 100 Hz, −155.55 at 2,800 Hz. — [t3376_calibration.csv](https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/PAPCA/3376/extras/t3376_calibration.csv)
- **History:** In 2014 Curtin's group first found the ~01:30 UTC signal on "one of six" IMOS stations in Perth Canyon, about 40 km west of Rottnest Island. A second IMOS station "at Scott Reef, off north-western Australia" (data recovered 3 Sep 2014) recorded a signal at **01:32:49 UTC**. Combining the data placed the source on the Carlsberg Ridge, judged geological. — [Nature blog, 5 Sep 2014](https://blogs.nature.com/blog/indian-ocean-signal-was-not-crash-of-flight-mh370/); [Scientific American](https://www.scientificamerican.com/article/hunt-for-malaysian-airliner-bolstered-by-new-clue1/)
- The ATSB told Senate Estimates (2015) that detailed analysis showed the Curtin acoustic event was incompatible with the satellite-to-aircraft range from the handshakes. — [ATSB answer, 1 Jun 2015](https://www.aph.gov.au/~/media/Committees/rrat_ctte/estimates/bud_1516/infra/ATSB_01062015.pdf)

### Inferences
- **The 2014 "Scott Reef" recorder is very likely the AODN PAKIM 3250 "Kimberley" deployment.** Three points support this:
  - It is the only IMOS recorder in NW Australia in the bucket for that period.
  - Its 01:30:00–01:35:08 window contains 01:32:49.
  - My quick look found a strong transient there (section 4).

  PAKIM sits at 15.48°S 121.25°E, about 170 km from Scott Reef proper (my estimate).
- **The duty cycle is 5 min on and 10 min off for these deployments, not "3–8 min".** Perth Canyon (on at :05/:20/:35/:50) and Kimberley/Portland (on at :00/:15/:30/:45) are offset by 5–10 min. Combining the sites therefore gives a different subset of each hour; across the three recorders, 00:00–02:00 is not continuously covered at any single site.
- Each calibration CSV appears to give whole-system sensitivity in dB re V/µPa against frequency. The −155 to −177 values, compared with the −196 dB hydrophone-only figure, imply about 40 dB of preamp gain. This is my interpretation and is not documented in the files I read.
- The press reports said the Perth Canyon station detected the Curtin event "just after 01:30". However, the open PAPCA 3376 file windows are 01:20:00–01:25 and 01:35:20–01:40:27, so no window covers 01:25–01:35:20. Either the press timing is loose, the RCS detection was in the 01:35:20 window, or Curtin used a different logger. My quick look at the 01:35:20 window showed only ≤4.4 dB fluctuations (section 4).

### Gaps
- I did not re-verify the AODN licence; the brief says CC BY. Check the AODN catalogue record before redistributing.
- I did not find Curtin's full technical report (the ATSB final report appendices are cited by Anderson) to confirm which logger and window the RCS detection used.
- I did not check the Portland (PAPOR) data. It is ~4,000 km from the 7th arc, likely shadowed by Australia's south-west coast, and of low priority.

---

## 2. Open seismic stations and T-phase detection on island seismometers

### Takeaway
Many relevant stations have open waveforms for 2014-03-08 00:00–02:00 UTC through FDSN with no login. They include Cocos, Christmas Island (two stations), Diego Garcia, Amsterdam, Kerguelen, Rodrigues (one at 100 Hz), Narrogin, Marble Bar, Giralia, the 13-element Pilbara array, Busselton (school station, 100 Hz) and nine Indonesian GEOFON stations, among them CISI only 90 km from Anderson's Java site. The CTBTO hydrophone and infrasound channels (H01, H08, I06AU, I04AU) are listed in the EarthScope metadata but return no data. Island seismometers record T-waves, but they are typically tens of dB less sensitive than SOFAR hydrophones and sample at only 20–40 sps. They are a poor substitute for HA01 for an M~3-equivalent surface impact more than 1,000 km away, but they are good at testing claims of larger events such as the 01:15 Java event.

### Cited Findings
- **Station inventory for the region 50°S–10°N, 60–130°E active on 2014-03-08** (the IRIS URL now redirects to service.earthscope.org) — [FDSN station query](https://service.iris.edu/fdsnws/station/1/query?minlat=-50&maxlat=10&minlon=60&maxlon=130&starttime=2014-03-08T00:00:00&endtime=2014-03-08T02:00:00&level=station&format=text). It lists:
  - **AU:** XMIS, XMI, GIRL, CARL, BLDU, MORW, RKGY, KLBR, MUN, MEEK, FORT, WRKA, FITZ, KNRA, the PSA00–PSAD3 Pilbara array, and the AU.H01W1–3 hydrophone metadata.
  - **IM:** H01, H08, I04, I06, I52.
  - **II:** COCO, DGAR, KAPI, PALK. **IU:** NWAO, MBWA.
  - **G:** AIS, PAF, ROCAM, RODM. **GE:** CISI, JAGI, SMRI, UGM, MNAI, PMBI, HMDM, KAAM and others.
  - **S1 school network:** AUBUS, AUCAR and others. **IN:** MNC. Plus MY, MS and TM stations.
- **Waveform availability, own ObsPy downloads 2026-11-05, window 2014-03-08 00:00–02:00 UTC.** These returned full 2-hour vertical-component data:

  | Data centre | Stations returned (channel, sps) |
  |---|---|
  | EarthScope | II.COCO.10.BHZ (40); II.DGAR 00/10.BHZ (20/40); AU.XMIS..BHZ (40); AU.XMI..BHZ (40); IU.NWAO 00/10.BHZ (20/40); IU.MBWA 00/10.BHZ (20/40) and 10.HHZ (100); AU.GIRL..BHZ (40); AU.PSA00.00.BHZ (40); II.KAPI (20/40); II.PALK.10.BHZ (40); S1.AUBUS HHZ/BHZ (100/10, with gaps); G.AIS/PAF/RODM .00.BHZ (20) |
  | [GEOFON](https://geofon.gfz.de/fdsnws/dataselect/1/) | GE.CISI, JAGI, SMRI, UGM, KAAM, MNAI, PMBI, MMRI, SOEI (all BHZ at 20) |
  | [RESIF](https://ws.resif.fr/fdsnws/dataselect/1/) | G.AIS 00.BHZ (20) and LHZ (1); G.PAF; G.RODM; G.ROCAM 00.BHZ (20) and **00.HHZ (100)**; G.CAN |
  | [AusPass](http://auspass.edu.au:8080/fdsnws/dataselect/1/) | S1.AUBUS (10/100); AU.XMIS BHZ (40) |

- **No data returned (HTTP 204):**
  - AU.H01W1, IM.H01W1, IM.H08S1, AU/IM.I06H1. This confirms the IMS hydrophone and infrasound waveforms are not public through FDSN, although the metadata are listed.
  - AU.CARL, AU.RKGY, IN.MNC, GE.HMDM, S1.AUCAR.
- The EarthScope `fdsnws/availability` service now returns "This service has been retired"; use dataselect or station `matchtimeseries` instead. — [EarthScope availability endpoint](https://service.earthscope.org/fdsnws/availability/1/query) (own query)
- **Stead (LANL, 2014) on station choice:** for near-surface sources the best records come from hydrophones, followed by near-shore seismometers recording T-phases. He found only three "open and readily available" stations (H01, H08, AIS). AIS was "a noisy site", and its 20 sps sampling (10 Hz Nyquist) "precludes examining the waveforms in the band of interest, 10–20 Hz". AIS noise bursts recur "several" times per hour. — [Stead LA-UR-14-24972](https://www.osti.gov/servlets/purl/1136454)
- **Hydrophone versus island seismometer:** hydrophones are much more sensitive than T-phase stations and give direction. A study at Ascension Island found hydrophone-to-seismometer signal ratios of about 20–40 dB at peak energy. (Per search snippet; record "Performance of an island seismic station for recording T-phases".) — [OSTI 289887 via openpolar](https://openpolar.no/Record/ftosti:oai:osti.gov:289887)
- **La Réunion OBS study:** T-phases on ocean-bottom seismometers resembled those at a coastal island station in waveform and duration, but T-phase magnitudes at the island stations were up to two orders of magnitude larger. — [EGU2016-6111](https://meetingorganizer.copernicus.org/EGU2016/EGU2016-6111.pdf)
- **Kadri 2024** shows that T-wave energy can cross land. The ARA San Juan explosion reached H03S after about 1,900 km over land at roughly 3.55 km/s, with amplitude only 11–21% of the water-path stations. — [Kadri 2024](https://www.nature.com/articles/s41598-024-60529-1.pdf)

### Inferences
- **Best open T-phase receivers for the 7th arc (25–41°S):**
  - AU.XMIS and XMI (Christmas I.) and II.COCO (Cocos, 40 sps): north of the arc.
  - G.AIS (20 sps): close to the southern end of the arc, about 470 km from 41°S 81°E.
  - S1.AUBUS (Busselton coast, 100 sps) and AU.GIRL (near Exmouth): WA coast conversion points.
  - AU.PSA Pilbara array (13 elements, 40 sps): the **only open seismic array** in the area. It can beamform back-azimuths of coastal T-phase conversions, although it is about 150 km inland.
  - G.ROCAM (100 sps): west, for Diego Garcia and Rodrigues paths.
- **Island seismometers cannot substitute for HA01 at the signal level Kadri reports.** Kadri implies ~0.5 Pa at HA01. Apply the 20–40 dB hydrophone-to-seismometer loss and the 10–20 Hz Nyquist limit, and such a signal would sit at or below noise on COCO, XMIS and AIS. This matches Stead's experience at AIS.
- **They are well suited to auditing larger claimed events** (M≥3.5 class), to calibrating travel times with catalogued earthquakes, and to coastal-conversion timing checks.

### Gaps
- I did not test the Malaysian (MY), Singapore (MS), Thai (TM) or Indonesian BMKG (IA) networks; IA is usually restricted.
- I did not test II.COCO location 00 or high-rate channels, or the AusPass temporary arrays of 2014 beyond S1.
- I found no Indian-Ocean-specific study quantifying island-seismometer versus IMS-hydrophone T-phase detection thresholds.

---

## 3. Coordinator add-on A: geometry and timing check of the HA01 bearings against the 7th arc

### Takeaway
The companion report is confirmed. Using a 7th arc checked against two published on-arc points, the 306.18° HA01 bearing crosses the arc **1,593 km** from HA01 at **25.7°S 101.4°E** (Kadri: 1,586 km). A crash at 00:19:29–00:21:30 would therefore arrive at about **00:37:25–00:39:26** at 1.48 km/s, about **15–17 min before** the observed 00:54:30. Bearing uncertainty (±0.4° to ±2°) moves the crossing by only 3–12 km, so the mismatch is robust. Kadri addressed this himself: a link to MH370 would require the aircraft to stay airborne at least 10 min, and in practice about 13–17 min, after the last handshake. By contrast, Stead's **246.9°** arrival at ~00:52 has timing consistent with a 7th-arc impact at **~41°S 81°E**, while Kadri's faint **268.24°** arrival at 00:39:02 is about 1 min too early for c ≤ 1.50 km/s.

### Cited Findings
- **Kadri 2024 (Methods):**
  - "The only major signal has a bearing of 306.18°, and it is recorded at 00:54 UTC. In that direction the distance of the 7th arc from H01W is R7 = 1586 km".
  - At c = 1,500 ± 70 m/s the travel time is 17.45 ± 0.65 min, leaving an extra 17.02 ± 0.65 min.
  - "the aircraft must have remained in air for at least 10 min prior to impacting"; even at an implausibly fast average velocity it needs "about 13 min after the last handshake, and travel an extra distance of about 350 km".
  - Table 1 lists 00:54:30 at 306.18° with Δt +17.10 min, and 00:39:02 at 268.24° as "the only signal with Δt = 0", described as faint.
  - Kadri's bearing accuracy is ±0.4° (99.5% CI).
  - Source: [Kadri 2024](https://www.nature.com/articles/s41598-024-60529-1.pdf)
- **Stead 2014:**
  - Signals at 3114–3130 s after 00:00 (00:51:54–00:52:10).
  - A late, dispersive ice-type arrival at a DOA of 190.5° and 1.46 km/s.
  - An earlier weak arrival that he manually aligned to a DOA of **246.9°**, with phase velocity fixed at 1.46 km/s.
  - "may point to a more southerly impact location". — [Stead](https://www.osti.gov/servlets/purl/1136454)
- **HA01 element coordinates** (W1 −34.8929, 114.1539; W2 −34.89708, 114.13403; W3 −34.88093, 114.13998; depths about 1,046–1,063 m) — [FDSN station metadata](https://service.iris.edu/fdsnws/station/1/query?minlat=-50&maxlat=10&minlon=60&maxlon=130&starttime=2014-03-08T00:00:00&endtime=2014-03-08T02:00:00&level=station&format=text)
- **7th-arc reference point:** the IG/UGIB analysis gives 34.2342°S 93.7875°E at 20,000 ft for BTO 18,422 µs. This comes from a search-result summary of Radiant Physics material, which I did not open. — [Radiant Physics](https://mh370.radiantphysics.com/?p=1598)
- Iannello describes Anderson's 8.36°S 107.92°E as "directly on the 7th Arc". — [Radiant Physics, 10 Mar 2026](https://mh370.radiantphysics.com/2026/03/10/a-candidate-site-for-mh370-that-can-be-searched-quickly-and-soon/)

### Inferences
**Own calculation (WGS84 geodesics, pyproj and ObsPy):**
- **Method.** I built the BTO ring with BTO 18,400 µs, bias −495,679 µs and the Perth GES at −31.8023, 115.8895. I fitted the satellite latitude (0.74°N at 64.52°E) so that the ring passes through 34.2342°S 93.7875°E at 6.1 km altitude. The calibrated ring falls within about 8 km of Anderson's on-arc site and reproduces Kadri's R7 to within 7 km, which validates the ring shape from 8°S to 34°S.
- **Sea-level arc points:** 39°S 86.07°E; 34°S 93.93°E; 30°S 98.09°E; 26°S 101.18°E; 24°S 102.44°E; 20°S 104.51°E; 15°S 106.41°E; 10°S 107.70°E.
- **Kadri 306.18° arrival (HA01 00:54:30):**
  - Arc crossing at 1,593 km, 25.72°S 101.36°E. The crossing is 1,590–1,595 km for ±0.4° and 1,582–1,605 km for ±2°.
  - Expected arrival for a crash at 00:19:29–00:21:30: 00:37:25–00:39:26 at c = 1.48 km/s, or 00:37:11–00:39:12 at 1.50 km/s.
  - The source position implied by an origin on the arc is 00:36:34. To match 00:54:30 with a crash at 00:20:30, the source would have to lie about 3,019 km out at about 16.7°S 91.6°E, roughly 960 km off the arc on the far side from HA01. That is inconsistent with the BTO and with fuel exhaustion.
- **Kadri 268.24° arrival (00:39:02):**
  - Arc crossing at 1,835 km, 33.75°S 94.22°E.
  - Implied origin 00:18:22–00:18:39 at c = 1.48–1.50, which is before the 00:19:29 and 00:19:37 transmissions. That is physically impossible unless effective speed exceeds about 1.56 km/s or part of the path is seismic.
  - It is close to the IG/UGIB area, so it is worth checking at Perth Canyon, though the predicted Perth Canyon arrival of about 00:40:24 falls about 16 s after that window closes.
- **Stead 246.9° arrival (~00:52:02):**
  - Arc crossing at 2,954 km, 40.98°S 81.21°E.
  - Implied origin 00:18:46 at 1.48 km/s or 00:19:13 at 1.50, consistent with a crash at about 00:19–00:21 given the speed uncertainty.
  - The bearing is nearly tangent to the arc, so ±2° moves the crossing between 40.0°S 83.7°E and 42.0°S 77.7°E.
  - G.AIS (open, ~470 km away) should see any T-phase at about 00:24, and Perth Canyon at about 00:54:30, which is inside the 00:50–00:55 window.
- **Curtin/Kadri 301.4° arrival (HA01 01:34:40):** arc crossing at 1,572 km, 26.7°S 100.7°E, with implied origin about 01:17 if on the arc. That is roughly 57 min after the last handshake, which is why the ATSB rejected it.
- **Did Stead and Kadri address the timing?**
  - Kadri explicitly quantified the roughly 17-min offset and argued for continued flight.
  - Stead said only that the ~00:52 arrival time "could be consistent", without computing ranges.
  - The two papers also disagree about the ~00:52 group. Kadri lists major signals at 00:52 with bearing 57°, plus 320–330°, 274.8° and 257.6° picks, but no 246.9°. Stead lists 246.9° plus a 190.5° ice event. The analyses are not reconcilable without the IMS waveforms.

### Gaps
- My satellite position is a calibration fit, not an ephemeris. Uncertainty of the ring is roughly ±10–20 km away from the calibration points.
- Group velocity is assumed constant at 1.475–1.50 km/s. No range-dependent ocean model was run, and mixed water/crust paths could shorten times by tens of seconds.

---

## 4. Ed Anderson / 370Location: data, method, claim, critiques, Iannello (March 2026), and an open-data quick check

### Takeaway
Anderson claims an uncatalogued event at **01:15:18 UTC** at **8.36°S 107.92°E**, directly on the 7th arc about 42 miles off Java. He says it was seen on "at least 40 regional seismometers using public data" and on HA08 at 01:59:20. Since 2018 he has interpreted it as a possible implosion of the sinking wreck about 55 min after impact. My quick look at open data confirms a real seismic event at that time. However, its amplitude, compared with a catalogued M4.1 nearby that night, implies roughly M4.3, which is energetically far too large for a 777 impact. That supports the "energy too high" critique. Iannello (10 Mar 2026) endorsed searching the site as an opportunity, while stating it is "impossible to definitively relate this acoustic event to MH370".

### Cited Findings
**Anderson's claim (370location.org, 2018)**
- "A Strong Anomalous Acoustic Event on the Seventh Arc near Java" (published 2018-02-21, updated 2024-07-27): event at 1:15:18 UTC, "almost an hour after the expected impact time".
- Location 8.36S 107.92E, "directly on the 7th Arc", placed by "analysis of nearby seismometers". No station codes or data centres are named.
- "four times stronger on local seismometers than a nearby M4.1 quake"; "not included in earthquake catalogs"; "may be evidence of an implosion". The signal reached HA08 from the direction of Java.
- Source: [370location 2018 post](https://370location.org/2018/02/a-strong-anomalous-acoustic-event-on-the-seventh-arc-near-java/)

**Anderson's letter of 9 Mar 2026 (summarized on Radiant Physics)**
- Epicentre "likely accurate to within 2-3 km". HA08 arrival 01:59:20. A weaker 1.2 Hz arrival about 6 min after the last ping.
- Data sources:
  - HA08 and HA01 (CTBTO, not public).
  - "IMOS Scott Reef".
  - Seven French hydrophones near Amsterdam I. (unpublished Brest report LDO-201608).
  - A towed array near Exmouth.
  - Curtin analyses in ATSB final-report appendices.
  - "at least 40 regional seismometers" using public data.
- He says the sound entered the SOFAR channel by reflecting off the Java coast, and he reinterprets Curtin's "301.6" signal as the Java event reflected off the 90°E Ridge.
- For the flight path he invokes a low, slow BTO-matching path at "oxygen altitude" and an earlier flaperon arrival from a 2025 barnacle analysis.
- Source: [Radiant Physics, 10 Mar 2026](https://mh370.radiantphysics.com/2026/03/10/a-candidate-site-for-mh370-that-can-be-searched-quickly-and-soon/)

**Iannello's assessment (10–12 Mar 2026)**
- Anderson's "mathematical analysis localizing the acoustic event has not been challenged", "although it is impossible to definitively relate this acoustic event to MH370".
- The site is further north on the arc than most investigators think likely.
- He frames it as a small, near-shore, good-weather area possibly searchable under the current Ocean Infinity contract ("That's my recommendation"; "It's possible we're done"). — [same post](https://mh370.radiantphysics.com/2026/03/10/a-candidate-site-for-mh370-that-can-be-searched-quickly-and-soon/)

**Critiques in the comments (11–16 Mar 2026)**
- "Viking": "the most serious problem with your site is that the energy release is too high"; later "It must have been a meteor". He also argued the roughly 50-min gap is too long for sinking.
- "Andrew": step-climbs are incompatible with an incapacitated crew.
- Others questioned the drift and WSPR methods.
- Source: [same post (comments)](https://mh370.radiantphysics.com/2026/03/10/a-candidate-site-for-mh370-that-can-be-searched-quickly-and-soon/)

**Calibration earthquake**
- USGS catalogues an **M4.1 at 2014-03-07 23:52:18.6 UTC, −9.6744, 108.4193, 34 km depth, "243 km SSW of Kroya"** (ISC: mb 4.04, 23:52:17.6, −9.5511, 108.4208, "South of Jawa").
- No event near 8.36°S 107.92°E at about 01:15 appears in either the USGS or the ISC (including IDC/BMKG contributions) catalogue for 22:00–03:00.
- Sources: [USGS query](https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2014-03-07T18:00:00&endtime=2014-03-08T03:00:00&minlatitude=-60&maxlatitude=15&minlongitude=40&maxlongitude=140&minmagnitude=2); [ISC query](http://www.isc.ac.uk/fdsnws/event/1/query?starttime=2014-03-07T22:00:00&endtime=2014-03-08T03:00:00&minlatitude=-60&maxlatitude=15&minlongitude=40&maxlongitude=140&format=text) (own queries 2026-11-05)

**Own quick look, open seismic data, 2–8 Hz.** Values are 5-s peak |amplitude| divided by the record median, from [GEOFON](https://geofon.gfz.de/fdsnws/dataselect/1/) and [EarthScope](https://service.earthscope.org/fdsnws/dataselect/1/):

| Station | M4.1 quake window | 01:15–01:22 window | Background max, 00:30–01:10 |
|---|---|---|---|
| GE.CISI (90 km from Anderson site) | 7.7× at 23:53:30 | **371×** at 01:15:40 | 13.8× |
| AU.XMIS (342 km; ~316 km from the M4.1) | 16.4× | **28×** at 01:16:45 | 2.0× |
| II.COCO | 3.1× | 4.2× | 4.4× (not significant) |
| GE.JAGI | 6.3× | 4.0× | 3.6× |

**Own quick look, open IMOS Kimberley file** [PAKIM/3250/20140308/raw/531A7289.DAT](https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/PAKIM/3250/20140308/raw/531A7289.DAT), window 01:30:00–01:35:08, calibrated with t3250_calibration.csv:
- Median band level about 97 dB re 1 µPa (10–40 Hz, 2-s RMS).
- A **+22 to +24 dB transient at ~01:32:56–01:33:06 UTC** in the 10–60 Hz bands.
- A separate +25 dB 5–15 Hz spike at 01:30:18 of unknown origin.

### Inferences
- **A real, uncatalogued seismic event did occur near Anderson's site at about 01:15 UTC.** CISI shows a huge peak at 01:15:40, consistent with an S wave 90 km from an origin at about 01:15:18. XMIS shows a 01:16:45 peak, consistent with S/Lg at 342 km.
- **Magnitude and energy.** At XMIS the two sources are at similar distances (~316 vs 342 km). The 01:15 event's amplitude is about 1.7 times the M4.1's, giving roughly **M≈4.3** by amplitude scaling. Using log E = 1.5M + 4.8, that is about 1.8×10¹¹ J (about 180 GJ). This is about 45 times Kadri's 4 GJ kinetic energy for a 200 t aircraft at 200 m/s, and seismic coupling from a surface impact is far less efficient than an earthquake's. On amplitude grounds the event is more consistent with a natural shallow earthquake (Java forearc) than with an impact. My rough estimate of the energy of air-volume collapse for a sinking fuselage (pressure × volume, ~10 GJ at ~1 km depth) also falls far short of the radiated energy. This rough figure supports Viking's critique.
- **Kimberley "Scott Reef" signal.**
  - Predicted pure-water T arrival at PAKIM for the Java origin (1,651 km): 01:33:54 at 1.48 km/s, or 01:33:39 at 1.50.
  - Observed: ~01:32:49–01:32:56, about 45–65 s earlier. That is explainable if around 100 km of the path is crustal (my assumption).
  - So the Kimberley transient, Curtin's "Scott Reef 01:32:49", could be the Java event's T-phase. That would mean the 2014 Curtin association of the Perth Canyon, HA01 and Scott Reef detections into one Carlsberg-Ridge source may have mixed events. This needs testing.
- **The Java event cannot explain the HA01 01:34:40 arrival at 301.4°.** The direct Java-to-HA01 path is 3,006 km, giving an earliest T arrival of about 01:49:09. Any reflected path is longer, so a 01:15:18 source cannot produce a 01:34:40 HA01 arrival. Anderson's "301.6" reinterpretation must refer to something else, or it fails on timing.
- **Most of Anderson's hydroacoustic inputs are not open** (HA08 and HA01 waveforms, the French report, the towed array). The seismic part and the IMOS Kimberley record can be replicated openly.

### Gaps
- Anderson's station list, picks and location method are not on the pages I read. He mentions Google Drive folders in comments (12–13 Mar 2026), which I did not access.
- I made no formal location or magnitude estimate. My amplitude comparison uses one band and a crude envelope measure.
- I could not read beyond the first ~100 kB of the Radiant Physics page, which runs to 778k characters, so later critiques (after 16 Mar 2026) were not reviewed.

---

## 5. Stead (LANL 2014) and Kadri (Sci Rep 2024): details that matter for open replication

### Takeaway
Both studies rest on IMS hydrophone data that cannot be shared, as Kadri states explicitly. What can be replicated openly:
- Stead's AIS analysis.
- Kadri's earthquake bearing checks, using catalogue events plus open seismometers.
- The timing predictions of every candidate bearing, tested against IMOS windows and island stations.

Kadri's entropy-plus-cross-correlation pipeline is fully described and can be applied to IMOS and seismic data.

### Cited Findings
**Stead, R.J., "Seismic and hydroacoustic analysis relevant to MH370", LA-UR-14-24972, issued 2014-07-03** (OSTI 1136454, DOI 10.2172/1136454). — [OSTI record](https://www.osti.gov/biblio/1136454); [PDF](https://www.osti.gov/servlets/purl/1136454)
- He scanned about 2 h of broadband H01 data and used octave bands of 5–10, 8–16, 10–20, 16–32 and 20–40 Hz. He analysed in 10–20 Hz.
- H01 element spacing is about 2 km. Early arrivals were incoherent across the elements, so he aligned four peaks manually.
- H08 (south array) was swamped by two repeating broadband sources. One repeated every 10 s at DOA 29.8° and 1.485 km/s; the other every 8 s at about 117°. They are anthropogenic (airgun) or biogenic.
- H08 north is blocked by Diego Garcia island.
- For AIS he used 2–9 Hz with polarization analysis; the expected DOA was about 137°. A noise burst at about 00:36 came from about 40°.
- Conclusion: a candidate at only a single station, possibly "toward the southern portion" of the search area. He calls the southern Indian Ocean "insufficiently monitored".

**Kadri, U., "Underwater acoustic analysis reveals unique pressure signals associated with aircraft crashes in the sea: revisiting MH370", Sci. Rep. 14:10102 (2024)**, received 16 Oct 2023, accepted 24 Apr 2024. — [Sci Rep PDF](https://www.nature.com/articles/s41598-024-60529-1.pdf)
- He used about 100 h of CTBTO data. Hydrophones sample at 250 Hz. Processing used a high-pass below 5 Hz and a 2–40 Hz band-pass.
- Detection uses a windowed entropy of a few seconds, stepped every 0.5 s, with a threshold of 2.3×10⁴. Bearing comes from cross-correlation time differences across the triangle (Eq. 3), quoted at ±0.4°.
- The table of signals at H01W from 00:36 UTC lists 19 picks. Examples: 00:38:29 at 261.24°, 00:39:02 at 268.24°, 00:40:34 at 303.28°, 00:51:50 at 320.40°, 00:54:30 at 306.18°, 00:55:07 at 314.15°.
- The 306° signal was not seen at H08S. There, airgun noise of 2–4 Pa from bearing 210° exceeds the expected 0.5 Pa.
- He used two calibration earthquakes:
  - M4.8 near Yōkaichiba, Japan, 2014-03-07 18:34:20: bearing at H11S matched to 311.83° versus 311.827°.
  - M2.7 85 km NE of Sinabang, Indonesia, 18:55:12: at H08S he measured 63.7° against a true 67.12° (3.3° off, about 140 km).
- Kadri also cites the 01:34:40 signal at 301.4 ± 0.4°. A later study by his refs 3 and 13 placed it 1,900 ± 200 km from H01W, centred at −23.662°, 96.676°, with source time 01:11–01:16 UTC.
- Data availability: "obtained from the CTBTO and cannot be shared … can be requested … through the virtual Data Exploitation Center (vDEC)".
- He recommends controlled explosions or airguns along the 7th arc to calibrate.

### Inferences
- Kadri's chance-coincidence argument (a signal "occurring by chance … is less than 3%") assumes a narrow window around the expected time. The 306° signal falls about 17 min outside the physically expected window (section 3), so that probability argument does not straightforwardly apply.
- Kadri's ref-13 location for the 01:34:40 signal (source 01:11–01:16, about 1,900 km out) and Anderson's 01:15:18 Java event share similar origin times but different places. The open seismic data in section 4 show the Java event is real, so the possibility that the two candidates are related should be tested rather than assumed.

### Gaps
- I did not extract Kadri's supplementary S1 (crash metadata) or the pressure amplitudes of the individual historical crashes. Only the AF447-to-F-35 ratio (75%) and the 0.5 Pa expectation are in the main text.

---

## 6. Coordinator add-on B: the OHASISBIO (Royer, CNRS/Brest) hydrophone report and data access

### Takeaway
Royer's report is about 18 pages, written in late 2016 and sent to French and Australian authorities. It became public through Popular Mechanics on 16 July 2026. It tentatively identified **five acoustic events** on the morning of 8 March 2014, but **no impact near the 7th arc**. The Northeast Amsterdam hydrophone, the one closest to the arc, was lost during recovery. OHASISBIO **raw waveforms for 2014 are not openly downloadable**. SEANOE holds only derived whale-call detection tables (CC BY-NC 4.0), so raw data would require a request to Geo-Ocean/Royer, not a free download. I found no public 2014 mooring coordinates.

### Cited Findings
**Report content and release (Jeff Wise, Popular Mechanics, 16 Jul 2026, reposted 19 Jul 2026)** — [jeffwise.net repost](https://www.jeffwise.net/?p=7076); [Popular Mechanics original](https://www.popularmechanics.com/flight/airlines/a71923663/mh370-missing-plane-search-new-clue/)
- In 2014 the network had "eight autonomous hydrophones at six sites", in waters near Crozet and Kerguelen, the Madagascar Basin and the Southeast Indian Ridge.
- The report: "18 pages of maps, spectrograms, arrival times, and careful conclusions", sent to French and Australian officials in late 2016.
- Five events were "tentatively identified". Two were already reported in CTBTO-based work, and one is an ice event far to the south.
- The hydrophones "didn't detect an impact near the seventh arc". Royer: it "didn't bring any new information relative to the CTBTO data".
- The Northeast Amsterdam hydrophone was lost during recovery by RV Marion Dufresne.
- Royer provided the file to Popular Mechanics; no public link is given.

**Other coverage and Anderson's citation**
- Drew Ponder's Substack (26 Jul 2026, paywalled): "Newly released hydrophone data recorded no convincing MH370 impact near the seventh arc". — [Substack](https://drewponder406.substack.com/p/newly-released-hydrophone-data-recorded)
- Anderson's letter cites "seven French hydrophones near Amsterdam Island (unpublished Univ. of Brest report LDO-201608)". — [Radiant Physics](https://mh370.radiantphysics.com/2026/03/10/a-candidate-site-for-mh370-that-can-be-searched-quickly-and-soon/)
- A search-result summary of Anderson's blog dates the report **22 December 2016**. That date was a search snippet I did not verify.

**Cruise and deployment**
- Cruise VT 135 / OHA-SIS-BIO-6 (DOI 10.17600/14002600), Marion Dufresne, **6 Jan–19 Feb 2014**, chief scientist J.-Y. Royer. It retrieved 7 moorings and deployed 8 autonomous hydrophone moorings, which were in place on 8 Mar 2014.
- The cruise text says "7 autonomous hydrophones on 5 sites, including a 3-hydrophone antenna with elements 30 km apart". There is no site list or coordinates in text form, only map images.
- Data archiving is through SISMER (sismer@ifremer.fr). The technical report is DOI 10.13155/114374.
- Source: [Cruise page](https://campagnes.flotteoceanographique.fr/campagnes/14002600/)
- Hydrophones sit at about 1,000–1,300 m depth on seabed-anchored lines; the network is described as 9 sites and 10 instruments in later years. — [IUEM](https://www-iuem.univ-brest.fr/observation/offshore-observation/nis-ohasisbio/); [Geo-Ocean](https://www.geo-ocean.fr/en/Expertise/Observation/Offshore-observation/OHA-SIS-BIO-in-the-Indian-Ocean)

**Open data**
- SEANOE 10.17882/46124 (Leroy, Royer, Bonnel, Samaran, Sep 2016, **CC BY-NC 4.0**) holds only CSV Antarctic blue whale Z-call detections and noise metrics, not raw waveforms. It lists the observatory DOI 10.18142/229. — [SEANOE 46124](https://www.seanoe.org/data/00350/46124/)

### Inferences
- I could not confirm the "~22 October 2026" public-release date from the coordinator. The earliest public disclosure I found is Popular Mechanics, 16 July 2026, and the "22 December 2016" date belongs to the report itself. The October date may be a confusion of these.
- OHASISBIO is the only long-range SOFAR hydrophone set besides the IMS that recorded the night of 8 March 2014. It is "open" only in the sense that one can request it, so it falls outside a strict free-download scope.
- The 2016 OHASISBIO whale papers (Leroy et al. 2016, PLoS ONE 10.1371/journal.pone.0163587) are the most likely open source of site coordinates for 2014.

### Gaps
- I found no public copy of the Royer report and no mooring coordinates or sample rate for 2014. I could not access the Slate.fr coverage (HTTP 403).

---

## 7. Public calibration events on 7–8 March 2014

### Takeaway
Several catalogued earthquakes that night can calibrate travel times, back-azimuths and amplitudes on the open stations and the IMOS recorders. The most useful are the M4.1 south of Java at 23:52, roughly 150 km from Anderson's site, the mb 3.7 Mauritius–Réunion event at 23:07 near Rodrigues, and the M4.5 on the western Indian–Antarctic Ridge at 20:36. Kadri's two bearing-validation quakes (Japan M4.8 and Sinabang M2.7) and Stead's Antarctic ice event at HA01 (DOA 190.5°, ~00:52) are documented, but only the earthquakes can be used with open data.

### Cited Findings
- **USGS catalogue, 2014-03-07 18:00 to 2014-03-08 03:00, 60°S–15°N, 40–140°E, M≥2.** — [USGS query](https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2014-03-07T18:00:00&endtime=2014-03-08T03:00:00&minlatitude=-60&maxlatitude=15&minlongitude=40&maxlongitude=140&minmagnitude=2)

  | Time (UTC) | Lat | Lon | Mag | Region |
  |---|---|---|---|---|
  | 2014-03-07 18:55:12 | 3.0715 | 96.8734 | M2.7 | Sinabang |
  | 2014-03-07 19:36:35 | −5.6858 | 134.0275 | M4.0 | Tual |
  | 2014-03-07 20:17:57 | −6.0019 | 125.5838 | M4.7 | 555 km deep |
  | **2014-03-07 20:36:06** | **−49.0178** | **123.3764** | **M4.5** | western Indian-Antarctic Ridge |
  | **2014-03-07 23:52:18** | **−9.6744** | **108.4193** | **M4.1** | S of Java |
  | 2014-03-08 01:13:09 | 2.3862 | 128.1896 | M4.1 | Halmahera |

- **ISC adds:** — [ISC query](http://www.isc.ac.uk/fdsnws/event/1/query?starttime=2014-03-07T22:00:00&endtime=2014-03-08T03:00:00&minlatitude=-60&maxlatitude=15&minlongitude=40&maxlongitude=140&format=text)
  - **IDC 2014-03-07 23:07:54, −20.3681, 66.6171, mb1 3.70, "Mauritius-Reunion region"**
  - IDC 23:27:16 Banda Sea, mb 3.6
  - ISC 00:22:02 Talaud Islands, mb 3.37
  - IDC 00:56:53 Banda Sea, ML 3.8
- **Kadri's calibration earthquakes:** M4.8 Japan at 18:34:20 (H11S) and M2.7 Sinabang at 18:55:12 (H08S, 63.7° measured versus 67.12° true). He also reports airgun noise at H08S from 210°. — [Kadri 2024](https://www.nature.com/articles/s41598-024-60529-1.pdf)
- **Stead's interfering signals:** an Antarctic ice event at HA01 (DOA 190.5°, ~00:52), and repeating 10-s and 8-s signals at H08 from 29.8° and about 117°. — [Stead](https://www.osti.gov/servlets/purl/1136454)

### Inferences
- The **M4.1 at 23:52** is the best amplitude and travel-time reference for the Java claim. It is recorded on CISI, XMIS, JAGI and COCO (section 4).
  - Its T-phase should reach PAKIM (about 1,500 km away) at roughly 00:09–00:10.
  - That probably falls in PAKIM's 00:05–00:15 off-period. PAKIM file 0x531A5D79 starts at 23:59:53, giving a window of about 00:00–00:05; the next window is 00:15–00:20. So it is likely unusable at Kimberley, but verify.
- The **M4.5 Indian–Antarctic Ridge event at 20:36** lies about 2,000 km south of Perth Canyon (rough estimate).
  - Its T-phase at Perth Canyon would arrive about 23 min after origin, around 20:59. That is probably in the 20:55–21:05 off-period, so check the 7 March file headers.
  - If any catalogued event does land in a PAPCA or PAKIM window, it gives an empirical detection threshold (dB per magnitude) for the open recorder, against which the expected MH370 levels can be scaled. Extend the catalogue search to 1–14 March to find such events.
- The **IDC mb 3.7 Mauritius–Réunion event (23:07)** calibrates the G.RODM/ROCAM (100 Hz) and II.DGAR paths.
- I found no public airgun-survey notices or controlled sources for that night.

### Gaps
- Arrival times of these events at the IMOS windows were not computed or checked. No ice-event catalogue for that night was found.

---

## 8. Energy scaling: 777 impact source level against detection at thousands of km

### Takeaway
Kadri's estimates: a 200 t aircraft at 200 m/s carries about 4 GJ (≈956 kg TNT, "magnitude 3.2"); at 100 m/s about 1 GJ (M2.8); at 30 m/s about 89 MJ (M2.1). His 10 historical crashes were detected on CTBTO hydrophones at **2,211–4,695 km**. At HA01 he expects a signal near **0.5 Pa**, and the open Perth Canyon recorder's ambient level in the relevant band is about 95–101 dB re 1 µPa (0.06–0.11 Pa). So a 0.5 Pa arrival would stand roughly 13–19 dB above noise at Perth Canyon if propagation there were comparable, but signals ~10–20 dB weaker would be lost.

### Cited Findings
- **Energies:** "An aircraft with a mass of 200 tons impacting the water surface at a velocity of 200 m/s possesses a kinetic energy of 4 GJ, equivalent to 956 kg of TNT or an earthquake of magnitude 3.2". At 100 m/s: 1 GJ, 239 kg TNT, M2.8. At 30 m/s: 89 MJ, 21 kg TNT, M2.1. — [Kadri 2024](https://www.nature.com/articles/s41598-024-60529-1.pdf)
- **Crash dataset** (distances 2,211–4,695 km): F-35A, Transair 810 and Asiana 991 (H11N/S); Yemenia 626 (H08N/S); AB Aviation 1103 and Sriwijaya 182 (H08S); AirAsia 8501 (H01W); Lion Air 904 (H01W and H08S); AF447 (H10S, about 2,200 km).
  - The F-35A signal was 6 s long and seen at both H11 stations more than 3,300 km away.
  - AF447's pressure reached 75% of the F-35A value at 2,200 km.
  - Three signature types: sharp energetic, longer-duration, and uncertain.
  - The 7th arc is about 1,600 km from H01W and about 3,700 km from H08S.
  - Source: [Kadri 2024](https://www.nature.com/articles/s41598-024-60529-1.pdf)
- **Expected levels:** the expected pressure at H08S, if similar to H01W, would be 0.5 Pa, against airgun noise of 2–4 Pa. — [Kadri 2024](https://www.nature.com/articles/s41598-024-60529-1.pdf)
- **Own measurement, IMOS PAPCA 2014-03-08 00:50:01–00:55:01**, calibrated with t3376_calibration.csv: median 2-s RMS band levels were 95.5 dB re 1 µPa (5–15 Hz and 8–20 Hz), 97.5 dB (10–40 Hz) and 101.1 dB (20–60 Hz). The spectrogram is dominated by a tonal band at about 45–50 Hz with harmonics, probably whale song or a ship. — [file](https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/PAPCA/3376/20140308/raw/531A6929.DAT); [calibration](https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/PAPCA/3376/extras/t3376_calibration.csv)

### Inferences
- **Quick-look result for the 306° and 246.9° predictions at Perth Canyon:** the only excess in the 00:50–00:55 window is +6 to +8 dB in 5–20 Hz at **00:53:11–00:53:25**. That coincides with the predicted Perth Canyon arrival (~00:53:23) for a source at Kadri's 306° arc crossing. However, the spectrogram suggests a narrowband ~10–12 Hz feature rather than an impulsive broadband arrival, and there is no comparable excess at 00:54:30 (Stead 246.9°). Treat this as an unverified coincidence until checked against other days, whale-call templates and ship tracks.
- **The expected MH370 level at Perth Canyon is uncertain.** The recorder sits at 390 m on the canyon slope, above a SOFAR axis of roughly 1,000 m. A coupling loss of 10–20 dB relative to HA01, which is at about 1,050 m, is plausible (my assumption). That would put a 0.5 Pa (114 dB) HA01-equivalent signal at 94–104 dB, comparable to ambient. **A non-detection at Perth Canyon is therefore only weakly diagnostic, while a detection would be significant.**
- **For seismometers:** an aircraft impact equivalent to M2–3.2 at 1,500–3,000 km, converted to T-phase at island coasts with 20–40 dB extra loss, is well below detection on 20–40 sps island seismometers (inference). An M~4.3-equivalent event such as the Java 01:15 one is easily detected, which is itself evidence against an impact source.

### Gaps
- Kadri's per-crash pressure amplitudes and source levels are not tabulated in the main text. I found no published source level in dB re 1 µPa at 1 m for a 777 impact.

---

## 9. Concrete open-data analysis plan (tools, steps, expected sensitivity)

### Takeaway
All of the following can be done with free downloads and ObsPy/NumPy/SciPy/pyproj, with no logins (I tested this on 2026-11-05):
1. Use the IMOS raw files (PAPCA, PAKIM, PAPOR) for 7–8 March plus control days.
2. Use open seismic waveforms from EarthScope, GEOFON, RESIF and AusPass.
3. Use the USGS and ISC catalogues for calibration.
4. Use predicted-arrival tables for each candidate (section 3) to check which windows can confirm or refute each hypothesis.

The highest-value open tests are:
- (a) Verify the Kimberley 01:32:56 transient and attribute it either to the Java 01:15 event or to the Curtin/Carlsberg source, using relative timing across PAKIM, COCO, XMIS, DGAR and PSA.
- (b) Vet the Perth Canyon 00:53:11–00:53:25 excess against the Kadri-306° prediction.
- (c) Locate the Java 01:15 event and estimate its magnitude from about 15 open stations against the M4.1 at 23:52.

### Cited Findings
- **Free data endpoints**, all verified working on 2026-11-05:
  - IMOS: S3 HTTPS listing and download — [AODN S3](https://imos-data.s3-ap-southeast-2.amazonaws.com/?list-type=2&prefix=IMOS/ANMN/Acoustic/)
  - EarthScope dataselect, where the IRIS URL redirects — [dataselect](https://service.earthscope.org/fdsnws/dataselect/1/)
  - [GEOFON](https://geofon.gfz.de/fdsnws/dataselect/1/)
  - [RESIF](https://ws.resif.fr/fdsnws/dataselect/1/)
  - [AusPass](http://auspass.edu.au:8080/fdsnws/dataselect/1/)
  - [USGS events](https://earthquake.usgs.gov/fdsnws/event/1/); [ISC events](http://www.isc.ac.uk/fdsnws/event/1/)
- **Reader:** the official MATLAB reader is [NL_load_logger_data_new.m](https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic/code/NL_load_logger_data_new.m). The Python equivalent I used reads the 5 header lines, then `np.frombuffer(..., '>u2')` for 300 s × 6,000 samples, converts with `(x - mean) * 5/65536` V, and divides by the calibration curve (dB re V/µPa) per frequency.
- **Detection and bearing method to emulate:** windowed entropy (a few seconds long, 0.5 s step) plus cross-correlation time differences across an array. — [Kadri 2024](https://www.nature.com/articles/s41598-024-60529-1.pdf)
- **Bands and polarization:** octave bands from 5–40 Hz, and 3-component polarization at a single station (AIS). — [Stead](https://www.osti.gov/servlets/purl/1136454)

### Inferences
Recommended plan. Steps are numbered; the sub-bullets are details.

**Step 0. Environment.**
- Create a venv and run `pip install obspy pyproj` (ObsPy brings SciPy and Matplotlib).
- Keep downloads in per-source directories.

**Step 1. IMOS acquisition.**
- Sites, deployments and days:
  - PAPCA 3376: 2014-03-07, -08 and -09.
  - PAKIM 3250: same days.
  - PAPOR 3274: optional.
  - Control days: 2014-03-01 to 03-14, for false-alarm statistics.
- Download size is 96 × 3.7 MB, about 355 MB per site-day. Fetch only the 00:00–03:00 files for a first pass, which is about 45 MB per site-day.
- Parse each footer for the exact UTC start, with the fraction of a second in 1/65536 s units.

**Step 2. Predicted-window table.** For each hypothesis compute arrival times at PAPCA, PAKIM, COCO, XMIS, XMI, AIS, DGAR, RODM/ROCAM, GIRL, AUBUS and PSA. Use c = 1.475–1.50 km/s for water legs and ak135 for crustal or seismic legs. The hypotheses:

| Hypothesis | Source location | Origin (UTC) |
|---|---|---|
| Kadri 306° | 25.72°S 101.36°E | 00:36:34 |
| Kadri 268° | 33.75°S 94.22°E | ~00:18:30 |
| Stead 247° | 40.98°S 81.21°E | ~00:19 |
| Curtin 301° | 26.7°S 100.7°E | ~01:17 |
| Anderson Java | 8.36°S 107.92°E | 01:15:18 |
| Generic 7th-arc grid | 7th arc, 1° steps | 00:19:29–00:22:00 |

Already computed (c = 1.48):
- Kadri 306° → PAPCA 00:53:23 (inside the window), PAKIM 01:03:07 (window 01:00–01:05).
- Stead 247° → PAPCA 00:54:30 (inside), AIS ~00:24.
- Java → PAKIM 01:33:54 (inside 01:30–01:35), PAPCA 01:45:43 (not covered), HA01 01:49:09, H08S 01:59:18, XMIS T ~01:19:09.

**Step 3. IMOS detection.**
- Calibrate to µPa.
- Run spectrograms (1–2 s windows, 5–150 Hz), band-RMS envelopes at 5–15, 8–20, 10–40 and 20–60 Hz, and an entropy or STA/LTA detector.
- Classify detections against whale-call templates. In March, pygmy blue whale song in Perth Canyon is strong at about 20–70 Hz; fin whale 20 Hz pulses and ship tonals also occur.
- Report SNR and onset time for each predicted window.
- Run identical statistics over the control days and the same UTC hours to get empirical false-alarm rates.

**Step 4. Seismic T-phase search.**
- Pull BHZ and HHZ (plus horizontals for polarization) for 2014-03-07 22:00 to 03-08 03:00 from:
  - II.COCO, AU.XMIS/XMI, G.AIS/PAF/RODM/ROCAM, II.DGAR, IU.NWAO/MBWA, AU.GIRL, S1.AUBUS, AU.PSA (13 elements).
  - GE.CISI/JAGI/SMRI/UGM/MNAI/PMBI/MMRI/SOEI/KAAM.
- Filter 2–8 Hz (20 sps) and 3–18 Hz (40 sps). Run STA/LTA and 3-component polarization (as Stead did), and beamform PSA with `obspy.signal.array_analysis` for back-azimuths of coastal conversions.

**Step 5. Calibration.**
- Measure arrivals and amplitudes from the catalogued events (section 7) on every station and IMOS window that covers them.
- Derive station corrections and an empirical "detectable magnitude versus distance" curve for each receiver.
- Compare with Kadri's 4 GJ / M~3 estimate for the aircraft.

**Step 6. The Java 01:15 event (most tractable).**
- Pick P and S at CISI, JAGI, SMRI, UGM, XMIS, XMI, MNAI, PMBI, COCO and KAPI.
- Grid-search a location with TauP/ak135, or use NonLinLoc.
- Compute ML or amplitude-ratio magnitude against the M4.1 at 23:52 (both events are recorded by the same stations).
- Check the T-phase timing at PAKIM (01:32:5x) and the timing of the claimed HA08 arrival (01:59:20).
- If the event has a double-couple-like S/P ratio and M≈4.3, the implied energy (~10¹¹ J) is about 45 times the aircraft's kinetic energy, which argues for a natural origin.

**Step 7. Curtin/Carlsberg test.**
- A Carlsberg Ridge source (~5°N 62°E region) would produce T-phases at II.DGAR and G.RODM/ROCAM tens of minutes before PAKIM and HA01.
- Search DGAR and ROCAM at roughly 00:55–01:20 for a matching T-phase. If none is found and the Java event fits PAKIM, the 2014 association should be revisited.

**Step 8. Expected sensitivity (inference).**
- IMOS PAPCA/PAKIM ambient noise is about 95–101 dB re 1 µPa (band RMS). The detection threshold is about +6–10 dB, roughly 0.1–0.2 Pa.
- That is sensitive to a 0.5 Pa (HA01-equivalent) signal only if Perth Canyon/Kimberley propagation is no more than about 10 dB worse than HA01's.
- Island seismometers are expected to detect only events of roughly M≥3.5 at more than 1,000 km, so they are unsuitable for a 4 GJ impact signal and suitable for auditing larger claims.

**Step 9. Reporting.**
- Publish code and window tables. Explicitly state the duty-cycle coverage gaps: for example, Perth Canyon 00:40–00:50 and Kimberley 00:35–00:45, which cover the expected 7th-arc impact arrivals at about 00:37–00:42 only partially.

### Gaps
- No open data can recover the HA01 or HA08 waveforms themselves. Confirming Kadri's or Stead's bearings still needs CTBTO vDEC access, which is outside this scope.
- The IMOS 5-of-15-min duty cycle leaves about 67% of each hour unrecorded per site, so a real event can be missed purely by timing.
- Ambient noise and whale chorus in March at Perth Canyon may mask signals weaker than about 100 dB re 1 µPa.
