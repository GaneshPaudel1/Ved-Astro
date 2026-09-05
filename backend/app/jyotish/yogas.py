"""Yoga detection.

A yoga is a named combination that classical texts treat as significant. Each
detector returns the planets involved and a plain-language reason, so the UI can
always show *why* something was flagged rather than asserting it.

Detection is deliberately conservative: where a text gives several competing
definitions, the stricter one is used. A false negative is a missing note; a
false positive tells someone they have a Raja yoga when they do not.
"""
from __future__ import annotations

from typing import Any

from . import constants as K
from .vargas import varga_sign


# --------------------------------------------------------------------------
# Relationship helpers
# --------------------------------------------------------------------------
def _house_of_sign(sign: int, asc_sign: int) -> int:
    return K.house_distance(asc_sign, sign)


def _lord_of_house(house: int, asc_sign: int) -> str:
    return K.SIGN_LORDS[(asc_sign + house - 1) % 12]


def _conjunct(p: dict, q: dict) -> bool:
    return p["sign"] == q["sign"]


def _aspects_sign(planet_name: str, from_sign: int, target_sign: int) -> bool:
    """Does this planet cast graha drishti on the target sign?"""
    distance = K.house_distance(from_sign, target_sign)
    return distance in ([7] + K.SPECIAL_ASPECTS.get(planet_name, []))


def _mutual_aspect(a_name: str, a: dict, b_name: str, b: dict) -> bool:
    return (_aspects_sign(a_name, a["sign"], b["sign"])
            and _aspects_sign(b_name, b["sign"], a["sign"]))


def _exchange(a_name: str, a: dict, b_name: str, b: dict) -> bool:
    """Parivartana: each sits in a sign the other owns."""
    return (a["sign"] in K.PLANET_OWNS.get(b_name, [])
            and b["sign"] in K.PLANET_OWNS.get(a_name, []))


def _connected(a_name: str, a: dict, b_name: str, b: dict) -> str | None:
    """How two planets are linked, if at all."""
    if a_name == b_name:
        return None
    if _conjunct(a, b):
        return "conjunction"
    if _exchange(a_name, a, b_name, b):
        return "exchange of signs"
    if _mutual_aspect(a_name, a, b_name, b):
        return "mutual aspect"
    return None


def _yoga(key, name, sanskrit, planets, houses, strength, summary, detail):
    return {
        "key": key, "name": name, "sanskrit": sanskrit,
        "planets": planets, "houses": houses,
        "strength": strength, "summary": summary, "detail": detail,
    }


# --------------------------------------------------------------------------
# Panch Mahapurusha
# --------------------------------------------------------------------------
_MAHAPURUSHA = {
    "Mars":    ("Ruchaka", "drive, courage and physical command"),
    "Mercury": ("Bhadra", "intelligence, speech and adaptability"),
    "Jupiter": ("Hamsa", "wisdom, ethics and teaching"),
    "Venus":   ("Malavya", "beauty, refinement and comfort"),
    "Saturn":  ("Sasha", "discipline, endurance and authority over structures"),
}


def panch_mahapurusha(planets, asc_sign) -> list[dict[str, Any]]:
    """A planet in its own or exaltation sign, standing in a kendra from lagna."""
    found = []
    for planet, (yoga_name, quality) in _MAHAPURUSHA.items():
        p = planets.get(planet)
        if not p:
            continue
        house = _house_of_sign(p["sign"], asc_sign)
        strong = p["dignity"] in ("exalted", "own sign", "moolatrikona")
        if strong and house in K.KENDRA_HOUSES:
            found.append(_yoga(
                f"mahapurusha_{yoga_name.lower()}",
                f"{yoga_name} Yoga", yoga_name,
                [planet], [house],
                "major",
                f"{planet} is {p['dignity']} in {p['sign_name']}, in the "
                f"{_ord(house)} house.",
                f"One of the five Mahapurusha ('great person') yogas. It forms "
                f"when {planet} stands in its own or exaltation sign in an angle "
                f"from the ascendant, and it emphasises {quality}.",
            ))
    return found


