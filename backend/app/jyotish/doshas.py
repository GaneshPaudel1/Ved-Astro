"""Dosha detection: Manglik, Kaal Sarp, Sade Sati, Pitra.

These carry real social weight in the communities that use them, so every
detector states its rule, lists cancellations, and describes severity honestly
rather than issuing a verdict. Where traditions disagree -- and on Manglik they
disagree a great deal -- the disagreement is reported rather than hidden.
"""
from __future__ import annotations

from typing import Any

import swisseph as swe

from . import constants as K
from .timeutil import jd_to_utc

# --------------------------------------------------------------------------
# Manglik / Kuja dosha
# --------------------------------------------------------------------------
# Houses counted from the reference point in which Mars is said to cause the
# dosha. The 2nd is counted by North Indian tradition and often dropped in the
# South; we include it but label its contribution.
MANGLIK_HOUSES = [1, 2, 4, 7, 8, 12]
MANGLIK_HOUSES_SOUTH = [1, 4, 7, 8, 12]


def manglik(planets: dict[str, dict[str, Any]], asc_sign: int | None) -> dict[str, Any]:
    """Mars in 1, 2, 4, 7, 8 or 12 -- checked from lagna, Moon and Venus."""
    mars = planets.get("Mars")
    if not mars:
        return {"present": False, "reason": "Mars position unavailable."}

    references: dict[str, int | None] = {
        "Lagna": asc_sign,
        "Moon": planets["Moon"]["sign"] if "Moon" in planets else None,
        "Venus": planets["Venus"]["sign"] if "Venus" in planets else None,
    }

    hits = []
    for label, base in references.items():
        if base is None:
            continue
        house = K.house_distance(base, mars["sign"])
        if house in MANGLIK_HOUSES:
            hits.append({
                "reference": label,
                "house": house,
                "counted_in_south_india": house in MANGLIK_HOUSES_SOUTH,
            })

    present = bool(hits)
    cancellations = _manglik_cancellations(planets, asc_sign, mars) if present else []

    strong_hits = [h for h in hits if h["counted_in_south_india"]]
    if not present:
        severity = "none"
    elif cancellations:
        severity = "cancelled"
    elif len(strong_hits) >= 2:
        severity = "high"
    elif strong_hits:
        severity = "moderate"
    else:
        severity = "low"

    return {
        "present": present,
        "severity": severity,
        "mars_sign": mars["sign_name"],
        "mars_house": K.house_distance(asc_sign, mars["sign"]) if asc_sign is not None else None,
        "hits": hits,
        "cancellations": cancellations,
        "rule": ("Mars falling in the 1st, 2nd, 4th, 7th, 8th or 12th house, "
                 "counted from the ascendant, the Moon and Venus in turn."),
        "note": ("Traditions differ. Southern practice usually omits the 2nd "
                 "house, and many astrologers only weigh the count from the "
                 "ascendant. Treat this as one factor in a compatibility "
                 "reading, not a verdict."),
    }


def _manglik_cancellations(planets, asc_sign, mars) -> list[str]:
    out = []
    sign = mars["sign"]

    if mars["dignity"] in ("own sign", "exalted", "moolatrikona"):
        out.append(f"Mars is {mars['dignity']} in {mars['sign_name']}, so it acts "
                   f"constructively rather than destructively.")
    # Mars in its own or Saturn's signs is classically exempt.
    if sign in (0, 7, 9, 10):
        out.append(f"Mars occupies {K.SIGN_NAMES[sign]}, one of the signs in "
                   f"which the dosha is traditionally not counted.")

    jup = planets.get("Jupiter")
    if jup and (jup["sign"] == sign
                or K.house_distance(jup["sign"], sign) in (5, 7, 9)):
        out.append("Jupiter joins or aspects Mars, which classical texts treat "
                   "as restraining it.")

    if asc_sign is not None:
        moon = planets.get("Moon")
        if moon and K.house_distance(asc_sign, moon["sign"]) in K.KENDRA_HOUSES:
            out.append("A strong angular Moon offsets the affliction.")

    sat = planets.get("Saturn")
    if sat and sat["sign"] == sign:
        out.append("Saturn sits with Mars, which slows and steadies it.")

    return out


