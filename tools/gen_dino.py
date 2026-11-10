"""Build dino-banner.svg and dino/index.html from sprites.py + index.template.html (themed).

usage: python3 gen.py OUT_DIR [--test-hook]
"""
import json
import os
import sys

sys.dont_write_bytecode = True
import sprites as S
import theme_colors

T = theme_colors.current()
ACCENT = T.accent

out_dir = sys.argv[1]
test_hook = "--test-hook" in sys.argv
os.makedirs(os.path.join(out_dir, "dino"), exist_ok=True)

# ------------------------------------------------------------------ SVG banner
U = 3
GROUND = 235
CYCLE = 6.0
START_X, END_X = 1050, -120
SPEED = (START_X - END_X) / CYCLE   # px/s: derived from the actual cactus travel so timing can never drift


def shapes(rows, u=U, cls=None):
    paths = S.path_by_colour(rows, u)
    order = ["D", "Y", "L", "K", "W", "g", "G", "h", "S", "P", "X"]
    items = []
    for c in order:
        if c in paths:
            items.append(f'<path fill="{S.PAL[c]}" d="{paths[c]}"/>')
    return "".join(items)


dino_rows = S.pad(S.ART["dinoBody"], 23)
dino_w = 24 * U
body_h = len(S.ART["dinoBody"]) * U
dino_h = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * U
dino_y = GROUND - dino_h
dino_x = 100

legsA = shapes(S.pad(S.ART["legsA"], 24))
legsB = shapes(S.pad(S.ART["legsB"], 24))
body = shapes(S.pad(S.ART["dinoBody"], 24))


def sprite_h(name):
    return len(S.ART[name]) * U


def sprite_w(name):
    return S.width(S.ART[name]) * U


# cactus A = saguaro; cactus B = small cactus + barrel cactus side by side
sag_h, sag_w = sprite_h("saguaro"), sprite_w("saguaro")
small_h, small_w = sprite_h("small"), sprite_w("small")
bar_h, bar_w = sprite_h("barrel"), sprite_w("barrel")
GAP = 6
B_w = small_w + GAP + bar_w

cactusA = f'<g transform="translate(0,{GROUND - sag_h})">{shapes(S.ART["saguaro"])}</g>'
cactusB = (
    f'<g transform="translate(0,{GROUND - small_h})">{shapes(S.ART["small"])}</g>'
    f'<g transform="translate({small_w + GAP},{GROUND - bar_h})">{shapes(S.ART["barrel"])}</g>'
)

# Jump timing: the dino body spans x in [DX0, DX1]; an obstacle of width w whose left edge is at x
# overlaps while  DX0 - w < x < DX1.  Obstacles move left at SPEED from START_X.
DX0, DX1 = dino_x + 4, dino_x + 68


def window(w, delay):
    t_in = (START_X - DX1) / SPEED + delay
    t_out = (START_X - (DX0 - w)) / SPEED + delay
    return t_in % CYCLE, t_out - t_in


# Jump: a smooth parabola, DUR seconds long, apex APEX_H px. The take-off is placed so the apex is centred
# on the moment the obstacle passes the middle of the dino (slightly early, like a real player), so the dino
# leaves the ground well before the cactus arrives and lands well after it has passed.
DUR, APEX_H, EARLY = 1.2, 80, 0.04
SAMPLES = 16


def jump_height(dt):
    u = (dt - DUR / 2) / (DUR / 2)
    return max(0.0, APEX_H * (1 - u * u))


tA, durA = window(sag_w, 0.0)
tB, durB = window(B_w, -3.0)
# the dino must stay above the obstacle for its whole window
for name, dur, oh in (("A", durA, sag_h), ("B", durB, small_h)):
    edge = jump_height(DUR / 2 - dur / 2 - EARLY)
    assert edge > oh + 6, (name, edge, oh)
starts = sorted([tA + durA / 2 - DUR / 2 - EARLY, tB + durB / 2 - DUR / 2 - EARLY])
assert starts[1] - starts[0] > DUR + 0.2, starts


def pct(t):
    return f"{t / CYCLE * 100:.2f}%"


events = []
for st in starts:
    for i in range(SAMPLES + 1):
        dt = DUR * i / SAMPLES
        events.append((st + dt, round(jump_height(dt))))
