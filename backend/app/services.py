"""Chart assembly and caching.

One place that turns birth details into every derived structure the API serves.
Results are cached per (profile inputs + ayanamsa + house system), because a
full bundle -- sixteen vargas, a five-level dasha tree, a century of Sade Sati
windows -- costs far more than a single chart and none of it changes unless an
input does.
"""
from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any

from .interpret.engine import get as get_interpreter
from .jyotish import (ashtakavarga, constants as K, dasha, doshas, matching,
                      transits, vargas, yogas)
from .jyotish.ephemeris import compute_chart, aspects
from .jyotish.timeutil import build_moment, julian_day


def now_jd() -> float:
    return julian_day(datetime.now(timezone.utc))


# --------------------------------------------------------------------------
# Cache
# --------------------------------------------------------------------------
class _Cache:
    """Small bounded in-process cache. Chart bundles are pure functions of
    their inputs, so a plain dict with an eviction cap is enough."""

    def __init__(self, capacity: int = 128) -> None:
        self._data: dict[str, Any] = {}
        self._order: list[str] = []
        self._lock = threading.Lock()
        self.capacity = capacity

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key in self._data:
                self._order.remove(key)
                self._order.append(key)
                return self._data[key]
        return None

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._data:
                self._order.remove(key)
            self._data[key] = value
            self._order.append(key)
            while len(self._order) > self.capacity:
                self._data.pop(self._order.pop(0), None)

    def clear(self) -> None:
        with self._lock:
            self._data.clear()
            self._order.clear()

    def stats(self) -> dict[str, int]:
        return {"entries": len(self._data), "capacity": self.capacity}


_cache = _Cache()


def cache_key(**parts: Any) -> str:
    blob = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:32]


# --------------------------------------------------------------------------
# Bundle
# --------------------------------------------------------------------------
def build_bundle(name: str, date: str, time: str | None,
                 latitude: float, longitude: float, place: str = "",
                 ayanamsa: str = K.DEFAULT_AYANAMSA,
                 house_system: str = "whole_sign",
                 node_type: str = "mean",
                 time_standard: str = "auto",
                 tz_name: str | None = None,
                 utc_offset_override: float | None = None,
                 include: set[str] | None = None,
                 use_cache: bool = True) -> dict[str, Any]:
    """Everything derived from one set of birth details."""
    include = include or {"all"}
    want = lambda k: "all" in include or k in include   # noqa: E731

    key = cache_key(date=date, time=time, lat=latitude, lon=longitude,
                    ayanamsa=ayanamsa, house_system=house_system,
                    node_type=node_type, time_standard=time_standard,
                    tz_name=tz_name, off=utc_offset_override,
                    include=sorted(include))
    if use_cache:
        hit = _cache.get(key)
        if hit is not None:
            out = dict(hit)
            out["name"] = name
            out["place"] = place
            out["cached"] = True
            return _refresh_live(out)

    moment = build_moment(date, time, latitude, longitude,
                          tz_name=tz_name,
                          override_offset_hours=utc_offset_override,
                          time_standard=time_standard)
    chart = compute_chart(moment, ayanamsa=ayanamsa,
                          house_system=house_system, node_type=node_type)
    chart_d = chart.to_dict()

    moon_lon = chart_d["planets"]["Moon"]["longitude"]
    jd = moment.jd_ut
    n_jd = now_jd()

    bundle: dict[str, Any] = {
        "name": name,
        "place": place,
        "chart": chart_d,
        "cache_key": key,
        "cached": False,
        # The interpreter needs "now" to tell a past Sade Sati from a future one.
        "now_jd": n_jd,
    }

    if want("aspects"):
        bundle["aspects"] = aspects(chart_d["planets"])

    if want("vargas"):
        bundle["vargas"] = vargas.compute_all_vargas(
            chart_d["planets"], chart_d["ascendant"])
        bundle["varga_strength"] = vargas.varga_strength(chart_d["planets"])
        bundle["vargottama"] = vargas.vargottama_planets(chart_d["planets"])

    if want("nakshatras"):
        bundle["nakshatra_detail"] = {
            n: vargas.nakshatra_detail(p["longitude"])
            for n, p in chart_d["planets"].items()
        }
        if chart_d["ascendant"] is not None:
            bundle["nakshatra_detail"]["Ascendant"] = vargas.nakshatra_detail(
                chart_d["ascendant"])

    if want("dasha"):
        bundle["dasha"] = dasha.vimshottari(moon_lon, jd, now_jd=n_jd, max_level=2)
        bundle["dasha_path"] = dasha.current_dasha_path(bundle["dasha"], n_jd, depth=5)
        bundle["dasha_alternates"] = {
            "yogini": dasha.yogini(moon_lon, jd, now_jd=n_jd),
            "ashtottari": dasha.ashtottari(moon_lon, jd, now_jd=n_jd),
        }

    if want("yogas"):
        bundle["yogas"] = yogas.detect_all(chart_d["planets"], chart_d["ascendant_sign"])

    if want("ashtakavarga"):
        bundle["ashtakavarga"] = ashtakavarga.compute(
            chart_d["planets"], chart_d["ascendant_sign"])

    if want("doshas"):
        bundle["doshas"] = doshas.detect_all(
            chart_d["planets"], chart_d["ascendant_sign"],
            birth_jd=jd, now_jd=n_jd, ayanamsa=ayanamsa)

    if want("transits"):
        bav = (bundle.get("ashtakavarga") or {}).get("bav")
        bundle["transits"] = transits.compute(
            chart_d["planets"], chart_d["ascendant_sign"], n_jd,
            ayanamsa=ayanamsa, bav=bav)
        bundle["transit_alerts"] = transits.alerts(chart_d["planets"], n_jd,
                                                   ayanamsa=ayanamsa)

    if want("interpretation"):
        bundle["interpretation"] = get_interpreter().interpret(bundle).to_dict()

    if use_cache:
        _cache.put(key, bundle)
    return bundle


