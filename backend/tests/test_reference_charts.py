"""Cross-check the engine against published birth charts.

These are the regression tests that matter. If a refactor moves a lagna across a
sign boundary, one of these fails.

Reference data comes from widely published Vedic charts (Astro-Databank birth
records, B. V. Raman's *Notable Horoscopes*). Sign placements are the assertion;
exact degrees are allowed a tolerance because sources disagree on the last
minute or two of birth time.
"""
from __future__ import annotations

import pytest

from app.jyotish import constants as K
from app.jyotish.timeutil import build_moment, lmt_offset
from app.jyotish.ephemeris import compute_chart


def chart_for(date, time, lat, lon, **kw):
    return compute_chart(build_moment(date, time, lat, lon, **kw), **{
        k: v for k, v in kw.items() if k in ("ayanamsa", "house_system", "node_type")
    })


# ---------------------------------------------------------------------------
# 1. Mahatma Gandhi -- 2 Oct 1869, 07:11:56 LMT, Porbandar (21N38, 69E36)
#    Published: Libra lagna, Sun in Virgo, Moon in Cancer / Ashlesha.
# ---------------------------------------------------------------------------
def test_gandhi():
    c = chart_for("1869-10-02", "07:11:56", 21.6417, 69.6293)
    assert c.houses[0]["sign_name"] == "Libra"
    assert c.planets["Sun"]["sign_name"] == "Virgo"
    assert c.planets["Moon"]["sign_name"] == "Cancer"
    assert c.planets["Moon"]["nakshatra_name"] == "Ashlesha"
    assert c.planets["Mars"]["sign_name"] == "Libra"
    assert c.planets["Venus"]["sign_name"] == "Libra"
    assert c.planets["Saturn"]["sign_name"] == "Scorpio"
    assert c.planets["Jupiter"]["retrograde"] is True
    # Pre-standard-time date must have auto-switched to Local Mean Time.
    assert c.moment["time_standard"] == "lmt"


def test_gandhi_lmt_matters():
    """The whole reason auto-LMT exists: the zone offset gives the wrong lagna."""
    zone = chart_for("1869-10-02", "07:11:56", 21.6417, 69.6293,
                     time_standard="zone")
    lmt = chart_for("1869-10-02", "07:11:56", 21.6417, 69.6293,
                    time_standard="lmt")
    assert zone.houses[0]["sign_name"] == "Virgo"     # wrong, Calcutta's clock
    assert lmt.houses[0]["sign_name"] == "Libra"      # right, Porbandar's clock


# ---------------------------------------------------------------------------
# 2. Albert Einstein -- 14 Mar 1879, 11:30 LMT, Ulm (48N24, 10E00)
#
#    Einstein's chart is published everywhere in *tropical* terms: Sun 23d30'
#    Pisces, Moon 14d32' Sagittarius, Ascendant ~11d Cancer. That makes it the
#    sharpest possible test of the sidereal conversion -- add the ayanamsa back
#    to our sidereal output and the published tropical figures must reappear.
# ---------------------------------------------------------------------------
def test_einstein_sidereal():
    c = chart_for("1879-03-14", "11:30:00", 48.4011, 9.9876)
    assert c.planets["Sun"]["sign_name"] == "Pisces"
    assert c.planets["Moon"]["sign_name"] == "Scorpio"
    assert K.SIGN_NAMES[c.ascendant_sign] == "Gemini"


def test_einstein_round_trips_to_published_tropical():
    c = chart_for("1879-03-14", "11:30:00", 48.4011, 9.9876)
    ay = c.ayanamsa_value

    def tropical(sid):
        return K.norm360(sid + ay)

    # Published tropical positions, degrees of absolute longitude.
    expected = {
        "Sun": 353.5,    # 23d30' Pisces
        "Moon": 254.5,   # 14d32' Sagittarius
    }
    for name, want in expected.items():
        got = tropical(c.planets[name]["longitude"])
        assert abs(((got - want + 180) % 360) - 180) < 0.5, (
            f"{name}: tropical {got:.2f} vs published {want}")

    asc_trop = tropical(c.ascendant)
    assert abs(asc_trop - 101.5) < 2.0, f"Asc tropical {asc_trop:.2f}, want ~11 Cancer"


# ---------------------------------------------------------------------------
# 3. Jawaharlal Nehru -- 14 Nov 1889, 23:03 LMT, Allahabad (25N27, 81E51)
#    Published: Cancer lagna, Moon in Cancer. The Sun sits right on the
#    Libra/Scorpio cusp sidereally and belongs to Scorpio by a quarter degree.
# ---------------------------------------------------------------------------
def test_nehru():
    c = chart_for("1889-11-14", "23:03:00", 25.4358, 81.8463)
    assert c.houses[0]["sign_name"] == "Cancer"
    assert c.planets["Moon"]["sign_name"] == "Cancer"
    assert c.planets["Sun"]["sign_name"] == "Scorpio"
    assert c.planets["Sun"]["degree_in_sign"] < 1.0


# ---------------------------------------------------------------------------
# 4. Sidereal vs tropical -- the single most common bug in Vedic software.
# ---------------------------------------------------------------------------
def test_zodiac_is_sidereal_not_tropical():
    """A chart cast for the spring equinox has the Sun at ~0 tropical Aries.

    Sidereally it must sit exactly one ayanamsa back from there, which lands it
    in Pisces. With the ayanamsa near 23.9 degrees and Pisces spanning 30, that
    is the first third of Pisces -- so assert the position, not a vague "end of
    Pisces".
    """
    c = chart_for("2000-03-20", "07:35:00", 28.6139, 77.2090)
    sun = c.planets["Sun"]["longitude"]
    assert 330.0 < sun < 360.0, f"Sun at {sun} looks tropical, not sidereal"
    assert c.planets["Sun"]["sign_name"] == "Pisces"
    # Ayanamsa for 2000 is close to 23d51'.
    assert 23.5 < c.ayanamsa_value < 24.2
    # The Sun must sit within a degree of (360 - ayanamsa).
    expected = K.norm360(360.0 - c.ayanamsa_value)
    assert abs(sun - expected) < 1.0, f"Sun {sun:.3f}, expected ~{expected:.3f}"


