"""
Positive thoughts for the daily greeting. All written for MindCheck (original),
so there are no copyright or attribution worries.
"""
import os
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None

TIMEZONE = os.environ.get("MINDCHECK_TZ", "Asia/Kolkata")

UPLIFTING = [
    "Your mind is like a garden. What you water today grows tomorrow.",
    "Small steps still move you forward. Today, one small step is enough.",
    "You don't have to be perfect to be wonderful.",
    "Every puzzle you try makes your brain a little stronger, even the ones you miss.",
    "Curiosity is a superpower. Ask one new question today.",
    "Be proud of how far you've come, and gentle about how far you have to go.",
    "A calm mind sees clearly. Take one slow breath before you begin.",
    "Learning is not a race. Your pace is the right pace.",
    "Mistakes are just proof that you are trying something new.",
    "Today is a fresh page. You get to write the first line.",
    "Your effort matters more than the score.",
    "Bright ideas often arrive after a little rest.",
    "Kindness to yourself is the best fuel for your brain.",
    "You are allowed to grow slowly. Trees do, and they reach the sky.",
    "One good thought can change the whole shape of a day.",
    "The more you practise, the more your brain builds new paths.",
    "Notice one thing you're grateful for. Let it warm you for a moment.",
    "Confidence grows every time you show up, even on hard days.",
    "Your story is still being written, and it has many good chapters ahead.",
    "Focus on what you can do today. That is where your power lives.",
    "A smile, a stretch and a sip of water: a tiny reset with big results.",
    "You bring something to the world that no one else can.",
    "Progress, not perfection. Every day counts.",
    "Let today be a day of trying, learning and being kind to yourself.",
]

GENTLE = [
    "It's okay to have a heavy day. You don't have to carry it all at once.",
    "Rest is not giving up. Rest is how strength comes back.",
    "You have made it through every hard day so far. That is real courage.",
    "Breathe in slowly. Breathe out longer. You are safe in this moment.",
    "Be as kind to yourself today as you would be to a good friend.",
    "Feelings are like weather. Even storms pass, and the sky clears again.",
    "Asking for help is a sign of strength, not weakness.",
    "You don't need to have it all figured out. Just the next small step.",
    "Today, doing less is enough. Gentle is still moving forward.",
    "You matter, exactly as you are, on good days and hard days.",
    "Slow down. Your mind deserves a little peace too.",
    "One breath, one moment, one step at a time.",
]


def local_now():
    if ZoneInfo:
        try:
            return datetime.now(ZoneInfo(TIMEZONE))
        except Exception:
            pass
    return datetime.now()


def greeting(now=None):
    h = (now or local_now()).hour
    if 5 <= h < 12:
        return "Good morning", "☀️"
    if 12 <= h < 17:
        return "Good afternoon", "🌤️"
    if 17 <= h < 21:
        return "Good evening", "🌇"
    return "Hello, night owl", "🌙"


def thought_for_today(heavy_day=False, offset=0, day=None):
    """Same thought all day (changes daily); `offset` lets the user ask for another one."""
    pool = GENTLE if heavy_day else UPLIFTING
    d = day or local_now().date()
    idx = (d.toordinal() + offset) % len(pool)
    return pool[idx]
