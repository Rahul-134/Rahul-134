"""Single source of truth for the pixel art used by the banner SVG and the game.

Rows are left-aligned strings; shorter rows are right-padded with '.' to the sprite width.
Palette letters: Y body, D shade, L highlight, O outline, B belly, E belly stripe, V spike, M mouth, T tongue,
K dark, W white,
G/g/h/S/P cactus colours, X bird. The dino is drawn on a finer grid (DINO_U px per cell) than the cacti and birds.
"""

import theme_colors

_T = theme_colors.current()
PAL = {
    "Y": _T.accent, "D": _T.shade, "L": _T.light, "K": "#161616", "W": "#FFFFFF",
    "G": "#4DAE6C", "g": "#2F7A4D", "h": "#86D7A3", "S": "#D9F2E0", "P": "#F472B6",
    "X": "#D6D6D6",
    # the cartoon T-rex: outline, belly, belly stripes, back spikes, mouth, tongue
    "O": _T.outline, "B": _T.belly, "E": _T.stripe, "V": _T.spike, "M": "#8E2B3A", "T": "#F4758F",
}
PAL.update(_T.cactus)        # a theme may recolour the cacti (the green theme does)

DINO_U, DINO_W, DUCK_W = 2, 36, 40      # px per cell and grid widths of the standing and ducking dino

ART = {
    # ---- dino, standing (36 wide, 2px cells): a cartoon T-rex, side view ----
    "dinoBody": [
        "....................................",
        ".......................OO...........",
        "......................OVVOOO........",
        ".....................OOVYYYYOO......",
        "....................OVYYOOOOOYO.....",
        "...................OVYYYYWWWYYYOO...",
        "...................OYYYYWWKKYYYYYOO.",
        "..................OVYYYYYWKKYYYYYYYO",
        ".................OVVYYYYYYWYYYYYYOYY",
        ".................OVYYYYYYYYYYYYYYYYY",
        "................OVOYYYYYYYYYYYYYYYYY",
        "...............OVVVYYYYYMMMWMMWMMWMO",
        "..............OOVVYYYYYYYMMMMMYYYYO.",
        ".............OVVOOYYYYYYYBBYYYYYYYYO",
        ".............OVVODYYYYYYEEEEYYYYYYO.",
        "...........OOOYYYYYYYYYYBBBOOOOOOO..",
        "..........OVVYDYYYBBBBYBBBBYO.......",
        "........OOOVYDYYYYEEEEEEEEEO........",
        ".......OVVOYYYYYYYBBBBBBBBO.........",
        ".....OOOVYYYYYYYYYBBBBBBYYO.........",
        "OOOOOVYYYYYYYYYYDYEEEEEYYYO.........",
        "YYYYYYYYYYDDYYYYYYBBBBBBYYYO........",
        "OBYYYYYYYYYYYYYYYYYBBBBBOYYWO.......",
        ".OBBBBBBBBBBYYYYYYYEEEEEOOWO........",
        "..OOOBBBBBBBYYYYYYYYBBBO..O.........",
        ".....OOOOOOYYYYYYYYYYDDDO...........",
        "..........OYYYYYYYYYDDDDO...........",
        "...........OYYYYYYYDDDDDO...........",
        "...........OYYYYYYYDDDDO............",
    ],
    "legsA": [
        "............OOYYYYOODDDO............",
        ".............OYYYYO.ODDDO...........",
        ".............OYYYYO.ODDDDOO.........",
        "..............OYYYO.ODDDDDDO........",
        "..............OYYYO..ODDDDO.........",
        "..............OYYYYOO.OOOO..........",
        "..............OYYYYYYO..............",
        "..............OYYYYYWWO.............",
        "...............OOYYYYO..............",
        ".................OOOO...............",
    ],
    "legsB": [
        "............OYYYYYOODDDO............",
        "...........OYYYYOO.ODDDO............",
        "...........OYYYOOO.ODDDO............",
        "...........OYYYYYYOODDDDO...........",
        "............OYYYYWO.ODDDO...........",
        ".............OOOOO..ODDDOO..........",
        "....................ODDDDDO.........",
        "....................ODDDDDDO........",
        ".....................ODDDDO.........",
        "......................OOOO..........",
    ],
    # ---- dino, ducking (28 wide) ----
    "duckBody": [
        "........................................",
        ".............................OO.........",
        "..........................OOOVVO........",
        "................O..OO.OOOOVVVVVVOOO.....",
        "............OO.OVOOVVOVVVVVVYOOOOYYO....",
        "......O..OOOVVOVVVOVVOVVVOVYYYWWWYYYO...",
        "..OO.OVOOVVOVVYYYYYYYYOOOOYYYYWKKYYYYOO.",
        "OOVVOVVOOYYYYYDYYYYYYYDYYYYYYYWWWYYYYYYO",
        "YYYYYYYYYYYDYYYYYYDYYYYYYYYYYYYYYYYYYOYO",
        "OBYYYYYYDYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYO",
        ".OBBBYYYYYYYYYYYYYYYYYYYYYYYYYMMMWMMWMMO",
        "..OOBBBBBBBBYYYYYYYYYYYYYYYYYYYYYYYYYYYO",
        "....OOOBBBBBYYYYYYEBBEBBEBBEBYOYYYYYYYYO",
        ".......OYYYYYYYYYYEBBEBBEBBEOO.OOOOOOOO.",
        "........OOYYYYYYYYEBBEBOOOOO............",
        "..........OYYYYYYYOODDDO................",
        "...........OYYYYYO.ODDDO................",
    ],
    "duckLegsA": [
        "............OYYYYO..ODDDO...............",
        ".............OYYYO..ODDDOOO.............",
        ".............OYYYOO.ODDDDDDO............",
        ".............OYYYYYOOODDDDDO............",
        ".............OYYYYYWYOOOOOO.............",
        "..............OYYYYYO...................",
        "...............OOOOO....................",
    ],
    "duckLegsB": [
        "...........OYYYOO..ODDDO................",
        "...........OYYYOO..ODDDO................",
        "...........OYYYYWO.ODDDOOO..............",
        "...........OYYYYYO..ODDDDDO.............",
        "............OOOOO...ODDDDDDO............",
        ".....................ODDDDO.............",
        "......................OOOO..............",
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
