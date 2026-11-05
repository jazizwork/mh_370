"""Georeference a progress-map image from graticule crosses, extract coverage polygons.
usage: oigeo.py config.json
config keys:
  image, crs, crosses: [[lon,lat,x_approx,y_approx],...], cross_arm (px, default 3), search (px, default 6)
  edge_ticks (optional): [["lon"|"lat", value, x, y], ...]  label/tick constraints (meridian/parallel passes through x,y)
  hsv: [hmin,hmax,smin,smax,vmin], close (px), open (px), exclude_polys: [[[x,y],...],...], include_polys (optional)
  min_area_px, eps_px, out (json path)
"""
import sys, json, numpy as np, cv2
from pyproj import CRS, Transformer
cfg = json.load(open(sys.argv[1]))
im = cv2.imread(cfg['image']); H, W = im.shape[:2]
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
bg = cv2.medianBlur(g.astype(np.uint8), 9).astype(float)
dark = np.clip(bg - g, 0, None)
L = cfg.get('cross_arm', 3)
K = np.zeros((2 * L + 1, 2 * L + 1)); K[L, :] = 1; K[:, L] = 1
resp = cv2.filter2D(dark, -1, K / K.sum(), borderType=cv2.BORDER_REPLICATE)
crs = CRS.from_user_input(cfg['crs'])
fwd = Transformer.from_crs('EPSG:4326', crs, always_xy=True); inv = Transformer.from_crs(crs, 'EPSG:4326', always_xy=True)
cps = []
sr = cfg.get('search', 6)
for lon, lat, xa, ya in cfg['crosses']:
    x0, y0 = int(round(xa)), int(round(ya))
    win = resp[max(0, y0 - sr):y0 + sr + 1, max(0, x0 - sr):x0 + sr + 1]
    iy, ix = np.unravel_index(np.argmax(win), win.shape)
    cy, cx = iy + max(0, y0 - sr), ix + max(0, x0 - sr)
    # subpixel parabolic
    def sub(a, b, c): d = a - 2 * b + c; return 0.0 if d == 0 else 0.5 * (a - c) / d
    dx = sub(resp[cy, cx - 1], resp[cy, cx], resp[cy, cx + 1]) if 0 < cx < W - 1 else 0
    dy = sub(resp[cy - 1, cx], resp[cy, cx], resp[cy + 1, cx]) if 0 < cy < H - 1 else 0
    cps.append((lon, lat, cx + dx, cy + dy, float(resp[cy, cx])))
cps = np.array(cps)
E, N = fwd.transform(cps[:, 0], cps[:, 1]); E = np.asarray(E); N = np.asarray(N)
Ec, Nc = E.mean(), N.mean(); S = 1e5
A = np.c_[(E - Ec) / S, (N - Nc) / S, np.ones(len(E))]
px = np.linalg.lstsq(A, cps[:, 2], rcond=None)[0]; py = np.linalg.lstsq(A, cps[:, 3], rcond=None)[0]
res = np.c_[A @ px - cps[:, 2], A @ py - cps[:, 3]]
M = np.array([[px[0], px[1]], [py[0], py[1]]]); kmpp = S / 1000 / np.sqrt(abs(np.linalg.det(M)))
print('crosses (lon lat x y resp | resid px):')
for c, r in zip(cps, res): print(f"  {c[0]:7.2f} {c[1]:7.2f} {c[2]:8.2f} {c[3]:8.2f} {c[4]:6.1f} | {r[0]:+.2f} {r[1]:+.2f}")
rms = float(np.sqrt(np.mean(np.sum(res ** 2, axis=1))))
print(f"affine fit: n={len(cps)} rms={rms:.2f} px  scale={kmpp:.3f} km/px  rms={rms*kmpp:.2f} km")
def pix2ll(x, y):
    en = np.linalg.solve(M, np.vstack([np.asarray(x) - px[2], np.asarray(y) - py[2]]))
    lon, lat = inv.transform(en[0] * S + Ec, en[1] * S + Nc); return np.asarray(lon), np.asarray(lat)
def ll2pix(lon, lat):
    e, n = fwd.transform(lon, lat); a = np.c_[(np.asarray(e) - Ec) / S, (np.asarray(n) - Nc) / S, np.ones(np.size(e))]
    return a @ px, a @ py
