"""Candidate (1)-(3) and generic 7th-arc impacts vs open island/coastal seismometers.

Hypotheses
  * generic: impact on the sea-level 7th arc at 20-42 S (0.5 deg) between 00:19:30 and
    00:25:00 UTC -> T window [00:19:30 + d/1.50 - 30 s, 00:25:00 + d/1.46 + 60 s];
  * Stead247: HA01 bearing 246.9 deg arc crossing, impact 00:19-00:25 (AIS is ~470 km away);
  * Kadri306: HA01 bearing 306.18 deg arc crossing, (i) impact 00:19:30-00:25 and
    (ii) the origin implied by the HA01 00:54:30 pick for that crossing (~00:36:3x);
  * Kadri268: HA01 268.24 deg crossing, origin implied by 00:39:02.
Stations with control nights: COCO, XMIS, AIS, NWAO, AUBUS, GIRL (Z, 2-8 Hz).
Statistic: max 5-s RMS in window / median RMS over [w0-900, w0-60] s (dB). Null: same
statistic at all window positions (step 10 s) in the 22:00-03:00 records of the three
control nights (2014-03-05, -10, -11) -> p-value. Path blockage from ETOPO 2022.

Outputs: outputs/acoustic/seismic/arc_windows.csv, arc_candidates.csv, fig_arc_windows.png
"""
from __future__ import annotations

import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from mh370 import acoustic as A
from mh370 import acoustic_seismic as S

OUT = A.ROOT / "outputs" / "acoustic" / "seismic"
STAS = ["COCO", "XMIS", "AIS", "NWAO", "AUBUS", "GIRL"]
CONTROLS = ["control_20140305", "control_20140310", "control_20140311"]
DAYSHIFT = {"control_20140305": -3 * 86400, "control_20140310": 2 * 86400,
            "control_20140311": 3 * 86400}
T_IMP = (A.hms8(0, 19, 30), A.hms8(0, 25, 0))


def blockage_to(lat, lon, sta, exclude_src_km=30.0, exclude_rcv_km=60.0, axis_m=1000.0):
    sla, slo = S.coords(sta)
    s, la, lo, z = A.path_profile(lat, lon, sla, slo)
    m = (s >= exclude_src_km) & (s <= s[-1] - exclude_rcv_km)
    zz = z[m]
    ds = np.gradient(s)[m]
    k = int(np.argmax(zz))
    return dict(max_elev_m=float(zz[k]), at=(round(float(la[m][k]), 2), round(float(lo[m][k]), 2)),
                km_above_axis=float(ds[zz > -axis_m].sum()), km_land=float(ds[zz > 0].sum()))


