"""Build about-card.svg: an animated terminal-style intro card (typewriter reveal) with the pixel dino.

usage: python3 gen_about.py OUT_DIR
"""
import os
import sys

sys.dont_write_bytecode = True
import sprites as S
import theme_colors

ACCENT = theme_colors.current().accent

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)

W = 900
CHAR_PX = 10.8                 # generous monospace advance at 18px, so the reveal always fully uncovers the text
X0 = 44                        # text left edge
FS = 18
Y0, DY = 90, 27
VAL_X = X0 + 150               # value column for the "label  value" stack lines

PROMPT = f'<tspan fill="{ACCENT}">$</tspan>'


def cmd(text, arg=None):
    m = f'{PROMPT} <tspan fill="#FFFFFF">{text}</tspan>'
    plain = f"$ {text}"
    if arg:
        m += f' <tspan fill="#86D7A3">{arg}</tspan>'
        plain += f" {arg}"
    return ("cmd", m, plain)


def out(markup, plain):
    return ("out", markup, plain)


def kv(label, value):
    """Label in green, value in the second column (explicit x so alignment never depends on font metrics)."""
    markup = (f'<tspan fill="#86D7A3">{label}</tspan>'
              f'<tspan x="{VAL_X}" fill="#C9D1D9">{value}</tspan>')
    plain = label.ljust(14) + value
    return ("out", markup, plain)


BLOCKS = [
    [cmd("whoami"),
     out('<tspan fill="#FFFFFF" font-weight="700">Rahul Lumbhani</tspan><tspan fill="#9aa0a6"> — AI/ML engineer</tspan>',
         "Rahul Lumbhani — AI/ML engineer")],
    [cmd("cat", "interests.txt"),
     out('<tspan fill="#C9D1D9">Generative AI · LLM apps · data &amp; ML platforms</tspan>',
         "Generative AI · LLM apps · data & ML platforms")],
    [cmd("ls", "./stack"),
     kv("languages/", "Python · Java · JavaScript"),
     kv("frameworks/", "React · Django · FastAPI"),
     kv("databases/", "SQL")],
    [cmd("./builds", "--list"),
     out('<tspan fill="#C9D1D9">AI co-pilots · web apps · interactive console games</tspan>',
         "AI co-pilots · web apps · interactive console games")],
]

# ---- schedule: type each command, then reveal its output lines, pause, next block
T = 0.6
schedule = []          # (kind, markup, plain, start, per_char)
for block in BLOCKS:
    for kind, markup, plain in block:
        per = 0.07 if kind == "cmd" else 0.02
        if kind == "out":
            T += 0.25 if schedule and schedule[-1][0] == "cmd" else 0.0
        schedule.append((kind, markup, plain, T, per))
        T += len(plain) * per + (0.15 if kind == "out" else 0.0)
    T += 0.55
LAST_PROMPT_AT = T
HOLD = 4.6
FADE_OUT_AT, FADE_END = LAST_PROMPT_AT + HOLD, LAST_PROMPT_AT + HOLD + 1.0
LOOP = round(FADE_END + 0.6, 1)

rows, covers, styles = [], [], []
for i, (kind, markup, plain, start, per) in enumerate(schedule):
    y = Y0 + i * DY
    n = len(plain)
    end = start + n * per
    travel = round(n * CHAR_PX + 10)
    rows.append(f'<text class="mono" x="{X0}" y="{y}" font-size="{FS}">{markup}</text>')
    covers.append(f'<rect class="cv c{i}" x="{X0 - 4}" y="{y - 20}" width="760" height="{DY}" fill="#161616"/>')
    p0, p1 = start / LOOP * 100, end / LOOP * 100
    styles.append(
        f"    .c{i}{{animation:k{i} {LOOP:g}s linear infinite}}\n"
        f"    @keyframes k{i}{{0%,{p0:.3f}%{{transform:translateX(0);animation-timing-function:steps({n},end)}}"
        f"{p1:.3f}%,100%{{transform:translateX({travel}px)}}}}"
    )

last_y = Y0 + len(schedule) * DY
H = last_y + 34
rows.append(
    f'<g class="last"><text class="mono" x="{X0}" y="{last_y}" font-size="{FS}"><tspan fill="{ACCENT}">$</tspan></text>'
    f'<rect class="blink" x="{X0 + 24}" y="{last_y - 16}" width="10" height="20" fill="{ACCENT}"/></g>'
)
p_last = LAST_PROMPT_AT / LOOP * 100
styles.append(
    f"    .last{{animation:last {LOOP:g}s linear infinite}}\n"
    f"    @keyframes last{{0%,{p_last - 0.01:.3f}%{{opacity:0}}{p_last:.3f}%,100%{{opacity:1}}}}"
)
styles.append(
    "    .blink{animation:blink 1.05s steps(1,end) infinite}\n"
    "    @keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
)
fo, fe = FADE_OUT_AT / LOOP * 100, FADE_END / LOOP * 100
styles.append(
    f"    .term{{animation:fade {LOOP:g}s linear infinite}}\n"
    f"    @keyframes fade{{0%,{fo:.3f}%{{opacity:1}}{fe:.3f}%,100%{{opacity:0}}}}"
)


