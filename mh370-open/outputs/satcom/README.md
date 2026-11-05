# Workstream A (satcom): MH370 end point from Inmarsat BTO/BFO + simple autopilot paths

Independent, public-data-only reanalysis (mh370-open). **Not authoritative.** Every assumption
is labelled *[assumption]*; the important ones have sensitivity runs (section 9).

## 0. Results in one screen

> **Update, 5 Nov 2026 (reviewer response; section 13).** Two path families were added: waypoint
> routes (FMT → a published waypoint → a new lateral mode) and generic two-leg paths. Their
> evidence is comparable to the single-mode families.
>
> * **The recommended layer is now `p_v2`**, evidence-weighted over all 7 families.
>   * Impact: median **38.17 S**, 50 % 38.69–37.65 S, 90 % **39.51–36.46 S**.
>   * For comparison, `p` gives 38.36 S, 50 % 38.83–37.93 S, 90 % 39.61–37.40 S.
> * **Weighting the 7 families equally:** median 37.0 S, 90 % 39.2–31.2 S.
> * **The satellite data alone do not exclude the UGIB latitude** (34.2 S). One extra turn fits it
>   as well as 38 S. A descent during the 18:40 call (UGIB's explanation of that BFO) costs no
>   evidence and moves the median to 35.8 S (90 % 38.1–30.9 S, `p_v2_sens_descent1840`).
> * Read sections 13.6–13.8 before using either layer. The tables below are the v1 single-mode
>   results.


| | 7th-arc latitude at 00:19:29 (aircraft position) | impact (default end-of-flight mixture, `p`) |
|---|---|---|
| peak | **38.15 S** | 38.25 S |
| median | 38.21 S | 38.36 S |
| 50 % interval | 38.66 S - 37.80 S | 38.83 S - 37.93 S |
| 90 % interval | 39.44 S - 37.29 S | 39.61 S - 37.40 S |

(Combined over autopilot modes with evidence weights; latitudes are of the nearest point on the
sea-level 7th arc. Longitude of the arc at 38.2 S is 87.8 E.)

Per mode (baseline; 00:19:29 crossing latitude; best-fit residual RMS over 12 BTO / 8 BFO):

| mode | evidence weight | log Z | peak | median | 50 % | 90 % | best fit BTO / BFO RMS |
|---|---|---|---|---|---|---|---|
| LNAV great circle | 0.63 | -18.5 | 38.35 S | 38.42 S | 38.87-38.03 S | 39.62-37.52 S | 30 us / 4.0 Hz |
| constant true track | 0.37 | -19.1 | 37.85 S | 37.87 S | 38.22-37.55 S | 38.79-37.13 S | 30 us / 4.2 Hz |
| constant magnetic track | 2.3e-5 | -28.8 | 33.65 S | 33.64 S | 33.83-33.46 S | 34.13-33.22 S | 57 us / 3.4 Hz |
| constant true heading | 1.4e-5 | -29.2 | 35.65 S | 35.69 S | 36.06-35.34 S | 36.65-34.84 S | 54 us / 5.4 Hz |
| constant magnetic heading | 3e-15 | -51.4 | 31.15 S | 31.18 S | 31.36-31.01 S | 31.66-30.78 S | 97 us / 5.1 Hz |

* Only the LNAV (great-circle) and constant-true-track families fit the satellite data to the
  measurement-noise level; both put the crossing at ~37.5-39.5 S, i.e. at or near the peak of the
  DSTG (2015/16) Bayesian result (digitised peak 37.8 S, 90 % 39.0-35.2 S).
* The magnetic-track and true-heading families reach 33.6 S and 35.7 S respectively, but only with
  slow speeds (M ~0.73 near the prior's lower edge, and M ~0.75 at the FL300 edge) and BTO misfits
  of 70-125 us at 20:41 / 22:41; their evidence is ~10 log-units lower. With equal weights per mode (not evidence-
  weighted) the combined median moves to 35.7 S (90 %: 38.9-31.0 S) - see "equal weights" in
  section 9. **The answer is therefore dominated by which autopilot families one admits.**
* FMT (final major turn): 18:32-18:40 (LNAV/CTT), bounded above by the 18:40 call BFO and below by
  the 18:28 BFO and 18:25-18:28 BTOs. Post-FMT track ~186-191 deg true, Mach 0.81-0.86 (LNAV) /
  0.80-0.84 (CTT); flight level is not constrained by the satellite data.
* **The UGIB 2020 last estimated position (34.23 S, 93.79 E) is strongly disfavoured within the
  single-mode family.**
  * LNAV/CTT can only reach it by turning after the 18:40 call. That BFO then misses by about
    46 Hz (−2 dlogL ~ 58–61).
  * CMT/CTH reach it with −2 dlogL ~ 17–20, at near-holding Mach.
  * This is a statement about that family, not about the data. Section 13 shows three things:
    * paths with one more turn, or with a turn at a published waypoint, fit 34.2 S as well as the
      best single-mode path fits 38 S;
    * UGIB's own route fits the data as well as our best path (log L −3.55 against −3.90), because
      it descends during the 18:40 call;
    * allowing such a descent costs no evidence.
  * The families still put most posterior mass near 38 S, through prior volume rather than
    likelihood.

Files: `data/derived/satcom_posterior.nc` (variables below), `outputs/satcom/arc_profile.csv`,
`summary.json`, `sensitivity.csv`, `profile_likelihood.csv`, validation CSVs and figures
(`fig_*.png`).

---

## 1. Data sources (all free, anonymous; provenance in `data/raw/*/SOURCE.md`)

| Data | Source / URL | Used for |
|---|---|---|
| Inmarsat SU log (redacted, 27 May 2014), CSV | Sladen, https://github.com/sladen/inmarsat-9m-mro (`external/sladen_inmarsat-9m-mro/inmarsat-su-log-redacted.csv`; conversion is public domain) | all BTO/BFO values |
| ATSB Tables 2, 4 (satellite ECEF + "Satellite and EAFC effect"), 5, 6 | ATSB "MH370 - Definition of Underwater Search Areas" (26 Jun 2014, rev. 13 Aug 2014), transcribed in the same repo (`atsb/`) | satellite ephemeris (via `geo.py`), df_sat+df_AFC, validation |
| Public ADS-B track 16:42-17:21 | FR24 / FlightAware / Planefinder, merged in the Sladen repo (`ads-b/all-combined.csv`) | in-flight BFO/BTO validation |
| Ashton et al. 2015, J. Navigation 68:1-22, doi:10.1017/S037346331400068X (open access, CC-BY) | https://cambridge.org/core/services/aop-cambridge-core/content/view/S037346331400068X (`data/raw/ashton2015/`) | BFO equation, frequencies, Table 6 values, Table 9 example path (validation) |
| DSTG, *Bayesian Methods in the Search for MH370* (Dec 2015 draft of the 2016 Springer open-access book, doi:10.1007/978-981-10-0379-0) | ATSB-hosted PDF via web.archive.org (`data/raw/dstg_book/`) | noise model, AES-compensation details, descent kernel, Fig. 10.3 (digitised) |
| ERA5 u, v, T, 150-350 hPa, hourly, 0.25 deg, 7 Mar 16 UTC - 8 Mar 01 UTC | Google ARCO-ERA5 public Zarr `gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3` (anonymous; `data/raw/era5_arco/`, 24 MB) | winds/temperature aloft |
| WMM2010 magnetic model, epoch 2014.18 | `pygeomag` (pip, pure python) with NOAA NCEI WMM2010 coefficients | magnetic track/heading modes |
| Airway N571 waypoints VAMPI, MEKAR (06 30 14 N 096 29 28 E), NILAM, IGOGU | Malaysian AIP ENR 3.3 RNAV routes, https://aip.caam.gov.my | radar-point prior |
| Last radar point 18:22:12, "about 10 NM beyond MEKAR" on N571 | ATSB, *The Operational Search for MH370* (3 Oct 2017); Ashton et al. 2015 sec. 6.1 ("close to MEKAR") | path start |
| UGIB 2020: Ulich, Godfrey, Iannello, Banks, *The Final Resting Place of MH370* (7 Mar 2020) | linked from https://mh370.radiantphysics.com/2020/03/09/new-report-released-for-mh370-search/ (`data/raw/ugib2020/`) | UGIB route definition and published states (section 13) |
| Indian Ocean / Andaman waypoint coordinates | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12), https://aip.caam.gov.my; opennav.com; R. Godfrey 2016 waypoint table (duncansteel.com/archives/2189) (`data/raw/waypoints_indian_ocean/`) | waypoint family (section 13.2) |

Python packages added to `.venv`: `zarr`, `gcsfs` (ERA5), `pygeomag` (WMM). `openap` was installed
to test a fuel model and then removed (section 8).

## 2. BTO/BFO forward model (`src/mh370/satcom.py`)

BTO: `geo.predicted_bto` (shared): round trip Perth GES -> satellite -> aircraft and back, bias
-495,679 us (ATSB Table 2).

BFO (Ashton et al. 2015 eq. 2; DSTG eq. 5.6):

    BFO = dF_up + dF_down + df_comp + (df_sat + df_AFC) + df_bias

* dF_up = -f_up (d|r_sat - r_ac|/dt)/c, f_up = 1646.6525 MHz, using the *true* satellite position
  and velocity (ATSB Table 4 spline from `geo.py`) and the aircraft ground velocity including
  vertical speed. This single term contains both the "aircraft" and the "satellite" uplink-Doppler
  rows of the ATSB/Ashton tables.
* dF_down = -f_down (d|r_sat - r_Perth|/dt)/c, f_down = 3615.1525 MHz.
* df_comp: the SDU's own pre-compensation, computed as DSTG sec. 5.3 describes it: horizontal
  velocity only, aircraft at altitude 0, motionless satellite at 64.5 E, 0 N, 35,788.12 + 422 km
  altitude; spherical Earth (WGS84 alternative differs by < 0.2 Hz).
* df_sat + df_AFC: **this - and only this - is what ATSB Table 4 ("Satellite and AFC values";
  "Satellite and EAFC Effect ... Measured") contains.** Evidence: (i) the 13-Aug-2014 revision of
  ATSB Tables 5/6 lists *Satellite Doppler (uplink)* and *Satellite Doppler (downlink)* as separate
  rows next to *Satellite and EAFC effect* (24.1 Hz at 17:07); (ii) Ashton Table 9 lists dF_down
  separately from "dF_sat + dF_AFC"; (iii) an independent reconstruction - digitised Ashton Fig. 11
  pilot frequency minus the computed Burum -> satellite -> Perth pilot Doppler (as in
  o-nesterov/MH370Solver, read but not run) - reproduces Table 4 to 0.28 Hz RMS, max 0.73 Hz, at
  all 11 table times (`validation_table4_crosscheck.csv`); (iv) the term-by-term reproductions
  below close only with this split. Between table times Table 4 is interpolated linearly (18:40:
  8.4 Hz, 23:14: -31.9 Hz; the Fig. 11 reconstruction gives 8.1 and -32.8 Hz - immaterial).
* df_bias: calibrated in 2.3; in the path fit a common bias with prior N(152, 3^2) Hz is
  marginalised analytically *[assumption: prior width]*.

## 2b. Validation of the forward model (`scripts/satcom_validate_bfo.py`)

**2.1 Published example path, Ashton et al. (2015) Table 9** (positions/tracks/speeds as
published, altitude 0 on ground and FL350 in flight, bias 150 Hz). My predicted BFO minus
Ashton's published "Pred" column: **|diff| <= 1.2 Hz at all 13 rows** (RMS 0.7 Hz). Individual
terms agree to <= 0.5 Hz (satellite uplink), <= 1.3 Hz (downlink), <= 1.1 Hz (df_sat+AFC); the
aircraft-uplink and compensation terms differ by up to 2.5 / 3.2 Hz with opposite signs (they
cancel; consistent with Ashton's rounded positions and a different altitude convention in the
compensation). BTOs at Ashton's rounded (0.1 deg) positions are within the ~+-50 us rounding
error at sea-level geometry.

| UTC | dF_up aircraft | dF_up sat | dF_down | df_comp | df_sat+AFC | pred (mine) | mine - Ashton |
|---|---|---|---|---|---|---|---|
| 16:30:00 | 0.0 | -6.1 | -84.6 | 0.0 | 29.1 | 88.4 | +0.4 |
| 16:42:31 | 193.7 | -5.8 | -80.3 | -179.7 | 27.5 | 105.3 | +0.3 |
| 16:55:53 | -421.5 | -4.4 | -75.3 | 450.2 | 25.7 | 124.6 | -0.4 |
| 17:07:19 | -457.8 | -3.2 | -71.0 | 488.1 | 24.0 | 130.2 | +0.2 |
| 18:25:27 | 574.5 | -1.3 | -36.8 | -555.0 | 10.6 | 142.0 | +1.0 |
| 18:39:58 | 350.6 | -0.9 | -29.9 | -386.3 | 8.5 | 92.0 | +1.0 |
| 19:41:03 | 31.6 | -0.6 | 0.1 | -71.4 | -0.5 | 109.2 | +1.2 |
| 20:41:05 | -181.6 | 5.4 | 29.2 | 142.3 | -1.5 | 143.8 | +0.8 |
| 21:41:27 | -363.0 | 16.0 | 55.9 | 329.3 | -18.1 | 170.1 | +0.1 |
| 22:41:22 | -519.7 | 29.5 | 78.2 | 494.2 | -28.5 | 203.7 | +0.7 |
| 23:14:00 | -593.2 | 37.3 | 88.1 | 572.8 | -31.9 | 223.1 | +1.1 |
| 00:11:00 | -699.5 | 50.2 | 100.7 | 688.1 | -37.7 | 251.8 | -0.2 |
| 00:19:29 | -714.9 | 51.9 | 102.1 | 704.8 | -37.8 | 256.0 | 0.0 |

**2.2 ATSB Tables 5/6 (17:07, 5.27 N 102.79 E, 867 km/h, track 0/25/50 deg)**: predicted BFO
135.9 / 132.5 / 123.5 Hz vs ATSB 135.1 / 131.7 / 122.5 Hz (+0.8 to +1.0 Hz); satellite uplink
-3.2 Hz (ATSB -3.2), downlink -71.1 Hz (ATSB -71.9). The latitude-sensitivity version (0.27 /
5.27 / 10.27 N) gives 128.6 / 132.5 / 136.2 vs ATSB's original 127.5 / 131.7 / 135.5 Hz.
(`validation_atsb_table5.csv`.)

**2.3 Bias calibration on the ground and in flight** (KLIA gate 16:00-16:11; ADS-B for 16:42-
17:07; positions after 17:02:40 dead-reckoned from ADS-B GS/track; vertical rate from ADS-B
altitude differences). One bias per channel type fitted to gate + 16:55 climb + 17:07 level data:
**R-channel 153.4 Hz, T-channel 156.0 Hz** (ATSB used 152.5, Ashton 150; the R-channel bias in
level flight alone is 150.6 Hz, at the gate 153.7 Hz). Residuals (Hz) with those biases
(`validation_bfo_residuals_by_phase.csv`, `fig_bfo_calibration.png`):

| phase | chan | n | mean | sd | RMS | max abs |
|---|---|---|---|---|---|---|
| gate 16:00:30-16:11 | R | 42 | +0.3 | 1.8 | 1.8 | 3.5 |
| gate 16:00:30-16:11 | T | 21 | -0.7 | 0.9 | 1.1 | 2.7 |
| climb 16:55-16:56 (~1,400 fpm) | R | 8 | +1.3 | 1.7 | 2.1 | 3.2 |
| climb 16:55-16:56 | T | 99 | +2.1 | 2.3 | 3.0 | 5.7 |
| level FL350 17:06-17:07 | R | 8 | -2.8 | 1.1 | 3.0 | 4.4 |
| level FL350 17:06-17:07 | T | 124 | -1.5 | 1.4 | 2.1 | 4.2 |
| climbing turn 16:42-16:43 | R / T | 5 / 61 | +5.2 / +5.8 | 6.9 / 3.0 | 8.1 / 6.5 | 12.6 / 10.2 |
| log-on burst 16:00:13-16:00:23 | R | 6 | **+17.0** | 0.4 | | |
| taxi? 16:27-16:30 | R / T | 6 / 56 | -1.6 / +0.9 | 4.4 / 4.5 | | |

So the model reproduces the calibration BFOs to <= 3 Hz RMS in steady flight and on the ground
(the 16:42-16:43 climbing turn is worse because of bank angle and the coarse ADS-B sampling).
The +17 Hz offset of the first R-channel bursts after the 16:00 log-on is the same SDU
oscillator warm-up signature reported by Holland (2018) - independent support for excluding the
18:25:34-18:28:05 BFOs and treating 18:25:27 with care.

**2.4 BTO**: gate R-channel BTOs (n = 54): mean residual -6 us, sd 30.5 us (ATSB Table 2's 17
values: sd 31.4 us). In flight 16:42-17:07 (n = 21): mean -1 us, sd 19 us, max 49 us.

Conclusion: the forward model meets the "~5 Hz / ~30 us" requirement and reproduces the only
published term-by-term path computation to ~1 Hz.

## 3. Winds and temperature

ERA5 via ARCO (anonymous; ~2.5 GB transferred, 24 MB stored). Quadrilinear interpolation in
time, log-pressure, latitude, longitude. Flight levels -> pressure by ISA (FL300 = 300.9 hPa,
FL350 = 238.4 hPa, FL400 = 187.5 hPa); geometric altitude in the BTO/BFO geometry approximated by
pressure altitude (< 300 m, < 2 us). GDAS1/NCEP were not needed.

## 4. Path model (`src/mh370/satcom_paths.py`)

* **Start** 18:22:12 at MEKAR + 10 NM along N571 (296.3 deg) = 6.578 N 96.341 E, with an isotropic
  Gaussian prior sd 10 NM *[assumption; DSTG did not use this point because of long-range radar
  inaccuracy, so it is soft here]*. Note: Wikipedia's "6 49 38 N 97 43 15 E" for this point is ~75 NM
  east of MEKAR and inconsistent with "10 NM beyond MEKAR", with the Pulau Perak 18:02 position
  (it would imply ~300 kt) and with the 18:25-18:28 BTOs (from it, any 480-kt track gives >= 13,130
  us at 18:25:27 vs 12,520 us measured; from MEKAR + 10 NM continuing on N571 gives 12,534 us); it
  was not used. Posterior position at
  18:22:12 (LNAV/CTT): 6.32-6.88 N, 96.27-96.56 E (5-95 %), i.e. essentially the prior: the radar
  point is not informative beyond its assumed 10 NM, and the pre-FMT ground speed stays broad
  (~360-510 kt), trading against the FMT time.
* **18:22:12 -> FMT**: constant ground speed GS_pre ~ U(350, 520) kt and true track
  trk_pre ~ U(270, 340) deg (covers N571 at 296 deg and offset manoeuvres approximately).
* **FMT** at t_fmt ~ U(18:22:42, 19:40:03), instantaneous turn *[assumption; turn time ~1-2 min
  is below the resolution of the data]*.
* **FMT -> 00:19:29**: one lateral mode at constant Mach M ~ U(0.70, 0.86) and constant pressure
  altitude FL ~ U(300, 400), integrated through ERA5 winds/temperatures on the WGS84 ellipsoid
  (midpoint scheme, 120 s step plus exact FMT and measurement times; vs 30 s steps the 00:19
  position changes < 0.07 km):
  * LNAV: great circle with initial azimuth theta (FMS direct-to a distant waypoint);
  * CTT: constant true track (loxodrome) theta;
  * CMT: constant magnetic track theta, true = theta + WMM2010 declination (-1 deg near the equator
    to -13 deg at 30 S 95 E and -30 deg at 38 S 88 E: magnetic modes curve strongly east);
  * CTH / CMH: constant true / magnetic heading theta; ground track then follows the wind.
  theta ~ U(140, 230) deg. Mode prior: equal *[assumption]*.
* **Measurements** (values from the public log; identical to Ashton Table 6):

| kind | UTC | value | sigma | note |
|---|---|---|---|---|
| BTO | 18:25:27.421 | 12520 us | 69 us | R600 log-on request, raw 17120 - 4600 |
| BTO | 18:27:03.9, 18:27:04.4, 18:27:08.4, 18:28:05.9, 18:28:14.9 | 12560, 12520, 12520, 12500, 12480 us | 42 us | R1200 |
| BFO | 18:28:14.9 | 143 Hz | 7 Hz | R1200; Ashton advises caution (warm-up); sensitivity "no1828bfo" |
| BFO | 18:40:08 (mean of 51 C-channel bursts 18:39:55-18:40:56) | 87.8 Hz | 7 Hz | call 1 |
| BTO/BFO | 19:41:02.9, 20:41:04.9, 21:41:26.9, 22:41:21.9, 00:10:59.9 | 11500/111, 11740/141, 12780/168, 14540/204, 18040/252 | 42 us / 7 Hz | R1200 handshakes |
| BFO | 23:14:21 (mean of 29 bursts) | 217.3 Hz | 7 Hz | call 2 |
| BTO | 00:19:29.416 | 18400 us | 69 us | R600 log-on, raw 23000 - 4600 |

  Not used: BFO 18:25:27 (log-on after a power-up; Holland 2018 judged it untrustworthy), BFOs
  18:25:34-18:28:05 (warm-up transient), BFO 00:19:29 and BFO/BTO 00:19:37 (descent; log-on
  acknowledge).

* **Noise model.** BTO sd = DSTG's empirical measurement sd (29 us R1200, 62 us R600, from 20
  previous 9M-MRO flights) combined in quadrature with a **path-model error of 30 us** -> 42 / 69 us
  *[assumption]*. Reason: this is a rigid deterministic path family with no process noise (unlike
  DSTG's filter), and ERA5 upper-air wind errors of ~2-3 m/s accumulated over the ~1 h between
  handshakes displace a path by ~5-8 km along track, i.e. ~25-40 us of BTO. The measurement-only
  version (29/62 us) is sensitivity "bto29". BFO sd = 7 Hz (DSTG: 4.3 Hz empirical in-flight sd,
  inflated to 7 Hz for bias drift; 4.3 Hz is sensitivity "bfo4p3"); one common bias offset
  ~ N(152, 3^2) Hz marginalised analytically (Sherman-Morrison). 3 Hz covers the calibrated
  150.6-153.7 Hz range; DSTG's 25 Hz is sensitivity "bias25".
* **Sampler** (`src/mh370/satcom_smc.py`): adaptive-tempering SMC (ESS halving, systematic
  resampling, random-walk Metropolis moves with particle covariance), 20,000 particles per mode
  (10,000 for sensitivities), 10-12 tempering stages; the SMC evidence estimate (log Z)
  weights the modes. Evidence is reproducible to ~0.1 (CTT: -22.14 with N = 20,000 vs -22.21 with
  N = 1,000 in a test with the 29 us noise model).

## 5. End-of-flight model (`scripts/satcom_posterior.py`)

The path posterior gives the aircraft at 00:19:29 (on the 7th arc at cruise altitude, which lies
~8-12 km beyond the sea-level arc). Impact positions are drawn per particle (25 draws):

* **(a) uncontrolled descent after fuel exhaustion** (`p_uncontrolled`): displacement = 5 NM
  along the final ground track + 2-D Gaussian scatter, sd 7 NM per axis *[assumption]*. Radial
  distance: median 9 NM, 90 % < 17 NM, 95 % < 19 NM, 99.5 % < 25 NM. Basis: ATSB/Boeing
  simulations - "a high likelihood of the aircraft reaching zero altitude within 15 nm of the
  beginning of descent" (DSTG 2016 sec. 10.5); the ten Boeing end-of-flight simulations shared
  by the ATSB (Iannello 2018) never flew wings-level after autopilot disconnect and Iannello
  recommended +-25 NM; the final BFOs imply 2,900-15,200 fpm at 00:19:29 rising to 13,800-
  25,300 fpm eight seconds later (ATSB 2017; Holland 2018: ~0.68 g downward), so the aircraft was
  already descending fast at the arc.
* **(b) piloted glide** (`p_glide`): distance ~ U(0, 120) NM along the final track +- N(0, 15 deg)
  *[assumption]*; 120 NM ~ still-air glide from ~FL350 at an assumed L/D of ~19-20. For scale:
  CAPTION's unsearched band is 50-70 NM from the arc; the 2023 Ulich-Iannello drift study used
  +-70 NM and +-140 NM zones for glide scenarios.
* **Default** `p = 0.8 p_uncontrolled + 0.2 p_glide` *[assumption/judgement]*: the two final BFOs
  and the "not configured for ditching" debris finding (ATSB 2017) favour no pilot input, but a
  recovered glide cannot be excluded with public data (Lyne 2024; CAPTION). The failed searches
  within +-25 NM would raise the glide weight a posteriori, but that belongs to workstream C
  (search POD), so it is not used here. Also provided: `p_dstg_kernel` (DSTG/ATSB indicative
  kernel: uniform 15 NM disc + Gaussian sd 30 NM drop-off; radial median 43 NM, 90 % < 74 NM).

## 6. Outputs

`data/derived/satcom_posterior.nc` (common grid, dims lat x lon, each variable sums to 1):

| variable | content |
|---|---|
| `p` | default: evidence-weighted modes, 0.8 uncontrolled + 0.2 glide |
| `p_uncontrolled`, `p_glide`, `p_dstg_kernel` | end-of-flight scenarios (evidence-weighted modes) |
| `p_arc0019` | aircraft position at 00:19:29 (no descent model) |
| `p_equal_modes` | as `p` but each autopilot mode weighted equally |
| `p_mode_LNAV`, `p_mode_CTT`, `p_mode_CMT`, `p_mode_CTH`, `p_mode_CMH` | as `p`, single mode |
| `p_sens_<variant>` | as `p` under each sensitivity variant of section 9 |
| `p_v2`, `p_v2_*`, `p_fam_waypoint`, `p_fam_twoleg` | **v2 (section 13.9)**: mixtures including the waypoint and two-leg families; `p_v2` is the recommended layer |

Grid smoothing: Gaussian, sd 1 cell (0.05 deg), to remove Monte-Carlo noise; no mass falls
outside the grid.

`outputs/satcom/arc_profile.csv`: per 0.1 deg latitude bin of the sea-level 7th arc (each grid
cell assigned to its nearest arc point): `arc_lon` (blank south of 43.5 S, where the 7th arc
ends), the grid layers above marginalised across the
arc (`p`, `p_uncontrolled`, ...), and `arc0019_<mode>` = per-mode distribution of the 00:19:29
crossing latitude.

Figures: `fig_bfo_calibration.png` (forward-model calibration residuals),
`fig_paths_by_mode.png` (best-fit and posterior paths), `fig_residuals_bestfit.png`,
`fig_arc_latitude_by_mode.png` (with DSTG overlay), `fig_parameters_by_mode.png`,
`fig_posterior_maps.png`, `fig_profile_likelihood.png`, `fig_sensitivity.png`.

## 7. Profile likelihood: how strongly is each latitude disfavoured?

`scripts/satcom_profile.py`: for each mode and imposed 00:19:29 latitude, the best achievable fit
(differential evolution over all 8 (9 with Mach drift) path parameters within the baseline prior
bounds; 2 seeds, plus a refinement pass with the FMT restricted to before 18:40:30 and 2 more seeds
because the unrestricted search sometimes stalled in a late-FMT local optimum; best kept;
`profile_likelihood_allruns.csv` has every run). Values are upper bounds on the true optimum.

`-2 dlogL` relative to the best fit over all modes and latitudes (baseline noise model; a difference of ~6-10 is strong evidence against). Columns: imposed latitude.

| mode | 40 | 39 | 38 | 37 | 36 | 35 | 34.23 | 33 | 32 | 31 | 30 | 29 | 28 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CMH | 1324.6 | 853.1 | 520.6 | 305.5 | 168.6 | 115.8 | 92.0 | 72.3 | 58.6 | 51.4 | 70.4 | 71.5 | 76.4 |
| CMT | 771.9 | 428.4 | 223.4 | 94.9 | 55.4 | 28.2 | 17.3 | 15.6 | 43.2 | 61.4 | 71.9 | 80.0 | 85.8 |
| CTH | 68.4 | 35.7 | 27.3 | 19.4 | 15.0 | 14.0 | 19.7 | 30.7 | 57.3 | 62.3 | 70.1 | 78.8 | 86.4 |
| CTT | 12.3 | 5.2 | 1.6 | 1.0 | 8.9 | 39.6 | 61.1 | 69.3 | 74.8 | 79.1 | 82.5 | 85.7 | 88.7 |
| LNAV | 5.3 | 2.2 | 0.3 | 1.5 | 11.8 | 44.6 | 60.8 | 68.2 | 73.5 | 78.1 | 81.6 | 85.0 | 88.1 |
| CTT + Mach drift | 4.7 | 2.0 | 0.3 | 1.0 | 7.2 | 33.1 | 58.2 | 67.1 | 73.3 | 78.2 | 82.0 | 85.5 | 88.6 |
| LNAV + Mach drift | 3.3 | 1.4 | -0.0 | 1.3 | 9.4 | 37.2 | 57.9 | 65.9 | 71.9 | 77.0 | 81.0 | 84.7 | 88.1 |

Best fits forced through the UGIB latitude (34.23 S):

| mode | -2 dlogL | BTO RMS (us) | BFO RMS (Hz) | max abs BFO (Hz) | Mach | dMach/h | FL | theta | FMT | end lon |
|---|---|---|---|---|---|---|---|---|---|---|
| CMH | 92.0 | 125 | 7.3 | 16.9 | 0.700 | - | 300 | 188.2 | 18:34:00 | 94.48 E |
| CMT | 17.3 | 62 | 4.4 | 7.9 | 0.719 | - | 301 | 186.8 | 18:38:41 | 94.16 E |
| CTH | 19.7 | 63 | 3.8 | 6.6 | 0.738 | - | 326 | 181.2 | 18:40:08 | 93.98 E |
| CTT | 61.1 | 49 | 17.7 | 47.8 | 0.802 | - | 400 | 179.5 | 18:53:56 | 93.84 E |
| LNAV | 60.8 | 50 | 17.6 | 47.6 | 0.802 | - | 400 | 179.5 | 18:53:53 | 93.85 E |
| CTT + drift | 58.2 | 51 | 17.1 | 45.6 | 0.786 | 0.0040 | 400 | 179.5 | 18:53:28 | 93.85 E |
| LNAV + drift | 57.9 | 51 | 17.0 | 45.4 | 0.785 | 0.0040 | 400 | 179.5 | 18:53:26 | 93.86 E |

**Reading.** For LNAV/CTT the fit is flat between ~37 and ~39.5 S and deteriorates sharply north
of 36.5 S (Delta >= 9 at 36 S, >= 33 at 35 S). The best LNAV/CTT path forced through the UGIB
latitude flies due south (179.5 deg) along ~93.85 E - essentially the UGIB southern leg - and fits
the 19:41-00:19 BTOs at ~50 us RMS, but it needs its single turn at ~18:54, after the 18:40 call,
so the 18:40 BFO misses by ~46 Hz. Among single modes, 34.2 S is reachable only by CMT/CTH
(Delta ~17-20) at M ~0.72-0.74, which our fuel-motivated check disfavours.

**This is a property of the single-mode family, not of the data** (section 13.6). Families with one
more turn reach 34.2 S with −2 dlogL ≈ −2.4 to +1.5 relative to the best single-mode fit: a
generic two-leg path, or FMT → MUTMI → about 178.5 T. UGIB's own route, which descends during the
18:40 call, fits as well as the best single-mode path (section 13.5).

## 8. Fuel

No fuel likelihood is used. A credible public fuel model for the 777-200ER/Trent 892 at the
needed accuracy (a few %) was not available: the open OpenAP B772 model (Trent 895 option) gives
~10-11 t/h at M0.84/FL350 and ~215 t, ~60 % above what MH370's own numbers imply (43,800 kg at
17:07 lasting to ~00:17:30 -> 6.1 t/h average), so it was removed. Qualitatively: the satellite
data alone leave flight level unconstrained; the favoured LNAV/CTT solutions fly M0.80-0.86, the
long-range-cruise regime that the IG/UGIB fuel model found consistent with exhaustion near 00:17
(UGIB used LRC at FL390). The magnetic/heading modes need M0.72-0.75 - near holding speed - which
would generally extend endurance beyond 00:17 (an argument against them that we cannot quantify). As a fuel-motivated sensitivity: requiring
M >= 0.78 (i.e. rejecting near-holding speeds) keeps 100 % of the LNAV and CTT posterior samples and
removes essentially all CMT/CTH/CMH samples (<= 0.1 % remain; also under the wide prior), so it
leaves the default unchanged and collapses the "equal-weight" alternative onto the default.
The "machdrift" sensitivity lets Mach vary linearly after the FMT (covering LRC-like decreasing-
Mach schedules); for LNAV/CTT the data prefer near-constant or slightly decreasing Mach (median dMach/dt -0.002
and -0.004 per hour) and the result barely moves (section 9).

