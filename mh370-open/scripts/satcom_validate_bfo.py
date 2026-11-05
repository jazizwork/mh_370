"""Validate the BTO/BFO forward model (src/mh370/satcom.py) against public calibration data.

1. ATSB (2014, rev. 13 Aug 2014) Tables 5/6: term-by-term BFO prediction at 17:07.
2. On-ground BFO/BTO at the KLIA gate (16:00-16:30): bias calibration.
3. In-flight BFO 16:42-17:07 against the public ADS-B track (FR24/FlightAware/Planefinder).
4. Cross-check of ATSB Table 4 (df_sat+df_AFC) against the independent digitisation of
   Ashton et al. (2015) Fig. 11 used in o-nesterov/MH370Solver (MIT licence; numbers only).

Writes outputs/satcom/validation_*.csv and prints a summary used in outputs/satcom/README.md.
Run: .venv/bin/python -I scripts/satcom_validate_bfo.py
"""
import json
import pathlib

import numpy as np
import pandas as pd

from mh370 import geo, satcom

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "satcom"
OUT.mkdir(parents=True, exist_ok=True)
KT = 1852 / 3600
FT = 0.3048

# KLIA satellite-terminal gate area (approx.; BFO/BTO are insensitive to ~1 km here)
KLIA_GATE = (2.7457, 101.7130, 20.0)


def atsb_table5():
    rows = []
    for hdg in (0.0, 25.0, 50.0):
        vn, ve = satcom.gs_track_to_vn_ve(867 / 1.852, hdg)
        for earth in ("sphere", "wgs84"):
            tt = satcom.bfo_terms(geo.hms(17, 7), 5.27, 102.79, 35000 * FT, vn, ve, 0.0,
                                  bias=152.5, aes_earth=earth)
            rows.append(dict(case=f"track {hdg:.0f}", aes_earth=earth,
                             comp=float(tt["df_comp"]), up_aircraft=float(tt["dF_up_ac"]),
                             up_sat=float(tt["dF_up_sat"]), down=float(tt["dF_down"]),
                             sat_afc=float(tt["afc"]), bias=152.5, bfo=float(tt["bfo"])))
    df = pd.DataFrame(rows)
    atsb = pd.DataFrame(dict(case=["track 0", "track 25", "track 50"],
                             comp=[108.9, 489.5, 777.8], up_aircraft=[-75.3, -459.4, -756.8],
                             up_sat=[-3.2] * 3, down=[-71.9] * 3, sat_afc=[24.1] * 3,
                             bias=[152.5] * 3, bfo=[135.1, 131.7, 122.5]))
    return df, atsb


def load_adsb():
    a = pd.read_csv(satcom.EXT / "ads-b" / "all-combined.csv")
    a["t"] = a["time"] - satcom.UNIX_T0
    return a.sort_values("t").reset_index(drop=True)


