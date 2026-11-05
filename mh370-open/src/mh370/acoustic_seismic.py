"""Workstream D, step 4: open FDSN seismometer checks of candidate acoustic events.

Helpers to load the downloaded waveforms (data/raw/fdsn_seismic), remove instrument
response, compute band envelopes / STA-LTA, predict P/S (ak135, obspy.taup) and T-phase
(geodesic distance / SOFAR speed) arrivals, and measure SNR against empirical noise.

Times: project seconds since 2014-03-07 00:00 UTC (mh370.acoustic.t_of / dt_of).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from obspy import Stream, UTCDateTime, read, read_inventory
from obspy.taup import TauPyModel

from mh370 import acoustic as A

ROOT = Path(__file__).resolve().parents[2]
SEIS = ROOT / "data" / "raw" / "fdsn_seismic"
EPOCH_UTC = UTCDateTime(2014, 3, 7)

# Preferred vertical channel per station (same choice on control nights)
ZCHAN = {
    "COCO": "II.COCO.10.BHZ", "XMIS": "AU.XMIS..BHZ", "XMI": "AU.XMI..BHZ",
    "AIS": "G.AIS.00.BHZ", "RODM": "G.RODM.00.BHZ", "ROCAM": "G.ROCAM.00.HHZ",
    "DGAR": "II.DGAR.10.BHZ", "NWAO": "IU.NWAO.10.BHZ", "MBWA": "IU.MBWA.10.BHZ",
    "AUBUS": "S1.AUBUS..HHZ", "GIRL": "AU.GIRL..BHZ", "CISI": "GE.CISI..BHZ",
    "JAGI": "GE.JAGI..BHZ", "SMRI": "GE.SMRI..BHZ", "UGM": "GE.UGM..BHZ",
    "KAAM": "GE.KAAM..BHZ", "MNC": "IN.MNC..HHZ",
}
NETSTA = {s: ".".join(c.split(".")[:2]) for s, c in ZCHAN.items()}


def ut(t: float) -> UTCDateTime:
    return EPOCH_UTC + float(t)


def tp(u: UTCDateTime) -> float:
    return float(u - EPOCH_UTC)


@lru_cache(maxsize=None)
def inventory(night: str, sta: str):
    return read_inventory(str(SEIS / night / f"{NETSTA[sta]}.xml"))


def coords(sta: str, night: str = "night_20140308"):
    inv = inventory(night, sta)
    c = inv.get_coordinates(ZCHAN[sta], UTCDateTime(2014, 3, 8))
    return c["latitude"], c["longitude"]


@lru_cache(maxsize=64)
def _raw(night: str, sta: str) -> Stream:
    return read(str(SEIS / night / f"{NETSTA[sta]}.mseed"))


def load(sta: str, night: str = "night_20140308", comp: str = "Z", output: str = "VEL",
         remove_resp: bool = True):
    """Return a single merged, response-corrected trace (m/s for VEL) for the station's
    preferred channel (comp 'Z', or 'N'/'E'/'1'/'2' horizontals with the same loc/band).
    Gaps are filled with zeros after demeaning (and reported in tr.stats.gaps_s)."""
    cid = ZCHAN[sta]
    if comp != "Z":
        n, s, loc, ch = cid.split(".")
        cands = [f"{n}.{s}.{loc}.{ch[:2]}{c}" for c in (comp,)]
    else:
        cands = [cid]
    st = Stream([tr.copy() for tr in _raw(night, sta) if tr.id in cands])
    if len(st) == 0:
        return None
    gaps = sum(g[6] for g in st.get_gaps() if g[6] > 0)
    st.detrend("demean")
    st.merge(method=1, fill_value=0)
    tr = st[0]
    tr.detrend("linear")
    tr.taper(0.002)
    if remove_resp:
        fs = tr.stats.sampling_rate
        tr.remove_response(inventory=inventory(night, sta), output=output,
                           pre_filt=(0.2, 0.4, 0.42 * fs, 0.48 * fs), water_level=60)
    tr.stats.gaps_s = gaps
    return tr


def band_env(tr, f1, f2, win_s=5.0, step_s=1.0):
    """Band-pass (4-pole zero-phase Butterworth) then RMS envelope in sliding windows.
    Returns (project times of window centres, rms)."""
    x = tr.copy()
    fs = x.stats.sampling_rate
    f2 = min(f2, 0.45 * fs)
    x.filter("bandpass", freqmin=f1, freqmax=f2, corners=4, zerophase=True)
    y = x.data.astype(float) ** 2
    w, s = int(win_s * fs), int(step_s * fs)
    c = np.r_[0, np.cumsum(y)]
    idx = np.arange(0, y.size - w + 1, s)
    rms = np.sqrt((c[idx + w] - c[idx]) / w)
    t = tp(x.stats.starttime) + (idx + w / 2) / fs
    return t, rms


def bands_for(tr):
    fs = tr.stats.sampling_rate
    lo = (2.0, 8.0)
    hi = (3.0, 18.0) if fs >= 50 else (3.0, 16.0) if fs >= 40 else None
    return {"2-8": lo, **({"3-18" if fs >= 50 else "3-16": hi} if hi else {})}


def window_stat(t, env, w0, w1, noise=(-900.0, -60.0), ref=None):
    """SNR statistic: max envelope in [w0, w1] over the median envelope in a noise window
    [ref+noise[0], ref+noise[1]] (ref defaults to w0). Returns (snr_db, t_of_max)."""
    ref = w0 if ref is None else ref
    m = (t >= w0) & (t <= w1)
    n = (t >= ref + noise[0]) & (t <= ref + noise[1])
    if m.sum() < 2 or n.sum() < 10:
        return np.nan, np.nan
    k = np.argmax(env[m])
    return 20 * np.log10(env[m][k] / np.median(env[n])), float(t[m][k])


def null_distribution(t, env, win_len, noise=(-900.0, -60.0), step=10.0, exclude=()):
    """Empirical distribution of window_stat over all window positions in a trace
    (noise-only reference), skipping windows overlapping any (a, b) in exclude."""
    out = []
    a = t[0] - noise[0]
    while a + win_len < t[-1]:
        if not any((a < e1 and a + win_len > e0) for e0, e1 in exclude):
            v, _ = window_stat(t, env, a, a + win_len, noise)
            if np.isfinite(v):
                out.append(v)
        a += step
    return np.array(out)


MODEL = None


def taup():
    global MODEL
    if MODEL is None:
        MODEL = TauPyModel("ak135")
    return MODEL


def ps_times(src_lat, src_lon, depth_km, sta_lat, sta_lon):
    """First P and S arrival travel times (s) from ak135; distance in degrees."""
    from obspy.geodetics import locations2degrees
    deg = locations2degrees(src_lat, src_lon, sta_lat, sta_lon)
    arr = taup().get_travel_times(max(depth_km, 0.0), deg, phase_list=["P", "p", "Pn", "Pg",
                                                                       "S", "s", "Sn", "Sg"])
    tp_ = min([a.time for a in arr if a.name.upper().startswith("P")], default=np.nan)
    ts_ = min([a.time for a in arr if a.name.upper().startswith("S")], default=np.nan)
    return tp_, ts_, deg


def t_window(dist_km, t0, c_lo=1.46, c_hi=1.50, pad_early=30.0, pad_late=60.0):
    """Predicted T-phase arrival window for a source at distance dist_km, origin t0."""
    return t0 + dist_km / c_hi - pad_early, t0 + dist_km / c_lo + pad_late


def fwd(lat, lon, az, dist_km):
    """Broadcast-safe geodesic forward problem (pyproj needs equal-length arrays)."""
    lat, lon, az, d = np.broadcast_arrays(*(np.asarray(v, float) for v in (lat, lon, az, dist_km)))
    lo, la, _ = A.GEOD.fwd(lon.ravel(), lat.ravel(), az.ravel(), d.ravel() * 1000.0)
    return np.asarray(la).reshape(lat.shape), np.asarray(lo).reshape(lat.shape)


def arc_crossing(rcv: str, az: float, rmax=6000.0, h_m=0.0):
    """First 7th-arc (sea level) crossing along azimuth az from a receiver in
    acoustic.RECEIVERS (same algorithm as acoustic.arc_crossing, broadcast-safe)."""
    from scipy.optimize import brentq
    r0 = A.RECEIVERS[rcv]
    rs = np.arange(50.0, rmax, 10.0)
    la, lo = fwd(r0["lat"], r0["lon"], az, rs)
    f = np.array([A._arc_resid(a, b, h_m) for a, b in zip(la, lo)])
    idx = np.where(np.sign(f[:-1]) != np.sign(f[1:]))[0]
    if idx.size == 0:
        return np.nan, np.nan, np.nan

    def g(r):
        a, b = fwd(r0["lat"], r0["lon"], az, r)
        return A._arc_resid(float(a), float(b), h_m)

    r = brentq(g, rs[idx[0]], rs[idx[0] + 1], xtol=1e-3)
    a, b = fwd(r0["lat"], r0["lon"], az, r)
    return r, float(a), float(b)
