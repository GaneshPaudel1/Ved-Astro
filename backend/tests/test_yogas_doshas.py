"""Yogas, ashtakavarga and doshas."""
from __future__ import annotations

import pytest

from app.jyotish import constants as K
from app.jyotish import yogas, doshas, ashtakavarga as av
from app.jyotish.timeutil import build_moment
from app.jyotish.ephemeris import compute_chart


def chart(date="1990-05-05", time="10:30:00", lat=28.6139, lon=77.2090):
    m = build_moment(date, time, lat, lon)
    return m, compute_chart(m)


def fake_planet(sign, dignity="neutral", longitude=None, **kw):
    base = {
        "sign": sign, "sign_name": K.SIGN_NAMES[sign], "dignity": dignity,
        "longitude": longitude if longitude is not None else sign * 30 + 5,
        "combust": False, "retrograde": False, "house": 0, "abbr": "??",
    }
    base.update(kw)
    return base


# --------------------------------------------------------------------------
# Ashtakavarga -- the tables are self-checking
# --------------------------------------------------------------------------
def test_bav_table_totals_match_published_values():
    assert av.table_totals() == av.EXPECTED_BAV_TOTALS


def test_sav_always_totals_337():
    _, c = chart()
    a = av.compute(c.planets, c.ascendant_sign)
    assert a["sav_total"] == av.EXPECTED_SAV_TOTAL == 337
    assert sum(a["sav"]) == 337
    assert len(a["sav"]) == 12


def test_bav_row_totals_hold_for_a_real_chart():
    _, c = chart()
    a = av.compute(c.planets, c.ascendant_sign)
    assert a["bav_totals"] == av.EXPECTED_BAV_TOTALS


@pytest.mark.parametrize("date", ["1950-01-01", "1975-06-15", "2001-11-30", "2024-02-29"])
def test_sav_total_invariant_across_charts(date):
    _, c = chart(date=date)
    assert av.compute(c.planets, c.ascendant_sign)["sav_total"] == 337


def test_bindus_are_bounded():
    _, c = chart()
    a = av.compute(c.planets, c.ascendant_sign)
    for planet, row in a["bav"].items():
        assert len(row) == 12
        assert all(0 <= b <= 8 for b in row), planet


# --------------------------------------------------------------------------
# Yogas
# --------------------------------------------------------------------------
def test_mahapurusha_requires_dignity_and_kendra():
    asc = 0     # Aries rising
    # Saturn exalted in Libra = 7th house from Aries -> Sasha yoga.
    p = {"Saturn": fake_planet(6, "exalted")}
    found = yogas.panch_mahapurusha(p, asc)
    assert [y["sanskrit"] for y in found] == ["Sasha"]

    # Same dignity but in the 3rd house -> no yoga.
    p = {"Saturn": fake_planet(2, "exalted")}
    assert yogas.panch_mahapurusha(p, asc) == []

    # Kendra but no dignity -> no yoga.
    p = {"Saturn": fake_planet(6, "neutral")}
    assert yogas.panch_mahapurusha(p, asc) == []


def test_all_five_mahapurusha_yogas_are_reachable():
    """Each planet placed in its exaltation sign, with an ascendant chosen so
    that sign falls in the 7th -- an angle. Mercury exalts in Virgo, which is
    never a kendra from Aries, so the ascendant has to move per planet."""
    cases = {
        "Mars": (9, "Ruchaka"), "Mercury": (5, "Bhadra"), "Jupiter": (3, "Hamsa"),
        "Venus": (11, "Malavya"), "Saturn": (6, "Sasha"),
    }
    for planet, (sign, name) in cases.items():
        asc = (sign + 6) % 12                       # puts `sign` in the 7th
        found = yogas.panch_mahapurusha({planet: fake_planet(sign, "exalted")}, asc)
        assert [y["sanskrit"] for y in found] == [name], planet
        assert found[0]["houses"] == [7]


def test_gaja_kesari_is_measured_from_the_moon_not_the_lagna():
    # Moon in Aries, Jupiter in Cancer = 4th from Moon -> yoga.
    p = {"Moon": fake_planet(0), "Jupiter": fake_planet(3)}
    assert yogas.gaja_kesari(p, 6) != []
    # Jupiter in Taurus = 2nd from Moon -> no yoga.
    p = {"Moon": fake_planet(0), "Jupiter": fake_planet(1)}
    assert yogas.gaja_kesari(p, 6) == []


