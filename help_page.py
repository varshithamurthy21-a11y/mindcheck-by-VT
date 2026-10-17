import streamlit as st

from theme import go
from widgets import hero, support_box


def render(nick):
    hero("Help & Safety", "You matter.", "If things feel too heavy, please reach out. Help is free and available 24x7.")
    support_box()
    st.button("Open the Grounding Toolbox", type="primary", on_click=go, args=("Grounding Toolbox",))
    st.markdown("""
#### About MindCheck
- All puzzles, questions, word lists and the emotion wheel were written for this app. Most puzzles are generated
  fresh from rules every time, so nothing is copied from published tests.
- Scores are practice scores for tracking yourself. MindCheck is **not** an IQ test and **not** a medical or
  psychological diagnosis. Only a qualified professional can diagnose a condition.

#### Your privacy
- Results are saved only under the nickname you choose. Use a nickname, not your real name.
- Journal entries are analysed inside the app with a simple word list. They are never sent to an AI or website.
- The optional AI coach (if an API key is added) only receives numbers and labels, never your journal text.
- You can delete everything at any time on the **My Progress** page.
""")
