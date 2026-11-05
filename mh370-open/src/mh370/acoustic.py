"""Workstream D (acoustic): open-data test of candidate hydroacoustic MH370 impact events.

Contents
  * Python port of the AODN/CMST MATLAB reader NL_load_logger_data_new.m
    (A. Gavrilov, CMST Curtin, 2012-13) for IMOS passive-acoustic .DAT files.
  * Calibration to sound pressure (uPa) with the per-deployment curves t<id>_calibration.csv
    ("Frequency response (power spectrum density) in dB re ADC unit/uPa", 1 Hz bins).
  * Geometry: receivers, candidate sources, 7th-arc points, geodesic T-phase travel times,
    bearing/arc crossings, bathymetric path profiles.
  * Signal processing: decimation, band levels, spectrograms, band-excess and STA/LTA detectors.

Time base: seconds since 2014-03-07 00:00:00 UTC (as mh370.geo); helpers convert datetimes.
All downloaded inputs live under data/raw/ (untrusted data; nothing there is executed).
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from pyproj import Geod
from scipy import signal
from scipy.optimize import brentq

from mh370 import geo

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "imos_acoustic"
BATHY = ROOT / "data" / "raw" / "etopo2022_subset" / "etopo2022_2min_55S12N_50E150E.nc"
EPOCH = dt.datetime(2014, 3, 7)  # project time base (UTC, naive)
GEOD = Geod(ellps="WGS84")

# --------------------------------------------------------------------------------------
# Sound speed for T-phases (horizontal group speed in the SOFAR channel)
# --------------------------------------------------------------------------------------
# 1.48 km/s is the conventional T-phase group speed for the mid-latitude Indian Ocean
# (Stead 2014 used 1.46-1.485 km/s; Kadri 2024 used 1.50 +/- 0.07). We use 1.48 nominal
# with +/-0.01 km/s sensitivity and +/-0.02 as a wide bound.
C_SOFAR = 1.48
C_SENS = (1.47, 1.49)
C_WIDE = (1.46, 1.50)

# --------------------------------------------------------------------------------------
# Receivers
# --------------------------------------------------------------------------------------
# IMOS positions/depths from AODN metadata/update.20191119-110328.csv (deployment rows).
# HA01 (IMS H01W triad) element positions from FDSN station metadata (EarthScope),
# W1 -34.892899 114.1539 (1063 m), W2 -34.897079 114.134033 (1046 m),
# W3 -34.880932 114.139977 (1056 m); we use the triad centroid.
RECEIVERS = {
    "PAPCA": dict(lat=-31.84216667, lon=115.01373333, depth_m=390.0, dep="3376",
                  name="IMOS Perth Canyon (PAPCA 3376)"),
    "PAKIM": dict(lat=-15.48336667, lon=121.251, depth_m=np.nan, dep="3250",
                  name="IMOS Kimberley (PAKIM 3250)"),
    "PAPOR": dict(lat=-38.53696667, lon=141.24756667, depth_m=159.0, dep="3274",
                  name="IMOS Portland VIC (PAPOR 3274)"),
    "HA01": dict(lat=float(np.mean([-34.892899, -34.897079, -34.880932])),
                 lon=float(np.mean([114.1539, 114.134033, 114.139977])), depth_m=1055.0,
                 dep=None, name="IMS HA01 / H01W Cape Leeuwin (waveforms not public)"),
    "HA08S": dict(lat=float(np.mean([-7.6453, -7.64534, -7.6275])),
                  lon=float(np.mean([72.474403, 72.493248, 72.483833])), depth_m=1376.0,
                  dep=None, name="IMS HA08 south triad, Diego Garcia (not public)"),
}
IMOS_SITES = ("PAPCA", "PAKIM", "PAPOR")


def t_of(d: dt.datetime) -> float:
    """Project time (s since 2014-03-07 00:00 UTC) of a naive-UTC datetime."""
    return (d - EPOCH).total_seconds()


def dt_of(t: float) -> dt.datetime:
    return EPOCH + dt.timedelta(seconds=float(t))


def hms8(h, m=0, s=0.0) -> float:
    """Project time for hh:mm:ss on 8 March 2014 (h may be <24)."""
    return geo.hms(24 + h, m, s)


def fmt(t: float, frac: int = 0) -> str:
    d = dt_of(t)
    s = d.strftime("%H:%M:%S")
    if frac:
        s += f"{(d.microsecond / 1e6):.{frac}f}"[1:]
    return s


# --------------------------------------------------------------------------------------
# Candidate events (published; see outputs/acoustic/README.md for sources)
# --------------------------------------------------------------------------------------
# Kadri (2024) Sci. Rep. 14:10102, Table 1: signals at H01W from 00:36 UTC (time, bearing,
# Kadri's delta-t in min). Bearing accuracy quoted +/-0.4 deg (99.5% CI).
KADRI_TABLE1 = [
    ("00:38:29", 261.24, -3.68), ("00:39:02", 268.24, 0.0), ("00:39:53", 256.77, -4.27),
    ("00:40:34", 303.28, 3.60), ("00:41:43", 309.96, 4.03), ("00:42:02", 253.66, 3.93),
    ("00:45:36", 311.98, 7.70), ("00:47:04", 343.16, -2.30), ("00:48:55", 291.13, 11.77),
    ("00:49:41", 234.67, np.nan), ("00:49:58", 260.41, 7.43), ("00:51:50", 320.40, 12.72),
    ("00:52:36", 329.51, 11.10), ("00:52:36", 324.26, 12.65), ("00:52:50", 274.84, 14.15),
    ("00:53:31", 257.58, 9.75), ("00:53:38", 315.46, 15.32), ("00:54:30", 306.18, 17.10),
    ("00:55:07", 314.15, 16.95),
]


def parse_hms8(s: str) -> float:
    h, m, sec = s.split(":")
    return hms8(int(h), int(m), float(sec))


# HA01 bearing candidates (arrival time at HA01, bearing, 1-sigma-ish bearing uncertainty,
# timing uncertainty of the published pick in s)
HA01_CANDIDATES = {
    "Kadri306": dict(t=parse_hms8("00:54:30"), az=306.18, daz=0.4, dt=5.0,
                     ref="Kadri 2024 Table 1 (major signal, 00:54:30, 306.18 deg)"),
    "Stead247": dict(t=parse_hms8("00:52:02"), az=246.9, daz=2.0, dt=8.0,
                     ref="Stead 2014 LA-UR-14-24972 (weak arrival 3114-3130 s, DOA 246.9 deg)"),
    "Kadri268": dict(t=parse_hms8("00:39:02"), az=268.24, daz=0.4, dt=5.0,
                     ref="Kadri 2024 Table 1 (faint, dt=0)"),
    "Curtin301": dict(t=parse_hms8("01:34:40"), az=301.6, daz=0.75, dt=10.0,
                      ref="ATSB 2017 App. H/I; Kadri 2024 (301.4+/-0.4)"),
}

# Located candidate sources (lat, lon, origin time or None)
SOURCES = {
    "Java_Anderson": dict(lat=-8.36, lon=107.92, t0=hms8(1, 15, 18),
                          ref="Anderson 370location 2018; Iannello 2026"),
    "Carlsberg_Curtin": dict(lat=2.11, lon=69.31, t0=None,
                             ref="Curtin 2014 relocation (Carlsberg Ridge), via ATSB/Nature blog"),
    "Curtin_June2014": dict(lat=-5.93, lon=77.22, t0=None, ref="Curtin June 2014 estimate"),
    "Kadri_ref13": dict(lat=-23.662, lon=96.676, t0=None,
                        ref="Kadri 2024 refs 3/13: 1900+/-200 km from H01W, source 01:11-01:16"),
}

# Catalogued earthquakes that night (USGS / ISC-IDC), used for calibration
CAL_EVENTS = {
    "Java_M4.1": dict(lat=-9.6744, lon=108.4193, depth_km=34.0, t0=geo.hms(23, 52, 18.6), mag=4.1),
    "IAR_M4.5": dict(lat=-49.0178, lon=123.3764, depth_km=10.0, t0=geo.hms(20, 36, 6.0), mag=4.5),
    "MauritiusReunion_mb3.7": dict(lat=-20.3681, lon=66.6171, depth_km=10.0,
                                   t0=geo.hms(23, 7, 54.0), mag=3.7),
}


# --------------------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------------------
def dist_az(lat1, lon1, lat2, lon2):
    """WGS84 geodesic distance (km) and forward azimuth (deg) from point 1 to point 2."""
    az, _, d = GEOD.inv(np.broadcast_to(lon1, np.shape(lat2)) if np.ndim(lat2) else lon1,
                        np.broadcast_to(lat1, np.shape(lat2)) if np.ndim(lat2) else lat1,
                        lon2, lat2)
    return np.asarray(d) / 1000.0, np.mod(np.asarray(az), 360.0)


def rdist_az(rcv: str, lat, lon):
    r = RECEIVERS[rcv]
    return dist_az(r["lat"], r["lon"], lat, lon)


def forward(lat, lon, az, dist_km):
    """Geodesic forward problem; broadcasts scalar/array inputs."""
    lat, lon, az, d = np.broadcast_arrays(np.asarray(lat, float), np.asarray(lon, float),
                                          np.asarray(az, float), np.asarray(dist_km, float))
    if lat.ndim == 0:
        lo, la, _ = GEOD.fwd(float(lon), float(lat), float(az), float(d) * 1000.0)
        return la, lo
    lo, la, _ = GEOD.fwd(lon.ravel(), lat.ravel(), az.ravel(), d.ravel() * 1000.0)
    return np.reshape(la, lat.shape), np.reshape(lo, lat.shape)


def tt_sofar(dist_km, c=C_SOFAR):
    """T-phase travel time (s) for a pure water path."""
    return np.asarray(dist_km) / c


def arc7_points(lat_min=-42.0, lat_max=-20.0, step=0.5, h_m=0.0):
    lats = np.round(np.arange(lat_max, lat_min - 1e-9, -step), 4)
    lons = np.array([geo.arc_lon_for_lat(la, geo.ARC7_BTO_US, geo.ARC7_TIME, h_m) for la in lats])
    ok = np.isfinite(lons)
    return lats[ok], lons[ok]


_ARC_R = None


def _arc_resid(lat, lon, h_m=0.0):
    global _ARC_R
    if _ARC_R is None:
        _ARC_R = geo.sat_to_aes_range_km(geo.ARC7_BTO_US, geo.ARC7_TIME)
    p = geo.llh_to_ecef(lat, lon, h_m)
    return np.linalg.norm(p - geo.sat_pos(geo.ARC7_TIME)) - _ARC_R


def arc_crossing(rcv: str, az: float, rmax=6000.0, h_m=0.0):
    """First crossing of the 7th arc (sea level) along azimuth az from receiver.
    Returns (range_km, lat, lon) or (nan, nan, nan)."""
    r0 = RECEIVERS[rcv]
    rs = np.arange(50.0, rmax, 10.0)
    la, lo = forward(r0["lat"], r0["lon"], np.full(rs.shape, az), rs)
    f = np.array([_arc_resid(a, b, h_m) for a, b in zip(la, lo)])
    idx = np.where(np.sign(f[:-1]) != np.sign(f[1:]))[0]
    if idx.size == 0:
        return np.nan, np.nan, np.nan
    i = idx[0]

    def g(r):
        a, b = forward(r0["lat"], r0["lon"], az, r)
        return _arc_resid(a, b, h_m)

    r = brentq(g, rs[i], rs[i + 1], xtol=1e-3)
    a, b = forward(r0["lat"], r0["lon"], az, r)
    return r, float(a), float(b)


def ray_points(rcv: str, az: float, ranges_km):
    r0 = RECEIVERS[rcv]
    return forward(r0["lat"], r0["lon"], np.full(np.shape(ranges_km), az), ranges_km)


# --------------------------------------------------------------------------------------
# Bathymetry along great-circle paths
# --------------------------------------------------------------------------------------
_BATHY = None


def bathy():
    global _BATHY
    if _BATHY is None:
        import xarray as xr
        ds = xr.open_dataset(BATHY, engine="h5netcdf")
        _BATHY = (ds.lat.values, ds.lon.values, ds.z.values)
    return _BATHY


def gc_path(lat1, lon1, lat2, lon2, step_km=5.0):
    d, _ = dist_az(lat1, lon1, lat2, lon2)
    n = max(int(np.ceil(float(d) / step_km)), 2)
    pts = GEOD.npts(lon1, lat1, lon2, lat2, n - 1)
    lo = np.r_[lon1, [p[0] for p in pts], lon2]
    la = np.r_[lat1, [p[1] for p in pts], lat2]
    return la, lo, np.linspace(0, float(d), la.size)


def depth_at(lat, lon):
    la, lo, z = bathy()
    i = np.clip(np.round((np.asarray(lat) - la[0]) / (la[1] - la[0])).astype(int), 0, la.size - 1)
    j = np.clip(np.round((np.asarray(lon) - lo[0]) / (lo[1] - lo[0])).astype(int), 0, lo.size - 1)
    return z[i, j]


def path_profile(lat1, lon1, lat2, lon2, step_km=5.0):
    la, lo, s = gc_path(lat1, lon1, lat2, lon2, step_km)
    return s, la, lo, depth_at(la, lo)


def blockage_summary(src_lat, src_lon, rcv: str, exclude_src_km=30.0, exclude_rcv_km=60.0,
                     axis_m=1000.0):
    """Qualitative SOFAR blockage along the geodesic source->receiver.
    Excludes the near-source and near-receiver ends (receiver slope coupling is expected).
    Returns dict: min elevation (m, +up), its location, km of path shallower than
    axis_m, 500 m, and land; and the shallowest point's distance from the source."""
    r = RECEIVERS[rcv]
    s, la, lo, z = path_profile(src_lat, src_lon, r["lat"], r["lon"])
    m = (s >= exclude_src_km) & (s <= s[-1] - exclude_rcv_km)
    if not m.any():
        m = np.ones_like(s, bool)
    zz = z[m]
    k = int(np.argmax(zz))
    ds = np.gradient(s)[m]
    return dict(dist_km=float(s[-1]), max_elev_m=float(zz[k]), at_lat=float(la[m][k]),
                at_lon=float(lo[m][k]), at_km=float(s[m][k]),
                km_above_axis=float(ds[zz > -axis_m].sum()),
                km_above_500=float(ds[zz > -500].sum()), km_land=float(ds[zz > 0].sum()))