def _refresh_live(bundle: dict[str, Any]) -> dict[str, Any]:
    """Recompute only the time-dependent parts of a cached bundle.

    The chart itself never changes, but 'which dasha is running now' and the
    transit overlay both do. Recomputing just these keeps the cache useful
    without ever serving a stale 'today'.
    """
    chart = bundle.get("chart") or {}
    planets = chart.get("planets") or {}
    if not planets:
        return bundle

    n_jd = now_jd()
    if "dasha" in bundle:
        tree = bundle["dasha"]
        _mark_current(tree["periods"], n_jd)
        bundle["dasha_path"] = dasha.current_dasha_path(tree, n_jd, depth=5)
    if "transits" in bundle:
        bav = (bundle.get("ashtakavarga") or {}).get("bav")
        bundle["transits"] = transits.compute(
            planets, chart.get("ascendant_sign"), n_jd,
            ayanamsa=chart.get("ayanamsa", K.DEFAULT_AYANAMSA), bav=bav)
    if "interpretation" in bundle:
        bundle["interpretation"] = get_interpreter().interpret(bundle).to_dict()
    return bundle


def _mark_current(nodes: list[dict[str, Any]], n_jd: float) -> None:
    for node in nodes:
        node["current"] = node["start_jd"] <= n_jd < node["end_jd"]
        if node.get("children"):
            _mark_current(node["children"], n_jd)


# --------------------------------------------------------------------------
# Matching
# --------------------------------------------------------------------------
def build_match(a: dict[str, Any], b: dict[str, Any],
                ayanamsa: str = K.DEFAULT_AYANAMSA) -> dict[str, Any]:
    """Kundli Milan between two sets of birth details.

    Only the Moon and Mars are needed, so this works for date-only charts --
    the Ashtakoot method never touches the ascendant.
    """
    bundles = []
    for person in (a, b):
        bundles.append(build_bundle(
            name=person.get("name", ""), date=person["date"],
            time=person.get("time"), latitude=person["latitude"],
            longitude=person["longitude"], place=person.get("place", ""),
            ayanamsa=ayanamsa, include={"doshas"}))

    a_chart, b_chart = bundles[0]["chart"], bundles[1]["chart"]
    a_label = a.get("name") or "First person"
    b_label = b.get("name") or "Second person"

    result = matching.ashtakoot(
        a_chart["planets"]["Moon"]["longitude"],
        b_chart["planets"]["Moon"]["longitude"],
        a_label=a_label, b_label=b_label)

    result["manglik"] = matching.compare_manglik(
        bundles[0]["doshas"]["manglik"], bundles[1]["doshas"]["manglik"])

    result["charts"] = {
        a_label: _mini(a_chart, a),
        b_label: _mini(b_chart, b),
    }
    if not a_chart["time_known"] or not b_chart["time_known"]:
        result["time_note"] = (
            "One or both birth times are unknown. Guna Milan only uses the "
            "Moon, so the score stands -- but a Moon computed for midday can "
            "be up to six degrees out, which occasionally changes the "
            "nakshatra and therefore the score.")
    return result


def _mini(chart: dict[str, Any], person: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": person.get("name", ""),
        "place": person.get("place", ""),
        "date": person.get("date"),
        "time": person.get("time"),
        "time_known": chart["time_known"],
        "moon_sign": chart["planets"]["Moon"]["sign_name"],
        "moon_degree": chart["planets"]["Moon"]["degree_str"],
        "nakshatra": chart["planets"]["Moon"]["nakshatra_name"],
        "pada": chart["planets"]["Moon"]["pada"],
        "ascendant": chart.get("ascendant_sign_name"),
    }


def cache_stats() -> dict[str, int]:
    return _cache.stats()


def clear_cache() -> None:
    _cache.clear()
