"""
Neuroagility trajectory (cognitive profile) and mind-body insights.
Pure functions over rows from core.db, so they are easy to test.
"""
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

from puzzles import PROFILE_AXES, SKILL_NAMES

SKILL_TO_AXIS = {s: axis for axis, skills in PROFILE_AXES.items() for s in skills}
MIN_GROUP = 8


def _day(ts):
    return ts[:10]


def _dt(ts):
    return datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")


def _skill_score(rows):
    """Accuracy with a small bonus for harder puzzles (0-100)."""
    if not rows:
        return None
    acc = statistics.mean(r["correct"] for r in rows)
    diff = statistics.mean(r["difficulty"] or 1 for r in rows)
    return round(min(100, 100 * acc * (0.8 + 0.1 * diff)))


def _battery_points(batteries):
    """Turn battery sessions into pseudo-attempt scores per skill."""
    pts = []
    for b in batteries:
        d = b.get("details") or {}
        sc = d.get("scores") or {}
        for skill, key in (("speed", "speed"), ("reaction", "reaction"), ("battery_memory", "memory")):
            if sc.get(key) is not None:
                pts.append({"ts": b["ts"], "skill": skill, "score": sc[key]})
    return pts


def axis_scores(attempts, batteries):
    by_axis = defaultdict(list)
    by_skill = defaultdict(list)
    for a in attempts:
        by_skill[a["skill"]].append(a)
    for skill, rows in by_skill.items():
        s = _skill_score(rows)
        if s is not None and skill in SKILL_TO_AXIS:
            by_axis[SKILL_TO_AXIS[skill]].append((s, len(rows)))
    for p in _battery_points(batteries):
        by_axis[SKILL_TO_AXIS[p["skill"]]].append((p["score"], 3))
    out = {}
    for axis in PROFILE_AXES:
        vals = by_axis.get(axis)
        if vals:
            w = sum(n for _, n in vals)
            out[axis] = round(sum(s * n for s, n in vals) / w)
        else:
            out[axis] = None
    return out


def cognitive_profile(attempts, batteries, recent_days=7, now=None):
    now = now or datetime.now()
    cut = now - timedelta(days=recent_days)
    recent = axis_scores([a for a in attempts if _dt(a["ts"]) >= cut],
                         [b for b in batteries if _dt(b["ts"]) >= cut])
    history = axis_scores([a for a in attempts if _dt(a["ts"]) < cut],
                          [b for b in batteries if _dt(b["ts"]) < cut])
    profile = {}
    for axis in PROFILE_AXES:
        r, h = recent[axis], history[axis]
        profile[axis] = {"recent": r, "history": h,
                         "growth": (r - h) if (r is not None and h is not None) else None}
    have = {k: v["recent"] for k, v in profile.items() if v["recent"] is not None}
    strongest = max(have, key=have.get) if have else None
    weakest = min(have, key=have.get) if len(have) > 1 else None
    grown = {k: v["growth"] for k, v in profile.items() if v["growth"] is not None}
    most_growth = max(grown, key=grown.get) if grown else None
    return {"axes": profile, "strongest": strongest, "weakest": weakest,
            "most_growth": most_growth if most_growth and grown[most_growth] > 0 else None}


def weekly_trajectory(attempts, batteries):
    """Rows of {week, axis, score} for a line chart."""
    weeks = defaultdict(lambda: ([], []))
    for a in attempts:
        weeks[_week(a["ts"])][0].append(a)
    for b in batteries:
        weeks[_week(b["ts"])][1].append(b)
    rows = []
    for wk in sorted(weeks):
        sc = axis_scores(*weeks[wk])
        for axis, v in sc.items():
            if v is not None:
                rows.append({"week": wk, "axis": axis, "score": v})
    return rows


def _week(ts):
    d = _dt(ts)
    start = d - timedelta(days=d.weekday())
    return start.strftime("%d %b")


# ------------------------------------------------------------------ MIND-BODY
def _pct_drop(low_rows, high_rows):
    a = statistics.mean(r["correct"] for r in low_rows)
    b = statistics.mean(r["correct"] for r in high_rows)
    if a == 0:
        return None
    return round(100 * (a - b) / a)


def significant(rows_a, rows_b, z_needed=1.96):
    """Two-proportion z-test: is the accuracy gap bigger than random noise?"""
    n1, n2 = len(rows_a), len(rows_b)
    p1 = sum(r["correct"] for r in rows_a) / n1
    p2 = sum(r["correct"] for r in rows_b) / n2
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = (p * (1 - p) * (1 / n1 + 1 / n2)) ** 0.5
    return se > 0 and abs(p1 - p2) / se >= z_needed


