# Feasibility of "reverse" aircraft-Doppler acoustic/seismic tracking applied to MH370

Scope note: The Nov-2026 prop-aircraft Doppler geolocation technique itself is covered elsewhere (do not re-research). These notes cover physics limits for a cruising B777 (Trent 892, FL350, ~470 kt TAS), candidate sensor archives for 7 Mar 2014 ~17:20–18:40 UTC (8 Mar MYT) and the southern Indian Ocean leg (to ~00:19 UTC), and prior work. Live checks of the FDSN web services (IRIS, GEOFON) were run on 2026-11-05. Results are reported below as "verified by direct query". Physics numbers I derived myself are labelled **[inference]**.

## 1. Jet engine acoustics at cruise: can a 777 at FL350 be heard or recorded on the ground, and is a Doppler curve resolvable?

### Takeaway
A cruising airliner is audible and recordable on the ground under quiet conditions. Published en-route noise work describes the signal as low-level, long-duration and lacking high frequencies, with low-frequency tonal content that decays slowly. Two things make a colsto-style S-curve fit much harder than for low props. Above roughly 1 kHz the sound is absorbed over an 11 km path. Refraction sets up a shadow zone that limits ground reception to a footprint of a few tens of km around the ground track. A 2026 NORSAR fibre-optic (DAS) study did see coherent low-frequency arrivals from jets "even at cruising altitudes". It could not resolve their Doppler harmonics because the jet tones sit above its 62.5 Hz Nyquist limit. Recovering bearing or track from cruise-altitude jets therefore looks possible with dense arrays, but nobody has shown it with a single sparse station.

