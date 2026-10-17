# 🧠 MindCheck by VT — brain training meets emotional wellbeing

MindCheck is a Streamlit app that trains different sides of your thinking, helps you put feelings into
words, and then **connects the two** so you can see how your mood, sleep and stress affect your brain.

> MindCheck is a self-reflection and practice tool. It is **not** an IQ test and **not** a medical or
> psychological diagnosis.

---

## Features

### 1. Cognitive training
| Feature | What it does |
|---|---|
| **Brain Battery** | A 90-second randomized micro-game (true/false maths, same/different symbols, digit recall, tap-when-ready). Measures processing speed, working memory and reaction time, then gives a **daily readiness score** compared with your own past days. |
| **Multi-domain puzzles** | Three pillars: **Fluid** (pattern recognition, matrix reasoning, spatial rotation and direction puzzles), **Crystallized** (vocabulary, verbal analogies, trivia logic) and **Working memory** (N-back and sequence memory games). |
| **Adaptive difficulty** | 2 right in a row → harder level, 1 wrong → easier level. |
| **Neuroagility trajectory** | *My Progress* shows a 6-axis **cognitive profile radar** (last 7 days vs your earlier average), your strongest skill, most room to grow, biggest growth and a week-by-week chart. |

### 2. Emotional wellbeing
| Feature | What it does |
|---|---|
| **Micro-journaling with private emotion analysis** | Write 1–2 sentences. An on-device word list (with "not", "very" handling) finds hidden emotions like anxiety, gratitude or burnout. **Text never leaves the app.** |
| **Body check-in** | Energy, sleep quality, stress, physical tension and *"where are you holding stress?"* with a live body map and quick release tips. |
| **Emotion wheel** | An interactive 3-ring wheel (Plotly sunburst) to drill down from a broad feeling ("Bad") to a precise one ("Overwhelmed"), with a description and coping tip. |
| **Wellbeing check-in** | 16 original questions on mood, stress and sensitivity, with an agent-written summary. |

### 3. Mind-body connection
| Feature | What it does |
|---|---|
| **Cognitive-emotional insights** | Finds patterns like *"When your stress is 8–10 out of 10, your working memory puzzle scores drop by 26%. Consider a two-minute breathing exercise."* A two-proportion z-test hides patterns that could just be luck. Also links sleep → readiness, energy → accuracy and journal tone → accuracy. |
| **Adaptive puzzle mode** | High stress, heavy journal emotions, low mood, low energy or low readiness → **Calm mode**: gentle level-1 spatial, pattern and word puzzles with no timer. High readiness + low stress → **Challenge mode**. |

### 4. Help, safety and grounding
| Feature | What it does |
|---|---|
| **Panic button** | "I need a moment" in the sidebar opens the Grounding Toolbox from any page. |
| **Grounding toolbox** | Animated **box breathing**, a **5-4-3-2-1 senses game**, and a guided body reset with a 4-in / 6-out breathing circle. |
| **Distress detection** | Very high stress, a very low quick mood, distress words on the emotion wheel, or crisis phrases in the journal show support lines and grounding straight away. |
| **Progressive micro-breaks** | 3 wrong answers in a row, 90+ seconds on one puzzle, or 20 minutes of play triggers a friendly mindfulness break. |

### The AI agent
The **coach agent** runs a pipeline: read today's state → safety check → choose puzzle mode → plan next steps
→ write a message. Scores, safety and modes are **rule-based**, so the AI can never invent a number or skip a
safety step. If you add a Claude API key, the agent writes its messages with AI (it only receives numbers and
labels, never journal text). Without a key it uses built-in messages.

---

## Originality
All puzzles, word lists, questions, the emotion wheel grouping and the code were written for this project.
Most puzzles are **generated from rules** every time (thousands of combinations), so nothing is copied from
published IQ tests or clinical questionnaires.

## Project structure
All files sit at the top level (easy to upload):
- `app.py` - starts the app and routes between pages
- `*_page.py`, `home.py`, `theme.py`, `widgets.py` - the screens (UI)
- `puzzles.py`, `battery.py`, `sentiment.py`, `emotion_wheel.py`, `adaptive.py`, `insights.py`, `agent.py`,
  `quotes.py`, `content.py`, `db.py`, `demo_data.py` - the logic
- `.streamlit/config.toml` - theme colours

## Run on your computer
```bash
pip install -r requirements.txt
streamlit run app.py
```
Tip: type a nickname in the sidebar, then open **My Progress** and click **Load 4 weeks of demo data** to see
the profile radar and insights right away. Remove it with one click.


Optional AI messages: create `.streamlit/secrets.toml` with
```toml
ANTHROPIC_API_KEY = "your-key-here"
```
Never upload this file to GitHub (it is already in `.gitignore`).

## Deploy for free (Streamlit Community Cloud)
1. Upload all files to a public GitHub repo, plus `.streamlit/config.toml`.
2. Go to **share.streamlit.io** → **Create app** → choose the repo → main file `app.py` → **Deploy**.
3. (Optional) Add `ANTHROPIC_API_KEY` under the app's **Settings → Secrets**.

Note: on the free cloud the SQLite file resets when the app restarts. For permanent history, move `core/db.py`
to a hosted database such as Supabase later.

## Limits to know
- Web timings include network delay, so Brain Battery is best for comparing you with yourself.
- The emotion analysis is a simple word list. It can miss sarcasm or unusual phrasing.
- Insights need enough data: at least 8 puzzles at low stress and 8 at high stress for a skill.

## Roadmap ideas
- Login with Supabase so history is saved permanently
- A browser-side reaction-time test for millisecond accuracy
- Kannada and Hindi language support
- Weekly PDF report of your cognitive profile and mood
