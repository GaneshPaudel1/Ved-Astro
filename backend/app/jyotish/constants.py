"""Classical Jyotish reference tables.

Pure data, no computation. Everything downstream reads its vocabulary from here
so the tables can be audited against a printed text in one place.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Rashis (signs).  Index 0 = Aries, matching sidereal longitude // 30.
# --------------------------------------------------------------------------
SIGNS = [
    # name          sanskrit      lord       element  quality    symbol
    ("Aries",       "Mesha",      "Mars",    "Fire",  "Movable", "Ram"),
    ("Taurus",      "Vrishabha",  "Venus",   "Earth", "Fixed",   "Bull"),
    ("Gemini",      "Mithuna",    "Mercury", "Air",   "Dual",    "Twins"),
    ("Cancer",      "Karka",      "Moon",    "Water", "Movable", "Crab"),
    ("Leo",         "Simha",      "Sun",     "Fire",  "Fixed",   "Lion"),
    ("Virgo",       "Kanya",      "Mercury", "Earth", "Dual",    "Maiden"),
    ("Libra",       "Tula",       "Venus",   "Air",   "Movable", "Scales"),
    ("Scorpio",     "Vrishchika", "Mars",    "Water", "Fixed",   "Scorpion"),
    ("Sagittarius", "Dhanu",      "Jupiter", "Fire",  "Dual",    "Archer"),
    ("Capricorn",   "Makara",     "Saturn",  "Earth", "Movable", "Crocodile"),
    ("Aquarius",    "Kumbha",     "Saturn",  "Air",   "Fixed",   "Water-bearer"),
    ("Pisces",      "Meena",      "Jupiter", "Water", "Dual",    "Fishes"),
]

SIGN_NAMES = [s[0] for s in SIGNS]
SIGN_SANSKRIT = [s[1] for s in SIGNS]
SIGN_LORDS = [s[2] for s in SIGNS]
SIGN_ELEMENT = [s[3] for s in SIGNS]
SIGN_QUALITY = [s[4] for s in SIGNS]


def is_odd_sign(sign: int) -> bool:
    """True for Aries, Gemini, Leo... the 'odd' (male, cruel) signs.

    Signs are 0-indexed here, so 0-indexed Aries is the 1st and therefore odd.
    """
    return sign % 2 == 0


# --------------------------------------------------------------------------
# Nakshatras.  Each spans 13d20' = 800 arc-minutes.
# fields: name, vimshottari lord, deity, symbol, gana, nadi, yoni, yoni_sex
# --------------------------------------------------------------------------
NAKSHATRAS = [
    ("Ashwini",           "Ketu",    "Ashwini Kumaras", "Horse's head",            "Deva",     "Adi",    "Horse",    "M"),
    ("Bharani",           "Venus",   "Yama",            "Yoni",                    "Manushya", "Madhya", "Elephant", "M"),
    ("Krittika",          "Sun",     "Agni",            "Razor and flame",         "Rakshasa", "Antya",  "Goat",     "F"),
    ("Rohini",            "Moon",    "Brahma",          "Ox cart",                 "Manushya", "Antya",  "Serpent",  "M"),
    ("Mrigashira",        "Mars",    "Soma",            "Deer's head",             "Deva",     "Madhya", "Serpent",  "F"),
    ("Ardra",             "Rahu",    "Rudra",           "Teardrop",                "Manushya", "Adi",    "Dog",      "F"),
    ("Punarvasu",         "Jupiter", "Aditi",           "Quiver of arrows",        "Deva",     "Adi",    "Cat",      "F"),
    ("Pushya",            "Saturn",  "Brihaspati",      "Cow's udder",             "Deva",     "Madhya", "Goat",     "M"),
    ("Ashlesha",          "Mercury", "Nagas",           "Coiled serpent",          "Rakshasa", "Antya",  "Cat",      "M"),
    ("Magha",             "Ketu",    "Pitris",          "Royal throne",            "Rakshasa", "Antya",  "Rat",      "M"),
    ("Purva Phalguni",    "Venus",   "Bhaga",           "Front legs of a bed",     "Manushya", "Madhya", "Rat",      "F"),
    ("Uttara Phalguni",   "Sun",     "Aryaman",         "Back legs of a bed",      "Manushya", "Adi",    "Cow",      "M"),
    ("Hasta",             "Moon",    "Savitr",          "Open hand",               "Deva",     "Adi",    "Buffalo",  "F"),
    ("Chitra",            "Mars",    "Tvashtar",        "Bright jewel",            "Rakshasa", "Madhya", "Tiger",    "F"),
    ("Swati",             "Rahu",    "Vayu",            "Young shoot in the wind", "Deva",     "Antya",  "Buffalo",  "M"),
    ("Vishakha",          "Jupiter", "Indra-Agni",      "Triumphal archway",       "Rakshasa", "Antya",  "Tiger",    "M"),
    ("Anuradha",          "Saturn",  "Mitra",           "Lotus flower",            "Deva",     "Madhya", "Deer",     "F"),
    ("Jyeshtha",          "Mercury", "Indra",           "Circular amulet",         "Rakshasa", "Adi",    "Deer",     "M"),
    ("Mula",              "Ketu",    "Nirriti",         "Bunch of roots",          "Rakshasa", "Adi",    "Dog",      "M"),
    ("Purva Ashadha",     "Venus",   "Apas",            "Elephant tusk",           "Manushya", "Madhya", "Monkey",   "M"),
    ("Uttara Ashadha",    "Sun",     "Vishvadevas",     "Planks of a bed",         "Manushya", "Antya",  "Mongoose", "M"),
    ("Shravana",          "Moon",    "Vishnu",          "Three footprints",        "Deva",     "Antya",  "Monkey",   "F"),
    ("Dhanishta",         "Mars",    "Vasus",           "Drum",                    "Rakshasa", "Madhya", "Lion",     "F"),
    ("Shatabhisha",       "Rahu",    "Varuna",          "Empty circle",            "Rakshasa", "Adi",    "Horse",    "F"),
    ("Purva Bhadrapada",  "Jupiter", "Aja Ekapada",     "Front of a funeral cot",  "Manushya", "Adi",    "Lion",     "M"),
    ("Uttara Bhadrapada", "Saturn",  "Ahir Budhnya",    "Back of a funeral cot",   "Manushya", "Madhya", "Cow",      "F"),
    ("Revati",            "Mercury", "Pushan",          "Pair of fish",            "Deva",     "Antya",  "Elephant", "F"),
]

NAKSHATRA_NAMES = [n[0] for n in NAKSHATRAS]
NAKSHATRA_SPAN = 360.0 / 27.0          # 13.3333... degrees
PADA_SPAN = NAKSHATRA_SPAN / 4.0       # 3.3333... degrees

# --------------------------------------------------------------------------
# Vimshottari dasha.  Order matters: it follows the nakshatra lord cycle.
# --------------------------------------------------------------------------
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars",
                     "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_TOTAL_YEARS = 120          # asserted in tests

# The classical dasha year. Texts reckon dashas in 365.25-day solar years.
SIDEREAL_YEAR_DAYS = 365.25

# --------------------------------------------------------------------------
# Grahas
# --------------------------------------------------------------------------
PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
PLANET_SANSKRIT = {
    "Sun": "Surya", "Moon": "Chandra", "Mars": "Mangala", "Mercury": "Budha",
    "Jupiter": "Guru", "Venus": "Shukra", "Saturn": "Shani",
    "Rahu": "Rahu", "Ketu": "Ketu", "Ascendant": "Lagna",
}
PLANET_GLYPH = {
    "Sun": "☉", "Moon": "☽", "Mars": "♂", "Mercury": "☿",
    "Jupiter": "♃", "Venus": "♀", "Saturn": "♄",
    "Rahu": "☊", "Ketu": "☋", "Ascendant": "As",
}
# Short labels used inside the chart diagrams.
PLANET_ABBR = {
    "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
    "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke", "Ascendant": "As",
}

# Sign ownership (0-indexed signs)
PLANET_OWNS = {
    "Mars": [0, 7], "Venus": [1, 6], "Mercury": [2, 5], "Moon": [3],
    "Sun": [4], "Jupiter": [8, 11], "Saturn": [9, 10],
}

# Exaltation: (sign index, exact degree of deep exaltation).
# Debilitation is the same degree in the opposite sign.
EXALTATION = {
    "Sun": (0, 10.0), "Moon": (1, 3.0), "Mars": (9, 28.0), "Mercury": (5, 15.0),
    "Jupiter": (3, 5.0), "Venus": (11, 27.0), "Saturn": (6, 20.0),
    "Rahu": (1, 20.0), "Ketu": (7, 20.0),
}
DEBILITATION = {p: ((s + 6) % 12, d) for p, (s, d) in EXALTATION.items()}

# Moolatrikona: (sign, start degree, end degree)
MOOLATRIKONA = {
    "Sun": (4, 0.0, 20.0), "Moon": (1, 4.0, 30.0), "Mars": (0, 0.0, 12.0),
    "Mercury": (5, 16.0, 20.0), "Jupiter": (8, 0.0, 10.0),
    "Venus": (6, 0.0, 15.0), "Saturn": (10, 0.0, 20.0),
}

# Naisargika (natural) relationships.
NATURAL_FRIENDS = {
    "Sun":     {"Moon", "Mars", "Jupiter"},
    "Moon":    {"Sun", "Mercury"},
    "Mars":    {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus":   {"Mercury", "Saturn"},
    "Saturn":  {"Mercury", "Venus"},
    "Rahu":    {"Venus", "Saturn", "Mercury"},
    "Ketu":    {"Mars", "Venus", "Saturn"},
}
NATURAL_ENEMIES = {
    "Sun":     {"Venus", "Saturn"},
    "Moon":    set(),
    "Mars":    {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus":   {"Sun", "Moon"},
    "Saturn":  {"Sun", "Moon", "Mars"},
    "Rahu":    {"Sun", "Moon", "Mars"},
    "Ketu":    {"Sun", "Moon"},
}
NATURAL_BENEFICS = {"Jupiter", "Venus", "Moon", "Mercury"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

# Combustion orbs (degrees from the Sun), classical values.
COMBUSTION_ORB = {
    "Moon": 12.0, "Mars": 17.0, "Mercury": 14.0, "Jupiter": 11.0,
    "Venus": 10.0, "Saturn": 15.0,
}
# Mercury and Venus have a tighter orb when retrograde.
COMBUSTION_ORB_RETRO = {"Mercury": 12.0, "Venus": 8.0}

# Special aspects (drishti) beyond the universal 7th-house aspect.
SPECIAL_ASPECTS = {
    "Mars": [4, 8], "Jupiter": [5, 9], "Saturn": [3, 10],
    "Rahu": [5, 9], "Ketu": [5, 9],
}

KENDRA_HOUSES = [1, 4, 7, 10]
TRIKONA_HOUSES = [1, 5, 9]
DUSTHANA_HOUSES = [6, 8, 12]
UPACHAYA_HOUSES = [3, 6, 10, 11]

HOUSE_MEANINGS = [
    "Self, body, vitality, how you meet the world",
    "Wealth, family, speech, accumulated resources",
    "Siblings, courage, effort, short journeys",
    "Home, mother, land, inner contentment",
    "Children, creativity, intellect, past merit",
    "Debt, disease, enemies, daily service",
    "Partnership, marriage, open dealings",
    "Longevity, upheaval, hidden matters, inheritance",
    "Fortune, dharma, father, higher learning",
    "Career, status, public action",
    "Gains, networks, elder siblings, fulfilment",
    "Loss, expense, seclusion, liberation",
]

# --------------------------------------------------------------------------
# Ayanamsa options exposed in the UI.
# --------------------------------------------------------------------------
AYANAMSA_OPTIONS = {
    "lahiri": {
        "label": "Lahiri (Chitrapaksha)", "swe_id": 1,
        "note": "India's official ayanamsa. The default for most Jyotish work.",
    },
    "raman": {
        "label": "B. V. Raman", "swe_id": 3,
        "note": "Runs about 1.2 degrees behind Lahiri.",
    },
    "kp": {
        "label": "KP (Krishnamurti)", "swe_id": 5,
        "note": "Used in Krishnamurti Paddhati. Very close to Lahiri.",
    },
    "yukteshwar": {
        "label": "Sri Yukteshwar", "swe_id": 7,
        "note": "From The Holy Science. Differs from Lahiri by roughly a degree.",
    },
}
DEFAULT_AYANAMSA = "lahiri"


# --------------------------------------------------------------------------
# Small shared helpers
# --------------------------------------------------------------------------
def norm360(deg: float) -> float:
    """Wrap an angle into [0, 360)."""
    return deg % 360.0


def sign_of(longitude: float) -> int:
    """0-indexed rashi containing this sidereal longitude."""
    return min(11, int(norm360(longitude) * 12.0 / 360.0))


def deg_in_sign(longitude: float) -> float:
    return norm360(longitude) % 30.0


def nakshatra_of(longitude: float) -> int:
    """0-indexed nakshatra (0 = Ashwini).

    Multiply before dividing. Dividing by NAKSHATRA_SPAN (13.3333...) is not
    exact in binary, so a planet sitting exactly on a boundary -- 120.0 is the
    start of Magha -- lands one nakshatra early. Scaling by 27/360 keeps the
    boundary cases exact.
    """
    return min(26, int(norm360(longitude) * 27.0 / 360.0))


def pada_of(longitude: float) -> int:
    """Pada 1-4 within the nakshatra. Exact on boundaries, as above."""
    return int(norm360(longitude) * 108.0 / 360.0) % 4 + 1


def dms(deg: float) -> tuple[int, int, int]:
    """Split a degree value into (degrees, arc-minutes, arc-seconds)."""
    d = int(deg)
    m_full = (deg - d) * 60
    m = int(m_full)
    s = int(round((m_full - m) * 60))
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    return d, m, s


def format_dms(deg: float) -> str:
    d, m, s = dms(deg)
    return f"{d}°{m:02d}'{s:02d}\""


def house_distance(from_sign: int, to_sign: int) -> int:
    """Whole-sign house count from one sign to another, 1-12 inclusive."""
    return ((to_sign - from_sign) % 12) + 1
