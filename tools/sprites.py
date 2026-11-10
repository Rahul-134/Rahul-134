"""Single source of truth for the pixel art used by the banner SVG and the game.

Rows are left-aligned strings; shorter rows are right-padded with '.' to the sprite width.
Palette letters: Y body, D shade, L highlight, O outline, B belly, E belly stripe, V spike, M mouth, T tongue,
K dark, W white,
G/g/h/S/P cactus colours, X/Z/N/R/I bird, Q cactus outline. The dino is drawn on a finer grid (DINO_U px per cell) than the cacti and birds.
"""

import theme_colors

_T = theme_colors.current()
PAL = {
    "Y": _T.accent, "D": _T.shade, "L": _T.light, "K": "#161616", "W": "#FFFFFF",
    "G": "#4DAE6C", "g": "#2F7A4D", "h": "#86D7A3", "S": "#D9F2E0", "P": "#F472B6",
    # the cartoon bird: body, wing, beak, outline, belly
    "X": "#B79CF2", "Z": "#8E6FD8", "N": "#FF9F43", "R": "#2E2157", "I": "#E4D9FB",
    # the cartoon T-rex: outline, belly, belly stripes, back spikes, mouth, tongue
    "O": _T.outline, "B": _T.belly, "E": _T.stripe, "V": _T.spike, "M": "#8E2B3A", "T": "#F4758F",
}
PAL.update(_T.cactus)        # a theme may recolour the cacti (the green theme does)


def _darker(hex_, k=0.42):
    import colorsys
    r, g, b = (int(hex_.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, sat = colorsys.rgb_to_hls(r, g, b)
    return "#%02X%02X%02X" % tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, l * k, sat))


PAL["Q"] = _darker(PAL["G"])     # cactus outline, from whatever colour the cacti are

DINO_U, DINO_W, DUCK_W = 2, 36, 40      # px per cell and grid widths of the standing and ducking dino
OBJ_U = 2                               # px per cell of the cacti and birds (same fine grid as the dino)

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
        ".......QGPPGQ.......",
        "......QGPPWPGQ......",
        "......QGGPPGGQQQQ...",
        "......QGgGGhGQGGGQ..",
        "...QQ.QGgGGhGQGGGGQ.",
        "..QGGQQGgGGhGQGGhGQ.",
        ".QGGGGQggGGhSQGShGQ.",
        ".QGGhGQggGGhGQGGhGQ.",
        ".QGGhGQgggGhGGGGhGQ.",
        ".QGGhSQggSGhGGGGhGQ.",
        ".QGGhGQgggGhGGGGGGQ.",
        ".QGGhGGgggGhGGGGGQ..",
        ".QGGGGGgggGhGQQQQ...",
        "..QGGGGgggGhSQ......",
        "...QQQQgggGhGQ......",
        "......QgggGhGQ......",
        "......QggSGhGQ......",
        "......QggGGhSQ......",
        "......QGgGGhGQ......",
        "......QGgGGhGQ......",
        "......QGgGGGGQ......",
    ],
    "small": [
        "....QPPQ...",
        "...QGPPGQ..",
        ".QQQGPPGQ..",
        "QGGQgGGhQ..",
        "QGGQgGGhQ..",
        "QGGQgGGhSQ.",
        "QGGGgGGhQ..",
        "QGGGgGGhQ..",
        "QGGGgGGhQ..",
        ".QQQgSGhSQ.",
        "...QgGGhQ..",
        "...QgGGhQ..",
    ],
    "barrel": [
        "......QPQ......",
        ".....QPWPQ.....",
        "...QQGPPPGQQ...",
        "..QGGGhGGhGGQ..",
        ".QGggGhGGhGGGQ.",
        "QGGSgghGGhGSGGQ",
        "QGGggghGGhGGGGQ",
        ".QGggghGGhGGGQ.",
        "..QggShGShGGQ..",
        "...QQGhGGhQQ...",
    ],
    # ---- birds (single colour) ----
    "birdUp": [
        ".............RRR.R......",
        "..........RRRZZZRZR.....",
        ".....RRRRRZZZZZZZZR.....",
        "....RXXXXRZZZZZZZR......",
        "...RXWWXXXZZZZZZZR..RRR.",
        "..RXWKWWXXXXXXXXXRRRZZZR",
        "RRRNXKWWXXXXXXXXXXZZZZR.",
        "NNNNXXWXXXXXXXXXXXXZZZR.",
        "RRRNXXXXPXXXXXXXXXXZZZR.",
        "...RRXXXIIIIIIIXXXZZZZZR",
        ".....RRIIIIIIIIIXRRRRRR.",
        ".......RRRIIIIXRR.......",
        "..........RRRRR.........",
        "........................",
    ],
    "birdDown": [
        "........................",
        "........................",
        ".....RRRR...............",
        "....RXXXXR..............",
        "...RXWWXXXRRRRRRR...RRR.",
        "..RXWKWWXXXXXXXXXRRRZZZR",
        "RRRNXKWWXXXXXXXXXXZZZZR.",
        "NNNNXXWXRRRRRRRRRXXZZZR.",
        "RRRNXXXXPZZZZZZZRXXZZZR.",
        "...RRXXXIRZZZZZZRXZZZZZR",
        ".....RRIIRRZZZZZZRRRRRR.",
        ".......RRRRZZZZZZR......",
        "..........RRZZZZZR......",
        "............RRRRR.......",
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
