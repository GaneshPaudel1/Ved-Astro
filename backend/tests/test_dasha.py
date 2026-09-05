"""Dasha arithmetic. The 120-year identity is the sanity check the brief asks for."""
from __future__ import annotations

import pytest

from app.jyotish import constants as K
from app.jyotish.dasha import (
    vimshottari, vimshottari_seed, current_dasha_path, periods_between,
    yogini, ashtottari, ASHTOTTARI_YEARS, YOGINI_YEARS, _sequence_from,
)
from app.jyotish.timeutil import build_moment
from app.jyotish.ephemeris import compute_chart

YEAR = K.SIDEREAL_YEAR_DAYS


def sample_chart():
    return compute_chart(build_moment("1990-05-05", "10:30:00", 28.6139, 77.2090))


# --------------------------------------------------------------------------
# The headline invariant
# --------------------------------------------------------------------------
def test_vimshottari_years_total_120():
    assert sum(K.VIMSHOTTARI_YEARS.values()) == 120


def test_full_cycle_spans_120_years():
    c = sample_chart()
    t = vimshottari(c.planets["Moon"]["longitude"], c.moment["jd_ut"], max_level=1)
    span_days = t["periods"][-1]["end_jd"] - t["periods"][0]["start_jd"]
    assert abs(span_days / YEAR - 120.0) < 1e-6


def test_all_nine_lords_appear_once():
    c = sample_chart()
    t = vimshottari(c.planets["Moon"]["longitude"], c.moment["jd_ut"], max_level=1)
    lords = [p["lord"] for p in t["periods"]]
    assert len(lords) == 9
    assert set(lords) == set(K.VIMSHOTTARI_ORDER)


def test_periods_are_contiguous_with_no_gaps():
    c = sample_chart()
    t = vimshottari(c.planets["Moon"]["longitude"], c.moment["jd_ut"], max_level=3)

    def check(nodes):
        for a, b in zip(nodes, nodes[1:]):
            assert abs(a["end_jd"] - b["start_jd"]) < 1e-9
        for n in nodes:
            kids = n.get("children") or []
            if kids:
                assert abs(kids[0]["start_jd"] - n["start_jd"]) < 1e-9
                assert abs(kids[-1]["end_jd"] - n["end_jd"]) < 1e-9
                check(kids)

    check(t["periods"])


def test_antardashas_sum_to_their_mahadasha():
    c = sample_chart()
    t = vimshottari(c.planets["Moon"]["longitude"], c.moment["jd_ut"], max_level=2)
    for md in t["periods"]:
        total = sum(ad["end_jd"] - ad["start_jd"] for ad in md["children"])
        assert abs(total - (md["end_jd"] - md["start_jd"])) < 1e-6
        assert len(md["children"]) == 9


def test_five_levels_available():
    c = sample_chart()
    t = vimshottari(c.planets["Moon"]["longitude"], c.moment["jd_ut"], max_level=5)
    node = t["periods"][0]
    for expected in ["Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"]:
        assert node["level_name"] == expected
        if expected != "Prana":
            node = node["children"][0]
    assert node["children"] == []


# --------------------------------------------------------------------------
# The seed: which lord starts, and with how much left
# --------------------------------------------------------------------------
def test_first_lord_is_the_moons_nakshatra_lord():
    c = sample_chart()
    moon = c.planets["Moon"]
    t = vimshottari(moon["longitude"], c.moment["jd_ut"], max_level=1)
    assert t["starting_lord"] == moon["nakshatra_lord"]
    assert t["birth_nakshatra"] == moon["nakshatra_name"]


@pytest.mark.parametrize("nak_index", range(27))
def test_seed_balance_matches_nakshatra_fraction(nak_index):
    """A Moon exactly at a nakshatra start has the full period still to run."""
    lon = nak_index * K.NAKSHATRA_SPAN
    seed = vimshottari_seed(lon, 2451545.0)
    lord = K.NAKSHATRAS[nak_index][1]
    assert seed.lord == lord
    assert abs(seed.balance_years - K.VIMSHOTTARI_YEARS[lord]) < 1e-9
    assert abs(seed.cycle_start_jd - 2451545.0) < 1e-9


