"""The README banner in the Playful style: Dino Run Season 2's four worlds in turn (desert, canyon, volcano and the
starry sky), each with its boss; the T-rex jumps the boss's attack and beats it with fire breath (tools/worlds.py
draws and times all of that). Over it: the sun or moon, drifting clouds, the name and the role pill. Two layouts:
a wide one for desktop and a taller one with bigger type and characters for phones (the README picks one with a
<picture> media query).

worlds.py checks the jump: the dino must be above each attack for the whole time it overlaps it, and on phones the
top of the jump must stay below the text.
"""
import base64
import math
import os

import sprites as S
import theme_colors
import worlds

# Colour roles shared by every card. RAHUL_MODE=night switches them to the Night look (set by tools/theme.py,
# which draws every card twice: the day files, and the night files under night/).
NIGHT = os.environ.get("RAHUL_MODE") == "night"
if NIGHT:
    INK = "#0C0B16"          # outlines and offset shadows; also text on bright fills (accent, sun yellow)
    TEXT = "#F4ECDD"         # text on the card, its panels and the sky
    PAPER = "#2C2A45"        # the card
    PANEL = "#3A3758"        # white tiles and panels inside a card
    TRACK = "#24223A"        # empty progress tracks, empty calendar cells
    SKY = "#2B3866"
    SAND, SAND_TOP, SAND_LOW, PEBBLE, TUFT, FLOWER = "#B3925F", "#C5A673", "#987A4D", "#7E6240", "#5E9A57", "#E46AA6"
    CLOUD, CLOUD_LOW = "#C7CFE6", "#A3AED0"
else:
    INK = "#2B1A12"
    TEXT = INK
    PAPER = "#FFFDF7"
    PANEL = "#FFFFFF"
    TRACK = "#F1E7D0"
    SKY = "#BFE7F7"
    SAND, SAND_TOP, SAND_LOW, PEBBLE, TUFT, FLOWER = "#F2D9A6", "#F9E8C4", "#E5C48C", "#CFA86E", "#7BC86C", "#F472B6"
    CLOUD, CLOUD_LOW = "#FFFFFF", "#DCEBF5"
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(HERE), "dino", "fonts", "baloo-2-latin-wght-normal.woff2")
ORDER = ["O", "D", "Y", "L", "B", "E", "V", "M", "T", "K", "W", "g", "G", "h", "S", "P", "Q", "X", "Z", "N", "R", "I"]

LAYOUTS = {
    # name: canvas, ground line, sprite scale, dino x, where the boss stands and its size, backdrop size, world label, text
    "desktop": dict(W=1000, H=290, ground=232, scale=1.0, dino_x=96, boss_x=880, boss_scale=0.85, back_scale=0.55, label=(24, 247), fly=95, fire_min_y=168,
                    title=[("Hey I am Rahul Lumbhani", 500, 98, 46)], pill=(500, 146, 21), hint=(500, 270, 13),
                    hint_text="CLICK TO PLAY  ·  SPACE / TAP TO JUMP", sun=(92, 70, 1.0), hi=(960, 44, 16),
                    clouds=[(70, 0.9, 36, 0), (300, 0.75, 46, -14), (190, 0.65, 40, -27)], text_bottom=None),   # dino is left of the title
    "mobile": dict(W=600, H=530, ground=446, scale=1.3, dino_x=40, boss_x=470, boss_scale=1.1, back_scale=0.8, label=(22, 462), fly=140,
                   title=[("Hey I am", 300, 100, 54), ("Rahul Lumbhani", 300, 156, 54)], pill=(300, 210, 24),
                   hint=(300, 508, 16), hint_text="TAP TO PLAY", sun=(66, 58, 1.0), hi=(560, 42, 18),
                   clouds=[(64, 0.85, 30, 0), (250, 0.7, 40, -12), (330, 0.6, 36, -26)], text_bottom=228),
}


def shapes(rows, u):
    paths = S.path_by_colour(rows, u)
    return "".join(f'<path fill="{S.PAL[c]}" d="{paths[c]}"/>' for c in ORDER if c in paths)


