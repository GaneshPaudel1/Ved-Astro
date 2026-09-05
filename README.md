# Jyotish

A Vedic (sidereal) astrology calculator. The astronomy is the product, so the
engine is built on the Swiss Ephemeris and is checked against published birth
charts on every test run.

---

## Running it

Two processes: a Python API and a Vite dev server.

```bash
cd backend && pip install -r requirements.txt
```

```bash
cd backend && python -m uvicorn app.main:app --reload --port 8000
```

```bash
cd frontend && npm install && npm run dev
```

Then open <http://localhost:5173>. The frontend proxies `/api` to port 8000, so
the API must be on 8000 (or change the proxy in `frontend/vite.config.ts`).

**On Windows, `tzdata` is not optional.** Windows ships no IANA timezone
database, and without the package every historical UTC offset silently falls
back to UTC — which moves ascendants across sign boundaries. It is pinned in
`requirements.txt` for this reason.

### Checking the numbers

```bash
cd backend && python verify.py
```

Runs the verification checklist and prints a readable report: three published
charts, the sidereal/tropical distinction, the timezone edge cases, and the
120-year dasha identity.

```bash
cd backend && python -m pytest -q
```

202 tests. The reference-chart tests are the ones that matter — if a refactor
moves a lagna across a sign boundary, they fail.

---

## Why these choices

**Python, because of `pyswisseph`.** The whole product rests on the ephemeris,
and the Swiss Ephemeris Python binding is the most battle-tested option
available. Everything else was built around that decision. There is no
hand-rolled orbital mechanics anywhere in this repository.

**Sidereal, everywhere.** `FLG_SIDEREAL` is set on every single call and the
ayanamsa mode is set before each batch. Casting a Vedic chart against the
tropical zodiac is the most common bug in astrology software written by people
new to the domain; `test_zodiac_is_sidereal_not_tropical` exists to catch it.

**Whole-sign houses by default**, which is the classical Vedic bhava. Placidus,
Koch, Equal and Sripati are available, and Placidus/Koch degrade with an
explicit warning above the polar circles rather than pretending to a precision
they do not have.

### The timezone problem

A chart must use the UTC offset in force **at that place on that date**. Two
things follow, and both are implemented:

1. **Historical offsets.** Resolved through the IANA database, so a 1943 Indian
   birth correctly gets the wartime `+06:30` and a 1918 New York birth gets the
   first US daylight saving.

2. **Pre-standard time.** Before standard time reached a region, the clock on
   the wall was that *town's* Local Mean Time. The tz database answers with one
   particular city's mean time — `Asia/Kolkata` reports Howrah Mean Time
   (`+05:53:20`) for 1869 — which is wrong for anywhere else in the country.

   Gandhi is the worked example. Born at Porbandar (69.6°E) in 1869, the tz
   database offset is out by 1h15m, and that moves the ascendant a whole sign:

   | Clock used | Offset | Lagna |
   |---|---|---|
   | tz database (Howrah Mean Time) | `+05:53:20` | Virgo — **wrong** |
   | Local Mean Time for Porbandar | `+04:38:31` | **Libra** — matches published charts |

   `time_standard: "auto"` detects this (an offset that is not a whole multiple
   of 15 minutes cannot be a standard zone) and switches to Local Mean Time,
   attaching a warning to the chart explaining why. `"zone"` and `"lmt"` force
   either behaviour.

### Unknown birth time

Supported as a real case, not papered over. Positions are computed for 12:00
local — noon keeps the Moon's worst-case error smallest and the date stable
under any offset. The chart is then honest about what it cannot know: the
ascendant is `null`, houses are empty, every planet's house is `0`, divisional
charts are suppressed, and the lagna reading is replaced by an explanation.
Sign positions, nakshatras, dashas, Panchang and Guna Milan all still work,
because none of them need an ascendant.

---

## What it computes

| Area | Detail |
|---|---|
| **Grahas** | Nine, sidereal, with speed, retrograde, combustion, dignity, nakshatra and pada |
| **Lagna & houses** | Ascendant to the arcsecond, twelve cusps, five house systems |
| **Vargas** | All sixteen: D1 D2 D3 D4 D7 D9 D10 D12 D16 D20 D24 D27 D30 D40 D45 D60 |
| **Dashas** | Vimshottari to five levels (Mahadasha → Prana), plus Yogini (36y) and Ashtottari (108y) |
| **Yogas** | Panch Mahapurusha, Gaja Kesari, Raja, Dhana, Neecha Bhanga, Parivartana, Vipreet, Budhaditya, Chandra-Mangal, Kemadruma, Chandra Adhi |
| **Ashtakavarga** | Bhinnashtakavarga per planet and the Sarvashtakavarga total |
| **Doshas** | Manglik (with cancellations), Kaal Sarp, Sade Sati with a full timeline, Pitra |
| **Panchang** | Tithi, Vara, Nakshatra, Yoga, Karana with end times; rise/set; Rahu Kaal, Yamaganda, Gulika, Abhijit |
| **Transits** | Gochar from the natal Moon, ingress dates, Ashtakavarga bindus, alerts |
| **Matching** | Full Ashtakoot Guna Milan, 36 points, with Manglik cross-check |

Several of these tables are self-checking, which is why they are trustworthy:

