"""Reusable UI pieces: support box, breathing animation, timers, body map."""
import html
import json

import streamlit as st
import streamlit.components.v1 as components

from content import SUPPORT_LINES

FONT = "<link href='https://fonts.googleapis.com/css2?family=Nunito:wght@800;900&family=Nunito+Sans:wght@400;700&display=swap' rel='stylesheet'>"


def hero(eyebrow, title, sub=""):
    st.markdown(f'<div class="mc-eyebrow">{html.escape(eyebrow)}</div>'
                f'<div class="mc-hero">{html.escape(title)}</div>'
                f'<div class="mc-sub">{html.escape(sub)}</div>', unsafe_allow_html=True)
    st.write("")


def card(title, body):
    st.markdown(f'<div class="mc-card"><h4>{html.escape(title)}</h4><div>{body}</div></div>',
                unsafe_allow_html=True)


def chips(items, negative=()):
    out = "".join(f'<span class="mc-chip{" neg" if i in negative else ""}">{html.escape(i)}</span>'
                  for i in items)
    st.markdown(out, unsafe_allow_html=True)


def support_box(compact=False):
    lines = "\n".join(f"- **{name}:** {num}" for name, num in SUPPORT_LINES)
    msg = ("**You don't have to go through this alone.** Please reach out now:\n\n" + lines +
           "\n\nYou can also talk to a family member, friend, teacher or doctor you trust.")
    if compact:
        st.info(msg)
    else:
        st.error(msg)


def need_nickname():
    st.info("Add a **nickname** in the sidebar so MindCheck can save your results and track your progress.")


def box_breathing(side_seconds=4, cycles=4, height=380, key="box"):
    """Animated box breathing: in - hold - out - hold."""
    phases = json.dumps(["Breathe in", "Hold", "Breathe out", "Hold"])
    components.html(f"""
{FONT}
<div style="font-family:'Nunito Sans',sans-serif;display:flex;flex-direction:column;align-items:center;gap:14px;padding:10px">
  <div style="position:relative;width:220px;height:220px">
    <div style="position:absolute;inset:0;border:4px solid #BFE0D9;border-radius:18px"></div>
    <div id="dot" style="position:absolute;width:26px;height:26px;border-radius:50%;background:#0F766E;
         left:-13px;top:207px;box-shadow:0 0 0 8px rgba(15,118,110,.18)"></div>
    <div id="fill" style="position:absolute;left:30px;right:30px;bottom:30px;top:30px;border-radius:12px;
         background:#D9EEEA;transform:scale(.4);transition:transform {side_seconds}s linear"></div>
    <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center">
      <div id="phase" style="font-family:Nunito;font-weight:900;font-size:26px;color:#12302E">Ready</div>
      <div id="count" style="font-family:Nunito;font-weight:900;font-size:44px;color:#0F766E">&nbsp;</div>
    </div>
  </div>
  <button id="go" style="border:0;border-radius:999px;background:#0F766E;color:#fff;font-weight:700;
     font-size:16px;padding:12px 26px;cursor:pointer;min-height:44px">Start box breathing</button>
  <div id="cyc" style="color:#4A6461;font-size:14px">{cycles} rounds · {side_seconds} seconds each side</div>
</div>
<script>
const P={phases}, S={side_seconds}, C={cycles};
const dot=document.getElementById('dot'), fill=document.getElementById('fill');
const ph=document.getElementById('phase'), ct=document.getElementById('count'), cyc=document.getElementById('cyc');
const corners=[[-13,-13],[207,-13],[207,207],[-13,207]]; // top-left, top-right, bottom-right, bottom-left
let timer=null;
function place(i,secs){{dot.style.transition='left '+secs+'s linear, top '+secs+'s linear';
  dot.style.left=corners[i][0]+'px'; dot.style.top=corners[i][1]+'px';}}
document.getElementById('go').onclick=()=>{{
  if(timer) clearInterval(timer);
  let step=0, sec=S, round=1; place(3,0);
  const startPhase=()=>{{const p=step%4; ph.textContent=P[p]; place(p,S);
     fill.style.transform = p===0? 'scale(1)' : p===2 ? 'scale(.4)' : fill.style.transform;
     cyc.textContent='Round '+round+' of '+C;}};
  startPhase(); ct.textContent=sec;
  timer=setInterval(()=>{{sec--; if(sec<=0){{step++; if(step%4===0) round++;
      if(round>C){{clearInterval(timer); ph.textContent='Well done'; ct.innerHTML='&#10003;';
        cyc.textContent='Notice how your body feels now.'; return;}}
      sec=S; startPhase();}} ct.textContent=sec; }},1000);
}};
</script>""", height=height)


