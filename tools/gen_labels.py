#!/usr/bin/env python3
"""Build the README's headings, captions and small link buttons in the Playful style, under labels/.

    python3 gen_labels.py OUT_DIR GROUP...       # writes OUT_DIR/labels/*.svg for the named groups

Groups, each drawn in its own section's (or project card's) theme by tools/theme.py:

    header      link-followers.svg (count from tools/stats.json), link-repositories.svg, link-portfolio.svg, link-linkedin.svg,
                link-leetcode.svg, link-github.svg: the badge row under the banner
    about       h-about-me.svg, h-tech-stack.svg, link-leetcode-profile.svg, link-stats-card.svg
    projects    h-featured-projects.svg, h-more-builds.svg, projects-intro.svg, link-browse-all.svg
    activity    h-github-activity.svg, h-leetcode.svg
    connect     h-lets-connect.svg
    <project>   peek-<project>.svg (the "Peek inside" row), cap-<project>-<n>.svg (one caption per screenshot),
                link-<project>-<name>.svg (the buttons under the card and at the end of the peek), and for
                DataPilot also datapilot-features.svg and datapilot-note.svg

The words live in the lists below. Change one, run `python tools/theme.py about=same` (any theme command
redraws everything), and keep the README's alt text in step. Each file embeds only the letters it uses
(needs `pip install fonttools brotli`; without them the whole font is embedded, which also works).
"""
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import banner  # noqa: E402
import counts  # noqa: E402
from playful import (ACCENT, INK, TEXT, PAPER, PANEL, SKY, e, shell, pill, style, text_width,  # noqa: E402
                     DINO_H, dino, cactus, icon)

LIVE_GREEN = "#5BD68A"
W = 900

# ------------------------------------------------------------------ the words
HEADINGS = {   # file slug: (group, title, icon)
    "about-me": ("about", "About Me", "laptop"),
    "tech-stack": ("about", "Tech Stack", "wrench"),
    "featured-projects": ("projects", "Featured Projects", "rocket"),
    "more-builds": ("projects", "More Builds", "puzzle"),
    "github-activity": ("activity", "GitHub Activity", "chart"),
    "leetcode": ("activity", "LeetCode", "code"),
    "lets-connect": ("connect", "Let's Connect", "chat"),
}

PEEKS = {      # project: (what the row says, count, [(caption title, caption text), ...])
    "bitcareer": ("BitCareer", "5 screens", [
        ("Career Dashboard", "readiness score, resume and GitHub analysis, skill ranks and an AI-written career analysis"),
        ("Learning Workspace", "roadmap sidebar, study notebook and code sandbox in one place"),
        ("AI Interview Dashboard", "configure a session, then review past sessions and score trends"),
        ("Live Interview Session", "speak or type your answer, or switch to the code editor"),
        ("Ask BitBuddy", "a personalised career overview with daily AI insights"),
    ]),
    "bitnote": ("BitNote", "4 screens", [
        ("Sign up & log in", "email and password, or Google Sign-In"),
        ("Home", "all your notebooks in one place"),
        ("Notebook layout", "an AI-generated learning roadmap beside the cell editor"),
        ("In-cell AI", "instant summaries and BitBuddy chat, in context of the cell"),
    ]),
    "datapilot": ("DataPilot", "7 screens", [
        ("Dashboard", "row and column counts, duplicates, nulls, a data health score and a column profile"),
        ("Data cleaning", "pick what to fix and preview the impact before applying"),
        ("Analytics", "ask questions in plain English, by typing or by voice"),
        ("AI web scraper", "URL mode and search mode (beta)"),
        ("ML Trainer · clean", "null counts, duplicates and IQR outlier detection before training"),
        ("ML Trainer · train", "choose a task, a model, the features and the target"),
        ("ML Trainer · results", "metrics, trained models, an auto-built prediction form, and code export"),
    ]),
    "business-bytes": ("Business Bytes", "6 screens", [
        ("Main menu", "start, load a saved game or read how to play"),
        ("Login & sign up", "accounts with live password-strength feedback"),
        ("Player setup", "2–4 players, custom names and tokens"),
        ("Game board", "a circular board of Indian cities"),
        ("Load game", "resume any of your saved games"),
        ("Leaderboard", "net-worth ranking when the game ends"),
    ]),
    "portfolio": ("Portfolio", "a quick tour + 7 screens", [
        ("Quick tour", "hero, skills, tech stack, projects, live stats and the terminal, in dark theme"),
        ("Light & dark", "the hero in both themes, switchable from the nav"),
        ("Skills", "tap a card for its proficiency and the projects where it shipped"),
        ("Tech Stack", "frameworks, databases and tools, filterable by category"),
        ("Stats & streaks", "live GitHub and LeetCode numbers"),
        ("Ask-me-anything terminal", "ask about my projects, skills or experience"),
        ("About", "my story, what I'm exploring now (RAG, agentic AI, MCP) and education"),
        ("Responsive", "the hero on a phone"),
    ]),
}

