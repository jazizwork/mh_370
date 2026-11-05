"""Run the SMC path inference for one autopilot mode and one assumption variant.

Usage: .venv/bin/python -I scripts/satcom_run_paths.py --mode CTT --variant baseline [--n 10000]
Output: data/derived/satcom_smc/<variant>_<mode>.npz
"""
import argparse
import json
import pathlib
import time

import numpy as np

from mh370 import geo
from mh370 import satcom_paths as sp
from mh370 import satcom_smc as smc

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "data" / "derived" / "satcom_smc"

# Assumption variants (see outputs/satcom/README.md for justification)
VARIANTS = {
    "baseline": dict(),
    "no1828bfo": dict(meas=dict(use_1828_bfo=False)),
    "no1827bto": dict(meas=dict(use_1827_btos=False)),
    "bfo4p3": dict(meas=dict(sig_bfo=4.3)),
    "bias25": dict(lik=dict(bias_sigma=25.0)),
    "bto29": dict(meas=dict(sig_r1200=29.0, sig_r600=62.0)),   # measurement noise only
    "wind90": dict(atm=dict(wind_scale=0.9)),
    "wind110": dict(atm=dict(wind_scale=1.1)),
    # wider speed/altitude prior (Mach 0.62-0.86, FL200-410)
    "wideprior": dict(prior=dict(mach=("u", 0.62, 0.86), fl=("u", 200.0, 410.0))),
    # Mach allowed to drift linearly after the FMT (covers LRC-like decreasing-Mach schedules)
    "machdrift": dict(drift=True),
}

DEG_NM = 1 / 60.0


def prior_spec(variant_cfg):
    la, lo = sp.RADAR_POS
    s = sp.RADAR_SIGMA_NM
    over = variant_cfg.get("prior", {})
    spec = [
        ("g", la, s * DEG_NM),                                   # lat0 at 18:22:12
        ("g", lo, s * DEG_NM / np.cos(np.radians(la))),          # lon0
        ("u", 270.0, 340.0),                                     # trk_pre (deg true)
        ("u", 350.0, 520.0),                                     # gs_pre (kt)
        ("u", sp.T_RADAR + 30.0, geo.hms(19, 41, 2.9) - 60.0),   # t_fmt
        ("u", 140.0, 230.0),                                     # theta (track/heading, deg)
        over.get("mach", ("u", 0.70, 0.86)),                     # Mach (at FMT)
        over.get("fl", ("u", 300.0, 400.0)),                     # flight level
    ]
    if variant_cfg.get("drift"):
        spec.append(("u", -0.012, 0.004))                        # dMach/dt per hour
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=sp.MODES)
    ap.add_argument("--variant", default="baseline", choices=list(VARIANTS))
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    cfg = VARIANTS[a.variant]
    OUTDIR.mkdir(parents=True, exist_ok=True)
    tag = f"{a.variant}_{a.mode}"
    logf = open(OUTDIR / f"{tag}.log", "w")

    def log(msg):
        print(msg, flush=True)
        logf.write(msg + "\n")
        logf.flush()

    meas = sp.build_measurements(**cfg.get("meas", {}))
    atm = sp.Atmos(**cfg.get("atm", {}))
    model = sp.PathModel(a.mode, meas, atm=atm, dt=cfg.get("dt", 120.0))
    lik = sp.Likelihood(meas, **cfg.get("lik", {}))
    names = sp.PathModel.PARAMS_DRIFT if cfg.get("drift") else sp.PathModel.PARAMS

    def loglik(x):
        P = {k: x[:, i] for i, k in enumerate(names)}
        out = model.run(P)
        return lik(out, model.t_meas)

    prior = smc.BoxGaussPrior(prior_spec(cfg))
    t0 = time.time()
    res = smc.smc(loglik, prior, n=a.n, seed=a.seed, log=log)
    log(f"done in {time.time()-t0:.0f}s logZ={res['logz']:.2f}")
    x = res["x"]
    P = {k: x[:, i] for i, k in enumerate(names)}
    out = model.run(P)
    ll, parts = lik(out, model.t_meas, return_parts=True)
    np.savez_compressed(
        OUTDIR / f"{tag}.npz", x=x, names=np.array(names), ll=ll, logz=res["logz"],
        t_meas=model.t_meas, lat=out["lat"], lon=out["lon"], vn=out["vn"], ve=out["ve"],
        h=out["h"], bto_res=parts["bto_res"], bfo_res=parts["bfo_res"], bias=parts["bias"],
        ll_bto=parts["ll_bto"], ll_bfo=parts["ll_bfo"],
        bto_t=lik.bto.t.to_numpy(), bfo_t=lik.bfo.t.to_numpy(),
        bto_label=lik.bto.label.to_numpy().astype(str), bfo_label=lik.bfo.label.to_numpy().astype(str),
        hist=json.dumps(res["hist"]))
    log(f"saved {OUTDIR / (tag + '.npz')}")


if __name__ == "__main__":
    main()