def adsb_state(a, t):
    """Interpolate aircraft state at times t from ADS-B: lat, lon, alt(ft), gs(kt), track,
    vertical rate (fpm).  Position after the last position report before 17:19 is dead-
    reckoned from GS/track (the FR24 'home' feed gives GS/track/roc but no positions)."""
    pos = a.dropna(subset=["lat", "lon"])
    pos = pos[pos.t < geo.hms(17, 10)]                  # use 16:42:30-17:02:40 positions
    pos = pos.groupby("t").mean(numeric_only=True).reset_index()
    alt = a.dropna(subset=["alt"]).groupby("t").mean(numeric_only=True).reset_index()
    kin = a.dropna(subset=["sog", "course"]).groupby("t").mean(numeric_only=True).reset_index()
    roc = a.dropna(subset=["roc"]).groupby("t").mean(numeric_only=True).reset_index()
    t = np.atleast_1d(np.asarray(t, float))
    gs = np.interp(t, kin.t, kin.sog)
    # unwrap course for interpolation
    crs = np.degrees(np.unwrap(np.radians(kin.course.to_numpy())))
    trk = np.mod(np.interp(t, kin.t, crs), 360)
    altf = np.interp(t, alt.t, alt.alt)
    # vertical rate: central difference of altitude reports over +-40 s (fpm)
    dt = 40.0
    vr = (np.interp(t + dt, alt.t, alt.alt) - np.interp(t - dt, alt.t, alt.alt)) / (2 * dt) * 60
    lat = np.interp(t, pos.t, pos.lat)
    lon = np.interp(t, pos.t, pos.lon)
    # dead reckoning beyond last position report
    tl = pos.t.iloc[-1]
    late = t > tl
    if late.any():
        # integrate GS/track from tl with 5 s steps
        tt = np.arange(tl, t.max() + 5, 5.0)
        g = np.interp(tt, kin.t, kin.sog) * KT
        c = np.radians(np.interp(tt, kin.t, crs))
        la = np.empty_like(tt); lo = np.empty_like(tt)
        la[0], lo[0] = pos.lat.iloc[-1], pos.lon.iloc[-1]
        R = 6371008.8
        for i in range(1, tt.size):
            la[i] = la[i - 1] + np.degrees(g[i - 1] * np.cos(c[i - 1]) * 5 / R)
            lo[i] = lo[i - 1] + np.degrees(g[i - 1] * np.sin(c[i - 1]) * 5 / (R * np.cos(np.radians(la[i - 1]))))
        lat[late] = np.interp(t[late], tt, la)
        lon[late] = np.interp(t[late], tt, lo)
    return dict(lat=lat, lon=lon, alt_ft=altf, gs_kt=gs, track=trk, vr_fpm=vr,
                vr_adsb=np.interp(t, roc.t, roc.roc) if len(roc) else np.nan)


def nesterov_afc(t):
    """df_sat+df_AFC reconstructed as in o-nesterov/MH370Solver initInmarsatAFC.cpp:
    digitised Ashton et al. Fig. 11 (10-min table from 00:00 7 Mar) minus the Burum->sat
    (uplink freq.) + sat->Perth (downlink freq.) pilot Doppler.  Cross-check only."""
    tab = np.array([
        15.932, 16.382, 16.592, 16.704, 16.869, 17.218, 17.720, 18.257, 18.717, 19.122,
        19.369, 19.476, 19.515, 19.483, 19.264, 18.866, 18.551, 18.397, 18.427, 18.602,
        18.738, 18.760, 18.663, 18.415, 18.015, 17.547, 17.029, 16.361, 15.659, 14.914,
        14.006, 13.228, 12.537, 11.661, 10.621, 9.561, 8.5731, 7.5284, 6.4872, 5.5041,
        4.5013, 3.4886, 2.5883, 1.6774, 0.90689, 0.25986, -0.47901, -1.5045, -2.6689, -3.8234,
        -4.964, -5.8111, -6.4525, -7.0422, -7.9048, -8.8941, -9.6847, -10.478, -11.194, -12.022,
        -12.818, -13.424, -14.022, -14.646, -15.285, -15.872, -16.390, -16.870, -17.365, -17.891,
        -18.344, -18.665, -18.910, -19.125, -19.296, -19.404, -19.510, -19.707, -19.985, -20.213,
        -20.330, -20.356, -20.304, -20.166, -19.964, -19.795, -19.717, -19.701, -19.707, -19.696,
        -19.628, -19.479, -19.267, -19.016, -18.770, -18.584, -18.419, -18.155, -17.729, -17.209,
        -16.642, -16.040, -15.413, -14.761, -14.077, -13.374, -12.668, -11.937, -11.184, -10.433,
        -9.7018, -8.9605, -8.1850, -7.3821, -6.5417, -5.6537, -4.672, -3.1114, -0.75563, 3.2262,
        6.3628, 9.4108, 11.553, 13.553, 15.413, 14.592, 13.901, 13.369, 12.983, 12.702,
        12.501, 12.393, 12.386, 12.526, 12.859, 13.272, 13.671, 14.009, 14.277, 14.527,
        14.820, 15.167, 15.443, 15.539, 15.932, 16.382, 16.592, 16.704, 16.869, 17.218,
        17.720, 18.257, 18.717, 19.122, 19.369, 19.476, 19.515])
    t = np.atleast_1d(np.asarray(t, float))
    fi = np.interp(t, np.arange(tab.size) * 600.0, tab)
    ps, vs = satcom.sat_state(t)
    burum = satcom.ecef_m(53.2844444, 6.21527778, 0.0)
    perth = satcom.ecef_m(-31.8048, 115.8878, 0.0)
    d1 = ps - burum
    f_u = -satcom.F_UP_HZ * np.sum(vs * d1, -1) / np.linalg.norm(d1, axis=-1) / satcom.C_M_S
    d2 = ps - perth
    f_d = -satcom.F_DOWN_HZ * np.sum(vs * d2, -1) / np.linalg.norm(d2, axis=-1) / satcom.C_M_S
    return fi - (f_u + f_d)


