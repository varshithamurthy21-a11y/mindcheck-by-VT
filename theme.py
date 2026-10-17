"""'Lagoon Bloom' theme: calm teal base with soft pastel colours, plus the friendly sidebar."""
import streamlit as st

import db

PAGES = [
    ("Home", "Start here"),
    ("Brain Battery", "90-second morning test"),
    ("Brain Puzzles", "Fluid, crystallized, memory"),
    ("Mind Journal", "Journal, body, emotion wheel"),
    ("Wellbeing Check-in", "Mood, stress, sensitivity"),
    ("My Progress", "Neuroagility trajectory"),
    ("Mind-Body Insights", "How mood affects your brain"),
    ("Grounding Toolbox", "Breathing and calm"),
    ("Help & Safety", "Support lines"),
]
PAGE_NAMES = [p for p, _ in PAGES]
PAGE_ICONS = {"Home": "🏡", "Brain Battery": "⚡", "Brain Puzzles": "🧩", "Mind Journal": "📝",
              "Wellbeing Check-in": "💙", "My Progress": "📈", "Mind-Body Insights": "🔗",
              "Grounding Toolbox": "🌿", "Help & Safety": "🤝"}
QUICK_MOODS = [("😞", 1, "Very low"), ("🙁", 2, "Low"), ("😐", 3, "Okay"), ("🙂", 4, "Good"), ("😄", 5, "Great")]

# Calm, colourful palette
TEAL, MINT, LAVENDER, PEACH, SKY, SUN = "#0F766E", "#CDEFE6", "#E7E1FC", "#FDE4D8", "#DCEBFA", "#FFF2CC"


