# Theme switcher

One command recolours the whole profile: the banner and its dino, the About card, every
project card, the playable game page, and the colour codes inside the README's badges and
stat cards.

## Switch from GitHub (one click)

1. Open the **Actions** tab of this repo.
2. Pick **Switch theme** in the left list, then **Run workflow**.
3. Choose a colour and run it. After about half a minute the profile is recoloured.

Themes: `yellow` (original), `orange`, `rose`, `violet`, `blue`, `cyan`, and `green` (a nature
theme: leaf-green dino on bark-brown cacti, so the two don't blend together).

## Switch locally

```bash
pip install pillow
python tools/theme.py            # list themes, shows the current one
python tools/theme.py violet     # apply a theme
git add -A && git commit -m "Switch theme to violet" && git push
```

## Add your own colour

Add one line to `THEMES` in `tools/theme_colors.py` (and the same name to the dropdown in
`.github/workflows/theme.yml`):

```python
"mint": {"accent": "#34D399"},
```

The darker shade and lighter highlight that shade the pixel dino are derived automatically.
To recolour the cacti as well, add `"cactus": {"G": ..., "g": ..., "h": ..., "S": ...}` (see `green`).

## What lives here

| File | Purpose |
|---|---|
| `theme.py` | the command above; regenerates everything and recolours the README |
| `theme_colors.py` | the theme list and colour maths |
| `sprites.py` | the shared pixel art (dino, cacti, birds) |
| `gen_dino.py` | `dino-banner.svg` and the `dino/` game page |
| `gen_about.py` | `about-card.svg` |
| `gen_projects.py` | the `projects/*.svg` cards |
| `assets/` | the screenshots embedded in the project cards |

The generated files are committed, so the profile works without running anything. The
tools only run when you change the theme.

## What the theme tool leaves alone

`dino/leaderboard.js` and `dino/leaderboard-config.js` are hand-written, not generated, so changing the theme never touches them. The leaderboard reads the accent colour from the game page's CSS, so it follows the theme automatically. See `leaderboard/README.md`.