events.sort()
kf = ["0%{transform:translateY(0)}"]
for t, h in events:
    kf.append(f"{pct(t)}{{transform:translateY(-{h}px)}}")
kf.append("100%{transform:translateY(0)}")
jump_kf = "".join(kf)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 290" width="1000" height="290" role="img" aria-labelledby="t d">
  <title id="t">Hey I am Rahul Lumbhani — AI/ML Engineer · GenAI Enthusiast</title>
  <desc id="d">An animated pixel dinosaur runs along the ground and jumps over cacti. Click to play the full game.</desc>
  <style>
    .mono{{font-family:'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace}}
    .jump{{animation:jump {CYCLE:g}s linear infinite}}
    .cactus{{animation:run {CYCLE:g}s linear infinite}}
    .cactusB{{animation:run {CYCLE:g}s linear infinite;animation-delay:-3s}}
    .legA{{animation:legA .24s steps(1,end) infinite}}
    .legB{{animation:legB .24s steps(1,end) infinite}}
    .ground{{animation:scroll {200/SPEED:.3f}s linear infinite}}
    .cloud1{{animation:cloud 34s linear infinite}}
    .cloud2{{animation:cloud 34s linear infinite;animation-delay:-17s}}
    @keyframes jump{{{jump_kf}}}
    @keyframes run{{from{{transform:translateX({START_X}px)}}to{{transform:translateX({END_X}px)}}}}
    @keyframes legA{{0%{{opacity:1}}50%{{opacity:0}}100%{{opacity:1}}}}
    @keyframes legB{{0%{{opacity:0}}50%{{opacity:1}}100%{{opacity:0}}}}
    @keyframes scroll{{from{{transform:translateX(0)}}to{{transform:translateX(-200px)}}}}
    @keyframes cloud{{from{{transform:translateX(1100px)}}to{{transform:translateX(-160px)}}}}
    @keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
    .cursor{{animation:blink 1.1s steps(1,end) infinite}}
    @media (prefers-reduced-motion:reduce){{.jump,.cactus,.cactusB,.legA,.legB,.ground,.cloud1,.cloud2,.cursor{{animation:none}}.cactus{{transform:translateX(640px)}}.cactusB{{transform:translateX(860px)}}.cloud1{{transform:translateX(220px)}}.cloud2{{transform:translateX(780px)}}.legB{{opacity:0}}}}
  </style>
  <defs>
    <linearGradient id="glow" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{ACCENT}" stop-opacity="0.9"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="halo" cx="0.5" cy="0.35" r="0.6">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.10"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1000" height="290" rx="16" fill="#161616"/>
  <rect width="1000" height="290" rx="16" fill="url(#halo)"/>
  <rect x="0.5" y="0.5" width="999" height="289" rx="15.5" fill="none" stroke="#2a2a2a"/>
  <rect x="300" y="0" width="400" height="2" fill="url(#glow)"/>

  <!-- clouds -->
  <g fill="#262626">
    <g class="cloud1"><g transform="translate(0,52)"><rect x="12" y="0" width="52" height="8" rx="4"/><rect x="0" y="8" width="84" height="8" rx="4"/><rect x="24" y="-8" width="28" height="8" rx="4"/></g></g>
    <g class="cloud2"><g transform="translate(0,186)"><rect x="12" y="0" width="52" height="8" rx="4"/><rect x="0" y="8" width="84" height="8" rx="4"/><rect x="24" y="-8" width="28" height="8" rx="4"/></g></g>
  </g>

  <!-- hi score -->
  <text class="mono" x="968" y="40" text-anchor="end" font-size="16" fill="#6b6b6b" letter-spacing="2">HI 00134</text>

  <!-- title -->
  <text class="mono" x="500" y="104" text-anchor="middle" font-size="42" font-weight="700" fill="#FFFFFF">Hey I am Rahul Lumbhani</text>
  <text class="mono" x="500" y="150" text-anchor="middle" font-size="22" fill="{ACCENT}" letter-spacing="3">AI/ML Engineer · GenAI Enthusiast<tspan class="cursor">_</tspan></text>

  <!-- ground -->
  <line x1="0" y1="{GROUND + 1}" x2="1000" y2="{GROUND + 1}" stroke="#3a3a3a" stroke-width="2"/>
  <line class="ground" x1="0" y1="{GROUND + 12}" x2="1400" y2="{GROUND + 12}" stroke="#2f2f2f" stroke-width="2" stroke-dasharray="20 40 8 62 4 66"/>
  <line class="ground" x1="-70" y1="{GROUND + 22}" x2="1330" y2="{GROUND + 22}" stroke="#262626" stroke-width="2" stroke-dasharray="6 54 14 40 4 82"/>

  <!-- cacti -->
  <g class="cactus">{cactusA}</g>
  <g class="cactusB">{cactusB}</g>

  <!-- dino -->
  <g transform="translate({dino_x},{dino_y})">
    <g class="jump">
      <g>{body}</g>
      <g transform="translate(0,{body_h})">
        <g class="legA">{legsA}</g>
        <g class="legB">{legsB}</g>
      </g>
    </g>
  </g>

  <text class="mono" x="500" y="276" text-anchor="middle" font-size="12" fill="#6b6b6b" letter-spacing="2">CLICK TO PLAY  ·  SPACE / TAP TO JUMP</text>
</svg>
'''
with open(os.path.join(out_dir, "dino-banner.svg"), "w") as f:
    f.write(svg)

# ------------------------------------------------------------------ game page
js = "  var PAL = " + json.dumps(S.PAL) + ";\n  var ART = {\n"
for k, rows in S.ART.items():
    js += f"    {k}: " + json.dumps(rows) + ",\n"
js += "  };"

here = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(here, "index.template.html")).read()
assert "/*__SPRITES__*/" in tpl
def art_svg(rows, u=3, pal=None):
    """A standalone inline <svg> of pixel art, used for the stickers and the logo on the game page."""
    rows = S.pad(rows)
    paths = S.path_by_colour(rows, u)
    pal = dict(S.PAL, **(pal or {}))
    order = ["D", "Y", "L", "K", "W", "g", "G", "h", "S", "P", "X"]
    body = "".join(f'<path fill="{pal[c]}" d="{paths[c]}"/>' for c in order if c in paths)
    return (f'<svg viewBox="0 0 {len(rows[0]) * u} {len(rows) * u}" aria-hidden="true" focusable="false" '
            f'shape-rendering="crispEdges">{body}</svg>')


ART_HTML = {
    "{{ART_DINO}}": art_svg(S.pad(S.ART["dinoBody"], 24) + S.pad(S.ART["legsA"], 24)),
    "{{ART_SAGUARO}}": art_svg(S.ART["saguaro"]),
    "{{ART_SMALL}}": art_svg(S.ART["small"]),
    "{{ART_BIRD}}": art_svg(S.ART["birdUp"], pal={"X": "#5B6B80"}),
}

html = tpl.replace("/*__SPRITES__*/", js).replace("{{ACCENT}}", T.accent).replace("{{ACCENT_RGB}}", T.rgb)
for key, markup in ART_HTML.items():
    html = html.replace(key, markup)
hook = (
    "  window.__dino = { get: function () { return { state: state, score: score, speed: speed, obstacles: obstacles.length,"
    " dinoY: dino.y, dinoX: dino.x, onGround: dino.onGround, ducking: ducking, raw: obstacles.map(function (o) { return { t: o.type, x: o.x, w: o.w, y: o.y, h: o.h }; }), parts: obstacles.map(function (o) { return o.parts ? o.parts.map(function (p) { return p.name; }).join('+') : o.type; }) }; },"
    " setScore: function (n) { distance = n / 0.025; } };"
    if test_hook else ""
)
html = html.replace("/*__TESTHOOK__*/", hook)
with open(os.path.join(out_dir, "dino", "index.html"), "w") as f:
    f.write(html)

print(f"dino {dino_w}x{dino_h}  saguaro {sag_w}x{sag_h}  cluster B w={B_w}  windows A(t={tA:.2f},{durA:.2f}s) B(t={tB:.2f},{durB:.2f}s)", file=sys.stderr)
print("jump starts:", [round(s, 2) for s in starts], file=sys.stderr)
