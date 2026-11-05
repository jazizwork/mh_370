# Physics, Signal Processing and Academic Prior Art: Locating an Observer (or Aircraft) from the Doppler-Shifted Sound of a Passing Aircraft

Scope note: Labels used below.
- "Cited" means the source says it. I read most sources at abstract or listing level only. Full texts were reached for Reid/Zoubir/Boashash (1997, via CORE) and for two GitHub READMEs.
- "Derivation" means standard kinematics I worked out myself. It is checked against the one cited model equation (Reid et al.) and is flagged where it goes beyond it.
- Context: in 2026 a YouTube video by "colsto" claimed that propeller Doppler "whooshes" can be matched to ADS-B to geolocate a recording. Two independent GitHub projects responded to it, and both are summarised below. They are the closest thing to "prior art for the geolocation application". The underlying flight-parameter estimation science dates from 1992 onward, mostly from DSTO Australia.

---

## Q1. Acoustic Doppler for a moving source: the S-curve, CPA, how the curve encodes speed and slant range, and emission vs reception (retarded) time

### Takeaway
- **What one microphone yields:** A fixed microphone hearing a constant tone f0 from an aircraft in straight, level, constant-speed flight records a falling S-shaped frequency-vs-time curve. Fitting it gives four quantities:
  - source speed v (from the asymptotes)
  - CPA slant range R_c (from the slope at the centre)
  - CPA time t_c (from the centre)
  - rest frequency f0
- **Retarded time:** The fit must use emission (retarded) time, τ, related to reception time by t = τ + R(τ)/c.
- **Prior art:** B. G. Ferguson (DSTO) published this single-sensor narrowband method for propeller aircraft in 1992. Ferguson & Quinn (1994) and Reid/Zoubir/Boashash (1997) refined it.

