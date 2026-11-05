# MH370: re-analysing the public Inmarsat SATCOM log, and other radio, atmospheric and incidental signal sources (outside acoustics, WSPR, imagery and debris)

Research date: 5 November 2026. Times are UTC. "Inference" marks my own reasoning, not a sourced claim. Acoustic, WSPR, imagery and debris-drift items appear only where they bear on SATCOM or path modelling; other researchers cover those topics.

---

## 1. Inmarsat SATCOM log: what is in it, calibration issues, open-source models, and the unresolved questions that move the end latitude

### Takeaway
The public 47-page log holds everything needed to recompute BTO rings and BFO curves. The calibration is well documented: BTO bias −495,679 μs, BFO fixed bias 150 Hz, BFO error σ 4.3 Hz, and published warm-up bounds for the SDU's oven-controlled oscillator. The arc positions are therefore not the weak point. The end latitude depends on unconstrained assumptions: autopilot mode and speed after the final major turn (FMT), when the FMT happened, and whether the aircraft glided after fuel exhaustion. Free tools exist to attack these (open path solvers, ERA5 or GDAS winds, the public log). Several key datasets remain unpublished: the full unredacted log fields, the BFOs from 9M-MRO's 20 previous flights, and other aircraft's logs.

### Cited findings

**The released log (document facts)**
- Inmarsat and Malaysia's Department of Civil Aviation (DCA) published the redacted ground-station records on 27 May 2014. — [Paul Sladen, inmarsat-9m-mro README](https://github.com/sladen/inmarsat-9m-mro)
- A copy of the PDF has 47 pages. Its PDF creation date is 23 May 2014. The copy is hosted on GitHub; the original was hosted by CNN at i2.cdn.turner.com/cnn/2014/images/05/27/flight.370.data.logs.pdf. — [BigDataMalaysia/MH370_Inmarsat](https://github.com/BigDataMalaysia/MH370_Inmarsat). I checked the page count and date locally with pdfinfo.
- The original DCA URL cited by Inmarsat's authors is http://www.dca.gov.my/mainpage/MH370%20Data%20Communication%20Logs.pdf (May 2014). — [Ashton et al. 2015, J. Navigation 68:1–22, references](https://doi.org/10.1017/S037346331400068X)
- Coverage: the log runs "from 16:00 to the last Handshake Request (Log On Interrogation) attempt at 01:16 UTC". In its own words, "some columns which contain no material information have been removed". The full record has 28 fields, including Rx power, C/No, estimated BER, SU contents, BFO and BTO, but the readable tables mostly show only time, channel, SU type, BFO and BTO. — [Released log notes, p.1–2 (GitHub copy)](https://github.com/BigDataMalaysia/MH370_Inmarsat)
- Paul Sladen's repository converts the PDF to CSV. It also has "a patchset [that] restores additional data transcribed from the CNN videos showing the unredacted SU logs". The repo also contains folders for radar, ADS-B, AMSS, ATSB material and transcripts. — [sladen/inmarsat-9m-mro](https://github.com/sladen/inmarsat-9m-mro)

**Key entries (BFO in Hz, BTO in μs), from the log and Ashton et al. Tables 1 and 6**
- 18:25:27 Log-on Request on channel IOR-R600-0-36E1: BFO 142, raw BTO 17120. Inmarsat corrects the BTO to 12520 by subtracting a fixed 4600 μs offset for Log-on Requests, found from the terminal's history. — [Ashton et al. 2015](https://doi.org/10.1017/S037346331400068X)
- 18:25:34 Log-on Acknowledge: BFO 273, BTO 51700. Then 18:27:04 user data (BFO 176/175), 18:27:08 (BFO 172), 18:28:06 (BFO 144) and 18:28:15 (BFO 143). Inmarsat says the BTOs at 18:25:34 and 00:19:37 "should be ignored" because of channel and frequency switching during log-on. It also says it is "prudent to discount" the BFOs from 18:25:34 to 18:28:15 inclusive, and the one at 00:19:37. — [Ashton et al. 2015](https://doi.org/10.1017/S037346331400068X)
- 18:39:52 ground-to-air telephone call, not answered. The call announcement went out on the P-channel at 18:39:52.907. C-channel BFOs were logged from 18:39:55 to channel release at 18:40:56 (BFO 90), on channel units IOR-3730/373E-21000. Inmarsat uses the average of 51 values between 86 and 90 Hz, which is 88. C-channel messages carry no BTO. — [Released log, pp. ~45–47](https://github.com/BigDataMalaysia/MH370_Inmarsat); [Ashton et al. Table 6](https://doi.org/10.1017/S037346331400068X)
- Hourly handshakes: 19:41:03 (BFO 111, BTO 11500), 20:41:05 (141, 11740), 21:41:27 (168, 12780), 22:41:22 (204, 14540) and 00:11:00 (252, 18040). — [Ashton et al. 2015](https://doi.org/10.1017/S037346331400068X)
- 23:13:58 second unanswered ground-to-air call. C-channel BFOs run from 216 at 23:14:00 to 219 at release at 23:15:02, on channel unit IOR-3737-21000. Inmarsat uses the average of 29 values between 216 and 222 Hz, which is 217. — [Released log](https://github.com/BigDataMalaysia/MH370_Inmarsat); [Ashton et al.](https://doi.org/10.1017/S037346331400068X)
- 00:19:29 Log-on Request on IOR-R600-0-36F8: BFO 182, raw BTO 23000, corrected to 18400. At 00:19:37.443 a Log-on/Log-off Acknowledge on IOR-R1200-0-36F6 gave BFO −2 and BTO 49660. The log annotates this as "the last transmission received from the aircraft terminal". — [Released log](https://github.com/BigDataMalaysia/MH370_Inmarsat)
- Inmarsat says the 00:19 log-on "appears to have been triggered by the aircraft terminal being power cycled, and may indicate the aircraft running out of fuel". — [Ashton et al. 2015 §3.3](https://doi.org/10.1017/S037346331400068X)

**Calibration and known issues**
- BTO bias: −495,679 μs, the mean of 17 measurements in the 30 minutes before takeoff. — [Ashton et al. 2015](https://doi.org/10.1017/S037346331400068X)
- BFO model: BFO = ΔFup + ΔFdown + δfcomp + δfsat + δfAFC + δfbias. The fixed bias of 150 Hz was calibrated on the ground before takeoff (Ashton Table 5). The terminal pre-compensates its own Doppler but assumes a stationary satellite. — [Ashton et al. 2015](https://doi.org/10.1017/S037346331400068X); [Released log notes](https://github.com/BigDataMalaysia/MH370_Inmarsat)
- Satellite effects: the satellite's translation-frequency oscillator showed a "kink" during the I-3F1 eclipse (19:19–20:26), attributed to thermal variation. The Perth ground station's automatic frequency control (AFC) treats L-band and C-band Doppler as additive and so removes about two-thirds of the variation. Inmarsat corrected for both empirically using the Pilot signal and satellite telemetry. — [Ashton et al. 2015 §5.1–5.2](https://doi.org/10.1017/S037346331400068X)
- Validation: Inmarsat validated the BFO equation against "several aircraft that were in flight at the same time as MH370", and against 9M-MRO in the preceding days. That validation data is not in the public log. — [Ashton et al. 2015 §5.4](https://doi.org/10.1017/S037346331400068X)
- BFO noise: based on 20 previous 9M-MRO flights, the BFO error has σ = 4.3 Hz. Holland's descent analysis uses hard bounds of [−28, +18] Hz, which span all 2,501 valid in-flight BFO errors. — [Holland, arXiv:1702.02432 v3 (IEEE AESM 2018)](https://arxiv.org/pdf/1702.02432)
- OCXO warm-up: a SATCOM sub-group study tested several SDUs. It attributed the 18:25 BFO transient to power-on drift and settling of the SDU's oven-controlled crystal oscillator (OCXO). Each SDU behaved repeatably for a given outage length. In four log-ons after outages in the preceding week, 9M-MRO's SDU started with a BFO "initially too high", which then decayed over a few minutes. — [Holland 2018](https://arxiv.org/pdf/1702.02432)
- Conflict between sources: Ashton et al. say the first Log-on Request message "did provide a consistent and accurate BFO measurement" ([Ashton §5.3](https://doi.org/10.1017/S037346331400068X)). Holland says the 18:25:27 Log-on Request had non-zero BER and unusually low C/N0 and power, so "the first BFO was deemed untrustworthy" ([Holland 2018](https://arxiv.org/pdf/1702.02432)). The 00:19:29 BFO (182) is used, with warm-up bounds.
- 18:25 vs 18:40 (FMT): Holland's timeline reads the BFOs as follows. At 18:25–18:28, "if flying level, MH370 still tracking NW". At 18:39–18:41, "if flying level, MH370 tracking southwards". — [Holland 2018 Table I](https://arxiv.org/pdf/1702.02432). Inmarsat's fit "fits the northern path until 18:25, but switches to the southern path by 18:40". — [Ashton §5.3](https://doi.org/10.1017/S037346331400068X)
- End-of-flight BFO: Holland bounds the descent rate under Hypothesis 1 (SDU restart after power loss). At 00:19:29 it was 3,900–14,800 fpm. At 00:19:37 it was 14,800–25,300 fpm. The implied downward acceleration is about 0.68 g. His conversion is roughly 1.7 Hz per 100 fpm at that geometry. — [Holland 2018 Tables III–IV](https://arxiv.org/pdf/1702.02432). Iannello likewise says the final BFOs suggest a steep descent of about 0.7 g. — [Radiant Physics, 2 Nov 2023](https://mh370.radiantphysics.com/)
- Counter-view: Vincent Lyne (University of Tasmania, retired) published a peer-reviewed open-access paper in J. Navigation 77:2 (2024) that rejects Holland's "motion-decoupled Up-Down model". It proposes a "Declination model" and argues for a "controlled eastward descent", which supports Larry Vance's powered-ditching interpretation. Lyne concludes "the official theory of fuel starvation and a high-speed dive are fundamentally flawed". — [Lyne 2024, doi:10.1017/S0373463324000262](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/3B8A244FB86B058D36A406BE6EB17345/S0373463324000262a.pdf/final-two-mh370-communications-suggest-controlled-eastward-descent.pdf)
- Inmarsat's own example route turned south after IGOGU, through ISBIX, at a ground speed of about 450 kt. It matched the 19:41–00:11 BFOs within 2 Hz and the call BFOs within 6 Hz, giving a last contact at 34.7°S, 93.0°E. The authors stress "that there remains significant uncertainty in the final location". — [Ashton et al. 2015 §6–7](https://doi.org/10.1017/S037346331400068X)

**Open-source and published path models**
- DSTG book: Davey, Gordon, Holland, Rutten and Williams, *Bayesian Methods in the Search for MH370* (Springer 2016, open access, CC BY-NC). It builds the prior from Malaysian military radar, a SATCOM likelihood and an aircraft-dynamics model, and shows how the Réunion flaperon changes the probability distribution. — [Springer](https://link.springer.com/book/10.1007/978-981-10-0379-0); [OAPEN PDF link](https://library.oapen.org/bitstream/20.500.12657/27976/1/1002023.pdf); [DOAB](https://directory.doabooks.org/handle/20.500.12854/34287). Springer and OAPEN both blocked automated download, so I did not extract the book's numbers in this session.
- UGIB (Ulich, Godfrey, Iannello, Banks), report of 7–9 March 2020:
  - Integrated model covering Malaysian civil and military radar (raw Kota Bharu and Butterworth data), Inmarsat BTO/BFO, 777-200ER performance and fuel, debris drift, and the 2014 aerial-search results.
  - About 2,300 candidate paths. Fuel exhaustion around 00:17.
  - Route assumptions: long-range-cruise (LRC) speed after BEDAX; a climb to FL390 between about 19:24 and 19:41; a due-south track from BEDAX along 93.7875°E.
  - Last Estimated Position (LEP): 34.2342°S, 93.7875°E.
  - Satellite data alone peaks near 34.3°S, with other peaks north and south along the arc.
  - Southern endpoints were rejected mainly on fuel and East African debris. Northern endpoints were rejected because the 2014 aerial search found no floating debris.
  - Search areas: A1, no pilot input, 23,050 km²; A2, southward glide, 22,000 km²; A3, glide in any direction, about 166,000 km².
  - Source: [Radiant Physics, Mar 2020](https://mh370.radiantphysics.com/2020/03). As far as I found, the UGIB model code is not published (see Gaps).
- Ulich–Iannello drift study, June 2023: BRAN2015 ocean model, 17 debris reports, 86,400 trials per debris class. Most likely impact about 34.0°S, about 76 km northeast of the UGIB LEP. Possible origins span 30°S–36°S. Zones are defined for no glide (Zone 1), ±70 NM (Zone 2) and ±140 NM (Zone 3). — [Radiant Physics, 12 Jun 2023](https://mh370.radiantphysics.com/)
- Open code found on GitHub (searched 5 Nov 2026 with `gh search repos`):
  - [o-nesterov/MH370Solver](https://github.com/o-nesterov/MH370Solver), updated Feb 2026. It fits paths by minimising BTO/BFO residuals. It uses an RK5(4) integrator, a fuel-flow model, and "meteorological forcing … either from GDAS1 or ERA5". It supports true track, true heading, magnetic track, magnetic heading and gyroscopic heading, both IAS and Mach speed modes, and level, V/S and FPA vertical modes. This is the most directly useful tool for the autopilot-mode question.
  - [sladen/inmarsat-9m-mro](https://github.com/sladen/inmarsat-9m-mro): PDF-to-CSV conversion plus forward and back track scripts.
  - [BigDataMalaysia/MH370_Inmarsat](https://github.com/BigDataMalaysia/MH370_Inmarsat): CSVs and the PDF.
  - [vincentclee/mh370_satellite_data_communication_logs](https://github.com/vincentclee/mh370_satellite_data_communication_logs): readable log, updated Oct 2026.
  - [kr-pr/mh370_sat_tools](https://github.com/kr-pr/mh370_sat_tools): BTO-to-range and BFO-to-azimuth grids.
  - [myhrvold/MH370_MCMC](https://github.com/myhrvold/MH370_MCMC): MCMC notebooks from 2014.
  - [waudbydaniel916-collab/MH370-Geodesic-Kinematics-Bayesian-Fusion](https://github.com/waudbydaniel916-collab/MH370-Geodesic-Kinematics-Bayesian-Fusion): updated Sep 2026. It claims ERA5 winds; unvetted, with 1 star.
- Other independent analyses:
  - Duncan Steel's archive, including BFO-bias, turn-time and azimuth studies. — [duncansteel.com/archives/1313](https://duncansteel.com/archives/1313); [/1639](https://www.duncansteel.com/archives/1639); [/1282](https://duncansteel.com/archives/1282)
  - Geoff Hyman's mid-flight azimuth fit: mean 286.8°, σ 3.6°. He concluded that both azimuth and navigation mode are "fairly uncertain". — [duncansteel.com/archives/1639](https://www.duncansteel.com/archives/1639)
  - Kristensen, arXiv:1811.09315: a non-Euclidean least-squares fit that reaches a different location using eyewitness and contrail inputs. Treat as an outlier. — [arXiv](https://arxiv.org/pdf/1811.09315v3)
- Other search proposals:
  - Ocean Infinity's March 2024 proposal: the 7th arc from about 33°S to 36°S, out to about ±45 NM (83 km). — [Radiant Physics, 5 Mar 2024](https://mh370.radiantphysics.com/)
  - A "High Priority Search Area" of about 30.5 km² near 34.53°S, 93.84°E that had never been scanned. — [Radiant Physics, 2 Nov 2023](https://mh370.radiantphysics.com/)

### Inferences
- The arcs are settled; the path between them is not. BTO residuals are small and the bias is well calibrated, so each arc's position is robust. Where the aircraft crosses the 7th arc is set by the path model (speed schedule, navigation mode, FMT time and winds). UGIB's satellite-only result has several peaks, which shows that BTO/BFO alone do not pick one latitude. Fuel and drift break the tie.
- Ranked open problems that would most change the predicted end point. My ranking is a judgement from the cited material.
  1. **Glide or no glide after fuel exhaustion.** This controls the width of the search across the arc: a narrow band near the arc with no glide (the 2023 drift study's "Zone 1") versus ±70–140 NM with one ("Zones 2–3"). Holland's BFO-derived 0.68 g descent supports no glide. Lyne and Vance argue for a controlled descent. This cannot be fully settled from public data. It can be tested by redoing Holland's bounds with the public BFOs and his published warm-up envelope, and by checking whether Lyne's Declination model is physically consistent. That is a self-contained, free reanalysis.
  2. **Navigation and speed mode after the FMT.** Options include LNAV great circle, constant true track, constant magnetic heading or track, and heading hold, combined with a Mach or LRC speed schedule. These map to different 7th-arc latitudes. MH370Solver plus ERA5 or GDAS lets anyone build a reproducible ensemble and publish residual statistics for each mode. Nobody appears to have published an open, reproducible comparison of all modes.
  3. **FMT timing and the 18:25–18:40 window.** The 51 C-channel BFOs over 18:39:55–18:40:56 are in the public log. Their small spread (86–90 Hz) can constrain whether the aircraft was turning or changing altitude during that minute. A combined analysis of the 18:28 BFOs, the 18:22 radar point and the 18:40 BFO, with uncertainty quantified, is doable with public data.
  4. **Timing between fuel exhaustion and the 7th arc.** This covers APU start and SDU reboot, from about 00:17 to 00:19:29, plus the absent 00:21 in-flight-entertainment log-on that the 2023 drift study uses for its Zone 1A. It needs Boeing and Honeywell system-timing knowledge, which is partly public in the ATSB and Malaysian reports.
- Data that would help most and is not public: the full unredacted log (C/N0, Rx power, BER and SU contents for every burst); the BFOs from 9M-MRO's 20 previous flights and 7 log-ons (Holland shows only summaries); and the BFO logs of other aircraft Inmarsat used for validation. These would need requests to Inmarsat, the ATSB or Malaysia's AAIB, not scraping.

### Gaps
- I could not extract figures from the DSTG book (download blocked). These need checking directly: its BTO σ, its BFO σ, whether the 18:40 BFO was used, and its posterior latitude peak.
- I found no public release of the UGIB or Ulich code or of the DSTG particle-filter code.
- I did not verify the ATSB *Operational Search for MH370* (3 Oct 2017) text on autopilot modes or end-of-flight scenarios: [ATSB PDF](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf).
- I did not find which fields were blacked out in the 27 May 2014 PDF beyond the "columns removed" note, or how complete Sladen's CNN-video recovery is.

---

## 2. Australia's JORN over-the-horizon radar: was it watching that night?

### Takeaway
I found no primary official statement (no Hansard transcript, no Defence media release) that says whether JORN was operating or detected MH370 on 7–8 March 2014. In 2014 Defence declined to comment on operational capability. Contemporaneous reporting cited RAAF documents saying JORN does not run 24/7. A 2019 Defence Innovation Network problem brief and a 2024 peer-reviewed paper both assert, without evidence, that it was not operating. JORN data is classified, so this is not a free-public-data avenue.

### Cited findings
- Reuters (via Yahoo, March 2014), citing RAAF documents: JORN "does not operate on a 24-hour basis" and does not continually "sweep" an area. Defence "did not reply to repeated requests" on whether JORN detected MH370. — [Reuters/Yahoo, "Australia takes over southern arc of search"](https://news.yahoo.com/australia-takes-over-southern-arc-search-missing-malaysian-052803864--sector.html)
- Foreign Minister Julie Bishop said relevant defence intelligence "has been and will continue to be passed on to Malaysian authorities". The same article notes Australia "releases little information about the system". — [Yahoo7, 19 Mar 2014](https://au.news.yahoo.com/spy-satellites-australia-could-unlock-060502070.html)
- iTWire, 17 Mar 2014: "JORN claims that it is not always activated, and also that it tends to focus on small areas of interest". This is unattributed. The author's "JORN official" quote is not on the record. — [iTWire](https://itwire.com/opinion-and-analysis-sp-481/whiskey-tango-foxtrot/did-australia-track-mh370)
- A 2019 problem brief for the NSW Defence Innovation Network (PDF metadata: UTS, 15 Jul 2019) lists among JORN's problems: "Radar may not always be operational – e.g. Such as when MH370 disappeared". — [Defence Innovation Network, "Sensors for JORN"](https://defenceinnovationnetwork.com/storage/2019/07/9.-Sensors-for-JORN.pdf)
- Lyne (J. Navigation 2024) writes "despite JORN not being on at the time". He draws a JORN southern boundary near 30°S, 92°E, citing Harris 2017, and builds a "JORN-avoidance" hypothesis around it. — [Lyne 2024](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/3B8A244FB86B058D36A406BE6EB17345/S0373463324000262a.pdf/final-two-mh370-communications-suggest-controlled-eastward-descent.pdf)
- Senate scrutiny: Australian Senate estimates questioned the ATSB's handling of the search in May 2018, but the excerpt I found does not mention JORN. — [Malay Mail, 17 May 2018](https://www.malaymail.com/news/malaysia/2018/05/17/senate-to-grill-australian-transport-safety-bureau-over-failed-mh370-search/1632004). The aph.gov.au Hansard pages returned HTTP 403 to automated fetch.

### Inferences
- Geometry (my calculation): the southern-route positions are about 2,100–3,000 km from the Laverton (WA) JORN radar. Examples: the UGIB LEP is about 2,750 km away, the 22:41 position about 2,980 km, and a 31°S, 100°E point about 2,115 km. That is within JORN's nominal 1,000–3,000 km reach. Detection would still have depended on the radar being on, its beam azimuth and dwell, ionospheric conditions and time of day. None of these is public.
- Any detection evidence would sit in classified Defence holdings. The only route is a formal FOI request or a Senate estimates question. That is not "free public data", and the expected yield is low.

### Gaps
- I found no Hansard primary source. Searching the APH Hansard manually for "Jindalee" with "MH370" in 2014–2018 estimates, and checking Questions on Notice, is still needed.
- I did not find a named Defence spokesperson quote stating JORN's status that night.

---

## 3. Other radio, atmospheric and incidental sources: MWA passive radar, GNSS TEC, lightning, ADS-B of other aircraft, AIS, ERA5 weather, phone data

### Takeaway
Most of these cannot constrain the end point. The Murchison Widefield Array (MWA) is physically out of range. GNSS total electron content (TEC) and lightning have no plausible signal from a single airliner, and no MH370 study using them exists. Weather (ERA5 or GDAS) is the one atmospheric dataset with real value, as an input to path models. AIS from 2012 onward (Global Fishing Watch) and FlightAware/ADS-B traffic from 2014 are free or cheap. They are useful for identifying possible witnesses and for checking context, not for locating the wreck.

### Cited findings
- **MWA passive radar.** The MWA has detected FM-band reflections from aircraft, meteors and space objects, for example the ISS using Perth and Geraldton FM transmitters (Tingay et al. 2013). It has also run non-coherent passive-radar surveys (Prabu, Hancock, Zhang, Tingay). — [PASA 2020 LEO survey](https://www.cambridge.org:443/core/services/aop-cambridge-core/content/view/BF1BFD69F15D72D65514E95868F21DBA/S1323358020000405a.pdf/lowfrequency_blind_survey_of_the_low_earth_orbit_environment_using_noncoherent_passive_radar_with_the_murchison_widefield_array.pdf); [ANU record, space-debris tracking](https://researchportalplus.anu.edu.au/en/publications/on-the-detection-and-tracking-of-space-debris-using-the-murchison/). I found no publication or statement linking the MWA to MH370.
- **GNSS TEC.** Ground GPS receivers detect ionospheric TEC disturbances from surface-generated Rayleigh, acoustic and gravity waves, such as those from earthquakes, tsunamis and volcanoes. — [Komjathy et al., Earth Planets Space](https://earth-planets-space.springeropen.com/counter/pdf/10.5047/eps.2012.08.003.pdf). I found no MH370 TEC study.
- **Lightning.** The University of Washington's WWLLN archive is "available to the public at nominal cost", so it is not free. — [WWLLN archive page](https://webflash.ess.washington.edu/archive.html). UCAR's EOL WWLLN dataset is password-protected and covers only 2018–19. — [UCAR WWLLN dataset](https://data.ucar.edu/dataset/wwlln-lightning-data)
- **ADS-B and other aircraft on 7–8 March 2014.**
  - OpenSky started around 2013 with volunteer receivers "throughout Central Europe". Access to the historical database is by individual request. — [OpenSky (Wikipedia)](https://en.wikipedia.org/wiki/OpenSky_Network); [ATM data sources guide](https://atmdata.github.io/sources)
  - FlightAware forum users note sparse ocean coverage and "very few other aircraft crossing the Indian Ocean during the flight of MH370". — [FlightAware forum](https://discussions.flightaware.com/t/mh370-ads-b-coverage/78537)
  - The French CAPTION group used FlightAware trajectories for 7 March 2014 and offers a downloadable set. They found MH370 likely crossed paths with 3–4 flights, the closest at about 12 NM, two of them at FL320–FL380. They found no flight close enough for plausible visual contact. Flights flagged for closer study: SIA478, ETD461, UAE407 and UAE359. — [CAPTION, "Possible MH370 encounters in the SIO"](https://www.mh370-caption.net/index.php/possible-mh370-encounters-in-the-southern-indian-ocean/); [CAPTION PDF](https://www.mh370-caption.net/wp-content/uploads/Caption-analysis-MH370-flights-after-FMT.pdf)
  - A comment on the Iannello-co-authored drift work states there were "no other commercial aircraft in the vicinity of MH370" at the relevant time, and that military aircraft do not appear in ADS-B. — [mh370search.com comment thread](https://www.mh370search.com/2021/01/21/mh370-debris-drift-analysis/comment-page-4)
  - Jeff Wise's "Wayward Etihad A330" post is an example of a community other-aircraft investigation. — [jeffwise.net](https://jeffwise.net/2016/01/26/minor-mh370-mysteries-1-the-case-of-the-wayward-etihad-a/comment-page-1)
  - Flightradar24 published blog material on MH370. — [FR24 blog, 2016](https://www.flightradar24.com/blog/flight-tracking-news/major-incident/searching-for-mh370-two-years-later/)
  - The best comparison data for BFO validation would be the Inmarsat logs of other aircraft flying that night, which Inmarsat used internally. — [Ashton §5.4](https://doi.org/10.1017/S037346331400068X)
- **AIS ship positions.**
  - Global Fishing Watch's AIS archive begins in January 2012 and holds 20+ billion messages from 200,000+ vessels. Access is free, with registration for some datasets.
  - Data products: gridded "AIS Vessel Presence" as static files for 2012–2020; a vessel-presence API in CSV, JSON or TIFF; and fishing-effort v3 for 2012–2024 on Zenodo or BigQuery.
  - Sources: [GFW vessel presence update](https://globalfishingwatch.org/platform-update/global-ais-vessel-presence-dataset/); [GFW API vs downloads PDF](https://globalfishingwatch.org/our-apis/assets/APIs_gfwr_and_Data_Downloads_Products_Differences.pdf); [Zenodo fishing effort v3](https://zenodo.org/records/14982712)
  - Iannello and Don Thompson use public AIS (destination fields, course changes) to follow Ocean Infinity's vessels in real time. — [Radiant Physics, 9 Mar 2025 and 4 Mar 2025](https://mh370.radiantphysics.com/)
- **Weather.** MH370Solver ingests GDAS1 or ERA5. — [MH370Solver README](https://github.com/o-nesterov/MH370Solver). UGIB's integrated model includes "weather along the route". — [Radiant Physics, Mar 2020](https://mh370.radiantphysics.com/2020/03)
- **Mobile phone (incidental radio).** Investigators flew a King Air 350 test flight over the relevant area, around the same time of night, to check whether mobile phones in a flying aircraft could connect to the ground network. This was in connection with the reported Penang-area phone registration. This is secondary reporting of the Malaysian investigation. — [vietnam.vn, Oct 2026](https://www.vietnam.vn/en/he-lo-manh-moi-moi-ve-mh370-sau-cu-ngoat-dinh-menh-khien-ca-may-bay-bien-mat-co-hoi-tim-kiem-con-hy-vong)

### Inferences
- **MWA: physically excluded.** A FL350 aircraft's radio horizon from a ground receiver is about 426 km. Every candidate southern-route point is 1,660–3,300 km from the MWA (my calculation: UGIB LEP about 2,340 km, the 31°S, 100°E point about 1,660 km, the 20:41 position about 3,290 km). FM forward-scatter or reflection detection is therefore impossible, regardless of whether the MWA was observing. Drop this avenue.
- **GNSS TEC: very low value.** A 777 hitting the water releases a tiny amount of energy compared with the tsunami and earthquake sources that TEC methods detect. The nearest IGS stations, such as Cocos and the WA coast, are also far away. The expected signal is below the noise. IGS RINEX data for March 2014 are free via NASA CDDIS with a free Earthdata login (from my background knowledge; not verified this session). Nobody has published a test, which may simply mean the idea was never seriously considered.
- **Lightning: no aircraft signal.** At most it adds weather context, such as convection along the route that could affect path-model winds or contrail claims. WWLLN costs money, and Blitzortung coverage of the 2014 SIO was likely negligible (inference). Low value.
- **ADS-B of other aircraft: low location value, some witness value.** The CAPTION flight list is a ready-made basis for targeted witness requests and ADS-C/FANS report requests. There is no free 2014 global ADS-B archive with Indian Ocean coverage that I could confirm. FlightAware's historical data is a paid product (not verified this session). What would actually move the end latitude are other aircraft's Inmarsat BFO logs (validation) and ADS-C reports, which are not public.
- **AIS 2014: modest value.** Uses include finding vessels near the 7th arc on 8 March 2014 as potential witnesses for sounds, lights or debris; checking claimed sightings; and pre-screening shipwreck and seabed sonar contacts. GFW is free with registration. 2014 satellite-AIS coverage of the remote SIO was thin (inference).
- **ERA5: highest value of the atmospheric sources.** ERA5 is free from the Copernicus Climate Data Store with a free account (background knowledge, not verified this session). Wind and temperature errors change ground speed, and so the arc-crossing latitude for a given mode. A cheap, publishable contribution is a GDAS-vs-ERA5 sensitivity study across autopilot modes using MH370Solver, reporting how many km the end point moves.

### Gaps
- I did not confirm FlightAware's or FR24's current pricing or terms for 2014 historical tracks, or whether any free archive covers the 2014 Indian Ocean.
- I did not confirm the exact availability and resolution of GFW 2014 AIS data in the 7th-arc region. This needs a portal check after free sign-up.
- I found no source on whether Indonesian, Indian (Andaman) or Thai radar data beyond the 2014 statements are available.
- I did not verify Blitzortung's 2014 coverage.

---

## 4. Where the independent community sees value now, and latest developments (to 5 November 2026)

### Takeaway
As of 5 Nov 2026, the official track is Ocean Infinity's no-find-no-fee contract, extended to 30 June 2027. About 7,428.54 km² of the priority area remains, and searching can only resume in the November 2026 to April 2027 weather window. I found no report that vessels had actually returned by 5 Nov 2026. The community's focus remains the UGIB/IG hotspot near 34.2°S and searching off-arc for a glide. A minority pushes alternatives such as the Java acoustic candidate and Lyne's controlled descent.

### Cited findings
- **Search timeline.**
  - Ocean Infinity began its third campaign on 30 Dec 2025 with Armada 86-05 and three Hugin AUVs, in an area first searched in March 2025. Iannello said it should reach "unsearched areas due south of the LEP", consistent with a statistically favoured due-south trajectory. — [Radiant Physics, 1 Jan 2026](https://mh370.radiantphysics.com/2026/01/01/the-search-for-mh370-continues-into-2026/)
  - Ocean Infinity left the area on 23 Jan 2026. Since 2018 it has spent 151 days at sea and mapped more than 140,000 km². — [NST, Mar 2026](https://www.nst.com.my/news/nation/2026/03/1393352/ocean-infinity-ends-2026-mh370-search-phase-without-success-indian); [Malay Mail, 9 Mar 2026](https://www.malaymail.com/news/malaysia/2026/03/09/ocean-infinity-ends-latest-mh370-hunt-after-151-days-at-sea-mapping-140000-sq-km-with-no-new-clues/211959)
  - Malaysia's investigation bureau (AAIB) reported 28 operational days covering about 7,571 km² across both phases.
  - Ocean Infinity CEO Oliver Plunkett, 8 Mar 2026: "If nothing else, we can say with confidence that it isn't where we looked. That matters – it brings clarity, and it will help those continuing to study the evidence refine their thinking and shape future search strategies." — [MiGFlug, 26 Aug 2026](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/); [Ocean Infinity statement](https://oceaninfinity.com/news/conclusion-of-the-search-for-malaysian-airlines-flight-mh370/)
- **Families.** Voice370, on 8 Mar 2026, urged extending the contract by addendum. It said any Ocean Infinity request to extend "should be granted without hesitation", and asked the government to consider other deep-sea firms under the same framework. — [FMT, 8 Mar 2026](https://www.freemalaysiatoday.com/category/nation/2026/03/08/voice370-urges-govt-to-extend-search-for-missing-aircraft); [The Star](https://www.thestar.com.my/news/nation/2026/03/08/mh370-voice370-urges-govt-to-extend-search)
- **Contract extension, 29 Jun 2026.**
  - The Cabinet extended the contract for one year from 1 July, to 30 June 2027, on the same no-find-no-fee terms (US$70m).
  - Remaining area: 7,428.54 km².
  - Ocean Infinity's assets were temporarily reassigned to commercial work, and redeployment "can only be conducted between November 2026 and April 2027".
  - Sources: [FMT, 29 Jun 2026](https://www.freemalaysiatoday.com/category/nation/2026/06/29/mh370-search-deal-with-ocean-infinity-extended-for-another-year); [The Star](https://www.thestar.com.my/news/nation/2026/06/29/govt-extends-deal-with-ocean-infinity-to-search-for-mh370-wreckage)
- **Iannello, 10 Mar 2026.** He endorsed searching Ed Anderson's hydroacoustic candidate at 8.36°S, 107.92°E, about 42 miles off Java, as quick and cheap ("an afternoon" for a Hugin). He conceded it "cannot be definitively linked" to MH370 and lies further north than most estimates. The IG hotspot search (34.23°S, 93.78°E) was paused for weather and Ocean Infinity's other commitments. — [Radiant Physics, 10 Mar 2026](https://mh370.radiantphysics.com/)
- **News, September to early November 2026.**
  - 27 Sep 2026: testimony that Malaysia Airlines' crisis team did not know in the first hours that MH370 had turned back, and initially searched the South China Sea for 7 days. — [The Vibes](https://www.thevibes.com/articles/news/127721/malaysia-airlines-team-did-not-know-mh370-had-turned-back-in-crucial-first-hours)
  - 22 Oct 2026: an 18-page OHASISBIO hydroacoustic report by J.-Y. Royer (CNRS), completed in late 2016 and sent to French and Australian investigators, "has just been released". This is acoustics scope; it is flagged for that researcher. — [Lao Dong, 22 Oct 2026](https://news.laodong.vn/the-gioi/manh-moi-moi-tu-dem-mh370-mat-tich-co-the-tao-buoc-ngoat-tim-kiem-1787489.ldo)
  - Late Oct to early Nov 2026: EgyptAir engineer Ismail Hamad's "standby magnetic compass deviation" hypothesis, placing the aircraft in a shallow corridor off Western Australia. It appeared only in tabloid syndication and is unverified opinion. — [Irish Star](https://www.irishstar.com/news/world-news/mh370-missing-flight-air-malaysia-36499568); [AOL](https://www.aol.com/articles/aviation-engineer-reveals-cunning-plan-083600000.html)
  - About 4 Nov 2026: Popular Mechanics feature on the robotic search, which my fetch tool could not retrieve. — [Popular Mechanics](https://www.popularmechanics.com/flight/airlines/a74313890/mh370-search-ocean-robots/)
- **Other community views.** CAPTION group pages; Godfrey and others; a blog with AI-generated "mag swarm" search plans (low quality). — [whereismh370today](https://whereismh370today.blogspot.com/2026/03/mag-swarm-still-best-bet.html)

### Inferences
- Where the independent community's value now lies:
  - Independently reproducing the end-point distribution with open code (MH370Solver, ERA5, public log), so the remaining 7,428 km² and any later extension can be prioritised transparently.
  - Settling the glide question, which sets the across-arc width.
  - Re-checking earlier sonar coverage gaps ("data holidays", steep terrain, the 30.5 km² High Priority Area).
- My searches up to 5 Nov 2026 found no confirmed new official search area and no report that Ocean Infinity had remobilised. This should be re-checked against Malaysia's Ministry of Transport or AAIB and against live AIS for Armada 78-06/86-05 before the final report states it.

### Gaps
- No Sep–Nov 2026 Radiant Physics post was visible. The homepage's latest post is 10 Mar 2026, so newer posts may exist but did not appear.
- I could not open the Popular Mechanics article (Nov 2026).
- I did not see the Malaysian Transport Ministry statement on the exact November 2026 deployment plan.

---

## 5. Ideas that have been floated and largely discredited (to steer effort away)

### Takeaway
Northern-route, spoofed-BFO and Kazakhstan scenarios, and Diego Garcia or South China Sea shoot-down stories, conflict with hard evidence: the BTO ring sequence, BFO behaviour, and debris confirmed in the western Indian Ocean. Several newer proposals are contested or weakly supported and should be treated as low-priority hypotheses: Lyne's controlled eastward descent, the Java acoustic site, compass deviation, and Kristensen's location.

### Cited findings
- Northern-route spoofing was explored seriously in 2015, including by Iannello himself. He found northern paths that ended at reachable airports, with BFO matching to RMS < 3.8 Hz, if the satellite inclination parameter was "spoofed" to 3.3°. Commenters noted the BFO fit is not unique to such paths. — [Jeff Wise guest post, 17 May 2015](https://jeffwise.net/2015/05/17/guest-post-northern-routes-and-burst-frequency-offset-for-mh370/comment-page-1). In 2018 French investigators were reported to be "eyeing" a spoof scenario. — [jeffwise.net, 31 Oct 2018](https://www.jeffwise.net/2018/10/31/french-mh370-investigators-eye-spoof-scenario/comment-page-1/)
- A flaperon from MH370 was found on Réunion in July 2015. — [The Vibes, 27 Sep 2026](https://www.thevibes.com/articles/news/127721/malaysia-airlines-team-did-not-know-mh370-had-turned-back-in-crucial-first-hours). Later drift work used 17 debris reports to place the origin between 30°S and 36°S. — [Radiant Physics, Jun 2023](https://mh370.radiantphysics.com/)
- The Diego Garcia shoot-down remains a popular-media theory. — [Popular Mechanics, Nov 2026 (search snippet)](https://www.popularmechanics.com/flight/airlines/a74313890/mh370-search-ocean-robots/)
- The SATCOM log shows the terminal logging on at 18:25:27 and exchanging hourly handshakes until 00:19:37, with BTO rising from 11500 μs at 19:41 to 18040 μs at 00:11. — [Ashton et al. 2015](https://doi.org/10.1017/S037346331400068X)
- Contested peer-reviewed alternative: Lyne 2024 (controlled eastward descent, "Penang Longitude", JORN-avoidance). — [Lyne 2024](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/3B8A244FB86B058D36A406BE6EB17345/S0373463324000262a.pdf/final-two-mh370-communications-suggest-controlled-eastward-descent.pdf). It contradicts Holland's 0.68 g bound. — [Holland 2018](https://arxiv.org/pdf/1702.02432)
- Outlier location claims: Kristensen (arXiv 2018), which uses eyewitness and contrail inputs. — [arXiv:1811.09315](https://arxiv.org/pdf/1811.09315v3). Ismail Hamad's compass hypothesis. — [Irish Star](https://www.irishstar.com/news/world-news/engineer-claims-overlooked-detail-could-36488109)
- Malaysian military radar altitude readings were judged not precise enough to trust, because the radar had not been calibrated finely enough. — [Yahoo/Malaysia report](https://my.news.yahoo.com/malaysian-military-radar-data-mh370-wrong-says-report-033152421.html). DSTG declined to use the 18:22:12 long-range radar point partly for accuracy reasons. — [duncansteel.com/archives/1987](https://duncansteel.com/archives/1987)

### Inferences
- **South China Sea shoot-down at about 17:20.** This is incompatible with the aircraft terminal initiating a log-on at 18:25 and then answering handshakes for about 6 hours, with steadily changing BTO. The SATCOM log alone falsifies it.
- **Diego Garcia.** By my geometry, Diego Garcia (about 7.3°S, 72.4°E) is only about 1,300 km from I-3F1's sub-satellite point (about 64.5°E, near the equator). That is closer than even the minimum-BTO 19:41 position, which is about 3,200 km from the sub-point. An aircraft at Diego Garcia at 00:19 would show a BTO far smaller than the recorded 18400 μs (corrected). This is inconsistent unless the BTO was also spoofed. BTO spoofing would require tampering with timing, which the aircraft terminal cannot do.
- **Kazakhstan, northern routes and spoofing.** These need a deliberate BFO-altering modification of the terminal's satellite parameters. They also leave the Réunion and East African debris unexplained. They should be deprioritised. The community's own leading proponent of the 2015 spoof analysis now leads southern-route work.
- **Approaches to avoid:** re-litigating the arcs; theories that depend on unreleased classified data (JORN, spy satellites); and media-driven single-clue hypotheses without residual statistics.
- **Approaches to favour:** reproducible BTO/BFO + fuel + wind ensembles; open reanalysis of the end-of-flight BFOs; and transparent prioritisation of unsearched or poorly imaged seabed near 34–35°S.

### Gaps
- I did not retrieve an official ATSB or Malaysian document that explicitly rejects the spoofing, Kazakhstan or Diego Garcia scenarios.
- I did not verify Florence de Changy's South China Sea interception claims, or any official response to them.
