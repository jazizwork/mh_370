"""Self-test of the combiner with SYNTHETIC placeholder inputs.

Run:  .venv/bin/python -I scripts/combine_selftest.py
Writes synthetic inputs to data/derived/selftest_SYNTHETIC/ and runs scripts/combine_run.py and
scripts/combine_mix_run.py on them into outputs/combine/selftest_SYNTHETIC/ (mixture run in .../mix/).
NOTHING produced here is a result about MH370. Tests TM1-TM9 cover the model-misspecification mixture
(src/mh370/combine_mix.py); TM1 uses the real broad-component cache (a prior layer, built if absent).
Exit code 0 only if every check passes.
"""
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import xarray as xr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from mh370 import combine, combine_mix, grid, search  # noqa: E402

SYN = ROOT / "data" / "derived" / "selftest_SYNTHETIC"
OUT = ROOT / "outputs" / "combine" / "selftest_SYNTHETIC"
RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")


def s_of_lat(lat):
    la, lo, s = search.arc_dense()
    o = np.argsort(la)
    return float(np.interp(lat, la[o], s[o]))


def make_inputs(af):
    SYN.mkdir(parents=True, exist_ok=True)
    lat, lon = grid.common_grid()
    S, N = af.cell_s, af.cell_n
    A = grid.cell_area_km2().values
    ok = np.isfinite(S) & (np.abs(N) < 2000)

    def gauss(s0, ss, sn):
        g = np.where(ok, np.exp(-0.5 * ((S - s0) / ss) ** 2 - 0.5 * (N / sn) ** 2), 0.0) * A
        return g / g.sum()
    s30, s36, s31, s29 = s_of_lat(-30.0), s_of_lat(-36.0), s_of_lat(-31.0), s_of_lat(-29.0)
    sat = xr.Dataset(coords={"lat": lat, "lon": lon})
    sat["p"] = (("lat", "lon"), gauss(s30, 250.0, 30.0).astype(np.float32))
    sat["p_south"] = (("lat", "lon"), gauss(s36, 200.0, 30.0).astype(np.float32))
    sat["p_glide"] = (("lat", "lon"), gauss(s30, 250.0, 100.0).astype(np.float32))
    sat.attrs["title"] = "SYNTHETIC satcom placeholder (Gaussian along the 7th arc) - NOT MH370 RESULTS"
    grid.save(sat, str(SYN / "satcom_posterior_SYNTHETIC.nc"))

    band = ok & (np.abs(N) < 300)
    dr = xr.Dataset(coords={"lat": lat, "lon": lon})
    dr["loglik"] = (("lat", "lon"), np.where(band, 0.0, np.nan).astype(np.float32))           # flat
    dr["loglik_const"] = (("lat", "lon"), np.where(band, -150.0, np.nan).astype(np.float32))  # flat, offset
    dr["loglik_gradient"] = (("lat", "lon"), np.where(band, -(S - s30) / 200.0, np.nan).astype(np.float32))
    dr["loglik_item_dummy"] = (("lat", "lon"), np.where(band, 0.0, np.nan).astype(np.float32))  # must be ignored
    dr.attrs["title"] = "SYNTHETIC drift placeholder - NOT MH370 RESULTS"
    grid.save(dr, str(SYN / "drift_loglik_SYNTHETIC.nc"))

    box = ok & (S >= s31) & (S <= s29) & (np.abs(N) < 40)
    pod = xr.Dataset(coords={"lat": lat, "lon": lon})
    for v, d in [("pod", 0.9), ("pod_low", 0.8), ("pod_high", 0.95)]:
        pod[v] = (("lat", "lon"), np.where(box, d, 0.0).astype(np.float32))
    for v in ["searched_frac", "searched_frac_low", "searched_frac_high"]:
        pod[v] = (("lat", "lon"), box.astype(np.float32))
    pod.attrs["title"] = "SYNTHETIC search POD placeholder - NOT MH370 RESULTS"
    grid.save(pod, str(SYN / "search_pod_SYNTHETIC.nc"))

    ac = xr.Dataset(coords={"lat": lat, "lon": lon})
    patch = ok & (np.abs(S - s_of_lat(-27.0)) < 80) & (np.abs(N) < 60)
    ac["loglik"] = (("lat", "lon"), np.where(patch, 2.0, np.where(band & (np.abs(S - s30) < 900), 0.0, np.nan)).astype(np.float32))
    ac.attrs["title"] = "SYNTHETIC acoustic placeholder - NOT MH370 RESULTS"
    grid.save(ac, str(SYN / "acoustic_loglik_SYNTHETIC.nc"))
    return sat, dr, pod, ac, box


