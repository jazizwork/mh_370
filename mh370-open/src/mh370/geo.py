"""Shared geometry for the mh370-open project.

Everything here is derived from public sources:
  * Satellite (Inmarsat-3F1) ECEF positions/velocities: ATSB "MH370 - Flight Path
    Analysis Update" (2014) Table 4, transcribed in external/sladen_inmarsat-9m-mro/atsb/.
  * BTO bias -495,679 us: ATSB Table 2 (KLIA gate calibration average).
  * BTO = (round-trip path GES->sat->AES->sat->GES)/c + bias  (ATSB 2014; Ashton et al. 2015).

Conventions used across all modules (see PROJECT.md):
  * Latitude/longitude in degrees, WGS84; heights in metres above the ellipsoid.
  * Times are seconds since 2014-03-07 00:00:00 UTC unless stated otherwise.
"""
from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.optimize import brentq

C_KM_S = 299_792.458
WGS84_A = 6378.137  # km
WGS84_F = 1 / 298.257223563
WGS84_E2 = WGS84_F * (2 - WGS84_F)

BTO_BIAS_US = -495_679.0

# Inmarsat Perth ground earth station (approx., public). Sensitivity: a 1 km error in
# GES position shifts every arc by well under 1 km because it enters both legs equally
# for all aircraft positions (it is a constant term in the path length).
PERTH_GES_LLH = (-31.8022, 115.8870, 0.0)

# ATSB Table 4: satellite ECEF position (km) and velocity (km/s)
_SAT_TABLE = np.array([
    # hh, mm, x, y, z, vx, vy, vz
    [16, 30, 18122.9, 38080.0, 828.5, 0.00216, -0.00107, 0.06390],
    [16, 45, 18124.8, 38079.0, 884.2, 0.00212, -0.00114, 0.05980],
    [16, 55, 18126.1, 38078.3, 919.2, 0.00209, -0.00118, 0.05693],
    [17, 5, 18127.3, 38077.6, 952.5, 0.00206, -0.00120, 0.05395],
    [18, 25, 18136.7, 38071.8, 1148.5, 0.00188, -0.00117, 0.02690],
    [19, 40, 18145.1, 38067.0, 1206.3, 0.00189, -0.00092, -0.00148],
    [20, 40, 18152.1, 38064.0, 1159.7, 0.00200, -0.00077, -0.02422],
    [21, 40, 18159.5, 38061.3, 1033.8, 0.00212, -0.00076, -0.04531],
    [22, 40, 18167.2, 38058.3, 837.2, 0.00211, -0.00096, -0.06331],
    [24, 10, 18177.5, 38051.7, 440.0, 0.00160, -0.00151, -0.08188],
    [24, 20, 18178.4, 38050.8, 390.5, 0.00150, -0.00158, -0.08321],
])
_SAT_T = _SAT_TABLE[:, 0] * 3600 + _SAT_TABLE[:, 1] * 60
# Hermite-style: fit cubic splines to position; velocity from the table is used for
# BFO work via its own spline (the spline derivative agrees to ~1e-4 km/s).
_SAT_POS_SPL = [CubicSpline(_SAT_T, _SAT_TABLE[:, 2 + i]) for i in range(3)]
_SAT_VEL_SPL = [CubicSpline(_SAT_T, _SAT_TABLE[:, 5 + i]) for i in range(3)]


def hms(h: float, m: float = 0, s: float = 0) -> float:
    """Seconds since 2014-03-07 00:00 UTC (use h>=24 for 8 March)."""
    return h * 3600 + m * 60 + s


def sat_pos(t: float) -> np.ndarray:
    """Satellite ECEF position (km) at time t (s since 2014-03-07 00:00 UTC)."""
    return np.array([s(t) for s in _SAT_POS_SPL])


def sat_vel(t: float) -> np.ndarray:
    """Satellite ECEF velocity (km/s)."""
    return np.array([s(t) for s in _SAT_VEL_SPL])


