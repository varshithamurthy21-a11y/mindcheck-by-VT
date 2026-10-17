"""
Brain Battery: a 90-second randomized micro-game that measures
processing speed, working memory and reaction time, then gives a
daily readiness score.

Note: in a web app, timings include a little network delay, so the
score is best used to compare you with yourself, day to day.
"""
import random
import statistics

DURATION_S = 90
SYMBOLS = ["▲", "●", "■", "◆", "★", "♥"]


def build_queue(rng=None):
    rng = rng or random.Random()
    q = ["reaction"] * 3 + ["memory"] * 3 + ["speed"] * 18
    rng.shuffle(q)
    # make sure the session starts with a quick, easy item
    q.insert(0, "speed")
    return q


def speed_item(rng=None):
    rng = rng or random.Random()
    if rng.random() < 0.5:
        a, b = rng.randint(2, 12), rng.randint(2, 12)
        true = rng.random() < 0.5
        shown = a + b if true else a + b + rng.choice([-2, -1, 1, 2])
        return {"type": "speed", "prompt": f"{a} + {b} = {shown}", "answer": "True" if true else "False",
                "options": ["True", "False"]}
    k = rng.randint(3, 4)
    left = [rng.choice(SYMBOLS) for _ in range(k)]
    same = rng.random() < 0.5
    right = list(left)
    if not same:
        i = rng.randrange(k)
        right[i] = rng.choice([s for s in SYMBOLS if s != left[i]])
    return {"type": "speed", "prompt": f"{' '.join(left)}    vs    {' '.join(right)}",
            "answer": "Same" if same else "Different", "options": ["Same", "Different"]}


def memory_item(rng=None, span=5):
    rng = rng or random.Random()
    return {"type": "memory", "digits": [rng.randint(0, 9) for _ in range(span)]}


def _clip(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def _scale(x, worst, best):
    """Map x to 0..100 where `best` -> 100 and `worst` -> 0 (works either direction)."""
    return _clip(100 * (x - worst) / (best - worst))


def raw_metrics(results):
    """results: list of {type, correct(bool), ms(int)}"""
    sp = [r for r in results if r["type"] == "speed"]
    me = [r for r in results if r["type"] == "memory"]
    re_ = [r for r in results if r["type"] == "reaction" and r.get("ms")]
    speed_time_min = max(1e-6, sum(r["ms"] for r in sp) / 60000)
    speed_per_min = sum(r["correct"] for r in sp) / speed_time_min if sp else 0
    memory_pct = 100 * sum(r["correct"] for r in me) / len(me) if me else 0
    reaction_ms = statistics.median(r["ms"] for r in re_) if re_ else None
    accuracy = 100 * sum(r["correct"] for r in sp) / len(sp) if sp else 0
    return {"speed_per_min": round(speed_per_min, 1), "speed_accuracy": round(accuracy),
            "memory_pct": round(memory_pct), "reaction_ms": round(reaction_ms) if reaction_ms else None}


def normalized(m):
    speed = _scale(m["speed_per_min"], 5, 40)
    memory = m["memory_pct"]
    reaction = _scale(m["reaction_ms"], 1500, 300) if m["reaction_ms"] else 50
    return {"speed": round(speed), "memory": round(memory), "reaction": round(reaction)}


def readiness(results, history=None):
    """history: list of previous sessions as dicts with keys speed, memory, reaction (0-100)."""
    m = raw_metrics(results)
    n = normalized(m)
    base = (n["speed"] + n["memory"] + n["reaction"]) / 3
    note = "This is your first few sessions, so the score compares you with general ranges."
    score = base
    history = [h for h in (history or []) if h]
    if len(history) >= 3:
        zs = []
        for k in ("speed", "memory", "reaction"):
            vals = [h[k] for h in history if h.get(k) is not None]
            if len(vals) >= 3:
                mu = statistics.mean(vals)
                sd = max(8.0, statistics.pstdev(vals))
                zs.append((n[k] - mu) / sd)
        if zs:
            z = sum(zs) / len(zs)
            score = 0.5 * base + 0.5 * _clip(50 + 20 * z)
            direction = "above" if z > 0.25 else "below" if z < -0.25 else "close to"
            note = f"Today you are {direction} your personal average."
    score = round(_clip(score))
    if score >= 70:
        label, advice = "Sharp", "A great day to try harder puzzles."
    elif score >= 45:
        label, advice = "Steady", "A normal day. Warm up with a few easy puzzles first."
    else:
        label, advice = "Take it easy", "Your brain may be tired. Try calm puzzles or a short break."
    return {"raw": m, "scores": n, "readiness": score, "label": label, "advice": advice, "note": note}
