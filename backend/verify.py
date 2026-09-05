"""Run the verification checklist from the project brief and print a report.

    python verify.py

This is deliberately separate from the pytest suite. The tests assert; this
prints, so a person can read the numbers and judge them. Cross-checking an
astrology engine is ultimately a human act.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from app.jyotish import constants as K
from app.jyotish.dasha import vimshottari
from app.jyotish.ephemeris import compute_chart, ephemeris_backend
from app.jyotish.timeutil import build_moment, julian_day

GREEN, RED, YEL, DIM, OFF = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"
if sys.platform == "win32":
    try:
        import colorama                    # noqa
        colorama.just_fix_windows_console()
    except Exception:
        GREEN = RED = YEL = DIM = OFF = ""

_failures = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global _failures
    mark = f"{GREEN}PASS{OFF}" if ok else f"{RED}FAIL{OFF}"
    if not ok:
        _failures += 1
    print(f"  [{mark}] {label}" + (f"  {DIM}{detail}{OFF}" if detail else ""))


def head(text: str) -> None:
    print(f"\n{YEL}{text}{OFF}\n" + "-" * 74)


# ---------------------------------------------------------------------------
head("Engine")
info = ephemeris_backend()
print(f"  Swiss Ephemeris {info['swe_version']} via the {info['backend']} backend")
print(f"  {DIM}{info['detail']}{OFF}")
if info["backend"] == "Moshier":
    print(f"  {DIM}To widen the date range, drop sepl_*.se1 / semo_*.se1 into "
          f"backend/ephe/.{OFF}")

# ---------------------------------------------------------------------------
head("1. Cross-check against published charts")

REFERENCES = [
    {
        "name": "Mahatma Gandhi",
        "birth": ("1869-10-02", "07:11:56", 21.6417, 69.6293),
        "note": "Porbandar. Pre-standard time -> Local Mean Time.",
        "expect": {"lagna": "Libra", "Sun": "Virgo", "Moon": "Cancer",
                   "moon_nakshatra": "Ashlesha", "Mars": "Libra",
                   "Venus": "Libra", "Saturn": "Scorpio"},
    },
    {
        "name": "Jawaharlal Nehru",
        "birth": ("1889-11-14", "23:03:00", 25.4358, 81.8463),
        "note": "Allahabad.",
        "expect": {"lagna": "Cancer", "Moon": "Cancer", "Sun": "Scorpio"},
    },
    {
        "name": "Albert Einstein",
        "birth": ("1879-03-14", "11:30:00", 48.4011, 9.9876),
        "note": "Ulm. Published tropically; checked by adding the ayanamsa back.",
        "expect": {"lagna": "Gemini", "Sun": "Pisces", "Moon": "Scorpio"},
        "tropical": {"Sun": 353.5, "Moon": 254.5},
    },
]

for ref in REFERENCES:
    date, time, lat, lon = ref["birth"]
    c = compute_chart(build_moment(date, time, lat, lon))
    print(f"\n  {ref['name']}  {DIM}{date} {time}  {ref['note']}{OFF}")
    print(f"    {DIM}offset used {c.moment['utc_offset_label']} "
          f"({c.moment['time_standard']}){OFF}")

    exp = ref["expect"]
    if "lagna" in exp:
        check(f"Lagna is {exp['lagna']}", c.ascendant_sign_name == exp["lagna"],
              f"got {c.ascendant_sign_name} {c.ascendant_degree_str}")
    for planet in ("Sun", "Moon", "Mars", "Venus", "Saturn"):
        if planet in exp:
            got = c.planets[planet]["sign_name"]
            check(f"{planet} in {exp[planet]}", got == exp[planet],
                  f"got {got} {c.planets[planet]['degree_str']}")
    if "moon_nakshatra" in exp:
        got = c.planets["Moon"]["nakshatra_name"]
        check(f"Moon nakshatra {exp['moon_nakshatra']}",
              got == exp["moon_nakshatra"], f"got {got}")

    for planet, want in (ref.get("tropical") or {}).items():
        got = K.norm360(c.planets[planet]["longitude"] + c.ayanamsa_value)
        delta = abs(((got - want + 180) % 360) - 180)
        check(f"{planet} matches published tropical {want}deg",
              delta < 0.5, f"got {got:.2f}deg, off by {delta * 60:.1f} arcmin")

# ---------------------------------------------------------------------------
head("2. Sidereal, not tropical")

c = compute_chart(build_moment("2000-03-20", "07:35:00", 28.6139, 77.2090))
sun = c.planets["Sun"]
# At the equinox the tropical Sun is at 0 Aries (360deg). Subtracting the
# ayanamsa puts it one ayanamsa back, i.e. in Pisces -- and since the ayanamsa
# is ~23.9deg while Pisces spans 30deg, it lands in the first third of Pisces.
expected = K.norm360(360.0 - c.ayanamsa_value)
check("Equinox Sun falls one ayanamsa back from 0 Aries, into Pisces",
      sun["sign_name"] == "Pisces" and abs(sun["longitude"] - expected) < 1.0,
      f"got {sun['degree_str']} {sun['sign_name']} ({sun['longitude']:.2f}deg), "
      f"expected about {expected:.2f}deg")
check("Ayanamsa for 2000 is about 23d51'", 23.5 < c.ayanamsa_value < 24.2,
      f"got {c.ayanamsa_str}")

vals = {}
for name in K.AYANAMSA_OPTIONS:
    vals[name] = compute_chart(
        build_moment("2000-01-01", "12:00:00", 28.6139, 77.2090),
        ayanamsa=name).ayanamsa_value
check("All four ayanamsas give different values",
      len({round(v, 4) for v in vals.values()}) == 4,
      ", ".join(f"{k} {v:.4f}" for k, v in vals.items()))

# ---------------------------------------------------------------------------
head("3. Edge cases")

m = build_moment("2000-01-01", "00:00:00", 28.6139, 77.2090)
check("Midnight birth keeps its calendar date",
      m.local.strftime("%Y-%m-%d %H:%M") == "2000-01-01 00:00",
      f"local {m.local}, UTC {m.utc.isoformat()}")

east = build_moment("2005-03-10", "23:30:00", -18.1416, 178.4419)
west = build_moment("2005-03-10", "23:30:00", -13.7590, -172.1046)
check("International date line: same clock time, different UTC dates",
      east.utc.date() != west.utc.date(),
      f"Fiji {east.utc.date()} vs Samoa {west.utc.date()}")

c = compute_chart(build_moment("1990-06-21", "02:00:00", 69.6492, 18.9553))
check("Extreme latitude (Tromso 69.6N) produces a chart",
      c.ascendant is not None and len(c.houses) == 12,
      f"lagna {c.ascendant_sign_name}")

c = compute_chart(build_moment("1990-06-21", "02:00:00", 78.2232, 15.6267),
                  house_system="placidus")
check("Placidus above the polar circle degrades with a warning",
      any("polar" in w.lower() or "fell back" in w.lower() for w in c.warnings),
      c.warnings[0][:60] if c.warnings else "no warning")

m = build_moment("1905-06-15", "10:00:00", 22.5726, 88.3639, time_standard="zone")
check("Pre-1947 India is not +5:30", abs(m.utc_offset_hours - 5.5) > 0.1,
      f"{m.offset_label} ({m.tz_abbrev})")

zone = compute_chart(build_moment("1869-10-02", "07:11:56", 21.6417, 69.6293,
                                  time_standard="zone"))
lmt = compute_chart(build_moment("1869-10-02", "07:11:56", 21.6417, 69.6293,
                                 time_standard="lmt"))
check("Auto Local Mean Time changes Gandhi's lagna to the published value",
      zone.ascendant_sign_name == "Virgo" and lmt.ascendant_sign_name == "Libra",
      f"zone gives {zone.ascendant_sign_name}, LMT gives {lmt.ascendant_sign_name}")

c = compute_chart(build_moment("1990-05-05", None, 28.6139, 77.2090))
check("Unknown birth time suppresses the lagna and houses",
      c.ascendant is None and c.houses == []
      and all(p["house"] == 0 for p in c.planets.values()),
      "sign and nakshatra data still present")
check("Unknown birth time still yields Sun sign, Moon sign and nakshatra",
      bool(c.planets["Sun"]["sign_name"] and c.planets["Moon"]["nakshatra_name"]),
      f"Sun {c.planets['Sun']['sign_name']}, "
      f"Moon {c.planets['Moon']['nakshatra_name']}")

# ---------------------------------------------------------------------------
head("4. Vimshottari dasha")

check("The nine dasha lengths total 120 years",
      sum(K.VIMSHOTTARI_YEARS.values()) == 120,
      " + ".join(str(v) for v in K.VIMSHOTTARI_YEARS.values()))

c = compute_chart(build_moment("1990-05-05", "10:30:00", 28.6139, 77.2090))
jd = c.moment["jd_ut"]
tree = vimshottari(c.planets["Moon"]["longitude"], jd,
                   now_jd=julian_day(datetime.now(timezone.utc)), max_level=2)

span = (tree["periods"][-1]["end_jd"] - tree["periods"][0]["start_jd"]) / K.SIDEREAL_YEAR_DAYS
check("The full cycle spans exactly 120 years", abs(span - 120) < 1e-6,
      f"{span:.9f} years")
check("The first mahadasha lord is the Moon's nakshatra lord",
      tree["starting_lord"] == c.planets["Moon"]["nakshatra_lord"],
      f"{tree['birth_nakshatra']} -> {tree['starting_lord']}")
check("Birth falls inside the first mahadasha",
      tree["periods"][0]["start_jd"] <= jd < tree["periods"][0]["end_jd"],
      f"balance at birth {tree['balance_at_birth']['readable']}")

gaps = [abs(a["end_jd"] - b["start_jd"])
        for a, b in zip(tree["periods"], tree["periods"][1:])]
check("Mahadashas are contiguous", max(gaps) < 1e-9, f"largest gap {max(gaps):.2e} days")

worst = 0.0
for md in tree["periods"]:
    total = sum(ad["end_jd"] - ad["start_jd"] for ad in md["children"])
    worst = max(worst, abs(total - (md["end_jd"] - md["start_jd"])))
check("Antardashas sum exactly to their mahadasha", worst < 1e-6,
      f"largest drift {worst:.2e} days")

# ---------------------------------------------------------------------------
head("5. Table integrity")

from app.jyotish import ashtakavarga as av           # noqa: E402
check("Ashtakavarga rows match the published totals",
      av.table_totals() == av.EXPECTED_BAV_TOTALS,
      str(av.table_totals()))
a = av.compute(c.planets, c.ascendant_sign)
check("Sarvashtakavarga totals 337", a["sav_total"] == 337, f"got {a['sav_total']}")

lords = [n[1] for n in K.NAKSHATRAS]
check("Each dasha lord rules exactly 3 nakshatras",
      all(lords.count(p) == 3 for p in K.VIMSHOTTARI_ORDER))
check("Gana and Nadi each split the 27 nakshatras 9/9/9",
      all([x[4] for x in K.NAKSHATRAS].count(g) == 9
          for g in ("Deva", "Manushya", "Rakshasa"))
      and all([x[5] for x in K.NAKSHATRAS].count(n) == 9
              for n in ("Adi", "Madhya", "Antya")))

from app.jyotish.matching import ashtakoot            # noqa: E402
r = ashtakoot(10.0, 200.0)
check("Ashtakoot weights total 36",
      sum(k["max"] for k in r["kootas"]) == 36.0,
      ", ".join(f"{k['koota']} {k['max']:g}" for k in r["kootas"]))

# ---------------------------------------------------------------------------
print()
if _failures:
    print(f"{RED}{_failures} check(s) failed.{OFF}\n")
    sys.exit(1)
print(f"{GREEN}All verification checks passed.{OFF}\n")
