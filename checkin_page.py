import streamlit as st

import agent, db
from content import SECTIONS, SCALE, SAFETY_QUESTION
from theme import go
from widgets import hero, support_box

BAND = {"low": "Low", "mild": "Mild", "moderate": "Moderate", "high": "High", "lower": "Lower"}


def render(nick):
    hero("Wellbeing Check-in", "A gentle look at the last two weeks.",
         "16 short questions about mood, stress and emotional sensitivity. There are no right or wrong answers.")
    st.markdown('<div class="mc-note">This is a self-reflection tool, <b>not</b> a medical or psychological diagnosis.</div>',
                unsafe_allow_html=True)
    st.write("")
    with st.form("wellbeing"):
        responses = {}
        for key, sec in SECTIONS.items():
            st.markdown(f"### {sec['title']}")
            st.caption(sec["intro"])
            responses[key] = [st.radio(q, SCALE, index=None, horizontal=True, key=f"wb_{key}_{j}")
                              for j, q in enumerate(sec["questions"])]
        st.markdown("### One more question")
        safety = st.radio(SAFETY_QUESTION, ["No", "Yes", "Prefer not to say"], index=None, horizontal=True)
        submitted = st.form_submit_button("See my results", type="primary")

    if not submitted:
        return
    if None in [a for lst in responses.values() for a in lst] + [safety]:
        st.warning("Please answer every question.")
        return
    with st.status("MindCheck agent is working...") as status:
        out = agent.checkin_summary(responses, safety, nick)
        for s in ["Scored your answers", "Checked whether support should be shown first",
                  "Matched tips to your results", "Wrote your summary" + (" with AI" if out["used_ai"] else "")]:
            st.write("✓ " + s)
        status.update(label="Done", state="complete")
    if out["support"]:
        support_box()
        st.button("Try a grounding exercise now", type="primary", on_click=go, args=("Grounding Toolbox",))
    st.markdown("### Your summary")
    st.write(out["summary"])
    cols = st.columns(3)
    for col, (key, sc) in zip(cols, out["scores"].items()):
        col.metric(SECTIONS[key]["title"], f"{sc['score']}/{sc['max']}", BAND[sc["band"]], delta_color="off")
    with st.expander("Tips for you"):
        for key, tip in out["tips"].items():
            st.markdown(f"**{SECTIONS[key]['title']}:** {tip}")
    if nick:
        db.insert("wellbeing", nick, **{k: v["score"] for k, v in out["scores"].items()})
        st.caption("Saved to your progress.")
