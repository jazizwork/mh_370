"""Combine per-mode SMC samples into the satcom end-point posterior on the common grid.

Inputs : data/derived/satcom_smc/<variant>_<mode>.npz  (scripts/satcom_run_paths.py)
Outputs: data/derived/satcom_posterior.nc, outputs/satcom/arc_profile.csv,
         outputs/satcom/summary.json, outputs/satcom/*.png
Run    : .venv/bin/python -I scripts/satcom_posterior.py
"""
import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree

from mh370 import geo, grid
from mh370 import satcom_paths as sp

ROOT = pathlib.Path(__file__).resolve().parents[1]
SMC = ROOT / "data" / "derived" / "satcom_smc"
OUT = ROOT / "outputs" / "satcom"
NC = ROOT / "data" / "derived" / "satcom_posterior.nc"
NM = 1852.0
MODES = sp.MODES
MODE_NAMES = {"LNAV": "LNAV great circle", "CTT": "constant true track",
              "CMT": "constant magnetic track", "CTH": "constant true heading",
              "CMH": "constant magnetic heading"}
# categorical slots 1-5 of the reference palette (fixed order, follows the mode)
COL = {"LNAV": "#2a78d6", "CTT": "#eb6834", "CMT": "#1baf7a", "CTH": "#eda100", "CMH": "#e87ba4"}
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"

# ------------------------------------------------------------------ end-of-flight model
EOF_DEFAULT_W_GLIDE = 0.2           # default mixture weight of the piloted-glide scenario
UNC_ALONG_NM, UNC_SIGMA_NM = 5.0, 7.0  # uncontrolled descent: mean along-track offset, 2-D sd
GLIDE_MAX_NM, GLIDE_DIR_SD = 120.0, 15.0
K_DRAWS = 25                         # displacement draws per posterior particle

COMPARE = [  # label, lat, lon, kind
    ("UGIB 2020 LEP", -34.2342, 93.7875, "satcom+fuel+drift"),
    ("Ashton et al. 2015 example", -34.7, 93.0, "satcom example"),
    ("IG Jun 2014", -36.0167, 88.5667, "satcom"),
    ("Godfrey v15.1 2015", -37.105, 89.871, "satcom"),
    ("Hardy 2015 (188 deg mag)", -38.082, 87.400, "satcom"),
    ("CSIRO 2017 drift", -35.6, 92.8, "drift"),
    ("Godfrey WSPR 2024", -29.128, 99.934, "WSPR (disputed)"),
]


def load_variant(variant):
    out = {}
    for m in MODES:
        f = SMC / f"{variant}_{m}.npz"
        if f.exists():
            out[m] = dict(np.load(f, allow_pickle=False))
    return out


def end_state(z):
    i = int(np.argmin(np.abs(z["t_meas"] - geo.ARC7_TIME)))
    vn, ve = z["vn"][:, i], z["ve"][:, i]
    return (z["lat"][:, i], z["lon"][:, i], np.mod(np.degrees(np.arctan2(ve, vn)), 360),
            np.hypot(vn, ve) / sp.KT)


def mode_weights(res, how="evidence"):
    lz = np.array([float(res[m]["logz"]) for m in res])
    if how == "equal":
        w = np.ones_like(lz)
    else:
        w = np.exp(lz - lz.max())
    return dict(zip(res, w / w.sum()))


# ------------------------------------------------------------------ arc projection
_ARC = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-50.0, -5.0, 0.005))
_ARC_XYZ = geo.llh_to_ecef(_ARC[:, 0], _ARC[:, 1], 0.0)
_ARC_TREE = cKDTree(_ARC_XYZ)


def arc_project(lat, lon):
    """(arc latitude of nearest 7th-arc point, signed distance km; + = beyond arc / farther
    from the sub-satellite point)."""
    xyz = geo.llh_to_ecef(np.asarray(lat), np.asarray(lon), 0.0)
    d, j = _ARC_TREE.query(xyz)
    s = np.sign(geo.predicted_bto(lat, lon, 0.0, geo.ARC7_TIME) - geo.ARC7_BTO_US)
    return _ARC[j, 0], s * d


