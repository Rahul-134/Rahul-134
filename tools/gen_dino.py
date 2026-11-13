"""Build the README banner (dino-banner.svg + dino-banner-mobile.svg, see banner.py) and dino/index.html
from sprites.py + index.template.html (themed).

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

# ------------------------------------------------------------------ README banner (desktop + mobile)
import banner  # noqa: E402
banner.write_all(out_dir, ACCENT)

# ------------------------------------------------------------------ game page
js = "  var PAL = " + json.dumps(S.PAL) + ";\n  var ART = {\n"
for k, rows in S.ART.items():
    js += f"    {k}: " + json.dumps(rows) + ",\n"
js += "  };"

here = os.path.dirname(os.path.abspath(__file__))
tpl = open(os.path.join(here, "index.template.html")).read()
assert "/*__SPRITES__*/" in tpl
def art_svg(rows, u=S.OBJ_U, pal=None):
    """A standalone inline <svg> of pixel art, used for the stickers and the logo on the game page."""
    rows = S.pad(rows)
    paths = S.path_by_colour(rows, u)
    pal = dict(S.PAL, **(pal or {}))
    order = ["O", "D", "Y", "L", "B", "E", "V", "M", "T", "K", "W", "g", "G", "h", "S", "P", "Q", "X", "Z", "N", "R", "I"]
    body = "".join(f'<path fill="{pal[c]}" d="{paths[c]}"/>' for c in order if c in paths)
    return (f'<svg viewBox="0 0 {len(rows[0]) * u} {len(rows) * u}" aria-hidden="true" focusable="false" '
            f'shape-rendering="crispEdges">{body}</svg>')


ART_HTML = {
    "{{ART_DINO}}": art_svg(S.pad(S.ART["dinoBody"], S.DINO_W) + S.pad(S.ART["legsA"], S.DINO_W), S.DINO_U),
    "{{ART_SAGUARO}}": art_svg(S.ART["saguaro"]),
    "{{ART_SMALL}}": art_svg(S.ART["small"]),
    "{{ART_BIRD}}": art_svg(S.ART["birdUp"]),
    "{{ART_DINO_B}}": art_svg(S.pad(S.ART["dinoBody"], S.DINO_W) + S.pad(S.ART["legsB"], S.DINO_W), S.DINO_U),
    "{{ART_DUCK_A}}": art_svg(S.pad(S.ART["duckBody"], S.DUCK_W) + S.pad(S.ART["duckLegsA"], S.DUCK_W), S.DINO_U),
    "{{ART_DUCK_B}}": art_svg(S.pad(S.ART["duckBody"], S.DUCK_W) + S.pad(S.ART["duckLegsB"], S.DUCK_W), S.DINO_U),
    "{{ART_BIRD_UP}}": art_svg(S.ART["birdUp"]),
    "{{ART_BIRD_DOWN}}": art_svg(S.pad(S.ART["birdDown"], S.width(S.ART["birdUp"]))),
}

html = tpl.replace("/*__SPRITES__*/", js).replace("{{ACCENT}}", T.accent).replace("{{ACCENT_RGB}}", T.rgb)
html = html.replace("{{DINO_U}}", str(S.DINO_U)).replace("{{OBJ_U}}", str(S.OBJ_U))
for key, markup in ART_HTML.items():
    html = html.replace(key, markup)
hook = (
    "  window.__dino = { get: function () { return { state: state, score: score, speed: speed, obstacles: obstacles.length,"
    " dinoY: dino.y, dinoX: dino.x, onGround: dino.onGround, ducking: ducking, raw: obstacles.map(function (o) { return { t: o.type, x: o.x, w: o.w, y: o.y, h: o.h }; }), parts: obstacles.map(function (o) { return o.parts ? o.parts.map(function (p) { return p.name; }).join('+') : o.type; }) }; },"
    " setScore: function (n) { distance = n / 0.025; },"
    " level: function () { return { level: level, fromLevel: fromLevel, fade: fade, banner: !!banner, spawnHold: spawnHold, cap: LEVELS[level].cap, name: LEVELS[level].name }; },"
    " kinds: function () { return obstacles.map(function (o) { return o.type + (o.type === 'meteor' ? (o.landed ? ':landed' : ':falling') : ''); }); },"
    " god: function (on) { if (on && !window.__realGameOver) { window.__realGameOver = gameOver; gameOver = function () { window.__hits = (window.__hits || 0) + 1; }; }"
    " else if (!on && window.__realGameOver) { gameOver = window.__realGameOver; window.__realGameOver = null; } } };"
    if test_hook else ""
)
html = html.replace("/*__TESTHOOK__*/", hook)
# Version the leaderboard scripts by their content, so a browser never pairs a new page with a cached old
# script (the night colours live in leaderboard.js).
import hashlib  # noqa: E402
for name in ("leaderboard.js", "leaderboard-config.js"):
    with open(os.path.join(here, "..", "dino", name), "rb") as f:
        ver = hashlib.sha1(f.read()).hexdigest()[:10]
    html = html.replace(f'<script src="{name}"></script>', f'<script src="{name}?v={ver}"></script>')
with open(os.path.join(out_dir, "dino", "index.html"), "w") as f:
    f.write(html)

print("banner: dino-banner.svg, dino-banner-mobile.svg; game page: dino/index.html", file=sys.stderr)
