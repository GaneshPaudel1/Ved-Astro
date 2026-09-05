"""The interpretation layer.

The boundary this file draws is the point of the whole design: everything above
it is *calculated astrological data*, everything below is *generated text*. The
engine receives a finished chart bundle and returns readable sections. It never
computes a longitude and the calculation modules never build a sentence.

Swapping in a model-backed engine later means implementing `Interpreter` and
registering it. Nothing in `app.jyotish` changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..jyotish import constants as K
from .rules import text as T


# --------------------------------------------------------------------------
# The interface
# --------------------------------------------------------------------------
@dataclass
class Section:
    key: str
    title: str
    body: str
    tags: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "title": self.title, "body": self.body,
                "tags": self.tags, "evidence": self.evidence}


@dataclass
class Reading:
    engine: str
    sections: list[Section]
    disclaimer: str = T.GENERAL_DISCLAIMER

    def to_dict(self) -> dict[str, Any]:
        return {"engine": self.engine,
                "sections": [s.to_dict() for s in self.sections],
                "disclaimer": self.disclaimer}


class Interpreter(Protocol):
    """Any interpretation backend implements this and nothing more."""

    name: str

    def interpret(self, bundle: dict[str, Any]) -> Reading:
        ...


# --------------------------------------------------------------------------
# Rule-based implementation
# --------------------------------------------------------------------------
class RuleBasedInterpreter:
    """Deterministic, template-driven. Same chart in, same words out."""

    name = "rule-based-v1"

    def interpret(self, bundle: dict[str, Any]) -> Reading:
        chart = bundle.get("chart") or {}
        sections: list[Section] = []

        for builder in (self._lagna, self._moon, self._chart_shape,
                        self._current_dasha, self._yogas, self._doshas,
                        self._strengths, self._remedies):
            try:
                s = builder(bundle, chart)
            except Exception:
                continue
            if s:
                sections.extend(s if isinstance(s, list) else [s])

        return Reading(engine=self.name, sections=sections)

    # ---------------------------------------------------------------- lagna
    def _lagna(self, bundle, chart):
        if not chart.get("time_known"):
            return Section(
                "lagna", "Ascendant unavailable",
                "Without a birth time the ascendant cannot be calculated, so "
                "everything that depends on it -- house placements, the lagna "
                "reading, and the divisional charts built from it -- is left "
                "out. The Moon-based reading below still stands, and so does "
                "the Panchang for your birth date.",
                tags=["lagna-uncertain"])

        sign = chart.get("ascendant_sign_name")
        if not sign or sign not in T.LAGNA:
            return None
        data = T.LAGNA[sign]
        lord = chart.get("ascendant_lord")
        lord_p = (chart.get("planets") or {}).get(lord, {})

        body = f"{data['keynote']} {data['body']}"
        evidence = [f"Ascendant at {chart.get('ascendant_degree_str')} "
                    f"{sign} ({K.SIGN_SANSKRIT[K.SIGN_NAMES.index(sign)]}), "
                    f"in {chart.get('ascendant_nakshatra')} nakshatra, "
                    f"pada {chart.get('ascendant_pada')}."]

        if lord_p:
            dignity = T.DIGNITY.get(lord_p.get("dignity", ""), "")
            house = lord_p.get("house")
            body += (f"\n\n{lord} rules your ascendant and sits in the "
                     f"{_ord(house)} house -- {T.HOUSE_SHORT.get(house, '')} -- "
                     f"{dignity}. That places the running theme of your chart "
                     f"there.")
            evidence.append(
                f"Lagna lord {lord} in {lord_p.get('sign_name')} "
                f"{lord_p.get('degree_str')}, house {house}, "
                f"{lord_p.get('dignity')}.")

        return Section("lagna", f"{sign} rising", body,
                       tags=["lagna", sign.lower()], evidence=evidence)

    # ----------------------------------------------------------------- moon
    def _moon(self, bundle, chart):
        moon = (chart.get("planets") or {}).get("Moon")
        if not moon:
            return None
        sign = moon["sign_name"]
        nak = moon["nakshatra_name"]
        nak_data = next((n for n in K.NAKSHATRAS if n[0] == nak), None)

        body = T.MOON_SIGN.get(sign, "")
        if nak_data:
            _, lord, deity, symbol, gana, nadi, yoni, _ = nak_data
            body += (f"\n\nYour birth star is {nak} (pada {moon['pada']}), "
                     f"ruled by {lord}, with {deity} as its deity and the "
                     f"{symbol.lower()} as its symbol. This is the measurement "
                     f"the whole Vimshottari dasha sequence is built from -- "
                     f"how far the Moon had travelled through {nak} at the "
                     f"moment you were born decided which planetary period you "
                     f"were born into.")

        if not chart.get("time_known"):
            body += ("\n\nBecause the birth time is unknown, the Moon's "
                     "position is calculated for midday and may be off by up "
                     "to about six degrees. If that places it near the edge of "
                     "a nakshatra, the dasha sequence could differ.")

        return Section("moon", f"Moon in {sign}", body,
                       tags=["moon", sign.lower(), nak.lower()],
                       evidence=[f"Moon at {moon['degree_str']} {sign}, "
                                 f"{nak} pada {moon['pada']}."])

    # ---------------------------------------------------------- chart shape
    def _chart_shape(self, bundle, chart):
        planets = chart.get("planets") or {}
        if not planets or not chart.get("time_known"):
            return None

        by_house: dict[int, list[str]] = {}
        for name, p in planets.items():
            by_house.setdefault(p["house"], []).append(name)

        stelliums = {h: ps for h, ps in by_house.items() if len(ps) >= 3}
        retro = [n for n, p in planets.items()
                 if p["retrograde"] and n not in ("Rahu", "Ketu")]
        combust = [n for n, p in planets.items() if p["combust"]]
        exalted = [n for n, p in planets.items() if p["dignity"] == "exalted"]
        debilitated = [n for n, p in planets.items() if p["dignity"] == "debilitated"]

        lines = []
        for h, ps in sorted(stelliums.items()):
            lines.append(
                f"Three or more planets ({', '.join(ps)}) gather in your "
                f"{_ord(h)} house, which concentrates the chart on "
                f"{T.HOUSE_SHORT.get(h, 'that area')}.")
        if exalted:
            lines.append(f"{_join(exalted)} {_isare(exalted)} exalted -- "
                         f"strongest possible placement by sign.")
        if debilitated:
            lines.append(
                f"{_join(debilitated)} {_isare(debilitated)} debilitated. "
                f"Check the yoga list below: classical rules often cancel this.")
        if retro:
            lines.append(
                f"{_join(retro)} {_isare(retro)} retrograde. A retrograde "
                f"planet is read as turned inward -- its matters get revisited "
                f"rather than resolved first time.")
        if combust:
            lines.append(
                f"{_join(combust)} {_isare(combust)} combust, sitting too close "
                f"to the Sun to act freely.")

        if not lines:
            return None
        return Section("shape", "What stands out", "\n\n".join(lines),
                       tags=["overview"])

    # --------------------------------------------------------------- dasha
    def _current_dasha(self, bundle, chart):
        path = bundle.get("dasha_path") or []
        if not path:
            return None
        maha = path[0]
        lord = maha["lord"]
        info = T.DASHA.get(lord)
        if not info:
            return None

        planets = chart.get("planets") or {}
        p = planets.get(lord, {})

        body = (f"You are running the {lord} Mahadasha -- {info['theme']}\n\n"
                f"{info['body']}\n\n"
                f"It began {maha['start']} and runs to {maha['end']}, and it is "
                f"{maha['elapsed_percent']:.0f}% through with "
                f"{maha['remaining']} remaining.")

        if p and chart.get("time_known"):
            body += (f"\n\nIn your chart {lord} sits in {p['sign_name']} in the "
                     f"{_ord(p['house'])} house -- {T.HOUSE_SHORT.get(p['house'], '')} "
                     f"-- and is {T.DIGNITY.get(p['dignity'], p['dignity'])}. "
                     f"That is where this period is most likely to show itself.")

        if len(path) > 1:
            sub = path[1]
            sub_info = T.DASHA.get(sub["lord"], {})
            body += (f"\n\nInside it, the {sub['lord']} Antardasha runs "
                     f"{sub['start']} to {sub['end']}. "
                     f"{sub_info.get('theme', '')} A sub-period colours the "
                     f"larger one rather than replacing it.")

        if len(path) > 2:
            names = " -> ".join(f"{n['lord']} ({n['level_name']})" for n in path[2:])
            body += f"\n\nFiner levels running now: {names}."

        return Section("dasha", f"{lord} Mahadasha", body,
                       tags=["dasha", lord.lower()],
                       evidence=[f"Birth nakshatra "
                                 f"{bundle.get('dasha', {}).get('birth_nakshatra')}; "
                                 f"balance at birth "
                                 f"{bundle.get('dasha', {}).get('balance_at_birth', {}).get('readable')}."])

    # --------------------------------------------------------------- yogas
    def _yogas(self, bundle, chart):
        found = bundle.get("yogas") or []
        if not found:
            return None
        top = found[:3]
        parts = []
        for y in top:
            parts.append(f"**{y['name']}** -- {y['summary']} {y['detail']}")
        body = "\n\n".join(parts)
        if len(found) > 3:
            rest = ", ".join(y["name"] for y in found[3:])
            body += f"\n\nAlso present: {rest}."
        return Section("yogas", "Combinations in your chart", body,
                       tags=["yogas"],
                       evidence=[f"{len(found)} yoga(s) detected."])

    # -------------------------------------------------------------- doshas
    def _doshas(self, bundle, chart):
        d = bundle.get("doshas") or {}
        parts, tags = [], []

        m = d.get("manglik") or {}
        if m.get("present"):
            tags.append("manglik")
            refs = ", ".join(f"the {_ord(h['house'])} from the {h['reference']}"
                             for h in m.get("hits", []))
            line = (f"**Manglik (Kuja) dosha** -- Mars falls in {refs}. "
                    f"Severity is judged {m['severity']}.")
            if m.get("cancellations"):
                line += (" It is considered cancelled: "
                         + " ".join(m["cancellations"]))
            line += f" {m.get('note', '')}"
            parts.append(line)

        ks = d.get("kaal_sarp") or {}
        if ks.get("present"):
            tags.append("kaal-sarp")
            parts.append(
                f"**Kaal Sarp dosha** ({ks.get('type') or 'unnamed type'}) -- "
                f"{ks.get('rule')} {ks.get('note')}")
        elif ks.get("partial"):
            parts.append(
                f"**Partial Kaal Sarp** -- every planet but "
                f"{_join(ks.get('breaking_planet', []))} lies on one side of "
                f"the Rahu-Ketu axis, so the full dosha does not form.")

        ss = d.get("sade_sati") or {}
        if ss.get("currently_active"):
            tags.append("sade-sati")
            ph = ss["current_phase"]
            parts.append(
                f"**Sade Sati -- {ph['phase']} phase**, running "
                f"{ph['start']} to {ph['end']}. {ph['description']} "
                f"{ss.get('note', '')}")
        elif ss.get("phases"):
            # "Next" must mean the next one still ahead. Filtering only on
            # `current` picks the earliest phase on record, which for an adult
            # chart is usually one that finished years ago.
            now_jd = bundle.get("now_jd") or 0.0
            future = [p for p in ss["phases"] if p["start_jd"] > now_jd]
            past = [p for p in ss["phases"] if p["end_jd"] <= now_jd]
            bits = ["Sade Sati is not running now."]
            if past:
                first, last = past[0], past[-1]
                bits.append(
                    f"The last cycle ran {first['start']} to {last['end']}.")
            if future:
                nxt = future[0]
                bits.append(
                    f"The next begins {nxt['start']} ({nxt['phase']} phase, "
                    f"Saturn entering {nxt['sign_name']}).")
            parts.append(" ".join(bits))

        pit = d.get("pitra") or {}
        if pit.get("present"):
            tags.append("pitra")
            parts.append("**Pitra dosha indicators** -- "
                         + " ".join(pit.get("indicators", []))
                         + f" {pit.get('note', '')}")

        if not parts:
            return Section("doshas", "Doshas",
                           "No Manglik, Kaal Sarp or Pitra dosha is indicated, "
                           "and Sade Sati is not currently running.",
                           tags=["doshas", "clear"])
        return Section("doshas", "Doshas", "\n\n".join(parts),
                       tags=["doshas"] + tags)

    # ----------------------------------------------------------- strengths
    def _strengths(self, bundle, chart):
        av = bundle.get("ashtakavarga")
        if not av or not chart.get("time_known"):
            return None
        signs = av.get("signs") or []
        if not signs:
            return None
        best = max(signs, key=lambda s: s["sav"])
        worst = min(signs, key=lambda s: s["sav"])
        body = (
            f"Your Sarvashtakavarga puts most support in {best['sign_name']} "
            f"({best['sav']} bindus), your {_ord(best['house'])} house -- "
            f"{T.HOUSE_SHORT.get(best['house'], '')}. The thinnest is "
            f"{worst['sign_name']} ({worst['sav']}), your "
            f"{_ord(worst['house'])} house -- "
            f"{T.HOUSE_SHORT.get(worst['house'], '')}.\n\n"
            f"Bindus measure how much support a sign has across the whole "
            f"chart. The twelve always total 337, so this is about where your "
            f"chart concentrates its strength, not an absolute score."
        )
        return Section("ashtakavarga", "Where your chart is strongest", body,
                       tags=["ashtakavarga"])

    # ------------------------------------------------------------ remedies
    def _remedies(self, bundle, chart):
        path = bundle.get("dasha_path") or []
        planets = (chart.get("chart") or chart).get("planets") or {}
        targets: list[str] = []

        if path:
            targets.append(path[0]["lord"])
        for name, p in planets.items():
            if p.get("dignity") == "debilitated" and name not in targets:
                targets.append(name)
        targets = [t for t in targets if t in T.REMEDIES][:3]
        if not targets:
            return None

        parts = []
        for t in targets:
            r = T.REMEDIES[t]
            parts.append(
                f"**{t}** -- {r['day']} is its day. Mantra: {r['mantra']}. "
                f"Traditional gemstone: {r['gemstone']}. "
                f"Customary practice: {r['practice']}")

        return Section(
            "remedies", "Traditional practices",
            "\n\n".join(parts) + "\n\n" + T.REMEDY_DISCLAIMER,
            tags=["remedies"])


# --------------------------------------------------------------------------
# Registry -- how a different engine gets swapped in later
# --------------------------------------------------------------------------
_REGISTRY: dict[str, Interpreter] = {}


def register(interpreter: Interpreter) -> None:
    _REGISTRY[interpreter.name] = interpreter


def get(name: str | None = None) -> Interpreter:
    if name and name in _REGISTRY:
        return _REGISTRY[name]
    return _REGISTRY["rule-based-v1"]


def available() -> list[str]:
    return sorted(_REGISTRY)


register(RuleBasedInterpreter())


# --------------------------------------------------------------------------
# Small text helpers
# --------------------------------------------------------------------------
def _ord(n: int | None) -> str:
    if not n:
        return "-"
    return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")


def _join(items: list[str]) -> str:
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _isare(items: list[str]) -> str:
    return "is" if len(items) == 1 else "are"
