"""Interpretation copy.

Pure data. No calculation reaches into this file and no astronomy leaves it,
which is what makes the interpretation layer swappable: replace this module (or
the engine that reads it) with a model-backed one and the chart engine is
untouched.

House style: active voice, plain English first, Sanskrit introduced alongside
rather than instead. Describe tendencies, not fates. Nothing here diagnoses,
prescribes or predicts money or health outcomes.
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Ascendant (Lagna) -- how a person meets the world
# --------------------------------------------------------------------------
LAGNA = {
    "Aries": {
        "keynote": "Direct, quick to start, impatient with delay.",
        "body": "Mars rules your ascendant, so you meet situations head-on and "
                "commit before you have all the information. You recover from "
                "setbacks quickly, which is the real advantage. The cost is "
                "that you can start more than you finish, and read caution in "
                "others as obstruction.",
    },
    "Taurus": {
        "keynote": "Steady, sensory, hard to move once settled.",
        "body": "Venus rules your ascendant. You build slowly and hold what you "
                "build, and you judge situations by whether they feel solid "
                "rather than by argument. The strength is endurance; the "
                "difficulty is that you resist changes you would benefit from.",
    },
    "Gemini": {
        "keynote": "Curious, verbal, quick across many subjects.",
        "body": "Mercury rules your ascendant, so you take the world in through "
                "language and comparison. You learn fast and explain well. The "
                "risk is breadth without depth, and restlessness that reads as "
                "inconsistency to people who want a settled answer.",
    },
    "Cancer": {
        "keynote": "Protective, tidal, guided by atmosphere.",
        "body": "The Moon rules your ascendant, so your reading of a room is "
                "usually accurate and rarely explicable. You protect what you "
                "belong to. The difficulty is that your mood moves with your "
                "surroundings, and you may withdraw rather than say what is wrong.",
    },
    "Leo": {
        "keynote": "Warm, visible, needs the work to mean something.",
        "body": "The Sun rules your ascendant. You take responsibility naturally "
                "and would rather lead than be managed. You are generous with "
                "people who are loyal. The difficulty is that recognition "
                "matters more to you than you admit, and pride can keep you in "
                "a position past its usefulness.",
    },
    "Virgo": {
        "keynote": "Precise, useful, quietly critical.",
        "body": "Mercury rules your ascendant, and you meet the world by "
                "noticing what is wrong with it. That makes you genuinely "
                "useful and hard to fool. The cost is a running commentary of "
                "correction, aimed at yourself as much as at anyone else.",
    },
    "Libra": {
        "keynote": "Balancing, sociable, reluctant to force a decision.",
        "body": "Venus rules your ascendant. You think through relationship and "
                "instinctively look for the fair arrangement. You are good "
                "company and better counsel. The difficulty is deferring a "
                "decision until it is made for you, and keeping the peace at "
                "your own expense.",
    },
    "Scorpio": {
        "keynote": "Private, intense, all-or-nothing.",
        "body": "Mars rules your ascendant and Ketu is closely associated with "
                "it. You hold things back until you are certain, then commit "
                "completely. You handle crisis better than most. The difficulty "
                "is suspicion, and a long memory for injury.",
    },
    "Sagittarius": {
        "keynote": "Open, principled, needs somewhere to be going.",
        "body": "Jupiter rules your ascendant. You look for the meaning of a "
                "situation rather than its detail, and you say what you think. "
                "People trust your judgement. The difficulty is bluntness, and "
                "restlessness once the horizon stops moving.",
    },
    "Capricorn": {
        "keynote": "Disciplined, patient, playing a longer game.",
        "body": "Saturn rules your ascendant, so you assume things take time and "
                "you are usually right. You take responsibility early, often "
                "earlier than is fair. The difficulty is a heaviness that reads "
                "as coldness, and difficulty allowing things to be easy.",
    },
    "Aquarius": {
        "keynote": "Independent, systemic, faintly outside.",
        "body": "Saturn rules your ascendant, with Rahu closely associated. You "
                "see the structure behind a situation and are unimpressed by "
                "who holds authority within it. The difficulty is detachment "
                "where warmth was wanted, and stubbornness dressed as principle.",
    },
    "Pisces": {
        "keynote": "Porous, imaginative, hard to pin down.",
        "body": "Jupiter rules your ascendant. You absorb the feeling of a place "
                "and work best where imagination is an asset. Compassion comes "
                "easily. The difficulty is boundaries -- taking on what is not "
                "yours, and avoiding the direct conversation.",
    },
}

# --------------------------------------------------------------------------
# Moon sign (Rashi) -- the inner weather. In Vedic practice this often
# describes a person better than the ascendant.
# --------------------------------------------------------------------------
MOON_SIGN = {
    "Aries": "Your mind moves fast and wants resolution. You feel better acting "
             "than waiting, and irritation is usually your first signal that "
             "something is wrong.",
    "Taurus": "The Moon is exalted here. You settle, and you steady other "
              "people. Comfort and familiarity genuinely restore you, and being "
              "rushed genuinely does not.",
    "Gemini": "Your mind is busy and rarely quiet. You process feeling by "
              "talking it through, and you need variety more than you need rest.",
    "Cancer": "The Moon rules this sign, so it sits at home. You feel deeply and "
              "remember long. Belonging matters more to you than status does.",
    "Leo": "You need your inner life to have some dignity to it. Warmth comes "
           "easily, and so does hurt when you feel overlooked.",
    "Virgo": "You process feeling by analysing it, which works less well than "
             "you would like. You are happiest when useful and least happy when idle.",
    "Libra": "Your equilibrium depends on the state of your relationships. You "
             "are diplomatic by reflex and dislike unresolved friction.",
    "Scorpio": "The Moon is debilitated here, which classical texts read as "
               "emotional intensity without an easy outlet. You feel things "
               "privately and completely, and trust is slow but total.",
    "Sagittarius": "You need room and a sense of direction. Optimism is your "
                   "default and confinement is what actually distresses you.",
    "Capricorn": "You are self-contained and undemonstrative, and you steady "
                 "under pressure. Rest feels like something to be earned.",
    "Aquarius": "You keep a certain distance from your own feelings and observe "
                "them. You are loyal to ideas and to groups more than to "
                "hierarchy.",
    "Pisces": "You absorb the emotional state of the people around you, often "
              "without noticing. Solitude is not withdrawal for you; it is how "
              "you clear the signal.",
}

# --------------------------------------------------------------------------
# Mahadasha -- the character of each planet's long period
# --------------------------------------------------------------------------
DASHA = {
    "Sun": {
        "years": 6,
        "theme": "Authority, visibility, and the question of what you stand for.",
        "body": "A Sun period tends to bring you forward. Position, recognition "
                "and dealings with authority come into focus, and matters "
                "involving your father or your own standing often resolve one "
                "way or the other. Short, at six years, and usually decisive.",
    },
    "Moon": {
        "years": 10,
        "theme": "Home, mind, and the people you belong to.",
        "body": "A Moon period turns attention inward and domestic. Mood, "
                "family, property and the state of your own mind take "
                "precedence over public ambition. Ten years that are felt "
                "rather than achieved.",
    },
    "Mars": {
        "years": 7,
        "theme": "Effort, conflict, and the willingness to force an issue.",
        "body": "A Mars period raises energy and lowers patience. Work gets "
                "done, disputes surface, and situations that were tolerable "
                "stop being tolerable. Property, siblings and physical exertion "
                "often feature.",
    },
    "Mercury": {
        "years": 17,
        "theme": "Learning, communication, trade and negotiation.",
        "body": "A Mercury period favours study, writing, commerce and anything "
                "requiring dexterity of mind. It is generally productive rather "
                "than dramatic. Seventeen years is long enough to change what "
                "you know for a living.",
    },
    "Jupiter": {
        "years": 16,
        "theme": "Growth, teaching, belief and good counsel.",
        "body": "A Jupiter period tends to expand things -- knowledge, family, "
                "reputation, responsibility. Teachers and advisors matter in "
                "it. Its weakness is that expansion is not always warranted, "
                "and it can encourage overreach.",
    },
    "Venus": {
        "years": 20,
        "theme": "Relationship, comfort, art and the pleasant things.",
        "body": "The longest period at twenty years. Venus periods favour "
                "partnership, aesthetics, comfort and material ease. Marriage "
                "and creative work often date from them. The risk is "
                "complacency once things become comfortable.",
    },
    "Saturn": {
        "years": 19,
        "theme": "Structure, endurance, consequence and slow reward.",
        "body": "A Saturn period is the one people ask about. It removes what "
                "is not load-bearing and rewards what is. Progress is real but "
                "slow, and it usually arrives through responsibility rather "
                "than opportunity. Nineteen years.",
    },
    "Rahu": {
        "years": 18,
        "theme": "Ambition, foreignness, and sudden unfamiliar gain.",
        "body": "A Rahu period tends to be unsettling and expansive at once. "
                "It favours the unconventional, the foreign and the "
                "technological, and it can raise you quickly into situations "
                "you are not yet prepared for. Endings are as abrupt as "
                "beginnings.",
    },
    "Ketu": {
        "years": 7,
        "theme": "Detachment, endings, and the loosening of a grip.",
        "body": "A Ketu period strips things back. Interests that no longer fit "
                "fall away, sometimes uncomfortably, and attention turns "
                "inward or towards research and solitary work. Seven years, "
                "often experienced as a clearing rather than a loss.",
    },
}

# --------------------------------------------------------------------------
# Houses -- terse, used when describing a placement
# --------------------------------------------------------------------------
HOUSE_SHORT = {
    1: "your body, temperament and how you come across",
    2: "money, family and speech",
    3: "courage, siblings and self-directed effort",
    4: "home, mother and inner contentment",
    5: "children, creativity and study",
    6: "work, debt, health and open opposition",
    7: "partnership and formal agreements",
    8: "upheaval, inheritance and hidden matters",
    9: "belief, fortune, teachers and long journeys",
    10: "career and public standing",
    11: "gains, networks and older siblings",
    12: "expense, seclusion, foreign places and rest",
}

# --------------------------------------------------------------------------
# Dignity phrasing
# --------------------------------------------------------------------------
DIGNITY = {
    "exalted": "at its strongest here, and it acts with confidence",
    "moolatrikona": "very comfortably placed and acts freely",
    "own sign": "at home here and acts without obstruction",
    "friendly sign": "supported here",
    "neutral": "neither helped nor hindered here",
    "enemy sign": "under some strain here, and its results come harder",
    "debilitated": "at its weakest here; its matters take longer and cost more",
}

PLANET_ROLE = {
    "Sun": "authority, vitality and your father",
    "Moon": "mind, mother and emotional weather",
    "Mars": "drive, courage and conflict",
    "Mercury": "reasoning, speech and commerce",
    "Jupiter": "judgement, growth and teachers",
    "Venus": "relationship, comfort and taste",
    "Saturn": "discipline, endurance and consequence",
    "Rahu": "ambition and the unfamiliar",
    "Ketu": "detachment and what you are done with",
}

# --------------------------------------------------------------------------
# Remedial practice -- presented as tradition, kept well away from advice
# --------------------------------------------------------------------------
REMEDIES = {
    "Sun": {"gemstone": "Ruby", "metal": "Gold or copper",
            "mantra": "Om Hraam Hreem Hraum Sah Suryaya Namah",
            "day": "Sunday",
            "practice": "Offering water at sunrise; charity of wheat or jaggery."},
    "Moon": {"gemstone": "Natural pearl", "metal": "Silver",
             "mantra": "Om Shraam Shreem Shraum Sah Chandraya Namah",
             "day": "Monday",
             "practice": "Charity of rice or milk; service to one's mother."},
    "Mars": {"gemstone": "Red coral", "metal": "Copper",
             "mantra": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
             "day": "Tuesday",
             "practice": "Charity of red lentils; Hanuman Chalisa."},
    "Mercury": {"gemstone": "Emerald", "metal": "Bronze",
                "mantra": "Om Braam Breem Braum Sah Budhaya Namah",
                "day": "Wednesday",
                "practice": "Charity of green gram; support for a student."},
    "Jupiter": {"gemstone": "Yellow sapphire", "metal": "Gold",
                "mantra": "Om Graam Greem Graum Sah Gurave Namah",
                "day": "Thursday",
                "practice": "Charity of turmeric or chana dal; respect shown to teachers."},
    "Venus": {"gemstone": "Diamond or white sapphire", "metal": "Silver",
              "mantra": "Om Draam Dreem Draum Sah Shukraya Namah",
              "day": "Friday",
              "practice": "Charity of white cloth or sugar."},
    "Saturn": {"gemstone": "Blue sapphire", "metal": "Iron",
               "mantra": "Om Praam Preem Praum Sah Shanaye Namah",
               "day": "Saturday",
               "practice": "Charity of sesame or black gram; service to labourers "
                           "and the elderly."},
    "Rahu": {"gemstone": "Hessonite (gomed)", "metal": "Lead",
             "mantra": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
             "day": "Saturday",
             "practice": "Charity of blankets or mustard oil."},
    "Ketu": {"gemstone": "Cat's eye (lehsunia)", "metal": "Lead",
             "mantra": "Om Sraam Sreem Sraum Sah Ketave Namah",
             "day": "Tuesday",
             "practice": "Charity of blankets; feeding dogs."},
}

REMEDY_DISCLAIMER = (
    "These are traditional practices, recorded here as part of the tradition. "
    "They are not medical, psychological, legal or financial advice, and "
    "nothing here should displace a qualified professional. Gemstones in "
    "particular are a costly custom -- classical texts prescribe them "
    "cautiously, and so should you."
)

GENERAL_DISCLAIMER = (
    "This reading is generated from classical rules applied to your calculated "
    "chart. It describes tendencies the tradition associates with these "
    "placements, not events that will happen."
)
