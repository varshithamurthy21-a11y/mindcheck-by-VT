"""
Demo data so the Progress and Insights pages can be explored straight away.
Every row is marked demo=1 and can be removed with one click.
The simulated person gets slowly better over three weeks, and high stress
lowers their working-memory scores (so the insights have something to find).
"""
import random
from datetime import datetime, timedelta

import db
from sentiment import analyze

JOURNAL_SAMPLES = [
    "Had a calm morning and enjoyed my tea. Grateful for a quiet day.",
    "So many deadlines today, I feel stressed and a bit overwhelmed.",
    "Felt lonely in the evening, nobody to talk to.",
    "Finished my project! Really proud and excited.",
    "Exhausted after classes, no energy left at all.",
    "Worried about my interview tomorrow, can't stop thinking about it.",
    "Good day with friends, laughed a lot. Thankful for them.",
    "Annoyed that the bus was late again, frustrating start.",
    "Relaxed weekend, slept well and feel rested.",
    "Not worried today, feeling hopeful about next week.",
]
HEAVY_TEXTS = [t for i, t in enumerate(JOURNAL_SAMPLES) if i in (1, 2, 4, 5, 7)]
LIGHT_TEXTS = [t for i, t in enumerate(JOURNAL_SAMPLES) if i in (0, 3, 6, 8, 9)]
SKILL_BASE = {"pattern": 0.72, "matrix": 0.62, "spatial": 0.66, "vocabulary": 0.78,
              "analogy": 0.74, "trivia_logic": 0.68, "nback": 0.64, "sequence": 0.66}
MEMORY_SKILLS = {"nback", "sequence"}
WHEEL_SAMPLES = [("Bad", "Stressed", "Overwhelmed"), ("Happy", "Grateful", "Appreciative"),
                 ("Calm", "Relaxed", "Rested"), ("Anxious", "Worried", "Nervous"),
                 ("Sad", "Lonely", "Isolated")]


def generate(nickname, days=28, seed=19):
    rng = random.Random(seed)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    stress = 5.0
    for d in range(days, 0, -1):
        day = today - timedelta(days=d)
        progress = (days - d) / days                     # 0 -> 1 over the period
        stress = max(1, min(10, 0.3 * stress + 0.7 * rng.uniform(1, 8)))
        if d % 5 == 0:
            stress = rng.uniform(8, 10)       # a few clearly stressful days
        st = round(stress)
        sleep = max(1, min(5, round(5 - st / 3 + rng.uniform(-1, 1))))
        energy = max(1, min(5, round((sleep + (6 - st / 2)) / 2 + rng.uniform(-0.8, 0.8))))

        def at(h, m=0):
            return db.now_str(day + timedelta(hours=h, minutes=m))

        db.insert("body_checkins", nickname, at(7, 30), 1, energy=energy, sleep=sleep,
                  tension=max(0, min(10, st + rng.randint(-2, 1))), stress=st,
                  areas=rng.sample(["Shoulders", "Neck", "Jaw", "Chest", "Stomach", "Back"], k=2 if st > 5 else 1))

        # Brain Battery
        speed = min(100, max(0, 45 + 25 * progress + 6 * (sleep - 3) + rng.uniform(-8, 8)))
        memory = min(100, max(0, 55 + 15 * progress - 3 * max(0, st - 5) + rng.uniform(-12, 12)))
        reaction = min(100, max(0, 50 + 15 * progress + 5 * (sleep - 3) + rng.uniform(-8, 8)))
        ready = round((speed + memory + reaction) / 3)
        db.insert("battery_sessions", nickname, at(7, 40), 1, speed=round(speed), memory=round(memory),
                  reaction_ms=round(1500 - reaction * 12), readiness=ready, stress=st, sleep=sleep,
                  details={"scores": {"speed": round(speed), "memory": round(memory), "reaction": round(reaction)}})

        # Puzzles
        for i in range(rng.randint(14, 20)):
            skill = rng.choice(list(SKILL_BASE) + ["nback", "sequence"])
            diff = rng.choice([1, 1, 2, 2, 3]) if progress > 0.4 else rng.choice([1, 1, 2])
            p = SKILL_BASE[skill] + 0.12 * progress - 0.07 * (diff - 1) + 0.02 * (energy - 3)
            if skill in MEMORY_SKILLS and st >= 8:
                p -= 0.15
            correct = rng.random() < max(0.05, min(0.97, p))
            db.insert("puzzle_attempts", nickname, at(18, i * 2), 1, pillar=_pillar(skill), skill=skill,
                      difficulty=diff, correct=int(correct), ms=rng.randint(4000, 30000),
                      mode="normal", stress=st, energy=energy)

        if rng.random() < 0.8:
            pool = HEAVY_TEXTS if st >= 6 else LIGHT_TEXTS if st <= 4 else JOURNAL_SAMPLES
            text = rng.choice(pool)
            res = analyze(text)
            db.insert("journals", nickname, at(21), 1, text=text, emotions=res, sentiment=res["sentiment"])
        if rng.random() < 0.4:
            c, g, s = rng.choice(WHEEL_SAMPLES)
            db.insert("wheel_entries", nickname, at(21, 5), 1, core=c, mid=g, specific=s)


def _pillar(skill):
    return "memory" if skill in MEMORY_SKILLS else "crystallized" if skill in (
        "vocabulary", "analogy", "trivia_logic") else "fluid"
