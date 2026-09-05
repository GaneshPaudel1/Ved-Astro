"""Panchang -- the five limbs of the Vedic calendar, plus the day's timings.

Tithi, Vara, Nakshatra, Yoga and Karana all derive from two numbers: the
sidereal longitudes of the Sun and Moon. Each limb is a band of that angle, so
finding when one ends means solving for the moment the angle next crosses a
multiple -- done here by bracketing and bisection against the real ephemeris
rather than by assuming the Moon moves at a constant rate. It does not.

Sunrise uses Swiss Ephemeris's Hindu convention (disc centre, no refraction),
which is what panchang tables are computed against.
"""
from __future__ import annotations

from datetime import date as _date, datetime, timedelta, timezone
from typing import Any

import swisseph as swe

from . import constants as K
from .ephemeris import _set_ayanamsa, _swe_lock
from .timeutil import julian_day, jd_to_utc, timezone_for, utc_offset_at

# --------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima",
]
TITHI_NAMES_KRISHNA = TITHI_NAMES[:14] + ["Amavasya"]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
FIXED_KARANAS = ["Shakuni", "Chatushpada", "Naga", "Kimstughna"]

VARA_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday",
              "Friday", "Saturday"]
VARA_SANSKRIT = ["Ravivara", "Somavara", "Mangalavara", "Budhavara",
                 "Guruvara", "Shukravara", "Shanivara"]
VARA_LORDS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

# Which eighth of the daytime each inauspicious period occupies, by weekday
# index (0 = Sunday). Values are 1-based segment numbers.
RAHU_KAAL_SEGMENT = {0: 8, 1: 2, 2: 7, 3: 5, 4: 6, 5: 4, 6: 3}
YAMAGANDA_SEGMENT = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 7, 6: 6}
GULIKA_SEGMENT = {0: 7, 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1}


# --------------------------------------------------------------------------
# Sun and Moon longitudes
# --------------------------------------------------------------------------
def _sun_moon(jd: float, ayanamsa: str) -> tuple[float, float]:
    with _swe_lock:
        _set_ayanamsa(ayanamsa)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        sun, _ = swe.calc_ut(jd, swe.SUN, flags)
        moon, _ = swe.calc_ut(jd, swe.MOON, flags)
    return K.norm360(sun[0]), K.norm360(moon[0])


def _tithi_angle(jd: float, ayanamsa: str) -> float:
    sun, moon = _sun_moon(jd, ayanamsa)
    return (moon - sun) % 360.0


def _yoga_angle(jd: float, ayanamsa: str) -> float:
    sun, moon = _sun_moon(jd, ayanamsa)
    return (sun + moon) % 360.0


def _moon_longitude(jd: float, ayanamsa: str) -> float:
    return _sun_moon(jd, ayanamsa)[1]


# --------------------------------------------------------------------------
# Boundary solving
# --------------------------------------------------------------------------
def _find_crossing(fn, jd_start: float, target: float, ayanamsa: str,
                   step: float = 0.02, max_days: float = 3.0) -> float | None:
    """First moment after jd_start at which fn(jd) reaches `target` degrees.

    The angle is compared modulo 360 through a signed difference, so the search
    is immune to the wrap at 0/360.
    """
    def delta(jd: float) -> float:
        return ((fn(jd, ayanamsa) - target + 180.0) % 360.0) - 180.0

    jd = jd_start
    prev = delta(jd)
    travelled = 0.0
    while travelled < max_days:
        jd_next = jd + step
        cur = delta(jd_next)
        # A rising angle crossing the target flips the sign from - to +.
        if prev < 0 <= cur and abs(cur - prev) < 180:
            lo, hi = jd, jd_next
            for _ in range(60):
                mid = (lo + hi) / 2.0
                if delta(mid) < 0:
                    lo = mid
                else:
                    hi = mid
            return (lo + hi) / 2.0
        jd, prev = jd_next, cur
        travelled += step
    return None


def _find_moon_nakshatra_end(jd_start: float, ayanamsa: str) -> float | None:
    idx = K.nakshatra_of(_moon_longitude(jd_start, ayanamsa))
    target = ((idx + 1) % 27) * K.NAKSHATRA_SPAN
    return _find_crossing(lambda j, a: _moon_longitude(j, a), jd_start, target, ayanamsa)


# --------------------------------------------------------------------------
# Rise and set
# --------------------------------------------------------------------------
def _rise_set(jd: float, body: int, lat: float, lon: float,
              which: int) -> float | None:
    """Rising or setting time, using the Hindu convention (disc centre, no
    refraction) that panchang tables assume."""
    flags = swe.BIT_HINDU_RISING
    try:
        with _swe_lock:
            res, tret = swe.rise_trans(jd, body, which | flags, (lon, lat, 0.0))
    except swe.Error:
        return None
    if res != 0:
        return None                 # circumpolar: no rise or set that day
    return tret[0]