def known_arrivals(sta):
    """(t_start, t_end, label) of P..S+150 s for catalogued events of the night and the
    uncatalogued 01:15 Java event (located in acoustic_seismic_java.py)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cal", A.ROOT / "scripts" / "acoustic_seismic_calibration.py")
    cal = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cal)
    evs = list(cal.EVENTS) + [("Java_0115_uncatalogued", A.hms8(1, 15, 21), -8.25, 107.88, 15.0, 4.1, "")]
    sla, slo = S.coords(sta)
    out = []
    for name, t0, la, lo, dep, mag, _ in evs:
        tP, tS, _ = S.ps_times(la, lo, dep, sla, slo)
        if np.isfinite(tP):
            out.append((t0 + tP - 5, t0 + (tS if np.isfinite(tS) else tP) + 150, name))
    return out


def explain(sta, tm, cache={}):
    if sta not in cache:
        cache[sta] = known_arrivals(sta)
    return ";".join(lab for a, b, lab in cache[sta] if a <= tm <= b) if np.isfinite(tm) else ""


def env_for(night, sta):
    tr = S.load(sta, night=night)
    t, e = S.band_env(tr, 2.0, 8.0, win_s=5.0, step_s=1.0)
    return t - DAYSHIFT.get(night, 0.0), e  # controls mapped onto the 8-March clock


def main():
    lats, lons = A.arc7_points(-42.0, -20.0, 0.5)
    envs = {(n, s): env_for(n, s) for s in STAS for n in ["night_20140308"] + CONTROLS}
    nulls = {}
    rows = []
    for s in STAS:
        sla, slo = S.coords(s)
        for la, lo in zip(lats, lons):
            d = float(A.dist_az(la, lo, sla, slo)[0])
            w0, w1 = T_IMP[0] + d / 1.50 - 30, T_IMP[1] + d / 1.46 + 60
            wl = round((w1 - w0) / 10) * 10
            if (s, wl) not in nulls:
                vals = []
                for n in CONTROLS:
                    t, e = envs[(n, s)]
                    vals.append(S.null_distribution(t, e, wl, noise=(-900, -60), step=10.0))
                nulls[(s, wl)] = np.concatenate(vals)
            t, e = envs[("night_20140308", s)]
            snr, tm = S.window_stat(t, e, w0, w1, noise=(-900, -60))
            ctrl = []
            for n in CONTROLS:
                tc, ec = envs[(n, s)]
                ctrl.append(S.window_stat(tc, ec, w0, w1, noise=(-900, -60))[0])
            blk = blockage_to(la, lo, s)
            rows.append(dict(station=s, arc_lat=la, arc_lon=round(lo, 2), dist_km=round(d),
                             w0=A.fmt(w0), w1=A.fmt(w1), snr_db=round(snr, 1),
                             t_max=A.fmt(tm) if np.isfinite(tm) else "",
                             p_null=round(float((nulls[(s, wl)] >= snr).mean()), 3),
                             explained_by=explain(s, tm),
                             ctrl_same_window_db="/".join(f"{c:.1f}" for c in ctrl),
                             path_max_elev_m=round(blk["max_elev_m"]),
                             path_km_above_1000m=round(blk["km_above_axis"]),
                             path_km_land=round(blk["km_land"])))
    with open(OUT / "arc_windows.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    sig = [r for r in rows if r["p_null"] < 0.05]
    print(f"{len(rows)} station-arc windows; p<0.01: {sum(r['p_null'] < 0.01 for r in rows)}; "
          f"p<0.05: {len(sig)}; p<0.05 unexplained: {sum(1 for r in sig if not r['explained_by'])}")
    for r in sig:
        print("  ", r)

    # specific HA01 candidates
    cand = []
    specs = []
    for key in ("Stead247", "Kadri306", "Kadri268"):
        c = A.HA01_CANDIDATES[key]
        rng, la, lo = S.arc_crossing("HA01", c["az"])
        t_origin = c["t"] - rng / A.C_SOFAR
        specs.append((key, la, lo, rng, t_origin))
    for key, la, lo, rng, t_origin in specs:
        for s in ("AIS", "COCO", "XMIS", "AUBUS", "GIRL", "NWAO"):
            sla, slo = S.coords(s)
            d = float(A.dist_az(la, lo, sla, slo)[0])
            blk = blockage_to(la, lo, s)
            hyps = [("impact 00:19:30-00:25", T_IMP[0], T_IMP[1])]
            if key in ("Kadri306", "Kadri268"):
                hyps.append(("origin implied by HA01 pick (c 1.47-1.49)",
                             A.HA01_CANDIDATES[key]["t"] - rng / 1.47,
                             A.HA01_CANDIDATES[key]["t"] - rng / 1.49))
            for lab, a, b in hyps:
                a, b = min(a, b), max(a, b)
                w0, w1 = a + d / 1.50 - 30, b + d / 1.46 + 60
                t, e = envs[("night_20140308", s)]
                snr, tm = S.window_stat(t, e, w0, w1, noise=(-900, -60))
                wl = round((w1 - w0) / 10) * 10
                if (s, wl) not in nulls:
                    nulls[(s, wl)] = np.concatenate([S.null_distribution(*envs[(n, s)], wl, noise=(-900, -60))
                                                     for n in CONTROLS])
                cand.append(dict(candidate=key, arc_lat=round(la, 2), arc_lon=round(lo, 2),
                                 ha01_range_km=round(rng), origin_c148=A.fmt(t_origin), hypothesis=lab,
                                 station=s, dist_km=round(d), w0=A.fmt(w0), w1=A.fmt(w1),
                                 snr_db=round(snr, 1), t_max=A.fmt(tm) if np.isfinite(tm) else "",
                                 p_null=round(float((nulls[(s, wl)] >= snr).mean()), 3),
                                 explained_by=explain(s, tm),
                                 path_max_elev_m=round(blk["max_elev_m"]), path_max_at=blk["at"],
                                 path_km_above_1000m=round(blk["km_above_axis"])))
    with open(OUT / "arc_candidates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cand[0]))
        w.writeheader()
        w.writerows(cand)
    for r in cand:
        print({k: r[k] for k in ("candidate", "hypothesis", "station", "dist_km", "w0", "w1",
                                 "snr_db", "t_max", "p_null", "explained_by", "path_max_elev_m")})

    # figure: envelopes (main vs controls) with arc windows
    fig, axs = plt.subplots(len(STAS), 1, figsize=(12, 2.0 * len(STAS)), sharex=True)
    cmap = plt.get_cmap("viridis")
    for ax, s in zip(axs, STAS):
        for n in CONTROLS:
            t, e = envs[(n, s)]
            m = (t >= A.hms8(0, 15)) & (t <= A.hms8(1, 15))
            ax.plot((t[m] - A.hms8(0)) / 60, 20 * np.log10(e[m] / np.median(e[m])), color="0.7", lw=0.5)
        t, e = envs[("night_20140308", s)]
        m = (t >= A.hms8(0, 15)) & (t <= A.hms8(1, 15))
        ax.plot((t[m] - A.hms8(0)) / 60, 20 * np.log10(e[m] / np.median(e[m])), color="k", lw=0.7)
        sla, slo = S.coords(s)
        for la, lo in zip(lats, lons):
            d = float(A.dist_az(la, lo, sla, slo)[0])
            a, b = (T_IMP[0] + d / 1.48 - A.hms8(0)) / 60, (T_IMP[1] + d / 1.48 - A.hms8(0)) / 60
            ax.plot([a, b], [-6 + (la + 42) / 22 * 4] * 2, color=cmap((la + 42) / 22), lw=2)
        for key, la, lo, rng, t_origin in specs:
            d = float(A.dist_az(la, lo, sla, slo)[0])
            col = {"Stead247": "tab:red", "Kadri306": "tab:orange", "Kadri268": "tab:purple"}[key]
            ax.axvspan((T_IMP[0] + d / 1.49 - A.hms8(0)) / 60, (T_IMP[1] + d / 1.47 - A.hms8(0)) / 60,
                       color=col, alpha=0.15)
            if key != "Stead247":
                tt = A.HA01_CANDIDATES[key]["t"] - rng / 1.48 + d / 1.48
                ax.axvline((tt - A.hms8(0)) / 60, color=col, ls="--", lw=1)
        ax.set_ylim(-7, 25)
        ax.set_ylabel(f"{s}\ndB")
    axs[-1].set_xlabel("minutes after 2014-03-08 00:00 UTC")
    axs[0].set_title("Z 2-8 Hz 5-s RMS envelope (dB re median): 8 Mar (black) vs 3 control nights (grey). "
                     "Bars: arc 20-42S T windows (c=1.48, impact 00:19:30-00:25; colour=lat, yellow=north);\n"
                     "shading: impact windows at Stead247 (red), Kadri306 (orange), Kadri268 (purple) crossings; "
                     "dashed: origin implied by HA01 pick", fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_arc_windows.png", dpi=130)


if __name__ == "__main__":
    main()