LINKS = {      # project: [(name, label, kind, icon)]; kind: live (green), main (theme colour) or plain
    "bitcareer": [("repo", "Full write-up in the repository", "plain", "github")],
    "bitnote": [("repo", "Setup, API and deployment notes", "plain", "github")],
    "datapilot": [("live", "Live app", "live", None), ("trainer", "ML Trainer", "main", "model"),
                  ("code", "Source code", "plain", "github")],
    "business-bytes": [("repo", "Design notes in the repository", "plain", "github")],
    "portfolio": [("live", "Live site", "live", None), ("tour", "Take a look around the live site", "plain", "globe")],
}

DATAPILOT_FEATURES = [   # (icon, title, tag, text)
    ("chart", "Dashboard", None, "upload CSV or Excel files for instant stats, a data health score and a column profile"),
    ("sparkle", "Data cleaning", None, "remove duplicates and handle nulls with a live preview, then download the cleaned file"),
    ("chat", "Natural-language analysis", None,
     "ask in plain English (or by voice); Gemini writes the pandas code, which is shown for transparency, and returns the results"),
    ("globe", "AI web scraper", "BETA", "URL and search modes with pagination detection, relevance filtering and a multi-model fallback"),
    ("model", "ML trainer", None,
     "regression and classification with automatic hyperparameter tuning, reports, predictions, seven chart types and Python code export"),
]
DATAPILOT_NOTE = "The screens below are the real app, shown on a made-up sample dataset (used-car listings)."
PROJECTS_INTRO = ("A selection of things I've designed, built and shipped",
                  "Click a card to open the project, or peek inside.")


# ------------------------------------------------------------------ helpers
out_dir = os.path.join(sys.argv[1] if len(sys.argv) > 2 else sys.exit(__doc__), "labels")
os.makedirs(out_dir, exist_ok=True)
written = []


def write(name, svg):
    with open(os.path.join(out_dir, name), "w") as f:
        f.write(svg)
    written.append(name)


def wrap(text, size, width, weight=600):
    """Split text into lines that fit `width`, then even them out so the last line is not a lone word."""
    def greedy(limit):
        lines, cur = [], ""
        for word in text.split():
            nxt = f"{cur} {word}".strip()
            if cur and text_width(nxt, size, weight) > limit:
                lines.append(cur)
                cur = word
            else:
                cur = nxt
        return lines + ([cur] if cur else [])
    lines = greedy(width)
    if len(lines) > 1:                               # narrowest width that still needs no extra line
        limit = width
        while limit > 40 and len(greedy(limit - 8)) == len(lines):
            limit -= 8
        lines = greedy(limit)
    return lines


def svg_open(w, h, title, words, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t">\n'
            f'  <title id="t">{e(title)}</title>\n  {style(extra_css, text=words)}\n')


TAP_CSS = '''
    .tap{animation:tap 2.2s ease-in-out infinite}
    @keyframes tap{0%,100%{transform:translateY(0)}50%{transform:translateY(3px)}}'''


