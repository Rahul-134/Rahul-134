# Theme switcher

One command recolours the whole profile: the banner and its dino, the About card, every
project card, Let's Connect, the playable game page, and the colour codes inside the README's
badges and stat cards. You can use one theme everywhere, or **mix themes section by section**
(for example a green banner with a blue About card and violet project cards).

Themes: `yellow` (original), `orange`, `rose`, `violet`, `blue`, `cyan`, and `green` (a nature
theme: leaf-green dino on sage-olive cacti, so the two don't blend together).

## Switch from GitHub (one click)

1. Open the **Actions** tab of this repo.
2. Pick **Switch theme** in the left list, then **Run workflow**.
3. Choose what you want, then run it. After about half a minute the profile is recoloured:
   * **theme**: one colour for the whole profile (this also clears any mix).
   * **header / about / projects / activity / connect / game**: a colour for just that section.
   * **extra**: single project cards, e.g. `bitnote=rose datapilot=cyan`.
   * Anything left on `keep` stays exactly as it is, so you can change one section at a time.

## Switch locally

```bash
pip install pillow
python tools/theme.py                                   # list themes and what is applied now
python tools/theme.py violet                            # one theme for everything
python tools/theme.py green about=blue projects=violet  # green base, with two sections overridden
python tools/theme.py game=orange                       # change one section, keep the rest
python tools/theme.py about=same                        # drop an override (back to the base theme)
git add -A && git commit -m "Switch theme" && git push
```

A bare theme name sets the base and clears every override; `section=theme` words then override
individual sections.

| Section | What it covers |
|---|---|
| `header` | the banner, the typing line and the badge row |
| `about` | the About card and the Tech Stack |
| `projects` | all project cards |
| `activity` | the GitHub stats and LeetCode section |
| `connect` | the Let's Connect section |
| `game` | the playable game page (`dino/index.html`) |

Single project cards follow `projects` unless you override them by name: `bitcareer`, `bitnote`,
`datapilot`, `business-bytes`, `portfolio`, `virtual-arcade-zone`, `leetcode-solutions`.

The current state is kept in `tools/theme.json`. The README is split into regions by the
`<!-- theme:... -->` comments in `README.md`; each region is recoloured with its own section's
theme, so keep those comments in place when you edit the README.

## Add your own colour

Add one line to `THEMES` in `tools/theme_colors.py` (and the same name to each dropdown in
`.github/workflows/theme.yml`):

```python
"mint": {"accent": "#34D399"},
```

The darker shade and lighter highlight that shade the pixel dino are derived automatically.
To recolour the cacti as well, add `"cactus": {"G": ..., "g": ..., "h": ..., "S": ...}` (see `green`).

## What lives here

| File | Purpose |
|---|---|
| `theme.py` | the command above; regenerates everything and recolours each README region |
| `theme_colors.py` | the theme list and colour maths |
| `sprites.py` | the shared pixel art (dino, cacti, birds) |
| `gen_dino.py` | the `dino/` game page, and the README banner via `banner.py` |
| `banner.py` | `dino-banner.svg` (wide) and `dino-banner-mobile.svg` (phones); the README picks one with a `<picture>` media query |
| `gen_about.py` | `about-card.svg` |
| `gen_projects.py` | the `projects/*.svg` cards |
| `gen_connect.py` | the `connect/*.svg` art for Let's Connect |
| `assets/` | the screenshots embedded in the project cards |

The generated files are committed, so the profile works without running anything. The
tools only run when you change the theme.

## What the theme tool leaves alone

`dino/leaderboard.js` and `dino/leaderboard-config.js` are hand-written, not generated, so changing the theme never touches them. The leaderboard reads the accent colour from the game page's CSS, so it follows the theme automatically. See `leaderboard/README.md`.
