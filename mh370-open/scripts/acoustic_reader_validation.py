"""Workstream D step 1: validate the Python port of the CMST/AODN .DAT reader and calibration.

Checks
  1. Header/footer timing for every downloaded night file: first-sample time vs hex file
     name (Unix time) and vs t<dep>_start_times.mat; Finalised - First Data; sample counts;
     overload flags; 15-min cadence.
  2. Continuity at the nominal 300-s boundary (justifies using the ~7 s of extra samples).
  3. Calibration: our calibrated PSD for a sample of files vs CMST's independently processed
     long-term spectrogram (t<dep>_longterm_spectrogram.mat, 'Spectrum' in dB re 1 uPa^2/Hz).
  4. Noise floor percentiles per site / band for the main night vs control nights.

Outputs: outputs/acoustic/reader_validation_files.csv, reader_validation_psd.csv,
         noise_floor.csv, fig_reader_psd_vs_cmst.png, fig_noise_floor.png
Run: .venv/bin/python -I scripts/acoustic_reader_validation.py
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.io as sio
from scipy import signal

from mh370 import acoustic as A

OUT = A.ROOT / "outputs" / "acoustic"


def file_checks(args):
    site, night, p = args
    rec = A.read_dat(p, full=True)
    hexname = A.t_of(__import__("datetime").datetime.fromtimestamp(
        int(p.stem, 16), __import__("datetime").timezone.utc).replace(tzinfo=None))
    v = rec.volts
    n0 = int(rec.duration_s * rec.fs)
    # continuity: rms 1 s before vs 1 s after the 300-s boundary and the jump at the boundary
    w = int(rec.fs)
    rb = v[n0 - w:n0].std()
    ra = v[n0:n0 + w].std() if v.size >= n0 + w else np.nan
    dv = np.abs(np.diff(v[n0 - w:n0 + w]))
    jump = abs(v[n0] - v[n0 - 1]) / (np.median(dv) + 1e-12) if v.size > n0 else np.nan
    return dict(site=site, night=night, file=p.stem, t0=rec.t0, t0_str=A.fmt(rec.t0, 3),
                t0_minus_hex=rec.t0 - hexname, final_minus_t0=rec.t_final - rec.t0,
                n_nominal=n0, n_extra=rec.n_extra, dur_full_s=v.size / rec.fs,
                overload=rec.overload, schedule=rec.meta["schedule"],
                filt=rec.meta["filters"][0], validity=" ".join(rec.meta["validity"]),
                rms_before=rb, rms_after=ra, rms_ratio=ra / rb, boundary_jump_rel=jump,
                vmax=float(np.abs(v).max()))


def psd_check(args):
    site, p, freqs = args
    rec = A.read_dat(p, full=False)
    pr = A.to_pressure(rec.volts, rec.fs, site)
    f, P = signal.welch(pr, rec.fs, nperseg=int(rec.fs), noverlap=int(rec.fs) // 2)
    # average over 1-Hz bins within +/- 1/48 octave of each CMST frequency
    out_mean, out_med = [], []
    fw, Pw = signal.welch(pr, rec.fs, nperseg=int(rec.fs), noverlap=int(rec.fs) // 2, average="median")
    for fc in freqs:
        m = (f >= fc * 2 ** (-1 / 48)) & (f <= fc * 2 ** (1 / 48))
        if not m.any():
            m = np.argmin(np.abs(f - fc))
        out_mean.append(10 * np.log10(np.mean(P[m])))
        out_med.append(10 * np.log10(np.mean(Pw[m])))
    return p.stem, np.array(out_mean), np.array(out_med)


def main():
    jobs = []
    for s in A.IMOS_SITES:
        for d in [A.MAIN_DAY] + A.CONTROL_DAYS:
            for p in A.night_files(s, d):
                jobs.append((s, d.isoformat(), p))
    with ProcessPoolExecutor(8) as ex:
        rows = list(ex.map(file_checks, jobs, chunksize=4))
    df = pd.DataFrame(rows).sort_values(["site", "t0"])
    # cross-check against start_times.mat
    for s in A.IMOS_SITES:
        tw, names = A.deployment_windows(s)
        mp = dict(zip(names, tw))
        m = df.site == s
        df.loc[m, "t0_minus_start_times"] = [r.t0 - mp.get(r.file, np.nan) for r in df[m].itertuples()]
    df["cadence_s"] = df.groupby(["site", "night"]).t0.diff()
    df.to_csv(OUT / "reader_validation_files.csv", index=False, float_format="%.4f")
    print(df.groupby("site")[["t0_minus_hex", "final_minus_t0", "n_extra", "rms_ratio",
                              "boundary_jump_rel", "t0_minus_start_times", "cadence_s"]]
          .describe(percentiles=[0.01, 0.5, 0.99]).T.to_string())
    print("overloads:", int(df.overload.sum()), "validity strings:", df.validity.unique()[:5])
    print("filters:", df.filt.unique())

    # ---- calibration check vs CMST long-term spectrogram ----
    prow = []
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, s in zip(axs, ("PAPCA", "PAKIM")):
        dep = A.RECEIVERS[s]["dep"]
        m = sio.loadmat(A.RAW / s / dep / f"t{dep}_longterm_spectrogram.mat")
        fr = m["Frequency"].ravel()
        spec = m["Spectrum"]
        names = list(m["File_name"])
        files = A.night_files(s, A.MAIN_DAY)[::3] + A.night_files(s, A.CONTROL_DAYS[0])[::5]
        keep = fr <= 2800
        with ProcessPoolExecutor(8) as ex:
            res = list(ex.map(psd_check, [(s, p, fr[keep]) for p in files]))
        diffs_mean, diffs_med = [], []
        for stem, pm, pmed in res:
            if stem not in names:
                continue
            ref = spec[keep, names.index(stem)]
            diffs_mean.append(pm - ref)
            diffs_med.append(pmed - ref)
            for fc, a, b, r in zip(fr[keep], pm, pmed, ref):
                prow.append(dict(site=s, file=stem, f_hz=fc, ours_mean=a, ours_median=b, cmst=r))
        dm = np.array(diffs_mean)
        dd = np.array(diffs_med)
        ax.semilogx(fr[keep], np.median(dm, 0), label="ours (Welch mean) - CMST")
        ax.fill_between(fr[keep], np.percentile(dm, 10, 0), np.percentile(dm, 90, 0), alpha=0.2)
        ax.semilogx(fr[keep], np.median(dd, 0), label="ours (Welch median) - CMST")
        ax.axhline(0, color="k", lw=0.5)
        ax.set_ylim(-6, 6)
        ax.set_xlabel("Hz")
        ax.set_ylabel("dB")
        ax.set_title(f"{s}: calibrated PSD, our port minus CMST long-term spectrogram\n"
                     f"({len(dm)} files; band = 10-90th pct)", fontsize=9)
        ax.legend(fontsize=8)
        b = (fr[keep] >= 8) & (fr[keep] <= 100)
        print(f"{s}: ours(mean)-CMST in 8-100 Hz: median {np.median(dm[:, b]):+.2f} dB, "
              f"IQR {np.percentile(dm[:, b], 25):+.2f}..{np.percentile(dm[:, b], 75):+.2f}; "
              f"ours(median)-CMST: {np.median(dd[:, b]):+.2f} dB")
    fig.tight_layout()
    fig.savefig(OUT / "fig_reader_psd_vs_cmst.png", dpi=130)
    plt.close(fig)
    pd.DataFrame(prow).to_csv(OUT / "reader_validation_psd.csv", index=False, float_format="%.2f")

    # ---- noise floor per band, main night vs controls (22:00-03:00) ----
    nrows = []
    for s in A.IMOS_SITES:
        for d in [A.MAIN_DAY] + A.CONTROL_DAYS:
            fl = A.night_files(s, d)
            with ProcessPoolExecutor(8) as ex:
                feats = list(ex.map(_feat, [(s, p) for p in fl]))
            for b in A.ALL_BANDS:
                L = np.concatenate([f[f"L_{b}"] for f in feats])
                nrows.append(dict(site=s, night=d.isoformat(), main=d == A.MAIN_DAY, band=b,
                                  p10=np.percentile(L, 10), p50=np.percentile(L, 50),
                                  p90=np.percentile(L, 90), p99=np.percentile(L, 99)))
    nf = pd.DataFrame(nrows)
    nf.to_csv(OUT / "noise_floor.csv", index=False, float_format="%.2f")
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), sharey=True)
    for ax, s in zip(axs, A.IMOS_SITES):
        x = nf[nf.site == s]
        for night, g in x.groupby("night"):
            main = night == A.MAIN_DAY.isoformat()
            ax.plot(range(len(A.ALL_BANDS)), g.set_index("band").loc[list(A.ALL_BANDS), "p50"],
                    "-o" if main else "-", color="r" if main else "0.6", lw=2 if main else 0.8,
                    label="8 Mar (median)" if main else None)
        ax.set_xticks(range(len(A.ALL_BANDS)), A.ALL_BANDS, rotation=45)
        ax.set_title(f"{s}: median 2-s band level, 22:00-03:00\nred = 7/8 Mar night, grey = 8 control nights",
                     fontsize=9)
        ax.legend(fontsize=8)
    axs[0].set_ylabel("dB re 1 uPa")
    fig.tight_layout()
    fig.savefig(OUT / "fig_noise_floor.png", dpi=130)
    plt.close(fig)
    print(nf[nf.band.isin(["8-16", "10-20", "20-40"])].pivot_table(index=["site", "band"], columns="main",
                                                                    values="p50", aggfunc="median").round(1))


def _feat(args):
    return A.file_features(args[1], args[0])


if __name__ == "__main__":
    main()