# --------------------------------------------------------------------------------------
# IMOS .DAT reader (port of NL_load_logger_data_new.m)
# --------------------------------------------------------------------------------------
@dataclass
class DatRecord:
    path: Path
    header: list[str]
    footer: list[str]
    fs: float
    duration_s: float
    n_channels: int
    t0: float               # project time of first sample (UTC), incl. fraction
    t_final: float          # 'Finalised' time from footer
    volts: np.ndarray       # (n,) channel 1, mean removed, volts at ADC
    overload: bool
    n_extra: int            # samples present after the nominal duration (ignored by default)
    meta: dict = field(default_factory=dict)

    @property
    def times(self):
        return self.t0 + np.arange(self.volts.size) / self.fs


_FOOT_RE = re.compile(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})\s*-\s*(\d+)")


def _footer_time(line: str) -> float:
    m = _FOOT_RE.search(line)
    if not m:
        return np.nan
    d = dt.datetime.strptime(m.group(1), "%Y/%m/%d %H:%M:%S")
    return t_of(d) + int(m.group(2)) / 65536.0


def read_dat(path, full: bool = False) -> DatRecord:
    """Read a CMST noise-logger .DAT file.

    Faithful to NL_load_logger_data_new.m:
      * 5 ASCII header lines (LF-terminated in these files; the MATLAB code's
        textscan + fseek(+1) lands on the first data byte, i.e. right after line 5);
      * sample rate from 'Sample Rate NNNNN Duration DDDDDDDDDD'; channels enabled from
        characters 13 and 18 of the two 'Filter' lines; FSample /= n_active_channels;
      * NumSamples = ceil(Duration * FSample) big-endian uint16 samples per channel,
        interleaved as MATLAB fread(fid,[N, nch],'uint16') i.e. column-major = channel blocks
        (only single-channel files are used here; we assert nch == 1);
      * volts = counts * 5/65536 - mean(counts * 5/65536); overload if max(counts) > 6e4;
      * UTC start = 'First Data-YYYY/MM/DD HH:MM:SS - FFFFF' with FFFFF in 1/65536 s.
    full=True additionally returns the ~7 s of samples the logger writes after the nominal
    duration (present between the data block and the 'Record Marker' footer).
    """
    path = Path(path)
    b = path.read_bytes()
    pos = 0
    header = []
    for _ in range(5):
        e = b.index(b"\n", pos)
        header.append(b[pos:e].decode("ascii", "replace").rstrip("\r"))
        pos = e + 1
    rate_line = header[2]
    fs = float(rate_line[12:rate_line.index("Duration")])
    dur = float(rate_line[rate_line.index("Duration") + 9:])
    ch = [int(header[3][12]), int(header[3][17]), int(header[4][12]), int(header[4][17])]
    nch = sum(ch)
    if nch != 1:
        raise NotImplementedError(f"{path}: {nch} active channels")
    fs = fs / nch
    nsamp = int(np.ceil(dur * fs))
    fm = b.rfind(b"Record Marker")
    if fm < 0:
        raise ValueError(f"{path}: no Record Marker footer")
    footer = [ln for ln in b[fm:].decode("ascii", "replace").replace("\r", "").split("\n") if ln]
    avail = (fm - 1 - pos) // 2  # data end at the LF preceding 'Record Marker'
    if avail < nsamp:
        raise ValueError(f"{path}: only {avail} samples, expected {nsamp}")
    n = avail if full else nsamp
    counts = np.frombuffer(b, dtype=">u2", count=n, offset=pos).astype(np.float64)
    overload = bool(counts[:nsamp].max() > 6e4)
    v = counts * (5.0 / 65536.0)
    v -= v[:nsamp].mean()
    t0 = _footer_time(footer[1])
    tf = _footer_time(footer[2]) if len(footer) > 2 else np.nan
    meta = dict(schedule=header[1], filters=(header[3], header[4]), validity=footer[3:4])
    return DatRecord(path, header, footer, fs, dur, nch, t0, tf, v, overload, avail - nsamp, meta)


