"""MindCheck v2 - brain training + emotional wellbeing, connected."""
import streamlit as st

st.set_page_config(page_title="MindCheck by VT", page_icon="🧠", layout="wide")

from views import (battery_page, checkin_page, grounding_page, help_page, home, insights_page,  # noqa: E402
                   journal_page, progress_page, puzzles_page)
from views.theme import apply_theme, sidebar  # noqa: E402

ROUTES = {
    "Home": home.render,
    "Brain Battery": battery_page.render,
    "Brain Puzzles": puzzles_page.render,
    "Mind Journal": journal_page.render,
    "Wellbeing Check-in": checkin_page.render,
    "My Progress": progress_page.render,
    "Mind-Body Insights": insights_page.render,
    "Grounding Toolbox": grounding_page.render,
    "Help & Safety": help_page.render,
}

apply_theme()
nick = sidebar()
ROUTES[st.session_state.get("nav", "Home")](nick)
