"""Workstream D: empirical calibration of the IMOS recorders with catalogued earthquakes.

For USGS events (Dec 2013 - May 2014, all directions; plus 28 Nov 2013 and Jun - Nov 2014 for the
box 65S-5S, 55-125E, i.e. west/south-west of the WA recorders) whose predicted T-phase (or P) arrival falls inside an
IMOS recording window, fetch that one file, and measure the band-level excess in the predicted
window vs a null distribution of the same statistic (control-night files, same site).
Gives (1) a timing check of the logger clock (P arrivals, sharp T onsets) and
(2) an empirical T-phase detectability vs magnitude and distance for PAPCA / PAKIM / PAPOR.

Selection (a priori): T: depth <= 70 km, M >= 4.0, d <= 4000 km (PAPOR 3000 km), predicted window
[t0 + d/1.50 - 15 s, t0 + d/1.46 + 30 s] inside [file start + 20 s, file start + 300 s].
P: M >= 5.5 (or M >= 5.0 within 2500 km), any depth, 1-95 deg, P (ak135) in [start + 20, start + 290].

Outputs: outputs/acoustic/imos_calibration_events.csv, fig_imos_detectability.png,
         fig_imos_calibration_examples.png
Run: .venv/bin/python -I scripts/acoustic_imos_calibration.py
"""
from __future__ import annotations

import datetime as dt
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"
BASE = "https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic"
CATS = [A.ROOT / "data" / "raw" / "usgs_catalog_acoustic" / f for f in
        ("usgs_201311_m4.csv", "usgs_201312_201406_m4.csv", "usgs_201406_201411_WSW_m4.csv")]
T_WIN = (1.50, 1.46, -15.0, 30.0)


def fetch(site, name):
    dep = A.RECEIVERS[site]["dep"]
    tn = dt.datetime.fromtimestamp(int(name, 16), dt.timezone.utc).replace(tzinfo=None)
    for day in (tn.date(), (tn + dt.timedelta(days=1)).date(), (tn - dt.timedelta(days=1)).date()):
        dest = A.RAW / site / dep / f"{day:%Y%m%d}" / "raw" / f"{name}.DAT"
        if dest.exists() and dest.stat().st_size > 3_000_000:
            return dest
    for day in (tn.date(), (tn + dt.timedelta(days=1)).date(), (tn - dt.timedelta(days=1)).date()):
        url = f"{BASE}/{site}/{dep}/{day:%Y%m%d}/raw/{name}.DAT"
        dest = A.RAW / site / dep / f"{day:%Y%m%d}" / "raw" / f"{name}.DAT"
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                data = r.read()
        except Exception:  # noqa: BLE001
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return dest
    print("missing", site, name, file=sys.stderr)
    return None


def update_manifest(items):
    import hashlib
    man = A.RAW / "manifest.csv"
    lines = man.read_text().splitlines()
    have = {ln.split(",")[3] for ln in lines[1:]}
    add = []
    for site, p in items:
        key = "IMOS/ANMN/Acoustic/" + str(p.relative_to(A.RAW))
        if key not in have:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
            add.append(f"{site},{A.RECEIVERS[site]['dep']},calibration-event,{key},{p.stat().st_size},{h}")
    man.write_text("\n".join(lines + sorted(add)) + "\n")


def select_events():
    from obspy.taup import TauPyModel
    model = TauPyModel("ak135")
    cat = pd.concat([pd.read_csv(c) for c in CATS], ignore_index=True).drop_duplicates("id")
    cat = cat.reset_index(drop=True)
    cat["t0"] = [A.t_of(pd.Timestamp(x).tz_localize(None).to_pydatetime()) for x in cat.time]
    rows = []
    for s in A.IMOS_SITES:
        tw, names = A.deployment_windows(s)
        tw = np.asarray(tw)
        d, baz = A.rdist_az(s, cat.latitude.values, cat.longitude.values)
        for i, ev in cat.iterrows():
            dd = float(d[i])
            # T phase
            if ev.depth <= 70 and ev.mag >= 4.0 and dd <= (3000 if s == "PAPOR" else 4000):
                a = ev.t0 + dd / T_WIN[0] + T_WIN[2]
                b = ev.t0 + dd / T_WIN[1] + T_WIN[3]
                k = np.searchsorted(tw, a) - 1
                if k >= 0 and a >= tw[k] + 20 and b <= tw[k] + 300:
                    rows.append(dict(site=s, phase="T", id=ev.id, time=ev.time[:19], lat=ev.latitude,
                                     lon=ev.longitude, depth=ev.depth, mag=ev.mag, d_km=dd,
                                     baz=float(baz[i]), t0=ev.t0, w1=a, w2=b, t_pred=ev.t0 + dd / 1.48,
                                     file=names[k], place=ev.place))
            # P phase
            if ev.mag >= 5.5 or (ev.mag >= 5.0 and dd <= 2500):
                deg = dd / 111.195
                if 1.0 <= deg <= 95:
                    arr = model.get_travel_times(max(ev.depth, 0.0), deg, ["P", "p", "Pn"])
                    if arr:
                        tp = ev.t0 + min(x.time for x in arr)
                        k = np.searchsorted(tw, tp) - 1
                        if k >= 0 and tp >= tw[k] + 20 and tp <= tw[k] + 290:
                            rows.append(dict(site=s, phase="P", id=ev.id, time=ev.time[:19],
                                             lat=ev.latitude, lon=ev.longitude, depth=ev.depth,
                                             mag=ev.mag, d_km=dd, baz=float(baz[i]), t0=ev.t0,
                                             w1=tp - 5, w2=tp + 15, t_pred=tp, file=names[k],
                                             place=ev.place))
    return pd.DataFrame(rows)


