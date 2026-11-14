"""Season 2's world tour, as SVG with CSS animation (no script), for the README banner and the game page's hero card.

The tour loops through the four worlds of Season 2, five seconds each: Desert, Canyon, Volcano and Starfall, in the
game's own Playful colours. In each one its boss arrives, attacks (the Golem rolls a boulder, the Serpent spits fire,
the Dragon drops a meteor; in the Desert a cactus comes by), the T-rex jumps it, breathes two fireballs that hit, and
the boss falls before the next world fades in. The bosses are the game's sprites (tools/boss_art.json).

    t = Tour(W, H, ground, scale, dino_x, boss_x, ...)
    t.defs()      shared <defs> (sprites, patterns, the white flash filter)
    t.back()      the four worlds: sky, backdrop, ground and label (behind the sun, clouds and any text)
    t.front()     bosses, attacks, fire and the T-rex (in front)
    t.css(...)    the animation, plus the colours for day and/or night

Colours that change between day and night are CSS classes (.wt-sky0, .wt-k ...), so one drawing serves both: the
README banner has a file per mode, the game page switches with html[data-mode=dark]. Each world's moving parts run
on the same 5-second timeline; only which world is showing changes.
"""
import json
import math
import os

import sprites as S

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "boss_art.json")) as f:
    BOSS_ART = json.load(f)

# The game's Playful scenery per world (LOOKS in index.template.html): sky, sand layers, pebbles, grass, backdrop.
LOOKS = [
    dict(day=dict(sky="#BFE7F7", sand="#F2D9A6", top="#F9E8C4", low="#E5C48C", peb="#CFA86E", tuft="#7BC86C"),
         night=dict(sky="#26325E", sand="#B3925F", top="#C5A673", low="#987A4D", peb="#7E6240", tuft="#5E9A57")),
    dict(day=dict(sky="#FFE3C7", sand="#EFB287", top="#F6CBA5", low="#D9925F", peb="#B06A44", tuft="#9DBB6A", far="#F2B98F", near="#E39A6C"),
         night=dict(sky="#3A2A4E", sand="#A9714F", top="#BC8762", low="#8A583C", peb="#6A4128", tuft="#5E7E4B", far="#5A3F5E", near="#4A3150")),
    dict(day=dict(sky="#F7C9B3", sand="#7A6460", top="#93807A", low="#5E4C49", peb="#463634", tuft=None, far="#A88378", near="#8C6A62"),
         night=dict(sky="#2B1B2C", sand="#5A4744", top="#6E5955", low="#433331", peb="#2F2322", tuft=None, far="#4A3036", near="#3B2830")),
    dict(day=dict(sky="#D9D2F7", sand="#E9CFE0", top="#F5E3EE", low="#D3B2CB", peb="#B48FAE", tuft="#8FC79A"),
         night=dict(sky="#1C1A44", sand="#9C7F99", top="#AF93AC", low="#7E647D", peb="#5F4A5E", tuft="#5E9A57")),
]
INK = dict(day="#2B1A12", night="#0C0B16")
NAMES = ["DESERT", "CANYON", "VOLCANO", "STARFALL"]
BOSS_KEYS = ["tyrant", "golem", "serpent", "dragon"]
BOSS_U = [1.8, 2.0, 2.0, 1.75]                # px per cell in the game
BOSS_PTS = [250, 300, 350, 500]
FLOWER = "#F472B6"

# The timeline of every world, in seconds (P per world, four worlds per loop)
P = 5.0
T = 4 * P
ENTER = 0.7                                    # the boss slides in
WIND, ATTACK, ATTACK_END = 0.55, 1.0, 1.4      # wind-up pose, then the attack pose (the attack leaves at ATTACK)
JUMP_AT = 2.6                                  # the attack (or the cactus) is under the T-rex
FIRES = [3.1, 3.42]                            # two fireballs, after the T-rex lands
FIRE_SPEED = 1000                              # px/s at scale 1
DOWN = 4.4                                     # the boss falls
FADE = 0.45                                    # the next world fades in over the last FADE seconds


def num(v):
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def pct(t, period=P):
    return f"{max(0.0, min(100.0, t / period * 100)):.3f}%"


def keyframes(name, points, period=P):
    """points: [(seconds, 'css'), ...] -> @keyframes over the period (0% and 100% filled in from the ends)."""
    pts = sorted(points, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0.0, pts[0][1]))
    if pts[-1][0] < period:
        pts.append((period, pts[-1][1]))
    return f"@keyframes {name}{{" + "".join(f"{pct(t, period)}{{{css}}}" for t, css in pts) + "}"


def rows_runs(rows, colour_of):
    """Pixel rows -> {colour: path d}, each run of a row drawn as one 1-unit-wide horizontal stroke (half the size
    of filled rectangles). Draw with stroke-width 1 at the cell scale."""
    out = {}
    for y, r in enumerate(rows):
        x, last = 0, {}
        while x < len(r):
            c = r[x]
            if c == ".":
                x += 1
                continue
            x0 = x
            while x < len(r) and r[x] == c:
                x += 1
            col = colour_of(c)
            seg = out.setdefault(col, [])
            if col in last:
                seg.append(f"m{x0 - last[col]} 0h{x - x0}")
            else:
                seg.append(f"M{x0} {y}.5h{x - x0}")
            last[col] = x
    return {c: "".join(v) for c, v in out.items()}


def silhouette(rows):
    """One path for every opaque cell (the solid underlay that hides seams between colours)."""
    d = []
    for y, r in enumerate(rows):
        x, first = 0, True
        while x < len(r):
            if r[x] == ".":
                x += 1
                continue
            x0 = x
            while x < len(r) and r[x] != ".":
                x += 1
            d.append(f"M{x0} {y}.5h{x - x0}")
    return "".join(d)


