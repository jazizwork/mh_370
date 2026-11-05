# Audio Forensics and OSINT Analogues to Aircraft-Doppler Geolocation: Techniques and Case Studies

Scope note: this file sets aircraft-Doppler geolocation (matching faint aircraft Doppler curves in a recording's audio to public ADS-B tracks) against older, established ways of getting time, place, distance or direction from sound. Each finding is tagged:
- **[DOPPLER-AIRCRAFT]**: the aircraft-Doppler plus flight-tracking technique itself
- **[DOPPLER-OTHER]**: Doppler analysis of a non-aircraft source (for example a munition)
- **[OTHER AUDIO]**: other audio techniques (ENF, crack-bang timing, sound delay, signatures)
- **[NON-AUDIO FLIGHT DATA]**: flight-tracking data used for verification without audio

Context for the aircraft-Doppler claim, which is covered in depth elsewhere:
- [DOPPLER-AIRCRAFT] A YouTube video by the OSINT researcher "colsto" (around early November 2026) claims to locate a recording to about 100 m from roughly 60 s of audio. It matches aircraft Doppler curves in the audio against public ADS-B flight tracks, and the curves reportedly do not need to be audible to a listener. — [TechRadar](https://www.techradar.com/computing/cyber-security/youtuber-discovers-aircraft-noise-trick-that-can-geolocate-your-videos-to-within-100m-doppler-effect-pinpoints-locations-from-just-60-seconds-of-audio); [Digg summary](https://digg.com/ai/7wr4rmyp); [X post, AGTP, citing @0x45o, Nov 3 2026](https://x.com/AGTPinsights/status/2117387488155029700)
- [DOPPLER-AIRCRAFT] A third-party write-up ran an open-source reimplementation on the original demo. It reports detecting 5 aircraft Doppler events in a 29-minute audio track in 36 s of processing. — [ThakiCloud blog](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- Caveat: these are demo and social-media claims, not peer-reviewed results. Search summaries also say the creator has not released tooling. A "DOPPLERGEIST" GitHub project is mentioned in coverage, but I did not verify it. — [lilithai.dev summary](https://lilithai.dev/radar/i-discovered-a-sound-that-leaks-your-exact-location-and-it-s-everywhere?lang=en)

---

## Q1. Electrical Network Frequency (ENF) analysis: dating and grid-locating recordings from mains hum

### Takeaway
ENF is the closest established forensic analogue to aircraft-Doppler geolocation. Both match a faint, unintended signal in a recording's audio against an external time-stamped reference log: the grid-frequency database for ENF, ADS-B flight tracks for Doppler. ENF is mature and used in court in the UK (Met Police logs since about 2005), but it mainly answers "when" and "was it edited?" It can only tell "where" at grid or interconnect level, with ~100-mile-scale experimental results at best. That makes aircraft-Doppler's claimed ~100 m spatial resolution a qualitatively different capability.

### Cited Findings
**How it works**
- [OTHER AUDIO] ENF analysis compares the frequency drift of background mains hum (nominally 50/60 Hz) in a recording against historical grid-frequency records. The hum acts as a time-dependent watermark that can indicate when a recording was made, reveal edits, or help rule out tampering. — [Wikipedia: ENF analysis](https://en.wikipedia.org/wiki/Electrical_network_frequency_analysis)
- [OTHER AUDIO] UK mains frequency sits around 50 Hz and fluctuates by "a few thousandths of a hertz." The Met compares a recording's frequency pattern against a database logging these changes 24 hours a day, 365 days a year, which provides a date and time stamp. — [BBC News, "The hum that helps to fight crime", Dec 2012](https://www.bbc.co.uk/news/science-environment-20629671)

**Who uses it**
- [OTHER AUDIO] Dr Alan Cooper, a senior digital forensic practitioner at the Met Police forensic lab in south London, uses ENF. In 2012 the Met had been logging grid frequency for about seven years. — [BBC News 2012](https://www.bbc.co.uk/news/science-environment-20629671)
- [OTHER AUDIO] The Met Police have kept frequency records since 2005. The Register quoted ENF being called "the most significant development in audio forensics since Watergate." — [The Register, 1 June 2010](https://www.theregister.com/2010/06/01/enf_met_police/) (via [Wikipedia](https://en.wikipedia.org/wiki/Electrical_network_frequency_analysis))
- [OTHER AUDIO] Bavarian police (Germany) have kept mains-frequency records since 2010. — [Süddeutsche Zeitung 2011](https://www.sueddeutsche.de/muenchen/landeskriminalamt-dem-verbrechen-auf-der-spur-1.1061222-2) (via Wikipedia)
- [OTHER AUDIO] UK court example: an undercover police recording of an arms deal involving Hume Bent, Carlos Moncrieffe and Christopher McKenzie. The defence alleged the police had tampered with the recording, and ENF analysis was used to authenticate it. — [BBC News 2012](https://www.bbc.co.uk/news/science-environment-20629671); also [Crime+Investigation UK](https://www.crimeandinvestigation.co.uk/articles/hidden-electrical-noise-can-catch-criminals)
- [OTHER AUDIO] Cooper (2008, AES 33rd International Conference) describes an automated ENF approach. Wikipedia, citing the BBC, says the process is fully automated in the UK. — [AES e-library 14411](https://www.aes.org/e-lib/browse.cfm?elib=14411); [Wikipedia](https://en.wikipedia.org/wiki/Electrical_network_frequency_analysis)

**Academic lineage**
- [OTHER AUDIO] Catalin Grigoras (2005, *International Journal of Speech, Language and the Law*) wrote a foundational paper, "Digital audio recording analysis: the Electric Network Frequency (ENF) Criterion." It argues ENF can show whether and where a recording was edited and whether it was made at the claimed time. — [Equinox journal](https://journal.equinoxpub.com/IJSLL/article/view/9977)
- [OTHER AUDIO] Kajstura et al. (2005, *Forensic Science International*) is a parallel early paper. — [FSI](http://www.fsijournal.org/article/S0379-0738%2804%2900766-2/abstract) (via Wikipedia)
- [OTHER AUDIO] A 2013 AAFS abstract by Grigoras and Smith argues that forensic use needs validated reference databases and known-error corrective procedures. — [AAFS 2013 B25](https://www.aafs.org/sites/default/files/media/documents/AAFS-2013-B25.pdf)
- [OTHER AUDIO] University of Maryland (Min Wu's group): Garg, Varna and Wu (2011, ACM Multimedia) showed "visual ENF." Indoor lights flicker with the supply, so ENF can be extracted from video frames despite heavy aliasing at 25–30 fps. Audio and visual ENF in the same file should match, which can expose an audio track laid over the video later. — [ACM DL doi:10.1145/2072298.2072303](http://dl.acm.org/citation.cfm?id=2072303)
- [OTHER AUDIO] Hajj-Ahmad, Garg and Wu, "ENF Based Location Classification of Sensor Recordings" (IEEE WIFS 2013), identify which grid a recording came from without a concurrent reference. They use statistical features of ENF variation fed into a multiclass classifier, and report "high accuracy" grid identification. — [UMD PDF](https://www.mast.umd.edu/files/paper_ENF/conf_paper7_WIFS13.pdf); [IEEE via Unpaywall](https://unpaywall.org/10.1109%2FWIFS.2013.6707808)
- [OTHER AUDIO] The IEEE Signal Processing Cup 2016 was built around grid-of-origin identification. Follow-on work includes Šarić et al. (2016), which covered 10 grids, found Random Forest best, and reported accuracy gains of 3–19% from new features. Suresha et al. (2017) reported a multi-stage SVM with a 17.33% improvement over baseline. — [Šarić et al. repository](https://researchrepository.mi.sanu.ac.rs/handle/123456789/4935); [Suresha et al., NITK](https://idr.nitk.ac.in/handle/123456789/7495)

**Location resolution and limitations**
- [OTHER AUDIO] SWGDE (US Scientific Working Group on Digital Evidence) reports experimental location estimates "on the order of 100 miles" using clean, non-forensic data from the US Eastern Interconnect. Real forensic recordings are noisier. SWGDE also notes the US has three major independent interconnections, which bounds the grid-level inference. — [SWGDE ENF discussion paper 09-A-001](https://www.swgde.org/documents/published-complete-listing/09-a-001-swgde-electric-network-frequency-discussion-paper/)
- [OTHER AUDIO] Huijbregtse and Geradts identify limits from fixed frequency offsets during recording and from self-similarity within the frequency database. These limits matter most for recordings shorter than about 10 minutes. — [Huijbregtse & Geradts PDF (archived)](https://web.archive.org/web/20110915000000/https://www.forensic.to/ENF%20processed.pdf)
- [OTHER AUDIO] Because the UK is a single synchronous grid, frequency is essentially the same across the country. That is good for timestamping but means ENF cannot locate a recording within Great Britain. — [Crime+Investigation UK](https://www.crimeandinvestigation.co.uk/articles/hidden-electrical-noise-can-catch-criminals); [SWGDE](https://www.swgde.org/documents/published-complete-listing/09-a-001-swgde-electric-network-frequency-discussion-paper/)

### Inferences
- Methodologically, aircraft-Doppler geolocation is "ENF with a moving, spatially varying reference." ENF is spatially uniform across a grid, so it gives time but not place. Aircraft Doppler curves are a function of observer position relative to a known track, so they can in principle give both place and time. This is the strongest conceptual precedent to cite.
- The two methods share the same weaknesses: dependence on a trustworthy reference log (grid database or ADS-B), short-recording ambiguity, and robustness to compression or filtering. The ENF community's insistence on validated databases and known error rates (Grigoras & Smith; SWGDE) is the bar aircraft-Doppler would need to meet for courtroom use.
- ENF can also detect splices. Aircraft Doppler curves that are discontinuous or inconsistent with a single track could likewise flag edited audio, but I found no source demonstrating this.

### Gaps
- I found no published Met Police error rate or total case count for ENF.
- I found no documented OSINT (non-court) case where ENF located a conflict video. Its use in open-source verification appears rare, but I could not confirm that.
- I did not obtain the accuracy figures from the WIFS 2013 paper itself; only the abstract says "high accuracy."

---

## Q2. Bellingcat / Forensic Architecture / Earshot / NYT / ShotSpotter: gunshot and explosion acoustics

### Takeaway
The best-documented audio forensics in OSINT is ballistic acoustics. It uses the time gap between a bullet's supersonic crack and the muzzle blast to estimate shooter distance, and spectrograms to count shots and infer fire rate and weapon type. It also uses flash-to-bang delay to estimate the distance to an explosion. Earshot (Lawrence Abu Hamdan) and the academic Robert Maher are the key practitioners, and they have worked for Forensic Architecture, Bellingcat, NYT, CNN and AP. Earshot has also used Doppler analysis of an incoming munition, which is the closest published OSINT precedent to aircraft-Doppler work.

### Cited Findings
**Crack-bang (shockwave to muzzle blast) ranging**
- [OTHER AUDIO] Shireen Abu Akleh killing (Jenin, May 2022), report by Forensic Architecture and Earshot authored by Dr Lawrence Abu Hamdan. It measured a crack-to-muzzle-blast gap of about 300 ms and assumed a bullet speed of 860 m/s, estimating the shooter about 180 m from the microphone. All 13 gunshots (volleys of 6 and 7) came from a single static position. — [FA/Earshot Audio and Acoustic Analysis report, 2 Nov 2022 (PDF)](https://content.forensic-architecture.org/wp-content/uploads/2022/11/2022.11.02_Final-Audio-and-Acoustic-Analysis-SAA-Report.pdf)
  - Sanity check (my own calculation): d = Δt / (1/c − 1/v) = 0.3 / (1/343 − 1/860) ≈ 171 m, which is consistent with "approximately 180 m."
- [OTHER AUDIO] Robert Maher (Montana State University) did audio analysis for news investigations of the Abu Akleh killing. The distance he measured matched the location of the Israeli forces. In 2019 he also helped NYT with audio analysis corroborating the identity of an Islamic State militant. — [Bozeman Magazine / MSU, July 2022](https://m.bozemanmagazine.com/news/2022/07/18/114495-msu-audio-forensics-expert-aids-news)
- [OTHER AUDIO] Gaza aid convoy killings (Tal as-Sultan, Rafah, 23 March 2025), analysed by Bellingcat (Carlos Gonzales, Jake Godin, 9 Apr 2025) with Dr Robert Maher and Steven Beck (Beck Audio Forensics). Findings:
  - Maher measured a crack-to-muzzle gap of 76–77 ms for the first shots, about 45 m. Beck estimated about 40 m.
  - A five-shot sequence with about 50 ms gaps implies about 30 m. Later gaps of 42 ms and 20 ms imply closer ranges.
  - The experts assumed bullet speeds of 800–1000 m/s.
  - 27 shots in the first 3 s; a burst of 22 shots in 2 s, consistent with about 600 rpm; at least three shooters at the start.
  - Stated caveats: echoes inflate the crack counts, an exchange of fire cannot be ruled out, and without video the shooters' movement is unknown.
  — [Bellingcat, "What Audio Analysis Reveals About Aid Workers Killed in Gaza"](https://www.bellingcat.com/news/2025/04/09/gaza-palestine-israel-killed-death-aid-workers-international-red-cross-crescent-audio-analysis/)
- [OTHER AUDIO] The same Rafah incident, analysed by Earshot with Forensic Architecture: at least 910 gunshots identified, 844 of them over 5.5 minutes. Some shots had no supersonic crack, only muzzle blast, which implies the shooter was within about 1–4 m. — [Dawn](https://www.dawn.com/news/1975588); [Qatar Tribune](https://www.qatar-tribune.com/article/221219/world/israeli-forces-fired-over-900-bullets-to-kill-gaza-medics-in-2025-report) (secondary reporting on the Earshot/FA report)
- [OTHER AUDIO] Hind Rajab killing (Gaza City, Jan 2024), Forensic Architecture with Earshot:
  - 64 gunshots counted in the final 6 s of the phone call.
  - Fire rate of 750–900 rpm.
  - Shooter estimated at 13–23 m.
  The IDF disputes the findings. — [Forensic Architecture, "The Killing of Hind Rajab"](https://forensic-architecture.org/investigation/the-killing-of-hind-rajab); [Al Jazeera, 23 June 2024](https://www.aljazeera.com/news/2024/6/23/israeli-tank-fired-at-hind-rajab-family-car-from-metres-away-investigation)
- [OTHER AUDIO] An early landmark is Abu Hamdan's audio-ballistic analysis with Forensic Architecture of the May 2014 killings of Nadeem Nawara and Mohammad Abu Daher (Beitunia, West Bank). Frequency analysis of the gunshots showed live ammunition was fired, not rubber bullets as claimed. The case is the subject of his 2016 exhibition "Earshot" at Portikus. — [My Art Guides: Earshot exhibition](https://myartguides.com/exhibitions/frankfurt/lawrence-abu-hamdan-earshot)
- [OTHER AUDIO] Physics background: the muzzle blast is highly directional, varying with azimuth from the muzzle to the recorder. A primer blast is recorded only behind or beside a nearby shooter. Both factors complicate distance and attribution estimates. — [Acoustics.org (ASA lay-language paper on forensic gunshot audio)](https://acoustics.org/tag/gunshots); [Maher, AES paper](https://nios.montana.edu/rmaher/publications/maher_aes_1016_9634.pdf); [NIJ: audio forensic gunshot analysis and multilateration](https://nij.ojp.gov/index%2Ephp/library/publications/audio-forensic-gunshot-analysis-and-multilateration)

**Explosion flash-to-bang ranging plus flight tracking (PS752)**
- [OTHER AUDIO + NON-AUDIO FLIGHT DATA] Ukraine International Airlines Flight PS752 (Tehran, 8 Jan 2020), Bellingcat, 9 Jan 2020. Bellingcat quotes: "By measuring the time that it took for the camera to hear the explosion (~10.7 seconds), we estimated the straight-line distance of the event from the camera at approximately 3.6 kilometers. By using the Pythagoras theorem, we calculated the land distance … to be approximately 3.3 kilometers. We then cross-referenced this distance with our tentative geolocation of the video, and also plotted the flight trajectory of PS752 (taken from FlightRadar24) … The land location of the event aligned with the trajectory of the plane as extended based on FlightRadar24's data." The video was geolocated to Parand. NYT obtained the original from the filmer and confirmed its authenticity. — [Bellingcat](https://www.bellingcat.com/news/mena/2020/01/09/video-apparently-showing-flight-ps572-missile-strike-geolocated-to-iranian-suburb/); [CJR Q&A with NYT on the Iran flight](https://www.cjr.org/q_and_a/new-york-times-iran-ukraine-flight.php)
  - Note: one search-engine summary misreported the ground distance as 2.8 km. The primary Bellingcat text says 3.3 km.
  - This is the clearest documented precedent for combining an acoustic range (sound delay) with Flightradar24 track data. It is not Doppler.

**Doppler analysis of a munition (closest precedent to aircraft-Doppler)**
- [DOPPLER-OTHER] al-Ahli Arab Hospital explosion (Gaza, 17 Oct 2023), Earshot thread of 20 Oct 2023:
  - Earshot treated the whistle of the incoming munition as a Doppler shift: rising pitch on approach, falling pitch as it recedes.
  - Video 1, about 150 m SE of the hospital: pitch rises then falls before impact, implying the munition passed closer to the camera first, so a trajectory from the NE, E or SE.
  - Video 2, about 1,500 m NW: pitch rises continuously until the explosion, suggesting an eastern approach.
  - Earshot argued both are inconsistent with the IDF's claimed south-western launch.
  - Earshot also said the IDF's released "intercepted call" put the two voices on separate L/R channels, indicating editing.
  - The thread published no frequency values or calculations.
  — [Earshot thread (Threadreader)](https://threadreaderapp.com/thread/1715381907230232929)
- [DOPPLER-OTHER] Conflicting assessments of al-Ahli:
  - HRW said the audible sound indicated a motor-propelled projectile, not artillery or air-dropped bombs, but could not conclusively identify the munition.
  - AP and CNN assessed a Palestinian rocket broke up and part of it struck the site.
  - The IDF and the US ODNI told CNN the audio could not support definitive conclusions, partly because of possible phone-microphone distortion.
  — [Al Jazeera survey of OSINT findings](https://www.aljazeera.com/news/2023/10/20/what-have-open-source-videos-revealed-about-the-gaza-hospital-explosion); [Jurist explainer](https://www.jurist.org/features/2023/10/23/explainer-suspicions-shroud-al-ahli-hospital-blast-probes/); [NPR/KUNC](https://www.kunc.org/2023-10-23/what-new-analysis-shows-about-the-gaza-hospital-explosion)
  - Lesson for aircraft-Doppler: a single-microphone Doppler curve from a phone can be contested on device-distortion grounds. The al-Ahli dispute shows how such evidence is received when stakes are high.

**Multi-video audio synchronisation**
- [OTHER AUDIO] NYT Visual Investigations, Las Vegas shooting (Oct 2017): "10 Minutes. 12 Gunfire Bursts. 30 Videos." The team built a timeline independent of officials by aligning dozens of video and audio clips using the gunfire bursts. It won 3rd prize, Long Form, in the 2018 World Press Photo Digital Storytelling contest. — [World Press Photo](https://www.worldpressphoto.org/collection/digital-storytelling-contest/2018/10-minutes-12-gunfire-bursts-30-videos)
- [OTHER AUDIO] GIJN material describes using gunshot waveform spikes as audio markers to sync footage from different angles. GIJN resources also cover matching police radio audio files to social-media video. — [GIJN audio tag](https://gijn.org/tag/audio/); [GIJN geolocation tag](https://gijn.org/tag/geolocation)

**ShotSpotter-style acoustic triangulation**
- [OTHER AUDIO] ShotSpotter (now SoundThinking) uses fixed microphone arrays and time-difference-of-arrival to detect and locate gunfire. The company claims 97% accuracy for detecting and locating gunfire. Critics, including the MacArthur Justice Center, note the system is proprietary and not openly audited. — [Campus Safety Magazine](https://www.campussafetymagazine.com/?p=104979); [MacArthur Justice Center](https://www.macarthurjustice.org/?p=35780)
- [OTHER AUDIO] Chicago OIG (Aug 2021) reviewed 50,176 alerts from Jan 2020 to May 2021. Only 9.1% led to evidence of a gun-related crime. The OIG stressed this measured "operational value," not sensor accuracy, and did not conclude the alerts were false. — [Reason](https://reason.com/2021/08/24/chicago-audit-finds-shotspotter-alerts-rarely-lead-to-evidence-of-gun-crimes/); [The Register](https://www.theregister.com/2021/08/25/shotspotter_chicago_report/); [SoundThinking response](https://www.soundthinking.com/blog/shotspotters-important-role-in-improving-public-safety/)
- [OTHER AUDIO] An AP investigation found the system can miss gunshots or classify other sounds as gunfire. — [Reason (summarising AP)](https://reason.com/2021/08/24/chicago-audit-finds-shotspotter-alerts-rarely-lead-to-evidence-of-gun-crimes/)

### Inferences
- The lineage runs from courtroom gunshot acoustics (Maher, NIJ-funded work) to NGO and newsroom investigations (Earshot/FA from 2014, then Bellingcat, NYT and CNN). All of these use known propagation physics (speed of sound, bullet speed) against features timed in a spectrogram. Aircraft-Doppler geolocation is the same kind of reasoning, but it inverts an external track dataset rather than a known source speed.
- Earshot's al-Ahli work is the nearest published OSINT use of Doppler. It inferred direction qualitatively from one source, with the munition track unknown. Aircraft-Doppler instead fits the observer's position quantitatively against a known ADS-B track, which is far more constrained.
- ShotSpotter shows how hard it is to validate acoustic location claims, even with dedicated, synchronised arrays. A single uncalibrated phone mic is a weaker sensor.

### Gaps
- I could not fetch Earshot's own website for a full case list. The figures for the Rafah medics case come from secondary press reports of the Earshot/FA report.
- I found no NYT acoustic analysis for Uvalde; this was not pursued further.
- I found no quantitative error bars published for Earshot's al-Ahli Doppler inference.

---

## Q3. Prior cases using aircraft or helicopter sounds, ambient sounds or signatures to geolocate or verify footage

### Takeaway
I found no documented, citable OSINT case before the 2026 "colsto" demonstration that used aircraft Doppler matched to ADS-B or Flightradar24 data to geolocate or timestamp a video. The established practice is different:
- flight-tracking data used visually or contextually, as in PS752 and the Minab check;
- engine-sound signatures used to classify a threat, as in Ukraine's Sky Fortress acoustic Shahed detection;
- language or dialect used as a coarse regional clue;
- Earshot's aerial-sound documentation in Lebanon, which is a record of events, not geolocation.
Church bells, call to prayer, train horns and birdsong appear in generic geolocation advice, but I found no well-documented case built on them.

### Cited Findings
**Aircraft and drone sound signatures (classification, not geolocation of a video)**
- [OTHER AUDIO] Ukraine's "Sky Fortress" (Nebo Fortetsia) is a nationwide network of cheap microphones. It listens for the distinctive engine signatures of Shahed-type drones (and some missiles) to give early warning and track them. Reported sensor counts vary: more than 10,000 (Wikipedia, citing Reuters), or about 9,500 phone-based units (ITC.ua). — [Wikipedia: Sky Fortress](https://en.wikipedia.org/wiki/Sky_Fortress_(drone_defense_system)); [ITC.ua](https://itc.ua/en/news/in-ukraine-9-500-phones-detect-shaheds-by-sound-and-transmit-air-defense-data); [FlightGlobal](https://flightglobal.com/military-uavs/how-ukraine-turned-mobile-phone-microphones-into-an-air-defence-network/159997.article); [Janes, Nov 2023](https://www.janes.com/defence-news/news-detail/ukraine-conflict-ukrainian-air-defence-employs-passive-sensors-for-detection-and-tracking)
- [OTHER AUDIO] Its acoustic data is fused with radar and AI in "Sky Map." Reporting in 2026 describes export interest and deployments: Lithuania from 2026, and reportedly US use in the Gulf. The US Prince Sultan Air Base claim comes only via a ZeroHedge/Pulse item and should be treated as weak. — [Al Jazeera, 4 May 2026](https://www.aljazeera.com/news/2026/5/4/what-is-the-ukrainian-anti-drone-system-sky-map-being-used-in-the-gulf); [United24](https://united24media.com/world/ukraines-acoustic-skyfortress-will-track-low-flying-drones-and-missiles-over-lithuania-23064); [NV.ua](https://english.nv.ua/nation/u-s-eyeing-ukraine-s-drone-detection-tech-50589732.html); [Pulse (weak)](https://www.pulse.bot/defense/news/us-deploys-ukrainian-acoustic-sensors-interceptor-drones-at-prince-sultan-air-base-e21e179d-5ab8-46bc-90d1-e277ce247ad7/)
- [OTHER AUDIO] A Ukrainian government claim, unverified, says detection stays largely unaffected despite Russian attempts to alter drone acoustic signatures, thanks to training on a large sound dataset. — [The Defense Post](https://gecici.thedefensepost.com/?p=108947)
- [OTHER AUDIO] Helicopters have distinctive acoustic signatures: a periodic low-frequency main rotor, a higher-pitched tail rotor, and "blade slap" in some flight regimes. These are used in detection research (DLR). I found no OSINT case using them to verify a video. — [DLR, Aerospace 12:903 (2025)](https://elib.dlr.de/217291/1/aerospace-12-00903.pdf)
- [OTHER AUDIO] Cruise missiles: Bellingcat identified the Kh-101 that hit Okhmatdyt children's hospital in Kyiv (8 July 2024) from visual features and a 3D model, not from sound. — [Bellingcat, 9 July 2024](https://www.bellingcat.com/news/2024/07/09/russian-missile-identified-in-kyiv-childrens-hospital-attack/)

**Aerial sound as a documentary record (Earshot, Lebanon)**
- [OTHER AUDIO] Lawrence Abu Hamdan's "Air Pressure (A Diary of the Sky)" (2021–) is a sonic and data documentation of Israeli military overflights of Lebanon. It draws on UN reports and his own audio diary from May 2020 to May 2021. Reported counts differ by source:
  - about 22,000 airspace violations from 2006 to 2021, sourced from 243 UN letters;
  - AirPressure.info lists about 9,000 jet and 13,200 drone incursions;
  - 2,412 jet and drone instances in the May 2020 to May 2021 diary period.
  — [Middle East Eye](https://www.middleeasteye.net/news/lebanon-israel-air-incursions-massive-scale-detailed); [La Virreina Barcelona](https://ajuntament.barcelona.cat/lavirreina/en/activities/air-pressure/761); [My Art Guides (Turin)](https://myartguides.com/exhibitions/turin/lawrence-abu-hamdan-air-pressure)
- [OTHER AUDIO] Al Jazeera (Aug 2024) covers Israeli sonic booms over Lebanon as psychological warfare, quoting Abu Hamdan. — [Al Jazeera](https://www.aljazeera.com/features/2024/8/10/sonic-booms-the-psychological-warfare-israel-uses-to-sow-fear-in-lebanon)

**Flight tracking used to verify time and place (no audio)**
- [NON-AUDIO FLIGHT DATA] PS752 (above) combined a sound-delay distance with the Flightradar24 trajectory. — [Bellingcat](https://www.bellingcat.com/news/mena/2020/01/09/video-apparently-showing-flight-ps572-missile-strike-geolocated-to-iranian-suburb/)
- [NON-AUDIO FLIGHT DATA] A Bellingcat challenge newsletter describes checking Flightradar24 for specific airlines (Condor, Icelandair, Vueling) over the Alps at a claimed time, and finding two matches. This is the visual-contrail or airliner-in-frame chronolocation approach. — [Bellingcat Challenges: "Above and Beyond"](https://bellingcat-challenges.beehiiv.com/p/above-and-beyond)
- [NON-AUDIO FLIGHT DATA] Caveat: flight-tracker positions can be wrong in conflict zones because of GNSS jamming or spoofing. One cited case put a plane hundreds of kilometres off its real location. — (search-result summary of [Bellingcat Challenge newsletter](https://bellingcat-challenges.beehiiv.com/p/after-the-blast); treat as indicative)
- [NON-AUDIO FLIGHT DATA] Prigozhin's Embraer crash (23 Aug 2023): flight-tracking data showed nothing abnormal until the last ~30 s. Witnesses described bangs or "several explosions." AP's frame-by-frame video analysis was consistent with a mid-air explosion. No published audio spectral analysis was found. — [The Star / AP](https://thestar.com.my/news/world/2023/08/24/russian-mercenary-yevgeny-prigozhin039s-plane-appeared-fine-on-radar-until-last-30-seconds); [TBS News](https://www.tbsnews.net/world/prigozhin-plane-crash-villagers-hear-bang-then-see-plane-plummet-ground-687910)

**Language, dialect and ambient sound in generic geolocation guidance**
- [OTHER AUDIO] BBC verification guidance lists audio clues, including language and dialect, alongside visual clues for location checks. — [BBC verification transcript](https://gotranscript.com/public/bbc-explains-how-it-verifies-viral-news-videos)
- [OTHER AUDIO] GIJN's emergency verification guide tells investigators to "look (and listen)" for identifying elements that indicate date and time. — [GIJN guide](https://gijn.org/stories/a-guide-to-verifying-digital-content-in-emergencies/)
- [OTHER AUDIO] Geolocation tip lists, such as those based on Josemonkey's, treat accents and spoken language as region-level "clues" rather than precise locators. — [Authentic8](https://www.authentic8.com/blog/8-geolocation-tips-josemonkey)
- [OTHER AUDIO] Academic and patent work on audio-only geolocation is coarse:
  - US patents 10,275,671 and 10,853,676 extract MFCC features and match them against city-level statistical models to validate claimed location. Their accuracy is unvalidated.
  - "Audio Geolocation: A Natural Sounds Benchmark" (arXiv) addresses geolocating from natural sounds such as birdsong.
  — [USPTO 10853676](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10853676); [Audio Geolocation benchmark](https://aitopics.org/doc/arxivorg:7E9ABA6D)

### Inferences
- Before 2026, aircraft entered OSINT verification mainly as visual objects (contrails, airliners in frame, crash debris) or through track data. Sound entered as a classifier (what weapon or drone) or as a ruler (flash-to-bang, crack-bang). Aircraft-Doppler merges the two strands: sound as a precise ruler against a known aircraft track. That combination appears to be novel in the public OSINT record.
- Sky Fortress shows that state-scale acoustic aircraft detection works with cheap phone-grade microphones. That is relevant evidence that consumer microphones capture usable aircraft acoustics, though it concerns low, loud, nearby drones rather than faint, high-altitude airliners.
- Call to prayer, church bells and train horns are generally treated as coarse cultural or regional cues. The cases I could find point to Doppler, flash-to-bang, crack-bang and ENF as the only audio methods yielding quantitative location or time.

### Gaps
- I found no documented case using call to prayer timing, church bell patterns, train horn signatures or birdsong to geolocate a specific newsworthy video. Such cases may exist on social media (for example individual geolocators' threads), but none surfaced in citable form.
- I found no documented case using the engine sound of a Shahed, Kh-101 or helicopter in a published video to verify that video's time or place, as opposed to identifying the munition type.
- I found no case before colsto's 2026 demonstration matching aircraft audio (Doppler or otherwise) to ADS-B Exchange or Flightradar24 to time-stamp a video. This is a negative finding from limited searching and should be stated with that hedge.

---

## Q4. Sound-based time verification (flight schedules, sonic booms, synchronising events)

### Takeaway
Sound is routinely used for relative timing: syncing multiple videos on gunshots or explosions, or flash-to-bang delays. Absolute time verification from sound is established mainly through ENF, matched to a grid-frequency log. I found no published OSINT case using sonic booms or scheduled-flight noise to establish a video's absolute time; aircraft-Doppler matching to ADS-B would be the first well-publicised method of this kind.

### Cited Findings
- [OTHER AUDIO] ENF provides absolute date and time stamping against a 24/7 grid-frequency log. It is used in UK criminal cases. — [BBC News 2012](https://www.bbc.co.uk/news/science-environment-20629671)
- [OTHER AUDIO] Relative synchronisation from sound:
  - NYT Las Vegas aligned about 30 videos on gunfire bursts. — [World Press Photo](https://www.worldpressphoto.org/collection/digital-storytelling-contest/2018/10-minutes-12-gunfire-bursts-30-videos)
  - GIJN describes gunshot waveform spikes as sync markers. — [GIJN](https://gijn.org/tag/audio/)
  - Bellingcat cross-checks multiple videos by syncing a key moment. — [Bellingcat Challenges](https://bellingcat-challenges.beehiiv.com/p/after-the-blast)
- [OTHER AUDIO] Physics teaching material on the 2020 Beirut explosion uses the lag between the shock front and sound arrival at known distances to estimate distance. This is the same flash-to-bang principle used in OSINT. — [arXiv 2209.14441](https://arxiv.org/pdf/2209.14441)
- [OTHER AUDIO] Low-cost infrasound and seismic sensors (for example Raspberry Shake/Boom) record explosions and booms with absolute timestamps. These can in principle corroborate the time of a sound captured on video. — [Raspberry Shake community](https://community.raspberryshake.org/t/about-the-rboom-infrasound-category/48)
- [DOPPLER-AIRCRAFT] The aircraft-Doppler method claims to recover location, and implicitly time, by matching Doppler curves to ADS-B tracks. — [TechRadar](https://www.techradar.com/computing/cyber-security/youtuber-discovers-aircraft-noise-trick-that-can-geolocate-your-videos-to-within-100m-doppler-effect-pinpoints-locations-from-just-60-seconds-of-audio)

### Inferences
- Aircraft-Doppler matching to ADS-B would be to absolute time what ENF is to absolute time. It would also add location, because each aircraft's track is spatially specific while grid frequency is spatially uniform. Several overflights would over-determine both time and position.
- Sonic booms are a plausible time anchor, since military flights are sometimes logged and booms are recorded by seismic and infrasound networks. I found no published case using one to verify a video's time.

### Gaps
- I found no documented OSINT case using sonic booms or airline schedules (heard rather than seen) to verify the time of a video.
- I did not find a published case using Raspberry Shake or infrasound data to timestamp a specific viral video, though the capability exists.
