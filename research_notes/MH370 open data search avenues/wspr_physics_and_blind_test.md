# WSPR aircraft-scatter physics and a fully public-data blind test of the WSPR-MH370 tracking hypothesis

Notes compiled 2026-11-05. Anything labelled **[INFERENCE]** is my own calculation or reasoning, not a sourced claim. Live database queries were run this session against `https://db1.wspr.live/`. Raw extracts and scripts are in the scratchpad:
- `mh370-open/video/data/ (gzipped) or <local scratch>/wspr/mh370_window.csv`: every spot from 2014-03-07 16:00 to 2014-03-08 01:00 UTC; 109,280 rows, 13.9 MB.
- `mh370-open/video/data/ (gzipped) or <local scratch>/wspr/recent_20m_2h.csv`: 20 m spots from 2025-03-07 16:00 to 18:00 UTC; 229,855 rows, 12.5 MB.
- `mh370-open/scripts/wspr/` holds four scripts: `wspr_cov.py` (path coverage), `wspr_lp.py` (long-path coverage), `wspr_var.py` (SNR/drift variability) and `physics.py` (link budget, Doppler, power analysis).

---

## Q1. Physics: can one airliner measurably change a WSPR spot's SNR or drift?

### Takeaway
No. A bistatic/forward-scatter link budget puts the scattered field of a Boeing 777 at roughly 50–120 dB below the direct skywave signal on typical WSPR geometries. That caps the change in reported SNR at about 0.00001–0.03 dB. WSPR reports SNR in 1 dB steps, and its natural slot-to-slot scatter is 3–5 dB (SD). A visible 1 dB change would need the scattered power to be only about 18 dB below the direct signal. That is 30 to 100 dB more than physics allows, unless the aircraft is very close to a high-power transmitter. Critics' published estimates and DK8OK's measurements agree on the order of magnitude.

### Cited Findings

