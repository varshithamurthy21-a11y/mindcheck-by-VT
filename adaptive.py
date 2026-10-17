"""
Mind-body bridge: reads how the user feels and adapts the puzzles.
All rules are simple and visible, so nothing happens 'by magic'.
"""
from datetime import datetime

import db
from emotion_wheel import DISTRESS_WORDS

HEAVY_EMOTIONS = {"anxiety", "stress", "burnout"}


def _today(rows):
    d = datetime.now().strftime("%Y-%m-%d")
    return [r for r in rows if r["ts"].startswith(d)]


def current_state(nickname):
    """Snapshot of today's emotional and physical signals."""
    if not nickname:
        return {}
    body = db.latest("body_checkins", nickname, same_day=True)
    journal = db.latest("journals", nickname, same_day=True)
    wheel = db.latest("wheel_entries", nickname, same_day=True)
    battery = db.latest("battery_sessions", nickname, same_day=True)
    wb = db.fetch("wellbeing", nickname, days=3)
    quick = db.latest("quick_mood", nickname, same_day=True)

    heavy = []
    crisis = False
    if journal and journal.get("emotions"):
        heavy = [e["label"] for e in journal["emotions"].get("emotions", [])
                 if e["key"] in HEAVY_EMOTIONS and e["strength"] >= 0.3]
        crisis = bool(journal["emotions"].get("crisis"))
    return {
        "stress": body["stress"] if body else None,
        "energy": body["energy"] if body else None,
        "sleep": body["sleep"] if body else None,
        "tension": body["tension"] if body else None,
        "heavy_emotions": heavy,
        "journal_sentiment": journal["sentiment"] if journal else None,
        "wheel_feeling": wheel["specific"] if wheel else None,
        "readiness": battery["readiness"] if battery else None,
        "wellbeing_stress_high": any(w["stress"] >= 13 or w["mood"] >= 13 for w in wb),
        "quick_mood": quick["value"] if quick else None,
        "crisis": crisis,
    }


def needs_grounding(state):
    """Extreme distress -> offer grounding tools straight away."""
    if not state:
        return False
    return bool(state.get("crisis")
                or (state.get("stress") is not None and state["stress"] >= 9)
                or state.get("wheel_feeling") in DISTRESS_WORDS
                or (state.get("quick_mood") == 1))


def recommend(state):
    """Choose the puzzle mode for right now."""
    reasons = []
    s = state or {}
    if s.get("stress") is not None and s["stress"] >= 7:
        reasons.append(f"you rated your stress {s['stress']}/10")
    if s.get("heavy_emotions"):
        reasons.append("your journal mentioned " + ", ".join(e.lower() for e in s["heavy_emotions"]))
    if s.get("wellbeing_stress_high"):
        reasons.append("your recent check-in showed a heavy stretch")
    if s.get("quick_mood") is not None and s["quick_mood"] <= 2:
        reasons.append("you picked a low mood today")
    if s.get("readiness") is not None and s["readiness"] < 45:
        reasons.append(f"your Brain Battery readiness was {round(s['readiness'])}")
    if s.get("energy") is not None and s["energy"] <= 2:
        reasons.append("your energy is low")

    if reasons:
        return {"mode": "calm", "title": "Calm mode",
                "message": "Because " + "; ".join(reasons) + ", we suggest gentle, low-pressure "
                           "spatial and pattern puzzles. No timer, no pressure.",
                "skills": ["spatial", "pattern", "vocabulary"], "max_difficulty": 1, "timed": False}
    if s.get("readiness") is not None and s["readiness"] >= 70 and (s.get("stress") or 0) <= 4:
        return {"mode": "challenge", "title": "Challenge mode",
                "message": "Your readiness is high and stress is low. A great time to push harder puzzles!",
                "skills": None, "max_difficulty": 3, "timed": True}
    return {"mode": "normal", "title": "Normal mode",
            "message": "Puzzles adapt as you go: two right in a row makes them harder, a miss makes them easier.",
            "skills": None, "max_difficulty": 3, "timed": True}


def next_difficulty(current, correct_streak, wrong_streak, max_difficulty=3):
    if correct_streak >= 2:
        return min(max_difficulty, current + 1)
    if wrong_streak >= 1:
        return max(1, current - 1)
    return min(current, max_difficulty)


def micro_break_reason(wrong_streak, seconds_on_puzzle, session_minutes):
    """Returns a friendly reason to pause, or None."""
    if wrong_streak >= 3:
        return "That's three tricky ones in a row. Brains learn best after a tiny pause."
    if seconds_on_puzzle >= 90:
        return "You've been on this one for a while. A short reset often brings the answer."
    if session_minutes >= 20:
        return "You've been working for 20 minutes. A quick break keeps your mind fresh."
    return None
