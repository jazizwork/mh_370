"""Candidate (5): Anderson's 01:15:18 event at 8.36S 107.92E, tested with open seismometers.

1. Automatic P (Z, 2-8 Hz, AIC) and S (horizontal, 1-6 Hz, AIC) picks, for the 01:15 event
   and for the USGS-catalogued M4.1 at 23:52:18.6 (-9.6744, 108.4193, 34 km) as master.
2. Absolute grid-search location (ak135 P/S tables) and master-event relative location
   (station terms cancel), with origin time solved analytically (mean residual).
3. Amplitude-ratio local magnitude vs the M4.1 (Wood-Anderson-simulated horizontals,
   Hutton & Boore 1987 distance term) at common stations; S/P amplitude ratio (source type).
4. Radiated-energy comparison with a 777 impact and predicted T-phase arrivals at XMIS,
   COCO, PAKIM, HA01, HA08S; measured T-band envelope at XMIS/XMI.

Outputs: outputs/acoustic/seismic/java_picks.csv, java_summary.csv, fig_java_event.png
"""
from __future__ import annotations

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from obspy.geodetics import locations2degrees
from obspy.signal.trigger import aic_simple

from mh370 import acoustic as A
from mh370 import acoustic_seismic as S

OUT = A.ROOT / "outputs" / "acoustic" / "seismic"
CLAIM = dict(lat=-8.36, lon=107.92, depth=10.0, t0=A.hms8(1, 15, 18))
MASTER = dict(lat=-9.6744, lon=108.4193, depth=34.05, t0=A.geo.hms(23, 52, 18.6), mag=4.1)
STAS = ["CISI", "UGM", "SMRI", "XMIS", "XMI", "JAGI", "GIRL", "COCO"]
WA_PAZ = {"poles": [-6.283 + 4.712j, -6.283 - 4.712j], "zeros": [0j, 0j], "gain": 1.0,
          "sensitivity": 2080.0}

# travel-time tables (ak135) for fast grid search
DEG = np.arange(0.0, 20.01, 0.02)
_TT = {}


def tt_table(depth):
    if depth not in _TT:
        P, Sx = [], []
        for d in DEG:
            arr = S.taup().get_travel_times(depth, max(d, 0.001), ["P", "p", "Pn", "Pg", "S", "s", "Sn", "Sg"])
            P.append(min([a.time for a in arr if a.name.upper().startswith("P")], default=np.nan))
            Sx.append(min([a.time for a in arr if a.name.upper().startswith("S")], default=np.nan))
        _TT[depth] = (np.array(P), np.array(Sx))
    return _TT[depth]


def tt(depth, deg, phase):
    P, Sx = tt_table(depth)
    return np.interp(deg, DEG, P if phase == "P" else Sx)


def aic_pick(tr, tpred, half=15.0, f=(2.0, 8.0), tmin=None):
    x = tr.copy()
    x.filter("bandpass", freqmin=f[0], freqmax=min(f[1], 0.45 * x.stats.sampling_rate),
             corners=4, zerophase=False)  # causal filter for onsets
    x.trim(S.ut(tpred - half - 20), S.ut(tpred + half + 5))
    t = S.tp(x.stats.starttime) + np.arange(x.stats.npts) / x.stats.sampling_rate
    lo = tpred - half if tmin is None else max(tpred - half, tmin)
    m = (t >= lo) & (t <= tpred + half)
    a = aic_simple(x.data[m])
    k = int(np.argmin(a[2:-2])) + 2
    pick = t[m][k]
    pre = x.data[(t >= pick - 10) & (t < pick - 0.5)]
    post = x.data[(t >= pick) & (t < pick + 3)]
    snr = 20 * np.log10(np.abs(post).max() / (np.std(pre) * 3 + 1e-30)) if pre.size and post.size else np.nan
    return pick, snr