def sunrise_sunset(jd_midnight: float, lat: float, lon: float) -> dict[str, float | None]:
    return {
        "sunrise": _rise_set(jd_midnight, swe.SUN, lat, lon, swe.CALC_RISE),
        "sunset": _rise_set(jd_midnight, swe.SUN, lat, lon, swe.CALC_SET),
        "moonrise": _rise_set(jd_midnight, swe.MOON, lat, lon, swe.CALC_RISE),
        "moonset": _rise_set(jd_midnight, swe.MOON, lat, lon, swe.CALC_SET),
    }


# --------------------------------------------------------------------------
# The five limbs
# --------------------------------------------------------------------------
def tithi_at(jd: float, ayanamsa: str) -> dict[str, Any]:
    angle = _tithi_angle(jd, ayanamsa)
    index = int(angle / 12.0)                 # 0..29
    paksha = "Shukla" if index < 15 else "Krishna"
    names = TITHI_NAMES if index < 15 else TITHI_NAMES_KRISHNA
    end_jd = _find_crossing(_tithi_angle, jd, ((index + 1) * 12.0) % 360.0, ayanamsa)
    return {
        "index": index + 1,
        "name": names[index % 15],
        "paksha": paksha,
        "paksha_meaning": ("Waxing -- the Moon is filling"
                           if paksha == "Shukla" else
                           "Waning -- the Moon is emptying"),
        "percent_complete": round((angle % 12.0) / 12.0 * 100, 2),
        "ends_jd": end_jd,
        "deity_note": ("Purnima, the full Moon" if index == 14 else
                       "Amavasya, the new Moon" if index == 29 else None),
    }


def nakshatra_at(jd: float, ayanamsa: str) -> dict[str, Any]:
    moon = _moon_longitude(jd, ayanamsa)
    idx = K.nakshatra_of(moon)
    name, lord, deity, symbol, gana, nadi, yoni, _ = K.NAKSHATRAS[idx]
    return {
        "index": idx + 1,
        "name": name,
        "lord": lord,
        "deity": deity,
        "symbol": symbol,
        "gana": gana,
        "nadi": nadi,
        "yoni": yoni,
        "pada": K.pada_of(moon),
        "percent_complete": round(
            (K.norm360(moon) - idx * K.NAKSHATRA_SPAN) / K.NAKSHATRA_SPAN * 100, 2),
        "ends_jd": _find_moon_nakshatra_end(jd, ayanamsa),
    }


def yoga_at(jd: float, ayanamsa: str) -> dict[str, Any]:
    angle = _yoga_angle(jd, ayanamsa)
    idx = int(angle / K.NAKSHATRA_SPAN)
    end_jd = _find_crossing(_yoga_angle, jd,
                            ((idx + 1) % 27) * K.NAKSHATRA_SPAN, ayanamsa)
    return {
        "index": idx + 1,
        "name": YOGA_NAMES[idx % 27],
        "percent_complete": round(
            (angle % K.NAKSHATRA_SPAN) / K.NAKSHATRA_SPAN * 100, 2),
        "ends_jd": end_jd,
        "inauspicious": YOGA_NAMES[idx % 27] in ("Vyatipata", "Vaidhriti",
                                                 "Parigha", "Vyaghata", "Atiganda"),
    }


def karana_at(jd: float, ayanamsa: str) -> dict[str, Any]:
    angle = _tithi_angle(jd, ayanamsa)
    idx = int(angle / 6.0)                    # 0..59, two per tithi
    name = _karana_name(idx)
    end_jd = _find_crossing(_tithi_angle, jd, ((idx + 1) * 6.0) % 360.0, ayanamsa)
    return {
        "index": idx + 1,
        "name": name,
        "type": "fixed" if name in FIXED_KARANAS else "movable",
        "percent_complete": round((angle % 6.0) / 6.0 * 100, 2),
        "ends_jd": end_jd,
        "inauspicious": name == "Vishti",
        "note": ("Vishti (Bhadra) is traditionally avoided for beginning "
                 "anything important." if name == "Vishti" else None),
    }


def _karana_name(idx: int) -> str:
    """Karana 1 is Kimstughna, then seven movable karanas repeat eight times,
    then the three remaining fixed karanas close the lunar month."""
    if idx == 0:
        return "Kimstughna"
    if idx <= 56:
        return MOVABLE_KARANAS[(idx - 1) % 7]
    return FIXED_KARANAS[idx - 57]


# --------------------------------------------------------------------------
# Inauspicious and auspicious periods
# --------------------------------------------------------------------------
def _segment(sunrise: float, sunset: float, number: int) -> tuple[float, float]:
    """The nth eighth of the daytime, 1-based."""
    length = (sunset - sunrise) / 8.0
    start = sunrise + (number - 1) * length
    return start, start + length


