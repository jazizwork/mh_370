"""Workstream B (drift): likelihood of the MH370 floating-debris evidence as a function of
origin location near the 7th arc.

Model: a Markov chain (transition matrix) of surface drift built from NOAA Global Drifter
Program 6-hourly undrogued drifters (see drift_mc.py), with a transit-speed calibration fitted
to held-out drifters (drift_validate.py), propagated from 8 March 2014 00:20 UTC.
For each debris item k (drift_debris.py) the likelihood of origin x is (default, MODE="visit")

    L_k(x) = P( object is in / enters the find region R_k at some time during the arrival
                window [t_k - d_max, t_k - d_min] | x )        (not stranded there earlier)

with t_k the find date and d the reporting delay (uniform window). MODE="first" uses instead the
density of the FIRST entry into R_k within the window. R_k = chain cells whose centre is within
R_KM of the find site (afloat or stranded there). The negative evidence (no debris reported from
Western Australia) enters as a Poisson non-detection term

    log P(no WA reports | x) = - lambda * P( reach WA coastal band within WA_DAYS | x ).

Total: loglik(x) = sum_k log(L_k(x) + eps_k) + log P(no WA | x), where eps_k = EPS_REL *
max_x L_k (a small "model failure" floor so that one item cannot veto an origin by more than
~ln(1/EPS_REL)). Origins are mapped onto the common 0.05-deg grid by bilinear mixing of the
chain cells' likelihoods (exact for a release distribution spread over neighbouring cells).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mh370 import geo
from mh370 import drift_debris as dd
from mh370 import drift_mc as mc
from mh370.drift_data import dist_to_coast_km

R_KM = 150.0
EPS_REL = 1e-3
BAND_KM = 300.0          # computed band either side of the 7th arc
MODE = "visit"           # item likelihood formulation (see cell_likelihoods)


# --------------------------------------------------------------------------------------
# Regions
# --------------------------------------------------------------------------------------
def valid_cells(chain: mc.Chain, min_count: int = 1) -> np.ndarray:
    return chain.counts[-1] >= min_count


def item_region(chain: mc.Chain, item: dd.Item, r_km: float = R_KM) -> np.ndarray:
    cells = mc.cells_within(chain.grid, item.lat, item.lon, r_km, valid_cells(chain))
    return mc.region_states(chain.grid, cells)


def wa_cells(grid: mc.MCGrid, valid: np.ndarray, coast_km: float = dd.WA_COAST_KM) -> np.ndarray:
    la, lo = grid.cell_centres()
    m = (la >= dd.WA_LAT[0]) & (la <= dd.WA_LAT[1]) & (lo >= dd.WA_LON_MIN) & valid
    idx = np.flatnonzero(m)
    dist = dist_to_coast_km(la[idx], lo[idx])
    return idx[dist <= coast_km]


def wa_region(chain: mc.Chain, coast_km: float = dd.WA_COAST_KM) -> np.ndarray:
    return mc.region_states(chain.grid, wa_cells(chain.grid, valid_cells(chain), coast_km))


# --------------------------------------------------------------------------------------
# Likelihood on chain cells
# --------------------------------------------------------------------------------------
@dataclass
class CellLik:
    """Per-chain-cell quantities (arrays of length grid.nc)."""
    chain_label: str
    item_L: dict          # key -> L_k (per day)
    item_window: dict     # key -> (a, b) days
    p_wa: np.ndarray      # P(reach WA band by WA_DAYS)
    wa_days: float
    valid: np.ndarray


def cell_likelihoods(chain: mc.Chain, items: list[dd.Item], window_scale: float = 1.0,
                     r_km: float = R_KM, wa_days: float = dd.WA_DAYS,
                     nobarn=dd.NOBARN_WINDOW, barn=dd.BARN_WINDOW,
                     date_override: dict | None = None, mode: str = MODE) -> CellLik:
    """mode = "visit": L_k = P(object present in / entering R_k during the arrival window)
                        (Godfrey 2021 / Ulich & Iannello 2023-style distance-time window);
       mode = "first": L_k = P(FIRST entry into R_k falls in the window) / window length."""
    if mode == "visit":
        return _cell_likelihoods_visit(chain, items, window_scale, r_km, wa_days, nobarn, barn,
                                       date_override)
    T = chain.step_days
    regions, steps, meta = [], [], []
    windows = {}
    for it in items:
        if date_override and it.key in date_override:
            it = dd.Item(**{**it.__dict__, "date": date_override[it.key]})
        a, b = it.window(window_scale, nobarn=nobarn, barn=barn)
        windows[it.key] = (a, b)
        r = item_region(chain, it, r_km)
        for tau in (a, b):
            n0 = int(np.floor(tau / T))
            for n in (n0, n0 + 1):
                regions.append(r)
                steps.append(max(n, 0))
                meta.append((it.key, tau, n))
    rwa = wa_region(chain)
    n0 = int(np.floor(wa_days / T))
    for n in (n0, n0 + 1):
        regions.append(rwa)
        steps.append(n)
        meta.append(("__wa__", wa_days, n))
    H = mc.hitting_probability(chain, regions, steps, dd.RELEASE_TIME)
    nc = chain.grid.nc
    Hc = {(k, n): H[:nc, c] for c, (k, tau, n) in enumerate(meta)}

    def H_at(key, tau):
        n0 = int(np.floor(tau / T))
        f = tau / T - n0
        return (1 - f) * Hc[(key, max(n0, 0))] + f * Hc[(key, max(n0 + 1, 0))]

    item_L = {}
    for it in items:
        a, b = windows[it.key]
        item_L[it.key] = np.clip(H_at(it.key, b) - H_at(it.key, a), 0, None) / (b - a)
    p_wa = H_at("__wa__", wa_days)
    return CellLik(chain.label, item_L, windows, p_wa, wa_days, valid_cells(chain))


def _cell_likelihoods_visit(chain, items, window_scale, r_km, wa_days, nobarn, barn, date_override):
    T = chain.step_days
    cells, na, nb, windows = [], [], [], {}
    valid = valid_cells(chain)
    for it in items:
        if date_override and it.key in date_override:
            it = dd.Item(**{**it.__dict__, "date": date_override[it.key]})
        a, b = it.window(window_scale, nobarn=nobarn, barn=barn)
        windows[it.key] = (a, b)
        cells.append(mc.cells_within(chain.grid, it.lat, it.lon, r_km, valid))
        na.append(int(round(a / T)))
        nb.append(max(int(round(b / T)), int(round(a / T)) + 1))
    wa = wa_cells(chain.grid, valid)
    cells.append(wa)
    na.append(0)
    nb.append(int(round(wa_days / T)))
    V = mc.visit_probability(chain, cells, na, nb, dd.RELEASE_TIME)
    nc = chain.grid.nc
    item_L = {it.key: V[:nc, c] for c, it in enumerate(items)}
    return CellLik(chain.label, item_L, windows, V[:nc, -1], wa_days, valid)


# --------------------------------------------------------------------------------------
# Mapping to the common grid
# --------------------------------------------------------------------------------------
def arc_geometry(h_m: float = 0.0):
    """Common-grid distance to the 7th arc (km, signed: + east/outside), the latitude and
    longitude of the nearest arc point, and the arc polyline."""
    from scipy.spatial import cKDTree
    from mh370.grid import common_grid
    lat, lon = common_grid()
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, h_m,
                           lats=np.arange(-50.0, -5.0 + 1e-9, 0.01))
    def xyz(la, lo):
        la, lo = np.radians(la), np.radians(lo)
        return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
    tree = cKDTree(xyz(arc[:, 0], arc[:, 1]))
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    d, j = tree.query(xyz(LA.ravel(), LO.ravel()))
    dist = 2 * 6371.0088 * np.arcsin(np.clip(d / 2, 0, 1))
    alat = arc[j, 0]
    alon = arc[j, 1]
    # sign: positive if the point is at larger longitude than the arc at the same latitude
    sign = np.where(LO.ravel() >= np.interp(LA.ravel(), arc[:, 0], arc[:, 1]), 1.0, -1.0)
    shape = LA.shape
    return (dist * sign).reshape(shape), alat.reshape(shape), alon.reshape(shape), arc


def to_common_grid(grid: mc.MCGrid, values: np.ndarray, valid: np.ndarray,
                   mask: np.ndarray) -> np.ndarray:
    """Bilinear (NaN-aware) interpolation of a per-cell field onto the common grid where
    mask is True; NaN elsewhere."""
    from scipy.interpolate import RegularGridInterpolator
    from mh370.grid import common_grid
    lat, lon = common_grid()
    v = np.where(valid, values, 0.0).reshape(grid.nlat, grid.nlon)
    w = valid.astype(float).reshape(grid.nlat, grid.nlon)
    kw = dict(method="linear", bounds_error=False, fill_value=np.nan)
    fv = RegularGridInterpolator((grid.lat_c, grid.lon_c), v, **kw)
    fw = RegularGridInterpolator((grid.lat_c, grid.lon_c), w, **kw)
    LA, LO = np.meshgrid(lat, lon, indexing="ij")
    pts = np.c_[LA[mask], LO[mask]]
    out = np.full(LA.shape, np.nan)
    ww = fw(pts)
    with np.errstate(invalid="ignore", divide="ignore"):
        out[mask] = np.where(ww > 0.25, fv(pts) / ww, np.nan)
    return out


def combine(cl_by_item: dict, grid_by_item: dict, keys: list[str], p_wa_grid: np.ndarray | None,
            lam: float = dd.WA_LAMBDA, eps_rel: float = EPS_REL) -> tuple[np.ndarray, dict]:
    """Sum of item log-likelihoods (+ WA term) on the common grid."""
    total = None
    per_item = {}
    for k in keys:
        L = grid_by_item[k]
        eps = eps_rel * np.nanmax(L)
        ll = np.log(L + eps)
        per_item[k] = ll
        total = ll if total is None else total + ll
    if p_wa_grid is not None and lam > 0:
        total = total - lam * p_wa_grid
    return total, per_item


def arc_profile(field: np.ndarray, dist_km: np.ndarray, alat: np.ndarray,
                lat_bins: np.ndarray, max_km: float = 100.0) -> np.ndarray:
    """log-mean-exp of a log-likelihood field across the arc (|dist| <= max_km) in bins of
    nearest-arc latitude. Uniform weight across the arc."""
    out = np.full(lat_bins.size - 1, np.nan)
    m0 = np.isfinite(field) & (np.abs(dist_km) <= max_km)
    idx = np.digitize(alat[m0], lat_bins) - 1
    vals = field[m0]
    for b in range(lat_bins.size - 1):
        v = vals[idx == b]
        if v.size:
            mx = v.max()
            out[b] = mx + np.log(np.mean(np.exp(v - mx)))
    return out


def profile_summary(lat_c: np.ndarray, ll: np.ndarray, lo: float = -42.0, hi: float = -20.0):
    """Peak latitude, posterior mean/sd and 68%/95% equal-tail intervals of exp(ll) with a
    uniform prior along the arc between lo and hi."""
    m = np.isfinite(ll) & (lat_c >= lo) & (lat_c <= hi)
    x, y = lat_c[m], ll[m]
    p = np.exp(y - y.max())
    p /= p.sum()
    c = np.cumsum(p)
    q = lambda a: float(np.interp(a, c, x))
    mean = float((p * x).sum())
    return dict(peak=float(x[np.argmax(y)]), mean=mean, sd=float(np.sqrt((p * (x - mean) ** 2).sum())),
                q16=q(0.16), q84=q(0.84), q025=q(0.025), q975=q(0.975),
                range_loglik=float(y.max() - y.min()))
