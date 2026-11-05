"""2014-15 hindcast particle tracking (cross-check for workstream B).

Physics (CSIRO, Griffin et al. 2016/2017 style, with HYCOM instead of BRAN2015):
    dx/dt = u_HYCOM(0 m, daily) + 0.012 * U10 (NCEP R1 daily)   [generic debris]
            (+ 0.10 m/s at 20 deg left of the wind for the flaperon)
            + isotropic random walk K = 100 m^2/s (sub-grid dispersion)
RK2 (midpoint) with a 6-hour step; HYCOM daily fields linearly interpolated in time and
bilinearly in space; a particle that steps onto Natural Earth land, or into a HYCOM land
(fill) point, is stranded where it was.
This is NOT OpenDrift; it is a minimal, transparent tracker (see README for why).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from mh370.drift_data import RAW, NcepDailyWind, on_land
from mh370.drift_mc import leeway_velocity

HYCOM_DIR = RAW / "hycom_glbv008_53X"
R_EARTH = 6_371_008.8


class HycomDaily:
    def __init__(self):
        files = sorted(HYCOM_DIR.glob("hycom_sfc_*.npz"))
        us, vs, ts = [], [], []
        for f in files:
            z = np.load(f)
            u = z["u"].astype(np.float32)
            v = z["v"].astype(np.float32)
            fill = z["u"] == z["fill_value"]
            u[fill] = np.nan
            v[fill] = np.nan
            us.append(u * float(z["scale_factor"]))
            vs.append(v * float(z["scale_factor"]))
            ts.append(z["time_hours_since_2000"])
            self.lat = z["lat"].astype(float)
            self.lon = z["lon"].astype(float)
        self.u = np.concatenate(us)
        self.v = np.concatenate(vs)
        th = np.concatenate(ts)
        self.t_unix = (np.datetime64("2000-01-01") - np.datetime64("1970-01-01")).astype("timedelta64[s]").astype(float) \
            + th * 3600.0
        o = np.argsort(self.t_unix)
        self.u, self.v, self.t_unix = self.u[o], self.v[o], self.t_unix[o]

    @property
    def t_end(self):
        return self.t_unix[-1]

    def __call__(self, t, lat, lon):
        k = np.clip(np.searchsorted(self.t_unix, t) - 1, 0, self.t_unix.size - 2)
        w = np.clip((t - self.t_unix[k]) / (self.t_unix[k + 1] - self.t_unix[k]), 0, 1)
        i = np.clip(np.searchsorted(self.lat, lat) - 1, 0, self.lat.size - 2)
        j = np.clip(np.searchsorted(self.lon, lon) - 1, 0, self.lon.size - 2)
        fy = (lat - self.lat[i]) / (self.lat[i + 1] - self.lat[i])
        fx = (lon - self.lon[j]) / (self.lon[j + 1] - self.lon[j])
        out = []
        for arr in (self.u, self.v):
            val = 0.0
            for kk, wk in ((k, 1 - w), (k + 1, w)):
                a = arr[kk]
                val = val + wk * (a[i, j] * (1 - fx) * (1 - fy) + a[i, j + 1] * fx * (1 - fy)
                                  + a[i + 1, j] * (1 - fx) * fy + a[i + 1, j + 1] * fx * fy)
            out.append(val)
        return out[0], out[1]


def run(release_lat, release_lon, t0_unix: float, n_days: float, leeway: str | None,
        windage: float = 0.012, K: float = 100.0, dt_h: float = 6.0, seed: int = 0,
        hycom: HycomDaily | None = None, wind: NcepDailyWind | None = None,
        record_every_h: float = 24.0):
    """Track particles; returns dict with daily positions (n_rec, n) and stranded flags."""
    rng = np.random.default_rng(seed)
    hycom = hycom or HycomDaily()
    wind = wind or NcepDailyWind([2014, 2015])
    lat = np.array(release_lat, float)
    lon = np.array(release_lon, float)
    n = lat.size
    alive = np.ones(n, bool)
    dt = dt_h * 3600.0
    nsteps = int(round(n_days * 24 / dt_h))
    rec_every = int(round(record_every_h / dt_h))
    recs_lat, recs_lon, recs_alive = [lat.copy()], [lon.copy()], [alive.copy()]

    def vel(t, la, lo):
        u, v = hycom(t, la, lo)
        U, V = wind(np.full(la.shape, t), la, lo)
        U = np.nan_to_num(U)
        V = np.nan_to_num(V)
        u = u + windage * U
        v = v + windage * V
        if leeway is not None:
            a, b = leeway_velocity(leeway, U, V)
            u = u + a
            v = v + b
        return u, v

    def move(la, lo, u, v, h):
        dla = np.degrees(v * h / R_EARTH)
        dlo = np.degrees(u * h / (R_EARTH * np.cos(np.radians(la))))
        return la + dla, lo + dlo

    t = t0_unix
    sig = np.sqrt(2 * K * dt)
    for s in range(nsteps):
        idx = np.flatnonzero(alive)
        la, lo = lat[idx], lon[idx]
        u1, v1 = vel(t, la, lo)
        lam, lom = move(la, lo, u1, v1, dt / 2)
        u2, v2 = vel(t + dt / 2, lam, lom)
        nla, nlo = move(la, lo, u2, v2, dt)
        nla, nlo = move(nla, nlo, sig * rng.standard_normal(idx.size), sig * rng.standard_normal(idx.size), 1.0)
        bad = ~np.isfinite(u1) | ~np.isfinite(u2) | ~np.isfinite(nla) | ~np.isfinite(nlo)
        land = np.zeros(idx.size, bool)
        land[~bad] = on_land(nla[~bad], nlo[~bad])
        out = (nlo < 20) | (nlo > 120) | (nla < -50) | (nla > 5)
        strand = bad | land
        ok = ~strand
        lat[idx[ok]] = nla[ok]
        lon[idx[ok]] = nlo[ok]
        alive[idx[strand | out]] = False
        t += dt
        if (s + 1) % rec_every == 0:
            recs_lat.append(lat.copy())
            recs_lon.append(lon.copy())
            recs_alive.append(alive.copy())
    return dict(lat=np.array(recs_lat), lon=np.array(recs_lon), alive=np.array(recs_alive),
                record_days=np.arange(len(recs_lat)) * record_every_h / 24.0)
