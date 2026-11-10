"""Build the "Let's Connect" section art in the Playful style: connect/card.svg, connect/<link>.svg and
connect/wave.svg.

The card is a sky-blue scene (sun, clouds, sand, cacti) with the cartoon T-rex hopping and saying "hey!"; each
link is its own cream button card so the README can wrap it in a normal <a>; the footer is a strip of sand dunes
with a little dino walking across. Everything follows the active accent theme.

usage: python3 gen_connect.py OUT_DIR      # writes OUT_DIR/connect/*.svg
"""
import html
import os
import sys

sys.dont_write_bytecode = True
import sprites as S
import theme_colors
import banner

T = theme_colors.current()
ACCENT = T.accent
INK, TEXT, SKY, PAPER, LIVE_GREEN = banner.INK, banner.TEXT, banner.SKY, banner.PAPER, "#5BD68A"
ROUND = "'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif"
MONO = "'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"

out_dir = os.path.join(sys.argv[1], "connect")
os.makedirs(out_dir, exist_ok=True)
e = html.escape


def write(name, text):
    with open(os.path.join(out_dir, name), "w") as f:
        f.write(text)


def shapes(rows_, u=S.OBJ_U):
    paths = S.path_by_colour(rows_, u)
    order = ["O", "D", "Y", "L", "B", "E", "V", "M", "T", "K", "W", "g", "G", "h", "S", "P", "Q", "X", "Z", "N", "R", "I"]
    return "".join(f'<path fill="{S.PAL[c]}" d="{paths[c]}"/>' for c in order if c in paths)


def shell(w, h, fill, rx=24):
    return (f'<rect x="11" y="11" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{INK}"/>'
            f'<rect x="3" y="3" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="4"/>')


def tw_(text, size):
    return len(text) * size * 0.56


COMMON_CSS = """
    .pulse{animation:pulse 1.8s ease-in-out infinite}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
    .caret{animation:caret 1.1s steps(1,end) infinite}
    @keyframes caret{0%,49%{opacity:1}50%,100%{opacity:0}}"""

DINO_H = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U


def dino(legs="legsA"):
    body = shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)
    lg = shapes(S.pad(S.ART[legs], S.DINO_W), S.DINO_U)
    return f'{body}<g transform="translate(0,{len(S.ART["dinoBody"]) * S.DINO_U})">{lg}</g>'


# ------------------------------------------------------------------ hero card
W, H = 900, 350
GROUND = 296
BUB = GROUND - 238                                  # speech bubble follows the dino down


