# The specific aircraft-Doppler audio geolocation project circulating in OSINT circles (Nov 2026): who, what, where, reception

Research date: 2026-11-05. Everything below happened within the 72 hours before this date, so coverage is thin, secondary sources are often AI-written or aggregator content, and repo statistics are snapshots that will change.

## Q1. What is the project, who made it, when and where was it published?

### Takeaway
The original is a YouTube video by the OSINT creator **colsto**, "I discovered a sound that leaks your exact location (and it's everywhere)" (https://www.youtube.com/watch?v=UytYrhYLOKI). It was uploaded on or about **2 November 2026**. colsto released **no code, tools or audio**. Within 1 to 3 days, a cluster of independent open-source reimplementations appeared on GitHub and PyPI. No single "official" tool exists. The thing "circulating" is the video plus a group of community clones.

### Cited Findings
**Original video (primary)**
- Title: "I discovered a sound that leaks your exact location (and it's everywhere)". Creator: colsto. URL: https://www.youtube.com/watch?v=UytYrhYLOKI. Archive mirror: https://archive.org/details/youtube-UytYrhYLOKI — [ThakiCloud blog](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- Upload date: 2 Nov 2026 — [Digg AI summary](https://digg.com/ai/7wr4rmyp); [franken_doppler_finder README](https://github.com/Dicklesworthstone/franken_doppler_finder) ("dated 2026-11-02"). The earliest Hacker News submission was 2026-11-02T22:21Z ([HN 50344762](https://news.ycombinator.com/item?id=50344762)). The earliest Lobsters submission was 2026-11-02 13:42 ([Lobsters](https://lobste.rs/s/s1btqo/this_background_sound_leaks_your_exact)).
- An alternate title on Lobsters was "This background sound leaks your exact location", which suggests the title was changed or A/B-tested. The dopplerprint PyPI page also cites the video under that title — [Lobsters](https://lobste.rs/s/s1btqo/this_background_sound_leaks_your_exact); [PyPI dopplerprint](https://pypi.org/project/dopplerprint/)
- The video description reportedly says no code or tools are being released. It also claims the project took months and more than 5,000 lines of code — [Digg](https://digg.com/ai/7wr4rmyp); [lilithai.dev](https://lilithai.dev/radar/i-discovered-a-sound-that-leaks-your-exact-location-and-it-s-everywhere?lang=en). A secondary summary adds about 50 GB of data — [lilithai.dev](https://lilithai.dev/radar/i-discovered-a-sound-that-leaks-your-exact-location-and-it-s-everywhere?lang=en); [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect)
- I could not fetch the YouTube page itself (no description or view count retrieved). The video's content is known only through secondary write-ups and the README notes of reimplementers.

**Open-source reimplementations (all credit colsto; none affiliated with him)**
| Project | Author / handle | Where | Language | Notes |
|---|---|---|---|---|
| dopplertrack | mjshiggins | https://github.com/mjshiggins/dopplertrack | Python | Most-starred (147 stars, 21 forks at snapshot). Linked in HN thread — [repo](https://github.com/mjshiggins/dopplertrack) |
| doppler-locate (`dopploc`) | digitalis-p | https://github.com/digitalis-p/doppler-locate | Python + CUDA/OpenMP, GTK4 app | 14 stars — [repo](https://github.com/digitalis-p/doppler-locate) |
| dopplerprint 0.1.0 | Henry Alexander (PyPI: hexay123; GitHub: Hexay) | https://pypi.org/project/dopplerprint/ ; https://github.com/Hexay/dopplerprint | Python | Released on PyPI 3 Nov 2026 — [PyPI](https://pypi.org/project/dopplerprint/) |
| DOPPLERGEIST | 1337isnot1337 ("DOPPLERGEIST contributors") | https://github.com/1337isnot1337/DOPPLERGEIST | — | Covered by VGTimes 3 Nov 2026 — [VGTimes](https://vgtimes.com/tech-and-hardware/173330-dopplergeist-uses-aircraft-sounds-to-estimate-where-a-recording-was-made.html) |
| franken_doppler_finder (`fdop`) | Dicklesworthstone | https://github.com/Dicklesworthstone/franken_doppler_finder | Rust (nightly) | Reimplements the dopplerprint method. 31 stars, 99 commits. Dev runs dated 3 to 4 Nov — [repo](https://github.com/Dicklesworthstone/franken_doppler_finder) |
| doppler-geo | teamchong | https://github.com/teamchong/doppler-geo ; live demo https://doppler.teamchong.net | JS + Rust WASM, in-browser | 0 stars — [repo](https://github.com/teamchong/doppler-geo) |
| DopplerGPS | Dyne Research | https://github.com/dyneresearch/DopplerGPS | Python | Framed as an "academic research artifact". 1 star. Synthetic results only — [repo](https://github.com/dyneresearch/DopplerGPS) |
| flyover-locator / dopplergeo | amintt2 | https://github.com/amintt2/flyover-locator | — | French-language. Not inspected in detail — [search listing](https://github.com/amintt2/flyover-locator) |
| hermes-aircraft-doppler-geolocation | mojomast | https://github.com/mojomast/hermes-aircraft-doppler-geolocation | — | A "Hermes plugin". Not inspected — [repo](https://github.com/mojomast/hermes-aircraft-doppler-geolocation) |
| colsto-leak-and-mask | Bodila51 | (GitHub; URL not retrieved) | — | Replication of the challenge plus a Claude Code skill to detect and mask flyovers — [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect) |
| doppler-experiments | Cbonitz | (GitHub; URL not retrieved) | — | A coding agent rebuilt the method in about 27 min for about $10 and tested it on synthetic worlds — [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect) |

- Paras Chopra (X) reportedly replicated the pipeline "in a few hours using Claude Code" and field-tested it on a live webcam about 7 km south of Southampton, UK. The heatmap reportedly peaked at the webcam's position (https://x.com/paraschopra/status/2117561731065274562) — reported only by [ThakiCloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/). I could not verify this independently, and Digg's aggregation does not mention it ([Digg](https://digg.com/ai/7wr4rmyp)).

### Inferences
- The "project circulating on OSINT forums" is best described as **colsto's closed-source demonstration video** plus a **swarm of AI-assisted open-source clones** built in 24 to 72 hours. Several clones were explicitly built with coding agents (Cbonitz, Paras Chopra, Bodila51's Claude Code skill).
- dopplertrack (mjshiggins) appears to be the most-cited and most-starred community implementation. dopplerprint and DOPPLERGEIST are the ones other projects benchmark against.

### Gaps
- I did not retrieve colsto's real identity, other channel details, view counts, or the full video description. The YouTube page could not be fetched.
- I did not get the GitHub URLs for Bodila51's and Cbonitz's repos, or repo creation dates for any repo.

## Q2. What exactly does the technique/tool claim (inputs, data sources, outputs, accuracy)?

### Takeaway
The audio must contain **propeller-aircraft** blade-pass tones (jets generally excluded). Each flyover produces a Doppler "sweep" in the spectrogram. Fitting it gives the aircraft's speed, closest-approach distance and closest-approach time. These are matched against **historical ADS-B tracks** (mostly **adsb.lol** archives), with terrain, sound-travel delay and weather corrections. At least **two flyovers** are needed for a fix. colsto's claim is roughly **100 m** (some write-ups say "a few hundred feet") on a continental-US search with a known date. Clones report 32 to 627 m on real recordings and many failures.

### Cited Findings
**colsto's method and claims (via secondary sources)**
- Test footage: a nearly static security-camera recording of trees and a river, dated 8 Sep 2026, believed to be in the continental US. The hour was unknown — [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect); [lilithai.dev](https://lilithai.dev/radar/i-discovered-a-sound-that-leaks-your-exact-location-and-it-s-everywhere?lang=en)
- Two faint propeller-aircraft Doppler curves, 920 s apart, were extracted from the spectrogram. The search covered the whole continental US on a 200 m grid, modelled sound arrival time, used silence between events as a filter, then scored modelled Doppler curves against the spectrogram. A Street View check reportedly showed a tree line and a camera on a pole at a riverbank — [lilithai.dev](https://lilithai.dev/radar/i-discovered-a-sound-that-leaks-your-exact-location-and-it-s-everywhere?lang=en); [Digg](https://digg.com/ai/7wr4rmyp)
- Location: Oyster Bay, NY (Long Island), per reimplementers — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [dopplertrack](https://github.com/mjshiggins/dopplertrack)
- Accuracy: about 100 m per the video description ([Digg](https://digg.com/ai/7wr4rmyp)), or "a few hundred feet" ([lilithai.dev](https://lilithai.dev/radar/i-discovered-a-sound-that-leaks-your-exact-location-and-it-s-everywhere?lang=en)). The 200 m figure is the grid step, not the precision ([Digg](https://digg.com/ai/7wr4rmyp)).
- A second test reportedly used one minute of nearly inaudible aircraft trace with a known recording time and ranked the true location first in a US-wide search — [Digg](https://digg.com/ai/7wr4rmyp); [lilithai.dev](https://lilithai.dev/radar/i-discovered-a-sound-that-leaks-your-exact-location-and-it-s-everywhere?lang=en)
- TechRadar's headline: "geolocate your videos to within 100m — 'Doppler effect' pinpoints locations from just 60 seconds of audio" — [TechRadar](https://www.techradar.com/computing/cyber-security/youtuber-discovers-aircraft-noise-trick-that-can-geolocate-your-videos-to-within-100m-doppler-effect-pinpoints-locations-from-just-60-seconds-of-audio). Only the headline was retrievable.
- Data source used by colsto: **conflicting reports**. doppler-locate's README says "the video used Flightradar24 and a 30 m DEM" ([doppler-locate](https://github.com/digitalis-p/doppler-locate)). A blog says the video names OpenSky and adsb.lol as archive sources and does not mention Flightradar24 ([pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect)).
- colsto published the hour of raw audio as a public challenge, per one source — [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect). doppler-locate says it processed the "video challenge recording" ([repo](https://github.com/digitalis-p/doppler-locate)). ThakiCloud says the field recording plays in the last about 3 minutes (26:51–29:07) of the 29 min video ([ThakiCloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)).

**Common data sources across clones**
- adsb.lol daily globe_history archives (ODbL, about 3.5–4 GB/day) are used by dopplertrack, doppler-locate, dopplerprint, fdop and doppler-geo — [dopplertrack](https://github.com/mjshiggins/dopplertrack); [doppler-locate](https://github.com/digitalis-p/doppler-locate); [PyPI dopplerprint](https://pypi.org/project/dopplerprint/); [fdop](https://github.com/Dicklesworthstone/franken_doppler_finder); [doppler-geo](https://github.com/teamchong/doppler-geo)
- Aircraft type tables are used to separate propeller aircraft from jets: tar1090-db, or the OpenSky mirror of ICAO Doc 8643 — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [dopplertrack](https://github.com/mjshiggins/dopplertrack)
- Terrain: Copernicus GLO-90/GLO-30, AWS Terrain Tiles, USGS 3DEP. Weather: NOAA GFS 0.25°, Open-Meteo, IEM radiosondes and ASOS — [doppler-locate](https://github.com/digitalis-p/doppler-locate); [fdop](https://github.com/Dicklesworthstone/franken_doppler_finder)
- DopplerGPS defines Parquet schemas for OpenSky, ADS-B Exchange and FlightAware — [DopplerGPS](https://github.com/dyneresearch/DopplerGPS)
- Inputs: an audio or video file or URL (yt-dlp/ffmpeg), the recording date, a time window, and usually a rough region. Outputs: ranked flight pairs, heatmaps, GeoJSON/GeoPackage/HTML maps, lat/lon plus radius, and confidence verdicts ("located/ambiguous/no match", "high/medium/low") — [dopplertrack](https://github.com/mjshiggins/dopplertrack); [fdop](https://github.com/Dicklesworthstone/franken_doppler_finder); [PyPI dopplerprint](https://pypi.org/project/dopplerprint/)

**Reported accuracy of clones (self-reported, unreviewed)**
- dopplertrack:
  - Oyster Bay (1 h): true pair ranked 1st, 32 m from truth, p = 0.001.
  - North Fort Myers eagle-cam (12 h): 627 m, "ambiguous" with two events, "located" with extra flyovers.
  - Atlanta rail-cam: failed.
  - In the Atlanta test, 2 of 20 searches with no correct answer still reached "located".
  - [repo](https://github.com/mjshiggins/dopplertrack)
- doppler-locate:
  - Video challenge: ranked 1st of 1,060 flight pairs, 67 m.
  - Synthetic: 52 m.
  - Single-event mode not reproduced.
  - Detector confidence rule was tuned on the same recording, so results are optimistic.
  - Benchmark hardware: RTX 4090 and 62 GB RAM. Including jets needs 34 GB memory.
  - [repo](https://github.com/digitalis-p/doppler-locate)
- dopplerprint:
  - Livermore, CA, 40 single-flyover recordings (Zenodo 23424278): correct aircraft in 34/40, median error 207 m, 27 of 40 within 500 m. Start time was known to ±2 s and the search radius was 4 km.
  - Oyster Bay: 79 m (DOPPLERGEIST: 52 m).
  - Flyover position in the recording is hand-supplied.
  - [PyPI](https://pypi.org/project/dopplerprint/)
- DOPPLERGEIST: two real recordings at 43.86 m and 357.47 m against non-surveyed reference coordinates. The developers say nationwide accuracy is not established — [VGTimes](https://vgtimes.com/tech-and-hardware/173330-dopplergeist-uses-aircraft-sounds-to-estimate-where-a-recording-was-made.html)
- fdop:
  - Author's own reference recording: about 260–270 m, radius about 400 m.
  - Osprey cam: 223 m.
  - Several live-cams gave no location. An Ithaca recording was placed 338 km off.
  - Low-traffic or rural sites all failed.
  - A 3 h recording searched over a state took about 2 h 40 min.
  - [repo](https://github.com/Dicklesworthstone/franken_doppler_finder)
- doppler-geo: two-plane Cranfield, UK example "within 40 meters" from 1,147 prop flights worldwide. A single plane gives only a shortlist — [repo](https://github.com/teamchong/doppler-geo)
- DopplerGPS: 25.6 m on synthetic data only — [repo](https://github.com/dyneresearch/DopplerGPS)
- Bodila51:
  - Challenge with hand-measured flyovers: 925 m from Oyster Bay centre.
  - Automatic detection: missed by 137 km; the true pair ranked 5th of 517. The search area was chosen knowing the answer.
  - Cbonitz agent rebuild: 6/6 synthetic worlds correct with two flyovers (85–830 m); 0/6 with one aircraft.
  - [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect)

**Stated limitations (common across repos)**
- Only propeller, turboprop and helicopter traffic works; jets are excluded. At least two flyovers are needed. Coverage is CONUS-only or untested elsewhere. Rural, low-traffic or no-ADS-B areas fail. City, indoor and night recordings usually catch nothing. A timestamp or time window is required. YouTube compression degrades the signal — [doppler-geo](https://github.com/teamchong/doppler-geo); [fdop](https://github.com/Dicklesworthstone/franken_doppler_finder); [DopplerGPS](https://github.com/dyneresearch/DopplerGPS); [ThakiCloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
- Two high, nearly overhead passes leave a plateau several km wide; one low or side pass is needed — [dopplertrack](https://github.com/mjshiggins/dopplertrack)

### Inferences
- Claims of "100 m from 60 s of any video" in headlines overstate the case. Real-world performance depends on prior knowledge of date, time and region and on at least two clean prop flyovers. Independent clones achieve tens to hundreds of metres in favourable US cases and frequently fail otherwise.
- The Oyster Bay recording has become the de-facto benchmark, but its "ground truth" is an approximate public coordinate, not a surveyed point ([PyPI dopplerprint](https://pypi.org/project/dopplerprint/)).

### Gaps
- No peer-reviewed paper or arXiv preprint was found for colsto's method or any clone.
- I could not confirm colsto's exact ADS-B source (Flightradar24 vs adsb.lol/OpenSky; sources conflict).

## Q3. Demos, case studies, challenges

### Takeaway
The canonical case is colsto's 8 Sep 2026 riverbank security-camera recording near Oyster Bay, Long Island, NY, released as a challenge. Community tests extend to webcams and live-cams (Lorain OH, North Fort Myers FL eagle cam, Atlanta rail cam, Ithaca bird feeder, osprey cam, Moosehead Lake, Livermore CA Zenodo set, Cranfield UK, Kampina NL, Southampton UK webcam).

### Cited Findings
- Lorain webcam (15 Jun 2026): 1 of 4 detections matched ADS-B. Moosehead Lake (12 Sep 2026): no ADS-B coverage to confirm. The HWNDU archive has only short clips — [doppler-locate](https://github.com/digitalis-p/doppler-locate)
- North Fort Myers FL (2024-12-28 eagle cam) and Atlanta rail cam — [dopplertrack](https://github.com/mjshiggins/dopplertrack)
- Ithaca bird-feeder placed 338 km off (Long Island); osprey cam at 223 m — [fdop](https://github.com/Dicklesworthstone/franken_doppler_finder)
- Cranfield UK (two planes, within 40 m) and Kampina NL (one plane, PH-TRG shortlisted), using a Freesound/klankbeeld field recording — [doppler-geo](https://github.com/teamchong/doppler-geo)
- Livermore CA 40-recording dataset by Praveen Pathak (Zenodo 23424278, CC BY 4.0) — [PyPI dopplerprint](https://pypi.org/project/dopplerprint/)
- ThakiCloud ran the doppler-locate detector on the 29 min 12 s video audio: 36 s on MacBook CPU, 5 aircraft events (3 high/medium), 6 road vehicles separated. It did not run the ADS-B matching stage, so it made no location claim — [ThakiCloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)

### Inferences
- doppler-locate's mention of an "HWNDU archive" suggests reimplementers see the 2017 "He Will Not Divide Us" flag geolocation (where aircraft were used as clues) as a spiritual precursor. I did not verify the details of that 2017 episode in this research.

### Gaps
- No Bellingcat, GeoGuessr or other organised OSINT challenge built around this technique was found beyond colsto's own challenge recording.

## Q4. Community reaction

### Takeaway
Reaction was fast and broad: viral on X, front-page-level on Lobsters (108 points), modest on HN (31 points), and blogged by Simon Willison. Mainstream tech press picked it up within 48 h (TechRadar, IBTimes UK, VGTimes). Praise focused on the ingenuity. Critiques focused on how rare usable prop flyovers are, the manual curve extraction, and the hype in headlines. Privacy-defence tooling and advice emerged alongside.

### Cited Findings
- **Hacker News:**
  - "I discovered a sound that leaks your exact location…" by fortran77, 2 Nov 2026, 31 points, 6 comments — [HN 50344762](https://news.ycombinator.com/item?id=50344762)
  - KeplerBoy called the two-prop example "contrived" and said two aircraft in audible range is "a pretty rare event".
  - mikewarot tried it on a Covid-era video with a GNU Radio flowgraph and saw possible curves.
  - xpct argued the curve extraction needs human judgment and can't be fully automated. sgerenser suggested frontier LLMs could do it, and xpct doubted that.
  - putlake linked dopplertrack.
  - Source: [HN item via Algolia](https://hn.algolia.com/api/v1/items/50344762)
- HN TechRadar submissions: 15 points / 1 comment (pain_perdu, 4 Nov) and 2 points (vrganj, 4 Nov, titled "Geolocating any audio recording using flight data and the Doppler Effect") — [HN 50372645](https://news.ycombinator.com/item?id=50372645); [HN 50363049](https://news.ycombinator.com/item?id=50363049)
- **Lobsters:**
  - "This background sound leaks your exact location", submitted by fanf, 2 Nov 2026, score 108, 8 comments — [Lobsters](https://lobste.rs/s/s1btqo/this_background_sound_leaks_your_exact)
  - calvin expected it to be about mains hum / electrical network frequency (ENF) analysis.
  - zesterer: "Even 'noise' is not actually noise: it's a manifestation of the physical environment."
  - A thread speculated about intelligence-agency capabilities.
  - tactility suggested EV pedestrian-warning sounds as a future signal.
- **Simon Willison** blogmark, 3 Nov 2026: "Genius piece of OSINT by Colsto" — [simonwillison.net](https://simonwillison.net/2026/Nov/3/a-sound-that-leaks-your-exact-location/)
- **X/Twitter:**
  - Amplified by @0x45o on 3 Nov 2026 (https://x.com/0x45o/status/2117332304880169152), described as the viral spread. An X "trending" page appeared: "Airplane Noises Pinpoint Video Locations with Precision" (https://x.com/i/trending/2117370600494879132) — [AGTP on X](https://x.com/AGTPinsights/status/2117387488155029700); [ThakiCloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)
  - Digg AI aggregated 30.5K combined views and 735 likes across 12 sources. It notes @LilithDatura's point that diffusion models could both improve extraction and enable synthetic flyover noise, and @grok's "Not bogus" assessment — [Digg](https://digg.com/ai/7wr4rmyp)
- **Press:**
  - TechRadar: "YouTuber discovers aircraft noise trick that can geolocate your videos to within 100m" — [TechRadar](https://www.techradar.com/computing/cyber-security/youtuber-discovers-aircraft-noise-trick-that-can-geolocate-your-videos-to-within-100m-doppler-effect-pinpoints-locations-from-just-60-seconds-of-audio)
  - IBTimes UK: "YouTuber Reveals How Sounds Humans Cannot Hear Can Expose a Video's Exact Location" (via [Digg](https://digg.com/ai/7wr4rmyp))
  - VGTimes on DOPPLERGEIST, 3 Nov, by Arkadiy Andrienko — [VGTimes](https://vgtimes.com/tech-and-hardware/173330-dopplergeist-uses-aircraft-sounds-to-estimate-where-a-recording-was-made.html)
  - Other blogs: [The Daily Brief](https://www.thedailybrief.io/article/cmw0p4i7q000ele02iwl8qth5); [fdaytalk](https://fdaytalk.com/geolocate-video-from-audio); [ThakiCloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/); [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect)
  - A YouTube Short also covered it: [YouTube Short](https://www.youtube.com/shorts/a9Nb19eU8CE)
- **Defensive advice:**
  - Stripping GPS metadata is insufficient.
  - A 200 Hz low-cut left the signal intact (Cbonitz test).
  - Re-editing or cutting audio breaks the 920 s continuity.
  - Replacing ambient audio with music or voice-over, or delaying publication without timing clues, helps.
  - Bodila51 ships a flyover-masking Claude Code skill.
  - Source: [pasqualepillitteri.it](https://pasqualepillitteri.it/en/news/30208/aircraft-noise-geolocates-video-doppler-effect)
- fdop and dopplerprint READMEs explicitly restrict use to one's own or consented recordings, framing the tools as self-audits before publishing — [fdop](https://github.com/Dicklesworthstone/franken_doppler_finder); [PyPI dopplerprint](https://pypi.org/project/dopplerprint/)

### Inferences
- The speed of replication (multiple working clones in under 48 h, several AI-agent-built) became part of the story, cited as evidence the technique is reproducible ([ThakiCloud](https://thakicloud.com/tech-blog/en/dev/airplane-doppler-geolocation/)).
- Skepticism was mostly about practicality (frequency of usable prop flyovers, ADS-B coverage, time prior), not about the physics.

### Gaps
- No Reddit (r/OSINT, r/geoguessr) threads were found by search. They may exist but are not indexed.
- No Bellingcat, Sector035 "Week in OSINT", OSINT Newsletter, Nixintel or Henk van Ess coverage was found as of 5 Nov 2026. This may be too recent to index.
- No Bluesky, Mastodon or LinkedIn posts were found.
- The Paras Chopra replication is unverified (single secondary source).

## Q5. Related / precursor hobbyist and academic work

### Takeaway
Before colsto, no open-source OSINT tool for "geolocate a recording from aircraft Doppler + ADS-B" was found. Precursors are academic and patent work on acoustic aircraft localization via Doppler (mostly multi-microphone or known-sensor setups), plus adjacent audio-forensics techniques such as ENF (mains-hum) analysis.

### Cited Findings
- UPC (Barcelona) thesis / Univ. Oviedo work on passive acoustic aircraft localization using Doppler across a mesh of at least 7 microphones, solved with a genetic algorithm — [Uniovi portal](https://portalinvestigacion.uniovi.es/documentos/638954266514871f78dd46d0?lang=gl); [UPC](https://upcommons.upc.edu/bitstreams/a00f4ad0-dc9b-4b95-b88c-520b7b1a5184/download)
- DRDO Defence Science Journal paper on single-microphone estimation of UAV altitude, speed and RPM from Doppler-shifted harmonics — [DSJ](https://publications.drdo.gov.in/ojs/index.php/dsj/article/download/2238/1198/7489)
- Patents:
  - US 10473752B2: aerial vehicle position and velocity via sound Doppler analysis — [Google Patents](https://patents.google.com/patent/US10473752)
  - US 8059489: acoustic airport surveillance estimating closest-approach time, slant range and speed from time-frequency curves — [USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/8059489)
  - Honeywell US 4360795: closest-point detection — [Justia](https://patents.justia.com/patent/4360795)
  - A noise-complaint patent combining ADS-B closest-approach computation (no acoustic Doppler) — [USPTO](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/10445847)
- Al-Nahrain University (Iraq) thesis on airplane radial velocity from Doppler shift in recorded sound — [Nahrain](https://www.nahrainuniv.edu.iq/en/node/955)
- "Extra Ears" iOS app predicts aircraft noise from ADS-B/Mode S (OpenSky) data. This is the reverse direction, not geolocation — [App Store](https://apps.apple.com/app/extra-ears/id1557158431)
- ENF / mains-hum analysis was raised on Lobsters as the expected technique — [Lobsters](https://lobste.rs/s/s1btqo/this_background_sound_leaks_your_exact)
- An unrelated precursor: GPS coordinates embedded in police-helicopter video audio, decoded from published footage — [Gizmodo](https://gizmodo.com/a-hacker-found-gps-data-in-the-audio-of-this-police-cha-1514803232)
- An engineering write-up on single-channel range and speed estimation via Doppler-induced zero-crossing timing — [engineered.at](https://engineered.at/articles/fat-albert). Secondary and AI-summarised; treat with caution.

### Inferences
- colsto's novelty is combining single-microphone Doppler-curve fitting with **crowd-sourced historical ADS-B archives** (adsb.lol) and a **continental-scale search**. The academic precursors assume known sensor positions or arrays.

### Gaps
- No pre-2026 hobbyist GitHub project for "acoustic ADS-B", "plane spotting by microphone" or "Raspberry Pi aircraft sound localization" matched against ADS-B was found in the limited searches performed. Absence is not proven.
