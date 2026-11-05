"""Step 4 calibration: measure catalogued earthquakes of 2014-03-07/08 on the open stations.

For every (event, station) pair within MAX_KM: predicted P/S (ak135) and T (geodesic /
1.46-1.50 km/s) windows, SNR in 2-8 Hz and 3-16/18 Hz (max 2-s (P) or 5-s (T) RMS envelope
over the median of a pre-event noise window), and an empirical p-value from the same
statistic evaluated at all window positions of that station's 7-h record (null).

Outputs: outputs/acoustic/seismic/calibration_measurements.csv, calibration_events.csv,
         fig_calibration_<event>.png
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mh370 import acoustic as A
from mh370 import acoustic_seismic as S

OUT = A.ROOT / "outputs" / "acoustic" / "seismic"
MAX_KM = 4500.0
G = A.geo.hms
# Catalogued events (USGS where available, else ISC/IDC), 2014-03-07 20:00 -> 03-08 02:30
EVENTS = [
    # name, t0, lat, lon, depth_km, mag, magtype/source
    ("BandaDeep_M4.7", G(20, 17, 57.13), -6.0019, 125.5838, 555.0, 4.7, "USGS mb"),
    ("IAR_M4.5", G(20, 36, 6.41), -49.0178, 123.3764, 14.9, 4.5, "USGS mb"),
    ("Molucca_mb3.5", G(20, 42, 38.73), 2.492, 127.4756, 10.0, 3.5, "IDC mb1"),
    ("NewGuinea_M5.1", G(21, 23, 22.68), -6.2815, 147.8283, 43.4, 5.1, "USGS/GCMT Mw"),
    ("CelebesDeep_mb3.6", G(21, 48, 35.04), 3.0809, 123.5133, 550.0, 3.6, "IDC"),
    ("Mindanao_mb3.5", G(22, 17, 12.05), 7.6618, 126.6816, 77.8, 3.48, "ISC mb"),
    ("Macquarie_M4.2", G(22, 50, 7.14), -54.357, 140.045, 10.7, 4.2, "USGS mb"),
    ("MauritiusReunion_mb3.7", G(23, 7, 54.44), -20.3681, 66.6171, 10.0, 3.7, "IDC mb1"),
    ("Banda_mb3.6", G(23, 27, 16.24), -6.9723, 129.3775, 122.2, 3.6, "IDC"),
    ("Java_M4.1", G(23, 52, 18.60), -9.6744, 108.4193, 34.05, 4.1, "USGS mb"),
    ("Talaud_mb3.4", G(24, 22, 2.81), 4.6369, 126.9653, 81.0, 3.37, "ISC mb"),
    ("Banda_ML3.8", G(24, 56, 53.35), -6.6275, 129.6086, 10.0, 3.8, "IDC ML"),
    ("Halmahera_M4.1", G(25, 13, 9.79), 2.3862, 128.1896, 63.4, 4.1, "USGS mb"),
]
STATIONS = [s for s in S.ZCHAN if s != "MBWA"]  # MBWA: periodic square-wave artifact on BHZ/HHZ


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    traces = {s: S.load(s) for s in STATIONS}
    env = {}
    nulls = {}
    for s, tr in traces.items():
        for b, (f1, f2) in S.bands_for(tr).items():
            env[(s, b, "P")] = S.band_env(tr, f1, f2, win_s=2.0, step_s=0.5)
            env[(s, b, "T")] = S.band_env(tr, f1, f2, win_s=5.0, step_s=1.0)
    rows = []
    for name, t0, la, lo, dep, mag, mt in EVENTS:
        for s in STATIONS:
            sla, slo = S.coords(s)
            d, _ = A.dist_az(la, lo, sla, slo)
            d = float(d)
            if d > MAX_KM:
                continue
            tP, tS, deg = S.ps_times(la, lo, dep, sla, slo)
            for b in S.bands_for(traces[s]):
                # P
                t, e = env[(s, b, "P")]
                w0, w1 = t0 + tP - 5, t0 + tP + 15
                snr, tmax = S.window_stat(t, e, w0, w1, noise=(-300, -15), ref=t0 + tP)
                key = (s, b, "P", 20.0)
                if key not in nulls:
                    nulls[key] = S.null_distribution(t, e, 20.0, noise=(-300, -15), step=5.0)
                pval = float((nulls[key] >= snr).mean()) if np.isfinite(snr) else np.nan
                rows.append(dict(event=name, mag=mag, depth_km=dep, station=s, band=b,
                                 dist_km=round(d), deg=round(deg, 2), phase="P",
                                 pred=A.fmt(t0 + tP, 1), w0=A.fmt(w0), w1=A.fmt(w1),
                                 snr_db=round(snr, 1), t_max=A.fmt(tmax, 1) if np.isfinite(tmax) else "",
                                 resid_s=round(tmax - (t0 + tP), 1) if np.isfinite(tmax) else "",
                                 p_null=round(pval, 4)))
                # T (shallow events; window start must be after S + 20 s to avoid S coda)
                if dep > 70:
                    continue
                t, e = env[(s, b, "T")]
                w0, w1 = S.t_window(d, t0)
                w0 = max(w0, t0 + tS + 20) if np.isfinite(tS) else w0
                if w1 <= w0 + 20:
                    continue
                wl = w1 - w0
                snr, tmax = S.window_stat(t, e, w0, w1, noise=(-900, -60), ref=t0 + tP)
                key = (s, b, "T", round(wl / 10) * 10)
                if key not in nulls:
                    nulls[key] = S.null_distribution(t, e, key[3], noise=(-900, -60), step=10.0)
                pval = float((nulls[key] >= snr).mean()) if np.isfinite(snr) else np.nan
                rows.append(dict(event=name, mag=mag, depth_km=dep, station=s, band=b,
                                 dist_km=round(d), deg=round(deg, 2), phase="T",
                                 pred=A.fmt(t0 + d / A.C_SOFAR, 1), w0=A.fmt(w0), w1=A.fmt(w1),
                                 snr_db=round(snr, 1), t_max=A.fmt(tmax, 1) if np.isfinite(tmax) else "",
                                 resid_s=round(tmax - (t0 + d / A.C_SOFAR), 1) if np.isfinite(tmax) else "",
                                 p_null=round(pval, 4)))
    with open(OUT / "calibration_measurements.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(OUT / "calibration_events.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event", "origin_utc", "lat", "lon", "depth_km", "mag", "source"])
        for name, t0, la, lo, dep, mag, mt in EVENTS:
            w.writerow([name, A.dt_of(t0).isoformat(), la, lo, dep, mag, mt])
    print(f"{len(rows)} measurements")

    # Figures for three key events: envelope record sections with P/S/T marks
    for name in ("Java_M4.1", "IAR_M4.5", "MauritiusReunion_mb3.7", "Macquarie_M4.2"):
        ev = [e for e in EVENTS if e[0] == name][0]
        _, t0, la, lo, dep, mag, _ = ev
        sts = []
        for s in STATIONS:
            sla, slo = S.coords(s)
            d = float(A.dist_az(la, lo, sla, slo)[0])
            if d <= MAX_KM:
                sts.append((d, s))
        sts.sort()
        fig, ax = plt.subplots(figsize=(10, 0.55 * len(sts) + 1.5))
        tmax_plot = max(d for d, _ in sts) / 1.46 + 240
        for k, (d, s) in enumerate(sts):
            t, e = env[(s, "2-8", "T")]
            m = (t >= t0 - 120) & (t <= t0 + tmax_plot)
            y = 20 * np.log10(e[m] / np.median(e[m]))
            ax.plot((t[m] - t0) / 60, k + np.clip(y, -5, 40) / 40 * 0.9, lw=0.6, color="k")
            sla, slo = S.coords(s)
            tP, tS, _ = S.ps_times(la, lo, dep, sla, slo)
            ax.plot([tP / 60] * 2, [k, k + 0.9], color="tab:blue", lw=1.2)
            if np.isfinite(tS):
                ax.plot([tS / 60] * 2, [k, k + 0.9], color="tab:green", lw=1.2)
            if dep <= 70:
                ax.fill_betweenx([k, k + 0.9], d / 1.50 / 60, d / 1.46 / 60, color="tab:orange", alpha=0.3)
            ax.text((t0 + tmax_plot - t0) / 60 * 1.005, k + 0.3, f"{s} {d:.0f} km", fontsize=8)
        ax.set_xlim(-2, tmax_plot / 60)
        ax.set_yticks([])
        ax.set_xlabel(f"minutes after origin {A.fmt(t0, 1)} UTC")
        ax.set_title(f"{name} ({la:.2f}, {lo:.2f}, {dep:.0f} km): 2-8 Hz 5-s RMS envelope, dB re trace median "
                     "(0-40 dB per row)\nblue=P, green=S (ak135), orange=T window 1.50-1.46 km/s", fontsize=9)
        fig.tight_layout()
        fig.savefig(OUT / f"fig_calibration_{name}.png", dpi=130)
        plt.close(fig)


if __name__ == "__main__":
    main()