def day_periods(sunrise: float | None, sunset: float | None,
                weekday: int) -> dict[str, Any]:
    """Rahu Kaal, Yamaganda, Gulika and Abhijit, all measured from sunrise."""
    if sunrise is None or sunset is None:
        return {"available": False,
                "reason": "The Sun does not rise or set here on this date."}

    rahu = _segment(sunrise, sunset, RAHU_KAAL_SEGMENT[weekday])
    yama = _segment(sunrise, sunset, YAMAGANDA_SEGMENT[weekday])
    gulika = _segment(sunrise, sunset, GULIKA_SEGMENT[weekday])

    # Abhijit is the 8th of fifteen muhurtas, straddling solar noon.
    day_len = sunset - sunrise
    muhurta = day_len / 15.0
    abhijit = (sunrise + 7 * muhurta, sunrise + 8 * muhurta)

    return {
        "available": True,
        "rahu_kaal": {"start_jd": rahu[0], "end_jd": rahu[1],
                      "note": "Traditionally avoided for starting new work."},
        "yamaganda": {"start_jd": yama[0], "end_jd": yama[1],
                      "note": "A second inauspicious window."},
        "gulika_kaal": {"start_jd": gulika[0], "end_jd": gulika[1],
                        "note": "Saturn's shadow period."},
        "abhijit_muhurat": {"start_jd": abhijit[0], "end_jd": abhijit[1],
                            "note": "The most auspicious window of the day, "
                                    "around solar noon. Not observed on "
                                    "Wednesdays in some traditions."},
        "day_length_hours": round(day_len * 24, 3),
    }


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------
def compute(date_str: str, lat: float, lon: float,
            ayanamsa: str = K.DEFAULT_AYANAMSA,
            tz_name: str | None = None) -> dict[str, Any]:
    """Panchang for a calendar date at a place.

    The Vedic day runs sunrise to sunrise, so all five limbs are reported as
    they stand *at sunrise* -- which is how printed panchangs quote them --
    along with the moment each one ends.
    """
    y, mo, d = [int(p) for p in date_str.split("-")]
    tz_name = tz_name or timezone_for(lat, lon)
    offset, tz_name, abbrev = utc_offset_at(lat, lon, datetime(y, mo, d, 12, 0), tz_name)

    # Local midnight expressed as a Julian Day in UT.
    jd_midnight = julian_day(datetime(y, mo, d, tzinfo=timezone.utc)) - offset / 24.0

    rs = sunrise_sunset(jd_midnight, lat, lon)
    sunrise = rs["sunrise"]
    reference_jd = sunrise if sunrise is not None else jd_midnight + 0.25

    weekday = (_date(y, mo, d).weekday() + 1) % 7      # Monday=0 -> Sunday=0

    tithi = tithi_at(reference_jd, ayanamsa)
    nak = nakshatra_at(reference_jd, ayanamsa)
    yoga = yoga_at(reference_jd, ayanamsa)
    karana = karana_at(reference_jd, ayanamsa)
    periods = day_periods(sunrise, rs["sunset"], weekday)

    def local(jd: float | None) -> str | None:
        if jd is None:
            return None
        return (jd_to_utc(jd) + timedelta(hours=offset)).replace(
            tzinfo=None, microsecond=0).isoformat()

    def localise(node: dict[str, Any]) -> dict[str, Any]:
        out = dict(node)
        for key in list(out):
            if key.endswith("_jd") and isinstance(out[key], (int, float)):
                out[key.replace("_jd", "")] = local(out[key])
        return out

    sun_lon, moon_lon = _sun_moon(reference_jd, ayanamsa)

    return {
        "date": date_str,
        "location": {"latitude": lat, "longitude": lon,
                     "tz_name": tz_name, "tz_abbrev": abbrev,
                     "utc_offset_hours": offset},
        "ayanamsa": ayanamsa,
        "vara": {
            "index": weekday,
            "name": VARA_NAMES[weekday],
            "sanskrit": VARA_SANSKRIT[weekday],
            "lord": VARA_LORDS[weekday],
        },
        "tithi": localise(tithi),
        "nakshatra": localise(nak),
        "yoga": localise(yoga),
        "karana": localise(karana),
        "sun": {
            "sunrise": local(rs["sunrise"]),
            "sunset": local(rs["sunset"]),
            "longitude": round(sun_lon, 4),
            "sign": K.SIGN_NAMES[K.sign_of(sun_lon)],
        },
        "moon": {
            "moonrise": local(rs["moonrise"]),
            "moonset": local(rs["moonset"]),
            "longitude": round(moon_lon, 4),
            "sign": K.SIGN_NAMES[K.sign_of(moon_lon)],
            "phase_angle": round((moon_lon - sun_lon) % 360, 2),
            "illumination_percent": round(
                (1 - __import__("math").cos(
                    __import__("math").radians((moon_lon - sun_lon) % 360))) / 2 * 100, 1),
        },
        "periods": {k: (localise(v) if isinstance(v, dict) else v)
                    for k, v in periods.items()},
        "note": ("The Vedic day runs from sunrise to sunrise, so each limb is "
                 "given as it stands at sunrise together with the time it ends."),
    }
