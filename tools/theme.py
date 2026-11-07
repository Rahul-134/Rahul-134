#!/usr/bin/env python3
"""Switch the accent colour of this whole profile README in one go.

    python tools/theme.py            # list themes and show the current one
    python tools/theme.py cyan       # apply a theme

What it regenerates (everything that used to be yellow):
  * dino-banner.svg, about-card.svg and projects/*.svg
  * dino/index.html (the playable game)
  * the colour codes inside README.md badges and stat cards
It needs Python 3 and Pillow (`pip install pillow`). Nothing else.
"""
import json
import os
import re
import subprocess
import sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.dont_write_bytecode = True
import theme_colors  # noqa: E402

STATE = os.path.join(TOOLS, "theme.json")


def saved():
    try:
        with open(STATE) as f:
            return json.load(f).get("theme", theme_colors.DEFAULT)
    except (OSError, ValueError):
        return theme_colors.DEFAULT


def run(script, *args, env):
    r = subprocess.run([sys.executable, os.path.join(TOOLS, script), *args], env=env, cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        raise SystemExit(f"{script} failed")


def recolour_readme(theme):
    """Swap every known accent hex (as written in README URLs, no leading #) for the new one."""
    path = os.path.join(ROOT, "README.md")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new = theme.bare
    count = 0
    for old in theme_colors.all_accents():
        if old != new:
            text, n = re.subn(old, new, text, flags=re.I)
            count += n
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return count


def apply(name):
    theme = theme_colors.Theme(name)
    env = dict(os.environ, RAHUL_THEME=name, PYTHONDONTWRITEBYTECODE="1")
    run("gen_dino.py", ROOT, env=env)              # dino-banner.svg + dino/index.html
    run("gen_about.py", ROOT, env=env)             # about-card.svg
    run("gen_projects.py", os.path.join(ROOT, "projects"), env=env)
    changed = recolour_readme(theme)
    with open(STATE, "w") as f:
        json.dump({"theme": name, "accent": theme.accent}, f, indent=2)
        f.write("\n")
    print(f"Applied theme '{name}' ({theme.accent}); recoloured {changed} README colour codes.")


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("list", "-l", "--list"):
        cur = saved()
        print("Themes:")
        for n, t in theme_colors.THEMES.items():
            print(f"  {'*' if n == cur else ' '} {n:7s} {t['accent']}")
        print("\nApply one with:  python tools/theme.py <name>")
        return
    apply(args[0].lower())


if __name__ == "__main__":
    main()
