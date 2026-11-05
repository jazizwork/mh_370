"""Extended T-phase detectability calibration for island/coastal seismometers.

Uses USGS-catalogued shallow (<=40 km) earthquakes 2014-02-01 -> 2014-05-01 with oceanic
epicentres (ETOPO 2022 seafloor deeper than 1500 m) within 3500 km of COCO, XMIS, AIS,
GIRL, DGAR, RODM and AUBUS (cap 45 events per station spread over distance). Raw counts
are used (SNR is a ratio, so response removal is unnecessary).

For each pair: T-window [d/1.50 - 30 s, d/1.46 + 60 s] after origin (start clipped to
S + 20 s); statistic = max 5-s RMS (2-8 Hz) / median RMS over [P-600, P-60] s, in dB.
Control statistic: same window length placed to end 60 s before P, with its own preceding
noise reference -> empirical false-alarm rate of any SNR threshold.

Outputs: data/raw/fdsn_seismic/calib_ext/*.mseed (cached), outputs/acoustic/seismic/
         tphase_detectability.csv, fig_tphase_detectability.png
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from obspy import UTCDateTime, read
from obspy.clients.fdsn import Client

from mh370 import acoustic as A
from mh370 import acoustic_seismic as S

RAWD = S.SEIS / "calib_ext"
OUT = A.ROOT / "outputs" / "acoustic" / "seismic"
CAT = S.SEIS / "catalog_usgs_201402_201404_region.csv"
STA = {  # sta: (net, loc, cha, server, lat, lon)
    "COCO": ("II", "10", "BHZ", "https://service.earthscope.org"),
    "XMIS": ("AU", "", "BHZ", "https://service.earthscope.org"),
    "GIRL": ("AU", "", "BHZ", "https://service.earthscope.org"),
    "DGAR": ("II", "10", "BHZ", "https://service.earthscope.org"),
    "AIS": ("G", "00", "BHZ", "https://ws.resif.fr"),
    "RODM": ("G", "00", "BHZ", "https://ws.resif.fr"),
    "AUBUS": ("S1", "", "HHZ", "http://auspass.edu.au:8080"),
}
MAXKM, CAP = 3500.0, 45
# AUBUS (school station, Busselton) has frequent glitches: control FAR 0.42 at 9 dB, i.e.
# no skill; it is excluded from the pooled fit (kept in the per-station CSV summary).
EXCLUDE_AUBUS = False


def pairs():
    d = pd.read_csv(CAT)
    d["t0"] = [S.tp(UTCDateTime(x)) for x in d.time]
    d = d[d.depth <= 40].copy()
    d["seafloor"] = A.depth_at(d.latitude.values, d.longitude.values)
    d = d[d.seafloor < -1500]
    out = []
    rng = np.random.default_rng(0)
    for s in STA:
        sla, slo = S.coords(s)
        dist = A.dist_az(sla, slo, d.latitude.values, d.longitude.values)[0]
        sel = d[(dist < MAXKM) & (dist > 100)].copy()
        sel["dist"] = dist[(dist < MAXKM) & (dist > 100)]
        if len(sel) > CAP:  # spread over distance: stratified sample in 8 bins
            bins = np.linspace(100, MAXKM, 9)
            keep = []
            for a, b in zip(bins[:-1], bins[1:]):
                g = sel[(sel.dist >= a) & (sel.dist < b)]
                k = min(len(g), int(np.ceil(CAP / 8)))
                keep += list(g.sort_values("mag", ascending=False).index[:k // 2]) + \
                    list(rng.choice(g.index, size=min(len(g), k - k // 2), replace=False)) if len(g) else []
            sel = sel.loc[sorted(set(keep))]
        for _, r in sel.iterrows():
            out.append((s, r.id, r.t0, r.latitude, r.longitude, r.depth, r.mag, r.dist, r.place))
    return out


def fetch(prs):
    RAWD.mkdir(parents=True, exist_ok=True)
    by = {}
    for p in prs:
        by.setdefault(p[0], []).append(p)
    for s, lst in by.items():
        net, loc, cha, url = STA[s]
        todo = []
        for (s_, eid, t0, la, lo, dep, mag, dist, place) in lst:
            f = RAWD / f"{eid}_{s}.mseed"
            if f.exists():
                continue
            a = S.ut(t0) - 900
            b = S.ut(t0) + dist / 1.46 + 240
            todo.append((net, s, loc, cha, a, b, f))
        if not todo:
            continue
        c = Client(url, timeout=300)
        for i in range(0, len(todo), 15):
            chunk = todo[i:i + 15]
            try:
                st = c.get_waveforms_bulk([t[:6] for t in chunk])
            except Exception as e:  # noqa: BLE001
                print(s, "bulk failed", type(e).__name__, str(e)[:80])
                continue
            for t in chunk:
                sub = st.slice(t[4], t[5])
                if len(sub):
                    sub.write(str(t[6]), format="MSEED")
            print(s, f"{i + len(chunk)}/{len(todo)}", flush=True)


def stat(t, e, w0, w1, nref):
    m = (t >= w0) & (t <= w1)
    n = (t >= nref[0]) & (t <= nref[1])
    if m.sum() < 5 or n.sum() < 20:
        return np.nan
    return 20 * np.log10(e[m].max() / np.median(e[n]))


def measure(prs):
    rows = []
    for (s, eid, t0, la, lo, dep, mag, dist, place) in prs:
        f = RAWD / f"{eid}_{s}.mseed"
        if not f.exists():
            continue
        st = read(str(f))
        st.merge(method=1, fill_value=0)
        tr = st[0]
        tr.detrend("demean")
        if tr.stats.sampling_rate < 16:
            continue
        sla, slo = S.coords(s)
        tP, tS, deg = S.ps_times(la, lo, dep, sla, slo)
        t, e = S.band_env(tr, 2.0, 8.0, win_s=5.0, step_s=1.0)
        w0, w1 = S.t_window(dist, t0)
        if np.isfinite(tS):
            w0 = max(w0, t0 + tS + 20)
        wl = w1 - w0
        if wl < 20:
            continue
        nref = (t0 + tP - 600, t0 + tP - 60)
        snr = stat(t, e, w0, w1, nref)
        # control: same length, ending 60 s before P; reference = [P-600, start-0]
        c1 = t0 + tP - 60
        c0 = c1 - min(wl, 250)
        ctrl = stat(t, e, c0, c1, (t0 + tP - 900, c0))
        zero_frac = float((tr.data == 0).mean())
        rows.append(dict(station=s, event=eid, origin=S.ut(t0).isoformat(), lat=la, lon=lo,
                         depth_km=dep, mag=mag, dist_km=round(dist), place=place,
                         snr_T_db=round(snr, 2), snr_ctrl_db=round(ctrl, 2),
                         zero_frac=round(zero_frac, 3)))
    return pd.DataFrame(rows)


def main():
    prs = pairs()
    print(len(prs), "pairs")
    fetch(prs)
    df = measure(prs)
    df = df[(df.zero_frac < 0.05) & np.isfinite(df.snr_T_db) & np.isfinite(df.snr_ctrl_db)]
    df = df[df.station != "AUBUS"] if EXCLUDE_AUBUS else df
    df.to_csv(OUT / "tphase_detectability.csv", index=False)
    thr = 9.0
    lines = []
    for s, g in df.groupby("station"):
        far = (g.snr_ctrl_db >= thr).mean()
        det = g.snr_T_db >= thr
        lines.append((s, len(g), far, det.mean()))
        print(f"{s}: n={len(g)} FAR(ctrl>={thr}dB)={far:.2f} det_frac={det.mean():.2f}")
    # pooled logistic fit P(det) ~ a + b*M + c*log10(d) on 'excess' detections
    import scipy.optimize as so
    g = df[df.station != "AUBUS"]
    y = (g.snr_T_db >= thr).astype(float).values
    X = np.c_[np.ones(len(g)), g.mag.values, np.log10(g.dist_km.values)]
    far0 = float((g.snr_ctrl_db >= thr).mean())  # false-alarm floor

    def nll(b):
        p = far0 + (1 - far0) / (1 + np.exp(-(X @ b)))
        p = np.clip(p, 1e-9, 1 - 1e-9)
        return -np.sum(y * np.log(p) + (1 - y) * np.log(1 - p))

    b = so.minimize(nll, np.array([-10.0, 3.0, -2.0]), method="Nelder-Mead",
                    options=dict(maxiter=20000, xatol=1e-6, fatol=1e-9)).x
    # bootstrap for the M50 at the arc-relevant distances
    rng = np.random.default_rng(2)
    boots = []
    for _ in range(300):
        ii = rng.integers(0, len(y), len(y))
        yy, XX = y[ii], X[ii]

        def nll_b(bb):
            p = far0 + (1 - far0) / (1 + np.exp(-(XX @ bb)))
            p = np.clip(p, 1e-9, 1 - 1e-9)
            return -np.sum(yy * np.log(p) + (1 - yy) * np.log(1 - p))
        boots.append(so.minimize(nll_b, b, method="Nelder-Mead").x)
    boots = np.array(boots)
    pred_rows = []
    for dk in (300, 500, 1000, 1500, 2000, 3000):
        m50 = -(b[0] + b[2] * np.log10(dk)) / b[1]
        bb = -(boots[:, 0] + boots[:, 2] * np.log10(dk)) / boots[:, 1]
        p32 = 1 / (1 + np.exp(-(b[0] + b[1] * 3.2 + b[2] * np.log10(dk))))
        p25 = 1 / (1 + np.exp(-(b[0] + b[1] * 2.5 + b[2] * np.log10(dk))))
        pred_rows.append((dk, round(m50, 2), round(np.percentile(bb, 5), 2),
                          round(np.percentile(bb, 95), 2), f"{p32:.3g}", f"{p25:.3g}"))
        print(f"d={dk} km: M50={m50:.2f} [{np.percentile(bb,5):.2f},{np.percentile(bb,95):.2f}]"
              f"  P_signal(M3.2)={p32:.3g} P_signal(M2.5)={p25:.3g}")
    with open(OUT / "tphase_detectability_fit.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["threshold_db", "a", "b_mag", "c_log10dist", "n", "pooled_ctrl_FAR"])
        w.writerow([thr, *np.round(b, 3), len(g), round(far0, 3)])
        w.writerow([])
        w.writerow(["dist_km", "M50_true_detection", "M50_p5", "M50_p95",
                    "P_true_det_M3.2", "P_true_det_M2.5"])
        w.writerows(pred_rows)
        w.writerow([])
        w.writerow(["station", "n", "ctrl_FAR", "T_det_frac"])
        for ln in lines:
            w.writerow([ln[0], ln[1], round(ln[2], 3), round(ln[3], 3)])
    print("logistic (a, b_M, c_logd):", b)

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
    ax = axs[0]
    for s, gg in df.groupby("station"):
        ax.scatter(gg.dist_km, gg.mag + 0.02 * np.random.default_rng(1).standard_normal(len(gg)),
                   c=np.clip(gg.snr_T_db, 0, 25), cmap="viridis", vmin=0, vmax=25, s=18,
                   marker={"COCO": "o", "XMIS": "s", "AIS": "^", "GIRL": "v", "DGAR": "D",
                           "RODM": "P", "AUBUS": "X"}[s], label=s, edgecolors="none")
    dd = np.linspace(200, 3500, 50)
    for p in (0.1, 0.5, 0.9):
        mm = (np.log(p / (1 - p)) - b[0] - b[2] * np.log10(dd)) / b[1]  # signal-detection prob.
        ax.plot(dd, mm, "k--" if p == 0.5 else "k:", lw=1)
    ax.axhspan(2.1, 3.2, color="tab:red", alpha=0.12)
    ax.text(250, 2.2, "777 impact 'M-equivalent' (Kadri: 2.1-3.2,\n100% energy conversion upper bound)",
            fontsize=7, color="tab:red")
    ax.set_xlabel("epicentral distance (km)")
    ax.set_ylabel("USGS magnitude")
    ax.set_ylim(1.8, 6)
    ax.legend(fontsize=7, ncol=2)
    ax.set_title(f"T-window SNR (2-8 Hz, colour, dB); lines: P(true det.)=0.1/0.5/0.9 (logistic, FAR floor {far0:.2f})",
                 fontsize=8)
    ax = axs[1]
    bins = np.arange(-2, 30, 1)
    ax.hist(df.snr_ctrl_db.dropna(), bins, alpha=0.6, label="control (pre-P) windows")
    ax.hist(df.snr_T_db.dropna(), bins, alpha=0.6, label="predicted T windows")
    ax.axvline(thr, color="k", ls="--")
    ax.set_xlabel("window statistic (dB re pre-event median)")
    ax.legend(fontsize=8)
    ax.set_title("All stations pooled", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_tphase_detectability.png", dpi=130)


if __name__ == "__main__":
    main()
