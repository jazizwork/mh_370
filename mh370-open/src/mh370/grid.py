"""Common output grid shared by all workstreams (see PROJECT.md)."""
import numpy as np
import xarray as xr

LAT = np.round(np.arange(-44.0, -16.0 + 1e-9, 0.05), 3)
LON = np.round(np.arange(78.0, 112.0 + 1e-9, 0.05), 3)


def common_grid():
    """Return (lat, lon) 1-D arrays of cell centres."""
    return LAT.copy(), LON.copy()


def empty(name: str, fill=np.nan) -> xr.DataArray:
    return xr.DataArray(np.full((LAT.size, LON.size), fill), coords={"lat": LAT, "lon": LON},
                        dims=("lat", "lon"), name=name)


def cell_area_km2() -> xr.DataArray:
    r = 6371.0088
    d = np.radians(0.05)
    a = (r * d) * (r * d * np.cos(np.radians(LAT)))[:, None] * np.ones(LON.size)[None, :]
    return xr.DataArray(a, coords={"lat": LAT, "lon": LON}, dims=("lat", "lon"), name="area_km2")


def save(ds: xr.Dataset, path: str):
    ds.to_netcdf(path, engine="h5netcdf")
