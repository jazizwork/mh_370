"""Refine a quadrilateral's corners by fitting straight lines to dark edge pixels near each approximate side.
usage: box_corners.py image.png x1,y1 x2,y2 x3,y3 x4,y4 [band]"""
import sys, cv2, numpy as np
im = cv2.imread(sys.argv[1]); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
dark = g < 70
C = [np.array(list(map(float, a.split(',')))) for a in sys.argv[2:6]]
band = float(sys.argv[6]) if len(sys.argv) > 6 else 4
ys, xs = np.nonzero(dark); P = np.c_[xs, ys].astype(float)
lines = []
for i in range(4):
    a, b = C[i], C[(i + 1) % 4]
    t = (b - a) / np.linalg.norm(b - a); nrm = np.array([-t[1], t[0]])
    s = (P - a) @ t; d = (P - a) @ nrm
    L = np.linalg.norm(b - a)
    sel = (s > 0.1 * L) & (s < 0.9 * L) & (np.abs(d) < band)
    Q = P[sel]
    # total least squares line
    c = Q.mean(axis=0); u, sv, vt = np.linalg.svd(Q - c); dirv = vt[0]
    res = (Q - c) @ vt[1]
    lines.append((c, dirv)); print(f"side {i}: n={sel.sum()} rms={np.sqrt(np.mean(res**2)):.2f}px")
def inter(l1, l2):
    (c1, d1), (c2, d2) = l1, l2
    A = np.c_[d1, -d2]; s = np.linalg.solve(A, c2 - c1); return c1 + s[0] * d1
for i in range(4):
    p = inter(lines[i - 1], lines[i]); print(f"corner {i}: {p[0]:.2f},{p[1]:.2f}")
