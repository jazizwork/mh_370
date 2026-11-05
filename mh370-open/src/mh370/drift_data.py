"""Data access for workstream B (drift): GDP drifters, land mask, NCEP winds.

All raw data live in data/raw/<source>/ (see SOURCE.md there) and are fetched by
scripts/drift_download.py. Nothing here downloads anything.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
GDP_ZARR = RAW / "gdp6h" / "gdp6h_ragged_may25.zarr"
NE_DIR = RAW / "naturalearth"
NCEP_DIR = RAW / "ncep_r1_daily"
GDP_CACHE = DERIVED / "drift_gdp6h_indian.npz"

# Region kept from the global GDP file (generous margin around the Markov-chain domain).
KEEP_LON = (10.0, 135.0)
KEEP_LAT = (-60.0, 20.0)


# --------------------------------------------------------------------------------------
# GDP 6-hourly drifters
# --------------------------------------------------------------------------------------
def _read_zarr_var(name: str) -> np.ndarray:
    import zarr
    g = zarr.open_group(str(GDP_ZARR), mode="r", zarr_format=2, use_consolidated=False)
    return np.asarray(g[name][:])


def build_gdp_cache(force: bool = False) -> Path:
    """Read the mirrored GDP zarr once and keep only trajectories that ever enter the
    Indian Ocean box; store compact arrays in data/derived/drift_gdp6h_indian.npz."""
    if GDP_CACHE.exists() and not force:
        return GDP_CACHE
    rowsize = _read_zarr_var("rowsize").astype(np.int64)
    ids = _read_zarr_var("id")
    typedeath = _read_zarr_var("typedeath").astype(np.int8)
    drogue_lost = _read_zarr_var("drogue_lost_date").astype(np.float64)
    lat = _read_zarr_var("lat")
    lon = _read_zarr_var("lon")
    lon = np.where(lon > 180, lon - 360, lon)
    time = _read_zarr_var("time")
    drog = _read_zarr_var("drogue_status").astype(np.int8)
    ve = _read_zarr_var("ve").astype(np.float32)
    vn = _read_zarr_var("vn").astype(np.float32)
    traj = np.repeat(np.arange(rowsize.size), rowsize)
    inbox = ((lon >= KEEP_LON[0]) & (lon <= KEEP_LON[1]) & (lat >= KEEP_LAT[0]) & (lat <= KEEP_LAT[1]))
    keep_traj = np.zeros(rowsize.size, bool)
    keep_traj[np.unique(traj[inbox])] = True
    m = keep_traj[traj]
    # renumber trajectories
    old = np.flatnonzero(keep_traj)
    new_index = -np.ones(rowsize.size, np.int64)
    new_index[old] = np.arange(old.size)
    DERIVED.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        GDP_CACHE,
        lat=lat[m].astype(np.float64), lon=lon[m].astype(np.float64), time=time[m],
        drogue=drog[m], ve=ve[m], vn=vn[m], traj=new_index[traj[m]],
        ids=ids[old], typedeath=typedeath[old], drogue_lost=drogue_lost[old],
        rowsize=rowsize[old],
    )
    return GDP_CACHE


@lru_cache(maxsize=1)
def load_gdp() -> dict:
    p = build_gdp_cache()
    with np.load(p) as z:
        return {k: z[k] for k in z.files}


# --------------------------------------------------------------------------------------
# Land mask (Natural Earth 1:10m land + minor islands)
# --------------------------------------------------------------------------------------
@lru_cache(maxsize=1)
def land_geometry(bbox=(5.0, -65.0, 140.0, 25.0)):
    """Union of Natural Earth land + minor-island polygons clipped to bbox (shapely)."""
    import shapefile
    from shapely.geometry import box, shape
    from shapely.ops import unary_union
    from shapely import make_valid
    clip = box(*bbox)
    geoms = []
    for stem in ["ne_10m_land", "ne_10m_minor_islands"]:
        shp = next((NE_DIR / stem).glob("*.shp"))
        r = shapefile.Reader(str(shp))
        for s in r.shapes():
            g = make_valid(shape(s.__geo_interface__))
            if g.intersects(clip):
                geoms.append(g.intersection(clip))
    return unary_union(geoms)


def land_fraction(lat_edges: np.ndarray, lon_edges: np.ndarray, sub: int = 10) -> np.ndarray:
    """Fraction of each (lat, lon) cell covered by land, by sub x sub point sampling."""
    import shapely
    g = land_geometry()
    shapely.prepare(g)
    nlat, nlon = lat_edges.size - 1, lon_edges.size - 1
    frac = np.zeros((nlat, nlon))
    for a in range(nlat):
        la = lat_edges[a] + (np.arange(sub) + 0.5) / sub * (lat_edges[a + 1] - lat_edges[a])
        lo = lon_edges[0] + (np.arange(nlon * sub) + 0.5) / sub * (lon_edges[1] - lon_edges[0])
        LO, LA = np.meshgrid(lo, la)
        inside = shapely.contains_xy(g, LO.ravel(), LA.ravel()).reshape(sub, nlon, sub)
        frac[a] = inside.mean(axis=(0, 2))
    return frac


def dist_to_coast_km(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """Approximate great-circle distance (km) from points to the nearest land boundary
    (planar distance in degrees scaled by local cos(lat); fine for < ~500 km)."""
    import shapely
    g = land_geometry()
    bd = g.boundary
    lat = np.asarray(lat, float)
    lon = np.asarray(lon, float)
    pts = shapely.points(lon, lat)
    # nearest point on boundary, then haversine
    from mh370.geo import haversine_km
    near = shapely.shortest_line(pts, bd)
    coords = shapely.get_coordinates(near).reshape(-1, 2, 2)
    return haversine_km(lat, lon, coords[:, 1, 1], coords[:, 1, 0])


# --------------------------------------------------------------------------------------
# NCEP R1 daily 10 m winds (for the leeway-augmented sensitivity variant)
# --------------------------------------------------------------------------------------
class NcepDailyWind:
    """Daily-mean 10 m wind from NCEP/NCAR R1 on the T62 Gaussian grid, sampled with
    bilinear interpolation in space and nearest day in time."""

    def __init__(self, years):
        import xarray as xr
        self.u, self.v, self.t0 = {}, {}, {}
        lat = lon = None
        for y in years:
            fu = NCEP_DIR / f"uwnd.10m.gauss.{y}.nc"
            fv = NCEP_DIR / f"vwnd.10m.gauss.{y}.nc"
            if not (fu.exists() and fv.exists()):
                continue
            du = xr.open_dataset(fu, engine="h5netcdf")
            dv = xr.open_dataset(fv, engine="h5netcdf")
            self.u[y] = du["uwnd"].values.astype(np.float32)
            self.v[y] = dv["vwnd"].values.astype(np.float32)
            self.t0[y] = np.datetime64(f"{y}-01-01")
            lat, lon = du["lat"].values, du["lon"].values
        self.lat = lat  # descending (90 .. -90)
        self.lon = lon  # 0 .. 358.125

    def __call__(self, t_unix: np.ndarray, lat: np.ndarray, lon: np.ndarray):
        t_unix = np.asarray(t_unix)
        days = (t_unix // 86400).astype(np.int64)
        dates = np.datetime64("1970-01-01") + days.astype("timedelta64[D]")
        years = dates.astype("datetime64[Y]").astype(int) + 1970
        lonp = np.mod(lon, 360.0)
        # bilinear indices
        dlon = self.lon[1] - self.lon[0]
        ix = lonp / dlon
        i0 = np.floor(ix).astype(int) % self.lon.size
        i1 = (i0 + 1) % self.lon.size
        fx = ix - np.floor(ix)
        # Gaussian lats are not uniform: use searchsorted on the ascending array
        la_asc = self.lat[::-1]
        j = np.clip(np.searchsorted(la_asc, lat) - 1, 0, la_asc.size - 2)
        fy = (lat - la_asc[j]) / (la_asc[j + 1] - la_asc[j])
        j0 = self.lat.size - 1 - j        # index into descending array
        j1 = j0 - 1
        U = np.full(lat.shape, np.nan, np.float32)
        V = np.full(lat.shape, np.nan, np.float32)
        for y in np.unique(years):
            if y not in self.u:
                continue
            s = years == y
            d = (dates[s] - self.t0[y]).astype(int)
            d = np.clip(d, 0, self.u[y].shape[0] - 1)
            for arr, out in ((self.u[y], U), (self.v[y], V)):
                a00 = arr[d, j0[s], i0[s]]
                a01 = arr[d, j0[s], i1[s]]
                a10 = arr[d, j1[s], i0[s]]
                a11 = arr[d, j1[s], i1[s]]
                fxs, fys = fx[s], fy[s]
                out[s] = (a00 * (1 - fxs) * (1 - fys) + a01 * fxs * (1 - fys)
                          + a10 * (1 - fxs) * fys + a11 * fxs * fys)
        return U, V


def on_land(lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
    """True where (lat, lon) falls inside a Natural Earth land / minor-island polygon."""
    import shapely
    g = land_geometry()
    shapely.prepare(g)
    return shapely.contains_xy(g, np.asarray(lon, float), np.asarray(lat, float))