# Ashton et al. (2015) Table 9 "Example Reconstructed Flight Path Results" (published values)
ASHTON_T9 = pd.DataFrame([
    # time, lat, lon, track, speed_kph, up_ac, up_sat, down, comp, afc, bias, pred, meas
    ("16:30:00", 2.7, 101.7, 0, 0, 0, -6, -85, 0, 29, 150, 88, 88),
    ("16:42:31", 2.8, 101.7, 333, 435, 194, -6, -79, -180, 27, 150, 105, 125),
    ("16:55:53", 4.0, 102.2, 25, 848, -424, -4, -76, 453, 26, 150, 125, 159),
    ("17:07:19", 5.3, 102.8, 25, 867, -460, -3, -72, 490, 24, 150, 130, 132),
    ("18:25:27", 6.9, 95.8, 300, 800, 575, -1, -37, -556, 11, 150, 141, 142),
    ("18:39:58", 7.5, 94.4, 200, 800, 353, -1, -30, -389, 8, 150, 91, 88),
    ("19:41:03", 0.0, 93.7, 186, 800, 32, -1, 0, -72, -1, 150, 108, 111),
    ("20:41:05", -7.5, 92.9, 182, 829, -182, 5, 29, 143, -1, 150, 143, 141),
    ("21:41:27", -15.0, 92.7, 180, 829, -365, 16, 55, 331, -18, 150, 170, 168),
    ("22:41:22", -22.5, 92.9, 179, 829, -522, 29, 78, 497, -29, 150, 203, 204),
    ("23:14:00", -26.6, 93.0, 179, 829, -595, 37, 88, 575, -33, 150, 222, 217),
    ("00:11:00", -33.7, 93.0, 180, 829, -702, 50, 101, 691, -38, 150, 252, 252),
    ("00:19:29", -34.7, 93.0, 180, 829, -717, 52, 102, 708, -38, 150, 256, 182),
], columns=["time", "lat", "lon", "track", "kph", "up_ac", "up_sat", "down", "comp", "afc",
            "bias", "pred", "meas"])


def ashton_table9():
    d = ASHTON_T9.copy()
    hh = d.time.str.split(":", expand=True).astype(int)
    t = hh[0] * 3600 + hh[1] * 60 + hh[2]
    d["t"] = np.where(hh[0] < 12, t + 86400, t)
    alt = np.where(d.kph > 0, 35000 * FT, 0.0)
    vn, ve = satcom.gs_track_to_vn_ve(d.kph / 1.852, d.track)
    tt = satcom.bfo_terms(d.t, d.lat, d.lon, alt, vn, ve, 0.0, bias=150.0)
    out = pd.DataFrame(dict(time=d.time, up_ac=tt["dF_up_ac"], up_sat=tt["dF_up_sat"],
                            down=tt["dF_down"], comp=tt["df_comp"], afc=tt["afc"],
                            pred=tt["bfo"]))
    # internal consistency of the published rows (sum of terms minus 'Pred', rounding only)
    chk = (d.up_ac + d.up_sat + d.down + d.comp + d.afc + d.bias) - d.pred
    out["ashton_rowsum_minus_pred"] = chk
    for k in ("up_ac", "up_sat", "down", "comp", "afc", "pred"):
        out[f"d_{k}"] = out[k] - d[k]
    out["bto_pred_us"] = satcom.bto(d.t, d.lat, d.lon, alt)
    out["bto_pred_us_h0"] = satcom.bto(d.t, d.lat, d.lon, 0.0)
    return out


