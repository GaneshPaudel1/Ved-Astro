"""The calculation core: sidereal planetary positions, lagna, and houses.

Everything here goes through the Swiss Ephemeris. There is no hand-rolled
orbital mechanics anywhere in this project, by design.

Two things separate this from a tropical (Western) engine, and both are the
usual source of wrong Vedic charts:

1. Every longitude is *sidereal* -- FLG_SIDEREAL is set on every call, and the
   ayanamsa mode is set before each calculation batch.
2. Houses default to *whole sign* (the classical Vedic bhava), not Placidus.
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field, asdict
from typing import Any

import swisseph as swe

from . import constants as K
from .timeutil import BirthMoment

# --------------------------------------------------------------------------
# Ephemeris setup
# --------------------------------------------------------------------------
_EPHE_DIR = os.environ.get(
    "SWISSEPH_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "ephe"),
)
if os.path.isdir(_EPHE_DIR):
    swe.set_ephe_path(_EPHE_DIR)

# swisseph global state (sidereal mode) is process-wide, so guard mutations.
_swe_lock = threading.RLock()

SWE_PLANET_IDS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}

HOUSE_SYSTEMS = {
    "whole_sign": b"W",
    "placidus": b"P",
    "koch": b"K",
    "equal": b"A",
    "sripati": b"O",   # Porphyry; Sripati is derived from it
}


def ephemeris_backend(jd: float = 2451545.0) -> dict[str, Any]:
    """Report which ephemeris actually served the request.

    Swiss Ephemeris silently falls back to its built-in Moshier theory when the
    compressed .se1 data files are absent. Silent fallbacks are how accuracy
    claims become untrue, so we surface it instead.
    """
    with _swe_lock:
        _, retflag = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    if retflag & swe.FLG_JPLEPH:
        kind, detail = "JPL", "JPL DE ephemeris files"
    elif retflag & swe.FLG_MOSEPH:
        kind, detail = ("Moshier",
                        "Built-in analytical theory. Sub-arcsecond for 1800-2400 "
                        "and far finer than astrological resolution, but the .se1 "
                        "data files give wider date coverage.")
    else:
        kind, detail = "Swiss", "Compressed Swiss Ephemeris .se1 files"
    return {"backend": kind, "detail": detail,
            "ephe_path": _EPHE_DIR if os.path.isdir(_EPHE_DIR) else None,
            "swe_version": swe.version}


def _set_ayanamsa(key: str) -> None:
    opt = K.AYANAMSA_OPTIONS.get(key) or K.AYANAMSA_OPTIONS[K.DEFAULT_AYANAMSA]
    swe.set_sid_mode(opt["swe_id"], 0, 0)


def ayanamsa_value(jd: float, ayanamsa: str = K.DEFAULT_AYANAMSA) -> float:
    with _swe_lock:
        _set_ayanamsa(ayanamsa)
        return swe.get_ayanamsa_ut(jd)


# --------------------------------------------------------------------------
# Result types
# --------------------------------------------------------------------------
@dataclass
class PlanetPosition:
    name: str
    sanskrit: str
    longitude: float           # sidereal, 0-360
    latitude: float
    speed: float               # degrees/day in longitude
    sign: int                  # 0-indexed rashi
    sign_name: str
    degree_in_sign: float
    degree_str: str
    nakshatra: int             # 0-indexed
    nakshatra_name: str
    nakshatra_lord: str
    pada: int
    house: int                 # 1-12, whole-sign from lagna
    retrograde: bool
    combust: bool
    dignity: str               # exalted / debilitated / own / moolatrikona / ...
    is_benefic: bool
    abbr: str
    glyph: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Chart:
    moment: dict[str, Any]
    ayanamsa: str
    ayanamsa_label: str
    ayanamsa_value: float
    ayanamsa_str: str
    house_system: str
    ascendant: float | None
    ascendant_sign: int | None
    # Whole-sign cusps all sit at 0 degrees, so the lagna's true degree has to
    # be reported separately or the UI will claim every ascendant is exact.
    ascendant_sign_name: str | None = None
    ascendant_degree_str: str | None = None
    ascendant_nakshatra: str | None = None
    ascendant_pada: int | None = None
    ascendant_lord: str | None = None
    houses: list[dict[str, Any]] = field(default_factory=list)
    planets: dict[str, dict[str, Any]] = field(default_factory=dict)
    time_known: bool = True
    warnings: list[str] = field(default_factory=list)
    engine: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------------
# Dignity
# --------------------------------------------------------------------------
def dignity_of(planet: str, sign: int, deg: float) -> str:
    ex = K.EXALTATION.get(planet)
    if ex and ex[0] == sign:
        return "exalted"
    de = K.DEBILITATION.get(planet)
    if de and de[0] == sign:
        return "debilitated"
    mt = K.MOOLATRIKONA.get(planet)
    if mt and mt[0] == sign and mt[1] <= deg < mt[2]:
        return "moolatrikona"
    if sign in K.PLANET_OWNS.get(planet, []):
        return "own sign"
    lord = K.SIGN_LORDS[sign]
    if lord in K.NATURAL_FRIENDS.get(planet, set()):
        return "friendly sign"
    if lord in K.NATURAL_ENEMIES.get(planet, set()):
        return "enemy sign"
    return "neutral"


def _is_combust(planet: str, lon: float, sun_lon: float, retro: bool) -> bool:
    if planet not in K.COMBUSTION_ORB:
        return False
    orb = K.COMBUSTION_ORB[planet]
    if retro and planet in K.COMBUSTION_ORB_RETRO:
        orb = K.COMBUSTION_ORB_RETRO[planet]
    sep = abs(((lon - sun_lon + 180) % 360) - 180)
    return sep <= orb


# --------------------------------------------------------------------------
# Raw longitudes -- the primitive every other module builds on
# --------------------------------------------------------------------------
def sidereal_longitudes(jd: float, ayanamsa: str = K.DEFAULT_AYANAMSA,
                        node_type: str = "mean") -> dict[str, tuple[float, float, float]]:
    """Return {planet: (longitude, latitude, speed)} in the sidereal zodiac."""
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
    out: dict[str, tuple[float, float, float]] = {}
    with _swe_lock:
        _set_ayanamsa(ayanamsa)
        for name, pid in SWE_PLANET_IDS.items():
            vals, _ = swe.calc_ut(jd, pid, flags)
            out[name] = (K.norm360(vals[0]), vals[1], vals[3])

        node_id = swe.TRUE_NODE if node_type == "true" else swe.MEAN_NODE
        vals, _ = swe.calc_ut(jd, node_id, flags)
        rahu = K.norm360(vals[0])
        out["Rahu"] = (rahu, vals[1], vals[3])
        out["Ketu"] = (K.norm360(rahu + 180.0), -vals[1], vals[3])
    return out


def ascendant_and_houses(jd: float, lat: float, lon: float,
                         ayanamsa: str = K.DEFAULT_AYANAMSA,
                         house_system: str = "whole_sign"
                         ) -> tuple[float, list[float], list[str]]:
    """Return (ascendant, 12 cusp longitudes, warnings), all sidereal.

    Placidus and Koch are undefined above the polar circles. Swiss Ephemeris
    substitutes Porphyry there; we pass that substitution on as a warning rather
    than letting the chart imply a precision it does not have.
    """
    warnings: list[str] = []
    hsys = HOUSE_SYSTEMS.get(house_system, b"W")
    if abs(lat) > 66.0 and hsys in (b"P", b"K"):
        warnings.append(
            f"{house_system.title()} houses are undefined above the polar circle "
            f"(latitude {lat:.2f}). Swiss Ephemeris substituted Porphyry cusps.")

    with _swe_lock:
        _set_ayanamsa(ayanamsa)
        try:
            cusps, ascmc = swe.houses_ex(jd, lat, lon, hsys, swe.FLG_SIDEREAL)
        except swe.Error:
            # Placidus/Koch genuinely fail this far north rather than degrading.
            # Whole sign is always defined, so fall back and say so.
            warnings.append(
                f"{house_system.title()} houses could not be computed at latitude "
                f"{lat:.2f}. Fell back to whole-sign houses.")
            hsys = b"W"
            cusps, ascmc = swe.houses_ex(jd, lat, lon, hsys, swe.FLG_SIDEREAL)

    asc = K.norm360(ascmc[0])
    cusp_list = [K.norm360(c) for c in cusps[:12]]

    if hsys == b"W":
        # Whole sign: the lagna's sign *is* the 1st house, starting at 0 degrees.
        start = K.sign_of(asc) * 30.0
        cusp_list = [K.norm360(start + 30.0 * i) for i in range(12)]
    return asc, cusp_list, warnings


# --------------------------------------------------------------------------
# Full chart
# --------------------------------------------------------------------------
def compute_chart(moment: BirthMoment, ayanamsa: str = K.DEFAULT_AYANAMSA,
                  house_system: str = "whole_sign",
                  node_type: str = "mean") -> Chart:
    jd = moment.jd_ut
    warnings: list[str] = list(moment.notes)

    ay_val = ayanamsa_value(jd, ayanamsa)
    lons = sidereal_longitudes(jd, ayanamsa, node_type)

    asc: float | None = None
    asc_sign: int | None = None
    cusps: list[float] = []

    if moment.time_known:
        asc, cusps, hw = ascendant_and_houses(
            jd, moment.latitude, moment.longitude, ayanamsa, house_system)
        asc_sign = K.sign_of(asc)
        warnings.extend(hw)
    else:
        warnings.append(
            "Birth time unknown. The lagna, house placements and every "
            "ascendant-dependent reading are suppressed. Positions are computed "
            "for 12:00 local time, so the Moon may be off by up to about 6 degrees.")

    sun_lon = lons["Sun"][0]
    planets: dict[str, dict[str, Any]] = {}

    for name in K.PLANETS:
        lon_val, lat_val, speed = lons[name]
        sign = K.sign_of(lon_val)
        d_in_sign = K.deg_in_sign(lon_val)
        nak = K.nakshatra_of(lon_val)
        # Rahu and Ketu are always retrograde by convention; their computed
        # speed is negative anyway for the mean node, but be explicit.
        retro = True if name in ("Rahu", "Ketu") else speed < 0

        house = 0
        if asc_sign is not None:
            house = K.house_distance(asc_sign, sign)

        planets[name] = PlanetPosition(
            name=name,
            sanskrit=K.PLANET_SANSKRIT[name],
            longitude=round(lon_val, 6),
            latitude=round(lat_val, 6),
            speed=round(speed, 6),
            sign=sign,
            sign_name=K.SIGN_NAMES[sign],
            degree_in_sign=round(d_in_sign, 6),
            degree_str=K.format_dms(d_in_sign),
            nakshatra=nak,
            nakshatra_name=K.NAKSHATRA_NAMES[nak],
            nakshatra_lord=K.NAKSHATRAS[nak][1],
            pada=K.pada_of(lon_val),
            house=house,
            retrograde=retro,
            combust=_is_combust(name, lon_val, sun_lon, retro),
            dignity=dignity_of(name, sign, d_in_sign),
            is_benefic=name in K.NATURAL_BENEFICS,
            abbr=K.PLANET_ABBR[name],
            glyph=K.PLANET_GLYPH[name],
        ).to_dict()

    houses: list[dict[str, Any]] = []
    if asc_sign is not None:
        for i in range(12):
            sign = (asc_sign + i) % 12 if house_system == "whole_sign" else K.sign_of(cusps[i])
            houses.append({
                "number": i + 1,
                "cusp": round(cusps[i], 6),
                "sign": sign,
                "sign_name": K.SIGN_NAMES[sign],
                "sign_sanskrit": K.SIGN_SANSKRIT[sign],
                "lord": K.SIGN_LORDS[sign],
                "degree_str": K.format_dms(K.deg_in_sign(cusps[i])),
                "meaning": K.HOUSE_MEANINGS[i],
                "planets": [p for p in K.PLANETS if planets[p]["house"] == i + 1],
            })

    opt = K.AYANAMSA_OPTIONS.get(ayanamsa, K.AYANAMSA_OPTIONS[K.DEFAULT_AYANAMSA])
    return Chart(
        moment={
            "jd_ut": moment.jd_ut,
            "utc": moment.utc.isoformat(),
            "local": moment.local.isoformat(),
            "latitude": moment.latitude,
            "longitude": moment.longitude,
            "tz_name": moment.tz_name,
            "utc_offset_hours": moment.utc_offset_hours,
            "utc_offset_label": moment.offset_label,
            "tz_abbrev": moment.tz_abbrev,
            "time_standard": moment.time_standard,
        },
        ayanamsa=ayanamsa,
        ayanamsa_label=opt["label"],
        ayanamsa_value=round(ay_val, 6),
        ayanamsa_str=K.format_dms(ay_val),
        house_system=house_system,
        ascendant=round(asc, 6) if asc is not None else None,
        ascendant_sign=asc_sign,
        ascendant_sign_name=K.SIGN_NAMES[asc_sign] if asc_sign is not None else None,
        ascendant_degree_str=K.format_dms(K.deg_in_sign(asc)) if asc is not None else None,
        ascendant_nakshatra=(K.NAKSHATRA_NAMES[K.nakshatra_of(asc)]
                             if asc is not None else None),
        ascendant_pada=K.pada_of(asc) if asc is not None else None,
        ascendant_lord=K.SIGN_LORDS[asc_sign] if asc_sign is not None else None,
        houses=houses,
        planets=planets,
        time_known=moment.time_known,
        warnings=warnings,
        engine=ephemeris_backend(jd),
    )


# --------------------------------------------------------------------------
# Aspects (graha drishti) -- sign-based, the classical Parashari model
# --------------------------------------------------------------------------
def aspects(planets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Which planet casts drishti on which house-from-itself.

    Every graha aspects the 7th from itself. Mars adds the 4th and 8th, Jupiter
    the 5th and 9th, Saturn the 3rd and 10th; the nodes are given Jupiter's.
    """
    out: list[dict[str, Any]] = []
    for name, p in planets.items():
        targets = [7] + K.SPECIAL_ASPECTS.get(name, [])
        for t in sorted(set(targets)):
            target_sign = (p["sign"] + t - 1) % 12
            out.append({
                "planet": name,
                "aspect_number": t,
                "from_sign": p["sign"],
                "target_sign": target_sign,
                "target_sign_name": K.SIGN_NAMES[target_sign],
                "special": t != 7,
            })
    return out
