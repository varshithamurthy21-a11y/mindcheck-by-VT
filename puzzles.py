"""
Puzzle engine. Most puzzles are generated fresh every time from simple rules,
so there are thousands of combinations and nothing is copied from any test.
The word banks below were written for MindCheck.

A puzzle is a dict:
  pillar, skill, difficulty (1-3), prompt, options (list[str]), answer (str),
  explanation, and optionally grid (matrix table) or option_grids (spatial).
"""
import random

PILLARS = {
    "fluid": {"name": "Fluid intelligence", "skills": ["pattern", "matrix", "spatial"],
              "blurb": "Spot rules and patterns you have never seen before."},
    "crystallized": {"name": "Crystallized intelligence", "skills": ["vocabulary", "analogy", "trivia_logic"],
                     "blurb": "Use what you already know: words, meaning and facts."},
    "memory": {"name": "Working memory", "skills": ["nback", "sequence"],
               "blurb": "Hold information in mind and update it."},
}

SKILL_NAMES = {
    "pattern": "Pattern recognition", "matrix": "Matrix reasoning", "spatial": "Spatial manipulation",
    "vocabulary": "Vocabulary", "analogy": "Verbal analogies", "trivia_logic": "Trivia logic",
    "nback": "N-back", "sequence": "Sequence memory",
    "speed": "Processing speed", "reaction": "Reaction time", "battery_memory": "Quick memory",
}

# Six axes of the cognitive profile graph
PROFILE_AXES = {
    "Pattern & matrix": ["pattern", "matrix"],
    "Spatial": ["spatial"],
    "Verbal": ["vocabulary", "analogy"],
    "Logic & knowledge": ["trivia_logic"],
    "Working memory": ["nback", "sequence", "battery_memory"],
    "Speed": ["speed", "reaction"],
}

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _rng(rng):
    return rng or random.Random()


def _mc(answer, distractors, rng):
    """Build 4 unique shuffled options as strings."""
    answer = str(answer)
    opts = [answer]
    for d in distractors:
        d = str(d)
        if d not in opts:
            opts.append(d)
        if len(opts) == 4:
            break
    filler = 1
    while len(opts) < 4:  # numeric fallback
        try:
            cand = str(int(answer) + filler * (1 if filler % 2 else -1) * 3)
        except ValueError:
            cand = answer + "?" * filler
        if cand not in opts:
            opts.append(cand)
        filler += 1
    rng.shuffle(opts)
    return opts


def _num_distractors(ans, step, rng):
    c = [ans + step, ans - step, ans + 1, ans - 1, ans + 2 * step, ans + rng.randint(3, 9)]
    return [x for x in c if x > 0 and x != ans]