# --------------------------------------------------------------------------------------
# Calibration
# --------------------------------------------------------------------------------------
def load_calibration(site: str):
    dep = RECEIVERS[site]["dep"]
    c = np.loadtxt(RAW / site / dep / "extras" / f"t{dep}_calibration.csv", delimiter=",")
    return c[:, 0], c[:, 1]  # Hz, dB re V/uPa (system response incl. preamp)


def to_pressure(volts: np.ndarray, fs: float, site: str, fmin: float = 3.0) -> np.ndarray:
    """Convert ADC volts to sound pressure in uPa by dividing the spectrum by the system
    response 10^(cal_dB/20) (V/uPa), linearly interpolated from the 1-Hz calibration table.
    Frequencies below fmin are zeroed (the response is ~-170 dB there and the analog
    high-pass at 8 Hz makes them unreliable)."""
    f_cal, db = load_calibration(site)
    n = volts.size
    nfft = int(2 ** np.ceil(np.log2(n)))
    X = np.fft.rfft(volts, nfft)
    f = np.fft.rfftfreq(nfft, 1 / fs)
    g = 10 ** (np.interp(f, f_cal, db) / 20.0)
    X = X / g
    X[f < fmin] = 0.0
    return np.fft.irfft(X, nfft)[:n]


def read_pressure(path, site: str, fs_out: float = 500.0, full: bool = False):
    """Read a .DAT file, decimate to fs_out (polyphase FIR, flat to ~0.8*Nyquist) and
    calibrate to uPa. Returns (t0, fs_out, p_uPa, record)."""
    rec = read_dat(path, full=full)
    q = int(round(rec.fs / fs_out))
    x = signal.resample_poly(rec.volts, 1, q)
    p = to_pressure(x, rec.fs / q, site)
    return rec.t0, rec.fs / q, p, rec