def test_seed_at_nakshatra_midpoint_has_half_remaining():
    lon = 5 * K.NAKSHATRA_SPAN + K.NAKSHATRA_SPAN / 2
    seed = vimshottari_seed(lon, 2451545.0)
    lord = K.NAKSHATRAS[5][1]
    assert abs(seed.balance_years - K.VIMSHOTTARI_YEARS[lord] / 2) < 1e-9


def test_birth_falls_inside_the_first_mahadasha():
    c = sample_chart()
    jd = c.moment["jd_ut"]
    t = vimshottari(c.planets["Moon"]["longitude"], jd, max_level=1)
    first = t["periods"][0]
    assert first["start_jd"] <= jd < first["end_jd"]
    assert first["partial_at_birth"] is True


def test_sequence_wraps_correctly():
    assert _sequence_from("Ketu") == K.VIMSHOTTARI_ORDER
    assert _sequence_from("Sun")[0] == "Sun"
    assert len(_sequence_from("Mercury")) == 9
    assert _sequence_from("Mercury")[1] == "Ketu"     # cycle wraps


# --------------------------------------------------------------------------
# Current period
# --------------------------------------------------------------------------
def test_current_path_is_nested_and_five_deep():
    c = sample_chart()
    jd = c.moment["jd_ut"]
    now = jd + 35 * YEAR
    t = vimshottari(c.planets["Moon"]["longitude"], jd, now_jd=now, max_level=2)
    path = current_dasha_path(t, now, depth=5)
    assert len(path) == 5
    for parent, child in zip(path, path[1:]):
        assert parent["start_jd"] <= child["start_jd"]
        assert child["end_jd"] <= parent["end_jd"] + 1e-9
        assert child["level"] == parent["level"] + 1
    for p in path:
        assert p["start_jd"] <= now < p["end_jd"]
        assert 0 <= p["elapsed_percent"] <= 100


def test_exactly_one_current_flag_per_level():
    c = sample_chart()
    jd = c.moment["jd_ut"]
    now = jd + 20 * YEAR
    t = vimshottari(c.planets["Moon"]["longitude"], jd, now_jd=now, max_level=2)
    assert sum(1 for p in t["periods"] if p.get("current")) == 1
    md = next(p for p in t["periods"] if p["current"])
    assert sum(1 for a in md["children"] if a.get("current")) == 1


def test_periods_between_filters_the_window():
    c = sample_chart()
    jd = c.moment["jd_ut"]
    t = vimshottari(c.planets["Moon"]["longitude"], jd, max_level=2)
    window = periods_between(t, jd, jd + 10 * YEAR, level=2)
    assert window
    for p in window:
        assert p["level"] == 2
        assert p["end_jd"] >= jd and p["start_jd"] <= jd + 10 * YEAR


# --------------------------------------------------------------------------
# Alternate systems
# --------------------------------------------------------------------------
def test_yogini_totals_36_years():
    assert sum(YOGINI_YEARS.values()) == 36
    c = sample_chart()
    t = yogini(c.planets["Moon"]["longitude"], c.moment["jd_ut"])
    first_cycle = t["periods"][:8]
    span = first_cycle[-1]["end_jd"] - first_cycle[0]["start_jd"]
    assert abs(span / YEAR - 36.0) < 1e-6
    assert len({p["lord"] for p in first_cycle}) == 8


def test_ashtottari_totals_108_years():
    assert sum(ASHTOTTARI_YEARS.values()) == 108
    c = sample_chart()
    t = ashtottari(c.planets["Moon"]["longitude"], c.moment["jd_ut"])
    span = t["periods"][-1]["end_jd"] - t["periods"][0]["start_jd"]
    assert abs(span / YEAR - 108.0) < 1e-6
    assert len(t["periods"]) == 8


def test_ashtottari_groups_cover_all_27_nakshatras():
    from app.jyotish.dasha import _ASHTOTTARI_GROUPS, _ashtottari_lord_for
    assert sum(count for _, count in _ASHTOTTARI_GROUPS) == 27
    seen = {_ashtottari_lord_for(i)[0] for i in range(27)}
    assert seen == set(ASHTOTTARI_YEARS)


def test_all_systems_start_before_birth_and_run_past_it():
    c = sample_chart()
    jd = c.moment["jd_ut"]
    lon = c.planets["Moon"]["longitude"]
    for tree in (vimshottari(lon, jd, max_level=1), yogini(lon, jd), ashtottari(lon, jd)):
        first = tree["periods"][0]
        assert first["start_jd"] <= jd < first["end_jd"], tree["system"]
