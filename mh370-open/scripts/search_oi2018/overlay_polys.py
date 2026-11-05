"""Draw lon/lat polygons (from oigeo outputs) on the OSU01 georeferenced image. usage: overlay_polys.py osu01_georef.json out.png geo1.json [geo2.json ...]"""
import sys, json, numpy as np, cv2
from pyproj import Transformer
d = json.load(open(sys.argv[1])); im = cv2.imread(d['image'])
fwd = Transformer.from_crs('EPSG:4326', d['crs'], always_xy=True)
Ec, Nc, S = d['norm']['Ec'], d['norm']['Nc'], d['norm']['Sc']; p = d['affine']
cols = [(0, 0, 255), (255, 0, 0), (0, 128, 0), (255, 0, 255), (0, 0, 0)]
for k, f in enumerate(sys.argv[3:]):
    g = json.load(open(f))
    for poly in g['polygons']:
        for ring in [poly['outer']] + poly['holes']:
            r = np.array(ring); e, n = fwd.transform(r[:, 0], r[:, 1]); e = (np.asarray(e) - Ec) / S; n = (np.asarray(n) - Nc) / S
            x = p[0] * e + p[1] * n + p[2]; y = p[3] * e + p[4] * n + p[5]
            cv2.polylines(im, [np.c_[x, y].round().astype(np.int32)], True, cols[k % 5], 1)
cv2.imwrite(sys.argv[2], im)
