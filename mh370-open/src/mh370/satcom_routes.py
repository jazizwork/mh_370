"""Workstream A extension (reviewer response): multi-leg route families.

The single-mode families of `satcom_paths` fly ONE lateral mode from the final major turn (FMT)
to 00:19:29.  A waypoint route such as UGIB 2020's (FMT ... BEDAX, then LNAV 180 deg true to the
South Pole) is not in that family.  This module adds two families that use exactly the same
ingredients (18:22:12 radar-point start, pre-FMT straight leg, ERA5 winds/temperatures, WGS84
midpoint integrator, constant Mach and constant flight level after the FMT, likelihood):

  WPT  (waypoint)  t_fmt -> LNAV great circle "direct to" a published waypoint W
                   -> at W (passage detected during integration), a new lateral mode
                   `mode2` in {LNAV, CTT, CMT, CTH, CMH} with free track/heading theta2.
                   W is fixed per SMC run; the family evidence is the average of the per-waypoint
                   (and per-mode2) evidences, i.e. a uniform prior over the discrete set.
  TWO  (generic two-leg)  t_fmt -> constant true track theta1 until t2 -> constant true track
                   theta2 until 00:19:29, with t2 = t_fmt + u2 (00:19:29 - t_fmt), u2 ~ U(0,1)
                   (i.e. the second-turn time is uniform between the FMT and the end).

Phases per particle: 0 = pre-FMT straight leg, 1 = first post-FMT leg, 2 = second leg.

WPT leg 1 ("direct to" W) is steered along the great-circle bearing from the *current* position
to W (as an FMS direct-to leg does), so the path arrives exactly at W.  (Following the course of
the great circle fixed at the FMT, as the single-mode LNAV model does, drifts 0.4-0.9 km
cross-track over ~150 NM because the course is spherical while the integrator advances on the
ellipsoid; it would then pass beside W.)  Passage is detected when W is closer than one step
of flight; the step is shortened to reach W and the position is snapped onto W (the snap
distance is returned as out["snap_km"]).  After W, mode2 = LNAV uses the single-mode LNAV
course law with the great circle fixed at W.
Vectorised over particles; every parameter is an (N,) array.

Waypoints: data/raw/waypoints_indian_ocean/waypoints.csv (provenance in SOURCE.md there).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from mh370 import geo, satcom
from mh370 import satcom_paths as sp

ROOT = sp.ROOT
WAYPOINT_CSV = ROOT / "data" / "raw" / "waypoints_indian_ocean" / "waypoints.csv"
MODES2 = sp.MODES
R_SPHERE = 6371008.8

PARAMS = {
    "WPT": ("lat0", "lon0", "trk_pre", "gs_pre", "t_fmt", "theta2", "mach", "fl"),
    # WPTS (sensitivity, UGIB-structure): as WPT but the FMT -> W leg is flown at its own constant
    # ground speed gs1 (e.g. a slow, low-level traverse as in UGIB 2020); cruise Mach/FL after W
    "WPTS": ("lat0", "lon0", "trk_pre", "gs_pre", "t_fmt", "gs1", "theta2", "mach", "fl"),
    "TWO": ("lat0", "lon0", "trk_pre", "gs_pre", "t_fmt", "theta1", "u2", "theta2", "mach", "fl"),
}

# ------------------------------------------------------------------------------ waypoint sets
# Regional set (primary): every published en-route fix in the table with 15 S <= lat <= 8 N and
# 88 E <= lon <= 97 E, i.e. ahead of / south of the aircraft at 18:22, except MEKAR (10 NM behind
# the radar point on N571).  Uniform prior over this set.
REGION_LAT = (-15.0, 8.0)
REGION_LON = (88.0, 97.0)
BEHIND = ("MEKAR",)
# Waypoints named as route points in published MH370 route hypotheses (UGIB 2020, Iannello 2014/
# 2017, Godfrey 2016/2021, Ashton et al. 2015, ATSB 2014) that fall in the region above.
LITERATURE_SET = ("NILAM", "IGOGU", "ANOKO", "NOPEK", "IGEBO", "ANSAX", "POVUS", "BEDAX",
                  "NISOK", "ISBIX", "DOLEM", "MUTMI", "RUNUT")


def load_waypoints(published_only=True):
    d = pd.read_csv(WAYPOINT_CSV)
    d = d[d.lat_deg.notna()]
    if published_only:
        d = d[d.verified.isin(["Y", "N"])]
    return d.set_index("name")


def waypoint_set(kind="regional"):
    d = load_waypoints()
    if kind == "regional":
        m = (d.lat_deg.between(*REGION_LAT) & d.lon_deg.between(*REGION_LON)
             & ~d.index.isin(BEHIND))
        return list(d.index[m])
    if kind == "literature":
        return [w for w in LITERATURE_SET if w in d.index]
    if kind in d.index:
        return [kind]
    raise ValueError(kind)


# ------------------------------------------------------------------------------ kinematics
def ground_velocity(mode, atm, mag, t, lat, lon, theta, mach, p_hpa, nv=None):
    """Ground velocity (vn, ve) in m/s for a lateral mode at constant Mach/pressure level.
    Same formulas as satcom_paths.PathModel.vel_final (kept identical on purpose)."""
    u, v, T = atm.interp(t, p_hpa, lat, lon)
    tas = mach * np.sqrt(sp.GAMMA_R * T)
    if mode in ("LNAV", "CTT", "CMT"):
        if mode == "LNAV":
            crs = sp.gc_course(nv, lat, lon)
        elif mode == "CTT":
            crs = theta
        else:
            crs = theta + mag(lat, lon)
        c = np.radians(crs)
        cx, cy = np.sin(c), np.cos(c)
        w_al = u * cx + v * cy
        w_cr = u * cy - v * cx
        sd = np.clip(-w_cr / tas, -0.95, 0.95)
        gs = tas * np.sqrt(1 - sd ** 2) + w_al
        return gs * cy, gs * cx
    hdg = theta if mode == "CTH" else theta + mag(lat, lon)
    h = np.radians(hdg)
    return tas * np.cos(h) + v, tas * np.sin(h) + u


def _unit(lat, lon):
    return sp._unit_r(np.asarray(lat, float), np.asarray(lon, float))


class RouteModel:
    """Forward model for the WPT and TWO families (see module docstring).

    `wpt`: waypoint name from the table, or a (lat, lon) tuple.  `extra_times`: additional times
    at which states are recorded (diagnostics only)."""

    def __init__(self, family, meas, mode2="CTT", wpt=None, atm=None, mag=None, dt=120.0,
                 extra_times=()):
        assert family in PARAMS
        self.family = family
        self.wfam = family in ("WPT", "WPTS")
        self.mode1 = "LNAV" if self.wfam else "CTT"
        self.mode2 = mode2 if self.wfam else "CTT"
        assert self.mode2 in MODES2
        self.atm = atm or sp.Atmos()
        self.mag = mag or (sp.MagVar() if self.mode2 in ("CMT", "CMH") else None)
        if self.wfam:
            if isinstance(wpt, str):
                d = load_waypoints(published_only=False)
                self.wpt_name = wpt
                self.wlat, self.wlon = float(d.loc[wpt, "lat_deg"]), float(d.loc[wpt, "lon_deg"])
            else:
                self.wpt_name = f"{wpt[0]:.3f},{wpt[1]:.3f}"
                self.wlat, self.wlon = float(wpt[0]), float(wpt[1])
            self.rW = _unit(self.wlat, self.wlon)
        self.meas = meas
        self.dt = dt
        tm = np.unique(np.concatenate([np.asarray(meas["t"], float),
                                       np.asarray(extra_times, float)]))
        self.t_meas = tm
        grid = np.arange(sp.T_RADAR, sp.T_END, dt)
        self.grid = np.unique(np.concatenate([grid, tm, [sp.T_END]]))
        self.grid = self.grid[self.grid >= sp.T_RADAR]
        self.PARAMS = PARAMS[family]

    # --------------------------------------------------------------------------------------
    def run(self, P, record_track=False):
        N = np.size(P["lat0"])
        fam = self.family
        wfam = self.wfam
        gs1 = np.asarray(P["gs1"], float) * sp.KT if fam == "WPTS" else None
        mach = np.asarray(P["mach"], float)
        fl = np.asarray(P["fl"], float)
        p_hpa = sp.fl_to_pressure_hpa(fl)
        h = fl * 100 * sp.FT
        lat = np.array(P["lat0"], float)
        lon = np.array(P["lon0"], float)
        tr = np.radians(P["trk_pre"])
        vn_pre = P["gs_pre"] * sp.KT * np.cos(tr)
        ve_pre = P["gs_pre"] * sp.KT * np.sin(tr)
        tf = np.asarray(P["t_fmt"], float)
        th2 = np.asarray(P["theta2"], float)
        th1 = np.asarray(P["theta1"], float) if fam == "TWO" else None
        t2 = tf + np.asarray(P["u2"], float) * (sp.T_END - tf) if fam == "TWO" else None
        phase = np.zeros(N, np.int8)
        nv2 = np.zeros((N, 3))
        t_sw2 = np.full(N, np.nan)          # W passage (WPT) or second turn (TWO)
        snap_km = np.full(N, np.nan)        # WPT: distance moved by the snap onto W
        atm, mag = self.atm, self.mag

        def vel(ph, idx, t, la, lo):
            if ph == 1:
                if fam == "WPTS":   # constant ground speed along the bearing to W
                    c = np.radians(sp.initial_bearing(la, lo, self.wlat, self.wlon))
                    return gs1[idx] * np.cos(c), gs1[idx] * np.sin(c)
                if fam == "WPT":
                    # LNAV "direct to" W: course = great-circle bearing from the current
                    # position to W (converges exactly onto W; see module docstring)
                    crs = sp.initial_bearing(la, lo, self.wlat, self.wlon)
                    return ground_velocity("CTT", atm, mag, t, la, lo, crs, mach[idx],
                                           p_hpa[idx])
                return ground_velocity("CTT", atm, mag, t, la, lo, th1[idx], mach[idx],
                                       p_hpa[idx])
            return ground_velocity(self.mode2, atm, mag, t, la, lo, th2[idx], mach[idx],
                                   p_hpa[idx], nv2[idx])

        def mid(ph, idx, t_start, dtx, v_start=None):
            """Midpoint step (same scheme as satcom_paths) for particles idx, per-particle dt."""
            la, lo, hh = lat[idx], lon[idx], h[idx]
            vn1, ve1 = v_start if v_start is not None else vel(ph, idx, t_start, la, lo)
            la_m, lo_m = sp.move(la, lo, vn1, ve1, dtx / 2, hh)
            vn2, ve2 = vel(ph, idx, t_start + dtx / 2, la_m, lo_m)
            M, Nn = sp.radii(la_m)
            lat[idx] = la + np.degrees(vn2 * dtx / (M + hh))
            lon[idx] = lo + np.degrees(ve2 * dtx / ((Nn + hh) * np.cos(np.radians(la_m))))

        def enter2(idx, t):
            phase[idx] = 2
            t_sw2[idx] = t
            if wfam:
                snap_km[idx] = geo.haversine_km(lat[idx], lon[idx], self.wlat, self.wlon)
                lat[idx] = self.wlat          # snap onto W (residual: see out["snap_km"])
                lon[idx] = self.wlon
                if self.mode2 == "LNAV":
                    nv2[idx] = sp.gc_normal(lat[idx], lon[idx], th2[idx])

        def enter1(idx, t):
            phase[idx] = 1
            if wfam:
                r = _unit(lat[idx], lon[idx])
                nc = np.linalg.norm(np.cross(r, self.rW), axis=-1)
                ok = nc > 1e-6                 # FMT not within ~6 m of W
                if (~ok).any():
                    enter2(idx[~ok], t[~ok] if np.ndim(t) else t)
            else:
                at_once = idx[t2[idx] <= tf[idx]]
                if at_once.size:
                    enter2(at_once, t2[at_once])

        nm = self.t_meas.size
        out = dict(lat=np.zeros((N, nm)), lon=np.zeros((N, nm)), vn=np.zeros((N, nm)),
                   ve=np.zeros((N, nm)), phase=np.zeros((N, nm), np.int8))
        mi = {t: i for i, t in enumerate(self.t_meas)}
        trk = [] if record_track else None

        def record(t):
            i = mi[t]
            out["lat"][:, i] = lat
            out["lon"][:, i] = lon
            out["phase"][:, i] = phase
            vn = vn_pre.copy()
            ve = ve_pre.copy()
            for ph in (1, 2):
                idx = np.nonzero(phase == ph)[0]
                if idx.size:
                    a, b = vel(ph, idx, t, lat[idx], lon[idx])
                    vn[idx], ve[idx] = a, b
            out["vn"][:, i] = vn
            out["ve"][:, i] = ve

        if sp.T_RADAR in mi:
            record(sp.T_RADAR)
        if record_track:
            trk.append((sp.T_RADAR, lat.copy(), lon.copy()))
        for k in range(self.grid.size - 1):
            t0, t1 = self.grid[k], self.grid[k + 1]
            D = t1 - t0
            tcur = np.full(N, t0)
            # ---- phase 0: straight pre-FMT leg (constant ground velocity)
            dt0 = np.clip(tf - t0, 0.0, D)
            i0 = np.nonzero(dt0 > 0)[0]
            if i0.size:
                d0 = dt0[i0]
                hh = h[i0]
                la_m, lo_m = sp.move(lat[i0], lon[i0], vn_pre[i0], ve_pre[i0], d0 / 2, hh)
                M, Nn = sp.radii(la_m)
                lat[i0] = lat[i0] + np.degrees(vn_pre[i0] * d0 / (M + hh))
                lon[i0] = lon[i0] + np.degrees(ve_pre[i0] * d0 / ((Nn + hh) * np.cos(np.radians(la_m))))
                tcur[i0] += d0
            sw = np.nonzero((phase == 0) & (tf <= t1))[0]
            if sw.size:
                enter1(sw, tf[sw])
            # ---- phase 1
            i1 = np.nonzero((phase == 1) & (tcur < t1))[0]
            if i1.size:
                rem = t1 - tcur[i1]
                if fam == "TWO":
                    d1 = np.clip(t2[i1] - tcur[i1], 0.0, rem)
                    j = d1 > 0
                    if j.any():
                        mid(1, i1[j], tcur[i1[j]], d1[j])
                    tcur[i1] += d1
                    reach = i1[t2[i1] <= t1]
                    if reach.size:
                        enter2(reach, t2[reach])
                else:
                    v0 = vel(1, i1, tcur[i1], lat[i1], lon[i1])
                    gs = np.hypot(*v0)
                    r = _unit(lat[i1], lon[i1])
                    ang = np.arctan2(np.linalg.norm(np.cross(r, self.rW), axis=-1),
                                     np.sum(r * self.rW, -1))
                    d_rem = ang * (R_SPHERE + h[i1])
                    t_need = d_rem / np.maximum(gs, 1.0)
                    d1 = np.minimum(t_need, rem)
                    mid(1, i1, tcur[i1], d1, v_start=v0)
                    tcur[i1] += d1
                    hit = t_need <= rem
                    if hit.any():
                        enter2(i1[hit], tcur[i1[hit]])
            # ---- phase 2
            i2 = np.nonzero((phase == 2) & (tcur < t1 - 1e-9))[0]
            if i2.size:
                mid(2, i2, tcur[i2], t1 - tcur[i2])
            if t1 in mi:
                record(t1)
            if record_track:
                trk.append((t1, lat.copy(), lon.copy()))
        out["h"] = h
        out["t_sw2"] = t_sw2
        out["snap_km"] = snap_km
        if record_track:
            out["track_t"] = np.array([x[0] for x in trk])
            out["track_lat"] = np.stack([x[1] for x in trk], 1)
            out["track_lon"] = np.stack([x[2] for x in trk], 1)
        return out


# ------------------------------------------------------------------------------ priors
GS1_PRIOR = ("u", 220.0, 520.0)        # WPTS: ground speed (kt) of the FMT -> W leg
ROC1840_PRIOR = ("u", -4000.0, 0.0)    # sensitivity: rate of climb (fpm) at the 18:40 call


class LikelihoodVU(sp.Likelihood):
    """satcom_paths.Likelihood plus an optional vertical speed at the 18:40 call (sensitivity
    "d1840"): model_out["roc1840_fpm"] (N,) enters the BFO uplink Doppler of that measurement
    (the AES compensates horizontal velocity only), as in satcom.bfo."""

    def predict(self, model_out, t_meas):
        bto, bfo = super().predict(model_out, t_meas)
        roc = model_out.get("roc1840_fpm")
        if roc is None:
            return bto, bfo
        j = list(self.bfo.label).index("C 18:40 mean")
        idx = {t: i for i, t in enumerate(t_meas)}
        k = idx[self.bfo.t.iloc[j]]
        o = model_out
        vu = np.asarray(roc, float) * 0.3048 / 60
        bfo = bfo.copy()
        bfo[:, j] = satcom.bfo(self.bfo.t.iloc[j], o["lat"][:, k], o["lon"][:, k], o["h"],
                               o["vn"][:, k], o["ve"][:, k], vu, bias=0.0)
        return bto, bfo
def prior_spec(family, base_spec, fix=None, tie=False):
    """Prior spec for a route family built from the single-mode baseline spec (same order as
    satcom_paths.PathModel.PARAMS: lat0, lon0, trk_pre, gs_pre, t_fmt, theta, mach, fl).

    WPT: theta2 takes the single-mode theta prior (U(140, 230) deg).  TWO: theta1 and theta2 both
    take it; u2 ~ U(0, 1).  `fix`: dict name -> value (removed from the sampled set).  `tie`
    (TWO only): theta2 := theta1 (sanity check: must reproduce the CTT single-mode evidence).
    Returns (names_sampled, spec_sampled, fixed_values, tie)."""
    b = dict(zip(sp.PathModel.PARAMS, base_spec))
    full = {"lat0": b["lat0"], "lon0": b["lon0"], "trk_pre": b["trk_pre"], "gs_pre": b["gs_pre"],
            "t_fmt": b["t_fmt"], "mach": b["mach"], "fl": b["fl"]}
    if family in ("WPT", "WPTS"):
        full["theta2"] = b["theta"]
        full["gs1"] = GS1_PRIOR
    else:
        full["theta1"] = b["theta"]
        full["u2"] = ("u", 0.0, 1.0)
        full["theta2"] = b["theta"]
    fix = dict(fix or {})
    names = [k for k in PARAMS[family] if k not in fix and not (tie and k == "theta2")]
    return names, [full[k] for k in names], fix, tie


def make_params(x, names, fix=None, tie=False):
    P = {k: x[:, i] for i, k in enumerate(names)}
    n = x.shape[0]
    for k, v in (fix or {}).items():
        P[k] = np.full(n, float(v))
    if tie:
        P["theta2"] = P["theta1"]
    return P
