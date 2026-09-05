"""Gochar -- transits read against a natal chart.

Vedic practice reads transits primarily from the natal *Moon*, not the
ascendant, so both counts are given and the Moon-based one leads. Where a
planet's own Ashtakavarga bindus are available they are attached, since the
same transit behaves differently over a sign where the planet holds five bindus
than over one where it holds one.
"""
from __future__ import annotations

from typing import Any

import swisseph as swe

from . import constants as K
from .ephemeris import sidereal_longitudes, _set_ayanamsa, _swe_lock
from .timeutil import jd_to_utc

SLOW_PLANETS = ["Jupiter", "Saturn", "Rahu", "Ketu"]

# How the classical texts read each planet crossing each house from the Moon.
GOCHAR_NOTES = {
    1: "over your natal Moon -- the matter becomes personal and unavoidable",
    2: "touching money, family and speech",
    3: "generally supportive; effort pays",
    4: "unsettling home and peace of mind",
    5: "affecting children, creativity and study",
    6: "generally supportive; you gain over opposition",
    7: "affecting partnership and open dealings",
    8: "a period of strain and hidden difficulty",
    9: "affecting fortune, travel and belief",
    10: "acting on career and public standing",
    11: "generally supportive; gains and networks",
    12: "draining -- expense, isolation, disturbed sleep",
}

# The houses from the natal Moon in which a transit is traditionally favourable.
FAVOURABLE_FROM_MOON = {
    "Sun": [3, 6, 10, 11], "Moon": [1, 3, 6, 7, 10, 11],
    "Mars": [3, 6, 11], "Mercury": [2, 4, 6, 8, 10, 11],
    "Jupiter": [2, 5, 7, 9, 11], "Venus": [1, 2, 3, 4, 5, 8, 9, 11, 12],
    "Saturn": [3, 6, 11], "Rahu": [3, 6, 11], "Ketu": [3, 6, 11],
}


def current_positions(jd: float, ayanamsa: str = K.DEFAULT_AYANAMSA,
                      node_type: str = "mean") -> dict[str, dict[str, Any]]:
    lons = sidereal_longitudes(jd, ayanamsa, node_type)
    out: dict[str, dict[str, Any]] = {}
    for name in K.PLANETS:
        lon, lat, speed = lons[name]
        sign = K.sign_of(lon)
        out[name] = {
            "name": name,
            "longitude": round(lon, 6),
            "sign": sign,
            "sign_name": K.SIGN_NAMES[sign],
            "degree_in_sign": round(K.deg_in_sign(lon), 6),
            "degree_str": K.format_dms(K.deg_in_sign(lon)),
            "nakshatra_name": K.NAKSHATRA_NAMES[K.nakshatra_of(lon)],
            "pada": K.pada_of(lon),
            "retrograde": True if name in ("Rahu", "Ketu") else speed < 0,
            "speed": round(speed, 6),
            "abbr": K.PLANET_ABBR[name],
        }
    return out


def compute(natal_planets: dict[str, dict[str, Any]],
            natal_asc_sign: int | None,
            jd: float,
            ayanamsa: str = K.DEFAULT_AYANAMSA,
            bav: dict[str, list[int]] | None = None) -> dict[str, Any]:
    """Overlay live positions on a natal chart."""
    transiting = current_positions(jd, ayanamsa)
    moon_sign = natal_planets["Moon"]["sign"] if "Moon" in natal_planets else None

    rows = []
    for name, t in transiting.items():
        from_moon = K.house_distance(moon_sign, t["sign"]) if moon_sign is not None else None
        from_lagna = (K.house_distance(natal_asc_sign, t["sign"])
                      if natal_asc_sign is not None else None)
        natal = natal_planets.get(name)

        row = {
            **t,
            "house_from_moon": from_moon,
            "house_from_lagna": from_lagna,
            "note": GOCHAR_NOTES.get(from_moon) if from_moon else None,
            "favourable": (from_moon in FAVOURABLE_FROM_MOON.get(name, [])
                           if from_moon else None),
            "natal_sign_name": natal["sign_name"] if natal else None,
            "returned_to_natal_sign": bool(natal and natal["sign"] == t["sign"]),
        }
        if bav and name in bav:
            row["bindus_in_sign"] = bav[name][t["sign"]]
            row["bindu_note"] = _bindu_note(bav[name][t["sign"]])

        # Conjunctions with natal planets, within 5 degrees.
        hits = []
        for n_name, n in natal_planets.items():
            sep = abs(((t["longitude"] - n["longitude"] + 180) % 360) - 180)
            if sep <= 5.0:
                hits.append({"natal_planet": n_name, "orb": round(sep, 2)})
        row["conjunct_natal"] = sorted(hits, key=lambda h: h["orb"])
        rows.append(row)

    return {
        "jd": jd,
        "moment": jd_to_utc(jd).replace(microsecond=0).isoformat(),
        "ayanamsa": ayanamsa,
        "natal_moon_sign": K.SIGN_NAMES[moon_sign] if moon_sign is not None else None,
        "read_from": ("Transits are counted from the natal Moon, which is the "
                      "usual Vedic practice; the count from the ascendant is "
                      "given alongside."),
        "planets": {r["name"]: r for r in rows},
    }


