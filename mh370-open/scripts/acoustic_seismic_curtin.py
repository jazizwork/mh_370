"""Candidate (4): the 'Curtin event' (HA01 01:34:40 on bearing ~301.6 deg; Kimberley/Scott
Reef 01:32:49), relocated by Curtin in Sep 2014 to the Carlsberg Ridge (2.11N 69.31E).

Tests with open seismometers:
  * origin time implied by HA01 01:34:40 for a Carlsberg source at c = 1.47/1.48/1.49 km/s;
  * predicted P/S (ak135) and T (geodesic/c) at MNC (Minicoy), KAAM (Maldives), DGAR,
    RODM/ROCAM, COCO, AIS; observed band envelopes and SNR vs empirical null;
  * Anderson's picks (Minicoy 00:28:40, Maldives 00:30:00);
  * blind scan: STA/LTA triggers 23:30-01:40 at MNC, KAAM, DGAR, RODM and a simple
    grid-search association for a common source (ridge region) using P and T moveout.

Outputs: outputs/acoustic/seismic/curtin_predictions.csv, curtin_triggers.csv,
         fig_curtin_record_section.png
"""
from __future__ import annotations

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from obspy.signal.trigger import classic_sta_lta, trigger_onset

from mh370 import acoustic as A
from mh370 import acoustic_seismic as S

OUT = A.ROOT / "outputs" / "acoustic" / "seismic"
SRC = dict(lat=2.11, lon=69.31, depth=10.0)
T_HA01 = A.hms8(1, 34, 40)
STAS = ["MNC", "KAAM", "DGAR", "RODM", "ROCAM", "COCO", "AIS", "XMIS"]
ANDERSON = {"MNC": A.hms8(0, 28, 40), "KAAM": A.hms8(0, 30, 0)}