# --------------------------------------------------------------------------
# Kaal Sarp dosha
# --------------------------------------------------------------------------
def kaal_sarp(planets: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """All seven visible planets hemmed between Rahu and Ketu.

    Worked on longitudes rather than signs, since the axis rarely falls on a
    sign boundary and the sign-level test gives false positives.
    """
    rahu = planets.get("Rahu")
    ketu = planets.get("Ketu")
    if not rahu or not ketu:
        return {"present": False}

    rahu_lon = rahu["longitude"]
    others = {n: p["longitude"] for n, p in planets.items()
              if n not in ("Rahu", "Ketu")}

    # Arc measured forward from Rahu. Everything inside 180 deg means all the
    # planets sit on the Rahu-to-Ketu side of the axis.
    arcs = {n: (lon - rahu_lon) % 360 for n, lon in others.items()}
    all_forward = all(0 < a < 180 for a in arcs.values())
    all_backward = all(180 < a < 360 for a in arcs.values())

    present = all_forward or all_backward
    partial = False
    breaking = []
    if not present:
        fwd = [n for n, a in arcs.items() if 0 < a < 180]
        bwd = [n for n, a in arcs.items() if 180 < a < 360]
        minority = fwd if len(fwd) < len(bwd) else bwd
        if len(minority) == 1:
            partial = True
            breaking = minority

    axis_house = None
    name = None
    if present:
        # The dosha is named for the house Rahu occupies.
        names = ["Anant", "Kulik", "Vasuki", "Shankhpal", "Padma", "Mahapadma",
                 "Takshak", "Karkotak", "Shankhachud", "Ghatak", "Vishdhar", "Sheshnag"]
        if rahu.get("house"):
            axis_house = rahu["house"]
            name = names[(axis_house - 1) % 12]

    return {
        "present": present,
        "partial": partial,
        "breaking_planet": breaking,
        "type": name,
        "rahu_house": axis_house,
        "rahu_sign": rahu["sign_name"],
        "ketu_sign": ketu["sign_name"],
        "rule": ("Every one of the seven visible grahas falls within the 180 "
                 "degrees on one side of the Rahu-Ketu axis."),
        "note": ("Read as life running along a narrow channel -- concentrated "
                 "effort, delayed but often decisive results. A single planet "
                 "outside the axis breaks it, which is why the partial case is "
                 "reported separately."),
    }


# --------------------------------------------------------------------------
# Sade Sati
# --------------------------------------------------------------------------
SADE_SATI_PHASES = {
    12: ("Rising", "Saturn in the 12th from your Moon. Expenses, sleep and "
                   "unsettled circumstances; the phase that arrives before the "
                   "pressure is obvious."),
    1:  ("Peak", "Saturn over your natal Moon. The heaviest stretch -- health, "
                 "mood and identity all under review."),
    2:  ("Setting", "Saturn in the 2nd from your Moon. Money, family and speech; "
                    "the phase where the lesson is consolidated."),
}


def _saturn_sign_at(jd: float, ayanamsa: str = K.DEFAULT_AYANAMSA) -> int:
    from .ephemeris import _set_ayanamsa, _swe_lock
    with _swe_lock:
        _set_ayanamsa(ayanamsa)
        vals, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    return K.sign_of(vals[0])


def sade_sati(moon_sign: int, from_jd: float, to_jd: float,
              now_jd: float | None = None,
              ayanamsa: str = K.DEFAULT_AYANAMSA) -> dict[str, Any]:
    """Locate every Sade Sati window in a date range.

    Saturn is scanned at ten-day steps -- it takes about two and a half years to
    cross a sign, so that resolution finds every ingress, and the boundary is
    then bisected to the day.
    """
    watched = {(moon_sign + 11) % 12: 12, moon_sign: 1, (moon_sign + 1) % 12: 2}

    step = 10.0
    spans: list[dict[str, Any]] = []
    jd = from_jd
    prev_sign = _saturn_sign_at(jd, ayanamsa)
    current: dict[str, Any] | None = None

    if prev_sign in watched:
        current = {"phase_house": watched[prev_sign], "start_jd": jd,
                   "sign": prev_sign, "open_start": True}

    while jd < to_jd:
        jd += step
        sign = _saturn_sign_at(jd, ayanamsa)
        if sign == prev_sign:
            continue
        boundary = _bisect_ingress(jd - step, jd, prev_sign, ayanamsa)
        if current is not None:
            current["end_jd"] = boundary
            spans.append(current)
            current = None
        if sign in watched:
            current = {"phase_house": watched[sign], "start_jd": boundary,
                       "sign": sign, "open_start": False}
        prev_sign = sign

    if current is not None:
        current["end_jd"] = to_jd
        current["open_end"] = True
        spans.append(current)

    phases = []
    for s in spans:
        label, description = SADE_SATI_PHASES[s["phase_house"]]
        phases.append({
            "phase": label,
            "house_from_moon": s["phase_house"],
            "sign": s["sign"],
            "sign_name": K.SIGN_NAMES[s["sign"]],
            "start": jd_to_utc(s["start_jd"]).date().isoformat(),
            "end": jd_to_utc(s["end_jd"]).date().isoformat(),
            "start_jd": s["start_jd"],
            "end_jd": s["end_jd"],
            "description": description,
            "current": (now_jd is not None
                        and s["start_jd"] <= now_jd < s["end_jd"]),
        })

    active = next((p for p in phases if p["current"]), None)
    return {
        "moon_sign": K.SIGN_NAMES[moon_sign],
        "currently_active": active is not None,
        "current_phase": active,
        "phases": phases,
        "rule": ("The roughly seven-and-a-half years during which Saturn "
                 "crosses the 12th, 1st and 2nd signs from your natal Moon."),
        "note": ("Sade Sati is a period of consolidation and testing, not a "
                 "sentence. Its weight depends on Saturn's dignity in the "
                 "chart and on which dasha is running alongside it."),
    }


def _bisect_ingress(lo_jd: float, hi_jd: float, sign_before: int,
                    ayanamsa: str, tolerance: float = 0.02) -> float:
    """Narrow a sign change to within about half an hour."""
    while hi_jd - lo_jd > tolerance:
        mid = (lo_jd + hi_jd) / 2.0
        if _saturn_sign_at(mid, ayanamsa) == sign_before:
            lo_jd = mid
        else:
            hi_jd = mid
    return (lo_jd + hi_jd) / 2.0


def small_panoti(moon_sign: int, jupiter_sign: int | None = None) -> dict[str, Any]:
    """Placeholder kept explicit: Dhaiya, Saturn's 2.5-year transit of the
    4th and 8th from the Moon."""
    return {
        "watched_signs": [(moon_sign + 3) % 12, (moon_sign + 7) % 12],
        "note": ("Dhaiya or Small Panoti: Saturn crossing the 4th or 8th from "
                 "the Moon, about two and a half years each."),
    }


# --------------------------------------------------------------------------
# Pitra dosha
# --------------------------------------------------------------------------
def pitra_dosha(planets: dict[str, dict[str, Any]],
                asc_sign: int | None) -> dict[str, Any]:
    """Indicators of ancestral obligation, centred on the Sun and the 9th house."""
    if asc_sign is None:
        return {"present": False,
                "reason": "Needs house positions, which require a birth time."}

    indicators: list[str] = []
    ninth_sign = (asc_sign + 8) % 12
    ninth_lord = K.SIGN_LORDS[ninth_sign]

    sun = planets.get("Sun")
    rahu = planets.get("Rahu")
    ketu = planets.get("Ketu")
    sat = planets.get("Saturn")

    if rahu and K.house_distance(asc_sign, rahu["sign"]) == 9:
        indicators.append("Rahu occupies the 9th house, the house of father and "
                          "ancestry.")
    if ketu and K.house_distance(asc_sign, ketu["sign"]) == 9:
        indicators.append("Ketu occupies the 9th house.")
    if sun and rahu and sun["sign"] == rahu["sign"]:
        indicators.append("The Sun is conjunct Rahu, an eclipse-like affliction "
                          "to the significator of the father.")
    if sun and sat and sun["sign"] == sat["sign"]:
        indicators.append("The Sun is conjunct Saturn, classically read as "
                          "distance or difficulty with the father.")
    if sun and K.house_distance(asc_sign, sun["sign"]) in K.DUSTHANA_HOUSES:
        h = K.house_distance(asc_sign, sun["sign"])
        indicators.append(f"The Sun falls in the {h}th, a difficult house.")

    nl = planets.get(ninth_lord)
    if nl and K.house_distance(asc_sign, nl["sign"]) in K.DUSTHANA_HOUSES:
        indicators.append(f"{ninth_lord}, lord of the 9th, falls in the "
                          f"{K.house_distance(asc_sign, nl['sign'])}th house.")

    return {
        "present": len(indicators) >= 2,
        "weak_indication": len(indicators) == 1,
        "indicators": indicators,
        "ninth_lord": ninth_lord,
        "rule": ("Affliction to the Sun, to the 9th house, or to the 9th lord "
                 "-- the significators of father and lineage."),
        "note": ("Read traditionally as an unmet obligation to the ancestors, "
                 "addressed through rites rather than remedial gemstones. Two "
                 "or more indicators are required before it is reported."),
    }


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def detect_all(planets: dict[str, dict[str, Any]], asc_sign: int | None,
               birth_jd: float | None = None, now_jd: float | None = None,
               ayanamsa: str = K.DEFAULT_AYANAMSA) -> dict[str, Any]:
    out: dict[str, Any] = {
        "manglik": manglik(planets, asc_sign),
        "kaal_sarp": kaal_sarp(planets),
        "pitra": pitra_dosha(planets, asc_sign),
    }
    if "Moon" in planets and birth_jd is not None:
        # Cover a full lifetime: Saturn's cycle is ~29.5 years, so a 100-year
        # window catches every Sade Sati a person can live through.
        out["sade_sati"] = sade_sati(
            planets["Moon"]["sign"], birth_jd, birth_jd + 100 * 365.25,
            now_jd=now_jd, ayanamsa=ayanamsa)
    return out
