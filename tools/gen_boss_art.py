#!/usr/bin/env python3
"""Turn the boss artwork into pixel sprites for the game.

    python3 tools/gen_boss_art.py            # reads tools/boss_art/*.webp, writes tools/boss_art.json

Each image (made with ChatGPT) shows one boss in three poses side by side: idle, wind-up (the warning before an
attack) and attack. For each pose this script cuts the boss out of its background, snaps it to a pixel grid and
keeps a small palette per boss. The game page embeds the result (tools/gen_dino.py) and draws the bosses like
every other sprite, crisp at any screen size (the size of a cell is BOSS_U in tools/index.template.html).

Cutting out: the Star Dragon and the Sky Tyrant sit on a flat colour, which is keyed out. The Golem and the
Serpent have scenery behind them, so everything enclosed by the boss's dark outline is kept and the rest is
scenery. Only the biggest piece of each pose is kept (thrown rocks, fireballs and speed lines are dropped:
the game draws its own).
"""
import json
import os
from collections import deque

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(HERE, "boss_art")
OUT = os.path.join(HERE, "boss_art.json")
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

# name: how to cut it out, its size in cells (along the given side), palette size,
# and which point of the pose stays put between frames
BOSSES = {
    "tyrant":  dict(cut="key", bg=(173, 231, 248), tol=42, cells=("w", 78), colours=14, anchor="mass",
                    keep=["#FB933E", "#D5D1F0"]),                       # orange beak, pale belly
    "golem":   dict(cut="outline", cells=("h", 64), colours=16, anchor="bottom-right",
                    keep=["#8FB233", "#F9C24A"],                        # moss, amber eyes
                    erase={2: (70, 48)}),                               # throw pose: dust kicked up behind the back foot
    "serpent": dict(cut="outline", cells=("h", 70), colours=16, anchor="bottom-right", pool=True),
    "dragon":  dict(cut="key", bg=(251, 4, 251), tol=90, cells=("w", 82), colours=18, anchor="mass",
                    poses=[0, 1, 0]),                                   # its attack art breathes a fire stream; the game
}                                                                      # throws its own fireball, so it attacks from idle
# keep: colours that are small in area but matter (they get their own palette entry instead of being averaged away)
# poses: which drawn pose to use for idle, wind-up and attack
WORK = 2          # segment at half resolution (enough for a 2-unit grid, and quick)


def components(mask):
    """Label 4-connected True regions; returns (labels, sizes)."""
    h, w = mask.shape
    labels = np.zeros((h, w), np.int32)
    sizes = [0]
    for y0, x0 in zip(*np.nonzero(mask)):
        if labels[y0, x0]:
            continue
        n = len(sizes); sizes.append(0)
        q = deque([(y0, x0)]); labels[y0, x0] = n
        while q:
            y, x = q.popleft(); sizes[n] += 1
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and mask[yy, xx] and not labels[yy, xx]:
                    labels[yy, xx] = n; q.append((yy, xx))
    return labels, sizes


def cut_out(rgb, spec):
    """True where the boss is."""
    if spec["cut"] == "key":
        d = np.sqrt(((rgb - np.array(spec["bg"], float)) ** 2).sum(-1))
        mask = d > spec["tol"]
        labels, _ = components(~mask)                 # a gap the boss fully encloses is part of it (a pale belly
        border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}   # close to the sky)
        return ~np.isin(labels, list(border))
    # outline: very dark pixels form the outline; scenery is whatever the border can reach without crossing it
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    outline = lum < 72
    labels, _ = components(~outline)
    border = set(np.unique(np.concatenate([labels[0], labels[-1], labels[:, 0], labels[:, -1]]))) - {0}
    scenery = np.isin(labels, list(border))
    return ~scenery


def poses(mask):
    """Split the sheet into its three poses and keep the biggest piece of each: [(y0, y1, x0, x1, piece_mask)]."""
    h, w = mask.shape
    out = []
    for i in range(3):
        a, b = w * i // 3, w * (i + 1) // 3
        labels, sizes = components(mask[:, a:b])
        if len(sizes) < 2:
            raise SystemExit("no boss found in a pose")
        big = int(np.argmax(sizes[1:])) + 1
        piece = labels == big
        ys, xs = np.nonzero(piece)
        out.append((ys.min(), ys.max() + 1, a + xs.min(), a + xs.max() + 1, piece[ys.min():ys.max() + 1, xs.min():xs.max() + 1]))
    return out