# --------------------------------------------------------------------------------------
# File index
# --------------------------------------------------------------------------------------
def list_files(site: str, t_start: float | None = None, t_end: float | None = None):
    """Local .DAT files for a site, sorted, with nominal start (hex name + 15 s)."""
    dep = RECEIVERS[site]["dep"]
    out = []
    for p in sorted((RAW / site / dep).glob("*/raw/*.DAT")):
        tn = t_of(dt.datetime.fromtimestamp(int(p.stem, 16), dt.timezone.utc).replace(tzinfo=None)) + 15.0
        if (t_start is None or tn + 310 >= t_start) and (t_end is None or tn <= t_end):
            out.append((tn, p))
    return out


def file_window(path, full: bool = False):
    """(t_first_sample, t_last_sample) from header/footer only (no data read)."""
    path = Path(path)
    with open(path, "rb") as f:
        head = f.read(400)
        f.seek(-400, 2)
        tail = f.read()
    lines = head.split(b"\n")[:5]
    rate = lines[2].decode()
    fs = float(rate[12:rate.index("Duration")])
    dur = float(rate[rate.index("Duration") + 9:])
    k = tail.rfind(b"Record Marker")
    foot = tail[k:].decode("ascii", "replace").split("\n")
    t0 = _footer_time(foot[1])
    if full:
        size = path.stat().st_size
        hdr = sum(len(x) + 1 for x in lines)
        n = (size - (len(tail) - k) - 1 - hdr) // 2
        return t0, t0 + (n - 1) / fs
    return t0, t0 + (np.ceil(dur * fs) - 1) / fs