# --------------------------------------------------------------------------
# Individual named yogas
# --------------------------------------------------------------------------
def gaja_kesari(planets, asc_sign) -> list[dict[str, Any]]:
    """Jupiter in an angle from the Moon."""
    moon, jup = planets.get("Moon"), planets.get("Jupiter")
    if not moon or not jup:
        return []
    dist = K.house_distance(moon["sign"], jup["sign"])
    if dist not in K.KENDRA_HOUSES:
        return []
    return [_yoga(
        "gaja_kesari", "Gaja Kesari Yoga", "Gajakesari",
        ["Jupiter", "Moon"],
        [_house_of_sign(jup["sign"], asc_sign)] if asc_sign is not None else [],
        "major",
        f"Jupiter sits in the {_ord(dist)} house from the Moon.",
        "Named for the elephant and the lion. Jupiter angular to the Moon is "
        "read as steadiness of mind supported by good judgement, and a "
        "reputation that outlasts setbacks.",
    )]


def budhaditya(planets, asc_sign) -> list[dict[str, Any]]:
    """Sun and Mercury together."""
    sun, mer = planets.get("Sun"), planets.get("Mercury")
    if not sun or not mer or sun["sign"] != mer["sign"]:
        return []
    weakened = mer["combust"]
    return [_yoga(
        "budhaditya", "Budhaditya Yoga", "Budha-Aditya",
        ["Sun", "Mercury"],
        [_house_of_sign(sun["sign"], asc_sign)] if asc_sign is not None else [],
        "moderate" if not weakened else "weak",
        f"Sun and Mercury share {sun['sign_name']}."
        + (" Mercury is combust, which dims the result." if weakened else ""),
        "The Sun's clarity joined to Mercury's reasoning. Associated with "
        "analytical skill and articulate speech. Mercury never strays far from "
        "the Sun, so this is a common combination -- and it is weakened when "
        "Mercury sits too close and burns.",
    )]


def chandra_mangal(planets, asc_sign) -> list[dict[str, Any]]:
    moon, mars = planets.get("Moon"), planets.get("Mars")
    if not moon or not mars or moon["sign"] != mars["sign"]:
        return []
    return [_yoga(
        "chandra_mangal", "Chandra-Mangal Yoga", "Chandra-Mangala",
        ["Moon", "Mars"],
        [_house_of_sign(moon["sign"], asc_sign)] if asc_sign is not None else [],
        "moderate",
        f"Moon and Mars share {moon['sign_name']}.",
        "Emotion joined to drive. Classically linked to earning capacity and "
        "enterprise, though it can also show as a sharp temper.",
    )]


def raja_yogas(planets, asc_sign) -> list[dict[str, Any]]:
    """Kendra lord linked to trikona lord.

    The 1st house is both an angle and a trine, so its lord is excluded from one
    side of the pairing to avoid a planet forming a Raja yoga with itself.
    """
    if asc_sign is None:
        return []
    found = []
    seen = set()
    kendra_lords = {h: _lord_of_house(h, asc_sign) for h in K.KENDRA_HOUSES}
    trikona_lords = {h: _lord_of_house(h, asc_sign) for h in K.TRIKONA_HOUSES}

    for kh, kl in kendra_lords.items():
        for th, tl in trikona_lords.items():
            if kl == tl or kh == th:
                continue
            a, b = planets.get(kl), planets.get(tl)
            if not a or not b:
                continue
            link = _connected(kl, a, tl, b)
            if not link:
                continue
            pair = tuple(sorted([kl, tl]))
            if pair in seen:
                continue
            seen.add(pair)
            found.append(_yoga(
                f"raja_{pair[0]}_{pair[1]}".lower(),
                "Raja Yoga", "Raja",
                [kl, tl], sorted({kh, th}),
                "major",
                f"{kl} rules the {_ord(kh)} (an angle) and {tl} rules the "
                f"{_ord(th)} (a trine); they are linked by {link}.",
                "An angle carries the capacity to act; a trine carries merit "
                "and support. When their lords connect, the chart is read as "
                "able to convert opportunity into standing.",
            ))
    return found