def prune(rows, passes=2):
    """Drop one-cell-wide strands (speed lines and dust wisps that touch the boss)."""
    g = [list(r) for r in rows]
    h, w = len(g), len(g[0])
    for _ in range(passes):
        drop = [(y, x) for y in range(h) for x in range(w) if g[y][x] != "." and
                sum(1 for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1))
                    if 0 <= yy < h and 0 <= xx < w and g[yy][xx] != ".") <= 1]
        for y, x in drop:
            g[y][x] = "."
    # anything that isn't part of a solid 2x2 block is a hairline (dust trails, motion streaks)
    solid = lambda y, x: 0 <= y < h and 0 <= x < w and g[y][x] != "."
    thick = set()
    for y in range(h - 1):
        for x in range(w - 1):
            if solid(y, x) and solid(y + 1, x) and solid(y, x + 1) and solid(y + 1, x + 1):
                thick.update(((y, x), (y + 1, x), (y, x + 1), (y + 1, x + 1)))
    for y in range(h):
        for x in range(w):
            if g[y][x] != "." and (y, x) not in thick:
                g[y][x] = "."
    # keep the boss itself: the biggest connected piece
    seen, best = set(), []
    for y in range(h):
        for x in range(w):
            if g[y][x] != "." and (y, x) not in seen:
                part, todo = [], [(y, x)]
                seen.add((y, x))
                while todo:
                    cy, cx = todo.pop()
                    part.append((cy, cx))
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if solid(ny, nx) and (ny, nx) not in seen:
                            seen.add((ny, nx))
                            todo.append((ny, nx))
                if len(part) > len(best):
                    best = part
    keep = set(best)
    return ["".join(c if (y, x) in keep else "." for x, c in enumerate(r)) for y, r in enumerate(g)]


def build(name, spec):
    im = Image.open(os.path.join(ART, name + ".webp")).convert("RGB")
    im = im.resize((im.width // WORK, im.height // WORK), Image.NEAREST)
    rgb = np.asarray(im).astype(float)
    mask = cut_out(rgb, spec)
    found = poses(mask)
    if spec.get("pool"):                          # the Serpent: drop its lava pool (the game draws its own)
        trimmed = []
        for y0, y1, x0, x1, m in found:
            sub = rgb[y0:y1, x0:x1]
            lava = (sub[..., 0] > 200) & (sub[..., 1] > 90) & (sub[..., 2] < 120) & m
            rows = lava.sum(1) / np.maximum(1, m.sum(1))
            cut = len(rows)
            for r in range(len(rows) - 1, len(rows) // 2, -1):
                if rows[r] > 0.55: cut = r
                elif cut < len(rows): break
            trimmed.append((y0, y0 + cut, x0, x1, m[:cut]))
        found = trimmed
    # one scale for all three poses, from the idle pose
    side, n = spec["cells"]
    y0, y1, x0, x1, _ = found[0]
    scale = ((x1 - x0) if side == "w" else (y1 - y0)) / n            # source pixels per game cell
    # one palette for the boss, from all its pixels
    pix = np.concatenate([rgb[a:b, c:d][m] for a, b, c, d, m in found]).astype(np.uint8)
    pal_img = Image.fromarray(pix.reshape(1, -1, 3)).quantize(colors=spec["colours"], method=Image.Quantize.MEDIANCUT)
    pal = np.array(pal_img.getpalette()[:3 * spec["colours"]]).reshape(-1, 3)
    for hx in spec.get("keep", []):
        pal = np.vstack([pal, [int(hx[i:i + 2], 16) for i in (1, 3, 5)]])
    frames = []
    for i, (a, b, c, d, m) in enumerate(found):
        sub = rgb[a:b, c:d]
        H, Wd = max(1, round((b - a) / scale)), max(1, round((d - c) / scale))
        idx = np.argmin(((sub[..., None, :] - pal[None, None]) ** 2).sum(-1), -1)
        rows = []
        for gy in range(H):
            row = ""
            for gx in range(Wd):
                ya, yb = int(gy * scale), max(int(gy * scale) + 1, int((gy + 1) * scale))
                xa, xb = int(gx * scale), max(int(gx * scale) + 1, int((gx + 1) * scale))
                cm = m[ya:yb, xa:xb]
                if cm.size == 0 or cm.mean() < 0.5:
                    row += "."; continue
                vals = idx[ya:yb, xa:xb][cm]
                row += LETTERS[int(np.bincount(vals, minlength=len(pal)).argmax())]
            rows.append(row.rstrip(".") or ".")
        width = max(len(r) for r in rows)
        rows = [r.ljust(width, ".") for r in rows]
        if i in spec.get("erase", {}):                                  # clear everything right of x and below y
            ex, ey = spec["erase"][i]
            rows = [r[:ex] + "." * (width - ex) if y >= ey else r for y, r in enumerate(rows)]
        rows = prune(rows)
        while len(rows) > 1 and not rows[-1].strip("."):                  # what was erased may leave empty rows below the feet
            rows.pop()
        frames.append({"rows": rows, "src": [int(a), int(b), int(c), int(d)]})
    # line the poses up: work out each pose's anchor in cells
    for f, (a, b, c, d, m) in zip(frames, found):
        if spec["anchor"] == "mass":
            ys, xs = np.nonzero(m); f["ax"], f["ay"] = round(xs.mean() / scale, 1), round(ys.mean() / scale, 1)
        else:
            f["ax"], f["ay"] = len(f["rows"][0]), len(f["rows"])                  # bottom-right corner
    frames = [frames[i] for i in spec.get("poses", [0, 1, 2])]
    used = sorted({ch for f in frames for r in f["rows"] for ch in r if ch != "."})
    return {"pal": {ch: "#%02X%02X%02X" % tuple(int(v) for v in pal[LETTERS.index(ch)]) for ch in used},
            "anchor": spec["anchor"], "frames": frames}


def main():
    out = {name: build(name, spec) for name, spec in BOSSES.items()}
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    for name, b in out.items():
        print(name, [f"{len(f['rows'][0])}x{len(f['rows'])}" for f in b["frames"]], len(b["pal"]), "colours")


if __name__ == "__main__":
    main()