def recording_windows(site: str, t_start: float, t_end: float, full: bool = False):
    """Exact recording windows of locally available files overlapping [t_start, t_end]."""
    out = []
    for tn, p in list_files(site, t_start - 400, t_end + 400):
        a, b = file_window(p, full)
        if b >= t_start and a <= t_end:
            out.append((a, b, p))
    return out


def deployment_windows(site: str):
    """All recording windows of the deployment from t<dep>_start_times.mat (project time
    of start, file name). Data only (scipy.io.loadmat)."""
    import scipy.io as sio
    dep = RECEIVERS[site]["dep"]
    m = sio.loadmat(RAW / site / dep / f"t{dep}_start_times.mat")["Start_times"][0, 0]
    dn = m["time"].ravel()
    names = [x[0][0] for x in m["file_name"]]
    t = (dn - 735665.0) * 86400.0  # datenum 735665 = 2014-03-07 00:00
    return t, names


# --------------------------------------------------------------------------------------
# Signal processing
# --------------------------------------------------------------------------------------
BANDS = {"5-10": (5, 10), "8-16": (8, 16), "10-20": (10, 20), "16-32": (16, 32),
         "20-40": (20, 40), "40-80": (40, 80), "5-100": (5, 100)}


def bandpass(x, fs, f1, f2, order=4):
    sos = signal.butter(order, [f1, f2], btype="band", fs=fs, output="sos")
    return signal.sosfiltfilt(sos, x)