## 9. Sensitivity runs (`scripts/satcom_run_paths.py --variant ...`, `sensitivity.csv`, `fig_sensitivity.png`)

| variant | weights LNAV/CTT/CMT/CTH/CMH | 00:19 peak | median | 50 % | 90 % | impact (p) median, 90 % | equal-weight median, 90 % |
|---|---|---|---|---|---|---|---|
| default (BTO 42/69 us, BFO 7 Hz, bias 152+/-3 Hz) | 0.63/0.37/0.00/0.00/0.00 | 38.15 S | 38.21 S | 38.66-37.80 S | 39.44-37.29 S | 38.36 S, 39.61-37.40 S | 35.69 S, 38.94-31.01 S |
| BTO sigma 29/62 us (measurement noise only) | 0.74/0.26/0.00/0.00/0.00 | 38.15 S | 38.21 S | 38.62-37.84 S | 39.28-37.35 S | 38.36 S, 39.47-37.47 S | 35.72 S, 38.79-28.33 S |
| drop 18:28:15 BFO | 0.65/0.35/0.00/0.00/0.00 | 38.15 S | 38.27 S | 38.76-37.85 S | 39.59-37.32 S | 38.43 S, 39.77-37.43 S | 35.83 S, 39.03-31.06 S |
| drop 18:27-18:28 R1200 BTOs | 0.56/0.44/0.00/0.00/0.00 | 38.05 S | 38.20 S | 38.72-37.74 S | 39.55-37.17 S | 38.35 S, 39.71-37.28 S | 35.50 S, 39.09-30.64 S |
| BFO sigma 4.3 Hz | 0.50/0.50/0.00/0.00/0.00 | 37.85 S | 37.87 S | 38.24-37.53 S | 38.86-37.09 S | 38.02 S, 39.07-37.20 S | 35.43 S, 38.53-30.96 S |
| BFO bias prior sd 25 Hz (DSTG) | 0.64/0.36/0.00/0.00/0.00 | 38.15 S | 38.23 S | 38.71-37.82 S | 39.54-37.30 S | 38.38 S, 39.70-37.41 S | 35.66 S, 38.99-31.08 S |
| ERA5 winds x0.9 | 0.65/0.35/0.00/0.00/0.00 | 38.15 S | 38.18 S | 38.62-37.77 S | 39.40-37.26 S | 38.32 S, 39.58-37.37 S | 35.82 S, 38.89-31.28 S |
| ERA5 winds x1.1 | 0.61/0.39/0.00/0.00/0.00 | 38.15 S | 38.25 S | 38.69-37.85 S | 39.47-37.33 S | 38.40 S, 39.65-37.43 S | 35.57 S, 38.99-30.83 S |
| Mach 0.62-0.86, FL200-410 | 0.65/0.35/0.00/0.00/0.00 | 38.15 S | 38.28 S | 38.75-37.87 S | 39.53-37.37 S | 38.43 S, 39.70-37.48 S | 36.47 S, 39.02-32.07 S |
| Mach linear drift -0.012..+0.004 /h | 0.52/0.47/0.00/0.00/0.00 | 38.15 S | 38.27 S | 38.72-37.88 S | 39.49-37.35 S | 38.42 S, 39.66-37.46 S | 36.17 S, 39.08-31.66 S |

