"""Grounding Toolbox: box breathing, 5-4-3-2-1 senses game, body reset."""
import streamlit as st

from widgets import hero, support_box, box_breathing, calm_breath

SENSES = [(5, "things you can SEE", "👀", "e.g. a window, my phone, a cup"),
          (4, "things you can FEEL or touch", "✋", "e.g. my chair, my sleeves"),
          (3, "things you can HEAR", "👂", "e.g. a fan, birds, traffic"),
          (2, "things you can SMELL", "👃", "e.g. soap, tea (or two smells you like)"),
          (1, "thing you can TASTE", "👅", "e.g. toothpaste, water")]
G = "g54321"


def _g_next(n_needed, step):
    filled = [st.session_state.get(f"g_{step}_{k}", "").strip() for k in range(n_needed)]
    if sum(1 for f in filled if f) < n_needed:
        st.session_state[G]["warn"] = True
        return
    st.session_state[G]["warn"] = False
    st.session_state[G]["step"] += 1


def _g_reset():
    st.session_state[G] = {"step": 0, "warn": False}
    for k in list(st.session_state.keys()):
        if k.startswith("g_"):
            del st.session_state[k]


def senses_game():
    s = st.session_state.setdefault(G, {"step": 0, "warn": False})
    step = s["step"]
    if step >= len(SENSES):
        st.balloons()
        st.success("You did it. You brought your attention back to right here, right now.")
        feel = st.select_slider("How do you feel now?", ["Still very upset", "A bit better", "Calmer", "Much calmer"],
                                value="A bit better")
        if feel == "Still very upset":
            st.write("That's okay. Try box breathing next, and please consider calling a support line.")
        st.button("Start again", on_click=_g_reset)
        return
    n, what, icon, hint = SENSES[step]
    st.progress(step / len(SENSES), text=f"Step {step + 1} of 5")
    st.markdown(f"### {icon} Name {n} {what}")
    cols = st.columns(min(n, 5))
    for k in range(n):
        cols[k % len(cols)].text_input(f"{k + 1}", key=f"g_{step}_{k}", placeholder=hint if k == 0 else "",
                                       label_visibility="collapsed")
    if s["warn"]:
        st.warning(f"Take your time. Try to fill all {n}. Small things count!")
    st.button("Next", type="primary", on_click=_g_next, args=(n, step))


def render(nick):
    hero("Grounding Toolbox", "Let's slow things down together.",
         "Pick one exercise. Each one takes about two minutes and helps your body feel safe again.")
    with st.expander("Need to talk to someone? Support lines", expanded=False):
        support_box(compact=True)

    t1, t2, t3 = st.tabs(["⬜ Box breathing", "🖐 5-4-3-2-1 senses", "🧘 Body reset"])
    with t1:
        st.write("Follow the dot around the square: breathe in for 4, hold for 4, breathe out for 4, hold for 4.")
        box_breathing(4, 4)
    with t2:
        st.write("This game pulls your attention out of worried thoughts and into your senses.")
        senses_game()
    with t3:
        st.markdown("""
1. **Feet on the floor.** Press them down and notice the ground holding you.
2. **Drop your shoulders.** Let them fall away from your ears.
3. **Unclench your jaw.** Let your tongue rest at the bottom of your mouth.
4. **Hand on your chest.** Feel it rise and fall.
5. **Long breath out.** Breathe in for 4 and out for 6, six times, with the circle below.
""")
        calm_breath(4, 6, rounds=6)
    st.caption("If you feel unsafe, please call 112 or Tele-MANAS on 14416 now.")
