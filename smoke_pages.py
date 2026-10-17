"""
Smoke test: runs app.py against a fake Streamlit and clicks through every page.
Run from the project folder:  python tests/smoke_pages.py
"""
import os
import runpy
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests", "stub"))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import streamlit as st  # the stub  # noqa: E402
from core import db  # noqa: E402

db.DB_PATH = os.path.join(tempfile.mkdtemp(), "smoke.db")
time.sleep = lambda s: None       # skip reaction-test waits
ss = st.session_state


def run(clicks=(), inputs=None, page=None):
    if page:
        ss["nav"] = page
    st.CLICK.clear()
    st.CLICK.update(clicks)
    st.INPUTS.clear()
    st.INPUTS.update(inputs or {})
    for _ in range(3):
        st.new_run()
        try:
            runpy.run_path("app.py", run_name="__main__")
            st.end_run()
            return
        except st.RerunException:
            continue


def check(label, cond):
    if not cond:
        raise AssertionError(label)
    print("ok ", label)


# ---------------------------------------------------------------- every page, no nickname
for page in ["Home", "Brain Battery", "Brain Puzzles", "Mind Journal", "Wellbeing Check-in", "My Progress",
             "Mind-Body Insights", "Grounding Toolbox", "Help & Safety"]:
    run(page=page)
check("all pages render without a nickname", True)

ss["nickname"] = "varsh"
for page in ["Home", "My Progress", "Mind-Body Insights"]:
    run(page=page)
check("empty-data pages render with a nickname", True)

# ---------------------------------------------------------------- quick mood + nav
run(clicks={"🙂"}, page="Home")
check("quick mood saved", db.latest("quick_mood", "varsh")["value"] == 4)
run(clicks={"🤍  I need a moment"})
check("panic button opens grounding", ss["nav"] == "Grounding Toolbox")

# ---------------------------------------------------------------- body check-in -> calm mode
run(page="Mind Journal", inputs={"b_stress": 9, "b_areas": ["Jaw", "Shoulders"], "b_energy": "Low"},
    clicks={"Save check-in"})
check("body check-in saved", db.latest("body_checkins", "varsh")["stress"] == 9)

run(page="Mind Journal", inputs={"mj_text": "So stressed with deadlines, really exhausted but grateful for my sister."},
    clicks={"Find my emotions"})
j = db.latest("journals", "varsh")
check("journal analysed and saved", {e["key"] for e in j["emotions"]["emotions"]} >= {"stress", "burnout", "gratitude"})
run(page="Mind Journal", inputs={"mj_text": "i want to die"}, clicks={"Find my emotions"})
check("crisis text flagged", ss["mj_result"][1]["crisis"])

run(page="Mind Journal", inputs={"w_core": "Bad"})
run(page="Mind Journal", inputs={"w_group_Bad": "Stressed"})
run(page="Mind Journal", inputs={"w_spec_Bad_Stressed": "Overwhelmed"}, clicks={"Save this feeling"})
check("emotion wheel feeling saved", db.latest("wheel_entries", "varsh")["specific"] == "Overwhelmed")

# ---------------------------------------------------------------- home coach with distress
run(page="Home")
check("home coach renders", True)
run(clicks={"✨ Another thought"})
check("another thought", ss["quote_offset"] == 1)

# ---------------------------------------------------------------- puzzles (calm mode because stress 9)
run(page="Brain Puzzles")
check("calm mode recommended", ss["pz"]["key"][1] == 1)
for i in range(6):
    p = ss["pz"]["puzzle"]
    n = ss["pz"]["n_shown"]
    wrong = next(o for o in p["options"] if o != p["answer"])
    run(inputs={f"pz_choice_{n}": wrong if i < 3 else p["answer"]}, clicks={"Check answer"})
    if ss["pz"].get("break"):
        check("micro-break triggered after 3 wrong", i == 2)
        run(clicks={"I'm ready to continue"})
    else:
        run(clicks={"Next puzzle"})
check("puzzle attempts saved", len(db.fetch("puzzle_attempts", "varsh")) == 6)

