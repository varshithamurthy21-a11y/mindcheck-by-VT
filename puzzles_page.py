"""Brain Puzzles: three cognitive pillars, adaptive difficulty, calm mode and micro-breaks."""
import random
import time

import streamlit as st

import adaptive, db, puzzles
from puzzles import SKILL_NAMES, PILLARS, GENERATORS
from widgets import hero, puzzle_timer, calm_breath, flash_digits, need_nickname

PZ, NB, SQ = "pz", "nb", "sq"
CHOICES = {"Mixed": list(GENERATORS),
           "Fluid intelligence": PILLARS["fluid"]["skills"],
           "Crystallized intelligence": PILLARS["crystallized"]["skills"]}


def _nick():
    return st.session_state.get("nickname", "").strip()


def _save_attempt(skill, difficulty, correct, ms, mode):
    nick = _nick()
    if not nick:
        return
    state = adaptive.current_state(nick)
    db.insert("puzzle_attempts", nick, pillar=_pillar_of(skill), skill=skill, difficulty=difficulty,
              correct=correct, ms=ms, mode=mode, stress=state.get("stress"), energy=state.get("energy"))


def _pillar_of(skill):
    for k, v in PILLARS.items():
        if skill in v["skills"]:
            return k
    return "fluid"


# ------------------------------------------------------------------ reasoning puzzles
def _new_puzzle(skills, max_diff):
    s = st.session_state[PZ]
    s["difficulty"] = min(s["difficulty"], max_diff)
    s["puzzle"] = puzzles.make_puzzle(random.choice(skills), s["difficulty"])
    s["started"], s["answered"], s["break"] = time.time(), False, None
    s["n_shown"] += 1


def _check(mode, max_diff):
    s = st.session_state[PZ]
    p = s["puzzle"]
    choice = st.session_state.get(f"pz_choice_{s['n_shown']}")
    if choice is None:
        s["warn"] = True
        return
    s["warn"] = False
    secs = time.time() - s["started"]
    correct = choice == p["answer"]
    s["answered"], s["was_correct"], s["choice"] = True, correct, choice
    s["n_done"] += 1
    s["n_correct"] += int(correct)
    if correct:
        s["correct_streak"] += 1
        s["wrong_streak"] = 0
    else:
        s["wrong_streak"] += 1
        s["correct_streak"] = 0
    _save_attempt(p["skill"], p["difficulty"], int(correct), int(secs * 1000), mode)
    new_d = adaptive.next_difficulty(s["difficulty"], s["correct_streak"], 0 if correct else 1, max_diff)
    if new_d != s["difficulty"]:
        s["correct_streak"] = 0
    s["difficulty"] = new_d
    s["break"] = adaptive.micro_break_reason(s["wrong_streak"], secs, (time.time() - s["session_start"]) / 60)


def _next(skills, max_diff):
    s = st.session_state[PZ]
    if s.get("break"):
        s["wrong_streak"] = 0
        s["session_start"] = time.time()
    _new_puzzle(skills, max_diff)


def _render_puzzle(p):
    stars = "●" * p["difficulty"] + "○" * (3 - p["difficulty"])
    st.markdown(f'<div class="mc-eyebrow">{SKILL_NAMES[p["skill"]]} · level {stars}</div>', unsafe_allow_html=True)
    st.markdown(f"### {p['prompt']}")
    if "grid" in p:
        cells = "".join("<tr>" + "".join(f'<td class="{"q" if v == "?" else ""}">{v}</td>' for v in row) + "</tr>"
                        for row in p["grid"])
        st.markdown(f'<table class="mc-matrix">{cells}</table>', unsafe_allow_html=True)
    if "option_grids" in p:
        st.markdown(f'<div class="mc-grid">{p["grid_shape"]}</div>', unsafe_allow_html=True)
        st.write("")
        cols = st.columns(4)
        for col, label, g in zip(cols, p["options"], p["option_grids"]):
            col.markdown(f"**{label}**")
            col.markdown(f'<div class="mc-grid" style="font-size:20px">{g}</div>', unsafe_allow_html=True)


