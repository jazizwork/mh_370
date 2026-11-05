"""Satcom layer v2 (reviewer response): evidence-weighted mixture over ALL path families.

Families (equal prior 1/7 each):
  5 single-mode families (LNAV, CTT, CMT, CTH, CMH; baseline runs of scripts/satcom_run_paths.py)
  WPT  waypoint family: FMT -> direct to W -> mode2 (uniform prior over the regional waypoint set
       x the 5 lateral modes); family evidence = mean of the component evidences
  TWO  generic two-leg family (constant true track theta1 -> theta2)
Within a family, components are weighted by their evidence (i.e. the family posterior).

Inputs : data/derived/satcom_smc/baseline_<mode>.npz, data/derived/satcom_smc/routes/*.npz
Outputs: NEW variables in data/derived/satcom_posterior.nc (existing variables untouched):
           p_v2, p_v2_uncontrolled, p_v2_glide, p_v2_arc0019, p_v2_equal_families,
           p_fam_waypoint, p_fam_twoleg
         outputs/satcom/arc_profile_v2.csv, evidence_v2.csv, evidence_components_v2.csv,
         summary_v2.json, fig_arc_latitude_by_family_v2.png, fig_paths_waypoint_v2.png,
         fig_evidence_by_waypoint_v2.png
Run    : .venv/bin/python -I scripts/satcom_posterior_v2.py
"""
import importlib.util
import json
import pathlib
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
from scipy.ndimage import gaussian_filter
from scipy.special import logsumexp

from mh370 import geo, grid, satcom
from mh370 import satcom_paths as sp
from mh370 import satcom_routes as sr

ROOT = pathlib.Path(__file__).resolve().parents[1]
SMC = ROOT / "data" / "derived" / "satcom_smc"
ROUTES = SMC / "routes"
OUT = ROOT / "outputs" / "satcom"
NC = ROOT / "data" / "derived" / "satcom_posterior.nc"


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SP = _load_script("satcom_posterior")     # end_state, arc_project, sample_eof, to_grid, ...
SINGLE = sp.MODES
FAMILIES = list(SINGLE) + ["WPT", "TWO"]
FAM_NAMES = dict(SP.MODE_NAMES, WPT="waypoint: FMT -> direct to W -> new mode",
                 TWO="generic two-leg: true track -> true track")
COL = dict(SP.COL, WPT="#008300", TWO="#6250d6")       # categorical slots 6, 7
INK, INK2, MUTED = SP.INK, SP.INK2, SP.MUTED
WG = SP.EOF_DEFAULT_W_GLIDE
N_RESAMPLE = 100_000            # particles per multi-component family for the grids
WPT_SET = "regional"


def lme(v):
    v = np.asarray(v, float)
    return float(logsumexp(v) - np.log(v.size))


# ------------------------------------------------------------------ loading
KEYS = ("x", "names", "ll", "logz", "t_meas", "lat", "lon", "vn", "ve", "h", "bto_res", "bfo_res",
        "bias", "bto_label", "bfo_label")


def load_npz(f):
    z = np.load(f, allow_pickle=False)
    d = {k: z[k] for k in KEYS}
    d["t_sw2"] = z["t_sw2"] if "t_sw2" in z else np.full(d["x"].shape[0], np.nan)
    for k in ("family", "wpt", "mode2", "fixed", "tie", "n", "seed"):
        if k in z:
            d[k] = z[k].item() if z[k].ndim == 0 else z[k]
    d["file"] = f.name
    return d


def pool(runs):
    """Combine replicate runs of one component: Z = mean of Z's; particles pooled."""
    out = {"logz": lme([r["logz"] for r in runs]), "logz_reps": [float(r["logz"]) for r in runs],
           "files": [r["file"] for r in runs], "n_each": int(runs[0]["x"].shape[0])}
    for k in ("x", "ll", "lat", "lon", "vn", "ve", "h", "bto_res", "bfo_res", "bias", "t_sw2"):
        out[k] = np.concatenate([r[k] for r in runs])
    for k in ("names", "t_meas", "bto_label", "bfo_label"):
        out[k] = runs[0][k]
    for k in ("family", "wpt", "mode2", "fixed", "tie"):
        if k in runs[0]:
            out[k] = runs[0][k]
    return out


RX = re.compile(r"^baseline_(WPT|TWO|SINGLE)_(.+)_n(\d+)_s(\d+)\.npz$|^baseline_(TWO)_n(\d+)_s(\d+)\.npz$")


def load_route_components():
    """{component key: [runs at the largest N]}; key = (family, wpt, mode2, tag)."""
    groups = {}
    for f in sorted(ROUTES.glob("baseline_*.npz")):
        stem = f.name
        m = re.match(r"^baseline_(.*)_n(\d+)_s(\d+)\.npz$", stem)
        if not m:
            continue
        body, n = m.group(1), int(m.group(2))
        parts = body.split("_")
        fam = parts[0]
        if fam in ("WPT", "WPTS"):
            key = (fam, parts[1], parts[2], "_".join(parts[3:]))
        elif fam == "TWO":
            key = ("TWO", "", "CTT", "_".join(parts[1:]))
        elif fam == "SINGLE":
            key = ("SINGLE", "", parts[1], "_".join(parts[2:]))
        else:
            continue
        groups.setdefault(key, {}).setdefault(n, []).append(f)
    comps = {}
    for key, byn in groups.items():
        nmax = max(byn)
        comps[key] = dict(runs=[load_npz(f) for f in byn[nmax]], n=nmax,
                          other_n={n: [load_npz(f)["logz"].item() for f in fs]
                                   for n, fs in byn.items() if n != nmax})
    return comps


