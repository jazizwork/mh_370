# Aircraft Doppler Audio Geolocation: Limitations, Failure Modes, Data Constraints, Countermeasures, Privacy/Ethics

Context (as of 5 Nov 2026): The technique was popularised by YouTuber "Colsto" in a ~29-min video published ~2 Nov 2026 ("I discovered a sound that leaks your exact location (and it's everywhere)"). He located a security-camera clip (trees/river, only known to be filmed 8 Sep 2026 somewhere in the continental US) to roughly 100 m / "a few hundred feet", using two propeller-aircraft flyovers 920 s apart plus ADS-B data (~50 GB) and terrain elevation; ~70,000 candidate points were filtered to ~15,000 and the top score stood out. He released no code. Within days several open-source reimplementations appeared (doppler-locate, dopplertrack, flyover-locator, franken_doppler_finder, dopplerprint on PyPI 2026-11-03). — [IBTimes UK, 3 Nov 2026](https://www.ibtimes.co.uk/inaudible-aircraft-sounds-reveal-recording-location-1829800); [Simon Willison, 3 Nov 2026](https://simonwillison.net/2026/Nov/3/a-sound-that-leaks-your-exact-location/); [Pillitteri summary](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect); [thakicloud write-up, updated 4 Nov 2026](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/); [dopplertrack](https://github.com/mjshiggins/dopplertrack); [doppler-locate](https://github.com/digitalis-p/doppler-locate); [flyover-locator](https://github.com/amintt2/flyover-locator); [franken_doppler_finder](https://github.com/Dicklesworthstone/franken_doppler_finder)

Caveat on evidence base: everything about the technique itself comes from a YouTube video, news write-ups that quote only the creator, and GitHub READMEs written in the days afterwards. None of it is peer-reviewed or independently field-validated at scale. Accuracy figures (~100 m; 67 m; 52 m synthetic) come from a handful of cases, mostly the creator's own challenge clip.

---

## 1. ADS-B data coverage, gaps and access constraints

### Takeaway
The technique only works where the overhead aircraft are in a public, archived ADS-B/MLAT dataset at low enough altitude to be heard. Coverage depends on volunteer receivers: good over the continental US/Europe, patchy in rural, oceanic and conflict areas. GNSS spoofing/jamming, military aircraft that don't broadcast, and privacy programmes all remove or corrupt tracks. Free historical archives exist (adsb.lol from 2023; OpenSky only by approved application), but terms are shifting.

### Cited Findings
**Which archives the tools actually use**
- The open reimplementations use the **adsb.lol "globe history" daily archive** (ODbL-licensed, ~3–4 GB/day globally). doppler-locate defaults to one UTC day over the continental US. Other regions need a bounding-box ingest that the README calls **untested**. — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [flyover-locator](https://github.com/amintt2/flyover-locator); [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- **adsb.lol history starts in 2023.** doppler-locate notes that 2017 test recordings (HWNDU clips, Greeneville TN) therefore cannot be geolocated. Historical depth is a hard limit. — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- flyover-locator warns that adsb.lol's volunteer-collected coverage "can have gaps in rural areas". It filters to aircraft below 6,000 m, excludes known jets, and samples one point every 4 s (~280 MB/day after filtering). — [flyover-locator](https://github.com/amintt2/flyover-locator)
- **Cross-network discrepancies matter.** In doppler-locate's single-event case, a faint curve at ~1279 s had **no matching aircraft in adsb.lol**. The author attributes this to receiver/MLAT coverage differences with Flightradar24. Many webcam test archives were in "rural areas with little low-altitude coverage." — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- One write-up: "In an empty sky, no answer is possible." Reliability scales with how many ADS-B-tracked aircraft were overhead. — [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)

**Receiver geometry / MLAT / oceans**
- Flightradar24: since **January 2025** its MLAT needs only **3 receivers** (previously 4). The lowest altitude at which multiple receivers can hear the same aircraft is typically **5,000–10,000 ft** in most locations, so low-altitude non-ADS-B (Mode S/MLAT-only) traffic is often invisible. A flight drops off the map when too few receivers hear it. — [FR24 blog: How we track flights with MLAT](https://www.flightradar24.com/blog/inside-flightradar24/how-we-track-flights-with-mlat/); [FR24 support: how it works](https://support.fr24.com/support/solutions/articles/3000117422-how-does-flightradar24-work-)
- Over oceans, ground receivers can't help. Satellite ADS-B fills in, with "dynamic" coverage, and only for ADS-B-equipped aircraft. — [FR24 blog: how does FR24 track aircraft](https://www.flightradar24.com/blog/inside-flightradar24/how-does-fr24-track-aircraft/); [Kalagireva & Radkov 2016](https://e-university.tu-sofia.bg/ETUS/publikacii/files/2266_Kalagireva_Radkov_AFASES2016.pdf)
- Explainer: track gaps over oceans/remote areas happen because "no receivers on the ground means no one is listening." — [planes.fyi](https://planes.fyi/blog/what-is-ads-b)

**ADS-B Exchange sale and community forks**
- **JETNET acquired ADS-B Exchange (announced 25 Jan 2023).** ADSBx said it would keep "unfiltered" data. Volunteer feeders objected to their data being monetised. — [JETNET press release](https://jetnet.com/news/jetnet-acquires-ads-b-exchange.html); [AIN, 25 Jan 2023](https://ainonline.com/aviation-news/business-aviation/2023-01-25/jetnet-buys-ads-b-exchange); [Hackaday, 26 Jan 2023](https://hackaday.com/2023/01/26/ads-b-exchange-sells-up-contributors-unhappy); [RTL-SDR](https://www.rtl-sdr.com/ads-b-exchange-acquired-by-private-firm-jetnet/)
- Feeders moved to community alternatives: **adsb.fi, adsb.lol** ("completely open-source and community-driven… ODbL-licensed data via a free API") and **airplanes.live** ("unfiltered aviation data"). Jack Sweeney (ElonJet) launched his own tracker in Feb 2023. — [awesome-adsb list](https://github.com/rickstaa/awesome-adsb); [scramble.nl forum](https://forum.scramble.nl/viewtopic.php?p=1050655); [Business Insider India](https://www.businessinsider.in/tech/news/the-college-student-who-tracks-elon-musks-private-jet-is-launching-his-own-flight-tracking-website/articleshow/97710843.cms)
- The ADS-B One API repo was **archived 29 Apr 2026** and reportedly merged into airplanes.live. — [ADS-B API comparison (third-party, data as of 2 Sep 2026)](https://flyitalyadsb.com/en/dati/confronto/)

**API terms and pricing (third-party, verify against official pages)**
- adsb.lol: rate limits are "dynamic based on environment load", and a future API key (obtained by feeding) is planned. It offers annual dumps `globe_history_YYYY` under ODbL. Commercial terms are "not specified." — [adsblol/api (via ecosyste.ms)](https://awesome.ecosyste.ms/projects/github.com%2Fadsblol%2Fapi); [comparison page](https://flyitalyadsb.com/en/dati/confronto/)
- airplanes.live: the free tier is 1 req/s. A Contributor tier allows 8,640 req/day with historical access. — [comparison page](https://flyitalyadsb.com/en/dati/confronto/); [airplanes-live/api-archive](https://github.com/airplanes-live/api-archive)
- **OpenSky Network historical data** is accessed through a Trino/MinIO SQL interface. Access is **application-reviewed**; OpenSky may decline insufficiently justified applications and revoke access for misuse. It is free for qualifying research; commercial users need a written licence with case-by-case pricing (per a third-party mirror of OpenSky plan data). Bulk whole-day pulls are discouraged in favour of contacting OpenSky. The backend migrated in 2024 and the Impala shell is deprecated. — [OpenSky Trino docs](https://openskynetwork.github.io/opensky-api/trino.html); [api-evangelist mirror (unofficial)](https://raw.githubusercontent.com/api-evangelist/opensky/refs/heads/main/plans/opensky-trino-api.yml)

**GNSS interference (corrupts ADS-B positions in conflict regions)**
- EUROCONTROL's 2024 Performance Review Report (Mar 2025) estimated up to **38% of European en-route traffic** passes through areas intermittently affected by RFI. Its voluntary reporting system logged **3,115 GNSS reports out of 7,453** in 2024 (~10/day). — [EUROCONTROL, GNSS Vulnerabilities & Emerging Threats (ICAO MID 2026 workshop)](https://www.icao.int/sites/default/files/MID/MeetingDocs/2026/GNSS%20%26%20PBN%20Workshop/Documentation/GNSS%20Vulnerabilities%20and%20Emerging%20Threats-EUROCONTROL.pdf); [ICAO APAC 2025 symposium slides](https://www.icao.int/sites/default/files/APAC/Meetings/2025/2025%20ICAO%20APAC%20Radio%20Navigation%20Symposium%20%20Radio%20N/4-Setting%20the%20Scene/SP03-ICAO-APAC-GNSS-Vulnerabilities-Threats.pdf)
- EUROCONTROL analyses: one spoofing event left **93 aircraft with ADS-B gaps**. Of 397 transatlantic flights spoofed over the Black Sea, ~10% were still broadcasting NIC = 0 (no position integrity) on entering oceanic airspace. EUROCONTROL monitors interference through a dedicated 1090 MHz network ("SHERLOCK"). — [same EUROCONTROL/ICAO decks](https://www.icao.int/sites/default/files/SAM/MeetingDocs/2026/0902-Taller-Radionavegacion-NAMCARSAM/2.%20Presentaciones%20-%20Presentations/ICAO-SAM-GNSS-Vulnerabilities-Threats-SEP2026.pdf)
- An EASA–EUROCONTROL joint GNSS interference action plan was published in response to a 6 June 2025 letter from 13 EU states (one source dates it to March 2026). EASA SIB 2022-02R3 says spoofing is a greater risk than jamming. — [GPS World](https://www.gpsworld.com/easa-eurocontrol-publish-action-plan-on-safety-during-gnss-interference/); [Geoawesome](https://geoawesome.com/easa-updates-gnss-guidance-as-jamming-and-spoofing-surge-what-geospatial-professionals-need-to-know/)

**Military aircraft not broadcasting**
- US military aircraft may fly with transponders off under "due regard". The Pentagon has agreements with the FAA and foreign ANSPs to switch off ADS-B when necessary, and DoD has called open-source tracking "a direct threat to our ability to conduct military air operations." A 2025 bill (Sen. Cruz) sought to curb Army helicopter ADS-B-off flights after the DCA collision. — [TWZ](https://www.twz.com/tracking-u-s-military-aircraft-online-could-become-much-harder); [Jalopnik](https://jalopnik.com/1914231/ted-cruz-army-helicopter-flight-tracking-bill/)
- Analysts read gaps in a P-8A track (Apr 2026) as likely transponder-off periods on station. This is a hypothesis, not confirmed. — [ItaMilRadar, 13 Apr 2026](https://www.itamilradar.com/2026/04/13/interrupted-tracks-the-complex-mission-of-a-p-8a-poseidon-between-djibouti-and-the-mediterranean/)
- A track gap alone doesn't show a deliberate shutoff. Coverage and transponder type (Mode S vs ADS-B) produce the same blank. — [TWZ](https://www.twz.com/tracking-u-s-military-aircraft-online-could-become-much-harder)

**LADD / PIA privacy programmes**
- **LADD** only limits display via FAA data feeds. Non-FAA receivers (ADSBx, adsb.lol, etc.) still capture the broadcast ICAO address. — [NBAA LADD page](https://nbaa.org/aircraft-operations/security/privacy/limiting-aircraft-data-displayed-ladd/)
- **PIA** (Privacy ICAO Address) is an alternate, temporary ICAO address not linked to the owner in the FAA registry. It is limited to US-registered, 1090ES-equipped aircraft using a third-party callsign, in US airspace. NBAA recommends using LADD and PIA together. — [FAA PIA page](https://www.faa.gov/media/91986); [Bombardier explainer](https://fullthrottle.bombardier.com/tech-corner/faa-privacy-icao-address-pia-program-an-alternate-solution-for-flight-tracking-privacynbsp); [AIN, Dec 2019](https://ainonline.com/aviation-news/business-aviation/2019-12-13/nbaa-advises-using-both-existing-new-privacy-programs)

### Inferences
- LADD/PIA hide *who* owns an aircraft, not *where* it is. Unfiltered aggregators still publish the positions, so these programmes barely affect the acoustic technique, which needs only position, speed and type class (prop vs jet). PIA aircraft may lack a type in tar1090-db, so they could be wrongly excluded or included by the prop/jet filter.
- The technique is strongest where three things overlap: dense volunteer receivers, frequent low-altitude prop traffic (GA airfields, seaplane bases, coastal commuter routes) and post-2023 recordings. It is weakest in conflict zones, which is the opsec-relevant case. There, GNSS spoofing corrupts ADS-B positions, military aircraft go dark, civil traffic is often rerouted away, and receivers are sparse. A spoofed position would yield a confidently wrong observer location, not just a missing one.
- Because coverage differs between networks (adsb.lol vs FR24 vs OpenSky), results depend on which dataset was used. Investigators should combine archives, and a "no match" is weak evidence against a claimed location.

### Gaps
- No official current adsb.lol or airplanes.live terms-of-service text was retrieved. Rate and licence details come from a third-party comparison page (dated 2 Sep 2026).
- No quantitative global or regional low-altitude coverage maps or receiver-density statistics were found (e.g., % of airspace below 3,000 ft covered).
- Current ADS-B Exchange (JETNET) historical-data pricing was not found. The ~$20m deal price is unverified.
- Specific datasets for Ukraine/Middle East low-altitude civil coverage were not found.

---

## 2. Audio-side limitations

### Takeaway
The signal is faint propeller/rotor tonals at ~50–600 Hz, often inaudible, recovered from a whitened spectrogram. Detection fails at a few km for pistons, ~7 km for turboprops, and almost always for jets. Speed changes, cuts, and unknown or misaligned clocks break the inter-event timing the method depends on. The creator reports that high-pass filtering, added noise and telephone-band compression did **not** remove the signal in his tests. Platform codec effects have not been systematically studied.

### Cited Findings
- **Source type:** The method needs steady-tone emitters (propeller aircraft are best, helicopters are kept). Jets are excluded by default because their noise is broadband and smears in the spectrogram, and including them blew up compute (search 305 s, 34 GB RAM). The best jet-involving pair ranked only 8th. — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- **Frequency band:** Propeller tones sit around **50–600 Hz** and are often inaudible. Steady local hums (the README cites 107, 160 and 241 Hz) must be removed first. — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- **Detection range limits:** In doppler-locate's tests, pistons at **4–10 km**, turboprops **beyond 7 km** and almost all jets were missed. In the Lorain webcam test, three pistons at 3–9 km were missed, and a Cessna 182 at 3.4 km faded after CPA, leaving speed and distance undetermined. A synthetic pass at 3.6 km was not found, and found passes had distances **12–29% too long**. — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- **Required content:** At least two clear prop flyovers (two-event search). Single-event mode is "implemented but not validated." Without a date, flyover-locator needs ≥2 clear passes to identify the day, and searches up to 31 days and 100 km radius by default. — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [flyover-locator](https://github.com/amintt2/flyover-locator)
- **Model assumptions:** The fit assumes constant-speed straight-line flight, so descending or slowing aircraft bias it. One event fit 134.4 Hz where the true geometry needed 126 Hz, which forced wide tolerances (±8% f0, ±8 s). — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- **Confusers:** Road vehicles must be separated (CPA under 150 m or under 30 m/s). Boats near harbours give similar slow-source signatures. Engines, tools and music can match aircraft templates. — [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/); [Firecrawl summary of tool READMEs](https://github.com/digitalis-p/doppler-locate)
- **Compression:** "YouTube compression degrades the spectrogram." Many webcam archives had **silent audio tracks**. — [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/); [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- **Creator's own robustness tests:** "high-pass filtering, added background noise, and telephone-style compression left the aircraft patterns detectable." Cutting sections out or adding noise cancellation "could make it harder." — [IBTimes UK, 3 Nov 2026](https://www.ibtimes.co.uk/inaudible-aircraft-sounds-reveal-recording-location-1829800)
- **Timestamps:** The audio clock must be known and is fitted with a shared shift. The creator's demo used the *gap* between events (920 s), which is preserved without an absolute timestamp, plus a known date. — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [IBTimes UK](https://www.ibtimes.co.uk/inaudible-aircraft-sounds-reveal-recording-location-1829800)
- **Tuning bias:** The detector's confidence rule was tuned on the challenge video itself, so its reported results are called "optimistic." On that video, 4 of 8 high/medium detections matched ADS-B, against ~0.6 expected by chance. — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- **Smartphone low-frequency processing:** Wind noise sits at ~0–100 Hz, so a ~100 Hz high-pass is a common wind-reduction choice. Fixed high-pass filters also remove other low-band content. These sources are patents and a pro-audio spec, not phone-specific data. — [US patent 8600072 (wind noise)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8600072); [Shure A15HP spec](https://www.almoproav.com/productdetails/SHURE/A15HP)
- **Parallel forensic literature (ENF):** Electric-network-frequency forensics, the closest analogue of a weak tonal used for forensic inference, finds that lossy compression (MP3/AAC) changes ENF values and creates casework pitfalls. Phase-based methods can survive MP3, and a notch filter is an effective anti-forensic erasure. Reliability depends on SNR and reference length. — [Grigoras, AES](https://aes2.org/publications/elibrary-page/?id=14331); [Springer, Circuits Systems Signal Process. 2018](https://link.springer.com/article/10.1007/s00034-018-0793-9); [Hua et al., arXiv 2011.00176](https://arxiv.org/pdf/2011.00176.pdf); [DSU audio forensics lecture](https://dsu-digital-sound-design.github.io/dad-498-audio-forensics/lectures/week-6/enf-analysis-and-metadata-consistency)

### Inferences
- **Pitch shift vs time stretch (my own physics reasoning, not tested in sources):**
  - For a straight constant-speed pass, v/c = (f_approach − f_recede)/(f_approach + f_recede). This ratio is unchanged by a pure pitch shift, and f0 is a free parameter anyway. So **pitch shifting alone probably does not defeat speed estimation**.
  - **Time-stretching or speed changes** alter the steepness of the Doppler transition, which sets CPA distance (≈ v × transition time scale), and they alter the inter-event gap. Both are central constraints.
  - A sample-rate mislabel (44.1 vs 48 kHz) scales both time and frequency by ~8.8% (48000/44100 = 1.088). That is the same order as the tools' ±8% f0 tolerance.
  - Edits that cut, splice or re-order footage destroy inter-event timing outright.
- **Codecs:** Perceptual codecs (AAC/Opus) at low bitrates may discard quiet low-frequency tonals masked by louder content, and voice-optimised paths (WhatsApp/Telegram voice notes, call-mode Opus) apply high-pass and noise suppression. However, the creator reports that telephone-band compression did not kill detection. A plausible explanation is that prop harmonics extend above 300 Hz. This needs systematic testing. No study of TikTok/Instagram/WhatsApp video pipelines specifically was found.
- **Wind and urban settings:** Wind noise (<100 Hz) overlaps the fundamental band. Urban canyons add reflections that produce multiple delayed copies with different Doppler (mirror-image sources), and traffic and HVAC hums add tonal clutter. These likely reduce detection range below the ~3–7 km figures above. This is inference; no source quantified it.
- **Multiple aircraft:** Overlapping aircraft produce crossing ridges. The tools handle this through ranked pairing and a "no other nearby aircraft in between" constraint, but ambiguity grows near busy airfields.

### Gaps
- No peer-reviewed study of this technique's error rates across devices, codecs or platforms was found.
- No measured smartphone mic/camera-app low-cut data (iPhone/Android "wind reduction") was found.
- No source tested time-stretching or pitch-shifting countermeasures directly.
- The franken_doppler_finder and dopplertrack READMEs were not fetched in full.

---

## 3. Atmospheric effects

### Takeaway
A still-air, 343 m/s assumption gives measurable residual errors. Adding model winds and temperature at aircraft altitude (NOAA GFS) materially improves fits. Refraction, inversions and temperature-dependent sound speed are second-order for location but affect audibility and range.

### Cited Findings
- doppler-locate's baseline is still air with c = 343 m/s. Adding **NOAA GFS 0.25°** wind and temperature at aircraft altitude reduced one residual from **0.55 Hz to 0.21 Hz**. Wind fitted from audio (14.4 m/s from 316°) closely matched GFS (15.1 m/s from 322°). The tool optionally uses surface wind from Iowa Environmental Mesonet ASOS and models path-mean sound speed, wind and emission-time delay. — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- Pipelines use Copernicus GLO-90/GLO-30 DEM or SRTM terrain to compute 3-D slant ranges. — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [flyover-locator](https://github.com/amintt2/flyover-locator); [IBTimes UK](https://www.ibtimes.co.uk/inaudible-aircraft-sounds-reveal-recording-location-1829800)
- flyover-locator does not mention atmospheric corrections. — [flyover-locator](https://github.com/amintt2/flyover-locator)

### Inferences
- The speed of sound varies by ~0.6 m/s per °C (textbook acoustics, not sourced here). Between a 20 °C surface and ~0 °C at 2 km, c differs by ~12 m/s (~3.5%). That biases inferred speed and range by a few percent unless modelled, consistent with the 12–29% range errors seen above being dominated by other factors.
- Wind can shift the apparent Doppler, and the wind vector can be fitted from the audio itself (as shown above). Without GFS, strong winds aloft could push a candidate outside the tolerance window.
- Refraction from temperature inversions or upwind shadow zones mostly changes *whether* a flyover is heard, not where the CPA appears. It can, however, create late or early arrivals and fades after CPA, which match the C182 failure mode above. This is inference, not tested.

### Gaps
- No quantitative study of atmospheric error contribution to final location error was found.

---

## 4. Geometric ambiguity

### Takeaway
One flyover gives speed, closest-approach time and slant range. That puts the observer on a ring around the aircraft's track at the CPA point, which on the ground is two mirror points either side of the track, plus along-track uncertainty. You need at least two flyovers on non-parallel tracks (or other cues) to resolve it, which is why every tool requires ≥2 clear events.

### Cited Findings
- Each event yields speed, CPA distance and CPA time, and "one event's fit alone could not fix the location." — [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- doppler-locate's main mode requires two events. Its single-event mode (one curve plus a known time window) is unvalidated, and the README does not explicitly address mirror solutions. Results come as ranked flight pairs with confidence tiers. In the main case the margin was narrow: score 3.66 vs 3.50 for ranks 1 and 2. — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- Demo outcomes: Oyster Bay NY truth ranked 1st of 1,060 flight pairs, 67 m from the camera (heat-map peak 13 m). Synthetic rank 1 was at 52 m. The creator used two flyovers 920 s apart. A one-minute clip with a known time pointed to the same location. — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [IBTimes UK](https://www.ibtimes.co.uk/inaudible-aircraft-sounds-reveal-recording-location-1829800)
- flyover-locator searches 200 m then 100 m grids. Candidates must match speed, distance and the time gap to a following point with no other aircraft in between, and all clear passages must match. — [flyover-locator](https://github.com/amintt2/flyover-locator)

### Inferences
- The mirror ambiguity is resolved only if the second aircraft's track is non-parallel. On a busy single airway or approach corridor where all traffic flies the same line, ambiguity can persist even with many events. Terrain (DEM), plausibility (water vs land) or visual cues may then decide it.
- Narrow score margins (3.66 vs 3.50) mean that a stated location should come with a confidence region and the runner-up candidates, not a pin. That matters for evidentiary use under the Berkeley Protocol's accuracy principle.

### Gaps
- No source quantifies how often mirror or parallel-track ambiguity occurs in practice.

---

## 5. Countermeasures / opsec

### Takeaway
Simple filtering, added noise and phone-band compression reportedly do **not** remove the signature. Effective countermeasures are removing or replacing audio, cutting or re-timing the footage, aggressive noise suppression, delaying publication without disclosing the date, and not recording where low-altitude prop traffic is heard. Existing military and journalist opsec guidance targets geotags and visual clues, not ambient audio.

### Cited Findings
- **Reported ineffective (creator tests):** high-pass filtering, added background noise and telephone-style compression. **Possibly effective:** cutting sections from the recording and additional noise cancellation. — [IBTimes UK, 3 Nov 2026](https://www.ibtimes.co.uk/inaudible-aircraft-sounds-reveal-recording-location-1829800)
- The creator himself says locating someone this way is unlikely and "easier methods likely exist." — [IBTimes UK](https://www.ibtimes.co.uk/inaudible-aircraft-sounds-reveal-recording-location-1829800); [Pillitteri](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect)
- A write-up suggests creators check whether aircraft are audible before publishing, "similar to stripping metadata," and argues that the usual notice-and-remove defence is weak because the leak is ambient. — [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- In ENF forensics, a notch filter at the hum frequency erases the trace. A tracking or comb notch on Doppler-varying tones is the analogue, though harder because the frequency moves. — [DSU lecture](https://dsu-digital-sound-design.github.io/dad-498-audio-forensics/lectures/week-6/enf-analysis-and-metadata-consistency)
- **US Army guidance** (2011–2012 materials, reiterated 2021): never geotag photos; deployed soldiers should not use location-based services; disable device geotagging; review photos and videos before posting for troop locations and equipment. A 2007 incident is cited in which posted helicopter photos enabled a mortar attack. — [Army.mil, Geotagging poses security risks (2012)](https://www.army.mil/article/75165/geotagging_poses_security_risks); [Army.mil, 2021](https://www.army.mil/article/242603/just_scrolling_through_army_urges_responsible_social_media_usage); [DVIDS](https://www.dvidshub.net/news/printable/63192)

### Inferences
- Ranked countermeasures (my synthesis):
  1. Strip or replace the audio track. This is the only certain fix.
  2. Low-pass or band-stop below ~1 kHz, or apply broadband AI noise suppression (voice isolation), accepting audio quality loss.
  3. Cut and splice to destroy inter-event timing, or publish short clips with fewer than two flyovers.
  4. Delay posting and withhold the date. This widens the day-search, though flyover-locator can search 31 days.
  5. Avoid recording under GA/approach paths.
  - Pitch-shifting alone is probably weak (see section 2). Time-stretching is probably stronger, but untested.
- In the military context, this technique is less relevant than cell-network, visual and metadata exposure, because front-line airspace is usually empty of tracked civil prop traffic. It matters more for rear areas, domestic bases near GA airfields, and for activists or victims in ordinary civilian airspace.

### Gaps
- No journalist-safety guide (CPJ, RSF, Freedom of the Press Foundation) addressing ambient-audio geolocation was found. Existing guides focus on metadata and visual geolocation.
- No independent test of countermeasures exists beyond the creator's statements.

---

## 6. Privacy and ethics

### Takeaway
This is a dual-use OSINT technique. It can verify claimed locations and trace leaks, but it can also locate people who deliberately hid where they are (activists, abuse survivors, whistleblowers), and its outputs are probabilistic and easy to over-trust. The Berkeley Protocol's principles of accuracy, harm minimisation and security apply directly. Tool authors are already adding consent-use clauses.

### Cited Findings
- The **Berkeley Protocol on Digital Open Source Investigations** (OHCHR + UC Berkeley Human Rights Center, published 2022, HR/PUB/20/2) sets standards for collecting, analysing and preserving digital information professionally, legally and ethically. It includes protecting the digital, physical and psychosocial safety of investigators, witnesses, victims and others. Core principles are summarised as competency, objectivity, accuracy and security. — [UN Digital Library record](https://digitallibrary.un.org/record/3973652?ln=en); [Berkeley Political Review, 31 Mar 2022](https://bpr.studentorg.berkeley.edu/2022/03/31/open-source-investigations-legal-accountability-and-ethical-labyrinths-in-the-dawn-of-a-new-era-of-international-justice)
- Koenig (AJIL Unbound, 2024) identifies the ethical risks of open-source investigations as inaccurate conclusions (unchecked bias, inadequate verification, insufficient expertise), physical, digital or psychological harm, and insults to dignity. — [Cambridge AJIL Unbound](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/FE78D42FD4D344F6B1EE98413C20B5DF/S2398772324000023a.pdf/ethical-considerations-for-open-source-investigations-into-international-crimes.pdf)
- **Tool-author ethics clauses:**
  - doppler-locate: use only on "your own recordings, public challenges, or recordings made with the maker's consent"; must not be used "to locate people who have not chosen to share where they are." Its git hooks block precise coordinates and media from commits.
  - flyover-locator: use only on your own recordings or in a legitimate investigation; set an APP_PASSWORD on public deployments.
  - — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [flyover-locator](https://github.com/amintt2/flyover-locator)
- Legitimate uses suggested: tracing the origin of leaked content, checking whether fabricated video matches its claimed region, and auditing livestream location exposure. — [thakicloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- **Precedents of soldiers or posts exposing locations:**
  - **Strava heatmap (Jan 2018)** revealed forward bases and patrol routes in Syria, Afghanistan, Niger and Israel. Nathan Ruser spotted it, and the Pentagon reviewed policy. — [Bellingcat Strava guide, 29 Jan 2018](https://bellingcat.com/resources/how-tos/2018/01/29/strava-interpretation-guide); [NPR/WBUR](https://www.wbur.org/npr/581597949/pentagon-reviews-gps-data-after-soldiers-strava-tracks-are-seemingly-exposed)
  - DFRLab and Bellingcat proved Russian troops' presence in Ukraine using soldiers' public social media photos. — [DFRLab](https://dfrlab.org/?p=448)
  - **Makiivka (1 Jan 2023):** Russia blamed soldiers' mobile phone use for a HIMARS strike that killed 89 (Russian figure). Ukrainian officials and pro-Kremlin correspondents disputed this as blame-shifting. An analyst noted cases where Russian soldiers posted easily located footage that was then struck. — [CBC](https://amp.cbc.ca/lite/story/1.6704793); [SCMP](https://scmp.com/news/world/europe/article/3205516/russia-blames-its-soldiers-mobile-phone-use-ukrainian-missile-strike-barracks)
  - US Army: 2007 helicopter photos enabled a mortar attack. — [Army.mil](https://www.army.mil/article/75165/geotagging_poses_security_risks)
- Earlier flight-tracking privacy conflict: jet trackers (ElonJet) and LADD/PIA show an existing tension between public ADS-B and privacy. — [Business Insider India](https://www.businessinsider.in/tech/news/the-college-student-who-tracks-elon-musks-private-jet-is-launching-his-own-flight-tracking-website/articleshow/97710843.cms); [NBAA](https://nbaa.org/aircraft-operations/security/privacy/limiting-aircraft-data-displayed-ladd/)

### Inferences
- **Who is most at risk:** people in ordinary civilian settings near GA airfields, seaplane bases or flight-school areas (suburban US/Europe) who post longer unedited clips with ambient sound. Examples are domestic-abuse survivors posting from shelters, activists or dissidents in exile, and whistleblowers' leaked recordings.
- **Practical risk vs other methods:** Visual geolocation, metadata, cell or IP data and acquaintance leaks are usually easier, as the creator himself says. The incremental risk is therefore highest when a target has already cleaned visual clues and metadata.
- **Evidentiary risk:** Narrow margins, tuning bias and coverage-dependent "no match" results create false-positive and false-negative risk. Under the Berkeley Protocol's accuracy principle, results should be reported as probabilistic with uncertainty and the alternatives, corroborated with independent methods, and the raw ADS-B snapshot preserved (archives change; adsb.lol only from 2023).
- **Harm minimisation:** Investigators should avoid publishing precise coordinates of private individuals. The tool authors' commit hooks model this.

### Gaps
- No specific Bellingcat or GIJN ethics piece on acoustic or Doppler geolocation was found; the technique is ~3 days old as of these notes.
- No documented real-world case (as of 5 Nov 2026) of this technique being used against a person or in a legal proceeding was found.
- The Berkeley Protocol full text was not fetched. Principles are cited via a catalogue record and secondary summaries.
