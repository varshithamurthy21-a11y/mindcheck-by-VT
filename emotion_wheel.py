"""
MindCheck Emotion Wheel (original grouping and wording).
Three rings: core feeling -> group -> specific feeling.
Drilling down from a broad word ("Bad") to a precise one ("Overwhelmed")
builds emotional vocabulary.
"""

WHEEL = {
    "Happy": {"color": "#F2C14E", "tip": "Notice what made today good and try to repeat it.", "groups": {
        "Content": {"Peaceful": "Settled and free from worry.", "Satisfied": "Pleased with how things are."},
        "Proud": {"Confident": "Sure of your own ability.", "Accomplished": "You finished something that mattered."},
        "Playful": {"Cheerful": "Light, bright and easy to smile.", "Silly": "In the mood to have fun."},
        "Grateful": {"Appreciative": "Thankful for someone or something.", "Touched": "Moved by kindness."},
    }},
    "Calm": {"color": "#5FB3A1", "tip": "Calm is a great time for focused work or deep puzzles.", "groups": {
        "Relaxed": {"Rested": "Your body feels recharged.", "At ease": "Comfortable where you are."},
        "Centred": {"Balanced": "Steady, not pulled in many directions.", "Present": "Fully in this moment."},
        "Safe": {"Secure": "Protected and supported.", "Trusting": "Able to rely on others."},
    }},
    "Sad": {"color": "#6C8EBF", "tip": "Sadness often needs company. Reach out to someone you trust.", "groups": {
        "Lonely": {"Isolated": "Cut off from people around you.", "Left out": "Not included by others.",
                   "Homesick": "Missing home or familiar people."},
        "Hurt": {"Disappointed": "Something did not go the way you hoped.", "Let down": "Someone did not keep their word.",
                 "Rejected": "Pushed away or not wanted."},
        "Low": {"Empty": "Flat, like nothing matters much.", "Gloomy": "A heavy, grey mood.",
                "Discouraged": "Losing belief that things will improve."},
        "Guilty": {"Regretful": "Wishing you had done something differently.", "Ashamed": "Feeling bad about who you are."},
    }},
    "Angry": {"color": "#D9725E", "tip": "Anger carries energy. A brisk walk can release it safely.", "groups": {
        "Frustrated": {"Stuck": "Blocked from moving forward.", "Annoyed": "Bothered by small things."},
        "Resentful": {"Bitter": "Holding on to an old hurt.", "Jealous": "Wanting what someone else has."},
        "Irritated": {"Impatient": "Wanting things to happen faster.", "Touchy": "Easily set off."},
    }},
    "Anxious": {"color": "#A78BDA", "tip": "Slow breathing tells your body it is safe. Try box breathing.", "groups": {
        "Worried": {"Nervous": "Uneasy about what might happen.", "Insecure": "Unsure of yourself."},
        "Scared": {"Panicked": "A sudden rush of fear.", "Helpless": "Feeling you cannot change things."},
        "Restless": {"On edge": "Tense and alert, hard to settle.", "Unfocused": "Your mind keeps jumping around."},
    }},
    "Bad": {"color": "#8D99A6", "tip": "When 'bad' is all you can say, start with rest and water.", "groups": {
        "Stressed": {"Overwhelmed": "Too much at once to handle.", "Pressured": "Pushed by deadlines or others.",
                     "Out of control": "Things feel like they are slipping away."},
        "Tired": {"Drained": "Your energy has run out.", "Sleepy": "Your body wants rest.",
                  "Burnt out": "Worn down from pushing too long."},
        "Disconnected": {"Isolated": "Far from people, even when they are near.", "Numb": "Hard to feel anything.",
                         "Bored": "Nothing feels interesting."},
    }},
    "Surprised": {"color": "#E59AC0", "tip": "Surprise means something new. Take a moment to make sense of it.", "groups": {
        "Amazed": {"Awed": "Struck by something wonderful.", "Inspired": "Filled with new ideas."},
        "Confused": {"Puzzled": "Not sure what is going on.", "Torn": "Pulled between two choices."},
        "Startled": {"Shocked": "Caught completely off guard.", "Alarmed": "Suddenly worried."},
    }},
}

# Specific feelings that suggest the user may want grounding right away
DISTRESS_WORDS = {"Panicked", "Helpless", "Overwhelmed", "Out of control", "Empty", "Discouraged", "Ashamed"}


def cores():
    return list(WHEEL)


def groups(core):
    return list(WHEEL[core]["groups"])


def specifics(core, group):
    return WHEEL[core]["groups"][group]


def sunburst_data(selected_core=None, selected_group=None, selected_specific=None):
    """ids, labels, parents, colors for a Plotly sunburst. Highlights the chosen path."""
    ids, labels, parents, colors = [], [], [], []

    def col(base, on):
        r, g, b = int(base[1:3], 16), int(base[3:5], 16), int(base[5:7], 16)
        return f"rgba({r},{g},{b},{1 if on else 0.3})"   # faded when not selected

    any_sel = selected_core is not None
    for core, info in WHEEL.items():
        on_core = (not any_sel) or core == selected_core
        ids.append(core); labels.append(core); parents.append(""); colors.append(col(info["color"], on_core))
        for g, feelings in info["groups"].items():
            gid = f"{core}/{g}"
            on_g = (not any_sel) or (core == selected_core and (selected_group in (None, g)))
            ids.append(gid); labels.append(g); parents.append(core); colors.append(col(info["color"], on_g))
            for f in feelings:
                on_f = (not any_sel) or (core == selected_core and g == selected_group
                                         and selected_specific in (None, f))
                ids.append(f"{gid}/{f}"); labels.append(f); parents.append(gid)
                colors.append(col(info["color"], on_f))
    return ids, labels, parents, colors