# ------------------------------------------------------------------ diagnostics
def excluded_bfo_rows():
    """18:25:27-18:28:05 R-channel BFOs (excluded from the likelihood: SDU warm-up)."""
    log = satcom.load_su_log()
    s = log[(log.t >= geo.hms(18, 25, 27)) & (log.t < geo.hms(18, 28, 10)) & (log.chan == "R")
            & log.bfo.notna()]
    return s.t.to_numpy(float), s.bfo.to_numpy(float), s.Time.str[-12:-4].to_numpy()


EXC_T, EXC_Z, EXC_LAB = excluded_bfo_rows()


def best_fit_diag(fam, comp, i, atm, meas):
    """Residuals of the excluded 18:25-18:28 BFOs for particle i of a component (fitted bias)."""
    names = list(comp["names"])
    P = {k: comp["x"][i:i + 1, j] for j, k in enumerate(names)}
    if fam in SINGLE:
        ex = {"t": np.unique(np.concatenate([meas.t.to_numpy(), EXC_T]))}
        m = sp.PathModel(fam, ex, atm=atm)
    else:
        m = sr.RouteModel(comp["family"], meas, mode2=comp.get("mode2", "CTT"),
                          wpt=comp.get("wpt") if comp["family"] in ("WPT", "WPTS") else None, atm=atm,
                          extra_times=EXC_T)
    o = m.run(P, record_track=True)
    k = np.searchsorted(m.t_meas, EXC_T)
    pred = satcom.bfo(EXC_T, o["lat"][0, k], o["lon"][0, k], o["h"][0], o["vn"][0, k], o["ve"][0, k],
                      0.0, bias=0.0)
    res = EXC_Z - pred - float(comp["bias"][i])
    return res, o


def qtiles(v, w, qs=(0.05, 0.25, 0.5, 0.75, 0.95)):
    o = np.argsort(v)
    c = np.cumsum(w[o]) / w.sum()
    return [float(np.interp(q, c, v[o])) for q in qs]


def hm(t):
    if not np.isfinite(t):
        return "-"
    t = t % 86400
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}"



def assemble(rc, tag=""):
    """Families for the baseline (tag "") or for the sensitivity variant tag "d1840" (free rate
    of climb at the 18:40 call for every family; the waypoint family is then WPTS, i.e. with its
    own ground speed on the FMT -> W leg)."""
    fams = {}
    rep_single = {}
    for m in SINGLE:
        if tag == "":
            z = load_npz(SMC / f"baseline_{m}.npz")
            z["logz_reps"] = [float(z["logz"])]
            z["logz"] = float(z["logz"])
            rep_single[m] = [z["logz"]] + [float(r["logz"]) for r in
                                           rc.get(("SINGLE", "", m, ""), {}).get("runs", [])]
        else:
            c = rc[("SINGLE", "", m, tag)]
            z = dict(pool(c["runs"]), n=c["n"])
            rep_single[m] = z["logz_reps"]
        fams[m] = dict(comps={m: z}, logz=z["logz"])
    wfam = "WPT" if tag == "" else "WPTS"
    wset = sr.waypoint_set(WPT_SET)
    wcomps = {}
    for (f, w, m2, t), c in rc.items():
        if f == wfam and t == tag and w in wset:
            wcomps[f"{w}/{m2}"] = dict(pool(c["runs"]), n=c["n"], other_n=c["other_n"])
    missing = [f"{w}/{m}" for w in wset for m in sr.MODES2 if f"{w}/{m}" not in wcomps]
    assert not missing, f"missing {wfam} {tag} components: {missing[:10]} ..."
    fams["WPT"] = dict(comps=wcomps, logz=lme([c["logz"] for c in wcomps.values()]))
    c = rc[("TWO", "", "CTT", tag)]
    fams["TWO"] = dict(comps={"TWO": dict(pool(c["runs"]), n=c["n"])})
    fams["TWO"]["logz"] = fams["TWO"]["comps"]["TWO"]["logz"]
    refs = {}
    sfx = "" if tag == "" else "_" + tag
    for key, lab in ((("TWO", "", "CTT", "tied"), "TWO_tied"),
                     (("WPT", "BEDAX", "LNAV", "ugib180"), "UGIB_like"),
                     (("WPT", "BEDAX", "LNAV", "d1840_ugib180"), "UGIB_like_d1840_cruise"),
                     (("WPTS", "BEDAX", "LNAV", "d1840_ugib180"), "UGIB_like_d1840_slowleg")):
        if key in rc and (tag == "") == ("d1840" not in key[3]):
            refs[lab] = dict(pool(rc[key]["runs"]), n=rc[key]["n"])
    return fams, rep_single, wcomps, refs


def family_ends(fams):
    """Per-family 00:19:29 end states with within-family evidence weights."""
    ends = {}
    for f in FAMILIES:
        L, O, T, G, A, Wt, FMT, TSW = [], [], [], [], [], [], [], []
        lzc = np.array([c["logz"] for c in fams[f]["comps"].values()])
        wc = np.exp(lzc - logsumexp(lzc))
        for (cid, c), wk in zip(fams[f]["comps"].items(), wc):
            if wk < 1e-7:
                continue
            la, lo, trk, gs = SP.end_state(c)
            n = la.size
            L.append(la); O.append(lo); T.append(trk); G.append(gs)
            A.append(SP.arc_project(la, lo)[0])
            Wt.append(np.full(n, wk / n))
            FMT.append(c["x"][:, list(c["names"]).index("t_fmt")])
            TSW.append(c["t_sw2"])
        e = dict(lat=np.concatenate(L), lon=np.concatenate(O), trk=np.concatenate(T),
                 gs=np.concatenate(G), alat=np.concatenate(A), w=np.concatenate(Wt),
                 t_fmt=np.concatenate(FMT), t_sw2=np.concatenate(TSW))
        e["w"] /= e["w"].sum()
        ends[f] = e
        fams[f]["comp_weights"] = {k: float(v) for k, v in zip(fams[f]["comps"], wc)}
    return ends