Per-mode medians of the 00:19 crossing latitude under each variant:

| variant | LNAV | CTT | CMT | CTH | CMH | best log L LNAV/CTT/CMT/CTH/CMH |
|---|---|---|---|---|---|---|
| baseline | 38.42 | 37.87 | 33.64 | 35.69 | 31.18 | -3.9/-4.1/-10.0/-10.0/-29.1 |
| bto29 | 38.36 | 37.79 | 33.61 | 35.72 | 28.62 | -5.3/-5.7/-17.2/-16.2/-51.3 |
| no1828bfo | 38.48 | 37.94 | 33.74 | 35.83 | 31.23 | -3.6/-3.9/-9.6/-8.4/-28.0 |
| no1827bto | 38.44 | 37.91 | 33.44 | 35.50 | 30.77 | -3.0/-3.1/-7.6/-7.7/-22.7 |
| bfo4p3 | 38.11 | 37.64 | 33.55 | 35.43 | 31.14 | -6.6/-6.3/-11.5/-12.5/-32.1 |
| bias25 | 38.44 | 37.88 | 33.63 | 35.66 | 31.25 | -5.5/-5.8/-11.7/-11.9/-31.1 |
| wind90 | 38.37 | 37.83 | 33.60 | 35.82 | 31.46 | -4.0/-4.1/-10.0/-9.1/-26.2 |
| wind110 | 38.47 | 37.92 | 33.66 | 35.57 | 31.01 | -3.8/-4.0/-9.9/-11.5/-33.7 |
| wideprior | 38.49 | 37.94 | 33.66 | 36.47 | 32.23 | -3.9/-4.1/-10.0/-8.1/-25.3 |
| machdrift | 38.46 | 38.08 | 34.01 | 36.17 | 31.97 | -4.0/-3.8/-6.5/-6.2/-18.9 |