def dhana_yogas(planets, asc_sign) -> list[dict[str, Any]]:
    """Links among the lords of the wealth houses: 2, 5, 9 and 11."""
    if asc_sign is None:
        return []
    wealth_houses = [2, 5, 9, 11]
    lords = {h: _lord_of_house(h, asc_sign) for h in wealth_houses}
    found, seen = [], set()
    for i, h1 in enumerate(wealth_houses):
        for h2 in wealth_houses[i + 1:]:
            l1, l2 = lords[h1], lords[h2]
            if l1 == l2:
                continue
            a, b = planets.get(l1), planets.get(l2)
            if not a or not b:
                continue
            link = _connected(l1, a, l2, b)
            if not link:
                continue
            pair = tuple(sorted([l1, l2]))
            if pair in seen:
                continue
            seen.add(pair)
            found.append(_yoga(
                f"dhana_{pair[0]}_{pair[1]}".lower(),
                "Dhana Yoga", "Dhana",
                [l1, l2], [h1, h2],
                "moderate",
                f"{l1} (lord of the {_ord(h1)}) and {l2} (lord of the "
                f"{_ord(h2)}) are linked by {link}.",
                "Dhana yogas connect the houses of accumulated wealth, earned "
                "income, fortune and gains. They describe capacity to build "
                "resources rather than a guarantee of any particular amount.",
            ))
    return found


def neecha_bhanga(planets, asc_sign) -> list[dict[str, Any]]:
    """Cancellation of debility.

    A debilitated planet is considered rescued when any classical condition
    holds. Each satisfied condition is listed so the reasoning stays visible.
    """
    if asc_sign is None:
        return []
    found = []
    for name, p in planets.items():
        if p["dignity"] != "debilitated":
            continue
        reasons = []
        dispositor = K.SIGN_LORDS[p["sign"]]
        disp = planets.get(dispositor)

        if disp:
            dh = _house_of_sign(disp["sign"], asc_sign)
            if dh in K.KENDRA_HOUSES:
                reasons.append(
                    f"{dispositor}, which rules the sign of debility, sits in "
                    f"the {_ord(dh)} house -- an angle from the ascendant")
            moon = planets.get("Moon")
            if moon and K.house_distance(moon["sign"], disp["sign"]) in K.KENDRA_HOUSES:
                reasons.append(f"{dispositor} is angular from the Moon")
            if _aspects_sign(dispositor, disp["sign"], p["sign"]):
                reasons.append(f"{dispositor} aspects the debilitated {name}")

        # The planet exalted in this sign, if it is angular.
        for other, (ex_sign, _) in K.EXALTATION.items():
            if ex_sign == p["sign"] and other in planets:
                oh = _house_of_sign(planets[other]["sign"], asc_sign)
                if oh in K.KENDRA_HOUSES:
                    reasons.append(
                        f"{other}, which is exalted in {p['sign_name']}, "
                        f"stands in the {_ord(oh)} house")

        # Exalted in navamsa.
        nav = varga_sign(p["longitude"], "D9")
        if K.EXALTATION.get(name, (None,))[0] == nav:
            reasons.append(f"{name} is exalted in the navamsa (D9)")

        if reasons:
            found.append(_yoga(
                f"neecha_bhanga_{name}".lower(),
                "Neecha Bhanga Raja Yoga", "Neecha Bhanga",
                [name], [_house_of_sign(p["sign"], asc_sign)],
                "major" if len(reasons) > 1 else "moderate",
                f"{name} is debilitated in {p['sign_name']}, but the debility "
                f"is cancelled.",
                "Cancellation of debility. Classically this is read as a "
                "difficult start in the matters of that planet, followed by "
                "unusual rise. Conditions met: " + "; ".join(reasons) + ".",
            ))
    return found


