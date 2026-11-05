"""Model-misspecification mixture (reviewer response): rank blocks under
    pi = (1 - eps) p_sat + eps p_broad,   posterior ∝ pi × exp(w·drift_loglik) × (1 − pod)
and report how far the null searches move belief towards "the satellite path model is wrong".

Run (real inputs):
    .venv/bin/python -I scripts/combine_mix_run.py                    # satellite var p (+ p_v2 if present)
    .venv/bin/python -I scripts/combine_mix_run.py --sat-vars p_v2 p  # p_v2 as the headline, p alongside
    .venv/bin/python -I scripts/combine_mix_run.py --sat-vars p_v2    # p_v2 only
The FIRST satellite variable listed is the headline (recommended default). Broad components are
cached in data/derived/combine_broad_components.nc (built on first use; --rebuild-broad to redo).

Outputs (alongside, never overwriting, the satellite-conditional outputs of combine_run.py):
    outputs/combine/RESULTS_mix.md, ranked_blocks_mix.csv, scenario_summary_mix.csv,
    old_blocks_under_mix.csv, fig_mix_vs_old.png, fig_mix_weights.png, run_info_mix.json
    data/derived/combined_posterior_mix.nc
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mh370 import combine, combine_mix, grid, search  # noqa: E402

BOUNDS = {"best": "pod", "low": "pod_low", "high": "pod_high"}
SF = {"best": "searched_frac", "low": "searched_frac_low", "high": "searched_frac_high"}
MAX_SEARCHED_FRAC = 0.10
# prior weights for the fixed-box sweep (component posteriors do not depend on eps, so this is exact and cheap)
EPS_SWEEP = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.125, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
# the four hypotheses of FINDINGS.md section 5 / README, as fixed boxes from ranked_blocks_all.csv
OLD_BLOCKS = [
    ("A", "A: just S of the ATSB limit, on the arc (old rank-1 unsearched, w=0)",
     dict(satcom="p", w=0.0, mode="unsearched")),
    ("B", "B: glide zone beyond the ATSB SE edge (old rank-1 unsearched, w=0.5)",
     dict(satcom="p", w=0.5, mode="unsearched")),
    ("C", "C: ATSB re-search (old rank-1 any ground, w=0.5)",
     dict(satcom="p", w=0.5, mode="any")),
    ("D", "D: equal mode weights candidate (p_equal_modes rank-1 unsearched, w=0.5)",
     dict(satcom="p_equal_modes", w=0.5, mode="unsearched")),
]


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--satcom", default=str(ROOT / "data/derived/satcom_posterior.nc"))
    ap.add_argument("--drift", default=str(ROOT / "data/derived/drift_loglik.nc"))
    ap.add_argument("--pod", default=str(ROOT / "data/derived/search_pod.nc"))
    ap.add_argument("--broad", default=str(combine_mix.BROAD_FILE), help="broad-component cache (built if absent)")
    ap.add_argument("--rebuild-broad", action="store_true")
    ap.add_argument("--broad-draws", type=int, default=8_000_000)
    ap.add_argument("--old-blocks", default=str(ROOT / "outputs/combine/ranked_blocks_all.csv"),
                    help="combine_run.py block table holding the old A-D boxes")
    ap.add_argument("--out", default=str(ROOT / "outputs/combine"))
    ap.add_argument("--posterior-out", default=str(ROOT / "data/derived/combined_posterior_mix.nc"))
    ap.add_argument("--label", default="", help="e.g. SYNTHETIC; stamped on every output")
    ap.add_argument("--sat-vars", nargs="+", default=["auto"],
                    help="satellite variable(s), e.g. p p_v2; 'auto' = p, plus p_v2 if present. First = headline")
    ap.add_argument("--broads", nargs="+", default=list(combine_mix.BROAD_NAMES))
    ap.add_argument("--eps", type=float, nargs="+", default=[0.05, 0.1, 0.2, 0.3])
    ap.add_argument("--weights", type=float, nargs="+", default=[0.0, 0.5, 1.0])
    ap.add_argument("--budgets", type=float, nargs="+", default=[5000.0, 7500.0, 15000.0])
    ap.add_argument("--pod-new", type=float, default=0.9)
    ap.add_argument("--n-boxes", type=int, default=5)
    ap.add_argument("--rec-eps", type=float, default=0.1)
    ap.add_argument("--rec-broad", default="broad_arc")
    ap.add_argument("--rec-w", type=float, default=0.5)
    ap.add_argument("--rec-pod", default="best")
    ap.add_argument("--no-plots", action="store_true")
    return ap.parse_args()


def fmt_lat(x):
    return f"{abs(x):.2f}{'S' if x < 0 else 'N'}"


def nf(x, spec=".3f"):
    """Format a number; NaN -> en dash (quantity not defined for that row)."""
    return "–" if x is None or not np.isfinite(x) else format(x, spec)


def fmt_ll(lat, lon):
    return f"{fmt_lat(lat)} {lon:.2f}E"


def main():
    a = parse()
    t0 = time.time()
    out = Path(a.out)
    tag = f"[{a.label}] " if a.label else ""
    if a.rec_eps not in a.eps:
        a.eps = sorted(a.eps + [a.rec_eps])
    if a.rec_broad not in a.broads:
        a.broads = a.broads + [a.rec_broad]
    sat_ds = combine.open_layer(a.satcom, "satcom", "p")
    if sat_ds is None:
        print(f"satcom input {a.satcom} not present - nothing to combine")
        sys.exit(2)
    if a.sat_vars == ["auto"]:
        sat_vars = ["p"] + (["p_v2"] if "p_v2" in sat_ds else [])
    else:
        sat_vars = a.sat_vars
    missing = [v for v in sat_vars if v not in sat_ds]
    if missing:
        print(f"satellite variable(s) {missing} not in {a.satcom} (has: {list(sat_ds.data_vars)})")
        sys.exit(3)
    out.mkdir(parents=True, exist_ok=True)
    drift_ds = combine.open_layer(a.drift, "drift", "loglik")
    pod_ds = combine.open_layer(a.pod, "search_pod", "pod")
    flags = []
    if drift_ds is None:
        flags.append("drift_loglik.nc absent: only w=0 computed")
    if pod_ds is None:
        flags.append("search_pod.nc absent: NO search subtraction (pod=0) - the mixture weights cannot move")
    weights = a.weights if drift_ds is not None else [0.0]
    drift_ll = drift_ds["loglik"].values.astype(float) if drift_ds is not None else None
    A = grid.cell_area_km2().values
    lat, lon = grid.common_grid()
    af = combine.build_arc_frame()
    if pod_ds is not None:
        pods = {b: pod_ds[v].values.astype(float) for b, v in BOUNDS.items()}
        sfs = {b: (pod_ds[SF[b]].values.astype(float) if SF[b] in pod_ds else pods[b]) for b in BOUNDS}
    else:
        z = np.zeros(A.shape)
        pods = {b: z for b in BOUNDS}
        sfs = {b: z for b in BOUNDS}
    broads, binfo = combine_mix.load_or_build_broad(a.broad, rebuild=a.rebuild_broad, n_draws=a.broad_draws)
    broads = {k: broads[k] for k in a.broads}
    print(f"inputs loaded ({time.time()-t0:.0f}s); satellite vars {sat_vars}; broads {list(broads)}")

    # ---------------------------------------------- old A-D boxes (fixed geometry)
    old_boxes = []
    if Path(a.old_blocks).exists():
        OB = pd.read_csv(a.old_blocks)
        for key, lab, sel in OLD_BLOCKS:
            q = OB[(OB.satcom == sel["satcom"]) & (OB.w == sel["w"]) & (OB["mode"] == sel["mode"])
                   & (OB.pod_bound == "best") & (OB.budget_km2 == 7500) & (OB["rank"] == 1)
                   & (OB.drift.isin(["loglik", "none"])) & (OB.acoustic == "no")]
            if len(q):
                r = q.iloc[0].to_dict()
                r.update(key=key, label=lab, old_mass=r["mass"])
                old_boxes.append(r)
    else:
        flags.append(f"{a.old_blocks} absent: old A-D boxes not evaluated")

    summaries, blocks, old_rows = [], [], []
    keep = {}
    sweep_store = {}
    sf_nodes = {b: combine.to_arc_raster(af, sfs[b] * A, A) for b in BOUNDS}
    pod_nodes = {b: combine.to_arc_raster(af, pods[b] * A, A) for b in BOUNDS}

    for sv in sat_vars:
        p_sat = sat_ds[sv].values.astype(float)
        for w in weights:
            for bound in BOUNDS:
                settings = [("none", 0.0)] + [(bn, e) for bn in broads for e in a.eps]
                for bname, eps in settings:
                    pb = broads[bname] if bname != "none" else next(iter(broads.values()))
                    res = combine_mix.mixture_posterior(p_sat, pb, eps, drift_ll if w > 0 else None, w,
                                                        pods[bound], sfs[bound])
                    sid = f"sat={sv}|broad={bname}|eps={eps:g}|w={w:g}|pod={bound}"
                    node = combine.to_arc_raster(af, res["post"], A)
                    node_s = combine.to_arc_raster(af, res["post_sat"], A)
                    node_b = combine.to_arc_raster(af, res["post_broad"], A)
                    node_pr = combine.to_arc_raster(af, res["prior"], A)
                    sm, ss, sb = res["split_mix"], res["split_sat"], res["split_broad"]
                    row = dict(scenario=sid, sat_var=sv, broad=bname, eps=eps, w=w, pod_bound=bound,
                               eps_after_drift=res["eps_drift"], eps_post=res["eps_post"],
                               p_null_given_sat=res["p_null_sat"], p_null_given_broad=res["p_null_broad"],
                               p_null_mixture=res["p_null_mix"],
                               bf_null_sat_vs_broad=res["bf_null_sat_vs_broad"],
                               bf_drift_sat_vs_broad=res["bf_drift_sat_vs_broad"],
                               p_unsearched_mixture=sm["post_prob_in_unsearched_ground"],
                               p_unsearched_given_sat=ss["post_prob_in_unsearched_ground"],
                               p_unsearched_given_broad=sb["post_prob_in_unsearched_ground"],
                               prior_mass_searched_mixture=sm["prior_mass_in_searched_ground"],
                               prior_mass_searched_given_sat=ss["prior_mass_in_searched_ground"],
                               prior_mass_searched_given_broad=sb["prior_mass_in_searched_ground"],
                               drift_prior_mass_in_nan=res["drift_info"]["mass_in_nan"],
                               post_mass_in_arc_frame=float(node.sum()))
                    if bname == "none":  # reference (old) run: no broad component in play
                        for k_ in ("p_null_given_broad", "bf_null_sat_vs_broad", "bf_drift_sat_vs_broad",
                                   "p_unsearched_given_broad", "prior_mass_searched_given_broad"):
                            row[k_] = np.nan
                    n_boxes = a.n_boxes if bound == "best" else 1
                    for B in a.budgets:
                        for mode, msf in [("any", None), ("unsearched", MAX_SEARCHED_FRAC)]:
                            rows = combine.best_boxes(af, node, B, n_boxes=n_boxes,
                                                      extra=dict(prior_mass=node_pr, mass_sat_cond=node_s,
                                                                 mass_broad_cond=node_b, searched_km2=sf_nodes[bound],
                                                                 pod_km2=pod_nodes[bound]),
                                                      searched=sf_nodes[bound], max_searched_frac=msf)
                            for r, br in enumerate(rows, 1):
                                br = dict(br)
                                br["corners"] = ";".join(f"({x[0]:.3f},{x[1]:.3f})" for x in br["corners"])
                                blocks.append(dict(scenario=sid, sat_var=sv, broad=bname, eps=eps, w=w,
                                                   pod_bound=bound, eps_post=res["eps_post"], mode=mode,
                                                   budget_km2=B, rank=r, p_success=br["mass"] * a.pod_new,
                                                   frac_previously_searched=br.pop("searched_km2") / br["area_km2"],
                                                   mean_prior_pod_in_block=br.pop("pod_km2") / br["area_km2"], **br))
                            sfx = "" if mode == "any" else "_unsearched"
                            if rows:
                                row[f"top{sfx}_{int(B)}_centre"] = fmt_ll(rows[0]["centre_lat"], rows[0]["centre_lon"])
                                row[f"top{sfx}_{int(B)}_mass"] = rows[0]["mass"]
                                row[f"top{sfx}_{int(B)}_mass_sat_cond"] = rows[0]["mass_sat_cond"]
                                row[f"top{sfx}_{int(B)}_p_success"] = rows[0]["mass"] * a.pod_new
                    for ob in old_boxes:
                        m_mix, m_s, m_b = (combine_mix.box_mass(af, x, ob) for x in (node, node_s, node_b))
                        row[f"old{ob['key']}_mass"] = m_mix
                        row[f"old{ob['key']}_mass_sat_cond"] = m_s
                        old_rows.append(dict(scenario=sid, sat_var=sv, broad=bname, eps=eps, w=w, pod_bound=bound,
                                             eps_post=res["eps_post"], block=ob["key"], label=ob["label"],
                                             centre=fmt_ll(ob["centre_lat"], ob["centre_lon"]),
                                             old_w=ob["w"], old_satcom=ob["satcom"], old_reported_mass=ob["old_mass"],
                                             mass_mixture=m_mix, mass_given_sat=m_s,
                                             mass_given_broad=m_b if bname != "none" else np.nan,
                                             p_success_mixture=m_mix * a.pod_new,
                                             shrink_factor=m_mix / m_s if m_s > 1e-4 else np.nan))
                    summaries.append(row)
                    if bname == a.rec_broad and eps == a.rec_eps and bound == a.rec_pod:
                        sweep_store[(sv, w)] = dict(node_s=node_s, node_b=node_b,
                                                    r=1.0 / (res["bf_drift_sat_vs_broad"] * res["bf_null_sat_vs_broad"]))
                    if sv == sat_vars[0] and bound == a.rec_pod and (bname == a.rec_broad or bname == "none" or
                                                                    (eps == a.rec_eps and w == a.rec_w)):
                        keep[sid] = res
            print(f"  {sv} w={w:g} done ({time.time()-t0:.0f}s)")

    S = pd.DataFrame(summaries)
    Bk = pd.DataFrame(blocks)
    if not Bk.empty:  # reference rows have no broad component in play
        Bk.loc[Bk.broad == "none", "mass_broad_cond"] = np.nan
    O = pd.DataFrame(old_rows)
    S.to_csv(out / "scenario_summary_mix.csv", index=False, float_format="%.5g")
    Bk.to_csv(out / "ranked_blocks_mix.csv", index=False, float_format="%.5g")
    if not O.empty:
        O.to_csv(out / "old_blocks_under_mix.csv", index=False, float_format="%.5g")

    rec = f"sat={sat_vars[0]}|broad={a.rec_broad}|eps={a.rec_eps:g}|w={a.rec_w:g}|pod={a.rec_pod}"
    ref = f"sat={sat_vars[0]}|broad=none|eps=0|w={a.rec_w:g}|pod={a.rec_pod}"
    Sw = eps_sweep(af, Bk, old_boxes, sweep_store, rec, a)
    if not Sw.empty:
        Sw.to_csv(out / "eps_sweep_mix.csv", index=False, float_format="%.5g")
    # ---------------------------------------------- posterior file
    ds = xr.Dataset(coords={"lat": lat, "lon": lon})
    if rec in keep:
        r = keep[rec]
        for nm, arr, ln in [("post_mix", r["post"], "MIXTURE posterior (recommended default): marginal over 'satellite "
                             "model right' / 'model wrong'"),
                            ("prior_mix", r["prior"], "mixture after drift evidence, before search subtraction"),
                            ("post_sat_cond", r["post_sat"], "posterior CONDITIONAL on the satellite model (= old ranking)"),
                            ("post_broad_cond", r["post_broad"], "posterior conditional on the broad component")]:
            ds[nm] = (("lat", "lon"), arr.astype(np.float32))
            ds[nm].attrs.update(long_name=ln, scenario=rec)
        ds.attrs.update(rec_eps_prior=a.rec_eps, rec_eps_after_drift=r["eps_drift"], rec_eps_post=r["eps_post"])
    for sid, r in keep.items():
        parts = dict(x.split("=") for x in sid.split("|"))
        if parts["broad"] == "none":
            continue
        nm = f"post_mix_{parts['broad']}_eps{parts['eps'].replace('.', 'p')}_w{parts['w'].replace('.', 'p')}"
        ds[nm] = (("lat", "lon"), r["post"].astype(np.float32))
        ds[nm].attrs.update(scenario=sid, eps_post=r["eps_post"])
    for bn, arr in broads.items():
        ds[f"p_{bn}"] = (("lat", "lon"), arr.astype(np.float32))
        ds[f"p_{bn}"].attrs["long_name"] = f"broad 'model is wrong' prior component {bn} (before any evidence)"
    ds.attrs.update(title=f"{tag}MH370 combined posterior, model-misspecification mixture",
                    formula="post ∝ ((1-eps) p_sat + eps p_broad) × exp(w·drift_loglik) × (1 − pod)",
                    label=a.label or "REAL INPUTS", satcom=a.satcom, sat_var=sat_vars[0], drift=a.drift, pod=a.pod,
                    recommended=rec, created=time.strftime("%Y-%m-%d %H:%M"))
    grid.save(ds, a.posterior_out)

    info = dict(label=a.label or "REAL INPUTS", flags=flags, created=time.strftime("%Y-%m-%d %H:%M"),
                inputs={k: dict(path=v, present=Path(v).exists(),
                                mtime=time.ctime(Path(v).stat().st_mtime) if Path(v).exists() else None)
                        for k, v in dict(satcom=a.satcom, drift=a.drift, pod=a.pod, broad=a.broad,
                                         old_blocks=a.old_blocks).items()},
                sat_vars=sat_vars, sat_vars_available=[v for v in sat_ds.data_vars if v in ("p", "p_v2")],
                broads=list(broads), broad_build=binfo, eps=a.eps, weights=weights, budgets=a.budgets,
                pod_new=a.pod_new, recommended=rec, reference=ref, runtime_s=round(time.time() - t0))
    (out / "run_info_mix.json").write_text(json.dumps(info, indent=1))
    write_results(out, S, Bk, O, Sw, a, tag, flags, info, sat_vars, rec, ref, old_boxes)
    if not a.no_plots:
        make_plots(out, keep, Bk, S, O, Sw, a, tag, af, sat_vars, rec, ref, old_boxes)
    print(f"done in {time.time()-t0:.0f}s -> {out}")


def eps_sweep(af, Bk, old_boxes, store, rec, a):
    """Captured probability of FIXED boxes (the recommended top-3 unsearched blocks and the old A-D)
    as a function of the prior weight eps, for the recommended broad component and POD bound.
    eps_post = eps r / ((1 - eps) + eps r), r = Z_b N_b / (Z_s N_s) = 1 / (BF_drift BF_null)."""
    Bm = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]
    boxes = [(f"U{int(r['rank'])}", r) for _, r in
             Bk[(Bk.scenario == rec) & (Bk["mode"] == "unsearched") & (Bk.budget_km2 == Bm) & (Bk["rank"] <= 3)].iterrows()]
    boxes += [(ob["key"], ob) for ob in old_boxes]
    rows = []
    for (sv, w), st in store.items():
        for key, bx in boxes:
            ms, mb = combine_mix.box_mass(af, st["node_s"], bx), combine_mix.box_mass(af, st["node_b"], bx)
            for e in EPS_SWEEP:
                ep = e * st["r"] / ((1 - e) + e * st["r"])
                rows.append(dict(sat_var=sv, broad=a.rec_broad, w=w, pod_bound=a.rec_pod, box=key,
                                 centre=fmt_ll(bx["centre_lat"], bx["centre_lon"]), eps=e, eps_post=ep,
                                 mass_given_sat=ms, mass_given_broad=mb, mass_mixture=(1 - ep) * ms + ep * mb))
    return pd.DataFrame(rows)


def crossover_eps(Sw, sv, w, k1, k2):
    """Text describing how the mixture ranking of fixed boxes k1 vs k2 depends on the prior eps."""
    q = Sw[(Sw.sat_var == sv) & (Sw.w == w)]
    a1, a2 = q[q.box == k1], q[q.box == k2]
    if a1.empty or a2.empty:
        return ""
    s1, b1 = a1.mass_given_sat.iloc[0], a1.mass_given_broad.iloc[0]
    s2, b2 = a2.mass_given_sat.iloc[0], a2.mass_given_broad.iloc[0]
    d0, d1 = s1 - s2, b1 - b2          # k1 minus k2 at eps_post = 0 and at eps_post = 1
    if d0 >= 0 and d1 >= 0:
        return f"{k1} ≥ {k2} for every ε"
    if d0 <= 0 and d1 <= 0:
        return f"{k1} < {k2} for every ε"
    ep = d0 / (d0 - d1)                 # posterior weight at which the two boxes tie
    r1 = q[q.box == k1].iloc[1]          # odds ratio r from the eps = 0.01 row
    r = r1.eps_post * (1 - r1.eps) / (r1.eps * (1 - r1.eps_post))
    e = ep / (r * (1 - ep) + ep)
    return (f"{k1} overtakes {k2} for prior ε > {e:.3f}" if d0 < 0 else f"{k1} beats {k2} only for prior ε < {e:.3f}") \
        + f" (posterior weight {ep:.2f})"


# ------------------------------------------------------------------------------------------------
# RESULTS_mix.md
# ------------------------------------------------------------------------------------------------
def md_blocks(t, pod_new):
    L = ["| budget km² | rank | centre | lat range | lon range | n from arc (km) | area km² | **captured prob. (mixture)** | "
         f"**P(success) @POD {pod_new:.2f} (mixture)** | captured prob. if sat. model right | if broad | previously searched |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        L.append(f"| {r.budget_km2:,.0f} | {r['rank']} | {fmt_ll(r.centre_lat, r.centre_lon)} | "
                 f"{fmt_lat(r.lat_max)}-{fmt_lat(r.lat_min)} | {r.lon_min:.2f}-{r.lon_max:.2f}E | "
                 f"{r.n0_km:+.0f} to {r.n1_km:+.0f} | {r.area_km2:,.0f} | **{r.mass:.4f}** | **{r.p_success:.4f}** | "
                 f"{r.mass_sat_cond:.4f} | {nf(r.mass_broad_cond, '.4f')} | {100*r.frac_previously_searched:.0f}% |")
    return "\n".join(L) + "\n"


def write_results(out, S, Bk, O, Sw, a, tag, flags, info, sat_vars, rec, ref, old_boxes):
    L = [f"# {tag}Model-misspecification mixture: combined posterior and ranked blocks\n"]
    if a.label:
        L.append(f"> **{a.label} INPUTS - these numbers are NOT results about MH370.**\n")
    L.append(f"Generated {info['created']} by `scripts/combine_mix_run.py` (method: `src/mh370/combine_mix.py`, "
             "`outputs/combine/README.md` section 'Model-misspecification mixture'). Inputs:\n")
    for k, v in info["inputs"].items():
        L.append(f"- {k}: `{Path(v['path']).name}` present={v['present']} (modified {v['mtime']})")
    if flags:
        L.append("\nFlags:\n" + "\n".join(f"- {x}" for x in flags))
    L.append(f"- satellite variable(s) run: {', '.join('`'+v+'`' for v in sat_vars)} (headline `{sat_vars[0]}`); "
             f"available in the satcom file: {info['sat_vars_available']}")
    bb = info["broad_build"]
    sg = bb.get("start_geometry", {})
    L.append(f"""