**Reading.** Within the stated path family the combined result is insensitive to the noise model,
to dropping the delicate 18:27-18:28 data, to +-10 % wind scaling, to widening the speed/altitude
prior (Mach 0.62-0.86, FL200-410) and to letting Mach drift (LRC-like): medians 37.9-38.3 S, 90 %
intervals within 39.8-37.1 S. LNAV vs constant-true-track weights move between 0.5/0.5 and
0.74/0.26, which shifts the result by only ~0.5 deg. The one assumption that moves the answer by
degrees is **how the autopilot families are weighted**: evidence weights (default) give ~38 S;
equal weights per mode give a median ~35.5-36.5 S with a 90 % interval reaching ~31 S, carried
by modes whose best fits are 2.3-25 log-likelihood units worse (CMT/CTH/CMH). The Mach >= 0.78
fuel-motivated check (section 8) removes those modes again.

## 10. Comparison with published results

| study | end point / peak | this work |
|---|---|---|
| DSTG Bayesian filter (2015/16), Fig. 10.3 digitised | peak 37.8 S, median 37.5 S, 50 % 38.2-36.4 S, 90 % 39.0-35.2 S (00:19 position) | peak 38.15 S, median 38.2 S, 90 % 39.4-37.3 S |
| UGIB 2020 LEP | 34.23 S 93.79 E | v1: ~4 deg further south (single-mode families). v2 (section 13): `p_v2` median 38.2 S, but 34.2 S fits as well as 38 S once one extra turn or a descent at 18:40 is allowed |
| Ashton et al. 2015 example | 34.7 S 93.0 E ("no more valid than many other routes") | constant-GS, re-track at each arc - not an autopilot mode |
| IG June 2014; Godfrey 2015 v15.1; Hardy 2015 (188 deg magnetic) | 36.0 S 88.6 E; 37.1 S 89.9 E; 38.1 S 87.4 E | Godfrey and Hardy fall inside our LNAV/CTT 90 % band (37.1-39.6 S); IG 2014 is ~1 deg north of it |
| CSIRO 2017 drift (not satcom) | 35.6 S 92.8 E | north of our satcom-only 90 % interval |

* **DSTG**: same peak latitude (~38 S) from a very different dynamics model (random manoeuvres +
  speed changes, prior at 18:01, not 18:22). Their pdf has a second mode near 36.2 S and a longer
  northern tail; ours is narrower because a single post-FMT mode at constant Mach is a much
  stronger constraint than DSTG's manoeuvre process. Our "equal-weight" and true-heading
  solutions populate the 34.8-36.7 S region that the DSTG tail covers.
* **UGIB 2020** (34.23 S): UGIB's route is now taken from the paper itself (section 13.1).
  * **Their route.** A descent to FL100 with the 18:40 call made while descending at 1,840 fpm on
    271 T, then a holding-speed traverse along the FIR boundaries via IGOGU, 6 N and BEDAX. After
    BEDAX, LNAV 180 T to the South Pole at LRC/FL390.
  * **How it was built.** The 19:41–00:11 leg was fitted to the satellite data, and BEDAX was
    chosen afterwards as the nearest waypoint to the fitted longitude. The earlier route was built
    by hand.
  * **Replayed through this model,** their route fits the BTO/BFO data as well as our best path
    (log L −3.55; BTO residuals agree with theirs to a few µs). The 18:40 BFO fits only because of
    the descent.
  * **The v1 statement "UGIB's solution needs a second turn"** was true only of the single-mode
    family. With waypoint and two-leg families added (section 13), the evidence-weighted posterior
    still peaks near 38 S. However:
    * 34.2 S is reachable at an equally good fit;
    * the specific BEDAX → 180 T route is disfavoured only if speed and altitude are held constant
      and the aircraft is level at 18:40;
    * allowing a descent at 18:40 costs no evidence and moves the median to 35.8 S.
  * **So the difference is a modelling choice, not a data discrepancy:** route structure, the 18:40
    vertical-speed assumption, the speed schedule, and UGIB's fuel/drift priors.
* **Ashton example**: not a single autopilot mode; agrees on the 19:41-00:11 BFOs to 2 Hz by
  construction.
* **Hardy 2015** (188 deg magnetic, 38.1 S 87.4 E): coincides with our constant-*true*-track
  solution (187 deg true, ~37.9 S). Our constant-magnetic-track mode, using the WMM2010 variation
  that grows from -1 deg to about -30 deg along the route, curves east and ends near 33.6 S, so that
  published path presumably treated magnetic variation differently (not verified).

## 11. Limitations (read before using `p`)

1. **Path families.**
   * v1 has one post-FMT lateral mode at constant Mach/FL. v2 adds waypoint routing and a generic
     second turn (section 13).
   * Every family is still at constant Mach/FL after the FMT and level at the 18:40 call.
     Speed/altitude changes enter only through the "machdrift" and "wideprior" variants and the
     d1840 sensitivity (section 13.7).
   * **Family selection, and above all the level-at-18:40 assumption, dominate the answer:**

     | weighting | median | 90 % interval |
     |---|---|---|
     | evidence weighting (`p_v2`) | 38.2 S | – |
     | families weighted equally | 37.0 S | 39.2–31.2 S |
     | descent allowed at 18:40 | 35.8 S | 38.1–30.9 S |

   * The BTO/BFO data do not discriminate between these.
2. Evidence weights depend on the noise model and on the (equal) mode priors; with measurement-
   only BTO noise (29 us) the LNAV/CTT dominance is even stronger (section 9).
3. 18:22 radar position and the 18:25-18:28 data are modelled crudely (straight pre-FMT leg); the
   pre-FMT speed is weakly constrained (350-520 kt) - it mainly trades against FMT time.
4. Winds: ERA5 only (no GDAS cross-check); wind error enters through the 30 us model-error term
   and the +-10 % wind-scaling variants.
5. AES magnetic variation: WMM2010; the 777 ADIRU uses its own (older) table - differences ~1 deg.
6. No fuel constraint (section 8); no debris drift (workstream B) or search coverage (C).
7. End-of-flight scenario weights (0.8/0.2) and kernel shapes are judgement calls documented
   above; layers are provided separately so they can be re-weighted.
8. 00:19:29 position is computed as if cruise continued to 00:19:29 (the descent began ~2 min
   earlier); the difference (<~15 NM) is inside the end-of-flight kernels.
9. The C-channel (call) BFOs share the R-channel bias prior; no C-channel calibration is public.
10. Only the public redacted log is used (no C/N0, BER, or previous-flight BFOs); the DSTG noise
    statistics from 20 previous flights are taken as published.

## 12. Reproduce

    .venv/bin/python -I scripts/satcom_get_era5.py          # ERA5 subset (~4 min)
    .venv/bin/python -I scripts/satcom_validate_bfo.py      # validation tables
    .venv/bin/python -I scripts/satcom_digitize_dstg.py     # DSTG Fig 10.3 digitisation
    for m in LNAV CTT CMT CTH CMH; do .venv/bin/python -I scripts/satcom_run_paths.py --mode $m --variant baseline --n 20000 --seed 41; done
    for v in bto29 no1828bfo no1827bto bfo4p3 bias25 wind90 wind110 wideprior machdrift; do for m in LNAV CTT CMT CTH CMH; do .venv/bin/python -I scripts/satcom_run_paths.py --mode $m --variant $v --n 10000 --seed 41; done; done
    .venv/bin/python -I scripts/satcom_posterior.py --sens  # grids, arc profile, figures, sensitivity
    .venv/bin/python -I scripts/satcom_profile.py           # profile likelihood, both passes (~40 min on 10 cores)

Each SMC run takes 5-10 min on one core (runs are independent; we ran 10 in parallel).

## 13. Waypoint and two-leg families (reviewer response)

**Critique.** "The satellite result comes mostly from which flight-path families you allow.
Single-mode paths from 18:22 can't represent a waypoint route like UGIB's, so 'UGIB needs a second
turn' is true by construction, and UGIB's own route already has that turn at BEDAX. ... A better
test is to add a family with an FMT, a waypoint and then a new track, and compare its evidence
directly."

