"""
Private, on-device emotion analysis for micro-journals.

No text ever leaves the app: this uses a small hand-written word list
(written for MindCheck) with simple handling of "not", "very", etc.
It finds emotions the user may not have picked on a checklist.
"""
import re

EMOTIONS = {
    "anxiety": {"label": "Anxiety", "valence": -1, "cues": [
        "anxious", "anxiety", "worried", "worry", "worrying", "nervous", "uneasy", "panic", "panicking",
        "scared", "afraid", "fear", "overthinking", "overthink", "what if", "restless", "on edge", "dread",
        "can't stop thinking", "cant stop thinking", "tense", "jittery", "butterflies"]},
    "stress": {"label": "Stress", "valence": -1, "cues": [
        "stressed", "stress", "stressful", "pressure", "deadline", "deadlines", "too much", "swamped",
        "rushed", "hectic", "overloaded", "behind on", "so much to do", "chaotic", "overwhelmed"]},
    "burnout": {"label": "Burnout", "valence": -1, "cues": [
        "exhausted", "drained", "burnt out", "burned out", "burnout", "no energy", "worn out",
        "running on empty", "can't keep up", "cant keep up", "tired of", "fed up with work",
        "no motivation", "unmotivated", "numb", "empty", "dragging myself"]},
    "sadness": {"label": "Sadness", "valence": -1, "cues": [
        "sad", "down", "cried", "crying", "upset", "unhappy", "heartbroken", "disappointed", "miss",
        "missing", "low", "gloomy", "hurt", "blue", "tearful", "lost"]},
    "loneliness": {"label": "Loneliness", "valence": -1, "cues": [
        "lonely", "alone", "isolated", "no one", "nobody", "left out", "ignored", "by myself",
        "no friends", "disconnected", "homesick"]},
    "anger": {"label": "Frustration", "valence": -1, "cues": [
        "angry", "annoyed", "frustrated", "frustrating", "irritated", "furious", "unfair", "fed up",
        "mad", "hate", "rage", "snapped"]},
    "gratitude": {"label": "Gratitude", "valence": 1, "cues": [
        "grateful", "thankful", "thanks to", "appreciate", "appreciated", "blessed", "lucky",
        "glad i have", "so kind", "helped me"]},
    "joy": {"label": "Joy", "valence": 1, "cues": [
        "happy", "excited", "great", "fun", "laughed", "laughing", "proud", "amazing", "enjoyed",
        "good day", "wonderful", "awesome", "smiled", "delighted", "celebrated", "loved it"]},
    "calm": {"label": "Calm", "valence": 1, "cues": [
        "calm", "relaxed", "peaceful", "rested", "content", "at ease", "chill", "slept well",
        "quiet day", "balanced", "okay", "fine"]},
    "hope": {"label": "Hope & motivation", "valence": 1, "cues": [
        "hopeful", "looking forward", "motivated", "can't wait", "cant wait", "determined",
        "progress", "inspired", "confident", "finally", "achieved", "ready"]},
}

# Phrases that mean someone may be in danger. Used only to show support at once.
CRISIS_CUES = ["kill myself", "end my life", "want to die", "suicide", "suicidal", "hurt myself",
               "harm myself", "self harm", "self-harm", "no reason to live", "better off without me",
               "can't go on", "cant go on", "don't want to be here", "dont want to be here"]

NEGATORS = {"not", "no", "never", "isn't", "isnt", "wasn't", "wasnt", "don't", "dont", "didn't",
            "didnt", "hardly", "barely", "without"}
INTENSIFIERS = {"very": 1.5, "really": 1.4, "so": 1.4, "extremely": 1.8, "super": 1.5,
                "totally": 1.5, "completely": 1.6, "too": 1.3, "a bit": 0.7, "slightly": 0.6,
                "little": 0.7}


def _tokens(text):
    return re.findall(r"[a-z']+", text.lower())


def analyze(text):
    text = (text or "").strip()
    low = " " + " ".join(_tokens(text)) + " "
    crisis = any(c in text.lower() for c in CRISIS_CUES)
    scores, evidence = {}, {}
    for key, info in EMOTIONS.items():
        for cue in sorted(info["cues"], key=len, reverse=True):
            cue_norm = " " + " ".join(_tokens(cue)) + " "
            start = 0
            while True:
                i = low.find(cue_norm, start)
                if i < 0:
                    break
                start = i + len(cue_norm)
                before = low[:i].split()[-3:]
                weight = 1.0
                for w in before:
                    if w in INTENSIFIERS:
                        weight *= INTENSIFIERS[w]
                negated = any(w in NEGATORS for w in before)
                if negated:
                    # "not worried" hints at calm; "not happy" hints at sadness
                    target = "calm" if info["valence"] < 0 else "sadness"
                    scores[target] = scores.get(target, 0) + 0.5
                    evidence.setdefault(target, []).append(f"not {cue}")
                else:
                    scores[key] = scores.get(key, 0) + weight
                    evidence.setdefault(key, []).append(cue)
                low = low[:i] + " " + "_" * (len(cue_norm) - 2) + " " + low[start:]
                start = i + len(cue_norm)
    total = sum(scores.values())
    emotions = []
    for key, s in sorted(scores.items(), key=lambda kv: -kv[1]):
        emotions.append({"key": key, "label": EMOTIONS[key]["label"], "strength": round(s / total, 2),
                         "evidence": sorted(set(evidence[key]))})
    pos = sum(s for k, s in scores.items() if EMOTIONS[k]["valence"] > 0)
    neg = sum(s for k, s in scores.items() if EMOTIONS[k]["valence"] < 0)
    sentiment = round((pos - neg) / total, 2) if total else 0.0
    return {"emotions": emotions[:4], "sentiment": sentiment, "crisis": crisis,
            "word_count": len(_tokens(text))}


def sentiment_label(s):
    if s >= 0.4:
        return "Mostly positive"
    if s > -0.4:
        return "Mixed"
    return "Mostly heavy"
