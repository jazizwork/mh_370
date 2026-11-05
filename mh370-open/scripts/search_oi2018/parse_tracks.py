# Parse GPS-Visualizer KMZ track exports of Seabed Constructor (AIS) into a CSV.
# Timestamps in the source are locale-mangled: for day<=12 they read YYYY-DD-MM. We fix using the file's month.
import sys, zipfile, re, glob, csv, datetime as dt
MONTH = {'December 2017': (2017, 12), 'January 2018': (2018, 1), 'February 2018': (2018, 2), 'March 2018': (2018, 3),
         'April 2018': (2018, 4), 'May 2018': (2018, 5), '607 Final': (2018, 6)}
rows = {}
for p in sorted(glob.glob(sys.argv[1] + "/Seabed Constructor Track*.kmz")):
    key = [k for k in MONTH if k in p][0]
    y, m = MONTH[key]
    z = zipfile.ZipFile(p)
    t = z.read(z.namelist()[0]).decode('utf-8', 'replace')
    pts = re.findall(r'trackpoint #(\d+)</b>.*?<i>Time:</i> (\d{4})-(\d\d)-(\d\d) (\d\d:\d\d:\d\d)\]\]>.*?<coordinates>([-\d.]+),([-\d.]+)</coordinates>', t, re.S)
    bad = 0; out = []
    for n, Y, a, b, hms, lo, la in pts:
        a, b = int(a), int(b)
        if a == m and not (b == m and False):
            day = b
            # ambiguous if b<=12 and b==m: e.g. 2018-04-04 -> fine either way
        elif b == m:
            day = a
        else:
            bad += 1; continue
        # if a==m and b<=12 and b!=m it could also be DD-MM with day=a... resolve: a==m -> MM-DD
        tm = dt.datetime(int(Y), m, day, *map(int, hms.split(':')))
        out.append((int(n), tm, float(la), float(lo)))
    out.sort()
    # monotonic check
    nonmono = sum(1 for i in range(1, len(out)) if out[i][1] < out[i-1][1])
    print(key, len(pts), 'bad', bad, 'non-monotonic', nonmono, out[0][1] if out else None, out[-1][1] if out else None)
    for n, tm, la, lo in out:
        rows[tm] = (la, lo, key)
with open(sys.argv[2], 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['time_utc_assumed', 'lat', 'lon', 'src_file_month'])
    for tm in sorted(rows):
        w.writerow([tm.isoformat(), f"{rows[tm][0]:.6f}", f"{rows[tm][1]:.6f}", rows[tm][2]])
print("total unique", len(rows))
