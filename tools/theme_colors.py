"""Accent themes. Everything yellow in this profile flows from one of these entries.

Add a theme by adding a line to THEMES. Only `accent` is required; the darker shade and
lighter highlight (used to shade the pixel dino) are derived unless you give them. A theme can
also recolour the cacti with `cactus` ({"G": body, "g": shadow, "h": highlight, "S": spines}),
which `green` does so the dino does not blend into green cacti.
"""
import colorsys
import os

THEMES = {
    # name: accent (and optional exact shade / highlight)
    "yellow": {"accent": "#E8D44D", "shade": "#B09B28", "light": "#F6EC9A"},   # the original look
    "orange": {"accent": "#FB923C"},
    "rose":   {"accent": "#FB7185"},
    "violet": {"accent": "#A78BFA"},
    "blue":   {"accent": "#60A5FA"},
    "cyan":   {"accent": "#22D3EE"},
    # nature: leaf-green dino on sage-olive cacti
    "green":  {"accent": "#4ADE80", "cactus": {"G": "#6B8F52", "g": "#43602F", "h": "#9CBF80", "S": "#E6EBD2"}},
}
DEFAULT = "yellow"


def _rgb(hex_):
    h = hex_.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _hex(rgb):
    return "#%02X%02X%02X" % tuple(round(max(0.0, min(1.0, v)) * 255) for v in rgb)


def derive(accent):
    h, l, s = colorsys.rgb_to_hls(*_rgb(accent))
    shade = colorsys.hls_to_rgb(h, l * 0.70, s * 0.95)
    light = colorsys.hls_to_rgb(h, min(0.93, l + 0.17), s * 0.90)
    return _hex(shade), _hex(light)


def trim_of(accent):
    """Belly, belly stripes and back spikes of the dino: the accent's hue turned 75 degrees, so they
    always contrast with the body (blue on the green theme)."""
    h, l, sat = colorsys.rgb_to_hls(*_rgb(accent))
    hb = (h + 75 / 360) % 1
    return (_hex(colorsys.hls_to_rgb(hb, 0.74, 0.80)), _hex(colorsys.hls_to_rgb(hb, 0.58, 0.70)),
            _hex(colorsys.hls_to_rgb(hb, 0.58, 0.75)))


def outline_of(accent):
    h, l, sat = colorsys.rgb_to_hls(*_rgb(accent))
    return _hex(colorsys.hls_to_rgb(h, l * 0.36, min(1.0, sat * 0.95)))


class Theme:
    def __init__(self, name):
        if name not in THEMES:
            raise SystemExit(f"unknown theme {name!r}; choose one of: {', '.join(THEMES)}")
        t = THEMES[name]
        self.name = name
        self.accent = t["accent"].upper()
        self.cactus = {k: v.upper() for k, v in t.get("cactus", {}).items()}
        d, l = derive(self.accent)
        self.shade = t.get("shade", d).upper()
        self.light = t.get("light", l).upper()
        self.outline = outline_of(self.accent)
        self.belly, self.stripe, self.spike = trim_of(self.accent)
        r, g, b = (int(round(v * 255)) for v in _rgb(self.accent))
        self.rgb = f"{r},{g},{b}"
        self.bare = self.accent.lstrip("#")            # as used inside README badge / stat-card URLs


def current():
    """The theme the generators should use (set by tools/theme.py through the environment)."""
    return Theme(os.environ.get("RAHUL_THEME", DEFAULT))


def all_accents():
    return [t["accent"].upper().lstrip("#") for t in THEMES.values()]
