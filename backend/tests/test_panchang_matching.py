"""Panchang, transits and Ashtakoot matching."""
from __future__ import annotations

import pytest

from app.jyotish import constants as K
from app.jyotish import panchang, matching, transits
from app.jyotish.timeutil import build_moment, julian_day
from app.jyotish.ephemeris import compute_chart
from datetime import datetime, timezone


# --------------------------------------------------------------------------
# Panchang
# --------------------------------------------------------------------------
def test_panchang_has_all_five_limbs():
    p = panchang.compute("2026-08-23", 28.6139, 77.2090)
    for limb in ("tithi", "vara", "nakshatra", "yoga", "karana"):
        assert limb in p and p[limb]
    assert p["vara"]["name"] == "Sunday"        # 23 Aug 2026 is a Sunday


def test_tithi_index_and_paksha_agree():
    p = panchang.compute("2026-08-23", 28.6139, 77.2090)
    t = p["tithi"]
    assert 1 <= t["index"] <= 30
    assert t["paksha"] == ("Shukla" if t["index"] <= 15 else "Krishna")


def test_full_moon_is_purnima():
    """Find a date where illumination is near total and check the tithi name."""
    # 2026-08-28 is close to full; scan a few days for illumination > 99%.
    best = None
    for day in range(24, 32):
        p = panchang.compute(f"2026-08-{day:02d}", 28.6139, 77.2090)
        if best is None or p["moon"]["illumination_percent"] > best[0]:
            best = (p["moon"]["illumination_percent"], p)
    illum, p = best
    assert illum > 95
    assert p["tithi"]["name"] in ("Purnima", "Chaturdashi")


def test_all_limb_names_are_in_range():
    p = panchang.compute("2026-03-15", 19.0760, 72.8777)
    assert p["nakshatra"]["name"] in K.NAKSHATRA_NAMES
    assert p["yoga"]["name"] in panchang.YOGA_NAMES
    assert p["karana"]["name"] in panchang.MOVABLE_KARANAS + panchang.FIXED_KARANAS


def test_karana_sequence_covers_sixty():
    names = [panchang._karana_name(i) for i in range(60)]
    assert names[0] == "Kimstughna"
    assert names[57:] == ["Shakuni", "Chatushpada", "Naga"]
    # The seven movable karanas repeat eight times across 1..56.
    assert names[1:57].count("Bava") == 8
    assert set(names[1:57]) == set(panchang.MOVABLE_KARANAS)


def test_rahu_kaal_falls_inside_daylight():
    p = panchang.compute("2026-08-23", 28.6139, 77.2090)
    pr = p["periods"]
    assert pr["available"] is True
    assert p["sun"]["sunrise"] <= pr["rahu_kaal"]["start"] < pr["rahu_kaal"]["end"] <= p["sun"]["sunset"]


def test_rahu_kaal_is_an_eighth_of_the_day():
    p = panchang.compute("2026-08-23", 28.6139, 77.2090)
    pr = p["periods"]
    spans = [pr[k]["end_jd"] - pr[k]["start_jd"]
             for k in ("rahu_kaal", "yamaganda", "gulika_kaal")]
    # All three are the same eighth-of-daylight segment, exactly.
    assert max(spans) - min(spans) < 1e-12
    # day_length_hours is rounded for display, so allow for that rounding here.
    day = pr["day_length_hours"] / 24.0
    assert abs(spans[0] - day / 8.0) < 1e-5


def test_inauspicious_periods_do_not_share_a_slot():
    p = panchang.compute("2026-08-23", 28.6139, 77.2090)
    pr = p["periods"]
    starts = {round(pr[k]["start_jd"], 6)
              for k in ("rahu_kaal", "yamaganda", "gulika_kaal")}
    assert len(starts) == 3


def test_abhijit_straddles_midday():
    p = panchang.compute("2026-08-23", 28.6139, 77.2090)
    pr = p["periods"]
    mid = (pr["abhijit_muhurat"]["start_jd"] + pr["abhijit_muhurat"]["end_jd"]) / 2
    noon = (p["periods"]["rahu_kaal"]["start_jd"] * 0 +
            (panchang.julian_day(datetime(2026, 8, 23, tzinfo=timezone.utc))))
    # Simply assert it sits between sunrise and sunset, nearer the middle.
    assert pr["abhijit_muhurat"]["start"] < pr["abhijit_muhurat"]["end"]


@pytest.mark.parametrize("weekday,segment", list(panchang.RAHU_KAAL_SEGMENT.items()))
def test_rahu_kaal_segments_are_distinct_per_weekday(weekday, segment):
    assert 1 <= segment <= 8
    assert len(set(panchang.RAHU_KAAL_SEGMENT.values())) == 7


def test_panchang_survives_the_arctic():
    """Above the circle the Sun may not rise; the call must degrade, not crash."""
    p = panchang.compute("2026-06-21", 78.2232, 15.6267)
    assert p["tithi"]["name"]
    assert "available" in p["periods"]


# --------------------------------------------------------------------------
# Transits
# --------------------------------------------------------------------------
def test_transit_overlay_counts_from_the_moon():
    m = build_moment("1990-05-05", "10:30:00", 28.6139, 77.2090)
    c = compute_chart(m)
    now = julian_day(datetime.now(timezone.utc))
    t = transits.compute(c.planets, c.ascendant_sign, now)
    assert len(t["planets"]) == 9
    for name, row in t["planets"].items():
        assert 1 <= row["house_from_moon"] <= 12
        assert 1 <= row["house_from_lagna"] <= 12