def family_grids(ends, rng):
    fam_layers = {}
    for f in FAMILIES:
        e = ends[f]
        if f in SINGLE and np.allclose(e["w"], e["w"][0]):
            la, lo, trk, w = e["lat"], e["lon"], e["trk"], e["w"]
        else:   # systematic resampling to N_RESAMPLE equally weighted particles
            u = (rng.random() + np.arange(N_RESAMPLE)) / N_RESAMPLE
            idx = np.minimum(np.searchsorted(np.cumsum(e["w"]), u), e["w"].size - 1)
            la, lo, trk = e["lat"][idx], e["lon"][idx], e["trk"][idx]
            w = np.full(N_RESAMPLE, 1 / N_RESAMPLE)
        g = {}
        for sc in ("uncontrolled", "glide"):
            a, b, wd = SP.sample_eof(la, lo, trk, w, sc, rng)
            g[sc], _ = SP.to_grid(a, b, wd)
        g["arc0019"], _ = SP.to_grid(la, lo, w)
        fam_layers[f] = g
    return fam_layers


def family_weights(fams):
    lz = np.array([fams[f]["logz"] for f in FAMILIES])
    w_ev = np.exp(lz - logsumexp(lz))
    return {"evidence": dict(zip(FAMILIES, w_ev)), "equal": {f: 1 / len(FAMILIES) for f in FAMILIES}}