def test_budhaditya_flags_combustion_as_weak():
    p = {"Sun": fake_planet(4), "Mercury": fake_planet(4, combust=True)}
    y = yogas.budhaditya(p, 0)[0]
    assert y["strength"] == "weak"
    p = {"Sun": fake_planet(4), "Mercury": fake_planet(4, combust=False)}
    assert yogas.budhaditya(p, 0)[0]["strength"] == "moderate"


def test_kemadruma_needs_an_isolated_moon():
    # A planet in the sign next to the Moon means the yoga never forms at all.
    p = {"Moon": fake_planet(3), "Sun": fake_planet(4)}
    assert yogas.kemadruma(p, 0) == []


def test_uncancelled_kemadruma_is_reported_as_caution():
    """Aries lagna, Moon in Gemini (3rd, not a kendra). Only malefics, none in
    a kendra from the Moon and none aspecting it."""
    p = {"Moon": fake_planet(2), "Sun": fake_planet(0), "Mars": fake_planet(4)}
    out = yogas.kemadruma(p, 0)
    assert len(out) == 1
    assert out[0]["key"] == "kemadruma"
    assert out[0]["strength"] == "caution"


def test_kemadruma_is_cancelled_by_a_graha_angular_to_the_moon():
    """Moon alone in Cancer with the Sun in the 7th from it -- Kemadruma Bhanga.

    Reporting the raw yoga here would tell someone they have a hardship
    combination that classical texts say is cancelled.
    """
    p = {"Moon": fake_planet(3), "Sun": fake_planet(9), "Mars": fake_planet(10)}
    out = yogas.kemadruma(p, 0)
    assert len(out) == 1
    assert out[0]["key"] == "kemadruma_bhanga"
    assert out[0]["strength"] != "caution"
    assert "angle from the Moon" in out[0]["detail"]


def test_kemadruma_is_cancelled_when_the_moon_is_angular_from_the_lagna():
    # Aries lagna, Moon in Cancer = the 4th house, an angle.
    p = {"Moon": fake_planet(3), "Sun": fake_planet(8), "Mars": fake_planet(10)}
    out = yogas.kemadruma(p, 0)
    assert out[0]["key"] == "kemadruma_bhanga"


def test_parivartana_detects_a_sign_exchange():
    # Mars in Venus's Taurus, Venus in Mars's Aries.
    p = {"Mars": fake_planet(1), "Venus": fake_planet(0)}
    found = yogas.parivartana_yogas(p, 0)
    assert len(found) == 1
    assert set(found[0]["planets"]) == {"Mars", "Venus"}


def test_neecha_bhanga_requires_a_cancelling_condition():
    # Sun debilitated in Libra; dispositor Venus angular in Aries (7th) -> cancelled.
    p = {"Sun": fake_planet(6, "debilitated"), "Venus": fake_planet(0)}
    assert yogas.neecha_bhanga(p, 0) != []
    # Dispositor tucked in the 6th -> no cancellation.
    p = {"Sun": fake_planet(6, "debilitated"), "Venus": fake_planet(5)}
    out = yogas.neecha_bhanga(p, 0)
    assert out == [] or "navamsa" in out[0]["detail"]


def test_detect_all_orders_by_strength_and_never_raises():
    _, c = chart()
    found = yogas.detect_all(c.planets, c.ascendant_sign)
    ranks = [yogas._STRENGTH_RANK[y["strength"]] for y in found]
    assert ranks == sorted(ranks)
    for y in found:
        assert y["summary"] and y["detail"] and y["planets"]


def test_yogas_tolerate_a_missing_ascendant():
    _, c = compute_no_time()
    found = yogas.detect_all(c.planets, None)
    assert isinstance(found, list)      # must not raise


def compute_no_time():
    m = build_moment("1990-05-05", None, 28.6139, 77.2090)
    return m, compute_chart(m)


# --------------------------------------------------------------------------
# Doshas
# --------------------------------------------------------------------------
def test_manglik_checks_all_three_reference_points():
    asc = 0
    # Mars in the 7th from the lagna.
    p = {"Mars": fake_planet(6), "Moon": fake_planet(2), "Venus": fake_planet(2)}
    r = doshas.manglik(p, asc)
    assert r["present"]
    assert [h["reference"] for h in r["hits"]] == ["Lagna"]


