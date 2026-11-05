"""usage: px2ll.py geo.json x,y [x,y ...]  -> lon lat using affine+crs from oigeo output"""
import sys, json, numpy as np
from pyproj import Transformer
d = json.load(open(sys.argv[1]))
inv = Transformer.from_crs(d['crs'], 'EPSG:4326', always_xy=True)
px, py = np.array(d['affine_px']), np.array(d['affine_py']); Ec, Nc, S = d['norm']
M = np.array([[px[0], px[1]], [py[0], py[1]]])
for a in sys.argv[2:]:
    x, y = map(float, a.split(','))
    e, n = np.linalg.solve(M, [x - px[2], y - py[2]])
    lon, lat = inv.transform(e * S + Ec, n * S + Nc)
    print(f"{a:>12} -> lon {lon:.4f} lat {lat:.4f}")