def llh_to_ecef(lat, lon, h_m=0.0):
    """WGS84 geodetic -> ECEF (km). Accepts scalars or arrays."""
    lat = np.radians(lat)
    lon = np.radians(lon)
    h = np.asarray(h_m) / 1000.0
    n = WGS84_A / np.sqrt(1 - WGS84_E2 * np.sin(lat) ** 2)
    x = (n + h) * np.cos(lat) * np.cos(lon)
    y = (n + h) * np.cos(lat) * np.sin(lon)
    z = (n * (1 - WGS84_E2) + h) * np.sin(lat)
    return np.stack([x, y, z], axis=-1)


GES_ECEF = llh_to_ecef(*PERTH_GES_LLH)


def bto_path_km(bto_us: float) -> float:
    """Round-trip path length implied by a BTO value."""
    return (bto_us - BTO_BIAS_US) * 1e-6 * C_KM_S


def predicted_bto(lat, lon, h_m, t) -> np.ndarray:
    """Predicted BTO (us) for an aircraft at (lat, lon, h) at time t."""
    s = sat_pos(t)
    d_aes = np.linalg.norm(llh_to_ecef(lat, lon, h_m) - s, axis=-1)
    d_ges = np.linalg.norm(GES_ECEF - s)
    return 2 * (d_aes + d_ges) / C_KM_S * 1e6 + BTO_BIAS_US


def sat_to_aes_range_km(bto_us: float, t: float) -> float:
    """Satellite-to-aircraft range implied by a BTO at time t."""
    d_ges = np.linalg.norm(GES_ECEF - sat_pos(t))
    return bto_path_km(bto_us) / 2 - d_ges


def arc_lon_for_lat(lat: float, bto_us: float, t: float, h_m: float = 0.0,
                    lon_bounds=(70.0, 125.0)) -> float:
    """Longitude on the BTO arc at a given latitude (the eastern/Indian Ocean branch
    within lon_bounds). Returns nan if the arc does not cross that latitude there."""
    r = sat_to_aes_range_km(bto_us, t)
    s = sat_pos(t)

    def f(lon):
        return np.linalg.norm(llh_to_ecef(lat, lon, h_m) - s) - r

    a, b = lon_bounds
    fa, fb = f(a), f(b)
    if np.sign(fa) == np.sign(fb):
        return np.nan
    return brentq(f, a, b, xtol=1e-7)


def arc_polyline(bto_us: float, t: float, h_m: float = 0.0,
                 lats=np.arange(-45.0, -5.0 + 1e-9, 0.05)) -> np.ndarray:
    """(N,2) array of (lat, lon) along the arc."""
    out = [(la, arc_lon_for_lat(la, bto_us, t, h_m)) for la in lats]
    return np.array([p for p in out if np.isfinite(p[1])])


# ---------------------------------------------------------------------------------
# Published handshake data (public Inmarsat log; ATSB/DSTG corrected values)
# BTO for the 18:25:27 and 00:19:29 log-on requests carries a known +4,600 us
# offset (ATSB 2014 / Ashton et al. 2015); corrected values are given here.
# ---------------------------------------------------------------------------------
ARC7_TIME = hms(24, 19, 29.416)
ARC7_BTO_US = 18_400.0

HANDSHAKES = [
    # label, time (s), BTO (us, corrected) or nan, BFO (Hz) or nan
    ("18:25:27 log-on req", hms(18, 25, 27.421), 12_520.0, 142.0),
    ("18:39 call (mean)", hms(18, 39, 58.0), np.nan, 88.0),
    ("19:41 HS", hms(19, 41, 0.0), 11_500.0, 111.0),
    ("20:41 HS", hms(20, 41, 2.0), 11_740.0, 141.0),
    ("21:41 HS", hms(21, 41, 24.0), 12_780.0, 168.0),
    ("22:41 HS", hms(22, 41, 19.0), 14_540.0, 204.0),
    ("23:14 call (mean)", hms(23, 14, 1.0), np.nan, 217.0),
    ("00:10:58 HS", hms(24, 10, 58.0), 18_040.0, 252.0),
    ("00:19:29 log-on req (7th arc)", ARC7_TIME, ARC7_BTO_US, 182.0),
]


def haversine_km(lat1, lon1, lat2, lon2, r=6371.0088):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = p2 - p1
    dl = np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))