# ------------------------------------------------------------------ section headings: a little sky with the T-rex
def heading(slug, title, kind, n):
    H = 104
    ground = H - 30
    k = 0.62
    dx = W - 150
    words = title
    svg = svg_open(W, H, title, words, '''
    .cl{animation:drift 40s linear infinite}
    @keyframes drift{0%{transform:translateX(0)}50%{transform:translateX(-90px)}100%{transform:translateX(0)}}
    .rays{animation:spin 60s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}''')
    svg += f"""  <defs><clipPath id="sky"><rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="22"/></clipPath>{banner.ground_tile(30)}</defs>
  {shell(W, H, SKY, 22)}
  <g clip-path="url(#sky)">
    {banner.stars(300, 10, 450, ground - 30, 9, seed=3 + n, avoid=[(90, 6, text_width(title, 38) + 30, 70), (W - 340, 4, 110, 50)])}
    {banner.sun(W - 60, 36, 0.62)}
    <g class="cl">{banner.cloud(W - 330, 8 + (n % 2) * 6, 0.5)}</g>
    <g transform="translate(0,{ground - 10})"><rect width="{W}" height="40" fill="url(#sand)"/></g>
    {cactus(dx - 70, ground + 1, "small" if n % 2 else "saguaro", 0.7)}
    <g class="bob" style="animation-delay:{-n * 0.4:.1f}s"><g transform="translate({dx},{ground - DINO_H * k + 1:.1f}) scale({k})">{dino()}</g></g>
  </g>
  <rect x="3" y="3" width="{W - 14}" height="{H - 14}" rx="22" fill="none" stroke="{INK}" stroke-width="4"/>
  <circle cx="60" cy="{ground / 2 + 8:.1f}" r="29" fill="{INK}"/>
  <circle cx="56" cy="{ground / 2 + 4:.1f}" r="29" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>
  {icon(kind, 56, ground / 2 + 4, 34)}
  <text x="102" y="{ground / 2 + 17:.1f}" font-size="38" font-weight="800" fill="{TEXT}">{e(title)}</text>
</svg>
"""
    write(f"h-{slug}.svg", svg)


# ------------------------------------------------------------------ a wide note: icon + one or two lines
def note(name, lines, kind, title):
    H = 92 if len(lines) > 1 else 72
    cy = (3 + H - 11) / 2
    words = " ".join(lines)
    body = []
    if len(lines) > 1:
        body.append(f'<text x="94" y="{cy - 3:.1f}" font-size="21" font-weight="800" fill="{TEXT}">{e(lines[0])}</text>')
        body.append(f'<text x="94" y="{cy + 21:.1f}" font-size="16" font-weight="600" fill="{TEXT}" fill-opacity=".75">{e(lines[1])}</text>')
    else:
        body.append(f'<text x="94" y="{cy + 6:.1f}" font-size="17" font-weight="700" fill="{TEXT}">{e(lines[0])}</text>')
    svg = svg_open(W, H, title, words)
    svg += f"""  {shell(W, H, PAPER, (H - 14) / 2)}
  <g class="bob"><circle cx="54" cy="{cy + 3:.1f}" r="24" fill="{INK}"/><circle cx="51" cy="{cy:.1f}" r="24" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>
  {icon(kind, 51, cy, 28)}</g>
  {"".join(body)}
</svg>
"""
    write(name, svg)


# ------------------------------------------------------------------ "Peek inside" rows (inside <summary>)
def peek(slug, name, count, n):
    H = 88
    cy = (3 + H - 11) / 2
    title = f"Peek inside {name}"
    tap, tap_w = pill(0, 0, "TAP TO PEEK", ACCENT, size=12, h=30)
    chip, _ = pill(96 + text_width(title, 25) + 16, cy - 13, count.upper(), PANEL, size=11, h=26, shadow=False, spacing=1.2)
    words = f"{title} {count.upper()} TAP TO PEEK"
    svg = svg_open(W, H, f"{title}: {count}. Tap to open.", words, TAP_CSS)
    svg += f"""  {shell(W, H, PAPER, 22)}
  <g class="bob" style="animation-delay:{-n * 0.5:.1f}s"><circle cx="55" cy="{cy + 4:.1f}" r="27" fill="{INK}"/>
  <circle cx="52" cy="{cy:.1f}" r="27" fill="{ACCENT}" stroke="{INK}" stroke-width="3"/>{icon("camera", 52, cy, 32)}</g>
  <text x="96" y="{cy + 9:.1f}" font-size="25" font-weight="800" fill="{TEXT}">{e(title)}</text>
  {chip}
  <g transform="translate({W - 46 - tap_w:.1f},{cy - 15:.1f})"><g class="tap" style="animation-delay:{-n * 0.4:.1f}s">{tap}</g></g>
</svg>
"""
    write(f"peek-{slug}.svg", svg)


