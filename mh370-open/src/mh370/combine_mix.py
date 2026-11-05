"""Workstream C, part 3: model-misspecification mixture (reviewer response).

The block ranking of `combine.py` is conditional on the satellite (BTO/BFO + simple autopilot path)
layer being right, yet that same model says the past searches had only a 3-18 % chance of all coming
up empty. Here the end-point prior is a two-component mixture

    pi(x) = (1 - eps) * p_sat(x) + eps * p_broad(x)

where p_broad ("the satellite path model is wrong") is a broad layer that does NOT use where the path
model puts the end point along the arc. The evidence then updates the component weights as well as
the location:

    posterior(x)  ∝  pi(x) * exp(w * drift_loglik(x)) * (1 - pod(x))

With   q_k  = p_k exp(w ll) / Z_k        (component k after the drift evidence),
       Z_k  = sum p_k exp(w ll)          (drift evidence for component k, common arbitrary constant),
       N_k  = 1 - sum q_k pod            (P(every past search misses | component k, drift)),
the component weights are
       eps_drift = eps Z_b / ((1 - eps) Z_s + eps Z_b)
       eps_post  = eps_drift N_b / ((1 - eps_drift) N_s + eps_drift N_b)
and the posterior is the weight-averaged component posteriors  post_k = q_k (1 - pod) / N_k.
N_s / N_b is the Bayes factor of the null search result for "satellite model right" vs "broad".

Broad components (common grid, each sums to 1):

* broad_arc : crossing point uniform in latitude of the sea-level 7th arc over 20-42 S; then the
  SAME end-of-flight kernel as the satellite layer's default `p` (replicated from
  scripts/satcom_posterior.py: 0.8 x uncontrolled [+5 NM along final track, Gaussian sd 7 NM per
  axis] + 0.2 x piloted glide [uniform 0-120 NM along final track, direction sd 15 deg], each
  gridded as a 2-D histogram smoothed by a 1-cell Gaussian and normalised). The kernel needs a
  start state at 00:19:29: the cross-arc offset of the aircraft from the sea-level arc (it is at
  cruise altitude, so on the higher BTO arc) and the angle between its final track and the arc
  normal. Both are drawn jointly from the satcom SMC end states pooled over ALL five autopilot
  modes with EQUAL weight (offset +3..+49 km, angle 29-44 deg). Only this local geometry is
  borrowed from the path model - not the along-arc position.
* broad_wide: crossing latitude as broad_arc, cross-arc offset uniform in +/-150 km of the
  sea-level arc (end-of-flight model also wrong). Same gridding.
* broad_arc_lnavctt: as broad_arc, but the 00:19:29 start geometry is pooled over LNAV and CTT only
  (the modes that carry the satellite layer's weight): the aircraft starts closer to the sea-level arc
  (offset +2..+25 km, angle 42-44 deg). Sensitivity of the broad component's cross-arc profile.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import xarray as xr
from scipy.ndimage import gaussian_filter

from . import combine, geo, grid, search

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"
BROAD_FILE = DERIVED / "combine_broad_components.nc"
SMC_DIR = DERIVED / "satcom_smc"
NM = 1852.0

# ---- end-of-flight kernel: replicated from scripts/satcom_posterior.py (default layer `p`) ----
# (self-test TM8 checks these numbers against that script so the two cannot silently diverge)
EOF_DEFAULT_W_GLIDE = 0.2
UNC_ALONG_NM, UNC_SIGMA_NM = 5.0, 7.0
GLIDE_MAX_NM, GLIDE_DIR_SD = 120.0, 15.0
GRID_SMOOTH_CELLS = 1.0

# ---- broad component definition --------------------------------------------------------------
BROAD_LAT_RANGE = (-42.0, -20.0)   # arc latitude of the 7th-arc crossing (uniform)
WIDE_HALF_KM = 150.0               # broad_wide: uniform cross-arc offset +/- this
MODES = ("LNAV", "CTT", "CMT", "CTH", "CMH")
# fallback start geometry if the SMC end states are not available (pooled medians/ranges)
FALLBACK_N0_KM = (3.0, 49.0)
FALLBACK_THETA_DEG = (29.0, 44.0)
BROAD_NAMES = ("broad_arc", "broad_wide", "broad_arc_lnavctt")
LNAVCTT = ("LNAV", "CTT")


# ------------------------------------------------------------------------------------------------
# geometry helpers
# ------------------------------------------------------------------------------------------------
def _arc_tables():
    """Sea-level 7th arc (lat ascending), lon and outward-normal azimuth at every arc node."""
    la, lo, _ = search.arc_dense()
    o = np.argsort(la)
    la, lo = la[o], lo[o]
    az_t = np.empty(la.size)
    az_t[1:-1] = search.GEOD.inv(lo[:-2], la[:-2], lo[2:], la[2:])[0]
    az_t[0], az_t[-1] = az_t[1], az_t[-2]
    k = la.size // 2
    ref = search.arc_normal_bearing(la[k], lo[k])
    sgn = 1.0 if abs(((az_t[k] + 90.0 - ref) + 180.0) % 360.0 - 180.0) < 1.0 else -1.0
    az_n = np.unwrap(np.radians(az_t + sgn * 90.0))
    return la, lo, np.degrees(az_n)


def pooled_start_geometry(smc_dir=SMC_DIR, variant="baseline", n_per_mode=20000, seed=1, modes=MODES):
    """Cross-arc offset n0 (km, + = beyond the sea-level arc) and track-minus-outward-normal angle
    theta (deg) of the aircraft at 00:19:29, pooled over all autopilot modes with equal weight.
    Returns (n0, theta, info)."""
    rng = np.random.default_rng(seed)
    la_t, lo_t, az_t = _arc_tables()
    n0s, ths, used = [], [], []
    for m in modes:
        f = Path(smc_dir) / f"{variant}_{m}.npz"
        if not f.exists():
            continue
        z = np.load(f, allow_pickle=False)
        i = int(np.argmin(np.abs(z["t_meas"] - geo.ARC7_TIME)))
        la, lo = z["lat"][:, i], z["lon"][:, i]
        trk = np.degrees(np.arctan2(z["ve"][:, i], z["vn"][:, i])) % 360.0
        k = rng.choice(la.size, min(n_per_mode, la.size), replace=False)
        _, n = search.arc_coords(la[k], lo[k])
        nb = np.interp(la[k], la_t, az_t)
        th = ((trk[k] - nb + 180.0) % 360.0) - 180.0
        n0s.append(n)
        ths.append(th)
        used.append(m)
    if not used:
        n = 4000
        info = dict(source="fallback (no SMC end states found)", modes=[],
                    n0_km=FALLBACK_N0_KM, theta_deg=FALLBACK_THETA_DEG)
        return rng.uniform(*FALLBACK_N0_KM, n), rng.uniform(*FALLBACK_THETA_DEG, n), info
    m_ = min(len(x) for x in n0s)  # equal weight per mode
    n0 = np.concatenate([x[:m_] for x in n0s])
    th = np.concatenate([x[:m_] for x in ths])
    info = dict(source=f"satcom SMC end states ({variant}), equal weight per mode", modes=used,
                n_per_mode=int(m_),
                n0_km_5_50_95=np.percentile(n0, [5, 50, 95]).round(1).tolist(),
                theta_deg_5_50_95=np.percentile(th, [5, 50, 95]).round(1).tolist())
    return n0, th, info


def to_grid(lat, lon, w=None):
    """Histogram part of scripts/satcom_posterior.to_grid (bins = common-grid cells). Returns
    (raw weighted counts, fraction of the weight inside the grid); smoothing and normalisation are
    applied once to the accumulated counts by _finish (1-cell Gaussian, as in the satcom script)."""
    LAT, LON = grid.common_grid()
    elat = np.r_[LAT - 0.025, LAT[-1] + 0.025]
    elon = np.r_[LON - 0.025, LON[-1] + 0.025]
    if w is None:
        w = np.ones(np.size(lat))
    h, _, _ = np.histogram2d(lat, lon, bins=[elat, elon], weights=w)
    return h, float(h.sum() / w.sum())


def _finish(h, smooth=GRID_SMOOTH_CELLS):
    if smooth:
        h = gaussian_filter(h, smooth, mode="constant")
    return h / h.sum()


def sample_eof(lat, lon, trk, scenario, rng):
    """Replica of scripts/satcom_posterior.sample_eof for one draw per start point."""
    from .satcom_paths import destination
    n = lat.size
    if scenario == "uncontrolled":
        dx = UNC_ALONG_NM * np.sin(np.radians(trk)) + rng.normal(0, UNC_SIGMA_NM, n)
        dy = UNC_ALONG_NM * np.cos(np.radians(trk)) + rng.normal(0, UNC_SIGMA_NM, n)
        brg, dist = np.degrees(np.arctan2(dx, dy)), np.hypot(dx, dy)
    elif scenario == "glide":
        brg = trk + rng.normal(0, GLIDE_DIR_SD, n)
        dist = rng.uniform(0, GLIDE_MAX_NM, n)
    else:
        raise ValueError(scenario)
    return destination(lat, lon, brg, dist * NM)


def _arc_starts(n, rng, la_t, lo_t, az_t, lat_range=BROAD_LAT_RANGE):
    lat0 = rng.uniform(lat_range[0], lat_range[1], n)
    return lat0, np.interp(lat0, la_t, lo_t), np.interp(lat0, la_t, az_t)


def build_broad_components(n_draws=8_000_000, chunk=2_000_000, seed=2026, lat_range=BROAD_LAT_RANGE,
                           wide_half_km=WIDE_HALF_KM, smc_dir=SMC_DIR):
    """Monte-Carlo build of the broad components on the common grid. Returns (dict name->array,
    info dict)."""
    from .satcom_paths import destination
    rng = np.random.default_rng(seed)
    la_t, lo_t, az_t = _arc_tables()
    pools = {"": pooled_start_geometry(smc_dir), "_lnavctt": pooled_start_geometry(smc_dir, modes=LNAVCTT)}
    shape = (grid.LAT.size, grid.LON.size)
    hist = {k: np.zeros(shape) for k in ("unc", "glide", "unc_lnavctt", "glide_lnavctt", "wide")}
    tot = {k: 0.0 for k in hist}
    done = 0
    while done < n_draws:
        n = min(chunk, n_draws - done)
        # --- broad_arc(_lnavctt): uniform arc latitude -> pooled 00:19:29 offset/track -> satcom EOF kernel
        for sfx, (n0_pool, th_pool, _) in pools.items():
            lat0, lon0, nb = _arc_starts(n, rng, la_t, lo_t, az_t, lat_range)
            k = rng.integers(0, n0_pool.size, n)
            la1, lo1 = destination(lat0, lon0, nb, n0_pool[k] * 1000.0)  # signed offset along the normal
            trk = (nb + th_pool[k]) % 360.0
            for sc, key in (("uncontrolled", "unc"), ("glide", "glide")):
                la2, lo2 = sample_eof(la1, lo1, trk, sc, rng)
                h, _ = to_grid(la2, lo2)
                hist[key + sfx] += h
                tot[key + sfx] += n
        # --- broad_wide: uniform arc latitude, uniform cross-arc offset +/- wide_half_km
        lat0, lon0, nb = _arc_starts(n, rng, la_t, lo_t, az_t, lat_range)
        off = rng.uniform(-wide_half_km, wide_half_km, n)
        la2, lo2 = destination(lat0, lon0, nb, off * 1000.0)
        h, _ = to_grid(la2, lo2)
        hist["wide"] += h
        tot["wide"] += n
        done += n
    inside = {k: float(hist[k].sum() / tot[k]) for k in hist}
    p_unc, p_gl = _finish(hist["unc"]), _finish(hist["glide"])
    p_unc2, p_gl2 = _finish(hist["unc_lnavctt"]), _finish(hist["glide_lnavctt"])
    layers = dict(broad_arc=(1 - EOF_DEFAULT_W_GLIDE) * p_unc + EOF_DEFAULT_W_GLIDE * p_gl,
                  broad_arc_uncontrolled=p_unc, broad_arc_glide=p_gl,
                  broad_wide=_finish(hist["wide"]),
                  broad_arc_lnavctt=(1 - EOF_DEFAULT_W_GLIDE) * p_unc2 + EOF_DEFAULT_W_GLIDE * p_gl2)
    info = dict(lat_range=list(lat_range), wide_half_km=wide_half_km, n_draws=int(n_draws), seed=seed,
                start_geometry=pools[""][2], start_geometry_lnavctt=pools["_lnavctt"][2],
                mass_inside_grid_before_renorm=inside,
                eof=dict(w_glide=EOF_DEFAULT_W_GLIDE, unc_along_nm=UNC_ALONG_NM, unc_sigma_nm=UNC_SIGMA_NM,
                         glide_max_nm=GLIDE_MAX_NM, glide_dir_sd=GLIDE_DIR_SD, smooth_cells=GRID_SMOOTH_CELLS))
    return layers, info


def load_or_build_broad(path=BROAD_FILE, rebuild=False, **kw):
    path = Path(path)
    if path.exists() and not rebuild:
        ds = xr.open_dataset(path, engine="h5netcdf").load()
        combine.check_grid(ds, "broad components")
        if all(k in ds for k in BROAD_NAMES):
            info = json.loads(ds.attrs.get("build_info", "{}"))
            return {v: np.asarray(ds[v].values, float) for v in ds.data_vars}, info
        ds.close()  # cache predates a component: rebuild
    layers, info = build_broad_components(**kw)
    lat, lon = grid.common_grid()
    ds = xr.Dataset({k: (("lat", "lon"), v.astype(np.float32)) for k, v in layers.items()},
                    coords={"lat": lat, "lon": lon})
    ds.attrs = dict(title="Broad 'satellite path model is wrong' components for the combine mixture",
                    workstream="C (combine)", method="see src/mh370/combine_mix.py and outputs/combine/README.md",
                    build_info=json.dumps(info))
    ds["broad_arc"].attrs["long_name"] = ("uniform in 7th-arc latitude 20-42 S x satcom default end-of-flight "
                                          "kernel (0.8 uncontrolled + 0.2 glide)")
    ds["broad_wide"].attrs["long_name"] = f"uniform in 7th-arc latitude 20-42 S x uniform +/-{WIDE_HALF_KM:g} km across the arc"
    ds["broad_arc_lnavctt"].attrs["long_name"] = ("as broad_arc, start geometry at 00:19:29 pooled over LNAV and CTT only "
                                                  "(closer to the arc)")
    for k in ds.data_vars:
        ds[k].attrs["units"] = "probability per 0.05x0.05 deg cell"
    path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(ds, str(path))
    return {k: np.asarray(v, float) for k, v in layers.items()}, info


# ------------------------------------------------------------------------------------------------
# mixture update
# ------------------------------------------------------------------------------------------------
def _clean(p):
    p = np.where(np.isfinite(p) & (p > 0), np.asarray(p, float), 0.0)
    return combine.normalise(p)


def mixture_posterior(p_sat, p_broad, eps, drift_ll=None, w=0.0, pod=None, searched_frac=None):
    """Two-component mixture update (see module docstring). Returns a dict with the mixture
    prior/posterior, the component posteriors and the weight bookkeeping."""
    if not 0.0 <= eps <= 1.0:
        raise ValueError("eps must be in [0, 1]")
    ps, pb = _clean(p_sat), _clean(p_broad)
    prior0 = (1.0 - eps) * ps + eps * pb
    # drift factor, centred on the mixture-prior-weighted mean likelihood; NaN cells -> 0 (neutral)
    f, info_d = combine.tempered_log_factor(drift_ll, w, prior0)
    sup = prior0 > 0
    f = f - (f[sup].max() if sup.any() else 0.0)
    L = np.exp(f)
    Zs, Zb = float(np.sum(ps * L)), float(np.sum(pb * L))
    qs = ps * L / Zs if Zs > 0 else np.zeros_like(ps)
    qb = pb * L / Zb if Zb > 0 else np.zeros_like(pb)
    eps_d = eps * Zb / ((1.0 - eps) * Zs + eps * Zb) if eps > 0 else 0.0
    if pod is None:
        pod = np.zeros_like(ps)
    pod = np.clip(np.nan_to_num(np.asarray(pod, float), nan=0.0), 0.0, 1.0)
    Ns, Nb = 1.0 - float(np.sum(qs * pod)), 1.0 - float(np.sum(qb * pod))
    den = (1.0 - eps_d) * Ns + eps_d * Nb
    eps_post = eps_d * Nb / den if eps_d > 0 else 0.0
    post_s = qs * (1.0 - pod) / Ns if Ns > 0 else np.zeros_like(qs)
    post_b = qb * (1.0 - pod) / Nb if Nb > 0 else np.zeros_like(qb)
    post = (1.0 - eps_post) * post_s + eps_post * post_b
    prior = (1.0 - eps_d) * qs + eps_d * qb
    out = dict(prior=prior, post=post, prior_sat=qs, prior_broad=qb, post_sat=post_s, post_broad=post_b,
               eps=float(eps), eps_drift=float(eps_d), eps_post=float(eps_post),
               p_null_sat=Ns, p_null_broad=Nb, p_null_mix=float(den),
               bf_null_sat_vs_broad=Ns / Nb if Nb > 0 else np.inf,
               bf_drift_sat_vs_broad=Zs / Zb if Zb > 0 else np.inf,
               drift_info=info_d)
    if searched_frac is not None:
        out["split_mix"] = combine.search_split(prior, pod, searched_frac)
        out["split_sat"] = combine.search_split(qs, pod, searched_frac)
        out["split_broad"] = combine.search_split(qb, pod, searched_frac)
    return out


def box_mass(af, node_mass, row):
    """Mass of a node raster inside a fixed arc-aligned box (row with s0_km, s1_km, n0_km, n1_km)."""
    ss = (af.s > row["s0_km"]) & (af.s < row["s1_km"])
    nn = (af.n > row["n0_km"]) & (af.n < row["n1_km"])
    return float(node_mass[np.ix_(ss, nn)].sum())


def kernel_constants_from_satcom_script(path=ROOT / "scripts" / "satcom_posterior.py"):
    """Parse the end-of-flight constants of the satcom script (for the replication self-test)."""
    import re
    txt = Path(path).read_text()
    out = {}
    m = re.search(r"EOF_DEFAULT_W_GLIDE\s*=\s*([0-9.]+)", txt)
    out["w_glide"] = float(m.group(1)) if m else None
    m = re.search(r"UNC_ALONG_NM,\s*UNC_SIGMA_NM\s*=\s*([0-9.]+),\s*([0-9.]+)", txt)
    out["unc"] = (float(m.group(1)), float(m.group(2))) if m else None
    m = re.search(r"GLIDE_MAX_NM,\s*GLIDE_DIR_SD\s*=\s*([0-9.]+),\s*([0-9.]+)", txt)
    out["glide"] = (float(m.group(1)), float(m.group(2))) if m else None
    m = re.search(r"def to_grid\(lat, lon, w, smooth=([0-9.]+)\)", txt)
    out["smooth"] = float(m.group(1)) if m else None
    return out
