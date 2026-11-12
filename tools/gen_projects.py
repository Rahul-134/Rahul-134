"""Build the Featured Projects card SVGs in the Playful style (cream cards, dark outlines, a cartoon browser
window with the screenshot, and a LIVE sticker plus a "Try it live" button on deployed projects).

usage: python3 gen_projects.py OUT_DIR
"""
import base64
import html
import os
import sys

sys.dont_write_bytecode = True

out_dir = sys.argv[1]
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(out_dir, exist_ok=True)

import theme_colors
import banner
import counts

ACCENT = theme_colors.current().accent
W, H = 900, 336
FRAME_W, FRAME_H, BAR_H = 400, 262, 28      # browser frame (bar + content)
PAD = 28
GAP = 30
SANS = "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace"

TECH = {   # name -> dot colour
    "React": "#61DAFB", "Django": "#44B78B", "PostgreSQL": "#4169E1", "Docker": "#2496ED", "Gemini": "#8E75B2",
    "FastAPI": "#05998B", "Ollama": "#F2F2F2", "SQLite": "#44A8D8", "Firebase": "#FFCA28", "Tailwind": "#06B6D4",
    "Streamlit": "#FF4B4B", "scikit-learn": "#F7931E", "pandas": "#9AA7FF", "Java": "#ED8B00", "JavaFX": "#44BB44",
    "MySQL": "#4479A1", "Maven": "#C71A36", "Python": "#FFD43B", "OOP": "#C9D1D9", "Algorithms": "#86D7A3",
    "Next.js": "#FFFFFF", "Vercel": "#BDBDBD", "OpenRouter": "#8B8FFF",
}

PROJECTS = [
    dict(slug="bitcareer", num="01", tag="GENAI · LEARNING PLATFORM", title="BitCareer", shot="bitcareer.jpg",
         url_label="bitcareer — career dashboard", zoom=1.5,
         pitch=["AI-powered learning & career-readiness", "platform for developers."],
         bullets=["Resume + GitHub → a personalised roadmap",
                  "Python & SQL sandbox in isolated Docker containers",
                  "Voice-enabled AI mock interviews with reports",
                  "Gamified ranks, from Fresher to Legend"],
         chips=["React", "Django", "PostgreSQL", "Docker", "Gemini"], mirror=False),
    dict(slug="bitnote", num="02", tag="GENAI · LOCAL LLMs", title="BitNote", shot="bitnote.jpg", live=True,
         live_url="https://bitnote-five.vercel.app/",
         url_label="bitnote — notebook",
         pitch=["Notion-style notebooks with a built-in", "AI tutor."],
         bullets=["Syllabus & week-by-week roadmap from one goal",
                  "Recall quizzes with AI grading & mastery tracking",
                  "BitBuddy: in-cell AI chat and one-click summaries",
                  "Local Ollama or hosted Gemini via one env var"],
         chips=["FastAPI", "Ollama", "SQLite", "Firebase", "Tailwind"], mirror=True),
    dict(slug="datapilot", num="03", tag="DATA · ML · AUTOMATION", title="DataPilot", shot="datapilot.jpg", live=True,
         live_url="https://datapilot-alpha-flame.vercel.app/",
         url_label="datapilot — dashboard",
         pitch=["AI-powered data analysis, web scraping and", "machine learning in one workspace."],
         bullets=["Ask your data questions in plain English",
                  "AI web scraper with pagination & search mode",
                  "No-code ML trainer with auto hyperparameter tuning",
                  "Charts, reports and exportable Python code"],
         chips=["FastAPI", "Streamlit", "scikit-learn", "Gemini"], mirror=False),
    dict(slug="business-bytes", num="04", tag="DESKTOP · GAME DEV", title="Business Bytes", shot="bizbytes.jpg",
         url_label="business bytes — game board",
         pitch=["An India-themed Monopoly board game", "for the desktop."],
         bullets=["2–4 player hot-seat play across Indian cities",
                  "Rent tiers, house building, debt and a shared bank",
                  "Save & resume games per account, backed by MySQL",
                  "Custom circular data structure for the board"],
         chips=["Java", "JavaFX", "MySQL", "Maven"], mirror=True),
    dict(slug="portfolio", num="05", tag="WEB · PORTFOLIO", title="Portfolio", shot="portfolio.jpg", live=True,
         live_url="https://rahul-lumbhani-portfolio.vercel.app/",
         url_label="rahul-lumbhani-portfolio.vercel.app",
         pitch=["My personal site: projects, skills and an", "ask-me-anything chatbot terminal."],
         bullets=["Ask-me-anything chatbot terminal, LLMs via OpenRouter",
                  "Tap-to-expand skills linked to where they shipped",
                  "Live GitHub & LeetCode stats, light and dark themes",
                  "Project pages, filterable tech stack and résumé"],
         chips=["Python", "Django", "React", "Next.js", "OpenRouter"], mirror=False),
]