def reasoning_tab(rec, use_rec):
    calm = use_rec and rec["mode"] == "calm"
    choice = st.radio("Choose a pillar", list(CHOICES), horizontal=True, key="pz_pillar",
                      disabled=calm)
    if calm:
        skills, max_diff, timed, mode = rec["skills"], 1, False, "calm"
        st.caption("Calm mode: gentle spatial, pattern and word puzzles, level 1, no timer.")
    else:
        skills = [x for x in CHOICES[choice] if x in GENERATORS]
        max_diff = rec["max_difficulty"] if use_rec else 3
        timed, mode = True, rec["mode"] if use_rec else "normal"
        blurb = {"Fluid intelligence": PILLARS["fluid"]["blurb"],
                 "Crystallized intelligence": PILLARS["crystallized"]["blurb"]}.get(choice, "A mix of all six puzzle types.")
        st.caption(blurb + "  Skills: " + ", ".join(SKILL_NAMES[x] for x in skills) + ".")

    key = (tuple(skills), max_diff)
    s = st.session_state.get(PZ)
    if not s or s.get("key") != key:
        st.session_state[PZ] = s = {"key": key, "difficulty": 1, "correct_streak": 0, "wrong_streak": 0,
                                    "n_shown": 0, "n_done": 0, "n_correct": 0, "session_start": time.time(),
                                    "answered": False, "break": None, "warn": False}
        _new_puzzle(skills, max_diff)

    p = s["puzzle"]
    c = st.columns(3)
    c[0].metric("Answered", s["n_done"])
    c[1].metric("Correct", s["n_correct"])
    c[2].metric("Current level", s["difficulty"])

    with st.container(border=True):
        _render_puzzle(p)
        n = s["n_shown"]
        st.radio("Your answer", p["options"], index=None, key=f"pz_choice_{n}",
                 horizontal=len(max(p["options"], key=len)) < 14, disabled=s["answered"])
        if timed and not s["answered"]:
            puzzle_timer(90, key=n)
        if s.get("warn") and not s["answered"]:
            st.warning("Pick an answer first (a guess is fine).")
        if not s["answered"]:
            st.button("Check answer", type="primary", on_click=_check, args=(mode, max_diff))
        else:
            if s["was_correct"]:
                st.success(f"Correct! {p['explanation']}")
            else:
                st.error(f"Not quite. The answer is **{p['answer']}**. {p['explanation']}")

    if s["answered"] and s.get("break"):
        with st.container(border=True):
            st.markdown("#### 🌿 Time for a micro-break")
            st.write(s["break"] + " Try three slow breaths with the circle below, then come back fresh.")
            calm_breath(4, 6, rounds=3, height=300)
            st.button("I'm ready to continue", type="primary", on_click=_next, args=(skills, max_diff))
    elif s["answered"]:
        st.button("Next puzzle", type="primary", on_click=_next, args=(skills, max_diff))


# ------------------------------------------------------------------ N-back
def _nb_start(n):
    seq, targets = puzzles.nback_sequence(n)
    st.session_state[NB] = {"n": n, "seq": seq, "targets": targets, "i": 0, "responses": [],
                            "start": time.time(), "result": None}


def _nb_step(resp):
    s = st.session_state[NB]
    if s["i"] >= s["n"]:
        s["responses"].append(resp)
    s["i"] += 1
    if s["i"] >= len(s["seq"]):
        s["result"] = puzzles.score_nback(s["targets"], s["responses"], s["n"])
        _save_attempt("nback", s["n"], s["result"]["accuracy"] / 100, int((time.time() - s["start"]) * 1000), "normal")