def stress_effects(attempts):
    """Compare accuracy on high-stress (8-10) vs low-stress (0-4) moments per axis."""
    found = []
    by_axis = defaultdict(list)
    for a in attempts:
        if a.get("stress") is not None and a["skill"] in SKILL_TO_AXIS:
            by_axis[SKILL_TO_AXIS[a["skill"]]].append(a)
    for axis, rows in by_axis.items():
        low = [r for r in rows if r["stress"] <= 4]
        high = [r for r in rows if r["stress"] >= 8]
        if len(low) >= MIN_GROUP and len(high) >= MIN_GROUP and significant(low, high):
            drop = _pct_drop(low, high)
            if drop is not None:
                found.append({"axis": axis, "drop": drop, "n_low": len(low), "n_high": len(high)})
    return sorted(found, key=lambda x: -x["drop"])


def build_insights(attempts, batteries, bodies, journals):
    insights = []
    for eff in stress_effects(attempts):
        if eff["drop"] >= 5:
            insights.append({
                "kind": "stress", "axis": eff["axis"], "value": -eff["drop"],
                "title": f"Stress and {eff['axis'].lower()}",
                "text": f"When your stress is 8–10 out of 10, your {eff['axis'].lower()} puzzle scores "
                        f"drop by {eff['drop']}% (based on {eff['n_low'] + eff['n_high']} puzzles).",
                "suggestion": "Consider a two-minute breathing exercise before your next puzzle."})
        elif eff["drop"] <= -12:
            insights.append({
                "kind": "stress", "axis": eff["axis"], "value": -eff["drop"],
                "title": f"Pressure helps your {eff['axis'].lower()}",
                "text": f"Interesting! Under high stress your {eff['axis'].lower()} scores are "
                        f"{-eff['drop']}% higher than when you are relaxed.",
                "suggestion": "A little pressure may sharpen you here. Just don't overdo it."})

    # Sleep vs readiness
    sleep_rows = [b for b in batteries if b.get("sleep") is not None and b.get("readiness") is not None]
    good = [b["readiness"] for b in sleep_rows if b["sleep"] >= 4]
    poor = [b["readiness"] for b in sleep_rows if b["sleep"] <= 2]
    if len(good) >= 3 and len(poor) >= 3:
        diff = round(statistics.mean(good) - statistics.mean(poor))
        if abs(diff) >= 5:
            insights.append({
                "kind": "sleep", "axis": "Speed", "value": diff,
                "title": "Sleep and morning readiness",
                "text": f"After a good night's sleep, your Brain Battery readiness is {diff} points "
                        f"{'higher' if diff > 0 else 'lower'} than after a poor night.",
                "suggestion": "Protecting your sleep is one of the easiest ways to think faster."})

    # Energy vs speed/accuracy
    energy_rows = [a for a in attempts if a.get("energy") is not None]
    hi = [a for a in energy_rows if a["energy"] >= 4]
    lo = [a for a in energy_rows if a["energy"] <= 2]
    if len(hi) >= MIN_GROUP and len(lo) >= MIN_GROUP and significant(hi, lo):
        drop = _pct_drop(hi, lo)
        if drop is not None and drop >= 5:
            insights.append({
                "kind": "energy", "axis": "All", "value": -drop,
                "title": "Energy and accuracy",
                "text": f"On low-energy days your overall puzzle accuracy is {drop}% lower.",
                "suggestion": "Try puzzles after a snack, water or a short walk."})

    # Journal mood vs that day's accuracy
    by_day = defaultdict(list)
    for a in attempts:
        by_day[_day(a["ts"])].append(a["correct"])
    pos, neg = [], []
    for j in journals:
        day = _day(j["ts"])
        if day in by_day and j.get("sentiment") is not None:
            acc = statistics.mean(by_day[day])
            (pos if j["sentiment"] >= 0.3 else neg if j["sentiment"] <= -0.3 else []).append(acc)
    if len(pos) >= 3 and len(neg) >= 3:
        diff = round(100 * (statistics.mean(pos) - statistics.mean(neg)))
        if abs(diff) >= 5:
            insights.append({
                "kind": "journal", "axis": "All", "value": diff,
                "title": "Your mood words and your focus",
                "text": f"On days your journal sounds positive, your puzzle accuracy is {abs(diff)} points "
                        f"{'higher' if diff > 0 else 'lower'}.",
                "suggestion": "Writing one line of gratitude before puzzles is a quick way to lift mood."})
    return insights


def daily_mind_body(attempts, bodies):
    """Per-day average stress and accuracy, for a scatter chart."""
    acc = defaultdict(list)
    for a in attempts:
        acc[_day(a["ts"])].append(a["correct"])
    stress = defaultdict(list)
    for b in bodies:
        if b.get("stress") is not None:
            stress[_day(b["ts"])].append(b["stress"])
    rows = []
    for day in sorted(set(acc) & set(stress)):
        rows.append({"day": day, "stress": round(statistics.mean(stress[day]), 1),
                     "accuracy": round(100 * statistics.mean(acc[day]))})
    return rows


def correlation(xs, ys):
    if len(xs) < 3:
        return None
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        return None
    return round(sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy), 2)


def skill_label(skill):
    return SKILL_NAMES.get(skill, skill)