e = html.escape


def data_uri(name):
    with open(os.path.join(SHOTS, name), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()


INK, TEXT, PAPER, PANEL, LIVE_GREEN = banner.INK, banner.TEXT, banner.PAPER, banner.PANEL, "#5BD68A"
BAR = "#45416A" if banner.NIGHT else "#F1E4CB"     # the browser window's top bar
ROUND = "'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif"
FONT_CSS = banner.font_face()


def tw_(text, size):            # rough width of Baloo text (it runs a little wide), for laying out pills
    return len(text) * size * 0.56


def chips_row(x, y, names, max_w, size=13.0):
    """Tech chips: white pills with a coloured dot; shrink the font a little if they would not fit."""
    def widths(fs):
        return [tw_(n, fs) + 34 for n in names]
    fs = size
    while sum(widths(fs)) + 8 * (len(names) - 1) > max_w and fs > 10:
        fs -= 0.5
    out, cx = [], x
    for n, w in zip(names, widths(fs)):
        dot = TECH.get(n, "#C9D1D9")
        out.append(f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="26" rx="13" fill="{PANEL}" stroke="{INK}" stroke-width="2"/>'
                   f'<circle cx="{cx + 14:.1f}" cy="{y + 13}" r="5" fill="{dot}" stroke="{INK}" stroke-width="1.5"/>'
                   f'<text x="{cx + 25:.1f}" y="{y + 17.5}" font-size="{fs}" font-weight="700" fill="{TEXT}" font-family="{ROUND}">{e(n)}</text>')
        cx += w + 8
    return "".join(out)


def pill(x, y, text, fill, size=12.5, h=26, spacing=1.2, anchor="start", shadow=False):
    w = tw_(text, size) + spacing * len(text) + 26
    if anchor == "end":
        x = x - w
    sh = f'<rect x="{x + 3:.1f}" y="{y + 4}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{INK}"/>' if shadow else ""
    return (sh + f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>'
            f'<text x="{x + 13:.1f}" y="{y + h / 2 + size * 0.36:.1f}" font-size="{size}" font-weight="800" fill="{TEXT if fill == PANEL else INK}" letter-spacing="{spacing}" font-family="{ROUND}">{e(text)}</text>'), w


def card_shell(w, h, rx=24):
    return (f'<rect x="11" y="11" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{INK}"/>'
            f'<rect x="3" y="3" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>')


def card(p):
    live = bool(p.get("live"))
    fx = (W - PAD - FRAME_W - 8) if p["mirror"] else PAD
    tx = PAD + 6 if p["mirror"] else (PAD + FRAME_W + GAP)
    tw = W - 2 * PAD - FRAME_W - GAP - 14
    fy = (H - FRAME_H) // 2 - 4
    content_h = FRAME_H - BAR_H
    r = 14
    s = []

    # --- text column: tag pill, call to action, title, pitch, bullets, chips
    tag, _ = pill(tx, 30, f'{p["num"]} · {p["tag"]}', ACCENT, size=12, h=26)
    s.append(tag)
    if live and p.get("live_url"):   # the README links this card to the live site
        cta, _ = pill(tx + tw, 30, "TRY IT LIVE ↗", LIVE_GREEN, size=12.5, h=26, anchor="end", shadow=True)
    else:
        cta, _ = pill(tx + tw, 30, "VIEW CODE ↗", PANEL, size=12, h=26, anchor="end")
    s.append(cta)
    s.append(f'<text x="{tx}" y="100" font-size="38" font-weight="800" fill="{TEXT}" font-family="{ROUND}">{e(p["title"])}</text>')
    for i, line in enumerate(p["pitch"]):
        s.append(f'<text x="{tx}" y="{128 + i * 21}" font-size="16" font-weight="500" fill="{TEXT}" fill-opacity=".72" font-family="{ROUND}">{e(line)}</text>')
    by = 186
    for i, b in enumerate(p["bullets"]):
        yy = by + i * 24
        s.append(f'<circle cx="{tx + 5}" cy="{yy - 5}" r="4.6" fill="{ACCENT}" stroke="{INK}" stroke-width="1.8"/>')
        s.append(f'<text x="{tx + 18}" y="{yy}" font-size="15" font-weight="500" fill="{TEXT}" font-family="{ROUND}">{e(b)}</text>')
    s.append(chips_row(tx, 280, p["chips"], tw))
    text_col = "".join(s)

    # --- cartoon browser window with the screenshot
    fr = [f'<rect x="{fx + 6}" y="{fy + 7}" width="{FRAME_W}" height="{FRAME_H}" rx="{r}" fill="{INK}"/>',
          f'<rect x="{fx}" y="{fy}" width="{FRAME_W}" height="{FRAME_H}" rx="{r}" fill="#fff"/>',
          f'<path d="M{fx} {fy + r}a{r} {r} 0 0 1 {r} -{r}h{FRAME_W - 2 * r}a{r} {r} 0 0 1 {r} {r}v{BAR_H - r}h-{FRAME_W}z" fill="{BAR}"/>',
          f'<line x1="{fx}" y1="{fy + BAR_H}" x2="{fx + FRAME_W}" y2="{fy + BAR_H}" stroke="{INK}" stroke-width="2.5"/>']
    for i, col in enumerate(("#FF6B4A", "#FFC83D", "#BFF0CF")):
        fr.append(f'<circle cx="{fx + 18 + i * 17}" cy="{fy + BAR_H / 2 + 1}" r="5" fill="{col}" stroke="{INK}" stroke-width="1.8"/>')
    ux, uw = fx + 78, FRAME_W - 78 - 14
    fr.append(f'<rect x="{ux}" y="{fy + 6}" width="{uw}" height="18" rx="9" fill="{PANEL}" stroke="{INK}" stroke-width="1.8"/>')
    if live:
        fr.append(f'<circle class="pulse" cx="{ux + 12}" cy="{fy + 15}" r="3.6" fill="{LIVE_GREEN}" stroke="{INK}" stroke-width="1.2"/>')
    fr.append(f'<text x="{ux + uw / 2 + (5 if live else 0)}" y="{fy + 19.5}" text-anchor="middle" font-size="11" font-weight="600" fill="{TEXT}" fill-opacity=".7" font-family="{ROUND}">{e(p["url_label"])}</text>')
    if p["shot"]:
        if p.get("zoom"):
            from PIL import Image
            iw0, ih0 = Image.open(os.path.join(SHOTS, p["shot"])).size
            iw = FRAME_W * p["zoom"]
            ih = iw * ih0 / iw0
            fr.append(f'<image href="{data_uri(p["shot"])}" x="{fx}" y="{fy + BAR_H}" width="{iw:.1f}" height="{ih:.1f}" '
                      f'preserveAspectRatio="none" clip-path="url(#shotclip{p["slug"]})"/>')
        else:
            fr.append(f'<image href="{data_uri(p["shot"])}" x="{fx}" y="{fy + BAR_H}" width="{FRAME_W}" height="{content_h}" '
                      f'preserveAspectRatio="xMidYMin slice" clip-path="url(#shotclip{p["slug"]})"/>')
    fr.append(f'<rect x="{fx}" y="{fy}" width="{FRAME_W}" height="{FRAME_H}" rx="{r}" fill="none" stroke="{INK}" stroke-width="3"/>')
    if live:   # a LIVE sticker slapped on the window's corner
        lx = fx + FRAME_W - 92 if not p["mirror"] else fx + 10
        fr.append(f'<g transform="rotate(-7 {lx + 44} {fy + BAR_H + 28})">'
                  f'<rect x="{lx + 3}" y="{fy + BAR_H + 15}" width="88" height="30" rx="15" fill="{INK}"/>'
                  f'<rect x="{lx}" y="{fy + BAR_H + 11}" width="88" height="30" rx="15" fill="{LIVE_GREEN}" stroke="{INK}" stroke-width="2.5"/>'
                  f'<circle class="pulse" cx="{lx + 18}" cy="{fy + BAR_H + 26}" r="5" fill="#fff" stroke="{INK}" stroke-width="1.6"/>'
                  f'<text x="{lx + 30}" y="{fy + BAR_H + 31.5}" font-size="15" font-weight="800" fill="{INK}" letter-spacing="1.5" font-family="{ROUND}">LIVE</text></g>')
    frame = "".join(fr)
    clip = (f'<clipPath id="shotclip{p["slug"]}"><path d="M{fx} {fy + BAR_H}h{FRAME_W}v{content_h - r}a{r} {r} 0 0 1 -{r} {r}h-{FRAME_W - 2 * r}a{r} {r} 0 0 1 -{r} -{r}z"/></clipPath>')

    state = "Live and deployed. " if live else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">{e(p["title"])}{" (live)" if live else ""}</title>
  <desc id="d">{state}{e(p["title"])}: {e(" ".join(p["pitch"]))} {e(". ".join(p["bullets"]))}. Built with {e(", ".join(p["chips"]))}.</desc>
  <style>
    {FONT_CSS}
    .float{{animation:float 6s ease-in-out infinite alternate}}
    @keyframes float{{from{{transform:translateY(0)}}to{{transform:translateY(-5px)}}}}
    .pulse{{animation:pulse 1.6s ease-in-out infinite}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
    @media (prefers-reduced-motion:reduce){{.float,.pulse{{animation:none}}}}
  </style>
  <defs>{clip}</defs>
  {card_shell(W, H)}
  <g class="float">{frame}</g>
  {text_col}
</svg>
'''
    with open(os.path.join(out_dir, f'{p["slug"]}.svg'), "w") as f:
        f.write(svg)
    return len(svg)


# ------------------------------------------------------------------ small cards
MW, MH = 440, 196

INVADER = ["..X.....X..", "...X...X...", "..XXXXXXX..", ".XX.XXX.XX.", "XXXXXXXXXXX", "X.XXXXXXX.X", "X.X.....X.X", "...XX.XX..."]
CHECK = [".........XX", "........XXX", "X......XXX.", "XX....XXX..", "XXX..XXX...", ".XXXXXX....", "..XXXX.....", "...XX......"]

MINI = [
    dict(slug="virtual-arcade-zone", num="06", tag="CONSOLE ARCADE", title="Virtual Arcade Zone", art=INVADER, col=ACCENT,
         desc=["7 mini-games — Hangman, Simon Says,", "Hand Cricket and more — in pure core Java."],
         chips=["Java", "OOP"]),
    dict(slug="leetcode-solutions", num="07", tag="PRACTICE", title="LeetCode Solutions", art=CHECK, col="#4DAE6C",
         desc=[f"{counts.solved()} problems solved, 60+ written up here", "in clean, runnable, type-hinted Python."],
         chips=["Python", "Algorithms"]),
]


def mini(p):
    u = 8
    aw, ah = len(p["art"][0]) * u, len(p["art"]) * u
    bx, by, bw, bh = 24, 26, 112, MH - 60
    s = [f'<rect x="{bx + 4}" y="{by + 5}" width="{bw}" height="{bh}" rx="16" fill="{INK}"/>',
         f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="16" fill="{banner.SKY}" stroke="{INK}" stroke-width="3"/>']
    ax, ay = round(bx + (bw - aw) / 2), round(by + (bh - ah) / 2)
    rects = []
    for y, row in enumerate(p["art"]):
        x = 0
        while x < len(row):
            if row[x] == "X":
                st = x
                while x < len(row) and row[x] == "X":
                    x += 1
                rects.append(f'<rect x="{st * u}" y="{y * u}" width="{(x - st) * u}" height="{u}"/>')
            else:
                x += 1
    s.append(f'<g class="bob" transform="translate({ax},{ay})" shape-rendering="crispEdges">'
             f'<g fill="{INK}" stroke="{INK}" stroke-width="5" stroke-linejoin="round">{"".join(rects)}</g>'
             f'<g fill="{p["col"]}">{"".join(rects)}</g></g>')
    tx = bx + bw + 24
    tag, _ = pill(tx, 24, f'{p["num"]} · {p["tag"]}', ACCENT, size=11, h=24)
    s.append(tag)
    s.append(f'<text x="{tx}" y="78" font-size="24" font-weight="800" fill="{TEXT}" font-family="{ROUND}">{e(p["title"])}</text>')
    for i, line in enumerate(p["desc"]):
        s.append(f'<text x="{tx}" y="{102 + i * 18}" font-size="13.5" font-weight="500" fill="{TEXT}" fill-opacity=".72" font-family="{ROUND}">{e(line)}</text>')
    s.append(chips_row(tx, MH - 56, p["chips"], MW - tx - 110, size=12))
    cta, _ = pill(MW - 30, MH - 56, "CODE ↗", PANEL, size=11.5, h=26, anchor="end")
    s.append(cta)
    body = "".join(s)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MW} {MH}" width="{MW}" height="{MH}" role="img" aria-labelledby="t d">
  <title id="t">{e(p["title"])}</title>
  <desc id="d">{e(p["title"])}: {e(" ".join(p["desc"]))} Built with {e(", ".join(p["chips"]))}.</desc>
  <style>
    {FONT_CSS}
    .bob{{animation:bobm 2.6s ease-in-out infinite alternate}}
    @keyframes bobm{{from{{transform:translate({ax}px,{ay}px)}}to{{transform:translate({ax}px,{ay - 5}px)}}}}
    @media (prefers-reduced-motion:reduce){{.bob{{animation:none}}}}
  </style>
  {card_shell(MW, MH, 22)}
  {body}
</svg>
'''
    with open(os.path.join(out_dir, f'{p["slug"]}.svg'), "w") as f:
        f.write(svg)
    return len(svg)


for p in PROJECTS:
    print(f'{p["slug"]}.svg', card(p) // 1024, "KB", file=sys.stderr)
for p in MINI:
    print(f'{p["slug"]}.svg', mini(p) // 1024, "KB", file=sys.stderr)