def sample_eof(lat, lon, trk, w, scenario, rng, k=K_DRAWS):
    """Displace 00:19:29 positions to impact positions. Returns lat, lon, weights."""
    n = lat.size
    lat = np.repeat(lat, k); lon = np.repeat(lon, k); trk = np.repeat(trk, k)
    w = np.repeat(w, k) / k
    if scenario == "uncontrolled":
        # mean UNC_ALONG_NM along final track + isotropic Gaussian scatter (sd per axis)
        dx = UNC_ALONG_NM * np.sin(np.radians(trk)) + rng.normal(0, UNC_SIGMA_NM, n * k)
        dy = UNC_ALONG_NM * np.cos(np.radians(trk)) + rng.normal(0, UNC_SIGMA_NM, n * k)
        brg, dist = np.degrees(np.arctan2(dx, dy)), np.hypot(dx, dy)
    elif scenario == "glide":
        brg = trk + rng.normal(0, GLIDE_DIR_SD, n * k)
        dist = rng.uniform(0, GLIDE_MAX_NM, n * k)
    elif scenario == "dstg_kernel":
        # DSTG/ATSB indicative kernel: uniform 15 NM disc + Gaussian drop-off sd 30 NM
        r = np.linspace(0, 200, 4001)
        f = r * np.where(r <= 15, 1.0, np.exp(-0.5 * ((r - 15) / 30.0) ** 2))
        c = np.cumsum(f); c /= c[-1]
        dist = np.interp(rng.random(n * k), c, r)
        brg = rng.uniform(0, 360, n * k)
    else:
        raise ValueError(scenario)
    la, lo = sp.destination(lat, lon, brg, dist * NM)
    return la, lo, w


LAT, LON = grid.common_grid()
_ELAT = np.r_[LAT - 0.025, LAT[-1] + 0.025]
_ELON = np.r_[LON - 0.025, LON[-1] + 0.025]


def to_grid(lat, lon, w, smooth=1.0):
    h, _, _ = np.histogram2d(lat, lon, bins=[_ELAT, _ELON], weights=w)
    inside = h.sum() / w.sum()
    if smooth:
        h = gaussian_filter(h, smooth, mode="constant")
    return h / h.sum(), inside


def stats_from_samples(x, w, bins=np.arange(-45, -10 + 1e-9, 0.1)):
    """Peak (of 0.1-deg histogram smoothed 0.2 deg), median, 50 % and 90 % central intervals."""
    w = w / w.sum()
    o = np.argsort(x)
    c = np.cumsum(w[o])
    q = {k: float(np.interp(k, c, x[o])) for k in (0.05, 0.25, 0.5, 0.75, 0.95)}
    h, e = np.histogram(x, bins=bins, weights=w)
    hs = gaussian_filter(h, 2.0)
    pk = float(0.5 * (e[:-1] + e[1:])[np.argmax(hs)])
    return dict(peak=pk, median=q[0.5], i50=[q[0.25], q[0.75]], i90=[q[0.05], q[0.95]])