def nback_game(level):
    n = puzzles.memory_settings(level)["n"]
    st.markdown(f"**{n}-back:** letters appear one at a time. Press **Match** when the letter is the same as "
                f"the one **{n} step{'s' if n > 1 else ''} back**.")
    s = st.session_state.get(NB)
    if not s or s["n"] != n:
        st.button(f"Start {n}-back", type="primary", on_click=_nb_start, args=(n,))
        return
    if s["result"]:
        r = s["result"]
        st.success(f"Accuracy **{r['accuracy']}%**: {r['hits']} matches caught, {r['misses']} missed, "
                   f"{r['false_alarms']} false alarms.")
        st.button("Play again", type="primary", on_click=_nb_start, args=(n,))
        return
    i = s["i"]
    st.progress(i / len(s["seq"]), text=f"Letter {i + 1} of {len(s['seq'])}")
    st.markdown(f'<div class="mc-stimulus">{s["seq"][i]}</div>', unsafe_allow_html=True)
    st.write("")
    if i < n:
        st.button("Got it, next letter", key=f"nb_{i}", on_click=_nb_step, args=(False,), use_container_width=True)
    else:
        a, b = st.columns(2)
        a.button("✓ Match", key=f"nbm_{i}", on_click=_nb_step, args=(True,), use_container_width=True, type="primary")
        b.button("No match", key=f"nbn_{i}", on_click=_nb_step, args=(False,), use_container_width=True)


# ------------------------------------------------------------------ Sequence memory
def _sq_start(length, backward):
    st.session_state[SQ] = {"digits": puzzles.digit_sequence(length), "backward": backward,
                            "length": length, "checked": None, "round": st.session_state.get(SQ, {}).get("round", 0) + 1}


def _sq_check(key):
    s = st.session_state[SQ]
    ok, target = puzzles.check_sequence(s["digits"], st.session_state.get(key, ""), s["backward"])
    s["checked"] = (ok, target)
    _save_attempt("sequence", 3 if s["backward"] else (1 if s["length"] <= 4 else 2), int(ok), 0, "normal")


def sequence_game(level):
    cfg = puzzles.memory_settings(level)
    back = cfg["backward"]
    st.markdown(f"**Sequence memory:** numbers flash for a moment. Type them back"
                f"{' **in reverse order**' if back else ''}. Get it right and the next one gets longer.")
    s = st.session_state.get(SQ)
    if not s or s.get("backward") != back:
        st.button("Start", type="primary", on_click=_sq_start, args=(cfg["span"], back))
        return
    if s["checked"] is None:
        flash_digits(s["digits"], 700 * len(s["digits"]) + 800, key=f"sq{s['round']}")
        key = f"sq_in_{s['round']}"
        with st.form(f"sqf_{s['round']}"):
            st.text_input("Your answer", key=key, placeholder="Type the digits")
            st.form_submit_button("Check", on_click=_sq_check, args=(key,))
    else:
        ok, target = s["checked"]
        nxt = s["length"] + 1 if ok else max(3, s["length"] - 1)
        if ok:
            st.success(f"Perfect! You remembered {s['length']} digits. Next: {nxt}.")
        else:
            st.error(f"The answer was **{' '.join(target)}**. Let's try {nxt} digits.")
        st.button("Next round", type="primary", on_click=_sq_start, args=(nxt, back))


# ------------------------------------------------------------------ page
def render(nick):
    hero("Brain Puzzles", "Train every side of your thinking.",
         "Fluid intelligence, crystallized intelligence and working memory. Puzzles adapt to your level and your mood.")
    if not nick:
        need_nickname()
    state = adaptive.current_state(nick) if nick else {}
    rec = adaptive.recommend(state)
    box = {"calm": st.info, "challenge": st.success}.get(rec["mode"], st.caption)
    box(f"**{rec['title']}.** {rec['message']}")
    use_rec = st.toggle("Use recommended mode", value=rec["mode"] != "normal", key="pz_use_rec")

    t1, t2 = st.tabs(["🧩 Reasoning puzzles", "🧠 Working memory games"])
    with t1:
        reasoning_tab(rec, use_rec)
    with t2:
        level = st.select_slider("Level", options=[1, 2, 3], value=1 if (use_rec and rec["mode"] == "calm") else 2,
                                 key="wm_level")
        game = st.radio("Game", ["N-back", "Sequence memory"], horizontal=True, key="wm_game")
        with st.container(border=True):
            if game == "N-back":
                nback_game(level)
            else:
                sequence_game(level)
