"""Run from the project folder:  python -m tests.test_core"""
import os
import random
import tempfile

from core import db

db.DB_PATH = os.path.join(tempfile.mkdtemp(), "test.db")

from core import puzzles, battery, sentiment, emotion_wheel, adaptive, insights, demo_data, agent  # noqa
from core.content import SECTIONS, SCALE


def test_puzzles():
    rng = random.Random(1)
    for skill in puzzles.GENERATORS:
        for d in (1, 2, 3):
            for _ in range(150):
                p = puzzles.make_puzzle(skill, d, rng)
                assert len(p["options"]) == 4, (skill, d, p)
                assert len(set(p["options"])) == 4, (skill, d, p["options"])
                assert p["answer"] in p["options"], (skill, d, p)
                if skill == "spatial" and "option_grids" in p:
                    assert len(set(p["option_grids"])) == 4
    # spatial correctness: rotation of a known grid
    g = [[1, 0, 0], [1, 1, 0], [0, 0, 0]]
    assert puzzles._rot_cw(g) == [[0, 1, 1], [0, 1, 0], [0, 0, 0]]
    assert puzzles._rot_ccw(puzzles._rot_cw(g)) == g


def test_matrix_answers():
    rng = random.Random(3)
    for d in (1, 2, 3):
        for _ in range(100):
            p = puzzles.matrix(d, rng)
            assert p["grid"][2][2] == "?"


def test_memory():
    rng = random.Random(2)
    seq, targets = puzzles.nback_sequence(2, rng=rng)
    assert len(seq) == 14
    for i, t in enumerate(targets):
        assert t == (i >= 2 and seq[i] == seq[i - 2])
    perfect = puzzles.score_nback(targets, targets[2:], 2)
    assert perfect["accuracy"] == 100 and perfect["false_alarms"] == 0
    ok, target = puzzles.check_sequence([1, 2, 3], "3 2 1", backward=True)
    assert ok and target == "321"


def test_battery():
    good = [{"type": "speed", "correct": True, "ms": 1200}] * 15 + \
           [{"type": "memory", "correct": True, "ms": 3000}] * 3 + \
           [{"type": "reaction", "correct": True, "ms": 400}] * 3
    poor = [{"type": "speed", "correct": False, "ms": 4000}] * 8 + \
           [{"type": "memory", "correct": False, "ms": 3000}] * 3 + \
           [{"type": "reaction", "correct": True, "ms": 1400}] * 3
    g, p = battery.readiness(good), battery.readiness(poor)
    assert g["readiness"] > 70 and g["label"] == "Sharp"
    assert p["readiness"] < 45
    hist = [{"speed": 50, "memory": 60, "reaction": 50}] * 5
    assert "personal average" in battery.readiness(good, hist)["note"]
    q = battery.build_queue(random.Random(1))
    assert q[0] == "speed" and q.count("reaction") == 3


def test_sentiment():
    r = sentiment.analyze("I feel so anxious about my exam and really exhausted, but grateful for my mom.")
    keys = [e["key"] for e in r["emotions"]]
    assert {"anxiety", "burnout", "gratitude"} <= set(keys), keys
    assert not r["crisis"]
    r2 = sentiment.analyze("I am not worried today. Feeling calm.")
    assert r2["emotions"][0]["key"] == "calm" and r2["sentiment"] > 0
    r3 = sentiment.analyze("i want to die")
    assert r3["crisis"]
    assert sentiment.analyze("")["emotions"] == []


def test_wheel():
    ids, labels, parents, colors = emotion_wheel.sunburst_data("Bad", "Stressed", "Overwhelmed")
    assert len(ids) == len(labels) == len(parents) == len(colors)
    assert len(set(ids)) == len(ids)
    assert "Overwhelmed" in emotion_wheel.specifics("Bad", "Stressed")


def test_adaptive_and_insights():
    nick = "tester"
    db.insert("body_checkins", nick, energy=2, sleep=2, tension=8, stress=9, areas=["Neck"])
    st = adaptive.current_state(nick)
    assert st["stress"] == 9
    assert adaptive.needs_grounding(st)
    rec = adaptive.recommend(st)
    assert rec["mode"] == "calm" and rec["max_difficulty"] == 1
    assert adaptive.recommend({})["mode"] == "normal"
    assert adaptive.next_difficulty(1, 2, 0) == 2
    assert adaptive.next_difficulty(2, 0, 1) == 1
    assert adaptive.micro_break_reason(3, 10, 2)
    assert adaptive.micro_break_reason(0, 10, 2) is None

    demo_data.generate("demo_user")
    att = db.fetch("puzzle_attempts", "demo_user")
    bat = db.fetch("battery_sessions", "demo_user")
    bod = db.fetch("body_checkins", "demo_user")
    jou = db.fetch("journals", "demo_user")
    assert len(att) > 100 and len(bat) == 28
    prof = insights.cognitive_profile(att, bat)
    assert prof["strongest"] is not None
    assert all(v["recent"] is not None for v in prof["axes"].values())
    ins = insights.build_insights(att, bat, bod, jou)
    assert any(i["kind"] == "stress" for i in ins), ins
    assert insights.weekly_trajectory(att, bat)
    assert insights.daily_mind_body(att, bod)
    assert db.has_demo("demo_user")
    db.delete_demo("demo_user")
    assert not db.fetch("puzzle_attempts", "demo_user")


def test_agent():
    out = agent.daily_coach("tester")
    assert out["support"] and out["plan"][0][0] == "grounding"
    resp = {k: [SCALE[3]] * len(s["questions"]) for k, s in SECTIONS.items()}
    s = agent.checkin_summary(resp, "No")
    assert s["support"] and "not a diagnosis" in s["summary"]


if __name__ == "__main__":
    os.environ.pop("ANTHROPIC_API_KEY", None)
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
    print("All core tests passed")
