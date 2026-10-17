"""Brain Battery: 90-second randomized micro-game -> daily readiness score."""
import random
import time

import pandas as pd
import streamlit as st

import battery, db
from puzzles import check_sequence
from theme import go
from widgets import hero, countdown, flash_digits, need_nickname

SS = "bb"


def _nick():
    return st.session_state.get("nickname", "").strip()


def _start():
    q = battery.build_queue()
    st.session_state[SS] = {"phase": "run", "start": time.time(), "queue": q, "i": 0,
                            "results": [], "item": None, "shown_at": None, "sub": None}
    _load_item()


def _load_item():
    s = st.session_state[SS]
    kind = s["queue"][s["i"]]
    if kind == "speed":
        s["item"] = battery.speed_item()
    elif kind == "memory":
        s["item"] = battery.memory_item(span=random.choice([4, 5, 5, 6]))
    else:
        s["item"] = {"type": "reaction"}
    s["shown_at"], s["sub"] = None, None


def _advance(result):
    s = st.session_state[SS]
    s["results"].append(result)
    s["i"] += 1
    if time.time() - s["start"] >= battery.DURATION_S or s["i"] >= len(s["queue"]):
        _finish()
    else:
        _load_item()


def _answer_speed(choice):
    s = st.session_state[SS]
    ms = int((time.time() - (s["shown_at"] or time.time())) * 1000)
    _advance({"type": "speed", "correct": choice == s["item"]["answer"], "ms": max(150, ms)})


def _submit_memory(key):
    s = st.session_state[SS]
    ok, _ = check_sequence(s["item"]["digits"], st.session_state.get(key, ""))
    _advance({"type": "memory", "correct": ok, "ms": 0})


def _reaction_ready():
    s = st.session_state[SS]
    s["sub"], s["delay"] = "armed", random.uniform(1.2, 3.2)


def _reaction_tap():
    s = st.session_state[SS]
    ms = int((time.time() - s["go_at"]) * 1000)
    _advance({"type": "reaction", "correct": True, "ms": ms})


def _finish():
    s = st.session_state[SS]
    nick = _nick()
    history = []
    if nick:
        for b in db.fetch("battery_sessions", nick, days=60):
            sc = (b.get("details") or {}).get("scores")
            if sc:
                history.append(sc)
    res = battery.readiness(s["results"], history)
    s["phase"], s["result"] = "done", res
    if nick:
        body = db.latest("body_checkins", nick, same_day=True)
        db.insert("battery_sessions", nick, speed=res["scores"]["speed"], memory=res["scores"]["memory"],
                  reaction_ms=res["raw"]["reaction_ms"], readiness=res["readiness"], details=res,
                  stress=body["stress"] if body else None, sleep=body["sleep"] if body else None)


def _reset():
    st.session_state[SS] = {"phase": "idle"}


def render(nick):
    hero("Brain Battery", "Charge up your brain.",
         "A 90-second mix of quick tasks. Best played first thing in the morning to get your daily readiness score.")
    s = st.session_state.setdefault(SS, {"phase": "idle"})

    if s["phase"] == "idle":
        if not nick:
            need_nickname()
        a, b, c = st.columns(3)
        a.markdown("**⚡ Processing speed**  \nTrue or false? Same or different? Answer fast.")
        b.markdown("**🧠 Working memory**  \nNumbers flash for 3 seconds. Type them back.")
        c.markdown("**🎯 Reaction time**  \nTap the button the moment it appears.")
        today = db.latest("battery_sessions", nick, same_day=True) if nick else None
        if today:
            st.success(f"You already charged today: readiness **{round(today['readiness'])}**. You can play again.")
        st.button("Start the 90-second Brain Battery", type="primary", on_click=_start)
        st.caption("Timings include a little internet delay, so your score is most useful compared with your own past days.")
        if nick:
            rows = db.fetch("battery_sessions", nick, days=30)
            if len(rows) >= 2:
                st.markdown("#### Your readiness, last 30 days")
                df = pd.DataFrame([{"Day": r["ts"][:10], "Readiness": r["readiness"]} for r in rows])
                st.line_chart(df.groupby("Day").mean())
        return

    if s["phase"] == "run":
        elapsed = time.time() - s["start"]
        if elapsed > battery.DURATION_S + 20:      # walked away
            _finish()
            st.rerun()
        left = max(0, battery.DURATION_S - elapsed)
        c1, c2 = st.columns([1, 3])
        with c1:
            countdown(left)
        c2.progress(min(1.0, elapsed / battery.DURATION_S), text=f"Task {s['i'] + 1}")
        item = s["item"]

        if item["type"] == "speed":
            if s["shown_at"] is None:
                s["shown_at"] = time.time()
            st.markdown(f'<div class="mc-stimulus">{item["prompt"]}</div>', unsafe_allow_html=True)
            st.write("")
            cols = st.columns(2)
            for col, opt in zip(cols, item["options"]):
                col.button(opt, key=f"bb_{s['i']}_{opt}", on_click=_answer_speed, args=(opt,),
                           use_container_width=True)

        elif item["type"] == "memory":
            st.markdown("**Remember these numbers.**")
            flash_digits(item["digits"], 3000, key=s["i"])
            key = f"bb_mem_{s['i']}"
            with st.form(f"bbf_{s['i']}"):
                st.text_input("Type the numbers in order", key=key, placeholder="e.g. 4 7 1 9")
                st.form_submit_button("Submit", on_click=_submit_memory, args=(key,))

        else:  # reaction
            if s["sub"] is None:
                st.markdown('<div class="mc-stimulus" style="font-size:28px;letter-spacing:0">'
                            'Reaction test: press Ready, then tap the green button the moment it appears.</div>',
                            unsafe_allow_html=True)
                st.write("")
                st.button("I'm ready", key=f"rr_{s['i']}", on_click=_reaction_ready, use_container_width=True)
            else:
                if s["sub"] == "armed":
                    ph = st.empty()
                    ph.markdown('<div class="mc-stimulus" style="font-size:30px;letter-spacing:0;background:#FBE4DC">'
                                'Wait for it…</div>', unsafe_allow_html=True)
                    time.sleep(s["delay"])
                    ph.empty()
                    s["sub"], s["go_at"] = "go", time.time()
                st.button("TAP NOW!", key=f"rt_{s['i']}", type="primary", on_click=_reaction_tap,
                          use_container_width=True)
        st.button("Stop", key="bb_stop", on_click=_reset)
        return

    # done
    res = s["result"]
    st.markdown(f'<div class="mc-eyebrow">Today\'s readiness</div><div class="mc-big">{res["readiness"]}</div>',
                unsafe_allow_html=True)
    st.subheader(res["label"])
    st.write(res["advice"])
    st.caption(res["note"])
    c = st.columns(3)
    c[0].metric("Processing speed", f"{res['scores']['speed']}/100",
                f"{res['raw']['speed_per_min']} correct per min", delta_color="off")
    c[1].metric("Working memory", f"{res['scores']['memory']}/100", f"{res['raw']['memory_pct']}% recalled",
                delta_color="off")
    rt = res["raw"]["reaction_ms"]
    c[2].metric("Reaction", f"{res['scores']['reaction']}/100", f"{rt} ms" if rt else "not measured",
                delta_color="off")
    if not nick:
        st.caption("Add a nickname to save this score.")
    b1, b2 = st.columns(2)
    b1.button("Play recommended puzzles", type="primary", on_click=go, args=("Brain Puzzles",),
              use_container_width=True)
    b2.button("Play again", on_click=_reset, use_container_width=True)
