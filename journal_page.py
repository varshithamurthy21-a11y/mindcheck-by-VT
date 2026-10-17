"""Mind Journal: micro-journaling with private emotion analysis, body check-in, emotion wheel."""
from collections import Counter

import pandas as pd
import plotly.graph_objects as go_
import streamlit as st

import db, emotion_wheel
from sentiment import analyze, sentiment_label, EMOTIONS
from theme import go
from widgets import hero, support_box, chips, body_map, need_nickname

ENERGY = ["Empty", "Low", "Okay", "Good", "Charged"]
SLEEP = ["Very poor", "Poor", "Okay", "Good", "Great"]
AREAS = ["Forehead", "Jaw", "Neck", "Shoulders", "Chest", "Stomach", "Back", "Hands", "Legs"]
NEG = {v["label"] for v in EMOTIONS.values() if v["valence"] < 0}


def _grounding_offer(text):
    st.warning(text)
    st.button("Open the Grounding Toolbox", type="primary", on_click=go, args=("Grounding Toolbox",),
              key=f"gro_{abs(hash(text)) % 10000}")


def journal_tab(nick):
    st.markdown("#### How was your day, in one or two sentences?")
    text = st.text_area("Your words", key="mj_text", max_chars=300, height=110,
                        placeholder="e.g. Deadlines piled up and I felt drained, but my friend made me laugh.",
                        label_visibility="collapsed")
    st.caption("🔒 Your words are analysed right here in the app with a simple word list. They are never sent to any AI or website.")
    if st.button("Find my emotions", type="primary", disabled=not (text or "").strip()):
        res = analyze(text)
        st.session_state["mj_result"] = (text, res)
        if nick:
            db.insert("journals", nick, text=text, emotions=res, sentiment=res["sentiment"])

    if st.session_state.get("mj_result"):
        text, res = st.session_state["mj_result"]
        if res["crisis"]:
            support_box()
            _grounding_offer("It sounds like you might be in a lot of pain right now. A grounding exercise "
                             "can help in this moment, and the people on the support lines want to help.")
        with st.container(border=True):
            if not res["emotions"]:
                st.write("I couldn't spot clear emotion words. Try adding how it **felt** "
                         "(for example: tired, proud, worried, grateful).")
            else:
                st.markdown(f"**Overall tone:** {sentiment_label(res['sentiment'])}")
                chips([e["label"] for e in res["emotions"]], negative=NEG)
                for e in res["emotions"]:
                    st.progress(e["strength"], text=f"{e['label']}: found in “{', '.join(e['evidence'])}”")
                hidden = [e["label"] for e in res["emotions"][1:]]
                if hidden:
                    st.caption("Underneath the main feeling, your words also hint at: " + ", ".join(hidden).lower() + ".")
            if nick:
                st.caption("Saved to your journal.")


def body_tab(nick):
    st.markdown("#### Body check-in")
    st.caption("Emotions live in the body too. This takes about 20 seconds.")
    left, right = st.columns([3, 2])
    with left:
        energy = st.select_slider("Energy level", options=ENERGY, value="Okay", key="b_energy")
        sleep = st.select_slider("Last night's sleep", options=SLEEP, value="Okay", key="b_sleep")
        stress = st.slider("Stress right now (0 = none, 10 = extreme)", 0, 10, 4, key="b_stress")
        tension = st.slider("Physical tension (0 = loose, 10 = very tight)", 0, 10, 3, key="b_tension")
        areas = st.multiselect("Where are you holding stress right now?", AREAS, key="b_areas")
    with right:
        body_map(areas)
    if st.button("Save check-in", type="primary"):
        if nick:
            db.insert("body_checkins", nick, energy=ENERGY.index(energy) + 1, sleep=SLEEP.index(sleep) + 1,
                      tension=tension, stress=stress, areas=areas)
            st.success("Saved. Your puzzles will adapt to how you feel today.")
        else:
            need_nickname()
        if stress >= 9:
            _grounding_offer("Your stress is very high right now. Would you like a two-minute grounding exercise?")
        elif stress >= 7:
            st.info("Stress is high today, so Brain Puzzles will suggest calm mode.")
        if areas:
            tips = {"Jaw": "unclench your teeth and let your tongue rest", "Shoulders": "drop your shoulders away from your ears",
                    "Neck": "slowly tilt your head side to side", "Forehead": "soften the space between your eyebrows",
                    "Chest": "take one slow breath into your belly", "Stomach": "place a hand on your belly and breathe out slowly",
                    "Hands": "open and close your hands five times", "Back": "sit tall, then gently roll your shoulders",
                    "Legs": "press your feet into the floor for five seconds"}
            st.write("**Quick release:** " + "; ".join(tips[a] for a in areas if a in tips) + ".")


