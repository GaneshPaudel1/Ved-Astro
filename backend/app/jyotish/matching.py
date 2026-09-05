"""Kundli Milan -- Ashtakoot Guna Milan, the 36-point compatibility method.

Eight kootas, weighted 1 to 8, totalling 36. Every koota here is computed from
the two Moons' nakshatra and sign; none of it needs a birth *time*, which is
why matching still works for date-only charts.

The scoring tables are the standard ones. Two points deserve stating plainly in
the output, and the module does state them:

* Bhakoot and Nadi together are 15 of the 36 points, so a chart can score badly
  on arithmetic while being unremarkable in practice.
* This method weighs the Moons only. It says nothing about the rest of either
  chart, and it is one input to a decision that belongs to the people involved.
"""
from __future__ import annotations

from typing import Any

from . import constants as K

# --------------------------------------------------------------------------
# Varna (1 point) -- by Moon sign
# --------------------------------------------------------------------------
# Water signs Brahmin, Fire Kshatriya, Earth Vaishya, Air Shudra.
VARNA_BY_SIGN = {
    3: "Brahmin", 7: "Brahmin", 11: "Brahmin",
    0: "Kshatriya", 4: "Kshatriya", 8: "Kshatriya",
    1: "Vaishya", 5: "Vaishya", 9: "Vaishya",
    2: "Shudra", 6: "Shudra", 10: "Shudra",
}
VARNA_RANK = {"Shudra": 1, "Vaishya": 2, "Kshatriya": 3, "Brahmin": 4}

# --------------------------------------------------------------------------
# Vashya (2 points) -- by Moon sign group
# --------------------------------------------------------------------------
VASHYA_GROUP = {
    0: "Chatushpada", 1: "Chatushpada", 8: "Chatushpada", 9: "Chatushpada",
    2: "Manava", 5: "Manava", 6: "Manava", 10: "Manava",
    3: "Jalachara", 11: "Jalachara",
    4: "Vanachara",
    7: "Keeta",
}
# Sagittarius' first half is human, second half four-footed; Capricorn's second
# half is water-borne. Handled below where the degree is known.

VASHYA_SCORE = {
    ("Chatushpada", "Chatushpada"): 2.0, ("Chatushpada", "Manava"): 1.0,
    ("Chatushpada", "Jalachara"): 1.0, ("Chatushpada", "Vanachara"): 0.0,
    ("Chatushpada", "Keeta"): 1.0,
    ("Manava", "Manava"): 2.0, ("Manava", "Chatushpada"): 0.5,
    ("Manava", "Jalachara"): 1.0, ("Manava", "Vanachara"): 0.0,
    ("Manava", "Keeta"): 1.0,
    ("Jalachara", "Jalachara"): 2.0, ("Jalachara", "Chatushpada"): 1.0,
    ("Jalachara", "Manava"): 1.0, ("Jalachara", "Vanachara"): 0.0,
    ("Jalachara", "Keeta"): 1.0,
    ("Vanachara", "Vanachara"): 2.0, ("Vanachara", "Chatushpada"): 1.0,
    ("Vanachara", "Manava"): 0.0, ("Vanachara", "Jalachara"): 1.0,
    ("Vanachara", "Keeta"): 1.0,
    ("Keeta", "Keeta"): 2.0, ("Keeta", "Chatushpada"): 1.0,
    ("Keeta", "Manava"): 0.5, ("Keeta", "Jalachara"): 1.0,
    ("Keeta", "Vanachara"): 1.0,
}

