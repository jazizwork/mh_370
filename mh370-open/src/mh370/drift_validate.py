"""Validation of the drifter Markov chain (workstream B).

1. K-fold hold-out by trajectory: chains are built from (K-1)/K of the drifters and tested on
   the held-out drifters (no drifter is used both to build and to test a chain).
   a. Predictive calibration: for held-out undrogued fixes in the arc-to-Africa source region,
      the fraction of true positions after n steps that fall inside the chain's 50/90 % highest-
      probability sets (well calibrated => ~0.5 / ~0.9), and the mean log score.
   b. Mean displacement bias after n steps (predicted mean vs observed).
   c. Transit time: Kaplan-Meier estimate (censored at the end of each held-out drifter's
      undrogued record) of the time for drifters starting near the 7th arc to reach west of
      a given longitude, compared with the chain's first-passage CDF from the same start
      cells and months.
2. Mass budget of forward propagation from arc cells (afloat / beached by region / out).
"""
from __future__ import annotations

import numpy as np

from mh370 import drift_mc as mc
from mh370 import geo
from mh370.drift_data import load_gdp

RELEASE = np.datetime64("2014-03-08T00:20")


def folds(ntraj: int, k: int = 5, seed: int = 370) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.permutation(ntraj) % k


def _month(t_unix):
    return ((np.datetime64("1970-01-01") + (np.asarray(t_unix) // 86400).astype("timedelta64[D]"))
            .astype("datetime64[M]").astype(int) % 12) + 1


def _start_date(t_unix):
    return np.datetime64("1970-01-01") + np.asarray(t_unix).astype("int64").astype("timedelta64[s]")


def test_starts(grid: mc.MCGrid, test_traj: np.ndarray, T_days: float, horizons: list[int],
                box=(-42.0, -18.0, 70.0, 110.0), stride_days: float = 5.0):
    """Held-out undrogued start fixes in box with the true position after each horizon."""
    g = load_gdp()
    lat, lon, time, dr, traj = g["lat"], g["lon"], g["time"], g["drogue"], g["traj"]
    stride = int(round(stride_days * 4))
    m = (test_traj[traj] & (dr == 0) & (lat >= box[0]) & (lat <= box[1])
         & (lon >= box[2]) & (lon <= box[3]))
    k = np.flatnonzero(m)
    k = k[(k % stride) == 0]
    out = {}
    L = int(round(T_days * 4))
    for n in horizons:
        kk = k[k + n * L < lat.size]
        e = kk + n * L
        ok = (traj[e] == traj[kk]) & (np.abs(time[e] - time[kk] - n * T_days * 86400) < 1) & (dr[e] == 0)
        kk, e = kk[ok], e[ok]
        out[n] = dict(c0=grid.cell(lat[kk], lon[kk]), c1=grid.cell(lat[e], lon[e]),
                      t0=time[kk], lat0=lat[kk], lon0=lon[kk], lat1=lat[e], lon1=lon[e])
    return out


def predictive_scores(chain: mc.Chain, starts: dict, batch: int = 1500):
    """Coverage of 50/90% HPD sets, log score and displacement bias for each horizon."""
    grid = chain.grid
    la_c, lo_c = grid.cell_centres()
    res = {}
    for n, s in starts.items():
        c0, c1, mon = s["c0"], s["c1"], _month(s["t0"])
        okc = (c0 >= 0)
        key = c0 * 100 + mon
        uk, inv = np.unique(key[okc], return_inverse=True)
        p_true = np.zeros(okc.sum())
        in50 = np.zeros(okc.sum(), bool)
        in90 = np.zeros(okc.sum(), bool)
        mlat = np.zeros(uk.size)
        mlon = np.zeros(uk.size)
        c1v = c1[okc]
        srt = np.argsort(inv, kind="stable")
        groups = np.split(srt, np.cumsum(np.bincount(inv, minlength=uk.size))[:-1])
        for b0 in range(0, uk.size, batch):
            ub = uk[b0:b0 + batch]
            p = np.zeros((grid.nstate, ub.size))
            p[ub // 100, np.arange(ub.size)] = 1.0
            # start date: mid-month of a generic year with the right month
            t_start = np.datetime64("2001-01-15") + np.array(
                [np.timedelta64(int(30.44 * (mm - 1)), "D") for mm in ub % 100])
            # propagate each month group separately (season sequence depends on start date)
            for mm in np.unique(ub % 100):
                cols = np.flatnonzero(ub % 100 == mm)
                pp = p[:, cols]
                for step in range(n):
                    P = chain.P[chain.season_of_step(step, t_start[cols[0]])]
                    pp = P.T @ pp
                p[:, cols] = pp
            pc = p[:grid.nc]            # afloat part
            # beached mass assigned to its cell for scoring
            pc = pc + p[grid.nc:2 * grid.nc]
            for j in range(ub.size):
                sel = groups[b0 + j]
                col = pc[:, j]
                tot = col.sum()
                mlat[b0 + j] = (col * la_c).sum() / max(tot, 1e-12)
                mlon[b0 + j] = (col * lo_c).sum() / max(tot, 1e-12)
                order = np.argsort(col)[::-1]
                cs = np.cumsum(col[order])
                rank = np.empty_like(order)
                rank[order] = np.arange(order.size)
                tc = c1v[sel]
                valid = tc >= 0
                pt = np.where(valid, col[np.maximum(tc, 0)], 0.0)
                p_true[sel] = pt
                r = np.where(valid, rank[np.maximum(tc, 0)], order.size - 1)
                cum_at = cs[r]
                # inside HPD set alpha if cumulative mass up to and including the true cell <= alpha
                # (with the true cell's own mass split evenly)
                frac = cum_at - 0.5 * pt
                in50[sel] = valid & (frac <= 0.5)
                in90[sel] = valid & (frac <= 0.9)
        dlat_obs = (s["lat1"] - s["lat0"])[okc]
        dlon_obs = (s["lon1"] - s["lon0"])[okc] * np.cos(np.radians(s["lat0"][okc]))
        dlat_pred = (mlat[inv] - la_c[c0[okc]])
        dlon_pred = (mlon[inv] - lo_c[c0[okc]]) * np.cos(np.radians(la_c[c0[okc]]))
        res[n] = dict(
            n_test=int(okc.sum()), days=n * chain.T_days,
            cover50=float(in50.mean()), cover90=float(in90.mean()),
            logscore=float(np.mean(np.log(np.maximum(p_true, 1e-6)))),
            obs_dx_km=float(np.mean(dlon_obs) * 111.2), pred_dx_km=float(np.mean(dlon_pred) * 111.2),
            obs_dy_km=float(np.mean(dlat_obs) * 111.2), pred_dy_km=float(np.mean(dlat_pred) * 111.2),
        )
    return res


def arc_start_cells(grid: mc.MCGrid, lat_range=(-40.0, -20.0), half_width_km=300.0):
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
    la, lo = grid.cell_centres()
    alon = np.interp(la, arc[:, 0], arc[:, 1])
    d = np.abs(lo - alon) * 111.2 * np.cos(np.radians(la))
    return (la >= lat_range[0]) & (la <= lat_range[1]) & (d <= half_width_km)


def kaplan_meier(t_event: np.ndarray, observed: np.ndarray, t_grid: np.ndarray):
    """CDF F(t) = 1 - S(t) for right-censored data."""
    order = np.argsort(t_event)
    t, e = t_event[order], observed[order]
    n = t.size
    at_risk = n - np.arange(n)
    surv = np.cumprod(np.where(e, 1 - 1 / at_risk, 1.0))
    S = np.ones_like(t_grid, dtype=float)
    for i, tg in enumerate(t_grid):
        j = np.searchsorted(t, tg, side="right") - 1
        S[i] = surv[j] if j >= 0 else 1.0
    return 1 - S, at_risk


def drifter_transits(grid: mc.MCGrid, test_traj: np.ndarray, start_mask_cells: np.ndarray,
                     lon_target: float, max_days: float = 1100.0, every_days: float | None = None):
    """For held-out drifters: undrogued start fix(es) in the start cells -> time to first fix west
    of lon_target (event) or end of undrogued record (censored).
    every_days=None: one start per drifter (first entry; flux-weighted sample).
    every_days=30: a start every 30 days while the drifter is in the start cells and east of the
    target (volume-weighted sample, closer to debris released at fixed points)."""
    g = load_gdp()
    lat, lon, time, dr, traj = g["lat"], g["lon"], g["time"], g["drogue"], g["traj"]
    rs = g["rowsize"]
    first = np.concatenate([[0], np.cumsum(rs)[:-1]])
    c = grid.cell(lat, lon)
    ins = (c >= 0) & start_mask_cells[np.maximum(c, 0)] & (dr == 0) & test_traj[traj]
    tt, ev, sc, st = [], [], [], []
    for tr in np.unique(traj[ins]):
        a, b = first[tr], first[tr] + rs[tr]
        seg = slice(a, b)
        cand = a + np.flatnonzero(ins[seg])
        if every_days is None:
            starts = cand[:1]
        else:
            starts, last = [], -np.inf
            for k in cand:
                if time[k] - last >= every_days * 86400 and lon[k] >= lon_target:
                    starts.append(k)
                    last = time[k]
        for k0 in starts:
            t1, e1 = _transit_one(k0, b, lon, time, dr, lon_target)
            tt.append(t1)
            ev.append(e1)
            sc.append(c[k0])
            st.append(time[k0])
    return np.array(tt), np.array(ev), np.array(sc), np.array(st)


def _transit_one(k0, b, lon, time, dr, lon_target):
    later = np.arange(k0, b)
    und = dr[later] == 0
    stop = later[~und][0] if (~und).any() else b
    later = np.arange(k0, stop)
    hit = later[lon[later] < lon_target]
    if hit.size:
        return (time[hit[0]] - time[k0]) / 86400.0, True
    return (time[stop - 1] - time[k0]) / 86400.0, False


def chain_transit_cdf(chain: mc.Chain, start_cells: np.ndarray, start_times: np.ndarray,
                      lon_target: float, t_grid: np.ndarray):
    """Average over starts of P(first passage to cells west of lon_target by t)."""
    grid = chain.grid
    la, lo = grid.cell_centres()
    target = np.flatnonzero(lo < lon_target)
    reg = mc.region_states(grid, target)
    nmax = int(np.ceil(t_grid.max() / chain.step_days))
    F = np.zeros(t_grid.size)
    months = _month(start_times)
    for mm in np.unique(months):
        sel = months == mm
        p = np.zeros(grid.nstate)
        np.add.at(p, start_cells[sel], 1.0)
        t0 = np.datetime64("2001-01-15") + np.timedelta64(int(30.44 * (mm - 1)), "D")
        absorbed = np.zeros(nmax + 1)
        q = p.copy()
        absorbed[0] = q[reg].sum()
        q[reg] = 0
        for m in range(nmax):
            P = chain.P[chain.season_of_step(m, t0)]
            q = P.T @ q
            absorbed[m + 1] = absorbed[m] + q[reg].sum()
            q[reg] = 0
        tt = np.arange(nmax + 1) * chain.step_days
        F += np.interp(t_grid, tt, absorbed)
    return F / start_cells.size


def mass_budget(chain: mc.Chain, start_lats, days=(180, 365, 508, 730, 1050)):
    grid = chain.grid
    arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
    la, lo = grid.cell_centres()
    west = lo < 70.0
    wa = (lo > 108) & (la > -36) & (la < -20)
    rows = []
    nmax = int(np.ceil(max(days) / chain.step_days))
    for alat in start_lats:
        alon = np.interp(alat, arc[:, 0], arc[:, 1])
        c = grid.cell(alat, alon)
        p = np.zeros(grid.nstate)
        p[c] = 1.0
        hist = mc.forward(chain, p[:, None], nmax, RELEASE)[:, :, 0]
        for d in days:
            n = int(round(d / chain.step_days))
            h = hist[n]
            afloat = h[:grid.nc]
            beached = h[grid.nc:2 * grid.nc]
            rows.append(dict(arc_lat=alat, day=d, total=float(h.sum()),
                             afloat=float(afloat.sum()), afloat_west70=float(afloat[west].sum()),
                             beached=float(beached.sum()), beached_west70=float(beached[west].sum()),
                             beached_WA=float(beached[wa].sum()), out=float(h[grid.out_state]),
                             stuck_nodata=float(afloat[chain.counts[-1] == 0].sum())))
    return rows
