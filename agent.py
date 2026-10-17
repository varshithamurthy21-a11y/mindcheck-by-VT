"""
MindCheck coach agent.

The agent runs a pipeline of small "tools":
  1. read_state      - today's body check-in, journal emotions, wheel feeling, readiness
  2. safety_check    - is grounding / support needed right now?
  3. choose_mode     - calm / normal / challenge puzzles (core.adaptive)
  4. plan_day        - 2-3 concrete next steps
  5. explain         - a warm summary (Claude if an API key is set, else a template)

Scores, safety and modes are always rule-based, so the AI can never invent
a number or skip a safety step. The AI only writes the friendly words.
"""
import os

from core import adaptive
from core.content import TIPS, score_wellbeing, wellbeing_needs_support

MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = """You are MindCheck, a kind wellbeing and brain-training coach.
Write in simple, warm English with short sentences.
Rules:
- Never diagnose any condition. Never use words like depression, anxiety disorder, PTSD or trauma.
- Never change or invent numbers. Use only the facts given.
- If support_needed is true, begin by gently encouraging the user to use the grounding tools or support lines.
- Under 120 words. No headings, no bullet lists."""


def _api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        return None


def _ask_claude(facts: str):
    key = _api_key()
    if not key:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)
        resp = client.messages.create(model=MODEL, max_tokens=350, system=SYSTEM_PROMPT,
                                      messages=[{"role": "user", "content": facts}])
        return resp.content[0].text.strip()
    except Exception:
        return None


def daily_coach(nickname):
    steps = []
    state = adaptive.current_state(nickname)
    steps.append("Read today's check-ins")
    support = adaptive.needs_grounding(state)
    steps.append("Ran the safety check")
    mode = adaptive.recommend(state)
    steps.append(f"Chose {mode['title'].lower()} for puzzles")

    plan = []
    if support:
        plan.append(("grounding", "Take two minutes with the Grounding Toolbox first."))
    if state.get("readiness") is None:
        plan.append(("battery", "Charge up with the 90-second Brain Battery."))
    if state.get("stress") is None:
        plan.append(("journal", "Do a 20-second body check-in so puzzles can adapt to you."))
    if mode["mode"] == "calm":
        plan.append(("puzzles", "Try a few calm spatial puzzles. No timer today."))
    elif mode["mode"] == "challenge":
        plan.append(("puzzles", "You're sharp today. Try level 3 puzzles."))
    else:
        plan.append(("puzzles", "Play a mixed puzzle set and see where you are strongest."))
    steps.append("Planned your next steps")

    facts = (f"support_needed: {support}\nstress: {state.get('stress')}\nenergy: {state.get('energy')}\n"
             f"readiness: {state.get('readiness')}\nheavy emotions in journal: {state.get('heavy_emotions')}\n"
             f"feeling from wheel: {state.get('wheel_feeling')}\nmode: {mode['title']}\n"
             f"plan: {[p[1] for p in plan]}\nWrite a short good-morning message for {nickname or 'friend'}.")
    text = _ask_claude(facts)
    used_ai = text is not None
    if not text:
        if support:
            text = ("It sounds like today might be heavy. You don't have to push through alone. "
                    "Start with a short grounding exercise, and reach out to the support lines if you need to.")
        elif mode["mode"] == "calm":
            text = "Let's keep today gentle. A few calm puzzles and a short breathing break can help you reset."
        elif mode["mode"] == "challenge":
            text = "You're in great shape today! It's a good day to stretch your brain with harder puzzles."
        else:
            text = "Welcome back! A quick check-in and a few puzzles will show how your mind is doing today."
    steps.append("Wrote your message" + (" with AI" if used_ai else ""))
    return {"state": state, "support": support, "mode": mode, "plan": plan,
            "message": text, "steps": steps, "used_ai": used_ai}


def checkin_summary(responses, safety_answer, nickname=""):
    scores = score_wellbeing(responses)
    support = wellbeing_needs_support(scores, safety_answer)
    tips = {k: TIPS[k][v["band"]] for k, v in scores.items()}
    facts = (f"Name: {nickname or 'friend'}\nsupport_needed: {support}\n" +
             "\n".join(f"{k}: {v['score']}/{v['max']} ({v['band']})" for k, v in scores.items()) +
             "\nWrite their personal summary of this self check-in.")
    text = _ask_claude(facts)
    used_ai = text is not None
    if not text:
        parts = []
        if support:
            parts.append("Thank you for being honest. It sounds like things have been hard lately, and you "
                         "don't have to handle that alone. Please consider the support lines below or someone you trust.")
        parts += list(tips.values())
        parts.append("Remember, this is a self check-in, not a diagnosis.")
        text = " ".join(parts)
    return {"scores": scores, "support": support, "tips": tips, "summary": text, "used_ai": used_ai}