# --------------------------------------------------------------------------
# Yoni (4 points) -- animal compatibility
# --------------------------------------------------------------------------
YONI_ENEMIES = {
    ("Horse", "Buffalo"), ("Elephant", "Lion"), ("Goat", "Monkey"),
    ("Serpent", "Mongoose"), ("Dog", "Deer"), ("Cat", "Rat"),
    ("Cow", "Tiger"), ("Monkey", "Goat"), ("Lion", "Elephant"),
    ("Buffalo", "Horse"), ("Mongoose", "Serpent"), ("Deer", "Dog"),
    ("Rat", "Cat"), ("Tiger", "Cow"),
}
YONI_FRIENDLY = {
    ("Horse", "Horse"), ("Elephant", "Elephant"), ("Goat", "Goat"),
    ("Serpent", "Serpent"), ("Dog", "Dog"), ("Cat", "Cat"), ("Rat", "Rat"),
    ("Cow", "Cow"), ("Buffalo", "Buffalo"), ("Tiger", "Tiger"),
    ("Deer", "Deer"), ("Monkey", "Monkey"), ("Mongoose", "Mongoose"),
    ("Lion", "Lion"),
}

# --------------------------------------------------------------------------
# Graha Maitri (5 points) -- friendship between the Moon-sign lords
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# Gana (6 points)
# --------------------------------------------------------------------------
GANA_SCORE = {
    ("Deva", "Deva"): 6.0, ("Deva", "Manushya"): 5.0, ("Deva", "Rakshasa"): 1.0,
    ("Manushya", "Deva"): 5.0, ("Manushya", "Manushya"): 6.0,
    ("Manushya", "Rakshasa"): 0.0,
    ("Rakshasa", "Deva"): 0.0, ("Rakshasa", "Manushya"): 0.0,
    ("Rakshasa", "Rakshasa"): 6.0,
}


def _nak(longitude: float) -> tuple[int, tuple]:
    idx = K.nakshatra_of(longitude)
    return idx, K.NAKSHATRAS[idx]


def _koota(name, sanskrit, score, maximum, verdict, explanation, detail=None):
    return {
        "koota": name, "sanskrit": sanskrit,
        "score": round(float(score), 2), "max": float(maximum),
        "verdict": verdict, "explanation": explanation, "detail": detail,
    }


# --------------------------------------------------------------------------
# The eight kootas
# --------------------------------------------------------------------------
def varna_koota(a_sign: int, b_sign: int) -> dict[str, Any]:
    """Bride's varna should not rank below the groom's."""
    a_varna, b_varna = VARNA_BY_SIGN[a_sign], VARNA_BY_SIGN[b_sign]
    score = 1.0 if VARNA_RANK[a_varna] >= VARNA_RANK[b_varna] else 0.0
    return _koota(
        "Varna", "Varna", score, 1,
        "compatible" if score else "not counted",
        f"The first partner's Moon sign is {a_varna}, the second's is {b_varna}.",
        "Varna compares the temperament and outlook the two Moon signs imply. "
        "It carries the least weight of the eight, one point out of 36.",
    )


def vashya_koota(a_sign: int, b_sign: int) -> dict[str, Any]:
    a_group, b_group = VASHYA_GROUP[a_sign], VASHYA_GROUP[b_sign]
    score = VASHYA_SCORE.get((a_group, b_group), 0.0)
    return _koota(
        "Vashya", "Vashya", score, 2,
        _verdict(score, 2),
        f"{K.SIGN_NAMES[a_sign]} is {a_group}; {K.SIGN_NAMES[b_sign]} is {b_group}.",
        "Vashya asks who naturally accommodates whom -- the balance of "
        "influence rather than dominance.",
    )


def tara_koota(a_nak: int, b_nak: int) -> dict[str, Any]:
    """Counted both ways; each direction is worth half the points."""
    def half(from_nak: int, to_nak: int) -> float:
        count = ((to_nak - from_nak) % 27) + 1
        remainder = count % 9
        # 3rd, 5th and 7th of the nine taras are the inauspicious ones.
        return 0.0 if remainder in (3, 5, 7) else 1.5

    score = half(a_nak, b_nak) + half(b_nak, a_nak)
    return _koota(
        "Tara", "Tara", score, 3,
        _verdict(score, 3),
        f"Counting between {K.NAKSHATRA_NAMES[a_nak]} and "
        f"{K.NAKSHATRA_NAMES[b_nak]} in both directions.",
        "Tara measures the birth stars against each other for mutual "
        "well-being. It is counted in both directions and scored separately "
        "for each.",
    )