def wheel_tab(nick):
    st.markdown("#### Emotion wheel")
    st.caption("Start broad, then go deeper. Naming a feeling precisely makes it easier to handle. "
               "You can also click the wheel to zoom in.")
    c1, c2 = st.columns([3, 2])
    with c2:
        core = st.radio("1. Broad feeling", emotion_wheel.cores(), index=None, key="w_core")
        group = st.radio("2. More exactly", emotion_wheel.groups(core), index=None, key=f"w_group_{core}") if core else None
        specific = None
        if core and group:
            feelings = emotion_wheel.specifics(core, group)
            specific = st.radio("3. Most exactly", list(feelings), index=None, key=f"w_spec_{core}_{group}")
    with c1:
        ids, labels, parents, colors = emotion_wheel.sunburst_data(core, group, specific)
        fig = go_.Figure(go_.Sunburst(ids=ids, labels=labels, parents=parents, marker=dict(colors=colors),
                                      insidetextorientation="radial", hoverinfo="label"))
        fig.update_layout(margin=dict(t=0, l=0, r=0, b=0), height=430, paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Nunito Sans", size=13))
        st.plotly_chart(fig, use_container_width=True)
    if specific:
        info = emotion_wheel.WHEEL[core]
        with st.container(border=True):
            st.markdown(f"### {specific}")
            st.write(f"*{emotion_wheel.specifics(core, group)[specific]}*  ({core} → {group} → {specific})")
            st.write("💡 " + info["tip"])
            if st.button("Save this feeling", type="primary"):
                if nick:
                    db.insert("wheel_entries", nick, core=core, mid=group, specific=specific)
                    st.success("Saved.")
                else:
                    need_nickname()
        if specific in emotion_wheel.DISTRESS_WORDS:
            _grounding_offer(f"Feeling {specific.lower()} is hard. A short grounding exercise can help right now.")


def history_tab(nick):
    if not nick:
        need_nickname()
        return
    js = db.fetch("journals", nick, days=30)
    bodies = db.fetch("body_checkins", nick, days=30)
    wheels = db.fetch("wheel_entries", nick, days=30)
    if not (js or bodies or wheels):
        st.write("Nothing saved yet. Your entries will appear here.")
        return
    if js:
        counts = Counter(e["label"] for j in js for e in (j["emotions"] or {}).get("emotions", []))
        if counts:
            st.markdown("#### Emotions in your journal (30 days)")
            st.bar_chart(pd.DataFrame({"Times": counts}).sort_values("Times", ascending=False))
    if bodies:
        st.markdown("#### Stress, energy and sleep")
        df = pd.DataFrame([{"Day": b["ts"][:10], "Stress (0-10)": b["stress"], "Energy (1-5)": b["energy"],
                            "Sleep (1-5)": b["sleep"]} for b in bodies]).groupby("Day").mean()
        st.line_chart(df)
    if wheels:
        st.markdown("#### Feelings you named")
        chips([w["specific"] for w in wheels[-15:]])
    if js:
        st.markdown("#### Recent entries")
        for j in js[::-1][:10]:
            labels = [e["label"] for e in (j["emotions"] or {}).get("emotions", [])]
            st.markdown(f"**{j['ts'][:16]}** · {', '.join(labels) or 'no clear emotion'}  \n{j['text']}")


def render(nick):
    hero("Mind Journal", "Put feelings into words.",
         "Write one line, check in with your body, or explore the emotion wheel. Each takes under a minute.")
    if not nick:
        need_nickname()
    t1, t2, t3, t4 = st.tabs(["📝 Micro-journal", "🫀 Body check-in", "🎡 Emotion wheel", "📚 History"])
    with t1:
        journal_tab(nick)
    with t2:
        body_tab(nick)
    with t3:
        wheel_tab(nick)
    with t4:
        history_tab(nick)
