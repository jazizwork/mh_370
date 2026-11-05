"""SMC evidence + posterior for one multi-leg route component (reviewer response).

Same sampler, likelihood, noise model, winds and priors as scripts/satcom_run_paths.py (the prior
and the assumption variants are imported from it, so they are identical by construction).

Usage examples:
  .venv/bin/python -I scripts/satcom_run_routes.py --family WPT --wpt BEDAX --mode2 LNAV --n 5000
  .venv/bin/python -I scripts/satcom_run_routes.py --family TWO --n 20000 --seed 41
  .venv/bin/python -I scripts/satcom_run_routes.py --family TWO --tie --n 20000   # sanity check
  .venv/bin/python -I scripts/satcom_run_routes.py --family WPT --wpt BEDAX --mode2 LNAV \
        --fix theta2=180 --tag ugib                                                # UGIB-like
  .venv/bin/python -I scripts/satcom_run_routes.py --family WPTS --wpt BEDAX --mode2 LNAV --roc1840
        # sensitivity d1840: free rate of climb at the 18:40 call; WPTS = own ground speed to W
  .venv/bin/python -I scripts/satcom_run_routes.py --family SINGLE --mode2 LNAV --seed 42 --n 20000
        # single-mode replicate (written here, not over the baseline files)
Output: data/derived/satcom_smc/routes/<variant>_<family>[_<wpt>_<mode2>][_<tag>]_n<N>_s<seed>.npz
"""
import argparse
import importlib.util
import json
import pathlib
import time

import numpy as np

from mh370 import satcom_paths as sp
from mh370 import satcom_routes as sr
from mh370 import satcom_smc as smc

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "data" / "derived" / "satcom_smc" / "routes"


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


RP = _load_script("satcom_run_paths")       # VARIANTS, prior_spec of the single-mode families


def run_tag(family, wpt, mode2, variant, n, seed, tag="", tie=False, roc=False):
    s = f"{variant}_{family}"
    if family in ("WPT", "WPTS"):
        s += f"_{wpt}_{mode2}"
    if family == "SINGLE":
        s += f"_{mode2}"
    if tie:
        s += "_tied"
    if roc:
        s += "_d1840"
    if tag:
        s += f"_{tag}"
    return s + f"_n{n}_s{seed}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=list(sr.PARAMS) + ["SINGLE"],
                    help="SINGLE = a single-mode family (mode from --mode2), for seed replicates "
                         "written here instead of over the baseline files")
    ap.add_argument("--wpt", default=None)
    ap.add_argument("--mode2", default="CTT", choices=sr.MODES2)
    ap.add_argument("--variant", default="baseline", choices=list(RP.VARIANTS))
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--fix", action="append", default=[], help="name=value (repeatable)")
    ap.add_argument("--tie", action="store_true", help="TWO: theta2 := theta1 (sanity check)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--roc1840", action="store_true",
                    help="sensitivity d1840: free rate of climb at the 18:40 call, U(-4000, 0) fpm")
    a = ap.parse_args()
    cfg = RP.VARIANTS[a.variant]
    assert not cfg.get("drift"), "Mach-drift variant not implemented for route families"
    if a.family in ("WPT", "WPTS"):
        assert a.wpt, "--wpt required"
    fix = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in a.fix}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    tag = run_tag(a.family, a.wpt, a.mode2, a.variant, a.n, a.seed, a.tag, a.tie, a.roc1840)
    logf = open(OUTDIR / f"{tag}.log", "w")

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()

    meas = sp.build_measurements(**cfg.get("meas", {}))
    atm = sp.Atmos(**cfg.get("atm", {}))
    lik = (sr.LikelihoodVU if a.roc1840 else sp.Likelihood)(meas, **cfg.get("lik", {}))
    if a.family == "SINGLE":
        model = sp.PathModel(a.mode2, meas, atm=atm, dt=cfg.get("dt", 120.0))
        names, spec, tie = list(sp.PathModel.PARAMS), RP.prior_spec(cfg), False
        assert not fix
        model.PARAMS = sp.PathModel.PARAMS
    else:
        model = sr.RouteModel(a.family, meas, mode2=a.mode2, wpt=a.wpt, atm=atm,
                              dt=cfg.get("dt", 120.0))
        names, spec, fix, tie = sr.prior_spec(a.family, RP.prior_spec(cfg), fix=fix, tie=a.tie)
    if a.roc1840:
        names = list(names) + ["roc1840"]
        spec = list(spec) + [sr.ROC1840_PRIOR]
    log(f"{tag}: sampled {names}; fixed {fix}; tie={tie}; prior {spec}")

    def params(x):
        if a.family == "SINGLE":
            return {k: x[:, i] for i, k in enumerate(names)}
        return sr.make_params(x, names, fix, tie)

    def run(P):
        out = model.run(P)
        if a.roc1840:
            out["roc1840_fpm"] = P["roc1840"]
        return out

    def loglik(x):
        out = run(params(x))
        return lik(out, model.t_meas)

    prior = smc.BoxGaussPrior(spec)
    t0 = time.time()
    res = smc.smc(loglik, prior, n=a.n, seed=a.seed, log=log)
    log(f"done in {time.time()-t0:.0f}s logZ={res['logz']:.3f}")
    x = res["x"]
    P = params(x)
    out = run(P)
    ll, parts = lik(out, model.t_meas, return_parts=True)
    allnames = list(model.PARAMS) + (["roc1840"] if a.roc1840 else [])
    if a.family == "SINGLE":
        out["t_sw2"] = np.full(x.shape[0], np.nan)
        out["phase"] = np.zeros_like(out["lat"], dtype=np.int8)
    xfull = np.stack([P[k] for k in allnames], 1)
    np.savez_compressed(
        OUTDIR / f"{tag}.npz", x=xfull, names=np.array(allnames), sampled=np.array(names),
        fixed=json.dumps(fix), tie=tie, family=a.family, wpt=str(a.wpt), mode2=a.mode2,
        variant=a.variant, n=a.n, seed=a.seed,
        ll=ll, logz=res["logz"], t_meas=model.t_meas, lat=out["lat"], lon=out["lon"],
        vn=out["vn"], ve=out["ve"], h=out["h"], t_sw2=out["t_sw2"], phase=out["phase"],
        bto_res=parts["bto_res"], bfo_res=parts["bfo_res"], bias=parts["bias"],
        ll_bto=parts["ll_bto"], ll_bfo=parts["ll_bfo"],
        bto_t=lik.bto.t.to_numpy(), bfo_t=lik.bfo.t.to_numpy(),
        bto_label=lik.bto.label.to_numpy().astype(str),
        bfo_label=lik.bfo.label.to_numpy().astype(str),
        hist=json.dumps(res["hist"]))
    log(f"saved {OUTDIR / (tag + '.npz')}")


if __name__ == "__main__":
    main()