def main():
    t0 = time.time()
    af = combine.build_arc_frame()
    sat, dr, pod, ac, box = make_inputs(af)
    p = sat["p"].values.astype(float)
    A = grid.cell_area_km2().values

    # T1 normalisation + T2 flat drift invariance + T3 constant offset with NaN outside
    r0 = combine.combine(p, None, 0.0, pod["pod"].values)
    check("T1 posterior normalised", abs(r0["post"].sum() - 1) < 1e-9 and abs(r0["prior"].sum() - 1) < 1e-9)
    for w in (0.5, 1.0):
        rf = combine.combine(p, dr["loglik"].values, w, pod["pod"].values)
        rc = combine.combine(p, dr["loglik_const"].values, w, pod["pod"].values)
        check(f"T2 flat drift (NaN outside band) leaves posterior unchanged, w={w}",
              np.abs(rf["post"] - r0["post"]).max() < 1e-12, f"max diff {np.abs(rf['post']-r0['post']).max():.1e}")
        check(f"T3 additive constant in loglik is irrelevant, w={w}",
              np.abs(rc["post"] - r0["post"]).max() < 1e-12, f"max diff {np.abs(rc['post']-r0['post']).max():.1e}")
    nan_mass = combine.combine(p, dr["loglik"].values, 1.0, None)["drift_info"]["mass_in_nan"]
    check("T3b NaN-mass flag reported", 0 <= nan_mass < 1e-3, f"prior mass in NaN drift cells = {nan_mass:.2e}")

    # T4 analytic missed fraction
    m = float((r0["prior"] * box).sum())
    d_syn = float(np.float32(0.9))  # the synthetic file stores POD as float32
    exp_missed = m * (1 - d_syn) / (1 - d_syn * m)
    sp = combine.search_split(r0["prior"], pod["pod"].values, pod["searched_frac"].values)
    check("T4 P(missed in searched ground) matches analytic m(1-d)/(1-dm)",
          abs(sp["post_prob_in_searched_ground_missed"] - exp_missed) < 1e-6,
          f"{sp['post_prob_in_searched_ground_missed']:.6f} vs {exp_missed:.6f} (prior mass in box {m:.4f})")
    direct = float((r0["post"] * box).sum())
    check("T4b missed fraction equals posterior mass in searched cells", abs(direct - exp_missed) < 1e-9, f"{direct:.9f}")

    # T5 tempering with a gradient
    S = np.nan_to_num(af.cell_s)
    means = {}
    posts = {}
    for w in (0.0, 0.5, 1.0):
        r = combine.combine(p, dr["loglik_gradient"].values, w, None)
        posts[w] = r["post"]
        means[w] = float((r["post"] * S).sum())
    check("T5 gradient drift moves posterior monotonically with w", means[1.0] < means[0.5] < means[0.0],
          f"mean s: {means[0.0]:.0f} / {means[0.5]:.0f} / {means[1.0]:.0f} km")
    msk = (posts[0.0] > 1e-12) & np.isfinite(dr["loglik_gradient"].values)
    lr = np.log(posts[1.0][msk] / posts[0.0][msk]) - 2 * np.log(posts[0.5][msk] / posts[0.0][msk])
    check("T5b exact tempering: log(p1/p0) - 2 log(p.5/p0) is constant", np.ptp(lr) < 1e-6, f"ptp {np.ptp(lr):.1e}")

    # T6 box finder recovers a known 7,500 km2 rectangle
    s_c = s_of_lat(-33.0)
    rect = np.isfinite(af.cell_s) & (np.abs(af.cell_s - s_c) < 50) & (af.cell_n > 20) & (af.cell_n < 95)
    q = np.where(rect, 1.0, 1e-4) * A * np.isfinite(af.cell_s)
    q /= q.sum()
    node = combine.to_arc_raster(af, q, A)
    rows = combine.best_boxes(af, node, 7500.0, n_boxes=2)
    b = rows[0]
    ov_s = max(0, min(b["s1_km"], s_c + 50) - max(b["s0_km"], s_c - 50)) / 100
    ov_n = max(0, min(b["n1_km"], 95) - max(b["n0_km"], 20)) / 75
    check("T6 best 7,500 km2 box recovers the planted 100x75 km block", ov_s * ov_n > 0.85,
          f"overlap {ov_s*ov_n:.2f}, box s {b['s0_km']:.0f}..{b['s1_km']:.0f}, n {b['n0_km']:.0f}..{b['n1_km']:.0f}, area {b['area_km2']:.0f}")
    check("T6b area of box within 3% of budget", abs(b["area_km2"] - 7500) / 7500 < 0.03, f"{b['area_km2']:.0f} km2")
    check("T6c second box is disjoint and smaller", rows[1]["mass"] < rows[0]["mass"] and
          (rows[1]["s0_km"] >= b["s1_km"] - 1e-6 or rows[1]["s1_km"] <= b["s0_km"] + 1e-6 or
           rows[1]["n0_km"] >= b["n1_km"] - 1e-6 or rows[1]["n1_km"] <= b["n0_km"] + 1e-6))
    # T6d unsearched-only ranking avoids a block that is marked as previously searched
    searched_node = combine.to_arc_raster(af, rect.astype(float) * A, A)
    ru = combine.best_boxes(af, node, 7500.0, n_boxes=1, searched=searched_node, max_searched_frac=0.10)[0]
    ov_s2 = max(0, min(ru["s1_km"], s_c + 50) - max(ru["s0_km"], s_c - 50)) / 100
    ov_n2 = max(0, min(ru["n1_km"], 95) - max(ru["n0_km"], 20)) / 75
    sl_ = (slice(int(np.searchsorted(af.s, ru["s0_km"])), int(np.searchsorted(af.s, ru["s1_km"]))),
           slice(int(np.searchsorted(af.n, ru["n0_km"])), int(np.searchsorted(af.n, ru["n1_km"]))))
    sf_box = float(searched_node[sl_].sum() / af.dA[sl_].sum())
    check("T6d unsearched-only ranking: block <= 10% previously searched and avoids the searched block",
          sf_box <= 0.1001 and ov_s2 * ov_n2 < 0.2, f"searched fraction {sf_box:.3f}, nominal overlap {ov_s2*ov_n2:.3f}")
    hm = combine.hdr_mass(q, A, 7500.0)
    _, bm, _ = combine.greedy_blob(q, A, 7500.0)
    check("T7 benchmarks: HDR >= blob-ish >= box (within resampling error)",
          hm >= b["mass"] - 0.02 and hm >= bm - 1e-9, f"hdr {hm:.3f}, blob {bm:.3f}, box {b['mass']:.3f}")
    check("T7b arc-raster resampling conserves mass within 1%",
          abs(node.sum() - q[np.isfinite(af.cell_s) & (np.abs(af.cell_n) < 440)].sum()) < 0.01, f"{node.sum():.4f}")

    # T8 grid check
    bad = xr.Dataset({"p": (("lat", "lon"), np.ones((10, 10)))}, coords={"lat": np.arange(10.0), "lon": np.arange(10.0)})
    try:
        combine.check_grid(bad, "bad")
        check("T8 wrong grid rejected", False)
    except combine.GridError:
        check("T8 wrong grid rejected", True)

    # T9 real search_pod.nc consistency (if present)
    fp = ROOT / "data" / "derived" / "search_pod.nc"
    if fp.exists():
        d = xr.open_dataset(fp, engine="h5netcdf")
        lo_, be, hi = d.pod_low.values, d.pod.values, d.pod_high.values
        viol_lo = float(((lo_ - be) > 1e-3).mean())
        viol_hi = float(((be - hi) > 1e-3).mean())
        check("T9 real search_pod.nc: values in [0,1]", all(np.nanmin(x) >= 0 and np.nanmax(x) <= 1 for x in (lo_, be, hi)))
        check("T9b real search_pod.nc: pod_low <= pod <= pod_high (cells violating by >1e-3)",
              viol_lo < 1e-3 and viol_hi < 1e-3, f"{viol_lo:.1e} / {viol_hi:.1e}")
        check("T9c real search_pod.nc: pod <= searched_frac", float(((be - d.searched_frac.values) > 1e-6).mean()) == 0)
    else:
        check("T9 real search_pod.nc present", False, "(not built yet)")

    # T10 end-to-end runner on synthetic files (with acoustic)
    cmd = [sys.executable, "-I", str(ROOT / "scripts" / "combine_run.py"),
           "--satcom", str(SYN / "satcom_posterior_SYNTHETIC.nc"), "--drift", str(SYN / "drift_loglik_SYNTHETIC.nc"),
           "--acoustic", str(SYN / "acoustic_loglik_SYNTHETIC.nc"), "--pod", str(SYN / "search_pod_SYNTHETIC.nc"),
           "--out", str(OUT), "--posterior-out", str(SYN / "combined_posterior_SYNTHETIC.nc"),
           "--label", "SYNTHETIC", "--n-boxes", "3"]
    pr = subprocess.run(cmd, capture_output=True, text=True)
    (OUT).mkdir(parents=True, exist_ok=True)
    (OUT / "runner_log_SYNTHETIC.txt").write_text(pr.stdout + "\n" + pr.stderr)
    expected = ["RESULTS.md", "scenario_summary.csv", "ranked_blocks_all.csv", "arc_profile.csv",
                "fig_posterior_w.png", "blocks_headline.geojson", "run_info.json"]
    missing = [e for e in expected if not (OUT / e).exists()]
    check("T10 end-to-end runner (synthetic, with acoustic) completes", pr.returncode == 0 and not missing,
          f"rc={pr.returncode} missing={missing}")
    if pr.returncode == 0:
        import pandas as pd
        Ssum = pd.read_csv(OUT / "scenario_summary.csv")
        check("T10b item-level drift variables excluded", not Ssum.drift.str.startswith("loglik_item_").any())
        check("T10c acoustic scenarios produced", (Ssum.acoustic == "yes").any())
        Bk = pd.read_csv(OUT / "ranked_blocks_all.csv")
        t = Bk[(Bk.satcom == "p") & (Bk.w == 0) & (Bk.pod_bound == "best") & (Bk.acoustic == "no") & (Bk["rank"] == 1)]
        # with a Gaussian centred at 30S and the 31S-29S core searched, the best block should sit just
        # outside the searched box (either along-arc end or off-arc), never centred inside it
        inside = ((t.s0_km > s_of_lat(-31.0)) & (t.s1_km < s_of_lat(-29.0)) & (t.n0_km > -40) & (t.n1_km < 40)).any()
        check("T10d top block avoids the fully searched synthetic box", not inside)
        t2 = Bk[(Bk.satcom == "p") & (Bk.w == 0) & (Bk.acoustic == "yes") & (Bk.pod_bound == "best") & (Bk["rank"] == 1)]
        check("T10e acoustic patch attracts a block when included", ((t2.centre_lat > -28) & (t2.centre_lat < -26)).any()
              or len(t2) == 0, f"centres {t2.centre_lat.round(2).tolist()}")

    # ---------------------------------------------------------------- mixture (combine_mix) tests
    test_mixture(af, p, pod, box, A, OUT)

    # report
    n_pass = sum(r[1] for r in RESULTS)
    lines = ["# SYNTHETIC self-test of the combiner - NOT MH370 RESULTS\n",
             "> Every input in this directory and in `data/derived/selftest_SYNTHETIC/` is a synthetic placeholder "
             "(Gaussian along the 7th arc for satcom, flat/gradient drift, a rectangular fake search, a fake acoustic "
             "patch). The maps and tables here demonstrate that the combiner runs; they say nothing about where MH370 is.\n",
             f"Run {time.strftime('%Y-%m-%d %H:%M')}, {n_pass}/{len(RESULTS)} checks passed, {time.time()-t0:.0f}s.\n",
             "| check | result | detail |", "|---|---|---|"]
    for n_, ok_, d_ in RESULTS:
        lines.append(f"| {n_} | {'PASS' if ok_ else 'FAIL'} | {d_} |")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.md").write_text("\n".join(lines) + "\n")
    print(f"{n_pass}/{len(RESULTS)} passed")
    sys.exit(0 if n_pass == len(RESULTS) else 1)


