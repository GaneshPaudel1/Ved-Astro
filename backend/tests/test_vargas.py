"""Divisional chart rules, checked against worked classical examples."""
from __future__ import annotations

import pytest

from app.jyotish import constants as K
from app.jyotish.vargas import VARGA_ORDER, VARGAS, varga_sign, compute_varga


def test_sixteen_vargas_present():
    assert len(VARGA_ORDER) == 16
    assert VARGA_ORDER == ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12",
                           "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]


@pytest.mark.parametrize("varga", VARGA_ORDER)
def test_every_varga_returns_a_valid_sign_everywhere(varga):
    """Sweep the whole zodiac finely; no rule may fall off the end of a table."""
    lon = 0.0
    while lon < 360.0:
        s = varga_sign(lon, varga)
        assert 0 <= s <= 11, f"{varga} at {lon} gave sign {s}"
        lon += 0.1


# --------------------------------------------------------------------------
# D9 Navamsha -- the varga everything else is checked against.
# Movable signs start from themselves, fixed from the 9th, dual from the 5th.
# --------------------------------------------------------------------------
@pytest.mark.parametrize("sign_name,expected_first_navamsa", [
    ("Aries", "Aries"),          # movable -> itself
    ("Taurus", "Capricorn"),     # fixed   -> 9th
    ("Gemini", "Libra"),         # dual    -> 5th
    ("Cancer", "Cancer"),        # movable
    ("Leo", "Aries"),            # fixed   -> 9th from Leo
    ("Virgo", "Capricorn"),      # dual    -> 5th from Virgo
    ("Libra", "Libra"),
    ("Scorpio", "Cancer"),
    ("Sagittarius", "Aries"),
    ("Capricorn", "Capricorn"),
    ("Aquarius", "Libra"),
    ("Pisces", "Cancer"),
])
def test_navamsha_start_signs(sign_name, expected_first_navamsa):
    sign = K.SIGN_NAMES.index(sign_name)
    lon = sign * 30 + 0.5
    assert K.SIGN_NAMES[varga_sign(lon, "D9")] == expected_first_navamsa


def test_navamsha_spans_all_twelve_within_one_sign():
    """The nine navamsas of a sign are nine consecutive signs."""
    got = [varga_sign(0 * 30 + i * (30 / 9) + 0.1, "D9") for i in range(9)]
    assert got == list(range(9))       # Aries..Sagittarius


def test_navamsha_last_degree_of_zodiac():
    # Pisces is dual, so its navamsas start at Cancer and run to Pisces.
    assert K.SIGN_NAMES[varga_sign(359.99, "D9")] == "Pisces"


# --------------------------------------------------------------------------
# Other vargas, spot-checked at their boundaries
# --------------------------------------------------------------------------
def test_hora():
    # Aries (odd): first half Leo (Sun), second half Cancer (Moon).
    assert K.SIGN_NAMES[varga_sign(5.0, "D2")] == "Leo"
    assert K.SIGN_NAMES[varga_sign(20.0, "D2")] == "Cancer"
    # Taurus (even): reversed.
    assert K.SIGN_NAMES[varga_sign(35.0, "D2")] == "Cancer"
    assert K.SIGN_NAMES[varga_sign(50.0, "D2")] == "Leo"


def test_drekkana_is_the_trine_series():
    assert K.SIGN_NAMES[varga_sign(5.0, "D3")] == "Aries"
    assert K.SIGN_NAMES[varga_sign(15.0, "D3")] == "Leo"
    assert K.SIGN_NAMES[varga_sign(25.0, "D3")] == "Sagittarius"


def test_chaturthamsha_is_the_kendra_series():
    for deg, want in [(3.0, "Aries"), (10.0, "Cancer"),
                      (18.0, "Libra"), (26.0, "Capricorn")]:
        assert K.SIGN_NAMES[varga_sign(deg, "D4")] == want