# ------------------------------------------------------------------ FLUID
def pattern(difficulty=1, rng=None):
    rng = _rng(rng)
    kind = {1: ["add", "letters"], 2: ["mul", "gaps", "alternate"], 3: ["affine", "squares", "fib"]}[difficulty]
    kind = rng.choice(kind)
    if kind == "letters":
        k, s = rng.randint(2, 4), rng.randint(0, 6)
        seq = [LETTERS[s + i * k] for i in range(4)]
        ans = LETTERS[s + 4 * k]
        near = [LETTERS[min(25, s + 4 * k + d)] for d in (1, -1, 2)]
        return _pz("fluid", "pattern", difficulty, f"Which letter comes next?   {', '.join(seq)}, ?",
                   _mc(ans, near, rng), ans, f"Each step moves {k} letters forward.")
    if kind == "add":
        k, s = rng.randint(2, 9), rng.randint(1, 20)
        seq = [s + i * k for i in range(5)]
        ans, why = s + 5 * k, f"Add {k} each time."
        step = k
    elif kind == "mul":
        m, s = rng.choice([2, 3]), rng.randint(1, 5)
        seq = [s * m ** i for i in range(5)]
        ans, why, step = s * m ** 5, f"Multiply by {m} each time.", seq[-1]
    elif kind == "gaps":
        a, inc, s = rng.randint(1, 4), rng.randint(1, 3), rng.randint(1, 10)
        seq, gap = [s], a
        for _ in range(5):
            seq.append(seq[-1] + gap)
            gap += inc
        ans, why, step = seq.pop(), f"The gap grows by {inc} each time.", inc
    elif kind == "alternate":
        a, b, ka, kb = rng.randint(1, 9), rng.randint(20, 40), rng.randint(2, 5), -rng.randint(1, 4)
        seq = []
        for i in range(6):
            seq.append(a + (i // 2) * ka if i % 2 == 0 else b + (i // 2) * kb)
        ans = a + 3 * ka
        why, step = f"Two patterns take turns: one adds {ka}, the other subtracts {-kb}.", ka
    elif kind == "affine":
        m, c, s = 2, rng.choice([-1, 1, 2, 3]), rng.randint(1, 5)
        seq = [s]
        for _ in range(4):
            seq.append(seq[-1] * m + c)
        ans = seq[-1] * m + c
        why = f"Double the number, then {'add' if c > 0 else 'subtract'} {abs(c)}."
        step = abs(c) + 1
    elif kind == "squares":
        c, s = rng.randint(-2, 3), rng.randint(1, 4)
        seq = [(s + i) ** 2 + c for i in range(5)]
        ans = (s + 5) ** 2 + c
        why = f"Square numbers ({s}x{s}, {s+1}x{s+1}, ...){' plus ' + str(c) if c > 0 else ' minus ' + str(-c) if c < 0 else ''}."
        step = 2 * (s + 5) - 1
    else:  # fib
        a, b = rng.randint(1, 5), rng.randint(2, 7)
        seq = [a, b]
        for _ in range(4):
            seq.append(seq[-1] + seq[-2])
        ans = seq[-1] + seq[-2]
        why, step = "Each number is the sum of the two before it.", seq[-2]
    return _pz("fluid", "pattern", difficulty, f"What comes next?   {', '.join(map(str, seq))}, ?",
               _mc(ans, _num_distractors(ans, step, rng), rng), ans, why)


def matrix(difficulty=1, rng=None):
    rng = _rng(rng)
    if difficulty == 1:
        k = rng.randint(2, 6)
        starts = rng.sample(range(1, 15), 3)
        grid = [[s, s + k, s + 2 * k] for s in starts]
        why, step = f"In every row, each number is {k} more than the one before.", k
    elif difficulty == 2:
        total = rng.randint(15, 30)
        grid = []
        for _ in range(3):
            a, b = rng.randint(1, total // 2), rng.randint(1, total // 3)
            grid.append([a, b, total - a - b])
        why, step = f"Every row adds up to {total}.", 2
    else:
        if rng.random() < 0.5:
            grid = [[a, b, a * b] for a, b in ((rng.randint(2, 7), rng.randint(2, 6)) for _ in range(3))]
            why = "In each row, the third number is the first times the second."
        else:
            r1 = [rng.randint(1, 9) for _ in range(3)]
            r2 = [rng.randint(1, 9) for _ in range(3)]
            grid = [r1, r2, [x + y for x, y in zip(r1, r2)]]
            why = "In each column, the bottom number is the sum of the two above it."
        step = 3
    ans = grid[2][2]
    shown = [[str(x) for x in row] for row in grid]
    shown[2][2] = "?"
    return _pz("fluid", "matrix", difficulty, "Find the missing number in the grid.",
               _mc(ans, _num_distractors(ans, step, rng), rng), ans, why, grid=shown)


def _rot_cw(g):
    return [list(r) for r in zip(*g[::-1])]


def _rot_ccw(g):
    return [list(r) for r in zip(*g)][::-1]


def _flip_lr(g):
    return [r[::-1] for r in g]


def _flip_ud(g):
    return g[::-1]


TRANSFORMS = {
    "turned 90° clockwise": _rot_cw,
    "turned 90° anticlockwise": _rot_ccw,
    "turned upside down (180°)": lambda g: _rot_cw(_rot_cw(g)),
    "flipped left-to-right (mirror)": _flip_lr,
    "flipped top-to-bottom": _flip_ud,
    "turned 90° clockwise and then mirrored": lambda g: _flip_lr(_rot_cw(g)),
}


def grid_text(g):
    return "\n".join(" ".join("■" if c else "□" for c in row) for row in g)


def spatial(difficulty=1, rng=None):
    rng = _rng(rng)
    if difficulty >= 2 and rng.random() < 0.3:
        return _walk(difficulty, rng)
    size = 4 if difficulty == 3 else 3
    names = {1: ["turned 90° clockwise"],
             2: ["turned 90° clockwise", "turned 90° anticlockwise", "turned upside down (180°)",
                 "flipped left-to-right (mirror)"],
             3: ["turned 90° clockwise and then mirrored", "turned 90° anticlockwise",
                 "flipped top-to-bottom"]}[difficulty]
    name = rng.choice(names)
    for _ in range(200):
        cells = rng.sample(range(size * size), rng.randint(size, size + 3))
        g = [[1 if r * size + c in cells else 0 for c in range(size)] for r in range(size)]
        correct = TRANSFORMS[name](g)
        others = []
        for n, f in TRANSFORMS.items():
            cand = f(g)
            if n != name and cand != correct and cand not in others:
                others.append(cand)
        if g != correct and g not in others:
            others.append(g)
        if len(others) >= 3:
            break
    picks = [correct] + rng.sample(others, 3)
    rng.shuffle(picks)
    labels = ["A", "B", "C", "D"]
    ans = labels[picks.index(correct)]
    p = _pz("fluid", "spatial", difficulty,
            f"Here is a shape. Which option shows it **{name}**?",
            labels, ans, f"Option {ans} is the shape {name}.")
    p["grid_shape"] = grid_text(g)
    p["option_grids"] = [grid_text(x) for x in picks]
    return p


def _walk(difficulty, rng):
    dirs = ["north", "east", "south", "west"]
    vec = {"north": (0, 1), "east": (1, 0), "south": (0, -1), "west": (-1, 0)}
    facing = start = rng.randint(0, 3)
    steps, x, y = [], 0, 0
    n = 3 if difficulty == 2 else 4
    for i in range(n):
        if i:
            turn = rng.choice(["right", "left"])
            facing = (facing + (1 if turn == "right" else -1)) % 4
            steps.append(f"turn {turn}")
        d = rng.randint(2, 6)
        dx, dy = vec[dirs[facing]]
        x, y = x + dx * d, y + dy * d
        steps.append(f"walk {d} m")

    def describe(x, y):
        parts = []
        if y:
            parts.append(f"{abs(y)} m {'north' if y > 0 else 'south'}")
        if x:
            parts.append(f"{abs(x)} m {'east' if x > 0 else 'west'}")
        return " and ".join(parts) or "back at the start"

    ans = describe(x, y)
    wrong = [describe(-x, y), describe(x, -y), describe(y, x), describe(-x, -y), describe(x + 2, y)]
    prompt = (f"You start facing {dirs[start]}. You {', then '.join(steps)}. "
              "Where are you now compared with where you started?")
    return _pz("fluid", "spatial", difficulty, prompt, _mc(ans, wrong, rng), ans,
               "Track each move on an imaginary map, one step at a time.")



# ------------------------------------------------------------------ CRYSTALLIZED
VOCAB = {
    1: [("Brief", "Short in time", ["Very bright", "Heavy", "Polite"]),
        ("Fragile", "Easily broken", ["Very old", "Sweet smelling", "Quick to anger"]),
        ("Ancient", "Very old", ["Very loud", "Nearby", "Freshly made"]),
        ("Generous", "Happy to give", ["Easily scared", "Always late", "Very tall"]),
        ("Rapid", "Very fast", ["Rough", "Rare", "Ready"]),
        ("Vacant", "Empty", ["Full of colour", "On holiday", "Very valuable"]),
        ("Humble", "Not proud", ["Quietly humming", "Damp", "Huge"]),
        ("Timid", "Shy and easily scared", ["Well organised", "Very small", "Sticky"]),
        ("Frequent", "Happening often", ["Very cold", "Friendly", "Free of cost"]),
        ("Reluctant", "Unwilling", ["Shining", "Returning", "Relaxed"])],
    2: [("Candid", "Honest and direct", ["Sweet like sugar", "Hidden", "Bright with light"]),
        ("Diligent", "Hard-working and careful", ["Slow to understand", "Very delicate", "Sad"]),
        ("Obsolete", "No longer used", ["Very large", "Impossible to see", "Stubborn"]),
        ("Lucid", "Clear and easy to understand", ["Lucky", "Slippery", "Lazy"]),
        ("Meticulous", "Very careful about details", ["Extremely small", "Fond of metal", "Musical"]),
        ("Resilient", "Quick to recover", ["Very shiny", "Quietly resting", "Easily annoyed"]),
        ("Ambiguous", "Having more than one meaning", ["Using both hands", "Very ambitious", "Huge in size"]),
        ("Tranquil", "Calm and peaceful", ["See-through", "Moving fast", "Sharp"]),
        ("Scarce", "Hard to find", ["Frightening", "Marked with a scar", "Very thin"]),
        ("Hostile", "Unfriendly and aggressive", ["Welcoming guests", "Very hot", "Holding tightly"])],
    3: [("Ephemeral", "Lasting a very short time", ["Related to the sky", "Made of glass", "Wise"]),
        ("Pragmatic", "Practical and realistic", ["Very proud", "Full of drama", "Talkative"]),
        ("Ubiquitous", "Found everywhere", ["Single and unique", "Very loud", "Difficult to like"]),
        ("Benevolent", "Kind and well-meaning", ["Easily bent", "Very lucky", "Dangerous"]),
        ("Esoteric", "Understood by only a few", ["Outside the body", "Very pleasant", "Easy to break"]),
        ("Laconic", "Using very few words", ["Lazy and slow", "Made of lace", "Full of energy"]),
        ("Cogent", "Clear and convincing", ["Mechanical", "Shared by two", "Thick and sticky"]),
        ("Gregarious", "Fond of company", ["Greedy", "Serious", "Large and heavy"]),
        ("Superfluous", "More than is needed", ["Extremely fluent", "Shallow", "Above average"]),
        ("Equanimity", "Calmness under pressure", ["Equal shares", "Care of animals", "Fairness in law"])],
}

ANALOGIES = {
    1: [("Bird", "Nest", "Bee", "Hive", ["Honey", "Flower", "Wing"]),
        ("Pen", "Write", "Knife", "Cut", ["Fork", "Sharp", "Kitchen"]),
        ("Hot", "Cold", "Up", "Down", ["High", "Sky", "Over"]),
        ("Puppy", "Dog", "Kitten", "Cat", ["Milk", "Mouse", "Pet"]),
        ("Foot", "Shoe", "Hand", "Glove", ["Finger", "Ring", "Arm"]),
        ("Teacher", "School", "Doctor", "Hospital", ["Medicine", "Nurse", "Patient"]),
        ("Fish", "Water", "Bird", "Air", ["Tree", "Feather", "Egg"]),
        ("Day", "Night", "Summer", "Winter", ["Sun", "Holiday", "Rain"])],
    2: [("Book", "Library", "Painting", "Gallery", ["Artist", "Brush", "Frame"]),
        ("Thermometer", "Temperature", "Clock", "Time", ["Wall", "Alarm", "Hour hand"]),
        ("Author", "Novel", "Composer", "Symphony", ["Piano", "Orchestra", "Concert"]),
        ("Drought", "Water", "Famine", "Food", ["Hunger", "Farm", "Rain"]),
        ("Chapter", "Book", "Verse", "Poem", ["Rhyme", "Poet", "Line"]),
        ("Rudder", "Ship", "Steering wheel", "Car", ["Road", "Driver", "Engine"]),
        ("Hungry", "Eat", "Tired", "Sleep", ["Bed", "Yawn", "Night"]),
        ("Seed", "Tree", "Egg", "Bird", ["Nest", "Shell", "Feather"])],
    3: [("Prologue", "Novel", "Overture", "Opera", ["Singer", "Stage", "Finale"]),
        ("Cartographer", "Map", "Architect", "Blueprint", ["Building", "Bricks", "City"]),
        ("Meticulous", "Careless", "Frugal", "Wasteful", ["Thrifty", "Wealthy", "Careful"]),
        ("Caterpillar", "Butterfly", "Tadpole", "Frog", ["Pond", "Fish", "Egg"]),
        ("Ore", "Metal", "Crude oil", "Petrol", ["Well", "Engine", "Barrel"]),
        ("Sapling", "Tree", "Foal", "Horse", ["Stable", "Pony", "Saddle"]),
        ("Archipelago", "Island", "Constellation", "Star", ["Galaxy", "Planet", "Telescope"]),
        ("Telescope", "Distant", "Microscope", "Tiny", ["Lens", "Laboratory", "Bright"])],
}

FACTS = {
    1: [("Which is heavier: 1 kg of cotton or 1 kg of iron?", "They weigh the same",
         ["Iron", "Cotton", "It depends on the size"], "A kilogram is a kilogram, whatever it is made of."),
        ("How many days are there in a leap year?", "366", ["365", "364", "367"],
         "A leap year adds 29 February."),
        ("Which of these is a mammal?", "Dolphin", ["Shark", "Octopus", "Turtle"],
         "Dolphins breathe air and feed their young milk."),
        ("Which planet is closest to the Sun?", "Mercury", ["Venus", "Mars", "Earth"],
         "Mercury has the smallest orbit.")],
    2: [("Ice floats on water because ice is...", "Less dense than water",
         ["Colder than water", "Full of air bubbles", "Lighter in colour"],
         "Water expands when it freezes, so ice is less dense."),
        ("Facing the sunset, which direction is on your right?", "North", ["South", "East", "West"],
         "The sun sets in the west. Facing west, north is on your right."),
        ("All roses are flowers. Some flowers fade quickly. Must some roses fade quickly?", "No",
         ["Yes", "Only red roses", "Only in summer"],
         "The flowers that fade quickly might not be roses."),
        ("Sunlight takes about how long to reach Earth?", "8 minutes",
         ["8 seconds", "8 hours", "8 days"], "Light travels about 150 million km in roughly 8 minutes.")],
    3: [("A shirt costs Rs 400 after a 20% discount. What was the original price?", "Rs 500",
         ["Rs 480", "Rs 420", "Rs 520"], "400 is 80% of the price, so the price was 400 / 0.8 = 500."),
        ("Water boils at a lower temperature on a high mountain because...", "Air pressure is lower",
         ["It is colder there", "The water is cleaner", "There is less sunlight"],
         "Lower pressure lets water molecules escape more easily."),
        ("If no cats are birds and all sparrows are birds, then...", "No sparrows are cats",
         ["Some sparrows are cats", "All cats are sparrows", "Nothing can be said"],
         "Every sparrow is a bird, and no bird is a cat."),
        ("A clock shows 3:00. What is the angle between the hands?", "90°",
         ["45°", "60°", "120°"], "Each hour mark is 30°, and 3 marks apart gives 90°.")],
}


def vocabulary(difficulty=1, rng=None):
    rng = _rng(rng)
    word, meaning, wrong = rng.choice(VOCAB[difficulty])
    return _pz("crystallized", "vocabulary", difficulty, f"What does **{word}** mean?",
               _mc(meaning, wrong, rng), meaning, f"'{word}' means: {meaning.lower()}.")


def analogy(difficulty=1, rng=None):
    rng = _rng(rng)
    a, b, c, d, wrong = rng.choice(ANALOGIES[difficulty])
    return _pz("crystallized", "analogy", difficulty, f"**{a}** is to **{b}** as **{c}** is to ...?",
               _mc(d, wrong, rng), d, f"{a} relates to {b} the same way {c} relates to {d}.")


def trivia_logic(difficulty=1, rng=None):
    rng = _rng(rng)
    kind = rng.choice(["fact", "fact", "days", "clock", "convert"])
    if kind == "fact":
        q, a, wrong, why = rng.choice(FACTS[difficulty])
        return _pz("crystallized", "trivia_logic", difficulty, q, _mc(a, wrong, rng), a, why)
    if kind == "days":
        start = rng.randint(0, 6)
        n = rng.randint(3, 13) if difficulty == 1 else rng.randint(15, 60)
        ago = difficulty == 3
        ans_i = (start - n) % 7 if ago else (start + n) % 7
        q = f"Today is {DAYS[start]}. What day {'was it' if ago else 'will it be'} {n} days {'ago' if ago else 'from now'}?"
        wrong = [DAYS[(ans_i + d) % 7] for d in (1, -1, 2)]
        return _pz("crystallized", "trivia_logic", difficulty, q, _mc(DAYS[ans_i], wrong, rng), DAYS[ans_i],
                   f"{n} days is {n // 7} week(s) and {n % 7} day(s); count the extra days.")
    if kind == "clock":
        h, m = rng.randint(6, 10), rng.choice([0, 15, 20, 40, 45, 50])
        dh, dm = rng.randint(1, 3), rng.choice([10, 25, 35, 45, 55]) if difficulty > 1 else rng.choice([15, 30])
        total = h * 60 + m + dh * 60 + dm
        fmt = lambda t: f"{(t // 60) % 24}:{t % 60:02d}"
        ans = fmt(total)
        q = f"A bus leaves at {h}:{m:02d} and the trip takes {dh} h {dm} min. When does it arrive?"
        wrong = [fmt(total + 10), fmt(total - 10), fmt(total + 60)]
        return _pz("crystallized", "trivia_logic", difficulty, q, _mc(ans, wrong, rng), ans,
                   f"Add {dh} hours, then {dm} minutes.")
    if difficulty == 1:
        n = rng.randint(2, 9)
        q, ans = f"How many minutes are there in {n} hours?", n * 60
    elif difficulty == 2:
        n = rng.randint(3, 12)
        q, ans = f"How many seconds are there in {n} minutes?", n * 60
    else:
        km, mins = rng.choice([(3, 15), (5, 25), (6, 30), (4, 16), (2, 8)])
        q, ans = f"A runner covers {km} km in {mins} minutes. How many metres is that per minute?", km * 1000 // mins
    return _pz("crystallized", "trivia_logic", difficulty, q,
               _mc(ans, _num_distractors(ans, max(10, ans // 10), rng), rng), ans,
               "Convert the units step by step.")


# ------------------------------------------------------------------ WORKING MEMORY
def nback_sequence(n=1, length=None, rng=None, match_rate=0.3):
    """Return (letters, targets) where targets[i] is True if letters[i] == letters[i-n]."""
    rng = _rng(rng)
    length = length or 12 + n
    pool = list("BCDFGHJKLMNPRSTV")
    seq = []
    for i in range(length):
        if i >= n and rng.random() < match_rate:
            seq.append(seq[i - n])
        else:
            choices = [c for c in pool if i < n or c != seq[i - n]]
            seq.append(rng.choice(choices))
    targets = [i >= n and seq[i] == seq[i - n] for i in range(length)]
    return seq, targets


def score_nback(targets, responses, n):
    """responses: list of bools (True = user said 'match') for positions n..end."""
    t = targets[n:]
    hits = sum(1 for a, r in zip(t, responses) if a and r)
    misses = sum(1 for a, r in zip(t, responses) if a and not r)
    false_alarms = sum(1 for a, r in zip(t, responses) if not a and r)
    correct = sum(1 for a, r in zip(t, responses) if a == r)
    return {"hits": hits, "misses": misses, "false_alarms": false_alarms,
            "accuracy": round(100 * correct / max(1, len(t)))}


def memory_settings(difficulty):
    return {1: {"n": 1, "span": 4, "backward": False},
            2: {"n": 2, "span": 6, "backward": False},
            3: {"n": 3, "span": 5, "backward": True}}[difficulty]


def digit_sequence(length, rng=None):
    rng = _rng(rng)
    return [rng.randint(0, 9) for _ in range(length)]


def check_sequence(shown, typed, backward=False):
    target = "".join(map(str, shown[::-1] if backward else shown))
    clean = "".join(ch for ch in str(typed) if ch.isdigit())
    return clean == target, target


# ------------------------------------------------------------------ DISPATCH
GENERATORS = {"pattern": pattern, "matrix": matrix, "spatial": spatial,
              "vocabulary": vocabulary, "analogy": analogy, "trivia_logic": trivia_logic}


def _pz(pillar, skill, difficulty, prompt, options, answer, explanation, grid=None):
    p = {"pillar": pillar, "skill": skill, "difficulty": difficulty, "prompt": prompt,
         "options": [str(o) for o in options], "answer": str(answer), "explanation": explanation}
    if grid:
        p["grid"] = grid
    return p


def make_puzzle(skill, difficulty=1, rng=None):
    return GENERATORS[skill](max(1, min(3, difficulty)), rng)


def random_puzzle(pillar, difficulty=1, rng=None, skills=None):
    rng = _rng(rng)
    pool = skills or [s for s in PILLARS[pillar]["skills"] if s in GENERATORS]
    return make_puzzle(rng.choice(pool), difficulty, rng)
