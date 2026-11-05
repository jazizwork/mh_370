"""Workstream B (drift): build Markov chains, compute the debris log-likelihood on the common
grid with sensitivity variants, write data/derived/drift_loglik.nc and outputs/drift/*.csv.

Run: .venv/bin/python -I scripts/drift_build.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from mh370 import drift as D
from mh370 import geo
from mh370 import drift_debris as dd
from mh370 import drift_mc as mc
from mh370.grid import common_grid, save

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "drift"
DER = ROOT / "data" / "derived"
OUT.mkdir(parents=True, exist_ok=True)

CHAINS = {
    # name: (bin deg, T days, drogue, leeway, seasons)
    "U1": (1.0, 5.0, 0, None, "miron3"),          # default: undrogued drifters
    "U1annual": (1.0, 5.0, 0, None, "annual"),
    "U05": (0.5, 5.0, 0, None, "miron3"),
    "U1T7": (1.0, 7.0, 0, None, "miron3"),
    "D1": (1.0, 5.0, 1, None, "miron3"),          # drogued drifters
    "F1": (1.0, 5.0, 0, "flaperon", "miron3"),    # + CSIRO flaperon leeway (10 cm/s, 20 deg left)
    "F1a10": (1.0, 5.0, 0, "flaperon10", "miron3"),
    "W3": (1.0, 5.0, 0, "windage3", "miron3"),    # ~3% windage generic object
}

_chain_cache: dict = {}


def time_scale() -> float:
    """Transit-speed calibration factor fitted in scripts/drift_validate.py (held-out drifters)."""
    p = OUT / "validation.json"
    if p.exists():
        v = json.loads(p.read_text()).get("time_scale_best")
        if v:
            return float(v)
    return 1.2


def chain(name: str) -> mc.Chain:
    if "_x" in name:                      # e.g. "U1_x115" -> time_scale 1.15
        import dataclasses
        base, fs = name.split("_x")
        if name not in _chain_cache:
            _chain_cache[name] = dataclasses.replace(chain(base), time_scale=int(fs) / 100.0, label=name)
        return _chain_cache[name]
    if name.endswith("_cal"):
        import dataclasses
        if name not in _chain_cache:
            _chain_cache[name] = dataclasses.replace(chain(name[:-4]), time_scale=time_scale(),
                                                     label=name)
        return _chain_cache[name]
    if name not in _chain_cache:
        d, T, drog, lee, seas = CHAINS[name]
        grid = mc.MCGrid(d=d)
        t = time.time()
        pairs = mc.transition_pairs(grid, T, drogue=drog, leeway=lee)
        _chain_cache[name] = mc.build_chain(pairs, grid, T, seas, label=name)
        print(f"chain {name}: {pairs.start.size} pairs, {time.time() - t:.1f} s", flush=True)
    return _chain_cache[name]


def main():
    lat, lon = common_grid()
    dist, alat, alon, arc = D.arc_geometry(0.0)
    band = np.abs(dist) <= D.BAND_KM

    # ---- cell likelihoods for every configuration we need --------------------------------
    # Default chain = undrogued drifters + validated transit-speed calibration ("U1_cal").
    # Evidence / likelihood-choice variants use the default chain; structural chain variants
    # (annual, 0.5 deg, 7 d, drogued) are uncalibrated and compare with loglik_uncalibrated.
    configs = {
        "U1_cal": dict(chain="U1_cal"),
        "F1_cal": dict(chain="F1_cal"),
        "F1a10_cal": dict(chain="F1a10_cal"),
        "W3_cal": dict(chain="W3_cal"),
        "U1": dict(chain="U1"),
        "F1": dict(chain="F1"),
        "U1annual": dict(chain="U1annual"),
        "U05": dict(chain="U05"),
        "U1T7": dict(chain="U1T7"),
        "D1": dict(chain="D1"),
        "U1_cal_win2": dict(chain="U1_cal", window_scale=2.0),
        "F1_cal_win2": dict(chain="F1_cal", window_scale=2.0),
        "U1_cal_wingodfrey": dict(chain="U1_cal", nobarn=(15.0, 79.0), barn=(0.0, 10.0)),
        "U1_cal_r100": dict(chain="U1_cal", r_km=100.0),
        "U1_cal_r250": dict(chain="U1_cal", r_km=250.0),
        "U1_cal_wa12": dict(chain="U1_cal", wa_days=365.0),
        "U1_cal_royofficial": dict(chain="U1_cal", date_override={"sa_roy": "2016-03-22"}),
        "U1_cal_first": dict(chain="U1_cal", mode="first"),
        "U1_x110": dict(chain="U1_x110"),
        "U1_x115": dict(chain="U1_x115"),
        "U1_x125": dict(chain="U1_x125"),
        "F1_cal_first": dict(chain="F1_cal", mode="first"),
    }
    cl = {}
    for name, cfg in configs.items():
        cfg = dict(cfg)
        ch = chain(cfg.pop("chain"))
        cl[name] = D.cell_likelihoods(ch, dd.ITEMS, **cfg)

    # ---- map to common grid ---------------------------------------------------------------
    G = {}
    for name, c in cl.items():
        ch = chain(configs[name]["chain"])
        G[name] = {k: D.to_common_grid(ch.grid, L, c.valid, band) for k, L in c.item_L.items()}
        G[name]["__wa__"] = D.to_common_grid(ch.grid, c.p_wa, c.valid, band)

    all_keys = [it.key for it in dd.ITEMS]
    first_keys = [it.key for it in dd.first_per_region()]
    lam = dd.WA_LAMBDA

    def comb(cfg, keys, wa=True, lam_=lam, mix=None):
        """mix: dict item_key -> config name overriding the source of that item."""
        gi = {k: (G[mix[k]][k] if mix and k in mix else G[cfg][k]) for k in keys}
        tot, per = D.combine(None, gi, keys, G[cfg]["__wa__"] if wa else None, lam_)
        return tot, per

    variants = {}
    descr = {}
    def add(name, field, text):
        variants[name] = field
        descr[name] = text

    f = time_scale()
    base = ("undrogued-drifter chain (1 deg, 5 d, 3 seasons) with transit-speed calibration "
            f"f={f:.2f}")
    add("loglik", comb("U1_cal", all_keys)[0],
        f"DEFAULT: {base}; 15 debris observations; WA non-detection (lambda=20, 18 months)")
    add("loglik_drogued", comb("D1", all_keys)[0],
        "Chain from drogued (15 m drogue) drifters, uncalibrated (compare loglik_uncalibrated)")
    add("loglik_no_negative", comb("U1_cal", all_keys, wa=False)[0], "Default without the WA non-detection term")
    add("loglik_flaperon_only", comb("U1_cal", ["flaperon"], wa=False)[0],
        "Reunion flaperon only (default chain), no WA term")
    add("loglik_leeway", comb("U1_cal", all_keys, mix={"flaperon": "F1_cal"})[0],
        "CSIRO-like physics: flaperon from the chain with extra flaperon leeway (+0.10 m/s, 20 deg left of wind), other items and WA term from the default chain")
    add("loglik_flaperon_only_leeway", comb("F1_cal", ["flaperon"], wa=False)[0],
        "Flaperon only, flaperon-leeway chain (20 deg left), calibrated")
    add("loglik_flaperon_only_leeway10", comb("F1a10_cal", ["flaperon"], wa=False)[0],
        "Flaperon only, flaperon leeway at 10 deg left, calibrated")
    add("loglik_all_leeway", comb("F1_cal", all_keys)[0],
        "All items AND the WA term from the flaperon-leeway chain (upper bound on the leeway effect)")
    add("loglik_windage3", comb("W3_cal", all_keys)[0],
        "All items and WA from a ~3% windage chain (extra 1.8% of wind, downwind), calibrated")
    add("loglik_first_per_region", comb("U1_cal", first_keys)[0],
        "Only the first find in each of 7 regions (less double counting of correlated finds), WA term")
    add("loglik_first_arrival", comb("U1_cal_first", all_keys)[0],
        "Item likelihood = density of FIRST arrival in the find region within the window (default: presence in window)")
    add("loglik_windows_x2", comb("U1_cal_win2", all_keys)[0], "Reporting-delay windows doubled in length")
    add("loglik_windows_godfrey", comb("U1_cal_wingodfrey", all_keys)[0],
        "Godfrey (2021)-like delays: barnacled 0-10 d, barnacle-free 15-79 d")
    add("loglik_radius100", comb("U1_cal_r100", all_keys)[0], "Find-region radius 100 km (default 150)")
    add("loglik_radius250", comb("U1_cal_r250", all_keys)[0], "Find-region radius 250 km")
    add("loglik_wa_lambda5", comb("U1_cal", all_keys, lam_=5.0)[0], "WA term with lambda=5")
    add("loglik_wa_lambda60", comb("U1_cal", all_keys, lam_=60.0)[0], "WA term with lambda=60")
    add("loglik_wa_12months", comb("U1_cal_wa12", all_keys)[0], "WA window 12 months instead of 18")
    add("loglik_roy_official_date", comb("U1_cal_royofficial", all_keys)[0],
        "'Roy' at its official find date 22 Mar 2016 instead of first photo 23 Dec 2015")
    add("loglik_no_roy", comb("U1_cal", [k for k in all_keys if k != "sa_roy"])[0], "Excluding 'Roy'")
    add("loglik_leeway_windows_x2", comb("U1_cal_win2", all_keys, mix={"flaperon": "F1_cal_win2"})[0],
        "loglik_leeway with doubled windows")
    add("loglik_leeway_first_arrival", comb("U1_cal_first", all_keys, mix={"flaperon": "F1_cal_first"})[0],
        "loglik_leeway with the first-arrival formulation")
    for fs in ("110", "115", "125"):
        add(f"loglik_timescale_{fs}", comb(f"U1_x{fs}", all_keys)[0],
            f"Default with transit-speed factor {int(fs) / 100:.2f} instead of {f:.2f}")
    # uncalibrated chains (raw Markov chain transit speed) and structural variants
    add("loglik_uncalibrated", comb("U1", all_keys)[0], "Default without the transit-speed calibration")
    add("loglik_leeway_uncalibrated", comb("U1", all_keys, mix={"flaperon": "F1"})[0],
        "loglik_leeway without the transit-speed calibration")
    add("loglik_flaperon_only_uncalibrated", comb("U1", ["flaperon"], wa=False)[0],
        "Flaperon only, undrogued chain, uncalibrated")
    add("loglik_flaperon_only_leeway_uncalibrated", comb("F1", ["flaperon"], wa=False)[0],
        "Flaperon only, leeway chain, uncalibrated")
    add("loglik_annual", comb("U1annual", all_keys)[0], "Time-homogeneous (annual) chain, uncalibrated")
    add("loglik_bin05", comb("U05", all_keys)[0], "0.5 deg chain cells, uncalibrated")
    add("loglik_T7", comb("U1T7", all_keys)[0], "7-day transition step, uncalibrated")

    # per-item fields (default chain and leeway chain)
    items_U = {k: comb("U1_cal", [k], wa=False)[0] for k in all_keys}
    items_F = {k: comb("F1_cal", [k], wa=False)[0] for k in all_keys}
    wa_U = -lam * G["U1_cal"]["__wa__"]
    wa_F = -lam * G["F1_cal"]["__wa__"]

    # ---- NetCDF ---------------------------------------------------------------------------
    ds = xr.Dataset(coords={"lat": lat, "lon": lon})
    enc = {}
    def put(name, arr, attrs):
        ds[name] = (("lat", "lon"), np.where(band, arr, np.nan).astype(np.float32), attrs)
        enc[name] = {"zlib": True, "complevel": 4}
    for k, v in variants.items():
        put(k, v, {"long_name": descr[k], "units": "nats (log-likelihood, arbitrary additive constant)"})
    for k, v in items_U.items():
        put(f"loglik_item_{k}", v, {"long_name": f"log-likelihood of item {k} alone (default chain)"})
    for k, v in items_F.items():
        put(f"loglik_itemleeway_{k}", v, {"long_name": f"log-likelihood of item {k} alone (flaperon-leeway chain)"})
    put("loglik_wa_term", wa_U, {"long_name": "WA non-detection term -lambda*p_WA (default chain, lambda=20)"})
    put("p_wa", G["U1_cal"]["__wa__"], {"long_name": "P(reach WA coastal band within 18 months), default chain"})
    put("p_wa_leeway", G["F1_cal"]["__wa__"], {"long_name": "P(reach WA coastal band within 18 months), flaperon-leeway chain"})
    ds["dist_to_arc_km"] = (("lat", "lon"), dist.astype(np.float32),
                            {"long_name": "signed distance to the sea-level 7th arc (+ = east of arc)"})
    ds.attrs.update(dict(
        title="mh370-open workstream B: log-likelihood of the MH370 debris evidence vs origin",
        method="Markov chain from NOAA GDP 6-hourly drifters; presence-in-find-region during arrival windows; WA non-detection. See outputs/drift/README.md",
        release_time="2014-03-08T00:20Z", band_km=D.BAND_KM, wa_lambda=lam, eps_rel=D.EPS_REL,
        time_scale_speedcal=time_scale(), item_likelihood_mode=D.MODE,
        region_radius_km=D.R_KM,
        computed_region="cells within 300 km of the sea-level 7th arc; NaN elsewhere",
        sources="GDP 6h doi:10.25921/7ntx-z961; NCEP/NCAR R1; Natural Earth; MH370 SIR 2018 Table 1.12A",
    ))
    DER.mkdir(parents=True, exist_ok=True)
    path = DER / "drift_loglik.nc"
    if path.exists():
        path.unlink()
    ds.to_netcdf(path, engine="h5netcdf", encoding=enc)
    print("wrote", path)

    # ---- arc profiles ------------------------------------------------------------------------
    bins = np.round(np.arange(-44.0, -16.0 + 1e-9, 0.25), 3)
    lat_c = 0.5 * (bins[:-1] + bins[1:])
    arc_lon = np.array([geo.arc_lon_for_lat(la, geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0) for la in lat_c])
    prof = pd.DataFrame({"arc_lat": lat_c, "arc_lon": np.round(arc_lon, 3)})
    for k, v in variants.items():
        prof[k] = D.arc_profile(v, dist, alat, bins, max_km=100.0)
    keep = prof[list(variants)].notna().any(axis=1).to_numpy()
    prof = prof[keep]
    prof.to_csv(OUT / "arc_profile.csv", index=False, float_format="%.4f")
    # on-arc only (|d| <= 10 km) for reference
    prof0 = pd.DataFrame({"arc_lat": lat_c, "arc_lon": np.round(arc_lon, 3)})
    for k, v in variants.items():
        prof0[k] = D.arc_profile(v, dist, alat, bins, max_km=10.0)
    prof0 = prof0[keep]
    prof0.to_csv(OUT / "arc_profile_onarc.csv", index=False, float_format="%.4f")
    pit = pd.DataFrame({"arc_lat": lat_c})
    for k in all_keys:
        pit[f"{k}"] = D.arc_profile(items_U[k], dist, alat, bins)
    for k in all_keys:
        pit[f"{k}__leeway"] = D.arc_profile(items_F[k], dist, alat, bins)
    pit["wa_term"] = D.arc_profile(wa_U, dist, alat, bins)
    pit["wa_term__leeway"] = D.arc_profile(wa_F, dist, alat, bins)
    with np.errstate(divide="ignore"):
        pit["p_wa"] = np.exp(D.arc_profile(np.log(G["U1_cal"]["__wa__"]), dist, alat, bins))
        pit["p_wa__leeway"] = np.exp(D.arc_profile(np.log(G["F1_cal"]["__wa__"]), dist, alat, bins))
    pit = pit[keep]
    pit.to_csv(OUT / "arc_profile_items.csv", index=False, float_format="%.4f")

    # ---- summary ------------------------------------------------------------------------------
    rows = []
    for k in variants:
        for w in (1.0, 0.5):
            s = D.profile_summary(prof.arc_lat.to_numpy(), w * prof[k].to_numpy())
            rows.append(dict(variant=k, w=w, **{a: round(b, 2) for a, b in s.items()}, description=descr[k]))
    for k in all_keys:
        for tag, src in (("undrogued", items_U), ("leeway", items_F)):
            s = D.profile_summary(lat_c[keep], D.arc_profile(src[k], dist, alat, bins)[keep])
            rows.append(dict(variant=f"item:{k}:{tag}", w=1.0, **{a: round(b, 2) for a, b in s.items()},
                             description=dd.ITEM_BY_KEY[k].name))
    summ = pd.DataFrame(rows)
    summ.to_csv(OUT / "profile_summary.csv", index=False)
    print(summ[summ.w == 1.0][["variant", "peak", "mean", "sd", "q16", "q84", "q025", "q975", "range_loglik"]]
          .to_string(index=False))
    dd.table().to_csv(OUT / "debris_items.csv", index=False)
    # arc-marginal likelihood of each variant (uniform prior 42S-20S): comparable between drift
    # physics because item likelihoods are probabilities (differences = log Bayes factors, w=1)
    m = (prof.arc_lat >= -42) & (prof.arc_lat <= -20)
    ev = []
    for k in variants:
        v = prof[k][m].to_numpy()
        mx = np.nanmax(v)
        ev.append(dict(variant=k, log_marginal=mx + np.log(np.nanmean(np.exp(v - mx))), max=mx))
    ev = pd.DataFrame(ev)
    ev["minus_default"] = ev.log_marginal - ev.log_marginal[ev.variant == "loglik"].iloc[0]
    ev.to_csv(OUT / "model_evidence.csv", index=False, float_format="%.3f")
    # diagnostics for the README
    diag = {}
    for name in ["U1", "D1", "F1", "U05"]:
        ch = chain(name)
        la, lo = ch.grid.cell_centres()
        nearc = (np.abs(lo - np.interp(la, arc[:, 0], arc[:, 1])) < 4) & (la > -42) & (la < -20)
        diag[name] = dict(
            n_cells_with_data=int((ch.counts[-1] > 0).sum()),
            min_pairs_near_arc=int(ch.counts[-1][nearc].min()),
            median_pairs_near_arc=float(np.median(ch.counts[-1][nearc])),
            wa_cells=int(D.wa_cells(ch.grid, D.valid_cells(ch)).size),
        )
    (OUT / "chain_diagnostics.json").write_text(json.dumps(diag, indent=1))
    print(json.dumps(diag, indent=1))


if __name__ == "__main__":
    main()