```
prior      pi = (1 − ε)·p_sat + ε·p_broad
posterior  ∝ pi × exp(w·drift_loglik) × (1 − pod)
```

**How to read the figures**
- **Conditional on the satellite model** (marked *if sat. model right* / *given sat*): what `combine_run.py` reports
  (`RESULTS.md`). These hold only if the satellite path model is right. ε = 0 rows reproduce them.
- **Mixture** (bold; *mixture*): marginal over "satellite model right" and "satellite model wrong" (broad component),
  after the drift evidence and the null searches have re-weighted the two. These are the figures to plan with,
  **conditional on the mixture assumptions** (the form of the broad component and the prior weight ε).

**Broad components** (cached in `{Path(info['inputs']['broad']['path']).name}`; {bb.get('n_draws', 0):,} Monte-Carlo draws each)
- `broad_arc`: 7th-arc crossing uniform in sea-level-arc latitude {bb.get('lat_range')}, then the satcom default
  end-of-flight kernel (0.8 uncontrolled: +5 NM along track, sd 7 NM; 0.2 glide: 0-120 NM, direction sd 15°). Start
  geometry at 00:19:29 pooled over all five autopilot modes with equal weight: cross-arc offset 5/50/95 % =
  {sg.get('n0_km_5_50_95')} km, final track minus outward arc normal = {sg.get('theta_deg_5_50_95')}°.