**Short answer.**

* **The critique is right about the earlier UGIB statement**: it described the single-mode family,
  not the data.
* **Two families were added.** One is a *waypoint* family: FMT → direct to a published waypoint →
  a new lateral mode. The other is a *generic two-leg* family. Both use the same integrator, winds,
  likelihood, noise model, priors and SMC as the single-mode families.
* **Their evidence is comparable** to the best single-mode family (LNAV):
  * the waypoint family: Δ log Z = −0.6;
  * the two-leg family: Δ log Z = −1.7;
  * the best single waypoint route (FMT → MUTMI → about 184 T): +3.0.
* **They barely move the bulk of the posterior.**
  * The recommended `p_v2` has impact median **38.17 S** and 90 % interval **39.51–36.46 S**.
  * The v1 `p` has 38.36 S and 39.61–37.40 S.
* **The UGIB-like configuration in these families reproduces 34.2 S but fits poorly** (Δ = −18).
  This is BEDAX → 180 T at constant Mach/FL, level at 18:40.
* **The satellite data do not exclude 34.2 S**:
  * a two-leg or waypoint path fits there as well as at 38 S;
  * UGIB's own route, which descends during the 18:40 call and then slows to holding speed, fits
    as well as our best path;
  * allowing a descent at 18:40 costs no evidence and moves the posterior median to 35.8 S.
* **The ~38 S preference therefore comes from assumptions, not from a BTO/BFO misfit**: level
  flight at 18:40, and the prior volume over turns and speeds.

### 13.1 What UGIB 2020 actually assumes

Source: Ulich, Godfrey, Iannello, Banks, *The Final Resting Place of MH370*, 7 March 2020, 186 pp.
Copy in `data/raw/ugib2020/`, provenance in that folder's `SOURCE.md`. Page numbers are the printed
footers.

* **18:22:12 radar point:** 6.578 N 96.341 E on N571, FL385, LRC, 296 T (p. 4, Table E-1 p. 130).
  This is essentially our start point (6.578 N 96.341 E).
* **18:23:48–18:27:43:** a 15 NM right lateral offset from N571 (p. 31, p. 117).
* **18:29:00:** FLCH descent at 250 KIAS from FL385 towards FL100.
* **18:35:27:** at FL250, "DIRECT TO" IGOGU, a left turn to 269.7 T (p. 133).
* **First call, 18:39:55:** 7.518 N 94.583 E, FL163, **ROC −1,840 fpm**, GS 337 kt, **track 271 T**
  (Fig. 3, p. 4). The 18:40 call BFO is explained by the descent, not by a southerly track. UGIB
  excluded the call BFOs from their noise analysis "because there were sufficient degrees of freedom
  in our FMT Model to always zero the mean error" (p. 145).
* **18:41:39, IGOGU:** a 90° left turn to due south along the FIR boundary (94.4167 E).
  * End of descent at 18:43:41, FL100.
  * Then **holding speed (217 KIAS, about 257 kt GS)** past ANOKO (18:46:21) and NOPEK (18:53:52).
* **19:02:16, 6NFIR (6 N 94.4165 E):** a 90° right turn to due west along the 6 N FIR boundary.
* **19:10:27, 6NFIRWEST (6 N 93.7875 E):** a 90° left turn to 180 T, towards BEDAX. UGIB calls this
  the FMT (§E.3.7 p. 135).
* **19:19:04, BEDAX:** passed at FL100, holding speed. Before BEDAX, "a waypoint was added after BEDAX
  for the South Pole. That ensured the LNAV track was maintained at exactly 180 °T until fuel
  exhaustion" (p. 136).
* **19:23:50:** ECON climb (CI 52), top of climb FL390 at 19:41:21.
* **After that:** **LRC at FL390 (M ≈ 0.840–0.837), LNAV great circle 180.00 T along 93.7875 E to fuel
  exhaustion at 00:17:30**. LEP 34.2342 S 93.7875 E (pp. 4–5, 168).
* **The 19:41–00:11 "SIO Route" is fitted to the satellite data only** (start position, bearing,
  speed mode and FL free; start "after the first SATCOM call ended at 18:40:56", p. 11).
  * The fitted longitude was 93.760 E, and "three waypoints are close – ISBIX, BEDAX, and BEBIM ...
    we therefore selected BEDAX" (p. 162).
  * The 18:22–19:41 "FMT Route" is a hand-built hypothesis, "developed (over a period of years)"
    (p. 127).
* **UGIB's own statement on the no-descent alternative** (p. 109): "the 18:40 BFO can only be
  satisfied with zero ROD by a SSW or SSE track ... A more-or-less direct track to the vicinity of
  BEDAX would arrive far too soon at cruising speed, so a circuitous path or a Holding pattern is
  required to arrive at the 19:41 location on time."
  * Their "simple FMT" alternative (no descent, turns to match the call BFO, §7.1 p. 41) moves the
    satcom + fuel peak to 32.2 S (176.5 T).

### 13.2 Waypoints

Coordinates are in `data/raw/waypoints_indian_ocean/waypoints.csv`, with provenance and per-point
URLs in `SOURCE.md` there. Verification status:

* **Malaysian AIP:** points in the Kuala Lumpur FIR are confirmed against the pre-2014 AIP
  (ENR 3.1/3.3, AMDT 2010–12, copies in `data/raw/ugib2020/`).
* **Jakarta, Colombo and Melbourne FIRs:** the Indonesian, Sri Lankan and Australian AIPs could not
  be reached. These points rest on secondary sources: opennav.com and R. Godfrey's 2016 waypoint
  table (duncansteel.com/archives/2189), which agree to the arcsecond. AirNav Indonesia lists the
  Jakarta-FIR names but gives no coordinates.
* **DOLEM** has a single secondary source.
* **Not found:** no coordinates for PAKRA (Godfrey 2021) or ULAGO, and OPOVI is a Penang procedure
  point. None of these is used.

**Regional set (primary, 28 points).** It holds every published fix in the table with 15 S ≤ lat
≤ 8 N and 88 E ≤ lon ≤ 97 E, except MEKAR, which is 10 NM behind the radar point. The prior over
the set is uniform. **Literature set (13).** It holds the points of the regional set that published
MH370 routes have named: UGIB 2020; Iannello 2014/2017; Godfrey 2016/2021; Ashton et al. 2015;
ATSB 2014.

Regional set (28) with coordinates and sources:

| waypoint | lat | lon | DMS | source | verified | in literature set |
|---|---|---|---|---|---|---|
| SAMAK | 7.9783 | 94.4167 | 07 58 42.00 N / 094 25 00.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) |  |
| IGOGU | 7.5169 | 94.4167 | 07 31 01.00 N / 094 25 00.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) | yes |
| ANOKO | 7.1361 | 94.4161 | 07 08 10.00 N / 094 24 58.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) | yes |
| NILAM | 6.7564 | 95.9764 | 06 45 23.00 N / 095 58 35.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) | yes |
| NOPEK | 6.6039 | 94.4167 | 06 36 14.00 N / 094 25 00.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) | yes |
| SANOB | 6.5861 | 95.6692 | 06 35 10.00 N / 095 40 09.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) |  |
| IGEBO | 6.2358 | 95.0808 | 06 14 09.00 N / 095 04 51.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) | yes |
| POVUS | 6.0000 | 94.6661 | 06 00 00.00 N / 094 39 58.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) | yes |
| ANSAX | 6.0000 | 95.5081 | 06 00 00.00 N / 095 30 29.00 E | Malaysian AIP ENR 3.1/3.3 (AMDT 2010-12) | Y (AIP) | yes |
| MEMAK | 6.0000 | 93.0833 | 06 00 00.00 N / 093 05 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| BEDAX | 5.3643 | 93.7876 | 05 21 51.58 N / 093 47 15.27 E | opennav.com + Godfrey 2016 table | N (secondary) | yes |
| TOPIN | 5.1500 | 92.0000 | 05 09 00.00 N / 092 00 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| BULVA | 4.5667 | 94.0000 | 04 34 00.00 N / 094 00 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| NIXUL | 4.0081 | 92.0000 | 04 00 29.00 N / 092 00 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| NISOK | 3.0483 | 92.0000 | 03 02 54.00 N / 092 00 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) | yes |
| DOLEM | 2.5606 | 96.5019 | 02 33 38.00 N / 096 30 07.00 E | opennav.com (single source) | N (secondary) | yes |
| SELSU | 1.1833 | 92.0000 | 01 11 00.00 N / 092 00 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| UPROB | 0.9433 | 94.5817 | 00 56 36.00 N / 094 34 54.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| ISBIX | 0.3667 | 93.6751 | 00 22 00.27 N / 093 40 30.39 E | opennav.com + Godfrey 2016 table | N (secondary) | yes |
| ODIRU | -0.3303 | 95.1009 | 00 19 49.14 S / 095 06 03.40 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| KETIV | -0.7000 | 92.0000 | 00 42 00.00 S / 092 00 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| PILEK | -2.9733 | 95.1300 | 02 58 24.00 S / 095 07 48.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| POSOD | -3.4917 | 94.1650 | 03 29 30.00 S / 094 09 54.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| MUTMI | -4.1333 | 92.9783 | 04 08 00.00 S / 092 58 42.00 E | opennav.com + Godfrey 2016 table | N (secondary) | yes |
| PIPOV | -4.3683 | 92.5417 | 04 22 06.00 S / 092 32 30.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| PIBED | -5.3367 | 90.7333 | 05 20 12.00 S / 090 44 00.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| BEBIM | -10.6450 | 93.8350 | 10 38 42.00 S / 093 50 06.00 E | opennav.com + Godfrey 2016 table | N (secondary) |  |
| RUNUT | -13.8267 | 91.3800 | 13 49 36.00 S / 091 22 48.00 E | opennav.com + Godfrey 2016 table | N (secondary) | yes |

### 13.3 Method: two new families with the same machinery

**Module and runner.** The new families are in `src/mh370/satcom_routes.py`; the runner is
`scripts/satcom_run_routes.py`. Several things are shared with the single-mode families, unchanged:

* the 18:22:12 radar-point prior and the pre-FMT straight leg;
* the ERA5 winds and temperatures;
* the WGS84 midpoint integrator (120 s steps, exact measurement and switch times);
* the ground-velocity law for each lateral mode, which is the same code;
* the measurements, the noise model (BTO 42/69 µs, BFO 7 Hz, common bias N(152, 3²) Hz
  marginalised), and the likelihood class;
* the adaptive-tempering SMC sampler and its evidence estimator.

The prior specification is imported from `scripts/satcom_run_paths.py`, so every shared parameter
has an identical prior.

* **(a) Waypoint family `WPT`.**
  * Last radar → FMT at t_fmt (same prior) → LNAV "direct to" a published waypoint W, at constant
    Mach and FL. The leg is steered along the great-circle bearing from the current position to W,
    so it arrives exactly at W.
  * At W (passage detected in the integration, snap ≤ 0.2 km) the aircraft switches to mode2. The
    options are LNAV great circle with initial azimuth θ2 at W, which includes "W → South Pole" at
    θ2 = 180; constant true track; constant magnetic track; constant true heading; or constant
    magnetic heading.
  * θ2 is free, and Mach and FL stay constant across W.
  * If W is not reached by 00:19:29, the path is simply direct-to W throughout.
* **(b) Generic two-leg family `TWO`.** FMT → constant true track θ1 until t2 → constant true
  track θ2 until 00:19:29, with t2 = t_fmt + u2·(00:19:29 − t_fmt).