# ------------------------------------------------------------------ main
def build(variant="baseline", seed=0, figures=True):
    rng = np.random.default_rng(seed)
    res = load_variant(variant)
    assert res, f"no SMC results for {variant}"
    wts = {h: mode_weights(res, h) for h in ("evidence", "equal")}
    summ = dict(variant=variant, modes={}, mode_weights=wts,
                eof=dict(w_glide=EOF_DEFAULT_W_GLIDE, unc_along_nm=UNC_ALONG_NM,
                         unc_sigma_nm=UNC_SIGMA_NM, glide_max_nm=GLIDE_MAX_NM,
                         glide_dir_sd=GLIDE_DIR_SD))
    ends = {}
    for m, z in res.items():
        la, lo, trk, gs = end_state(z)
        alat, adist = arc_project(la, lo)
        x = z["x"]
        names = list(z["names"])
        n = la.size
        ends[m] = dict(lat=la, lon=lo, trk=trk, gs=gs, alat=alat)
        ib = int(np.argmax(z["ll"]))
        par = {k: np.percentile(x[:, i], [5, 50, 95]).tolist() for i, k in enumerate(names)}
        summ["modes"][m] = dict(
            name=MODE_NAMES[m], logZ=float(z["logz"]), n=int(n),
            n_unique=int(np.unique(x[:, 0]).size),
            arc0019=stats_from_samples(alat, np.ones(n)),
            ll_max=float(z["ll"][ib]),
            map_params=dict(zip(names, x[ib].tolist())),
            map_bto_res=z["bto_res"][ib].round(1).tolist(),
            map_bfo_res=z["bfo_res"][ib].round(1).tolist(),
            map_bias=float(z["bias"][ib]),
            map_bto_rms=float(np.sqrt(np.mean(z["bto_res"][ib] ** 2))),
            map_bfo_rms=float(np.sqrt(np.mean(z["bfo_res"][ib] ** 2))),
            bto_labels=z["bto_label"].tolist(), bfo_labels=z["bfo_label"].tolist(),
            params_5_50_95=par,
            end_lat_5_50_95=np.percentile(la, [5, 50, 95]).tolist(),
            end_lon_5_50_95=np.percentile(lo, [5, 50, 95]).tolist(),
            final_track_5_50_95=np.percentile(trk, [5, 50, 95]).tolist(),
            final_gs_kt_5_50_95=np.percentile(gs, [5, 50, 95]).tolist())
    # combined arc latitude at 00:19:29
    for how, ww in wts.items():
        a = np.concatenate([ends[m]["alat"] for m in res])
        w = np.concatenate([np.full(ends[m]["alat"].size, ww[m] / ends[m]["alat"].size) for m in res])
        summ[f"arc0019_combined_{how}"] = stats_from_samples(a, w)

    # ---------------- grids ----------------
    layers, inside = {}, {}
    def grid_for(weights_by_mode, scenario, modes=None):
        L, O, W = [], [], []
        for m in (modes or res):
            e = ends[m]
            w = np.full(e["lat"].size, weights_by_mode[m] / e["lat"].size)
            if scenario == "arc0019":
                L.append(e["lat"]); O.append(e["lon"]); W.append(w)
            else:
                la, lo, wd = sample_eof(e["lat"], e["lon"], e["trk"], w, scenario, rng)
                L.append(la); O.append(lo); W.append(wd)
        return to_grid(np.concatenate(L), np.concatenate(O), np.concatenate(W))

    we = wts["evidence"]
    for sc in ("uncontrolled", "glide", "dstg_kernel", "arc0019"):
        layers[f"p_{sc}"], inside[sc] = grid_for(we, sc)
    wg = EOF_DEFAULT_W_GLIDE
    layers["p"] = (1 - wg) * layers["p_uncontrolled"] + wg * layers["p_glide"]
    unc_eq, _ = grid_for(wts["equal"], "uncontrolled")
    gl_eq, _ = grid_for(wts["equal"], "glide")
    layers["p_equal_modes"] = (1 - wg) * unc_eq + wg * gl_eq
    for m in res:
        one = {k: (1.0 if k == m else 0.0) for k in res}
        u, _ = grid_for(one, "uncontrolled", modes=[m])
        g, _ = grid_for(one, "glide", modes=[m])
        layers[f"p_mode_{m}"] = (1 - wg) * u + wg * g
    summ["mass_inside_grid_before_renorm"] = {k: float(v) for k, v in inside.items()}

    attrs = dict(
        title="MH370 end-point probability implied by Inmarsat BTO/BFO + simple autopilot paths",
        workstream="A (satcom)", variant=variant,
        method="SMC over 5 autopilot modes (LNAV, CTT, CMT, CTH, CMH) at constant Mach/FL with "
               "ERA5 winds; mode weights from SMC evidence (equal mode priors); "
               f"end-of-flight mixture p = {1-wg:.2f}*p_uncontrolled + {wg:.2f}*p_glide",
        mode_weights_evidence=json.dumps({k: round(v, 4) for k, v in we.items()}),
        note="Each variable sums to 1 over the grid (mass outside the grid renormalised away; "
             "see outputs/satcom/summary.json). See outputs/satcom/README.md.")
    ds = xr.Dataset({k: (("lat", "lon"), v.astype("float32")) for k, v in layers.items()},
                    coords={"lat": LAT, "lon": LON}, attrs=attrs)
    for k in ds.data_vars:
        ds[k].attrs["units"] = "probability per 0.05x0.05 deg cell"
    ds["p"].attrs["long_name"] = f"default: {1-wg:.2f} uncontrolled + {wg:.2f} piloted glide"
    ds["p_uncontrolled"].attrs["long_name"] = (f"uncontrolled descent: +{UNC_ALONG_NM} NM along final "
                                               f"track, 2-D Gaussian sd {UNC_SIGMA_NM} NM per axis")
    ds["p_glide"].attrs["long_name"] = (f"piloted glide: uniform 0-{GLIDE_MAX_NM} NM along final track "
                                        f"+/- N(0,{GLIDE_DIR_SD} deg)")
    ds["p_dstg_kernel"].attrs["long_name"] = "DSTG/ATSB kernel: 15 NM uniform disc + Gaussian sd 30 NM"
    ds["p_arc0019"].attrs["long_name"] = "aircraft position at 00:19:29 (no descent model)"
    ds["p_equal_modes"].attrs["long_name"] = "as p, but equal weight per autopilot mode"

    # ---------------- arc profile ----------------
    glat, glon = np.meshgrid(LAT, LON, indexing="ij")
    alat_cell, adist_cell = arc_project(glat.ravel(), glon.ravel())
    bins = np.round(np.arange(-44.0, -16.0 + 1e-9, 0.1), 2)
    be = np.r_[bins - 0.05, bins[-1] + 0.05]
    prof = pd.DataFrame({"lat": bins,
                         "arc_lon": [geo.arc_lon_for_lat(b, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
                                     for b in bins]})
    for k in ["p", "p_uncontrolled", "p_glide", "p_dstg_kernel", "p_equal_modes", "p_arc0019"] + \
            [f"p_mode_{m}" for m in res]:
        prof[k], _ = np.histogram(alat_cell, bins=be, weights=ds[k].values.ravel())
    for m in res:   # 00:19:29 arc-crossing latitude per mode (sample-based)
        prof[f"arc0019_{m}"], _ = np.histogram(ends[m]["alat"], bins=be)
        prof[f"arc0019_{m}"] /= ends[m]["alat"].size
    for k, v in summ["mode_weights"]["evidence"].items():
        summ["modes"][k]["weight_evidence"] = v
    for k in ("p", "p_uncontrolled", "p_glide", "p_dstg_kernel", "p_equal_modes"):
        summ[f"arcprofile_{k}"] = stats_from_samples(prof.lat.to_numpy(), prof[k].to_numpy())
    if variant == "baseline":
        grid.save(ds, NC)
        prof.round(6).to_csv(OUT / "arc_profile.csv", index=False)
    else:
        ds.to_netcdf(SMC / f"posterior_{variant}.nc", engine="h5netcdf")
        prof.round(6).to_csv(SMC / f"arc_profile_{variant}.csv", index=False)
    sp_ = OUT / "summary.json" if variant == "baseline" else SMC / f"summary_{variant}.json"
    sp_.write_text(json.dumps(summ, indent=1))
    if figures and variant == "baseline":
        make_figures(res, ends, ds, prof, summ)
    return summ, ds


VARIANT_LABELS = {
    "baseline": "default (BTO 42/69 us, BFO 7 Hz, bias 152+/-3 Hz)",
    "bto29": "BTO sigma 29/62 us (measurement noise only)",
    "no1828bfo": "drop 18:28:15 BFO",
    "no1827bto": "drop 18:27-18:28 R1200 BTOs",
    "bfo4p3": "BFO sigma 4.3 Hz",
    "bias25": "BFO bias prior sd 25 Hz (DSTG)",
    "wind90": "ERA5 winds x0.9",
    "wind110": "ERA5 winds x1.1",
    "wideprior": "Mach 0.62-0.86, FL200-410",
    "machdrift": "Mach linear drift -0.012..+0.004 /h",
}


def sensitivity(variants):
    rows, extra = [], {}
    for v in variants:
        if len(load_variant(v)) < len(MODES):
            print("skip (incomplete)", v)
            continue
        s, ds = build(v, figures=False) if v != "baseline" else (json.loads((OUT / "summary.json").read_text()), None)
        r = dict(variant=v, description=VARIANT_LABELS.get(v, v))
        for m in MODES:
            r[f"w_{m}"] = round(s["mode_weights"]["evidence"][m], 3)
            r[f"med_{m}"] = round(s["modes"][m]["arc0019"]["median"], 2)
            r[f"llmax_{m}"] = round(s["modes"][m]["ll_max"], 1)
        for k, key in (("arc0019", "arc0019_combined_evidence"), ("impact", "arcprofile_p")):
            st = s[key]
            r[f"{k}_peak"] = round(st["peak"], 2)
            r[f"{k}_median"] = round(st["median"], 2)
            r[f"{k}_50lo"], r[f"{k}_50hi"] = (round(x, 2) for x in st["i50"])
            r[f"{k}_90lo"], r[f"{k}_90hi"] = (round(x, 2) for x in st["i90"])
        eq = s["arc0019_combined_equal"]
        if v == "baseline":
            eq_base = eq
        r["arc0019_equalw_median"] = round(eq["median"], 2)
        r["arc0019_equalw_90lo"], r["arc0019_equalw_90hi"] = (round(x, 2) for x in eq["i90"])
        rows.append(r)
        if ds is not None:
            extra[f"p_sens_{v}"] = ds["p"]
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "sensitivity.csv", index=False)
    # add sensitivity layers to the primary NetCDF
    if extra:
        base = xr.load_dataset(NC, engine="h5netcdf")
        for k, v in extra.items():
            base[k] = v.astype("float32")
            base[k].attrs["long_name"] = "default mixture under sensitivity variant: " + \
                VARIANT_LABELS.get(k[7:], k[7:])
        grid.save(base, NC)
    # figure: intervals per variant
    fig, ax = plt.subplots(figsize=(8.5, 0.42 * (len(df) + 1) + 1.2))
    y = np.arange(len(df) + 1)[::-1]
    for yi, (_, r) in zip(y, df.iterrows()):
        ax.plot([r.arc0019_90lo, r.arc0019_90hi], [yi, yi], color="#86b6ef", lw=6, solid_capstyle="butt")
        ax.plot([r.arc0019_50lo, r.arc0019_50hi], [yi, yi], color="#256abf", lw=6, solid_capstyle="butt")
        ax.plot(r.arc0019_median, yi, "o", color=INK, ms=4)
    e = eq_base   # structural alternative: equal weight per autopilot mode (baseline)
    ax.plot(e["i90"], [0, 0], color="#f4b49a", lw=6, solid_capstyle="butt")
    ax.plot(e["i50"], [0, 0], color="#eb6834", lw=6, solid_capstyle="butt")
    ax.plot(e["median"], 0, "o", color=INK, ms=4)
    ax.set_yticks(y)
    ax.set_yticklabels(list(df.description) + ["default, but EQUAL weight per autopilot mode"],
                       fontsize=7.5, color=INK2)
    ax.axvline(-34.2342, color=MUTED, lw=0.8, ls="--")
    ax.text(-34.2, y.max() + 0.6, "UGIB LEP", fontsize=7, color=INK2)
    ax.set_xlabel("7th-arc latitude at 00:19:29 (deg); bars: 50 % (dark) and 90 % (light) intervals, "
                  "dot: median", fontsize=8, color=INK2)
    ax.set_ylim(-0.7, y.max() + 1.2)
    _style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig_sensitivity.png", dpi=150)
    plt.close(fig)
    return df


