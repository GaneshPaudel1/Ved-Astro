"""Ashtakavarga -- the bindu (point) system.

Each of the seven visible planets is scored across the twelve signs. Eight
contributors vote: the seven planets and the lagna. A contributor gives a bindu
to the signs that fall at certain house-distances from where it sits, and each
planet has its own table of which distances count.

The tables below are the classical Parashari ones. Their row totals are fixed
and well known -- Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56, Venus 52,
Saturn 39, summing to 337 in the Sarvashtakavarga -- which makes them
self-checking. The tests assert exactly those numbers.
"""
from __future__ import annotations

from typing import Any

from . import constants as K

CONTRIBUTORS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Ascendant"]
BAV_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# BENEFIC_PLACES[planet][contributor] = houses (1-12) counted from the
# contributor's own sign in which `planet` receives a bindu.
BENEFIC_PLACES: dict[str, dict[str, list[int]]] = {
    "Sun": {
        "Sun":       [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":      [3, 6, 10, 11],
        "Mars":      [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury":   [3, 5, 6, 9, 10, 11, 12],
        "Jupiter":   [5, 6, 9, 11],
        "Venus":     [6, 7, 12],
        "Saturn":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun":       [3, 6, 7, 8, 10, 11],
        "Moon":      [1, 3, 6, 7, 10, 11],
        "Mars":      [2, 3, 5, 6, 9, 10, 11],
        "Mercury":   [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter":   [1, 4, 7, 8, 10, 11, 12],
        "Venus":     [3, 4, 5, 7, 9, 10, 11],
        "Saturn":    [3, 5, 6, 11],
        "Ascendant": [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":       [3, 5, 6, 10, 11],
        "Moon":      [3, 6, 11],
        "Mars":      [1, 2, 4, 7, 8, 10, 11],
        "Mercury":   [3, 5, 6, 11],
        "Jupiter":   [6, 10, 11, 12],
        "Venus":     [6, 8, 11, 12],
        "Saturn":    [1, 4, 7, 8, 9, 10, 11],
        "Ascendant": [1, 3, 6, 10, 11],
    },
    "Mercury": {
        "Sun":       [5, 6, 9, 11, 12],
        "Moon":      [2, 4, 6, 8, 10, 11],
        "Mars":      [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury":   [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter":   [6, 8, 11, 12],
        "Venus":     [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Ascendant": [1, 2, 4, 6, 8, 10, 11],
    },
    "Jupiter": {
        "Sun":       [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon":      [2, 5, 7, 9, 11],
        "Mars":      [1, 2, 4, 7, 8, 10, 11],
        "Mercury":   [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter":   [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus":     [2, 5, 6, 9, 10, 11],
        "Saturn":    [3, 5, 6, 12],
        "Ascendant": [1, 2, 4, 5, 6, 7, 9, 10, 11],
    },
    "Venus": {
        "Sun":       [8, 11, 12],
        "Moon":      [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars":      [3, 5, 6, 9, 11, 12],
        "Mercury":   [3, 5, 6, 9, 11],
        "Jupiter":   [5, 8, 9, 10, 11],
        "Venus":     [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn":    [3, 4, 5, 8, 9, 10, 11],
        "Ascendant": [1, 2, 3, 4, 5, 8, 9, 11],
    },
    "Saturn": {
        "Sun":       [1, 2, 4, 7, 8, 10, 11],
        "Moon":      [3, 6, 11],
        "Mars":      [3, 5, 6, 10, 11, 12],
        "Mercury":   [6, 8, 9, 10, 11, 12],
        "Jupiter":   [5, 6, 11, 12],
        "Venus":     [6, 11, 12],
        "Saturn":    [3, 5, 6, 11],
        "Ascendant": [1, 3, 4, 6, 10, 11],
    },
}

# Published row totals, used as an integrity check on the tables above.
EXPECTED_BAV_TOTALS = {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54,
                       "Jupiter": 56, "Venus": 52, "Saturn": 39}
EXPECTED_SAV_TOTAL = 337


def table_totals() -> dict[str, int]:
    """Sum each planet's table. Should reproduce EXPECTED_BAV_TOTALS exactly."""
    return {p: sum(len(v) for v in rows.values())
            for p, rows in BENEFIC_PLACES.items()}


def bhinnashtakavarga(planet: str, positions: dict[str, int]) -> list[int]:
    """Bindus for one planet across the twelve signs.

    ``positions`` maps each contributor (including "Ascendant") to its 0-indexed
    sign. Returns a 12-item list indexed by sign, Aries first.
    """
    bindus = [0] * 12
    for contributor, houses in BENEFIC_PLACES[planet].items():
        base = positions.get(contributor)
        if base is None:
            continue
        for h in houses:
            bindus[(base + h - 1) % 12] += 1
    return bindus


def compute(planets: dict[str, dict[str, Any]],
            ascendant_sign: int | None) -> dict[str, Any]:
    """Full Bhinnashtakavarga set plus the Sarvashtakavarga totals."""
    positions = {name: planets[name]["sign"] for name in BAV_PLANETS if name in planets}
    if ascendant_sign is not None:
        positions["Ascendant"] = ascendant_sign

    bav: dict[str, list[int]] = {}
    for planet in BAV_PLANETS:
        bav[planet] = bhinnashtakavarga(planet, positions)

    sav = [sum(bav[p][s] for p in BAV_PLANETS) for s in range(12)]

    signs = []
    for s in range(12):
        signs.append({
            "sign": s,
            "sign_name": K.SIGN_NAMES[s],
            "sign_sanskrit": K.SIGN_SANSKRIT[s],
            "house": (K.house_distance(ascendant_sign, s)
                      if ascendant_sign is not None else 0),
            "sav": sav[s],
            "bav": {p: bav[p][s] for p in BAV_PLANETS},
            # 28 is the neutral SAV value (337/12 rounds to 28).
            "strength": _sav_band(sav[s]),
        })

    return {
        "bav": bav,
        "sav": sav,
        "sav_total": sum(sav),
        "bav_totals": {p: sum(v) for p, v in bav.items()},
        "signs": signs,
        "ascendant_sign": ascendant_sign,
        "strongest_sign": max(range(12), key=lambda s: sav[s]),
        "weakest_sign": min(range(12), key=lambda s: sav[s]),
        "note": ("A sign with 30 or more bindus supports the matters of its "
                 "house; under 25 asks for more effort there. The twelve "
                 "always total 337."),
    }


def _sav_band(value: int) -> str:
    if value >= 33:
        return "very strong"
    if value >= 30:
        return "strong"
    if value >= 25:
        return "moderate"
    if value >= 20:
        return "weak"
    return "very weak"


def transit_bindus(ashtakavarga: dict[str, Any], planet: str, sign: int) -> int:
    """Bindus a transiting planet has in the sign it is passing through.

    Used by the transit view: a planet crossing a sign where it holds 5 or more
    of its own bindus tends to deliver its results more smoothly.
    """
    if planet not in ashtakavarga["bav"]:
        return 0
    return ashtakavarga["bav"][planet][sign % 12]