def picks_for(ev):
    rows = []
    for s in STAS:
        sla, slo = S.coords(s)
        deg = locations2degrees(ev["lat"], ev["lon"], sla, slo)
        tp_ = ev["t0"] + tt(ev["depth"], deg, "P")
        ts_ = ev["t0"] + tt(ev["depth"], deg, "S")
        z = S.load(s)
        pP, sP = aic_pick(z, tp_, half=12.0)
        # S on the horizontal with larger S-window energy
        best = None
        for c in ("E", "N", "1", "2"):
            h = S.load(s, comp=c)
            if h is None:
                continue
            ps, ss = aic_pick(h, ts_, half=15.0, f=(1.0, 6.0),
                              tmin=pP + 0.7 * (ts_ - tp_))  # S search starts after P
            if best is None or ss > best[1]:
                best = (ps, ss)
        rows.append(dict(station=s, deg=deg, pred_P=tp_, pick_P=pP, snr_P=sP,
                         pred_S=ts_, pick_S=best[0] if best else np.nan,
                         snr_S=best[1] if best else np.nan))
    return rows


def grid_locate(picks, depth, lat_rng, lon_rng, step=0.02, use_S=True, min_snr=6.0,
                master=None):
    """Grid search; if master=(mrows, mev), residuals use differential times
    (t_ev - t_master)_obs - (T_ev(x) - T_master(master_loc)) per station/phase."""
    lats = np.arange(lat_rng[0], lat_rng[1] + 1e-9, step)
    lons = np.arange(lon_rng[0], lon_rng[1] + 1e-9, step)
    obs = []
    for r in picks:
        for ph in ("P", "S") if use_S else ("P",):
            if r[f"snr_{ph}"] < min_snr:
                continue
            sla, slo = S.coords(r["station"])
            o = r[f"pick_{ph}"]
            corr = 0.0
            if master is not None:
                mrows, mev = master
                mr = [m for m in mrows if m["station"] == r["station"]][0]
                if mr[f"snr_{ph}"] < min_snr:
                    continue
                mdeg = locations2degrees(mev["lat"], mev["lon"], sla, slo)
                # station/path term from the master: observed - predicted
                corr = (mr[f"pick_{ph}"] - mev["t0"]) - tt(mev["depth"], mdeg, ph)
            obs.append((sla, slo, ph, o - corr))
    LA, LO = np.meshgrid(lats, lons, indexing="ij")
    res = np.zeros(LA.shape + (len(obs),))
    for k, (sla, slo, ph, o) in enumerate(obs):
        deg = locations2degrees(LA, LO, sla, slo)
        res[..., k] = o - tt(depth, deg, ph)
    t0 = res.mean(-1)
    rms = np.sqrt(((res - t0[..., None]) ** 2).mean(-1))
    i, j = np.unravel_index(np.argmin(rms), rms.shape)
    return dict(lat=lats[i], lon=lons[j], t0=t0[i, j], rms=rms[i, j], n=len(obs),
                grid=(lats, lons, rms), resid=res[i, j] - t0[i, j], obs=obs)


def wa_peak(s, ev, ts_pred):
    amps = []
    for c in ("E", "N", "1", "2"):
        h = S.load(s, comp=c, output="DISP")
        if h is None:
            continue
        h.simulate(paz_simulate=WA_PAZ, water_level=60)
        h.filter("bandpass", freqmin=0.5, freqmax=min(8.0, 0.45 * h.stats.sampling_rate))
        x = h.slice(S.ut(ts_pred - 5), S.ut(ts_pred + 40)).data
        amps.append(np.abs(x).max())
    return np.mean(amps) * 1e3 if amps else np.nan  # mm (WA)


def zpeak(s, t0, t1, f=(2.0, 8.0)):
    z = S.load(s)
    z.filter("bandpass", freqmin=f[0], freqmax=f[1], corners=4, zerophase=True)
    return np.abs(z.slice(S.ut(t0), S.ut(t1)).data).max()