def test_manglik_absent_when_mars_is_clear():
    asc = 0
    # Mars in the 3rd from lagna, Moon and Venus.
    p = {"Mars": fake_planet(2), "Moon": fake_planet(0), "Venus": fake_planet(0)}
    assert doshas.manglik(p, asc)["present"] is False


def test_manglik_cancellation_downgrades_severity():
    asc = 0
    # Mars exalted in Capricorn, which is also the 10th -- not a manglik house,
    # so put it in the 8th (Scorpio) where it owns the sign.
    p = {"Mars": fake_planet(7, "own sign"), "Moon": fake_planet(2),
         "Venus": fake_planet(2)}
    r = doshas.manglik(p, asc)
    assert r["present"] and r["severity"] == "cancelled"
    assert r["cancellations"]


def test_manglik_reports_south_indian_variation():
    asc = 0
    p = {"Mars": fake_planet(1), "Moon": fake_planet(4), "Venus": fake_planet(4)}
    r = doshas.manglik(p, asc)          # Mars in the 2nd from lagna
    assert r["present"]
    assert r["hits"][0]["counted_in_south_india"] is False


def test_kaal_sarp_true_when_all_planets_lie_on_one_side():
    p = {"Rahu": fake_planet(0, longitude=0.0), "Ketu": fake_planet(6, longitude=180.0)}
    for i, name in enumerate(["Sun", "Moon", "Mars", "Mercury", "Jupiter",
                              "Venus", "Saturn"]):
        p[name] = fake_planet(1, longitude=20.0 + i * 15)   # all within 0-180
    r = doshas.kaal_sarp(p)
    assert r["present"] is True


def test_kaal_sarp_false_when_one_planet_escapes():
    p = {"Rahu": fake_planet(0, longitude=0.0), "Ketu": fake_planet(6, longitude=180.0)}
    for i, name in enumerate(["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus"]):
        p[name] = fake_planet(1, longitude=20.0 + i * 15)
    p["Saturn"] = fake_planet(8, longitude=250.0)           # the other side
    r = doshas.kaal_sarp(p)
    assert r["present"] is False
    assert r["partial"] is True
    assert r["breaking_planet"] == ["Saturn"]


def test_sade_sati_phases_are_ordered_and_contiguous_in_type():
    m, c = chart()
    r = doshas.sade_sati(c.planets["Moon"]["sign"], m.jd_ut, m.jd_ut + 40 * 365.25)
    assert r["phases"]
    for a, b in zip(r["phases"], r["phases"][1:]):
        assert a["start_jd"] <= b["start_jd"]
    for p in r["phases"]:
        assert p["house_from_moon"] in (12, 1, 2)
        assert p["phase"] in ("Rising", "Peak", "Setting")


def test_sade_sati_watches_the_right_three_signs():
    m, c = chart()
    moon_sign = c.planets["Moon"]["sign"]
    expected = {(moon_sign + 11) % 12, moon_sign, (moon_sign + 1) % 12}
    r = doshas.sade_sati(moon_sign, m.jd_ut, m.jd_ut + 40 * 365.25)
    assert {p["sign"] for p in r["phases"]} <= expected


def test_pitra_needs_two_indicators():
    asc = 0
    # Sun conjunct Rahu in the 9th: two indicators.
    p = {"Sun": fake_planet(8), "Rahu": fake_planet(8),
         "Saturn": fake_planet(1), "Jupiter": fake_planet(2)}
    assert doshas.pitra_dosha(p, asc)["present"] is True


def test_pitra_suppressed_without_birth_time():
    assert doshas.pitra_dosha({}, None)["present"] is False


def test_detect_all_doshas_runs_end_to_end():
    m, c = chart()
    r = doshas.detect_all(c.planets, c.ascendant_sign, m.jd_ut, m.jd_ut + 30 * 365.25)
    assert set(r) >= {"manglik", "kaal_sarp", "pitra", "sade_sati"}
    for key in ("manglik", "kaal_sarp", "pitra"):
        assert "rule" in r[key] or "reason" in r[key]