**WSPR signal and measurement facts**
- WSPR protocol parameters from the WSJT-X 2.7 guide, Table "WSPR": FEC "K=32, r=1/2 (162,50)", 4-FSK, keying rate 1.465 baud (tone spacing equals the keying rate), occupied bandwidth 5.9 Hz, Tx duration 110.6 s, S/N threshold −31 dB. The guide says WSPR "can be decoded at signal-to-noise ratios as low as -31 dB in a 2500 Hz bandwidth." FST4W-120 has the same 1.46 Hz/5.9 Hz parameters and a −32.8 dB threshold; FST4W-1800 reaches −44.8 dB. — [WSJT-X 2.7 User Guide](https://wsjt.sourceforge.io/wsjtx-doc/wsjtx-main-2.7.0.html)
- How the reference decoder `wsprd.c` measures SNR. It estimates noise as the "30'th percentile" of a 7-point-smoothed average spectrum over ±150 Hz (411 bins). It then computes SNR as 10·log10(peak/noise − 1) − 26.3 dB for WSPR-2 (35.3 dB for WSPR-15). A code comment says the decode threshold is "near -7dB in wspr bandwidth, corresponding to -7-26.3=-33.3dB in 2500 Hz bandwidth." The spectrum is averaged over the whole transmission, so one spot's SNR is a single ~110.6 s average, and it is a ratio to the receiver's own noise estimate, not an absolute signal level. — [wsprd.c (GitHub mirror of WSJT-X source)](https://raw.githubusercontent.com/saitohirga/WSJT-X/master/lib/wsprd/wsprd.c)
- How `wsprd.c` defines drift. "The frequency drift model is linear, deviation of +/- drift/2 over the span of 162 symbols." The search runs over integer drifts from −maxdrift to +maxdrift with `maxdrift=4`, refines by ±0.5 Hz, and outputs `(int)drift`. So the database "drift" is the total frequency change in Hz across the ~110.6 s transmission. WSJT-X displays label it "Hz/min", and wspr.live lists the unit as unknown. The frequency grid uses df = 375/256/2 ≈ 0.73 Hz bins. — [wsprd.c](https://raw.githubusercontent.com/saitohirga/WSJT-X/master/lib/wsprd/wsprd.c); [wspr.live schema notes](https://wspr.live/)
- The wspr.live schema stores `snr` as Int8 in dB (so 1 dB quantisation) and `drift` as Int8 with "unit unknown, possibly Hz". Latitude/longitude are the centre of the Maidenhead locator box. — [wspr.live](https://wspr.live/)

**Forward-scatter and bistatic scattering theory**
- Peak forward-scatter RCS is σ_FS = 4πA²/λ², where A is the silhouette (projected) area. This holds when the target is much larger than λ and is independent of material (Babinet's principle). The forward-scatter lobe width is θ_FS ≈ Kλ/D with K ≈ 1. Forward-scatter geometry "gives good detection but poor localization," and a target on the baseline produces no measurable range delay. — [RF Essentials glossary: bistatic cross-section](https://rfessentials.com/resources/rf-glossary/bistatic-cross-section/); [US Patent 12710505 (USPTO)](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/12710505); [MiGFlug Afterburner article, quoting H. Griffiths](https://migflug.com/afterburner/forward-scatter-radar-babinet-principle-stealth-fence/)
- At HF, manned aircraft sit in the Mie (resonance) regime at 10–60 m wavelengths, and the whole airframe contributes to RCS. A generic aircraft RCS is dominated by the vertical stabiliser at low HF and by the fuselage at higher HF for broadside incidence. Most military HF targets have RCS between a few m² and more than 1000 m² (~0–30+ dBsm). — [Turkish J. Elec. Eng. (TÜBİTAK) 2010 paper, vol. 18 no. 3; one of two PDFs returned by search, attribution between them not verified](https://aj.tubitak.gov.tr/elektrik/issues/elk-10-18-3/elk-18-3-8-0912-7.pdf)

**Published link budgets for the MH370 WSPR claim**
- Victor Iannello's Case 1 (Dec 2021) uses the path HB9CZF (Switzerland) → VK1CH (Canberra): 16,527 km at 14.097 MHz with 1 W. MH370 is placed at FL350, 9,868 km from the transmitter and 6,660 km from the receiver, giving about 5 hops. He takes the direct signal as about −110 dBm (free space) and λ = 21.3 m. The 777-200ER forward-scatter RCS is estimated at 18,791 m², about 23× the projected area. The resulting forward-scattered signal is about −210 dBm, roughly 100 dB below direct. Computed S/N is −81 dB against a required ~−30 dB, about 51 dB short. — [Iannello, "WSPR Can't Find MH370", radiantphysics, 19 Dec 2021](https://mh370.radiantphysics.com/2021/12/19/wspr-cant-find-mh370/)
- Iannello's Case 2 checks the same method against measurements by DK8OK (Nils Schiffhauer). The source is China Radio International at 17.530 MHz, 250 kW, 25 dBi, about 7,600 km away. The carrier measured −59.1 dBm, average Doppler scatter −105.9 dBm and noise −108 dBm. The calculation, using a B737 at about 2.2 km slant range, gives about −102 dBm for the scatter, within ~4 dB of the measurement. The scatter is about 47 dB below the carrier, appearing as Doppler sidebands about 5–20 Hz below the carrier. — [Iannello 2021](https://mh370.radiantphysics.com/2021/12/19/wspr-cant-find-mh370/)
- Iannello cites Steve Kent's paper, which "formally treats skywave propagation and scatter off airplanes" and concludes "insufficient signal strength (by many orders of magnitude)" for WSPR to detect aircraft over long distances. I did not read the paper itself; it is linked at Google Drive `1qO5ECvaJEjC-tyS85BBS67EfTsB7N8vU`. — [Iannello 2021](https://mh370.radiantphysics.com/2021/12/19/wspr-cant-find-mh370/); [Kent paper (Drive link, not read)](https://drive.google.com/file/d/1qO5ECvaJEjC-tyS85BBS67EfTsB7N8vU/)
- DK8OK draws on years of observing aircraft scatter on shortwave broadcast carriers (about 30 Doppler tracks). He finds the effect on overall signal level is "almost always well below 0.3 dB". He also notes that "level changes of 30 dB within seconds are common on shortwave." — [rtl-sdr.com summary of DK8OK](https://www.rtl-sdr.com/nils-critiques-the-mh370-wspr-aircraft-scatter-theory/); original: [dk8ok.org 2021-12-06](https://dk8ok.org/2021/12/06/mh370-and-wspr-aircraft-scatter-on-hf-a-critical-review/)
- Iannello (2025) says that in his experiments with Schiffhauer, scatter "could only be detected when the direct signal was extremely strong (transmitter power with hundreds of kilowatts)" and "the aircraft was fairly close (tens of kilometers) from either the transmitter or receiver." — [Iannello, "Update on the Search for MH370", 31 Mar 2025](https://mh370.radiantphysics.com/2025/03/31/update-on-the-search-for-mh370/)
- Joe Taylor (K1JT, WSPR's author) is quoted: "I do not believe that historical data from the WSPR network can provide any information useful for aircraft tracking." — [Iannello 2021](https://mh370.radiantphysics.com/2021/12/19/wspr-cant-find-mh370/)

### Inferences

**[INFERENCE] Equations used** (my working; standard bistatic radar forms)
- Direct (free-space) power: P_d = P_t·G_t·G_r·λ² / ((4π)²·R²).
- Bistatic scattered power: P_s = P_t·G_t·G_r·λ²·σ_b / ((4π)³·R_1²·R_2²).
- Their ratio: **P_s/P_d = σ_b·R² / (4π·R_1²·R_2²)**. R is the TX–RX path length, R_1 is TX–aircraft and R_2 is aircraft–RX. To first order, ionospheric absorption and focusing apply to both paths; the scattered path pays extra hop losses if it does not coincide with the direct ray, so this is optimistic for the scatter.
- Shadow/Babinet form for an aircraft on the baseline: |E_s/E_d| ≈ A·R/(λ·R_1·R_2). The first Fresnel-zone radius is r_F = √(λ·R_1·R_2/R).
- Largest possible change in reported SNR (coherent, in-phase scatter): ΔSNR_max = 20·log10(1 + √(P_s/P_d)). A 1 dB change needs amplitude ratio 0.122, i.e. P_s/P_d ≥ −18.3 dB. A 0.5 dB change needs −24.5 dB; 3 dB needs −7.7 dB.

**[INFERENCE] Assumed numbers**
- 777-200ER dimensions: length ~63.7 m, wingspan ~60.9 m, wing area ~428 m². These are standard published values, not re-verified this session.
- Silhouette A = 100–800 m², depending on aspect (skywave arrives from 5–30° elevation, so the projected area mixes planform and side area).
- At 14.097 MHz (λ = 21.27 m), σ_FS = 4πA²/λ² gives 24.4 dBsm (A = 100 m²), 34.0 dBsm (300 m²), 38.4 dBsm (500 m²) and 42.5 dBsm (800 m²). Iannello's 18,791 m² (42.7 dBsm) implies A ≈ 824 m², i.e. near-planform. The 777 is only 1.5λ long at 7 MHz and 3λ at 14 MHz (resonance regime), so the optical formula is an upper-end estimate. The forward lobe is about 38° wide at 7 MHz, 19° at 14 MHz and 10° at 28 MHz.

**[INFERENCE] Computed ratios.** Output of `physics.py`. σ is 20, 30, 40 or 42.7 dBsm; the parenthesised figure is ΔSNR_max at 42.7 dBsm.

| Geometry | P_s/P_d at 20 / 30 / 40 / 42.7 dBsm | ΔSNR_max |
|---|---|---|
| 4,000 km link, aircraft at midpoint | −111 / −101 / −91 / −88 dB | 0.0003 dB |
| 4,000 km link, aircraft 40 km from TX (where a ~10–15° ray is at ~10 km altitude) | −83 / −73 / −63 / −60 dB | 0.008 dB |
| 4,000 km link, aircraft 10 km from TX | −71 / −61 / −51 / −48 dB | 0.033 dB |
| 16,527 km HB9CZF→VK1CH, aircraft at 9,868 / 6,660 km | −123 / −113 / −103 / −100 dB | 0.00008 dB (Iannello got ~−100 dB) |
| 252 km W8AC→N8GA "short-distance" link, aircraft at midpoint | −87 / −77 / −67 / −64 dB | 0.005 dB |
| 252 km link, aircraft 20 km from TX | −76 / −66 / −56 / −54 dB | 0.018 dB |

**[INFERENCE] Shadow/Fresnel view** (A = 400 m², 14 MHz)

| Geometry | \|E_s/E_d\| | ΔSNR_max | First Fresnel radius r_F | Time to cross r_F at 250 m/s |
|---|---|---|---|---|
| 4,000 km link, midpoint | 1.9×10⁻⁵ | 0.00016 dB | 4.6 km | 37 s |
| 4,000 km link, 10 km from TX | 1.9×10⁻³ | 0.016 dB | 0.46 km | 4 s |
| 252 km link, midpoint | 3.0×10⁻⁴ | 0.0026 dB | 1.2 km | 9 s |

Both methods agree: a 1 dB change would need the aircraft within roughly 100 m of an antenna. Even then, the crossing lasts seconds while each SNR value is a 110.6 s average, which dilutes the effect further.

**[INFERENCE] Ray-geometry objection to "great-circle tripwires".** On a skywave link the ray is below airliner altitude (~12 km) only in short segments near the TX, the RX and each ground-reflection point. Using h ≈ x·tanΔ + x²/(2R_e):
- the ray reaches 10 km altitude about 105 km from the ground point at elevation Δ = 5°, and about 55 km at Δ = 10°;
- so on a ~3,500 km F-layer hop, only about 3–6% of the great-circle length lies at aircraft altitudes;
- the other ~95% is 100–350 km up, where an aircraft cannot sit in the ray.

Treating every point on the great circle as a "tripwire" is therefore not physical. Off-great-circle propagation (ionospheric tilts) and Maidenhead locator uncertainty (4-character squares are 1°×2°) add further position error.

**[INFERENCE] Doppler versus WSPR resolution**
- The bistatic Doppler of the scattered component is f_D = (V/λ)·[cos θ_T + cos θ_R], with a maximum of 2V/λ. At V = 250 m/s that maximum is 11.7 Hz (7 MHz), 16.9 Hz (10 MHz), 23.5 Hz (14 MHz), 30 Hz (18 MHz), 35 Hz (21 MHz) and 47 Hz (28 MHz).
- Off the forward direction, the scatter therefore usually falls outside the 5.9 Hz WSPR signal band and the decoder's 7-bin (~5 Hz) peak smoothing. It would show up only as a separate, very weak spectral line, tens of dB below the −31 dB decode threshold, and it does not enter the decoded spot's SNR or drift. This is the opposite of what the hypothesis needs.
- In exact forward geometry the Doppler tends to 0 and the scatter adds coherently, but the shadow estimate above already caps its effect at ≤0.03 dB.
- Reported drift is the drift of the dominant (direct) component, fitted over 162 symbols. A component 50–100 dB weaker cannot move a frequency fit quantised to 1 Hz. **[INFERENCE] Physics predicts zero drift anomalies attributable to aircraft.**

**[INFERENCE] Noise floor context.** Thermal kTB in 2,500 Hz is −140 dBm. HF external noise is typically 20–50 dB higher; Iannello measured −102 dBm on his antenna. Even with a perfect receiver, scatter at −160 to −210 dBm cannot be seen in a 2,500 Hz-referenced SNR.

### Gaps
- I did not read Steve Kent's paper directly (Google Drive). Its numbers are known only through Iannello's summary.
- I found no measured HF (3–30 MHz) RCS for a Boeing 777 or any wide-body airliner in open literature. The 20–43 dBsm range is a modelling assumption.
- I did not retrieve a primary citation for Glaser's forward-scatter RCS derivation; the formula is cited via secondary references.
- No numerical (NEC/FEKO) model of a 777 in the HF resonance region was found.

---

## Q2. Comparison with HF passive radar and OTH radar literature

### Takeaway
Purpose-built HF systems do detect aircraft, but only with large transmit power and arrays (e.g. JORN, about 560 kW), or by using megawatt-class broadcast stations with coherent Doppler processing over many seconds and suppression of the direct-path signal. WSPR provides none of this. It sends 0.2–5 W from simple antennas, with no phase or Doppler record and no direct-path cancellation, and its only output is one quantised SNR value per 2 minutes.

### Cited Findings
- JORN's transmit arrays at Longreach and Laverton have 28 elements, each driven by a 20 kW amplifier, giving 560 kW total. The arrays are about 1 km long. JORN is expected to detect air objects "equivalent in size to a BAe Hawk-127 aircraft or larger", and its range is about 1,000–3,000 km. — [Wikipedia: Jindalee Operational Radar Network](https://en.wikipedia.org/wiki/Jindalee_Operational_Radar_Network)
- HF skywave OTH radars face "exceptionally high levels of clutter from the earth's surface". A DSTO estimate puts typical HF RCS for a fighter or small vessel at about 20–25 dBsm. This was seen as a search abstract only; full text not read. — [TÜBİTAK 2010 / search summary](https://aj.tubitak.gov.tr/elektrik/issues/elk-10-18-3/elk-18-3-8-0912-7.pdf)
- The University of Adelaide project "Exploiting HF Emitters of Opportunity for OTH Radar" reports targets "detected passively using AM radio broadcast in an OTH radar context". The illuminators are high-power broadcast stations, not low-power beacons. — [Adelaide projects wiki 2014S1-50](https://projectswiki.eleceng.adelaide.edu.au/projects/index.php/Projects:2014S1-50_Exploiting_HF_Emitters_of_Opportunity_for_OTH_Radar)
- DK8OK's CRI example shows aircraft scatter from a 250–500 kW, 25 dBi broadcast transmitter as Doppler sidebands about 47 dB below the carrier. The aircraft was only ~2 km away, and the sidebands were visible only in high-resolution waterfall processing. — [Iannello 2021](https://mh370.radiantphysics.com/2021/12/19/wspr-cant-find-mh370/); [rtl-sdr.com](https://www.rtl-sdr.com/nils-critiques-the-mh370-wspr-aircraft-scatter-theory/)

### Inferences
- **[INFERENCE] Power gap.** JORN (560 kW, high-gain arrays) has about 50–60 dB more transmit power than a 1 W WSPR beacon (+57.5 dB), before counting array gain. Broadcast-based passive radar (100–500 kW) is about 50–57 dB above a 1 W beacon.
- **[INFERENCE] Processing gap.** Passive radars recover targets 40–100 dB below the direct signal through coherent integration (cross-ambiguity over seconds to tens of seconds) and adaptive cancellation of the direct path. WSPR keeps none of the needed raw data (I/Q, phase); the database holds one quantised SNR, one frequency and one integer drift per 2-minute slot.
- **[INFERENCE] Direction of the effect.** Professional systems find aircraft by separating the Doppler-shifted echo from the direct signal. The WSPR hypothesis instead assumes the echo changes the direct signal's own SNR and drift, which is exactly what radar designers suppress and what physics says is negligible.

### Gaps
- Search-engine abstracts named several HF passive radar papers, but I did not retrieve their full texts, coherent integration times or direct-path suppression figures. They should be cited only after verification:
  - Fabrizio et al., IEEE RadarCon 2015: AM-broadcast OTH passive radar, aircraft "at ranges of thousands of kilometers";
  - Underhill 2013: DRM-based detection to ~1,500 km;
  - Thomas, Baker & Griffiths, IET 2007: DRM ambiguity functions;
  - Wan/Zhao (Wuhan): DRM HF passive bistatic radar.
- Fabrizio's book *High Frequency Over-the-Horizon Radar* (McGraw-Hill, 2013) is the standard reference but was not accessed.

---

## Q3. Natural variability of WSPR SNR and drift

### Takeaway
Ionospheric fading, multipath and receiver-noise changes move WSPR SNR by several dB from slot to slot. In my own queries the SD of consecutive SNR differences on the same link is about 3.5–4.7 dB at 2-minute lag and about 5 dB at 10–30 minute lag. About 40–55% of consecutive spot pairs differ by ≥3 dB. Drift is 0 in 75–84% of spots, ±1 in 11–22%, and |drift| ≥ 2 in 2–3%. Any "anomaly" threshold of 1–3 dB is therefore crossed constantly by chance.

### Cited Findings
- Frissell et al. (2014), "Ionospheric sounding using real-time amateur radio reporting networks", *Space Weather* 12(12): 651–656. It establishes RBN, PSKReporter and WSPR as ionospheric remote-sensing tools and shows a sharp drop in path counts after an X2.9 flare. — [SRI publication page](https://www.sri.com/publication/information-computer-science-pubs/ionospheric-sounding-using-real-time-amateur-radio-reporting-networks/); [NJIT](https://researchwith.njit.edu/en/publications/ionospheric-sounding-using-real-time-amateur-radio-reporting-netw/)
- Griffiths (G3ZIL), HamSCI 2024: SNR, "the only measurements from modes WSPR, FT8 etc., can be a compromised proxy for signal level when noise level varies." FST4W spread measurements identified one-hop propagation by a frequency spread under 100 mHz, with mixed one- and two-hop paths showing higher spread. — [Griffiths HamSCI 2024 slides](https://hamsci.org/sites/default/files/pages/hamsci_workshop_2024/orals/O11_Gwyn_Griffiths_G3ZIL.pdf)
- Griffiths et al. (TAPR DCC 2022): at 2 Hz Doppler spread, FST4W-120 decodes at −24 dB while WSPR needs −17 dB. "With WSPR we cannot say whether failure to decode a spot was due to inadequate SNR or excess spectral spread." — [TAPR DCC 2022 paper](https://web.tapr.org/tech_docs/DCCpapers/2022%2002.pdf)
- Gerzoff & Griffiths (HamSCI 2025, "Short Term Variability") modelled reported WSPR SNR against noise differences by hour, month and path length. The patterns they found accounted for only a "(very) small" share of the variation, i.e. most short-term SNR variability is unexplained by those regressors. — [Gerzoff HamSCI 2025](https://hamsci.org/sites/default/files/pages/hamsci_workshop_2025/orals/O17_Gerzoff_2025%20Short%20Term%20Variablity%20Presentation%20Final.pdf)
- DK8OK: "level changes of 30 dB within seconds are common on shortwave." — [rtl-sdr.com](https://www.rtl-sdr.com/nils-critiques-the-mh370-wspr-aircraft-scatter-theory/)
- On the MH370 HB9CZF→VK1CH link, about 16 hours of spots (graphed by Exner and Ulich) show the spot flagged at 17:16 UTC lying within the normal scatter, with ordinary frequency and drift. A commenter (Mick Gilbert, comment not article) found the flagged SNR (−20) and drift (−1) equal to the 48-hour mean/mode over 69 spots. — [Iannello 2021](https://mh370.radiantphysics.com/2021/12/19/wspr-cant-find-mh370/)

**My wspr.live measurements** (this session; scripts `wspr_var.py`; source [wspr.live](https://wspr.live/)). Method: same (tx, rx, band) triple, bands 80–10 m, deduplicated by timestamp, consecutive spots at the given lag.

2014-03-07 16:00 to 2014-03-08 01:00 UTC (all bands):

| Lag | n | SD of ΔSNR | Median \|Δ\| | 5–95% range | Fraction \|Δ\| ≥ 3 dB |
|---|---|---|---|---|---|
| 2 min | 1,299 | 4.06 dB | 2 dB | −6 to +6 | 0.41 |
| 2 min, links >1,000 km | 819 | 3.46 dB | — | — | 0.39 |
| 10 min | 16,301 | 4.81 dB | — | — | 0.51 |
| 30 min | 1,800 | 5.23 dB | — | — | 0.55 |

- In 30-minute windows with ≥5 spots, the median within-window SNR SD is 2.56 dB for links >1,000 km (90th percentile 4.62 dB) and 2.10 dB for links ≤1,000 km.
- Drift distribution: 0 → 75.3%, ±1 → 21.7%, ±2 → 2.0%, ±3 → 0.9%, ±4 → 0.15%.

2025-03-07 16:00–18:00 UTC, 20 m only:

| Lag | n | SD of ΔSNR | Fraction \|Δ\| ≥ 3 dB |
|---|---|---|---|
| 2 min | 26,655 | 4.65 dB | 0.46 |
| 10 min | 22,943 | 5.00 dB | 0.51 |

- The 30-minute-window SNR SD median is 2.67 dB for links >1,000 km.
- Drift: 0 → 84.0%, ±1 → 10.7%, |drift| ≥ 2 → 5.2%.

On MH370 night, the 7th-arc-crossing link HB9CZF→VK6ZRY on 14.097 MHz had 10 spots between 20:56 and 23:06 UTC. SNRs were −25, −24, −24, −25, −25, −26, −25, −22, −26, −25, drift was −1 every time, and frequency was 14,097,074–079 Hz. **[INFERENCE]** The +3 dB excursion at 22:46 is a 1-in-10 event, entirely ordinary given the statistics above.

### Inferences
- **[INFERENCE]** Per-spot SNR noise is about SD(Δ)/√2 ≈ 2.5–3.3 dB. With 1 dB quantisation (adding only ~0.29 dB RMS), a 0.01–0.03 dB physical effect sits 2 orders of magnitude below the per-spot noise.
- **[INFERENCE]** About 40–55% of consecutive spot pairs differ by ≥3 dB. Any rule that calls a ≥1–3 dB SNR change, or a drift ≠ 0, an "anomaly" will flag a large share of all slots (about 16–25% for drift and roughly half for a ≥3 dB SNR change). The prior probability of an "anomaly" is high regardless of aircraft.
- **[INFERENCE]** Variability is non-stationary. It depends on time of day, greyline, band and path length, and on the receiver's noise (SNR = signal/noise). A valid test must model these confounds or match on them (same link, same time of day, nearby slots).

### Gaps
- I found no peer-reviewed paper giving a published distribution of WSPR SNR fading statistics (e.g. a slot-to-slot SD by band and path length). My numbers come from two samples, a 9-hour window in 2014 and a 2-hour 20 m window in 2025, and should be extended (different seasons and solar conditions).
- WSPR transmitters usually run about 20% duty cycles, so 2-minute-lag pairs come mainly from 100%-duty or multi-band stations. This may bias the 2-minute statistics.

---

## Q4. Published tests of aircraft detection with WSPR or similar beacon data

### Takeaway
No peer-reviewed, blinded, controlled test of WSPR aircraft detection exists in the sources I found. Proponent material (Godfrey, Coetzee, Maskell; Westphal) consists of self-published reports and conference posters that search for anomalies with the aircraft position already known. The proponents' own headline statistic, a cruise-phase AUROC of about 0.59–0.60 on 70 observations, has a confidence interval that includes 0.5. A 2022 Qantas validation test was called "not scientific" by its own validator. The University of Liverpool's announced 2024 study of other 777 flights had no published results in what I found.

### Cited Findings
- Godfrey and Coetzee use GDTAAA ("Global Detection and Tracking of Any Aircraft Anywhere") on WSPRnet data. Cruise-phase ROC analysis "used 70 observations", and the "area under the curve increases from 58.66% to 60.43%" depending on whether duplicates are kept. Critics (Iannello) said that with discarded data included, the true positive rate stays near 52% while the false positive rate rises from 37% to 44%, calling it "junk science". Mick Gilbert graded the AUROC an "F". Godfrey cited Maskell: "the report is logical and statistically correct." — [AirlineRatings, "Critics of WSPRnet tracking MH370 been answered" (proponent-aligned outlet)](https://www.airlineratings.com/news/critics-of-wsprnet-tracking-mh370-been-answered/)
- Short-distance paper by Godfrey, Coetzee and Maskell, "How does WSPR detect Aircraft over short Distances?" (Dec 2023). The link was W8AC → N8GA (252 km, "short ionospheric propagation") on 3 Nov 2023. It reports 9 commercial flights, 8 detected, 13 SNR anomalies and 2 drift anomalies. The article does not state SNR magnitudes, transmit power, controls or blinding. — [AirlineRatings, "Revolutionary MH370 tracking proven over short distances"](https://www.airlineratings.com/news/revolutionary-mh370-tracking-proven-over-short-distances/)
  - A commenter reports that PDF "has been deleted from DropBox".
  - Mick Gilbert (comment) says the paper used selective flight data.
  - Source for both: [Iannello 2025 comments](https://mh370.radiantphysics.com/2025/03/31/update-on-the-search-for-mh370/)
- Qantas validation test (2021–22): validator Mike Glynn, a former Qantas captain, said "my opinion remains that the test process was not scientific." The proponent "declined another test". Iannello writes that the tests "were not scientifically rigorous" and that positive results reflected cherry-picked data. — [Iannello, radiantphysics, 11 Aug 2022](https://mh370.radiantphysics.com/2022/08/11/wspr-tracking-validator-now-believes-testing-was-not-scientific/)
- University of Liverpool (6 Mar 2024): Prof. Simon Maskell, Alberto Acuto, Paul Horridge and Shashi Lakra "are analysing other Boeing 777's flights, for which the trajectories are known, and the associated WSPR data." — [Univ. of Liverpool news](https://news.liverpool.ac.uk/2024/03/06/university-researchers-provide-statistical-expertise-to-help-locate-mh370/)
  - In March 2025 Iannello wrote: "Years have gone by, and they have not run those basic experiments to demonstrate the physical principles." — [Iannello 2025](https://mh370.radiantphysics.com/2025/03/31/update-on-the-search-for-mh370/)
  - A Maskell-group Cessna (OE-FGR) case study reportedly used 183 observations and 119 unique Tx-Rx-frequency triples (secondary report, via search summary). — [mh370search.com](https://www.mh370search.com/?p=1266)
- Westphal (DJ4FF), HamSCI 2021 poster "'Geocaching' in the Ionosphere":
  - claims WSPR detections of aircraft in Antarctica up to 7,600 km (DP0GVN → ZL2005SWL), using Flightradar24 as reference;
  - says "we are in need of a validation process" and that "more ADS-B data … is a need for reference to avoid false alarms";
  - describes shapes of non-decoded KiwiSDR waterfall signals, not WSPR database statistics;
  - claims MH370 WSPR data "indicate the U-turn at 17:22 h UTC";
  - describes no controls or blinding.
  — [Westphal HamSCI 2021 PDF](https://hamsci.org/sites/default/files/publications/2021_HamSCI/20210320_1700z-Robert_Westphal_DJ4FF.pdf)
- A Singapore DSTA student report, "Forward Scatter Aircraft Detection with Amateur Radio Network WSPRnet", cites an earlier study saying "WSPR is a noisy sensor with an area under receiver operator characteristics curve (AUC) of approximately 60%". The full text returned HTTP 403, so only the search snippet was seen. — [DSTA report PDF](https://www.dsta.gov.sg/staticfile/ydsp/projects/files/reports/Report%20-%20Forward%20Scatter%20Aircraft%20Detection%20with%20Amateur%20Radio%20Network%20WSPRnet.pdf)
- A 2024 MH370 commenter notes that "proponents of WSPR don't seem to be able to provide examples of tracked aircraft" where the track was not already known. — [Iannello 2025 comments](https://mh370.radiantphysics.com/2025/03/31/update-on-the-search-for-mh370/)

### Inferences
- **[INFERENCE] The reported AUC is not significant.** For AUROC = 0.6043 with 70 observations, the Hanley–McNeil SE is about 0.068–0.077 depending on class split (35/35: 95% CI 0.47–0.74; 20/50: 0.45–0.76). This does not exclude AUC = 0.5 (no skill), even before correcting for selection of links and thresholds.
- **[INFERENCE] The claimed effect size contradicts the physics.** An AUC of 0.60 under an equal-variance Gaussian model corresponds to d′ ≈ 0.36, i.e. a mean shift of about 1.2 dB on a 3.3 dB per-spot SD. Physics predicts ≤0.03 dB (d′ ≤ 0.01, AUC ≤ 0.503). A real AUC of 0.6 would mean the bistatic radar equation is wrong by 30–100 dB. The parsimonious explanation is selection bias or look-elsewhere effects.
- **[INFERENCE] The existing designs are unblinded.** In all of them, the analyst knows the aircraft track when choosing which links, slots and anomaly definitions count. That is the classic setting for confirmation bias, so the decisive missing experiment is a blinded one (Q6).

### Gaps
- I could not access the full DSTA report, the deleted short-distance PDF, Godfrey's 2022–2023 reports, or any Liverpool output. Their exact methods and sample sizes are unverified.
- I found no arXiv, IEEE or Radio Science paper testing WSPR aircraft detection against ADS-B.

---

## Q5. WSPR coverage on 7–8 March 2014 (live wspr.live queries)

### Takeaway
On MH370 night the global WSPR network was sparse: about 9,000–17,000 spots per hour and about 230–280 active transmitters worldwide. The Indian Ocean region had only three genuine transmitters and three receivers (Bangkok, Singapore, Perth). Only 11 spots on 2 links had short-path great circles crossing a broad southern 7th-arc box (40–20°S, 85–105°E), and none did after 23:06 UTC. The final arcs (00:11 and 00:19 UTC) therefore have no short-path WSPR "tripwires" in that box. Allowing long-path geometry inflates the candidate set enormously, a strong look-elsewhere hazard.

### Cited Findings

All counts are from queries run this session against `https://db1.wspr.live/` (database `wspr`, table `rx`). [wspr.live](https://wspr.live/) notes that the data are raw from wsprnet.org and "there might be duplicates, false spots and other errors".

**Hourly totals, all bands, worldwide**

| Hour (UTC) | Spots | Unique TX | Unique RX |
|---|---|---|---|
| 07 Mar 16:00 | 17,093 | 269 | 256 |
| 17:00 | 15,878 | 272 | 271 |
| 18:00 | 13,641 | 280 | 279 |
| 19:00 | 11,645 | 258 | 267 |
| 20:00 | 11,620 | 265 | 268 |
| 21:00 | 10,939 | 254 | 270 |
| 22:00 | 9,743 | 242 | 244 |
| 23:00 | 9,864 | 233 | 240 |
| 08 Mar 00:00 | 8,857 | 233 | 228 |

- Window total (16:00–01:00 UTC): 109,280 spots.
- Daily totals: 280,882 spots (595 TX, 590 RX) on 2014-03-07 and 276,004 (662 TX, 656 RX) on 2014-03-08. For comparison, 2025-03-07 had 7,827,129 spots, 4,947 TX and 1,696 RX, about 28× more.
- Window spots by band code: 20 m (14) 30,482; 10 m (28) 29,281; 30 m (10) 27,459; 40 m (7) 7,993; 160 m (1) 4,680; 80 m (3) 3,493; 630 m (0) 1,928; 15 m (21) 2,078; 12 m (24) 185; 17 m (18) 381. The rest were LF/6 m/2 m.

**Stations located in the Indian Ocean / SE Asia box** (lat 50°S–30°N, lon 40–120°E): 678 spots (0.6% of the window), 35 TX signs and 63 RX signs involved.
- Genuine transmitters in the box: HS0ZKM (Bangkok, OK03gr; 442 spots; 20 m and 10 m), 9V1TD (Singapore, OJ11wi; 22 spots; 40 m) and VK6EZ (Perth, OF78vd; 20 spots; 30 m).
- Six other in-box TX callsigns appear exactly once at mid-ocean grid centres (DN3IFG NF68, U92ZKM LE47, XT9ESZ OG06, P59ACL NJ78, VR3YBO OF81, 7F1GVA LL19). **[INFERENCE]** These are almost certainly false decodes. Across the whole window, 54 TX signs appear only once.
- Receivers in the box: HS0ZKM (107 spots), VK6ZRY (Perth OF78vd; 58 spots; 20 m) and 9V1TD (24 spots).

**Short-path great-circle crossings** (TX signs seen ≥3×; script `wspr_cov.py`)
- **SIO 7th-arc box (40–20°S, 85–105°E): 11 spots on 2 links, all 20 m.**
  - HB9CZF (JN47ch) → VK6ZRY (OF78vd), 13,809 km: 10 spots, 20:56–23:06 UTC.
  - VK3DXE → EA7JKC, 17,058 km: 1 spot, 16:16 UTC.
  - By hour: 16h 1, 20h 1, 21h 4, 22h 4, 23h 1, 00h **0**.
- Broad Indian Ocean box (45°S–10°N, 70–115°E): 543 spots on 114 tx-rx-band links. Bands: 20 m 375, 40 m 153, 10 m 9, 80 m 3, 160 m 3. By hour 16–00: 39, 48, 50, 63, 211, 108, 14, 2, 8.
- Malacca/Andaman box (0–15°N, 90–105°E): 956 spots on 162 links. HS0ZKM paths to Japan, Europe, North America and Australia dominate. By hour 16–00: 104, 123, 121, 135, 281, 140, 27, 9, 16.

**Long-path great-circle crossings of the SIO box** (script `wspr_lp.py`)
- With no distance restriction: 53,301 spots (about half of all spots) on 7,366 links. This includes physically implausible cases, e.g. WB8ELK→W3GXT at 1,052 km.
- Restricted to links ≥12,000 km: 731 spots on 205 links. Restricted to ≥15,000 km: 387 spots on 105 links. Most are US–VK/ZL on 10 m and 20 m, concentrated 21:00–00:59 UTC.

**MH370 timeline for alignment:** departure ~16:42 UTC; final primary radar 18:22:12 UTC; satellite log-on 18:25:27 UTC; 7th-arc log-on request 00:19:29 UTC (acknowledged 00:19:37); no response to 01:15 UTC handshakes. — [Journal of Navigation (Cambridge) paper, "Final two MH370 communications suggest controlled eastward descent"](https://resolve.cambridge.org/core/services/aop-cambridge-core/content/view/3B8A244FB86B058D36A406BE6EB17345/S0373463324000262a.pdf/final-two-mh370-communications-suggest-controlled-eastward-descent.pdf)

### Inferences
- **[INFERENCE]** The short-path data offer essentially no "tripwire" coverage of the southern 7th arc in the last hour of flight. The 7th-arc time (00:19 UTC) has no short-path coverage in the 40–20°S, 85–105°E box at all, so any end-point claim there relies on long-path or skewed-path interpretations.
- **[INFERENCE]** Long-path interpretation is a large researcher degree of freedom. Admitting long paths for links of any length turns about half of the planet's spots into "candidate" SIO detections. Even restricted to ≥15,000 km links, it adds about 35× the short-path candidates. A blind test must fix the path model (short path only, or long path only above a stated distance) in advance.
- **[INFERENCE]** 2014 coverage was about 1/28 of 2025 levels. A method validated on dense modern data would not transfer directly to 2014 densities. Validation data should be thinned to 2014-like link density for an honest analogue.

### Gaps
- My boxes are coarse rectangles. A proper analysis would use the official 7th-arc polyline and buffer widths.
- Great circles were computed between Maidenhead square centres. Locator precision (4 vs 6 characters) was not modelled, and ionospheric off-great-circle propagation was not modelled.

---

## Q6. Blind test design using only free public data

### Takeaway
A decisive test is feasible with free data: wspr.live (WSPR spots, SQL over HTTP, no sign-up, non-commercial terms) and adsb.lol daily archives (ODbL, free, about 1.8–2.1 GB per day from 2023). Its core features:
- pre-registered anomaly definitions;
- labels kept from the analyst (a commit-reveal hash, or a third party);
- matched control slots and time-shifted decoy tracks;
- AUC with a permutation null and correction for multiple comparisons;
- a track-recovery task that hands the method real and decoy flights.

Physics predicts AUC ≈ 0.50. The proponents' implied effect (AUC ≈ 0.6, d′ ≈ 0.36) would be confirmed or refuted with a few hundred crossing events.

### Cited Findings

**WSPR data access ([wspr.live](https://wspr.live/))**
- Endpoint: `https://db1.wspr.live/` (also `http://db1.wspr.live:80/`), ClickHouse SQL via the `?query=` GET parameter. POST is not accepted and other parameters are stripped.
- Database and table: `wspr.rx`, with columns id, time, band, rx_sign, rx_lat, rx_lon, rx_loc, tx_sign, tx_lat, tx_lon, tx_loc, distance, azimuth, rx_azimuth, frequency, power, snr, drift, version, code (verified with `DESCRIBE` this session).
- Rate limit: 20 requests/minute since 29 Oct 2023.
- Terms: "You are allowed to use the services provided on wspr.live for your own reasearch and projects"; "You are not allowed to use this service for any commercial or profit oriented use cases"; no warranties.
- Recommended practice: always filter by time and band; avoid JOINs.
- The `code` mode mapping changed on 2023-01-16 (WSPR-2 vs FST4W variants). Known data incidents include a July 2024 re-import loss, a November 2024 period when only wsprdaemon data was returned, and an October 2025 frequency fix.
- The database covers "all spots ever reported to wsprnet.org". This session saw spots back to 2008, and 161,174,760 rows before 2014.

**ADS-B ground truth ([adsb.lol historical docs](https://www.adsb.lol/docs/open-data/historical/))**
- Daily GitHub releases per instance (readsb-prod-0, prod-1, staging-0). Format: readsb gzip JSON, with `traces/` (one file per aircraft per day) and `heatmap/`.
- Multipart releases are rejoined with `cat … .tar.aa … .tar.ab | tar -xf -`. Licence: ODbL 1.0 ("use it freely, just keep it open"). Record schema: [readsb README-json, trace JSONs](https://github.com/wiedehopf/readsb/blob/dev/README-json.md#trace-jsons).
- Repositories (GitHub API, this session): [adsblol/globe_history_2023](https://github.com/adsblol/globe_history_2023) (created 2023-03-08; earliest releases include a 2023-02-16 test-0 tag and prod-0 from 2023-03-10), [globe_history_2024](https://github.com/adsblol/globe_history_2024) and [globe_history_2025](https://github.com/adsblol/globe_history_2025), all ODbL-1.0.
- Sizes (GitHub API, this session): v2024.12.30-planes-readsb-prod-0 is 2,000 MB (`.tar.aa`) + 70 MB (`.tar.ab`). v2023.08.25 prod-0 and prod-1 are about 1.83–1.84 GB each (single `.tar`). So expect about 2 GB per day per instance.
- Downloads use the standard GitHub release-asset URL pattern `https://github.com/adsblol/globe_history_2024/releases/download/<tag>/<asset>`. No sign-up is needed.
- OpenSky historical data requires an application, so it is excluded per the constraints.

### Inferences

All of the following is **[INFERENCE]**: my proposed protocol.

**A. Pre-registration (freeze before touching any labels)**
1. Hypotheses.
   - H1 (proponents): a WSPR spot whose link geometry is "crossed" by an airliner during its 110.6 s transmission has a higher anomaly score than matched uncrossed spots.
   - H0: no difference (AUC = 0.5).
   - Secondary: dose-response, where the anomaly score increases with the predicted physical coupling P_s/P_d from the bistatic equation in Q1.
2. Link selection, by rule, not by eye.
   - Take all (tx, rx, band) triples with ≥100 spots per day during the test period, on 7, 10 and 14 MHz.
   - Stratify by distance: <500 km, 500–3,000 km, 3,000–10,000 km, >10,000 km.
   - Require both endpoints' great-circle segments to fall inside regions with good adsb.lol coverage (e.g. Europe, CONUS), because over-ocean coverage from ground feeders is poor.
   - Also run a "2014-density" subsample: randomly thin the links to about 1/28 to mimic MH370-night density.
3. Crossing definition (exposure), fixed in advance.
   - An aircraft with altitude ≥ FL200 whose ADS-B track, interpolated to 1 s, comes within D km of the path's great circle at any time in [t₀ + 1 s, t₀ + 111.6 s]. D is pre-set to the proponents' preferred tripwire width (e.g. ±25 km) plus a physics variant: within r_F, and only in the "low-altitude ray" segments within about 100 km of TX, RX or hop reflection points.
   - Path model: short path only (primary); long path only if distance ≥ 15,000 km (secondary).
   - Uncrossed (control) slot: no aircraft within 10×D during the slot.
4. Anomaly scores, fixed in advance, preferably the proponents' own definitions. Defaults:
   - s₁ = |SNR_t − median(SNR on the same triple within ±30 min, excluding t)|;
   - s₂ = 1[drift_t ≠ the triple's modal drift over ±60 min];
   - s₃ = |frequency_t − median frequency within ±60 min| ≥ 2 Hz;
   - plus any multi-receiver or multi-band aggregation rule, written down exactly.
5. Primary endpoint: AUC of s₁ for crossed vs uncrossed slots, pooled across links with stratification by link. One-sided α = 0.05. Everything else is secondary with Holm correction. A max-statistic permutation (Westfall–Young) over all scores × bands × strata gives a look-elsewhere-corrected p-value.

**B. Blinding.** Two options:
- Commit-reveal: the ADS-B analyst computes crossing labels for every candidate slot and publishes only `SHA-256(labels.csv)`. The WSPR analyst then publishes anomaly scores (and their hash). The label file is revealed afterwards and anyone recomputes the AUC.
- Decoy-track (track-recovery) test: the WSPR method is given the spots plus a set of 2N candidate flight tracks. N are real; N are decoys made by shifting the same tracks by k×24 h ± U(−60, +60) min (preserving diurnal ionospheric and traffic cycles) or by rotating them about the link midpoint. The method must rank which tracks are real. A ROC is computed from the ranking.

**C. Controls and nulls**
1. Matched controls: the same triple, slots within ±1 h and the same day, with no aircraft. This controls ionosphere, receiver noise and TX power.
2. Time-shift null: recompute labels with ADS-B shifted by whole days (±1…±14 d) at the same time of day. AUC under these shifts is the empirical null distribution, giving a permutation p-value.
3. Placebo geometry: links sharing the same RX but with no aircraft on their path at that time.
4. Negative-control band/noise check: the same analysis on the receiver's reported noise (where wsprdaemon noise data exist) or on non-crossing links that share the same RX, to catch RX-side artefacts.
5. Positive-control sanity check: the pipeline must recover a synthetic injected anomaly (e.g. +1 dB on 10% of crossed slots) at the planned power.

**D. Sample size / power.** Per-spot SNR SD is about 2.5–3.3 dB (Q3). The number of crossed slots n needed for 80% power is n = ((z_α + z_β)·s/δ)².

| δ | s = 2.5 dB, α = 0.05 | s = 2.5 dB, α = 5×10⁻⁵ | s = 3.3 dB, α = 0.05 | s = 3.3 dB, α = 5×10⁻⁵ | Note |
|---|---|---|---|---|---|
| 1 dB | 39 | 140 | 67 | 244 | ≈ proponents' implied effect, AUC ≈ 0.6 |
| 0.5 dB | 155 | 560 | 269 | 975 | |
| 0.1 dB | 3,864 | 13,996 | 6,733 | 24,387 | |
| 0.01 dB | ~0.39 M | ~1.4 M | ~0.67 M | ~2.4 M | ≈ most favourable physics |

So a few hundred to ~1,000 crossing events decisively test the claimed effect. Testing the physically plausible effect is impractical, and systematic biases would dominate long before reaching it.

**Exposure availability.** In dense European or US airspace, a 1,000 km path segment will typically be crossed by several aircraft per 2-minute slot. Uncrossed controls may then be rare; prefer sparse-traffic hours (01–05 local) or sparse regions with ADS-B coverage, and use a dose-response model (number and geometry of crossings) rather than a binary label. This is an order-of-magnitude estimate, not computed from data; the analyst should measure it from adsb.lol.

**E. Data volumes and example queries**
- WSPR volumes: 2025 full day, all bands ≈ 7.8 M rows (≈1 GB CSV at about 127 bytes/row). 20 m only for 2 h ≈ 230 k rows (12.5 MB, 8 columns). 2014 full day ≈ 280 k rows. Pull per link and per day to respect the 20 requests/minute limit.
- ADS-B volumes: about 2 GB per day per instance. A 30-day test is about 60 GB. Keep only aircraft with altitude ≥ FL200 inside a bounding box around the selected paths. After filtering, this shrinks to tens of MB per day.

Example: hourly coverage (as run this session).
```
curl -G 'https://db1.wspr.live/' --data-urlencode "query=
SELECT toStartOfHour(time) h, count() spots, uniqExact(tx_sign) tx, uniqExact(rx_sign) rx
FROM wspr.rx WHERE time >= '2014-03-07 16:00:00' AND time < '2014-03-08 01:00:00'
GROUP BY h ORDER BY h FORMAT TSVWithNames"
```

Example: per-link time series with deduplication.
```
SELECT time, band, tx_sign, tx_loc, rx_sign, rx_loc, distance,
       any(frequency) f, any(snr) snr, any(drift) drift, any(power) pwr, any(code) code, count() dup
FROM wspr.rx
WHERE time >= '2024-06-01 00:00:00' AND time < '2024-06-02 00:00:00'
  AND band IN (7,10,14) AND tx_sign = 'XXXX' AND rx_sign IN ('YYYY','ZZZZ')
GROUP BY time, band, tx_sign, tx_loc, rx_sign, rx_loc, distance
ORDER BY time FORMAT CSVWithNames
```

Example: candidate-link census.
```
SELECT tx_sign, rx_sign, band, any(distance) d, count() n
FROM wspr.rx WHERE time >= '2024-06-01' AND time < '2024-06-02' AND band IN (7,10,14)
GROUP BY tx_sign, rx_sign, band HAVING n >= 100 ORDER BY n DESC FORMAT TSVWithNames
```

Example: adsb.lol download.
```
curl -LO https://github.com/adsblol/globe_history_2024/releases/download/v2024.12.30-planes-readsb-prod-0/v2024.12.30-planes-readsb-prod-0.tar.aa
curl -LO https://github.com/adsblol/globe_history_2024/releases/download/v2024.12.30-planes-readsb-prod-0/v2024.12.30-planes-readsb-prod-0.tar.ab
cat v2024.12.30-planes-readsb-prod-0.tar.a? | tar -xf - -C 2024-12-30
```
Then parse `traces/*/trace_full_<icao>.json` (gzip JSON; schema per the readsb README), interpolate to 1 s, and intersect with path buffers.

**F. Pitfalls to pre-empt**
- Duplicates and false decodes: drop TX signs seen fewer than 3× per day, and dedupe on (time, tx, rx, band).
- Self-reported `power` can be wrong.
- Locator precision: 4-character vs 6-character locators.
- Receiver decoder differences, e.g. wsprdaemon multi-decoder.
- SNR depends on RX noise.
- The TX duty cycle makes slots irregular.
- The decode threshold truncates low SNRs: spots below about −31 dB are missing, not low. Treat non-decodes as censored. Proponents also count missing spots as "anomalies", so pre-register how missingness is scored.
- Antenna and sunrise/greyline effects co-vary with traffic peaks. This is why controls must match on time of day.

**G. The MH370-specific track test.** Before applying the method to 2014, it should pass a blinded flight-recovery test:
- The method receives N real oceanic or long-haul flight segments (with ADS-B withheld) plus their departure and known waypoint constraints, at 2014-like WSPR density.
- It must predict the position at T+X hours.
- Errors are compared with a naive prior: a great circle or Inmarsat-arc baseline, or a random point on the corresponding arc.
- Success means beating the prior by a pre-registered margin with p < 0.01 under the decoy-date permutation.

### Gaps
- adsb.lol coverage over the Indian Ocean and other oceans is not documented. Ground feeders give little oceanic coverage, so the free ground truth cannot validate over-ocean claims directly; validation must use land or coastal regions, or sparse regions such as Antarctic gateway routes only where feeders exist.
- ADS-B Exchange free monthly sample days and other no-sign-up historical sources were not verified this session.
- I did not measure actual aircraft-crossing rates per slot from adsb.lol data, so the exposure density and control availability are unquantified.
- Whether wsprdaemon/wspr.rocks noise data, which would help separate RX-noise effects, are freely queryable without sign-up was not verified. wspr.rocks is mentioned as holding "every WSPR spot back to 2008" in a [timescale.com blog](https://timescale.com/blog/wsprdaemon-combines-timescaledb-grafana-analyze-radio), but its access terms were not checked.