- `broad_wide`: same crossing latitudes, cross-arc offset uniform in ±{bb.get('wide_half_km')} km of the sea-level arc.
- `broad_arc_lnavctt` (sensitivity): as `broad_arc`, but the start geometry is pooled over LNAV and CTT only (the modes
  that carry the satellite layer's weight): offset {bb.get('start_geometry_lnavctt', {}).get('n0_km_5_50_95')} km,
  angle {bb.get('start_geometry_lnavctt', {}).get('theta_deg_5_50_95')}°, i.e. closer to the arc.
- Mass inside the common grid before renormalisation: {bb.get('mass_inside_grid_before_renorm')}.
""")
    # ---- weights table
    for sv in sat_vars:
        L.append(f"\n## 1. How far the evidence moves belief towards 'model is wrong' (satellite `{sv}`)\n")
        L.append("ε = prior weight of the broad component; ε_drift after the drift evidence; **ε_post** after the null "
                 "searches as well. BF = Bayes factor *satellite model : broad*; BF < 1 favours 'model is wrong'. "
                 "P(null | ·) = probability that every past search misses, given the component (after drift).\n")
        for bound in ["best", "low", "high"]:
            t = S[(S.sat_var == sv) & (S.pod_bound == bound)].sort_values(["broad", "w", "eps"])
            if t.empty:
                continue
            L.append(f"\n**POD {bound}**\n")
            L.append("| broad | w | ε prior | ε after drift | **ε posterior** | P(null \\| sat) | P(null \\| broad) | "
                     "BF null (sat:broad) | BF drift (sat:broad) | P(unsearched \\| sat) | P(unsearched \\| broad) | "
                     "**P(unsearched), mixture** |")
            L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
            for _, r in t.iterrows():
                bl = r.broad if r.broad != "none" else "none (ε = 0: old, conditional)"
                L.append(f"| {bl} | {r.w:g} | {r.eps:g} | {r.eps_after_drift:.3f} | **{r.eps_post:.3f}** | "
                         f"{r.p_null_given_sat:.3f} | {nf(r.p_null_given_broad)} | {nf(r.bf_null_sat_vs_broad, '.3g')} | "
                         f"{nf(r.bf_drift_sat_vs_broad, '.3g')} | {r.p_unsearched_given_sat:.3f} | "
                         f"{nf(r.p_unsearched_given_broad)} | **{r.p_unsearched_mixture:.3f}** |")
    # ---- recommended default blocks
    rr = S[S.scenario == rec]
    L.append(f"\n## 2. Recommended default: `{rec}`\n")
    if len(rr):
        r = rr.iloc[0]
        L.append(f"Broad weight ε: prior {r.eps:g} → after drift {r.eps_after_drift:.3f} → **after the null searches "
                 f"{r.eps_post:.3f}**. P(wreck in unsearched ground): **{r.p_unsearched_mixture:.3f} (mixture)**; "
                 f"{r.p_unsearched_given_sat:.3f} if the satellite model is right; {r.p_unsearched_given_broad:.3f} "
                 f"under the broad component.\n")
    for mode, title in [("unsearched", f"essentially unsearched ground (≤ {MAX_SEARCHED_FRAC:.0%} previously searched)"),
                        ("any", "any ground (re-search allowed; posterior already discounts it by 1 − POD)")]:
        for B in a.budgets:
            t = Bk[(Bk.scenario == rec) & (Bk["mode"] == mode) & (Bk.budget_km2 == B)]
            if t.empty:
                continue
            L.append(f"\n### {B:,.0f} km², {title}\n")
            L.append(md_blocks(t, a.pod_new))
    L.append("n > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. Corners in "
             "`ranked_blocks_mix.csv`.\n")
    # ---- old ranking for comparison
    L.append(f"\n## 3. Old ranking (ε = 0, conditional on the satellite model) at the same w and POD: `{ref}`\n")
    L.append("With ε = 0 the 'mixture' columns equal the conditional figures.\n")
    for B in a.budgets:
        t = Bk[(Bk.scenario == ref) & (Bk["mode"] == "unsearched") & (Bk.budget_km2 == B) & (Bk["rank"] <= 3)]
        if len(t):
            L.append(f"\n**{B:,.0f} km², unsearched**\n")
            L.append(md_blocks(t, a.pod_new))
    # ---- old A-D under mixture
    if not O.empty:
        L.append("\n## 4. The old hypotheses A-D under the mixture (fixed 7,500 km² boxes from `ranked_blocks_all.csv`)\n")
        L.append("'captured if sat. right' is the old (conditional) figure at that w; 'mixture' is the same box under the "
                 "mixture posterior. Shrink = mixture / conditional.\n")
        for ob in old_boxes:
            L.append(f"- **{ob['label']}**: centre {fmt_ll(ob['centre_lat'], ob['centre_lon'])}, "
                     f"{fmt_lat(ob['lat_max'])}-{fmt_lat(ob['lat_min'])} / {ob['lon_min']:.2f}-{ob['lon_max']:.2f}E, "
                     f"n {ob['n0_km']:+.0f} to {ob['n1_km']:+.0f} km; old reported mass {ob['old_mass']:.3f} "
                     f"(satellite `{ob['satcom']}`, w={ob['w']:g})")
        for sv in sat_vars:
            for bname in [b for b in O.broad.unique() if b != "none"]:
                t = O[(O.sat_var == sv) & (O.broad == bname) & (O.pod_bound == "best")]
                if t.empty:
                    continue
                L.append(f"\n**satellite `{sv}`, {bname}, POD best**\n")
                L.append("| block | w | ε prior | ε post | captured if sat. right | captured if broad | **captured, mixture** | "
                         "**P(success) @0.9, mixture** | shrink |")
                L.append("|---|---|---|---|---|---|---|---|---|")
                for _, r in t.sort_values(["block", "w", "eps"]).iterrows():
                    L.append(f"| {r.block} | {r.w:g} | {r.eps:g} | {r.eps_post:.3f} | {r.mass_given_sat:.4f} | "
                             f"{nf(r.mass_given_broad, '.4f')} | **{r.mass_mixture:.4f}** | **{r.p_success_mixture:.4f}** | "
                             f"{nf(r.shrink_factor, '.2f')} |")
    # ---- eps sweep for fixed boxes
    Bm = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]
    if not Sw.empty:
        L.append(f"\n## 4b. Sensitivity to the prior weight ε (fixed boxes, {a.rec_broad}, POD {a.rec_pod})\n")
        L.append(f"Boxes: U1-U3 = recommended top-3 unsearched {Bm:,.0f} km² blocks; A-D = old hypotheses. "
                 "Captured probability under the mixture (the boxes are held fixed; the optimal box at another ε "
                 "can differ slightly - see section 5 for re-optimised blocks).\n")
        for sv in sat_vars:
            for w in sorted(Sw[Sw.sat_var == sv].w.unique()):
                q = Sw[(Sw.sat_var == sv) & (Sw.w == w)]
                keys = list(dict.fromkeys(q.box))
                L.append(f"\n**satellite `{sv}`, w = {w:g}**\n")
                L.append("| ε prior | ε post | " + " | ".join(f"{k} ({q[q.box == k].centre.iloc[0]})" for k in keys) + " |")
                L.append("|---|---|" + "---|" * len(keys))
                for e in EPS_SWEEP:
                    qq = q[np.isclose(q.eps, e)]
                    L.append(f"| {e:g} | {qq.eps_post.iloc[0]:.3f} | " + " | ".join(
                        f"{qq[qq.box == k].mass_mixture.iloc[0]:.4f}" for k in keys) + " |")
                xs = [crossover_eps(Sw, sv, w, "U1", k2) for k2 in keys if k2 in ("A", "B", "C")]
                xs = [x for x in xs if x]
                if xs:
                    L.append("\nCrossovers (fixed boxes): " + "; ".join(xs) + ".\n")
    # ---- rank-1 across all settings
    for sv in sat_vars:
        L.append(f"\n## 5. Rank-1 blocks in every setting (satellite `{sv}`), {Bm:,.0f} km²\n")
        L.append("| broad | ε | w | POD | ε post | top unsearched block | **mixture mass** | if sat. right | "
                 "top block, any ground | **mixture mass** | P(unsearched), mixture |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|")
        t = S[S.sat_var == sv].sort_values(["broad", "eps", "w", "pod_bound"])
        for _, r in t.iterrows():
            L.append(f"| {r.broad} | {r.eps:g} | {r.w:g} | {r.pod_bound} | {r.eps_post:.3f} | "
                     f"{r.get(f'top_unsearched_{int(Bm)}_centre', '')} | **{r.get(f'top_unsearched_{int(Bm)}_mass', np.nan):.4f}** | "
                     f"{r.get(f'top_unsearched_{int(Bm)}_mass_sat_cond', np.nan):.4f} | "
                     f"{r.get(f'top_{int(Bm)}_centre', '')} | **{r.get(f'top_{int(Bm)}_mass', np.nan):.4f}** | "
                     f"{r.p_unsearched_mixture:.3f} |")
    (out / "RESULTS_mix.md").write_text("\n".join(L) + "\n")


# ------------------------------------------------------------------------------------------------
# figures
# ------------------------------------------------------------------------------------------------
def make_plots(out, keep, Bk, S, O, Sw, a, tag, af, sat_vars, rec, ref, old_boxes):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from matplotlib.lines import Line2D
    from mh370 import geo
    INK, INK2, MUTED, GRIDC = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1"
    C_OLD, C_MIX, C_BROAD = "#2a78d6", "#eb6834", "#1baf7a"
    lat, lon = grid.common_grid()
    A = grid.cell_area_km2().values
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-44.0, -15.0, 0.05))
    items = None
    sf_contour = None
    if a.label:
        try:
            sf_contour = xr.open_dataset(a.pod, engine="h5netcdf")["searched_frac"].values
        except Exception:  # noqa: BLE001
            pass
    else:
        try:
            items = search.build_items()
        except Exception:  # noqa: BLE001
            pass
    Bm = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]
    make_weights_figure(out, S, Sw, a, tag, sat_vars)
    if rec not in keep or ref not in keep:
        return
    post_old, post_mix = keep[ref]["post"], keep[rec]["post"]
    d_old, d_mix = post_old / A, post_mix / A
    vmax = np.nanpercentile(d_old[d_old > 0], 99.9)
    norm = LogNorm(vmin=vmax * 1e-4, vmax=vmax)
    ext = (78.0, 110.0, -44.0, -17.0)
    cmap = search.seq_cmap()

    fig = plt.figure(figsize=(15.5, 12.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.55, 1.0], hspace=0.22, wspace=0.08)
    ax_maps = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])]
    titles = [f"{tag}OLD: conditional on the satellite model (ε = 0)\nsatellite `{sat_vars[0]}`, w = {a.rec_w:g}, POD {a.rec_pod}",
              f"{tag}MIXTURE: ε = {a.rec_eps:g} {a.rec_broad} → posterior ε = {keep[rec]['eps_post']:.2f}\n"
              f"satellite `{sat_vars[0]}`, w = {a.rec_w:g}, POD {a.rec_pod}"]
    for ax, dens, sid, ttl in zip(ax_maps, [d_old, d_mix], [ref, rec], titles):
        search.basemap(ax, ext)
        m = np.ma.masked_less_equal(dens, norm.vmin)
        im = ax.pcolormesh(lon, lat, m, cmap=cmap, norm=norm, shading="nearest", zorder=2)
        if items is not None:
            for c in search.CAMPAIGNS:
                search.fill_geom(ax, search.campaign_union(items, c, "best"), "none", lw=0.5, edge=search.CAMPAIGN_COLOR[c])
        elif sf_contour is not None:
            ax.contour(lon, lat, sf_contour, levels=[0.5], colors=["#eb6834"], linewidths=0.8, zorder=6)
        ax.plot(arc[:, 1], arc[:, 0], color=INK, lw=0.7, zorder=5)
        for ob in old_boxes:  # old hypotheses: grey outlines + letter
            xy = combine.box_outline(ob)
            ax.plot(xy[:, 0], xy[:, 1], color=INK2, lw=0.9, ls=":", zorder=7)
            ax.text(ob["centre_lon"] - 1.1, ob["centre_lat"], ob["key"], fontsize=8, color=INK2, ha="center",
                    va="center", zorder=8, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.8))
        t = Bk[(Bk.scenario == sid) & (Bk.budget_km2 == Bm) & (Bk["rank"] <= 3)]
        for mode, ls, pre in [("any", "-", ""), ("unsearched", "--", "U")]:
            for _, r in t[t["mode"] == mode].iterrows():
                xy = combine.box_outline(r)
                ax.plot(xy[:, 0], xy[:, 1], color=INK, lw=1.5 if r["rank"] == 1 else 0.9, ls=ls, zorder=7)
                ax.text(r.centre_lon + 1.1, r.centre_lat, f"{pre}{int(r['rank'])}", fontsize=8, ha="center",
                        va="center", color=INK, zorder=8,
                        bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
        ax.set_title(ttl, fontsize=10, loc="left")
    cb = fig.colorbar(im, ax=ax_maps, shrink=0.8, pad=0.01)
    cb.set_label("posterior density per km² (log scale, same for both maps)")

    # arc profile
    ax = fig.add_subplot(gs[1, :])
    la_c, h_old = combine.arc_latitude_profile(af, post_old)
    _, h_mix = combine.arc_latitude_profile(af, post_mix)
    _, h_br = combine.arc_latitude_profile(af, keep[rec]["eps_post"] * keep[rec]["post_broad"])
    _, h_pr = combine.arc_latitude_profile(af, keep[rec]["prior"])
    sel = (la_c >= -44) & (la_c <= -16)
    floor = 1e-7
    ax.plot(la_c[sel], np.maximum(h_old[sel], floor), color=C_OLD, lw=2, label="old posterior (satellite model assumed right)")
    ax.plot(la_c[sel], np.maximum(h_mix[sel], floor), color=C_MIX, lw=2, label="mixture posterior")
    ax.plot(la_c[sel], np.maximum(h_br[sel], floor), color=C_BROAD, lw=1.5,
            label=f"…of which the broad ('model wrong') part, ε_post = {keep[rec]['eps_post']:.2f}")
    ax.plot(la_c[sel], np.maximum(h_pr[sel], floor), color=INK2, lw=1.1, ls=":", label="mixture before search subtraction")
    ax.set_yscale("log")
    ax.set_ylim(1e-6, max(h_old.max(), h_mix.max()) * 2)
    ax.set_xlim(-44, -17)
    la_arc, _, s_arc = search.arc_dense()
    o = np.argsort(s_arc)
    t = Bk[(Bk.scenario == rec) & (Bk.budget_km2 == Bm) & (Bk["mode"] == "unsearched") & (Bk["rank"] <= 3)]
    ytop = ax.get_ylim()[1]
    for _, r in t.iterrows():  # new blocks: shaded spans, labelled at the bottom
        lo_, hi_ = sorted(np.interp([r.s0_km, r.s1_km], s_arc[o], la_arc[o]))
        ax.axvspan(lo_, hi_, color=C_MIX, alpha=0.12, lw=0)
        ax.text((lo_ + hi_) / 2 + (0.35 if r["rank"] == 3 else 0.0), 1.5e-6, f"U{int(r['rank'])}", ha="center",
                va="bottom", fontsize=8, color=INK)
    for ob in old_boxes:  # old hypotheses: bars at the top
        lo_, hi_ = sorted(np.interp([ob["s0_km"], ob["s1_km"]], s_arc[o], la_arc[o]))
        yb = ytop / (2.2 if ob["key"] in ("A", "C") else 4.5)
        ax.plot([lo_, hi_], [yb] * 2, color=INK2, lw=2.5, solid_capstyle="butt")
        ax.text(hi_ + 0.12, yb, ob["key"], ha="left", va="center", fontsize=8, color=INK2)
    ax.set_xlabel("latitude of nearest point on the sea-level 7th arc")
    ax.set_ylabel("probability per 0.05° of arc latitude (log)")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.grid(axis="y", color=GRIDC, lw=0.6)
    ax.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax.set_title(f"{tag}Marginal along the 7th arc. Shaded: top-3 mixture blocks on unsearched ground ({Bm:,.0f} km²); "
                 "grey bars: old hypotheses A-D", fontsize=10, loc="left")
    fig.text(0.01, 0.005, f"{tag}Map boxes: {Bm:,.0f} km² arc-aligned blocks; solid 1-3 = any ground, dashed U1-U3 = "
             f"essentially unsearched (≤ {MAX_SEARCHED_FRAC:.0%} previously searched); dotted A-D = old hypotheses. "
             + ("Outlines: searched areas (blue ATSB, orange OI 2018, green OI 2025-26 assumed)." if items is not None
                else "Orange contour: searched area of the supplied POD file."), fontsize=8, color=INK2)
    fig.savefig(out / "fig_mix_vs_old.png", dpi=125, bbox_inches="tight")
    plt.close(fig)



def make_weights_figure(out, S, Sw, a, tag, sat_vars):
    """Posterior broad weight vs prior eps, and fixed-box captured probability vs eps (needs only the
    summary and sweep tables)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    INK2, MUTED, GRIDC = "#52514e", "#8a8984", "#e6e5e1"
    Bm = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]
    sv = sat_vars[0]
    wcol = {0.0: "#9ec5f4", 0.5: "#3987e5", 1.0: "#0d366b"}
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    ax = axs[0]
    eps_all = sorted(S[S.broad != "none"].eps.unique())
    ax.plot([0, max(eps_all)], [0, max(eps_all)], color=MUTED, lw=0.8, ls="-")
    ax.text(max(eps_all) * 0.97, max(eps_all) * 0.90, "no update (posterior = prior)", color=MUTED, fontsize=8,
            ha="right", va="top")
    for bname, ls, mk in [("broad_arc", "-", "o"), ("broad_wide", "--", "s"), ("broad_arc_lnavctt", ":", "^")]:
        for w, c in wcol.items():
            q = {b: S[(S.sat_var == sv) & (S.broad == bname) & (S.w == w) & (S.pod_bound == b)].sort_values("eps")
                 for b in ("best", "low", "high")}
            if q["best"].empty:
                continue
            ax.plot(q["best"].eps, q["best"].eps_post, ls=ls, marker=mk, ms=6, color=c, lw=2, mec="white", mew=0.8)
            lo_ = np.minimum(q["low"].eps_post.values, q["high"].eps_post.values)
            hi_ = np.maximum(q["low"].eps_post.values, q["high"].eps_post.values)
            ax.vlines(q["best"].eps + {"broad_wide": 0.004, "broad_arc_lnavctt": -0.004}.get(bname, 0.0), lo_, hi_,
                      color=c, lw=1)
            if bname == "broad_arc":
                ax.text(q["best"].eps.values[-1] + 0.01, q["best"].eps_post.values[-1], f"w={w:g}", fontsize=7.5,
                        color=INK2, va="center")
    ax.set_xlabel("prior weight ε of the broad 'model is wrong' component")
    ax.set_ylabel("posterior weight after drift + null searches")
    ax.set_xlim(0, max(eps_all) * 1.45)
    ax.set_ylim(0, 1)
    h = [Line2D([], [], color=c, lw=2, label=f"w = {w:g}") for w, c in wcol.items()]
    h += [Line2D([], [], color=INK2, ls="-", marker="o", label="broad_arc"),
          Line2D([], [], color=INK2, ls="--", marker="s", label="broad_wide"),
          Line2D([], [], color=INK2, ls=":", marker="^", label="broad_arc_lnavctt")]
    ax.legend(handles=h, fontsize=8, frameon=True, framealpha=0.95, edgecolor="none", loc="lower right")
    ax.set_title(f"{tag}How far the evidence moves belief towards 'model is wrong'\n(satellite `{sv}`; "
                 "markers POD best, bars POD low-high)", fontsize=10, loc="left")
    ax = axs[1]
    q = Sw[(Sw.sat_var == sv) & (Sw.w == a.rec_w)] if not Sw.empty else Sw
    if not q.empty:
        # categorical slots in fixed order: U1 (new rank-1), B, A, C
        series = [("U1", "#eb6834", "-"), ("B", "#2a78d6", "-"), ("A", "#1baf7a", "-"), ("C", "#eda100", "--")]
        for key, c, ls in series:
            qq = q[q.box == key].sort_values("eps")
            if qq.empty:
                continue
            lab = {"U1": "U1 new rank-1 unsearched", "B": "B (old, glide zone)", "A": "A (old, S of ATSB limit)",
                   "C": "C (old, ATSB re-search)"}[key]
            ax.plot(qq.eps, qq.mass_mixture, color=c, lw=2, ls=ls, label=f"{lab}, {qq.centre.iloc[0]}")
        ax.axvline(a.rec_eps, color=MUTED, lw=0.8, ls=":")
        ax.text(a.rec_eps + 0.004, ax.get_ylim()[1] * 0.97, f"recommended ε = {a.rec_eps:g}", fontsize=7.5,
                color=INK2, va="top")
        ax.set_xlim(0, max(EPS_SWEEP))
        ax.set_ylim(0, None)
        ax.legend(fontsize=8, frameon=False, loc="upper right")
        ax.set_xlabel("prior weight ε of the broad component")
        ax.set_ylabel(f"captured probability of the fixed {Bm:,.0f} km² box (mixture)")
        ax.set_title(f"{tag}Fixed boxes under the mixture ({a.rec_broad}, w = {a.rec_w:g}, POD {a.rec_pod}); "
                     "ε = 0 is the old figure", fontsize=10, loc="left")
    for ax in axs:
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(color=GRIDC, lw=0.6)
    fig.tight_layout()
    fig.savefig(out / "fig_mix_weights.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
