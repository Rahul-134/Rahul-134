"""Single source of truth for the pixel art used by the banner SVG and the game.

Rows are left-aligned strings; shorter rows are right-padded with '.' to the sprite width.
Palette letters: Y body, D shade, L highlight, K dark, W white, G/g/h/S/P cactus colours, X bird.
"""

import theme_colors

_T = theme_colors.current()
PAL = {
    "Y": _T.accent, "D": _T.shade, "L": _T.light, "K": "#161616", "W": "#FFFFFF",
    "G": "#4DAE6C", "g": "#2F7A4D", "h": "#86D7A3", "S": "#D9F2E0", "P": "#F472B6",
    "X": "#D6D6D6",
}
PAL.update(_T.cactus)        # a theme may recolour the cacti (the green theme does)

ART = {
    # ---- dino, standing (24 wide) ----
    "dinoBody": [
        ".............LLLLLLLL",
        "............LYYYYYYYYY",
        "............YYYYYYYYYYY",
        "............YYWKYYYYYYY",
        "............YYYYYYYYYYY",
        "............YYYYYYYYYYY",
        "............YYYYYYYYYY",
        "............YYYYYKKKKK",
        "............YYYYYYYY",
        "...........DYYYYYYY",
        "..........DDYYYYYYY",
        ".........DDYYYYYYYYY",
        "D.......DDYYYYYYYYYY.YY",
        "DD.....DDYYYYYYYYYYYY.Y",
        "DDD...DDYYYYYYYYYYYY",
        ".DDDDDDYYYYYYYYYYYYY",
        "..DDDDDYYYYYYYYYYYYY",
        "...DDDDYYYYYYYYYYYY",
        "....DDDYYYYYYYYYYYY",
        ".....DDLYYYYYYYYYY",
        "......DDYYYYYYYYY",
        "......DDYYYYYYYY",
    ],
    "legsA": [
        ".......YYYYY..DDDDD",
        ".......YYY....DDD",
        ".......YYY....DD",
        ".......YYYY",
    ],
    "legsB": [
        ".......YYYYY..DDDDD",
        ".......YY.....DDDD",
        ".......Y......DDD",
        "..............DDDD",
    ],
    # ---- dino, ducking (28 wide) ----
    "duckBody": [
        "................LLLLLLLL",
        "...............LYYYYYYYYY",
        "...............YYYYYYYYYYY",
        "...............YYWKYYYYYYY",
        "...............YYYYYYYYYYY",
        "...............YYYYYYYYYY",
        "...............YYYYYKKKKK",
        "..DDDDDDDDDDDDYYYYYYYY",
        ".DDYYYYYYYYYYYYYYYYYYY",
        "DDYYYYYYYYYYYYYYYYYYY",
        "DDDYYYYYYYYYYYYYYYYY",
        ".DDDDYYYYYYYYYYYYYYY",
        "..DDDDDYYYYYYYYYYYY",
        "....DDDDYYYYYYYYYY",
    ],
    "duckLegsA": [
        "......YYYY...DDDD",
        "......YYY....DD",
        "......YYYY",
    ],
    "duckLegsB": [
        "......YYYY...DDDD",
        "......YY.....DDD",
        ".............DDDD",
    ],
    # ---- cacti ----
    "saguaro": [
        "......hGg",
        "......hGg",
        "......hGg.hGg",
        "......hGg.hGg",
        "......hGg.hGg",
        "......hGGGGGg",
        "..hGg.hGg",
        "..hGg.hGg",
        "..hGg.hGg",
        "..hGGGGGg",
        "......hGg",
        "......hGg",
        "......hSg",
        "......hGg",
    ],
    "small": [
        "...hGg",
        "...hGg",
        "hGg.hGg",
        "hGg.hGg",
        "hGGGGGg",
        "...hGg",
        "...hGg",
        "...hGg",
    ],
    "barrel": [
        "....PP",
        "...hGGGg",
        "..hGGGGGg",
        ".hGGSGGGGg",
        ".hGGGGGGGg",
        ".hGGGGSGGg",
        "..hGGGGGg",
    ],
    # ---- birds (single colour) ----
    "birdUp": [
        "..........X",
        ".........XX",
        "........XXX",
        ".......XXXX",
        "......XXXXXX",
        "XXXXXXXXXXXXXXX",
        "..XXXXXXXXXXXXXX",
        "....XXXXXXXXXX",
        "......XXXXX",
    ],
    "birdDown": [
        "",
        "",
        "..........X",
        "XXXXXXXXXXXXXXX",
        "..XXXXXXXXXXXXXX",
        "....XXXXXXXXXX",
        "......XXXXXXX",
        ".......XXXXX",
        ".........XX",
    ],
}


def width(rows):
    return max(len(r) for r in rows)


def pad(rows, w=None):
    w = w or width(rows)
    return [r.ljust(w, ".") for r in rows]


def full(name_body, name_legs):
    """Body + legs stacked, padded to one common width."""
    rows = ART[name_body] + ART[name_legs]
    return pad(rows)


def path_by_colour(rows, u):
    """Return {letter: svg path 'd'} with horizontal runs merged."""
    rows = pad(rows)
    out = {}
    for y, r in enumerate(rows):
        x = 0
        while x < len(r):
            c = r[x]
            if c == ".":
                x += 1
                continue
            s = x
            while x < len(r) and r[x] == c:
                x += 1
            out.setdefault(c, []).append(f"M{s*u} {y*u}h{(x-s)*u}v{u}h-{(x-s)*u}z")
    return {k: "".join(v) for k, v in out.items()}