def test_saptamsha_even_sign_starts_from_seventh():
    # Taurus is even, so its saptamsas begin at Scorpio.
    assert K.SIGN_NAMES[varga_sign(30.0 + 1.0, "D7")] == "Scorpio"
    # Aries is odd, begins at itself.
    assert K.SIGN_NAMES[varga_sign(1.0, "D7")] == "Aries"


def test_dashamsha_even_sign_starts_from_ninth():
    assert K.SIGN_NAMES[varga_sign(1.0, "D10")] == "Aries"          # Aries, odd
    assert K.SIGN_NAMES[varga_sign(31.0, "D10")] == "Capricorn"     # Taurus, even


def test_dwadashamsha_starts_from_itself():
    assert K.SIGN_NAMES[varga_sign(1.0, "D12")] == "Aries"
    assert K.SIGN_NAMES[varga_sign(3.0, "D12")] == "Taurus"


def test_trimshamsha_unequal_divisions_odd_sign():
    """Aries: Mars 5, Saturn 5, Jupiter 8, Mercury 7, Venus 5."""
    for deg, want in [(2.0, "Aries"), (7.0, "Aquarius"), (14.0, "Sagittarius"),
                      (20.0, "Gemini"), (27.0, "Libra")]:
        assert K.SIGN_NAMES[varga_sign(deg, "D30")] == want, deg


def test_trimshamsha_unequal_divisions_even_sign():
    """Taurus: Venus 5, Mercury 7, Jupiter 8, Saturn 5, Mars 5."""
    base = 30.0
    for deg, want in [(2.0, "Taurus"), (8.0, "Virgo"), (15.0, "Pisces"),
                      (22.0, "Capricorn"), (27.0, "Scorpio")]:
        assert K.SIGN_NAMES[varga_sign(base + deg, "D30")] == want, deg


def test_trimshamsha_never_maps_to_a_luminary_sign():
    """Trimshamsha uses only the five non-luminary planets' signs."""
    forbidden = {K.SIGN_NAMES.index("Cancer"), K.SIGN_NAMES.index("Leo")}
    lon = 0.0
    while lon < 360.0:
        assert varga_sign(lon, "D30") not in forbidden
        lon += 0.25


def test_d60_advances_every_half_degree():
    a = varga_sign(10.0, "D60")
    b = varga_sign(10.4, "D60")
    c = varga_sign(10.6, "D60")
    assert a == b
    assert c == (a + 1) % 12


def test_bhamsha_starts_by_element():
    for sign_name, want in [("Aries", "Aries"), ("Taurus", "Cancer"),
                            ("Gemini", "Libra"), ("Cancer", "Capricorn")]:
        sign = K.SIGN_NAMES.index(sign_name)
        assert K.SIGN_NAMES[varga_sign(sign * 30 + 0.1, "D27")] == want


# --------------------------------------------------------------------------
# Projection into a full varga chart
# --------------------------------------------------------------------------
def test_compute_varga_builds_twelve_houses():
    planets = {
        "Sun": {"longitude": 100.0, "sign": 3, "abbr": "Su", "retrograde": False},
        "Moon": {"longitude": 200.0, "sign": 6, "abbr": "Mo", "retrograde": False},
    }
    v = compute_varga(planets, ascendant=15.0, varga="D9")
    assert len(v["houses"]) == 12
    assert sorted(h["sign"] for h in v["houses"]) == list(range(12))
    for p in v["planets"].values():
        assert 1 <= p["house"] <= 12


def test_compute_varga_without_ascendant_suppresses_houses():
    planets = {"Sun": {"longitude": 100.0, "sign": 3, "abbr": "Su", "retrograde": False}}
    v = compute_varga(planets, ascendant=None, varga="D9")
    assert v["houses"] == []
    assert v["planets"]["Sun"]["house"] == 0


def test_vargottama_flag():
    """A planet in the same sign in D1 and D9 is vargottama."""
    # Aries 0-3d20' has its navamsa in Aries too.
    planets = {"Sun": {"longitude": 1.0, "sign": 0, "abbr": "Su", "retrograde": False}}
    v = compute_varga(planets, ascendant=1.0, varga="D9")
    assert v["planets"]["Sun"]["vargottama"] is True
