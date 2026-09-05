"""Dasha systems -- the timing engine.

Vimshottari is the primary system and the one the UI leads with. Its whole
structure hangs off a single measurement: how far the Moon had travelled
through its nakshatra at birth. That fraction decides which lord rules first
and how much of that first period was already spent before you were born.

Yogini (36 years) and Ashtottari (108 years) are provided as alternates.

Sub-periods nest by the same proportional rule at every level, so one recursive
routine serves mahadasha through prana.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import constants as K
from .timeutil import jd_to_utc

LEVEL_NAMES = ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"]


def _jd_to_iso_date(jd: float) -> str:
    return jd_to_utc(jd).date().isoformat()


def _jd_to_iso(jd: float) -> str:
    return jd_to_utc(jd).replace(microsecond=0).isoformat()


# --------------------------------------------------------------------------
# Vimshottari
# --------------------------------------------------------------------------
@dataclass
class DashaSeed:
    """Where the Vimshottari cycle stands at birth."""
    lord: str
    nakshatra: str
    fraction_elapsed: float       # 0..1 through the birth nakshatra
    balance_years: float          # of the first mahadasha, still to run
    cycle_start_jd: float         # notional start of that first mahadasha


def vimshottari_seed(moon_longitude: float, birth_jd: float,
                     year_days: float = K.SIDEREAL_YEAR_DAYS) -> DashaSeed:
    """Locate the birth moment inside the 120-year cycle."""
    nak_index = K.nakshatra_of(moon_longitude)
    nak_start = nak_index * K.NAKSHATRA_SPAN
    fraction = (K.norm360(moon_longitude) - nak_start) / K.NAKSHATRA_SPAN
    fraction = min(max(fraction, 0.0), 1.0)

    lord = K.NAKSHATRAS[nak_index][1]
    total_years = K.VIMSHOTTARI_YEARS[lord]
    balance = total_years * (1.0 - fraction)

    # The period began before birth; rewind by the elapsed portion so that all
    # sub-period boundaries fall where the classical method puts them.
    elapsed_days = total_years * fraction * year_days
    return DashaSeed(
        lord=lord,
        nakshatra=K.NAKSHATRA_NAMES[nak_index],
        fraction_elapsed=fraction,
        balance_years=balance,
        cycle_start_jd=birth_jd - elapsed_days,
    )


def _sequence_from(lord: str) -> list[str]:
    i = K.VIMSHOTTARI_ORDER.index(lord)
    return K.VIMSHOTTARI_ORDER[i:] + K.VIMSHOTTARI_ORDER[:i]


def _build_periods(parent_lord: str, start_jd: float, span_days: float,
                   level: int, max_level: int, year_days: float,
                   now_jd: float | None) -> list[dict[str, Any]]:
    """Recursively divide a period among the nine lords.

    A sub-period's share of its parent is its own dasha years over 120. The
    sequence starts with the parent's own lord and follows the fixed cycle.
    """
    if level > max_level:
        return []

    out: list[dict[str, Any]] = []
    cursor = start_jd
    for lord in _sequence_from(parent_lord):
        share = K.VIMSHOTTARI_YEARS[lord] / K.VIMSHOTTARI_TOTAL_YEARS
        sub_days = span_days * share
        node: dict[str, Any] = {
            "lord": lord,
            "level": level,
            "level_name": LEVEL_NAMES[level - 1],
            "start_jd": cursor,
            "end_jd": cursor + sub_days,
            "start": _jd_to_iso_date(cursor),
            "end": _jd_to_iso_date(cursor + sub_days),
            "duration_years": round(sub_days / year_days, 4),
            "duration_days": round(sub_days, 2),
        }
        if now_jd is not None:
            node["current"] = cursor <= now_jd < cursor + sub_days
        node["children"] = _build_periods(
            lord, cursor, sub_days, level + 1, max_level, year_days, now_jd)
        out.append(node)
        cursor += sub_days
    return out


def vimshottari(moon_longitude: float, birth_jd: float, now_jd: float | None = None,
                max_level: int = 2, year_days: float = K.SIDEREAL_YEAR_DAYS
                ) -> dict[str, Any]:
    """Full Vimshottari tree.

    ``max_level`` 1 = mahadasha only, 2 adds antardasha, up to 5 for prana.
    Periods that ended before birth are dropped, but the *first* mahadasha is
    kept and marked partial -- its balance is what astrologers quote.
    """
    seed = vimshottari_seed(moon_longitude, birth_jd, year_days)

    mahadashas: list[dict[str, Any]] = []
    cursor = seed.cycle_start_jd
    for lord in _sequence_from(seed.lord):
        span_days = K.VIMSHOTTARI_YEARS[lord] * year_days
        node = {
            "lord": lord,
            "level": 1,
            "level_name": LEVEL_NAMES[0],
            "start_jd": cursor,
            "end_jd": cursor + span_days,
            "start": _jd_to_iso_date(cursor),
            "end": _jd_to_iso_date(cursor + span_days),
            "duration_years": K.VIMSHOTTARI_YEARS[lord],
            "duration_days": round(span_days, 2),
            "partial_at_birth": cursor < birth_jd < cursor + span_days,
        }
        if now_jd is not None:
            node["current"] = cursor <= now_jd < cursor + span_days
        node["children"] = _build_periods(
            lord, cursor, span_days, 2, max_level, year_days, now_jd)
        mahadashas.append(node)
        cursor += span_days

    return {
        "system": "Vimshottari",
        "total_years": K.VIMSHOTTARI_TOTAL_YEARS,
        "birth_nakshatra": seed.nakshatra,
        "starting_lord": seed.lord,
        "fraction_elapsed_at_birth": round(seed.fraction_elapsed, 6),
        "balance_at_birth": {
            "lord": seed.lord,
            "years": round(seed.balance_years, 4),
            "readable": _readable_years(seed.balance_years),
        },
        "cycle_start": _jd_to_iso_date(seed.cycle_start_jd),
        "cycle_end": _jd_to_iso_date(cursor),
        "periods": mahadashas,
    }


def _readable_years(years: float) -> str:
    y = int(years)
    months_f = (years - y) * 12
    m = int(months_f)
    d = int(round((months_f - m) * 30.4375))
    if d >= 30:
        d = 0
        m += 1
    if m >= 12:
        m = 0
        y += 1
    parts = []
    if y:
        parts.append(f"{y}y")
    if m:
        parts.append(f"{m}m")
    if d or not parts:
        parts.append(f"{d}d")
    return " ".join(parts)


def current_dasha_path(tree: dict[str, Any], now_jd: float,
                       depth: int = 5, year_days: float = K.SIDEREAL_YEAR_DAYS
                       ) -> list[dict[str, Any]]:
    """The chain of periods running right now, mahadasha down to prana.

    Computed on demand so the main tree stays small: expanding all five levels
    for all nine lords would be 59,049 nodes.
    """
    path: list[dict[str, Any]] = []
    node = None
    for md in tree["periods"]:
        if md["start_jd"] <= now_jd < md["end_jd"]:
            node = md
            break
    if node is None:
        return path

    path.append(_summarise(node, now_jd, year_days))
    lord, start, span = node["lord"], node["start_jd"], node["end_jd"] - node["start_jd"]

    for level in range(2, depth + 1):
        cursor = start
        found = None
        for sub_lord in _sequence_from(lord):
            sub_days = span * K.VIMSHOTTARI_YEARS[sub_lord] / K.VIMSHOTTARI_TOTAL_YEARS
            if cursor <= now_jd < cursor + sub_days:
                found = (sub_lord, cursor, sub_days)
                break
            cursor += sub_days
        if not found:
            break
        sub_lord, sub_start, sub_days = found
        path.append(_summarise({
            "lord": sub_lord,
            "level": level,
            "level_name": LEVEL_NAMES[level - 1],
            "start_jd": sub_start,
            "end_jd": sub_start + sub_days,
        }, now_jd, year_days))
        lord, start, span = sub_lord, sub_start, sub_days
    return path


def _summarise(node: dict[str, Any], now_jd: float, year_days: float) -> dict[str, Any]:
    start, end = node["start_jd"], node["end_jd"]
    total = end - start
    elapsed = max(0.0, min(now_jd - start, total))
    return {
        "lord": node["lord"],
        "level": node["level"],
        "level_name": node["level_name"],
        "start": _jd_to_iso_date(start),
        "end": _jd_to_iso_date(end),
        "start_jd": start,
        "end_jd": end,
        "duration_years": round(total / year_days, 4),
        "elapsed_percent": round(elapsed / total * 100, 2) if total else 0.0,
        "remaining": _readable_years(max(0.0, (end - now_jd)) / year_days),
    }


def periods_between(tree: dict[str, Any], from_jd: float, to_jd: float,
                    level: int = 2) -> list[dict[str, Any]]:
    """Flatten the tree to the periods overlapping a window -- for the timeline."""
    out: list[dict[str, Any]] = []

    def walk(nodes: list[dict[str, Any]]) -> None:
        for n in nodes:
            if n["end_jd"] < from_jd or n["start_jd"] > to_jd:
                continue
            if n["level"] == level:
                out.append(n)
            elif n["level"] < level:
                walk(n.get("children", []))

    walk(tree["periods"])
    return out


# --------------------------------------------------------------------------
# Yogini dasha -- 36-year cycle of eight yoginis
# --------------------------------------------------------------------------
YOGINI_ORDER = ["Mangala", "Pingala", "Dhanya", "Bhramari",
                "Bhadrika", "Ulka", "Siddha", "Sankata"]
YOGINI_YEARS = {"Mangala": 1, "Pingala": 2, "Dhanya": 3, "Bhramari": 4,
                "Bhadrika": 5, "Ulka": 6, "Siddha": 7, "Sankata": 8}
YOGINI_LORD = {"Mangala": "Moon", "Pingala": "Sun", "Dhanya": "Jupiter",
               "Bhramari": "Mars", "Bhadrika": "Mercury", "Ulka": "Saturn",
               "Siddha": "Venus", "Sankata": "Rahu"}


def yogini(moon_longitude: float, birth_jd: float, now_jd: float | None = None,
           year_days: float = K.SIDEREAL_YEAR_DAYS) -> dict[str, Any]:
    """Yogini dasha. The starting yogini follows (nakshatra number + 3) mod 8."""
    nak_index = K.nakshatra_of(moon_longitude)          # 0-based
    start_idx = ((nak_index + 1) + 3) % 8               # texts count from 1
    fraction = ((K.norm360(moon_longitude) - nak_index * K.NAKSHATRA_SPAN)
                / K.NAKSHATRA_SPAN)

    first = YOGINI_ORDER[start_idx]
    first_years = YOGINI_YEARS[first]
    cursor = birth_jd - first_years * fraction * year_days

    periods = []
    order = YOGINI_ORDER[start_idx:] + YOGINI_ORDER[:start_idx]
    # Run three full cycles so the timeline covers a normal lifetime.
    for cycle in range(3):
        for name in order:
            span = YOGINI_YEARS[name] * year_days
            node = {
                "lord": name,
                "graha": YOGINI_LORD[name],
                "level": 1,
                "level_name": "Yogini Dasha",
                "start_jd": cursor,
                "end_jd": cursor + span,
                "start": _jd_to_iso_date(cursor),
                "end": _jd_to_iso_date(cursor + span),
                "duration_years": YOGINI_YEARS[name],
            }
            if now_jd is not None:
                node["current"] = cursor <= now_jd < cursor + span
            periods.append(node)
            cursor += span

    return {
        "system": "Yogini",
        "total_years": sum(YOGINI_YEARS.values()),
        "starting_lord": first,
        "birth_nakshatra": K.NAKSHATRA_NAMES[nak_index],
        "balance_at_birth": {
            "lord": first,
            "years": round(first_years * (1 - fraction), 4),
            "readable": _readable_years(first_years * (1 - fraction)),
        },
        "periods": periods,
    }


# --------------------------------------------------------------------------
# Ashtottari dasha -- 108-year cycle
# --------------------------------------------------------------------------
ASHTOTTARI_ORDER = ["Sun", "Moon", "Mars", "Mercury",
                    "Saturn", "Jupiter", "Rahu", "Venus"]
ASHTOTTARI_YEARS = {"Sun": 6, "Moon": 15, "Mars": 8, "Mercury": 17,
                    "Saturn": 10, "Jupiter": 19, "Rahu": 12, "Venus": 21}

# Ashtottari groups the 27 nakshatras unevenly across its eight lords, counting
# from Ardra. Nakshatra counts per lord, in cycle order starting at Ardra (#6).
_ASHTOTTARI_GROUPS = [("Sun", 3), ("Moon", 3), ("Mars", 4), ("Mercury", 3),
                      ("Saturn", 4), ("Jupiter", 3), ("Rahu", 4), ("Venus", 3)]


def _ashtottari_lord_for(nak_index: int) -> tuple[str, int, int]:
    """Return (lord, position within its group, group size). Counting starts at Ardra."""
    offset = (nak_index - 5) % 27          # Ardra is index 5
    cursor = 0
    for lord, count in _ASHTOTTARI_GROUPS:
        if offset < cursor + count:
            return lord, offset - cursor, count
        cursor += count
    return _ASHTOTTARI_GROUPS[-1][0], 0, _ASHTOTTARI_GROUPS[-1][1]


def ashtottari(moon_longitude: float, birth_jd: float, now_jd: float | None = None,
               year_days: float = K.SIDEREAL_YEAR_DAYS) -> dict[str, Any]:
    nak_index = K.nakshatra_of(moon_longitude)
    lord, pos_in_group, group_size = _ashtottari_lord_for(nak_index)

    within_nak = ((K.norm360(moon_longitude) - nak_index * K.NAKSHATRA_SPAN)
                  / K.NAKSHATRA_SPAN)
    fraction = (pos_in_group + within_nak) / group_size

    total = ASHTOTTARI_YEARS[lord]
    cursor = birth_jd - total * fraction * year_days

    i = ASHTOTTARI_ORDER.index(lord)
    order = ASHTOTTARI_ORDER[i:] + ASHTOTTARI_ORDER[:i]

    periods = []
    for name in order:
        span = ASHTOTTARI_YEARS[name] * year_days
        node = {
            "lord": name,
            "level": 1,
            "level_name": "Ashtottari Dasha",
            "start_jd": cursor,
            "end_jd": cursor + span,
            "start": _jd_to_iso_date(cursor),
            "end": _jd_to_iso_date(cursor + span),
            "duration_years": ASHTOTTARI_YEARS[name],
        }
        if now_jd is not None:
            node["current"] = cursor <= now_jd < cursor + span
        periods.append(node)
        cursor += span

    return {
        "system": "Ashtottari",
        "total_years": sum(ASHTOTTARI_YEARS.values()),
        "starting_lord": lord,
        "birth_nakshatra": K.NAKSHATRA_NAMES[nak_index],
        "balance_at_birth": {
            "lord": lord,
            "years": round(total * (1 - fraction), 4),
            "readable": _readable_years(total * (1 - fraction)),
        },
        "periods": periods,
    }
