#!/usr/bin/env python3
"""Recolour this profile README, as one theme or a mix of themes.

    python tools/theme.py                         # list themes and show what is applied now
    python tools/theme.py cyan                    # one theme for everything
    python tools/theme.py green about=blue        # green everywhere, but the About section blue
    python tools/theme.py about=violet            # change just one section, keep the rest as it is
    python tools/theme.py projects=cyan bitnote=rose game=orange
    python tools/theme.py about=same              # drop an override (back to the base theme)

A bare theme name sets the base theme and clears every override. `section=theme` overrides one
section; `card=theme` overrides a single project card (cards otherwise follow `projects`).

Sections: header (banner, typing line, badge row), about (About card + Tech Stack),
projects (the project cards), activity (GitHub stats + LeetCode), connect (Let's Connect) and
game (the playable game page).

What it regenerates: dino-banner.svg (+ dino-banner-mobile.svg), about-card.svg, projects/*.svg, connect/*.svg,
stats/*.svg (from the numbers saved in tools/stats.json), dino/index.html
and the colour codes inside README.md (each region of the README follows its own section's theme).
It needs Python 3 and Pillow (`pip install pillow`). Nothing else.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.dont_write_bytecode = True
import theme_colors  # noqa: E402

STATE = os.path.join(TOOLS, "theme.json")

SECTIONS = {
    "header": "banner, typing line and badge row",
    "about": "About card and Tech Stack",
    "projects": "the project cards",
    "activity": "GitHub stats and LeetCode",
    "connect": "Let's Connect",
    "game": "the playable game page",
}
CARDS = ["bitcareer", "bitnote", "datapilot", "business-bytes", "portfolio",   # keep in sync with gen_projects.py
         "virtual-arcade-zone", "leetcode-solutions"]
MARK = re.compile(r"(<!-- theme:(\w+) -->)")                                    # region markers inside README.md


# ------------------------------------------------------------------ state
def load():
    try:
        with open(STATE) as f:
            raw = json.load(f)
    except (OSError, ValueError):
        raw = {}
    base = raw.get("theme", theme_colors.DEFAULT)
    if base not in theme_colors.THEMES:
        base = theme_colors.DEFAULT
    keys = set(SECTIONS) | set(CARDS)
    over = {k: v for k, v in (raw.get("sections") or {}).items() if k in keys and v in theme_colors.THEMES and v != base}
    return {"theme": base, "sections": over}


def save(state):
    out = {"theme": state["theme"], "accent": theme_colors.Theme(state["theme"]).accent}
    if state["sections"]:
        out["sections"] = dict(sorted(state["sections"].items()))
    with open(STATE, "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")


def parse(args, state):
    """Apply command-line words to the saved state; returns the new state."""
    state = {"theme": state["theme"], "sections": dict(state["sections"])}
    bare = [a for a in args if "=" not in a]
    if len(bare) > 1:
        raise SystemExit(f"give at most one base theme, got: {', '.join(bare)}")
    if bare:
        name = bare[0].lower()
        if name not in theme_colors.THEMES:
            raise SystemExit(f"unknown theme {name!r}; choose one of: {', '.join(theme_colors.THEMES)}")
        state = {"theme": name, "sections": {}}
    for a in args:
        if "=" not in a:
            continue
        key, _, val = a.partition("=")
        key, val = key.strip().lower(), val.strip().lower()
        if key not in SECTIONS and key not in CARDS:
            raise SystemExit(f"unknown section {key!r}; choose one of: {', '.join(list(SECTIONS) + CARDS)}")
        if val in ("same", "default", "base", ""):
            state["sections"].pop(key, None)
        elif val not in theme_colors.THEMES:
            raise SystemExit(f"unknown theme {val!r} for {key}; choose one of: {', '.join(theme_colors.THEMES)}")
        else:
            state["sections"][key] = val
    state["sections"] = {k: v for k, v in state["sections"].items() if v != state["theme"]}
    return state


def effective(state):
    """(theme per section, theme per project card)."""
    sec = {k: state["sections"].get(k, state["theme"]) for k in SECTIONS}
    cards = {c: state["sections"].get(c, sec["projects"]) for c in CARDS}
    return sec, cards


def summary(state):
    if not state["sections"]:
        return state["theme"]
    return f"{state['theme']} (" + ", ".join(f"{k}={v}" for k, v in sorted(state["sections"].items())) + ")"


# ------------------------------------------------------------------ generators
def run(script, out_dir, theme, *extra):
    env = dict(os.environ, RAHUL_THEME=theme, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, os.path.join(TOOLS, script), out_dir, *extra], env=env, cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"{script} failed")


def build_projects(cards):
    """One generator run per distinct theme; each card file is taken from the run with its own theme."""
    dest = os.path.join(ROOT, "projects")
    by_theme = {}
    for slug, th in cards.items():
        by_theme.setdefault(th, []).append(slug)
    if len(by_theme) == 1:
        run("gen_projects.py", dest, next(iter(by_theme)))
        return
    for th, slugs in by_theme.items():
        with tempfile.TemporaryDirectory() as tmp:
            run("gen_projects.py", tmp, th)
            for slug in slugs:
                shutil.copyfile(os.path.join(tmp, slug + ".svg"), os.path.join(dest, slug + ".svg"))


def recolour_readme(sec):
    """Swap every known accent hex (as written in README URLs, no leading #) inside each marked region."""
    path = os.path.join(ROOT, "README.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    # heal stray region names left right after a marker by an earlier version of this tool
    text = re.sub(r"(<!-- theme:(\w+) -->)(?:\2)+", r"\1", text)
    pieces = MARK.split(text)          # [before, marker, name, body, marker, name, body, ...]
    out, count = [pieces[0]], 0
    for i in range(1, len(pieces), 3):
        marker, name, body = pieces[i], pieces[i + 1], pieces[i + 2]
        if name not in sec:
            raise SystemExit(f"README.md has an unknown theme region <!-- theme:{name} -->")
        new = theme_colors.Theme(sec[name]).bare
        for old in theme_colors.all_accents():
            if old != new:
                body, n = re.subn(old, new, body, flags=re.I)
                count += n
        out += [marker, body]          # the captured name is not part of the text, so it is not written back
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(out))
    return count


def apply(state):
    sec, cards = effective(state)
    run("gen_dino.py", ROOT, sec["header"])                       # dino-banner(-mobile).svg (+ a game page in the same colour)
    if sec["game"] != sec["header"]:                              # the game page has its own theme
        with tempfile.TemporaryDirectory() as tmp:
            run("gen_dino.py", tmp, sec["game"])
            shutil.copyfile(os.path.join(tmp, "dino", "index.html"), os.path.join(ROOT, "dino", "index.html"))
    run("gen_about.py", ROOT, sec["about"])                       # about-card.svg
    build_projects(cards)                                         # projects/*.svg
    run("gen_connect.py", ROOT, sec["connect"])                   # connect/*.svg
    run("gen_stats.py", ROOT, sec["activity"])                    # stats/*.svg (saved numbers, no network)
    changed = recolour_readme(sec)
    save(state)
    print(f"Applied {summary(state)}; recoloured {changed} README colour codes.")


def show(state):
    cur = state["theme"]
    print("Themes:")
    for n, t in theme_colors.THEMES.items():
        print(f"  {'*' if n == cur else ' '} {n:7s} {t['accent']}")
    sec, cards = effective(state)
    print("\nApplied now:")
    for k, why in SECTIONS.items():
        print(f"  {k:9s} {sec[k]:7s} {why}")
    odd = {c: t for c, t in cards.items() if t != sec["projects"]}
    for c, t in odd.items():
        print(f"  {c:9s} {t:7s} (project card)")
    print("\nOne theme:   python tools/theme.py <name>")
    print("Mix themes:  python tools/theme.py <name> about=<name> projects=<name> game=<name> ...")
    print("One section: python tools/theme.py about=<name>        (keeps everything else)")


def main():
    args = sys.argv[1:]
    state = load()
    if "--summary" in args:
        print(summary(state))
        return
    if not args or args[0] in ("list", "-l", "--list"):
        show(state)
        return
    apply(parse(args, state))


if __name__ == "__main__":
    main()