def _feat(args):
    site, path = args
    try:
        return A.file_features(path, site)
    except Exception as e:  # noqa: BLE001
        print("feat fail", path, e, file=sys.stderr)
        return None


def main():
    ev = select_events()
    print(ev.groupby(["site", "phase"]).size())
    need = sorted(set(zip(ev.site, ev.file)))
    print("files needed", len(need), flush=True)
    with ThreadPoolExecutor(8) as ex:
        paths = list(ex.map(lambda sn: fetch(*sn), need))
    pmap = {sn: p for sn, p in zip(need, paths)}
    update_manifest([(s, p) for (s, n), p in pmap.items() if p is not None])
    with ProcessPoolExecutor(8) as ex:
        feats = list(ex.map(_feat, [(s, p) for (s, n), p in pmap.items() if p is not None]))
    fmap = {}
    for ((s, n), p), f in zip([(k, v) for k, v in pmap.items() if v is not None], feats):
        fmap[(s, n)] = f
    # null distributions from control nights (same site), per window width, smoothing 0 and 10 s
    ctrl = {}
    for s in A.IMOS_SITES:
        fl = [p for d in A.CONTROL_DAYS for p in A.night_files(s, d)]
        with ProcessPoolExecutor(8) as ex:
            ctrl[s] = [f for f in ex.map(_feat, [(s, p) for p in fl]) if f is not None]
        print(s, "control files", len(ctrl[s]), flush=True)
    nulls = {}
    out = []
    for _, r in ev.iterrows():
        f = fmap.get((r.site, r.file))
        if f is None:
            continue
        a, b = A.file_window(pmap[(r.site, r.file)], full=True)
        res = dict(r)
        res["file_t0"] = a
        width = round(r.w2 - r.w1)
        for sm, lab in ((0.0, "s0"), (10.0, "s10"), (-8.0, "sm8")):
            key = (r.site, width, sm)
            if key not in nulls:
                nulls[key] = A.null_window_stats(ctrl[r.site], width, smooth_s=sm, step_s=10.0)
            st, band, tm = A.window_stat(f, r.w1, r.w2, smooth_s=sm)
            res[f"stat_{lab}"] = st
            res[f"band_{lab}"] = band
            res[f"tpeak_{lab}"] = tm
            res[f"p_{lab}"] = A.pvalue(st, nulls[key])
        # low-frequency arrival-like statistic (T-phase band, 8-s running median), window
        # extended to +60 s after d/1.46 because T-phase energy peaks late (emergent arrivals)
        wl2 = r.w2 + 30.0
        widthl = round(wl2 - r.w1)
        keyl = (r.site, widthl, "lf")
        if keyl not in nulls:
            nulls[keyl] = A.null_window_stats(ctrl[r.site], widthl, bands=A.LF_BANDS, smooth_s=-8.0, step_s=10.0)
        st, band, tm = A.window_stat(f, r.w1, wl2, bands=A.LF_BANDS, smooth_s=-8.0)
        res["stat_lf"], res["band_lf"], res["tpeak_lf"] = st, band, tm
        res["p_lf"] = A.pvalue(st, nulls[keyl])
        res["tpeak_lf_minus_pred_s"] = tm - r.t_pred if np.isfinite(tm) else np.nan
        b = A.blockage_summary(r.lat, r.lon, r.site)
        res["path_max_elev_m"] = b["max_elev_m"]
        res["path_km_above1000"] = b["km_above_axis"]
        res["open_path"] = b["max_elev_m"] < -1000
        # onset pick (first crossing of +6 dB in the best band, 2-s levels) for timing check
        if res["band_s0"]:
            E = A.excess_series(f, res["band_s0"])
            m = (f["t"] >= r.w1 - 30) & (f["t"] <= r.w2)
            idx = np.where(m & (E > 6.0))[0]
            res["t_onset"] = float(f["t"][idx[0]]) if idx.size else np.nan
            res["onset_minus_pred_s"] = res["t_onset"] - r.t_pred if idx.size else np.nan
        out.append(res)
    df = pd.DataFrame(out)
    df["time_pred"] = [A.dt_of(t).strftime("%Y-%m-%d %H:%M:%S") for t in df.t_pred]
    df.to_csv(OUT / "imos_calibration_events.csv", index=False, float_format="%.3f")
    summarize(df)
    plots(df, fmap, pmap)


