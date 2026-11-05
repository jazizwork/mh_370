"""Workstream A ("satcom"): BTO/BFO forward model for 9M-MRO / Inmarsat-3F1.

Independent Python implementation of the published measurement model:

  BFO = dF_up + dF_down + df_comp + df_sat + df_AFC + df_bias          (Ashton et al. 2015 eq. 1;
                                                                        DSTG book eq. 5.6)
  * dF_up    : Doppler of the L-band uplink (aircraft -> satellite) from the *relative*
               aircraft/satellite motion (true satellite ephemeris, ATSB Table 4).
  * dF_down  : Doppler of the C-band downlink (satellite -> Perth GES), satellite motion only.
  * df_comp  : AES (SDU) pre-compensation: the AES removes the Doppler it *expects* from its own
               horizontal ground velocity, assuming (DSTG 2016 sec 5.3) altitude 0, vertical
               speed 0, and a motionless satellite at 64.5E, 0N, 422 km above the nominal
               35,788.12 km geostationary altitude.
  * df_sat + df_AFC : satellite translation-oscillator variation + Perth EAFC correction.
               These are *measured* (Inmarsat, pilot-signal method) and published only as the
               combined "Satellite and EAFC effect" in ATSB (2014) Table 4 (= the CSV
               external/sladen_inmarsat-9m-mro/atsb/table-4-satellite-and-afc-values.csv).
               Table 4 does NOT contain the satellite-motion Doppler terms: ATSB Tables 5/6
               (13 Aug 2014 revision) list "Satellite Doppler (uplink)" and "Satellite Doppler
               (downlink)" as separate rows next to "Satellite and EAFC effect" (24.1 Hz at
               17:07).  This is verified numerically in scripts/satcom_validate_bfo.py.
  * df_bias  : fixed frequency bias of the AES oscillator etc.; calibrated here from the
               on-ground and early in-flight R-channel data (ATSB/Ashton: ~150-152.5 Hz).

BTO uses mh370.geo (round trip GES->sat->AES->sat->GES, bias -495,679 us).

Units: SI internally (m, m/s, Hz); time in seconds since 2014-03-07 00:00 UTC.
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

from mh370 import geo

ROOT = pathlib.Path(__file__).resolve().parents[2]
EXT = ROOT / "external" / "sladen_inmarsat-9m-mro"

C_M_S = 299_792_458.0
F_UP_HZ = 1_646.6525e6      # L-band AES transmit (Ashton et al. 2015; ATSB 2014)
F_DOWN_HZ = 3_615.1525e6    # C-band satellite -> GES (Ashton et al. 2015)

# Nominal satellite position assumed by the AES Doppler pre-compensation (DSTG 2016 sec 5.3)
AES_SAT_LON = 64.5
AES_SAT_ALT_M = (35_788.12 + 422.0) * 1e3

# Unix time of the time base (2014-03-07 00:00:00 UTC)
UNIX_T0 = 1_394_150_400


# ----------------------------------------------------------------------------------------
# geometry helpers (vectorised)
# ----------------------------------------------------------------------------------------
def sat_state(t):
    """Satellite ECEF position and velocity (m, m/s) for scalar/array t. Shapes (...,3)."""
    t = np.asarray(t, dtype=float)
    p = np.stack([s(t) for s in geo._SAT_POS_SPL], axis=-1) * 1e3
    v = np.stack([s(t) for s in geo._SAT_VEL_SPL], axis=-1) * 1e3
    return p, v


def ecef_m(lat, lon, h_m):
    return geo.llh_to_ecef(lat, lon, h_m) * 1e3


def enu_basis(lat, lon):
    """Unit east/north/up vectors in ECEF for geodetic lat/lon (deg). Each (...,3)."""
    la, lo = np.radians(lat), np.radians(lon)
    sl, cl, so, co = np.sin(la), np.cos(la), np.sin(lo), np.cos(lo)
    e = np.stack([-so, co, np.zeros_like(so)], axis=-1)
    n = np.stack([-sl * co, -sl * so, cl], axis=-1)
    u = np.stack([cl * co, cl * so, sl], axis=-1)
    return e, n, u


def vel_ecef(lat, lon, vn, ve, vu=0.0):
    e, n, u = enu_basis(lat, lon)
    vn, ve, vu = (np.asarray(x, dtype=float)[..., None] for x in (vn, ve, vu))
    return vn * n + ve * e + vu * u


def _sph_ecef(lat, lon, r):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([r * np.cos(la) * np.cos(lo), r * np.cos(la) * np.sin(lo),
                     r * np.sin(la) * np.ones_like(lo)], axis=-1)


# ----------------------------------------------------------------------------------------
# df_sat + df_AFC  (ATSB Table 4)
# ----------------------------------------------------------------------------------------
def load_table4_afc():
    df = pd.read_csv(EXT / "atsb" / "table-4-satellite-and-afc-values.csv")
    hh = df.iloc[:, 0].str.split(":", expand=True).astype(int)
    t = hh[0] * 3600 + hh[1] * 60 + hh[2]
    t = np.where(hh[0] < 12, t + 86400, t)       # 00:xx belongs to 8 March
    return np.asarray(t, float), df.iloc[:, 1].to_numpy(float)


_T4_T, _T4_V = load_table4_afc()


def sat_afc_hz(t, extrapolate="hold"):
    """df_sat + df_AFC (Hz) by linear interpolation of ATSB Table 4.
    Outside the table range the end value is held (flagged in the validation)."""
    return np.interp(np.asarray(t, float), _T4_T, _T4_V)


# ----------------------------------------------------------------------------------------
# BFO model
# ----------------------------------------------------------------------------------------
def bfo_terms(t, lat, lon, h_m, vn, ve, vu=0.0, bias=150.0, aes_earth="sphere",
              afc=None):
    """Return dict of BFO components (Hz). Inputs broadcast; velocities are ground-relative
    (m/s, north/east/up). `afc` overrides df_sat+df_AFC if given."""
    t = np.asarray(t, float)
    lat, lon, h_m = np.broadcast_arrays(np.asarray(lat, float), np.asarray(lon, float),
                                        np.asarray(h_m, float))
    ps, vs = sat_state(t)
    pa = ecef_m(lat, lon, h_m)
    va = vel_ecef(lat, lon, vn, ve, vu)
    # uplink: range rate of satellite w.r.t. aircraft (positive = receding)
    d = ps - pa
    rng = np.linalg.norm(d, axis=-1)
    rdot_up = np.sum((vs - va) * d, axis=-1) / rng
    dF_up = -F_UP_HZ * rdot_up / C_M_S
    # downlink: satellite -> Perth GES (GES fixed in ECEF)
    g = geo.GES_ECEF * 1e3
    dg = ps - g
    rdot_dn = np.sum(vs * dg, axis=-1) / np.linalg.norm(dg, axis=-1)
    dF_down = -F_DOWN_HZ * rdot_dn / C_M_S
    # AES compensation: horizontal velocity only, altitude 0, nominal satellite
    if aes_earth == "sphere":
        R = geo.WGS84_A * 1e3
        pa0 = _sph_ecef(lat, lon, R)
        sbar = _sph_ecef(0.0, AES_SAT_LON, R + AES_SAT_ALT_M)
    else:
        pa0 = ecef_m(lat, lon, 0.0)
        sbar = ecef_m(0.0, AES_SAT_LON, AES_SAT_ALT_M)
    vh = vel_ecef(lat, lon, vn, ve, 0.0)
    d0 = sbar - pa0
    rdot_nom = np.sum((-vh) * d0, axis=-1) / np.linalg.norm(d0, axis=-1)
    df_comp = +F_UP_HZ * rdot_nom / C_M_S       # removes the expected aircraft Doppler
    # split of uplink into aircraft and satellite parts (for reporting only)
    dF_up_ac = -F_UP_HZ * np.sum((-va) * d, axis=-1) / rng / C_M_S
    dF_up_sat = dF_up - dF_up_ac
    f_afc = sat_afc_hz(t) if afc is None else np.asarray(afc, float)
    total = dF_up + dF_down + df_comp + f_afc + bias
    return dict(dF_up=dF_up, dF_up_ac=dF_up_ac, dF_up_sat=dF_up_sat, dF_down=dF_down,
                df_comp=df_comp, afc=f_afc * np.ones_like(total), bias=bias * np.ones_like(total),
                bfo=total)


def bfo(t, lat, lon, h_m, vn, ve, vu=0.0, bias=150.0, **kw):
    return bfo_terms(t, lat, lon, h_m, vn, ve, vu, bias=bias, **kw)["bfo"]


def bto(t, lat, lon, h_m):
    """Predicted BTO (us), vectorised version of geo.predicted_bto (same constants)."""
    t = np.asarray(t, float)
    ps, _ = sat_state(t)
    pa = ecef_m(lat, lon, h_m)
    d_aes = np.linalg.norm(pa - ps, axis=-1)
    d_ges = np.linalg.norm(geo.GES_ECEF * 1e3 - ps, axis=-1)
    return 2 * (d_aes + d_ges) / C_M_S * 1e6 + geo.BTO_BIAS_US


def gs_track_to_vn_ve(gs_kt, track_deg):
    gs = np.asarray(gs_kt, float) * 1852 / 3600
    tr = np.radians(track_deg)
    return gs * np.cos(tr), gs * np.sin(tr)


# ----------------------------------------------------------------------------------------
# Inmarsat log
# ----------------------------------------------------------------------------------------
def load_su_log():
    df = pd.read_csv(EXT / "inmarsat-su-log-redacted.csv")
    ts = pd.to_datetime(df["Time"], format="%d/%m/%Y %H:%M:%S.%f")
    df["t"] = (ts - pd.Timestamp("2014-03-07")).dt.total_seconds()
    df["bfo"] = df["Frequency Offset (Hz)"]
    df["bto"] = df["Burst Timing Offset (microseconds)"]
    df["chan"] = df["Channel Type"].str[0]          # R, T, C, P
    return df


# Measurements used in the path likelihood (Ashton et al. 2015 Table 6 values; geo.HANDSHAKES)
# kind: 'R1200' handshake, 'C' call (mean of C-channel BFOs), 'R600' log-on request.
MEAS = [
    # label,          t (s),                       BTO us, BFO Hz, kind
    ("18:25:27", geo.hms(18, 25, 27.421), 12_520.0, 142.0, "R600"),
    ("18:28:15", geo.hms(18, 28, 15.0), np.nan, 143.0, "R1200"),
    ("18:39:58", geo.hms(18, 39, 58.0), np.nan, 88.0, "C"),
    ("19:41:03", geo.hms(19, 41, 3.0), 11_500.0, 111.0, "R1200"),
    ("20:41:05", geo.hms(20, 41, 5.0), 11_740.0, 141.0, "R1200"),
    ("21:41:27", geo.hms(21, 41, 27.0), 12_780.0, 168.0, "R1200"),
    ("22:41:22", geo.hms(22, 41, 22.0), 14_540.0, 204.0, "R1200"),
    ("23:14:01", geo.hms(23, 14, 1.0), np.nan, 217.0, "C"),
    ("00:10:59", geo.hms(24, 10, 59.0), 18_040.0, 252.0, "R1200"),
    ("00:19:29", geo.ARC7_TIME, geo.ARC7_BTO_US, 182.0, "R600"),
]