def main():
    summary = {}
    t9 = ashton_table9()
    print("== Ashton et al. (2015) Table 9 example path: my terms minus published (Hz)")
    print(t9.round(1).to_string(index=False))
    t9.to_csv(OUT / "validation_ashton_table9.csv", index=False)
    summary["ashton_t9_pred_diff_max_hz"] = float(t9.d_pred.abs().max())
    summary["ashton_t9_pred_diff_rms_hz"] = float(np.sqrt(np.mean(t9.d_pred ** 2)))
    # ---------------- 1. ATSB Table 5 ----------------
    mine, atsb = atsb_table5()
    print("== ATSB Table 5 (17:07, 5.27N 102.79E, GS 867 km/h, FL350) term check")
    print(mine.round(1).to_string(index=False))
    print(atsb.to_string(index=False))
    mine.to_csv(OUT / "validation_atsb_table5.csv", index=False)
    sph = mine[mine.aes_earth == "sphere"].reset_index(drop=True)
    summary["atsb_table5_max_term_diff_hz"] = float(np.max(np.abs(
        sph[["comp", "up_aircraft", "up_sat", "down", "bfo"]].to_numpy()
        - atsb[["comp", "up_aircraft", "up_sat", "down", "bfo"]].to_numpy())))

    # ---------------- 4. Table 4 cross-check ----------------
    tt = satcom._T4_T
    cmp4 = pd.DataFrame(dict(t_utc=[f"{int(x // 3600) % 24:02d}:{int(x % 3600 // 60):02d}" for x in tt],
                             table4=satcom._T4_V, nesterov_fig11=nesterov_afc(tt)))
    cmp4["diff"] = cmp4.nesterov_fig11 - cmp4.table4
    print("\n== ATSB Table 4 vs digitised Ashton Fig.11 reconstruction (Hz)")
    print(cmp4.round(2).to_string(index=False))
    cmp4.to_csv(OUT / "validation_table4_crosscheck.csv", index=False)
    extra = [geo.hms(16, 0), geo.hms(16, 10), geo.hms(16, 28), geo.hms(18, 28, 15),
             geo.hms(18, 40, 20), geo.hms(23, 14, 30)]
    print("Fig.11-based values at other times:",
          {f"{int(x//3600)%24:02d}:{int(x%3600//60):02d}": round(float(v), 1)
           for x, v in zip(extra, nesterov_afc(extra))})
    print("Table-4 linear interp at same times:",
          [round(float(v), 1) for v in satcom.sat_afc_hz(extra)])
    summary["table4_vs_fig11_rms_hz"] = float(np.sqrt(np.mean(cmp4["diff"] ** 2)))

    # ---------------- 2. ground calibration ----------------
    log = satcom.load_su_log()
    m = log[log.bfo.notna() & log.chan.isin(["R", "T"])].copy()
    ground = m[(m.t < geo.hms(16, 30))].copy()
    lat, lon, h = KLIA_GATE
    ground["bfo_nobias"] = satcom.bfo(ground.t, lat, lon, h, 0.0, 0.0, 0.0, bias=0.0)
    ground["bfo_nobias_fig11"] = satcom.bfo(ground.t, lat, lon, h, 0.0, 0.0, 0.0, bias=0.0,
                                            afc=nesterov_afc(ground.t))
    ground["bias_est"] = ground.bfo - ground.bfo_nobias
    ground["bias_est_fig11"] = ground.bfo - ground.bfo_nobias_fig11
    # 16:00:13-16:00:30: first bursts after the 16:00 log-on (BFO 103-104 Hz, ~15 Hz high:
    # the same OCXO warm-up signature as 18:25); 16:27-16:30: aircraft starting to move (taxi).
    ground["window"] = np.select([ground.t < geo.hms(16, 0, 30), ground.t < geo.hms(16, 20)],
                                 ["16:00:13-16:00:30 log-on", "16:00:30-16:11 gate"], "16:27-16:30 taxi?")
    gs = ground.groupby(["window", "chan"]).agg(n=("bfo", "size"), bfo_mean=("bfo", "mean"),
                                                 bias_mean=("bias_est", "mean"),
                                                 bias_sd=("bias_est", "std"),
                                                 bias_mean_fig11=("bias_est_fig11", "mean"))
    print("\n== On-ground BFO bias estimates (bias = measured - model without bias)")
    print(gs.round(2).to_string())
    # BTO at gate
    gb = log[(log.t < geo.hms(16, 30)) & (log.chan == "R") & log.bto.notna()].copy()
    gb["bto_pred"] = satcom.bto(gb.t, lat, lon, h)
    gb["res"] = gb.bto - gb.bto_pred
    print(f"Gate BTO (R-channel, n={len(gb)}): mean residual {gb.res.mean():.1f} us, "
          f"sd {gb.res.std():.1f} us (ATSB Table 2 sd of its 17 values: "
          f"{pd.read_csv(satcom.EXT/'atsb'/'table-2-bto-calibration-kuala-lumpur-international-airport.csv').iloc[:17,4].astype(float).std():.1f} us)")
    summary["gate_bto_mean_res_us"] = float(gb.res.mean())
    summary["gate_bto_sd_us"] = float(gb.res.std())
    ground.to_csv(OUT / "validation_ground_bfo.csv", index=False)

    # ---------------- 3. in-flight ----------------
    a = load_adsb()
    fl = m[(m.t >= geo.hms(16, 42, 30)) & (m.t <= geo.hms(17, 8))].copy()
    st = adsb_state(a, fl.t.to_numpy())
    for k, v in st.items():
        fl[k] = v
    vn, ve = satcom.gs_track_to_vn_ve(fl.gs_kt, fl.track)
    fl["model_nobias"] = satcom.bfo(fl.t, fl.lat, fl.lon, fl.alt_ft * FT, vn, ve,
                                    fl.vr_fpm * FT / 60, bias=0.0)
    fl["model_nobias_novs"] = satcom.bfo(fl.t, fl.lat, fl.lon, fl.alt_ft * FT, vn, ve, 0.0, bias=0.0)
    fl["phase"] = np.select([fl.t < geo.hms(16, 50), fl.t < geo.hms(17, 0)],
                            ["16:42-16:43 climb/turn", "16:55-16:56 climb"], "17:06-17:07 level FL350")
    # bias from ground, by channel (16:00-16:11 window is the cleaner 'gate' period)
    gbias = ground[ground.window == "16:00:30-16:11 gate"].groupby("chan").bias_est.mean()
    fl["bias_ground"] = fl.chan.map(gbias)
    fl["res_ground_bias"] = fl.bfo - (fl.model_nobias + fl.bias_ground)
    fl["bias_est"] = fl.bfo - fl.model_nobias
    tab = fl.groupby(["phase", "chan"]).agg(n=("bfo", "size"), bfo_mean=("bfo", "mean"),
                                            vr_fpm=("vr_fpm", "mean"),
                                            res_mean=("res_ground_bias", "mean"),
                                            res_sd=("res_ground_bias", "std"),
                                            inflight_bias=("bias_est", "mean"))
    print("\n== In-flight BFO residuals using the on-ground bias per channel (Hz)")
    print(tab.round(2).to_string())
    fl.to_csv(OUT / "validation_inflight_bfo.csv", index=False)
    lvl = fl[fl.phase.str.startswith("17:06")]
    summary["ground_bias_R"] = float(gbias.get("R"))
    summary["ground_bias_T"] = float(gbias.get("T"))
    summary["inflight_level_bias_R"] = float(lvl[lvl.chan == "R"].bias_est.mean())
    summary["inflight_level_bias_T"] = float(lvl[lvl.chan == "T"].bias_est.mean())
    summary["inflight_level_res_R_mean"] = float(lvl[lvl.chan == "R"].res_ground_bias.mean())
    summary["inflight_level_res_T_mean"] = float(lvl[lvl.chan == "T"].res_ground_bias.mean())
    clb = fl[fl.phase.str.startswith("16:55")]
    summary["climb_1655_res_R_mean"] = float(clb[clb.chan == "R"].res_ground_bias.mean())
    summary["climb_1655_res_T_mean"] = float(clb[clb.chan == "T"].res_ground_bias.mean())
    # in-flight BTO (R channel)
    fb = fl[(fl.chan == "R") & fl.bto.notna()].copy()
    fb["bto_pred"] = satcom.bto(fb.t, fb.lat, fb.lon, fb.alt_ft * FT)
    fb["res"] = fb.bto - fb.bto_pred
    print(f"\nIn-flight BTO (R-channel, n={len(fb)}): mean residual {fb.res.mean():.1f} us, "
          f"sd {fb.res.std():.1f} us, max |res| {fb.res.abs().max():.0f} us")
    summary["inflight_bto_mean_res_us"] = float(fb.res.mean())
    summary["inflight_bto_sd_us"] = float(fb.res.std())
    # ATSB-style single point 17:07 (Table 5 'measured BFO' 132 is an R-channel value)
    print("\nATSB Table 5 measured 132.0 Hz vs log R-channel 17:07 mean "
          f"{log[(log.t>=geo.hms(17,7))&(log.t<geo.hms(17,8))&(log.chan=='R')].bfo.mean():.1f} Hz")
    # ---- single bias per channel fitted to gate + climb(16:55) + level(17:06-17:07) ----
    cal = pd.concat([
        ground[ground.window == "16:00:30-16:11 gate"].assign(phase="gate 16:00:30-16:11"),
        fl[~fl.phase.str.startswith("16:42")]])
    cal_bias = cal.groupby("chan").bias_est.mean()
    allp = pd.concat([ground.assign(phase="ground " + ground.window), fl])
    allp["res_cal"] = allp.bias_est - allp.chan.map(cal_bias)
    rt = allp.groupby(["phase", "chan"]).agg(n=("bfo", "size"), mean=("res_cal", "mean"),
                                             sd=("res_cal", "std"),
                                             rms=("res_cal", lambda x: float(np.sqrt(np.mean(x**2)))),
                                             maxabs=("res_cal", lambda x: float(np.max(np.abs(x)))))
    print("\n== Residuals with one bias per channel fitted to gate+16:55 climb+17:07 level")
    print("fitted biases:", cal_bias.round(2).to_dict())
    print(rt.round(2).to_string())
    rt.round(2).to_csv(OUT / "validation_bfo_residuals_by_phase.csv")
    summary["cal_bias_R"] = float(cal_bias["R"]); summary["cal_bias_T"] = float(cal_bias["T"])
    # figure: calibration residuals vs time
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 3.6))
    for ch, col, lab in (("R", "#2a78d6", "R-channel"), ("T", "#eb6834", "T-channel")):
        d = allp[allp.chan == ch]
        ax.plot((d.t - geo.hms(16)) / 60, d.res_cal, "o", ms=3.5, color=col, label=lab, alpha=0.8)
    ax.axhspan(-4.3, 4.3, color="#e4e3df", zorder=0, label="+/-4.3 Hz (DSTG in-flight sd)")
    ax.axhline(0, color="#8a8984", lw=0.8)
    for x, txt in ((0.2, "log-on\nburst"), (5, "gate"), (28, "taxi?"), (42.5, "climbing\nturn"),
                   (55.5, "climb"), (66.5, "FL350")):
        ax.text(x, 19, txt, fontsize=7, color="#52514e", va="top")
    ax.set_xlabel("minutes after 16:00 UTC, 7 Mar 2014", fontsize=8, color="#52514e")
    ax.set_ylabel("BFO measured - model (Hz)", fontsize=8, color="#52514e")
    ax.set_title(f"Calibration residuals, one bias per channel (R {cal_bias['R']:.1f} Hz, "
                 f"T {cal_bias['T']:.1f} Hz)", fontsize=9)
    for sname in ("top", "right"):
        ax.spines[sname].set_visible(False)
    ax.grid(color="#e4e3df", lw=0.6)
    ax.tick_params(labelsize=8, colors="#52514e")
    ax.legend(fontsize=7, frameon=False, loc="lower left", ncol=3)
    fig.tight_layout()
    fig.savefig(OUT / "fig_bfo_calibration.png", dpi=150)
    plt.close(fig)
    (OUT / "validation_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
