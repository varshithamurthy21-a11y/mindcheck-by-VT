"""Mind-Body Insights: how mood, sleep and stress affect your brain."""
import pandas as pd
import plotly.express as px
import streamlit as st

import adaptive, db, insights
from progress_page import demo_controls
from theme import go
from widgets import hero, need_nickname

ICON = {"stress": "🌡️", "sleep": "🌙", "energy": "🔋", "journal": "📝"}


def render(nick):
    hero("Mind-Body Insights", "How your feelings affect your brain.",
         "MindCheck links your check-ins with your puzzle results and looks for real patterns.")
    if not nick:
        need_nickname()
        return
    attempts = db.fetch("puzzle_attempts", nick)
    batteries = db.fetch("battery_sessions", nick)
    bodies = db.fetch("body_checkins", nick)
    journals = db.fetch("journals", nick)
    found = insights.build_insights(attempts, batteries, bodies, journals)

    if not found:
        st.info("No clear patterns yet. Insights appear once you have a few days of body check-ins and puzzles "
                "(at least 8 puzzles at low stress and 8 at high stress). Patterns that could just be luck are hidden.")
        demo_controls(nick, "i")
    for ins in found:
        with st.container(border=True):
            st.markdown(f"#### {ICON.get(ins['kind'], '💡')} {ins['title']}")
            st.write(ins["text"])
            st.caption(ins["suggestion"])
            if ins["kind"] == "stress" and ins["value"] < 0:
                st.button("Try 2-minute breathing", key=f"ins_{ins['axis']}", on_click=go, args=("Grounding Toolbox",))

    daily = insights.daily_mind_body(attempts, bodies)
    if len(daily) >= 3:
        st.markdown("#### Stress vs puzzle accuracy, day by day")
        df = pd.DataFrame(daily)
        r = insights.correlation(df["stress"].tolist(), df["accuracy"].tolist())
        fig = px.scatter(df, x="stress", y="accuracy", hover_name="day", color_discrete_sequence=["#0F766E"])
        fig.update_traces(marker=dict(size=13, opacity=0.8))
        fig.update_layout(height=360, xaxis=dict(range=[-0.5, 10.5], title="Stress that day (0-10)"),
                          yaxis=dict(range=[0, 100], title="Puzzle accuracy (%)"), paper_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Nunito Sans"), margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)
        if r is not None:
            strength = "strong" if abs(r) >= 0.5 else "moderate" if abs(r) >= 0.3 else "weak"
            st.caption(f"Correlation r = {r} ({strength}). A negative number means higher stress goes with lower accuracy.")

    st.markdown("#### Adaptive puzzles right now")
    rec = adaptive.recommend(adaptive.current_state(nick))
    st.write(f"**{rec['title']}:** {rec['message']}")
    st.button("Go to Brain Puzzles", on_click=go, args=("Brain Puzzles",))
    if found and db.has_demo(nick):
        st.divider()
        demo_controls(nick, "i2")