def _bindu_note(bindus: int) -> str:
    if bindus >= 5:
        return f"{bindus} of its own bindus here -- the transit runs smoothly."
    if bindus >= 4:
        return f"{bindus} bindus -- mixed."
    return f"only {bindus} bindus -- this crossing asks for more care."


# --------------------------------------------------------------------------
# Ingresses and alerts
# --------------------------------------------------------------------------
_SWE_ID = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
           "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
           "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}


def _sign_at(jd: float, planet: str, ayanamsa: str) -> int:
    with _swe_lock:
        _set_ayanamsa(ayanamsa)
        vals, _ = swe.calc_ut(jd, _SWE_ID[planet], swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    lon = vals[0] + (180.0 if planet == "Ketu" else 0.0)
    return K.sign_of(lon)


def next_ingresses(jd: float, planets: list[str] | None = None,
                   horizon_days: float = 1100.0,
                   ayanamsa: str = K.DEFAULT_AYANAMSA) -> list[dict[str, Any]]:
    """When each slow planet next changes sign.

    Stepped coarsely then bisected. The horizon defaults to three years, which
    is long enough to always catch Saturn -- it needs about 2.5 years per sign.
    """
    planets = planets or SLOW_PLANETS
    out = []
    for name in planets:
        key = "Rahu" if name == "Ketu" else name
        start_sign = _sign_at(jd, key, ayanamsa)
        if name == "Ketu":
            start_sign = (start_sign + 6) % 12

        step = 2.0 if name in ("Jupiter", "Saturn", "Rahu", "Ketu") else 0.5
        cursor = jd
        found = None
        while cursor - jd < horizon_days:
            cursor += step
            s = _sign_at(cursor, key, ayanamsa)
            if name == "Ketu":
                s = (s + 6) % 12
            if s != start_sign:
                lo, hi = cursor - step, cursor
                for _ in range(50):
                    mid = (lo + hi) / 2.0
                    ms = _sign_at(mid, key, ayanamsa)
                    if name == "Ketu":
                        ms = (ms + 6) % 12
                    if ms == start_sign:
                        lo = mid
                    else:
                        hi = mid
                found = ((lo + hi) / 2.0, s)
                break
        if found:
            when, new_sign = found
            out.append({
                "planet": name,
                "from_sign": K.SIGN_NAMES[start_sign],
                "to_sign": K.SIGN_NAMES[new_sign],
                "jd": when,
                "date": jd_to_utc(when).date().isoformat(),
                "days_away": round(when - jd, 1),
            })
    return sorted(out, key=lambda r: r["jd"])


def alerts(natal_planets: dict[str, dict[str, Any]], jd: float,
           ayanamsa: str = K.DEFAULT_AYANAMSA) -> list[dict[str, Any]]:
    """Notable upcoming shifts, phrased relative to the natal Moon."""
    if "Moon" not in natal_planets:
        return []
    moon_sign = natal_planets["Moon"]["sign"]
    out = []

    for ing in next_ingresses(jd, ["Jupiter", "Saturn", "Rahu", "Ketu"],
                              ayanamsa=ayanamsa):
        to_sign_idx = K.SIGN_NAMES.index(ing["to_sign"])
        house = K.house_distance(moon_sign, to_sign_idx)
        severity = "info"
        if ing["planet"] == "Saturn" and house in (12, 1, 2):
            severity = "major"
        elif ing["planet"] == "Saturn" and house in (4, 8):
            severity = "notable"
        elif ing["planet"] == "Jupiter" and house in (2, 5, 9, 11):
            severity = "favourable"

        message = (f"{ing['planet']} enters {ing['to_sign']} on {ing['date']}, "
                   f"the {_ord(house)} house from your natal Moon -- "
                   f"{GOCHAR_NOTES.get(house, '')}.")
        if ing["planet"] == "Saturn" and house == 12:
            message += " This begins Sade Sati."
        if ing["planet"] == "Saturn" and house == 2:
            message += " This is the closing phase of Sade Sati."

        out.append({**ing, "house_from_moon": house,
                    "severity": severity, "message": message})
    return out


def _ord(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")