# ------------------------------------------------------------------ figures
def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(color="#e4e3df", lw=0.6)
    ax.set_axisbelow(True)


def _arcs(ax):
    for lab, t, b in [("19:41", geo.hms(19, 41, 2.906), 11500), ("20:41", geo.hms(20, 41, 4.904), 11740),
                      ("21:41", geo.hms(21, 41, 26.905), 12780), ("22:41", geo.hms(22, 41, 21.906), 14540),
                      ("00:11", geo.hms(24, 10, 59.928), 18040), ("00:19", geo.ARC7_TIME, 18400)]:
        a = geo.arc_polyline(b, t, 10_000.0, lats=np.arange(-45, 12, 0.25))
        ax.plot(a[:, 1], a[:, 0], color=MUTED, lw=0.8, ls="--", zorder=1)
        k = np.argmin(np.abs(a[:, 1] - 80.5))
        ax.text(a[k, 1], a[k, 0], lab, fontsize=6.5, color=INK2, ha="left", va="bottom")


def make_figures(res, ends, ds, prof, summ):
    atm, mag = sp.Atmos(), sp.MagVar()
    meas = sp.build_measurements()
    rng = np.random.default_rng(5)
    # ---- 1. paths, one panel per mode (small multiples; identity also in titles)
    fig, axs = plt.subplots(1, len(res), figsize=(3.0 * len(res), 6.2), sharey=True)
    for ax, m in zip(np.atleast_1d(axs), res):
        z = res[m]
        names = list(z["names"])
        pick = np.r_[np.argmax(z["ll"]), rng.choice(z["x"].shape[0], 40, replace=False)]
        P = {k: z["x"][pick, i] for i, k in enumerate(names)}
        o = sp.PathModel(m, meas, atm=atm, mag=mag).run(P, record_track=True)
        _arcs(ax)
        for j in range(1, pick.size):
            ax.plot(o["track_lon"][j], o["track_lat"][j], color=COL[m], lw=0.5, alpha=0.35)
        ax.plot(o["track_lon"][0], o["track_lat"][0], color=INK, lw=1.6, label="best fit")
        ax.scatter(ends[m]["lon"][::20], ends[m]["lat"][::20], s=2, color=COL[m], alpha=0.4)
        for lab, la, lo, kind in COMPARE[:5]:
            ax.scatter(lo, la, marker="x", s=14, color=INK2, lw=0.8)
        ax.scatter([sp.RADAR_POS[1]], [sp.RADAR_POS[0]], marker="^", color=INK, s=16)
        s = summ["modes"][m]
        ax.set_title(f"{MODE_NAMES[m]}\nweight {s['weight_evidence']:.2f}, "
                     f"median {abs(s['arc0019']['median']):.1f}S", fontsize=8.5, color=INK)
        ax.set_xlim(80, 106); ax.set_ylim(-42, 10); ax.set_aspect(1 / np.cos(np.radians(-15)))
        ax.set_xlabel("longitude (deg E)", fontsize=8, color=INK2)
        _style(ax)
    np.atleast_1d(axs)[0].set_ylabel("latitude (deg)", fontsize=8, color=INK2)
    fig.suptitle("Best-fit (black) and 40 posterior paths per autopilot mode; dashed: BTO arcs "
                 "at 10 km altitude; x: published end points; triangle: 18:22 radar point",
                 fontsize=9, color=INK, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT / "fig_paths_by_mode.png", dpi=150)
    plt.close(fig)

    # ---- 2. residuals of best-fit path per mode
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.2))
    for k, m in enumerate(res):
        s = summ["modes"][m]
        xb = np.arange(len(s["map_bto_res"])) + (k - 2) * 0.12
        xf = np.arange(len(s["map_bfo_res"])) + (k - 2) * 0.12
        a1.plot(xb, s["map_bto_res"], "o", ms=4, color=COL[m], label=MODE_NAMES[m])
        a2.plot(xf, s["map_bfo_res"], "o", ms=4, color=COL[m], label=MODE_NAMES[m])
    bto_s = meas[meas.kind == "BTO"].sigma.to_numpy()
    a1.fill_between(np.arange(bto_s.size), -bto_s, bto_s, step="mid", color="#e4e3df", zorder=0,
                    label=f"+/-1 sigma ({bto_s.min():.0f} / {bto_s.max():.0f} us)")
    a2.axhspan(-7, 7, color="#e4e3df", zorder=0, label="+/-1 sigma (7 Hz)")
    a1.set_xticks(range(bto_s.size)); a1.set_xticklabels(summ["modes"][m]["bto_labels"], rotation=30, fontsize=7)
    a2.set_xticks(range(len(summ["modes"][m]["bfo_labels"])))
    a2.set_xticklabels(summ["modes"][m]["bfo_labels"], rotation=30, fontsize=7)
    a1.set_ylabel("BTO residual (us)", fontsize=8, color=INK2)
    a2.set_ylabel("BFO residual (Hz)\n(after fitted bias)", fontsize=8, color=INK2)
    for a in (a1, a2):
        a.axhline(0, color=MUTED, lw=0.8)
        _style(a)
    a1.legend(fontsize=7, ncol=3, frameon=False)
    a1.set_title("Measured minus predicted, best-fit path of each mode", fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "fig_residuals_bestfit.png", dpi=150)
    plt.close(fig)

    # ---- 3. arc-latitude posterior per mode (00:19:29) + combined + DSTG
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    lat = prof.lat.to_numpy()
    for m in res:
        y = gaussian_filter(prof[f"arc0019_{m}"].to_numpy(), 1.0) / 0.1
        ax.plot(lat, y, color=COL[m], lw=1.6,
                label=f"{MODE_NAMES[m]} (w={summ['modes'][m]['weight_evidence']:.2f})")
    yc = gaussian_filter(prof["p_arc0019"].to_numpy(), 1.0) / 0.1
    ax.plot(lat, yc, color=INK, lw=2.2, label="combined (evidence-weighted)")
    dg = OUT / "dstg_fig10_3_digitised.csv"
    if dg.exists():
        d = pd.read_csv(dg)
        ax.plot(d.lat, d.pdf_per_deg, color=INK2, lw=1.2, ls=":", label="DSTG 2015 Fig 10.3 (digitised)")
    ax.axvline(-34.2342, color=MUTED, lw=0.8, ls="--")
    ax.text(-34.15, ax.get_ylim()[1] * 0.92, "UGIB LEP", fontsize=7, color=INK2)
    ax.set_xlim(-42, -26)
    ax.set_xlabel("latitude of 7th-arc crossing at 00:19:29 (deg)", fontsize=8, color=INK2)
    ax.set_ylabel("probability density (per deg)", fontsize=8, color=INK2)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig_arc_latitude_by_mode.png", dpi=150)
    plt.close(fig)

    # ---- 4. maps of p, p_uncontrolled, p_glide
    fig, axs = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "blue_seq", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"])
    for ax, k, t in zip(axs, ["p", "p_uncontrolled", "p_glide"],
                        ["default mixture", "uncontrolled descent", "piloted glide"]):
        v = ds[k].values / grid.cell_area_km2().values * 1e6
        im = ax.pcolormesh(LON, LAT, np.ma.masked_less(v, v.max() * 1e-3), cmap=cmap, shading="nearest")
        a = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-44, -16, 0.1))
        ax.plot(a[:, 1], a[:, 0], color=MUTED, lw=0.7, ls="--")
        for lab, la, lo, kind in COMPARE:
            ax.scatter(lo, la, marker="x", s=14, color=INK, lw=0.8)
            if ax is axs[0]:
                ax.annotate(lab.split(" (")[0], (lo, la), xytext=(4, 2), textcoords="offset points",
                            fontsize=6, color=INK2)
        ax.set_xlim(80, 106); ax.set_ylim(-42, -24)
        ax.set_aspect(1 / np.cos(np.radians(-32)))
        ax.set_title(t, fontsize=9, color=INK)
        ax.set_xlabel("longitude (deg E)", fontsize=8, color=INK2)
        _style(ax)
        cb = fig.colorbar(im, ax=ax, shrink=0.7)
        cb.set_label("probability per 10^6 km^2", fontsize=7, color=INK2)
        cb.ax.tick_params(labelsize=7)
    axs[0].set_ylabel("latitude (deg)", fontsize=8, color=INK2)
    fig.suptitle("Satcom end-point probability density (x: published end points; dashed: 7th arc)",
                 fontsize=9, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(OUT / "fig_posterior_maps.png", dpi=150)
    plt.close(fig)

    # ---- 5. parameter posteriors
    fig, axs = plt.subplots(2, 3, figsize=(11, 6))
    names = list(next(iter(res.values()))["names"])
    show = ["t_fmt", "theta", "mach", "fl", "gs_pre", "trk_pre"]
    lab = {"t_fmt": "FMT time (min after 18:00)", "theta": "post-FMT track/heading (deg)",
           "mach": "Mach", "fl": "flight level", "gs_pre": "pre-FMT ground speed (kt)",
           "trk_pre": "pre-FMT track (deg true)"}
    for ax, k in zip(axs.ravel(), show):
        i = names.index(k)
        for m in res:
            v = res[m]["x"][:, i]
            if k == "t_fmt":
                v = (v - geo.hms(18)) / 60
            h, e = np.histogram(v, bins=50, density=True)
            ax.plot(0.5 * (e[1:] + e[:-1]), h, color=COL[m], lw=1.4, label=MODE_NAMES[m])
        ax.set_xlabel(lab[k], fontsize=8, color=INK2)
        _style(ax)
    axs[0, 0].legend(fontsize=6.5, frameon=False)
    fig.suptitle("Posterior of path parameters per autopilot mode (baseline)", fontsize=9, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "fig_parameters_by_mode.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    import sys
    s, _ = build("baseline")
    print(json.dumps({k: s[k] for k in s if k.startswith(("arc0019_combined", "arcprofile_p"))}, indent=1))
    if "--sens" in sys.argv:
        df = sensitivity(list(VARIANT_LABELS))
        print(df.to_string())
