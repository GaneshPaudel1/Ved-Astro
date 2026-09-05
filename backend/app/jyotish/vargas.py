"""Shodasavarga -- the classical sixteen divisional charts.

Each varga slices a 30-degree sign into D parts and maps each part to a sign by
its own rule. The rules genuinely differ from one another; there is no single
formula that produces all sixteen, so each is written out explicitly and can be
checked against Brihat Parashara Hora Shastra line by line.
"""
from __future__ import annotations

from typing import Any, Callable

from . import constants as K

# Movable = 0, Fixed = 1, Dual = 2
_MOVABLE, _FIXED, _DUAL = 0, 1, 2


def _modality(sign: int) -> int:
    return sign % 3


def _element(sign: int) -> int:
    """0 fire, 1 earth, 2 air, 3 water."""
    return sign % 4


def _odd(sign: int) -> bool:
    return sign % 2 == 0        # 0-indexed Aries is the 1st, an odd sign


# --------------------------------------------------------------------------
# Individual varga rules. Each takes (rashi, degrees-in-sign) -> varga sign.
# --------------------------------------------------------------------------
def _d1(sign: int, deg: float) -> int:
    return sign


def _d2_hora(sign: int, deg: float) -> int:
    """Hora (wealth). Sun's hora is Leo, Moon's is Cancer."""
    first_half = deg < 15.0
    if _odd(sign):
        return 4 if first_half else 3       # Leo then Cancer
    return 3 if first_half else 4           # Cancer then Leo


def _d3_drekkana(sign: int, deg: float) -> int:
    """Drekkana (siblings). 1st third the sign itself, then its trines."""
    part = int(deg / 10.0)
    return (sign + 4 * part) % 12


def _d4_chaturthamsha(sign: int, deg: float) -> int:
    """Chaturthamsha (property). The sign and its kendras."""
    part = int(deg / 7.5)
    return (sign + 3 * part) % 12


def _d7_saptamsha(sign: int, deg: float) -> int:
    """Saptamsha (children). Odd signs from themselves, even from the 7th."""
    part = int(deg * 7 / 30.0)
    start = sign if _odd(sign) else (sign + 6) % 12
    return (start + part) % 12


def _d9_navamsha(sign: int, deg: float) -> int:
    """Navamsha (spouse, dharma, and the varga that confirms every reading).

    Movable signs start from themselves, fixed from the 9th, dual from the 5th
    -- which the compact form (rashi * 9 + part) reproduces exactly.
    """
    part = int(deg * 9 / 30.0)
    return (sign * 9 + part) % 12


def _d10_dashamsha(sign: int, deg: float) -> int:
    """Dashamsha (career). Odd signs from themselves, even from the 9th."""
    part = int(deg / 3.0)
    start = sign if _odd(sign) else (sign + 8) % 12
    return (start + part) % 12


def _d12_dwadashamsha(sign: int, deg: float) -> int:
    """Dwadashamsha (parents). Always from the sign itself."""
    part = int(deg / 2.5)
    return (sign + part) % 12


def _d16_shodashamsha(sign: int, deg: float) -> int:
    """Shodashamsha (vehicles, comforts)."""
    part = int(deg * 16 / 30.0)
    start = {_MOVABLE: 0, _FIXED: 4, _DUAL: 8}[_modality(sign)]
    return (start + part) % 12


def _d20_vimshamsha(sign: int, deg: float) -> int:
    """Vimshamsha (spiritual practice)."""
    part = int(deg * 20 / 30.0)
    start = {_MOVABLE: 0, _FIXED: 8, _DUAL: 4}[_modality(sign)]
    return (start + part) % 12


def _d24_chaturvimshamsha(sign: int, deg: float) -> int:
    """Chaturvimshamsha (learning). Odd from Leo, even from Cancer."""
    part = int(deg * 24 / 30.0)
    start = 4 if _odd(sign) else 3
    return (start + part) % 12


def _d27_bhamsha(sign: int, deg: float) -> int:
    """Bhamsha / Nakshatramsha (innate strength). Starts by element."""
    part = int(deg * 27 / 30.0)
    start = {0: 0, 1: 3, 2: 6, 3: 9}[_element(sign)]
    return (start + part) % 12


# Trimshamsha is the one varga with unequal divisions.
# (upper degree bound, sign ruled by that planet)
_D30_ODD = [(5.0, 0), (10.0, 10), (18.0, 8), (25.0, 2), (30.0, 6)]
#            Mars      Saturn      Jupiter    Mercury   Venus
_D30_EVEN = [(5.0, 1), (12.0, 5), (20.0, 11), (25.0, 9), (30.0, 7)]
#             Venus     Mercury    Jupiter     Saturn    Mars


