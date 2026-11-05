"""Arc-relative coordinates for the OI-2018 digitisation workstream.

cross_arc_signed(lon, lat) -> (lat_on_arc, d_km): latitude of the nearest point on the sea-level 7th arc
(BTO 18,400 us at 00:19:29.416, from mh370.geo) and the signed perpendicular distance to it,
positive = south-east of the arc (further from the satellite, 'outside'), negative = north-west ('inside').
offset_point(arc_lat, d_km) -> lon/lat of the point at signed distance d_km from the arc at arc latitude arc_lat.
"""
import sys
from pathlib import Path
import numpy as np
from pyproj import Geod

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from mh370 import geo  # noqa: E402

_ARC = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-40.0, -20.0 + 1e-9, 0.01))
R = 6371.0088
_G = Geod(ellps='WGS84')


def _xyz(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], axis=-1)


_A = _xyz(_ARC[:, 0], _ARC[:, 1])


def _cross_arc(lon, lat):
    lon = np.atleast_1d(np.asarray(lon, float)); lat = np.atleast_1d(np.asarray(lat, float))
    P = _xyz(lat, lon)
    out_lat = np.empty(len(P)); out_d = np.empty(len(P))
    for k in range(0, len(P), 2000):
        p = P[k:k + 2000]
        i = np.clip(np.argmax(p @ _A.T, axis=1), 1, len(_A) - 2)   # nearest arc node (0.01 deg spacing)
        a = _A[i]; t = _A[i + 1] - _A[i - 1]; t /= np.linalg.norm(t, axis=1)[:, None]
        n = np.cross(a, t)
        ang = np.arccos(np.clip(np.sum(p * a, axis=1), -1, 1)) * R  # distance to node
        s = np.sum((p - a) * t, axis=1) * R                          # along-arc residual
        out_lat[k:k + 2000] = _ARC[i, 0]
        out_d[k:k + 2000] = np.sign(np.sum(p * n, axis=1)) * np.sqrt(np.maximum(ang ** 2 - s ** 2, 0))
    return out_lat, out_d


_la0 = -30.0
_SIGN = float(np.sign(_cross_arc(np.interp(_la0, _ARC[:, 0], _ARC[:, 1]) + 0.5, _la0)[1][0]))  # east => positive


def cross_arc_signed(lon, lat):
    la, d = _cross_arc(lon, lat)
    return la, d * _SIGN


def arc_lon(lat):
    return np.interp(lat, _ARC[:, 0], _ARC[:, 1])


def offset_point(arc_lat, d_km):
    arc_lat = np.atleast_1d(np.asarray(arc_lat, float)); d_km = np.broadcast_to(np.asarray(d_km, float), arc_lat.shape)
    out = []
    for la, d in zip(arc_lat, d_km):
        lo = arc_lon(la); lo2 = arc_lon(la + 0.01)
        az, _, _ = _G.inv(lo, la, lo2, la + 0.01)       # tangent pointing north-east along the arc
        x, y, _ = _G.fwd(lo, la, az + 90.0, d * 1000.0)  # +90 deg = south-east side
        out.append((x, y))
    return np.array(out)