# ------------------------------------------------------------------ screenshot captions
def caption(slug, i, title, text):
    t_pill_w = pill(0, 0, title, ACCENT, size=15, h=34, spacing=0.3)[1]
    x_text = 26 + t_pill_w + 18
    lines = wrap(text, 19, W - 14 - 22 - x_text)
    H = max(80, 30 + 25 * len(lines) + 24)
    top = (3 + H - 11 - (len(lines) - 1) * 25) / 2 + 7
    p, _ = pill(26, (3 + H - 11) / 2 - 17, title, ACCENT, size=15, h=34, spacing=0.3)
    body = "".join(f'<text x="{x_text:.1f}" y="{top + j * 25:.1f}" font-size="19" font-weight="600" fill="{TEXT}">{e(line)}</text>'
                   for j, line in enumerate(lines))
    words = f"{title} {text}"
    svg = svg_open(W, H, f"{title}: {text}", words)
    svg += f"""  {shell(W, H, PAPER, 20)}
  {p}
  {body}
</svg>
"""
    write(f"cap-{slug}-{i}.svg", svg)


# ------------------------------------------------------------------ link buttons
def link_button(name, label, kind, glyph, sym="↗", circle=None):
    size, H = 21, 62
    cy = (3 + H - 9) / 2
    w = 66 + text_width(label, size) + 60
    fill = {"live": LIVE_GREEN, "main": ACCENT}.get(kind, PANEL)
    fg = TEXT if fill == PANEL else INK
    if kind == "live":
        lead = (f'<circle cx="36" cy="{cy:.1f}" r="16" fill="#fff" stroke="{INK}" stroke-width="2.6"/>'
                f'<circle class="pulse" cx="36" cy="{cy:.1f}" r="7" fill="{LIVE_GREEN}" stroke="{INK}" stroke-width="1.8"/>')
    elif glyph == "in":                             # LinkedIn's "in" on its own blue
        lead = (f'<circle cx="36" cy="{cy:.1f}" r="18" fill="{circle}" stroke="{INK}" stroke-width="2.6"/>'
                f'<text x="36" y="{cy + 7:.1f}" text-anchor="middle" font-size="20" font-weight="800" fill="#fff">in</text>')
    else:
        lead = (f'<circle cx="36" cy="{cy:.1f}" r="18" fill="{circle or ("#fff" if kind == "main" else ACCENT)}" stroke="{INK}" stroke-width="2.6"/>'
                f'{icon(glyph, 36, cy, 22)}')
    words = label + sym + ("in" if glyph == "in" else "")
    svg = svg_open(int(w) + 8, H, label, words, '''
    .pulse{animation:pulse 1.6s ease-in-out infinite}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}''')
    svg += f"""  <rect x="7" y="7" width="{w - 5:.1f}" height="{H - 10}" rx="{(H - 10) / 2}" fill="{INK}"/>
  <rect x="2" y="2" width="{w - 5:.1f}" height="{H - 10}" rx="{(H - 10) / 2}" fill="{fill}" stroke="{INK}" stroke-width="3"/>
  {lead}
  <text x="66" y="{cy + 7:.1f}" font-size="{size}" font-weight="800" fill="{fg}">{e(label)}</text>
  <g class="nudge"><circle cx="{w - 30:.1f}" cy="{cy:.1f}" r="15" fill="#fff" stroke="{INK}" stroke-width="2.4"/>
  <text x="{w - 30:.1f}" y="{cy + 6.5:.1f}" text-anchor="middle" font-size="17" font-weight="800" fill="{INK}">{sym}</text></g>
</svg>
"""
    write(f"link-{name}.svg", svg)


