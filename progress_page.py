"""My Progress: the Neuroagility Trajectory (cognitive profile, not just one score)."""
import pandas as pd
import plotly.graph_objects as go_
import plotly.express as px
import streamlit as st

import db, demo_data, insights
from puzzles import PROFILE_AXES
from widgets import hero, need_nickname

TEAL, CORAL = "#0F766E", "#D9725E"


def demo_controls(nick, key):
    if db.has_demo(nick):
        if st.button("Remove demo data", key=f"rm_{key}"):
            db.delete_demo(nick)
            st.rerun()
        st.caption("You are looking at demo data (28 simulated days).")
    else:
        if st.button("Load 4 weeks of demo data to explore", key=f"ld_{key}"):
            demo_data.generate(nick)
            st.rerun()


def radar(profile):
    axes = list(PROFILE_AXES)
    rec = [profile["axes"][a]["recent"] or 0 for a in axes]
    hist = [profile["axes"][a]["history"] for a in axes]
    fig = go_.Figure()
    if any(h is not None for h in hist):
        fig.add_trace(go_.Scatterpolar(r=[h or 0 for h in hist] + [hist[0] or 0], theta=axes + [axes[0]],
                                       name="Your average before", line=dict(color=CORAL, dash="dot"),
                                       fill="toself", fillcolor="rgba(217,114,94,0.12)"))
    fig.add_trace(go_.Scatterpolar(r=rec + [rec[0]], theta=axes + [axes[0]], name="Last 7 days",
                                   line=dict(color=TEAL, width=3), fill="toself", fillcolor="rgba(15,118,110,0.22)"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], showticklabels=True, tickfont=dict(size=10)),
                                 bgcolor="rgba(0,0,0,0)"),
                      height=460, margin=dict(t=30, b=30, l=60, r=60), paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", y=-0.1), font=dict(family="Nunito Sans"))
    return fig


def render(nick):
    hero("My Progress", "Your neuroagility trajectory.",
         "A cognitive profile across six skills, compared with your own history, so you can see real growth.")
    if not nick:
        need_nickname()
        return
    attempts = db.fetch("puzzle_attempts", nick)
    batteries = db.fetch("battery_sessions", nick)
    if not attempts and not batteries:
        st.info("No results yet. Play the Brain Battery or some puzzles, or load demo data to explore this page.")
        demo_controls(nick, "p")
        return

    prof = insights.cognitive_profile(attempts, batteries)
    c = st.columns(3)
    c[0].metric("Strongest right now", prof["strongest"] or "—")
    c[1].metric("Most room to grow", prof["weakest"] or "—")
    g = prof["axes"][prof["most_growth"]]["growth"] if prof["most_growth"] else None
    c[2].metric("Biggest growth", prof["most_growth"] or "—", f"+{g} points" if g else None)

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(radar(prof), use_container_width=True)
    with right:
        st.markdown("#### This week vs your average")
        rows = []
        for axis, v in prof["axes"].items():
            rows.append({"Skill": axis, "Last 7 days": v["recent"], "Before": v["history"],
                         "Change": (f"{v['growth']:+d}" if v["growth"] is not None else "—")})
        st.dataframe(pd.DataFrame(rows).set_index("Skill"), use_container_width=True)
        if prof["strongest"] and prof["weakest"]:
            st.write(f"Right now you are excelling at **{prof['strongest'].lower()}**, "
                     f"while **{prof['weakest'].lower()}** has the most room to grow.")

    traj = insights.weekly_trajectory(attempts, batteries)
    if traj:
        st.markdown("#### Week by week")
        df = pd.DataFrame(traj)
        fig = px.line(df, x="week", y="score", color="axis", markers=True,
                      color_discrete_sequence=["#0F766E", "#D9725E", "#6C8EBF", "#E0A72E", "#8E6CC2", "#4A6461"])
        fig.update_layout(height=360, yaxis=dict(range=[0, 100], title="Score"), xaxis_title="Week starting",
                          legend_title="", paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=10),
                          font=dict(family="Nunito Sans"))
        st.plotly_chart(fig, use_container_width=True)

    if batteries:
        st.markdown("#### Morning readiness")
        bd = pd.DataFrame([{"Day": b["ts"][:10], "Readiness": b["readiness"]} for b in batteries]).groupby("Day").mean()
        st.area_chart(bd, color=TEAL)

    with st.expander("How scores are calculated"):
        st.write("Each skill score is your accuracy, with a small bonus for harder levels. Speed comes from the "
                 "Brain Battery. 'Before' is your average from more than 7 days ago. These are practice scores "
                 "for tracking yourself, not an IQ score.")
    st.divider()
    demo_controls(nick, "p2")
    if st.button("Delete ALL my saved data"):
        db.delete_user(nick)
        st.success("All your data has been deleted.")