def band_level(x, fs, f1, f2, win_s=2.0, step_s=0.5):
    """Band RMS level in dB re 1 uPa over sliding windows. Returns (t_rel, L)."""
    y = bandpass(x, fs, f1, f2) ** 2
    w = int(win_s * fs)
    st = int(step_s * fs)
    c = np.r_[0, np.cumsum(y)]
    idx = np.arange(0, y.size - w + 1, st)
    ms = (c[idx + w] - c[idx]) / w
    return (idx + w / 2) / fs, 10 * np.log10(np.maximum(ms, 1e-30))


def spectrogram_db(x, fs, nperseg=None, overlap=0.75, fmax=125.0):
    nperseg = nperseg or int(fs)  # 1 s
    f, t, S = signal.spectrogram(x, fs, window="hann", nperseg=nperseg,
                                 noverlap=int(nperseg * overlap), scaling="density", mode="psd")
    k = f <= fmax
    return f[k], t, 10 * np.log10(np.maximum(S[k], 1e-30))  # dB re 1 uPa^2/Hz


def excess_segments(t, L, thr_db=6.0, min_dur=2.0, bg_win_s=60.0, step_s=0.5, merge_s=2.0):
    """Detect segments where band level exceeds a running-median background by thr_db.
    Returns list of dicts (t_on, t_off, dur, t_peak, peak_db) with times relative to t."""
    k = max(int(bg_win_s / step_s) | 1, 3)
    bg = _running_median(L, k)
    E = L - bg
    on = E > thr_db
    segs = []
    i = 0
    n = on.size
    while i < n:
        if on[i]:
            j = i
            while j + 1 < n and on[j + 1]:
                j += 1
            segs.append([i, j])
            i = j + 1
        else:
            i += 1
    merged = []
    for s in segs:
        if merged and (t[s[0]] - t[merged[-1][1]]) <= merge_s:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    out = []
    for i, j in merged:
        dur = t[j] - t[i] + step_s
        if dur >= min_dur:
            kk = i + int(np.argmax(E[i:j + 1]))
            out.append(dict(t_on=float(t[i]), t_off=float(t[j]), dur=float(dur),
                            t_peak=float(t[kk]), peak_db=float(E[kk])))
    return out, E