def sprite_svg(rows, colour_of, base=None):
    """A sprite at 1 unit per cell (scale it with a transform)."""
    runs = rows_runs(rows, colour_of)
    if base is None:
        counts = {c: d.count("h") for c, d in runs.items()}
        base = max(counts, key=counts.get)
    return (f'<g fill="none" stroke-width="1"><path stroke="{base}" d="{silhouette(rows)}"/>'
            + "".join(f'<path stroke="{c}" d="{d}"/>' for c, d in runs.items()) + "</g>")


def art(name):
    rows = S.pad(S.ART[name])
    return rows, sprite_svg(rows, lambda c: S.PAL[c])


class Tour:
    def __init__(self, W, H, ground, scale, dino_x, boss_x, boss_scale, back_scale, label_xy, prefix="wt", fly_y=None, max_apex=None, fire_min_y=None):
        self.max_apex, self.fire_min_y = max_apex, fire_min_y
        self.W, self.H, self.G, self.sc = W, H, ground, scale
        self.dino_x, self.boss_x, self.bs, self.backs = dino_x, boss_x, boss_scale, back_scale
        self.label_xy, self.p = label_xy, prefix
        self.fly_y = fly_y if fly_y is not None else ground - 112 * scale
        self.speed = 200 * scale                    # ground speed, px/s
        u = S.DINO_U * scale
        self.du = u
        self.dino_w = S.DINO_W * u
        self.dino_h = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * u
        self.mouth = (dino_x + self.dino_w - 8 * scale, ground - self.dino_h + 23 * scale)
        self.akf = {}
        self._bosses()
        self._jump()
        self._fire_times()

    # ---------- bosses: where each pose sits, where its attacks leave from, where fire hits it ----------
    def _bosses(self):
        self.B = []
        for k, key in enumerate(BOSS_KEYS):
            A = BOSS_ART[key]
            u = BOSS_U[k] * self.bs
            poses = []
            for f in A["frames"]:
                rows = f["rows"]
                n, w = len(rows), max(len(r) for r in rows)
                if A["anchor"] == "mass":
                    ax, ay = f["ax"], f["ay"]
                else:                                # standing: the middle of what touches the ground
                    xs = [x for r in rows[-3:] for x, c in enumerate(r) if c != "."]
                    ax, ay = sum(xs) / len(xs) + 0.5, n
                poses.append(dict(rows=rows, w=w, h=n, ax=ax, ay=ay))
            if k in (0, 3):
                anchor = (self.boss_x, self.fly_y)
            elif k == 1:
                anchor = (self.boss_x, self.G)
            else:
                anchor = (self.boss_x + 10 * self.sc, self.G + 4 * self.sc)
            idle = poses[0]
            left, top = anchor[0] - idle["ax"] * u, anchor[1] - idle["ay"] * u
            w, h = idle["w"] * u, idle["h"] * u
            if k == 1:
                hit = (left + w * 0.2, top + h * 0.45)
            elif k == 2:
                hit = (left + w * 0.12, top + h * 0.25)
            else:
                hit = (left + w * 0.3, top + h * 0.5)
            if self.fire_min_y is not None:              # keep the fire's path under any text: hit lower on the boss
                hit = (hit[0], min(top + h * 0.92, max(hit[1], self.fire_min_y)))
            self.B.append(dict(k=k, key=key, u=u, poses=poses, anchor=anchor, left=left, top=top, w=w, h=h, hit=hit, pal=A["pal"]))

    @staticmethod
    def poses_used(k):
        """The Sky Tyrant just hovers (the Desert keeps its cactus); the Dragon's third pose is its idle one again."""
        return [[0], [0, 1, 2], [0, 1, 2], [0, 1]][k]

    def pose_xy(self, b, i):
        p = b["poses"][i]
        return b["anchor"][0] - p["ax"] * b["u"], b["anchor"][1] - p["ay"] * b["u"]

    def cell(self, b, i, cx, cy):
        x, y = self.pose_xy(b, i)
        return x + cx * b["u"], y + cy * b["u"]

    # ---------- the T-rex's jump: centred on JUMP_AT, high enough to clear every world's attack ----------
    def _jump(self):
        sc = self.sc
        body0, body1 = self.dino_x + 8 * sc, self.dino_x + self.dino_w - 4 * sc
        cac_rows, _ = art("saguaro")
        hazards = [(S.width(cac_rows) * S.OBJ_U * sc, len(cac_rows) * S.OBJ_U * sc, self.speed),       # cactus
                   (14 * S.OBJ_U * 1.25 * sc, 14 * S.OBJ_U * 1.25 * sc, self._boulder_speed()),       # boulder
                   (18 * sc, 26 * sc + 9 * sc, self._spit_speed()),                                    # spit (low lane)
                   (12 * S.OBJ_U * 1.5 * sc, 12 * S.OBJ_U * 1.5 * sc, self.speed)]                      # meteor

        def clears(dur, apex):                        # above each hazard for the whole time they overlap, with a margin
            for w, h, v in hazards:
                span = (body1 - body0 + w) / v
                for dt in (-span / 2, span / 2):
                    u = dt / (dur / 2)
                    if abs(u) >= 1 or apex * (1 - u * u) < h + 6 * sc:
                        return False
            return True
        for dur in [x / 100 for x in range(70, 131, 2)]:
            apex = next((a * sc for a in range(50, 116) if clears(dur, a * sc) and (self.max_apex is None or a * sc <= self.max_apex)), None)
            if apex is not None:
                self.jump_dur, self.jump_apex = dur, apex
                break
        else:
            raise SystemExit("tour: no jump clears every attack")
        assert self.G - self.dino_h - self.jump_apex > 0

    def _boulder_speed(self):
        b = self.B[1]
        return (b["left"] - (self.dino_x + self.dino_w / 2)) / (JUMP_AT - ATTACK)

    def _spit_speed(self):
        b = self.B[2]
        mx, _ = self.cell(b, 2, 8, 26)
        return (mx - (self.dino_x + self.dino_w / 2)) / (JUMP_AT - ATTACK)

    def _fire_times(self):
        """For each world: when each fireball leaves and lands (it flies straight from the mouth to the boss)."""
        mx, my = self.mouth
        self.fire = []
        for b in self.B:
            tx, ty = b["hit"]
            dur = math.hypot(tx - mx, ty - my) / (FIRE_SPEED * self.sc)
            self.fire.append([(t0, t0 + dur) for t0 in FIRES])
            assert self.fire[-1][-1][1] + 0.2 < DOWN, "tour: the last fireball lands too late"
        assert FIRES[0] > JUMP_AT + self.jump_dur / 2, "tour: fire before the T-rex has landed"

    # ---------- shared defs ----------
    def defs(self):
        p, out = self.p, []
        out.append(f'<filter id="{p}-white" x="-5%" y="-5%" width="110%" height="110%"><feFlood flood-color="#fff"/>'
                   f'<feComposite in2="SourceAlpha" operator="in"/></filter>')
        for b in self.B:
            for i, pose in enumerate(b["poses"]):
                if i not in self.poses_used(b["k"]):
                    continue
                pal = b["pal"]
                out.append(f'<g id="{p}-{b["key"]}{i}">{sprite_svg(pose["rows"], lambda c, pal=pal: pal[c])}</g>')
        for name in ("saguaro", "boulder", "meteor"):
            out.append(f'<g id="{p}-{name}">{art(name)[1]}</g>')
        for part in ("dinoBody", "legsA", "legsB"):
            out.append(f'<g id="{p}-{part}">{sprite_svg(S.pad(S.ART[part], S.DINO_W), lambda c: S.PAL[c], base=S.PAL["Y"])}</g>')
        for k in range(4):
            out.append(self._ground_tile(k))
        out.append(f'<clipPath id="{p}-above"><rect x="-50" y="-50" width="{self.W + 100}" height="{self.G + 50 + 3 * self.sc:.1f}"/></clipPath>')
        return "".join(out)

    def _ground_tile(self, k):
        """A 200-wide sand tile like the game's Playful ground (the banner's tile, recoloured per world)."""
        p, h = self.p, self.H - self.G + 6
        deep = h + 40
        pts = " ".join(f"L{x} {10 + h * 0.62 + 3.5 * math.sin(x / 200 * 4 * math.pi):.1f}" for x in range(0, 201, 4))
        pebbles = "".join(
            f'<ellipse class="{p}-peb{k}" cx="{x}" cy="{10 + y:.1f}" rx="{rx}" ry="{ry}" stroke="rgba(43,26,18,.55)" stroke-width="1.3"/>'
            f'<ellipse cx="{x - rx * .3:.1f}" cy="{10 + y - ry * .35:.1f}" rx="{rx * .35:.1f}" ry="{ry * .3:.1f}" fill="#fff" opacity=".55"/>'
            for x, y, rx, ry in [(34, 20, 5, 3.1), (118, 28, 3.8, 2.4), (166, 15, 3.1, 2.0), (86, h * 0.8, 3.6, 2.1)])

        def tuft(x, flower):
            d = f"M{x - 5} 11 L{x - 6} 5 L{x - 2.5} 10 L{x} 2 L{x + 2.5} 10 L{x + 6} 4 L{x + 5} 11 Z"
            s = f'<path class="{p}-tuft{k} {p}-ks" d="{d}" stroke-width="1.4" stroke-linejoin="round"/>'
            return s + (f'<circle class="{p}-ks" cx="{x}" cy="1.6" r="2.2" fill="{FLOWER}" stroke-width="1.1"/>' if flower else "")
        tufts = (tuft(72, False) + tuft(150, True)) if LOOKS[k]["day"]["tuft"] else ""
        return (f'<pattern id="{p}-sand{k}" width="200" height="{deep + 14:.0f}" patternUnits="userSpaceOnUse">'
                f'<rect class="{p}-sand{k}" y="10" width="200" height="{deep:.0f}"/><rect class="{p}-top{k}" y="13" width="200" height="7"/>'
                f'<path class="{p}-low{k}" d="M0 {deep + 10:.0f} {pts[1:]} L200 {deep + 10:.0f} Z"/>'
                f'{pebbles}<rect class="{p}-k" y="10" width="200" height="3.5"/>{tufts}</pattern>')

    # ---------- behind: sky and backdrop per world ----------
    def back(self, label_font="inherit"):
        """Each world as one solid layer: sky, backdrop, ground and its label (so nothing from the worlds underneath
        shows through while they cross-fade)."""
        p, W, G, H = self.p, self.W, self.G, self.H
        gh = H - G + 6
        out = []
        for k in range(4):
            g = [f'<rect class="{p}-sky{k}" x="-10" y="-10" width="{W + 20}" height="{G + 20}"/>']
            g.append(self._backdrop(k))
            g.append(f'<g transform="translate(0,{G - 10:.1f})"><rect class="{p}-ground" width="{W + 220}" height="{gh + 10:.1f}" fill="url(#{p}-sand{k})"/></g>')
            g.append(self._label(k, label_font))
            out.append(f'<g class="{p}-v{k}"{"" if k == 0 else " opacity=\"0\""}>{"".join(g)}</g>')
        return "".join(out)

    def _backdrop(self, k):
        p, G, s, W = self.p, self.G, self.backs, self.W
        span = 900 * s                                  # the backdrop repeats every `span`, and drifts by one span
        copies = int(W / span) + 2
        if k == 1:                                      # Canyon: flat-topped mesas, far and near
            shapes = []
            for n, (cls, dx, base) in enumerate([("far", 0.0, 70), ("near", 0.5, 40)]):
                for c in range(copies):
                    for mx, mw, mh in [(60, 120, 70), (330, 90, 55), (600, 150, 80)]:
                        x, w = (c * 900 + mx + dx * 140) * s, mw * s
                        top = G - (base + mh * (0.55 if n else 1)) * s
                        shapes.append(f'<path class="{p}-{cls}{k} {p}-ks" stroke-width="2.5" stroke-linejoin="round" d="M{x:.1f} {G}L{x + 14 * s:.1f} {top + 8 * s:.1f}'
                                      f'L{x + 20 * s:.1f} {top:.1f}L{x + w - 20 * s:.1f} {top:.1f}L{x + w - 14 * s:.1f} {top + 8 * s:.1f}L{x + w:.1f} {G}Z"/>'
                                      f'<rect x="{x + 22 * s:.1f}" y="{top + 3 * s:.1f}" width="{max(0, w - 44 * s):.1f}" height="{4 * s:.1f}" fill="#fff" opacity=".18"/>')
            return f'<g class="{p}-drift">{"".join(shapes)}</g>'
        if k == 2:                                      # Volcano: two cones with a glowing crater and lava running down
            shapes = []
            for c in range(copies):
                for vx, vw, vh, cls, seed in [(120, 230, 120, "far", 0), (540, 300, 165, "near", 1)]:
                    x, w, top = (c * 900 + vx) * s, vw * s, G - vh * s
                    shapes.append(f'<path class="{p}-{cls}{k} {p}-ks" stroke-width="2.5" stroke-linejoin="round" d="M{x:.1f} {G}L{x + w * .42:.1f} {top:.1f}L{x + w * .58:.1f} {top:.1f}L{x + w:.1f} {G}Z"/>')
                    shapes.append(self._lava(x, w, top, seed))
                    shapes.append(f'<ellipse class="{p}-glow" cx="{x + w / 2:.1f}" cy="{top:.1f}" rx="{w * .12:.1f}" ry="{9 * s + 4:.1f}" fill="#FFB347" opacity=".45"/>')
                    shapes.append(f'<path class="{p}-ks" fill="#FF8A3D" stroke-width="2.5" stroke-linejoin="round" d="M{x + w * .42:.1f} {top:.1f}L{x + w * .58:.1f} {top:.1f}L{x + w * .54:.1f} {top + 12 * s:.1f}L{x + w * .46:.1f} {top + 12 * s:.1f}Z"/>')
            return f'<g class="{p}-drift">{"".join(shapes)}</g>'
        if k == 3:                                      # Starfall: three soft aurora bands and shooting stars
            bands = []
            for col, y, ph in [("rgba(124,242,194,.32)", 40, 0), ("rgba(180,156,255,.28)", 62, 1.7), ("rgba(255,156,214,.22)", 84, 3.1)]:
                yy = y * self.H / 260
                wave = lambda x: yy + 12 * math.sin(x / 140 + ph)                  # the band's top edge
                thick = lambda x: (22 + 6 * math.sin(x / 90 + ph)) * self.H / 260    # and a thickness that never pinches
                top = " ".join(f"L{x:.0f} {wave(x):.1f}" for x in range(-60, int(W) + 120, 30))
                bot = " ".join(f"L{x:.0f} {wave(x) + thick(x):.1f}" for x in range(int(W) + 120, -61, -30))
                bands.append(f'<path class="{p}-sway" fill="{col}" d="M-60 {yy + 26:.1f} {top} {bot} Z"/>')
            shoot = "".join(f'<g class="{p}-shoot" style="animation-delay:{-d:.1f}s"><path d="M0 0l{-46 * self.sc:.0f} {-16 * self.sc:.0f}" stroke="#FFF3C4" stroke-width="{2.4 * self.sc:.1f}" stroke-linecap="round" opacity=".85"/>'
                            f'<circle r="{2.6 * self.sc:.1f}" fill="#FFF7DA"/></g>' for d in (0.0, 1.7))
            return "".join(bands) + f'<g transform="translate({W * 0.55:.0f},{self.H * 0.08:.0f})">{shoot}</g>'
        return ""

    def _lava(self, x, w, top, seed):
        """Two or three lava tongues from the rim, with a bright current that flows downhill."""
        s, p, G = self.backs, self.p, self.G
        out = []
        flows = [(-1, 0.55, 5.5), (1, 0.62, 6.5), (1, 0.32, 4.5)] if seed else [(-1, 0.5, 5), (1, 0.4, 4.5)]
        for side, reach, wid in flows:
            x0, y0 = x + w * (0.5 + side * 0.06), top + 4 * s
            x1, y1 = x + w * (0.5 + side * 0.3 * reach), top + (G - top) * reach   # down the slope, inside the cone's edge
            nx, ny = (y1 - y0), -(x1 - x0)
            d = math.hypot(nx, ny)
            nx, ny = nx / d, ny / d
            w0, w1 = wid * s * 4.4, wid * s * 2.0
            pts_l = [(x0 + (x1 - x0) * t + nx * (w0 + (w1 - w0) * t) / 2, y0 + (y1 - y0) * t + ny * (w0 + (w1 - w0) * t) / 2) for t in (0, .5, 1)]
            pts_r = [(x0 + (x1 - x0) * t - nx * (w0 + (w1 - w0) * t) / 2, y0 + (y1 - y0) * t - ny * (w0 + (w1 - w0) * t) / 2) for t in (1, .5, 0)]
            dpath = "M" + " L".join(f"{a:.1f} {b:.1f}" for a, b in pts_l + pts_r) + "Z"
            out.append(f'<path class="{p}-ks" d="{dpath}" fill="#F2552C" stroke-width="2.6" stroke-linejoin="round"/>')
            out.append(f'<path class="{p}-flow" d="M{x0:.1f} {y0:.1f}L{x1:.1f} {y1:.1f}" stroke="#FFD166" stroke-width="{max(1.6, w0 * .28):.1f}" stroke-linecap="round" stroke-dasharray="5 11" fill="none"/>')
        return "".join(out)

    # ---------- in front: ground, label, boss, attack, T-rex, fire ----------
    def front(self, hint=""):
        p, W, H, G, sc = self.p, self.W, self.H, self.G, self.sc
        gh = H - G + 6
        out = []
        for k in range(4):                             # boss, attack and fire: only while their world is on
            g = [self._boss(k), self._attack(k), self._fire(k)]
            out.append(f'<g class="{p}-a{k}"{"" if k == 0 else " opacity=\"0\""}>{"".join(g)}</g>')
        out.append(hint)
        out.append(self._dino())
        return "".join(out)

    def _label(self, k, font):
        p, sc = self.p, self.sc
        x, y = self.label_xy
        text = f"WORLD {k + 1} · {NAMES[k]}"
        fs = 12 * sc
        w = max(len(f"WORLD {i + 1} · {n}") for i, n in enumerate(NAMES)) * fs * 0.62 + 18 * sc   # one width: they cover each other
        h = fs * 1.75
        return (f'<g transform="translate({x:.1f},{y:.1f})"><rect class="{p}-k" x="{2 * sc:.1f}" y="{3 * sc:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}"/>'
                f'<rect class="{p}-paper {p}-ks" width="{w:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" stroke-width="{2.2 * sc:.1f}"/>'
                f'<text class="{p}-label" x="{w / 2:.1f}" y="{h * 0.68:.1f}" text-anchor="middle" font-size="{fs:.1f}" font-weight="800" letter-spacing="{1 * sc:.1f}" font-family="{font}">{text}</text></g>')

    def _boss(self, k):
        p, b = self.p, self.B[k]
        key, u = b["key"], b["u"]
        poses = self.poses_used(k)
        layers = []
        for i in poses:
            x, y = self.pose_xy(b, i)
            cls = f'{p}-pose{i}' if len(poses) > 1 else ""
            if key == "dragon" and i == 1:
                cls = f'{p}-pose12'                    # no attack pose of its own: it holds the wind-up through the attack
            layers.append(f'<g class="{cls}" transform="translate({x:.1f},{y:.1f}) scale({u:.3f})"{" opacity=\"0\"" if i else ""}><use href="#{p}-{key}{i}"/></g>')
        x, y = self.pose_xy(b, 0)
        layers.append(f'<g class="{p}-flash{k}" opacity="0" transform="translate({x:.1f},{y:.1f}) scale({u:.3f})"><use href="#{p}-{key}0" filter="url(#{p}-white)"/></g>')
        body = "".join(layers)
        if k == 2:                                     # the Serpent rises out of its lava pool
            cx, sc = b["anchor"][0] - 10 * self.sc, self.sc
            body = (f'<g clip-path="url(#{p}-above)">{body}</g>'
                    f'<ellipse class="{p}-ks" cx="{cx:.1f}" cy="{self.G + 3 * sc:.1f}" rx="{58 * sc * self.bs:.1f}" ry="{10 * sc:.1f}" fill="#FF7A3D" stroke-width="2.6"/>'
                    f'<rect x="{cx - 40 * sc * self.bs:.1f}" y="{self.G:.1f}" width="{80 * sc * self.bs:.1f}" height="{3 * sc:.1f}" fill="#FFD166"/>')
        bob = f'{p}-bob' if k in (0, 3) else (f'{p}-sway2' if k == 2 else "")
        hx, hy = b["hit"]
        pts = (f'<text class="{p}-pts {p}-ink" x="{b["left"] + b["w"] / 2:.1f}" y="{b["top"] + b["h"] * 0.3:.1f}" text-anchor="middle" font-size="{18 * self.sc:.1f}" font-weight="800" opacity="0">+{BOSS_PTS[k]}</text>')
        burst = "".join(f'<circle class="{p}-spark{k}" cx="{hx:.1f}" cy="{hy:.1f}" r="{(3 + j % 3) * self.sc:.1f}" fill="{["#FFD166", "#FF8A3D", "#FF5E7A"][j % 3]}" opacity="0" style="--dx:{math.cos(j * 1.3) * 22 * self.sc:.0f}px;--dy:{math.sin(j * 1.3) * 18 * self.sc - 6:.0f}px"/>' for j in range(6))
        return f'<g class="{p}-boss"><g class="{bob}">{body}</g></g>{burst}{pts}'

    def _attack(self, k):
        p, G, sc = self.p, self.G, self.sc
        mid = self.dino_x + self.dino_w / 2
        if k == 0:                                     # the Desert: a cactus, at ground speed
            rows, _ = art("saguaro")
            w, h = S.width(rows) * S.OBJ_U * sc, len(rows) * S.OBJ_U * sc
            x0 = mid - w / 2 + self.speed * JUMP_AT
            pts = [(0, f"transform:translateX({x0:.1f}px)"), (P, f"transform:translateX({x0 - self.speed * P:.1f}px)")]
            self.akf[0] = keyframes(f"{p}-cac", pts)
            return f'<g class="{p}-cac"><g transform="translate(0,{G - h:.1f}) scale({S.OBJ_U * sc:.3f})"><use href="#{p}-saguaro"/></g></g>'
        if k == 1:                                     # the Canyon: the Golem rolls a boulder
            u = S.OBJ_U * 1.25 * sc
            r = 7 * u
            b = self.B[1]
            x0, v = b["left"] + r, self._boulder_speed()
            x_at = lambda t: x0 - v * (t - ATTACK)
            pts = [(0, "opacity:0;transform:translate(0,0) rotate(0)")]
            for t in [ATTACK - 0.001, ATTACK, (ATTACK + P) / 2, P]:
                if t < ATTACK:
                    pts.append((t, f"opacity:0;transform:translate({x0:.1f}px,0) rotate(0deg)"))
                    continue
                pts.append((t, f"opacity:1;transform:translate({x_at(t):.1f}px,0) rotate({-(x0 - x_at(t)) / r * 57.3:.0f}deg)"))
            self.akf[1] = keyframes(f"{p}-roll", pts)
            return (f'<g transform="translate(0,{G - r:.1f})"><g class="{p}-roll" opacity="0"><g transform="translate({-r:.1f},{-r:.1f}) scale({u:.3f})">'
                    f'<use href="#{p}-boulder"/></g></g></g>')
        if k == 2:                                     # the Volcano: the Serpent spits fire along the low lane
            b = self.B[2]
            mx, my = self.cell(b, 2, 8, 26)
            v, lane = self._spit_speed(), G - 26 * sc
            pts = [(0, "opacity:0"), (ATTACK - 0.001, f"opacity:0;transform:translate({mx:.1f}px,{my:.1f}px)")]
            for t in [ATTACK, ATTACK + 0.35, P]:
                y = lane if t > ATTACK else my
                pts.append((t, f"opacity:1;transform:translate({mx - v * (t - ATTACK):.1f}px,{y:.1f}px)"))
            self.akf[2] = keyframes(f"{p}-spit", pts)
            trail = "".join(f'<circle cx="{j * 9 * sc:.1f}" r="{9 * sc * a:.1f}" fill="#FF5E7A" opacity="{o}"/>' for j, o, a in [(1, .5, .8), (2, .3, .62), (3, .15, .45)])
            return (f'<g class="{p}-spit" opacity="0">{trail}<circle class="{p}-ks" r="{9 * sc:.1f}" fill="#FF5E7A" stroke-width="2.4"/>'
                    f'<circle r="{4 * sc:.1f}" fill="#FFD1DA"/></g>')
        # the Starfall: the Dragon drops a meteor that lands ahead and slides with the ground
        b = self.B[3]
        u = S.OBJ_U * 1.5 * sc
        size = 12 * u
        sx, sy = self.cell(b, 1, 10, 38)
        land_t = ATTACK + 0.6
        lx = mid + self.speed * (JUMP_AT - land_t)
        pts = [(0, "opacity:0"), (ATTACK - 0.001, f"opacity:0;transform:translate({sx - size / 2:.1f}px,{sy - size / 2:.1f}px)")]
        for j in range(9):                             # a lob: it drops first, then swings forward to land
            t = ATTACK + (land_t - ATTACK) * j / 8
            q = j / 8
            y = sy + (G - size / 2 - sy) * (1 - (1 - q) ** 2)
            pts.append((t, f"opacity:1;transform:translate({sx + (lx - sx) * q - size / 2:.1f}px,{y - size / 2:.1f}px)"))
        pts.append((P, f"opacity:1;transform:translate({lx - self.speed * (P - land_t) - size / 2:.1f}px,{G - size:.1f}px)"))
        self.akf[3] = keyframes(f"{p}-meteor", pts)
        ring = (f'<ellipse class="{p}-ring" cx="{lx:.1f}" cy="{G + 2 * sc:.1f}" rx="{20 * sc:.1f}" ry="{5 * sc:.1f}" fill="none" stroke="#FF5E7A" stroke-width="{2.4 * sc:.1f}" opacity="0"/>')
        return ring + f'<g class="{p}-meteor" opacity="0"><g transform="scale({u:.3f})"><use href="#{p}-meteor"/></g></g>'

    def _dino(self):
        p, sc, u = self.p, self.sc, self.du
        body_h = len(S.ART["dinoBody"]) * u
        y = self.G - self.dino_h
        return (f'<g transform="translate({self.dino_x:.1f},{y:.1f})"><g class="{p}-jump">'
                f'<g transform="scale({u:.3f})"><use href="#{p}-dinoBody"/></g>'
                f'<g transform="translate(0,{body_h:.1f}) scale({u:.3f})"><g class="{p}-stride"><g class="{p}-legA"><use href="#{p}-legsA"/></g>'
                f'<g class="{p}-legB"><use href="#{p}-legsB"/></g></g><g class="{p}-air" opacity="0"><use href="#{p}-legsA"/></g></g></g></g>')

    def _fire(self, k):
        p, sc = self.p, self.sc
        out = []
        for n in range(len(FIRES)):
            out.append(f'<g class="{p}-fire{k}{n}" opacity="0"><circle r="{11 * sc:.1f}" fill="#FFB347" opacity=".35"/>'
                       f'<circle class="{p}-ks" r="{7 * sc:.1f}" fill="#FF8A3D" stroke-width="{2.4 * sc:.1f}"/><circle r="{3.2 * sc:.1f}" fill="#FFE08A"/></g>')
        return "".join(out)

    # ---------- the animation ----------
    def css(self, modes=("day",), scope="", reduced_static=True):
        """Animation rules plus colours. `modes`: [("day", selector prefix), ("night", "html[data-mode=dark] ")] for
        the game page, or a single mode for a README file."""
        p, sc = self.p, self.sc
        rules, kfs = [], []
        # colours
        for mode, pre in modes:
            sel = lambda c: f"{pre}{scope} .{p}-{c}"
            ink = INK[mode]
            r = [f"{sel('k')}{{fill:{ink}}}", f"{sel('ks')}{{stroke:{ink}}}", f"{sel('ink')}{{fill:{ink}}}",
                 f"{sel('paper')}{{fill:{'#2C2A45' if mode == 'night' else '#FFFDF7'}}}", f"{sel('label')}{{fill:{'#F4ECDD' if mode == 'night' else ink}}}"]
            for k in range(4):
                L = LOOKS[k][mode]
                for role in ("sky", "sand", "top", "low", "peb", "tuft", "far", "near"):
                    if L.get(role):
                        r.append(f"{sel(role + str(k))}{{fill:{L[role]}}}")
            rules.append("".join(r))
        # which world is showing: world 0 underneath, 1-3 fade in on top in turn, and 3 fades out to reveal 0 again
        for k in (1, 2, 3):
            start, end = k * P, (k + 1) * P
            pts = [(0, "opacity:0"), (start - FADE, "opacity:0"), (start, "opacity:1")]
            if k < 3:
                pts += [(end, "opacity:1"), (end + 0.001, "opacity:0")]
            else:
                pts += [(end - FADE, "opacity:1"), (end, "opacity:0")]
            kfs.append(keyframes(f"{p}-v{k}", pts, T))
            rules.append(f"{scope} .{p}-v{k}{{animation:{p}-v{k} {T:g}s linear infinite}}")
        for k in range(4):                             # a world's actors: in just after it begins, gone when it ends
            start, end = k * P, (k + 1) * P
            if k == 0:
                pts = [(0, "opacity:1"), (end, "opacity:1"), (end + 0.001, "opacity:0"), (T - 0.001, "opacity:0")]
            else:
                pts = [(0, "opacity:0"), (start, "opacity:0"), (start + 0.25, "opacity:1"), (end, "opacity:1"), (min(T, end + 0.001), "opacity:0")]
            kfs.append(keyframes(f"{p}-a{k}", pts, T))
            rules.append(f"{scope} .{p}-a{k}{{animation:{p}-a{k} {T:g}s linear infinite}}")
        # the boss: in, then down
        off = self.W - self.boss_x + 120 * sc
        kfs.append(keyframes(f"{p}-boss", [(0, f"transform:translate({off:.0f}px,0);opacity:1"), (ENTER, "transform:translate(0,0);opacity:1"),
                                           (DOWN, "transform:translate(0,0);opacity:1"), (P - 0.05, f"transform:translate(0,{60 * sc:.0f}px);opacity:0")]))
        rules.append(f"{scope} .{p}-boss{{animation:{p}-boss {P:g}s cubic-bezier(.3,.7,.4,1) infinite}}")
        kfs.append(keyframes(f"{p}-pose1", [(0, "opacity:0"), (WIND, "opacity:0"), (WIND + .001, "opacity:1"), (ATTACK, "opacity:1"), (ATTACK + .001, "opacity:0")]))
        kfs.append(keyframes(f"{p}-pose2", [(0, "opacity:0"), (ATTACK, "opacity:0"), (ATTACK + .001, "opacity:1"), (ATTACK_END, "opacity:1"), (ATTACK_END + .001, "opacity:0")]))
        kfs.append(keyframes(f"{p}-pose0", [(0, "opacity:1"), (WIND, "opacity:1"), (WIND + .001, "opacity:0"), (ATTACK_END, "opacity:0"), (ATTACK_END + .001, "opacity:1")]))
        kfs.append(keyframes(f"{p}-pose12", [(0, "opacity:0"), (WIND, "opacity:0"), (WIND + .001, "opacity:1"), (ATTACK_END, "opacity:1"), (ATTACK_END + .001, "opacity:0")]))
        rules.append(f"{scope} .{p}-pose12{{animation:{p}-pose12 {P:g}s linear infinite}}")
        rules.append(f"{scope} .{p}-pose0{{animation:{p}-pose0 {P:g}s linear infinite}}{scope} .{p}-pose1{{animation:{p}-pose1 {P:g}s linear infinite}}"
                     f"{scope} .{p}-pose2{{animation:{p}-pose2 {P:g}s linear infinite}}")
        # fire: leaves the mouth and hits the boss (it flashes white, sparks fly); then the boss falls with its points
        mx, my = self.mouth
        for k, b in enumerate(self.B):
            tx, ty = b["hit"]
            flash, spark = [(0, "opacity:0")], [(0, "opacity:0;transform:translate(0,0)")]
            for n, (t0, t1) in enumerate(self.fire[k]):
                kfs.append(keyframes(f"{p}-fire{k}{n}", [(0, "opacity:0"), (t0 - 0.001, f"opacity:0;transform:translate({mx:.1f}px,{my:.1f}px)"),
                                                         (t0, f"opacity:1;transform:translate({mx:.1f}px,{my:.1f}px)"),
                                                         (t1, f"opacity:1;transform:translate({tx:.1f}px,{ty:.1f}px)"),
                                                         (t1 + 0.001, f"opacity:0;transform:translate({tx:.1f}px,{ty:.1f}px)")]))
                rules.append(f"{scope} .{p}-fire{k}{n}{{animation:{p}-fire{k}{n} {P:g}s linear infinite}}")
                flash += [(t1, "opacity:0"), (t1 + .001, "opacity:.85"), (t1 + .1, "opacity:0"), (t1 + .17, "opacity:.85"), (t1 + .26, "opacity:0")]
                spark += [(t1, "opacity:0;transform:translate(0,0)"), (t1 + .001, "opacity:1;transform:translate(0,0)"), (t1 + .4, "opacity:0;transform:translate(var(--dx),var(--dy))")]
            kfs.append(keyframes(f"{p}-flash{k}", flash))
            kfs.append(keyframes(f"{p}-spark{k}", spark))
            rules.append(f"{scope} .{p}-flash{k}{{animation:{p}-flash{k} {P:g}s linear infinite}}{scope} .{p}-spark{k}{{animation:{p}-spark{k} {P:g}s ease-out infinite}}")
        kfs.append(keyframes(f"{p}-pts", [(0, "opacity:0;transform:translateY(0)"), (DOWN, "opacity:0;transform:translateY(0)"), (DOWN + .05, "opacity:1;transform:translateY(0)"),
                                          (P - 0.1, f"opacity:0;transform:translateY({-26 * sc:.0f}px)")]))
        rules.append(f"{scope} .{p}-pts{{animation:{p}-pts {P:g}s ease-out infinite}}")
        # attacks
        for k in range(4):
            self._attack(k)                            # (re)builds self.akf[k]
        kfs += [self.akf[k] for k in range(4)]
        rules.append(f"{scope} .{p}-cac{{animation:{p}-cac {P:g}s linear infinite}}{scope} .{p}-roll{{animation:{p}-roll {P:g}s linear infinite}}"
                     f"{scope} .{p}-spit{{animation:{p}-spit {P:g}s linear infinite}}{scope} .{p}-meteor{{animation:{p}-meteor {P:g}s linear infinite}}")
        land_t = ATTACK + 0.6
        kfs.append(keyframes(f"{p}-ring", [(0, "opacity:0"), (ATTACK + .1, "opacity:0"), (ATTACK + .15, "opacity:.9"), (land_t, "opacity:.2"), (land_t + .001, "opacity:0")]))
        rules.append(f"{scope} .{p}-ring{{animation:{p}-ring {P:g}s linear infinite}}")
        # the T-rex: legs, the jump
        dur, apex = self.jump_dur, self.jump_apex
        t0 = JUMP_AT - dur / 2
        jump = [(0, "transform:translateY(0)"), (t0, "transform:translateY(0)")]
        for i in range(1, 24):
            t = t0 + dur * i / 24
            uu = (t - JUMP_AT) / (dur / 2)
            jump.append((t, f"transform:translateY({-apex * (1 - uu * uu):.1f}px)"))
        jump.append((t0 + dur, "transform:translateY(0)"))
        kfs.append(keyframes(f"{p}-jump", jump))
        kfs.append(keyframes(f"{p}-air", [(0, "opacity:0"), (t0, "opacity:0"), (t0 + .001, "opacity:1"), (t0 + dur, "opacity:1"), (t0 + dur + .001, "opacity:0")]))
        kfs.append(keyframes(f"{p}-stride", [(0, "opacity:1"), (t0, "opacity:1"), (t0 + .001, "opacity:0"), (t0 + dur, "opacity:0"), (t0 + dur + .001, "opacity:1")]))
        kfs.append("@keyframes %s-legA{0%%{opacity:1}50%%{opacity:0}100%%{opacity:1}}@keyframes %s-legB{0%%{opacity:0}50%%{opacity:1}100%%{opacity:0}}" % (p, p))
        rules.append(f"{scope} .{p}-jump{{animation:{p}-jump {P:g}s linear infinite}}{scope} .{p}-air{{animation:{p}-air {P:g}s linear infinite}}"
                     f"{scope} .{p}-stride{{animation:{p}-stride {P:g}s linear infinite}}"
                     f"{scope} .{p}-legA{{animation:{p}-legA .24s steps(1,end) infinite}}{scope} .{p}-legB{{opacity:0;animation:{p}-legB .24s steps(1,end) infinite}}")
        # scenery motion
        tile_s = 200 / self.speed
        span = 900 * self.backs
        kfs.append(f"@keyframes {p}-ground{{from{{transform:translateX(0)}}to{{transform:translateX(-200px)}}}}")
        kfs.append(f"@keyframes {p}-drift{{from{{transform:translateX(0)}}to{{transform:translateX({-span:.0f}px)}}}}")
        kfs.append(f"@keyframes {p}-bob{{0%,100%{{transform:translateY({-7 * sc:.1f}px)}}50%{{transform:translateY({7 * sc:.1f}px)}}}}")
        kfs.append(f"@keyframes {p}-sway2{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY({5 * sc:.1f}px)}}}}")
        kfs.append(f"@keyframes {p}-sway{{0%,100%{{transform:translateX(0)}}50%{{transform:translateX({-40 * sc:.0f}px)}}}}")
        kfs.append(f"@keyframes {p}-flow{{to{{stroke-dashoffset:-32}}}}")
        kfs.append(f"@keyframes {p}-glow{{0%,100%{{opacity:.25}}50%{{opacity:.6}}}}")
        kfs.append(f"@keyframes {p}-shoot{{0%{{transform:translate(0,0);opacity:0}}6%{{opacity:1}}30%{{transform:translate({-260 * sc:.0f}px,{90 * sc:.0f}px);opacity:0}}100%{{transform:translate({-260 * sc:.0f}px,{90 * sc:.0f}px);opacity:0}}}}")
        rules.append(f"{scope} .{p}-ground{{animation:{p}-ground {tile_s:.4f}s linear infinite}}{scope} .{p}-drift{{animation:{p}-drift {span / (self.speed * 0.12):.1f}s linear infinite}}"
                     f"{scope} .{p}-bob{{animation:{p}-bob 1.6s ease-in-out infinite}}{scope} .{p}-sway2{{animation:{p}-sway2 1.3s ease-in-out infinite}}"
                     f"{scope} .{p}-sway{{animation:{p}-sway 9s ease-in-out infinite}}{scope} .{p}-flow{{animation:{p}-flow 1.2s linear infinite}}"
                     f"{scope} .{p}-glow{{animation:{p}-glow 1.6s ease-in-out infinite}}{scope} .{p}-shoot{{animation:{p}-shoot 3.4s linear infinite}}")
        if reduced_static:
            rules.append(f"@media (prefers-reduced-motion:reduce){{{scope} [class^='{p}-'],{scope} [class*=' {p}-']{{animation:none!important}}"
                         f"{scope} .{p}-cac{{transform:translateX({self.W * 0.55:.0f}px)}}}}")
        return "".join(rules) + "".join(kfs)
