#!/usr/bin/env python3
"""Build the Tech Stack card in the Playful style: tech-stack.svg.

    python3 tools/gen_stack.py OUT_DIR      # writes OUT_DIR/tech-stack.svg

Each technology is a sticker tile in its brand colour. The logos are the simple-icons paths kept in
tools/stack_icons.json (CC0). To add one, copy its slug, title, hex and path from simpleicons.org
into that file and add the slug to GROUPS below. Colours of the card follow the `about` section theme.
"""
import html
import json
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
INK, TEXT, PAPER, PANEL = banner.INK, banner.TEXT, banner.PAPER, banner.PANEL
ROUND = "'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif"
e = html.escape
W = 900

with open(os.path.join(HERE, "stack_icons.json")) as f:
    ICONS = json.load(f)

# (slug, label, tile colour override); "vscode" has no simple-icons logo, so it gets a code glyph
GROUPS = [
    ("LANGUAGES", [("python", "Python", None), ("openjdk", "Java", "#E76F00"), ("javascript", "JavaScript", None),
                   ("html5", "HTML", None), ("css3", "CSS", None)]),
    ("DATABASES", [("sqlite", "SQLite", None), ("mysql", "MySQL", None), ("postgresql", "PostgreSQL", None),
                   ("mongodb", "MongoDB", None)]),
    ("FRAMEWORKS & LIBRARIES", [("fastapi", "FastAPI", None), ("react", "React", None), ("nodedotjs", "Node.js", None),
                                ("express", "Express", None), ("django", "Django", None), ("tailwindcss", "Tailwind", None),
                                ("bootstrap", "Bootstrap", None)]),
    ("TOOLS & PLATFORMS", [("git", "Git", None), ("github", "GitHub", None), ("docker", "Docker", None),
                           ("vercel", "Vercel", None), ("vscode", "VS Code", "#007ACC"), ("intellijidea", "IntelliJ", None),
                           ("pycharm", "PyCharm", None), ("figma", "Figma", None)]),
]
TILE, STEP, PAD = 68, 84, 18          # sticker size, distance between stickers, panel padding
TOP = 60                              # tiles start this far below the panel top
PANEL_H = TOP + TILE + 22 + 16


def tw(text, size):
    return len(text) * size * 0.56


def lum(hex_):
    r, g, b = (int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def pill(x, y, text, fill=ACCENT, size=12, h=28):
    w = tw(text, size) + 1.5 * len(text) + 28
    return (f'<rect x="{x + 3:.1f}" y="{y + 3}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{INK}"/>'
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>'
            f'<text x="{x + 14:.1f}" y="{y + h / 2 + size * 0.36:.1f}" font-size="{size}" font-weight="800" fill="{INK}" letter-spacing="1.5">{e(text)}</text>')


def panel(x, y, w, h):
    return (f'<rect x="{x + 4}" y="{y + 4}" width="{w}" height="{h}" rx="18" fill="{INK}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{PANEL}" stroke="{INK}" stroke-width="3"/>')


def sticker(i, x, y, slug, label, colour):
    fill = colour or ICONS[slug]["hex"]
    glyph_fill = INK if lum(fill) > 0.62 else "#FFFFFF"
    k = 36 / 24
    gx, gy = x + (TILE - 36) / 2, y + (TILE - 36) / 2
    if slug == "vscode":
        logo = (f'<text x="{x + TILE / 2}" y="{y + TILE / 2 + 9}" text-anchor="middle" font-size="27" font-weight="800" '
                f'fill="{glyph_fill}" font-family="{ROUND}">&lt;/&gt;</text>')
    else:
        logo = f'<path transform="translate({gx:.1f},{gy:.1f}) scale({k})" fill="{glyph_fill}" d="{ICONS[slug]["path"]}"/>'
    return (f'<g class="pop" style="animation-delay:{-i * 0.21:.2f}s">'
            f'<rect x="{x + 4}" y="{y + 4}" width="{TILE}" height="{TILE}" rx="18" fill="{INK}"/>'
            f'<rect x="{x}" y="{y}" width="{TILE}" height="{TILE}" rx="18" fill="{fill}" stroke="{INK}" stroke-width="3"/>'
            f'<rect x="{x + 9}" y="{y + 7}" width="{TILE - 30}" height="5" rx="2.5" fill="#FFFFFF" opacity=".35"/>'
            f'{logo}</g>'
            f'<text x="{x + TILE / 2 + 2}" y="{y + TILE + 22}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{TEXT}" fill-opacity=".8">{e(label)}</text>')


DINO_H = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U


def dino(x, y_bottom, k):
    body = banner.shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)
    legs = banner.shapes(S.pad(S.ART["legsA"], S.DINO_W), S.DINO_U)
    w = S.DINO_W * S.DINO_U
    return (f'<g transform="translate({x},{y_bottom - DINO_H * k:.1f}) scale({k}) translate({w},0) scale(-1,1)">'
            f'{body}<g transform="translate(0,{len(S.ART["dinoBody"]) * S.DINO_U})">{legs}</g></g>')


