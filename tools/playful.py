"""Shared drawing helpers for the Playful cards: the card shell, pills, the arrow button, the T-rex and cacti,
and a set of little line icons. Colours come from the active theme and the Day / Night mode (banner.py).
"""
import html
import io
import base64
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sprites as S  # noqa: E402
import theme_colors  # noqa: E402
import banner  # noqa: E402

T = theme_colors.current()
ACCENT = T.accent
INK, TEXT, PAPER, PANEL, SKY = banner.INK, banner.TEXT, banner.PAPER, banner.PANEL, banner.SKY
ROUND = "'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif"
e = html.escape


def font_face(text=None):
    """The Baloo 2 @font-face. Given `text`, only the letters it uses are embedded (about 9 KB instead of 44 KB);
    that needs fontTools and brotli (`pip install fonttools brotli`), and falls back to the whole font without them."""
    if text is None:
        return banner.font_face()
    try:
        from fontTools import subset
    except ImportError:
        return banner.font_face()
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    try:
        font = subset.load_font(banner.FONT, opts)
    except ImportError:                              # no brotli: cannot read the woff2 font
        return banner.font_face()
    sub = subset.Subsetter(opts)
    sub.populate(text=text + " .,")
    sub.subset(font)
    buf = io.BytesIO()
    subset.save_font(font, buf, opts)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'Baloo 2';font-weight:400 800;src:url(data:font/woff2;base64,{data}) format('woff2')}}"


# ------------------------------------------------------------------ shared bits
def tw(text, size):
    return len(text) * size * 0.56



_ADVANCE = {}


def text_width(text, size, weight=800):
    """How wide `text` really is in Baloo 2 at this size and weight, read from the font's own letter widths
    (needs fontTools and brotli); without them it falls back to the rough estimate `tw`."""
    if weight not in _ADVANCE:
        try:
            from fontTools.ttLib import TTFont
            from fontTools.varLib import instancer
            font = instancer.instantiateVariableFont(TTFont(banner.FONT), {"wght": weight})
            cmap, hmtx, upm = font.getBestCmap(), font["hmtx"].metrics, font["head"].unitsPerEm
            _ADVANCE[weight] = {chr(c): hmtx[g][0] / upm for c, g in cmap.items()}
        except Exception:                            # fontTools or brotli missing
            _ADVANCE[weight] = None
    adv = _ADVANCE[weight]
    if adv is None:
        return tw(text, size)
    return sum(adv.get(ch, 0.55) for ch in text) * size


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


def style(extra="", text=None):
    """The card's <style>: the font (all of it, or only the letters in `text`) and the shared animations."""
    return f"""<style>
    {font_face(text)}
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

GITHUB = ("M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04"
          "-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 "
          "1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 "
          "0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02."
          "006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 "
          "4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 "
          "22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12")


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
    if kind == "laptop":                 # About Me
        return g(f'<rect x="4" y="4" width="16" height="11" rx="1.8" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                 f'<path d="M1.5 18.5h21l-1.5 2.5h-18z" fill="#fff" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
                 f'<circle cx="9.5" cy="9" r="1" fill="{INK}"/><circle cx="14.5" cy="9" r="1" fill="{INK}"/>'
                 f'<path d="M9.5 11.5q2.5 2 5 0" stroke="{INK}" stroke-width="1.4" fill="none" stroke-linecap="round"/>')
    if kind == "wrench":                 # Tech Stack
        return g(f'<path d="M14.5 3.2a5.2 5.2 0 0 0-5 6.8L3.4 16.1a2.2 2.2 0 0 0 3.1 3.1l6.1-6.1a5.2 5.2 0 0 0 6.8-5l-3 3-3.2-.8-.8-3.2z" '
                 f'fill="#fff" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/><circle cx="5.2" cy="17.6" r="1.1" fill="{INK}"/>')
    if kind == "chart":                  # GitHub Activity
        return g(f'<path d="M3 21h18" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>'
                 f'<rect x="4.5" y="12" width="4" height="8" rx="1" fill="#fff" stroke="{INK}" stroke-width="1.8"/>'
                 f'<rect x="10" y="7" width="4" height="13" rx="1" fill="#FFC83D" stroke="{INK}" stroke-width="1.8"/>'
                 f'<rect x="15.5" y="3" width="4" height="17" rx="1" fill="#fff" stroke="{INK}" stroke-width="1.8"/>')
    if kind == "code":                   # LeetCode
        return g(f'<rect x="2" y="4" width="20" height="16" rx="3" fill="#fff" stroke="{INK}" stroke-width="2"/>'
                 f'<path d="M9 9l-3 3 3 3M15 9l3 3-3 3M13 8l-2 8" stroke="{INK}" stroke-width="1.9" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    if kind == "chat":                   # Let's Connect
        return g(f'<path d="M3 4.5h12a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H8l-4 3v-3H3a2 2 0 0 1-2-2v-6a2 2 0 0 1 2-2z" fill="#fff" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
                 f'<path d="M19 9h2a2 2 0 0 1 2 2v5.5a2 2 0 0 1-2 2h-.5V21l-3.5-2.5H12a2 2 0 0 1-2-2V16" fill="#FFC83D" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
                 f'<circle cx="6" cy="9.5" r="1.1" fill="{INK}"/><circle cx="9" cy="9.5" r="1.1" fill="{INK}"/><circle cx="12" cy="9.5" r="1.1" fill="{INK}"/>')
    if kind == "camera":                 # Peek inside
        return g(f'<path d="M8 5.5l1.5-2.5h5L16 5.5h4a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7.5a2 2 0 0 1 2-2z" fill="#fff" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>'
                 f'<circle cx="12" cy="12.5" r="4.4" fill="{ACCENT}" stroke="{INK}" stroke-width="1.8"/><circle cx="13.3" cy="11.2" r="1.2" fill="#fff"/>'
                 f'<circle cx="18.5" cy="8.6" r="1" fill="{INK}"/>')
    if kind == "sparkle":
        return g(f'<path d="M12 2l2.4 7.6L22 12l-7.6 2.4L12 22l-2.4-7.6L2 12l7.6-2.4z" fill="#FFC83D" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
                 f'<path d="M19.5 2.5l.7 2 2 .7-2 .7-.7 2-.7-2-2-.7 2-.7z" fill="#fff" stroke="{INK}" stroke-width="1" stroke-linejoin="round"/>')
    if kind == "github":
        return g(f'<circle cx="12" cy="12.3" r="11.4" fill="#fff"/><path fill="{INK}" d="{GITHUB}"/>')
    if kind == "book":
        return g(f'<path d="M12 6c-2.5-1.8-5.5-2.2-9-1.6v14c3.5-.6 6.5-.2 9 1.6 2.5-1.8 5.5-2.2 9-1.6v-14c-3.5-.6-6.5-.2-9 1.6z" fill="#fff" stroke="{INK}" stroke-width="1.9" stroke-linejoin="round"/>'
                 f'<path d="M12 6v14" stroke="{INK}" stroke-width="1.6"/>')
    raise ValueError(kind)