def yoni_koota(a_nak: int, b_nak: int) -> dict[str, Any]:
    a_yoni, a_sex = K.NAKSHATRAS[a_nak][6], K.NAKSHATRAS[a_nak][7]
    b_yoni, b_sex = K.NAKSHATRAS[b_nak][6], K.NAKSHATRAS[b_nak][7]

    if (a_yoni, b_yoni) in YONI_FRIENDLY and a_yoni == b_yoni:
        score = 4.0 if a_sex != b_sex else 3.0
    elif (a_yoni, b_yoni) in YONI_ENEMIES:
        score = 0.0
    else:
        score = 2.0

    return _koota(
        "Yoni", "Yoni", score, 4,
        _verdict(score, 4),
        f"{a_yoni} and {b_yoni}.",
        "Yoni pairs each nakshatra with an animal and compares the two for "
        "physical and instinctive compatibility. Matched animals score "
        "highest; traditional enemies score nothing.",
    )


def graha_maitri_koota(a_sign: int, b_sign: int) -> dict[str, Any]:
    a_lord, b_lord = K.SIGN_LORDS[a_sign], K.SIGN_LORDS[b_sign]

    def relation(x: str, y: str) -> str:
        if x == y:
            return "same"
        if y in K.NATURAL_FRIENDS.get(x, set()):
            return "friend"
        if y in K.NATURAL_ENEMIES.get(x, set()):
            return "enemy"
        return "neutral"

    r1, r2 = relation(a_lord, b_lord), relation(b_lord, a_lord)
    pair = {r1, r2}
    if "same" in pair:
        score = 5.0
    elif pair == {"friend"}:
        score = 5.0
    elif pair == {"friend", "neutral"}:
        score = 4.0
    elif pair == {"neutral"}:
        score = 3.0
    elif pair == {"friend", "enemy"}:
        score = 1.0
    elif pair == {"neutral", "enemy"}:
        score = 0.5
    else:
        score = 0.0

    return _koota(
        "Graha Maitri", "Graha Maitri", score, 5,
        _verdict(score, 5),
        f"{a_lord} rules {K.SIGN_NAMES[a_sign]}; {b_lord} rules "
        f"{K.SIGN_NAMES[b_sign]}. They are {r1}/{r2}.",
        "Friendship between the two Moon-sign lords. This is the koota most "
        "directly about mental affinity -- whether the two minds find each "
        "other easy company.",
    )


def gana_koota(a_nak: int, b_nak: int) -> dict[str, Any]:
    a_gana, b_gana = K.NAKSHATRAS[a_nak][4], K.NAKSHATRAS[b_nak][4]
    score = GANA_SCORE.get((a_gana, b_gana), 0.0)
    return _koota(
        "Gana", "Gana", score, 6,
        _verdict(score, 6),
        f"{a_gana} and {b_gana}.",
        "Gana sorts the nakshatras into divine, human and demonic "
        "temperaments -- broadly, how each person handles conflict. A "
        "Manushya-Rakshasa pairing is the one classical texts warn about.",
    )


def bhakoot_koota(a_sign: int, b_sign: int) -> dict[str, Any]:
    """Zero when the Moon signs stand 6/8 or 5/9 apart."""
    forward = ((b_sign - a_sign) % 12) + 1
    backward = ((a_sign - b_sign) % 12) + 1
    pair = tuple(sorted([forward, backward]))
    bad = {(6, 8), (5, 9), (2, 12)}
    score = 0.0 if pair in bad else 7.0
    label = {(6, 8): "6-8 (Shadashtak)", (5, 9): "5-9 (Navam-Pancham)",
             (2, 12): "2-12 (Dwir-Dwadash)"}.get(pair)
    return _koota(
        "Bhakoot", "Bhakoot", score, 7,
        _verdict(score, 7),
        f"The Moon signs stand {forward} and {backward} from each other"
        + (f" -- a {label} relationship." if label else "."),
        "Bhakoot compares the two Moon signs' positions. It is worth seven "
        "points, so a single unfavourable arrangement costs nearly a fifth of "
        "the total -- one reason arithmetic alone should not decide anything.",
    )