def cactus(x, y_bottom, k, kind):
    rows = S.ART[kind]
    return (f'<g transform="translate({x},{y_bottom - len(rows) * S.OBJ_U * k:.1f}) scale({k})">'
            f'{banner.shapes(rows, S.OBJ_U)}</g>')


def sand(x, y, w):
    """A little patch of sand for the dino and cacti to stand on (y is its top edge)."""
    return (f'<rect x="{x}" y="{y - 2}" width="{w}" height="12" rx="6" fill="{banner.SAND}" stroke="{INK}" stroke-width="2.5"/>'
            f'<ellipse cx="{x + w * 0.3:.1f}" cy="{y + 4}" rx="3" ry="1.8" fill="#CFA86E"/><ellipse cx="{x + w * 0.72:.1f}" cy="{y + 5}" rx="2.4" ry="1.5" fill="#CFA86E"/>')


def build():
    X0, Y0, GAP = 36, 112, 18
    inner = W - 2 * X0 - 4
    body, i = [], 0
    rows = [[GROUPS[0], GROUPS[1]], [GROUPS[2]], [GROUPS[3]]]
    y = Y0
    for r, row in enumerate(rows):
        x = X0
        for g, (title, items) in enumerate(row):
            natural = 2 * PAD + len(items) * STEP - (STEP - TILE)
            w = natural if len(row) > 1 and g == 0 else (X0 + inner - x)   # the last panel in a row fills it
            body.append(panel(x, y, w, PANEL_H) + pill(x + PAD, y + 16, title))
            for j, (slug, label, colour) in enumerate(items):
                body.append(sticker(i, x + PAD + j * STEP, y + TOP, slug, label, colour))
                i += 1
            ground = y + PANEL_H - 22
            if r == 1:                                  # the T-rex hangs out next to the frameworks
                body.append(sand(x + w - 196, ground, 168))
                body.append(cactus(x + w - 176, ground, 1.0, "small"))
                body.append(f'<g class="bob">{dino(x + w - 118, ground, 0.9)}</g>')
            if r == 2:                                  # and a couple of cacti grow by the tools
                body.append(sand(x + w - 140, ground, 112))
                body.append(cactus(x + w - 124, ground, 1.0, "saguaro"))
                body.append(cactus(x + w - 70, ground, 1.0, "small"))
            x += w + GAP
        y += PANEL_H + GAP
    H = y - GAP + 4 + 22 + 11
    names = "; ".join(f"{t.title()}: " + ", ".join(lbl for _, lbl, _ in items) for t, items in GROUPS)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Tech stack</title>
  <desc id="d">{e(names)}.</desc>
  <style>
    {banner.font_face()}
    text{{font-family:{ROUND}}}
    .pop{{animation:pop 3.4s ease-in-out infinite}}
    @keyframes pop{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
    .bob{{animation:bob 2.8s ease-in-out infinite}}
    @keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
    @media (prefers-reduced-motion:reduce){{.pop,.bob{{animation:none}}}}
  </style>
  <rect x="11" y="11" width="{W - 14}" height="{H - 14}" rx="24" fill="{INK}"/>
  <rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="24" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>
  {pill(36, 26, "TECH STACK", size=12.5, h=30)}
  <text x="36" y="92" font-size="32" font-weight="800" fill="{TEXT}">Tools I build with</text>
  {"".join(body)}
</svg>
"""


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    with open(os.path.join(sys.argv[1], "tech-stack.svg"), "w") as f:
        f.write(build())
    print("stack: tech-stack.svg", file=sys.stderr)


if __name__ == "__main__":
    main()