def hero():
    cactus, cactus_h = shapes(S.ART["small"]), len(S.ART["small"]) * S.OBJ_U
    sag, sag_h = shapes(S.ART["saguaro"]), len(S.ART["saguaro"]) * S.OBJ_U
    pill_txt = "OPEN TO CONVERSATIONS"
    pill_w = tw_(pill_txt, 12.5) + 1.5 * len(pill_txt) + 44
    dino_x = 850                                    # right edge; flipped so the dino faces the text
    mark_w = tw_("useful, together.", 40) + 28
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Let's connect</title>
  <desc id="d">Let's build something useful, together. Open to interesting projects and conversations about AI, backend engineering and building useful products. A cartoon T-rex hops in a sunny desert and says hey.</desc>
  <style>
    {banner.font_face()}
    text{{font-family:{ROUND}}}{COMMON_CSS}
    .hop{{animation:hop 3.6s cubic-bezier(.3,.6,.4,1) infinite}}
    @keyframes hop{{0%,6%{{transform:translateY(0)}}16%{{transform:translateY(-34px)}}28%,100%{{transform:translateY(0)}}}}
    .say{{transform-box:fill-box;transform-origin:85% 100%;animation:say 3.6s ease-out infinite}}
    @keyframes say{{0%,22%{{opacity:0;transform:scale(.6)}}30%{{opacity:1;transform:scale(1.06)}}34%{{transform:scale(1)}}78%{{opacity:1;transform:scale(1)}}90%,100%{{opacity:0;transform:scale(.9)}}}}
    .cl{{animation:drift 46s linear infinite}}
    @keyframes drift{{0%{{transform:translateX(880px);opacity:0}}12%{{opacity:1}}82%{{opacity:1}}100%{{transform:translateX(480px);opacity:0}}}}
    .rays{{animation:spin 60s linear infinite}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    @media (prefers-reduced-motion:reduce){{.pulse,.caret,.hop,.say,.cl,.rays{{animation:none}}.say{{opacity:1}}.cl{{transform:translateX(640px)}}}}
  </style>
  <defs>
    <clipPath id="card"><rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="24"/></clipPath>
    {banner.ground_tile(60)}
  </defs>
  {shell(W, H, SKY)}
  <g clip-path="url(#card)">
    {banner.stars(470, 14, 410, GROUND - 70, 12, seed=5, avoid=[(770, 10, 100, 100), (676, 90 + BUB, 116, 70)])}
    {banner.sun(818, 60, 0.95)}
    <g class="cl">{banner.cloud(0, 18, 0.8)}</g>
    <g class="cl" style="animation-duration:62s;animation-delay:-30s">{banner.cloud(0, 100, 0.62)}</g>
    <g transform="translate(0,{GROUND - 10})"><rect width="{W}" height="70" fill="url(#sand)"/></g>
    <g transform="translate(590,{GROUND - sag_h})">{sag}</g>
    <g transform="translate(642,{GROUND - cactus_h})">{cactus}</g>
    <g class="hop"><g transform="translate({dino_x},{GROUND - DINO_H}) scale(-1,1)">{dino()}</g></g>
    <g class="say">
      <rect x="682" y="{98 + BUB}" width="98" height="42" rx="16" fill="#fff" stroke="{INK}" stroke-width="3"/>
      <path d="M760 {138 + BUB} L782 {156 + BUB} L770 {136 + BUB} Z" fill="#fff" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
      <rect x="752" y="{133 + BUB}" width="18" height="6" fill="#fff"/>
      <text x="731" y="{126 + BUB}" text-anchor="middle" font-size="21" font-weight="800" fill="{INK}">hey!</text>
    </g>
  </g>

  <!-- status pill -->
  <rect x="38" y="34" width="{pill_w:.0f}" height="30" rx="15" fill="{ACCENT}" stroke="{INK}" stroke-width="2.5"/>
  <circle class="pulse" cx="57" cy="49" r="5.5" fill="#fff" stroke="{INK}" stroke-width="1.8"/>
  <text x="72" y="54" font-size="12.5" font-weight="800" fill="{INK}" letter-spacing="1.5">{pill_txt}</text>

  <!-- headline: the second line sits on a marker pill in the theme colour -->
  <text x="40" y="118" font-size="42" font-weight="800" fill="{TEXT}">Let's build something</text>
  <g transform="rotate(-2 {40 + mark_w / 2:.0f} 150)">
    <rect x="40" y="{126 + 5}" width="{mark_w:.0f}" height="50" rx="16" fill="{INK}" transform="translate(4,4)"/>
    <rect x="40" y="{126 + 5}" width="{mark_w:.0f}" height="50" rx="16" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>
    <text x="54" y="168" font-size="40" font-weight="800" fill="{INK}">useful, together.</text>
  </g>
  <text x="40" y="214" font-size="16" font-weight="600" fill="{TEXT}" fill-opacity=".75">Interesting projects and conversations about AI,</text>
  <text x="40" y="236" font-size="16" font-weight="600" fill="{TEXT}" fill-opacity=".75">backend engineering and building useful products.</text>

  <!-- prompt chip -->
  <rect x="40" y="254" width="168" height="30" rx="12" fill="{INK}"/>
  <text x="54" y="274" font-size="15" font-family="{MONO}"><tspan fill="{ACCENT}">$</tspan><tspan fill="#FFFFFF"> say hello</tspan><tspan class="caret" fill="{ACCENT}">_</tspan></text>
</svg>
"""
    write("card.svg", svg)


# ------------------------------------------------------------------ link buttons
BW, BH = 440, 116
CY = (3 + BH - 11) / 2                              # vertical middle of the card face (shell sits at y 3..BH-11)
LABEL_Y, SUB_Y = CY - 2, CY + 23                     # baselines; the two lines together are centred on CY

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
    cx, cy = 62, CY
    if kind == "in":
        return f'<text x="{cx}" y="{cy + 9}" text-anchor="middle" font-size="27" font-weight="800" fill="{INK}">in</text>'
    if kind == "github":
        return f'<g transform="translate({cx - 17},{cy - 17}) scale(1.42)"><path fill="{INK}" d="{GITHUB}"/></g>'
    if kind == "globe":
        return (f'<g transform="translate({cx - 17},{cy - 17}) scale(1.42)" fill="none" stroke="{INK}" stroke-width="1.9" stroke-linecap="round">'
                '<circle cx="12" cy="12" r="9.6"/><ellipse cx="12" cy="12" rx="4.2" ry="9.6"/><path d="M2.4 12h19.2M4 7h16M4 17h16"/></g>')
    # the dino game: the T-rex itself, peeking out of the icon
    k = 44 / DINO_H                                  # 44 px tall, inside the 66 px circle
    w, h = S.DINO_W * S.DINO_U * k, DINO_H * k
    return f'<g transform="translate({cx - w / 2 + 1:.1f},{cy - h / 2 + 1:.1f}) scale({k:.3f})">{dino()}</g>'


def link(i, p):
    primary = p.get("primary")
    sub_size = 13 if len(p["sub"]) > 30 else 15
    card_fill = ACCENT if primary else PAPER
    icon_fill = "#FFFFFF" if primary else (SKY if p["glyph"] == "play" else ACCENT)   # the dino needs sky behind it
    live = ""
    if p.get("live"):
        live = (f'<g transform="rotate(-8 340 26)"><rect x="300" y="15" width="74" height="26" rx="13" fill="{INK}"/>'
                f'<rect x="297" y="11" width="74" height="26" rx="13" fill="{LIVE_GREEN}" stroke="{INK}" stroke-width="2.4"/>'
                f'<circle class="pulse" cx="313" cy="24" r="4.4" fill="#fff" stroke="{INK}" stroke-width="1.5"/>'
                f'<text x="323" y="29" font-size="13.5" font-weight="800" fill="{INK}" letter-spacing="1.3">LIVE</text></g>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BW} {BH}" width="{BW}" height="{BH}" role="img" aria-labelledby="t">
  <title id="t">{e(p["desc"])}</title>
  <style>
    {banner.font_face()}
    text{{font-family:{ROUND}}}{COMMON_CSS}
    .nudge{{animation:nudge 2.4s ease-in-out infinite}}
    @keyframes nudge{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(3px,-3px)}}}}
    @media (prefers-reduced-motion:reduce){{.pulse,.nudge{{animation:none}}}}
  </style>
  {shell(BW, BH, card_fill, 22)}
  <circle cx="66" cy="{CY + 4}" r="33" fill="{INK}"/>
  <circle cx="62" cy="{CY}" r="33" fill="{icon_fill}" stroke="{INK}" stroke-width="3"/>
  {glyph(p["glyph"], primary)}
  <text x="114" y="{LABEL_Y}" font-size="28" font-weight="800" fill="{INK if primary else TEXT}">{e(p["label"])}</text>
  <text x="114" y="{SUB_Y}" font-size="{sub_size}" font-weight="600" fill="{INK if primary else TEXT}" fill-opacity=".68">{e(p["sub"])}</text>
  {live}
  <g class="nudge"><circle cx="{BW - 42}" cy="{CY}" r="17" fill="#fff" stroke="{INK}" stroke-width="2.6"/>
  <text x="{BW - 42}" y="{CY + 7}" text-anchor="middle" font-size="19" font-weight="800" fill="{INK}">↗</text></g>
</svg>
"""
    write(f'{p["slug"]}.svg', svg)


# ------------------------------------------------------------------ footer: dunes with a dino strolling across
def wave():
    WW, WH = 900, 120
    import math
    def top(x, base=72, amp=34, period=420, phase=1.2):
        return base - amp * (0.5 + 0.5 * math.sin(x / period * 2 * math.pi + phase))

    def dune(base, amp, period, phase):
        pts = " ".join(f"L{x} {base - amp * (0.5 + 0.5 * math.sin(x / period * 2 * math.pi + phase)):.1f}" for x in range(0, WW + 1, 6))
        return f"M0 {WH} {pts[1:] if pts.startswith('L') else pts} L{WW} {WH} Z"
    small, small_h = shapes(S.ART["small"]), len(S.ART["small"]) * S.OBJ_U
    sag, sag_h = shapes(S.ART["saguaro"]), len(S.ART["saguaro"]) * S.OBJ_U
    ground = 92
    dino_s = 0.75
    dh = DINO_H * dino_s
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WW} {WH}" width="{WW}" height="{WH}" role="img" aria-label="">
  <style>
    .walk{{animation:walk 22s linear infinite}}
    @keyframes walk{{from{{transform:translateX(-90px)}}to{{transform:translateX({WW + 20}px)}}}}
    .legA{{animation:legA .32s steps(1,end) infinite}}.legB{{animation:legB .32s steps(1,end) infinite}}
    @keyframes legA{{0%{{opacity:1}}50%{{opacity:0}}100%{{opacity:1}}}}
    @keyframes legB{{0%{{opacity:0}}50%{{opacity:1}}100%{{opacity:0}}}}
    @media (prefers-reduced-motion:reduce){{.walk,.legA,.legB{{animation:none}}.walk{{transform:translateX(420px)}}.legB{{opacity:0}}}}
  </style>
  <defs>{banner.ground_tile(30)}</defs>
  <path d="{dune(72, 34, 420, 1.2)}" fill="{banner.SAND_TOP}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>
  <g transform="translate(150,{max(top(x) for x in range(150, 191)) + 2 - sag_h:.1f})">{sag}</g>
  <g transform="translate(640,{max(top(x) for x in range(640, 663)) + 2 - small_h:.1f})">{small}</g>
  <g transform="translate(0,{ground - 10})"><rect width="{WW}" height="40" fill="url(#sand)"/></g>
  <g class="walk"><g transform="translate(0,{ground - dh:.1f}) scale({dino_s})">
    {shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)}
    <g transform="translate(0,{len(S.ART["dinoBody"]) * S.DINO_U})">
      <g class="legA">{shapes(S.pad(S.ART["legsA"], S.DINO_W), S.DINO_U)}</g>
      <g class="legB">{shapes(S.pad(S.ART["legsB"], S.DINO_W), S.DINO_U)}</g>
    </g>
  </g></g>
</svg>
"""
    write("wave.svg", svg)


hero()
for i, p in enumerate(LINKS):
    link(i, p)
wave()
print("connect: card.svg, " + ", ".join(p["slug"] + ".svg" for p in LINKS) + ", wave.svg", file=sys.stderr)