def shapes(rows_, u=3):
    paths = S.path_by_colour(rows_, u)
    order = ["O", "D", "Y", "L", "B", "M", "T", "K", "W", "g", "G", "h", "S", "P", "X"]
    return "".join(f'<path fill="{S.PAL[c]}" d="{paths[c]}"/>' for c in order if c in paths)


dino_h = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U
GROUND_Y = H - 40
dino_x_right = 862                       # flipped: the dino faces left, towards the text and the cactus
body = shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)
legsA = shapes(S.pad(S.ART["legsA"], S.DINO_W), S.DINO_U)
legsB = shapes(S.pad(S.ART["legsB"], S.DINO_W), S.DINO_U)
body_h = len(S.ART["dinoBody"]) * S.DINO_U
cactus_h = len(S.ART["small"]) * 3
sag_h = len(S.ART["saguaro"]) * 3

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">About Rahul Lumbhani</title>
  <desc id="d">A terminal window types out: whoami, Rahul Lumbhani, AI/ML engineer; interests, generative AI, LLM apps and data and ML platforms; stack, languages Python, Java and JavaScript, frameworks React, Django and FastAPI, databases SQL; builds, AI co-pilots, web apps and interactive console games. A pixel dinosaur stands beside a cactus.</desc>
  <style>
    .mono{{font-family:'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace}}
{chr(10).join(styles)}
    .bob{{animation:bob 2.4s ease-in-out infinite}}
    @keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
    .legA{{animation:legA .5s steps(1,end) infinite}}
    .legB{{animation:legB .5s steps(1,end) infinite}}
    @keyframes legA{{0%{{opacity:1}}50%{{opacity:0}}100%{{opacity:1}}}}
    @keyframes legB{{0%{{opacity:0}}50%{{opacity:1}}100%{{opacity:0}}}}
    @media (prefers-reduced-motion:reduce){{.cv{{display:none}}.term,.last,.blink,.bob,.legA,.legB{{animation:none}}.legB{{opacity:0}}}}
  </style>
  <defs>
    <radialGradient id="halo" cx="0.88" cy="0.95" r="0.45">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.10"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{ACCENT}" stop-opacity="0.85"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
  </defs>

  <!-- window -->
  <rect width="{W}" height="{H}" rx="14" fill="#161616"/>
  <path d="M0 14a14 14 0 0 1 14-14h{W - 28}a14 14 0 0 1 14 14v26H0z" fill="#1d1d1d"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="#2a2a2a"/>
  <rect x="200" y="0" width="{W - 400}" height="2" fill="url(#edge)"/>
  <circle cx="26" cy="20" r="6" fill="#ff5f56"/><circle cx="48" cy="20" r="6" fill="#ffbd2e"/><circle cx="70" cy="20" r="6" fill="#27c93f"/>
  <text class="mono" x="{W // 2}" y="25" text-anchor="middle" font-size="13" fill="#7d8590" letter-spacing="1">rahul@github: ~/about</text>
  <line x1="0" y1="40" x2="{W}" y2="40" stroke="#2a2a2a"/>

  <!-- terminal text, revealed line by line by sliding a background-coloured cover to the right -->
  <g class="term">
    {chr(10).join("    " + r for r in rows)}
    {chr(10).join("    " + c for c in covers)}
  </g>

  <rect width="{W}" height="{H}" rx="14" fill="url(#halo)"/>

  <!-- dino + cactus, facing each other -->
  <line x1="640" y1="{GROUND_Y + 1}" x2="{W - 16}" y2="{GROUND_Y + 1}" stroke="#3a3a3a" stroke-width="2"/>
  <line x1="650" y1="{GROUND_Y + 11}" x2="{W - 30}" y2="{GROUND_Y + 11}" stroke="#2a2a2a" stroke-width="2" stroke-dasharray="14 36 6 50 4 60"/>
  <g transform="translate(676,{GROUND_Y - sag_h})">{shapes(S.ART["saguaro"])}</g>
  <g transform="translate(730,{GROUND_Y - cactus_h})">{shapes(S.ART["small"])}</g>
  <g transform="translate({dino_x_right},{GROUND_Y - dino_h}) scale(-1,1)">
    <g class="bob">
      <g>{body}</g>
      <g transform="translate(0,{body_h})">
        <g class="legA">{legsA}</g>
        <g class="legB">{legsB}</g>
      </g>
    </g>
  </g>
</svg>
'''
with open(os.path.join(out_dir, "about-card.svg"), "w") as f:
    f.write(svg)
print(f"about-card.svg {len(svg)} bytes, {len(schedule)} text rows, H={H}, loop={LOOP}s, last prompt at {LAST_PROMPT_AT:.1f}s", file=sys.stderr)
# rows that could collide with the dino/cactus area (x >= 640, y >= GROUND_Y - 78)
for i, (_, _, plain, _, _) in enumerate(schedule):
    y = Y0 + i * DY
    right = X0 + len(plain) * CHAR_PX
    if right > 630 and y > GROUND_Y - 80:
        print(f"WARNING: row {i} may overlap the dino area: {plain!r} ends x~{right:.0f}", file=sys.stderr)