def _d30_trimshamsha(sign: int, deg: float) -> int:
    """Trimshamsha (misfortune, character). Unequal 5/5/8/7/5 divisions."""
    table = _D30_ODD if _odd(sign) else _D30_EVEN
    for bound, result in table:
        if deg < bound:
            return result
    return table[-1][1]


def _d40_khavedamsha(sign: int, deg: float) -> int:
    """Khavedamsha (maternal legacy). Odd from Aries, even from Libra."""
    part = int(deg * 40 / 30.0)
    start = 0 if _odd(sign) else 6
    return (start + part) % 12


def _d45_akshavedamsha(sign: int, deg: float) -> int:
    """Akshavedamsha (paternal legacy, general character)."""
    part = int(deg * 45 / 30.0)
    start = {_MOVABLE: 0, _FIXED: 4, _DUAL: 8}[_modality(sign)]
    return (start + part) % 12


def _d60_shashtiamsha(sign: int, deg: float) -> int:
    """Shashtiamsha (the finest division; past-life indications)."""
    part = int(deg * 2)          # 0..59
    return (sign + part) % 12


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------
VargaRule = Callable[[int, float], int]

VARGAS: dict[str, dict[str, Any]] = {
    "D1":  {"name": "Rashi",             "divisions": 1,  "signifies": "The body and the whole life",        "fn": _d1},
    "D2":  {"name": "Hora",              "divisions": 2,  "signifies": "Wealth and resources",               "fn": _d2_hora},
    "D3":  {"name": "Drekkana",          "divisions": 3,  "signifies": "Siblings, courage, initiative",      "fn": _d3_drekkana},
    "D4":  {"name": "Chaturthamsha",     "divisions": 4,  "signifies": "Home, land, fixed assets",           "fn": _d4_chaturthamsha},
    "D7":  {"name": "Saptamsha",         "divisions": 7,  "signifies": "Children and creative issue",        "fn": _d7_saptamsha},
    "D9":  {"name": "Navamsha",          "divisions": 9,  "signifies": "Marriage, dharma, inner strength",   "fn": _d9_navamsha},
    "D10": {"name": "Dashamsha",         "divisions": 10, "signifies": "Career and public action",           "fn": _d10_dashamsha},
    "D12": {"name": "Dwadashamsha",      "divisions": 12, "signifies": "Parents and ancestry",               "fn": _d12_dwadashamsha},
    "D16": {"name": "Shodashamsha",      "divisions": 16, "signifies": "Vehicles, comforts, contentment",    "fn": _d16_shodashamsha},
    "D20": {"name": "Vimshamsha",        "divisions": 20, "signifies": "Spiritual practice and devotion",    "fn": _d20_vimshamsha},
    "D24": {"name": "Chaturvimshamsha",  "divisions": 24, "signifies": "Learning and formal education",      "fn": _d24_chaturvimshamsha},
    "D27": {"name": "Bhamsha",           "divisions": 27, "signifies": "Innate strengths and weaknesses",    "fn": _d27_bhamsha},
    "D30": {"name": "Trimshamsha",       "divisions": 30, "signifies": "Misfortune, hardship, character",    "fn": _d30_trimshamsha},
    "D40": {"name": "Khavedamsha",       "divisions": 40, "signifies": "Maternal legacy and auspiciousness", "fn": _d40_khavedamsha},
    "D45": {"name": "Akshavedamsha",     "divisions": 45, "signifies": "Paternal legacy and conduct",        "fn": _d45_akshavedamsha},
    "D60": {"name": "Shashtiamsha",      "divisions": 60, "signifies": "Past-life merit; the finest detail", "fn": _d60_shashtiamsha},
}

VARGA_ORDER = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
               "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]

# The Shadvarga / Saptavarga groups used for Vimshopaka strength.
SHADVARGA = ["D1", "D2", "D3", "D9", "D12", "D30"]


def varga_sign(longitude: float, varga: str) -> int:
    """Sign a longitude falls into within the given divisional chart."""
    rule = VARGAS[varga]["fn"]
    return rule(K.sign_of(longitude), K.deg_in_sign(longitude))