### Cited Findings
- **Ferguson 1992 (founding paper).** B. G. Ferguson, "A ground-based narrow-band passive acoustic technique for estimating the altitude and speed of a propeller-driven aircraft," *J. Acoust. Soc. Am.* 92(3), 1403–1407 (1992), DOI 10.1121/1.403934. Single ground microphone. The propeller blade-rate frequency is tracked over short intervals as the aircraft passes and fitted by least squares to a Doppler model — [AIP abstract](https://pubs.aip.org/asa/jasa/article-abstract/92/3/1403/697032/A-ground-based-narrow-band-passive-acoustic?redirectedFrom=fulltext). I did not read the full text.
- **Ferguson & Quinn 1994.** B. G. Ferguson & B. G. Quinn, "Application of the short-time Fourier transform and the Wigner-Ville distribution to the acoustic localization of aircraft," *JASA* 96(2), 821–827 (1994), DOI 10.1121/1.410320 — [Macquarie Univ. record](https://researchers.mq.edu.au/en/publications/application-of-the-short-time-fourier-transform-and-the-wigner-vi/); DOI from [cbonitz/doppler-experiments refs](https://github.com/cbonitz/doppler-experiments).
  - A turboprop flies at constant altitude and speed past a single sensor.
  - The STFT and WVD estimate the propeller blade rate at short intervals.
  - A localization algorithm then estimates speed and range at CPA.
- **Ferguson 1995 ASA abstract.** "Application of narrow-band and broadband signal processing techniques to the acoustic detection and localization of aircraft," ASA 130th Meeting (1995), paper 4pSP10 — [ASA abstract](https://auditory.org/asamtgs/asa95stl/4pSP/4pSP10.html).
  - Because of Doppler, a stationary observer sees the transiting aircraft's spectrum as time-varying.
  - The blade-rate history from a single sensor gives speed, CPA range and the source (rest) frequency of the blade rate. This covers propeller aircraft and helicopters.
  - Broadband cross-correlation between two separated microphones detects transits.
  - Fast aircraft need short integration times and Doppler compensation.
- **Reid, Zoubir & Boashash 1997 (the observer-frequency model).** D. C. Reid, A. M. Zoubir, B. Boashash, "Aircraft flight parameter estimation based on passive acoustic techniques using the polynomial Wigner–Ville distribution," *JASA* (1997) — [full text via CORE](https://core.ac.uk/download/15120179.pdf). Volume and page numbers not verified.
  - Observed frequency: f_o(t) = f_a (c + v_m cos γ(t)) / (c + v_m cos γ(t) ± v_a cos γ(t)), with cos γ(t) = r(t)/√(h² + r²(t)).
  - Time–position relation: t = ±r(t)/v_a + (√(h² + r²(t)) − h)/c. This is the emission/reception (retarded-time) relation.
  - Symbols: h = constant height, v_a = aircraft speed, v_m = wind/medium term, r = horizontal range, f_a = source frequency.
  - The parameters (h, ground speed, source frequency, range) are estimated by computing instantaneous frequency with the PWVD/WVD and then fitting this model by least squares.
  - Example values: source frequency of about 68–100 Hz, speeds of 30.8–102.9 m/s (60–200 kn), heights of 152–897 m.
  - The fourth-order PWVD gave a lower instantaneous-frequency mean-square error than the WVD (e.g., 4.23×10⁻⁶ vs 3.53×10⁻⁵ Hz² in one example).
- **Related DSTO-era references** (from Reid et al.'s bibliography; titles not independently verified) — [CORE PDF](https://core.ac.uk/download/15120179.pdf):
  - B. G. Ferguson, *JASA* 94, 3244–3247 (1993). Search snippets suggest this paper treats the Doppler effect for an airborne source received by sensors above and below the sea surface (hydrophones), but the title is unverified.
  - B. G. Quinn, *JASA* 98, 2560–2566 (1995).
  - B. G. Ferguson & G. C. Speechley, ISSPA 92 (1992).
  - B. G. Ferguson, R. C. Trider, J. L. Hanlon, ICSPAT (1993).
  - D. C. Reid, Ph.D. thesis, QUT (1997).
- **Ferguson & Lo 2000 (narrowband vs broadband).** B. G. Ferguson & K. W. Lo, "Turboprop and rotary-wing aircraft flight parameter estimation using both narrow-band and broadband passive acoustic signal-processing methods," *JASA* 108(4), 1763–1771 (2000), DOI 10.1121/1.1286150 — [AIP abstract](https://pubs.aip.org/asa/jasa/article-abstract/108/4/1763/553561/Turboprop-and-rotary-wing-aircraft-flight).
  - Narrowband method: straight-line, constant speed and altitude, time-frequency analysis of a single sensor.
  - Broadband method: the same kinematics, fitted to TDOA histories (GCC-PHAT) across a planar array.
  - Data: one turboprop and two rotary-wing aircraft types.
- **Equations used in the 2026 replication.** Reception time t_r = t_e + r(t_e)/c, observed frequency f = f₀·c/(c + v_r), with c = 343 m/s — [cbonitz/doppler-experiments](https://github.com/cbonitz/doppler-experiments).
  - Information content: a 2-minute synthetic trace with 0.4 Hz frequency noise gave speed ±0.3 m/s and CPA distance ±20 m.
  - A waveform synthesised from propagation delay alone matched the Doppler formula to 0.026 Hz.
  - Using reception-time instead of emission-time geometry gave a shape error of up to 1.6 Hz. After a time shift this fell to near noise level, so the report calls the video's warning about it "overstated."
- **What the curve encodes (stated in the replication).** The frequency drop gives aircraft speed, the steepness gives CPA slant distance, and the midpoint gives the CPA time on the recording's clock — [cbonitz/doppler-experiments](https://github.com/cbonitz/doppler-experiments).

### Inferences (derivation: standard kinematics, consistent with the cited models)
- **Geometry.**
  - Source path: **s**(τ) = **s**_c + **v**(τ − τ_c), straight and level at speed v. The observer is at **x**, with CPA emission time τ_c.
  - Slant range: R(τ) = √(R_c² + v²(τ − τ_c)²), where R_c = √(Δh² + d²). Here Δh is the aircraft height above the microphone and d is the horizontal offset of the observer from the ground track.
- **Retarded time.**
  - t(τ) = τ + R(τ)/c, so dt/dτ = 1 + v_r/c, where the range rate is v_r = dR/dτ = v²(τ − τ_c)/R(τ).
  - Example: R = 1 km gives a delay of about 2.9 s. At 70 m/s the aircraft moves about 200 m in that time, so geometry evaluated at reception time is biased.
- **Doppler (still air, stationary observer).** f(τ) = f0 / (1 + v_r/c) = f0 / (1 − M cos θ(τ)), with M = v/c and θ the angle between the velocity and the source→observer line at emission. This matches Reid's model with v_m = 0.
- **Asymptotes and their inversion.**
  - Approaching, the curve tends to f₊ = f0/(1 − M). Receding, it tends to f₋ = f0/(1 + M).
  - Inverting: v = c (f₊ − f₋)/(f₊ + f₋) and f0 = 2 f₊ f₋/(f₊ + f₋).
  - Note that (f₊ + f₋)/2 = f0/(1 − M²) is slightly above f0, so the visual midpoint of the S is not exactly f0.
- **CPA.** At τ = τ_c, v_r = 0, so f = f0 exactly, and that sound is received at t_c = τ_c + R_c/c. Because dt/dτ = 1 there, the slope at that point is the same in emission and reception time.
- **Slope at CPA:** df/dt|_c = −f0 v²/(c R_c), so R_c = f0 v² / (c |df/dt|_c).
- **Duration of the swing.** The time scale of the transition is about R_c/v. A close or low pass gives a sharp step. A distant pass gives a gentle S.
- **Worked example.** f0 = 100 Hz, v = 70 m/s, c = 343 m/s (M ≈ 0.204):
  - f₊ ≈ 125.6 Hz and f₋ ≈ 83.1 Hz.
  - For R_c = 500 m the slope at CPA is about −2.86 Hz/s and the swing takes about 7 s.
  - For R_c = 3 km the slope is about −0.48 Hz/s.
- **Harmonics.** Every harmonic k·f0 carries the same fractional curve. Tracking higher harmonics improves the absolute frequency resolution of the slope estimate, and harmonics survive band-limiting.
- **Asymmetry in reception time.** dt/dτ = 1 + v_r/c means the approach is compressed and the recession stretched. The received S-curve is therefore slightly asymmetric about t_c, and the asymmetry grows with M. Fitting in emission time with an explicit t(τ) mapping, as Reid et al. do, removes this bias.

### Gaps
- **Full texts not read:** Ferguson 1992, Ferguson & Quinn 1994 and Ferguson & Lo 2000 were seen at abstract level only. The exact estimator equations, Cramér–Rao bounds and field accuracies (e.g., % error in altitude and speed for real turboprop transits) are not captured here.
- **Two titles unconfirmed:** Quinn 1995 (*JASA* 98, 2560) and Ferguson 1993 (*JASA* 94, 3244).
- **Reid et al. 1997 citation incomplete:** the volume and page numbers are not verified.

---

## Q2. Which aircraft sound features are usable: propeller BPF, turbofan fan/buzz-saw tones, helicopter rotor tones, and why jet broadband noise is harder

### Takeaway
- **Best features:** Stable narrowband tonals with a harmonic family. These are propeller blade-passage frequency (BPF) lines from turboprops and piston aircraft, and helicopter rotor lines.
- **Turbofans:** They emit fan BPF and "buzz-saw" multiple pure tones (shaft-order harmonics), but these are higher in frequency, directional and variable.
- **Jets:** Jet-mixing noise is broadband, so it carries no clean Doppler line. The DSTO group handled jets with broadband methods instead: ground-reflection multipath (Lloyd's mirror) and array TDOA.

### Cited Findings
- **Propellers.** Propeller aircraft emit a tone at blade-passage frequency, roughly 50–150 Hz, and a fixed microphone hears a falling S-shaped Doppler curve — [cbonitz/doppler-experiments](https://github.com/cbonitz/doppler-experiments). This is a secondary, AI-assisted source. Its propeller-noise references are NASA TP-2356 ([NTRS](https://ntrs.nasa.gov/citations/19840024054)) and NASA RP-1258 ([NTRS](https://ntrs.nasa.gov/citations/19920001380)).
- **DSTO aircraft types.** The narrowband Doppler work targeted propeller-driven aircraft and helicopters — [Ferguson 1995 ASA abstract](https://auditory.org/asamtgs/asa95stl/4pSP/4pSP10.html). Data included a turboprop and two rotary-wing types — [Ferguson & Lo 2000](https://pubs.aip.org/asa/jasa/article-abstract/108/4/1763/553561/Turboprop-and-rotary-wing-aircraft-flight).
- **Jets.** Lo, Perry & Ferguson (2002) model the Lloyd's mirror interference pattern seen during jet aircraft transits rather than a tonal Doppler line. They tested on 10 jet transits — [ResearchGate listing](https://www.researchgate.net/publication/3003442_Aircraft_flight_parameter_estimation_using_acoustical_Lloyd's_mirror_effect); [Academia.edu PDF](https://www.academia.edu/4391164/Aircraft_flight_parameter_estimation_using_acoustical_Lloyds_mirror_effect).
- **Turbofan buzz-saw / multiple pure tones (MPT).**
  - Shock-related tones appear at harmonics of shaft rotation frequency (engine orders), not only at BPF. They peak near a fan relative tip Mach number of about 1.2 — [Han et al., Iowa State CAAL](https://www.aere.iastate.edu/caal/assets/papers/han_2014_mpt.pdf); [HAL: MPT in turbofans at transonic regime](https://hal.archives-ouvertes.fr/hal-01067840).
  - Blade-to-blade stagger variation drives the tone content.
  - Energy can leak into shaft-order tones even at subsonic tip speeds — [NASA CEAS/AIAA 2024 paper](https://ntrs.nasa.gov/api/citations/20240005861/downloads/Fernandes%20CEAS%20AIAA%20Aeroacoustics%202024.pdf).
  - Buzz-saw is mainly a forward-radiated, takeoff/climb phenomenon tied to high fan speeds (search summary; same sources).
- **Drones and UAVs.**
  - BPF is f0 = N_blades × RPM/60 and forms a "harmonic stack". The fundamentals are typically 150–400 Hz for commercial drones — [drone-warfare.com Counter-UAS 101](https://drone-warfare.com/counter-uas/acoustic-detection/) (trade source; treat as indicative).
  - As propeller designs reduce tonal noise, broadband turbulent noise becomes the dominant signature (same source).
- **Phone-band survival.** Under telephone band limits (300–3400 Hz), the curve survives through harmonics. Synthetic tests recovered 96% of frames when harmonics were strong and 51% when they were weak. A linear high-pass had no effect after per-bin normalisation — [cbonitz/doppler-experiments](https://github.com/cbonitz/doppler-experiments).
- **Real recordings are harder than synthetic ones.** An independent open-source implementation reports that "turning flights and livestream/field audio often yield no events" — [mojomast/hermes-aircraft-doppler-geolocation](https://github.com/mojomast/hermes-aircraft-doppler-geolocation).

### Inferences
- **Feature ranking for geolocation:**
  1. Turboprop and piston BPF harmonics: low frequency, strong, stable rpm in cruise.
  2. Helicopter main and tail rotor lines.
  3. Turbofan fan BPF and buzz-saw tones: high frequency, directional, rpm changes with thrust, tones strongest near airports in climb.
  4. Jet broadband: no Doppler line, but usable through multipath delay, cepstrum or arrays.
- **What makes a tone usable:** the source rest frequency f0 must be constant across the pass. Any rpm or thrust change during the pass is confounded with Doppler. This favours cruise or level segments.
- **Why jets are harder:**
  - The broadband spectrum has no single instantaneous frequency to track.
  - Jet noise is highly directional, with the peak aft, which distorts the amplitude envelope.
  - At high altitude the high frequencies are absorbed.
  - Doppler can still be read from the time-scaling of the broadband envelope or from Lloyd's-mirror fringe shapes, which Lo et al. exploit.
- **Helicopter values (general knowledge, not sourced here):** main-rotor BPF is typically on the order of 10–30 Hz and tail-rotor lines several tens of Hz to about 100 Hz. Both are strongly harmonic.

### Gaps
- No primary measured values were captured for helicopter main/tail rotor frequencies or for turboprop BPF by type, for example as N_blades × propeller rpm/60. NASA TP-2356 and RP-1258 are the right sources but were not read.
- No source quantified the tonal-to-broadband ratio of modern turbofans at cruise altitude as heard on the ground.

---

## Q3. How matching works: candidate observer locations × ADS-B tracks, unknown recording time and unknown f0, and how multiple passes triangulate

### Takeaway
- **Forward model:** for every candidate ground point, predict each nearby ADS-B aircraft's Doppler curve (CPA time, CPA slant range, speed) using retarded time and the real, possibly turning, track. Then score against the measured tone track(s).
- **Nuisance parameters:** f0 is fitted per event, and the recording clock offset is searched.
- **What one or two passes give:**
  - One straight pass with an unknown clock constrains the observer to two lines parallel to the track. The left/right mirror ambiguity is broken only by turns or speed/altitude changes.
  - Two passes, with the measured inter-event offset locking the clocks, collapse this to roughly one point.
- **State of practice:** two independent 2026 implementations show it works well on synthetic data. A real-audio implementation reports mostly failures on unseen clips.

### Cited Findings
- **Replicated pipeline (cbonitz):**
  1. Extract the S-curve.
  2. Read speed, CPA distance and CPA time.
  3. For each candidate point and flight, predict when the aircraft would be heard, at what distance and at what speed.
  4. Keep points where two flights match the measured time offset (920 s in the synthetic test) and no other aircraft should have been heard in between (the "silence filter").
  5. Refine with the exact Doppler curve from the real turning path, locking the second event's timing to the first.

  [cbonitz/doppler-experiments](https://github.com/cbonitz/doppler-experiments)
- **Locus geometry.**
  - One curve with an unknown clock constrains the observer to two lines parallel to the track. Two curves give four crossings, and locking the clocks via the measured offset leaves one point.
  - A straight pass is mirror-ambiguous. Mirror observers differ by only 0.7 Hz at a 0.1°/s turn and by 6.3 Hz at 1°/s.

  [cbonitz/doppler-experiments](https://github.com/cbonitz/doppler-experiments)
- **Filter funnel.** The offset filter alone keeps 98% of candidate points. Adding the speed and distance filters keeps 4%. Adding the silence filter keeps 1.2% — [cbonitz](https://github.com/cbonitz/doppler-experiments).
- **Synthetic results (cbonitz).**
  - Setup: 242 propeller flights over 6 h in a 40×40 km region with an airport. The recording is 25 min long, with two faint flyovers and no clock or location given.
  - **Two flyovers, unknown time of day:** the correct pair ranked first in 6/6 synthetic worlds. Location error was 85–465 m in 5 worlds and 830 m in the sixth, and 4 m with no model errors.
  - **Single flight:**
    - With the clock known to ±1 min, the correct flight ranked first in 5/6 worlds.
    - With a 1-hour window, it ranked first in 0/6, because segments of other flights produced near-ties.
  - **Compute:** a two-event search over one day of CONUS data takes about 5–10 minutes on a laptop.

  [cbonitz](https://github.com/cbonitz/doppler-experiments)
- **Failure modes (cbonitz):**
  - Missing ADS-B. Low-level general aviation is not required to carry ADS-B Out everywhere; see 14 CFR 91.225 ([LII](https://www.law.cornell.edu/cfr/text/14/91.225)).
  - Sparse traces during turns.
  - Barometric altitude bias.
  - Refraction shadow zones that falsely trigger the silence filter.
  - Automatic event detection failed in 1 of 7 worlds.

  [cbonitz](https://github.com/cbonitz/doppler-experiments)
- **Real-audio implementation (hermes / `dopplergeo`, v0.3.1).**
  - **Front end:** 4 kHz resampling, whitened 1 s spectrogram, harmonic sum (k ≤ 6), CFAR detection, Viterbi multi-ridge tracking.
  - **Event acceptance test:** an F-test against a constant tone, plus a frequency drop, plausible speed, CPA inside the tone, and a non-degenerate distance.
  - **Inputs:** ADS-B from adsb.lol daily dumps, the Copernicus GLO-30 DEM for ground height, and Open-Meteo temperature to set c.
  - **Search and model:** a coarse-to-fine grid at 1000/200/50 m. Emission time τ is solved so that t = τ + r(τ)/c.
  - **Scoring:** a robust f0 scale per event, a joint likelihood across events, a penalty on missing expected passes, and a posterior tempered by the Birge ratio. Unknown start times are searched with sliding offsets.
  - **Reported accuracy:**
    - About 1 km on clean multi-pass recordings, but it "mostly fails on unseen clips."
    - Tonal pipeline on 14 held-out clips: 1 solved under 3 km, median error 12.1 km for solved runs.
    - With broadband added, 18 held-out clips: 2 under 3 km.

  [mojomast/hermes-aircraft-doppler-geolocation](https://github.com/mojomast/hermes-aircraft-doppler-geolocation)
- **ADS-B data sources:** OpenSky Trino historical database ([docs](https://openskynetwork.github.io/opensky-api/trino.html)), adsb.lol globe_history ([GitHub](https://github.com/adsblol/globe_history)) and ADS-B Exchange ([data products](https://www.adsbexchange.com/data-products/)) — listed in [cbonitz refs](https://github.com/cbonitz/doppler-experiments). ADS-B decoding background: J. Sun, *The 1090 MHz Riddle* ([mode-s.org](https://mode-s.org/1090mhz/content/ads-b/1-basics.html)).
- **Origin of the claim.** colsto, "I discovered a sound that leaks your exact location (and it's everywhere)," YouTube (2026). It claims geolocation of a security-camera recording "within a couple hundred feet" and released no code — [video](https://www.youtube.com/watch?v=UytYrhYLOKI), as summarised by [cbonitz](https://github.com/cbonitz/doppler-experiments).
- **Analogous forensic technique.** Electrical Network Frequency (ENF) matching timestamps recordings against a reference grid-frequency log — C. Grigoras, *Forensic Sci. Int.* 167 (2007), DOI 10.1016/j.forsciint.2006.06.033 (cited in [cbonitz](https://github.com/cbonitz/doppler-experiments)).

### Inferences
- **Measurement model (derivation).** Each detected event k gives a measured frequency track f_k(t_i). The forward model for observer **x**, clock offset Δ and aircraft j is:
  - f̂(t) = f0_k / (1 + v_r,j(τ; **x**)/c)
  - with t = τ + R_j(τ; **x**)/c + Δ
  - and R_j, v_r,j computed from the interpolated ADS-B track (lat, lon, geometric or corrected baro altitude, ground velocity), minus the DEM elevation at **x**.
  - Cost: Σ_k min_{f0_k} Σ_i [f_k(t_i) − f̂]² / σ², with Δ shared across events. This is the multi-event analogue of Reid et al.'s least-squares fit.
- **Unknown f0.** f0 is a pure scale factor per event, so the ratio f/f0 carries all the geometry and f0 can be profiled out analytically. The aircraft type (ICAO Doc 8643 / tar1090-db) can give a prior on BPF from blade count × typical rpm and help select candidate aircraft.
- **Speed cross-check.** The speed is measured independently, as v = c·(f₊ − f₋)/(f₊ + f₋). It should match the ADS-B speed, after correcting for wind (Q5), which helps pick the right aircraft.
- **CPA range → offset from the track.** R_c combined with ADS-B altitude gives the horizontal offset d = √(R_c² − Δh²). This is the "two parallel lines" locus. Its accuracy depends on the R_c error, so a high pass at small d constrains d poorly (∂d/∂R_c = R_c/d is large).
- **CPA time → position along the track.** If the absolute time is known, t_c pins the along-track position, giving a v·σ_t error. For example, a 1 s error at 70 m/s is 70 m. If time is unknown, the along-track position is free for a single event. That is why two events with a measured relative offset are needed.
- **Triangulation geometry.** Two passes on non-parallel tracks give well-conditioned intersections. Parallel tracks, such as successive arrivals on the same approach path, give poor intersections, which is a likely failure mode near airports.
- **Negative information.** The "silence" constraint (no other aircraft should have been audible) is powerful but brittle. It depends on complete ADS-B coverage and on propagation modelling.

### Gaps
- No peer-reviewed paper was found that does observer geolocation by Doppler matching against ADS-B. The prior art is either aircraft-parameter estimation (DSTO, 1992–2016) or the 2026 community or AI-assisted replications, which are not peer reviewed.
- The colsto video's real-world result has not been independently reproduced. No audio or ADS-B extract has been published.

---

## Q4. Lloyd's mirror / ground-reflection interference as an altitude and geometry cue

### Takeaway
- **What the reflection produces:** a microphone near the ground receives the direct path plus a ground-reflected path delayed by about 2·h_r·sin(elevation)/c. This produces comb-filter notches ("Lloyd's mirror" fringes) in the spectrogram, whose frequencies vary as the elevation angle changes during the pass.
- **Prior art:** Lo, Perry & Ferguson (2002) and Lo & Ferguson (2003) estimate jet speed and altitude from these fringes and delays. A cepstrum-based estimator was the most precise.

### Cited Findings
- **Lo, Perry & Ferguson 2002.** K. W. Lo, S. W. Perry, B. G. Ferguson, "Aircraft flight parameter estimation using acoustical Lloyd's mirror effect," *IEEE Trans. Aerosp. Electron. Syst.* 38(1), 137–151 (2002), DOI 10.1109/7.993235 — [ResearchGate](https://www.researchgate.net/publication/3003442_Aircraft_flight_parameter_estimation_using_acoustical_Lloyd's_mirror_effect); [Academia.edu](https://www.academia.edu/4391164/Aircraft_flight_parameter_estimation_using_acoustical_Lloyds_mirror_effect).
  - Models the interference pattern in the time-frequency output of a near-ground microphone during a jet transit.
  - Analyses feasibility with the Cramér–Rao lower bound.
  - Uses nonlinear least squares and a generalized Hough transform.
  - Validated on 10 jet transits recorded by individual sensors of a large array.
- **Lo & Ferguson 2003.** K. W. Lo & B. G. Ferguson, "Aircraft flight parameter estimation using acoustic multipath delays," *IEEE TAES* 39(1) (2003), DOI 10.1109/TAES.2003.1188908 (DOI as listed by [hermes repo](https://github.com/mojomast/hermes-aircraft-doppler-geolocation)).
  - The direct-to-ground-reflected arrival difference ("multipath delay") gives an instantaneous estimate of the source elevation angle.
  - Model: a jet in level flight over hard ground.
  - Two estimators: autocorrelation and cepstrum. The cepstrum method gave the most precise speed and altitude estimates compared with its counterpart and two earlier methods.

  Search-result summaries of the abstract; full text not read.
- **Conference work:** "Flight parameter identification from cepstrum tracks," IDC 2002, DOI 10.1109/IDC.2002.995436 — listed by [hermes repo](https://github.com/mojomast/hermes-aircraft-doppler-geolocation). Authorship is given inconsistently ("Ferguson & Lo / Quinn") and is unverified.
- **Small-array extension:** "Flight parameter estimation using time delay and intersensor multipath delay measurements from a small aperture acoustic array," *JASA* 134(1), 17 (2013) — [AIP](https://pubs.aip.org/asa/jasa/article-abstract/134/1/17/614445/Flight-parameter-estimation-using-time-delay-and?redirectedFrom=fulltext). Authors not verified; likely the Lo/Ferguson group.
- **Tracking low-flying aircraft (2016):** "Passive acoustic system for tracking low-flying aircraft," *IET Radar, Sonar & Navigation* (2016), DOI 10.1049/iet-rsn.2016.0159 — [IET](https://digital-library.theiet.org/doi/full/10.1049/iet-rsn.2016.0159). Authors not verified.
- **Spectrogram vs cepstrogram.** Flight-vehicle spectrograms show several orders of destructive-interference curves, and cepstrogram analysis gave more accurate estimates than the spectrogram — [KoreaScience article](https://www.koreascience.or.kr/article/JAKO201534165173876.page?&lang=en) (abstract-level).
- **Recent machine-learning use.** Adaptive cepstral filtering is used to mitigate Lloyd's-mirror multipath artefacts in ship and aircraft spectrograms for classification — [arXiv 2512.11165](https://arxiv.org/html/2512.11165v2).
- **Implementation.** The hermes implementation tracks the cepstral peak of the ground-reflection delay (about 2·h·sin(elevation)/c) and fits a delay curve to estimate CPA and speed. This "broadband" mode is experimental — [hermes repo](https://github.com/mojomast/hermes-aircraft-doppler-geolocation).

### Inferences (derivation)
- **Geometry.** Microphone height h_r, source height h_s, horizontal range x. The image source sits at −h_s.
  - Path difference: Δℓ = √(x² + (h_s + h_r)²) − √(x² + (h_s − h_r)²) ≈ 2 h_r sin φ for h_s, x ≫ h_r, where φ is the elevation angle.
  - Delay: τ_m(t) ≈ 2 h_r sin φ(t)/c.
- **Notch frequencies.** For a hard ground with reflection coefficient ≈ +1, the notches fall at f_n = (2n+1)/(2 τ_m), n = 0, 1, 2, … The notch spacing is 1/τ_m.
- **Example: phone or camera at 1.5 m.** τ_m,max = 2·1.5/343 ≈ 8.7 ms at φ = 90°. The first notch is then at about 57 Hz and the spacing about 115 Hz. As elevation falls toward the horizon, the notches sweep upward, producing the characteristic arched fringes centred on CPA.
- **Microphone heights compared.** At 10 m (a rooftop CCTV camera), τ_m,max ≈ 58 ms and the notches are about 17 Hz apart. Fringes are then dense and easy to see in broadband jet noise.
- **Geolocation cue:**
  - The fringe history gives sin φ(t). At CPA, sin φ_c = Δh/R_c.
  - Combined with the ADS-B altitude, this gives the horizontal offset from the track: d = Δh·cot φ_c. This is independent of the tonal Doppler slope.
  - The shape of sin φ(t) has a time scale of R_c/v.
  - The catch: the microphone height h_r is an unknown nuisance parameter, which scales the delay.
  - Ground impedance (grass vs pavement) changes the reflection phase and shifts the notches. This was not quantified here.
- **Interaction with tonal Doppler.** Notches can also cut through a tonal Doppler track and look like gaps or dropouts in the tonal ridge. cbonitz explicitly did not model ground-reflection notches.

### Gaps
- The full texts of the 2002 and 2003 papers were not read, so their CRLB values and field accuracies (e.g., % error in altitude/speed for the 10 jet transits) are not captured.
- The authors of the 2013 *JASA* and 2016 *IET* papers are not verified.
- No source quantified Lloyd's-mirror visibility for handheld or elevated consumer microphones, or how impedance-ground effects alter it.

---

## Q5. Speed of sound, temperature and wind effects on predictions

### Takeaway
- **How c enters:** linearly in the speed estimate (v ∝ c) and in the CPA range (R_c ∝ f0 v²/(c·slope), so ∝ c once v scales with c). It also sets the retarded-time delay.
- **Temperature:** produces errors at the per-cent level, about 0.18% of c per °C.
- **Wind:** enters both the Doppler ratio and the propagation time. It also creates the discrepancy between ADS-B ground speed and the air-relative speed that Doppler measures.
- **Refraction:** from wind and temperature gradients, it can create shadow zones. This matters most for "should have been heard" logic.
- **Size of the effect in practice:** the 2026 synthetic replication found wind and temperature residuals of only about 0.5 Hz.

### Cited Findings
- **Replication (cbonitz).**
  - Worked example uses c = 343 m/s.
  - Wind and temperature cause residuals of about 0.5 Hz.
  - Synthetic error model: wind, temperature, barometric altitude bias, ADS-B noise, 2 s sampling.
  - Not modelled: wind-shear refraction, real background noise, ground-reflection notches.

  [cbonitz/doppler-experiments](https://github.com/cbonitz/doppler-experiments)
- **Atmosphere references** (from [cbonitz refs](https://github.com/cbonitz/doppler-experiments)):
  - Speed of sound in air ([Wikipedia](https://en.wikipedia.org/wiki/Speed_of_sound)).
  - Outdoor sound propagation, Embleton, *JASA* 100 (1996), DOI 10.1121/1.415879.
  - Atmospheric absorption: ISO 9613-1:1993 ([ISO](https://www.iso.org/standard/17426.html)) and Bass et al., *JASA* 97 (1995), DOI 10.1121/1.412989.
- **Reid et al.'s model** includes a medium or wind velocity term, v_m: f_o(t) = f_a (c + v_m cos γ)/(c + v_m cos γ ± v_a cos γ) — [CORE PDF](https://core.ac.uk/download/15120179.pdf).
- **hermes temperature handling.** Uses Open-Meteo temperature to set c, and uses the DEM ground height for the observer — [hermes repo](https://github.com/mojomast/hermes-aircraft-doppler-geolocation).
- **Track altitude tolerance.** In airport noise-monitoring correlation, radar flight tracks carry altitude errors of up to about 200 ft, consistent with normal radar tolerances — [Airservices Australia STMP Tarragindi report](https://www.airservicesaustralia.com/wp-content/uploads/Short_Term_Monitoring_Program_Tarragindi_QLD_-_Aug_20131.pdf).
- **Barometric altitude bias** is a named real-world risk — [cbonitz](https://github.com/cbonitz/doppler-experiments).

### Inferences (derivation)
- **Temperature formula.** c ≈ 331.3·√(1 + T/273.15) m/s, roughly 331.3 + 0.606·T(°C). Each 10 °C is about a 1.8% change in c.
- **Sensitivities:**
  - Speed estimate: v̂ = c (f₊ − f₋)/(f₊ + f₋) scales 1:1 with c.
  - CPA range: R̂_c = f0 v̂²/(c |ḟ|) also scales about 1:1 with c, so a 10 °C error gives about 1.8% of R_c (9 m at 500 m).
  - Retarded-time delay R/c shifts t_c by about R_c·δc/c² (e.g., 1 km and 6 m/s gives about 0.05 s).
- **Temperature profile.** The atmosphere cools about 6.5 °C/km in the standard lapse rate. A path to an aircraft at 1–3 km should use a path-averaged c, not the surface value.
- **Wind (first order).**
  - In an air-fixed frame, the source velocity is **u**_s = **v**_g − **w** and the observer's is **u**_o = −**w**, where **v**_g is the ADS-B ground velocity and **w** the wind.
  - The general Doppler form is f = f0 (c − **u**_o·k̂)/(c − **u**_s·k̂), with k̂ the unit propagation direction from source to observer.
  - So wind enters as an effective sound speed c + **w**·k̂ along the ray, and as the air-relative aircraft speed.
  - A 10 m/s wind on a 60 m/s aircraft is a large perturbation, about 16%, of the airspeed. Doppler-derived speed should be compared with **v**_g − **w**, not raw ground speed.
  - Wind aloft is available from reanalysis (e.g., Open-Meteo/ERA5) or from Mode-S EHS-derived winds.
- **Refraction.** Upwind and temperature-inversion conditions bend rays and create shadow zones or enhancements. They alter both audibility (the silence filter) and the effective arrival angle (Lloyd's mirror).

### Gaps
- No peer-reviewed quantification was found of how errors in wind or temperature profiles propagate into observer-location error for this specific application. The only numbers are cbonitz's synthetic ones.
- I did not read Embleton (1996) or ISO 9613-1. Values for absorption at aircraft distances (e.g., dB/km at 100 Hz vs 1 kHz) are not captured here.

---

## Q6. Related research: passive acoustic aircraft detection and tracking networks, airport noise monitoring correlated with flight tracks, drone detection, ADS-B-labelled audio datasets, machine learning

### Takeaway
- **Airport noise monitoring:** these systems routinely correlate microphone noise events with radar or flight tracks. They use threshold-triggered events and time and space windows, with 67–92% correlation rates. That is coarse event-to-track matching, not Doppler geolocation.
- **ADS-B-labelled audio:** AeroSonicDB shows that ADS-B can be used to label aircraft audio automatically.
- **Drone acoustic detection:** this literature relies on BPF harmonics plus array TDOA and beamforming.
- **Defence systems:** DSTO's array work (1995–2016) is the closest academic lineage to acoustic aircraft tracking.

### Cited Findings
- **How airport noise-and-track monitoring works.**
  - Monitors trigger events on threshold exceedance for a set duration. The system then automatically correlates the events with aircraft movement and radar data — [Dublin Airport noise monitoring](https://www.dublinairport.com/docs/default-source/North-Runway-Docs/aircraft-noise-monitoring.pdf?sfvrsn=0).
  - Sound alone cannot determine which aircraft was responsible, which is why track data is required — [Wallis & Tingay, IOA](https://www.ioa.org.uk/system/files/publications/AD%20WALLIS%20JD%20TINGAY%20AN%20INTERNATIONAL%20PERSPECTIVE%20ON%20AIRPORT%20NOISE%20MONITORING.pdf).
  - Farnborough searches radar data for aircraft within a set radius of each monitor — [FACC](https://www.facc.org.uk/?p=198).
- **MACNOMS (Minneapolis–St Paul).**
  - Event trigger: 65 dBA for at least 8 s.
  - Validation against field observations: noise-to-track agreement 92.1% and operation-to-operation 97.1%.

  [MAC NOMS validation report 2014](https://metroairports.org/documents/reports/macnoms-validation-report-2014/direct)
- **Airservices Australia correlation rates.** A 79% overall correlation is "a good result". Sites range from about 67% (Gymea Bay) to 92% (Haberfield 2) — [Tarragindi](https://www.airservicesaustralia.com/wp-content/uploads/Short_Term_Monitoring_Program_Tarragindi_QLD_-_Aug_20131.pdf); [Gymea Bay](https://www.airservicesaustralia.com/wp-content/uploads/Short_Term_Monitoring_Program_Gymea_Bay_NSW_-_March_2014.pdf); [Haberfield 2](https://www.airservicesaustralia.com/wp-content/uploads/Short_Term_Monitoring_Program_Haberfield_2_NSW_-_March_2014.pdf).
- **AeroSonicDB (YPAD-0523).**
  - Low-flying aircraft audio, labelled passively by exploiting ADS-B transmissions to trigger recordings.
  - 625 aircraft recordings (18–60 s each, 8.87 h in total) from 301 unique aircraft, plus about 3.5 h of background.
  - Filenames carry the ICAO address, last reported altitude, time, location and microphone ID.

  [arXiv 2311.06368](https://arxiv.org/abs/2311.06368); [Zenodo](https://zenodo.org/records/8368882)
- **AeroSonicDB 3K.** A machine-labelled extension with more than 3,000 events, recorded near Adelaide Airport — [Zenodo 12775560](https://zenodo.org/records/12775560).
- **No OpenSky audio dataset found.** I found no dataset explicitly built on OpenSky plus microphones. The search came back empty, which is a negative result.
- **Other datasets and classifiers:**
  - A microphone-array take-off noise dataset (188 measurements) with ML classification — [alejandECE/air-noise](https://github.com/alejandECE/air-noise).
  - An "automatic classification of aircraft flyovers using acoustic data" system (IEEE conference) — [ResearchGate](https://www.researchgate.net/publication/3943573_A_system_for_automatic_classification_of_aircraft_flyovers_using_acoustic_data).
  - An acoustic vector sensor for localizing low-flying aircraft — [JOAST](https://www.joast.org/index.php/joast/article/download/434/411/825).
  - "Aircraft localization using a passive acoustic method. Experimental test," *Aerospace Science and Technology* (2015) — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1270963815003673).
- **DSTO detection and array work.** Ferguson 1995 used broadband cross-correlation between two microphones for automatic transit detection — [ASA abstract](https://auditory.org/asamtgs/asa95stl/4pSP/4pSP10.html). Ferguson & Lo 2000 used GCC-PHAT TDOA tracking on a planar array — [AIP](https://pubs.aip.org/asa/jasa/article-abstract/108/4/1763/553561/Turboprop-and-rotary-wing-aircraft-flight).
- **Underwater sensing of aircraft.**
  - Ferguson and Lo also estimated aircraft speed and altitude from hydrophone data, using Doppler and differential arrival times — search summaries of DSTO work (see [CORE refs](https://core.ac.uk/download/15120179.pdf)).
  - A 2022 *Frontiers in Marine Science* paper models the helicopter line spectrum at a single hydrophone as a Doppler-modulated signal — [Frontiers](https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2022.996493/pdf).
  - A low-flying helicopter's head wave has been used to estimate sediment sound speed — [JASA 142(4) 2273](https://pubs.aip.org/asa/jasa/article-abstract/142/4/2273/853175/Estimating-the-sound-speed-of-a-shallow-water?redirectedFrom=fulltext).
- **Drone and UAV acoustics.**
  - A 2025 *IEEE Access* systematic review covers drone-mounted sound source localization (49 studies from 2014–2024; 60% use 8 or fewer microphones) — [DOAJ](https://doaj.org/article/d729ae01232e405fac3931be37ef3ea0).
  - Biologically inspired acoustic UAV detection — [JASA 151(2) 968](https://pubs.aip.org/asa/jasa/article/151/2/968/2838373/Acoustic-detection-of-unmanned-aerial-vehicles).
  - An ESA NAVISP topic on acoustic arrays for drone localization — [ESA](https://navisp.esa.int/opportunity/details/145/show).
  - A neural BPF estimator with a mean absolute error of 16 Hz within 150 m — [arXiv 2602.09991](https://arxiv.org/html/2602.09991) (preprint).
  - Trade sources claim a 300–500 m range for small quadcopters, with degradation in wind above 5 m/s — [drone-warfare.com](https://drone-warfare.com/counter-uas/acoustic-detection/) (unverified secondary).
- **Time-frequency textbook treatment.** *Time-Frequency Signal Analysis and Processing* (Boashash, ed., 2nd ed. 2016) includes an application in which a propeller aircraft or helicopter passing overhead allows flight-parameter estimation via Doppler — [QSpace listing](https://qspace.qu.edu.qa/handle/10576/22917). Chapter authorship not verified.

### Inferences
- **Noise-monitoring infrastructure as a resource.** Airport noise-and-track systems are effectively the "inverse" problem at known microphone locations. Their correlation logic (time windows, search radii) and their 67–97% agreement rates are a realistic benchmark for event-to-aircraft association. Noise monitoring terminal (NMT) data plus flight tracks would make a ready-made ground-truth testbed for validating Doppler-geolocation methods.
- **ADS-B-triggered datasets.** AeroSonicDB-style datasets have ground-truth ICAO and time labels. They could be used to train the tone-detection front end, which is the weakest link according to the hermes results on real audio.
- **Machine learning is used for detection, classification and BPF estimation,** not for end-to-end geolocation. No ML geolocation-by-Doppler paper was found.

### Gaps
- No peer-reviewed "acoustic ADS-B validation" study was found that compares Doppler-derived flight parameters with ADS-B truth. A literature search on combinations such as "ADS-B" + "Doppler" + "acoustic" + "validation" in JASA, Applied Acoustics or IEEE Sensors is warranted.
- Commercial airport noise systems (e.g., Envirosuite/ANOMS, Brüel & Kjær/EMS WebTrak) were not examined. Their correlation algorithms are not public in the sources found.
- Applied MH370 relevance: no source was found tying Doppler-audio geolocation to the MH370 case. Nothing found here supports any such link.