def test_mixture(af, p, pod, box, A, OUT):
    """TM1-TM9: model-misspecification mixture  pi = (1-eps) p_sat + eps p_broad."""
    broads, binfo = combine_mix.load_or_build_broad()
    la_arc, _, s_arc = search.arc_dense()
    o = np.argsort(s_arc)
    fin = np.isfinite(af.cell_s)
    foot = np.interp(af.cell_s, s_arc[o], la_arc[o])
    # TM1 broad components: normalised, uniform in arc latitude, broad_wide flat across the arc
    for k in combine_mix.BROAD_NAMES:
        b = broads[k]
        check(f"TM1 {k}: finite, non-negative, sums to 1", np.isfinite(b).all() and b.min() >= 0 and abs(b.sum() - 1) < 1e-6,
              f"sum {b.sum():.8f}")
        h, _ = np.histogram(foot[fin], bins=np.arange(-41.0, -21.0 + 1e-9, 1.0), weights=b[fin])
        dev = np.abs(h * 22.0 - 1.0).max()
        check(f"TM1b {k}: uniform in 7th-arc latitude (1-deg bins 41-21 S within 5%)", dev < 0.05, f"max dev {dev:.3f}")
    hn, _ = np.histogram(af.cell_n[fin], bins=np.arange(-125.0, 125.0 + 1e-9, 25.0), weights=broads["broad_wide"][fin])
    outside = float(broads["broad_wide"][fin & (np.abs(af.cell_n) > 175)].sum())
    check("TM1c broad_wide flat within +/-125 km of the arc and ~0 beyond 175 km",
          np.abs(hn / hn.mean() - 1).max() < 0.05 and outside < 0.005, f"max dev {np.abs(hn/hn.mean()-1).max():.3f}, mass beyond {outside:.4f}")

    pb = broads["broad_arc"]
    pod_ = pod["pod"].values.astype(float)
    sf_ = pod["searched_frac"].values.astype(float)
    S = np.nan_to_num(af.cell_s)
    grad = np.where(fin, -(S - s_of_lat(-30.0)) / 400.0, 0.0)   # finite everywhere (no NaN subtleties)

    # TM2 eps = 0 reproduces combine.combine; eps = 1 reproduces the broad-only posterior
    for w in (0.0, 0.5):
        r0 = combine_mix.mixture_posterior(p, pb, 0.0, grad, w, pod_)
        c0 = combine.combine(p, grad, w, pod_)
        r1 = combine_mix.mixture_posterior(p, pb, 1.0, grad, w, pod_)
        c1 = combine.combine(pb, grad, w, pod_)
        check(f"TM2 eps=0 == satellite-only combiner, eps=1 == broad-only (w={w})",
              np.abs(r0["post"] - c0["post"]).max() < 1e-12 and np.abs(r1["post"] - c1["post"]).max() < 1e-12
              and r0["eps_post"] == 0.0 and abs(r1["eps_post"] - 1.0) < 1e-12,
              f"max diff {max(np.abs(r0['post']-c0['post']).max(), np.abs(r1['post']-c1['post']).max()):.1e}")

    # TM3 satellite component placed ON searched ground (synthetic box, POD 0.9): broad weight must rise,
    # exactly as the analytic two-hypothesis update says
    p_in = p * box
    p_in = p_in / p_in.sum()
    d = float(np.float32(0.9))
    m_b = float((pb / pb.sum() * box).sum())
    Ns, Nb = 1.0 - d, 1.0 - d * m_b
    for eps in (0.05, 0.1, 0.3):
        r = combine_mix.mixture_posterior(p_in, pb, eps, None, 0.0, pod_, sf_)
        exp_post = eps * Nb / ((1 - eps) * Ns + eps * Nb)
        check(f"TM3 sat on searched ground: eps {eps} -> analytic posterior weight",
              abs(r["eps_post"] - exp_post) < 1e-9 and r["eps_post"] > eps and abs(r["bf_null_sat_vs_broad"] - Ns / Nb) < 1e-9,
              f"eps_post {r['eps_post']:.4f} (analytic {exp_post:.4f}); P(null|sat) {r['p_null_sat']:.3f}, "
              f"P(null|broad) {r['p_null_broad']:.3f}, BF {r['bf_null_sat_vs_broad']:.3f}")
    # more thorough past searching -> stronger shift (monotone in POD)
    e_by_d = []
    for dd in (0.5, 0.9, 0.99):
        r = combine_mix.mixture_posterior(p_in, pb, 0.1, None, 0.0, np.where(box, dd, 0.0))
        e_by_d.append(r["eps_post"])
    check("TM3b posterior broad weight rises monotonically with past POD (0.5 / 0.9 / 0.99)",
          e_by_d[0] < e_by_d[1] < e_by_d[2], " / ".join(f"{x:.3f}" for x in e_by_d))

    # TM4 control: satellite component on UNsearched ground -> null result favours it (weight falls)
    p_far = np.where(fin & (np.abs(S - s_of_lat(-36.0)) < 200) & (np.abs(np.nan_to_num(af.cell_n)) < 60), 1.0, 0.0) * A
    p_far = p_far / p_far.sum()
    r = combine_mix.mixture_posterior(p_far, pb, 0.1, None, 0.0, pod_)
    check("TM4 sat on unsearched ground: null result lowers the broad weight", r["eps_post"] < 0.1 and r["p_null_sat"] == 1.0,
          f"eps_post {r['eps_post']:.4f}, P(null|broad) {r['p_null_broad']:.3f}")

    # TM5 normalisation and the direct formula
    r = combine_mix.mixture_posterior(p, pb, 0.2, grad, 0.5, pod_, sf_)
    direct = (0.8 * p / p.sum() + 0.2 * pb / pb.sum()) * np.exp(0.5 * grad) * (1 - np.clip(pod_, 0, 1))
    direct /= direct.sum()
    sums = [r[k].sum() for k in ("post", "prior", "post_sat", "post_broad", "prior_sat", "prior_broad")]
    check("TM5 mixture prior/posterior and component posteriors each sum to 1", max(abs(x - 1) for x in sums) < 1e-9,
          " ".join(f"{x:.10f}" for x in sums))
    check("TM5b posterior == normalise(((1-eps) p_sat + eps p_broad) exp(w ll) (1-pod)) and == weighted components",
          np.abs(r["post"] - direct).max() < 1e-12 and
          np.abs(r["post"] - ((1 - r["eps_post"]) * r["post_sat"] + r["eps_post"] * r["post_broad"])).max() < 1e-12,
          f"max diff {np.abs(r['post']-direct).max():.1e}")
    sp = r["split_mix"]
    check("TM5c P(unsearched | mixture) == weighted component values",
          abs(sp["post_prob_in_unsearched_ground"] - ((1 - r["eps_post"]) * r["split_sat"]["post_prob_in_unsearched_ground"]
                                                      + r["eps_post"] * r["split_broad"]["post_prob_in_unsearched_ground"])) < 1e-9)

    # TM6 drift evidence: weight after drift matches direct Z ratio; additive constant irrelevant
    w = 0.5
    Zs = float((p / p.sum() * np.exp(w * grad)).sum())
    Zb = float((pb / pb.sum() * np.exp(w * grad)).sum())
    exp_d = 0.1 * Zb / (0.9 * Zs + 0.1 * Zb)
    ra = combine_mix.mixture_posterior(p, pb, 0.1, grad, w, pod_)
    rb = combine_mix.mixture_posterior(p, pb, 0.1, grad - 250.0, w, pod_)
    check("TM6 weight after drift = eps Z_b / ((1-eps) Z_s + eps Z_b); additive constant in loglik irrelevant",
          abs(ra["eps_drift"] - exp_d) < 1e-9 and abs(ra["eps_post"] - rb["eps_post"]) < 1e-12,
          f"eps_drift {ra['eps_drift']:.5f} (direct {exp_d:.5f}); BF drift {ra['bf_drift_sat_vs_broad']:.3f}")

    # TM7 box decomposition: mixture box mass = (1-eps_post) sat-conditional + eps_post broad-conditional
    node = combine.to_arc_raster(af, ra["post"], A)
    ns_ = combine.to_arc_raster(af, ra["post_sat"], A)
    nb_ = combine.to_arc_raster(af, ra["post_broad"], A)
    rows = combine.best_boxes(af, node, 7500.0, n_boxes=2, extra=dict(ms=ns_, mb=nb_))
    dev = max(abs(x["mass"] - ((1 - ra["eps_post"]) * x["ms"] + ra["eps_post"] * x["mb"])) for x in rows)
    dev2 = max(abs(combine_mix.box_mass(af, node, x) - x["mass"]) for x in rows)
    check("TM7 block mass decomposes into sat-conditional and broad-conditional parts; box_mass reproduces it",
          dev < 1e-9 and dev2 < 1e-9, f"max dev {dev:.1e} / {dev2:.1e}")

    # TM8 replicated end-of-flight kernel matches the satcom script
    kc = combine_mix.kernel_constants_from_satcom_script()
    ok = (kc["w_glide"] == combine_mix.EOF_DEFAULT_W_GLIDE and kc["unc"] == (combine_mix.UNC_ALONG_NM, combine_mix.UNC_SIGMA_NM)
          and kc["glide"] == (combine_mix.GLIDE_MAX_NM, combine_mix.GLIDE_DIR_SD) and kc["smooth"] == combine_mix.GRID_SMOOTH_CELLS)
    check("TM8 broad_arc kernel constants == scripts/satcom_posterior.py", ok, str(kc))

    # TM9 end-to-end mixture runner on synthetic inputs, with p_v2 auto-detection
    sat = xr.Dataset(coords={"lat": grid.LAT, "lon": grid.LON})
    sat["p"] = (("lat", "lon"), p_in.astype(np.float32))                  # on the searched box
    sat["p_v2"] = (("lat", "lon"), p_far.astype(np.float32))              # unsearched ground at 36 S
    sat.attrs["title"] = "SYNTHETIC satcom placeholder with p_v2 - NOT MH370 RESULTS"
    f_sat = SYN / "satcom_posterior_v2_SYNTHETIC.nc"
    grid.save(sat, str(f_sat))
    mix_out = OUT / "mix"
    cmd = [sys.executable, "-I", str(ROOT / "scripts" / "combine_mix_run.py"), "--satcom", str(f_sat),
           "--drift", str(SYN / "drift_loglik_SYNTHETIC.nc"), "--pod", str(SYN / "search_pod_SYNTHETIC.nc"),
           "--old-blocks", str(OUT / "ranked_blocks_all.csv"), "--out", str(mix_out),
           "--posterior-out", str(SYN / "combined_posterior_mix_SYNTHETIC.nc"), "--label", "SYNTHETIC",
           "--eps", "0.1", "0.3", "--weights", "0", "0.5", "--budgets", "7500", "--n-boxes", "2"]
    pr = subprocess.run(cmd, capture_output=True, text=True)
    mix_out.mkdir(parents=True, exist_ok=True)
    (mix_out / "runner_log_SYNTHETIC.txt").write_text(pr.stdout + "\n" + pr.stderr)
    expected = ["RESULTS_mix.md", "ranked_blocks_mix.csv", "scenario_summary_mix.csv", "eps_sweep_mix.csv",
                "fig_mix_vs_old.png", "fig_mix_weights.png", "run_info_mix.json"]
    missing = [e for e in expected if not (mix_out / e).exists()]
    check("TM9 end-to-end mixture runner (synthetic) completes", pr.returncode == 0 and not missing,
          f"rc={pr.returncode} missing={missing}")
    if pr.returncode == 0:
        import pandas as pd
        Sm = pd.read_csv(mix_out / "scenario_summary_mix.csv")
        check("TM9b p_v2 auto-detected and run alongside p", set(Sm.sat_var) == {"p", "p_v2"})
        q = Sm[(Sm.broad == "broad_arc") & (Sm.w == 0) & (Sm.pod_bound == "best")]
        up = (q[q.sat_var == "p"].eps_post > q[q.sat_var == "p"].eps).all()
        down = (q[q.sat_var == "p_v2"].eps_post < q[q.sat_var == "p_v2"].eps).all()
        check("TM9c runner: weight rises when sat is on searched ground (p), falls when unsearched (p_v2)", up and down,
              f"p: {q[q.sat_var=='p'].eps_post.round(3).tolist()}, p_v2: {q[q.sat_var=='p_v2'].eps_post.round(3).tolist()}")
        Bm = pd.read_csv(mix_out / "ranked_blocks_mix.csv")
        dev = (Bm.mass - ((1 - Bm.eps_post) * Bm.mass_sat_cond + Bm.eps_post * Bm.mass_broad_cond)).abs().max()
        check("TM9d every ranked block: mixture mass = weighted conditional masses", dev < 1e-4, f"max dev {dev:.1e}")
    pr2 = subprocess.run(cmd[:3] + ["--satcom", str(f_sat), "--sat-vars", "p_v3", "--out", str(mix_out / "tmp"),
                                    "--no-plots"], capture_output=True, text=True)
    check("TM9e requesting a missing satellite variable fails cleanly (exit 3)", pr2.returncode == 3, f"rc={pr2.returncode}")


if __name__ == "__main__":
    main()
