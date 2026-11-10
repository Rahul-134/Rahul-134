"""Build the "Let's Connect" section art: connect/card.svg, connect/<link>.svg and connect/wave.svg.

The card is an animated hero (hopping pixel dino saying hi, pulsing status pill, blinking prompt); each link is
its own SVG so the README can wrap it in a normal <a>. Everything follows the active accent theme.

usage: python3 gen_connect.py OUT_DIR      # writes OUT_DIR/connect/*.svg
"""
import html
import math
import os
import sys

sys.dont_write_bytecode = True
import sprites as S
import theme_colors

T = theme_colors.current()
ACCENT, SHADE, LIGHT = T.accent, T.shade, T.light
SANS = "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"

out_dir = os.path.join(sys.argv[1], "connect")
os.makedirs(out_dir, exist_ok=True)
e = html.escape


def write(name, text):
    with open(os.path.join(out_dir, name), "w") as f:
        f.write(text)


def shapes(rows_, u=3):
    paths = S.path_by_colour(rows_, u)
    order = ["O", "D", "Y", "L", "B", "M", "T", "K", "W", "g", "G", "h", "S", "P", "X"]
    return "".join(f'<path fill="{S.PAL[c]}" d="{paths[c]}"/>' for c in order if c in paths)


# ------------------------------------------------------------------ shared bits
def frame_defs(w, h, glow_x=0.2):
    return f'''
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.55"/>
      <stop offset="0.45" stop-color="#2a2a2a"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0.30"/>
    </linearGradient>
    <radialGradient id="glow" cx="{glow_x}" cy="0.35" r="0.6">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.16"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#fff" stop-opacity="0.07"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="card"><rect width="{w}" height="{h}" rx="20"/></clipPath>'''


def frame(w, h, delay=0.0, period=7):
    return f'''
  <rect width="{w}" height="{h}" rx="20" fill="#151515"/>
  <rect width="{w}" height="{h}" rx="20" fill="url(#glow)"/>
  <rect x="0.75" y="0.75" width="{w - 1.5}" height="{h - 1.5}" rx="19.25" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
  <g clip-path="url(#card)"><g class="shine" style="animation-delay:{delay}s"><rect x="-260" y="-40" width="130" height="{h + 80}" fill="url(#beam)" transform="skewX(-18)"/></g></g>'''


COMMON_CSS = """
    .pulse{animation:pulse 2s ease-in-out infinite}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
    .caret{animation:caret 1.1s steps(1,end) infinite}
    @keyframes caret{0%,49%{opacity:1}50%,100%{opacity:0}}"""


# ------------------------------------------------------------------ hero card
W, H = 900, 300
GROUND = 246
DINO_H = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U


