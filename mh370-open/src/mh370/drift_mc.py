"""Markov-chain (transition-matrix) drift model built from GDP drifters (workstream B).

State space (for a regular lat/lon grid of n_c cells):
    0 .. n_c-1        "afloat in cell c"
    n_c .. 2n_c-1     "beached in cell c"      (absorbing)
    2 n_c             "left the domain"        (absorbing)
Transitions are counted from every pair of 6-hourly GDP fixes separated by exactly T days
on the same trajectory and with the same drogue state at both ends (Miron et al. 2019 style,
overlapping pairs). Beaching: a trajectory whose GDP death code is 1 ("ran aground") and whose
last fix lies within BEACH_KM of the Natural-Earth coastline contributes, for every fix
within T days of its end, a transition into "beached in the cell of the last fix".
Pairs whose drifter died at sea (other death codes) before T days are not used.

Optional extra leeway (for flaperon-like objects; CSIRO Griffin et al. 2017 Part II): the
end point of each pair is shifted by the time integral of an extra velocity derived from
NCEP R1 daily 10 m winds along the drifter's actual 6-hourly track.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import scipy.sparse as sp

from mh370.drift_data import load_gdp, dist_to_coast_km, land_fraction
from mh370.geo import haversine_km

SEC_DAY = 86400.0
FIX_DT = 6 * 3600.0
BEACH_KM = 50.0

SEASONS = {
    "annual": {m: 0 for m in range(1, 13)},
    # Miron et al. (2019): Jan-Mar (NE monsoon), Jul-Sep (SW monsoon), Apr-Jun + Oct-Dec
    "miron3": {1: 0, 2: 0, 3: 0, 7: 1, 8: 1, 9: 1, 4: 2, 5: 2, 6: 2, 10: 2, 11: 2, 12: 2},
    "quarters": {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3},
}


@dataclass
class MCGrid:
    lon0: float = 20.0
    lon1: float = 120.0
    lat0: float = -50.0
    lat1: float = 10.0
    d: float = 1.0
    nlon: int = field(init=False)
    nlat: int = field(init=False)

    def __post_init__(self):
        self.nlon = int(round((self.lon1 - self.lon0) / self.d))
        self.nlat = int(round((self.lat1 - self.lat0) / self.d))

    @property
    def nc(self) -> int:
        return self.nlon * self.nlat

    @property
    def nstate(self) -> int:
        return 2 * self.nc + 1

    @property
    def out_state(self) -> int:
        return 2 * self.nc

    @property
    def lat_c(self):
        return self.lat0 + (np.arange(self.nlat) + 0.5) * self.d

    @property
    def lon_c(self):
        return self.lon0 + (np.arange(self.nlon) + 0.5) * self.d

    @property
    def lat_edges(self):
        return self.lat0 + np.arange(self.nlat + 1) * self.d

    @property
    def lon_edges(self):
        return self.lon0 + np.arange(self.nlon + 1) * self.d

    def cell_centres(self):
        LA, LO = np.meshgrid(self.lat_c, self.lon_c, indexing="ij")
        return LA.ravel(), LO.ravel()

    def cell(self, lat, lon) -> np.ndarray:
        lat = np.asarray(lat)
        lon = np.asarray(lon)
        i = np.floor((lat - self.lat0) / self.d).astype(np.int64)
        j = np.floor((lon - self.lon0) / self.d).astype(np.int64)
        ok = (i >= 0) & (i < self.nlat) & (j >= 0) & (j < self.nlon) & np.isfinite(lat) & np.isfinite(lon)
        return np.where(ok, i * self.nlon + j, -1)


# --------------------------------------------------------------------------------------
# Extra leeway models (velocity added on top of an undrogued drifter's motion)
# --------------------------------------------------------------------------------------
def leeway_velocity(model: str, u10: np.ndarray, v10: np.ndarray):
    """Extra (east, north) velocity in m/s for a given 10 m wind.

    flaperon : CSIRO Part II (Griffin et al. 2017): real flaperon = 1.2% of wind (the
               undrogued-drifter windage, already in the data) + 0.10 m/s directed 20 deg to
               the LEFT of downwind. Implemented as +0.10 m/s at +20 deg (counter-clockwise)
               from the wind vector, tapered linearly to 0 for winds below 2 m/s.
    flaperon10: same with 10 deg (CSIRO's alternative).
    windage3 : generic high-windage object, total ~3% of wind downwind (CSIRO Part II sec. 4):
               extra 1.8% of wind, 0 deg.
    """
    spd = np.hypot(u10, v10)
    if model in ("flaperon", "flaperon10"):
        ang = np.radians(20.0 if model == "flaperon" else 10.0)
        ur = u10 * np.cos(ang) - v10 * np.sin(ang)
        vr = u10 * np.sin(ang) + v10 * np.cos(ang)
        mag = 0.10 * np.clip(spd / 2.0, 0, 1)
        with np.errstate(invalid="ignore", divide="ignore"):
            ue = np.where(spd > 0, mag * ur / spd, 0.0)
            vn = np.where(spd > 0, mag * vr / spd, 0.0)
        return ue, vn
    if model == "windage3":
        return 0.018 * u10, 0.018 * v10
    raise ValueError(model)


# --------------------------------------------------------------------------------------
# Transition pairs
# --------------------------------------------------------------------------------------
@dataclass
class Pairs:
    start: np.ndarray     # start state (ocean cell)
    end: np.ndarray       # end state (cell / beached / out)
    month: np.ndarray     # calendar month of the start fix
    traj: np.ndarray      # trajectory index (for hold-out splits)
    t0: np.ndarray        # start time (unix s)


def transition_pairs(grid: MCGrid, T_days: float = 5.0, drogue: int = 0,
                     leeway: str | None = None, traj_keep: np.ndarray | None = None,
                     beach_km: float = BEACH_KM) -> Pairs:
    g = load_gdp()
    lat, lon, time, dr, traj = g["lat"], g["lon"], g["time"], g["drogue"], g["traj"]
    L = int(round(T_days * SEC_DAY / FIX_DT))
    n = lat.size
    k = np.arange(n - L)
    ok = ((traj[k + L] == traj[k]) & (np.abs(time[k + L] - time[k] - T_days * SEC_DAY) < 1)
          & (dr[k] == drogue) & (dr[k + L] == drogue))
    c0 = grid.cell(lat[k], lon[k])
    ok &= c0 >= 0
    if traj_keep is not None:
        ok &= traj_keep[traj[k]]
    k = k[ok]
    lat1, lon1 = lat[k + L].copy(), lon[k + L].copy()
    beached_by_leeway = np.zeros(k.size, bool)
    if leeway is not None:
        from mh370.drift_data import NcepDailyWind
        years = np.unique((np.datetime64("1970-01-01") + (time[k] // SEC_DAY).astype("timedelta64[D]"))
                          .astype("datetime64[Y]").astype(int) + 1970)
        years = np.union1d(years, years + 1)
        wind = NcepDailyWind(years)
        # extra velocity at every fix used by any pair (fixes k .. k+L-1)
        need = np.zeros(n, bool)
        for s in range(L):
            need[k + s] = True
        idx = np.flatnonzero(need)
        U, V = wind(time[idx], lat[idx], lon[idx])
        ue = np.zeros(n)
        vn = np.zeros(n)
        a, b = leeway_velocity(leeway, np.nan_to_num(U), np.nan_to_num(V))
        ue[idx], vn[idx] = a, b
        # exclusive cumulative displacement (m)
        Se = np.concatenate([[0.0], np.cumsum(ue * FIX_DT)])
        Sn = np.concatenate([[0.0], np.cumsum(vn * FIX_DT)])
        de = Se[k + L] - Se[k]
        dn = Sn[k + L] - Sn[k]
        lat1 = lat1 + dn / 111_195.0
        lon1 = lon1 + de / (111_195.0 * np.cos(np.radians(lat1)))
        # shifted end point on land -> the object stranded during the step
        from mh370.drift_data import on_land
        beached_by_leeway = on_land(lat1, lon1)
    c1 = grid.cell(lat1, lon1)
    end = np.where(c1 >= 0, c1, grid.out_state)
    if leeway is not None and beached_by_leeway.any():
        # pushed onto land: beached in the cell of the un-shifted end point
        cb = grid.cell(lat[k + L], lon[k + L])
        end = np.where(beached_by_leeway & (cb >= 0), grid.nc + cb, end)
    start = c0[ok]
    month = (np.datetime64("1970-01-01") + (time[k] // SEC_DAY).astype("timedelta64[D]")) \
        .astype("datetime64[M]").astype(int) % 12 + 1
    trj = traj[k]
    t0 = time[k]

    # beaching pairs
    rs = g["rowsize"]
    last = np.cumsum(rs) - 1
    aground = g["typedeath"] == 1
    la_e, lo_e = lat[last], lon[last]
    ce = grid.cell(la_e, lo_e)
    cand = aground & (ce >= 0)
    if cand.any():
        dist = np.full(rs.size, np.inf)
        dist[cand] = dist_to_coast_km(la_e[cand], lo_e[cand])
        cand &= dist < beach_km
    if traj_keep is not None:
        cand &= traj_keep
    tend = time[last]
    kb = np.arange(n)
    mb = cand[traj] & (tend[traj] - time < T_days * SEC_DAY) & (dr == drogue)
    cb0 = grid.cell(lat, lon)
    mb &= cb0 >= 0
    kb = kb[mb]
    bstart = cb0[kb]
    bend = grid.nc + ce[traj[kb]]
    bmonth = (np.datetime64("1970-01-01") + (time[kb] // SEC_DAY).astype("timedelta64[D]")) \
        .astype("datetime64[M]").astype(int) % 12 + 1
    return Pairs(start=np.concatenate([start, bstart]), end=np.concatenate([end, bend]),
                 month=np.concatenate([month, bmonth]), traj=np.concatenate([trj, traj[kb]]),
                 t0=np.concatenate([t0, time[kb]]))


# --------------------------------------------------------------------------------------
# Transition matrices
# --------------------------------------------------------------------------------------
@dataclass
class Chain:
    grid: MCGrid
    T_days: float
    seasons: str
    P: list            # list of csr matrices (one per season)
    counts: np.ndarray  # (nseason+1, nc) number of pairs leaving each cell (last = annual)
    label: str = ""
    # Transit-speed calibration: one transition represents T_days / time_scale REAL days
    # (time_scale > 1 speeds the chain up; fitted to held-out drifter transit times).
    time_scale: float = 1.0

    @property
    def step_days(self) -> float:
        """Real-time length of one transition."""
        return self.T_days / self.time_scale

    def season_of_step(self, m: int, t_start: np.datetime64) -> int:
        tmid = t_start + np.timedelta64(int((m + 0.5) * self.step_days * 24), "h")
        month = int(tmid.astype("datetime64[M]").astype(int) % 12 + 1)
        return SEASONS[self.seasons][month]


def _row_normalise(C: sp.csr_matrix, nc: int, nstate: int, fallback: sp.csr_matrix | None,
                   alpha: float):
    n = np.asarray(C.sum(axis=1)).ravel()
    if fallback is not None and alpha > 0:
        # Bayesian shrinkage toward the fallback (annual) row: (C + a Q) / (n + a)
        C = C + alpha * fallback
        n = n + alpha * np.asarray(fallback.sum(axis=1)).ravel()
    with np.errstate(divide="ignore"):
        inv = np.where(n > 0, 1.0 / n, 0.0)
    P = sp.diags(inv) @ C
    # rows without data (and all absorbing states): identity
    empty = n == 0
    P = P + sp.diags(empty.astype(float))
    return P.tocsr()


def build_chain(pairs: Pairs, grid: MCGrid, T_days: float, seasons: str = "miron3",
                alpha: float = 20.0, label: str = "") -> Chain:
    nst = grid.nstate
    smap = SEASONS[seasons]
    ns = max(smap.values()) + 1
    def counts(mask):
        return sp.coo_matrix((np.ones(mask.sum()), (pairs.start[mask], pairs.end[mask])),
                             shape=(nst, nst)).tocsr()
    Ca = counts(np.ones(pairs.start.size, bool))
    Pa = _row_normalise(Ca, grid.nc, nst, None, 0.0)
    cnt = np.zeros((ns + 1, grid.nc))
    cnt[ns] = np.bincount(pairs.start, minlength=nst)[:grid.nc]
    if ns == 1:
        return Chain(grid, T_days, seasons, [Pa], cnt, label)
    season = np.array([smap[m] for m in range(1, 13)])[pairs.month - 1]
    Ps = []
    for s in range(ns):
        m = season == s
        Cs = counts(m)
        cnt[s] = np.bincount(pairs.start[m], minlength=nst)[:grid.nc]
        Ps.append(_row_normalise(Cs, grid.nc, nst, Pa, alpha))
    return Chain(grid, T_days, seasons, Ps, cnt, label)


# --------------------------------------------------------------------------------------
# Propagation
# --------------------------------------------------------------------------------------
def region_states(grid: MCGrid, cells: np.ndarray) -> np.ndarray:
    """State indices for 'afloat or beached in any of these cells'."""
    cells = np.asarray(cells, dtype=np.int64)
    return np.concatenate([cells, grid.nc + cells])


def hitting_probability(chain: Chain, regions: list[np.ndarray], n_steps: list[int],
                        t_start: np.datetime64) -> np.ndarray:
    """H[:, c] = P(state enters regions[c] at or before step n_steps[c] | start state).

    Backward (adjoint) recursion with the region made absorbing:
        v <- P_m v ; v[region] = 1, for m = n-1 .. 0.
    Returns array (nstate, ncols)."""
    nst = chain.grid.nstate
    ncol = len(regions)
    V = np.zeros((nst, ncol))
    for c, r in enumerate(regions):
        V[r, c] = 1.0
    n_steps = np.asarray(n_steps)
    for m in range(int(n_steps.max()) - 1, -1, -1):
        act = np.flatnonzero(n_steps > m)
        if act.size == 0:
            continue
        P = chain.P[chain.season_of_step(m, t_start)]
        V[:, act] = P @ V[:, act]
        for c in act:
            V[regions[c], c] = 1.0
    return V


def forward(chain: Chain, p0: np.ndarray, n_steps: int, t_start: np.datetime64,
            keep_every: int = 1) -> np.ndarray:
    """Forward propagation of a (nstate, k) distribution; returns (n_keep, nstate, k)."""
    p = np.array(p0, dtype=float)
    out = [p.copy()]
    for m in range(n_steps):
        P = chain.P[chain.season_of_step(m, t_start)]
        p = P.T @ p
        if (m + 1) % keep_every == 0:
            out.append(p.copy())
    return np.array(out)


def cells_within(grid: MCGrid, lat: float, lon: float, r_km: float,
                 valid: np.ndarray | None = None) -> np.ndarray:
    la, lo = grid.cell_centres()
    d = haversine_km(lat, lon, la, lo)
    m = d <= r_km
    if valid is not None:
        m &= valid
    if not m.any():
        dd = np.where(valid if valid is not None else True, d, np.inf)
        m = dd == dd.min()
    return np.flatnonzero(m)


def grid_landfrac(grid: MCGrid) -> np.ndarray:
    return land_fraction(grid.lat_edges, grid.lon_edges, sub=10)


def visit_probability(chain: Chain, grid_cells: list[np.ndarray], n_a: list[int], n_b: list[int],
                      t_start: np.datetime64) -> np.ndarray:
    """V[:, c] = P(the object is in (afloat) or enters (afloat/beached) the cells grid_cells[c]
    at some step in [n_a[c], n_b[c]] | start state), excluding objects already beached
    there before step n_a (they would have arrived before the window).

    Backward recursion: absorbing in the window, then plain propagation before it."""
    grid = chain.grid
    nst = grid.nstate
    ncol = len(grid_cells)
    V = np.zeros((nst, ncol))
    regs = [region_states(grid, c) for c in grid_cells]
    beached = [grid.nc + np.asarray(c, np.int64) for c in grid_cells]
    for c, r in enumerate(regs):
        V[r, c] = 1.0
    n_a = np.asarray(n_a)
    n_b = np.asarray(n_b)
    for m in range(int(n_b.max()) - 1, -1, -1):
        act = np.flatnonzero(n_b > m)
        if act.size == 0:
            continue
        P = chain.P[chain.season_of_step(m, t_start)]
        V[:, act] = P @ V[:, act]
        for c in act:
            if m >= n_a[c]:
                V[regs[c], c] = 1.0
            if m == n_a[c]:
                V[beached[c], c] = 0.0
    return V