def main():
    ha = A.RECEIVERS["HA01"]
    d_ha, az_ha = A.dist_az(ha["lat"], ha["lon"], SRC["lat"], SRC["lon"])
    d_ha = float(d_ha)
    origins = {c: T_HA01 - d_ha / c for c in (1.47, 1.48, 1.49)}
    print(f"Carlsberg->HA01 {d_ha:.0f} km, back-azimuth from HA01 {float(az_ha):.2f} deg; origin "
          + ", ".join(f"c={c}: {A.fmt(t)}" for c, t in origins.items()))
    t0 = origins[1.48]
    pk = A.RECEIVERS["PAKIM"]
    d_pk = float(A.dist_az(SRC["lat"], SRC["lon"], pk["lat"], pk["lon"])[0])
    pk_pred = {c: A.fmt(o + d_pk / c) for c, o in origins.items()}
    print(f"Carlsberg->PAKIM {d_pk:.0f} km; predicted PAKIM T: {pk_pred} (Curtin 'Scott Reef' 01:32:49)")
    blk_pk = A.blockage_summary(SRC["lat"], SRC["lon"], "PAKIM")
    blk_ha = A.blockage_summary(SRC["lat"], SRC["lon"], "HA01")
    print("blockage PAKIM", blk_pk)
    print("blockage HA01", blk_ha)

    rows = []
    traces = {s: S.load(s) for s in STAS}
    fig, ax = plt.subplots(figsize=(11, 8))
    order = sorted(STAS, key=lambda s: float(A.dist_az(SRC["lat"], SRC["lon"], *S.coords(s))[0]))
    for i, s in enumerate(order):
        tr = traces[s]
        sla, slo = S.coords(s)
        d = float(A.dist_az(SRC["lat"], SRC["lon"], sla, slo)[0])
        tP, tS, deg = S.ps_times(SRC["lat"], SRC["lon"], SRC["depth"], sla, slo)
        blk = A.blockage_summary(SRC["lat"], SRC["lon"], "HA01") if False else None
        for band, (f1, f2) in S.bands_for(tr).items():
            t, e = S.band_env(tr, f1, f2, win_s=2.0, step_s=0.5)
            for ph, tc, half in (("P", t0 + tP, (10 + 7, 25 + 7)), ("S", t0 + tS, (15 + 7, 35 + 7))):
                # +/-7 s from the 1.47-1.49 km/s origin-time spread
                snr, tm = S.window_stat(t, e, tc - half[0], tc + half[1], noise=(-600, -30), ref=tc - half[0])
                nul = S.null_distribution(t, e, sum(half), noise=(-600, -30), step=5.0)
                rows.append(dict(station=s, band=band, phase=ph, dist_km=round(d), pred=A.fmt(tc, 1),
                                 window=f"{A.fmt(tc - half[0])}-{A.fmt(tc + half[1])}",
                                 snr_db=round(snr, 1), t_max=A.fmt(tm, 1),
                                 p_null=round(float((nul >= snr).mean()), 3)))
            tt, ee = S.band_env(tr, f1, f2, win_s=5.0, step_s=1.0)
            w0, w1 = origins[1.49] + d / 1.50 - 30, origins[1.47] + d / 1.46 + 60
            snr, tm = S.window_stat(tt, ee, w0, w1, noise=(-900, -60), ref=t0 + tP)
            nul = S.null_distribution(tt, ee, w1 - w0, noise=(-900, -60), step=10.0)
            rows.append(dict(station=s, band=band, phase="T", dist_km=round(d), pred=A.fmt(t0 + d / 1.48, 1),
                             window=f"{A.fmt(w0)}-{A.fmt(w1)}", snr_db=round(snr, 1), t_max=A.fmt(tm, 1),
                             p_null=round(float((nul >= snr).mean()), 3)))
        # plot 2-8 Hz envelope dB
        t, e = S.band_env(tr, 2.0, 8.0, win_s=2.0, step_s=0.5)
        m = (t >= A.hms8(0, 10)) & (t <= A.hms8(0, 55))
        y = 20 * np.log10(e[m] / np.median(e[m]))
        ax.plot((t[m] - t0) / 60, i + np.clip(y, -5, 30) / 30 * 0.9, lw=0.6, color="k")
        ax.plot([tP / 60] * 2, [i, i + .9], color="tab:blue", lw=1.5)
        ax.plot([tS / 60] * 2, [i, i + .9], color="tab:green", lw=1.5)
        ax.fill_betweenx([i, i + .9], (origins[1.49] - t0 + d / 1.50) / 60, (origins[1.47] - t0 + d / 1.46) / 60,
                         color="tab:orange", alpha=0.35)
        if s in ANDERSON:
            ax.plot([(ANDERSON[s] - t0) / 60] * 2, [i, i + .9], "r--", lw=1.2)
        ax.text((A.hms8(0, 55) - t0) / 60 + 0.2, i + 0.3, f"{s} {d:.0f} km", fontsize=8)
    ax.set_xlim((A.hms8(0, 10) - t0) / 60, (A.hms8(0, 55) - t0) / 60 + 4)
    ax.set_yticks([])
    ax.set_xlabel(f"minutes after implied origin {A.fmt(t0)} UTC (Carlsberg 2.11N 69.31E, HA01 01:34:40, c=1.48)")
    ax.set_title("Curtin/Carlsberg test: Z 2-8 Hz 2-s RMS envelope (dB re median, 0-30 dB per row)\n"
                 "blue P, green S (ak135); orange T window (c 1.46-1.50, origin for c 1.47-1.49); "
                 "red dashed: Anderson's picks", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fig_curtin_record_section.png", dpi=130)

    with open(OUT / "curtin_predictions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
        f.write("\n# Carlsberg->HA01 km,%.0f\n# implied origin c=1.47/1.48/1.49,%s\n" %
                (d_ha, "/".join(A.fmt(o) for o in origins.values())))
        f.write("# Carlsberg->PAKIM km,%.0f; predicted PAKIM T c=1.47/1.48/1.49,%s\n" %
                (d_pk, "/".join(pk_pred.values())))
        f.write(f"# blockage to PAKIM (max elevation along path excl. ends),{blk_pk}\n")
        f.write(f"# blockage to HA01,{blk_ha}\n")

    # Anderson picks vs predictions
    for s, ta in ANDERSON.items():
        sla, slo = S.coords(s)
        d = float(A.dist_az(SRC["lat"], SRC["lon"], sla, slo)[0])
        tP, tS, _ = S.ps_times(SRC["lat"], SRC["lon"], SRC["depth"], sla, slo)
        print(f"{s}: Anderson {A.fmt(ta)}; pred P {A.fmt(t0 + tP)} S {A.fmt(t0 + tS)} "
              f"T {A.fmt(t0 + d / 1.48)}; implied origin if P: {A.fmt(ta - tP)}, if S: {A.fmt(ta - tS)}, "
              f"if T: {A.fmt(ta - d / 1.48)}")

    # STA/LTA triggers 23:30-01:40 at the four western stations (2-8 Hz)
    trig = []
    for s in ("MNC", "KAAM", "DGAR", "RODM"):
        tr = traces[s].copy()
        tr.filter("bandpass", freqmin=2, freqmax=8, corners=4, zerophase=True)
        tr.trim(S.ut(A.hms8(-1, 30) + 0), S.ut(A.hms8(1, 40)))
        fs = tr.stats.sampling_rate
        cft = classic_sta_lta(tr.data, int(2 * fs), int(60 * fs))
        for on, off in trigger_onset(cft, 4.0, 1.5):
            ton = S.tp(tr.stats.starttime) + on / fs
            trig.append((s, A.fmt(ton, 1), round(float(cft[on:off + 1].max()), 1), round((off - on) / fs, 1)))
    with open(OUT / "curtin_triggers.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station", "trigger_on_utc", "max_sta_lta", "duration_s"])
        w.writerows(trig)
    for x in trig:
        if A.hms8(0, 15) <= A.parse_hms8(x[1]) <= A.hms8(0, 50):
            print("trigger", x)


if __name__ == "__main__":
    main()


# --------------------------------------------------------------------------------------
# Association: where along the HA01 301.6 deg bearing does the HA01-PAKIM T-time difference
# put the source, and does a free grid search with the weak open-seismic T picks agree?
# PAKIM time: Curtin 2014 'Scott Reef' 01:32:49 (published) and 01:32:56 (quick-look value
# in research notes); the parent IMOS analysis supersedes these.
# --------------------------------------------------------------------------------------
def associate():
    ha = A.RECEIVERS["HA01"]
    pk = A.RECEIVERS["PAKIM"]
    rows = []
    rs = np.arange(500.0, 7500.0, 5.0)
    for az in (300.85, 301.6, 302.35):
        la, lo = A.forward(np.full(rs.shape, ha["lat"]), np.full(rs.shape, ha["lon"]),
                           np.full(rs.shape, az), rs)
        dpk = A.dist_az(pk["lat"], pk["lon"], la, lo)[0]
        for tpk_lab, tpk in (("01:32:49", A.hms8(1, 32, 49)), ("01:32:56", A.hms8(1, 32, 56))):
            for c in (1.47, 1.48, 1.49):
                f = (dpk - rs) / c - (tpk - T_HA01)
                k = np.where(np.sign(f[:-1]) != np.sign(f[1:]))[0]
                for kk in k[:2]:
                    rows.append(dict(az=az, pakim=tpk_lab, c=c, range_km=float(rs[kk]),
                                     lat=round(float(la[kk]), 2), lon=round(float(lo[kk]), 2),
                                     origin=A.fmt(T_HA01 - rs[kk] / c)))
    # grid search: T times at HA01, PAKIM(01:32:49+/-10), KAAM 00:30:02+/-15, DGAR 00:37:47+/-20,
    # plus HA01 bearing 301.6+/-0.75
    obs = [("HA01", T_HA01, 5.0), ("PAKIM", A.hms8(1, 32, 52), 10.0),
           ("KAAM", A.hms8(0, 30, 2), 15.0), ("DGAR", A.hms8(0, 37, 47), 20.0)]
    lats = np.arange(-12, 12.01, 0.1)
    lons = np.arange(58, 82.01, 0.1)
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    best = {}
    for use in (("HA01", "PAKIM"), ("HA01", "PAKIM", "KAAM", "DGAR")):
        res, w = [], []
        for name, t, sig in obs:
            if name not in use:
                continue
            if name in A.RECEIVERS:
                rla, rlo = A.RECEIVERS[name]["lat"], A.RECEIVERS[name]["lon"]
            else:
                rla, rlo = S.coords(name)
            d = A.dist_az(rla, rlo, LA.ravel(), LO.ravel())[0].reshape(LA.shape)
            res.append(t - d / 1.48)
            w.append(1 / sig ** 2)
        res, w = np.array(res), np.array(w)[:, None, None]
        t0 = (res * w).sum(0) / w.sum(0)
        chi2 = (((res - t0) ** 2) * w).sum(0)
        _, baz = A.dist_az(ha["lat"], ha["lon"], LA.ravel(), LO.ravel())
        chi2 = chi2 + ((((baz.reshape(LA.shape) - 301.6 + 180) % 360 - 180) / 0.75) ** 2)
        i, j = np.unravel_index(np.argmin(chi2), chi2.shape)
        best[use] = (lats[i], lons[j], A.fmt(t0[i, j]), float(chi2[i, j]), chi2, t0)
        print("association", use, "best", round(lats[i], 2), round(lons[j], 2), A.fmt(t0[i, j]),
              "chi2", round(float(chi2[i, j]), 2), "dist to Carlsberg pt",
              round(float(A.dist_az(lats[i], lons[j], SRC["lat"], SRC["lon"])[0])), "km")
    with open(OUT / "curtin_association.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
        for use, b in best.items():
            f.write(f"# grid best using {'+'.join(use)} (+HA01 bearing 301.6+/-0.75): lat {b[0]:.2f} lon {b[1]:.2f} "
                    f"origin {b[2]} chi2 {b[3]:.2f}\n")
    for r in rows:
        if r["c"] == 1.48:
            print(r)
    # map
    fig, ax = plt.subplots(figsize=(8, 7))
    use = ("HA01", "PAKIM", "KAAM", "DGAR")
    chi2 = best[use][4]
    cs = ax.contourf(lons, lats, chi2, levels=[0, 2.3, 6.2, 11.8, 30, 100], cmap="Blues_r", alpha=0.8)
    plt.colorbar(cs, ax=ax, label="chi2 (T at HA01, PAKIM, KAAM, DGAR + HA01 bearing)")
    bz = A.bathy()
    li = (bz[0] >= -12) & (bz[0] <= 12)
    lj = (bz[1] >= 58) & (bz[1] <= 82)
    ax.contour(bz[1][lj], bz[0][li], bz[2][np.ix_(li, lj)], levels=[0], colors="k", linewidths=0.7)
    ax.contour(bz[1][lj], bz[0][li], bz[2][np.ix_(li, lj)], levels=[-1000], colors="grey", linewidths=0.4)
    rr = np.arange(4000, 7000, 20.0)
    for az in (300.85, 301.6, 302.35):
        la, lo = A.forward(np.full(rr.shape, ha["lat"]), np.full(rr.shape, ha["lon"]),
                           np.full(rr.shape, az), rr)
        ax.plot(lo, la, "r-" if az == 301.6 else "r:", lw=1)
    ax.plot(SRC["lon"], SRC["lat"], "k*", ms=14, label="Curtin Carlsberg Ridge (2.11N 69.31E)")
    ax.plot(77.22, -5.93, "kD", label="Curtin June 2014 (5.93S 77.22E)")
    for s in ("KAAM", "DGAR", "MNC"):
        la, lo = S.coords(s)
        ax.plot(lo, la, "g^", ms=8)
        ax.text(lo + 0.2, la, s, fontsize=8)
    b = best[use]
    ax.plot(b[1], b[0], "yo", mec="k", ms=9, label=f"best fit {b[0]:.1f},{b[1]:.1f} origin {b[2]}")
    ax.set_xlim(58, 82)
    ax.set_ylim(-12, 12)
    ax.legend(fontsize=7, loc="lower left")
    ax.set_title("Curtin event: HA01 bearing 301.6+/-0.75 (red), T-phase association\n"
                 "(HA01 01:34:40, PAKIM ~01:32:52, KAAM 00:30:02*, DGAR 00:37:47*; *weak open-seismic picks)",
                 fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_curtin_association.png", dpi=130)


if __name__ == "__main__":
    associate()