def hero():
    body = shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)
    legs = shapes(S.pad(S.ART["legsA"], S.DINO_W), S.DINO_U)
    body_h = len(S.ART["dinoBody"]) * S.DINO_U
    cactus = shapes(S.ART["small"])
    cactus_h = len(S.ART["small"]) * 3
    sag = shapes(S.ART["saguaro"])
    sag_h = len(S.ART["saguaro"]) * 3

    pill = "OPEN TO CONVERSATIONS"
    pill_w = round(len(pill) * 8.1 + 48)
    dino_x = 846                                    # right edge; flipped so the dino faces the text
    sparkles = "".join(
        f'<g class="tw" style="animation-delay:{d}s"><path d="M{x} {y - 6}v12M{x - 6} {y}h12" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" fill="none"/></g>'
        for x, y, d in [(588, 78, 0), (872, 112, 0.9), (700, 52, 1.7), (560, 160, 2.4)])

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Let's connect</title>
  <desc id="d">Let's build something useful, together. Open to interesting projects and conversations about AI, backend engineering and building useful products. A pixel dinosaur hops and says hey.</desc>
  <style>{COMMON_CSS}
    .shine{{animation:shine 7s ease-in-out infinite}}
    @keyframes shine{{0%,62%{{transform:translateX(0)}}100%{{transform:translateX({W + 420}px)}}}}
    .hop{{animation:hop 3.6s cubic-bezier(.3,.6,.4,1) infinite}}
    @keyframes hop{{0%,6%{{transform:translateY(0)}}16%{{transform:translateY(-34px)}}28%,100%{{transform:translateY(0)}}}}
    .say{{transform-box:fill-box;transform-origin:85% 100%;animation:say 3.6s ease-out infinite}}
    @keyframes say{{0%,22%{{opacity:0;transform:scale(.6)}}30%{{opacity:1;transform:scale(1.06)}}34%{{transform:scale(1)}}78%{{opacity:1;transform:scale(1)}}90%,100%{{opacity:0;transform:scale(.9)}}}}
    .tw{{animation:tw 3.2s ease-in-out infinite;opacity:.15}}
    @keyframes tw{{0%,100%{{opacity:.1}}50%{{opacity:.8}}}}
    @media (prefers-reduced-motion:reduce){{.pulse,.caret,.shine,.hop,.say,.tw{{animation:none}}.say{{opacity:1}}.tw{{opacity:.5}}}}
  </style>
  <defs>{frame_defs(W, H)}
  </defs>
  {frame(W, H)}

  <!-- status pill -->
  <rect x="44" y="40" width="{pill_w}" height="26" rx="13" fill="{ACCENT}" fill-opacity="0.10" stroke="{ACCENT}" stroke-opacity="0.35"/>
  <circle class="pulse" cx="60" cy="53" r="4" fill="{ACCENT}"/>
  <text x="74" y="58" font-size="11.5" fill="{ACCENT}" letter-spacing="1.5" font-family="{MONO}">{pill}</text>

  <!-- headline -->
  <text x="44" y="124" font-size="40" font-weight="800" fill="#FFFFFF" font-family="{SANS}">Let's build something</text>
  <text x="44" y="170" font-size="40" font-weight="800" fill="{ACCENT}" font-family="{SANS}">useful, together.</text>
  <text x="44" y="206" font-size="14.5" fill="#9aa0a6" font-family="{SANS}">Interesting projects and conversations about AI,</text>
  <text x="44" y="226" font-size="14.5" fill="#9aa0a6" font-family="{SANS}">backend engineering and building useful products.</text>

  <!-- prompt -->
  <text x="44" y="268" font-size="14" font-family="{MONO}"><tspan fill="{ACCENT}">$</tspan><tspan fill="#FFFFFF"> say hello</tspan><tspan class="caret" fill="{ACCENT}">_</tspan></text>

  <!-- scene -->
  {sparkles}
  <path d="M520 {GROUND} H {W - 28}" stroke="#3a3a3a" stroke-width="2" stroke-linecap="round"/>
  <path d="M560 {GROUND + 9} h14 M640 {GROUND + 9} h30 M760 {GROUND + 9} h10 M820 {GROUND + 9} h22" stroke="#2f2f2f" stroke-width="2" stroke-linecap="round"/>
  <g transform="translate(586,{GROUND - sag_h})">{sag}</g>
  <g transform="translate(634,{GROUND - cactus_h})">{cactus}</g>
  <g class="hop">
    <g transform="translate({dino_x},{GROUND - DINO_H}) scale(-1,1)">{body}<g transform="translate(0,{body_h})">{legs}</g></g>
  </g>
  <g class="say">
    <rect x="662" y="104" width="96" height="40" rx="14" fill="#FFFFFF"/>
    <path d="M750 142 L772 160 L764 138 Z" fill="#FFFFFF"/>
    <text x="710" y="130" text-anchor="middle" font-size="19" font-weight="800" fill="#161616" font-family="{SANS}">hey!</text>
  </g>