out = dict(image=cfg['image'], crs=cfg['crs'], crosses=cps[:, :4].tolist(), resid_px=res.tolist(), rms_px=rms, km_per_px=kmpp,
           affine_px=px.tolist(), affine_py=py.tolist(), norm=[Ec, Nc, S])
if 'hsv' in cfg:
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(int)
    hmin, hmax, smin, smax, vmin = cfg['hsv']
    if cfg.get('mode') == 'nonbg':
        # background = blue bathymetry: hue in [bg_hmin,bg_hmax] and saturation >= bg_smin
        bh0, bh1, bs0 = cfg['bg']
        m = (~((hsv[..., 0] >= bh0) & (hsv[..., 0] <= bh1) & (hsv[..., 1] >= bs0))).astype(np.uint8)
    else:
        m = ((hsv[..., 0] >= hmin) & (hsv[..., 0] <= hmax) & (hsv[..., 1] >= smin) & (hsv[..., 1] <= smax) & (hsv[..., 2] >= vmin)).astype(np.uint8)
    for poly in cfg.get('exclude_polys', []):
        cv2.fillPoly(m, [np.array(poly, np.int32)], 0)
    if cfg.get('include_polys'):
        inc = np.zeros_like(m)
        for poly in cfg['include_polys']: cv2.fillPoly(inc, [np.array(poly, np.int32)], 1)
        m &= inc
    for poly in cfg.get('force_polys', []):
        cv2.fillPoly(m, [np.array(poly, np.int32)], 1)
    if cfg.get('close'): m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((cfg['close'], cfg['close']), np.uint8))
    if cfg.get('open'): m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((cfg['open'], cfg['open']), np.uint8))
    if cfg.get('keep_largest'):
        n_, lab_, st_, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        keep = np.zeros(n_, bool); order = np.argsort(-st_[1:, 4]) + 1
        keep[order[:cfg['keep_largest']]] = True; m = keep[lab_].astype(np.uint8)
    cv2.imwrite(cfg['out'].replace('.json', '_mask.png'), m * 255)
    # fill small holes
    cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    polys = []
    vis = im.copy()
    minA = cfg.get('min_area_px', 80); eps = cfg.get('eps_px', 0.8)
    for i, c in enumerate(cnts):
        if hier[0][i][3] != -1: continue  # outer contours only here
        if cv2.contourArea(c) < minA: continue
        ring = cv2.approxPolyDP(c, eps, True)[:, 0, :].astype(float)
        holes = []
        j = hier[0][i][2]
        while j != -1:
            if cv2.contourArea(cnts[j]) >= cfg.get('min_hole_px', 80):
                holes.append(cv2.approxPolyDP(cnts[j], eps, True)[:, 0, :].astype(float))
            j = hier[0][j][0]
        def tolonlat(r):
            lo, la = pix2ll(r[:, 0], r[:, 1]); ll = np.c_[lo, la]; return np.vstack([ll, ll[:1]]).round(5).tolist()
        polys.append(dict(outer=tolonlat(ring), holes=[tolonlat(h) for h in holes], outer_px=ring.tolist(), npx=float(cv2.contourArea(c))))
        cv2.polylines(vis, [ring.astype(np.int32)], True, (0, 0, 255), 1)
        for h in holes: cv2.polylines(vis, [h.astype(np.int32)], True, (255, 0, 255), 1)
    for c in cps: cv2.circle(vis, (int(round(c[2])), int(round(c[3]))), 5, (0, 255, 255), 1)
    cv2.imwrite(cfg['out'].replace('.json', '_overlay.png'), vis)
    out['polygons'] = polys
    # area via EPSG:6933
    from shapely.geometry import Polygon
    from shapely.ops import transform as stx, unary_union
    t6933 = Transformer.from_crs('EPSG:4326', 'EPSG:6933', always_xy=True)
    shp = unary_union([Polygon(p['outer'], p['holes']).buffer(0) for p in polys])
    a = stx(lambda x, y: t6933.transform(x, y), shp).area / 1e6
    out['area_km2_eqarea'] = a
    print('polygons', len(polys), 'vertices', [len(p['outer']) for p in polys], 'area km2', round(a))
json.dump(out, open(cfg['out'], 'w'), indent=1)
