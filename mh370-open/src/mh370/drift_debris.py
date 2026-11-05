"""MH370 debris evidence used by the drift likelihood (workstream B).

Selection: items classed CONFIRMED, ALMOST CERTAIN or HIGHLY LIKELY from 9M-MRO in
Malaysia's 2018 Safety Investigation Report (SIR) Table 1.12A, found up to Jan 2017.
Coordinates: as printed in Ulich & Iannello (2023) Table 3.2-1 (identical to Godfrey 2021
Table 1 to 4 decimals). Dates: SIR / ATSB debris-examination updates (official), with the
known conflicts noted below.

Reporting-delay windows (days between first arrival at the find region and the find):
  * items with many / a few live barnacles (flaperon, Rodrigues closet, Pemba flap, "Roy",
    Mpame fairing): 0-30 d  (Godfrey 2021: 0-10 d for fully barnacled, 5-15 d few; we widen
    to 30 d to cover the 5-day model time step and position uncertainty);
  * barnacle-free items: 15-150 d (Ulich & Iannello 2023: 10-150 d; Godfrey 2021: 15-79 d).
Sensitivity variants change these windows.

Sources
  SIR 2018 Table 1.12A (court-filing copy):
    https://images.law.com/contrib/content/uploads/documents/398/20710/Malaysia-Air-final-report.pdf
  ATSB debris examination updates 1, 2, 3, 5:
    https://www.atsb.gov.au/sites/default/files/media/5773385/debris-examination-update-1_amended.pdf (etc.)
  Ulich & Iannello (2023), Improved prediction of MH370 crash location based on drift modeling
    of floating debris, https://mh370.radiantphysics.com/2023/06/12/improved-drift-model-and-search-recommendations-for-mh370/
  Godfrey (2021), MH370 Floating Debris Drift Analysis,
    https://www.mh370search.com/2021/01/21/mh370-debris-drift-analysis/
Known conflicts (see outputs/drift/README.md):
  * "Roy" (engine nose cowl): official find 22 Mar 2016; first photographed on the beach
    23 Dec 2015 (used by Godfrey, Ulich & Iannello and CSIRO Part I). We use 23 Dec 2015.
  * Mauritius left outboard flap: official ~10 May 2016 (SIR table; ATSB update 5); Ulich &
    Iannello / Godfrey Table 1 give 15 Mar 2016. We use 10 May 2016.
  * Nosy Boraha (Madagascar) items MOT11, MOT15 (Riake, 6 Jun 2016) and MOT16, MOT18
    (Antsiraka, 12 Jun 2016) were found together by one searcher within 1.5 km; they are
    treated as ONE observation (earliest date) to avoid counting one arrival event 4 times.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

RELEASE_TIME = np.datetime64("2014-03-08T00:20")   # ~7th arc (00:19:29 UTC 8 Mar 2014)

BARN_WINDOW = (0.0, 30.0)
NOBARN_WINDOW = (15.0, 150.0)


@dataclass(frozen=True)
class Item:
    key: str
    name: str
    sir: str            # SIR item number(s)
    cls: str            # SIR class
    date: str           # find date used (ISO)
    lat: float
    lon: float
    region: str         # coarse region (for the first-per-region variant)
    barnacles: bool     # live barnacles reported -> short reporting delay
    note: str = ""

    @property
    def days(self) -> float:
        """Find time in days after release."""
        return float((np.datetime64(self.date + "T12:00") - RELEASE_TIME)
                     / np.timedelta64(1, "h")) / 24.0

    def window(self, scale: float = 1.0, nobarn=NOBARN_WINDOW, barn=BARN_WINDOW):
        """(t_early, t_late) in days after release: interval of first arrival times
        consistent with the find (find date minus max/min reporting delay)."""
        dmin, dmax = barn if self.barnacles else nobarn
        dmax = dmin + (dmax - dmin) * scale
        return self.days - dmax, self.days - dmin


ITEMS: list[Item] = [
    Item("flaperon", "Right flaperon", "MOT1", "Confirmed", "2015-07-29",
         -20.91618, 55.64915, "Reunion", True,
         "Saint-Andre, Reunion; beach cleaners: absent at sunset 28 Jul (Godfrey 2021)"),
    Item("moz_daghatane", "No.7 flap support fairing (676EB)", "MOT2", "Almost certain",
         "2015-12-27", -24.07806, 35.49980, "Mozambique", False, "Liam Lotter"),
    Item("sa_roy", "Engine nose cowl 'Roy'", "MOT4", "Almost certain", "2015-12-23",
         -34.09377, 22.14991, "South Africa", True,
         "Klein Brak River, Mossel Bay; first photographed 23 Dec 2015 (official find 22 Mar 2016); many barnacles"),
    Item("moz_nostep", "'NO STEP' horizontal stabiliser panel", "MOT3", "Almost certain",
         "2016-02-27", -22.08857, 35.51902, "Mozambique", False, "Paluma sandbank, Vilankulo; Gibson"),
    Item("rodrigues", "Door R1 stowage closet panel", "MOT5", "Almost certain", "2016-03-30",
         -19.73871, 63.47163, "Rodrigues", True, "Var-Brule, Rodrigues; few barnacles"),
    Item("moz_chidenguele", "Right engine fan cowling piece", "MOT6", "Almost certain",
         "2016-04-24", -24.95802, 34.19637, "Mozambique", False, "south of Chidenguele"),
    Item("mus_flap", "Left outboard flap trailing-edge section", "MOT10", "Confirmed",
         "2016-05-10", -20.02338, 57.70139, "Mauritius", False, "Ilot Bernache, Mauritius"),
    Item("moz_macaneta", "Left wing trailing-edge panel", "MOT9", "Highly likely",
         "2016-05-22", -25.86302, 32.74599, "Mozambique", False, "Macaneta peninsula, Maputo Bay"),
    Item("mus_grisgris", "No.1 flap support fairing tail cone", "MOT8", "Highly likely",
         "2016-05-24", -20.52245, 57.53762, "Mauritius", False, "Gris-Gris beach, Souillac"),
    Item("mdg_nosyboraha", "4 items (IFE trim panel, trailing-edge panel, cabin panel, nose-gear door)",
         "MOT11,15,16,18", "Highly likely/Almost certain", "2016-06-06",
         -16.78694, 49.98528, "Madagascar", False,
         "Riake & Antsiraka beaches, Nosy Boraha (Ste-Marie); Gibson; locals saw items ~1 month earlier"),
    Item("tza_pemba", "Right outboard flap (inboard section)", "MOT19", "Confirmed", "2016-06-20",
         -5.05607, 39.86809, "Tanzania", True, "Kojani Island, Pemba; few barnacles"),
    Item("sa_kosi", "Right aft wing-to-body fairing", "MOT20", "Highly likely", "2016-06-21",
         -26.89381, 32.88089, "South Africa", False, "Kosi Bay mouth, KwaZulu-Natal"),
    Item("moz_lingalinga", "Right vertical stabiliser panel", "MOT22", "Almost certain",
         "2016-08-26", -23.73931, 35.40077, "Mozambique", False, "Linga Linga"),
    Item("sa_nautilus", "Right aileron (inboard section)", "MOT26", "Highly likely", "2016-12-23",
         -34.22081, 21.97875, "South Africa", False, "Nautilus Bay"),
    Item("sa_mpame", "No.7 flap support fairing (fixed fwd part)", "MOT27", "Highly likely",
         "2017-01-27", -32.09748, 29.06285, "South Africa", True, "Mpame beach, Eastern Cape; few barnacles"),
]

ITEM_BY_KEY = {it.key: it for it in ITEMS}


def first_per_region() -> list[Item]:
    seen, out = set(), []
    for it in sorted(ITEMS, key=lambda x: x.days):
        if it.region not in seen:
            seen.add(it.region)
            out.append(it)
    return out


# Negative evidence: no MH370 debris reported from the Western Australian coast.
# Region: Markov-chain cells whose centre lies within WA_COAST_KM of the WA coastline
# between WA_LAT and east of WA_LON_MIN. Time: first WA_DAYS after release.
WA_LAT = (-35.6, -21.0)
WA_LON_MIN = 112.0
WA_COAST_KM = 100.0
WA_DAYS = 548.0          # ~18 months (to ~Sep 2015)
WA_LAMBDA = 20.0         # expected number of reported WA finds if p(reach WA band)=1


def table():
    import pandas as pd
    rows = []
    for it in ITEMS:
        a, b = it.window()
        rows.append(dict(key=it.key, name=it.name, sir=it.sir, cls=it.cls, find_date=it.date,
                         lat=it.lat, lon=it.lon, region=it.region, barnacles=it.barnacles,
                         find_day=round(it.days, 1), arrive_from_day=round(a, 1),
                         arrive_to_day=round(b, 1), note=it.note))
    return pd.DataFrame(rows)
