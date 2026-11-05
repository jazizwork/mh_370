"""Workstream D: absolute clock check of the IMOS loggers with deep-focus earthquake P waves.

Intermediate/deep earthquakes (depth >= 70 km) radiate impulsive, high-frequency P waves that
couple into the water under the hydrophone. For USGS events (Dec 2013 - May 2014, M >= 4.3,
<= 3000 km) whose ak135 P arrival falls inside a recording window, we fetch that file and stack
the 5-20 Hz envelope (0.5-s RMS, 0.1-s step, dB over the file median) aligned on the predicted
P time. A correct UTC clock gives a stack peak at ~0 to +2 s (envelope peaks lag onsets);
the file-name time convention would give ~-15 s, and a local-time clock +/- hours.

Outputs: outputs/acoustic/timing_check_events.csv, timing_check_stack.csv,
         fig_timing_check.png
Run: .venv/bin/python -I scripts/acoustic_timing_check.py
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"
CAT = A.ROOT / "data" / "raw" / "usgs_catalog_acoustic" / "usgs_201312_201406_m4.csv"
LAGS = np.arange(-60.0, 90.0 + 1e-9, 0.1)


def select(site, dmax=3000.0):
    from obspy.taup import TauPyModel
    m = TauPyModel("ak135")
    cat = pd.read_csv(CAT)
    cat["t0"] = [A.t_of(pd.Timestamp(x).tz_localize(None).to_pydatetime()) for x in cat.time]
    tw, names = A.deployment_windows(site)
    tw = np.asarray(tw)
    d, _ = A.rdist_az(site, cat.latitude.values, cat.longitude.values)
    rows = []
    for i, e in cat.iterrows():
        dd = float(d[i])
        if e.depth >= 70 and e.mag >= 4.3 and dd <= dmax:
            arr = m.get_travel_times(e.depth, dd / 111.195, ["P", "p"])
            if not arr:
                continue
            tp = e.t0 + min(a.time for a in arr)
            k = np.searchsorted(tw, tp) - 1
            if k >= 0 and tw[k] + 65 <= tp <= tw[k] + 215:  # full -60..+90 s lag range inside file
                rows.append(dict(site=site, id=e.id, time=e.time[:19], lat=e.latitude, lon=e.longitude,
                                 depth=e.depth, mag=e.mag, d_km=dd, t_p=tp, file=names[k]))
    return pd.DataFrame(rows)


def envelope(args):
    site, path, tp = args
    t0, fs, p, rec = A.read_pressure(path, site, 500.0, full=True)
    y = A.bandpass(p, fs, 5.0, 20.0) ** 2
    w = int(0.5 * fs)
    c = np.r_[0, np.cumsum(y)]
    tc = t0 + (np.arange(y.size - w + 1) + w / 2) / fs
    e = (c[w:] - c[:-w]) / w
    e = 10 * np.log10(np.maximum(e, 1e-30))
    e -= np.median(e)
    return np.interp(tp + LAGS, tc, e[:tc.size], left=np.nan, right=np.nan)


def main():
    ev = pd.concat([select("PAKIM"), select("PAPCA")], ignore_index=True)
    print(ev.groupby("site").size())
    with ThreadPoolExecutor(8) as ex:
        paths = list(ex.map(lambda r: A.fetch_raw(r[0], r[1], "timing-check"), zip(ev.site, ev.file)))
    ev["path"] = paths
    ev = ev[ev.path.notna()].reset_index(drop=True)
    with ProcessPoolExecutor(8) as ex:
        envs = np.array(list(ex.map(envelope, zip(ev.site, ev.path, ev.t_p))))
    # per-event measures
    k0 = (LAGS >= -10) & (LAGS <= 15)
    pre = (LAGS >= -60) & (LAGS <= -15)
    ev["peak_lag_s"] = [LAGS[k0][np.nanargmax(e[k0])] for e in envs]
    ev["peak_db_in_pwin"] = [np.nanmax(e[k0]) for e in envs]
    ev["pre_p95_db"] = [np.nanpercentile(e[pre], 95) for e in envs]
    ev["snr_db"] = ev.peak_db_in_pwin - ev.pre_p95_db
    onset = []
    for e in envs:
        thr = np.nanpercentile(e[pre], 95) + 3
        idx = np.where(k0 & (e > thr))[0]
        onset.append(LAGS[idx[0]] if idx.size else np.nan)
    ev["onset_lag_s"] = onset
    ev.drop(columns=["path"]).to_csv(OUT / "timing_check_events.csv", index=False, float_format="%.2f")

    rows = []
    fig, axs = plt.subplots(2, 2, figsize=(13, 8), gridspec_kw=dict(height_ratios=[1, 1.4]))
    for j, s in enumerate(("PAKIM", "PAPCA")):
        m = (ev.site == s).values
        E = envs[m]
        if not len(E):
            continue
        stack = np.nanmean(E, axis=0)
        # bootstrap of the stack peak lag over the wide lag range (no prior window)
        rng = np.random.default_rng(1)
        bl = []
        for _ in range(500):
            ii = rng.integers(0, len(E), len(E))
            st = np.nanmean(E[ii], axis=0)
            bl.append(LAGS[np.nanargmax(st)])
        bl = np.array(bl)
        good = E[(ev[m].snr_db > 3).values]
        sg = np.nanmean(good, axis=0) if len(good) else np.full(LAGS.size, np.nan)
        rows.append(dict(site=s, n_events=len(E), stack_peak_lag_s=LAGS[np.nanargmax(stack)],
                         stack_peak_db=np.nanmax(stack), boot_lag_p05=np.percentile(bl, 5),
                         boot_lag_p50=np.percentile(bl, 50), boot_lag_p95=np.percentile(bl, 95),
                         n_snr_gt3=len(good), stack_snr3_peak_lag_s=LAGS[np.nanargmax(sg)] if len(good) else np.nan,
                         median_onset_lag_snr3=float(np.nanmedian(ev[m & (ev.snr_db > 3)].onset_lag_s))))
        axs[0, j].plot(LAGS, stack, "k", lw=1, label=f"all {len(E)} events")
        if len(good):
            axs[0, j].plot(LAGS, sg, "r", lw=1, label=f"{len(good)} with SNR>3 dB")
        axs[0, j].axvline(0, color="b", ls="--", lw=0.8, label="ak135 P (footer clock)")
        axs[0, j].axvline(-15.5, color="m", ls=":", lw=0.8, label="where P would be with file-name clock")
        axs[0, j].set_title(f"{s}: 5-20 Hz envelope stack on predicted P (deep events)", fontsize=9)
        axs[0, j].legend(fontsize=7)
        axs[0, j].set_xlabel("lag after predicted P (s)")
        axs[0, j].set_ylabel("dB over file median")
        order = np.argsort(ev[m].snr_db.values)[::-1]
        axs[1, j].imshow(E[order], aspect="auto", extent=[LAGS[0], LAGS[-1], len(E), 0], cmap="magma",
                         vmin=0, vmax=15)
        axs[1, j].axvline(0, color="c", lw=0.6)
        axs[1, j].set_xlabel("lag after predicted P (s)")
        axs[1, j].set_ylabel("events (sorted by SNR)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_timing_check.png", dpi=120)
    plt.close(fig)
    st = pd.DataFrame(rows)
    st.to_csv(OUT / "timing_check_stack.csv", index=False, float_format="%.2f")
    print(st.to_string())
    print(ev.sort_values("snr_db", ascending=False).head(15)[["site", "time", "mag", "depth", "d_km",
                                                               "snr_db", "onset_lag_s", "peak_lag_s"]].to_string())


if __name__ == "__main__" and "--step" not in __import__("sys").argv:
    main()


def step_fit(stack, lo=-60.0, hi=60.0):
    """Best two-level step time (s) for a lag series: min SSE of a (lag<tau) / b (lag>=tau)."""
    m = (LAGS >= lo) & (LAGS <= hi) & np.isfinite(stack)
    x, y = LAGS[m], stack[m]
    best = (np.inf, np.nan, np.nan)
    for tau in np.arange(-40.0, 40.01, 0.5):
        a, b = y[x < tau], y[x >= tau]
        sse = ((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()
        if sse < best[0]:
            best = (sse, tau, b.mean() - a.mean())
    return best[1], best[2]


def step_analysis():
    """Re-uses the cached envelopes by recomputing them (cheap) and fits the step onset."""
    ev = pd.read_csv(OUT / "timing_check_events.csv")
    ev["path"] = [A.fetch_raw(s, f, "timing-check") for s, f in zip(ev.site, ev.file)]
    with ProcessPoolExecutor(8) as ex:
        envs = np.array(list(ex.map(envelope, zip(ev.site, ev.path, ev.t_p))))
    rows = []
    rng = np.random.default_rng(2)
    for s in ("PAKIM", "PAPCA"):
        E = envs[(ev.site == s).values]
        tau, jump = step_fit(np.nanmean(E, axis=0))
        bt = []
        for _ in range(1000):
            ii = rng.integers(0, len(E), len(E))
            bt.append(step_fit(np.nanmean(E[ii], axis=0))[0])
        # null: same fit on envelopes with random circular lag shifts (destroys alignment)
        nt = []
        for _ in range(300):
            sh = np.array([np.roll(e, rng.integers(0, LAGS.size)) for e in E])
            nt.append(step_fit(np.nanmean(sh, axis=0))[1])
        rows.append(dict(site=s, n=len(E), step_tau_s=tau, step_jump_db=jump,
                         tau_p05=np.percentile(bt, 5), tau_p50=np.percentile(bt, 50),
                         tau_p95=np.percentile(bt, 95),
                         jump_null_p95=np.percentile(nt, 95),
                         p_jump=(1 + np.sum(np.array(nt) >= jump)) / (1 + len(nt))))
    st = pd.DataFrame(rows)
    st.to_csv(OUT / "timing_check_step.csv", index=False, float_format="%.3f")
    print(st.to_string())


if __name__ == "__main__" and "--step" in __import__("sys").argv:
    step_analysis()
