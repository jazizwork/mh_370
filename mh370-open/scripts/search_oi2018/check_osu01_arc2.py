import sys, json, numpy as np, cv2
sys.path.insert(0, 'src')
from mh370 import geo
from pyproj import Transformer
d = json.load(open(sys.argv[1]))
im = cv2.imread(d['image'])
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.int16)
bg = cv2.medianBlur(g.astype(np.uint8), 9).astype(np.int16)
mask = (bg - g) > 15
ys, xs = np.nonzero(mask)
# initial line through (255,928) and (1170,15)
x0, y0, x1, y1 = 255, 928, 1170, 15
def dist(xs, ys, coef): return xs - np.polyval(coef, ys)
coef = np.polyfit([y0, y1], [x0, x1], 1)
for it, tol in enumerate([8, 4, 2, 1.5]):
    sel = np.abs(dist(xs, ys, coef)) < tol
    coef = np.polyfit(ys[sel], xs[sel], 3)
print('n', sel.sum())
Ec, Nc, S = d['norm']['Ec'], d['norm']['Nc'], d['norm']['Sc']; p = d['affine']
M = np.array([[p[0], p[1]], [p[3], p[4]]]); t = np.array([p[2], p[5]])
inv = Transformer.from_crs(d['crs'], 'EPSG:4326', always_xy=True)
arc = geo.arc_polyline(geo.ARC7_BTO_US, geo.ARC7_TIME, 0.0, lats=np.arange(-37, -28, 0.01))
for yy in range(60, 930, 80):
    xx = np.polyval(coef, yy)
    e, n = np.linalg.solve(M, [xx - t[0], yy - t[1]])
    lon, lat = inv.transform(e * S + Ec, n * S + Nc)
    al = np.interp(lat, arc[:, 0], arc[:, 1])
    ew = (lon - al) * 111.32 * np.cos(np.radians(lat))
    # perpendicular distance ~ ew * cos(theta) where theta = arc azimuth from N; compute local slope
    i = np.searchsorted(arc[:, 0], lat); dlat = arc[i + 1, 0] - arc[i - 1, 0]; dlon = arc[i + 1, 1] - arc[i - 1, 1]
    az = np.degrees(np.arctan2(dlon * np.cos(np.radians(lat)), dlat))
    print(f"y={yy} map-arc at lat {lat:.3f} lon {lon:.3f}; geo arc lon {al:.3f}; E-W offset {ew:+.2f} km; perpendicular {ew*np.cos(np.radians(az)):+.2f} km")