**Priors (all proper; the extra structure carries its prior volume, so the evidence includes the
Occam penalty):**

| parameter | single-mode (existing) | WPT | TWO |
|---|---|---|---|
| lat0, lon0 at 18:22:12 | N(MEKAR+10 NM, 10 NM) | same | same |
| trk_pre, gs_pre | U(270, 340) deg, U(350, 520) kt | same | same |
| t_fmt | U(18:22:42, 19:40:03) | same | same |
| lateral mode | 1 of 5 (each its own family) | mode2: uniform over the 5 modes (prob. 1/5 each) | CTT → CTT |
| waypoint W | – | uniform over the 28-point regional set (prob. 1/28 each) | – |
| θ (track/heading) | U(140, 230) deg | θ2 ~ U(140, 230) deg after W; leg 1 has no free direction (set by W) | θ1, θ2 ~ U(140, 230) deg each |
| second-turn time | – | determined by W | u2 ~ U(0, 1), i.e. t2 uniform on (t_fmt, 00:19:29) |
| Mach, FL | U(0.70, 0.86), U(300, 400) | same (constant across W) | same (constant across the turn) |

**Evidence.**

* **Waypoint components.** Each (W, mode2) pair is run as its own SMC with the same settings as the
  existing families.
  * Screening run for all 140 components: N = 5,000.
  * Every component that carries ≥ 0.5 % of the family evidence is re-run at N = 20,000 with two
    seeds.
  * The family evidence is the prior-weighted mean, Z_WPT = (1/140) Σ Z(W, mode2). That is the
    marginal likelihood under the uniform prior over the discrete set. The log(140) = 4.9 nats of
    "choice" are part of it.
* **TWO** is a single 10-parameter SMC (N = 20,000, three seeds).
* **Mixture.** All families have equal prior probability (1/7). The posterior weight of a family is
  ∝ Z_family. Within a family, components are weighted by their own evidence.

**Validation (`scripts/satcom_routes_check.py`, `outputs/satcom/routes_sanity_check.txt`).**

1. TWO with the second turn at 00:19:29 is bit-identical to the single-mode CTT model.
2. TWO with θ2 = θ1 and a random turn time differs from CTT by ≤ 0.02 µs BTO and 0.0001 Hz BFO
   (≤ 5 m at 00:19:29).
3. WPT with mode2 = LNAV continuing on the same great circle at W reproduces single-mode LNAV to
   0.8–1.1 km at 00:19:29 (BEDAX), 1.2–2.0 km (ISBIX) and 2.8–3.6 km (RUNUT).
   * The difference is entirely the existing LNAV course law, which follows a great circle fixed at
     the FMT and drifts 0.4–0.9 km cross-track per ~150 NM because the course is spherical and the
     integration ellipsoidal.
   * The new direct-to leg arrives exactly at W (snap ≤ 175 m).
4. **Evidence-level check:** a TWO run with θ2 tied to θ1 must give the CTT single-mode evidence,
   since u2 then integrates out to 1. Result: log Z = −19.02 and −19.05 (two seeds, N = 20,000),
   against −19.05 (baseline) and −19.05 (replicate) for CTT. The arc-crossing median is also the
   same: 37.87 S.

5. **Convergence.** Several runs were repeated with 2–3 independent seeds: LNAV, CTT, TWO, the
   tied check, the UGIB-like run, and the 21 waypoint components that carry ≥ 0.5 % of the family
   evidence. Those 21 components were also run at two particle counts. The remaining 119 waypoint
   components (together < 1 % of the family) and CMT/CTH/CMH have one run each.
   * Single-mode LNAV gives −18.51 and −18.45 at N = 20,000, and −18.58 at N = 5,000.
   * CTT gives −19.05 and −19.05 (N = 20,000) and −18.95 (N = 5,000).
   * TWO gives −20.12, −20.30 and −20.11.
   * The waypoint components agree to ≤ 0.1 between seeds and to ≤ 0.25 between N = 5,000 and
     N = 20,000. For example, MUTMI/CTT gives −15.58 and −15.48 at N = 20,000 and −15.66 at
     N = 5,000.
   * SMC ends every tempering stage at ESS = N/2 by construction, followed by 4–25 random-walk
     moves; after the final resampling 57–78 % of the particles are unique.
   * The family log-evidences are reproducible to about ±0.15. Differences smaller than about 0.3
     are therefore treated below as "no difference".

### 13.4 Evidence table (baseline noise model; `evidence_v2.csv`, `evidence_components_v2.csv`)

**How to read the table.**

* **Δ** is log Z minus the best single-mode family (LNAV, −18.51). **w** is the family's posterior
  weight when the 7 families have equal prior.
* **Best fit** is the highest-likelihood posterior particle. Its columns give:
  * log L;
  * BTO RMS (12 values) and BFO RMS (8 values, after the fitted bias);
  * the residuals of the 18:28:15 BFO and the 18:40 call BFO;
  * the latitude where that path crosses the 7th arc.
* **Arc** is the posterior latitude of the 00:19:29 crossing.

| family | log Z (replicates) | Δ | w | best log L | BTO / BFO RMS | BFO 18:28 / 18:40 | best-fit crossing | FMT median (90 %) | arc median | arc 50 % | arc 90 % | P(north of 36 S) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LNAV great circle (single mode) | -18.51 (-18.51 -18.45) | +0.00 | 0.433 | -3.90 | 30 µs / 4.0 Hz | -2.0 / +1.1 Hz | 37.19 S | 18:37 (18:32-18:39) | 38.42 S | 38.9–38.0 S | 39.6–37.5 S | 0.00 |
| constant true track (single mode) | -19.05 (-19.05 -19.05) | -0.54 | 0.253 | -4.11 | 30 µs / 4.2 Hz | +1.5 / +1.6 Hz | 37.38 S | 18:38 (18:33-18:39) | 37.87 S | 38.2–37.5 S | 38.8–37.1 S | 0.00 |
| constant magnetic track (single mode) | -28.75 (-28.75) | -10.24 | 0 | -10.02 | 57 µs / 3.4 Hz | +3.8 / -1.6 Hz | 33.53 S | 18:39 (18:37-18:40) | 33.64 S | 33.8–33.5 S | 34.1–33.2 S | 1.00 |
| constant true heading (single mode) | -29.21 (-29.21) | -10.70 | 0 | -9.95 | 54 µs / 5.4 Hz | +9.8 / +0.1 Hz | 36.02 S | 18:38 (18:35-18:40) | 35.69 S | 36.1–35.3 S | 36.6–34.8 S | 0.72 |
| constant magnetic heading (single mode) | -51.37 (-51.37) | -32.85 | 0 | -29.07 | 96 µs / 5.1 Hz | +10.0 / -5.0 Hz | 30.86 S | 18:39 (18:38-18:40) | 31.18 S | 31.4–31.0 S | 31.7–30.8 S | 1.00 |
| **waypoint (WPT)**, 28 waypoints x 5 modes | -19.13 (–) | -0.62 | 0.232 | -3.06 | 23 µs / 3.6 Hz | -2.1 / +0.1 Hz | 36.76 S | 18:34 (18:25-18:39) | 37.38 S | 37.9–36.8 S | 38.8–34.7 S | 0.12 |
| **generic two-leg (TWO)** | -20.17 (-20.12 -20.30 -20.11) | -1.66 | 0.0823 | -2.66 | 26 µs / 2.9 Hz | -2.1 / -0.8 Hz | 34.27 S | 18:36 (18:29-18:39) | 37.75 S | 38.4–36.9 S | 39.3–35.0 S | 0.11 |

**Sub-families and specific configurations** (same columns; these rows are not extra families):

| configuration | log Z (replicates) | Δ | best log L | BTO / BFO RMS | BFO 18:28 / 18:40 | best-fit crossing | FMT median | W passage / 2nd turn (median) | arc median | arc 90 % |
|---|---|---|---|---|---|---|---|---|---|---|
| WPT, mode2 = LNAV only | -18.26 (–) | +0.25 | -3.18 | 23 µs / 3.6 Hz | -3.3 / +0.6 Hz | 36.06 S | 18:35 | 19:55 | 37.61 S | 39.0–35.7 S |
| WPT, mode2 = CTT only | -18.26 (–) | +0.25 | -3.06 | 23 µs / 3.6 Hz | -2.1 / +0.1 Hz | 36.76 S | 18:34 | 19:56 | 37.25 S | 38.4–35.6 S |
| WPT, mode2 = CMT only | -20.85 (–) | -2.34 | -4.33 | 32 µs / 3.2 Hz | +0.6 / -3.5 Hz | 31.92 S | 18:32 | 20:12 | 32.36 S | 33.4–31.3 S |
| WPT, mode2 = CTH only | -22.55 (–) | -4.04 | -4.62 | 32 µs / 3.4 Hz | +0.7 / -1.1 Hz | 35.07 S | 18:30 | 20:04 | 34.21 S | 35.6–32.7 S |
| WPT, mode2 = CMH only | -40.17 (–) | -21.66 | -18.01 | 71 µs / 5.2 Hz | -10.4 / -5.5 Hz | 29.19 S | 18:39 | 19:49 | 29.77 S | 30.4–29.1 S |
| WPT, literature set (13 x 5) | -18.45 (–) | +0.06 | -3.06 | 23 µs / 3.6 Hz | -2.1 / +0.1 Hz | 36.76 S | 18:34 | 19:59 | 37.43 S | 38.8–34.4 S |
| WPT, BEDAX only (x 5 modes) | -21.80 (–) | -3.29 | -5.63 | 35 µs / 4.2 Hz | -7.8 / -1.5 Hz | 35.72 S | 18:38 | 19:00 | 36.24 S | 36.8–32.9 S |
| WPT, best single component (MUTMI/CTT) | -15.53 (-15.58 -15.48) | +2.98 | -3.06 | 23 µs / 3.6 Hz | -2.1 / +0.1 Hz | 36.76 S | 18:35 | 20:04 | 37.01 S | 38.3–35.2 S |
| WPT, BEDAX/LNAV (theta2 free) | -21.23 (-21.23) | -2.72 | -5.90 | 38 µs / 4.0 Hz | -6.6 / -1.7 Hz | 36.10 S | 18:38 | 19:00 | 36.40 S | 36.9–35.8 S |
| WPT, BEDAX/CTT (theta2 free) | -20.82 (-20.82) | -2.31 | -5.63 | 35 µs / 4.2 Hz | -7.8 / -1.5 Hz | 35.72 S | 18:38 | 19:00 | 36.23 S | 36.7–35.7 S |
| UGIB-like: BEDAX -> LNAV 180 T (theta2 fixed) | -36.69 (-36.63 -36.75) | -18.18 | -14.54 | 51 µs / 7.8 Hz | -20.5 / -2.2 Hz | 34.23 S | 19:03 | 19:22 | 34.27 S | 34.4–34.1 S |
| check: TWO with theta2 = theta1 (must equal CTT) | -19.04 (-19.02 -19.05) | -0.52 | -4.08 | 31 µs / 4.1 Hz | -0.8 / +1.7 Hz | 37.39 S | 18:38 | 21:28 | 37.87 S | 38.8–37.1 S |

**The 18:25–18:28 BFOs that the likelihood excludes** (SDU warm-up; see section 4) have similar
best-fit residuals in every family. In order, the values at 18:25:27, 18:25:34, 18:27:03, 18:27:04,
18:27:08 and 18:28:05 are about −2, +129, +31, +30, +27 and −1 Hz (LNAV, CTT, WPT and TWO alike).
No family explains the +30 Hz at 18:27, consistent with the OCXO warm-up transient. The UGIB-like
configuration is worse at 18:28 (−20 Hz) because it needs a pre-FMT track of about 335 T.

