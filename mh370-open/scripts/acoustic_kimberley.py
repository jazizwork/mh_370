"""Workstream D: the Kimberley (PAKIM) 01:30-01:35 UTC window - Curtin/Carlsberg vs Java.

Picks, in the PAKIM file starting 01:30:01 UTC on 8 March 2014:
  F1  short 20-60 Hz burst (~01:32:56)       onset of the strongest segment with 20-40 Hz 1-s level
                                              > file median + 10 dB in 01:32:30-01:33:20
  F2  impulsive broadband burst (~01:33:04)  onset = first 0.25-s step with 100-400 Hz 1-s level
                                              > file median + 10 dB in 01:32:30-01:33:20
  F3  emergent low-frequency arrival         5-10 & 8-16 Hz 10-s running-median level; onset =
                                              first time > pre-event background (01:30:30-01:32:40
                                              median) + 6 dB and staying above for >= 30 s;
                                              peak = max of the 10-s level
Chance-coincidence rates: the same F1/F2/F3 detectors run on all PAKIM control-night files
(22:00-03:00, 8 nights): events per hour -> P(at least one within +/- w s of a given time).

Predictions compared: Carlsberg (from HA01 01:34:40, c 1.47-1.49), Curtin's published 01:32:49,
Java 01:15:18 T (c 1.46-1.50; fork relocation 8.12-8.30S, origin 01:15:19-24), and the Java
T delay observed at XMIS (+45 s vs 1.48 km/s; outputs/acoustic/seismic/SEISMIC.md).

Outputs: outputs/acoustic/kimberley_picks.json, kimberley_analysis.csv,
         fig_kimberley_0130.png
Run: .venv/bin/python -I scripts/acoustic_kimberley.py
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"
FS = 1000.0


def levels(p, fs, f1, f2, win=1.0, step=0.25):
    return A.band_level(p, fs, f1, f2, win, step)


def lf_level(L5, L8, n=40):
    """10-s running MEDIAN (robust to the short F1/F2 transients) of max(5-10, 8-16 Hz) 1-s levels."""
    from scipy.ndimage import median_filter
    return np.maximum(median_filter(L5, size=n, mode="nearest"), median_filter(L8, size=n, mode="nearest"))


def segments(mask):
    out, i = [], 0
    while i < mask.size:
        if mask[i]:
            j = i
            while j + 1 < mask.size and mask[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def detect_types(path):
    """F1/F2/F3-type events in one PAKIM file (absolute times)."""
    t0, fs, p, rec = A.read_pressure(path, "PAKIM", FS, full=True)
    tr, Lw = levels(p, fs, 20, 40)
    _, Lh = levels(p, fs, 100, 400)
    _, L5 = levels(p, fs, 5, 10)
    _, L8 = levels(p, fs, 8, 16)
    t = t0 + tr
    ev = {"F1": [], "F2": [], "F3": []}
    edge = (t >= t[0] + 3) & (t <= t[-1] - 3)
    # F1: 20-40 Hz >= +10 dB, duration 2-10 s, WITHOUT simultaneous 100-400 Hz >= +10 dB
    for name, L, other in (("F1", Lw, Lh), ("F2", Lh, None)):
        on = (L - np.median(L) > 10) & edge
        i = 0
        while i < on.size:
            if on[i]:
                j = i
                while j + 1 < on.size and on[j + 1]:
                    j += 1
                dur = (j - i + 1) * 0.25
                if name == "F1" and 2.0 <= dur <= 10.0:
                    ev["F1"].append((t[i], dur, float((L - np.median(L))[i:j + 1].max())))
                if name == "F2" and dur <= 10.0:
                    ev["F2"].append((t[i], dur, float((L - np.median(L))[i:j + 1].max())))
                i = j + 1
            else:
                i += 1
    # F3: emergent LF: 10-s power-avg of 5-10 and 8-16 Hz > first-120-s median + 6 dB for >= 30 s
    S = lf_level(L5, L8)
    bg = np.median(S[(t >= t[0] + 5) & (t <= t[0] + 125)])
    on = (S - bg > 6) & edge
    i = 0
    while i < on.size:
        if on[i]:
            j = i
            while j + 1 < on.size and on[j + 1]:
                j += 1
            if (j - i + 1) * 0.25 >= 30:
                ev["F3"].append((t[i], (j - i + 1) * 0.25, float((S - bg)[i:j + 1].max())))
            i = j + 1
        else:
            i += 1
    return str(path), (t[0], t[-1]), ev


def main():
    w = A.recording_windows("PAKIM", A.hms8(1, 31), A.hms8(1, 33), full=True)[0]
    path = w[2]
    t0, fs, p, rec = A.read_pressure(path, "PAKIM", FS, full=True)
    tr, Lw = levels(p, fs, 20, 40)
    _, Lh = levels(p, fs, 100, 400)
    _, L5 = levels(p, fs, 5, 10)
    _, L8 = levels(p, fs, 8, 16)
    t = t0 + tr
    win = (t >= A.hms8(1, 32, 30)) & (t <= A.hms8(1, 33, 20))
    segs = [(i, j) for i, j in segments(win & (Lw - np.median(Lw) > 10))]
    i1 = max(segs, key=lambda ij: (Lw - np.median(Lw))[ij[0]:ij[1] + 1].max())[0]  # strongest F1 burst
    f1 = t[i1]
    f2 = t[np.where(win & (Lh - np.median(Lh) > 10))[0][0]]
    S = lf_level(L5, L8)
    pre = (t >= A.hms8(1, 30, 30)) & (t <= A.hms8(1, 32, 40))
    bg = np.median(S[pre])
    above = (S - bg > 6) & (t > A.hms8(1, 32, 40))
    f3 = np.nan
    for i in np.where(above)[0]:
        k = int(round(30 / 0.25))
        if above[i:i + k].all():
            f3 = t[i]
            break
    # F3 onset is masked by F2 (the LF level stays >= +8 dB after F2), so also report robust
    # measures: first time after F2 ends (f2 + 10 s) at >= +15 dB, and the energy centroid of
    # the LF excess (> +6 dB) from F2 end to the end of the file (truncated at 01:35:08).
    f2_end = f2 + 10.0
    k15 = np.where((t > f2_end) & (S - bg >= 15))[0]
    f3_rise15 = t[k15[0]] if k15.size else np.nan
    wgt = np.where((t > f2_end) & (S - bg > 6), 10 ** ((S - bg) / 10) - 1, 0.0)
    f3_centroid = float((t * wgt).sum() / wgt.sum())
    f3_peak = t[np.argmax(np.where(t > A.hms8(1, 33, 15), S, -np.inf))]
    f3_peak_db = float(np.max(S[t > A.hms8(1, 33, 15)]) - bg)
    # amplitudes
    bb = A.bandpass(p, fs, 5, 400)
    tt = t0 + np.arange(p.size) / fs
    amp = lambda a, b: float(np.abs(bb[(tt >= a) & (tt <= b)]).max() / 1e6)  # noqa: E731
    picks = {"F1 20-60 Hz burst onset": A.fmt(f1, 2), "F2 broadband impulsive onset": A.fmt(f2, 2),
             "F3 emergent LF onset (masked by F2)": A.fmt(f3, 2),
             "F3 reaches +15 dB after F2": A.fmt(f3_rise15, 2),
             "F3 energy centroid": A.fmt(f3_centroid, 2), "F3 emergent LF peak": A.fmt(f3_peak, 2)}
    print(picks, "F3 peak +%.1f dB over pre-event" % f3_peak_db,
          "peak |p| F1 %.2f Pa, F2 %.2f Pa" % (amp(f1, f1 + 6), amp(f2, f2 + 7)))
    (OUT / "kimberley_picks.json").write_text(json.dumps({k: v for k, v in picks.items()}, indent=1))

    # predictions
    pred = {}
    car = A.SOURCES["Carlsberg_Curtin"]
    dH, _ = A.rdist_az("HA01", car["lat"], car["lon"])
    dK, _ = A.rdist_az("PAKIM", car["lat"], car["lon"])
    pc = [A.HA01_CANDIDATES["Curtin301"]["t"] + (float(dK) - float(dH)) / c for c in (1.47, 1.49)]
    pred["Carlsberg (HA01 01:34:40 - TDOA)"] = (min(pc), max(pc))
    pred["Curtin published 'Scott Reef'"] = (A.hms8(1, 32, 49), A.hms8(1, 32, 49))
    jv = A.SOURCES["Java_Anderson"]
    for lab, la, lo, t0j in (("Java T, Anderson loc", jv["lat"], jv["lon"], jv["t0"]),
                             ("Java T, fork relocation", -8.19, 107.90, A.hms8(1, 15, 23))):
        d, _ = A.rdist_az("PAKIM", la, lo)
        pred[lab + " (c 1.50-1.46)"] = (t0j + float(d) / 1.50, t0j + float(d) / 1.46)
        pred[lab + " +45 s XMIS-like delay"] = (t0j + float(d) / 1.48 + 45, t0j + float(d) / 1.48 + 45)
    rows = []
    for k, (a, b) in pred.items():
        r = dict(prediction=k, t_lo=A.fmt(a, 1), t_hi=A.fmt(b, 1))
        for nm, tv in (("F1", f1), ("F2", f2), ("F3onset", f3), ("F3rise15", f3_rise15),
                       ("F3centroid", f3_centroid), ("F3peak", f3_peak)):
            r[f"{nm}_minus_pred_s"] = (tv - b) if tv > b else (tv - a) if tv < a else 0.0
        rows.append(r)

    # chance-coincidence rates from control nights
    files = [p_ for d in A.CONTROL_DAYS for p_ in A.night_files("PAKIM", d)]
    with ProcessPoolExecutor(8) as ex:
        res = list(ex.map(detect_types, files))
    hours = sum(b - a for _, (a, b), _ in res) / 3600
    rates = {k: sum(len(e[k]) for _, _, e in res) / hours for k in ("F1", "F2", "F3")}
    # strength-conditioned rates (as strong as observed)
    obs_strength = {"F1": float((Lw - np.median(Lw))[(t >= f1) & (t <= f1 + 6)].max()),
                    "F2": float((Lh - np.median(Lh))[(t >= f2) & (t <= f2 + 7)].max()),
                    "F3": f3_peak_db}
    rates_strong = {k: sum(sum(1 for x in e[k] if x[2] >= obs_strength[k]) for _, _, e in res) / hours
                    for k in ("F1", "F2", "F3")}
    _, _, emain = detect_types(path)
    for r in rows:
        pass
    stats_rows = []
    for k in ("F1", "F2", "F3"):
        for wsec in (10, 15, 30, 60):
            lam = rates[k] / 3600 * 2 * wsec
            lam_s = rates_strong[k] / 3600 * 2 * wsec
            stats_rows.append(dict(feature=k, rate_per_hour=rates[k], rate_as_strong_per_hour=rates_strong[k],
                                   observed_strength_db=obs_strength[k], half_window_s=wsec,
                                   p_chance_any=1 - np.exp(-lam), p_chance_as_strong=1 - np.exp(-lam_s)))
    st = pd.DataFrame(stats_rows)
    an = pd.DataFrame(rows)
    with open(OUT / "kimberley_analysis.csv", "w") as fh:
        fh.write("# predictions vs PAKIM picks (s; 0 = inside predicted interval)\n")
        an.to_csv(fh, index=False, float_format="%.1f")
        fh.write("\n# chance-coincidence rates from PAKIM control nights (%.1f recorded hours)\n" % hours)
        st.to_csv(fh, index=False, float_format="%.4f")
    print(an.to_string())
    print(st.to_string())
    print("control hours", round(hours, 1), "main-file events:", {k: [(A.fmt(x[0], 1), round(x[2], 1)) for x in v]
                                                                for k, v in emain.items()})

    # figure
    f, ts, Sg = signal.spectrogram(p, fs, nperseg=1000, noverlap=750)
    Sg = 10 * np.log10(Sg + 1e-30)
    fig, axs = plt.subplots(3, 1, figsize=(13, 9), sharex=True, gridspec_kw=dict(height_ratios=[1.4, 1, 1]))
    x = t0 + ts - A.hms8(1, 30)
    axs[0].pcolormesh(x, f, Sg, shading="auto", cmap="viridis", vmin=np.percentile(Sg, 5),
                      vmax=np.percentile(Sg, 99.7))
    axs[0].set_ylim(2, 120)
    axs[0].set_ylabel("Hz")
    xt = t - A.hms8(1, 30)
    axs[1].plot(xt, Lw - np.median(Lw), lw=0.6, label="20-40 Hz (1 s)")
    axs[1].plot(xt, Lh - np.median(Lh), lw=0.6, label="100-400 Hz (1 s)")
    axs[1].set_ylabel("dB over median")
    axs[1].legend(fontsize=7)
    from scipy.ndimage import median_filter
    axs[2].plot(xt, median_filter(L5, 40, mode="nearest") - bg, lw=0.9, label="5-10 Hz (10-s running median)")
    axs[2].plot(xt, median_filter(L8, 40, mode="nearest") - bg, lw=0.9, label="8-16 Hz (10-s running median)")
    axs[2].axhline(6, color="k", ls=":")
    axs[2].set_ylabel("dB over pre-event")
    axs[2].legend(fontsize=7)
    cols = ["tab:red", "tab:orange", "c", "m", "tab:green", "y", "tab:brown"]
    for i, (k, (a, b)) in enumerate(pred.items()):
        for ax in axs:
            if b - a < 1:
                ax.axvline(a - A.hms8(1, 30), color=cols[i % len(cols)], lw=1.2)
            else:
                ax.axvspan(a - A.hms8(1, 30), b - A.hms8(1, 30), color=cols[i % len(cols)], alpha=0.2)
        axs[0].text(a - A.hms8(1, 30), 115 - 9 * i, k, fontsize=6.5, color=cols[i % len(cols)],
                    bbox=dict(facecolor="w", alpha=0.6, lw=0))
    for nm, tv in (("F1", f1), ("F2", f2), ("F3", f3)):
        axs[2].annotate(nm, (tv - A.hms8(1, 30), 8), fontsize=8)
        for ax in axs[1:]:
            ax.axvline(tv - A.hms8(1, 30), color="k", ls="--", lw=0.7)
    axs[2].set_xlabel("seconds after 01:30:00 UTC, 8 March 2014")
    axs[0].set_title("IMOS Kimberley (PAKIM 3250): Curtin 'Scott Reef' window. F1/F2 = short transients, "
                     "F3 = emergent LF (T-phase-like) arrival; coloured = predictions", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig_kimberley_0130.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    main()
