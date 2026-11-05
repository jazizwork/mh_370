import sys, json, numpy as np, cv2
sys.path.insert(0, 'scripts/search_oi2018')
import arcframe as af
from shapely.geometry import Polygon, LineString
im = cv2.imread(sys.argv[1]).astype(int)[:1080]
B, G, R = im[..., 0], im[..., 1], im[..., 2]
yel = (R > 190) & (G > 190) & (B < 120)
# exclude label boxes (yellow filled rectangles): remove big filled components
n, lab, st, _ = cv2.connectedComponentsWithStats(yel.astype(np.uint8), connectivity=8)
fill = st[:, 4] / np.maximum(st[:, 2] * st[:, 3], 1)
bad = (fill > 0.35) & (st[:, 4] > 200); bad[0] = False
yel &= ~bad[lab]
blue = (B > 150) & (R < 80) & (G > 80) & (G < 170)
lonf = lambda x: 93.2 + (x - 30) / 936.7
latf = lambda y: -33.9 - (y - 60) / 1133.0
for name, m in [('yellow', yel), ('blue(7th arc as drawn)', blue)]:
    ys, xs = np.nonzero(m)
    la, d = af.cross_arc_signed(lonf(xs), latf(ys))
    h, e = np.histogram(d, bins=np.arange(-80, 80, 2))
    print(name, len(xs))
    print('  d-hist peaks (km):', [(round(e[i] + 1), int(h[i])) for i in range(len(h)) if h[i] > 0.02 * len(xs)])
# compare with digitised Site 1 polygon boundary in the same window
g = json.load(open(sys.argv[2]))
poly = Polygon(g['polygons'][0]['outer'])
win = Polygon([(lonf(0), latf(0)), (lonf(1189), latf(0)), (lonf(1189), latf(1080)), (lonf(0), latf(1080))])
bd = poly.boundary.intersection(win)
pts = []
geoms = getattr(bd, 'geoms', [bd])
for ln in geoms:
    L = ln.length
    for t in np.linspace(0, L, 400): p = ln.interpolate(t); pts.append((p.x, p.y))
pts = np.array(pts)
la, d = af.cross_arc_signed(pts[:, 0], pts[:, 1])
h, e = np.histogram(d, bins=np.arange(-80, 80, 2))
print('digitised OSU11 Site1 boundary d-hist peaks:', [(round(e[i] + 1), int(h[i])) for i in range(len(h)) if h[i] > 0.02 * len(d)])
