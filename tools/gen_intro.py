#!/usr/bin/env python3
"""Build the About Me intro and its three "tap a row" sections in the Playful style, under about/:

    intro.svg              the intro: "I turn models into products", a sky window with the T-rex, and the
                           data -> model -> backend -> pixel strip
    hint.svg               the "Tap a row to see what's behind it" sign above the rows
    row-<slug>.svg         the clickable title of each row (Focus, Problem solving, Builds), used in <summary>
    focus-<slug>.svg       Focus: one wide button per project (the README links each to its repository)
    problem-solving.svg    Problem solving: the solved count, the write-ups and the topics
    build-<slug>.svg       Builds: one button per project, tagged AI co-pilot / web app / game

Each link is its own image so the README can wrap it in a normal <a>. Colours follow the `about` section
theme, and RAHUL_MODE=night draws the Night look (tools/theme.py draws both).

usage: python3 gen_intro.py OUT_DIR      # writes OUT_DIR/about/*.svg
"""
import html
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sprites as S  # noqa: E402
import theme_colors  # noqa: E402
import banner  # noqa: E402
import counts  # noqa: E402

T = theme_colors.current()
ACCENT = T.accent
INK, TEXT, PAPER, PANEL, SKY = banner.INK, banner.TEXT, banner.PAPER, banner.PANEL, banner.SKY
ROUND = "'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif"
e = html.escape

SOLVED = counts.solved()   # LeetCode problems solved, rounded down to a ten, from tools/stats.json
WRITTEN_UP = "60+"         # solutions written up in leetcode-solutions-python

out_dir = os.path.join(sys.argv[1] if len(sys.argv) > 1 else sys.exit(__doc__), "about")
os.makedirs(out_dir, exist_ok=True)


def write(name, text):
    with open(os.path.join(out_dir, name), "w") as f:
        f.write(text)


# ------------------------------------------------------------------ shared bits
def tw(text, size):
    return len(text) * size * 0.56


def shell(w, h, fill=PAPER, rx=24):
    return (f'<rect x="11" y="11" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{INK}"/>'
            f'<rect x="3" y="3" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="4"/>')


def pill(x, y, text, fill=ACCENT, size=12.5, h=28, anchor="start", shadow=True, dot=None, spacing=1.5):
    """A rounded label. Returns (svg, width). `dot` adds a coloured dot in front (category chips)."""
    pad = 34 if dot else 14
    w = tw(text, size) + spacing * len(text) + pad + 14
    if anchor == "end":
        x -= w
    fg = TEXT if fill == PANEL else INK
    s = f'<rect x="{x + 3:.1f}" y="{y + 3}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{INK}"/>' if shadow else ""
    s += f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>'
    if dot:
        s += f'<circle cx="{x + 15:.1f}" cy="{y + h / 2}" r="5" fill="{dot}" stroke="{INK}" stroke-width="1.6"/>'
    s += (f'<text x="{x + pad:.1f}" y="{y + h / 2 + size * 0.36:.1f}" font-size="{size}" font-weight="800" fill="{fg}" '
          f'letter-spacing="{spacing}">{e(text)}</text>')
    return s, w


def style(extra=""):
    return f"""<style>
    {banner.font_face()}
    text{{font-family:{ROUND}}}
    .nudge{{animation:nudge 2.4s ease-in-out infinite}}
    @keyframes nudge{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(3px,-3px)}}}}
    .bob{{animation:bob 2.8s ease-in-out infinite}}
    @keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}{extra}
    @media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
  </style>"""


def arrow(cx, cy, sym="↗"):
    return (f'<g class="nudge"><circle cx="{cx}" cy="{cy}" r="17" fill="#fff" stroke="{INK}" stroke-width="2.6"/>'
            f'<text x="{cx}" y="{cy + 7}" text-anchor="middle" font-size="19" font-weight="800" fill="{INK}">{sym}</text></g>')


DINO_H = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U
DINO_W = S.DINO_W * S.DINO_U