# ------------------------------------------------------------------ main
def main():
    rng = np.random.default_rng(11)
    meas = sp.build_measurements()
    atm = sp.Atmos()
    rc = load_route_components()
    fams, rep_single, wcomps, refs = assemble(rc, "")
    wset = sr.waypoint_set(WPT_SET)
    # ---------- family weights and end states
    W = family_weights(fams)
    best_single = max(fams[m]["logz"] for m in SINGLE)
    ends = family_ends(fams)

    # ---------- evidence table
    rows = []
    best_fits = {}

    def fam_row(label, f, comps, logz, e=None, reps=None):
        # best-fit particle over all components
        bi, bc, bll = None, None, -np.inf
        for cid, c in comps.items():
            i = int(np.argmax(c["ll"]))
            if c["ll"][i] > bll:
                bi, bc, bll = i, cid, float(c["ll"][i])
        c = comps[bc]
        fam_key = f if f in SINGLE else c.get("family", f)
        exc, o = best_fit_diag(f if f in SINGLE else fam_key, c, bi, atm, meas)
        bl, tl = list(c["bfo_label"]), list(c["bto_label"])
        rb, rf = c["bto_res"][bi], c["bfo_res"][bi]
        i1828 = [k for k, s in enumerate(tl) if s.startswith(("R600 18:25", "R1200 18:27", "R1200 18:28"))]
        names = list(c["names"])
        la_b, lo_b, _, _ = SP.end_state(c)
        best_arc = float(SP.arc_project(la_b[bi:bi + 1], lo_b[bi:bi + 1])[0][0])
        r = dict(family=label, logZ=round(logz, 2), dlogZ_vs_best_single=round(logz - best_single, 2),
                 logZ_reps=" ".join(f"{v:.2f}" for v in (reps or [])),
                 best_component=bc, best_loglik=round(bll, 2), best_arc_lat=round(best_arc, 2),
                 best_bto_rms_us=round(float(np.sqrt(np.mean(rb ** 2))), 1),
                 best_bfo_rms_hz=round(float(np.sqrt(np.mean(rf ** 2))), 1),
                 best_bto_rms_1825_1828_us=round(float(np.sqrt(np.mean(rb[i1828] ** 2))), 1),
                 best_bfo_res_1828_hz=round(float(rf[bl.index("R1200 18:28:15")]), 1),
                 best_bfo_res_1840_call_hz=round(float(rf[bl.index("C 18:40 mean")]), 1),
                 best_excluded_bfo_1825_1828_res_hz=" ".join(f"{v:+.0f}" for v in exc),
                 best_bias_hz=round(float(c["bias"][bi]), 1),
                 best_t_fmt=hm(c["x"][bi, names.index("t_fmt")]),
                 best_t_sw2=hm(c["t_sw2"][bi]),
                 best_mach=round(float(c["x"][bi, names.index("mach")]), 3),
                 best_fl=round(float(c["x"][bi, names.index("fl")]), 0),
                 best_theta=" / ".join(f"{c['x'][bi, names.index(k)]:.1f}" for k in ("theta", "theta1", "theta2")
                                       if k in names))
        if e is None:
            la, lo, trk, gs = SP.end_state(c)
            e = dict(alat=SP.arc_project(la, lo)[0], w=np.full(la.size, 1 / la.size),
                     t_fmt=c["x"][:, names.index("t_fmt")], t_sw2=c["t_sw2"])
        q = qtiles(e["alat"], e["w"])
        qf = qtiles(e["t_fmt"], e["w"])
        r.update(arc_median=round(q[2], 2), arc_50=f"{q[1]:.2f} to {q[3]:.2f}", arc_90=f"{q[0]:.2f} to {q[4]:.2f}",
                 p_north_of_36S=round(float(np.sum(e["w"][e["alat"] > -36.0])), 4),
                 p_34p2_pm0p5=round(float(np.sum(e["w"][np.abs(e["alat"] + 34.2342) < 0.5])), 4),
                 fmt_median=hm(qf[2]), fmt_90=f"{hm(qf[0])}-{hm(qf[4])}")
        ok = np.isfinite(e["t_sw2"])
        if ok.any():
            qs = qtiles(e["t_sw2"][ok], e["w"][ok])
            r.update(t_sw2_median=hm(qs[2]), t_sw2_90=f"{hm(qs[0])}-{hm(qs[4])}",
                     p_reached_w=round(float(np.sum(e["w"][ok])), 3))
        best_fits[label] = dict(comp=bc, i=bi, track=(o["track_lon"][0], o["track_lat"][0]))
        rows.append(r)
        return r

    for m in SINGLE:
        fam_row(m, m, fams[m]["comps"], fams[m]["logz"], ends[m], rep_single[m])
    fam_row("WPT (regional set, 28 x 5)", "WPT", fams["WPT"]["comps"], fams["WPT"]["logz"], ends["WPT"])
    fam_row("TWO", "TWO", fams["TWO"]["comps"], fams["TWO"]["logz"], ends["TWO"],
            fams["TWO"]["comps"]["TWO"]["logz_reps"])
    # WPT sub-families
    for m2 in sr.MODES2:
        sub = {k: v for k, v in wcomps.items() if k.endswith("/" + m2)}
        fam_row(f"WPT, mode2 = {m2} only", "WPT", sub, lme([c["logz"] for c in sub.values()]),
                _sub_ends(sub))
    lit = sr.waypoint_set("literature")
    sub = {k: v for k, v in wcomps.items() if k.split("/")[0] in lit}
    fam_row(f"WPT, literature set ({len(lit)} x 5)", "WPT", sub, lme([c["logz"] for c in sub.values()]),
            _sub_ends(sub))
    sub = {k: v for k, v in wcomps.items() if k.startswith("BEDAX/")}
    fam_row("WPT, BEDAX only (x 5 modes)", "WPT", sub, lme([c["logz"] for c in sub.values()]), _sub_ends(sub))
    bestc = max(wcomps, key=lambda k: wcomps[k]["logz"])
    fam_row(f"WPT, best single component ({bestc})", "WPT", {bestc: wcomps[bestc]}, wcomps[bestc]["logz"],
            _sub_ends({bestc: wcomps[bestc]}), wcomps[bestc]["logz_reps"])
    for k in ("BEDAX/LNAV", "BEDAX/CTT"):
        fam_row(f"WPT, {k} (theta2 free)", "WPT", {k: wcomps[k]}, wcomps[k]["logz"], _sub_ends({k: wcomps[k]}),
                wcomps[k]["logz_reps"])
    if "UGIB_like" in refs:
        c = refs["UGIB_like"]
        fam_row("UGIB-like: BEDAX -> LNAV 180 T (theta2 fixed)", "WPT", {"BEDAX/LNAV180": c}, c["logz"],
                _sub_ends({"BEDAX/LNAV180": c}), c["logz_reps"])
    if "TWO_tied" in refs:
        c = refs["TWO_tied"]
        fam_row("check: TWO with theta2 = theta1 (must equal CTT)", "TWO", {"TWO_tied": c}, c["logz"],
                _sub_ends({"TWO_tied": c}), c["logz_reps"])
    # ---------- sensitivity d1840: free rate of climb at the 18:40 call (all families), waypoint
    # family with its own ground speed on the FMT -> W leg (WPTS).  Same data, so the log
    # evidences are directly comparable with the baseline rows.
    d18 = None
    try:
        fams_d, rep_d, wcomps_d, refs_d = assemble(rc, "d1840")
    except (KeyError, AssertionError) as err:
        print("d1840 variant incomplete, skipped:", repr(err)[:200])
    else:
        W_d = family_weights(fams_d)
        ends_d = family_ends(fams_d)
        for m in SINGLE:
            fam_row(f"[d1840] {m}", m, fams_d[m]["comps"], fams_d[m]["logz"], ends_d[m], rep_d[m])
        fam_row("[d1840] WPTS (regional set, 28 x 5)", "WPT", fams_d["WPT"]["comps"], fams_d["WPT"]["logz"],
                ends_d["WPT"])
        fam_row("[d1840] TWO", "TWO", fams_d["TWO"]["comps"], fams_d["TWO"]["logz"], ends_d["TWO"],
                fams_d["TWO"]["comps"]["TWO"]["logz_reps"])
        sub = {k: v for k, v in wcomps_d.items() if k.startswith("BEDAX/")}
        fam_row("[d1840] WPTS, BEDAX only (x 5 modes)", "WPT", sub, lme([c["logz"] for c in sub.values()]),
                _sub_ends(sub))
        bc = max(wcomps_d, key=lambda k: wcomps_d[k]["logz"])
        fam_row(f"[d1840] WPTS, best single component ({bc})", "WPT", {bc: wcomps_d[bc]}, wcomps_d[bc]["logz"],
                _sub_ends({bc: wcomps_d[bc]}), wcomps_d[bc]["logz_reps"])
        for key, lab in (("UGIB_like_d1840_cruise", "[d1840] UGIB-like BEDAX -> LNAV 180 T, cruise-speed leg (WPT)"),
                         ("UGIB_like_d1840_slowleg", "[d1840] UGIB-like BEDAX -> LNAV 180 T, own-speed leg (WPTS)")):
            if key in refs_d:
                c = refs_d[key]
                fam_row(lab, "WPT", {key: c}, c["logz"], _sub_ends({key: c}), c["logz_reps"])
        d18 = dict(fams=fams_d, W=W_d, ends=ends_d, wcomps=wcomps_d, refs=refs_d)

    ev = pd.DataFrame(rows)
    for f in FAMILIES:
        lab = f if f in SINGLE else ("WPT (regional set, 28 x 5)" if f == "WPT" else "TWO")
        ev.loc[ev.family == lab, "weight_evidence_7fam"] = round(W["evidence"][f], 4)
        if d18 is not None:
            lab = f"[d1840] {f}" if f in SINGLE else ("[d1840] WPTS (regional set, 28 x 5)" if f == "WPT"
                                                     else "[d1840] TWO")
            ev.loc[ev.family == lab, "weight_evidence_7fam"] = round(d18["W"]["evidence"][f], 4)
    ev.to_csv(OUT / "evidence_v2.csv", index=False)

    # per-component table (WPT + others)
    crow = []
    for k, c in wcomps.items():
        w, m2 = k.split("/")
        la, lo, trk, gs = SP.end_state(c)
        a = SP.arc_project(la, lo)[0]
        i = int(np.argmax(c["ll"]))
        crow.append(dict(component=k, wpt=w, mode2=m2, wpt_lat=sr.load_waypoints().loc[w, "lat_deg"],
                         wpt_lon=sr.load_waypoints().loc[w, "lon_deg"], n=c["n"],
                         n_reps=len(c["logz_reps"]), logZ=round(c["logz"], 3),
                         logZ_reps=" ".join(f"{v:.2f}" for v in c["logz_reps"]),
                         logZ_other_n=json.dumps(c.get("other_n", {})),
                         weight_in_family=round(fams["WPT"]["comp_weights"][k], 5),
                         best_loglik=round(float(c["ll"][i]), 2), arc_median=round(float(np.median(a)), 2),
                         p_reached_w=round(float(np.isfinite(c["t_sw2"]).mean()), 3)))
    cdf = pd.DataFrame(crow).sort_values("logZ", ascending=False)
    cdf.to_csv(OUT / "evidence_components_v2.csv", index=False)
    if d18 is not None:
        crow = []
        for k, c in d18["wcomps"].items():
            w, m2 = k.split("/")
            la, lo, trk, gs = SP.end_state(c)
            i = int(np.argmax(c["ll"]))
            names = list(c["names"])
            crow.append(dict(component=k, wpt=w, mode2=m2, n=c["n"], logZ=round(c["logz"], 3),
                             logZ_reps=" ".join(f"{v:.2f}" for v in c["logz_reps"]),
                             weight_in_family=round(d18["fams"]["WPT"]["comp_weights"][k], 5),
                             best_loglik=round(float(c["ll"][i]), 2),
                             arc_median=round(float(np.median(SP.arc_project(la, lo)[0])), 2),
                             gs1_median=round(float(np.median(c["x"][:, names.index("gs1")])), 0),
                             roc1840_median=round(float(np.median(c["x"][:, names.index("roc1840")])), 0)))
        pd.DataFrame(crow).sort_values("logZ", ascending=False).to_csv(
            OUT / "evidence_components_v2_d1840.csv", index=False)

    # ---------- grids
    layers = {}
    fam_layers = family_grids(ends, rng)
    for sc in ("uncontrolled", "glide", "arc0019"):
        layers[f"p_v2_{sc}"] = sum(W["evidence"][f] * fam_layers[f][sc] for f in FAMILIES)
    layers["p_v2"] = (1 - WG) * layers["p_v2_uncontrolled"] + WG * layers["p_v2_glide"]
    layers["p_v2_equal_families"] = sum(
        W["equal"][f] * ((1 - WG) * fam_layers[f]["uncontrolled"] + WG * fam_layers[f]["glide"])
        for f in FAMILIES)
    layers["p_fam_waypoint"] = (1 - WG) * fam_layers["WPT"]["uncontrolled"] + WG * fam_layers["WPT"]["glide"]
    layers["p_fam_twoleg"] = (1 - WG) * fam_layers["TWO"]["uncontrolled"] + WG * fam_layers["TWO"]["glide"]
    if d18 is not None:
        fl_d = family_grids(d18["ends"], rng)
        layers["p_v2_sens_descent1840"] = sum(
            d18["W"]["evidence"][f] * ((1 - WG) * fl_d[f]["uncontrolled"] + WG * fl_d[f]["glide"])
            for f in FAMILIES)
    for k in layers:
        layers[k] = layers[k] / layers[k].sum()
    base = xr.load_dataset(NC, engine="h5netcdf")
    old_vars = list(base.data_vars)
    wtxt = json.dumps({k: round(float(v), 5) for k, v in W["evidence"].items()})
    long = {
        "p_v2": f"RECOMMENDED v2: evidence-weighted over 7 path families (5 single-mode + waypoint + "
                f"two-leg, equal family priors), {1-WG:.2f} uncontrolled + {WG:.2f} piloted glide",
        "p_v2_uncontrolled": "v2 family mixture, uncontrolled-descent end of flight",
        "p_v2_glide": "v2 family mixture, piloted-glide end of flight",
        "p_v2_arc0019": "v2 family mixture, aircraft position at 00:19:29 (no descent model)",
        "p_v2_equal_families": "as p_v2 but each of the 7 families weighted equally (components within "
                               "a family still weighted by evidence)",
        "p_fam_waypoint": "waypoint family only (FMT -> direct to a published waypoint -> new lateral "
                          "mode; uniform prior over 28 regional waypoints x 5 modes), default EOF mixture",
        "p_fam_twoleg": "generic two-leg family only (true track -> true track), default EOF mixture",
        "p_v2_sens_descent1840": "SENSITIVITY: as p_v2 but every family has a free rate of climb at the "
                                 "18:40 call (U(-4000, 0) fpm) and the waypoint family has its own ground "
                                 "speed on the FMT -> W leg (WPTS); evidence-weighted over 7 families",
    }
    for k, v in layers.items():
        base[k] = (("lat", "lon"), v.astype("float32"))
        base[k].attrs["units"] = "probability per 0.05x0.05 deg cell"
        base[k].attrs["long_name"] = long[k]
        if k.startswith("p_v2"):
            base[k].attrs["family_weights_evidence"] = wtxt
    base.attrs["v2_note"] = ("p_v2* / p_fam_* added for the reviewer response (waypoint and two-leg "
                             "families); see outputs/satcom/README.md section 13. Existing variables "
                             "unchanged.")
    grid.save(base, NC)
    chk = xr.load_dataset(NC, engine="h5netcdf")
    assert all(k in chk for k in old_vars) and all(k in chk for k in layers)

    # ---------- arc profile v2
    glat, glon = np.meshgrid(SP.LAT, SP.LON, indexing="ij")
    alat_cell, _ = SP.arc_project(glat.ravel(), glon.ravel())
    bins = np.round(np.arange(-44.0, -16.0 + 1e-9, 0.1), 2)
    be = np.r_[bins - 0.05, bins[-1] + 0.05]
    old_prof = pd.read_csv(OUT / "arc_profile.csv")
    prof = pd.DataFrame({"lat": bins, "arc_lon": old_prof.arc_lon.to_numpy()})
    prof["p"] = old_prof["p"].to_numpy()
    prof["p_arc0019"] = old_prof["p_arc0019"].to_numpy()
    for k in layers:
        prof[k], _ = np.histogram(alat_cell, bins=be, weights=chk[k].values.ravel())
    for f in FAMILIES:
        prof[f"arc0019_{f}"], _ = np.histogram(ends[f]["alat"], bins=be, weights=ends[f]["w"])
    if d18 is not None:
        a = np.concatenate([d18["ends"][f]["alat"] for f in FAMILIES])
        w = np.concatenate([d18["W"]["evidence"][f] * d18["ends"][f]["w"] for f in FAMILIES])
        prof["arc0019_v2_sens_descent1840"], _ = np.histogram(a, bins=be, weights=w)
        for f in FAMILIES:
            prof[f"arc0019_d1840_{f}"], _ = np.histogram(d18["ends"][f]["alat"], bins=be,
                                                         weights=d18["ends"][f]["w"])
    prof.round(6).to_csv(OUT / "arc_profile_v2.csv", index=False)

    # ---------- summary
    def st(k):
        return SP.stats_from_samples(prof.lat.to_numpy(), prof[k].to_numpy())

    a_all = np.concatenate([ends[f]["alat"] for f in FAMILIES])
    summ = dict(
        families=FAMILIES, waypoint_set=WPT_SET, waypoints=wset,
        family_logZ={f: fams[f]["logz"] for f in FAMILIES},
        family_weights=W, single_mode_logZ_replicates=rep_single,
        arc0019_v2=SP.stats_from_samples(a_all, np.concatenate([W["evidence"][f] * ends[f]["w"] for f in FAMILIES])),
        arc0019_v2_equal_families=SP.stats_from_samples(
            a_all, np.concatenate([W["equal"][f] * ends[f]["w"] for f in FAMILIES])),
        arc0019_by_family={f: SP.stats_from_samples(ends[f]["alat"], ends[f]["w"]) for f in FAMILIES},
        arcprofile={k: st(k) for k in ["p", "p_arc0019"] + list(layers)},
        wpt_top_components=cdf.head(15).to_dict("records"),
        refs={k: dict(logZ=v["logz"], logZ_reps=v["logz_reps"]) for k, v in refs.items()})
    if d18 is not None:
        summ["d1840"] = dict(
            family_logZ={f: d18["fams"][f]["logz"] for f in FAMILIES}, family_weights=d18["W"],
            arc0019=SP.stats_from_samples(prof.lat.to_numpy(), prof["arc0019_v2_sens_descent1840"].to_numpy()),
            arc0019_by_family={f: SP.stats_from_samples(d18["ends"][f]["alat"], d18["ends"][f]["w"])
                               for f in FAMILIES},
            refs={k: dict(logZ=v["logz"], logZ_reps=v["logz_reps"]) for k, v in d18["refs"].items()})
    (OUT / "summary_v2.json").write_text(json.dumps(summ, indent=1, default=float))
    print(ev[["family", "logZ", "dlogZ_vs_best_single", "logZ_reps", "best_loglik", "best_bto_rms_us",
              "best_bfo_rms_hz", "best_bfo_res_1828_hz", "best_bfo_res_1840_call_hz", "fmt_median",
              "arc_median", "arc_50", "arc_90"]].to_string())
    print(json.dumps({k: summ[k] for k in ("family_weights", "arc0019_v2", "arc0019_v2_equal_families")},
                     indent=1, default=float))
    print(json.dumps(summ["arcprofile"], indent=1))
    make_figures(fams, ends, W, prof, cdf, best_fits, refs, meas, atm, rng, wset)


