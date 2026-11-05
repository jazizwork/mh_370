"""Workstream C, part 2: combine the independent evidence layers and rank unsearched areas.

    posterior  ∝  satcom_p  ×  exp(w · drift_loglik)  ×  [exp(w_ac · acoustic_loglik)]  ×  (1 − pod)

* satcom_p: probability per cell (var `p` and scenario vars `p_*`), normalised here.
* drift_loglik / acoustic_loglik: log-likelihoods with an arbitrary additive constant and NaN
  where not computed. NaN cells are treated as UNINFORMATIVE: after tempering by w the layer
  is centred on its prior-weighted log-mean-exp over the computed cells, and NaN cells get 0
  (= the average likelihood). The prior mass that falls in NaN cells is reported as a flag.
* pod: probability of detection of past searches (search_pod.nc, `pod`, `pod_low`, `pod_high`).

Ranking uses a regular raster in the 7th-arc frame (s = along-arc km, n = signed cross-arc km,
+ = farther from the satellite) so that candidate blocks are arc-aligned rectangles - the shape
a search would actually be planned as. A free-form greedy region-growing block and the
non-contiguous highest-density set are reported as upper-bound benchmarks.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import xarray as xr

from . import grid, search

ROOT = Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"

# drift variables that are NOT alternative whole-evidence log-likelihoods
DRIFT_EXCLUDE_PREFIX = ("loglik_item_", "loglik_itemleeway_", "loglik_wa_term")


class GridError(ValueError):
    pass


# ---------------------------------------------------------------------------------------
# input handling
# ---------------------------------------------------------------------------------------
def check_grid(ds: xr.Dataset, name: str):
    lat, lon = grid.common_grid()
    if "lat" not in ds.coords or "lon" not in ds.coords:
        raise GridError(f"{name}: missing lat/lon coordinates")
    if ds.lat.size != lat.size or ds.lon.size != lon.size or \
            not np.allclose(ds.lat.values, lat, atol=1e-6) or not np.allclose(ds.lon.values, lon, atol=1e-6):
        raise GridError(f"{name}: not on the common grid (lat {ds.lat.size}, lon {ds.lon.size})")


def open_layer(path, name, required):
    path = Path(path)
    if not path.exists():
        return None
    ds = xr.open_dataset(path, engine="h5netcdf").load()
    check_grid(ds, name)
    if required not in ds:
        raise KeyError(f"{name}: required variable '{required}' not found in {path}")
    for v in ds.data_vars:
        if ds[v].dims != ("lat", "lon"):
            ds[v] = ds[v].transpose("lat", "lon")
    return ds


def satcom_scenarios(ds: xr.Dataset) -> dict:
    """{name: normalised probability array} for `p` and every `p_*` variable."""
    out = {}
    for v in ds.data_vars:
        if v == "p" or v.startswith("p_"):
            a = np.asarray(ds[v].values, float)
            a = np.where(np.isfinite(a) & (a > 0), a, 0.0)
            s = a.sum()
            if s <= 0:
                continue
            out[v] = a / s
    if "p" not in out:
        raise KeyError("satcom: variable 'p' missing or empty")
    return out


def loglik_variants(ds: xr.Dataset | None, include_items=False) -> dict:
    if ds is None:
        return {}
    out = {}
    for v in ds.data_vars:
        if v == "loglik" or (v.startswith("loglik_") and (include_items or not v.startswith(DRIFT_EXCLUDE_PREFIX))):
            out[v] = np.asarray(ds[v].values, float)
    return out


# ---------------------------------------------------------------------------------------
# core combination
# ---------------------------------------------------------------------------------------
def tempered_log_factor(loglik, w, ref_p):
    """log of exp(w*loglik), centred so that the ref_p-weighted mean likelihood over computed
    cells is 1; NaN (not computed) cells -> 0 (uninformative). Returns (array, info)."""
    shape = ref_p.shape
    if loglik is None or w == 0:
        return np.zeros(shape), dict(neutral=0.0, mass_in_nan=0.0, n_nan=0)
    ll = w * np.asarray(loglik, float)
    fin = np.isfinite(ll)
    pw = ref_p * fin
    if pw.sum() <= 0:  # prior has no mass where the layer is computed -> layer is irrelevant
        return np.zeros(shape), dict(neutral=np.nan, mass_in_nan=1.0, n_nan=int((~fin).sum()))
    m = ll[fin].max()
    neutral = m + np.log(np.sum(pw[fin] * np.exp(ll[fin] - m)) / pw.sum())
    out = np.where(fin, ll - neutral, 0.0)
    return out, dict(neutral=float(neutral), mass_in_nan=float(ref_p[~fin].sum() / ref_p.sum()),
                     n_nan=int((~fin).sum()))


def normalise(a):
    s = a.sum()
    if not np.isfinite(s) or s <= 0:
        raise ValueError("cannot normalise: zero or non-finite total")
    return a / s


def combine(p_sat, drift_ll=None, w=0.0, pod=None, acoustic_ll=None, w_ac=1.0):
    """Return dict with prior (pre-search, normalised), post (normalised) and flags."""
    p_sat = normalise(np.where(np.isfinite(p_sat) & (p_sat > 0), p_sat, 0.0))
    f_d, info_d = tempered_log_factor(drift_ll, w, p_sat)
    f_a, info_a = tempered_log_factor(acoustic_ll, w_ac if acoustic_ll is not None else 0.0, p_sat)
    logf = f_d + f_a
    logf -= logf[p_sat > 0].max() if (p_sat > 0).any() else 0.0
    prior = normalise(p_sat * np.exp(logf))
    if pod is None:
        post = prior.copy()
    else:
        pod = np.clip(np.nan_to_num(np.asarray(pod, float), nan=0.0), 0.0, 1.0)
        post = normalise(prior * (1.0 - pod))
    return dict(prior=prior, post=post, drift_info=info_d, acoustic_info=info_a)


def search_split(prior, pod, searched_frac):
    """Prior mass in searched ground, probability past searches would have found it, and the
    post-search probability that the wreck is in already-searched ground (missed)."""
    pod = np.clip(np.nan_to_num(pod, nan=0.0), 0, 1)
    sf = np.clip(np.nan_to_num(searched_frac, nan=0.0), 0, 1)
    sf = np.maximum(sf, pod)  # by construction pod <= searched fraction
    p_found_if_there = float(np.sum(prior * pod))
    prior_searched = float(np.sum(prior * sf))
    denom = 1.0 - p_found_if_there
    missed = float(np.sum(prior * (sf - pod)) / denom) if denom > 0 else np.nan
    return dict(prior_mass_in_searched_ground=prior_searched,
                prob_searches_would_have_found=p_found_if_there,
                post_prob_in_searched_ground_missed=missed,
                post_prob_in_unsearched_ground=1.0 - missed if np.isfinite(missed) else np.nan)


# ---------------------------------------------------------------------------------------
# arc-frame raster
# ---------------------------------------------------------------------------------------
@dataclass
class ArcFrame:
    s: np.ndarray        # node centres along arc (km)
    n: np.ndarray        # node centres across arc (km)
    lat: np.ndarray      # (ns, nn) node latitude
    lon: np.ndarray      # (ns, nn)
    dA: np.ndarray       # (ns, nn) node cell area km2
    ds: float
    dn: float
    interp: tuple        # (i0, j0, wi, wj, valid) bilinear indices into the common grid
    cell_s: np.ndarray   # (lat, lon) s of every common-grid cell centre (nan far away)
    cell_n: np.ndarray


def build_arc_frame(ds_km=2.5, dn_km=2.5, n_max=450.0, cache=True) -> ArcFrame:
    cpath = DERIVED / "combine_arc_frame.npz"
    key = np.array([ds_km, dn_km, n_max])
    if cache and cpath.exists():
        z = np.load(cpath)
        if np.allclose(z["key"], key):
            return ArcFrame(z["s"], z["n"], z["lat"], z["lon"], z["dA"], ds_km, dn_km,
                            (z["i0"], z["j0"], z["wi"], z["wj"], z["valid"]), z["cell_s"], z["cell_n"])
    la_arc, lo_arc, s_arc = search.arc_dense()
    lat_g, lon_g = grid.common_grid()
    # extent in s: the part of the arc whose +/- n_max band touches the grid
    inside = (la_arc >= lat_g[0] - 5) & (la_arc <= lat_g[-1] + 5) & (lo_arc >= lon_g[0] - 6) & (lo_arc <= lon_g[-1] + 6)
    s0, s1 = s_arc[inside].min(), s_arc[inside].max()
    s = np.arange(np.floor(s0 / ds_km) * ds_km, s1 + ds_km, ds_km) + ds_km / 2
    n = np.arange(-n_max, n_max, dn_km) + dn_km / 2
    a_lat = np.interp(s, s_arc, la_arc)
    a_lon = np.interp(s, s_arc, lo_arc)
    # normal azimuth from neighbouring arc points (pointing to +n = away from satellite)
    la_p = np.interp(s + 1.0, s_arc, la_arc)
    lo_p = np.interp(s + 1.0, s_arc, lo_arc)
    la_m = np.interp(s - 1.0, s_arc, la_arc)
    lo_m = np.interp(s - 1.0, s_arc, lo_arc)
    az_t = search.GEOD.inv(lo_m, la_m, lo_p, la_p)[0]
    # decide the sign once using the satellite range test
    az_test = search.arc_normal_bearing(a_lat[len(s) // 2], a_lon[len(s) // 2])
    sgn = 1.0 if abs(((az_t[len(s) // 2] + 90 - az_test) + 180) % 360 - 180) < 1 else -1.0
    az_n = az_t + sgn * 90.0
    S, N = np.meshgrid(s, n, indexing="ij")
    AZ = np.where(N >= 0, az_n[:, None], az_n[:, None] + 180.0) * np.ones_like(N)
    LO0 = a_lon[:, None] * np.ones_like(N)
    LA0 = a_lat[:, None] * np.ones_like(N)
    lo, la, _ = search.GEOD.fwd(LO0.ravel(), LA0.ravel(), AZ.ravel(), np.abs(N).ravel() * 1000.0)
    lo = lo.reshape(S.shape)
    la = la.reshape(S.shape)
    # cell area: along-arc spacing at constant n times dn (normals are geodesics)
    d_along = np.empty_like(S)
    d_along[1:-1] = 0.5 * search.GEOD.inv(lo[:-2].ravel(), la[:-2].ravel(), lo[2:].ravel(), la[2:].ravel())[2].reshape(lo[2:].shape) / 1000.0
    d_along[0] = d_along[1]
    d_along[-1] = d_along[-2]
    dA = d_along * dn_km
    # bilinear interpolation indices into the common grid (density field)
    step = 0.05
    fi = (la - lat_g[0]) / step
    fj = (lo - lon_g[0]) / step
    valid = (fi >= 0) & (fi <= lat_g.size - 1) & (fj >= 0) & (fj <= lon_g.size - 1)
    i0 = np.clip(np.floor(fi).astype(int), 0, lat_g.size - 2)
    j0 = np.clip(np.floor(fj).astype(int), 0, lon_g.size - 2)
    wi = np.clip(fi - i0, 0, 1)
    wj = np.clip(fj - j0, 0, 1)
    # s, n of every grid cell centre (for arc profiles)
    LAg, LOg = np.meshgrid(lat_g, lon_g, indexing="ij")
    cs, cn = search.arc_coords(LAg, LOg)
    af = ArcFrame(s, n, la, lo, dA, ds_km, dn_km, (i0, j0, wi, wj, valid), cs, cn)
    if cache:
        np.savez_compressed(cpath, key=key, s=s, n=n, lat=la, lon=lo, dA=dA, i0=i0, j0=j0, wi=wi, wj=wj,
                            valid=valid, cell_s=cs, cell_n=cn)
    return af


def to_arc_raster(af: ArcFrame, cell_prob, area_km2):
    """Resample a per-cell probability to arc-frame node masses (via bilinear density)."""
    dens = cell_prob / area_km2
    i0, j0, wi, wj, valid = af.interp
    d = ((1 - wi) * (1 - wj) * dens[i0, j0] + wi * (1 - wj) * dens[i0 + 1, j0]
         + (1 - wi) * wj * dens[i0, j0 + 1] + wi * wj * dens[i0 + 1, j0 + 1])
    return np.where(valid, d * af.dA, 0.0)


def _box_sums(P, L, W):
    """All box sums of size (L, W) using a 2-D prefix sum; returns array (ns-L+1, nn-W+1)."""
    C = np.zeros((P.shape[0] + 1, P.shape[1] + 1))
    C[1:, 1:] = P.cumsum(0).cumsum(1)
    return C[L:, W:] - C[:-L, W:] - C[L:, :-W] + C[:-L, :-W]


def best_boxes(af: ArcFrame, mass, budget_km2, n_boxes=5, widths_km=None, extra=None,
               searched=None, max_searched_frac=None):
    """Greedy sequence of disjoint arc-aligned rectangles of ~budget_km2 that maximise the
    captured mass. extra: dict of additional node-arrays to summarise per box (sum).
    searched / max_searched_frac: node array of previously searched km2; boxes whose searched
    fraction exceeds max_searched_frac are not allowed (ranking of essentially new ground)."""
    if widths_km is None:
        widths_km = np.arange(20.0, 300.0 + 1e-9, 10.0)
    M = mass.copy()
    dA = af.dA
    mean_dA = float(np.median(dA))
    res = []
    taken = np.zeros(M.shape, bool)
    for _ in range(n_boxes):
        best = None
        CM = np.zeros((M.shape[0] + 1, M.shape[1] + 1))
        CM[1:, 1:] = M.cumsum(0).cumsum(1)
        CT = np.zeros_like(CM)
        CT[1:, 1:] = taken.cumsum(0).cumsum(1)
        if max_searched_frac is not None and searched is not None:
            CSf = np.zeros_like(CM)
            CSf[1:, 1:] = searched.cumsum(0).cumsum(1)
            CA = np.zeros_like(CM)
            CA[1:, 1:] = dA.cumsum(0).cumsum(1)
        for Wkm in widths_km:
            W = int(round(Wkm / af.dn))
            L = int(np.ceil(budget_km2 / (W * mean_dA)))
            if W > M.shape[1] or L > M.shape[0] or L < 1:
                continue
            S = CM[L:, W:] - CM[:-L, W:] - CM[L:, :-W] + CM[:-L, :-W]
            T = CT[L:, W:] - CT[:-L, W:] - CT[L:, :-W] + CT[:-L, :-W]
            S = np.where(T > 0.5, -np.inf, S)  # keep blocks disjoint
            if max_searched_frac is not None and searched is not None:
                sf_box = (CSf[L:, W:] - CSf[:-L, W:] - CSf[L:, :-W] + CSf[:-L, :-W]) / \
                    (CA[L:, W:] - CA[:-L, W:] - CA[L:, :-W] + CA[:-L, :-W])
                S = np.where(sf_box > max_searched_frac, -np.inf, S)
            k = np.unravel_index(np.argmax(S), S.shape)
            if best is None or S[k] > best[0]:
                best = (S[k], k[0], k[1], L, W)
        if best is None or not np.isfinite(best[0]) or best[0] <= 0:
            break
        val, i, j, L, W = best
        sl = (slice(i, i + L), slice(j, j + W))
        mm = mass[sl]
        s0, s1 = af.s[i] - af.ds / 2, af.s[i + L - 1] + af.ds / 2
        n0, n1 = af.n[j] - af.dn / 2, af.n[j + W - 1] + af.dn / 2
        area = float(dA[sl].sum())
        wsum = mm.sum()
        cen_lat, cen_lon = search.sn_to_latlon([(s0 + s1) / 2], [(n0 + n1) / 2])
        if wsum > 0:
            ms = float((mm.sum(1) * af.s[i:i + L]).sum() / wsum)
            mn = float((mm.sum(0) * af.n[j:j + W]).sum() / wsum)
            mlat, mlon = search.sn_to_latlon([ms], [mn])
        else:
            ms = mn = np.nan
            mlat = mlon = [np.nan]
        corners_lat, corners_lon = search.sn_to_latlon([s0, s1, s1, s0], [n0, n0, n1, n1])
        row = dict(mass=float(val), area_km2=area, s0_km=s0, s1_km=s1, n0_km=n0, n1_km=n1,
                   length_km=s1 - s0, width_km=n1 - n0,
                   centre_lat=float(cen_lat[0]), centre_lon=float(cen_lon[0]),
                   mass_centre_lat=float(mlat[0]), mass_centre_lon=float(mlon[0]),
                   lat_min=float(np.min(corners_lat)), lat_max=float(np.max(corners_lat)),
                   lon_min=float(np.min(corners_lon)), lon_max=float(np.max(corners_lon)),
                   corners=[(round(float(a), 4), round(float(b), 4)) for a, b in zip(corners_lat, corners_lon)])
        if extra:
            for k_, arr in extra.items():
                row[k_] = float(arr[sl].sum())
        res.append(row)
        taken[sl] = True
        M[sl] = 0.0
    return res


def box_outline(row, n_pts=40):
    """Lon/lat outline of an arc-aligned box (densified along s)."""
    s0, s1, n0, n1 = row["s0_km"], row["s1_km"], row["n0_km"], row["n1_km"]
    ss = np.linspace(s0, s1, n_pts)
    s_all = np.concatenate([ss, np.full(5, s1), ss[::-1], np.full(5, s0)])
    n_all = np.concatenate([np.full(n_pts, n0), np.linspace(n0, n1, 5), np.full(n_pts, n1), np.linspace(n1, n0, 5)])
    la, lo = search.sn_to_latlon(s_all, n_all)
    return np.column_stack([lo, la])


def greedy_blob(post, area_km2, budget_km2, exclude=None):
    """Free-form contiguous block grown from the densest cell (4-neighbour), benchmark."""
    dens = post / area_km2
    if exclude is not None:
        dens = np.where(exclude, -1.0, dens)
    start = np.unravel_index(np.argmax(dens), dens.shape)
    mask = np.zeros(post.shape, bool)
    heap = [(-dens[start], start)]
    seen = {start}
    area = 0.0
    mass = 0.0
    while heap and area < budget_km2:
        d, (i, j) = heapq.heappop(heap)
        if -d < 0:
            break
        mask[i, j] = True
        area += area_km2[i, j]
        mass += post[i, j]
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < post.shape[0] and 0 <= b < post.shape[1] and (a, b) not in seen:
                seen.add((a, b))
                heapq.heappush(heap, (-dens[a, b], (a, b)))
    return mask, float(mass), float(area)


def hdr_mass(post, area_km2, budget_km2):
    """Mass in the highest-density cells totalling budget_km2 (no contiguity): upper bound."""
    dens = (post / area_km2).ravel()
    o = np.argsort(dens)[::-1]
    ca = np.cumsum(area_km2.ravel()[o])
    k = np.searchsorted(ca, budget_km2)
    return float(post.ravel()[o][:k + 1].sum())


def arc_latitude_profile(af: ArcFrame, cell_prob, lat_step=0.05):
    """Marginalise a cell probability onto the latitude of the nearest sea-level arc point."""
    la_arc, _, s_arc = search.arc_dense()
    o = np.argsort(s_arc)
    foot_lat = np.interp(af.cell_s, s_arc[o], la_arc[o])
    edges = np.round(np.arange(-46.0, -5.0 + 1e-9, lat_step), 3)
    h, _ = np.histogram(foot_lat[np.isfinite(foot_lat)], bins=edges, weights=cell_prob[np.isfinite(foot_lat)])
    return 0.5 * (edges[:-1] + edges[1:]), h


def polygon_cell_fraction(geom, sub=5):
    """Fraction of each common-grid cell inside a lon/lat polygon (sub x sub sampling)."""
    import shapely
    lat, lon = grid.common_grid()
    out = np.zeros((lat.size, lon.size))
    if geom is None or geom.is_empty:
        return out
    x0, y0, x1, y1 = geom.bounds
    i0, i1 = max(np.searchsorted(lat, y0) - 2, 0), min(np.searchsorted(lat, y1) + 2, lat.size)
    j0, j1 = max(np.searchsorted(lon, x0) - 2, 0), min(np.searchsorted(lon, x1) + 2, lon.size)
    off = (np.arange(sub) + 0.5) / sub * 0.05 - 0.025
    la = (lat[i0:i1, None] + off).ravel()
    lo = (lon[j0:j1, None] + off).ravel()
    LO, LA = np.meshgrid(lo, la)
    shapely.prepare(geom)
    m = shapely.contains_xy(geom, LO, LA).astype(float)
    out[i0:i1, j0:j1] = m.reshape(i1 - i0, sub, j1 - j0, sub).mean(axis=(1, 3))
    return out


def named_areas():
    """Published / contracted candidate areas to evaluate (lon/lat polygons)."""
    import json
    from shapely.geometry import Point
    areas = {}
    try:
        oi25 = {p["name"]: p for p in json.load(open(search.F_OI25))["polygons"]}
        for key, label in [("OI2025_26_remaining_unsearched_NW_strip_slide", "OI contract remainder: NW strip (slide, 6,902 km2)"),
                           ("OI2025_26_remaining_NW_strip_calibrated_7428", "OI contract remainder: NW strip calibrated to 7,428 km2"),
                           ("OI_contract_area_best__slide_digitised", "OI 2025 contract area (both strips, slide)"),
                           ("CAPTION_Blelly_Marchand_recommended_zone", "CAPTION Blelly/Marchand zone"),
                           ("Ulich_Iannello_2023_70NM_glide_racetrack", "Ulich-Iannello 2023 70 NM glide racetrack")]:
            if key in oi25:
                areas[label] = search._poly_from_parts(oi25[key]["rings"])
    except FileNotFoundError:
        pass
    for lab, la, lo, _ in search.candidate_points():
        if -44 <= la <= -16:
            areas[f"50 km radius around {lab}"] = search.buffer_km(Point(lo, la), 50.0)
    return areas