def dino(legs="legsA"):
    body = banner.shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)
    lg = banner.shapes(S.pad(S.ART[legs], S.DINO_W), S.DINO_U)
    return f'{body}<g transform="translate(0,{len(S.ART["dinoBody"]) * S.DINO_U})">{lg}</g>'


def cactus(x, y_bottom, kind, k=1.0):
    rows = S.ART[kind]
    return (f'<g transform="translate({x},{y_bottom - len(rows) * S.OBJ_U * k:.1f}) scale({k})">'
            f'{banner.shapes(rows, S.OBJ_U)}</g>')


# ------------------------------------------------------------------ icons (drawn on a 24-unit grid, centred on cx, cy)
INVADER = ["..X.....X..", "...X...X...", "..XXXXXXX..", ".XX.XXX.XX.", "XXXXXXXXXXX", "X.XXXXXXX.X", "X.X.....X.X", "...XX.XX..."]
GLOBE = ('<g fill="none" stroke="{ink}" stroke-width="1.9" stroke-linecap="round"><circle cx="12" cy="12" r="9.6" fill="#fff"/>'
         '<ellipse cx="12" cy="12" rx="4.2" ry="9.6"/><path d="M2.4 12h19.2M4 7h16M4 17h16"/></g>')


def icon(kind, cx, cy, size=34):
    k = size / 24
    g = lambda inner: f'<g transform="translate({cx - size / 2:.1f},{cy - size / 2:.1f}) scale({k:.3f})">{inner}</g>'
    if kind == "compass":
        return g(f'<circle cx="12" cy="12" r="10" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                 f'<path d="M12 4.6 L14.7 12 L12 19.4 L9.3 12Z" fill="{INK}"/>'
                 f'<path d="M12 4.6 L14.7 12 L9.3 12Z" fill="#FF6B4A" stroke="{INK}" stroke-width="1.1" stroke-linejoin="round"/>'
                 f'<circle cx="12" cy="12" r="1.7" fill="#fff" stroke="{INK}" stroke-width="1.1"/>')
    if kind == "notebook":
        lines = "".join(f'<path d="M10 {y}h7" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>' for y in (8.5, 12, 15.5))
        rings = "".join(f'<rect x="3.6" y="{y}" width="4" height="2" rx="1" fill="{INK}"/>' for y in (6, 11, 16))
        return g(f'<rect x="5.5" y="2.5" width="14" height="19" rx="2.4" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                 f'<rect x="15.5" y="2.5" width="2.6" height="7" fill="#FF6B4A" stroke="{INK}" stroke-width="1"/>{lines}{rings}')
    if kind == "target":
        return g(f'<circle cx="11" cy="13" r="9.5" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                 f'<circle cx="11" cy="13" r="6" fill="#FF6B4A" stroke="{INK}" stroke-width="1.6"/>'
                 f'<circle cx="11" cy="13" r="2.6" fill="#fff" stroke="{INK}" stroke-width="1.4"/>'
                 f'<path d="M11 13 L20.5 3.5" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
                 f'<path d="M18 3 L21 3 L21 6 M20.5 3.5 L23 1" stroke="{INK}" stroke-width="1.8" stroke-linecap="round" fill="none"/>')
    if kind == "globe":
        return g(GLOBE.format(ink=INK))
    if kind == "dice":
        pips = "".join(f'<circle cx="{x}" cy="{y}" r="1.7" fill="{INK}"/>' for x, y in ((7.5, 7.5), (16.5, 7.5), (12, 12), (7.5, 16.5), (16.5, 16.5)))
        return g(f'<g transform="rotate(-10 12 12)"><rect x="3" y="3" width="18" height="18" rx="4.5" fill="#fff" stroke="{INK}" stroke-width="2"/>{pips}</g>')
    if kind == "invader":
        u = 2
        rects = []
        for y, row in enumerate(INVADER):
            for x, c in enumerate(row):
                if c == "X":
                    rects.append(f'<rect x="{x * u}" y="{y * u}" width="{u}" height="{u}"/>')
        return g(f'<g transform="translate(1,4)" fill="{INK}" shape-rendering="crispEdges">{"".join(rects)}</g>')
    if kind == "dino":
        k2 = size * 1.25 / DINO_H
        w, h = DINO_W * k2, DINO_H * k2
        return f'<g transform="translate({cx - w / 2 + 1:.1f},{cy - h / 2 + 1:.1f}) scale({k2:.3f})">{dino()}</g>'
    if kind == "down":
        return g(f'<rect x="4" y="2.5" width="16" height="11" rx="2.5" fill="#fff" stroke="{INK}" stroke-width="1.8"/>'
                 f'<rect x="7" y="5.5" width="10" height="5" rx="1" fill="{ACCENT}" stroke="{INK}" stroke-width="1.2"/>'
                 f'<path d="M12 15.5v6M8.5 18.5l3.5 3.5 3.5-3.5" stroke="{INK}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')
    if kind == "data":
        return g(f'<g fill="#fff" stroke="{INK}" stroke-width="1.9"><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6"/>'
                 f'<path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3" fill="none"/><ellipse cx="12" cy="6" rx="7" ry="3"/></g>')
    if kind == "model":
        nodes = [(5, 7), (5, 17), (12, 4.5), (12, 12), (12, 19.5), (19, 12)]
        edges = [(0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 5)]
        ln = "".join(f'<path d="M{nodes[a][0]} {nodes[a][1]}L{nodes[b][0]} {nodes[b][1]}"/>' for a, b in edges)
        dots = "".join(f'<circle cx="{x}" cy="{y}" r="2.6" fill="#fff" stroke="{INK}" stroke-width="1.6"/>' for x, y in nodes)
        return g(f'<g stroke="{INK}" stroke-width="1.3">{ln}</g>{dots}')
    if kind == "backend":
        return g(f'<g fill="#fff" stroke="{INK}" stroke-width="1.9"><rect x="3.5" y="4" width="17" height="7" rx="2"/>'
                 f'<rect x="3.5" y="13" width="17" height="7" rx="2"/></g>'
                 f'<circle cx="7.5" cy="7.5" r="1.4" fill="#5BD68A" stroke="{INK}" stroke-width=".9"/>'
                 f'<circle cx="7.5" cy="16.5" r="1.4" fill="#5BD68A" stroke="{INK}" stroke-width=".9"/>'
                 f'<path d="M12 7.5h5M12 16.5h5" stroke="{INK}" stroke-width="1.6" stroke-linecap="round"/>')
    if kind == "pixel":
        return g(f'<rect x="2.5" y="3.5" width="19" height="13" rx="2" fill="#fff" stroke="{INK}" stroke-width="1.9"/>'
                 f'<rect x="13" y="8" width="4" height="4" fill="{ACCENT}" stroke="{INK}" stroke-width="1"/>'
                 f'<path d="M9 21h6M12 16.5V21" stroke="{INK}" stroke-width="1.9" stroke-linecap="round"/>')
    if kind == "scope":                  # Focus: a crosshair on a lens
        return g(f'<circle cx="12" cy="12" r="9.5" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                 f'<circle cx="12" cy="12" r="4.2" fill="#FF6B4A" stroke="{INK}" stroke-width="1.6"/>'
                 f'<path d="M12 1v5M12 18v5M1 12h5M18 12h5" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>'
                 f'<circle cx="12" cy="12" r="1.3" fill="{INK}"/>')
    if kind == "puzzle":                 # Problem solving
        return g(f'<path d="M3.5 8.5h5a3 3 0 1 1 6 0h5v5a3 3 0 1 1 0 6v1.5H3.5V15a3 3 0 1 0 0-6z" fill="#FFC83D" '
                 f'stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
                 f'<path d="M6.5 11.5h3" stroke="#fff" stroke-width="1.8" stroke-linecap="round" opacity=".8"/>')
    if kind == "rocket":                 # Builds
        return g(f'<path d="M9.5 19.5c-1.4 1.6-2 3-2.5 4 1-.3 2.6-1 4.2-2.4" fill="#FF6B4A" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
                 f'<path d="M7 13l-3.6 1.4 2.4-4.6 4-.6zM11 17l-1.4 3.6 4.6-2.4.6-4z" fill="#FF6B4A" stroke="{INK}" stroke-width="1.5" stroke-linejoin="round"/>'
                 f'<path d="M7.5 16.5c2-6.5 6.5-12 14-13.5-1.5 7.5-7 12-13.5 14z" fill="#fff" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
                 f'<circle cx="15" cy="9" r="2.4" fill="{ACCENT}" stroke="{INK}" stroke-width="1.6"/>')
    raise ValueError(kind)


# ------------------------------------------------------------------ intro card
def intro():
    W, H = 900, 368
    # sky window on the right, with the T-rex
    sx, sy, sw, sh = 626, 30, 240, 208
    ground = sy + sh - 34
    pills, x = [], 36
    for text, fill in (("HI, I'M RAHUL", ACCENT), ("AI/ML ENGINEER", PANEL), ("GENAI ENTHUSIAST", PANEL)):
        p, w = pill(x, 30, text, fill, size=12)
        pills.append(p)
        x += w + 12
    mark_w = tw("into products.", 40) + 28
    tech = ["Python", "FastAPI", "Django", "React"]
    tech_line = (f'<tspan fill-opacity=".75">built with </tspan>' +
                 "".join(f'<tspan font-weight="800">{t}</tspan><tspan fill-opacity=".75">{sep}</tspan>'
                         for t, sep in zip(tech, [", ", ", ", " and ", "."])))
    # the end-to-end strip
    stations = [("data", "the data"), ("model", "the model"), ("backend", "the backend"), ("pixel", "the last pixel")]
    st_y, st_h, gap = 284, 54, 34
    st_w = (W - 14 - 2 * 36 - 3 * gap) / 4
    strip = []
    for i, (kind, label) in enumerate(stations):
        x0 = 36 + i * (st_w + gap)
        strip.append(f'<g class="bob" style="animation-delay:{-i * 0.35:.2f}s">'
                     f'<rect x="{x0 + 4:.1f}" y="{st_y + 4}" width="{st_w:.1f}" height="{st_h}" rx="16" fill="{INK}"/>'
                     f'<rect x="{x0:.1f}" y="{st_y}" width="{st_w:.1f}" height="{st_h}" rx="16" fill="{PANEL}" stroke="{INK}" stroke-width="3"/>'
                     f'<circle cx="{x0 + 30:.1f}" cy="{st_y + st_h / 2}" r="19" fill="{ACCENT}" stroke="{INK}" stroke-width="2.5"/>'
                     f'{icon(kind, x0 + 30, st_y + st_h / 2, 24)}'
                     f'<text x="{x0 + 58:.1f}" y="{st_y + st_h / 2 + 6}" font-size="17" font-weight="800" fill="{TEXT}">{label}</text></g>')
        if i < 3:
            ax = x0 + st_w + 5
            ay = st_y + st_h / 2
            strip.append(f'<path class="flow" d="M{ax:.1f} {ay}h{gap - 12}" stroke="{TEXT}" stroke-width="3" stroke-linecap="round" stroke-dasharray="2 6"/>'
                         f'<path d="M{ax + gap - 15:.1f} {ay - 5}l6 5-6 5" stroke="{TEXT}" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    k = 0.92
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">About me</title>
  <desc id="d">Hi, I'm Rahul, an AI/ML engineer and Generative AI enthusiast. I turn models into products: LLM-powered apps, data platforms and ML tooling built with Python, FastAPI, Django and React. I like owning a project end to end, from the data and the model to the backend and the last pixel on screen.</desc>
  {style('''
    .flow{animation:flow .9s linear infinite}
    @keyframes flow{to{stroke-dashoffset:-16}}
    .hop{animation:hop 3.2s cubic-bezier(.3,.6,.4,1) infinite}
    @keyframes hop{0%,8%{transform:translateY(0)}18%{transform:translateY(-26px)}30%,100%{transform:translateY(0)}}
    .say{transform-box:fill-box;transform-origin:100% 100%;animation:say 3.2s ease-out infinite}
    @keyframes say{0%,24%{opacity:0;transform:scale(.6)}32%{opacity:1;transform:scale(1.06)}36%{transform:scale(1)}80%{opacity:1}92%,100%{opacity:0}}
    .rays{animation:spin 60s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}''')}
  <defs>
    <clipPath id="sky"><rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="18"/></clipPath>
    {banner.ground_tile(40)}
  </defs>
  {shell(W, H)}
  {"".join(pills)}
  <text x="36" y="118" font-size="44" font-weight="800" fill="{TEXT}">I turn models</text>
  <g transform="rotate(-2 {36 + mark_w / 2:.0f} 152)">
    <rect x="40" y="133" width="{mark_w:.0f}" height="50" rx="16" fill="{INK}"/>
    <rect x="36" y="129" width="{mark_w:.0f}" height="50" rx="16" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>
    <text x="50" y="166" font-size="40" font-weight="800" fill="{INK}">into products.</text>
  </g>
  <text x="36" y="214" font-size="17" font-weight="600" fill="{TEXT}" fill-opacity=".75">LLM-powered apps, data platforms and ML tooling,</text>
  <text x="36" y="238" font-size="17" font-weight="600" fill="{TEXT}">{tech_line}</text>

  <rect x="{sx + 5}" y="{sy + 6}" width="{sw}" height="{sh}" rx="18" fill="{INK}"/>
  <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="18" fill="{SKY}"/>
  <g clip-path="url(#sky)">
    {banner.stars(sx + 6, sy + 8, sw - 60, 100, 9, seed=11, avoid=[(sx + 150, sy, 90, 80)])}
    {banner.sun(sx + sw - 40, sy + 40, 0.8)}
    {banner.cloud(sx + 14, sy + 22, 0.55)}
    <g transform="translate({sx},{ground - 10})"><rect width="{sw}" height="60" fill="url(#sand)"/></g>
    {cactus(sx + 22, ground + 1, "saguaro", 0.9)}
    {cactus(sx + 70, ground + 1, "small", 0.9)}
    <g class="hop"><g transform="translate({sx + sw - 30},{ground - DINO_H * k + 1:.1f}) scale({-k},{k})">{dino()}</g></g>
    <g class="say">
      <rect x="{sx + 92}" y="{sy + 60}" width="92" height="38" rx="15" fill="#fff" stroke="{INK}" stroke-width="3"/>
      <path d="M{sx + 166} {sy + 96} L{sx + 186} {sy + 112} L{sx + 176} {sy + 94} Z" fill="#fff" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
      <rect x="{sx + 160}" y="{sy + 91}" width="18" height="6" fill="#fff"/>
      <text x="{sx + 138}" y="{sy + 85}" text-anchor="middle" font-size="18" font-weight="800" fill="{INK}">ship it!</text>
    </g>
  </g>
  <rect x="{sx}" y="{sy}" width="{sw}" height="{sh}" rx="18" fill="none" stroke="{INK}" stroke-width="3"/>

  <text x="36" y="270" font-size="15" font-weight="700" fill="{TEXT}" fill-opacity=".7">I like owning a project end to end, from</text>
  {"".join(strip)}
</svg>
"""
    write("intro.svg", svg)


# ------------------------------------------------------------------ Focus: wide project buttons
FOCUS = [
    dict(slug="datapilot", name="DataPilot", icon="compass", tag="DATA · ML · AI",
         lines=["Ask questions of your data in plain English, scrape the web with AI,", "and train ML models, all in one workspace."]),
    dict(slug="bitnote", name="BitNote", icon="notebook", tag="GENAI · LOCAL LLMs",
         lines=["Notion-style notebooks with an AI tutor: syllabuses, learning", "roadmaps and recall quizzes."]),
    dict(slug="bitcareer", name="BitCareer", icon="target", tag="GENAI · CAREERS",
         lines=["A learning and career-readiness platform with AI mock interviews", "and skill analysis."]),
]


def focus(p):
    W, H = 900, 150
    cy = (3 + H - 11) / 2
    tag, _ = pill(146 + tw(p["name"], 32) + 18, 30, p["tag"], ACCENT, size=11.5, h=26)
    lines = "".join(f'<text x="146" y="{88 + i * 25}" font-size="18" font-weight="600" fill="{TEXT}" fill-opacity=".75">{e(t)}</text>'
                    for i, t in enumerate(p["lines"]))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
  <title id="t">{e(p["name"])}: {e(" ".join(p["lines"]))}</title>
  {style()}
  {shell(W, H, rx=22)}
  <g class="bob"><circle cx="80" cy="{cy + 4}" r="40" fill="{INK}"/>
  <circle cx="76" cy="{cy}" r="40" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>
  {icon(p["icon"], 76, cy, 44)}</g>
  <text x="146" y="56" font-size="32" font-weight="800" fill="{TEXT}">{e(p["name"])}</text>
  {tag}
  {lines}
  {arrow(W - 52, cy)}
</svg>
"""
    write(f'focus-{p["slug"]}.svg', svg)


# ------------------------------------------------------------------ Problem solving card
TOPICS = ["Arrays & hashing", "Strings", "Two pointers", "Sliding window", "Dynamic programming", "Bit manipulation"]


def problems():
    W, H = 900, 348
    head, _ = pill(36, 28, "PROBLEM SOLVING", ACCENT, size=12.5, h=30)
    cta, _ = pill(W - 50, 30, "SOLUTIONS ↗", PANEL, size=12, h=28, anchor="end")
    bx, by, bw, bh = 36, 78, 250, 160
    checks = [(f"{WRITTEN_UP} solutions written up", " in leetcode-solutions-python"),
              ("Each one runnable", " and type-hinted"),
              ("Shipped with", " a built-in test case")]
    rows = []
    for i, (strong, rest) in enumerate(checks):
        y = 126 + i * 40
        rows.append(f'<circle cx="{bx + bw + 46}" cy="{y - 6}" r="12" fill="{ACCENT}" stroke="{INK}" stroke-width="2.4"/>'
                    f'<path d="M{bx + bw + 40} {y - 6}l4.5 4.5 7.5-8.5" stroke="{INK}" stroke-width="2.8" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
                    f'<text x="{bx + bw + 68}" y="{y}" font-size="19" fill="{TEXT}"><tspan font-weight="800">{e(strong)}</tspan>'
                    f'<tspan font-weight="600" fill-opacity=".75">{e(rest)}</tspan></text>')
    dots = ["#FF6B4A", "#FFC83D", "#5BD68A", "#60A5FA", "#A78BFA", "#F472B6"]
    chips = []
    for r, row in enumerate((TOPICS[:3], TOPICS[3:])):           # two rows of three
        x = 36
        for j, t in enumerate(row):
            i = r * 3 + j
            c, w = pill(x, 258 + r * 38, t, PANEL, size=13, h=28, shadow=False, dot=dots[i], spacing=0.6)
            chips.append(f'<g class="bob" style="animation-delay:{-i * 0.4:.1f}s">{c}</g>')
            x += w + 10
    num_fill = TEXT if banner.NIGHT else INK
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Problem solving</title>
  <desc id="d">{SOLVED} LeetCode problems solved, with {WRITTEN_UP} of the solutions written up in leetcode-solutions-python, each one runnable, type-hinted and shipped with a built-in test case. Topics: {e(", ".join(TOPICS))}.</desc>
  {style('''
    .pop{transform-box:fill-box;transform-origin:center;animation:pop 3s ease-in-out infinite}
    @keyframes pop{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}''')}
  <defs><clipPath id="board"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="18"/></clipPath>{banner.ground_tile(30)}</defs>
  {shell(W, H)}
  {head}
  {cta}
  <rect x="{bx + 5}" y="{by + 6}" width="{bw}" height="{bh}" rx="18" fill="{INK}"/>
  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="18" fill="{SKY}"/>
  <g clip-path="url(#board)">
    {banner.stars(bx + 8, by + 6, bw - 16, 40, 6, seed=3)}
    <g transform="translate({bx},{by + bh - 30})"><rect width="{bw}" height="40" fill="url(#sand)"/></g>
    {cactus(bx + bw - 44, by + bh - 19, "small", 0.8)}
    <g class="bob"><g transform="translate({bx + 14},{by + bh - 20 - DINO_H * 0.55:.1f}) scale(.55)">{dino()}</g></g>
  </g>
  <rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="18" fill="none" stroke="{INK}" stroke-width="3"/>
  <text class="pop" x="{bx + bw / 2}" y="{by + 62}" text-anchor="middle" font-size="58" font-weight="800" fill="{num_fill}">{SOLVED}</text>
  <text x="{bx + bw / 2}" y="{by + 86}" text-anchor="middle" font-size="13" font-weight="800" fill="{num_fill}" letter-spacing="1.5">SOLVED ON LEETCODE</text>
  {"".join(rows)}
  {"".join(chips)}
</svg>
"""
    write("problem-solving.svg", svg)


# ------------------------------------------------------------------ Builds: one button per project
CATS = {"ai": ("AI CO-PILOT", "#A78BFA"), "web": ("WEB APP", "#5BD68A"), "game": ("GAME", "#FB923C")}
BUILDS = [
    dict(slug="datapilot", label="DataPilot", sub="Chat with data, scrape, train ML", icon="compass", cats=["ai"]),
    dict(slug="bitnote", label="BitNote", sub="Notebooks with an AI tutor", icon="notebook", cats=["ai", "web"]),
    dict(slug="bitcareer", label="BitCareer", sub="AI mock interviews, skill analysis", icon="target", cats=["web"]),
    dict(slug="portfolio", label="Portfolio", sub="With an ask-me-anything terminal", icon="globe", cats=["web"]),
    dict(slug="virtual-arcade-zone", label="Virtual Arcade Zone", sub="7 console mini-games, pure Java", icon="invader", cats=["game"]),
    dict(slug="business-bytes", label="Business Bytes", sub="A desktop Monopoly", icon="dice", cats=["game"]),
    dict(slug="dino", label="Play the dino game", sub="Can you top the leaderboard?", icon="dino", cats=["game"]),
    dict(slug="more", label="Featured Projects", sub="Screens and demos, just below", icon="down", primary=True),
]


def build(p):
    BW, BH = 440, 116
    cy = (3 + BH - 11) / 2
    primary = p.get("primary")
    face = ACCENT if primary else PAPER
    fg = INK if primary else TEXT
    circle = "#FFFFFF" if primary else (SKY if p["icon"] == "dino" else ACCENT)
    chips, x = [], 114
    for c in p.get("cats", []):
        label, dot = CATS[c]
        s, w = pill(x, 16, label, PANEL, size=10, h=22, shadow=False, dot=dot)
        chips.append(s)
        x += w + 6
    if primary:
        s, _ = pill(114, 16, "MORE", "#FFFFFF", size=10, h=22, shadow=False)
        chips.append(s)
    size = 24
    while tw(p["label"], size) > BW - 114 - 76 and size > 18:
        size -= 1
    desc = f'{p["label"]}: {p["sub"]}' + (f' ({", ".join(CATS[c][0].lower() for c in p.get("cats", []))})' if p.get("cats") else "")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BW} {BH}" width="{BW}" height="{BH}" role="img" aria-labelledby="t">
  <title id="t">{e(desc)}</title>
  {style()}
  {shell(BW, BH, face, 22)}
  <circle cx="66" cy="{cy + 4}" r="33" fill="{INK}"/>
  <circle cx="62" cy="{cy}" r="33" fill="{circle}" stroke="{INK}" stroke-width="3"/>
  {icon(p["icon"], 62, cy, 36)}
  {"".join(chips)}
  <text x="114" y="{cy + 13}" font-size="{size}" font-weight="800" fill="{fg}">{e(p["label"])}</text>
  <text x="114" y="{cy + 35}" font-size="14" font-weight="600" fill="{fg}" fill-opacity=".7">{e(p["sub"])}</text>
  {arrow(BW - 42, cy, "↓" if primary else "↗")}
</svg>
"""
    write(f'build-{p["slug"]}.svg', svg)


# ------------------------------------------------------------------ the three rows' clickable titles
ROWS = [
    dict(slug="focus", title="Focus", sub="Generative AI, LLM apps and data & ML platforms", icon="scope"),
    dict(slug="problems", title="Problem solving", sub=f"{SOLVED} LeetCode problems solved", icon="puzzle"),
    dict(slug="builds", title="Builds", sub="AI co-pilots, web apps and interactive console games", icon="rocket"),
]


def row(i, p):
    """A big button-card for a row's <summary>, so the rows stand out between the cards around them."""
    W, H = 900, 112
    cy = (3 + H - 11) / 2
    tap, tap_w = pill(0, 0, "TAP TO OPEN", ACCENT, size=12, h=30)
    tx = W - 46 - tap_w
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
  <title id="t">{e(p["title"])}: {e(p["sub"])}. Tap to open.</title>
  {style('''
    .tap{animation:tap 2.2s ease-in-out infinite}
    @keyframes tap{0%,100%{transform:translateY(0)}50%{transform:translateY(3px)}}''')}
  {shell(W, H, PAPER, 22)}
  <g class="bob" style="animation-delay:{-i * 0.5:.1f}s"><circle cx="70" cy="{cy + 4}" r="34" fill="{INK}"/>
  <circle cx="66" cy="{cy}" r="34" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>
  {icon(p["icon"], 66, cy, 40)}</g>
  <text x="122" y="{cy - 3}" font-size="30" font-weight="800" fill="{TEXT}">{e(p["title"])}</text>
  <text x="122" y="{cy + 23}" font-size="17" font-weight="600" fill="{TEXT}" fill-opacity=".75">{e(p["sub"])}</text>
  <g transform="translate({tx:.1f},{cy - 15})"><g class="tap" style="animation-delay:{-i * 0.4:.1f}s">{tap}</g></g>
</svg>
"""
    write(f'row-{p["slug"]}.svg', svg)


def hint():
    """The "tap a row" sign between the intro and the rows: a bouncing sticker arrow on a theme-colour banner."""
    W, H = 620, 84
    text = "Tap a row to see what's behind it"
    bw = 96 + tw(text, 23) + 40
    x0 = (W - 14 - bw) / 2 + 3
    cy = (3 + H - 11) / 2
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t">
  <title id="t">{e(text)}</title>
  {style('''
    .down{animation:down 1.3s ease-in-out infinite}
    @keyframes down{0%,100%{transform:translateY(-3px)}50%{transform:translateY(4px)}}''')}
  <rect x="{x0 + 6:.1f}" y="9" width="{bw:.1f}" height="{H - 18}" rx="{(H - 18) / 2}" fill="{INK}"/>
  <rect x="{x0:.1f}" y="3" width="{bw:.1f}" height="{H - 18}" rx="{(H - 18) / 2}" fill="{ACCENT}" stroke="{INK}" stroke-width="3.5"/>
  <circle cx="{x0 + 40:.1f}" cy="{cy}" r="22" fill="#fff" stroke="{INK}" stroke-width="3"/>
  <g class="down"><path d="M{x0 + 40:.1f} {cy - 11}v20M{x0 + 31:.1f} {cy + 1}l9 9 9-9" stroke="{INK}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/></g>
  <text x="{x0 + 76:.1f}" y="{cy + 8}" font-size="23" font-weight="800" fill="{INK}">{e(text)}</text>
</svg>
"""
    write("hint.svg", svg)


intro()
hint()
for i, p in enumerate(ROWS):
    row(i, p)
for p in FOCUS:
    focus(p)
problems()
for p in BUILDS:
    build(p)
print("intro: intro.svg, hint.svg, " + ", ".join(f'row-{p["slug"]}.svg' for p in ROWS) + ", " + ", ".join(f'focus-{p["slug"]}.svg' for p in FOCUS) + ", problem-solving.svg, "
      + ", ".join(f'build-{p["slug"]}.svg' for p in BUILDS), file=sys.stderr)