### Cited Findings
- NASA ran a laboratory annoyance study on noise from aircraft at cruise conditions, using ground-level recordings of six conventional turbofan airliners. So cruise-altitude turbofan noise has been recorded at ground level. — [NASA NTRS 19920011237](https://ntrs.nasa.gov/api/citations/19920011237/downloads/19920011237.pdf) (from the search snippet; I did not read the full text)
- A NASA report describes en-route jet noise as having "relatively low noise levels, lack of high frequency spectral content, and long durations" compared with terminal-area noise. — [NASA NTRS 19900015539](https://ntrs.nasa.gov/api/citations/19900015539/downloads/19900015539.pdf) (snippet only; the PDF is a scanned image with no text layer, so I could not extract numeric levels)
- An FAA presentation says low-frequency tonal content can be a challenge for high-altitude flights over very quiet areas, and that low-frequency noise decays much more slowly. — [US DOT/ROSA P dot_12253](https://rosap.ntl.bts.gov/view/dot/12253/dot_12253_DS1.pdf) (snippet)
- The EU NINHA project built long-range propagation and en-route noise impact models for turbofans, turboprops and open rotors, using EASA BANOERAC source data. — [CORDIS NINHA results](https://cordis.europa.eu/docs/results/266/266046/final1-d4-6-publishable-project-results.pdf)
- NORSAR's NORFOX DAS array (A. Baird, 2026) tracked helicopters at a few hundred metres using Doppler signatures checked against ADS-B. For jets, "source frequencies typically exceed the 62.5 Hz Nyquist" so Doppler harmonics were not resolved. However, "coherent lower-frequency arrivals are still observed, even at cruising altitudes", and tracking them across the array gave time-varying back-azimuth and apparent slowness. — [Copernicus GC14-FibreOptic-42](https://meetingorganizer.copernicus.org/GC14-FibreOptic/GC14-FibreOptic-42.html)
- Seismometers sampling at 500 sps along Alaska's Parks Highway (303 nodes, 35 days, 2019) recorded ~1,200 aircraft passages, classified as piston, turboprop or jet from "frequency combs" after removing Doppler. The authors say direction and speed can be inferred from the Doppler curves. They give no detection distances or altitudes, and say first-detection range is future work (Seppi, Tape & Fee, *The Seismic Record* 5(4), 2025). — [UAF Geophysical Institute](https://www.gi.alaska.edu/news/seismic-data-can-identify-aircraft-type); [UAF news](https://www.uaf.edu/news/uaf-study-seismic-data-can-identify-aircraft-by-type.php)
- Meng & Ben-Zion (2018) catalogued airplanes and helicopters on the dense Sage Brush Flats nodal array near Anza, California: 1,816 manually detected air-traffic events from 2014, with MATLAB Doppler modelling code. — JGR Solid Earth 123, 4783–4797, [doi:10.1029/2017JB015240](https://doi.org/10.1029/2017JB015240); [Mendeley dataset](https://data.mendeley.com/datasets/kpftptxdj5)
- Follow-up work automated aircraft-signal detection in seismic array data with machine learning (Zhang, Arrowsmith et al., 2022, with Meng and Ben-Zion). — [SUSTech faculty page](https://sustech.edu.cn/en/faculties/haoranmeng.html)
- A single-seismometer study at Guangzhou Baiyun airport estimated aircraft speed, acceleration and altitude by Doppler-curve fitting during takeoff and landing only, not cruise. — [EurekAlert release](https://www.eurekalert.org/news-releases/1106579) (search snippet)
- I found no paper reporting a single ground seismometer detecting a jet at cruise altitude and fitting its Doppler curve. The search turned up only low-altitude or terminal-area results, plus the NORFOX array result above. — (negative search result; see searches for [UAF](https://www.gi.alaska.edu/news/seismic-data-can-identify-aircraft-type) and [NORFOX](https://meetingorganizer.copernicus.org/GC14-FibreOptic/GC14-FibreOptic-42.html))

### Inferences
- **[inference] Geometry and spreading.** The minimum slant range is about 10.7 km. Spherical spreading from 1 m is then about 81 dB at closest approach and about 90 dB at 30–35 km slant range. A prop at 300–1,000 m AGL has 20–30 dB less spreading loss. That alone explains why the colsto technique has a 4–10 km range for props: a cruise jet starts in a far worse position.
- **[inference] Absorption.** Using standard ISO 9613-1-type absorption coefficients, from memory and not re-sourced here: below about 200 Hz the loss over an 11–35 km path is a few dB at most. At about 1 kHz it is tens of dB. Trent 800-series fan blade-pass tones at cruise N1 are likely in the high hundreds of Hz to low kHz range: wide-chord fan with about 26 blades, N1 of a few thousand rpm, both unverified. Those tones would be heavily attenuated. Only the low-frequency content can plausibly survive to the ground: buzz-saw or multiple pure tones at N1 shaft harmonics, broadband jet-mixing noise, and the "coherent lower-frequency arrivals" NORFOX saw.
- **[inference] Refraction shadow zone.** At FL350, ISA temperature is about −54 °C (c ≈ 297 m/s). The tropical surface is about +28 °C (c ≈ 348 m/s). With no wind, Snell's invariant (cos θ / c) means only rays leaving the aircraft at depression angles of at least about 31° reach the ground, since arccos(297/348) ≈ 31°. Shallower rays turn upward. The direct-ray ground footprint is therefore limited to roughly 25–40 km either side of the track, and the strongly sheared upper-tropospheric winds can shift it substantially. Beyond that lies a geometric shadow zone, reached only by scattered or turbulent energy, so stations 100+ km from the track should be treated as non-starters for direct-path tones.
- **[inference] Doppler is large, which helps.** Cruise TAS of about 242 m/s against c ≈ 297 m/s at the source gives M ≈ 0.82. For rays that reach the ground (|cos θ| ≤ 0.85), the received-frequency factor 1/(1 − M cos θ cos ψ) runs from about 3.3 (approaching, ahead on track) to about 0.59 (receding). A 50 Hz shaft tone would sweep from about 165 Hz down to about 30 Hz over the 4–6 minutes the aircraft takes to cross the footprint. That is a far larger and slower sweep than a prop's S-curve, and very diagnostic if any tone is detectable. Convective amplification also favours the forward arc. Forward-arc buzz-saw noise plus a 3× upshift could push energy above the Nyquist of 100 sps seismometers (50 Hz) during approach. Only the receding branch might fall in band.
- **[inference] Accuracy if detected.** With a single station and a clean tone, an S-curve fit constrains the closest-approach time well (seconds) and the speed-to-sound-speed ratio reasonably. Closest-approach distance and side are poorly constrained, because altitude and lateral offset trade off and the stratified sound-speed and wind profile must be modelled. Expect several km of cross-track ambiguity and left/right ambiguity unless there are two or more stations or an array. This is still potentially valuable because MH370's primary-radar track over the peninsula and Malacca Strait is already known approximately. A detection would mainly serve as an independent timing and track check, not a new search area.

### Gaps
- I have no sourced numeric ground-level dBA or OASPL for a twin-engine widebody at FL350. The NASA PDFs were scanned images. The Georgia Tech/FAA "En Route Jet Aircraft Noise Analysis" report and the EASA BANOERAC study should hold these numbers.
- I could not confirm Trent 892 fan blade count, cruise N1 rpm, or measured cruise tone spectra.
- The NORFOX abstract does not give the altitude, frequency band or SNR of the jet arrivals.

## 2. Can underwater hydrophones detect aircraft overhead, and could IMOS/CTBTO hydrophones have heard MH370 at cruise?

### Takeaway
Air-to-water aircraft detection is well established for low-flying turboprops (Urick 1972; Ferguson 1993). It works only inside the narrow Snell cone directly above the hydrophone, about 13° half-angle, plus an evanescent component that decays with depth. For a source at 10.7 km the cone footprint is only about 2–3 km wide, and the in-water level is reduced further. Deep IMS hydrophone stations are hundreds to thousands of km from any plausible MH370 cruise track. Hydroacoustic detection of MH370 in flight is physically implausible. Hydroacoustics was only ever useful for a possible impact.

### Cited Findings
- Urick (1972), "Noise signature of an aircraft in level flight over a hydrophone in the sea," JASA 52, 993–999. The underwater signature arrives by four paths: direct refracted, bottom reflections, lateral (evanescent) wave, and sea-surface scattering. In a P-3 Orion overflight of deep-water hydrophones, the signature lasted "but a few seconds" and was explained by the refracted field. In the far field the airborne source acts like an in-water source with cos² directivity and a source level 7 dB below the real source. — [Acoustics Today, Ferguson 2019 student challenge](https://acousticstoday.org/wp-content/uploads/2019/03/International-Student-Challenge-Problem-in-Acoustic-Signal-Processing-2019-Brian-G.-Ferguson-1.pdf); [Acoustics Today p.73](https://acousticstoday.org/issues/2019AT/Spring2019/files/basic-html/page73.html)
- Ferguson (1993) is the "Doppler effect for sound emitted by a moving airborne source and received by acoustic sensors located above and below the sea surface" paper the brief cites as JASA 2000. It is actually JASA 94(6), 3244–3247, 1993. It tracked the Doppler-shifted propeller blade rate of a turboprop above and below the sea surface and matched it to a two-isospeed-media ray model. — [Sonicfield library entry](https://labs.sonicfield.org/library/doppler-effect-for-sound-emitted-by-a-moving-airborne-source-and-received-by-aco) (the brief's "2000" date appears to be wrong)
- Ferguson & Lo extended this to estimating aircraft speed, altitude and propeller blade rate from the instantaneous frequency of the received signal. Ferguson, Lo & Speechley reported turboprop tones on a horizontal hydrophone line array matching the ray-path model. — [Acoustics Today 2019](https://acousticstoday.org/wp-content/uploads/2019/03/International-Student-Challenge-Problem-in-Acoustic-Signal-Processing-2019-Brian-G.-Ferguson-1.pdf)
- In 2014 CTBTO said its networks could in principle detect an aircraft impact or explosion, but processing "has not provided information as to the whereabouts of the plane". It encouraged researchers to probe the data. — [CTBTO news](https://www.ctbto.org/news-and-events/news/researchers-encouraged-probe-ctbto-monitoring-data-signs-missing-malaysian); [CBS News](https://cbsnews.com/news/missing-malaysia-air-flight-370-nuclear-test-experts-to-see-if-missing-plane-exploded)
- LANL (Stead, 2014), "Seismic and hydroacoustic analysis relevant to MH370," found only three usable stations near the search zone, with "rather inconclusive" results that "may point to a more southerly impact location". — [OSTI 1136454](https://www.osti.gov/servlets/purl/1136454)
- Curtin University (Duncan et al.) found a hydroacoustic event on 8 Mar 2014 that was later judged likely geological in origin. — [WTVR/CNN 2014](https://www.wtvr.com/2014/06/03/is-mystery-underwater-sound-the-crash-of-flight-370)
- A 2017 Scientific Reports paper reported pressure signatures in CTBTO hydroacoustic data from 8 Mar 2014 that could be associated with surface impacts. It is framed as a method, not a confirmed MH370 detection. — [Sci. Rep. s41598-017-14177-3](https://link.springer.com/10.1038/s41598-017-14177-3)

### Inferences
- **[inference] Snell's window.** arcsin(c_air/c_water) ≈ arcsin(340/1530) ≈ 12.8°. For a source at 10.7 km, refracted energy enters the water only when the aircraft is within about 10.7 × tan 12.8° ≈ 2.4 km horizontally of the point above the hydrophone, so the exposure lasts about 20 s at 242 m/s. Outside that cone only the evanescent wave reaches the water, and it decays over about a wavelength in depth (15 m at 100 Hz). An IMS SOFAR-channel hydrophone at about 1 km depth would receive essentially nothing. Bottom reflections and surface scattering add little at this range.
- **[inference] Distances.** CTBTO HA01 (Cape Leeuwin) and HA08 (Diego Garcia), and IMOS moorings off Western Australia, are hundreds to over 1,000 km from the 7th-arc region and the southern cruise track. No public hydrophone sat under MH370's cruise path. The only plausible "near-overhead" hydrophones would be unknown military or scientific moorings in the Andaman Sea or Strait of Malacca, and those are not public.
- **[inference]** Hydrophone in-flight detection should be dropped. Impact-related hydroacoustics has already been studied (CTBTO, LANL, Curtin) and is out of scope here.

### Gaps
- I did not verify the IMOS passive-acoustic mooring positions or recording schedules for March 2014.
- I did not obtain the full text of Ferguson 1993 or Urick 1972 for source levels and SNR versus altitude.

## 3. Infrasound from cruising jets: detectable by IMS infrasound arrays at range?

### Takeaway
I found no published detection of a single cruising subsonic airliner by an IMS infrasound array at regional range. Subsonic turbofans radiate little below about 20 Hz compared with the noise floors of IMS arrays, which are tuned for about 0.01–5 Hz explosions, volcanoes and microbaroms. Wind noise at island sites would also dominate. The one relevant 2026 result (NORFOX) suggests low-frequency coherent arrivals can be tracked by a dense array near the track, not at hundreds of km. MH370's southern leg may have passed within a few hundred km of IMS station IS06 (Cocos Islands), but its 2014 data are not openly downloadable.

### Cited Findings
- CTBTO said its infrasound and seismic networks could in principle catch an impact or explosion, but found nothing indicating the plane's whereabouts. — [CTBTO](https://www.ctbto.org/news-and-events/news/researchers-encouraged-probe-ctbto-monitoring-data-signs-missing-malaysian)
- NORSAR's DAS array observed coherent lower-frequency arrivals from jets at cruise and used them for back-azimuth and slowness tracking. — [GC14-FibreOptic-42](https://meetingorganizer.copernicus.org/GC14-FibreOptic/GC14-FibreOptic-42.html)
- **Verified by direct query (IRIS FDSN station service):** IMS infrasound station IS06 elements (IM.I06H1–H8, also as AU.I06H*) at about 12.15°S, 96.82°E on Cocos (Keeling) Islands have 20 sps BDF channels in metadata. A dataselect request for 2014-03-07T19:00–2014-03-08T00:30 returned HTTP 204 (no data). IMS infrasound for that date is not openly served by IRIS and would need CTBTO vDEC access. — [IRIS fdsnws station](https://service.iris.edu/fdsnws/station/1/); [IRIS fdsnws dataselect](https://service.iris.edu/fdsnws/dataselect/1/)

### Inferences
- **[inference]** A 20 sps infrasound channel (Nyquist 10 Hz) could not capture shaft or buzz-saw tones in the tens of Hz. It could see only sub-10 Hz energy, which a subsonic jet radiates weakly. Combined with the refraction shadow zone (section 1), the chance that IS06 recorded MH370 at cruise is very low unless the aircraft passed nearly overhead. Detection would also need the stratospheric and thermospheric ducting usually invoked for long-range infrasound, which applies to energetic sources, not to roughly 100 kW-class acoustic power.
- **[inference]** It is worth asking how close reconstructed southern tracks pass to Cocos (about 96.8°E, 12.2°S). If any candidate route passes within about 30–40 km, IS06 and the co-located seismometer II.COCO (section 5) become a cheap test. I did not compute this; it needs the DSTG or Iannello/Godfrey route ensembles.

### Gaps
- I found no paper quantifying the infrasound source level of subsonic airliners at cruise.
- I did not check vDEC access terms for 2014 IS06 data.

## 4. Inmarsat BFO as an existing "reverse Doppler" inversion

### Takeaway
The MH370 satellite analysis already is a reverse-Doppler track inversion. One sensor with known position and motion (Inmarsat-3F1, via the Perth ground station) logged Burst Frequency Offsets (BFO) on sparse handshakes. Those offsets were inverted, with Burst Timing Offsets (BTO, i.e. range), for the aircraft's position and velocity. The acoustic version has the same unknowns: aircraft track and speed, with known sensor location. The differences are that an acoustic version would need many sensors within about 30 km, and its Doppler is a continuous S-curve rather than roughly hourly samples.

### Cited Findings
- Ashton et al., "The Search for MH370," *Journal of Navigation* 68 (2015) 1–22, open access, [doi:10.1017/S037346331400068X](https://doi.org/10.1017/S037346331400068X). BFO is defined as the difference between received and nominal frequency at the ground station. It depends on several factors including the aircraft's location and ground velocity. — [Cambridge Core](https://cambridge.org/core/services/aop-cambridge-core/content/view/S037346331400068X)
- The aircraft terminal pre-compensates its uplink Doppler assuming a stationary satellite at a nominal position. The residual Doppler from the satellite's inclined-orbit motion is therefore what gives the BFO its geographic sensitivity, and the instantaneous velocity cannot be read off directly. — [Slate via jeffwise.net](https://www.jeffwise.net/?p=3292) (secondary, quoting an Inmarsat source; check against Ashton et al.)
- Inmarsat's Doppler analysis was publicly explained in March 2014. It initially produced two possible tracks, northern and southern, and the BFO discriminated between them. — [The Register, 2014](https://www.theregister.co.uk/2014/03/26/inmarsat_doppler_effect_helped_locate_mh370/)
- Later re-analyses use the final BFOs to infer end-of-flight behaviour. Holland (arXiv 1702.02432) infers a high-rate descent. Lyne (2024, J. Navigation) argues for a "controlled eastward descent" and criticises the official "Up-Down model". — [arXiv 1702.02432](https://arxiv.org/abs/1702.02432v1); [Lyne 2024, J. Navigation](https://resolve-he.cambridge.org/core/journals/journal-of-navigation/article/final-two-mh370-communications-suggest-controlled-eastward-descent/3B8A244FB86B058D36A406BE6EB17345)
- Others have discussed the BFO as a Doppler problem in amateur metrology forums (time-nuts, 2014). — [time-nuts archive](https://www.febo.com/pipermail/time-nuts/2014-August/086275.html)

### Inferences
- **[inference] Conceptual mapping:**

  | | Inmarsat BFO | Ground acoustic/seismic |
  |---|---|---|
  | Carrier | 1.6 GHz | tens of Hz |
  | Doppler | about v/c ≈ 10⁻⁶ fractional, about tens–hundreds of Hz | about M ≈ 0.8, a factor of 3 swing |
  | Sensors | 1, moving and known | N, fixed |
  | Samples | about 7–9 handshakes over 6+ h | continuous during roughly 5 min footprint crossings |
  | Range | BTO gives range rings | only closest-approach geometry |

  Physically the acoustic Doppler is enormous and easy to measure, if the tone is detected. The obstacle is detection range and sensor density, not frequency precision.
- **[inference]** An acoustic or seismic detection in the Malaysian or Strait of Malacca segment would add nothing to the southern search area directly. That segment is already constrained by military primary radar. It could at best tighten timing and speed at about 18:00–18:40 UTC, which feeds the initial conditions of BTO/BFO path models such as the speed and heading at the final major turn. That is a modest but real value. The southern leg, where it would matter most, has essentially no sensors within acoustic reach.

### Gaps
- I did not extract the BFO noise and bias figures (Hz) from Ashton et al. for a quantitative comparison.

## 5. Candidate public archives with incidental audio or seismic records (17:20–18:40 UTC and the southern leg)

### Takeaway
Seismic data exist and are partly public. The Malaysian MY network stations nearest the flight path, notably KUM (Kulim, about 40 km from Penang), are listed in IRIS metadata but returned no waveform data for the window. The closest openly downloadable stations are 100+ km from the radar track, outside the estimated refraction footprint (TM.SKLT, IN.PBA, GE.LHMI, PS.PSI), or have low sample rates. Island stations near possible southern routes (II.COCO, AU.XMIS) have public 20–40 sps data. Citizen audio archives are unlikely to hold anything: the overflight of the peninsula was at about 01:20–02:40 local time.

### Cited Findings (verified by direct FDSN queries, 2026-11-05)
Stations listed by the IRIS station service in the box 1°S–15°N, 92–106°E, operating on 2014-03-07 17:00–19:00 UTC — [IRIS fdsnws-station](https://service.iris.edu/fdsnws/station/1/query?minlat=-1&maxlat=15&minlon=92&maxlon=106&starttime=2014-03-07T17:00:00&endtime=2014-03-07T19:00:00&level=station&format=text):
- **MY (Malaysian Meteorological Dept.):** KUM (Kulim, Kedah; 5.290°N 100.649°E; HH 100 sps, BH 20 sps), IPM (Ipoh; 4.480°N 101.025°E), KTM (Kuala Terengganu; 5.328°N 103.136°E), FRM (FRIM Kepong; 3.233°N 101.633°E), KGM (Kulang; 2.016°N 103.319°E), KOM (Kota Tinggi; 1.792°N 103.847°E).
  - Dataselect for 2014-03-07T17:50–18:30 returned **HTTP 204 (no data)** for MY.KUM, MY.IPM, MY.KTM and MY.FRM. The waveforms are not openly archived at IRIS for this window and would need a request to MetMalaysia.
- **TM (Thai Meteorological Dept.):** SKLT (Songkhla, 7.176°N 100.616°E, BH 100 sps), SURA (Surat Thani), SRIT (Nakhon Si Thammarat), PRAC, CHBT, NAYO, SRDT, TMDB (Bangkok).
  - **TM.SKLT.BHZ returned data (HTTP 200, about 232 kB for 40 min)**.
- **IN.PBA** (Port Blair, Andaman Is.; 11.656°N 92.744°E; HH 100 sps): **data returned (HTTP 200)**.
- **GE (GEOFON/BMKG) LHMI** (Lhokseumawe, Aceh; 5.229°N 96.947°E): HHZ returned 204 at both IRIS and GEOFON. **BHZ (20 sps) and SHZ (50 sps) returned data from GEOFON**. — [GEOFON fdsnws](https://geofon.gfz.de/fdsnws/station/1/query?minlat=-1&maxlat=14&minlon=92&maxlon=105&starttime=2014-03-07&endtime=2014-03-09&level=station&format=text)
- **GE.GSI** (Nias): HHZ 204. **GE.BKNI** (Bangkinang): listed.
- **PS.PSI** (Parapat, Sumatra; BH 20 sps): data returned.
- **MS (Singapore):** BTDF, UBIN (HH 100 sps), NTU, KAPK, PTK, BESC (EH 100 sps). These are far south of the flight path.
- **Southern leg:**
  - **II.COCO** (Cocos Is., 12.19°S 96.83°E): location 10 BHZ at 40 sps **returned data** for 2014-03-07T19:00–03-08T00:30. Location 00 returned 204.
  - **AU.XMIS** (Christmas Is., 10.48°S 105.65°E, BH 40 sps): **returned data**.
  - IMS infrasound IS06 (Cocos): no public data (see section 3).

Other cited findings:
- Seismometers at 500 sps capture aircraft frequency combs. Lower sample rates limit which tones are visible. — [UAF](https://www.gi.alaska.edu/news/seismic-data-can-identify-aircraft-type)
- NORFOX at 125 sps (62.5 Hz Nyquist) could not resolve jet Doppler harmonics. — [GC14-FibreOptic-42](https://meetingorganizer.copernicus.org/GC14-FibreOptic/GC14-FibreOptic-42.html)

### Inferences
- **[inference] Proximity to the known route.** Per the brief and public reconstructions, MH370 recrossed the peninsula near Kota Bharu at about 17:30–17:37 UTC, passed close to Penang at about 18:00 UTC, and flew up the Strait of Malacca to the last primary-radar fix at about 18:22 UTC. Approximate distances:
  - **MY.KUM:** about 40 km from Penang. This is the single best candidate: possibly inside the roughly 25–40 km direct-ray footprint, and its HH channel at 100 sps is usable up to 50 Hz. Its data are not public at IRIS.
  - **MY.KTM:** about 110–130 km from the Kota Bharu crossing.
  - **TM.SKLT:** about 150 km from the Kota Bharu–Penang leg.
  - **GE.LHMI:** likely 100+ km from the Strait track.
  - **IN.PBA:** about 400+ km from the last radar point.

  All of these except KUM are likely in the acoustic shadow zone. These distances are my rough great-circle estimates and should be recomputed against the Malaysian Factual Information / Safety Investigation Report radar track.
- **[inference] Sample rate.** BH 20 sps channels (LHMI BH, PSI, GSI BH) have a 10 Hz Nyquist and are nearly useless for tonal Doppler from a turbofan. HH/EH/SH at 50–100 sps are marginal: only the receding, down-shifted branch of shaft-harmonic tones would fit below 25–50 Hz. II.COCO.10 and AU.XMIS at 40 sps have a 20 Hz Nyquist and are also marginal.
- **[inference] Citizen audio.** Xeno-canto, Macaulay Library and Freesound recordings carry date and often time metadata. Bird recordists are rarely active at 01:30–02:40 local, but nocturnal (owl, frog) recordists exist, so a date/location API query is cheap and worth doing. YouTube/Facebook uploads rarely have trustworthy timestamps. CCTV audio is generally not retained or public. Webcams with audio are unlikely for 2014.
- **[inference] Maldives.** The widely reported Kudahuvadhoo (Maldives) eyewitness "low-flying jet" claim was, as I recall, about 06:15 local (about 01:15 UTC). That is after the 00:19 UTC final handshake and inconsistent with the Inmarsat arcs. I could not reconcile the brief's "~14:00 local Maldives" with any source. This needs checking; I did not source it in this session.

### Gaps
- I did not test MetMalaysia data access policy. The MY network's 2014 waveforms may be obtainable on request.
- I did not check BMKG's own archive (Indonesia), Thai TMD's direct archive, the Raspberry Shake network (very sparse in 2014), or temporary PASSCAL/FDSN experiments (X*/Y*/Z* networks) in Malaysia or Sumatra in March 2014.
- I did not query the Xeno-canto, Macaulay or Freesound APIs.

## 6. Has anyone proposed scanning seismic or infrasound data for MH370's overflight?

### Takeaway
I found no published or forum proposal to detect MH370's in-flight overflight in seismic, infrasound or hydrophone data. All prior geophysical work targeted the impact or end-of-flight event (CTBTO, LANL, Curtin, Sci. Rep. 2017, a seismic crash-location patent). I could not find any 2026 discussion linking "colsto" or the clones to MH370.

### Cited Findings
- In 2014 CTBTO encouraged researchers to probe its data for signs of MH370, framed around explosion or impact. — [CTBTO](https://www.ctbto.org/node/4355)
- The LANL seismic/hydroacoustic analysis was impact-focused. — [OSTI 1136454](https://www.osti.gov/servlets/purl/1136454)
- A US patent covers locating aircraft crash sites in water from seismic data, again impact-focused. — [USPTO 11194068](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11194068)
- Other "non-traditional" MH370 sensing has been proposed, notably WSPR amateur-radio link disturbances. Godfrey's WSPR work is cited for a 33.2°S 95.3°E point. — [AirlineRatings](https://www.airlineratings.com/articles/comprehensive-credible-new-report-published-showing-mh370-location)
- A March 2026 blog reports the Dec-2025 to Jan-2026 search phase (about 7,236 km²) made no significant detections. It is opinion-heavy and should be treated cautiously. — [whereismh370today blog](https://whereismh370today.blogspot.com/2026/03/mh370-search-update-opinion.html)

### Inferences
- **[inference]** The absence of overflight-detection proposals in 12 years of intense amateur analysis, including the Iannello/IG community, is weak evidence that analysts either judged it implausible or never thought of it. The physics above suggests mostly the former, with one untested exception: MY.KUM near Penang.

### Gaps
- I did not search Victor Iannello's blog (mh370.radiantphysics.com), Reddit r/MH370, or Metabunk directly with site: queries, so a forum thread could have been missed. My search for colsto/MH370 found nothing.

## 7. Overall verdict and realistic experimental plan

### Takeaway
- **Hydrophone detection of MH370 in flight:** implausible, because of Snell's window and distance.
- **IMS infrasound:** implausible, and the data are not public.
- **Citizen audio at 01:30 local:** very unlikely.
- **Ground seismometers within about 30–40 km of the radar-tracked segment:** the only physically plausible avenue, and it is a long shot. The best candidate (MY.KUM, Kulim, about 40 km from Penang, 100 sps) is not public, and the public stations are mostly outside the expected footprint or under-sampled.
- **Even a success** would add timing and speed constraints to an already radar-tracked segment, not a new southern search area.
- **Nobody has validated the method on modern cruise jets with single stations.** That is the necessary first step.

### Cited Findings
- Cruise-altitude jet arrivals have been seen on a dense DAS array, with direction from array processing rather than single-sensor Doppler. — [NORFOX abstract](https://meetingorganizer.copernicus.org/GC14-FibreOptic/GC14-FibreOptic-42.html)
- Aircraft signals plus ADS-B (Flightradar24) ground truth have been used to build seismic aircraft catalogues. — [UAF](https://www.gi.alaska.edu/news/seismic-data-can-identify-aircraft-type); [Meng & Ben-Zion 2018](https://doi.org/10.1029/2017JB015240)

### Inferences (proposed plan)
1. **Validation on modern data, which is decisive and cheap.** Use OpenSky or ADS-B Exchange history to list B777/A330/A350 overflights at FL330–FL390 that pass within 0–50 km of public 100+ sps stations. Good candidates are TM.SKLT, IN.PBA and MS.UBIN today, plus mid-latitude dense networks such as Raspberry Shake and US/EU networks for statistics. Stack spectrograms on predicted closest-approach times and fit the stratified-atmosphere Doppler model (section 1). Report detection probability against lateral offset, sample rate and local time (night is quieter). If cruise-jet detection probability at 30 km is near zero on modern data, stop there.
2. **Re-run the 2014 test on public stations with ADS-B-era controls.** Even if the stations are too far away, check TM.SKLT, IN.PBA, GE.LHMI and the KTM/KUM vicinity for other known 777 overflights on 7–8 March 2014 (if 2014 ADS-B archives exist) to calibrate.
3. **Request MY network waveforms** (KUM, IPM, KTM) for 2014-03-07 17:20–18:30 UTC from MetMalaysia, and if possible request BMKG data for northern Sumatra. Search KUM for a slowly sweeping tonal arc around 17:55–18:05 UTC, with expected sweep from roughly 3× down to 0.6× of the source tone over several minutes.
4. **Southern leg.** Check whether any route-ensemble member passes within about 40 km of Cocos (II.COCO.10, IS06) or Christmas Island (AU.XMIS). Only if one does, apply the same detector to those windows.
5. **Guard against confirmation bias.** Run a blind analysis: scan the full night of data, not just the expected window, and report false-alarm rates. Any "detection" should come with the rate of similar features on control nights.
