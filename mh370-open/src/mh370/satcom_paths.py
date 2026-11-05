"""Workstream A: "simple autopilot path" model for MH370 after the last radar point.

Path family (as used by the Independent Group / UGIB, Ashton et al., DSTG-style priors):
  * 18:22:12 UTC: start at the last military-radar point (MEKAR + 10 NM along N571; ATSB 2017 /
    Malaysian SIR), with a Gaussian position prior (sigma RADAR_SIGMA_NM, assumption).
  * 18:22:12 -> t_fmt: constant ground speed GS_pre and true track trk_pre (no wind needed).
  * t_fmt (final major turn, instantaneous) -> 00:19:29: ONE lateral mode at constant Mach and
    constant pressure altitude (flight level), integrated with ERA5 winds and temperature:
        LNAV : great circle (FMS LNAV with a single far waypoint), initial azimuth theta
        CTT  : constant true track (loxodrome)           theta = true track
        CMT  : constant magnetic track                   theta = magnetic track (WMM2010)
        CTH  : constant true heading                     theta = true heading
        CMH  : constant magnetic heading                 theta = magnetic heading (WMM2010)
Positions are integrated on the WGS84 ellipsoid (meridional/prime-vertical radii) with a
2nd-order (midpoint) scheme, fixed step DT plus exact handling of FMT and measurement times.

Vectorised over particles: every parameter is an array of shape (N,).
"""
from __future__ import annotations

import pathlib

import numpy as np
import xarray as xr

from mh370 import geo, satcom

ROOT = satcom.ROOT
ERA5_FILE = ROOT / "data" / "raw" / "era5_arco" / "era5_mh370_uvT.nc"
MAGVAR_FILE = ROOT / "data" / "derived" / "satcom_magvar_wmm2010.npz"

KT = 1852.0 / 3600.0
FT = 0.3048
NM = 1852.0
GAMMA_R = 1.4 * 287.05287

# --- waypoints (Malaysian AIP ENR 3.3, airway N571; https://aip.caam.gov.my) -----------
WPT = {
    "VAMPI": (6 + 10 / 60 + 56 / 3600, 97 + 35 / 60 + 8 / 3600),
    "MEKAR": (6 + 30 / 60 + 14 / 3600, 96 + 29 / 60 + 28 / 3600),
    "NILAM": (6 + 45 / 60 + 23 / 3600, 95 + 58 / 60 + 36 / 3600),
    "IGOGU": (7 + 31 / 60 + 1 / 3600, 94 + 25 / 60 + 0 / 3600),
}
T_RADAR = geo.hms(18, 22, 12)
T_END = geo.ARC7_TIME
RADAR_SIGMA_NM = 10.0
MODES = ("LNAV", "CTT", "CMT", "CTH", "CMH")


def destination(lat, lon, brg_deg, dist_m, R=6371008.8):
    """Great-circle destination on a sphere (adequate for <= tens of NM offsets)."""
    p1, l1, b, d = np.radians(lat), np.radians(lon), np.radians(brg_deg), dist_m / R
    p2 = np.arcsin(np.sin(p1) * np.cos(d) + np.cos(p1) * np.sin(d) * np.cos(b))
    l2 = l1 + np.arctan2(np.sin(b) * np.sin(d) * np.cos(p1), np.cos(d) - np.sin(p1) * np.sin(p2))
    return np.degrees(p2), np.degrees(l2)


