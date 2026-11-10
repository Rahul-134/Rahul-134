"""Build about-card.svg in the Playful style: a cream card with a console top bar, a dark terminal screen that
types out the intro (typewriter reveal), and a little sky window with the sun, cacti and the cartoon T-rex.

usage: python3 gen_about.py OUT_DIR
"""
import os
import sys

sys.dont_write_bytecode = True
import sprites as S
import theme_colors
import banner

ACCENT = theme_colors.current().accent

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)

W = 900
CHAR_PX = 10.8                 # generous monospace advance at 18px, so the reveal always fully uncovers the text
X0 = 44                        # text left edge
FS = 18
Y0, DY = 104, 27
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

SCREEN = "#1E1A17"   # the terminal screen (warm near-black, like the game console's bezel)
rows, covers, styles = [], [], []
for i, (kind, markup, plain, start, per) in enumerate(schedule):
    y = Y0 + i * DY
    n = len(plain)
    end = start + n * per
    travel = round(n * CHAR_PX + 10)
    rows.append(f'<text class="mono" x="{X0}" y="{y}" font-size="{FS}">{markup}</text>')
    covers.append(f'<rect class="cv c{i}" x="{X0 - 4}" y="{y - 20}" width="760" height="{DY}" fill="{SCREEN}"/>')
    p0, p1 = start / LOOP * 100, end / LOOP * 100
    styles.append(
        f"    .c{i}{{animation:k{i} {LOOP:g}s linear infinite}}\n"
        f"    @keyframes k{i}{{0%,{p0:.3f}%{{transform:translateX(0);animation-timing-function:steps({n},end)}}"
        f"{p1:.3f}%,100%{{transform:translateX({travel}px)}}}}"
    )

last_y = Y0 + len(schedule) * DY
H = last_y + 48
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


def shapes(rows_, u=S.OBJ_U):
    paths = S.path_by_colour(rows_, u)
    order = ["O", "D", "Y", "L", "B", "E", "V", "M", "T", "K", "W", "g", "G", "h", "S", "P", "Q", "X", "Z", "N", "R", "I"]
    return "".join(f'<path fill="{S.PAL[c]}" d="{paths[c]}"/>' for c in order if c in paths)