def _sub_ends(comps):
    lzc = np.array([c["logz"] for c in comps.values()])
    wc = np.exp(lzc - logsumexp(lzc))
    A, Wt, F, T = [], [], [], []
    for c, wk in zip(comps.values(), wc):
        la, lo, trk, gs = SP.end_state(c)
        A.append(SP.arc_project(la, lo)[0])
        Wt.append(np.full(la.size, wk / la.size))
        F.append(c["x"][:, list(c["names"]).index("t_fmt")])
        T.append(c["t_sw2"])
    return dict(alat=np.concatenate(A), w=np.concatenate(Wt), t_fmt=np.concatenate(F),
                t_sw2=np.concatenate(T))


# ------------------------------------------------------------------ figures
def make_figures(fams, ends, W, prof, cdf, best_fits, refs, meas, atm, rng, wset):
    style = SP._style
    lat = prof.lat.to_numpy()
    # ---- 1. arc latitude by family (left) and combined old vs v2 (right)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4), sharex=True)
    for f in FAMILIES:
        y = gaussian_filter(prof[f"arc0019_{f}"].to_numpy(), 1.0) / 0.1
        a1.plot(lat, y, color=COL[f], lw=2.0 if f in ("WPT", "TWO") else 1.3,
                label=f"{FAM_NAMES[f]}  (w={W['evidence'][f]:.2f})")
    a1.set_title("00:19:29 arc crossing, per family (each normalised)", fontsize=9, color=INK)
    for k, lab, kw in (("p_arc0019", "v1: 5 single-mode families, evidence-weighted", dict(color=MUTED, lw=1.6, ls="--")),
                       ("p_v2_arc0019", "v2: 7 families, evidence-weighted (recommended)", dict(color=INK, lw=2.2))):
        a2.plot(lat, gaussian_filter(prof[k].to_numpy(), 1.0) / 0.1, label=lab, **kw)
    # equal-family version at 00:19 from samples
    ae = np.concatenate([ends[f]["alat"] for f in FAMILIES])
    we = np.concatenate([W["equal"][f] * ends[f]["w"] for f in FAMILIES])
    h, e = np.histogram(ae, bins=np.r_[lat - 0.05, lat[-1] + 0.05], weights=we)
    a2.plot(lat, gaussian_filter(h, 1.0) / 0.1, color=COL["TWO"], lw=1.4, ls=":",
            label="v2 families weighted equally (sensitivity)")
    if "arc0019_v2_sens_descent1840" in prof:
        a2.plot(lat, gaussian_filter(prof["arc0019_v2_sens_descent1840"].to_numpy(), 1.0) / 0.1, color=COL["WPT"],
                lw=1.4, ls="-.", label="sensitivity: free descent at the 18:40 call + own-speed waypoint leg")
    dg = OUT / "dstg_fig10_3_digitised.csv"
    if dg.exists():
        d = pd.read_csv(dg)
        a2.plot(d.lat, d.pdf_per_deg, color=INK2, lw=1.0, ls="-.", label="DSTG 2015 Fig 10.3 (digitised)")
    a2.set_title("combined 00:19:29 arc crossing", fontsize=9, color=INK)
    a1.set_ylim(0, a1.get_ylim()[1] * 1.55)
    a2.set_ylim(0, a2.get_ylim()[1] * 1.05)
    for a, loc in ((a1, "upper left"), (a2, "upper right")):
        a.axvline(-34.2342, color=MUTED, lw=0.8, ls="--")
        a.text(-34.32, a.get_ylim()[1] * 0.45, "UGIB LEP 34.23 S", fontsize=7, color=INK2, rotation=90,
               va="center", ha="right")
        a.set_xlim(-42, -26)
        a.set_xlabel("latitude of 7th-arc crossing at 00:19:29 (deg)", fontsize=8, color=INK2)
        a.legend(fontsize=6.5, frameon=False, loc=loc)
        style(a)
    a1.set_ylabel("probability density (per deg)", fontsize=8, color=INK2)
    fig.tight_layout()
    fig.savefig(OUT / "fig_arc_latitude_by_family_v2.png", dpi=150)
    plt.close(fig)

    # ---- 2. per-waypoint evidence (dot plot), waypoints sorted north -> south
    wp = sr.load_waypoints()
    order = sorted(wset, key=lambda w: -wp.loc[w, "lat_deg"])
    XMIN = -60.0
    fig, ax = plt.subplots(figsize=(7.8, 0.26 * len(order) + 1.9))
    for j, w in enumerate(order):
        for k, m2 in enumerate(sr.MODES2):
            r = cdf[cdf.component == f"{w}/{m2}"].iloc[0]
            y = j + (k - 2) * 0.13
            clipped = r.logZ < XMIN
            ax.plot(max(r.logZ, XMIN), y, "<" if clipped else "o", ms=4.5 if not clipped else 4,
                    color=COL[m2], mec="#fcfcfb", mew=0.6, ls="none",
                    label=SP.MODE_NAMES[m2] if j == 0 else None)
    refs_ = [(fams["LNAV"]["logz"], COL["LNAV"], "-", "single-mode LNAV family"),
             (fams["CTT"]["logz"], COL["CTT"], "--", "single-mode CTT family"),
             (fams["WPT"]["logz"], COL["WPT"], "-", "waypoint family (mean over 28 x 5)"),
             (fams["TWO"]["logz"], COL["TWO"], ":", "two-leg family")]
    for x, c, ls, lab in refs_:
        ax.axvline(x, color=c, lw=1.1, ls=ls, label=f"{lab}: {x:.1f}")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([f"{w} ({wp.loc[w, 'lat_deg']:+.1f}, {wp.loc[w, 'lon_deg']:.1f})" for w in order],
                       fontsize=7, color=INK2)
    ax.invert_yaxis()
    ax.set_xlim(XMIN - 1.5, max(-10, cdf.logZ.max() + 2))
    ax.set_xlabel(f"log evidence of each component (waypoint W, mode after W); '<' = below {XMIN:.0f}",
                  fontsize=8, color=INK2)
    ax.legend(fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(0.0, -0.06), ncol=2)
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig_evidence_by_waypoint_v2.png", dpi=150)
    plt.close(fig)

    # ---- 3. best-fit paths on a map
    fig, axs = plt.subplots(1, 3, figsize=(13.0, 11.0), sharey=True)
    top = cdf.head(5)

    def paths(comp_family, comp, k=30, wpt=None, mode2="CTT"):
        n = comp["x"].shape[0]
        pick = np.r_[np.argmax(comp["ll"]), rng.choice(n, min(k, n), replace=False)]
        names = list(comp["names"])
        P = {kk: comp["x"][pick, j] for j, kk in enumerate(names)}
        m = sr.RouteModel(comp_family, meas, mode2=mode2, wpt=wpt, atm=atm)
        return m.run(P, record_track=True)

    def base_ax(ax):
        SP._arcs(ax)
        for w in wset:
            ax.plot(wp.loc[w, "lon_deg"], wp.loc[w, "lat_deg"], marker="^", ms=3.5, color=MUTED, ls="none")
        ax.scatter([sp.RADAR_POS[1]], [sp.RADAR_POS[0]], marker="^", color=INK, s=18, zorder=5)
        ax.plot(93.7875, -34.2342, "x", color=INK, ms=6, mew=1.2)
        ax.annotate("UGIB LEP", (93.7875, -34.2342), xytext=(4, -9), textcoords="offset points", fontsize=6.5, color=INK2)
        ax.set_xlim(82, 102); ax.set_ylim(-42, 10)
        ax.set_aspect(1 / np.cos(np.radians(-15)))
        ax.set_xlabel("longitude (deg E)", fontsize=8, color=INK2)
        style(ax)

    ax = axs[0]
    base_ax(ax)
    styles = ["-", "--", ":", "-.", (0, (5, 1, 1, 1, 1, 1))]
    seen = set()
    for (_, r), ls in zip(top.iterrows(), styles):
        c = fams["WPT"]["comps"][r.component]
        o = paths("WPT", c, k=0, wpt=r.wpt, mode2=r.mode2)
        ax.plot(o["track_lon"][0], o["track_lat"][0], color=COL["WPT"], lw=1.5, ls=ls,
                label=f"{r.wpt} -> {SP.MODE_NAMES[r.mode2]} (w={r.weight_in_family:.2f})")
        if r.wpt not in seen:
            seen.add(r.wpt)
            ax.plot(wp.loc[r.wpt, "lon_deg"], wp.loc[r.wpt, "lat_deg"], marker="^", ms=5, color=INK, ls="none")
            ax.annotate(r.wpt, (wp.loc[r.wpt, "lon_deg"], wp.loc[r.wpt, "lat_deg"]), xytext=(4, -2),
                        textcoords="offset points", fontsize=6.5, color=INK2)
    ax.legend(fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(0.0, -0.05))
    ax.set_title("waypoint family: best fit of the 5 highest-evidence\ncomponents (W / mode after W)",
                 fontsize=8.5, color=INK)
    ax.set_ylabel("latitude (deg)", fontsize=8, color=INK2)
    # UGIB-like
    ax = axs[1]
    base_ax(ax)
    if "UGIB_like" in refs:
        c = refs["UGIB_like"]
        o = paths("WPT", c, k=30, wpt="BEDAX", mode2="LNAV")
        for j in range(1, o["track_lon"].shape[0]):
            ax.plot(o["track_lon"][j], o["track_lat"][j], color=COL["WPT"], lw=0.5, alpha=0.35)
        ax.plot(o["track_lon"][0], o["track_lat"][0], color=COL["WPT"], lw=1.6,
                label="this model: FMT -> BEDAX -> 180 T,\nconstant Mach/FL (best fit + 30 posterior)")
    UR = _load_script("satcom_ugib_replay")
    ts = np.arange(geo.hms(18, 22, 12), geo.hms(24, 19, 29), 30.0)
    st = np.array([UR.state_at(t)[:2] for t in ts])
    ax.plot(st[:, 1], st[:, 0], color=INK, lw=1.4, ls="--",
            label="UGIB 2020 published route (descent to FL100,\nholding speed, 6N FIR turns, BEDAX)")
    lbest = best_fits["LNAV"]["track"]
    ax.plot(lbest[0], lbest[1], color=COL["LNAV"], lw=1.2, label="single-mode LNAV best fit")
    ax.plot(wp.loc["BEDAX", "lon_deg"], wp.loc["BEDAX", "lat_deg"], marker="^", ms=5, color=INK, ls="none")
    ax.annotate("BEDAX", (wp.loc["BEDAX", "lon_deg"], wp.loc["BEDAX", "lat_deg"]), xytext=(-30, 2),
                textcoords="offset points", fontsize=6.5, color=INK2)
    ax.legend(fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(0.0, -0.05))
    ax.set_title("UGIB-like configuration vs UGIB's own route", fontsize=8.5, color=INK)
    # two-leg
    ax = axs[2]
    base_ax(ax)
    c = fams["TWO"]["comps"]["TWO"]
    o = paths("TWO", c, k=30)
    for j in range(1, o["track_lon"].shape[0]):
        ax.plot(o["track_lon"][j], o["track_lat"][j], color=COL["TWO"], lw=0.5, alpha=0.35)
    ax.plot(o["track_lon"][0], o["track_lat"][0], color=INK, lw=1.5, label="best fit (highest-likelihood particle)")
    ax.plot([], [], color=COL["TWO"], lw=0.8, label="30 posterior paths")
    ax.legend(fontsize=6.5, frameon=False, loc="upper left", bbox_to_anchor=(0.0, -0.05))
    ax.set_title("generic two-leg family: best fit + 30 posterior paths", fontsize=8.5, color=INK)
    fig.suptitle("Multi-leg route families (dashed grey: BTO arcs at 10 km; triangles: regional waypoint set; "
                 "black triangle: 18:22 radar point)", fontsize=9, color=INK, y=0.995)
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig.savefig(OUT / "fig_paths_waypoint_v2.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    main()