def main():
    pj = picks_for(CLAIM)
    pm = picks_for(MASTER)
    with open(OUT / "java_picks.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event", "station", "dist_deg", "pred_P", "pick_P", "P_resid_s", "snr_P_db",
                    "pred_S", "pick_S", "S_resid_s", "snr_S_db"])
        for name, rows in (("01:15 event (pred. from claimed loc/time)", pj),
                           ("M4.1 23:52 (pred. from USGS)", pm)):
            for r in rows:
                w.writerow([name, r["station"], round(r["deg"], 3), A.fmt(r["pred_P"], 1),
                            A.fmt(r["pick_P"], 2), round(r["pick_P"] - r["pred_P"], 2),
                            round(r["snr_P"], 1), A.fmt(r["pred_S"], 1), A.fmt(r["pick_S"], 2),
                            round(r["pick_S"] - r["pred_S"], 2), round(r["snr_S"], 1)])
    for r in pj:
        print(f"{r['station']:5s} P {A.fmt(r['pick_P'],2)} (res {r['pick_P']-r['pred_P']:+.1f}, snr {r['snr_P']:.0f})"
              f"  S {A.fmt(r['pick_S'],2)} (res {r['pick_S']-r['pred_S']:+.1f}, snr {r['snr_S']:.0f})")

    # locations
    summ = []
    rng_lat, rng_lon = (-10.5, -6.6), (106.0, 110.0)
    for depth in (10.0, 20.0, 35.0):
        a = grid_locate(pj, depth, rng_lat, rng_lon)
        m = grid_locate(pj, depth, rng_lat, rng_lon, master=(pm, MASTER))
        mm = grid_locate(pm, MASTER["depth"], (-11.0, -8.0), (107.0, 110.0))  # master check
        for lab, L in (("absolute", a), ("master-relative", m)):
            d_claim = float(A.dist_az(CLAIM["lat"], CLAIM["lon"], L["lat"], L["lon"])[0])
            summ.append(dict(method=lab, depth_km=depth, lat=round(L["lat"], 3), lon=round(L["lon"], 3),
                             origin=A.fmt(L["t0"], 1), rms_s=round(L["rms"], 2), n_obs=L["n"],
                             km_from_claim=round(d_claim, 1),
                             origin_minus_claim_s=round(L["t0"] - CLAIM["t0"], 1)))
        print(f"depth {depth}: abs {a['lat']:.2f},{a['lon']:.2f} {A.fmt(a['t0'],1)} rms {a['rms']:.2f}"
              f" | rel {m['lat']:.2f},{m['lon']:.2f} {A.fmt(m['t0'],1)} rms {m['rms']:.2f}"
              f" | master self-loc {mm['lat']:.2f},{mm['lon']:.2f} {A.fmt(mm['t0'],1)} rms {mm['rms']:.2f}")
    best_rel = min([x for x in summ if x["method"] == "master-relative"], key=lambda x: x["rms_s"])
    # fit at the claimed location: residual rms with origin time free
    obs = grid_locate(pj, 10.0, (CLAIM["lat"], CLAIM["lat"]), (CLAIM["lon"], CLAIM["lon"]), step=1.0)
    print("claimed loc fit: origin", A.fmt(obs["t0"], 1), "rms", round(obs["rms"], 2))

    # magnitude by amplitude ratio (common stations), WA horizontal peak in S window
    mag_rows = []
    for rj, rm in zip(pj, pm):
        s = rj["station"]
        sla, slo = S.coords(s)
        rj_km = float(A.dist_az(best_rel["lat"], best_rel["lon"], sla, slo)[0])
        rm_km = float(A.dist_az(MASTER["lat"], MASTER["lon"], sla, slo)[0])
        hj = np.hypot(rj_km, best_rel["depth_km"])
        hm = np.hypot(rm_km, MASTER["depth"])
        aj = wa_peak(s, CLAIM, rj["pred_S"])
        am = wa_peak(s, MASTER, rm["pred_S"])
        dM = np.log10(aj / am) + 1.11 * np.log10(hj / hm) + 0.00189 * (hj - hm)
        # S/P ratio on Z (2-8 Hz)
        spj = zpeak(s, rj["pred_S"] - 3, rj["pred_S"] + 30) / zpeak(s, rj["pred_P"] - 3, rj["pred_S"] - 5)
        spm = zpeak(s, rm["pred_S"] - 3, rm["pred_S"] + 30) / zpeak(s, rm["pred_P"] - 3, rm["pred_S"] - 5)
        mag_rows.append(dict(station=s, r_event_km=round(hj), r_master_km=round(hm),
                             WA_event_mm=aj, WA_master_mm=am, dM=round(dM, 2),
                             M_est=round(MASTER["mag"] + dM, 2), SP_event=round(spj, 2),
                             SP_master=round(spm, 2)))
    good = [r for r in mag_rows if 0.6 < r["r_event_km"] / r["r_master_km"] < 1.6]
    Ms = np.array([r["M_est"] for r in good])
    M = float(np.median(Ms))
    E = 10 ** (1.5 * M + 4.8)
    print("magnitude per station:", [(r["station"], r["M_est"]) for r in mag_rows])
    print(f"median M (similar-distance stations) {M:.2f} +/- {Ms.std():.2f}; E={E:.2e} J")
    with open(OUT / "java_magnitude.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(mag_rows[0]))
        w.writeheader()
        for r in mag_rows:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in r.items()})

    # predicted T arrivals for claimed and relocated source
    tpred = []
    for lab, la, lo, t0 in (("claimed", CLAIM["lat"], CLAIM["lon"], CLAIM["t0"]),
                            ("relocated", best_rel["lat"], best_rel["lon"],
                             CLAIM["t0"] + best_rel["origin_minus_claim_s"])):
        for rcv in ("XMIS", "COCO", "PAKIM", "PAPCA", "HA01", "HA08S"):
            if rcv in A.RECEIVERS:
                rla, rlo = A.RECEIVERS[rcv]["lat"], A.RECEIVERS[rcv]["lon"]
            else:
                rla, rlo = S.coords(rcv)
            d = float(A.dist_az(la, lo, rla, rlo)[0])
            tpred.append((lab, rcv, round(d), A.fmt(t0 + d / 1.50), A.fmt(t0 + d / 1.48),
                          A.fmt(t0 + d / 1.47)))
    # observed T-band energy at XMIS / XMI after the S coda
    tobs = {}
    for s in ("XMIS", "XMI", "COCO"):
        z = S.load(s)
        t, e = S.band_env(z, 2.0, 8.0, win_s=5.0, step_s=1.0)
        sla, slo = S.coords(s)
        d = float(A.dist_az(best_rel["lat"], best_rel["lon"], sla, slo)[0])
        w0, w1 = CLAIM["t0"] + d / 1.50 - 30, CLAIM["t0"] + d / 1.46 + 90
        snr, tm = S.window_stat(t, e, w0, w1, noise=(-900, -120), ref=CLAIM["t0"])
        tobs[s] = (round(snr, 1), A.fmt(tm, 0), round(tm - (CLAIM["t0"] + d / 1.48), 0))
    print("T-band obs:", tobs)

    with open(OUT / "java_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["section", "k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9"])
        for r in summ:
            w.writerow(["location", *r.values()])
        w.writerow(["location_claim_fit", "origin_free", A.fmt(obs["t0"], 1), "rms_s", round(obs["rms"], 2)])
        w.writerow(["magnitude", "median_M", round(M, 2), "std", round(float(Ms.std()), 2),
                    "E_J", f"{E:.2e}", "E_over_4GJ", round(E / 4e9, 1)])
        for row in tpred:
            w.writerow(["T_pred", *row])
        for s, v in tobs.items():
            w.writerow(["T_obs_2-8Hz", s, *v])

    # figure: record section for both events + location panel
    fig = plt.figure(figsize=(14, 8))
    for col, (ev, lab) in enumerate(((CLAIM, "01:15 event (claimed 8.36S 107.92E 01:15:18)"),
                                     (MASTER, "USGS M4.1 23:52:18.6 (-9.67, 108.42)"))):
        ax = fig.add_subplot(1, 3, col + 1)
        rows = sorted(((float(A.dist_az(ev["lat"], ev["lon"], *S.coords(s))[0]), s) for s in STAS))
        for i, (d, s) in enumerate(rows):
            z = S.load(s)
            z.filter("bandpass", freqmin=2, freqmax=8, corners=4, zerophase=True)
            tt_ = S.tp(z.stats.starttime) + np.arange(z.stats.npts) / z.stats.sampling_rate
            m = (tt_ >= ev["t0"] - 30) & (tt_ <= ev["t0"] + 420)
            y = z.data[m] / np.percentile(np.abs(z.data[m]), 99.9)
            ax.plot(tt_[m] - ev["t0"], i + 0.45 * y, lw=0.35, color="k")
            sla, slo = S.coords(s)
            deg = locations2degrees(ev["lat"], ev["lon"], sla, slo)
            for ph, c in (("P", "tab:blue"), ("S", "tab:green")):
                tq = tt(ev["depth"], deg, ph)
                ax.plot([tq, tq], [i - .45, i + .45], color=c, lw=1)
            ax.fill_betweenx([i - .45, i + .45], d / 1.50, d / 1.46, color="tab:orange", alpha=0.35)
            ax.text(415, i + 0.1, f"{s}\n{d:.0f} km", fontsize=7, ha="right")
        ax.set_xlim(-30, 420)
        ax.set_yticks([])
        ax.set_xlabel("s after origin")
        ax.set_title(lab + "\nZ 2-8 Hz; blue P, green S (ak135), orange T 1.50-1.46 km/s", fontsize=8)
    ax = fig.add_subplot(1, 3, 3)
    lats, lons, rms = grid_locate(pj, best_rel["depth_km"], rng_lat, rng_lon, master=(pm, MASTER))["grid"]
    cs = ax.contourf(lons, lats, rms, levels=np.arange(0, 6.1, 0.5), cmap="viridis_r", extend="max")
    plt.colorbar(cs, ax=ax, label="rms residual (s), master-relative")
    bz = A.bathy()
    li = (bz[0] >= -11) & (bz[0] <= -6.5)
    lj = (bz[1] >= 105.5) & (bz[1] <= 110.5)
    ax.contour(bz[1][lj], bz[0][li], bz[2][np.ix_(li, lj)], levels=[0], colors="k", linewidths=0.8)
    ax.contour(bz[1][lj], bz[0][li], bz[2][np.ix_(li, lj)], levels=[-4000, -2000, -1000], colors="grey",
               linewidths=0.4)
    ax.plot(CLAIM["lon"], CLAIM["lat"], "r*", ms=12, label="Anderson claim")
    ax.plot(best_rel["lon"], best_rel["lat"], "wo", mec="k", label="master-relative (this work)")
    ax.plot(MASTER["lon"], MASTER["lat"], "ks", label="USGS M4.1 (master)")
    for s in ("CISI", "UGM", "SMRI"):
        ax.plot(*S.coords(s)[::-1], "k^", ms=6)
        ax.text(*S.coords(s)[::-1], s, fontsize=7)
    try:  # 7th arc
        al = np.arange(-11, -6.4, 0.05)
        alon = [A.geo.arc_lon_for_lat(x, A.geo.ARC7_BTO_US, A.geo.ARC7_TIME, 0.0) for x in al]
        ax.plot(alon, al, "m-", lw=1, label="7th arc (sea level)")
    except Exception:  # noqa: BLE001
        pass
    ax.set_xlim(105.5, 110.5)
    ax.set_ylim(-11, -6.5)
    ax.legend(fontsize=7, loc="lower left")
    ax.set_title(f"M~{M:.1f} (amplitude ratio vs M4.1); E~{E:.1e} J = {E / 4e9:.0f}x a 4 GJ impact", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_java_event.png", dpi=130)


if __name__ == "__main__":
    main()