def _running_median(x, k):
    from scipy.ndimage import median_filter
    return median_filter(x, size=k, mode="nearest")


def sta_lta(x, fs, f1, f2, sta_s=2.0, lta_s=30.0, decim_to=50.0):
    """Classic STA/LTA (obspy) on the band-passed signal, on a decimated envelope grid."""
    from obspy.signal.trigger import classic_sta_lta
    y = bandpass(x, fs, f1, f2)
    q = max(int(fs // decim_to), 1)
    e = signal.resample_poly(y ** 2, 1, q) if q > 1 else y ** 2
    e = np.sqrt(np.maximum(e, 0))
    fs2 = fs / q
    r = classic_sta_lta(e, int(sta_s * fs2), int(lta_s * fs2))
    return np.arange(r.size) / fs2, r


# --------------------------------------------------------------------------------------
# Per-file features and window statistics (used by detection, calibration and tests)
# --------------------------------------------------------------------------------------
DET_BANDS = ("5-10", "8-16", "10-20", "16-32", "20-40")
LF_BANDS = ("5-10", "8-16", "10-20")   # T-phase band; avoids the 20-40 Hz whale-song bands
ALL_BANDS = DET_BANDS + ("40-80", "5-100")
CACHE = ROOT / "data" / "derived" / "acoustic_cache"


def file_features(path, site: str, bands=ALL_BANDS, fs_out=500.0, use_cache=True):
    """Band levels (dB re 1 uPa, 2-s RMS, 0.5-s step) for one file, with absolute times.
    Cached in data/derived/acoustic_cache/<site>/<HEX>.npz."""
    path = Path(path)
    cf = CACHE / site / f"{path.stem}.npz"
    if use_cache and cf.exists():
        z = np.load(cf, allow_pickle=False)
        if all(f"L_{b}" in z for b in bands):
            return {k: z[k] for k in z.files}
    t0, fs, p, rec = read_pressure(path, site, fs_out, full=True)
    out = dict(t0=np.float64(t0), fs=np.float64(fs), n=np.int64(p.size),
               overload=np.bool_(rec.overload), n_extra=np.int64(rec.n_extra))
    for b in bands:
        f1, f2 = BANDS[b]
        tr, L = band_level(p, fs, f1, f2, 2.0, 0.5)
        out["t"] = t0 + tr
        out[f"L_{b}"] = L.astype(np.float32)
    if use_cache:
        import os
        import tempfile
        cf.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=cf.parent, suffix=".npz")
        os.close(fd)
        np.savez_compressed(tmp, **out)
        os.replace(tmp, cf)  # atomic: concurrent writers cannot leave a corrupt cache file
    return out


def smooth_db(L, n):
    """Moving average of band level in the power domain over n samples, returned in dB."""
    if n <= 1:
        return L
    pw = 10 ** (np.asarray(L, float) / 10)
    k = np.ones(n) / n
    return 10 * np.log10(np.convolve(pw, k, mode="same"))


def excess_series(feat, band, smooth_s=0.0, ref="median"):
    """Band level minus the file's median level (dB) on the 0.5-s grid.
    smooth_s > 0: power-domain moving average over smooth_s seconds first.
    smooth_s < 0: running MEDIAN over |smooth_s| seconds first - robust to impulsive
    transients (knocks, clicks) shorter than ~|smooth_s|/2, keeps arrivals >~ |smooth_s|."""
    L = np.asarray(feat[f"L_{band}"], float)
    if smooth_s > 0:
        L = smooth_db(L, int(round(smooth_s / 0.5)))
    elif smooth_s < 0:
        n = int(round(-smooth_s / 0.5)) | 1
        L = _running_median(L, n)
    return L - np.median(L)


def window_stat(feat, t1, t2, bands=DET_BANDS, smooth_s=0.0):
    """max over bands of max excess (dB over file median) within [t1, t2] (absolute times).
    Returns (stat, band, t_at_max) or (nan, '', nan) if the window is not covered."""
    t = feat["t"]
    m = (t >= t1) & (t <= t2)
    if not m.any():
        return np.nan, "", np.nan
    best = (-np.inf, "", np.nan)
    for b in bands:
        E = excess_series(feat, b, smooth_s)
        k = np.argmax(np.where(m, E, -np.inf))
        if E[k] > best[0]:
            best = (float(E[k]), b, float(t[k]))
    return best


def null_window_stats(feats, width_s, bands=DET_BANDS, smooth_s=0.0, step_s=5.0, edge_s=5.0):
    """Null distribution of window_stat for windows of width width_s slid across files.
    Edges (edge_s) are excluded to match filtering edge effects."""
    out = []
    for f in feats:
        t = f["t"]
        Es = np.max([excess_series(f, b, smooth_s) for b in bands], axis=0)
        a = t[0] + edge_s
        while a + width_s <= t[-1] - edge_s:
            m = (t >= a) & (t <= a + width_s)
            out.append(float(Es[m].max()))
            a += step_s
    return np.array(out)


def pvalue(stat, null):
    null = np.asarray(null)
    null = null[np.isfinite(null)]
    if not np.isfinite(stat) or null.size == 0:
        return np.nan
    return (1 + np.sum(null >= stat)) / (1 + null.size)


# --------------------------------------------------------------------------------------
# Nights
# --------------------------------------------------------------------------------------
MAIN_DAY = dt.date(2014, 3, 8)
CONTROL_DAYS = [dt.date(2014, 3, d) for d in (1, 3, 5, 6, 9, 10, 11, 13)]


def night_interval(day: dt.date):
    """Night D: D-1 21:40 -> D 03:05 UTC (project time), matching the download script."""
    t = t_of(dt.datetime.combine(day, dt.time()))
    return t - 2 * 3600 - 20 * 60, t + 3 * 3600 + 5 * 60


def night_files(site: str, day: dt.date):
    a, b = night_interval(day)
    return [p for tn, p in list_files(site, a - 60, b + 60) if a <= tn - 15.0 <= b]


def night_offset(day: dt.date) -> float:
    """Seconds to add to a control-night time to map it onto the main night's clock."""
    return t_of(dt.datetime.combine(MAIN_DAY, dt.time())) - t_of(dt.datetime.combine(day, dt.time()))


# --------------------------------------------------------------------------------------
# On-demand fetch of single raw files (anonymous HTTPS, AODN S3)
# --------------------------------------------------------------------------------------
S3_BASE = "https://imos-data.s3-ap-southeast-2.amazonaws.com/IMOS/ANMN/Acoustic"


def fetch_raw(site: str, name: str, tag: str = "on-demand"):
    """Download <name>.DAT for a site (tries the UTC date folder of the hex time and the
    neighbouring days) into data/raw/imos_acoustic and append it to manifest.csv."""
    import hashlib
    import urllib.request
    dep = RECEIVERS[site]["dep"]
    tn = dt.datetime.fromtimestamp(int(name, 16), dt.timezone.utc).replace(tzinfo=None)
    days = [tn.date(), (tn + dt.timedelta(days=1)).date(), (tn - dt.timedelta(days=1)).date()]
    for day in days:
        dest = RAW / site / dep / f"{day:%Y%m%d}" / "raw" / f"{name}.DAT"
        if dest.exists() and dest.stat().st_size > 3_000_000:
            return dest
    for day in days:
        dest = RAW / site / dep / f"{day:%Y%m%d}" / "raw" / f"{name}.DAT"
        try:
            with urllib.request.urlopen(f"{S3_BASE}/{site}/{dep}/{day:%Y%m%d}/raw/{name}.DAT",
                                        timeout=120) as r:
                data = r.read()
        except Exception:  # noqa: BLE001
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(dest)
        key = "IMOS/ANMN/Acoustic/" + str(dest.relative_to(RAW))
        with open(RAW / "manifest.csv", "a") as fh:
            fh.write(f"{site},{dep},{tag},{key},{len(data)},{hashlib.sha256(data).hexdigest()}\n")
        return dest
    return None