</svg>
'''
    write("card.svg", svg)


# ------------------------------------------------------------------ link buttons
BW, BH = 440, 116

GITHUB = ("M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04"
          "-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 "
          "1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 "
          "0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02."
          "006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 "
          "4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 "
          "22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12")

LINKS = [
    dict(slug="linkedin", label="Say hello", sub="LinkedIn · let's talk", primary=True, glyph="in",
         desc="LinkedIn: say hello and let's talk."),
    dict(slug="github", label="Follow along", sub="GitHub · @Rahul-134", glyph="github",
         desc="GitHub: follow along at Rahul-134."),
    dict(slug="portfolio", label="See my work", sub="rahul-lumbhani-portfolio.vercel.app", glyph="globe", live=True,
         desc="Portfolio: projects, skills, live stats and an ask-me-anything terminal."),
    dict(slug="play", label="Play my dino game", sub="Can you top the leaderboard?", glyph="play",
         desc="Play the dino game and try to top the leaderboard."),
]


def glyph(kind, primary):
    cx, cy = 60, 58
    ink = "#161616" if primary else ACCENT
    if kind == "in":
        return f'<text x="{cx}" y="{cy + 8}" text-anchor="middle" font-size="22" font-weight="800" fill="{ink}" font-family="{SANS}">in</text>'
    if kind == "github":
        return f'<g transform="translate({cx - 18},{cy - 18}) scale(1.5)"><path fill="{ink}" d="{GITHUB}"/></g>'
    if kind == "globe":
        return (f'<g transform="translate({cx - 18},{cy - 18}) scale(1.5)" fill="none" stroke="{ink}" stroke-width="1.7" stroke-linecap="round">'
                '<circle cx="12" cy="12" r="9.6"/><ellipse cx="12" cy="12" rx="4.2" ry="9.6"/><path d="M2.4 12h19.2M4 7h16M4 17h16"/></g>')
    return f'<g transform="translate({cx - 18},{cy - 18}) scale(1.5)"><path fill="{ink}" d="M8 5.2v13.6L19.2 12z"/></g>'


def link(i, p):
    primary = p.get("primary")
    sub_size = 12.5 if len(p["sub"]) > 30 else 14
    live = ""
    if p.get("live"):
        lx = BW - 118
        live = (f'<rect x="{lx}" y="22" width="54" height="20" rx="10" fill="#27c93f" fill-opacity="0.12" stroke="#27c93f" stroke-opacity="0.45"/>'
                f'<circle class="pulse" cx="{lx + 13}" cy="32" r="3.2" fill="#27c93f"/>'
                f'<text x="{lx + 22}" y="36" font-size="10" fill="#5EE27A" letter-spacing="1.3" font-family="{MONO}">LIVE</text>')
    circle_fill = f'fill="{ACCENT}"' if primary else f'fill="{ACCENT}" fill-opacity="0.12" stroke="{ACCENT}" stroke-opacity="0.4"'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BW} {BH}" width="{BW}" height="{BH}" role="img" aria-labelledby="t">
  <title id="t">{e(p["desc"])}</title>
  <style>{COMMON_CSS}
    .shine{{animation:shine 7s ease-in-out infinite}}
    @keyframes shine{{0%,62%{{transform:translateX(0)}}100%{{transform:translateX({BW + 360}px)}}}}
    .nudge{{animation:nudge 2.4s ease-in-out infinite}}
    @keyframes nudge{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(3px,-3px)}}}}
    @media (prefers-reduced-motion:reduce){{.pulse,.shine,.nudge{{animation:none}}}}
  </style>
  <defs>{frame_defs(BW, BH, 0.12)}
  </defs>
  {frame(BW, BH, delay=i * 1.3)}
  <circle cx="60" cy="58" r="31" {circle_fill}/>
  {glyph(p["glyph"], primary)}
  <text x="112" y="56" font-size="26" font-weight="800" fill="#FFFFFF" font-family="{SANS}">{e(p["label"])}</text>
  <text x="112" y="82" font-size="{sub_size}" fill="#9aa0a6" font-family="{MONO}">{e(p["sub"])}</text>
  {live}
  <text class="nudge" x="{BW - 34}" y="40" text-anchor="end" font-size="20" fill="{ACCENT}" font-family="{MONO}">↗</text>
</svg>
'''
    write(f'{p["slug"]}.svg', svg)


# ------------------------------------------------------------------ footer wave
def wave():
    WW, WH, P = 900, 110, 450

    def layer(base, amp, phase):
        pts = []
        for x in range(0, WW + P + 1, 6):
            y = base + amp * math.sin(2 * math.pi * x / P + phase) + 0.35 * amp * math.sin(4 * math.pi * x / P + phase * 1.7)
            pts.append(f"{x},{y:.1f}")
        return "M" + " L".join(pts) + f" L{WW + P},{WH} L0,{WH} Z"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WW} {WH}" width="{WW}" height="{WH}" role="img" aria-label="">
  <style>
    .w1{{animation:slide {P / 28:g}s linear infinite}}
    .w2{{animation:slide {P / 18:g}s linear infinite reverse}}
    .w3{{animation:slide {P / 40:g}s linear infinite}}
    @keyframes slide{{from{{transform:translateX(0)}}to{{transform:translateX(-{P}px)}}}}
    @media (prefers-reduced-motion:reduce){{.w1,.w2,.w3{{animation:none}}}}
  </style>
  <defs>
    <linearGradient id="fadeX" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff"/>
      <stop offset="0.55" stop-color="#fff" stop-opacity="0.55"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0.04"/>
    </linearGradient>
    <mask id="m"><rect width="{WW}" height="{WH}" fill="url(#fadeX)"/></mask>
  </defs>
  <g mask="url(#m)">
    <g class="w3"><path d="{layer(46, 9, 2.1)}" fill="{SHADE}" fill-opacity="0.30"/></g>
    <g class="w2"><path d="{layer(58, 11, 0.6)}" fill="{ACCENT}" fill-opacity="0.38"/></g>
    <g class="w1"><path d="{layer(72, 10, 4.0)}" fill="{ACCENT}" fill-opacity="0.85"/></g>
  </g>
</svg>
'''
    write("wave.svg", svg)


hero()
for i, p in enumerate(LINKS):
    link(i, p)
wave()
print("connect: card.svg, " + ", ".join(p["slug"] + ".svg" for p in LINKS) + ", wave.svg", file=sys.stderr)