def detected(x):
    """Detection rule: LF arrival-like statistic p < 0.01, or 5-40 Hz arrival-like p < 0.01.
    (The 5-40 Hz-only rule of the first pass missed visually obvious PAKIM T-phases because the
    20-40 Hz whale-song bands dominate PAKIM's null distribution; see README.)"""
    return (x.p_lf < 0.01) | (x.p_sm8 < 0.01)


def summarize(df):
    det = df[(df.phase == "T")]
    rows = []
    for s in A.IMOS_SITES:
        d = det[det.site == s]
        if d.empty:
            continue
        print(f"\n{s}: T windows {len(d)}; detected: {detected(d).sum()} "
              f"(open water path: {detected(d[d.open_path]).sum()}/{d.open_path.sum()})")
        for op in (True, False):
            for lo, hi in ((0, 1000), (1000, 2000), (2000, 3000), (3000, 4000)):
                for m1, m2 in ((4.0, 4.5), (4.5, 5.0), (5.0, 9)):
                    x = d[(d.d_km >= lo) & (d.d_km < hi) & (d.mag >= m1) & (d.mag < m2) & (d.open_path == op)]
                    if len(x):
                        k = int(detected(x).sum())
                        rows.append(dict(site=s, open_path=op, d_lo=lo, d_hi=hi, m_lo=m1, m_hi=m2, n=len(x),
                                         n_detected=k))
                        print(f"   open={op} d {lo}-{hi} km M{m1}-{m2}: {k}/{len(x)} detected")
    pd.DataFrame(rows).to_csv(OUT / "imos_detectability_table.csv", index=False)
    p = df[df.phase == "P"]
    print("\nP windows:", len(p), "detected:", detected(p).sum(), "p_s0<0.01:", (p.p_s0 < 0.01).sum())
    print(det[detected(det)][["site", "time", "mag", "d_km", "depth", "baz", "path_max_elev_m", "stat_lf",
                              "p_lf", "stat_sm8", "p_sm8", "tpeak_lf_minus_pred_s", "place"]].to_string())


def plots(df, fmap, pmap):
    t = df[df.phase == "T"]
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
    for ax, s in zip(axs, A.IMOS_SITES):
        d = t[t.site == s]
        det = detected(d)
        op = d.open_path
        ax.scatter(d.d_km[~det & op], d.mag[~det & op], s=16, facecolors="none", edgecolors="k",
                   label="not detected, open path")
        ax.scatter(d.d_km[~det & ~op], d.mag[~det & ~op], s=10, marker="x", c="0.6",
                   label="not detected, blocked path")
        ax.scatter(d.d_km[det], d.mag[det], s=22, c="tab:red", label="detected")
        ax.set_title(f"{s}: catalogued earthquakes with T-phase\nwindow inside a recording", fontsize=9)
        ax.set_xlabel("distance (km)")
        ax.axhspan(2.1, 3.2, color="tab:blue", alpha=0.15, label="777 impact equiv. M2.1-3.2 (Kadri)")
        ax.set_ylim(2.0, 6.6)
        ax.legend(fontsize=7, loc="upper left")
    axs[0].set_ylabel("magnitude (USGS)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_imos_detectability.png", dpi=130)
    plt.close(fig)

    # examples: strongest detections per site with spectrogram and predicted window
    ex = df[(df.phase == "T") & detected(df)].sort_values("stat_sm8", ascending=False)
    ex = pd.concat([ex[ex.site == s].head(2) for s in A.IMOS_SITES])
    if ex.empty:
        return
    fig, axs = plt.subplots(len(ex), 1, figsize=(11, 2.6 * len(ex)))
    axs = np.atleast_1d(axs)
    for ax, (_, r) in zip(axs, ex.iterrows()):
        t0, fs, p, rec = A.read_pressure(pmap[(r.site, r.file)], r.site, 250.0, full=True)
        f, tt, S = A.spectrogram_db(p, fs, nperseg=256)
        ax.pcolormesh((t0 + tt - r.t_pred), f, S, shading="auto", cmap="viridis",
                      vmin=np.percentile(S, 5), vmax=np.percentile(S, 99.5))
        ax.axvline(0, color="r", ls="--", lw=1)
        ax.axvspan(r.w1 - r.t_pred, r.w2 - r.t_pred, color="w", alpha=0.15)
        ax.set_ylim(3, 100)
        ax.set_ylabel("Hz")
        ax.set_title(f"{r.site} {r.phase} | {r.time} M{r.mag} {r.place} | d={r.d_km:.0f} km | "
                     f"Sm8 {r.stat_sm8:.1f} dB p={r.p_sm8:.3f} | onset-pred {r.get('onset_minus_pred_s', np.nan):.1f} s",
                     fontsize=7)
    axs[-1].set_xlabel("s relative to predicted arrival (T: d/1.48 km/s; P: ak135)")
    fig.tight_layout()
    fig.savefig(OUT / "fig_imos_calibration_examples.png", dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