**Waypoints that matter.** Of the 140 waypoint components, 21 carry 99 % of the family evidence
(`fig_evidence_by_waypoint_v2.png`). Shares of the family, by waypoint:

| waypoint | share | note |
|---|---|---|
| MUTMI (4.13 S 92.98 E) | 0.54 | 0.50 for LNAV/CTT after W |
| ISBIX | 0.10 | |
| IGOGU | 0.08 | |
| POVUS, ANOKO, NOPEK, SAMAK | 0.05 each | Kuala Lumpur FIR-boundary fixes: in effect, "the FMT happens at a published fix" |
| BULVA | 0.035 | |
| RUNUT | 0.018 | |
| IGEBO | 0.011 | |
| **BEDAX** | **0.0025** | |

Waypoints on 92 E (TOPIN, NIXUL, NISOK, SELSU, KETIV), in the east (DOLEM, ODIRU, PILEK) and
PIBED have log Z < −60. The components with LNAV or CTT after W cross at 37.0–38.9 S, the same band
as the single-mode families. MUTMI/CMT (32.3 S, 0.035 of the family) and MUTMI/CTH (34.1 S, 0.006)
supply the family's northern tail.

### 13.5 The UGIB-like configuration

* **This model: FMT → direct to BEDAX → LNAV 180 T (θ2 fixed), constant Mach/FL, level flight.**
  * log Z = −36.7 (−36.63 / −36.75), which is **Δ = −18.2**.
  * It reproduces 34.2 S geometrically: posterior crossing 34.27 S (90 %: 34.35–34.14 S). The
    93.79 E meridian meets the 7th arc there.
  * The fit is poor. The highest-likelihood posterior particle has log L = −14.54, against −3.90 for single-mode LNAV. It has BTO RMS 51 µs and an 18:28:15 BFO residual of −20.5 Hz, and it needs the 18:22 position about 40 NM (4 sigma) north of the radar fix. The best fit with the radar-point prior included (Nelder-Mead polish, `bestfit_polished_v2.csv`) is worse on likelihood: log L = -17.30, BTO RMS 57 µs, BFO RMS 8.3 Hz, 18:28:15 BFO -22.0 Hz, 18:40 BFO -2.5 Hz. That path flies a pre-FMT track of 337 T at 520 kt, makes the FMT at 18:40, passes BEDAX at 19:12:33, then flies 180 T at M0.805 FL400 and crosses at 34.23 S. Its BTO residuals (µs) are -32 +32 -8 -7 -13 -31 +0 -129 -125 -23 +44 +29, so it misses 20:41 and 21:41 by about 125 µs.
  * At constant cruise speed, a near-direct leg from the FMT area to BEDAX arrives about 20 min too
    early for the 19:41 position on the meridian: the BEDAX/LNAV and BEDAX/CTT posteriors pass BEDAX at about 19:00, while a 180 T leg that fits the later arcs must pass that latitude at about 19:20–19:22. The only way to fit is a pre-FMT detour to the
    north, which spoils the 18:28 BFO, or a turn after the 18:40 call, which spoils the 18:40 BFO.
  * UGIB state exactly this for a no-descent route (p. 109).
* **BEDAX with θ2 free:** log Z = −20.8 (CTT) and −21.2 (LNAV), Δ ≈ −2.5. The crossing is at
  36.2–36.4 S (θ2 ≈ 183.5 T). The 180 T track is not preferred once the speed is held constant.
* **UGIB's own published route, replayed through this likelihood** (`scripts/satcom_ugib_replay.py`,
  `ugib_replay.csv`; UGIB Figs. 3–4 states):
  * **log L = −3.55.** That is as good as the best single-mode fit (−3.90).
  * BTO RMS is 29 µs overall and 36 µs for 19:41–00:11. UGIB report 35.6 µs, and the residuals
    agree term by term in magnitude: ours are −9 / −45 / −24 / +55 / −31 µs, theirs +5.5 / +41.4 /
    +21.4 / −57.4 / +29.2 with the opposite sign convention. This independently cross-validates
    the two forward models.
  * BFO RMS is 2.4 Hz; the 18:28:15 residual is −1.1 Hz and the 18:40 call residual −0.3 Hz.
  * **The 18:40 call fits only because of UGIB's descent** (−1,840 fpm, track 271 T). With level
    flight at that moment the call BFO misses by −39 Hz and log L drops to −20.3.
  * The 19:41 timing works only because of the FL100 holding-speed segment.

### 13.6 Profile likelihood: can the new families reach 34.2 S? (`profile_likelihood_v2.csv`)

The table gives −2 Δlog L relative to the best single-mode fit of section 7 (log L = −3.72). Each
value is the best fit found by differential evolution with the 00:19:29 latitude imposed (2 seeds).
These are upper bounds; DE can stall.

| configuration | 40 | 39 | 38 | 37 | 36 | 35 | 34.23 | 33 | 32 | 31 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| two-leg (TWO) | 1.7 | -0.3 | -0.5 | -1.8 | -2.2 | -2.5 | -2.4 | -1.9 | -1.1 | -0.1 | 40.7 |
| WPT MUTMI → CTT | 16.6 | 1.9 | -0.5 | -1.4 | -1.2 | -0.3 | 1.5 | 6.4 | 12.0 | 20.3 | 27.3 |
| WPT MUTMI → LNAV | 5.0 | 1.0 | -0.6 | -1.2 | -1.2 | -0.3 | 1.1 | 4.9 | 9.2 | 15.0 | 75.4 |
| WPT ISBIX → CTT | 40.4 | 8.2 | 1.9 | -0.0 | 3.7 | 12.9 | 22.3 | 69.4 | 74.2 | 77.1 | 79.5 |
| WPT IGOGU → CTT | 185.0 | 64.9 | 9.1 | 1.0 | 20.1 | 78.5 | 104.0 | 151.0 | 116.5 | 116.1 | 130.9 |
| WPT BEDAX → CTT | 217.5 | 98.8 | 36.9 | 11.3 | 4.1 | 12.3 | 41.8 | 46.3 | 50.2 | 60.7 | 80.5 |
| WPT BEDAX → LNAV 180 T (UGIB-like) | (4350) | (2843) | (1674) | (837) | (322) | (77) | 27.2* | (196) | (548) | (1102) | (1877) |

\* BEDAX → 180 T always ends near 34.3 S (the 93.79 E meridian), so only the 34.23 S column is meaningful. That value is the Nelder-Mead polish of the best SMC particles (`bestfit_polished_v2.csv`). DE stalled at a worse optimum for this configuration; its values are shown in brackets.

**Single-mode LNAV / CTT, for reference (section 7):**

| configuration | 40 | 39 | 38 | 37 | 36 | 35 | 34.23 | 33 | 32 | 31 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| LNAV | 5.3 | 2.2 | 0.3 | 1.5 | 11.8 | 44.6 | 60.8 | 68.2 | 73.5 | 78.1 | 81.6 |
| CTT | 12.3 | 5.2 | 1.6 | 1.0 | 8.9 | 39.6 | 61.1 | 69.3 | 74.8 | 79.1 | 82.5 |

**One free extra turn is enough to make the likelihood flat from 39 S to 31 S.**

* **Two-leg family at 34.23 S:** −2Δlog L = −2.4, i.e. *better* than any single-mode fit. The fit
  has BTO RMS 26 µs and BFO RMS 2.8 Hz, with the 18:40 residual at −1.3 Hz.
  * The path: FMT 18:40, 185.3 T, then a 7.7° left turn at 21:08 to 177.5 T, M 0.76, FL346.
* **FMT → MUTMI → about 178.5 T** reaches 34.24 S at +1.1 to +1.5.
* The highest-likelihood particle of the whole two-leg posterior crosses at 34.27 S (log L -2.66).

So in these families the BTO/BFO likelihood does not exclude 34.2 S. It strongly disfavours that
latitude only for single-mode paths and for BEDAX → 180 T at constant Mach/FL.

### 13.7 Sensitivity: a descent at the 18:40 call ("d1840")

**Why this test.** All families above are level at 18:40, and UGIB's route depends on a descent
there (section 13.5).

**Variant.** It applies to every family, with the same data:
* a free rate of climb at the 18:40 call, ROC ~ U(−4000, 0) fpm, which enters the BFO through
  the uplink Doppler of the vertical velocity;
* for the waypoint family, the WPTS form: the FMT → W leg is flown at its own constant ground
  speed gs1 ~ U(220, 520) kt, which covers a slow, low-level traverse such as UGIB's, with cruise
  Mach/FL after W.

**Comparability.** Same data, so the log-evidences are directly comparable with the baseline rows.

| family (d1840) | log Z | Δ vs baseline LNAV | w (7 families, d1840) | best log L | arc median | arc 90 % | P(north of 36 S) | ROC at 18:40, median (90 %) |
|---|---|---|---|---|---|---|---|---|
| LNAV great circle (single mode) | -18.47 | +0.04 | 0.4 | -3.14 | 35.95 S | 38.2–31.5 S | 0.51 | −2786 (−3443 to −397) |
| constant true track (single mode) | -18.51 | -0.00 | 0.385 | -3.20 | 35.45 S | 37.6–31.0 S | 0.62 | −2799 (−3443 to −476) |
| constant magnetic track (single mode) | -22.99 | -4.48 | 0.0044 | -7.11 | 29.79 S | 32.3–24.9 S | 1.00 | −2890 (−3537 to −2177) |
| constant true heading (single mode) | -27.13 | -8.62 | 0.0001 | -10.69 | 29.40 S | 34.7–25.1 S | 0.99 | −2784 (−3482 to −1908) |
| constant magnetic heading (single mode) | -29.68 | -11.17 | 0 | -11.86 | 26.62 S | 28.4–23.2 S | 1.00 | −2959 (−3577 to −2320) |
| **waypoint, own-speed leg (WPTS)**, 28 waypoints x 5 modes | -19.73 | -1.22 | 0.114 | -1.95 | 36.24 S | 37.7–29.8 S | 0.46 | −2478 (−3355 to −179) |
| **generic two-leg (TWO)** | -19.88 | -1.37 | 0.0974 | -1.88 | 34.74 S | 37.5–29.9 S | 0.71 | −2763 (−3443 to −1730) |
| WPTS, BEDAX only (x 5 modes) | -18.35 | +0.17 | – | -3.30 | 34.94 S | 36.0–33.4 S | 0.95 | |
| WPTS, best single component (ISBIX/CTT) | -16.81 | +1.71 | – | -2.61 | 34.89 S | 37.1–30.6 S | 0.73 | |
| UGIB-like BEDAX -> LNAV 180 T, cruise-speed leg (WPT) | -14.68 (-14.68) | +3.83 | – | -3.62 | 34.29 S | 34.4–34.2 S | 1.00 | |
| UGIB-like BEDAX -> LNAV 180 T, own-speed leg (WPTS) | -14.73 (-14.71 -14.75) | +3.78 | – | -3.63 | 34.29 S | 34.4–34.2 S | 1.00 | |

**Reading the d1840 variant.**

* **The evidence does not change.** The single-mode families give LNAV −18.47 and CTT −18.51,
  against −18.51 and −19.05 for the level baseline. Every family is within ±0.6 of its level value.
  Over all 7 families, the Bayes factor "descent allowed" : "level" is 1.1. **The satellite data
  cannot tell whether the aircraft was level or descending during the 18:40 call.**