run(inputs={"pz_use_rec": False, "pz_pillar": "Fluid intelligence"})
for i in range(5):
    p = ss["pz"]["puzzle"]
    run(inputs={f"pz_choice_{ss['pz']['n_shown']}": p["answer"]}, clicks={"Check answer"})
    run(clicks={"Next puzzle"})
check("difficulty rises after correct answers", ss["pz"]["difficulty"] >= 2)
for pillar in ["Crystallized intelligence", "Mixed"]:
    run(inputs={"pz_pillar": pillar})
    for _ in range(4):
        p = ss["pz"]["puzzle"]
        run(inputs={f"pz_choice_{ss['pz']['n_shown']}": p["answer"]}, clicks={"Check answer"})
        run(clicks={"Next puzzle"})
check("all puzzle pillars render", True)

# working memory
run(inputs={"wm_game": "N-back", "wm_level": 2}, clicks={"Start 2-back"})
while not ss["nb"]["result"]:
    i = ss["nb"]["i"]
    if i < 2:
        run(clicks={"Got it, next letter"})
    else:
        run(clicks={"✓ Match" if ss["nb"]["targets"][i] else "No match"})
check("n-back perfect score", ss["nb"]["result"]["accuracy"] == 100)
run(inputs={"wm_game": "Sequence memory", "wm_level": 1}, clicks={"Start"})
digits = "".join(map(str, ss["sq"]["digits"]))
run(inputs={f"sq_in_{ss['sq']['round']}": digits}, clicks={"Check"})
check("sequence memory correct", ss["sq"]["checked"][0])
run(clicks={"Next round"})
check("sequence gets longer", ss["sq"]["length"] == 5)

# ---------------------------------------------------------------- brain battery
run(page="Brain Battery", clicks={"Start the 90-second Brain Battery"})
steps = 0
while ss["bb"]["phase"] == "run" and steps < 60:
    item = ss["bb"]["item"]
    i = ss["bb"]["i"]
    if item["type"] == "speed":
        run(clicks={item["answer"]})
    elif item["type"] == "memory":
        run(inputs={f"bb_mem_{i}": " ".join(map(str, item["digits"]))}, clicks={"Submit"})
    else:
        if ss["bb"]["sub"] is None:
            run(clicks={"I'm ready"})
        run(clicks={"TAP NOW!"})
    steps += 1
    if steps == 15:
        ss["bb"]["start"] -= 200      # jump past 90 seconds
check("battery finished", ss["bb"]["phase"] == "done")
check("battery saved", db.latest("battery_sessions", "varsh")["readiness"] is not None)
run()
run(clicks={"Play again"})

# ---------------------------------------------------------------- check-in
from core.content import SECTIONS  # noqa: E402
answers = {f"wb_{k}_{j}": "Often" for k, s in SECTIONS.items() for j in range(len(s["questions"]))}
run(page="Wellbeing Check-in", inputs=answers)
# safety radio has no key: patch default by clicking submit with all keyed answers set
st_radio = st.radio


def radio_yes(*a, **k):
    if a and str(a[0]).startswith("In the past two weeks"):
        return "No"
    return st_radio(*a, **k)


import views.checkin_page as cp  # noqa: E402
cp.st.radio = radio_yes
run(clicks={"See my results"})
cp.st.radio = st_radio
check("wellbeing check-in saved", db.latest("wellbeing", "varsh")["mood"] == 10)

# ---------------------------------------------------------------- demo data, progress, insights
run(page="My Progress", clicks={"Load 4 weeks of demo data to explore"})
run(page="My Progress")
run(page="Mind-Body Insights")
check("progress and insights render with demo data", db.has_demo("varsh"))
run(page="My Progress", clicks={"Remove demo data"})
check("demo data removed", not db.has_demo("varsh"))

# ---------------------------------------------------------------- grounding game
run(page="Grounding Toolbox")
from views.grounding_page import SENSES  # noqa: E402
for step, (n, *_rest) in enumerate(SENSES):
    run(inputs={f"g_{step}_{k}": f"thing{k}" for k in range(n)}, clicks={"Next"})
check("5-4-3-2-1 game completes", ss["g54321"]["step"] == 5)
run(clicks={"Start again"})
for page in ["Help & Safety", "Home"]:
    run(page=page)
print("All page smoke tests passed")
