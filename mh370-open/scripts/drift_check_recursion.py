"""Numerical check (workstream B): the backward "visit" recursion in drift_mc.visit_probability
agrees with a direct Monte Carlo simulation of the same Markov chain (20,000 walkers).
Run: .venv/bin/python -I scripts/drift_check_recursion.py
"""
import numpy as np
from mh370 import geo, drift as D, drift_mc as mc, drift_debris as dd
grid = mc.MCGrid()
ch = mc.build_chain(mc.transition_pairs(grid, 5.0, 0), grid, 5.0, "miron3")
v = D.valid_cells(ch)
it = dd.ITEM_BY_KEY["flaperon"]
cells = mc.cells_within(grid, it.lat, it.lon, D.R_KM, v)
a, b = it.window()
na, nb = int(round(a / 5)), int(round(b / 5))
V = mc.visit_probability(ch, [cells], [na], [nb], dd.RELEASE_TIME)[:, 0]
arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0)
rng = np.random.default_rng(1)
Pc = [P.tocsr() for P in ch.P]
R = set(cells.tolist()) | set((grid.nc + cells).tolist())
Rb = set((grid.nc + cells).tolist())
for alat in (-25.0, -30.0, -35.0):
    c0 = grid.cell(alat, np.interp(alat, arc[:, 0], arc[:, 1]))
    N = 20000
    state = np.full(N, c0)
    hit = np.zeros(N, bool)
    pre = np.zeros(N, bool)
    for m in range(nb):
        P = Pc[ch.season_of_step(m, dd.RELEASE_TIME)]
        # sample next state for each walker
        new = np.empty(N, np.int64)
        for s in np.unique(state):
            idx = np.flatnonzero(state == s)
            row = P.getrow(s)
            new[idx] = rng.choice(row.indices, size=idx.size, p=row.data / row.data.sum())
        state = new
        t = m + 1
        if na <= t <= nb:
            inR = np.isin(state, list(R))
            if t == na:
                pre = np.isin(state, list(Rb))  # beached there before the window: excluded forever
            hit |= inR & ~pre
    print(f"{alat}: backward V = {V[c0]:.4f}   Monte Carlo = {hit.mean():.4f} +/- {np.sqrt(hit.mean()*(1-hit.mean())/N):.4f}")