def initial_bearing(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dl = np.radians(lon2 - lon1)
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return np.mod(np.degrees(np.arctan2(y, x)), 360)


BRG_MEKAR_NILAM = float(initial_bearing(*WPT["MEKAR"], *WPT["NILAM"]))
RADAR_POS = destination(*WPT["MEKAR"], BRG_MEKAR_NILAM, 10 * NM)   # ~(6.577N, 96.34E)


def fl_to_pressure_hpa(fl):
    """ISA pressure (hPa) at pressure altitude FL*100 ft."""
    h = np.asarray(fl, float) * 100 * FT
    p_trop = 1013.25 * (1 - 0.0065 * np.minimum(h, 11000.0) / 288.15) ** 5.255877
    return np.where(h <= 11000.0, p_trop, 226.3206 * np.exp(-(h - 11000.0) / 6341.62))


# ----------------------------------------------------------------------------------------
# atmosphere (ERA5) interpolation
# ----------------------------------------------------------------------------------------
class Atmos:
    """Quadrilinear interpolation of (u, v, T) in time, log-pressure, lat, lon."""

    def __init__(self, path=ERA5_FILE, wind_scale=1.0, wind_bias=(0.0, 0.0), temp_bias=0.0):
        ds = xr.open_dataset(path, engine="h5netcdf")
        ds = ds.sortby("latitude").sortby("level")
        self.lat = ds.latitude.values.astype(float)
        self.lon = ds.longitude.values.astype(float)
        self.lev = ds.level.values.astype(float)
        tt = (ds.time.values - np.datetime64("2014-03-07T00:00")) / np.timedelta64(1, "s")
        self.t = tt.astype(float)
        u = ds.u_component_of_wind.values.astype(float) * wind_scale + wind_bias[0]
        v = ds.v_component_of_wind.values.astype(float) * wind_scale + wind_bias[1]
        T = ds.temperature.values.astype(float) + temp_bias
        self.arr = np.stack([u, v, T], axis=-1)          # (nt, nlev, nlat, nlon, 3)
        self.flat = self.arr.reshape(-1, 3)
        self.shape = self.arr.shape[:4]
        self.lnp = np.log(self.lev)
        self.dlat = self.lat[1] - self.lat[0]
        self.dlon = self.lon[1] - self.lon[0]
        self.dt = self.t[1] - self.t[0]
        nt, nl, na, no = self.shape
        self.strides = (nl * na * no, na * no, no, 1)

    def interp(self, t, p_hpa, lat, lon):
        t = np.broadcast_to(np.asarray(t, float), np.shape(lat))
        nt, nl, na, no = self.shape
        ft = np.clip((t - self.t[0]) / self.dt, 0, nt - 1 - 1e-9)
        fl = np.clip(np.interp(np.log(p_hpa), self.lnp, np.arange(nl)), 0, nl - 1 - 1e-9)
        fl = np.broadcast_to(fl, np.shape(lat))
        fa = np.clip((lat - self.lat[0]) / self.dlat, 0, na - 1 - 1e-9)
        fo = np.clip((lon - self.lon[0]) / self.dlon, 0, no - 1 - 1e-9)
        idx, frac = [], []
        for f in (ft, fl, fa, fo):
            i = np.floor(f).astype(np.int64)
            idx.append(i)
            frac.append(f - i)
        out = np.zeros(np.shape(lat) + (3,))
        st = self.strides
        for c in range(16):
            b = [(c >> k) & 1 for k in range(4)]
            w = np.ones(np.shape(lat))
            flat = np.zeros(np.shape(lat), dtype=np.int64)
            for k in range(4):
                w = w * (frac[k] if b[k] else (1 - frac[k]))
                flat = flat + (idx[k] + b[k]) * st[k]
            out += w[..., None] * self.flat[flat]
        return out[..., 0], out[..., 1], out[..., 2]


# ----------------------------------------------------------------------------------------
# magnetic variation (WMM2010, epoch 2014.18, 10 km altitude)
# ----------------------------------------------------------------------------------------
class MagVar:
    def __init__(self):
        if not MAGVAR_FILE.exists():
            self._build()
        z = np.load(MAGVAR_FILE)
        self.lat, self.lon, self.d = z["lat"], z["lon"], z["decl"]

    @staticmethod
    def _build():
        from pygeomag import GeoMag
        from pygeomag.wmm.wmm_2010 import WMM_2010
        gm = GeoMag(coefficients_data=WMM_2010)
        lat = np.arange(-50.0, 20.0 + 1e-9, 1.0)
        lon = np.arange(70.0, 120.0 + 1e-9, 1.0)
        d = np.array([[gm.calculate(glat=a, glon=o, alt=10.0, time=2014.18).d for o in lon]
                      for a in lat])
        MAGVAR_FILE.parent.mkdir(parents=True, exist_ok=True)
        np.savez(MAGVAR_FILE, lat=lat, lon=lon, decl=d)

    def __call__(self, lat, lon):
        fa = np.clip((lat - self.lat[0]) / 1.0, 0, self.lat.size - 1 - 1e-9)
        fo = np.clip((lon - self.lon[0]) / 1.0, 0, self.lon.size - 1 - 1e-9)
        ia, io = np.floor(fa).astype(int), np.floor(fo).astype(int)
        a, o = fa - ia, fo - io
        d = self.d
        return ((1 - a) * (1 - o) * d[ia, io] + a * (1 - o) * d[ia + 1, io]
                + (1 - a) * o * d[ia, io + 1] + a * o * d[ia + 1, io + 1])


# ----------------------------------------------------------------------------------------
# kinematics
# ----------------------------------------------------------------------------------------
def radii(lat):
    s2 = np.sin(np.radians(lat)) ** 2
    a = geo.WGS84_A * 1e3
    e2 = geo.WGS84_E2
    N = a / np.sqrt(1 - e2 * s2)
    M = a * (1 - e2) / (1 - e2 * s2) ** 1.5
    return M, N


def move(lat, lon, vn, ve, dt, h):
    M, N = radii(lat)
    dlat = np.degrees(vn * dt / (M + h))
    dlon = np.degrees(ve * dt / ((N + h) * np.cos(np.radians(lat))))
    return lat + dlat, lon + dlon


def _unit_r(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)


def gc_normal(lat, lon, az_deg):
    """Unit normal of the great circle through (lat,lon) with azimuth az (spherical)."""
    e, n, _ = satcom.enu_basis(lat, lon)
    a = np.radians(az_deg)[..., None]
    d = np.sin(a) * e + np.cos(a) * n
    nv = np.cross(_unit_r(lat, lon), d)
    return nv / np.linalg.norm(nv, axis=-1, keepdims=True)


def gc_course(nv, lat, lon):
    e, n, _ = satcom.enu_basis(lat, lon)
    d = np.cross(nv, _unit_r(lat, lon))
    return np.degrees(np.arctan2(np.sum(d * e, -1), np.sum(d * n, -1)))


class PathModel:
    """Vectorised forward model: parameters -> predicted BTO/BFO and end state."""

    PARAMS = ("lat0", "lon0", "trk_pre", "gs_pre", "t_fmt", "theta", "mach", "fl")
    PARAMS_DRIFT = PARAMS + ("dmach",)

    def __init__(self, mode, meas, atm=None, mag=None, dt=120.0):
        assert mode in MODES
        self.mode = mode
        self.atm = atm or Atmos()
        self.mag = mag or (MagVar() if mode in ("CMT", "CMH") else None)
        self.meas = meas
        self.dt = dt
        tm = np.unique(np.asarray(meas["t"], float))
        self.t_meas = tm
        grid = np.arange(T_RADAR, T_END, dt)
        self.grid = np.unique(np.concatenate([grid, tm, [T_END]]))
        self.grid = self.grid[self.grid >= T_RADAR]

    # -- final-mode ground velocity -------------------------------------------------------
    def vel_final(self, t, lat, lon, P, nv):
        u, v, T = self.atm.interp(t, P["p_hpa"], lat, lon)
        mach = P["mach"]
        if "dmach" in P:   # optional linear Mach drift (per hour since FMT), e.g. LRC-like
            mach = mach + P["dmach"] * np.maximum(t - P["t_fmt"], 0.0) / 3600.0
        tas = mach * np.sqrt(GAMMA_R * T)
        m = self.mode
        if m in ("LNAV", "CTT", "CMT"):
            if m == "LNAV":
                crs = gc_course(nv, lat, lon)
            elif m == "CTT":
                crs = P["theta"]
            else:
                crs = P["theta"] + self.mag(lat, lon)
            c = np.radians(crs)
            cx, cy = np.sin(c), np.cos(c)
            w_al = u * cx + v * cy
            w_cr = u * cy - v * cx              # wind component to the right of track
            sd = np.clip(-w_cr / tas, -0.95, 0.95)
            gs = tas * np.sqrt(1 - sd ** 2) + w_al
            return gs * cy, gs * cx
        hdg = P["theta"] if m == "CTH" else P["theta"] + self.mag(lat, lon)
        h = np.radians(hdg)
        return tas * np.cos(h) + v, tas * np.sin(h) + u

    def run(self, P, record_track=False):
        """P: dict of (N,) arrays with PARAMS. Returns dict with states at measurement times."""
        N = np.size(P["lat0"])
        P = dict(P)
        P["p_hpa"] = fl_to_pressure_hpa(P["fl"])
        h = np.asarray(P["fl"], float) * 100 * FT
        lat = np.array(P["lat0"], float)
        lon = np.array(P["lon0"], float)
        tr = np.radians(P["trk_pre"])
        vn_pre = P["gs_pre"] * KT * np.cos(tr)
        ve_pre = P["gs_pre"] * KT * np.sin(tr)
        tf = np.asarray(P["t_fmt"], float)
        nv = np.zeros((N, 3))
        if self.mode == "LNAV":
            done = tf <= T_RADAR
            if done.any():
                nv[done] = gc_normal(lat[done], lon[done], P["theta"][done])
        nm = self.t_meas.size
        out = dict(lat=np.zeros((N, nm)), lon=np.zeros((N, nm)), vn=np.zeros((N, nm)),
                   ve=np.zeros((N, nm)))
        trk = [] if record_track else None
        mi = {t: i for i, t in enumerate(self.t_meas)}

        def record(t, lat, lon):
            i = mi[t]
            post = tf <= t
            vn_f, ve_f = self.vel_final(t, lat, lon, P, nv)
            out["lat"][:, i] = lat
            out["lon"][:, i] = lon
            out["vn"][:, i] = np.where(post, vn_f, vn_pre)
            out["ve"][:, i] = np.where(post, ve_f, ve_pre)

        if T_RADAR in mi:
            record(T_RADAR, lat, lon)
        if record_track:
            trk.append((T_RADAR, lat.copy(), lon.copy()))
        for k in range(self.grid.size - 1):
            t0, t1 = self.grid[k], self.grid[k + 1]
            D = t1 - t0
            dt1 = np.clip(tf - t0, 0.0, D)                  # pre-FMT part of this step
            if np.any(dt1 > 0):
                lat_m, lon_m = move(lat, lon, vn_pre, ve_pre, dt1 / 2, h)
                lat_n, lon_n = move(lat, lon, vn_pre, ve_pre, dt1, h)
                # midpoint for radius terms
                M, Nn = radii(lat_m)
                lat = lat + np.degrees(vn_pre * dt1 / (M + h))
                lon = lon + np.degrees(ve_pre * dt1 / ((Nn + h) * np.cos(np.radians(lat_m))))
                if self.mode == "LNAV":
                    sw = (tf > t0) & (tf <= t1)
                    if sw.any():
                        nv[sw] = gc_normal(lat[sw], lon[sw], P["theta"][sw])
            dt2 = D - dt1
            if np.any(dt2 > 0):
                ts = t0 + dt1
                vn1, ve1 = self.vel_final(ts, lat, lon, P, nv)
                la_m, lo_m = move(lat, lon, vn1, ve1, dt2 / 2, h)
                vn2, ve2 = self.vel_final(ts + dt2 / 2, la_m, lo_m, P, nv)
                M, Nn = radii(la_m)
                lat = lat + np.degrees(vn2 * dt2 / (M + h))
                lon = lon + np.degrees(ve2 * dt2 / ((Nn + h) * np.cos(np.radians(la_m))))
            if t1 in mi:
                record(t1, lat, lon)
            if record_track:
                trk.append((t1, lat.copy(), lon.copy()))
        out["h"] = h
        if record_track:
            out["track_t"] = np.array([x[0] for x in trk])
            out["track_lat"] = np.stack([x[1] for x in trk], 1)
            out["track_lon"] = np.stack([x[2] for x in trk], 1)
        return out


# ----------------------------------------------------------------------------------------
# measurements and likelihood
# ----------------------------------------------------------------------------------------
# BTO sigma = measurement noise (DSTG 2016: 29 us R1200, 62 us R600, from 20 previous flights)
# combined in quadrature with a path-model error of 30 us (ERA5 wind error ~2-3 m/s accumulated
# over ~1 h between handshakes ~ 5-8 km along track ~ 25-40 us; see README). Default 42 / 69 us.
SIG_MODEL_US = 30.0
SIG_R1200 = float(np.hypot(29.0, SIG_MODEL_US))
SIG_R600 = float(np.hypot(62.0, SIG_MODEL_US))


def build_measurements(use_1828_bfo=True, use_1827_btos=True, sig_r1200=SIG_R1200,
                       sig_r600=SIG_R600, sig_bfo=7.0):
    """Measurement table from the public log (values identical to Ashton et al. Table 6)."""
    log = satcom.load_su_log()
    rows = []
    # BTO, R600 log-on requests (corrected by -4600 us; Ashton et al. 2015)
    rows.append(("BTO", geo.hms(18, 25, 27.421), 17120.0 - 4600.0, sig_r600, "R600 18:25:27"))
    if use_1827_btos:
        sel = log[(log.t > geo.hms(18, 27)) & (log.t < geo.hms(18, 28, 20)) & (log.chan == "R")]
        for _, r in sel.iterrows():
            rows.append(("BTO", float(r.t), float(r.bto), sig_r1200, "R1200 " + r.Time[-12:-4]))
    hs = log[(log.t > geo.hms(19)) & (log.chan == "R") & log.Time.str.contains("41:|10:59")
             & log.bto.notna() & (log.t < geo.hms(24, 15))]
    for _, r in hs.iterrows():
        rows.append(("BTO", float(r.t), float(r.bto), sig_r1200, "R1200 " + r.Time[-12:-4]))
        rows.append(("BFO", float(r.t), float(r.bfo), sig_bfo, "R1200 " + r.Time[-12:-4]))
    rows.append(("BTO", geo.ARC7_TIME, 23000.0 - 4600.0, sig_r600, "R600 00:19:29"))
    if use_1828_bfo:
        r = log[(log.t > geo.hms(18, 28, 14)) & (log.t < geo.hms(18, 28, 15.5)) & (log.chan == "R")].iloc[0]
        rows.append(("BFO", float(r.t), float(r.bfo), sig_bfo, "R1200 18:28:15"))
    for a, b, lab in ((geo.hms(18, 39), geo.hms(18, 41), "C 18:40 mean"),
                      (geo.hms(23, 13), geo.hms(23, 16), "C 23:14 mean")):
        c = log[(log.t > a) & (log.t < b) & (log.chan == "C") & log.bfo.notna()]
        rows.append(("BFO", float(np.round(c.t.mean(), 1)), float(c.bfo.mean()), sig_bfo, lab))
    import pandas as pd
    m = pd.DataFrame(rows, columns=["kind", "t", "z", "sigma", "label"]).sort_values("t")
    return m.reset_index(drop=True)


class Likelihood:
    def __init__(self, meas, bias_mean=152.0, bias_sigma=3.0):
        self.meas = meas
        self.bto = meas[meas.kind == "BTO"].reset_index(drop=True)
        self.bfo = meas[meas.kind == "BFO"].reset_index(drop=True)
        self.b0 = bias_mean
        self.sb = bias_sigma

    def predict(self, model_out, t_meas):
        idx = {t: i for i, t in enumerate(t_meas)}
        ib = np.array([idx[t] for t in self.bto.t])
        jf = np.array([idx[t] for t in self.bfo.t])
        o = model_out
        h = o["h"][:, None]
        bto = satcom.bto(self.bto.t.to_numpy()[None, :], o["lat"][:, ib], o["lon"][:, ib], h)
        bfo = satcom.bfo(self.bfo.t.to_numpy()[None, :], o["lat"][:, jf], o["lon"][:, jf], h,
                         o["vn"][:, jf], o["ve"][:, jf], 0.0, bias=0.0)
        return bto, bfo

    def __call__(self, model_out, t_meas, return_parts=False):
        bto, bfo = self.predict(model_out, t_meas)
        rb = (self.bto.z.to_numpy() - bto) / self.bto.sigma.to_numpy()
        ll_bto = -0.5 * np.sum(rb ** 2, 1)
        s = self.bfo.sigma.to_numpy()
        r = self.bfo.z.to_numpy() - bfo - self.b0
        # marginalise a common bias offset ~ N(0, sb^2) (Sherman-Morrison; equal sigmas)
        s2 = s[0] ** 2
        n = r.shape[1]
        sb2 = self.sb ** 2
        q = np.sum(r ** 2, 1) / s2 - (sb2 / (s2 * (s2 + n * sb2))) * np.sum(r, 1) ** 2
        ll_bfo = -0.5 * q - 0.5 * np.log1p(n * sb2 / s2)
        b_post = sb2 * np.sum(r, 1) / (s2 + n * sb2)          # posterior mean bias offset
        ll = ll_bto + ll_bfo
        if return_parts:
            return ll, dict(ll_bto=ll_bto, ll_bfo=ll_bfo, bto_res=self.bto.z.to_numpy() - bto,
                            bfo_res=r - b_post[:, None], bias=self.b0 + b_post)
        return ll
