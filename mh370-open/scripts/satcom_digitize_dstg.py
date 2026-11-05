"""Digitise DSTG (2015 draft) Fig. 10.3 lower panel: posterior pdf of the 00:19 latitude with
BFO measurements, for comparison with this workstream's arc-latitude posterior.

Renders PDF page 103 with pdftoppm (poppler) at 400 dpi, finds the blue curve, and converts
pixels to (latitude, relative frequency) using the axis tick positions found in the image.
Output: outputs/satcom/dstg_fig10_3_digitised.csv  (+ summary printed)
"""
import pathlib
import subprocess
import tempfile

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDF = ROOT / "data" / "raw" / "dstg_book" / "Bayesian_Methods_MH370_Search_3Dec2015.pdf"
OUT = ROOT / "outputs" / "satcom" / "dstg_fig10_3_digitised.csv"


def main():
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-f", "103", "-l", "103", "-r", "400", "-png", str(PDF),
                        f"{td}/p"], check=True)
        im = np.asarray(Image.open(next(pathlib.Path(td).glob("p*.png"))).convert("RGB")).astype(int)
    H, W, _ = im.shape
    # lower panel region (fractions of page found by inspection of the rendered page)
    y0, y1, x0, x1 = int(0.30 * H), int(0.495 * H), int(0.22 * W), int(0.80 * W)
    sub = im[y0:y1, x0:x1]
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    blue = (b > 150) & (r < 120) & (g < 120)
    black = (r + g + b) < 420
    # axes frame: long horizontal rows = bottom (value 0) and top (value 0.4) frame lines;
    # long vertical columns = left (-50 deg) and right (+50 deg) frame lines
    rows = np.where(black.sum(1) > 0.6 * sub.shape[1])[0]
    y_axis0, top = rows.max(), rows.min()
    cols = np.where(black.sum(0) > 0.5 * (y_axis0 - top))[0]
    xl, xr = cols.min(), cols.max()
    lat_of = lambda x: -50 + 100 * (x - xl) / (xr - xl)
    val_of = lambda y: 0.4 * (y_axis0 - y) / (y_axis0 - top)
    xs, vs = [], []
    for x in range(xl + 2, xr - 1):
        ys = np.where(blue[:, x])[0]
        if ys.size:
            xs.append(lat_of(x))
            vs.append(max(val_of(ys.min()), 0.0))
    lat = np.array(xs)
    v = np.array(vs)
    v[v < 0.004] = 0.0
    p = v / np.trapezoid(v, lat)
    cdf = np.cumsum(p) * np.gradient(lat)
    cdf /= cdf[-1]
    q = {k: float(np.interp(k, cdf, lat)) for k in (0.05, 0.25, 0.5, 0.75, 0.95)}
    peak = float(lat[np.argmax(v)])
    np.savetxt(OUT, np.c_[lat, v, p], delimiter=",", header="lat,rel_freq,pdf_per_deg",
               comments="", fmt="%.4f")
    print(f"DSTG Fig 10.3 (with BFO): peak {peak:.2f}, median {q[0.5]:.2f}, "
          f"50% [{q[0.25]:.2f},{q[0.75]:.2f}], 90% [{q[0.05]:.2f},{q[0.95]:.2f}]")


if __name__ == "__main__":
    main()