def compute_varga(chart_planets: dict[str, dict[str, Any]],
                  ascendant: float | None,
                  varga: str) -> dict[str, Any]:
    """Project a natal chart into one divisional chart.

    Houses in a varga are counted whole-sign from the varga ascendant, which is
    the standard way these charts are read.
    """
    meta = VARGAS[varga]
    asc_sign = varga_sign(ascendant, varga) if ascendant is not None else None

    planets: dict[str, dict[str, Any]] = {}
    for name, p in chart_planets.items():
        sign = varga_sign(p["longitude"], varga)
        planets[name] = {
            "name": name,
            "sign": sign,
            "sign_name": K.SIGN_NAMES[sign],
            "house": K.house_distance(asc_sign, sign) if asc_sign is not None else 0,
            "abbr": p["abbr"],
            "retrograde": p["retrograde"],
            # Dignity is re-evaluated in the varga; the degree is not carried
            # across, so only sign-level dignity is meaningful here.
            "dignity": _varga_dignity(name, sign),
            "vargottama": varga != "D1" and sign == p["sign"],
        }

    houses = []
    if asc_sign is not None:
        for i in range(12):
            s = (asc_sign + i) % 12
            houses.append({
                "number": i + 1,
                "sign": s,
                "sign_name": K.SIGN_NAMES[s],
                "lord": K.SIGN_LORDS[s],
                "planets": [n for n, pp in planets.items() if pp["sign"] == s],
            })

    return {
        "varga": varga,
        "name": meta["name"],
        "divisions": meta["divisions"],
        "signifies": meta["signifies"],
        "ascendant_sign": asc_sign,
        "ascendant_sign_name": K.SIGN_NAMES[asc_sign] if asc_sign is not None else None,
        "planets": planets,
        "houses": houses,
    }


def _varga_dignity(planet: str, sign: int) -> str:
    ex = K.EXALTATION.get(planet)
    if ex and ex[0] == sign:
        return "exalted"
    de = K.DEBILITATION.get(planet)
    if de and de[0] == sign:
        return "debilitated"
    if sign in K.PLANET_OWNS.get(planet, []):
        return "own sign"
    lord = K.SIGN_LORDS[sign]
    if lord in K.NATURAL_FRIENDS.get(planet, set()):
        return "friendly sign"
    if lord in K.NATURAL_ENEMIES.get(planet, set()):
        return "enemy sign"
    return "neutral"


def compute_all_vargas(chart_planets: dict[str, dict[str, Any]],
                       ascendant: float | None,
                       which: list[str] | None = None) -> dict[str, Any]:
    names = which or VARGA_ORDER
    return {v: compute_varga(chart_planets, ascendant, v) for v in names}


def vargottama_planets(chart_planets: dict[str, dict[str, Any]]) -> list[str]:
    """Planets holding the same sign in D1 and D9 -- a notable strength."""
    return [n for n, p in chart_planets.items()
            if varga_sign(p["longitude"], "D9") == p["sign"]]


def varga_strength(chart_planets: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Count, per planet, how many of the sixteen vargas it sits well in.

    A rough but genuinely useful summary: a planet strong across many vargas
    delivers its results more reliably than one strong only in the rashi chart.
    """
    out: dict[str, dict[str, Any]] = {}
    # Moolatrikona is deliberately absent: it is defined by a degree range, and
    # a varga placement only carries a sign. _varga_dignity never returns it.
    good = {"exalted", "own sign", "friendly sign"}
    for name, p in chart_planets.items():
        tally = {"exalted": 0, "own sign": 0, "friendly sign": 0,
                 "neutral": 0, "enemy sign": 0, "debilitated": 0}
        for v in VARGA_ORDER:
            tally[_varga_dignity(name, varga_sign(p["longitude"], v))] += 1
        score = sum(tally[k] for k in good)
        out[name] = {
            "counts": tally,
            "favourable_vargas": score,
            "total_vargas": len(VARGA_ORDER),
            "vargottama": varga_sign(p["longitude"], "D9") == p["sign"],
        }
    return out


# --------------------------------------------------------------------------
# Nakshatra detail, applied to any placement rather than only the Moon
# --------------------------------------------------------------------------
def nakshatra_detail(longitude: float) -> dict[str, Any]:
    idx = K.nakshatra_of(longitude)
    name, lord, deity, symbol, gana, nadi, yoni, yoni_sex = K.NAKSHATRAS[idx]
    start = idx * K.NAKSHATRA_SPAN
    return {
        "index": idx,
        "number": idx + 1,
        "name": name,
        "lord": lord,
        "deity": deity,
        "symbol": symbol,
        "gana": gana,
        "nadi": nadi,
        "yoni": yoni,
        "yoni_sex": yoni_sex,
        "pada": K.pada_of(longitude),
        "span_start": round(start, 4),
        "span_end": round(start + K.NAKSHATRA_SPAN, 4),
        "degrees_traversed": round(K.norm360(longitude) - start, 4),
        "percent_through": round(
            (K.norm360(longitude) - start) / K.NAKSHATRA_SPAN * 100, 2),
    }