def calm_breath(in_s=4, out_s=6, rounds=6, height=330):
    """A softer 4-in / 6-out breathing circle."""
    components.html(f"""
{FONT}
<div style="font-family:'Nunito Sans',sans-serif;display:flex;flex-direction:column;align-items:center;gap:14px;padding:10px">
  <div id="c" style="width:200px;height:200px;border-radius:50%;background:#D9EEEA;display:flex;align-items:center;
      justify-content:center;transform:scale(.6);border:4px solid #0F766E">
    <div id="t" style="font-family:Nunito;font-weight:900;font-size:22px;color:#0B4F4A">Ready</div></div>
  <button id="b" style="border:0;border-radius:999px;background:#0F766E;color:#fff;font-weight:700;font-size:16px;
      padding:12px 26px;cursor:pointer;min-height:44px">Start</button>
</div>
<script>
const c=document.getElementById('c'), t=document.getElementById('t');
document.getElementById('b').onclick=()=>{{let r=0;
  const cycle=()=>{{ if(r>={rounds}){{t.textContent='Done';return;}} r++;
    t.textContent='In'; c.style.transition='transform {in_s}s ease-in-out'; c.style.transform='scale(1)';
    setTimeout(()=>{{t.textContent='Out'; c.style.transition='transform {out_s}s ease-in-out'; c.style.transform='scale(.6)';
      setTimeout(cycle,{out_s}*1000);}},{in_s}*1000);}};
  cycle();}};
</script>""", height=height)


def puzzle_timer(limit_s=90, key=0):
    """Shows seconds on this puzzle; after limit shows a friendly nudge (runs in the browser)."""
    components.html(f"""
{FONT}
<div id="w{key}" style="font-family:'Nunito Sans',sans-serif;font-size:14px;color:#4A6461;padding:4px 2px">
  ⏱ <span id="s">0</span>s on this puzzle</div>
<script>
let s=0; const el=document.getElementById('s'), w=document.getElementById('w{key}');
setInterval(()=>{{ s++; el.textContent=s;
  if(s==={limit_s}) {{ w.innerHTML='<div style="background:#FBE4DC;color:#5C2414;border-radius:12px;padding:10px 14px;font-size:15px">'+
   '🌿 You have been on this one for a while. Try a slow breath, look away from the screen for a moment, or skip to the next puzzle.</div>'; }}
}},1000);
</script>""", height=70)


def countdown(seconds_left, height=60):
    components.html(f"""
{FONT}
<div style="font-family:Nunito;font-weight:900;font-size:22px;color:#0F766E">
  <span id="t">{int(seconds_left)}</span>s left</div>
<script>let t={int(seconds_left)};const e=document.getElementById('t');
setInterval(()=>{{ if(t>0){{t--;e.textContent=t;}} if(t===0) e.parentElement.innerHTML='Time! Answer this last one.'; }},1000);</script>
""", height=height)


def flash_digits(digits, show_ms=3000, key=0, height=150):
    """Show digits briefly, then hide them (for memory tasks)."""
    text = " ".join(str(d) for d in digits)
    components.html(f"""
{FONT}
<div id="d{key}" style="font-family:Nunito;font-weight:900;font-size:52px;letter-spacing:10px;text-align:center;
  background:#FFFFFF;border-radius:20px;padding:26px;color:#12302E">{text}</div>
<script>setTimeout(()=>{{const d=document.getElementById('d{key}');
  d.innerHTML='<span style="color:#4A6461;font-size:22px;letter-spacing:0">Now type what you saw</span>';}},{show_ms});</script>
""", height=height)


BODY_AREAS = {
    "Forehead": (100, 30, 22, 10), "Jaw": (100, 62, 18, 8), "Neck": (100, 84, 12, 10),
    "Shoulders": (100, 104, 52, 10), "Chest": (100, 140, 30, 20), "Stomach": (100, 190, 26, 20),
    "Back": (100, 165, 40, 12), "Hands": (100, 230, 82, 10), "Legs": (100, 300, 26, 40),
}


def body_map(selected):
    """Simple body silhouette with highlighted stress areas."""
    shapes = []
    for area, (cx, cy, rx, ry) in BODY_AREAS.items():
        on = area in selected
        if area == "Hands":
            for x in (cx - rx, cx + rx):
                shapes.append(f'<ellipse cx="{x}" cy="{cy}" rx="11" ry="11" fill="{"#D9725E" if on else "none"}" '
                              f'opacity="{0.85 if on else 0}"/>')
            continue
        if area == "Legs":
            for x in (cx - 18, cx + 18):
                shapes.append(f'<ellipse cx="{x}" cy="{cy}" rx="14" ry="{ry}" fill="#D9725E" opacity="{0.8 if on else 0}"/>')
            continue
        shapes.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="#D9725E" opacity="{0.8 if on else 0}"/>')
    svg = f"""
<svg viewBox="0 0 200 360" width="190" height="340" role="img" aria-label="Body map showing where you hold stress">
  <g fill="#E3F1EE" stroke="#0F766E" stroke-width="2">
    <circle cx="100" cy="44" r="30"/>
    <rect x="90" y="72" width="20" height="22" rx="6"/>
    <path d="M52 100 Q100 88 148 100 L156 210 Q100 222 44 210 Z"/>
    <path d="M52 102 L20 228 L32 232 L62 130 Z"/><path d="M148 102 L180 228 L168 232 L138 130 Z"/>
    <path d="M66 212 L72 350 L96 350 L100 230 L104 350 L128 350 L134 212 Z"/>
  </g>
  {''.join(shapes)}
</svg>"""
    st.markdown(svg, unsafe_allow_html=True)