def nadi_koota(a_nak: int, b_nak: int) -> dict[str, Any]:
    a_nadi, b_nadi = K.NAKSHATRAS[a_nak][5], K.NAKSHATRAS[b_nak][5]
    score = 0.0 if a_nadi == b_nadi else 8.0
    return _koota(
        "Nadi", "Nadi", score, 8,
        _verdict(score, 8),
        f"Both are {a_nadi} nadi." if score == 0 else f"{a_nadi} and {b_nadi}.",
        "Nadi is the heaviest single koota at eight points, and it is all or "
        "nothing: a shared nadi scores zero. Classical texts read it as "
        "constitutional similarity. It is also the koota most often set aside "
        "when other factors are strong.",
    )


def _verdict(score: float, maximum: float) -> str:
    if maximum == 0:
        return "n/a"
    ratio = score / maximum
    if ratio >= 0.99:
        return "excellent"
    if ratio >= 0.66:
        return "good"
    if ratio >= 0.34:
        return "moderate"
    if ratio > 0:
        return "weak"
    return "none"


# --------------------------------------------------------------------------
# Exceptions that cancel Bhakoot and Nadi
# --------------------------------------------------------------------------
def _bhakoot_cancellations(a_sign, b_sign, a_nak, b_nak) -> list[str]:
    out = []
    if K.SIGN_LORDS[a_sign] == K.SIGN_LORDS[b_sign]:
        out.append("Both Moon signs share the same lord, which classical texts "
                   "accept as cancelling Bhakoot dosha.")
    a_lord, b_lord = K.SIGN_LORDS[a_sign], K.SIGN_LORDS[b_sign]
    if (b_lord in K.NATURAL_FRIENDS.get(a_lord, set())
            and a_lord in K.NATURAL_FRIENDS.get(b_lord, set())):
        out.append("The two Moon-sign lords are mutual friends, which softens "
                   "the Bhakoot result.")
    return out


