"""Workstream D step 3: detection on IMOS windows, false-alarm rates, and candidate tests.

1. Band-level excess detector (2-s RMS levels, 0.5-s step; excess over a 120-s running median;
   >= 6 dB for >= 2 s; bands 5-10, 8-16, 10-20, 16-32, 20-40, 40-80 Hz) on every file of the
   main night (7/8 Mar 21:40-03:05 UTC) and 8 control nights. Detections merged across bands
   into events. Main-night events get spectral/impulsiveness features.
2. False-alarm rates (events/hour vs threshold), main night vs control nights.
3. Candidate tests: for each predicted arrival window (HA01 picks -> IMOS via TDOA along the
   bearing; located sources; 7th-arc grid), the statistic S = max over 5-40 Hz bands of the
   max excess (dB over file median) inside the window, for 2-s levels (S0) and 10-s
   power-averaged levels (S10), and for an 8-s running median of the 2-s levels (Sm8: robust to
   impulsive knocks/clicks shorter than ~4 s; the primary 'arrival-like' statistic);
   p = fraction of control-night windows of equal width with S >= observed (same site, slid
   every 5 s). Slf: the same arrival-like statistic restricted to 5-20 Hz (T-phase band, avoids
   the 20-40 Hz whale-song bands that dominate the PAKIM/PAPCA nulls).
4. STA/LTA (2 s / 30 s) triggers in 8-16 and 10-20 Hz for the main night (reported).

Outputs (outputs/acoustic/): detections_events_all.csv, detections_20140308.csv,
  far_by_threshold.csv, tests_candidates.csv, tests_arc_grid.csv, stalta_20140308.csv,
  fig_far.png, fig_spec_*.png, fig_arc_pvalues.png
Run: .venv/bin/python -I scripts/acoustic_detect.py
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal, stats

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"
EV_BANDS = A.DET_BANDS + ("40-80",)
THR, MIN_DUR, BG_WIN = 6.0, 2.0, 120.0
C_LO, C_HI = A.C_SENS


# ----------------------------------------------------------------------------- features
def _feat(args):
    site, p = args
    return str(p), A.file_features(p, site)


def load_night(site, day):
    fl = A.night_files(site, day)
    with ProcessPoolExecutor(8) as ex:
        res = dict(ex.map(_feat, [(site, p) for p in fl]))
    return [(p, res[str(p)]) for p in fl]


# ----------------------------------------------------------------------------- detector
def detect_file(site, night, path, feat):
    t = feat["t"]
    segs = []
    for b in EV_BANDS:
        s, _ = A.excess_segments(t, feat[f"L_{b}"].astype(float), THR, MIN_DUR, BG_WIN, 0.5, 2.0)
        for x in s:
            segs.append((x["t_on"], x["t_off"], x["peak_db"], x["t_peak"], b))
    segs.sort()
    events = []
    for on, off, pk, tp, b in segs:
        if events and on <= events[-1]["t_off"] + 2.0:
            e = events[-1]
            e["t_off"] = max(e["t_off"], off)
            e["bands"].add(b)
            if pk > e["peak_db"]:
                e.update(peak_db=pk, t_peak=tp, band_max=b)
        else:
            events.append(dict(t_on=on, t_off=off, peak_db=pk, t_peak=tp, band_max=b, bands={b}))
    out = []
    for e in events:
        out.append(dict(site=site, night=night, file=path.stem, t_on=e["t_on"], t_off=e["t_off"],
                        dur=e["t_off"] - e["t_on"] + 0.5, t_peak=e["t_peak"], peak_db=e["peak_db"],
                        band_max=e["band_max"], bands="|".join(sorted(e["bands"], key=lambda z: A.BANDS[z][0])),
                        n_bands=len(e["bands"]),
                        lf_only=all(A.BANDS[z][1] <= 20 for z in e["bands"])))
    return out


def event_features(site, path, evs):
    """Spectral peak, LF fraction and kurtosis for events of one file (main night)."""
    if not evs:
        return evs
    t0, fs, p, rec = A.read_pressure(path, site, 500.0, full=True)
    tt = t0 + np.arange(p.size) / fs
    f, ts, S = signal.spectrogram(p, fs, nperseg=500, noverlap=250)
    ts = t0 + ts
    med = np.median(S, axis=1)
    bb = A.bandpass(p, fs, 5, 100)
    for e in evs:
        m = (ts >= e["t_on"] - 0.5) & (ts <= e["t_off"] + 0.5)
        if not m.any():
            continue
        ex = 10 * np.log10(np.mean(S[:, m], axis=1) / med)
        k = (f >= 5) & (f <= 100)
        e["f_peak_hz"] = float(f[k][np.argmax(ex[k])])
        pw = np.mean(S[:, m], axis=1) - med
        pw = np.clip(pw, 0, None)
        e["lf_frac_5_20"] = float(pw[(f >= 5) & (f <= 20)].sum() / max(pw[k].sum(), 1e-30))
        mm = (tt >= e["t_on"] - 1) & (tt <= e["t_off"] + 1)
        e["kurtosis"] = float(stats.kurtosis(bb[mm])) if mm.sum() > 10 else np.nan
        e["peak_pa"] = float(np.abs(bb[mm]).max() / 1e6) if mm.any() else np.nan
    return evs


# ----------------------------------------------------------------------------- windows
def ha01_pick_window(site, t_ha01, az, daz, rmin=500.0, rmax=6000.0, pad=10.0):
    """Arrival window at an IMOS site for a source anywhere on the HA01 ray (az +/- daz,
    range rmin..rmax) whose HA01 arrival was t_ha01; c = 1.47..1.49 km/s."""
    ts = []
    for a in np.linspace(az - daz, az + daz, 5):
        for R in np.linspace(rmin, rmax, 56):
            la, lo = A.ray_points("HA01", a, np.array([R]))
            d, _ = A.rdist_az(site, float(la[0]), float(lo[0]))
            for c in (C_LO, A.C_SOFAR, C_HI):
                ts.append(t_ha01 + (float(d) - R) / c)
    return min(ts) - pad, max(ts) + pad


def candidate_windows():
    """List of (test_id, site, t1, t2, description)."""
    W = []
    picks = [(f"Kadri_{t}_{az:.2f}", A.parse_hms8(t), az, 0.4) for t, az, _ in A.KADRI_TABLE1]
    picks += [("Stead_246.9", A.HA01_CANDIDATES["Stead247"]["t"], 246.9, 2.0),
              ("Curtin_301.6", A.HA01_CANDIDATES["Curtin301"]["t"], 301.6, 0.75)]
    for name, t, az, daz in picks:
        for s in A.IMOS_SITES:
            # (a) source anywhere along the bearing (500-6000 km)
            a, b = ha01_pick_window(s, t, az, daz)
            W.append((f"{name}|ray", s, a, b, f"HA01 {A.fmt(t)} az {az}+/-{daz}, source 500-6000 km on ray"))
            # (b) source at the 7th-arc crossing of the bearing
            R, la, lo = A.arc_crossing("HA01", az)
            if np.isfinite(R):
                d, _ = A.rdist_az(s, la, lo)
                tt = [t + (float(d) - R) / c for c in (C_LO, C_HI)]
                W.append((f"{name}|arc", s, min(tt) - 10, max(tt) + 10,
                          f"source at arc crossing ({la:.2f},{lo:.2f}), origin from HA01 pick"))
    # located sources
    jv = A.SOURCES["Java_Anderson"]
    for s in A.IMOS_SITES:
        d, _ = A.rdist_az(s, jv["lat"], jv["lon"])
        d = float(d)
        W.append(("Java_0115|T", s, jv["t0"] + d / 1.50 - 10, jv["t0"] + d / 1.46 + 60,
                  "Anderson 01:15:18 Java event T-phase (c 1.46-1.50, +60 s for emergent peak)"))
    car = A.SOURCES["Carlsberg_Curtin"]
    dH, _ = A.rdist_az("HA01", car["lat"], car["lon"])
    for s in A.IMOS_SITES:
        d, _ = A.rdist_az(s, car["lat"], car["lon"])
        tt = [A.HA01_CANDIDATES["Curtin301"]["t"] + (float(d) - float(dH)) / c for c in (C_LO, C_HI)]
        W.append(("Carlsberg|T", s, min(tt) - 15, max(tt) + 15,
                  "Curtin/Carlsberg source, origin implied by HA01 01:34:40"))
    W.append(("Curtin_ScottReef_0132:49|obs", "PAKIM", A.hms8(1, 32, 49) - 15, A.hms8(1, 32, 49) + 15,
              "Curtin's reported 'Scott Reef' arrival 01:32:49 +/-15 s"))
    k13 = A.SOURCES["Kadri_ref13"]
    for s in A.IMOS_SITES:
        d, _ = A.rdist_az(s, k13["lat"], k13["lon"])
        dH, _ = A.rdist_az("HA01", k13["lat"], k13["lon"])
        tt = [A.HA01_CANDIDATES["Curtin301"]["t"] + (float(d) - float(dH)) / c for c in (C_LO, C_HI)]
        W.append(("Kadri_ref13|T", s, min(tt) - 15, max(tt) + 15,
                  "Kadri ref-13 location of the 01:34:40 signal (23.66S 96.68E)"))
    return W


def arc_windows():
    lats, lons = A.arc7_points(-42.0, -20.0, 0.5)
    W = []
    for la, lo in zip(lats, lons):
        for s in A.IMOS_SITES:
            d, _ = A.rdist_az(s, la, lo)
            a = A.hms8(0, 19, 30) + float(d) / C_HI - 10
            b = A.hms8(0, 25, 0) + float(d) / C_LO + 10
            W.append((f"arc_{la:.1f}", s, a, b, f"impact 00:19:30-00:25 at ({la:.1f},{lo:.2f})"))
    return W


def test_windows(W, main, ctrl, nulls):
    rows = []
    for tid, s, a, b, desc in W:
        files = [(p, f) for p, f in main[s] if f["t"][-1] >= a and f["t"][0] <= b]
        cov = 0.0
        best0 = (np.nan, "", np.nan)
        best10 = (np.nan, "", np.nan)
        bestm = (np.nan, "", np.nan)
        bestl = (np.nan, "", np.nan)
        for p, f in files:
            lo, hi = max(a, f["t"][0] + 5), min(b, f["t"][-1] - 5)
            if hi <= lo:
                continue
            cov += hi - lo
            r0 = A.window_stat(f, lo, hi, smooth_s=0.0)
            r10 = A.window_stat(f, lo, hi, smooth_s=10.0)
            rm = A.window_stat(f, lo, hi, smooth_s=-8.0)
            rl = A.window_stat(f, lo, hi, bands=A.LF_BANDS, smooth_s=-8.0)
            if not np.isfinite(bestl[0]) or rl[0] > bestl[0]:
                bestl = rl
            if not np.isfinite(best0[0]) or r0[0] > best0[0]:
                best0 = r0
            if not np.isfinite(best10[0]) or r10[0] > best10[0]:
                best10 = r10
            if not np.isfinite(bestm[0]) or rm[0] > bestm[0]:
                bestm = rm
        width = cov
        row = dict(test=tid, site=s, t1=A.fmt(a), t2=A.fmt(b), width_s=b - a, covered_s=cov,
                   coverage=cov / (b - a), desc=desc)
        if cov > 0:
            wq = int(max(10, round(min(width, 290) / 10) * 10))
            for sm, best, lab, bands in ((0, best0, "0", A.DET_BANDS), (10, best10, "10", A.DET_BANDS),
                                         (-8, bestm, "m8", A.DET_BANDS), (-8, bestl, "lf", A.LF_BANDS)):
                key = (s, wq, sm, lab)
                if key not in nulls:
                    nulls[key] = A.null_window_stats([f for _, f in ctrl[s]], wq, bands=bands, smooth_s=float(sm),
                                                     step_s=5.0)
                row[f"S{lab}_db"] = best[0]
                row[f"S{lab}_band"] = best[1]
                row[f"S{lab}_t"] = A.fmt(best[2]) if np.isfinite(best[2]) else ""
                row[f"p{lab}"] = A.pvalue(best[0], nulls[key])
        rows.append(row)
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- figures
def spec_figure(site, path, marks, fname, title):
    t0, fs, p, rec = A.read_pressure(path, site, 250.0, full=True)
    f, tt, S = A.spectrogram_db(p, fs, nperseg=256)
    fig, axs = plt.subplots(2, 1, figsize=(13, 6.5), sharex=True,
                            gridspec_kw=dict(height_ratios=[1.4, 1]))
    x = (t0 + tt - A.hms8(0)) / 60
    im = axs[0].pcolormesh(x, f, S, shading="auto", cmap="viridis",
                           vmin=np.percentile(S, 5), vmax=np.percentile(S, 99.7))
    fig.colorbar(im, ax=axs[0], pad=0.01, label="dB re 1 uPa^2/Hz")
    axs[0].set_ylim(3, 110)
    axs[0].set_ylabel("Hz")
    for b in ("5-10", "8-16", "10-20", "16-32", "20-40"):
        f1, f2 = A.BANDS[b]
        tr, L = A.band_level(p, fs, f1, f2)
        axs[1].plot((t0 + tr - A.hms8(0)) / 60, L - np.median(L), lw=0.7, label=f"{b} Hz")
    cols = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for i, (lab, a, b) in enumerate(marks):
        for ax in axs:
            ax.axvspan((a - A.hms8(0)) / 60, (b - A.hms8(0)) / 60, color=cols[(i + 5) % len(cols)], alpha=0.18)
        axs[0].text((a - A.hms8(0)) / 60, 105 - 9 * (i % 6), lab, fontsize=7, color="w",
                    bbox=dict(facecolor=cols[(i + 5) % len(cols)], alpha=0.7, lw=0))
    axs[1].axhline(6, color="k", ls=":", lw=0.8)
    axs[1].set_ylabel("excess over file median (dB)")
    axs[1].set_xlabel("minutes after 2014-03-08 00:00 UTC")
    axs[1].legend(fontsize=7, ncol=5, loc="upper left")
    axs[1].grid(alpha=0.3)
    axs[0].set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=120)
    plt.close(fig)


def main():
    nights = [A.MAIN_DAY] + A.CONTROL_DAYS
    data = {s: {d: load_night(s, d) for d in nights} for s in A.IMOS_SITES}
    main_ = {s: data[s][A.MAIN_DAY] for s in A.IMOS_SITES}
    ctrl = {s: [x for d in A.CONTROL_DAYS for x in data[s][d]] for s in A.IMOS_SITES}

    # 1. detections, all nights
    allev = []
    for s in A.IMOS_SITES:
        for d in nights:
            for p, f in data[s][d]:
                evs = detect_file(s, d.isoformat(), p, f)
                if d == A.MAIN_DAY:
                    evs = event_features(s, p, evs)
                allev += evs
    ev = pd.DataFrame(allev)
    ev["t_on_str"] = [A.fmt(t, 1) for t in ev.t_on]
    ev["t_peak_str"] = [A.fmt(t, 1) for t in ev.t_peak]
    ev.to_csv(OUT / "detections_events_all.csv", index=False, float_format="%.3f")
    mn = ev[ev.night == A.MAIN_DAY.isoformat()]
    mn.to_csv(OUT / "detections_20140308.csv", index=False, float_format="%.3f")

    # 2. FAR
    hours = {s: {d.isoformat(): sum(f["t"][-1] - f["t"][0] for _, f in data[s][d]) / 3600 for d in nights}
             for s in A.IMOS_SITES}
    frows = []
    for s in A.IMOS_SITES:
        for d in nights:
            e = ev[(ev.site == s) & (ev.night == d.isoformat())]
            for thr in (6, 10, 15, 20):
                for kind, sel in (("any", e.peak_db >= thr),
                                  ("5-40Hz,>=5s", (e.peak_db >= thr) & (e.dur >= 5) & (e.band_max != "40-80"))):
                    frows.append(dict(site=s, night=d.isoformat(), main=d == A.MAIN_DAY, thr_db=thr, kind=kind,
                                      n=int(sel.sum()), rec_hours=hours[s][d.isoformat()],
                                      per_hour=sel.sum() / hours[s][d.isoformat()]))
    far = pd.DataFrame(frows)
    far.to_csv(OUT / "far_by_threshold.csv", index=False, float_format="%.3f")
    print(far.pivot_table(index=["site", "kind", "thr_db"], columns="main", values="per_hour",
                          aggfunc="median").round(2))

    # 3. tests
    nulls = {}
    tc = test_windows(candidate_windows(), main_, ctrl, nulls)
    tc.to_csv(OUT / "tests_candidates.csv", index=False, float_format="%.3f")
    ta = test_windows(arc_windows(), main_, ctrl, nulls)
    ta.to_csv(OUT / "tests_arc_grid.csv", index=False, float_format="%.3f")
    pd.set_option("display.width", 250)
    print(tc[tc.coverage > 0][["test", "site", "t1", "t2", "coverage", "S0_db", "S0_band", "S0_t", "p0",
                               "Sm8_db", "Sm8_t", "pm8", "Slf_db", "Slf_t", "plf"]].to_string())
    print(ta[ta.coverage > 0][["test", "site", "t1", "t2", "coverage", "S0_db", "p0",
                               "Sm8_db", "Sm8_t", "pm8", "Slf_db", "Slf_t", "plf"]].to_string())

    # main night vs controls: whole-distribution comparison of S10 in 60-s windows
    for s in A.IMOS_SITES:
        nm = A.null_window_stats([f for _, f in main_[s]], 60, smooth_s=10.0, step_s=5.0)
        key = (s, 60, 10, "10")
        if key not in nulls:
            nulls[key] = A.null_window_stats([f for _, f in ctrl[s]], 60, smooth_s=10.0, step_s=5.0)
        ks = stats.ks_2samp(nm, nulls[key])
        print(f"{s}: 60-s window S10, main median {np.median(nm):.2f} vs control {np.median(nulls[key]):.2f} dB; "
              f"KS p={ks.pvalue:.3g}")

    # 4. STA/LTA main night
    srows = []
    for s in A.IMOS_SITES:
        for p, f in main_[s]:
            t0, fs, pr, rec = A.read_pressure(p, s, 500.0, full=True)
            for b in ("8-16", "10-20"):
                tr, r = A.sta_lta(pr, fs, *A.BANDS[b])
                from obspy.signal.trigger import trigger_onset
                for on, off in trigger_onset(r, 3.0, 1.5):
                    if tr[on] < 35:  # LTA warm-up
                        continue
                    srows.append(dict(site=s, file=p.stem, band=b, t_on=A.fmt(t0 + tr[on], 1),
                                      t_off=A.fmt(t0 + tr[min(off, r.size - 1)], 1),
                                      max_ratio=float(r[on:off + 1].max())))
    pd.DataFrame(srows).to_csv(OUT / "stalta_20140308.csv", index=False, float_format="%.2f")

    # figures
    far_figure(far)
    arc_pvalue_figure(ta)
    key_spectrograms(main_, tc)


def far_figure(far):
    fig, axs = plt.subplots(1, 3, figsize=(13, 4), sharey=True)
    for ax, s in zip(axs, A.IMOS_SITES):
        for kind, ls in (("any", "-"), ("5-40Hz,>=5s", "--")):
            x = far[(far.site == s) & (far.kind == kind)]
            for night, g in x.groupby("night"):
                main = night == A.MAIN_DAY.isoformat()
                ax.semilogy(g.thr_db, g.per_hour.clip(lower=0.05), ls, color="r" if main else "0.6",
                            lw=2 if main else 0.8, label=f"{'8 Mar' if main else 'control'} {kind}"
                            if (main or night == A.CONTROL_DAYS[0].isoformat()) else None)
        ax.set_xlabel("event threshold (dB over 120-s running median)")
        ax.set_title(f"{s}: detected events per recorded hour", fontsize=9)
        ax.legend(fontsize=7)
    axs[0].set_ylabel("events / hour")
    fig.tight_layout()
    fig.savefig(OUT / "fig_far.png", dpi=130)
    plt.close(fig)


def arc_pvalue_figure(ta):
    fig, axs = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for s, col in zip(A.IMOS_SITES, ("k", "tab:green", "tab:purple")):
        x = ta[ta.site == s].copy()
        x["lat"] = [float(t.split("_")[1]) for t in x.test]
        axs[0].plot(x.coverage, x.lat, "o-", color=col, ms=3, label=s)
        y = x[x.coverage > 0]
        axs[1].plot(np.minimum(y.pm8, y.plf), y.lat, "o", color=col, ms=4, label=s)
    axs[0].set_xlabel("fraction of predicted arrival window recorded")
    axs[1].set_xlabel("min p, arrival-like statistics (5-40 & 5-20 Hz) vs control nights")
    axs[1].set_xscale("log")
    axs[1].axvline(0.05, color="r", ls=":")
    axs[0].set_ylabel("7th-arc latitude")
    for ax in axs:
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.suptitle("7th-arc impact 00:19:30-00:25, c 1.47-1.49 km/s: IMOS coverage and window test", fontsize=10)
    fig.tight_layout()
    fig.savefig(OUT / "fig_arc_pvalues.png", dpi=130)
    plt.close(fig)


def key_spectrograms(main_, tc):
    specs = [("PAPCA", 0, 50, "Kadri 306.18 / Stead 246.9 windows (and other HA01 picks)"),
             ("PAPCA", 0, 35, "northern-arc impact windows; Kadri 303.28 pick"),
             ("PAKIM", 1, 0, "Kadri 306.18 at PAKIM; southern/central arc"),
             ("PAKIM", 1, 30, "Curtin/Carlsberg vs Java 01:15 T-phase"),
             ("PAKIM", 0, 45, "northern-arc impacts at PAKIM"),
             ("PAPOR", 1, 15, "Stead 246.9 at PAPOR")]
    for s, h, m, ttl in specs:
        w = [x for x in A.recording_windows(s, A.hms8(h, m) + 30, A.hms8(h, m) + 60, full=True)]
        if not w:
            continue
        a, b, p = w[0]
        sel = tc[(tc.site == s) & (tc.coverage > 0)]
        marks = []
        for _, r in sel.iterrows():
            t1, t2 = A.parse_hms8(r.t1), A.parse_hms8(r.t2)
            if t2 >= a and t1 <= b and (t2 - t1) < 200 and ("|arc" in r.test or "|T" in r.test or "|obs" in r.test):
                marks.append((r.test.replace("|", " "), t1, t2))
        spec_figure(s, p, marks, f"fig_spec_{s}_{h:02d}{m:02d}.png",
                    f"{s} {A.fmt(a, 1)}-{A.fmt(b, 1)} UTC 8 Mar 2014: {ttl}. Shaded: predicted windows")


if __name__ == "__main__":
    main()
