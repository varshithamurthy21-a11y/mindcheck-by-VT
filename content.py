"""
Wellbeing check-in content and support lines.
All wording is original to MindCheck. Not a clinical questionnaire.
"""

SCALE = ["Not at all", "Sometimes", "Often", "Almost always"]  # scored 0..3

SECTIONS = {
    "mood": {
        "title": "Mood",
        "intro": "Over the past two weeks, how often...",
        "questions": [
            "I felt low or flat for most of the day.",
            "Things I usually enjoy felt less interesting.",
            "I felt tired or low on energy, even after rest.",
            "I was hard on myself or felt I wasn't good enough.",
            "My sleep felt off (too little or too much).",
        ],
    },
    "stress": {
        "title": "Stress",
        "intro": "Over the past two weeks, how often...",
        "questions": [
            "I felt tense or found it hard to relax.",
            "My mind kept racing with worries.",
            "Small problems felt bigger than usual.",
            "I felt irritated or short-tempered.",
            "I found it hard to focus on one thing.",
        ],
    },
    "sensitivity": {
        "title": "Emotional sensitivity",
        "intro": "In general, how true is this for you...",
        "questions": [
            "Other people's moods affect me strongly.",
            "Loud noise, bright light or crowds overwhelm me.",
            "I notice small details that others miss.",
            "I am deeply moved by music, art or nature.",
            "Criticism stays with me for a long time.",
            "I need quiet time alone to recharge after a busy day.",
        ],
    },
}

SAFETY_QUESTION = (
    "In the past two weeks, have you had thoughts of hurting yourself, "
    "or felt that life isn't worth living?"
)

# Indian support lines. Check these are still current before you publish.
SUPPORT_LINES = [
    ("Tele-MANAS (free, 24x7, many Indian languages)", "14416  or  1-800-891-4416"),
    ("Emergency", "112"),
]

TIPS = {
    "mood": {
        "low": "Your mood seems steady. Keep doing what helps you feel good.",
        "mild": "A few low days are normal. Short walks, sunlight and talking to a friend can lift mood.",
        "moderate": "Low mood has been showing up often. Try to share how you feel with someone you trust.",
        "high": "Your answers suggest a hard stretch. Talking to a counsellor or doctor could really help.",
    },
    "stress": {
        "low": "Stress looks well managed right now.",
        "mild": "Some stress is showing. Slow breathing (in for 4, out for 6) for two minutes can help.",
        "moderate": "Stress is high fairly often. Breaking tasks into small steps and protecting sleep can help.",
        "high": "Stress seems very heavy. Please consider speaking with a professional for support.",
    },
    "sensitivity": {
        "lower": "You tend to stay steady in busy or emotional situations.",
        "moderate": "You have a balanced level of sensitivity: you feel things, but they don't usually overwhelm you.",
        "high": "You seem highly sensitive. That often comes with empathy and creativity. Quiet breaks help you recharge.",
    },
}


def _mood_stress_band(score: int) -> str:
    if score <= 4:
        return "low"
    if score <= 9:
        return "mild"
    if score <= 12:
        return "moderate"
    return "high"


def _sensitivity_band(score: int) -> str:
    if score <= 6:
        return "lower"
    if score <= 12:
        return "moderate"
    return "high"


def score_wellbeing(responses: dict) -> dict:
    """responses: {section_key: [answer_text, ...]} using SCALE labels."""
    result = {}
    for key, section in SECTIONS.items():
        total = sum(SCALE.index(a) for a in responses[key])
        maximum = 3 * len(section["questions"])
        band = _sensitivity_band(total) if key == "sensitivity" else _mood_stress_band(total)
        result[key] = {"score": total, "max": maximum, "band": band}
    return result


def wellbeing_needs_support(scores: dict, safety_answer: str) -> bool:
    if safety_answer == "Yes":
        return True
    return scores["mood"]["band"] == "high" or scores["stress"]["band"] == "high"