dino_h = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U
INK = banner.INK
SX0, SX1 = 644, W - 26                  # the sky window on the right
SY0, SY1 = 64, H - 24
GROUND_Y = SY1 - 40                     # sand below this line
TX0, TX1 = 22, 628                      # the terminal screen on the left
dino_x_right = SX1 - 22                 # flipped: the dino faces left, towards the text and the cacti
body = shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)
legsA = shapes(S.pad(S.ART["legsA"], S.DINO_W), S.DINO_U)
legsB = shapes(S.pad(S.ART["legsB"], S.DINO_W), S.DINO_U)
body_h = len(S.ART["dinoBody"]) * S.DINO_U
cactus_h = len(S.ART["small"]) * S.OBJ_U
sag_h = len(S.ART["saguaro"]) * S.OBJ_U

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">About Rahul Lumbhani</title>
  <desc id="d">A terminal window types out: whoami, Rahul Lumbhani, AI/ML engineer; interests, generative AI, LLM apps and data and ML platforms; stack, languages Python, Java and JavaScript, frameworks React, Django and FastAPI, databases SQL; builds, AI co-pilots, web apps and interactive console games. A cartoon T-rex stands beside two cacti in a little desert window.</desc>
  <style>
    {banner.font_face()}
    .mono{{font-family:'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace}}
    .round{{font-family:'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif}}
{chr(10).join(styles)}
    .bob{{animation:bob 2.4s ease-in-out infinite}}
    @keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
    .legA{{animation:legA .5s steps(1,end) infinite}}
    .legB{{animation:legB .5s steps(1,end) infinite}}
    @keyframes legA{{0%{{opacity:1}}50%{{opacity:0}}100%{{opacity:1}}}}
    @keyframes legB{{0%{{opacity:0}}50%{{opacity:1}}100%{{opacity:0}}}}
    .cl{{animation:drift 40s linear infinite}}
    @keyframes drift{{from{{transform:translateX({SX1 + 20}px)}}to{{transform:translateX({SX0 - 110}px)}}}}
    .rays{{animation:spin 60s linear infinite}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    @media (prefers-reduced-motion:reduce){{.cv{{display:none}}.term,.last,.blink,.bob,.legA,.legB,.cl,.rays{{animation:none}}.legB{{opacity:0}}.cl{{transform:translateX({SX0 + 20}px)}}}}
  </style>
  <defs>
    <clipPath id="scr"><rect x="{TX0}" y="{SY0}" width="{TX1 - TX0}" height="{SY1 - SY0}" rx="16"/></clipPath>
    <clipPath id="sky"><rect x="{SX0}" y="{SY0}" width="{SX1 - SX0}" height="{SY1 - SY0}" rx="16"/></clipPath>
    {banner.ground_tile(40)}
  </defs>

  <!-- the card: cream, dark outline, offset shadow, console top bar -->
  <rect x="11" y="11" width="{W - 14}" height="{H - 14}" rx="24" fill="{INK}"/>
  <rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="24" fill="#FFFDF7" stroke="{INK}" stroke-width="4"/>
  <circle cx="34" cy="33" r="7.5" fill="#FF6B4A" stroke="{INK}" stroke-width="2.5"/>
  <circle cx="58" cy="33" r="7.5" fill="#FFC83D" stroke="{INK}" stroke-width="2.5"/>
  <circle cx="82" cy="33" r="7.5" fill="#BFF0CF" stroke="{INK}" stroke-width="2.5"/>
  <text class="round" x="{(TX0 + TX1) / 2:.0f}" y="40" text-anchor="middle" font-size="19" font-weight="800" fill="{INK}">rahul@github: ~/about</text>
  <rect x="{SX1 - 120}" y="18" width="116" height="30" rx="15" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>
  <text class="round" x="{SX1 - 62}" y="39" text-anchor="middle" font-size="15" font-weight="800" fill="{INK}" letter-spacing="1.5">ABOUT ME</text>

  <!-- terminal screen; lines are revealed by sliding a screen-coloured cover to the right -->
  <rect x="{TX0}" y="{SY0}" width="{TX1 - TX0}" height="{SY1 - SY0}" rx="16" fill="{SCREEN}"/>
  <g clip-path="url(#scr)">
    <g class="term">
    {chr(10).join("    " + r for r in rows)}
    {chr(10).join("    " + c for c in covers)}
    </g>
  </g>
  <rect x="{TX0}" y="{SY0}" width="{TX1 - TX0}" height="{SY1 - SY0}" rx="16" fill="none" stroke="{INK}" stroke-width="3"/>

  <!-- sky window: sun, a drifting cloud, sand, cacti and the T-rex -->
  <rect x="{SX0}" y="{SY0}" width="{SX1 - SX0}" height="{SY1 - SY0}" rx="16" fill="{banner.SKY}"/>
  <g clip-path="url(#sky)">
    {banner.sun(SX1 - 46, SY0 + 46, 0.82)}
    <g class="cl">{banner.cloud(0, SY0 + 70, 0.62)}</g>
    <g transform="translate({SX0},{GROUND_Y - 10})"><rect width="{SX1 - SX0}" height="50" fill="url(#sand)"/></g>
    <g transform="translate({SX0 + 22},{GROUND_Y - sag_h})">{shapes(S.ART["saguaro"])}</g>
    <g transform="translate({SX0 + 72},{GROUND_Y - cactus_h})">{shapes(S.ART["small"])}</g>
    <g transform="translate({dino_x_right},{GROUND_Y - dino_h}) scale(-1,1)">
      <g class="bob">
        <g>{body}</g>
        <g transform="translate(0,{body_h})">
          <g class="legA">{legsA}</g>
          <g class="legB">{legsB}</g>
        </g>
      </g>
    </g>
  </g>
  <rect x="{SX0}" y="{SY0}" width="{SX1 - SX0}" height="{SY1 - SY0}" rx="16" fill="none" stroke="{INK}" stroke-width="3"/>
</svg>
'''
with open(os.path.join(out_dir, "about-card.svg"), "w") as f:
    f.write(svg)
print(f"about-card.svg {len(svg)} bytes, {len(schedule)} text rows, H={H}, loop={LOOP}s, last prompt at {LAST_PROMPT_AT:.1f}s", file=sys.stderr)
# rows that would run past the right edge of the terminal screen
for i, (_, _, plain, _, _) in enumerate(schedule):
    y = Y0 + i * DY
    right = X0 + len(plain) * CHAR_PX
    if right > TX1 - 10:
        print(f"WARNING: row {i} may run past the terminal screen: {plain!r} ends x~{right:.0f}", file=sys.stderr)
