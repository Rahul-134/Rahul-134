"""The README banner in the Playful style: a sky-blue card with a sun, drifting clouds, a scrolling sand ground,
cacti, and the T-rex running and jumping over them. Two layouts: a wide one for desktop and a taller one with
bigger type and characters for phones (the README picks one with a <picture> media query).

The jump timing is computed from the real cactus widths and speed, and checked: the dino must be above each
cactus for the whole time it overlaps it, and the top of the jump must stay below the text.
"""
import base64
import math
import os

import sprites as S
import theme_colors

INK, SKY, SAND = "#2B1A12", "#BFE7F7", "#F2D9A6"
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(os.path.dirname(HERE), "dino", "fonts", "baloo-2-latin-wght-normal.woff2")
ORDER = ["O", "D", "Y", "L", "B", "E", "V", "M", "T", "K", "W", "g", "G", "h", "S", "P", "Q", "X", "Z", "N", "R", "I"]

LAYOUTS = {
    # name: canvas, ground line, sprite scale, dino x, cactus travel, cycle, text
    "desktop": dict(W=1000, H=290, ground=232, scale=1.0, dino_x=96, start=1060, end=-130, cycle=6.0,
                    title=[("Hey I am Rahul Lumbhani", 500, 98, 46)], pill=(500, 146, 21), hint=(500, 270, 13),
                    hint_text="CLICK TO PLAY  ·  SPACE / TAP TO JUMP", sun=(92, 70, 1.0), hi=(960, 44, 16),
                    clouds=[(70, 0.9, 36, 0), (300, 0.75, 46, -14), (190, 0.65, 40, -27)], text_bottom=None),   # dino is left of the title
    "mobile": dict(W=600, H=530, ground=446, scale=1.3, dino_x=40, start=660, end=-150, cycle=4.2,
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
            f'<g fill="{INK}" stroke="{INK}" stroke-width="6" stroke-linejoin="round">{puffs}</g><g fill="#fff">{puffs}</g>'
            f'<rect x="14" y="37" width="76" height="6" rx="3" fill="#DCEBF5"/><ellipse cx="40" cy="14" rx="7" ry="3.2" fill="#fff"/></g>')


def sun(x, y, s):
    rays = "".join(f'<line x1="0" y1="-26.5" x2="0" y2="-32.5" transform="rotate({i * 30})"/>' for i in range(12))
    return (f'<g transform="translate({x},{y}) scale({s})"><circle r="28" fill="#FFC83D" opacity=".22"/>'
            f'<g class="rays" stroke="#FFB547" stroke-width="4.6" stroke-linecap="round">{rays}</g>'
            f'<circle r="21.5" fill="#FFC83D" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M-14 -9 A15.5 15.5 0 0 1 -3 -16.5" stroke="#FFE7A0" stroke-width="3.6" fill="none" stroke-linecap="round"/></g>')


def ground_tile(h):
    """A 200-wide sand tile (matches the game's Playful ground), tufts poking 10 units above the line."""
    pts = " ".join(f"L{x} {10 + h * 0.62 + 3.5 * math.sin(x / 200 * 4 * math.pi):.1f}" for x in range(0, 201, 4))
    pebbles = "".join(
        f'<ellipse cx="{x}" cy="{10 + y}" rx="{rx}" ry="{ry}" fill="#CFA86E" stroke="rgba(43,26,18,.55)" stroke-width="1.3"/>'
        f'<ellipse cx="{x - rx * .3:.1f}" cy="{10 + y - ry * .35:.1f}" rx="{rx * .35:.1f}" ry="{ry * .3:.1f}" fill="#fff" opacity=".55"/>'
        for x, y, rx, ry in [(34, 20, 5, 3.1), (118, 28, 3.8, 2.4), (166, 15, 3.1, 2.0), (86, h * 0.8, 3.6, 2.1)])

    def tuft(x, flower):
        d = f"M{x - 5} 11 L{x - 6} 5 L{x - 2.5} 10 L{x} 2 L{x + 2.5} 10 L{x + 6} 4 L{x + 5} 11 Z"
        s = f'<path d="{d}" fill="#7BC86C" stroke="{INK}" stroke-width="1.4" stroke-linejoin="round"/>'
        return s + (f'<circle cx="{x}" cy="1.6" r="2.2" fill="#F472B6" stroke="{INK}" stroke-width="1.1"/>' if flower else "")
    return (f'<pattern id="sand" width="200" height="{h + 10}" patternUnits="userSpaceOnUse">'
            f'<rect y="10" width="200" height="{h}" fill="{SAND}"/><rect y="13" width="200" height="7" fill="#F9E8C4"/>'
            f'<path d="M0 {h + 10} {pts[1:] if pts.startswith("L") else pts} L200 {h + 10} Z" fill="#E5C48C"/>'
            f'{pebbles}<rect y="10" width="200" height="3.5" fill="{INK}"/>{tuft(72, False)}{tuft(150, True)}</pattern>')


def build(name, accent):
    L = LAYOUTS[name]
    W, H, G, sc = L["W"], L["H"], L["ground"], L["scale"]
    u_obj, u_dino = S.OBJ_U * sc, S.DINO_U * sc
    speed = (L["start"] - L["end"]) / L["cycle"]

    # ---- sprites
    dino_w = S.DINO_W * u_dino
    body_h = len(S.ART["dinoBody"]) * u_dino
    dino_h = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * u_dino
    body = shapes(S.pad(S.ART["dinoBody"], S.DINO_W), u_dino)
    legsA = shapes(S.pad(S.ART["legsA"], S.DINO_W), u_dino)
    legsB = shapes(S.pad(S.ART["legsB"], S.DINO_W), u_dino)
    hw = lambda n: (len(S.ART[n]) * u_obj, S.width(S.ART[n]) * u_obj)
    sag_h, sag_w = hw("saguaro"); small_h, small_w = hw("small"); bar_h, bar_w = hw("barrel")
    gap = 6 * sc
    B_w = small_w + gap + bar_w
    cactusA = f'<g transform="translate(0,{G - sag_h:.1f})">{shapes(S.ART["saguaro"], u_obj)}</g>'
    cactusB = (f'<g transform="translate(0,{G - small_h:.1f})">{shapes(S.ART["small"], u_obj)}</g>'
               f'<g transform="translate({small_w + gap:.1f},{G - bar_h:.1f})">{shapes(S.ART["barrel"], u_obj)}</g>')

    # ---- jump timing (body span DX0..DX1 measured on the sprite, not the tail tip)
    dx0, dx1 = L["dino_x"] + 8 * sc, L["dino_x"] + dino_w - 4 * sc
    def window(w, delay):
        t_in = (L["start"] - dx1) / speed + delay
        return t_in % L["cycle"], (dx1 - dx0 + w) / speed
    tA, durA = window(sag_w, 0.0)
    tB, durB = window(B_w, -L["cycle"] / 2)
    early = 0.04
    # the smallest smooth jump that clears both clusters with a margin, and stays below the text
    for dur in [x / 100 for x in range(100, 201, 2)]:
        apex = None
        for a in range(int(40 * sc), int(170 * sc)):
            def h(dt, a=a, dur=dur):
                u = (dt - dur / 2) / (dur / 2)
                return max(0.0, a * (1 - u * u))
            ok = all(h(dur / 2 - d / 2 - early) > oh + 8 * sc and h(dur / 2 + d / 2 - early) > oh + 8 * sc
                     for d, oh in ((durA, sag_h), (durB, max(small_h, bar_h))))
            if ok:
                apex = a
                break
        if apex is not None and (L["text_bottom"] is None or G - dino_h - apex > L["text_bottom"] + 6):
            DUR, APEX = dur, apex
            break
    else:
        raise SystemExit(f"banner {name}: no jump clears the cacti and stays below the text")

    def jump_height(dt):
        u = (dt - DUR / 2) / (DUR / 2)
        return max(0.0, APEX * (1 - u * u))
    starts = sorted([tA + durA / 2 - DUR / 2 - early, tB + durB / 2 - DUR / 2 - early])
    assert starts[1] - starts[0] > DUR + 0.2, starts
    pct = lambda t: f"{(t % L['cycle']) / L['cycle'] * 100:.4f}%"
    ev = sorted((st + DUR * i / 24, jump_height(DUR * i / 24)) for st in starts for i in range(25))
    jump_kf = "0%{transform:translateY(0)}" + "".join(f"{pct(t)}{{transform:translateY(-{h:.1f}px)}}" for t, h in ev) + "100%{transform:translateY(0)}"
    air_kf = "0%{opacity:0}" + "".join(f"{pct(st)}{{opacity:1}}{pct(st + DUR)}{{opacity:0}}" for st in starts)
    stride_kf = "0%{opacity:1}" + "".join(f"{pct(st)}{{opacity:0}}{pct(st + DUR)}{{opacity:1}}" for st in starts)

    # ---- scenery
    gh = H - G - 6                                   # visible ground height inside the card
    tile_s = 200 / speed                             # ground scrolls exactly with the cacti
    clouds = "".join(f'<g class="cl" style="animation-duration:{70 + i * 18}s;animation-delay:{d}s">{cloud(0, y, s)}</g>'
                     for i, (y, s, _, d) in enumerate(L["clouds"]))
    title = "".join(f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="800" fill="{INK}">{tx}</text>'
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
    dino_y = G - dino_h

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">Hey I am Rahul Lumbhani — AI/ML Engineer · GenAI Enthusiast</title>
  <desc id="d">A cartoon T-rex runs across a sunny desert and jumps over cacti. Click to play the full game.</desc>
  <style>
    {font_face()}
    text{{font-family:'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif}}
    .jump{{animation:jump {L["cycle"]:g}s linear infinite}}
    .cactus{{animation:run {L["cycle"]:g}s linear infinite}}
    .cactusB{{animation:run {L["cycle"]:g}s linear infinite;animation-delay:-{L["cycle"] / 2:g}s}}
    .legA{{animation:legA .24s steps(1,end) infinite}}
    .legB{{animation:legB .24s steps(1,end) infinite}}
    .air{{opacity:0;animation:air {L["cycle"]:g}s steps(1,end) infinite}}
    .stride{{animation:stride {L["cycle"]:g}s steps(1,end) infinite}}
    .ground{{animation:scroll {tile_s:.4f}s linear infinite}}
    .cl{{animation:drift 80s linear infinite}}
    .rays{{animation:spin 60s linear infinite}}
    @keyframes jump{{{jump_kf}}}
    @keyframes air{{{air_kf}}}
    @keyframes stride{{{stride_kf}}}
    @keyframes run{{from{{transform:translateX({L["start"]}px)}}to{{transform:translateX({L["end"]}px)}}}}
    @keyframes legA{{0%{{opacity:1}}50%{{opacity:0}}100%{{opacity:1}}}}
    @keyframes legB{{0%{{opacity:0}}50%{{opacity:1}}100%{{opacity:0}}}}
    @keyframes scroll{{from{{transform:translateX(0)}}to{{transform:translateX(-200px)}}}}
    @keyframes drift{{from{{transform:translateX({W + 40}px)}}to{{transform:translateX(-140px)}}}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    @keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
    @media (prefers-reduced-motion:reduce){{.jump,.cactus,.cactusB,.legA,.legB,.air,.stride,.ground,.cl,.rays{{animation:none}}.cactus{{transform:translateX({W * 0.62:.0f}px)}}.cactusB{{transform:translateX({W * 0.86:.0f}px)}}.cl{{transform:translateX({W * 0.4:.0f}px)}}.legB{{opacity:0}}}}
  </style>
  <defs>
    <clipPath id="card"><rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="22"/></clipPath>
    {ground_tile(gh)}
  </defs>

  <rect x="11" y="11" width="{W - 14}" height="{H - 14}" rx="22" fill="{INK}"/>
  <rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="22" fill="{SKY}"/>
  <g clip-path="url(#card)">
    {sun(sx, sy, ss)}
    {clouds}
    <text x="{ix}" y="{iy}" text-anchor="end" font-size="{iff}" font-weight="700" fill="{INK}" fill-opacity=".45" letter-spacing="1.5">HI 00134</text>
    {title}
    {pill}

    <!-- ground: a sand pattern that scrolls with the cacti -->
    <g transform="translate(0,{G - 10})"><g class="ground"><rect width="{W + 220}" height="{gh + 10}" fill="url(#sand)"/></g></g>
    <text x="{hx}" y="{hy}" text-anchor="middle" font-size="{hf}" font-weight="800" fill="{INK}" fill-opacity=".55" letter-spacing="2">{L["hint_text"]}</text>

    <g class="cactus">{cactusA}</g>
    <g class="cactusB">{cactusB}</g>

    <g transform="translate({L["dino_x"]},{dino_y:.1f})">
      <g class="jump">
        <g>{body}</g>
        <g transform="translate(0,{body_h:.1f})">
          <g class="stride"><g class="legA">{legsA}</g><g class="legB">{legsB}</g></g>
          <g class="air">{legsA}</g>
        </g>
      </g>
    </g>
  </g>
  <rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="22" fill="none" stroke="{INK}" stroke-width="4"/>
</svg>
'''


def write_all(out_dir, accent):
    for name, fn in (("desktop", "dino-banner.svg"), ("mobile", "dino-banner-mobile.svg")):
        with open(os.path.join(out_dir, fn), "w") as f:
            f.write(build(name, accent))