def test_ayanamsa_options_differ_and_are_ordered():
    kw = dict(date="2000-01-01", time="12:00:00", lat=28.6139, lon=77.2090)
    vals = {}
    for name in ("lahiri", "raman", "kp", "yukteshwar"):
        c = compute_chart(build_moment(kw["date"], kw["time"], kw["lat"], kw["lon"]),
                          ayanamsa=name)
        vals[name] = c.ayanamsa_value
    assert len({round(v, 4) for v in vals.values()}) == 4, "ayanamsas must differ"
    # Raman runs behind Lahiri; KP sits very close to Lahiri.
    assert vals["raman"] < vals["lahiri"]
    assert abs(vals["kp"] - vals["lahiri"]) < 0.2


# ---------------------------------------------------------------------------
# 5. Edge cases from the brief
# ---------------------------------------------------------------------------
def test_midnight_birth_keeps_correct_date():
    c = chart_for("2000-01-01", "00:00:00", 28.6139, 77.2090)
    assert c.moment["local"].startswith("2000-01-01T00:00")
    # IST is +5:30, so UTC lands on the previous evening.
    assert c.moment["utc"].startswith("1999-12-31T18:30")


def test_international_date_line():
    """Two points a few degrees apart across the line get different zones."""
    east = build_moment("2005-03-10", "23:30:00", -18.1416, 178.4419)   # Fiji
    west = build_moment("2005-03-10", "23:30:00", -13.7590, -172.1046)  # Samoa
    assert east.utc_offset_hours > 0
    assert west.utc_offset_hours < 0
    assert east.utc.date() != west.utc.date()


def test_extreme_latitude_whole_sign_still_works():
    c = chart_for("1990-06-21", "02:00:00", 69.6492, 18.9553)  # Tromso
    assert c.ascendant is not None
    assert len(c.houses) == 12


def test_extreme_latitude_placidus_warns():
    m = build_moment("1990-06-21", "02:00:00", 78.2232, 15.6267)  # Svalbard
    c = compute_chart(m, house_system="placidus")
    assert any("polar" in w.lower() for w in c.warnings)


def test_pre_1947_india_offset():
    """India unified to IST late; a 1905 Calcutta birth is not +5:30."""
    m = build_moment("1905-06-15", "10:00:00", 22.5726, 88.3639,
                     time_standard="zone")
    assert abs(m.utc_offset_hours - 5.5) > 0.1
    assert m.tz_abbrev == "MMT"


def test_unknown_birth_time_suppresses_lagna():
    c = compute_chart(build_moment("1990-05-05", None, 28.6139, 77.2090))
    assert c.time_known is False
    assert c.ascendant is None
    assert c.houses == []
    assert all(p["house"] == 0 for p in c.planets.values())
    assert any("time unknown" in w.lower() for w in c.warnings)
    # Sign-level data is still available.
    assert c.planets["Sun"]["sign_name"]
    assert c.planets["Moon"]["nakshatra_name"]


# ---------------------------------------------------------------------------
# 6. Internal consistency
# ---------------------------------------------------------------------------
def test_ketu_opposes_rahu():
    c = chart_for("1990-05-05", "10:30:00", 28.6139, 77.2090)
    sep = (c.planets["Ketu"]["longitude"] - c.planets["Rahu"]["longitude"]) % 360
    assert abs(sep - 180.0) < 1e-6
    assert (c.planets["Ketu"]["sign"] - c.planets["Rahu"]["sign"]) % 12 == 6


def test_every_planet_lands_in_a_house():
    c = chart_for("1990-05-05", "10:30:00", 28.6139, 77.2090)
    for name, p in c.planets.items():
        assert 1 <= p["house"] <= 12, name
        assert 0 <= p["sign"] <= 11
        assert 1 <= p["pada"] <= 4
        assert 0 <= p["nakshatra"] <= 26


def test_houses_cover_all_twelve_signs_whole_sign():
    c = chart_for("1990-05-05", "10:30:00", 28.6139, 77.2090)
    assert sorted(h["sign"] for h in c.houses) == list(range(12))


def test_dignity_table():
    assert __import__("app.jyotish.ephemeris", fromlist=["x"]).dignity_of("Sun", 0, 10.0) == "exalted"
    from app.jyotish.ephemeris import dignity_of
    assert dignity_of("Sun", 6, 10.0) == "debilitated"       # Libra
    assert dignity_of("Jupiter", 3, 5.0) == "exalted"        # Cancer
    assert dignity_of("Saturn", 6, 20.0) == "exalted"        # Libra
    assert dignity_of("Venus", 11, 27.0) == "exalted"        # Pisces
    assert dignity_of("Mars", 0, 5.0) == "moolatrikona"      # Aries 0-12
    assert dignity_of("Moon", 3, 15.0) == "own sign"         # Cancer


@pytest.mark.parametrize("lon,expected_nak,expected_pada", [
    (0.0, "Ashwini", 1),
    (13.0, "Ashwini", 4),
    (13.5, "Bharani", 1),
    (359.9, "Revati", 4),
    (120.0, "Magha", 1),
])
def test_nakshatra_boundaries(lon, expected_nak, expected_pada):
    assert K.NAKSHATRA_NAMES[K.nakshatra_of(lon)] == expected_nak
    assert K.pada_of(lon) == expected_pada
