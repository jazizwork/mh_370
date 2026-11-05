"""Fit pixel <- affine(projected(lon,lat)) to a graticule dash mask (ICP-like robust least squares).
usage: georef_fit.py config.json out.json
config: image, thr, blur, max_dash, exclude[[x0,y0,x1,y1]], crs (e.g. EPSG:32746 or 'eqc' or 'merc' ...),
        lon_step, lat_step, init_cps [[lon,lat,px,py],...] (>=3), label_lons / label_lats (optional, unused)
Outputs affine params, residual stats, and control points (graticule intersections) with pixel coords.
"""
import sys, json, numpy as np, cv2
from pyproj import CRS, Transformer
from scipy.optimize import least_squares
cfg = json.load(open(sys.argv[1]))
im = cv2.imread(cfg['image'])
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.int16)
bg = cv2.medianBlur(g.astype(np.uint8), cfg.get('blur', 9)).astype(np.int16)
mask = (bg - g) > cfg.get('thr', 30)
for x0, y0, x1, y1 in cfg.get('exclude', []):
    mask[y0:y1, x0:x1] = False
if cfg.get('dash_only', True):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    big = np.maximum(st[:, 2], st[:, 3]) > cfg.get('max_dash', 14); big[0] = False
    mask = mask & ~big[lab]
ys, xs = np.nonzero(mask)
P = np.c_[xs, ys].astype(float)

def make_proj(name):
    if name.startswith('EPSG') or name.startswith('+'):
        crs = CRS.from_user_input(name)
    elif name == 'eqc':
        crs = CRS.from_proj4('+proj=eqc +lon_0=0 +lat_ts=0 +datum=WGS84')
    elif name.startswith('eqc_ts'):
        crs = CRS.from_proj4(f"+proj=eqc +lat_ts={name.split('=')[1]} +datum=WGS84")
    elif name == 'merc':
        crs = CRS.from_proj4('+proj=merc +datum=WGS84')
    else:
        crs = CRS.from_proj4(name)
    fwd = Transformer.from_crs('EPSG:4326', crs, always_xy=True)
    inv = Transformer.from_crs(crs, 'EPSG:4326', always_xy=True)
    return fwd, inv
fwd, inv = make_proj(cfg['crs'])
cp0 = np.array(cfg['init_cps'], float)
E0, N0 = fwd.transform(cp0[:, 0], cp0[:, 1])
# normalise projected coords
Ec, Nc, Sc = np.mean(E0), np.mean(N0), 1e5
def proj_n(lon, lat):
    E, N = fwd.transform(lon, lat); return (np.asarray(E) - Ec) / Sc, (np.asarray(N) - Nc) / Sc
def unproj_n(e, n):
    return inv.transform(e * Sc + Ec, n * Sc + Nc)
# initial affine: [px,py] = M @ [e,n] + t
e0, n0 = proj_n(cp0[:, 0], cp0[:, 1])
Aeq = np.c_[e0, n0, np.ones_like(e0)]
sx = np.linalg.lstsq(Aeq, cp0[:, 2], rcond=None)[0]; sy = np.linalg.lstsq(Aeq, cp0[:, 3], rcond=None)[0]
params = np.r_[sx, sy]
lstep, bstep = cfg.get('lon_step', 2.0), cfg.get('lat_step', 1.0)
lon_off, lat_off = cfg.get('lon_offset', 0.0), cfg.get('lat_offset', 0.0)

def px_of(params, lon, lat):
    e, n = proj_n(lon, lat)
    return params[0] * e + params[1] * n + params[2], params[3] * e + params[4] * n + params[5]

def residuals(params, cutoff):
    M = np.array([[params[0], params[1]], [params[3], params[4]]]); t = np.array([params[2], params[5]])
    en = np.linalg.solve(M, (P - t).T)
    lon, lat = unproj_n(en[0], en[1])
    lon = np.asarray(lon); lat = np.asarray(lat)
    # nearest meridian / parallel
    Lm = np.round((lon - lon_off) / lstep) * lstep + lon_off
    Bp = np.round((lat - lat_off) / bstep) * bstep + lat_off
    xm, ym = px_of(params, Lm, lat)   # point on nearest meridian at same lat
    xp, yp = px_of(params, lon, Bp)   # point on nearest parallel at same lon
    dm = np.hypot(P[:, 0] - xm, P[:, 1] - ym); dp = np.hypot(P[:, 0] - xp, P[:, 1] - yp)
    # signed residual components toward the nearer line
    use_m = dm < dp
    rx = np.where(use_m, P[:, 0] - xm, P[:, 0] - xp); ry = np.where(use_m, P[:, 1] - ym, P[:, 1] - yp)
    d = np.minimum(dm, dp)
    w = np.where(d < cutoff, 1.0, 0.0)
    return np.r_[rx * w, ry * w], d

for cutoff in cfg.get('cutoffs', [12, 6, 3, 2]):
    res = least_squares(lambda p: residuals(p, cutoff)[0], params, method='lm')
    params = res.x
    _, d = residuals(params, cutoff)
    inl = d < cutoff
    print(f"cutoff {cutoff}: inliers {inl.sum()}/{len(d)} rms {np.sqrt(np.mean(d[inl]**2)):.3f} px")
_, d = residuals(params, 2)
inl = d < 2
# control points: intersections in image
lons = np.arange(cfg['lon_range'][0], cfg['lon_range'][1] + 1e-9, lstep)
lats = np.arange(cfg['lat_range'][0], cfg['lat_range'][1] + 1e-9, bstep)
H, W = mask.shape
cps = []
for L in lons:
    for B in lats:
        x, y = px_of(params, L, B)
        if 0 <= x < W and 0 <= y < H:
            cps.append([float(L), float(B), float(x), float(y)])
# pixel scale (km/px) at centre
cx, cy = W / 2, H / 2
M = np.array([[params[0], params[1]], [params[3], params[4]]])
kmpp = Sc / 1000 / np.sqrt(abs(np.linalg.det(M)))
out = dict(image=cfg['image'], crs=cfg['crs'], norm=dict(Ec=Ec, Nc=Nc, Sc=Sc), affine=params.tolist(),
           n_inliers=int(inl.sum()), rms_px=float(np.sqrt(np.mean(d[inl] ** 2))), km_per_px=float(kmpp),
           control_points_lon_lat_px_py=cps)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
print('km/px', kmpp, 'rms_px', out['rms_px'], 'rms_km', out['rms_px'] * kmpp)
# overlay
dbg = im.copy()
for L in np.arange(cfg['lon_range'][0] - 4, cfg['lon_range'][1] + 4.01, lstep):
    bb = np.linspace(cfg['lat_range'][0] - 3, cfg['lat_range'][1] + 3, 400)
    x, y = px_of(params, np.full_like(bb, L), bb)
    pts = np.c_[x, y].round().astype(np.int32); cv2.polylines(dbg, [pts], False, (0, 0, 255), 1)
for B in np.arange(cfg['lat_range'][0] - 3, cfg['lat_range'][1] + 3.01, bstep):
    ll = np.linspace(cfg['lon_range'][0] - 4, cfg['lon_range'][1] + 4, 400)
    x, y = px_of(params, ll, np.full_like(ll, B))
    pts = np.c_[x, y].round().astype(np.int32); cv2.polylines(dbg, [pts], False, (255, 0, 0), 1)
cv2.imwrite(sys.argv[2].replace('.json', '_overlay.png'), dbg)
