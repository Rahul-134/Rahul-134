"""Single source of truth for the pixel art used by the banner SVG and the game.

Rows are left-aligned strings; shorter rows are right-padded with '.' to the sprite width.
Palette letters: Y body, D shade, L highlight, O outline, B belly, M mouth, T tongue, K dark, W white,
G/g/h/S/P cactus colours, X bird. The dino is drawn on a finer grid (DINO_U px per cell) than the cacti and birds.
"""

import theme_colors

_T = theme_colors.current()
PAL = {
    "Y": _T.accent, "D": _T.shade, "L": _T.light, "K": "#161616", "W": "#FFFFFF",
    "G": "#4DAE6C", "g": "#2F7A4D", "h": "#86D7A3", "S": "#D9F2E0", "P": "#F472B6",
    "X": "#D6D6D6",
    # the cartoon dino: outline, cream belly, mouth, tongue
    "O": _T.outline, "B": "#F6E7B0", "M": "#8E2B3A", "T": "#F4758F",
}
PAL.update(_T.cactus)        # a theme may recolour the cacti (the green theme does)

DINO_U, DINO_W, DUCK_W = 2, 36, 40      # px per cell and grid widths of the standing and ducking dino

ART = {
    # ---- dino, standing (36 wide, 2px cells): a cute cartoon build ----
    "dinoBody": [
        "...............OOOYYYYYYYOOO........",
        ".............OOYYYYLLLLYYYYYOO......",
        "............OYYLLLLYYOOOYYYYYYO.....",
        "...........OYYLLYYYYOWWWOYYYYYYO....",
        "..........OYYYYYYYYOWWWKKOYYYYYYO...",
        "..........OYYYYYYYYWWWKWKKYYYYYYO...",
        ".........OYYYYYYYYYWWWKKKKYYYYYYYO..",
        ".........OYYYYYYYYYOWWKKKKYYYYYYYYO.",
        ".........OYYYYYYYYYYOWWKKYYYYYYYYYYO",
        ".........OYYYYYYYYYYYOOOYYYYYYYYYYYO",
        "..........OYYYYYYYYYYYYYYYYYYYYYYYYO",
        "..........OYYYYYYYYOMMWWWMWWWMWWWMMM",
        "...........OYYYYYYYOMMWWWMWWWMWWWMMM",
        ".OO.........OYYYYYYYOMMMMTTTTMMMMMMO",
        "OYYO.........OOYYYYYOOMTTTTTTTTMMMOO",
        "YYYYO......OOYYYYYYBBOOMMTTTTMMMMOOO",
        "YYYYO.....OYYYYYYYYBBBOOOMMMMMMOOOO.",
        "YYYYO....OYYYYYDYYYBBBBBBOOOOOOBBBO.",
        "YYYYO....OYYYYYYYYYBBBBBBBOOOBBBOO..",
        "YYYYO...OYYYYYYYYYBBBBBBBOYYYOOO....",
        "YYYYYO..OYYYDYYYYBBBBBBBOYYYYYOO....",
        "YYYYYO.OYYYYYYYYYBBBBBBBOYYYYWOO....",
        "YYYBYOOOYYYYYDYYBBBBBBBBBOYYYWO.....",
        "YYBBBYYYYYYYYYYYBBBBBBBBBBOOOO......",
        "YYBBBYYYYYYYYYYYBBBBBBBBBBYOO.......",
        "YYBBBBYYYYYDYYYYBBBBBBBBBBYO........",
        "OYYBBBBBYYYYYYYYBBBBBBBBBBO.........",
        "OYYBBBBBBYYYYYYYBBBBBBBBBBO.........",
        "OYYYBBBBBBYYYYYYYBBBBBBBBO..........",
        ".OYYYBBBOYYYYYYOYOYYYYYYOO..........",
        "..OYYYBBOYYYYYYOYOYYYYYYOO..........",
        "...OYYYYOYYYYYYOYOYYYYYYOO..........",
    ],
    "legsA": [
        "....OOOOOYYYYYYOYOYYYYYYYYOO........",
        ".......OOYYYYYYOOOYYYYYYYYYYO.......",
        ".......OOYYYYYYOOOYYYYYYYYWYOO......",
        ".......OOYYYYYYYYOOOYYYYYYOOO.......",
        ".......OOYYYYYYYYYYOOOOOOOOO........",
        ".......OOYYYYYYYYWYOOOOOOO..........",
        "........OOOYYYYYYOOO................",
    ],
    "legsB": [
        "....OOOOOYYYYYYYYOYYYYYYOO..........",
        ".......OOYYYYYYYYOYYYYYYOO..........",
        ".......OOYYYYYYYYOYYYYYYOO..........",
        "........OOOYYYYYYOYYYYYYYYOO........",
        ".........OOOOOOOOOYYYYYYYYYYO.......",
        "...........OOOOOOOYYYYYYYYWYOO......",
        ".................OOOYYYYYYOOO.......",
    ],
    # ---- dino, ducking (28 wide) ----
    "duckBody": [
        "..........................OOOOOOO.......",
        "........................OOYOOOLLYOO.....",
        ".......................OYLOWWWOYYYYO....",
        "......................OYYOWWWKKOYYYYO...",
        "OO..........OOOOOOOOOOYYYOWWKWKKYYYYYO..",
        "YYO.....OOOOYYYYYYYYYYYYYOWWKKKKYYYYYYO.",
        "YYYO...OYYYYYYYYYYYYYYYYYYWWWKKYYYYYYYYO",
        "YYYYOOOYYYYYYYYYYDYYYYYYYYYWWWYYYYYYYYYY",
        "YYYYYYYYYYYYYDYYYYYYYYYYYYYYYYYYYYYYYYYY",
        "YYYBYYYYYYYYYYYYYYYYYYYYYYYYYOMWWWMWWWMO",
        "OYYBYYYYYYYYYYYYYYYYYYYYYYYYYOMWWWTWWWMO",
        "OYYBYYYYYDYYYBBBBBBBBBBYYYYYYYOTTTTTTMOO",
        ".OYYYYYYYYBBBBBBBBBBBBBBBBYYYYBOTTTTMOO.",
        "..OYYYYYYBBBBBBBBBBBBBBBBBBYYBBBOOOOOBBO",
        "...OOYYYYBBBBBBBBBBBBBBBBBBOOOBBBBBBBBO.",
        ".....OOYYYBBBBBBBBBBBBBBBBO...OBBBBBBO..",
    ],
    "duckLegsA": [
        ".......OOYYYYBBBBBBBBBBYYOOO...OOOOOO...",
        ".......OOYYYYYOOOOOOYOYYYYYOO...........",
        ".......OOYYYYYOO..OOYYYYYYYYYO..........",
        ".......OOYYYYYOOO.OOYYYYYYYWYOO.........",
        ".......OOYOYYYYYOO.OOOYYYYYOOO..........",
        ".......OOYYYYYYYYYO.OOOOOOOOO...........",
        ".......OOYYYYYYYWYOO.OOOOOOO............",
        "........OOOYYYYYOOO.....................",
    ],
    "duckLegsB": [
        ".......OOYYYYBBBBBBBBBBYYOO....OOOOOO...",
        ".......OOYOYYYYYOOOOYYYYYOO.............",
        ".......OOYYYYYYYYYOOYYYYYOO.............",
        ".......OOYYYYYYYWYOOYYYYYOOO............",
        "........OOOYYYYYOOOOYOYYYYYOO...........",
        ".........OOOOOOOOOOOYYYYYYYYYO..........",
        "..........OOOOOOO.OOYYYYYYYWYOO.........",
        "...................OOOYYYYYOOO..........",
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
