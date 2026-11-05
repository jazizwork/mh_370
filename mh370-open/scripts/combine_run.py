"""Combine satcom x drift x (acoustic) x (1 - search POD) and rank unsearched blocks.

Run (real inputs):   .venv/bin/python -I scripts/combine_run.py
Self-test inputs:    see scripts/combine_selftest.py (passes --label SYNTHETIC and its own paths)

Missing inputs are handled: no satcom -> exit 2; no drift -> w=0 only (flagged); no pod ->
no search subtraction (flagged); acoustic optional (adds a with-acoustic scenario set).
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
from mh370 import combine, grid, search  # noqa: E402

BOUNDS = {"best": "pod", "low": "pod_low", "high": "pod_high"}
MAX_SEARCHED_FRAC = 0.10  # "unsearched" ranking: blocks with <= 10% previously searched area
SF = {"best": "searched_frac", "low": "searched_frac_low", "high": "searched_frac_high"}


def parse():
    ap = argparse.ArgumentParser()
    ap.add_argument("--satcom", default=str(ROOT / "data/derived/satcom_posterior.nc"))
    ap.add_argument("--drift", default=str(ROOT / "data/derived/drift_loglik.nc"))
    ap.add_argument("--acoustic", default=str(ROOT / "data/derived/acoustic_loglik.nc"))
    ap.add_argument("--pod", default=str(ROOT / "data/derived/search_pod.nc"))
    ap.add_argument("--out", default=str(ROOT / "outputs/combine"))
    ap.add_argument("--posterior-out", default=str(ROOT / "data/derived/combined_posterior.nc"))
    ap.add_argument("--label", default="", help="e.g. SYNTHETIC; stamped on every output")
    ap.add_argument("--budgets", type=float, nargs="+", default=[5000.0, 7500.0, 15000.0])
    ap.add_argument("--weights", type=float, nargs="+", default=[0.0, 0.5, 1.0])
    ap.add_argument("--pod-new", type=float, default=0.9)
    ap.add_argument("--n-boxes", type=int, default=5)
    ap.add_argument("--headline-satcom", default="p")
    ap.add_argument("--headline-w", type=float, default=0.5)
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--no-drift-sensitivity", action="store_true")
    return ap.parse_args()


def fmt_lat(x):
    return f"{abs(x):.2f}{'S' if x < 0 else 'N'}"


def fmt_lon(x):
    return f"{x:.2f}E"


def main():
    a = parse()
    t0 = time.time()
    out = Path(a.out)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    tag = f"[{a.label}] " if a.label else ""
    sat_ds = combine.open_layer(a.satcom, "satcom", "p")
    if sat_ds is None:
        print(f"satcom input {a.satcom} not present - nothing to combine")
        sys.exit(2)
    drift_ds = combine.open_layer(a.drift, "drift", "loglik")
    ac_ds = combine.open_layer(a.acoustic, "acoustic", "loglik")
    pod_ds = combine.open_layer(a.pod, "search_pod", "pod")
    flags = []
    if drift_ds is None:
        flags.append("drift_loglik.nc absent: only w=0 (satcom x search) computed")
    if pod_ds is None:
        flags.append("search_pod.nc absent: NO search subtraction (pod=0)")
    if ac_ds is None:
        flags.append("acoustic_loglik.nc absent: acoustic layer not used")
    sats = combine.satcom_scenarios(sat_ds)
    drifts = combine.loglik_variants(drift_ds)
    weights = a.weights if drift_ds is not None else [0.0]
    A = grid.cell_area_km2().values
    lat, lon = grid.common_grid()
    af = combine.build_arc_frame()
    if pod_ds is not None:
        pods = {b: pod_ds[v].values.astype(float) for b, v in BOUNDS.items()}
        sfs = {b: (pod_ds[SF[b]].values.astype(float) if SF[b] in pod_ds else pods[b]) for b in BOUNDS}
    else:
        z = np.zeros(A.shape)
        pods = {"best": z, "low": z, "high": z}
        sfs = {"best": z, "low": z, "high": z}
    ac_ll = ac_ds["loglik"].values.astype(float) if ac_ds is not None else None

    summaries, blocks = [], []
    NAMED = {k: combine.polygon_cell_fraction(g) for k, g in combine.named_areas().items()}
    keep = {}  # posteriors to save

    def run_one(sat_name, drift_name, w, bound, acoustic, n_boxes, save=False):
        res = combine.combine(sats[sat_name], drifts.get(drift_name) if w > 0 else None, w,
                              pods[bound], ac_ll if acoustic else None, 1.0)
        split = combine.search_split(res["prior"], pods[bound], sfs[bound])
        sid = f"sat={sat_name}|drift={drift_name if w > 0 else 'none'}|w={w:g}|pod={bound}|ac={'yes' if acoustic else 'no'}"
        mass_node = combine.to_arc_raster(af, res["post"], A)
        prior_node = combine.to_arc_raster(af, res["prior"], A)
        sf_node = combine.to_arc_raster(af, sfs[bound] * A, A)  # searched km2 per node
        pod_node = combine.to_arc_raster(af, pods[bound] * A, A)
        srow = dict(scenario=sid, satcom=sat_name, drift=drift_name if w > 0 else "none", w=w, pod_bound=bound,
                    acoustic="yes" if acoustic else "no",
                    drift_prior_mass_in_nan_cells=res["drift_info"]["mass_in_nan"],
                    post_mass_in_arc_frame=float(mass_node.sum()), **split)
        srow["p_null_search_given_scenario"] = 1.0 - split["prob_searches_would_have_found"]
        for B in a.budgets:
            for mode, msf in [("any", None), ("unsearched", MAX_SEARCHED_FRAC)]:
                rows = combine.best_boxes(af, mass_node, B, n_boxes=n_boxes,
                                          extra=dict(prior_mass=prior_node, searched_km2=sf_node, pod_km2=pod_node),
                                          searched=sf_node, max_searched_frac=msf)
                for r, row in enumerate(rows, 1):
                    row = dict(row)
                    row["corners"] = ";".join(f"({x[0]:.3f},{x[1]:.3f})" for x in row["corners"])
                    blocks.append(dict(scenario=sid, satcom=sat_name, drift=srow["drift"], w=w, pod_bound=bound,
                                       acoustic=srow["acoustic"], mode=mode, budget_km2=B, rank=r,
                                       p_success=row["mass"] * a.pod_new,
                                       frac_previously_searched=row.pop("searched_km2") / row["area_km2"],
                                       mean_prior_pod_in_block=row.pop("pod_km2") / row["area_km2"], **row))
                sfx = "" if mode == "any" else "_unsearched"
                if rows:
                    srow[f"top{sfx}_{int(B)}_mass"] = rows[0]["mass"]
                    srow[f"top{sfx}_{int(B)}_p_success"] = rows[0]["mass"] * a.pod_new
                    srow[f"top{sfx}_{int(B)}_centre"] = f"{fmt_lat(rows[0]['centre_lat'])} {fmt_lon(rows[0]['centre_lon'])}"
                    srow[f"top{sfx}_{int(B)}_searched_frac"] = blocks[-len(rows)]["frac_previously_searched"]
            srow[f"hdr_{int(B)}_mass_upper_bound"] = combine.hdr_mass(res["post"], A, B)
            _, bm, _ = combine.greedy_blob(res["post"], A, B)
            srow[f"blob_{int(B)}_mass"] = bm
        for lab, frac in NAMED.items():
            srow[f"mass[{lab}]"] = float(np.sum(res["post"] * frac))
        summaries.append(srow)
        if save:
            keep[sid] = res
        return res

    # ------------------------------------------------ main scenario grid
    acoustic_opts = [False, True] if ac_ll is not None else [False]
    n_main = 0
    for ac in acoustic_opts:
        for sat_name in sats:
            for w in weights:
                for bound in BOUNDS:
                    headline = sat_name == a.headline_satcom
                    run_one(sat_name, "loglik", w, bound, ac, a.n_boxes if headline or bound == "best" else 1,
                            save=headline and not ac)
                    n_main += 1
    print(f"{n_main} main scenarios in {time.time()-t0:.0f}s")
    # ------------------------------------------------ drift-variant sensitivity
    if drifts and not a.no_drift_sensitivity:
        for dv in drifts:
            if dv == "loglik":
                continue
            for w in [x for x in weights if x > 0]:
                run_one(a.headline_satcom, dv, w, "best", False, 1)
        print(f"drift sensitivity done ({time.time()-t0:.0f}s)")

    S = pd.DataFrame(summaries)
    Bk = pd.DataFrame(blocks)
    S.to_csv(out / "scenario_summary.csv", index=False, float_format="%.5g")
    Bk.to_csv(out / "ranked_blocks_all.csv", index=False, float_format="%.5g")

    # ------------------------------------------------ per-scenario tables
    cols = ["rank", "budget_km2", "centre_lat", "centre_lon", "mass_centre_lat", "mass_centre_lon",
            "lat_min", "lat_max", "lon_min", "lon_max", "area_km2", "length_km", "width_km", "n0_km", "n1_km",
            "s0_km", "s1_km", "mass", "p_success", "prior_mass", "frac_previously_searched",
            "mean_prior_pod_in_block", "corners"]
    main_ids = S[(S.drift.isin(["loglik", "none"]))].scenario.unique()
    for sid in main_ids:
        t = Bk[Bk.scenario == sid][["mode"] + cols]
        if t.empty:
            continue
        fn = sid.replace("|", "__").replace("=", "-")
        t.to_csv(out / "tables" / f"{fn}.csv", index=False, float_format="%.5g")
        with open(out / "tables" / f"{fn}.md", "w") as f:
            f.write(f"# {tag}Ranked blocks: `{sid}`\n\n")
            f.write("## Any ground (re-search of previously searched seabed allowed)\n\n")
            f.write(md_blocks(t[t["mode"] == "any"], a.pod_new))
            f.write(f"\n## Essentially unsearched ground (<= {MAX_SEARCHED_FRAC:.0%} of block previously searched)\n\n")
            f.write(md_blocks(t[t["mode"] == "unsearched"], a.pod_new))

    # ------------------------------------------------ save headline posteriors
    if keep:
        ds = xr.Dataset(coords={"lat": lat, "lon": lon})
        for sid, res in keep.items():
            parts = dict(x.split("=") for x in sid.split("|"))
            nm = f"post_w{parts['w'].replace('.', 'p')}_{parts['pod']}"
            ds[nm] = (("lat", "lon"), res["post"].astype(np.float32))
            ds[nm].attrs["scenario"] = sid
            if parts["pod"] == "best":
                ds[f"prior_w{parts['w'].replace('.', 'p')}"] = (("lat", "lon"), res["prior"].astype(np.float32))
                ds[f"prior_w{parts['w'].replace('.', 'p')}"].attrs["long_name"] = "satcom x drift^w before search subtraction"
        ds.attrs = dict(title=f"{tag}MH370 combined posterior (satcom x drift^w x (1-pod))",
                        label=a.label or "REAL INPUTS", satcom=a.satcom, drift=a.drift, pod=a.pod,
                        acoustic=a.acoustic if ac_ll is not None else "absent", created=time.strftime("%Y-%m-%d %H:%M"))
        grid.save(ds, a.posterior_out)

    # ------------------------------------------------ arc profile (latitude marginal)
    prof = {}
    for sid, res in keep.items():
        parts = dict(x.split("=") for x in sid.split("|"))
        la_c, h = combine.arc_latitude_profile(af, res["post"])
        prof[f"post_w{parts['w']}_{parts['pod']}"] = h
        if parts["pod"] == "best":
            prof[f"prior_w{parts['w']}"] = combine.arc_latitude_profile(af, res["prior"])[1]
    if prof:
        P = pd.DataFrame(prof)
        P.insert(0, "arc_lat", np.round(la_c, 3))
        P = P[(P.arc_lat >= -44) & (P.arc_lat <= -16)]
        P.to_csv(out / "arc_profile.csv", index=False, float_format="%.6g")

    info = dict(label=a.label or "REAL INPUTS", flags=flags, created=time.strftime("%Y-%m-%d %H:%M"),
                inputs={k: dict(path=v, present=Path(v).exists(),
                                mtime=time.ctime(Path(v).stat().st_mtime) if Path(v).exists() else None)
                        for k, v in dict(satcom=a.satcom, drift=a.drift, acoustic=a.acoustic, pod=a.pod).items()},
                satcom_scenarios=list(sats), drift_variants=list(drifts), weights=weights,
                budgets=a.budgets, pod_new=a.pod_new, headline=dict(satcom=a.headline_satcom, w=a.headline_w),
                satcom_attrs={k: str(v) for k, v in sat_ds.attrs.items()},
                drift_attrs={k: str(v) for k, v in (drift_ds.attrs.items() if drift_ds is not None else [])},
                runtime_s=round(time.time() - t0))
    with open(out / "run_info.json", "w") as f:
        json.dump(info, f, indent=1)
    write_results_md(out, S, Bk, a, tag, flags, info)
    if not a.no_plots:
        make_plots(out, keep, Bk, S, a, tag, af)
    print(f"done in {time.time()-t0:.0f}s -> {out}")


def md_blocks(t, pod_new):
    lines = ["| budget km2 | rank | centre | lat range | lon range | across-arc n (km) | area km2 | "
             "posterior mass | P(success) @POD %.2f | previously searched | prior mass |" % pod_new,
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in t.iterrows():
        lines.append(f"| {r.budget_km2:,.0f} | {r['rank']} | {fmt_lat(r.centre_lat)} {fmt_lon(r.centre_lon)} | "
                     f"{fmt_lat(r.lat_max)}-{fmt_lat(r.lat_min)} | {r.lon_min:.2f}-{r.lon_max:.2f}E | "
                     f"{r.n0_km:+.0f} to {r.n1_km:+.0f} | {r.area_km2:,.0f} | {r.mass:.4f} | {r.p_success:.4f} | "
                     f"{100*r.frac_previously_searched:.0f}% | {r.prior_mass:.4f} |")
    return "\n".join(lines) + "\n\nn > 0 = south-east of (farther from the satellite than) the sea-level 7th arc. " \
        "Blocks are arc-aligned rectangles; corners (lat, lon) are in the CSV.\n"


def write_results_md(out, S, Bk, a, tag, flags, info):
    L = [f"# {tag}Combined posterior and ranked search blocks\n"]
    if a.label:
        L.append(f"> **{a.label} INPUTS - these numbers are NOT results about MH370.** They exist only to test the "
                 "combiner.\n")
    L.append(f"Generated {info['created']} by `scripts/combine_run.py`. Inputs:\n")
    for k, v in info["inputs"].items():
        L.append(f"- {k}: `{Path(v['path']).name}` present={v['present']} (modified {v['mtime']})")
    if flags:
        L.append("\nFlags:\n" + "\n".join(f"- {x}" for x in flags))
    L.append(f"\nposterior ∝ satcom_p × exp(w·drift_loglik) × (1 − pod); POD_new for a future search = {a.pod_new}.\n")
    # headline: satcom p, loglik, all w, all bounds
    h = S[(S.satcom == a.headline_satcom) & (S.drift.isin(["loglik", "none"])) & (S.acoustic == "no")]
    L.append(f"## Headline satcom scenario `{a.headline_satcom}`: searched vs unsearched\n")
    L.append("| w | POD bound | prior mass in searched ground | P(past searches would have found it) | "
             "P(wreck in searched ground, missed) | P(wreck in unsearched ground) | drift prior mass in NaN cells |")
    L.append("|---|---|---|---|---|---|---|")
    for _, r in h.iterrows():
        L.append(f"| {r.w:g} | {r.pod_bound} | {r.prior_mass_in_searched_ground:.3f} | "
                 f"{r.prob_searches_would_have_found:.3f} | {r.post_prob_in_searched_ground_missed:.3f} | "
                 f"{r.post_prob_in_unsearched_ground:.3f} | {r.drift_prior_mass_in_nan_cells:.4f} |")
    for mode, title in [("any", "re-search of previously searched ground allowed"),
                        ("unsearched", f"essentially unsearched ground only (<= {MAX_SEARCHED_FRAC:.0%} previously searched)")]:
        for B in a.budgets:
            L.append(f"\n## Top blocks, {B:,.0f} km², {title} (satcom `{a.headline_satcom}`, POD best)\n")
            for w in sorted(h.w.unique()):
                t = Bk[(Bk.satcom == a.headline_satcom) & (Bk.drift.isin(["loglik", "none"])) & (Bk.w == w)
                       & (Bk.pod_bound == "best") & (Bk.budget_km2 == B) & (Bk.acoustic == "no") & (Bk["mode"] == mode)]
                if t.empty:
                    continue
                L.append(f"\n**w = {w:g}**\n")
                L.append(md_blocks(t, a.pod_new))
                if mode == "any":
                    r = h[(h.w == w) & (h.pod_bound == "best")].iloc[0]
                    L.append(f"Benchmarks for {B:,.0f} km²: best free-form contiguous block captures "
                             f"{r[f'blob_{int(B)}_mass']:.4f}; highest-density cells (non-contiguous) "
                             f"{r[f'hdr_{int(B)}_mass_upper_bound']:.4f}.\n")
    # named areas
    named_cols = [c for c in S.columns if c.startswith("mass[")]
    if named_cols:
        L.append(f"\n## Posterior mass in named areas (satcom `{a.headline_satcom}`, drift `loglik`)\n")
        L.append("| area | " + " | ".join(f"w={w:g} {b}" for w in sorted(h.w.unique()) for b in ["low", "best", "high"]) + " |")
        L.append("|---|" + "---|" * (3 * len(h.w.unique())))
        for c in named_cols:
            vals = []
            for w in sorted(h.w.unique()):
                for b in ["low", "best", "high"]:
                    rr = h[(h.w == w) & (h.pod_bound == b)]
                    vals.append(f"{rr[c].iloc[0]:.4f}" if len(rr) else "")
            L.append(f"| {c[5:-1]} | " + " | ".join(vals) + " |")
    # all satcom scenarios: top block per budget
    for mode, sfx in [("any", ""), ("unsearched", "_unsearched")]:
        L.append(f"\n## All satcom scenarios: rank-1 block, mode '{mode}' (drift `loglik`)\n")
        L.append("| satcom | w | POD | P(null search given scenario) | P(missed in searched) | " + " | ".join(
            f"top {B/1000:g}k centre | mass | P(succ)" for B in a.budgets) + " |")
        L.append("|---|---|---|---|---|" + "---|---|---|" * len(a.budgets))
        for _, r in S[(S.drift.isin(["loglik", "none"])) & (S.acoustic == "no")].iterrows():
            cells = []
            for B in a.budgets:
                cells += [str(r.get(f"top{sfx}_{int(B)}_centre", "")), f"{r.get(f'top{sfx}_{int(B)}_mass', np.nan):.4f}",
                          f"{r.get(f'top{sfx}_{int(B)}_p_success', np.nan):.4f}"]
            L.append(f"| {r.satcom} | {r.w:g} | {r.pod_bound} | {r.p_null_search_given_scenario:.3f} | "
                     f"{r.post_prob_in_searched_ground_missed:.3f} | " + " | ".join(cells) + " |")
    d = S[~S.drift.isin(["loglik", "none"])]
    if not d.empty:
        B = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]
        L.append(f"\n## Drift-variant sensitivity (satcom `{a.headline_satcom}`, POD best, budget {B:,.0f} km²)\n")
        L.append("| drift variant | w | P(null search) | P(missed in searched) | top block (any) | mass | "
                 "top unsearched block | mass | P(success) |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for _, r in d.sort_values(["w", "drift"]).iterrows():
            L.append(f"| {r.drift} | {r.w:g} | {r.p_null_search_given_scenario:.3f} | {r.post_prob_in_searched_ground_missed:.3f} | "
                     f"{r.get(f'top_{int(B)}_centre', '')} | {r.get(f'top_{int(B)}_mass', np.nan):.4f} | "
                     f"{r.get(f'top_unsearched_{int(B)}_centre', '')} | {r.get(f'top_unsearched_{int(B)}_mass', np.nan):.4f} | "
                     f"{r.get(f'top_unsearched_{int(B)}_p_success', np.nan):.4f} |")
    (out / "RESULTS.md").write_text("\n".join(L) + "\n")


def make_plots(out, keep, Bk, S, a, tag, af):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mh370 import geo
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-44.0, -15.0, 0.05))
    lat, lon = grid.common_grid()
    A = grid.cell_area_km2().values
    cmap = search.seq_cmap()
    items = None
    sf_contour = None
    if a.label:  # synthetic/test run: outline the searched area of the supplied POD file
        try:
            sf_contour = xr.open_dataset(a.pod, engine="h5netcdf")["searched_frac"].values
        except Exception:  # noqa: BLE001
            pass
    else:
        try:
            items = search.build_items()
        except Exception:  # noqa: BLE001
            pass
    Bmid_ = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]

    def panel(ax, post, sid_filter, title, ext):
        search.basemap(ax, ext)
        dens = post / A
        vmax = np.nanpercentile(dens[dens > 0], 99.9) if (dens > 0).any() else 1
        m = np.ma.masked_less_equal(dens, vmax * 1e-3)
        im = ax.pcolormesh(lon, lat, m, cmap=cmap, vmin=0, vmax=vmax, shading="nearest", zorder=2)
        if items is not None:
            for c in search.CAMPAIGNS:
                u = search.campaign_union(items, c, "best")
                search.fill_geom(ax, u, "none", lw=0.6, edge=search.CAMPAIGN_COLOR[c])
        elif sf_contour is not None:
            ax.contour(lon, lat, sf_contour, levels=[0.5], colors=["#eb6834"], linewidths=0.8, zorder=6)
        ax.plot(arc[:, 1], arc[:, 0], color="#0b0b0b", lw=0.8, zorder=5)
        t = Bk[sid_filter(Bk)]
        Bmid = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]
        for mode, ls, pre in [("any", "-", ""), ("unsearched", "--", "U")]:
            tb = t[(t.budget_km2 == Bmid) & (t["rank"] <= 3) & (t["mode"] == mode)]
            for _, r in tb.iterrows():
                xy = combine.box_outline(r)
                ax.plot(xy[:, 0], xy[:, 1], color="#0b0b0b", lw=1.4 if r["rank"] == 1 else 0.9, ls=ls, zorder=7)
                ax.text(r.centre_lon, r.centre_lat, f"{pre}{int(r['rank'])}", fontsize=7.5, ha="center", va="center",
                        color="#0b0b0b", zorder=8, bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
        ax.set_title(title, fontsize=10, loc="left")
        return im

    ws = sorted({float(k.split("|")[2].split("=")[1]) for k in keep})
    if keep:
        # extent from the headline posterior mass
        res0 = keep[next(iter(keep))]["post"]
        ii = np.argwhere(res0 > res0.max() * 1e-3)
        y0, y1 = lat[ii[:, 0].min()] - 1, lat[ii[:, 0].max()] + 1
        x0, x1 = lon[ii[:, 1].min()] - 1, lon[ii[:, 1].max()] + 1
        ext = (max(x0, 78), min(x1, 112), max(y0, -44), min(y1, -16))
        fig, axes = plt.subplots(1, len(ws), figsize=(5.6 * len(ws), 6.4), squeeze=False)
        for ax, w in zip(axes[0], ws):
            sid = [k for k in keep if f"|w={w:g}|pod=best" in k][0]
            im = panel(ax, keep[sid]["post"],
                       lambda d, w=w: (d.satcom == a.headline_satcom) & (d.drift.isin(["loglik", "none"])) & (d.w == w)
                       & (d.pod_bound == "best") & (d.acoustic == "no"),
                       f"{tag}posterior, satcom '{a.headline_satcom}', w={w:g}, POD best", ext)
        cb = fig.colorbar(im, ax=axes[0].tolist(), shrink=0.75, pad=0.01)
        cb.set_label("posterior density (per km2)")
        fig.text(0.01, 0.01, f"{tag}Boxes: top-3 arc-aligned {Bmid_:,.0f} km2 blocks; solid 1-3 = any ground (re-search "
                 f"allowed), dashed U1-U3 = essentially unsearched ground (<= {MAX_SEARCHED_FRAC:.0%} previously searched). "
                 + ("Outlines: searched areas (blue ATSB, orange OI 2018, green OI 2025-26)." if items is not None
                    else "Orange contour: searched area of the supplied POD file."), fontsize=8, color="#52514e")
        fig.savefig(out / "fig_posterior_w.png", dpi=130, bbox_inches="tight")
        plt.close(fig)
        # pod bounds at headline w
        wh = a.headline_w if a.headline_w in ws else ws[-1]
        fig, axes = plt.subplots(1, 3, figsize=(16.8, 6.4))
        for ax, bound in zip(axes, ["low", "best", "high"]):
            sid = [k for k in keep if f"|w={wh:g}|pod={bound}" in k][0]
            im = panel(ax, keep[sid]["post"],
                       lambda d, bound=bound: (d.satcom == a.headline_satcom) & (d.drift.isin(["loglik", "none"]))
                       & (d.w == wh) & (d.pod_bound == bound) & (d.acoustic == "no"),
                       f"{tag}w={wh:g}, POD {bound}", ext)
        cb = fig.colorbar(im, ax=axes.tolist(), shrink=0.75, pad=0.01)
        cb.set_label("posterior density (per km2)")
        fig.savefig(out / "fig_posterior_pod_bounds.png", dpi=130, bbox_inches="tight")
        plt.close(fig)
    # rank-1 block centres across all satcom scenarios
    B = a.budgets[1] if len(a.budgets) > 1 else a.budgets[0]
    for mode in ["any", "unsearched"]:
        t = Bk[(Bk["rank"] == 1) & (Bk.budget_km2 == B) & (Bk.drift.isin(["loglik", "none"])) & (Bk.acoustic == "no")
               & (Bk["mode"] == mode)]
        if t.empty:
            continue
        fig, ax = plt.subplots(figsize=(9, 8))
        ext2 = (max(t.centre_lon.min() - 3, 78), min(t.centre_lon.max() + 3, 112),
                max(t.centre_lat.min() - 3, -44), min(t.centre_lat.max() + 3, -16))
        search.basemap(ax, ext2)
        if items is not None:
            for c in search.CAMPAIGNS:
                search.fill_geom(ax, search.campaign_union(items, c, "best"), search.CAMPAIGN_COLOR[c], alpha=0.25, lw=0.5)
        ax.plot(arc[:, 1], arc[:, 0], color="#0b0b0b", lw=0.8, zorder=5)
        mk = {"best": "o", "low": "v", "high": "^"}
        cw = {0.0: "#cde2fb", 0.5: "#3987e5", 1.0: "#0d366b"}
        for _, r in t.iterrows():
            ax.plot(r.centre_lon, r.centre_lat, mk[r.pod_bound], ms=7, mfc=cw.get(r.w, "#6da7ec"), mec="#0b0b0b",
                    mew=0.6, zorder=8)
        from matplotlib.lines import Line2D
        h = [Line2D([], [], marker=mk[b], ls="none", mfc="white", mec="#0b0b0b", label=f"POD {b}") for b in mk]
        h += [Line2D([], [], marker="s", ls="none", mfc=c, mec="#0b0b0b", label=f"w = {w:g}") for w, c in cw.items()]
        ax.legend(handles=h, loc="upper left", fontsize=8.5)
        ax.set_title(f"{tag}Centre of the rank-1 {B:,.0f} km2 block ({mode} ground), every satcom scenario x w x POD bound",
                     fontsize=10, loc="left")
        fig.savefig(out / f"fig_top_block_centres_{mode}.png", dpi=130, bbox_inches="tight")
        plt.close(fig)
    # arc profile
    pf = out / "arc_profile.csv"
    if pf.exists():
        P = pd.read_csv(pf)
        fig, ax = plt.subplots(figsize=(11, 4.4))
        colors = {"0": "#9ec5f4", "0.5": "#3987e5", "1": "#0d366b"}
        for c in P.columns:
            if c.startswith("post_w") and c.endswith("_best"):
                w = c[6:-5]
                ax.plot(P.arc_lat, P[c], color=colors.get(w, "#52514e"), lw=2, label=f"posterior w={w} (POD best)")
            if c.startswith("prior_w") and c[7:] == "0":
                ax.plot(P.arc_lat, P[c], color="#52514e", lw=1.2, ls=":", label="satcom only, before search")
        ax.set_xlabel("latitude of nearest point on the sea-level 7th arc")
        ax.set_ylabel("probability per 0.05 deg of arc latitude")
        nz = P[[c for c in P.columns if c != "arc_lat"]].sum(axis=1) > 1e-6
        if nz.any():
            ax.set_xlim(P.arc_lat[nz].min() - 0.5, P.arc_lat[nz].max() + 0.5)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(axis="y", color="#e6e5e1", lw=0.6)
        ax.legend(fontsize=8.5, frameon=False)
        ax.set_title(f"{tag}Posterior marginalised along the 7th arc", fontsize=10.5, loc="left")
        fig.tight_layout()
        fig.savefig(out / "fig_arc_profile.png", dpi=130)
        plt.close(fig)
    # GeoJSON of headline blocks
    feats = []
    for _, r in Bk[(Bk.satcom == a.headline_satcom) & (Bk.drift.isin(["loglik", "none"])) & (Bk.acoustic == "no")
                   & (Bk.pod_bound == "best")].iterrows():
        xy = combine.box_outline(r)
        feats.append(dict(type="Feature", geometry=dict(type="Polygon", coordinates=[xy.round(4).tolist()]),
                          properties=dict(label=a.label or "REAL INPUTS", mode=r["mode"], w=r.w, budget_km2=r.budget_km2,
                                          rank=int(r["rank"]), mass=round(r.mass, 5), p_success=round(r.p_success, 5),
                                          area_km2=round(r.area_km2), centre_lat=round(r.centre_lat, 4),
                                          centre_lon=round(r.centre_lon, 4))))
    with open(out / "blocks_headline.geojson", "w") as f:
        json.dump(dict(type="FeatureCollection", features=feats), f)


if __name__ == "__main__":
    main()