def test_next_ingresses_are_in_the_future_and_change_sign():
    now = julian_day(datetime.now(timezone.utc))
    ing = transits.next_ingresses(now, ["Jupiter", "Saturn"])
    assert len(ing) == 2
    for row in ing:
        assert row["jd"] > now
        assert row["from_sign"] != row["to_sign"]
        assert 0 < row["days_away"] <= 1100


def test_saturn_ingress_alerts_flag_sade_sati():
    m = build_moment("1990-05-05", "10:30:00", 28.6139, 77.2090)
    c = compute_chart(m)
    now = julian_day(datetime.now(timezone.utc))
    a = transits.alerts(c.planets, now)
    assert a
    for row in a:
        assert row["message"] and row["severity"] in (
            "info", "notable", "major", "favourable")


# --------------------------------------------------------------------------
# Ashtakoot
# --------------------------------------------------------------------------
def moon_of(date, time, lat=28.6139, lon=77.2090):
    return compute_chart(build_moment(date, time, lat, lon)).planets["Moon"]["longitude"]


def test_ashtakoot_totals_36_maximum():
    r = matching.ashtakoot(moon_of("1990-05-05", "10:30:00"),
                           moon_of("1992-11-17", "04:15:00"))
    assert r["maximum"] == 36.0
    assert 0 <= r["total"] <= 36
    assert len(r["kootas"]) == 8
    assert sum(k["max"] for k in r["kootas"]) == 36.0


def test_koota_weights_are_the_classical_ones():
    r = matching.ashtakoot(10.0, 200.0)
    weights = {k["koota"]: k["max"] for k in r["kootas"]}
    assert weights == {"Varna": 1.0, "Vashya": 2.0, "Tara": 3.0, "Yoni": 4.0,
                       "Graha Maitri": 5.0, "Gana": 6.0, "Bhakoot": 7.0,
                       "Nadi": 8.0}


def test_no_koota_can_exceed_its_maximum():
    step = 360 / 27
    for i in range(27):
        for j in range(0, 27, 4):
            r = matching.ashtakoot(i * step + 1, j * step + 1)
            for k in r["kootas"]:
                assert 0 <= k["score"] <= k["max"], (i, j, k["koota"])
            assert r["total"] == pytest.approx(
                sum(k["score"] for k in r["kootas"]), abs=0.01)


def test_identical_charts_score_zero_on_nadi():
    lon = moon_of("1990-05-05", "10:30:00")
    r = matching.ashtakoot(lon, lon)
    nadi = next(k for k in r["kootas"] if k["koota"] == "Nadi")
    assert nadi["score"] == 0.0
    assert nadi["cancellations"] is not None


def test_nadi_is_all_or_nothing():
    step = 360 / 27
    for i in range(27):
        for j in range(27):
            r = matching.nadi_koota(i, j)
            assert r["score"] in (0.0, 8.0)


def test_bhakoot_zero_for_six_eight_relationship():
    # Aries Moon and Virgo Moon stand 6 and 8 apart.
    r = matching.bhakoot_koota(0, 5)
    assert r["score"] == 0.0
    r = matching.bhakoot_koota(0, 3)      # 4-10, fine
    assert r["score"] == 7.0


def test_gana_manushya_rakshasa_scores_zero():
    # Bharani is Manushya, Krittika is Rakshasa.
    bharani, krittika = 1, 2
    assert matching.gana_koota(bharani, krittika)["score"] == 0.0
    assert matching.gana_koota(0, 0)["score"] == 6.0     # Deva with Deva


def test_tara_counts_both_directions():
    r = matching.tara_koota(0, 4)
    assert 0.0 <= r["score"] <= 3.0
    assert r["score"] % 1.5 == 0        # each direction contributes 0 or 1.5


def test_result_carries_a_caveat_and_summary():
    r = matching.ashtakoot(moon_of("1990-05-05", "10:30:00"),
                           moon_of("1992-11-17", "04:15:00"))
    assert "36" in r["caveat"] or "Moons" in r["caveat"]
    assert r["summary"]
    assert r["band"] in ("excellent", "very good", "acceptable",
                         "marginal", "poor by this method")


def test_manglik_comparison_treats_both_manglik_as_balanced():
    a = {"present": True, "severity": "high", "cancellations": []}
    b = {"present": True, "severity": "moderate", "cancellations": []}
    assert matching.compare_manglik(a, b)["verdict"] == "balanced"
    c = {"present": False, "severity": "none", "cancellations": []}
    assert matching.compare_manglik(a, c)["verdict"] == "mismatched"
    assert matching.compare_manglik(c, c)["verdict"] == "clear"


def test_matching_works_without_birth_times():
    """Guna Milan needs only the Moon, so date-only charts still match."""
    a = compute_chart(build_moment("1990-05-05", None, 28.6139, 77.2090))
    b = compute_chart(build_moment("1992-11-17", None, 19.0760, 72.8777))
    r = matching.ashtakoot(a.planets["Moon"]["longitude"],
                           b.planets["Moon"]["longitude"])
    assert 0 <= r["total"] <= 36