# ------------------------------------------------------------------ DataPilot: what's inside
def datapilot_features():
    x_text = 100
    rows, y = [], 78
    for kind, title, tag, text in DATAPILOT_FEATURES:
        lines = wrap(text, 17, W - 14 - 30 - x_text)
        h = 30 + 23 * len(lines)
        cy = y + 18
        rows.append(f'<circle cx="58" cy="{cy + 3}" r="22" fill="{INK}"/><circle cx="55" cy="{cy}" r="22" fill="{ACCENT}" stroke="{INK}" stroke-width="2.6"/>'
                    f'{icon(kind, 55, cy, 26)}'
                    f'<text x="{x_text}" y="{y + 16}" font-size="21" font-weight="800" fill="{TEXT}">{e(title)}</text>')
        if tag:
            rows.append(pill(x_text + text_width(title, 21) + 12, y - 2, tag, PANEL, size=10.5, h=22, shadow=False)[0])
        rows += [f'<text x="{x_text}" y="{y + 40 + j * 23}" font-size="17" font-weight="600" fill="{TEXT}" fill-opacity=".78">{e(line)}</text>'
                 for j, line in enumerate(lines)]
        y += h + 18
    H = y + 12
    head, _ = pill(30, 26, "WHAT'S INSIDE", ACCENT, size=12.5, h=30)
    words = "WHAT'S INSIDE " + " ".join(f"{t} {g or ''} {x}" for _, t, g, x in DATAPILOT_FEATURES)
    svg = svg_open(W, H, "DataPilot: " + "; ".join(f"{t}: {x}" for _, t, _, x in DATAPILOT_FEATURES), words)
    svg += f"""  {shell(W, H, PAPER, 22)}
  {head}
  {"".join(rows)}
</svg>
"""
    write("datapilot-features.svg", svg)


# ------------------------------------------------------------------ main
GROUPS = sys.argv[2:]
for n, (slug, (group, title, kind)) in enumerate(HEADINGS.items()):
    if group in GROUPS:
        heading(slug, title, kind, n)
if "header" in GROUPS:                                # the badge row under the banner
    n = counts.followers()
    link_button("followers", f"{n} follower{'s' if n != 1 else ''}" if n is not None else "Follow me", "main", "github")
    link_button("repositories", "Explore repos", "plain", "book")
    link_button("portfolio", "My portfolio", "plain", "globe")
    link_button("linkedin", "Connect on LinkedIn", "plain", "in", circle="#0A66C2")
    link_button("leetcode", "Rahul_134 on LeetCode", "plain", "code", circle="#FFA116")
    link_button("github", "Rahul-134 on GitHub", "plain", "github")
if "about" in GROUPS:                                 # under the Problem solving card
    link_button("leetcode-profile", "Live on LeetCode", "main", "code")
    link_button("stats-card", "Stats card", "plain", "chart", sym="↓")
if "projects" in GROUPS:
    note("projects-intro.svg", list(PROJECTS_INTRO), "sparkle", " — ".join(PROJECTS_INTRO))
    link_button("browse-all", "Browse all repositories", "main", "github", sym="→")
for n, (slug, (name, count, caps)) in enumerate(PEEKS.items()):
    if slug not in GROUPS:
        continue
    peek(slug, name, count, n)
    for i, (title, text) in enumerate(caps, 1):
        caption(slug, i, title, text)
    for lname, label, kind, glyph in LINKS.get(slug, []):
        link_button(f"{slug}-{lname}", label, kind, glyph)
    if slug == "datapilot":
        datapilot_features()
        note("datapilot-note.svg", [DATAPILOT_NOTE], "sparkle", DATAPILOT_NOTE)
unknown = [g for g in GROUPS if g not in {"header", "about", "projects", "activity", "connect"} | set(PEEKS)]
if unknown:
    raise SystemExit(f"unknown group(s): {', '.join(unknown)}")
print(f"labels: {len(written)} files ({', '.join(GROUPS)})", file=sys.stderr)