- The nine Vimshottari periods sum to **exactly 120 years** (asserted to 1e-6).
- The seven Bhinnashtakavarga rows total **48, 49, 39, 54, 56, 52, 39** and the
  Sarvashtakavarga always totals **337** — in every chart, without exception.
- The 27 nakshatras split **9/9/9** across both gana and nadi, and each of the
  nine dasha lords rules exactly **3** of them.
- The eight kootas weigh **1+2+3+4+5+6+7+8 = 36**.

If a transcription error crept into any of those tables, these totals break.

---

## Layout

```
backend/
  app/
    jyotish/          the calculation engine — no text, no HTTP
      constants.py      classical reference tables
      timeutil.py       historical timezones, LMT, Julian Day
      ephemeris.py      sidereal positions, lagna, houses  ← the core
      vargas.py         the sixteen divisional charts
      dasha.py          Vimshottari, Yogini, Ashtottari
      yogas.py          combination detection
      ashtakavarga.py   bindu tables
      doshas.py         Manglik, Kaal Sarp, Sade Sati, Pitra
      panchang.py       the five limbs and the day's timings
      transits.py       gochar and ingresses
      matching.py       Ashtakoot Guna Milan
    interpret/        the text layer — no astronomy
      engine.py         the swappable interface
      rules/text.py     all the prose, as data
    main.py           FastAPI routes (thin)
    services.py       chart assembly and caching
  tests/            202 tests
  verify.py         the checklist, as a readable report
frontend/
  src/components/charts/   the kundli diagrams, drawn from geometry
  src/views/               one file per section
```

### The interpretation layer is deliberately separable

The brief calls for a rule-based engine now and an LLM later, so the seam is
real rather than nominal:

```python
class Interpreter(Protocol):
    name: str
    def interpret(self, bundle: dict) -> Reading: ...
```

Everything above that line is *calculated astrological data*; everything below
is *generated text*. `app/jyotish/` never builds a sentence and
`app/interpret/` never computes a longitude. Dropping in a model-backed engine
means implementing `Interpreter` and calling `register()` — no file in
`app/jyotish/` changes.

---

## The charts

Both layouts are drawn from geometry rather than a background image, so they
stay sharp at any size and every region is a real hit target.

**North Indian** — houses fixed, signs rotate. A square crossed by both
diagonals and by the rhombus joining the edge midpoints; each rhombus edge
meets one diagonal at a quarter point, giving twelve regions. House 1 is the
top diamond and the houses run anticlockwise.

**South Indian** — signs fixed, houses rotate. A 4×4 ring with Pisces top-left,
signs running clockwise, the middle 2×2 left empty, and the ascendant marked
with a corner stroke.

Both are verified structurally in the test suite rather than by eye.

---

## Design notes

The brief asked to avoid the astrology-app default of violet gradients, star
fields and script faces; the reference image supplied alongside it was a purple
cosmic landing page. Those pull in opposite directions, so the resolution here
takes the *depth* of the reference — a dark ground, generous space, real
orbital geometry — and drops the decoration. Colour is spent almost entirely on
the chart, where it carries dignity (exalted, debilitated, own sign,
retrograde) rather than atmosphere. **Say the word if you would rather have the
literal purple-cosmic treatment** — the palette is thirty-odd tokens in
`src/styles/tokens.css` and swapping it touches nothing else.

Type is a deliberate trio: **Fraunces** (display, with optical sizing),
**Instrument Sans** (body), **JetBrains Mono** (all degrees, bindus and tables,
so figures align in columns). Tiro Devanagari Sanskrit is loaded for Devanagari.

Light mode is not an inversion — the ground becomes warm paper and the chart is
drawn in ink, which is how a kundli is actually printed.

Mobile-first, keyboard-navigable with visible focus, and
`prefers-reduced-motion` is respected.

---

## Known limits

- **The ephemeris backend is Moshier, not the `.se1` files.** Swiss Ephemeris
  falls back to its built-in analytical theory when the data files are absent.
  That is sub-arcsecond for 1800–2400 — far finer than any astrological
  distinction, where the smallest unit is a 3°20′ pada — but the `.se1` files
  cover a wider date range. `/api/health` reports which backend is live rather
  than letting the fallback stay silent. To upgrade, drop `sepl_*.se1` and
  `semo_*.se1` into `backend/ephe/`.
- **Interpretation is rule-based**, so it composes pre-written text from
  detected placements. It is deterministic and it will not surprise you.
- **Yoga detection is conservative.** Where texts disagree, the stricter
  reading wins. Expect false negatives, not false positives.
- **Auth is minimal** — PBKDF2-SHA256 at 200k iterations with bearer tokens,
  adequate for a testing-phase build. No email verification, rate limiting, or
  password reset.
- Export is browser print-to-PDF rather than server-side rendering.
- Text is centralised in `interpret/rules/text.py` but not wired to an i18n
  framework, per the brief.

---

## A note on what this is

Charts here describe tendencies the tradition associates with a set of
placements. They are not predictions, and nothing in the app is medical,
psychological, legal or financial advice. Remedial practices are recorded as
tradition, clearly separated, and gemstones carry an explicit caution — the
classical texts prescribe them sparingly and so does this.

Guna Milan gets its own caveat in the output: Bhakoot and Nadi alone are 15 of
the 36 points, the method reads only the two Moons, and the number is one input
to a decision that belongs to the people involved.