def parivartana_yogas(planets, asc_sign) -> list[dict[str, Any]]:
    """Two planets sitting in each other's signs."""
    if asc_sign is None:
        return []
    found, seen = [], set()
    names = [n for n in K.PLANETS if n not in ("Rahu", "Ketu")]
    for i, a_name in enumerate(names):
        for b_name in names[i + 1:]:
            a, b = planets.get(a_name), planets.get(b_name)
            if not a or not b or not _exchange(a_name, a, b_name, b):
                continue
            pair = tuple(sorted([a_name, b_name]))
            if pair in seen:
                continue
            seen.add(pair)
            h1 = _house_of_sign(a["sign"], asc_sign)
            h2 = _house_of_sign(b["sign"], asc_sign)
            dusthana = {h1, h2} & set(K.DUSTHANA_HOUSES)
            found.append(_yoga(
                f"parivartana_{pair[0]}_{pair[1]}".lower(),
                "Parivartana Yoga", "Parivartana",
                [a_name, b_name], [h1, h2],
                "moderate" if dusthana else "major",
                f"{a_name} and {b_name} occupy each other's signs.",
                "An exchange of signs ties two houses tightly together; the "
                "matters of each start to depend on the other."
                + (" One of them falls in a difficult house, so the link cuts "
                   "both ways." if dusthana else ""),
            ))
    return found


def kemadruma(planets, asc_sign) -> list[dict[str, Any]]:
    """The Moon with no planet in the signs adjacent to it, nor with it.

    Kemadruma is reported only when it is *not* cancelled. The classical
    cancellations (Kemadruma Bhanga) are well established, and an uncancelled
    reading of this yoga alarms people who do not in fact have it -- the same
    reason the rest of this module errs strict.
    """
    moon = planets.get("Moon")
    if not moon:
        return []
    neighbours = {(moon["sign"] - 1) % 12, moon["sign"], (moon["sign"] + 1) % 12}
    companions = [n for n, p in planets.items()
                  if n not in ("Moon", "Rahu", "Ketu") and p["sign"] in neighbours]
    if companions:
        return []

    cancellations: list[str] = []

    # 1. Any graha standing in an angle from the Moon itself.
    in_kendra = [n for n, p in planets.items()
                 if n != "Moon"
                 and K.house_distance(moon["sign"], p["sign"]) in K.KENDRA_HOUSES]
    if in_kendra:
        cancellations.append(
            f"{_join(in_kendra)} stand{'s' if len(in_kendra) == 1 else ''} in an "
            f"angle from the Moon")

    # 2. The Moon itself angular from the ascendant.
    if asc_sign is not None:
        mh = _house_of_sign(moon["sign"], asc_sign)
        if mh in K.KENDRA_HOUSES:
            cancellations.append(f"the Moon is angular from the lagna, in the "
                                 f"{_ord(mh)} house")

    # 3. A natural benefic aspecting the Moon.
    aspecting = [n for n in ("Jupiter", "Venus", "Mercury")
                 if n in planets
                 and _aspects_sign(n, planets[n]["sign"], moon["sign"])]
    if aspecting:
        cancellations.append(f"{_join(aspecting)} aspect{'s' if len(aspecting) == 1 else ''} "
                             f"the Moon")

    if cancellations:
        return [_yoga(
            "kemadruma_bhanga", "Kemadruma cancelled (Kemadruma Bhanga)", "Kemadruma Bhanga",
            ["Moon"],
            [_house_of_sign(moon["sign"], asc_sign)] if asc_sign is not None else [],
            "moderate",
            "The Moon stands alone, but the isolation is cancelled.",
            "Kemadruma would form -- no planet occupies the Moon's sign or "
            "either sign beside it -- but classical exceptions cancel it here: "
            + "; ".join(cancellations) + ". The cancelled form is read as early "
            "self-reliance that turns into genuine independence, rather than as "
            "the hardship the uncancelled yoga describes.",
        )]

    return [_yoga(
        "kemadruma", "Kemadruma Yoga", "Kemadruma",
        ["Moon"],
        [_house_of_sign(moon["sign"], asc_sign)] if asc_sign is not None else [],
        "caution",
        "No planet occupies the Moon's sign or either sign beside it, and no "
        "classical cancellation applies.",
        "An isolated Moon. Read as periods of feeling unsupported and having "
        "to rely on your own resources.",
    )]


