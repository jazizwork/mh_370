# Official Investigation and Searches for MH370 (9M-MRO), status as of 5 November 2026

Note on times: official Malaysian documents and much press coverage use Malaysian time (MYT = UTC+8). UTC is used below unless marked MYT. The flight departed late on 7 March UTC, which was early on 8 March MYT.

## 1. Known flight path timeline (ACARS, ADS-B/Mode S, military and neighbouring radar)

### Takeaway
MH370 behaved normally until it passed IGARI at about 17:20 UTC. Secondary radar (Mode S/ADS-B) was lost at about 17:21 UTC. Malaysian military primary radar then followed an unidentified target (taken to be MH370) back across the peninsula and up the Strait of Malacca and the Andaman Sea, until a last point at 18:22:12 UTC, about 10 NM beyond waypoint MEKAR. After that, the only data are Inmarsat SATCOM metadata.

### Cited Findings
- Departure: 00:42 MYT on 8 March 2014 (16:42 UTC on 7 March). 227 passengers and 12 crew (239 total), Kuala Lumpur to Beijing. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370); [ATSB search overview](https://www.atsb.gov.au/mh370-search-overview)
- Last ACARS transmission: 01:06 MYT (17:06–17:07 UTC). — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370); [MiGFlug, 26 Aug 2026](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- Last voice transmission: "Good night Malaysian three seven zero" at 01:19:30 MYT (17:19:30 UTC). — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- The aircraft passed waypoint IGARI (6°56′12″N 103°35′6″E) at 17:20:31 UTC. The Mode S symbol disappeared from secondary radar about 5 s later, and the transponder had stopped by about 17:21 UTC. MiGFlug gives the transponder loss as 01:21:13 MYT. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370); [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- Malaysian military primary radar: the target turned right, then left onto a south-westerly heading, crossed the Malay Peninsula, passed south of Penang (about 17:52 UTC / 01:52 MYT per MiGFlug), and crossed the Strait of Malacca. It passed VAMPI and Pulau Perak at about 18:03 UTC (02:03 MYT), then followed airway N571. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370); [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- Last radar point: 18:22:12 UTC, about 10 NM after IFR waypoint MEKAR. — [ATSB, The Operational Search for MH370 (3 Oct 2017)](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf). Wikipedia adds an altitude of about 29,500 ft, 237 NM from Penang, and 247.3 NM north-west of Penang airport. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- Reported altitude across the peninsula was roughly 31,000–33,000 ft (secondary source; primary radar altitude is low-accuracy). — [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- Neighbouring states:
  - Indonesian military radar tracked MH370 towards IGARI before the transponder loss. Indonesian ATC did not register the aircraft's transponder code afterwards.
  - Thai military radar detected an aircraft that "might have been" MH370, without identifying data; the time of its last contact is not known.
  - Vietnam said it saw MH370 turning back west.
  - Source for all three: [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- After the initial search in the South China Sea and Strait of Malacca, Malaysia asked Australia on 17 March 2014 to take over search operations, because analysis showed the aircraft had turned south into Australia's search and rescue region. — [ATSB search overview](https://www.atsb.gov.au/mh370-search-overview)
- ATSB: no transmissions from automatic position systems (transponder, ACARS) were received after the first 38 minutes of flight. — [APO summary of the ATSB final report](https://apo.org.au/node/112656)

### Inferences
- The primary radar track (about 17:21–18:22 UTC) is the last positional fix. Everything after 18:22 UTC is inferred from satellite metadata, drift modelling and performance modelling.

### Gaps
- I could not open the raw Thai radar statement from 2014 or confirm its exact times; the Wikipedia wording is used.
- Primary radar data at full resolution have not been officially published. A 2024 claim that Geoscience Australia released the data is discussed on [mh370search.com (21 Apr 2024)](https://www.mh370search.com/2024/04/21/malaysian-military-radar/) but is not confirmed officially.

## 2. Inmarsat satellite data: handshakes, BTO arcs, BFO, the DSTG Bayesian analysis

### Takeaway
The aircraft's satellite data unit (SDU) logged back on to Inmarsat-3F1 at 18:25:27 UTC. It then answered hourly ground-initiated handshakes until 00:10:58 UTC. At 00:19:29 UTC the aircraft sent its own log-on request (the 7th arc), which is interpreted as an APU-powered restart after fuel exhaustion. The aircraft did not answer the next handshake, at 01:15:56 UTC.

- **BTO (burst timing offset)** gives the range from the satellite. Each BTO value defines a ring ("arc") of possible positions on the Earth.
- **BFO (burst frequency offset)** reflects Doppler shift. It is what showed a southern rather than northern route.
- DSTG combined the radar prior, BTO, BFO and aircraft dynamics in a Bayesian particle filter to produce a probability density along the southern 7th arc.

### Cited Findings
- Handshake times (UTC), from the ATSB final report:

| Event | Time (UTC) |
|---|---|
| Log-on (1st arc) | 18:25:27 |
| Handshake | 19:41:00 |
| Handshake | 20:41:02 |
| Handshake | 21:41:24 |
| Handshake | 22:41:19 |
| Handshake | 00:10:58 |
| Aircraft-initiated log-on (7th arc) | 00:19:29 |
| Failed handshake (no response) | 01:15:56 |

  Source: [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf)
- 7th handshake detail: log-on request at 00:19:29.416 UTC and log-on acknowledge at 00:19:37.443 UTC, the last transmission received. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370) (converted from MYT)
- Two ground-to-air telephone calls, at 18:39 UTC and 23:13 UTC, were acknowledged by the SDU but not answered. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- The ATSB interprets the 7th arc as the point of fuel exhaustion and descent. — [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf)
- Definitions:
  - BTO is the time difference between the ground station's transmission and the received response. It is proportional to twice the distance from the ground station, via the satellite, to the aircraft, and is used to define the range arcs.
  - BFO is the difference between expected and received frequency. It is caused by aircraft-to-satellite-to-ground Doppler, SDU oscillator drift and bias, and the aircraft's uplink Doppler compensation. It is used to infer speed and heading.
  - Source: [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- The ATSB's end-of-flight analysis used the BFOs of the final log-on. They imply descent rates of 2,900–15,200 ft/min, increasing to 13,800–25,300 ft/min eight seconds later. That is a high and increasing rate of descent. — [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf); restated in [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- The search-area definition combined flight-path modelling from "unique and sophisticated analysis of the metadata associated with the periodic automated satellite communications ... in the final six hours of the flight" with end-of-flight behaviour simulations. — [ATSB search overview](https://www.atsb.gov.au/mh370-search-overview)
- DSTG book: Davey, Gordon, Holland, Rutten and Williams, *Bayesian Methods in the Search for MH370*, SpringerBriefs in Electrical and Computer Engineering, Springer, published 25 July 2016, © Commonwealth of Australia 2016, open access. — [OAPEN Library](https://library.oapen.org/handle/20.500.12657/27976); [FreeComputerBooks listing](https://freecomputerbooks.com/Bayesian-Methods-in-the-Search-for-MH370.html). An earlier version (3 Dec 2015) is hosted by the ATSB. — [ATSB PDF](https://www.atsb.gov.au/sites/default/files/media/5733804/Bayesian_Methods_MH370_Search_3Dec2015.pdf)
- The book applies nonlinear/non-Gaussian Bayesian time-series estimation, using probabilistic models of aircraft flight dynamics, satellite communication system measurements, environmental effects and radar. — [Telkom University catalogue abstract](https://repositori.telkomuniversity.ac.id/home/catalog/id/245964/slug/bayesian-methods-in-the-search-for-mh370.html); [Amazon description](https://www.amazon.sg/Bayesian-Methods-Search-MH370-Gordon/dp/9811003785)
- The DSTG framework combined a radar-derived prior, Inmarsat BTO and BFO measurements, and a stochastic aircraft dynamics model. A March 2026 independent paper (Godfrey's blog) argues that its result is sensitive to the dynamics constraint: allowing a single LNAV direct-to waypoint command during the southbound phase widens the range of 7th-arc latitudes consistent with the arcs. — [mh370search.com, 15 Mar 2026](https://www.mh370search.com/2026/03/15/where-is-mh370/) (independent analysis, not official)

### Inferences
- In practice, the BTO arcs constrain range only, and the BFO constrains the general direction (south) and gives a weak speed/heading signal. The end-point latitude along the 7th arc therefore depends on assumptions about the autopilot mode, speed and any manoeuvres. This is why each successive search covered a different latitude band.

### Gaps
- The DSTG PDF fetch timed out. I could not verify the specific numbers in the DSTG analysis (BTO/BFO noise standard deviations; the 90% probability latitude band, about 39.4°S to 33.5°S with a peak near 38°S as I recall). Treat these as unverified.
- I did not fetch Ashton et al., "The Search for MH370", *Journal of Navigation* 68(1), 2015 (Inmarsat's description of the method). Cite it directly if needed.

## 3. ATSB search, 2014–2017, and the First Principles Review

### Takeaway
After a surface search (8 March to 28 April 2014) and an acoustic pinger search that found nothing, the ATSB led an underwater sonar search of about 120,000 km² along the 7th arc, between about 32.8°S and 39.5°S. It ran from October 2014 (bathymetry from May 2014) and was suspended on 17 January 2017. The search cost about A$198 million.

The First Principles Review (Canberra, 2–4 November 2016; report 20 December 2016) identified a further unsearched area of about 25,000 km² to the north. The final report (3 October 2017) said the most likely area was under 25,000 km².

### Cited Findings
- Surface search: several million km², 8 March to 28 April 2014, coordinated by AMSA with Australian Defence Force support. — [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf); [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- Acoustic search for the flight recorder beacons: Ocean Shield with a towed pinger locator (TPL) and the Bluefin-21 AUV, covering about 860 km² near the Zenith Plateau. No signals associated with MH370 were found. — [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf); [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- On 5 May 2014 the Malaysia–China–Australia tripartite agreed that Australia would lead the underwater search. — [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- Underwater search details:
  - Area about 120,000 km², with an indicative search area along the 7th arc from 32.8°S to 39.5°S.
  - Width typically 25 NM either side of the arc; earlier variants were −20/+30 NM and ±40 NM.
  - Water depths up to about 6,000 m.
  - Bathymetric survey of about 710,000 km².
  - Vessels: Fugro Discovery, Fugro Equator, Go Phoenix, Fugro Supporter, Dong Hai Jiu 101 and Havila Harmony.
  - Sensors: deep-tow side-scan sonar, AUV and synthetic aperture sonar.
  - Source: [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf)
- Geoscience Australia supported the search with bathymetry and sonar imagery. ROV images showed man-made objects (shipwrecks and similar) but nothing from MH370. — [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- On 17 January 2017 Malaysia, Australia and China jointly suspended the search "until further credible evidence" became available. — [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- First Principles Review:
  - Held in Canberra on 2–4 November 2016; report released 20 December 2016.
  - Participants were experts in data processing, satellite communications, accident investigation, aircraft performance, flight operations, sonar data, acoustic data and oceanography.
  - It identified a previously unsearched area of about 25,000 km² with the highest probability, north of the searched area (roughly 33°S–36°S along the arc).
  - Sources: [Wikipedia: Search for MH370 (FPR link)](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370); [ATSB FPR PDF](https://www.atsb.gov.au/media/5772107/ae2014054_final-first-principles-report.pdf); [ATSB operational search reports page](https://www.atsb.gov.au/mh370-operational-search-reports)
- Final report *The Operational Search for MH370*: published 3 October 2017, 440 pages. — [ATSB PDF](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf); [changingtimes.media, 3 Oct 2017](https://changingtimes.media/2017/10/03/australian-authorities-express-deep-regret-for-failure-to-find-mh370/)
  - "The understanding of where MH370 may be located is better now than it has ever been. This analysis complements the findings of the First Principles Review and identifies an area of less than 25,000 square kilometres which has the highest likelihood of containing MH370." — [APO](https://apo.org.au/node/112656)
  - "It is almost inconceivable and certainly societally unacceptable in the modern aviation era ... for a large commercial aircraft to be missing and for the world not to know with certainty what became of the aircraft and those on board." — [APO](https://apo.org.au/node/112656)
  - From the debris, "the aircraft was not configured for a ditching at the end-of-flight". The flaperon was probably retracted. — [APO](https://apo.org.au/node/112656); [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf)
  - Hydroacoustic data (Curtin University and the CTBTO HA01 station off Cape Leeuwin): the candidate events were inconsistent with MH370 or geological in origin (for example the Carlsberg Ridge) and added no useful information. — [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf)
  - Total search cost about A$198 million. — [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf). The Star/Bernama (29 Jun 2026) gives the overall cost as about US$200 million, with 82 aircraft and 84 ships from 26 countries. — [The Star](https://www.thestar.com.my/news/nation/2026/06/29/govt-extends-deal-with-ocean-infinity-to-search-for-mh370-wreckage)
- With the final report, the ATSB ceased any formal search role. — [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- A Geoscience Australia data review in 2022 is listed by the ATSB. — [ATSB MH370 data review](https://www.atsb.gov.au/mh370-data-review)

### Inferences
- The hydroacoustic finding matters for any acoustic-tracking feasibility study: official analysis found the CTBTO and Curtin hydrophone data did not usefully localise an impact.

### Gaps
- I did not verify the exact latitude bounds of the First Principles Review area from the FPR PDF itself. The figure of about 33°S–36°S is commonly reported but should be checked against the PDF.
- The ATSB query tool answered inconsistently on the FPR latitudes.

## 4. Ocean Infinity searches: 2018 (Seabed Constructor) and 2025–2026 ("no find, no fee"), and status at November 2026

### Takeaway
- **2018:** Ocean Infinity searched immediately north of the ATSB area from about 22 January to 29 May 2018 and covered more than 112,000 km² without success.
- **2024–2025 deal:** Malaysia agreed in principle on 20 December 2024 and signed a contract on 25 March 2025. The terms were a 15,000 km² new area, US$70 million paid only if the wreck is found, and an 18-month term (contract to about June 2026).
- **2025–2026 operations:** Phase 1 ran 25–28 March 2025, and Malaysia announced a suspension on 3 April 2025 because of the season. Phase 2 ran 31 December 2025 to 23 January 2026 with the Armada 86 05. Over 28 operational days about 7,571 km² was surveyed, with nothing found.
- **Extension:** On 29 June 2026 Malaysia extended the contract to 30 June 2027 to finish the remaining 7,428.54 km². Operations are possible only in the calm season, November 2026 to April 2027.
- **As of 5 November 2026:** I found no confirmed report that search operations have resumed.

### Cited Findings
- **2018:** On 16 January 2018 Malaysia announced a second search by Ocean Infinity, "no find, no fee", "located immediately north of the previous search area". On 29 May 2018 Malaysia said it had ended. The total seafloor searched by then was more than 1,800 km long, 86–146 km wide, and close to 200,000 km² in total, without finding the aircraft. — [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- Ocean Infinity searched more than 112,000 km² in 2018 and stopped in May 2018. — [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/); [Wikipedia: Search for MH370](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370)
- Cumulative latitude coverage (Godfrey, March 2026): the ATSB searched about 120,000 km² from 40°S to about 33°S, and Ocean Infinity about 140,000 km² from 36°S to 25°S. — [mh370search.com, 15 Mar 2026](https://www.mh370search.com/2026/03/15/where-is-mh370/)
- Run-up to the new search:
  - March 2022: Ocean Infinity committed to resuming in 2023/24, pending approval, with new robotic ships.
  - 8 March 2023: Transport Minister Anthony Loke said Malaysia would not "close the book" and would consider "new and credible information".
  - Source: [Wikipedia: Search for MH370](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370)
  - 2 May 2024: Ocean Infinity presented a new proposal to Loke. — [mh370search.com, 5 May 2024](https://www.mh370search.com/2024/05/05/new-search/)
- 20 December 2024: the Malaysian government agreed "in principle" to a new Ocean Infinity search. — [Wikipedia: Search for MH370](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370)
- 25 February 2025: Loke announced the start of the new search, covering 15,000 km² over 18 months, "no find, no fee", with US$70 million payable on discovery. — [Wikipedia: Search for MH370](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370)
- 19 March 2025: Malaysia said it had agreed Ocean Infinity's terms (15,000 km², US$70 million only if found). — [Reuters, 29 Jun 2026, citing the 19 Mar 2025 deal](https://www.reuters.com/world/china/malaysia-extends-search-missing-flight-mh370-by-one-year-2026-06-29/)
- 25 March 2025: the contract was signed. The Ministry of Transport's official update says Ocean Infinity also carried out "additional survey activities ... within the broader search area before the formal signing". — [MOT / AAIB "Update to Families", 8 Mar 2026](https://www.mot.gov.my/en/Kenyataan%20Media/Year%202026/MH370%20Search%20Operation%202025-2026%20-%20Update%20to%20Families.pdf)
- 3 April 2025: Loke said Ocean Infinity had suspended the search because it was "not the season". — [Reuters, 3 Apr 2025](https://www.reuters.com/world/asia-pacific/search-missing-flight-mh370-suspended-due-bad-weather-says-malaysia-transport-2025-04-03/); [Wikipedia](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370)
- 3 December 2025: Malaysia announced the search would resume on 30 December 2025 with an intermittent 55-day seabed search in a targeted area. — [Reuters, 3 Dec 2025](https://www.reuters.com/world/asia-pacific/search-missing-flight-mh370-resume-december-30-malaysia-says-2025-12-03/); [DW](https://www.dw.com/en/mh370-search-for-missing-flight-to-resume-in-december/a-74992914); [SCMP](https://www.scmp.com/news/asia/southeast-asia/article/3334999/malaysia-resumes-search-mh370-ocean-infinity-indian-ocean-after-over-decade)
- Phase 2 used the vessel Armada 86 05 with AUVs. — [Wikipedia: Search for MH370](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370); [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- **Official phase dates and results.** Phase 1 ran 25–28 March 2025 and Phase 2 ran 31 December 2025 to 23 January 2026. Together that was 28 operational search days and about 7,571 km² of seabed surveyed within the defined area. Weather and sea conditions periodically disrupted work. The update states that "the search activities undertaken have not yielded any findings that confirm the location of the aircraft wreckage." It was issued by the Air Accident Investigation Bureau, Ministry of Transport, on 8 March 2026. — [MOT update to families (PDF)](https://www.mot.gov.my/en/Kenyataan%20Media/Year%202026/MH370%20Search%20Operation%202025-2026%20-%20Update%20to%20Families.pdf); [AP via PBS, 8 Mar 2026](https://www.pbs.org/newshour/world/renewed-search-for-missing-flight-mh370-comes-up-empty-12-years-later-as-families-press-for-answers)
- **Ocean Infinity statement, 8 March 2026.** The vessel "departed the search area" on 23 January 2026. Since 2018 the company has spent 151 days at sea and mapped more than 140,000 km² of seafloor. CEO Oliver Plunkett: "If nothing else, we can say with confidence that it isn't where we looked ... Although this phase of the search has concluded, our commitment has not. We're continuing to work with the Malaysian Government in the hope of being able to return when circumstances allow." — [Ocean Infinity, 8 Mar 2026](https://oceaninfinity.com/news/conclusion-of-the-search-for-malaysian-airlines-flight-mh370/)
- **Extension, 29 June 2026.** The Cabinet (meeting on Friday 26 June 2026) extended the Ocean Infinity agreement for 12 months, from 1 July 2026 to 30 June 2027. Terms are unchanged ("no find, no fee"; US$70 million only if found). The aim is to complete the remaining 7,428.54 km².
  - The extension takes account of Ocean Infinity's new commercial contracts, which require key assets to be reassigned temporarily.
  - Rescheduled deployment is possible only "from this November until April 2027", the calm-sea season.
  - Sources: [The Star/Bernama, 29 Jun 2026](https://www.thestar.com.my/news/nation/2026/06/29/govt-extends-deal-with-ocean-infinity-to-search-for-mh370-wreckage); [Reuters, 29 Jun 2026](https://www.reuters.com/world/china/malaysia-extends-search-missing-flight-mh370-by-one-year-2026-06-29/); [FMT, 29 Jun 2026](https://www.freemalaysiatoday.com/category/nation/2026/06/29/mh370-search-deal-with-ocean-infinity-extended-for-another-year); [FlightGlobal, Jun 2026](https://www.flightglobal.com/archive/2026/06/mh370-wreckage-search-pact-enables-team-to-complete-exploration-of-focus-area/)
- Consistency check: 7,571 km² surveyed plus 7,428.54 km² remaining is about 15,000 km², which matches the contracted area (my calculation from the [MOT](https://www.mot.gov.my/en/Kenyataan%20Media/Year%202026/MH370%20Search%20Operation%202025-2026%20-%20Update%20to%20Families.pdf) and [The Star](https://www.thestar.com.my/news/nation/2026/06/29/govt-extends-deal-with-ocean-infinity-to-search-for-mh370-wreckage) figures).
- At 26 August 2026 a secondary source said work was "not expected to resume before November" and that "roughly half the priority zone has been swept". — [MiGFlug, 26 Aug 2026](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- A YouTube short dated 3 November 2026 is framed as "will [Armada 86 05] travel to the southern Indian Ocean" as the seasonal window opens. That implies no confirmed resumption at that date. — [YouTube, 3 Nov 2026](https://www.youtube.com/shorts/u6TDnKib2KM) (low-reliability source, used only as an indicator)
- Popular Mechanics noted that the original contract ran to June 2026. — [Popular Mechanics](https://www.popularmechanics.com/flight/airlines/a74313890/mh370-search-ocean-robots/)

### Inferences
- **Status at 5 November 2026:**
  - No wreckage has been found by any search (ATSB 2014–17, Ocean Infinity 2018, Ocean Infinity 2025–26).
  - A contract is in force to 30 June 2027, with about 7,429 km² of the 15,000 km² priority area left to survey.
  - The weather window for resumption (November 2026 to April 2027) has just opened.
  - I found no official announcement (MOT or Ocean Infinity) of a specific restart date or of a vessel departing, as of 5 November 2026.
- About 7,571 km² in roughly 28 days is about 270 km² per operational day. If that rate held, the remaining area would take roughly 27–28 operational days. This is my rough estimate only, not an official figure.

### Gaps
- No official coordinates or latitude bounds of the 2025–26 15,000 km² area were found. Press reports describe it only as a "new area" or "targeted area" in the southern Indian Ocean. Its basis (for example, new drift and BFO reanalysis by Ocean Infinity's experts; the WSPR hypothesis was publicly debated) was not confirmed from official sources.
- I could not find any news dated September to 5 November 2026 confirming a restart date. Recommend a re-check close to the report date.

## 5. Malaysian Safety Investigation Report (July 2018): key conclusions

### Takeaway
The ICAO Annex 13 report (MH370 Safety Investigation Team, released 30 July 2018; about 495 pages plus about 1,500 pages of appendices) found that the turn-back was made manually and that the communication systems' loss was consistent with manual action. It found no evidence of mechanical failure that would explain the flight path, but could not determine the cause: "the Team is unable to determine the real cause for the disappearance of MH370". It did not exclude unlawful interference by a third party.

### Cited Findings
- Release date 30 July 2018; nearly 500 pages plus about 1,500 pages of appendices. The turn-back was manual. "In conclusion, the Team is unable to determine the real cause for the disappearance of MH370." It found no evidence the aircraft was flown by anyone other than the designated crew, but did not exclude third-party intervention. — [MiGFlug, quoting Section 3.2](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/); [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- The aircraft was manually taken off its assigned path just after 01:00 MYT, "either by the pilot or a third party". It went undetected by ATC radar for about 20 minutes before anyone was alerted. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- The ATSB summary gives the date as 31 July 2018 (probably a time-zone or date-convention difference). It says the report "was unable to draw definitive conclusions" because the main wreckage and recorders had not been found. — [ATSB overview](https://www.atsb.gov.au/mh370-search-overview). Official report PDF: [MOT](https://www.mot.gov.my/en/MH370%20Investigation%20Report/01-Report/MH370SafetyInvestigationReport.pdf)
- Captain Zaharie's home simulator held seven manually entered waypoints, in a file dated 3 February 2014, forming a path into the southern Indian Ocean. The ATSB said the simulated track was not consistent with the satellite-modelled tracks. The Malaysian report found no unusual activities beyond game-related simulation, and no psychological or behavioural red flags in the crew. — [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/) (secondary summary)
- The cargo included 221 kg of lithium-ion batteries. No fire damage was found on any debris, but fire or failure could not be fully eliminated. — [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/) (secondary summary)

### Inferences
- The official cause is undetermined. The location inference does not depend on the cause, but it does depend on assumptions about piloted versus autopilot flight after 18:22 UTC, which the report does not resolve.

### Gaps
- I did not fetch the 2018 Safety Investigation Report PDF directly. Its quotations are taken from secondary sources quoting Section 3.2.

## 6. Debris finds and drift modelling (CSIRO, GEOMAR)

### Takeaway
More than 20 items, mostly found on western Indian Ocean shores, have been attributed to MH370. The ATSB rated 18 as "very likely" or "almost certain" and 2 as "probably" from 9M-MRO; independent counts list about 43 found. The Réunion flaperon (29 July 2015) was confirmed by serial number. CSIRO drift modelling (2016–2017) favoured a location near 35.6°S 92.8°E, at the northern end of or north of the ATSB area. This supported the First Principles Review area. The debris confirms the southern Indian Ocean but does not give a precise position.

### Cited Findings
- **Right flaperon:** found 29 July 2015 at Saint-André, Réunion. Confirmed "with certainty" via internal serial numbers on 3 September 2015 (French investigators). — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370); [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- **Flap track fairing (stencil "676EB"):** found December 2015 in southern Mozambique; "almost certain" (March 2016). — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- **Horizontal stabiliser panel ("NO STEP"):** found February 2016, Bazaruto Archipelago / Vilanculos, Mozambique; "almost certain". — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- **Rolls-Royce engine cowling fragment:** found 21 March 2016 near Mossel Bay, South Africa. **Interior panel:** found late March 2016 on Rodrigues Island, Mauritius. Both were assessed "almost certainly" from MH370 on 11 May 2016. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- **Right outboard flap section:** found on Pemba Island, Tanzania (handed over June 2016); confirmed by Malaysia's Ministry of Transport on 15 September 2016. It was examined at the ATSB in Canberra. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370); [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- **Madagascar:** five pieces recovered between December 2016 and August 2018 were handed to Loke on 30 November 2018. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370)
- **ATSB classification:** 18 items very likely or almost certain, 2 probably. — [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf); [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- **Independent count:** 43 pieces of floating debris found, 41 delivered to the Malaysian authorities (Godfrey, December 2023; non-official). — [mh370search.com, 7 Dec 2023](https://www.mh370search.com/2023/12/07/new-clues/)
- **CSIRO drift study** (published 16 August 2017): it identified the crash area "with unprecedented precision and certainty" at 35°36′S 92°48′E, north-east of the 120,000 km² zone. The study drew on drift modelling plus analysis of Pléiades satellite imagery from 23 March 2014 showing possible man-made objects. — [Wikipedia: MH370](https://en.wikipedia.org/wiki/Malaysia_Airlines_Flight_370); [ATSB final report](https://www.atsb.gov.au/sites/default/files/media/5773565/operational-search-for-mh370_final_3oct2017.pdf); CSIRO reports index: [ATSB CSIRO drift reports](https://www.atsb.gov.au/csiro-mh370-drift-reports); imagery: [Geoscience Australia Pléiades analysis](https://www.atsb.gov.au/summary-imagery-analyses-non-natural-objects-support-search-flight-mh370)
- The ATSB said the debris "yielded significant new insights into how and where the aircraft ended its flight". — [ATSB overview](https://www.atsb.gov.au/mh370-search-overview)
- A secondary source characterises the drift patterns as "consistent with an origin in the southern Indian Ocean ... corroboration of the arc, not a position". — [MiGFlug](https://migflug.com/afterburner/mh370-what-is-known-2026-ocean-infinity-search/)
- Other drift analysis: a University of Western Australia (UWA) drift analysis produced a crash-location area. — referenced in [mh370search.com, 22 Dec 2023](https://www.mh370search.com/2023/12/22/mh370-search-area/)

### Inferences
- The 35.6°S 92.8°E drift-favoured point lies within the band (36°S–25°S) that Ocean Infinity says it has largely covered (more than 140,000 km² cumulative). So the drift result, while not ruled out (seafloor coverage is never 100%), has been substantially tested. The Ocean Infinity CEO's remark "it isn't where we looked" applies to it.

### Gaps
- I did not retrieve the GEOMAR (Kiel) drift study directly. It reportedly favoured a broader area along the arc (around 28°S–35°S); this is unverified.
- I did not verify a full official debris table (the Malaysian MOT debris examination reports).

## 7. Reactions of the Malaysian government and families (Voice370); anniversary developments

### Takeaway
Malaysia's line since 2023 has been "not closing the book" and acting on "credible" new evidence, implemented through no-cost-unless-found contracts. Voice370 has consistently pressed for searches to continue. At the 12th anniversary (8 March 2026) the families urged Malaysia to extend Ocean Infinity's contract and to offer similar terms to other firms. Malaysia extended the contract on 29 June 2026.

### Cited Findings
- 8 March 2023 (9th anniversary): Loke vowed not to "close the book", with consideration for "new and credible information". — [Wikipedia: Search for MH370](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370)
- 2024 (10th anniversary period): Ocean Infinity met Loke on 2 May 2024 to propose a new search. — [mh370search.com](https://www.mh370search.com/2024/05/05/new-search/). The government agreed in principle on 20 December 2024. — [Wikipedia](https://en.wikipedia.org/wiki/Search_for_Malaysia_Airlines_Flight_370)
- 8 March 2026 (12th anniversary): the AAIB published its update to families. Voice370 urged the government to extend Ocean Infinity's contract and to "consider extending similar no find, no fee opportunities to other capable deep sea exploration companies". It noted that the vessel had been redeployed for other work and was unlikely to return soon with winter approaching. Quote: "The government pays nothing unless the aircraft is found ... We will never give up!" — [AP via PBS, 8 Mar 2026](https://www.pbs.org/newshour/world/renewed-search-for-missing-flight-mh370-comes-up-empty-12-years-later-as-families-press-for-answers); [Reuters, 8 Mar 2026](https://www.reuters.com/world/china/families-flight-mh370-passengers-urge-malaysia-extend-search-2026-03-08/); [Voice370 press release, 8 Mar 2026 (Facebook)](https://www.facebook.com/MH370Families/posts/voice370-press-release-dated-8th-march-2026mh370-12-years-on/1345192684315615/)
- 29 June 2026: Loke called the extension "a manifestation of the government's unwavering and continuous commitment to providing the long-awaited closure for the families". — [The Star/Bernama](https://www.thestar.com.my/news/nation/2026/06/29/govt-extends-deal-with-ocean-infinity-to-search-for-mh370-wreckage)
- 8 March 2026: Ocean Infinity thanked "the families, the Malaysian Government, the Australian Government". — [Ocean Infinity](https://oceaninfinity.com/news/conclusion-of-the-search-for-malaysian-airlines-flight-mh370/)

### Inferences
- The government's position has moved from "awaiting credible new evidence" (2017–2023) to contracting a time-limited, performance-based search, which is low fiscal risk to Malaysia. The pressure from families appears to have shaped the June 2026 extension.

### Gaps
- I did not read the full Voice370 press release (Facebook). Specific Chinese next-of-kin reactions and the status of the compensation lawsuits in Beijing were not researched.
- I found no official MOT statement between July and November 2026 beyond the 29 June 2026 extension.