def _nadi_cancellations(a_sign, b_sign, a_nak, b_nak) -> list[str]:
    out = []
    if a_nak == b_nak and a_sign != b_sign:
        out.append("The birth star is the same but the Moon signs differ, "
                   "a recognised exception to Nadi dosha.")
    if a_sign == b_sign and a_nak != b_nak:
        out.append("The Moon signs are the same but the birth stars differ, "
                   "a recognised exception to Nadi dosha.")
    if K.SIGN_LORDS[a_sign] == K.SIGN_LORDS[b_sign]:
        out.append("Both Moon signs share the same lord.")
    return out


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
def ashtakoot(a_moon_longitude: float, b_moon_longitude: float,
              a_label: str = "First person",
              b_label: str = "Second person") -> dict[str, Any]:
    a_nak, _ = _nak(a_moon_longitude)
    b_nak, _ = _nak(b_moon_longitude)
    a_sign = K.sign_of(a_moon_longitude)
    b_sign = K.sign_of(b_moon_longitude)

    kootas = [
        varna_koota(a_sign, b_sign),
        vashya_koota(a_sign, b_sign),
        tara_koota(a_nak, b_nak),
        yoni_koota(a_nak, b_nak),
        graha_maitri_koota(a_sign, b_sign),
        gana_koota(a_nak, b_nak),
        bhakoot_koota(a_sign, b_sign),
        nadi_koota(a_nak, b_nak),
    ]

    total = sum(k["score"] for k in kootas)

    for k in kootas:
        if k["koota"] == "Bhakoot" and k["score"] == 0:
            k["cancellations"] = _bhakoot_cancellations(a_sign, b_sign, a_nak, b_nak)
        if k["koota"] == "Nadi" and k["score"] == 0:
            k["cancellations"] = _nadi_cancellations(a_sign, b_sign, a_nak, b_nak)

    return {
        "total": round(total, 2),
        "maximum": 36.0,
        "percent": round(total / 36.0 * 100, 1),
        "band": _band(total),
        "summary": _summary(total, kootas),
        "kootas": kootas,
        "people": {
            a_label: {
                "moon_sign": K.SIGN_NAMES[a_sign],
                "nakshatra": K.NAKSHATRA_NAMES[a_nak],
                "pada": K.pada_of(a_moon_longitude),
                "gana": K.NAKSHATRAS[a_nak][4],
                "nadi": K.NAKSHATRAS[a_nak][5],
                "yoni": K.NAKSHATRAS[a_nak][6],
                "varna": VARNA_BY_SIGN[a_sign],
            },
            b_label: {
                "moon_sign": K.SIGN_NAMES[b_sign],
                "nakshatra": K.NAKSHATRA_NAMES[b_nak],
                "pada": K.pada_of(b_moon_longitude),
                "gana": K.NAKSHATRAS[b_nak][4],
                "nadi": K.NAKSHATRAS[b_nak][5],
                "yoni": K.NAKSHATRAS[b_nak][6],
                "varna": VARNA_BY_SIGN[b_sign],
            },
        },
        "caveat": ("Guna Milan compares the two Moons and nothing else. It "
                   "does not look at either chart's ascendant, dasha or "
                   "seventh house, and Bhakoot and Nadi alone account for 15 "
                   "of the 36 points. Treat the number as one input among "
                   "several, not a decision."),
    }


def _band(total: float) -> str:
    if total >= 32:
        return "excellent"
    if total >= 26:
        return "very good"
    if total >= 18:
        return "acceptable"
    if total >= 14:
        return "marginal"
    return "poor by this method"


def _summary(total: float, kootas: list[dict[str, Any]]) -> str:
    strong = [k["koota"] for k in kootas if k["verdict"] in ("excellent", "good")]
    weak = [k["koota"] for k in kootas if k["score"] == 0]
    parts = [f"{total:g} of 36 points."]
    if strong:
        parts.append("Strongest on " + ", ".join(strong) + ".")
    if weak:
        parts.append("No points from " + ", ".join(weak) + ".")
    if total >= 18:
        parts.append("Conventionally 18 or more is treated as workable.")
    else:
        parts.append("This falls below the conventional threshold of 18, "
                     "which is usually a prompt to look at the full charts "
                     "rather than to stop.")
    return " ".join(parts)


def compare_manglik(a_manglik: dict[str, Any],
                    b_manglik: dict[str, Any]) -> dict[str, Any]:
    """Cross-check Manglik status between two charts."""
    a_present = bool(a_manglik.get("present")) and a_manglik.get("severity") != "cancelled"
    b_present = bool(b_manglik.get("present")) and b_manglik.get("severity") != "cancelled"

    if a_present and b_present:
        verdict, note = "balanced", (
            "Both charts carry Manglik dosha. Tradition treats this as "
            "cancelling out -- the usual objection is to pairing one Manglik "
            "chart with a non-Manglik one.")
    elif not a_present and not b_present:
        verdict, note = "clear", "Neither chart carries an active Manglik dosha."
    else:
        which = "first" if a_present else "second"
        verdict, note = "mismatched", (
            f"Only the {which} chart carries an active Manglik dosha. This is "
            "the combination traditional practice raises; check the "
            "cancellations listed on that chart before drawing conclusions.")

    return {
        "verdict": verdict,
        "note": note,
        "first": {"present": a_present, "severity": a_manglik.get("severity"),
                  "cancellations": a_manglik.get("cancellations", [])},
        "second": {"present": b_present, "severity": b_manglik.get("severity"),
                   "cancellations": b_manglik.get("cancellations", [])},
    }