def brain_svg(size=40):
    """Original two-colour brain logo."""
    return f"""<svg width="{size}" height="{size}" viewBox="0 0 48 48" role="img" aria-label="MindCheck brain logo">
<circle cx="24" cy="24" r="23" fill="#FFFFFF"/>
<path d="M23 9 C17 7 11 10 11 16 C7 17 6 22 8 25 C6 29 9 34 13 34 C14 38 19 40 23 38 Z"
      fill="#B9A8F2" stroke="#5B4BB8" stroke-width="1.6" stroke-linejoin="round"/>
<path d="M25 9 C31 7 37 10 37 16 C41 17 42 22 40 25 C42 29 39 34 35 34 C34 38 29 40 25 38 Z"
      fill="#8EDCC9" stroke="#0F766E" stroke-width="1.6" stroke-linejoin="round"/>
<g fill="none" stroke="#FFFFFF" stroke-width="1.8" stroke-linecap="round">
  <path d="M18 14 C15 17 19 19 16 22"/><path d="M12 27 C15 25 18 28 21 26"/><path d="M17 32 C19 30 21 33 22 31"/>
  <path d="M30 14 C33 17 29 19 32 22"/><path d="M36 27 C33 25 30 28 27 26"/><path d="M31 32 C29 30 27 33 26 31"/>
</g>
<circle cx="39" cy="9" r="3" fill="#F6B49A"/><circle cx="8" cy="40" r="2.2" fill="#F2C96B"/>
</svg>"""


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito:ital,wght@0,700;0,800;0,900;1,700&family=Nunito+Sans:wght@400;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, p, label, input, textarea, button { font-family: 'Nunito Sans', sans-serif; }
h1, h2, h3, h4, h5 { font-family: 'Nunito', sans-serif !important; font-weight: 800 !important; color: #12302E; }

/* soft pastel background, calm and bright */
.stApp {
  background:
    radial-gradient(circle at 8% 0%, #E7E1FC 0, rgba(231,225,252,0) 34%),
    radial-gradient(circle at 96% 6%, #DCEBFA 0, rgba(220,235,250,0) 30%),
    radial-gradient(circle at 85% 100%, #FDE4D8 0, rgba(253,228,216,0) 32%),
    radial-gradient(circle at 0% 95%, #D6F3EA 0, rgba(214,243,234,0) 30%),
    #F5F9F8;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2rem; max-width: 1120px; }

/* sidebar */
[data-testid="stSidebar"] { background: linear-gradient(180deg, #E6F5F0 0%, #EEEBFB 60%, #FCEFE8 100%);
  border-right: 1px solid #D6E6E2; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 2px; }
[data-testid="stSidebar"] [role="radiogroup"] label { padding: 9px 12px; border-radius: 14px; width: 100%;
  margin: 0; cursor: pointer; transition: background .15s; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.7); }
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: #0F766E;
  box-shadow: 0 6px 14px rgba(15,118,110,.25); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p { color: #FFFFFF; font-weight: 700; }
[data-testid="stSidebar"] .stButton > button { border-radius: 12px; padding: 4px 0; background: rgba(255,255,255,.8);
  border: 1px solid #D6E6E2; }
.st-key-breath button { background: #E7E1FC !important; border: 0 !important; color: #3D2F8F !important; }
.st-key-panic button { background: #F2A58E !important; border: 0 !important; color: #4A1A0D !important; }
.st-key-panic button:hover { background: #EE9479 !important; }

/* buttons */
.stButton > button, .stFormSubmitButton > button { border-radius: 999px; font-weight: 700; min-height: 44px; }

/* cards and metrics */
[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 22px; background: rgba(255,255,255,.92); }
[data-testid="stMetric"] { border-radius: 18px; padding: 14px 16px; background: #FFFFFF;
  box-shadow: 0 1px 2px rgba(18,48,46,.05), 0 8px 22px rgba(18,48,46,.06); border-top: 5px solid #8EDCC9; }
[data-testid="stColumn"]:nth-child(4n+2) [data-testid="stMetric"] { border-top-color: #B9A8F2; }
[data-testid="stColumn"]:nth-child(4n+3) [data-testid="stMetric"] { border-top-color: #F6B49A; }
[data-testid="stColumn"]:nth-child(4n+4) [data-testid="stMetric"] { border-top-color: #9CC3EE; }
.st-key-card_bb, .st-key-card_pz, .st-key-card_mj { border-radius: 18px; padding: 16px 16px 12px; }
.st-key-card_bb { background: #FFF2CC; }
.st-key-card_pz { background: #E7E1FC; }
.st-key-card_mj { background: #FDE4D8; }

/* tabs */
[data-baseweb="tab-list"] { gap: 6px; }
[data-baseweb="tab"] { background: rgba(255,255,255,.75); border-radius: 999px; padding: 6px 16px; }
[data-baseweb="tab"][aria-selected="true"] { background: #CDEFE6; }

.mc-eyebrow { font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #0F766E; }
.mc-hero { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 44px; line-height: 1.08; margin: 4px 0 8px; color: #12302E; }
.mc-sub { font-size: 17px; color: #3E5A57; max-width: 640px; }
.mc-brand { display: flex; align-items: center; gap: 10px; font-family: 'Nunito', sans-serif; font-weight: 900;
  font-size: 24px; color: #0F766E; margin-bottom: 6px; }
.mc-brand span.dot { color: #8B7CF6; }
.mc-brand .by { display: block; font-family: 'Nunito Sans', sans-serif; font-size: 12px; font-weight: 700;
  letter-spacing: .12em; text-transform: uppercase; color: #5B4BB8; margin-top: -2px; }
.mc-greet { background: rgba(255,255,255,.9); border-radius: 18px; padding: 14px; display: flex; gap: 12px;
  align-items: center; box-shadow: 0 6px 18px rgba(18,48,46,.07); margin-bottom: 8px; }
.mc-avatar { width: 44px; height: 44px; border-radius: 50%; background: linear-gradient(135deg, #0F766E, #8B7CF6);
  color: #fff; display: flex; align-items: center; justify-content: center; font-family: 'Nunito', sans-serif;
  font-weight: 900; font-size: 19px; flex: none; }
.mc-welcome { border-radius: 26px; padding: 28px 30px; margin-bottom: 14px; display: flex; gap: 22px; align-items: center;
  background: linear-gradient(120deg, #D6F3EA 0%, #E7E1FC 55%, #FDE4D8 100%);
  box-shadow: 0 10px 30px rgba(91,75,184,.10); flex-wrap: wrap; }
.mc-welcome .hello { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 38px; line-height: 1.1; color: #12302E; }
.mc-welcome .label { font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #5B4BB8; margin-top: 14px; }
.mc-welcome .quote { font-family: 'Nunito', sans-serif; font-style: italic; font-weight: 700; font-size: 22px;
  line-height: 1.35; color: #24324A; margin-top: 4px; max-width: 700px; }
.mc-chip { display: inline-block; padding: 4px 12px; margin: 3px 4px 3px 0; border-radius: 999px; font-size: 14px;
  font-weight: 700; background: #CDEFE6; color: #0B4F4A; }
.mc-chip.neg { background: #FDE4D8; color: #7A2E1C; }
.mc-card { background: #FFFFFF; border-radius: 20px; padding: 20px 22px; margin-bottom: 12px;
  box-shadow: 0 1px 2px rgba(18,48,46,.06), 0 8px 24px rgba(18,48,46,.06); }
.mc-card h4 { margin: 0 0 6px 0; }
.mc-note { background: linear-gradient(90deg, #DCEBFA, #E7E1FC); border-radius: 14px; padding: 14px 18px;
  color: #24324A; font-size: 15px; }
.mc-big { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 64px; line-height: 1; color: #0F766E; }
.mc-grid { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 26px; line-height: 1.25;
  letter-spacing: 4px; white-space: pre; background: #F1EEFC; border-radius: 14px; padding: 12px 16px;
  display: inline-block; color: #2B2160; }
table.mc-matrix { border-collapse: separate; border-spacing: 8px; }
table.mc-matrix td { width: 64px; height: 64px; text-align: center; font-size: 26px; font-weight: 800;
  background: #FFFFFF; border-radius: 14px; box-shadow: 0 2px 8px rgba(18,48,46,.08); }
table.mc-matrix td.q { background: #8B7CF6; color: #FFFFFF; }
.mc-stimulus { font-family: 'Nunito', sans-serif; font-weight: 900; font-size: 56px; text-align: center;
  background: linear-gradient(135deg, #FFFFFF, #F1EEFC); border-radius: 22px; padding: 28px; color: #12302E;
  letter-spacing: 6px; box-shadow: 0 8px 24px rgba(91,75,184,.10); }
</style>
"""


def apply_theme():
    st.markdown(CSS, unsafe_allow_html=True)


def go(page):
    """Callback: jump to a page (safe to use with on_click)."""
    st.session_state["nav"] = page


def _set_quick_mood(value):
    nick = st.session_state.get("nickname", "").strip()
    st.session_state["quick_mood"] = value
    if nick:
        db.insert("quick_mood", nick, value=value)
    if value == 1:
        st.session_state["nav"] = "Grounding Toolbox"


def sidebar():
    sb = st.sidebar
    sb.markdown(f'<div class="mc-brand">{brain_svg(42)}<div>Mind<span class="dot">Check</span><span class="by">by VT</span></div></div>',
                unsafe_allow_html=True)
    nick = sb.text_input("Nickname", key="nickname", placeholder="e.g. varsh",
                         help="Use a nickname, not your real name. Your results are saved under it.")
    nick = (nick or "").strip()
    initial = (nick[:1] or "?").upper()
    hello = f"Hi, {nick}" if nick else "Hi there"
    sb.markdown(f'<div class="mc-greet"><div class="mc-avatar">{initial}</div><div>'
                f'<div style="font-family:Nunito;font-weight:800;font-size:17px">{hello}</div>'
                f'<div style="font-size:13px;color:#4A6461">How are you feeling?</div></div></div>',
                unsafe_allow_html=True)
    cols = sb.columns(5)
    for col, (face, val, label) in zip(cols, QUICK_MOODS):
        col.button(face, key=f"qm{val}", help=label, on_click=_set_quick_mood, args=(val,),
                   type="primary" if st.session_state.get("quick_mood") == val else "secondary")

    if "nav" not in st.session_state:
        st.session_state["nav"] = "Home"
    sb.radio("Go to", PAGE_NAMES, key="nav", label_visibility="collapsed",
             format_func=lambda p: f"{PAGE_ICONS[p]}  {p}")

    sb.markdown("---")
    sb.button("🫁  1-minute breath", key="breath", use_container_width=True, on_click=go,
              args=("Grounding Toolbox",))
    sb.button("🤍  I need a moment", key="panic", use_container_width=True, on_click=go,
              args=("Grounding Toolbox",), help="Opens calming grounding exercises straight away")
    sb.caption("MindCheck is for self-reflection. It is not an IQ test or a medical diagnosis.")
    return nick