* **The posteriors use the freedom.**
  * The 18:40 ROC has a median of about −2,800 fpm in every single-mode family. Only 4 % of the
    LNAV/CTT posterior keeps |ROC| < 300 fpm.
  * The FMT then moves after the call (LNAV/CTT medians 18:47–18:49), with the 18:40 BFO explained
    by the descent on the pre-FMT track, as UGIB do.
  * The crossing moves north:
    * LNAV: 35.95 S (90 %: 38.2–31.5 S).
    * CTT: 35.45 S (90 %: 37.6–31.0 S).
    * The 7-family mixture (`p_v2_sens_descent1840`): impact median **35.82 S** (50 %: 36.98–34.16 S;
      90 %: 38.07–30.93 S; peak 36.95 S), compared with 38.17 S for `p_v2`.
* **BEDAX → LNAV 180 T fits as well as anything once a descent is allowed.**
  * The best-fit log L is −3.62, crossing at 34.30 S.
  * As a point hypothesis (BEDAX and 180 T fixed) its evidence is −14.68 with a cruise-speed leg
    and −14.73 with its own-speed leg. That is Δ = +3.8 over the best baseline family.
  * The slow leg is not needed: the FMT moves to about 18:52–18:57 and BEDAX is reached on time at
    cruise speed.
  * Caveat: BEDAX and 180.00 T were *selected by UGIB after fitting the same data* (UGIB pp. 162,
    164), so the point evidence includes a selection bonus.
  * Counted as one of 140 a-priori waypoint/mode combinations with θ2 free, the WPTS family evidence
    is −19.73 (Δ −1.2), and BEDAX/LNAV with θ2 free is −17.35 (Δ +1.2).
  * In the WPTS family, BEDAX carries 0.14 of the family weight and ISBIX 0.26 (baseline WPT: 0.0025).

### 13.8 Interpretation

**Do the new families have comparable or higher evidence? Yes.**

* **The waypoint family is comparable to the best single-mode family.** Its evidence is −19.13
  against −18.51 for LNAV (Δ = −0.6), after paying log 140 ≈ 4.9 nats for the uniform choice of
  waypoint and mode.
  * Restricted to the 13 waypoints named in published MH370 routes it is −18.45 (Δ +0.06). That
    set was chosen with hindsight.
  * Its best components beat every single-mode family: FMT → MUTMI → CTT or LNAV (Δ ≈ +3.0), ISBIX
    (+1.3), IGOGU (+1.2).
* **The two-leg family scores Δ = −1.7.** That is a Bayes factor of about 5, not decisive.
* **These families hardly change where the bulk of the mass lies.**
  * Their crossing medians are 37.4 S (waypoint) and 37.8 S (two-leg).
  * Their best components fly about 188–191 T from an FMT at 18:30–18:40, then turn a few degrees
    left.
  * The data mildly favour a small mid-flight left turn over a single straight leg, but not a
    different end point.

**How the recommended arc-latitude distribution changes.**

* **`p_v2`.** The family weights are LNAV 0.43, CTT 0.25, waypoint 0.23 and two-leg 0.08 (the
  magnetic and heading modes ≈ 0).
  * Impact median **38.17 S**, 50 % 38.69–37.65 S, **90 % 39.51–36.46 S**.
  * For comparison, `p` gives 38.36 S, 50 % 38.83–37.93 S, 90 % 39.61–37.40 S.
  * The peak barely moves (38.15 S against 38.25 S). The northern 90 % bound moves about 0.9°
    north.
  * P(impact north of 36 S) goes from ~0 to 0.03.
* **Families weighted equally** (`p_v2_equal_families`): median 37.0 S, 90 % 39.2–31.2 S,
  P(north of 36 S) = 0.40.
* **Descent allowed at 18:40** (`p_v2_sens_descent1840`): median 35.8 S, 90 % 38.1–30.9 S,
  P(north of 36 S) = 0.53, P(33.75–34.75 S) = 0.12.

**What this says about UGIB 2020 (34.23 S): the corrected framing.** The earlier statement in this
README, "UGIB's route implies a second turn ... outside a single-mode family", was true only by
construction of that family. The correct statements are about which families the data favour:

1. **Within these families, the posterior concentrates at about 36.5–39.5 S.** This covers every
   family that flies constant Mach and FL after the FMT and is level during the 18:40 call
   (single-mode, waypoint, two-leg).
   * The specific UGIB-like configuration (FMT → BEDAX → 180 T) is strongly disfavoured (Δ = −18).
   * Its best fits miss the 18:28 BFO by about 20 Hz, or two BTOs by about 125 µs, because at
     constant cruise speed it reaches BEDAX about 20 min early. UGIB say the same of such routes
     (p. 109).
2. **The BTO/BFO data are not what rules out 34.2 S.**
   * A generic two-leg path, or a waypoint route (FMT → MUTMI → about 178.5 T), fits at 34.2 S as
     well as the best single-mode path fits at 38 S (section 13.6).
   * The single highest-likelihood two-leg path crosses at 34.3 S.
   * Most posterior mass stays near 38 S because a much larger share of each family's prior volume
     fits there. The 34.2 S fits need an FMT right at the 18:40 call, a specific later turn and
     M ≈ 0.75–0.78.
   * That is a prior-volume effect. It inherits the (uniform, but arbitrary) priors on turn time,
     track and Mach.
3. **UGIB's own route fits the data as well as any path here** (log L −3.55 against −3.90).
   * It explains the 18:40 BFO with a descent.
   * Allowing such a descent costs nothing in evidence. With it, BEDAX → 180 T is among the
     best-supported configurations, and the combined median moves to 35.8 S.
4. **On satellite data alone, this analysis cannot discriminate between ~38 S and ~34 S.**
   * The assumptions that decide it are (a) level flight versus a descent during the 18:40 call,
     and (b) the prior over route complexity: the number and timing of turns, and speed/altitude
     changes.
   * UGIB resolved this with fuel, debris-drift and aerial-search constraints that this layer does
     not use. The DSTG resolved it with its dynamics prior.
   * Those are legitimate inputs, but they are not satellite evidence.
   * Users of `p_v2` should treat `p_v2_sens_descent1840` as a structural alternative with equal
     support from the satellite data. A 50/50 mixture of the two is the even-handed choice if level
     flight and descent at 18:40 are considered equally likely a priori.

### 13.9 Files

**New variables in `data/derived/satcom_posterior.nc`.** All existing variables are unchanged.
Every variable sums to 1. The end-of-flight model is the same as for `p` (section 5).

| variable | content |
|---|---|
| `p_v2` | **recommended v2**: evidence-weighted over 7 families with equal family priors; 0.8 uncontrolled + 0.2 glide |
| `p_v2_uncontrolled`, `p_v2_glide` | the two end-of-flight components of `p_v2` |
| `p_v2_arc0019` | aircraft position at 00:19:29 under the v2 family mixture |
| `p_v2_equal_families` | as `p_v2`, but each family weighted 1/7. Components within a family are still evidence-weighted. |
| `p_fam_waypoint`, `p_fam_twoleg` | the waypoint family alone and the two-leg family alone, default EOF mixture |
| `p_v2_sens_descent1840` | sensitivity: free descent at the 18:40 call for every family (WPTS as the waypoint family) |

**Tables:**
* `arc_profile_v2.csv`: per 0.1° of the 7th arc, the layers above, plus `p` and the 00:19:29
  crossing distribution per family (`arc0019_<family>`, `arc0019_d1840_<family>`).
* `evidence_v2.csv`: the evidence table.
* `evidence_components_v2.csv`, `evidence_components_v2_d1840.csv`: the 140 waypoint components,
  with replicates.
* `profile_likelihood_v2.csv` (+ `_allruns`).
* `bestfit_polished_v2.csv`.
* `ugib_replay.csv` / `.txt`.
* `routes_sanity_check.txt`.
* `summary_v2.json`.

**Figures:**
* `fig_arc_latitude_by_family_v2.png`: crossing latitude per family, and combined v1 vs v2 vs
  sensitivities.
* `fig_paths_waypoint_v2.png`: best-fit waypoint paths, the UGIB-like configuration against UGIB's
  published route, and two-leg paths.
* `fig_evidence_by_waypoint_v2.png`.

**Inputs:**
* `data/raw/waypoints_indian_ocean/` (waypoint coordinates and provenance).
* `data/raw/ugib2020/` (UGIB 2020 and related PDFs, Malaysian AIP pages, provenance).

**SMC runs:** `data/derived/satcom_smc/routes/*.npz` (+ logs).

### 13.10 Caveats specific to this section

1. **Constant Mach and FL after the FMT.** All new families keep constant Mach and constant FL after
   the FMT, with instantaneous turns. The d1840 variant is the only place a descent or a separate
   leg speed enters, and there only at the 18:40 call and on the FMT → W leg.
2. **Waypoint set.**
   * The family evidence depends on the set by roughly log(set size): regional −19.13, literature
     −18.45.
   * The Jakarta-, Colombo- and Melbourne-FIR coordinates come from secondary sources (opennav and
     Godfrey 2016, which agree to the arcsecond). They are not AIP-verified. DOLEM has one source.
3. **The turn at the 18:40 call.** Some best fits put the FMT at exactly 18:40:08, the time at which
   the call BFO (the mean of 51 bursts) is evaluated.
   * The bursts are stable (sd 1.25 Hz, trend 0.6 Hz/min over 18:39:55–18:40:56). The aircraft was
     therefore not turning in level flight during the call, so the turn must be complete by
     18:39:55.
   * The 13 s difference (about 1.7 NM) is immaterial.
4. **Run sizes.** The d1840 waypoint components were run at N = 5,000 only (stage-2 comparisons
   suggest ±0.25 accuracy). The single-mode d1840 runs use one seed (N = 20,000).
5. **Profile values are upper bounds.** DE stalled for BEDAX → 180 T and was corrected by a local
   polish.
6. **The UGIB replay** uses UGIB's published states (Figs. 3–4), interpolated between them, and a
   simplified geometry for the 18:23–18:28 offset. It is the likelihood of their path, not an
   evidence: their route has many hand-tuned degrees of freedom.

### 13.11 Reproduce (v2)

    .venv/bin/python -I scripts/satcom_routes_check.py        # forward-model sanity checks
    # SMC runs (each line one job; we ran them with xargs -P 10, OMP/OPENBLAS/VECLIB threads = 1):
    #   --family TWO --n 20000 --seed {41,42,43};  --family TWO --tie --n 20000 --seed {41,42}
    #   --family WPT --wpt W --mode2 M --n 5000 --seed 1   for W in the 28-point regional set, M in 5 modes
    #   ... and --n 20000 --seed {41,42} for the 21 components with >= 0.5 % of the family evidence
    #   --family WPT --wpt BEDAX --mode2 LNAV --fix theta2=180 --tag ugib180 --n 20000 --seed {41,42}
    #   --family SINGLE --mode2 {LNAV,CTT} --n {20000,5000} --seed {42,1}            (replicates)
    #   d1840: add --roc1840 (single modes, TWO; WPTS instead of WPT for the waypoint family)
    .venv/bin/python -I scripts/satcom_run_routes.py <args>
    .venv/bin/python -I scripts/satcom_ugib_replay.py         # UGIB published route through this likelihood
    .venv/bin/python -I scripts/satcom_routes_profile.py --wpt MUTMI:LNAV --wpt MUTMI:CTT --wpt ISBIX:CTT --wpt IGOGU:CTT
    .venv/bin/python -I scripts/satcom_routes_polish.py
    .venv/bin/python -I scripts/satcom_posterior_v2.py        # v2 layers, tables, figures

Run times: about 95 s per N = 5,000 SMC run and 6–11 min per N = 20,000 run on one core. The
complete v2 set (about 340 runs) took about 2.5 h on 10 cores.