def chandra_adhi_yoga(planets, asc_sign) -> list[dict[str, Any]]:
    """Benefics in the 6th, 7th and 8th from the Moon."""
    moon = planets.get("Moon")
    if not moon:
        return []
    targets = {6, 7, 8}
    hits = {n for n in ("Jupiter", "Venus", "Mercury")
            if n in planets
            and K.house_distance(moon["sign"], planets[n]["sign"]) in targets}
    if len(hits) < 2:
        return []
    return [_yoga(
        "chandra_adhi", "Chandra Adhi Yoga", "Adhi",
        sorted(hits) + ["Moon"], [],
        "moderate" if len(hits) == 2 else "major",
        f"{', '.join(sorted(hits))} occupy the 6th, 7th or 8th from the Moon.",
        "Benefics arranged around the Moon in these houses are read as quiet, "
        "durable support -- capable colleagues and a settled position.",
    )]


def vipreet_raja_yoga(planets, asc_sign) -> list[dict[str, Any]]:
    """Lords of 6, 8 or 12 placed in another of those houses."""
    if asc_sign is None:
        return []
    found = []
    for h in K.DUSTHANA_HOUSES:
        lord = _lord_of_house(h, asc_sign)
        p = planets.get(lord)
        if not p:
            continue
        ph = _house_of_sign(p["sign"], asc_sign)
        if ph in K.DUSTHANA_HOUSES and ph != h:
            label = {6: "Harsha", 8: "Sarala", 12: "Vimala"}[h]
            found.append(_yoga(
                f"vipreet_{label}".lower(),
                f"{label} Yoga (Vipreet Raja Yoga)", label,
                [lord], [h, ph],
                "moderate",
                f"{lord}, lord of the {_ord(h)}, sits in the {_ord(ph)}.",
                "A 'reversed' Raja yoga. When the lords of the difficult "
                "houses fall into each other, the harm they would do is turned "
                "against itself -- read as gain arriving through obstacles "
                "rather than in spite of them.",
            ))
    return found


def _ord(n: int) -> str:
    return {1: "1st", 2: "2nd", 3: "3rd", 21: "21st", 22: "22nd", 23: "23rd"}.get(
        n, f"{n}th")


def _join(items: list[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------
_DETECTORS = [
    panch_mahapurusha, gaja_kesari, budhaditya, chandra_mangal,
    raja_yogas, dhana_yogas, neecha_bhanga, parivartana_yogas,
    kemadruma, chandra_adhi_yoga, vipreet_raja_yoga,
]

_STRENGTH_RANK = {"major": 0, "moderate": 1, "weak": 2, "caution": 3}


def detect_all(planets: dict[str, dict[str, Any]],
               asc_sign: int | None) -> list[dict[str, Any]]:
    """Run every detector. Results are ordered strongest first."""
    out: list[dict[str, Any]] = []
    for fn in _DETECTORS:
        try:
            out.extend(fn(planets, asc_sign))
        except Exception:            # one bad detector must not lose the rest
            continue
    out.sort(key=lambda y: (_STRENGTH_RANK.get(y["strength"], 9), y["name"]))
    return out