def font_face():
    with open(FONT, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return f"@font-face{{font-family:'Baloo 2';font-weight:400 800;src:url(data:font/woff2;base64,{data}) format('woff2')}}"


def cloud(x, y, s):
    puffs = '<circle cx="26" cy="29" r="12"/><circle cx="44" cy="21" r="16"/><circle cx="64" cy="25" r="13"/><circle cx="80" cy="32" r="9"/><rect x="14" y="29" width="76" height="14" rx="7"/>'
    return (f'<g transform="translate({x},{y}) scale({s})">'
            f'<g fill="{INK}" stroke="{INK}" stroke-width="6" stroke-linejoin="round">{puffs}</g><g fill="{CLOUD}">{puffs}</g>'
            f'<rect x="14" y="37" width="76" height="6" rx="3" fill="{CLOUD_LOW}"/><ellipse cx="40" cy="14" rx="7" ry="3.2" fill="#fff" opacity="{.55 if NIGHT else 1}"/></g>')


def sun(x, y, s):
    if NIGHT:                                        # the night sky gets a calm full moon in the same spot
        return (f'<g transform="translate({x},{y}) scale({s})"><circle r="30" fill="#FFF3C4" opacity=".12"/><circle r="25" fill="#FFF3C4" opacity=".15"/>'
                f'<circle r="20" fill="#FBEFC9" stroke="{INK}" stroke-width="3"/><circle cx="-6" cy="-5" r="4.2" fill="#E9DAAA"/>'
                f'<circle cx="7" cy="5" r="3" fill="#E9DAAA"/><circle cx="-3" cy="9" r="2.2" fill="#E9DAAA"/>'
                f'<path d="M-13 -8 A14.5 14.5 0 0 1 -4 -14.5" stroke="#fff" stroke-width="3" fill="none" stroke-linecap="round"/></g>')
    rays = "".join(f'<line x1="0" y1="-26.5" x2="0" y2="-32.5" transform="rotate({i * 30})"/>' for i in range(12))
    return (f'<g transform="translate({x},{y}) scale({s})"><circle r="28" fill="#FFC83D" opacity=".22"/>'
            f'<g class="rays" stroke="#FFB547" stroke-width="4.6" stroke-linecap="round">{rays}</g>'
            f'<circle r="21.5" fill="#FFC83D" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M-14 -9 A15.5 15.5 0 0 1 -3 -16.5" stroke="#FFE7A0" stroke-width="3.6" fill="none" stroke-linecap="round"/></g>')


def stars(x0, y0, w, h, n=14, seed=7, avoid=()):
    """Night only: a fixed scatter of little twinkling sparkles in the box (x0, y0, w, h); empty by day.
    `avoid` is a list of (x, y, w, h) boxes to keep clear (text, the moon)."""
    if not NIGHT:
        return ""
    out, k = [], seed
    def rand():
        nonlocal k
        k = (k * 16807) % 2147483647
        return k / 2147483647
    tries = 0
    while len(out) < n and tries < n * 20:
        tries += 1
        x, y, r = x0 + rand() * w, y0 + rand() * h, 1.6 + rand() * 2.4
        if any(ax - 6 <= x <= ax + aw + 6 and ay - 6 <= y <= ay + ah + 6 for ax, ay, aw, ah in avoid):
            continue
        d = (f"M{x:.1f} {y - r * 1.8:.1f}L{x + r * .5:.1f} {y - r * .5:.1f}L{x + r * 1.8:.1f} {y:.1f}L{x + r * .5:.1f} {y + r * .5:.1f}"
             f"L{x:.1f} {y + r * 1.8:.1f}L{x - r * .5:.1f} {y + r * .5:.1f}L{x - r * 1.8:.1f} {y:.1f}L{x - r * .5:.1f} {y - r * .5:.1f}Z")
        out.append(f'<path class="tw" style="animation-delay:{-rand() * 3:.2f}s" d="{d}" fill="{"#FFF3C4" if rand() > .6 else "#E8E2F2"}"/>')
    return ('<style>.tw{transform-box:fill-box;transform-origin:center;animation:tw 2.8s ease-in-out infinite}'
            '@keyframes tw{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.7)}}'
            '@media (prefers-reduced-motion:reduce){.tw{animation:none}}</style>' + "".join(out))


def ground_tile(h):
    """A 200-wide sand tile (matches the game's Playful ground), tufts poking 10 units above the line.

    The sand runs on 40 units below `h`, and the tile's last 4 units are left empty. When a browser scales the
    image it blends a sliver of a tile's bottom row into the top of the strip; with sand there, that drew a thin
    sand-coloured line across the sky above the ground on every card."""
    pts = " ".join(f"L{x} {10 + h * 0.62 + 3.5 * math.sin(x / 200 * 4 * math.pi):.1f}" for x in range(0, 201, 4))
    deep = h + 40                                    # sand below the line (strips can be up to h + 50 tall)
    pebbles = "".join(
        f'<ellipse cx="{x}" cy="{10 + y}" rx="{rx}" ry="{ry}" fill="{PEBBLE}" stroke="rgba(43,26,18,.55)" stroke-width="1.3"/>'
        f'<ellipse cx="{x - rx * .3:.1f}" cy="{10 + y - ry * .35:.1f}" rx="{rx * .35:.1f}" ry="{ry * .3:.1f}" fill="#fff" opacity=".55"/>'
        for x, y, rx, ry in [(34, 20, 5, 3.1), (118, 28, 3.8, 2.4), (166, 15, 3.1, 2.0), (86, h * 0.8, 3.6, 2.1)])

    def tuft(x, flower):
        d = f"M{x - 5} 11 L{x - 6} 5 L{x - 2.5} 10 L{x} 2 L{x + 2.5} 10 L{x + 6} 4 L{x + 5} 11 Z"
        s = f'<path d="{d}" fill="{TUFT}" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
        return s + (f'<circle cx="{x}" cy="1.6" r="2.2" fill="{FLOWER}" stroke="{INK}" stroke-width="1.1"/>' if flower else "")
    return (f'<pattern id="sand" width="200" height="{deep + 14}" patternUnits="userSpaceOnUse">'
            f'<rect y="10" width="200" height="{deep}" fill="{SAND}"/><rect y="13" width="200" height="7" fill="{SAND_TOP}"/>'
            f'<path d="M0 {deep + 10} {pts[1:] if pts.startswith("L") else pts} L200 {deep + 10} Z" fill="{SAND_LOW}"/>'
            f'{pebbles}<rect y="10" width="200" height="3.5" fill="{INK}"/>{tuft(72, False)}{tuft(150, True)}</pattern>')


def build(name, accent):
    L = LAYOUTS[name]
    W, H, G, sc = L["W"], L["H"], L["ground"], L["scale"]
    tour = worlds.Tour(W, H, G, sc, L["dino_x"], L["boss_x"], L["boss_scale"], L["back_scale"], L["label"],
                       fly_y=G - L["fly"], fire_min_y=L.get("fire_min_y"), max_apex=None if L["text_bottom"] is None else G - (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U * sc - L["text_bottom"] - 8)
    mode = "night" if NIGHT else "day"

    clouds = "".join(f'<g class="cl" style="animation-duration:{70 + i * 18}s;animation-delay:{d}s">{cloud(0, y, s)}</g>'
                     for i, (y, s, _, d) in enumerate(L["clouds"]))
    title = "".join(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="800" fill="{TEXT}">{tx}</text>'
                    for tx, x, y, fs in L["title"])
    px, py, pf = L["pill"]
    pill_txt = "AI/ML Engineer · GenAI Enthusiast"
    pw = len(pill_txt) * pf * 0.52 + 40
    pill = (f'<rect x="{px - pw / 2 + 4:.0f}" y="{py - pf * 1.15 + 5:.0f}" width="{pw:.0f}" height="{pf * 1.75:.0f}" rx="{pf * .87:.0f}" fill="{INK}"/>'
            f'<rect x="{px - pw / 2:.0f}" y="{py - pf * 1.15:.0f}" width="{pw:.0f}" height="{pf * 1.75:.0f}" rx="{pf * .87:.0f}" fill="{accent}" stroke="{INK}" stroke-width="3"/>'
            f'<text x="{px}" y="{py + pf * 0.2:.0f}" text-anchor="middle" font-size="{pf}" font-weight="800" fill="{INK}">{pill_txt}</text>')
    hx, hy, hf = L["hint"]
    sx, sy, ss = L["sun"]
    ix, iy, iff = L["hi"]
    hint = (f'<text x="{hx}" y="{hy}" text-anchor="middle" font-size="{hf}" font-weight="800" fill="{INK}" fill-opacity="{.7 if NIGHT else .55}" '
            f'letter-spacing="2">{L["hint_text"]}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Hey I am Rahul Lumbhani — AI/ML Engineer · GenAI Enthusiast</title>
  <desc id="d">Dino Run Season 2: a cartoon T-rex runs through four worlds (desert, canyon, volcano and a starry sky), jumps the bosses' attacks and beats each boss with fire breath. Click to play the full game.</desc>
  <style>
    {font_face()}
    text{{font-family:'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif}}
    .cl{{animation:drift 80s linear infinite}}
    .rays{{animation:spin 60s linear infinite}}
    @keyframes drift{{from{{transform:translateX({W + 40}px)}}to{{transform:translateX(-140px)}}}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    @media (prefers-reduced-motion:reduce){{.cl,.rays{{animation:none}}.cl{{transform:translateX({W * 0.4:.0f}px)}}}}
    {tour.css(modes=[(mode, "")])}
  </style>
  <defs>
    <clipPath id="card"><rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="22"/></clipPath>
    {tour.defs()}
  </defs>

  <rect x="11" y="11" width="{W - 14}" height="{H - 14}" rx="22" fill="{INK}"/>
  <g clip-path="url(#card)">
    <!-- the four worlds of Season 2, in turn: sky, backdrop, ground -->
    {tour.back()}
    {stars(20, 16, W - 40, G - 60, 18, avoid=[(sx - 40, sy - 40, 80, 80)] + [(x - len(tx) * fs * .29, y - fs, len(tx) * fs * .58, fs * 1.2) for tx, x, y, fs in L["title"]] + [(px - pw / 2, py - pf * 1.2, pw, pf * 1.9), (ix - 120, iy - iff, 125, iff + 4)])}
    {sun(sx, sy, ss)}
    {clouds}
    <text x="{ix}" y="{iy}" text-anchor="end" font-size="{iff}" font-weight="700" fill="{TEXT}" fill-opacity=".5" letter-spacing="1.5">HI 00134</text>
    {title}
    {pill}
    <!-- each world's boss, its attack, the T-rex and its fire -->
    {tour.front(hint=hint)}
  </g>
  <rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="22" fill="none" stroke="{INK}" stroke-width="4"/>
</svg>
'''


def write_all(out_dir, accent):
    for name, fn in (("desktop", "dino-banner.svg"), ("mobile", "dino-banner-mobile.svg")):
        with open(os.path.join(out_dir, fn), "w") as f:
            f.write(build(name, accent))
