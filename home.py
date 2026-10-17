import html

import streamlit as st

from core import agent, db, quotes
from views.theme import go, brain_svg
from views.widgets import support_box, need_nickname

PLAN_PAGES = {"grounding": "Grounding Toolbox", "battery": "Brain Battery",
              "journal": "Mind Journal", "puzzles": "Brain Puzzles"}


def _another_thought():
    st.session_state["quote_offset"] = st.session_state.get("quote_offset", 0) + 1


def welcome(nick, heavy_day):
    hello, icon = quotes.greeting()
    thought = quotes.thought_for_today(heavy_day, st.session_state.get("quote_offset", 0))
    name = f", {html.escape(nick)}" if nick else ""
    st.markdown(f'<div class="mc-welcome">{brain_svg(84)}<div style="flex:1;min-width:260px">'
                f'<div class="hello">{hello}{name} {icon}</div>'
                f'<div class="mc-sub">Know your mind a little better today.</div>'
                f'<div class="label">Thought for today</div>'
                f'<div class="quote">“{html.escape(thought)}”</div></div></div>', unsafe_allow_html=True)
    st.button("✨ Another thought", key="quote_next", on_click=_another_thought)


def render(nick):
    coach = agent.daily_coach(nick) if nick else None
    heavy = bool(coach and (coach["support"] or coach["mode"]["mode"] == "calm"))
    welcome(nick, heavy)
    if not nick:
        need_nickname()
    if coach and coach["support"]:
        support_box()
        st.button("Open the Grounding Toolbox now", type="primary", on_click=go, args=("Grounding Toolbox",))

    if coach:
        with st.container(border=True):
            st.markdown("#### Your coach for today")
            st.write(coach["message"])
            for i, (kind, text) in enumerate(coach["plan"]):
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{i + 1}.** {text}")
                c2.button("Go", key=f"plan{i}", on_click=go, args=(PLAN_PAGES[kind],), use_container_width=True)
            with st.expander("How the coach decided"):
                for s in coach["steps"]:
                    st.write("✓ " + s)
                st.caption(coach["mode"]["message"])

        s = coach["state"]
        today = [a for a in db.fetch("puzzle_attempts", nick, days=1)]
        c = st.columns(4)
        c[0].metric("Readiness", f"{round(s['readiness'])}" if s.get("readiness") is not None else "—")
        c[1].metric("Stress", f"{s['stress']}/10" if s.get("stress") is not None else "—")
        c[2].metric("Energy", f"{s['energy']}/5" if s.get("energy") is not None else "—")
        c[3].metric("Puzzles (24 h)", len(today))

    st.write("")
    st.markdown("#### What would you like to do?")
    a, b, c = st.columns(3)
    with a:
        with st.container(border=True, key="card_bb"):
            st.markdown("##### ⚡ Brain Battery")
            st.write("A 90-second morning game for speed, memory and reaction time.")
            st.button("Start", key="h_bb", on_click=go, args=("Brain Battery",), use_container_width=True)
    with b:
        with st.container(border=True, key="card_pz"):
            st.markdown("##### 🧩 Brain Puzzles")
            st.write("Fluid, crystallized and working-memory puzzles that adapt to you.")
            st.button("Play", key="h_pz", on_click=go, args=("Brain Puzzles",), use_container_width=True)
    with c:
        with st.container(border=True, key="card_mj"):
            st.markdown("##### 📝 Mind Journal")
            st.write("One line about your day, a body check-in and the emotion wheel.")
            st.button("Write", key="h_mj", on_click=go, args=("Mind Journal",), use_container_width=True)

    st.markdown('<div class="mc-note">MindCheck is a self-reflection tool for learning and fun. It is <b>not</b> '
                'an IQ test and <b>not</b> a medical or psychological diagnosis.</div>', unsafe_allow_html=True)
