"""Build the Featured Projects card SVGs (animated, screenshots embedded as data URIs).

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
         url_label="bitnote — notebook",
         pitch=["Notion-style notebooks with a built-in", "AI tutor."],
         bullets=["Syllabus & week-by-week roadmap from one goal",
                  "Recall quizzes with AI grading & mastery tracking",
                  "BitBuddy: in-cell AI chat and one-click summaries",
                  "Local Ollama or hosted Gemini via one env var"],
         chips=["FastAPI", "Ollama", "SQLite", "Firebase", "Tailwind"], mirror=True),
    dict(slug="datapilot", num="03", tag="DATA · ML · AUTOMATION", title="DataPilot", shot="datapilot.jpg", live=True,
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
    dict(slug="portfolio", num="05", tag="WEB · PORTFOLIO", title="Portfolio", shot="portfolio.jpg",
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


def chip(x, y, name):
    w = round(len(name) * 6.8 + 31)
    dot = TECH.get(name, "#C9D1D9")
    return (f'<rect x="{x}" y="{y}" width="{w}" height="24" rx="12" fill="#1e1e1e" stroke="#303030"/>'
            f'<circle cx="{x + 13}" cy="{y + 12}" r="4" fill="{dot}"/>'
            f'<text x="{x + 24}" y="{y + 16}" font-size="12" fill="#D6D6D6" font-family="{SANS}">{e(name)}</text>'), w + 8


def card(p):
    fx = (W - PAD - FRAME_W) if p["mirror"] else PAD
    tx = PAD if p["mirror"] else (PAD + FRAME_W + GAP)
    tw = W - 2 * PAD - FRAME_W - GAP
    fy = (H - FRAME_H) // 2
    content_h = FRAME_H - BAR_H
    s = []

    # --- text column
    pill_w = round((len(p["num"]) + 3 + len(p["tag"])) * 8.1 + 44)
    s.append(f'<rect x="{tx}" y="36" width="{pill_w}" height="24" rx="12" fill="{ACCENT}" fill-opacity="0.10" stroke="{ACCENT}" stroke-opacity="0.35"/>')
    s.append(f'<circle class="pulse" cx="{tx + 14}" cy="48" r="3.5" fill="{ACCENT}"/>')
    s.append(f'<text x="{tx + 27}" y="52" font-size="11" fill="{ACCENT}" letter-spacing="1.4" font-family="{MONO}">{p["num"]} · {e(p["tag"])}</text>')
    s.append(f'<text x="{tx + tw}" y="52" text-anchor="end" font-size="11" fill="#8b8b8b" letter-spacing="1.2" font-family="{MONO}">OPEN ↗</text>')
    if p.get("live"):
        lx = tx + tw - 112
        s.append(f'<rect x="{lx}" y="38" width="54" height="20" rx="10" fill="#27c93f" fill-opacity="0.12" stroke="#27c93f" stroke-opacity="0.45"/>')
        s.append(f'<circle class="pulse" cx="{lx + 13}" cy="48" r="3.2" fill="#27c93f"/>')
        s.append(f'<text x="{lx + 22}" y="52" font-size="10" fill="#4ade80" letter-spacing="1.3" font-family="{MONO}">LIVE</text>')
    s.append(f'<text x="{tx}" y="104" font-size="34" font-weight="800" fill="#FFFFFF" font-family="{SANS}">{e(p["title"])}</text>')
    for i, line in enumerate(p["pitch"]):
        s.append(f'<text x="{tx}" y="{132 + i * 20}" font-size="14.5" fill="#9aa0a6" font-family="{SANS}">{e(line)}</text>')
    by = 186
    for i, b in enumerate(p["bullets"]):
        yy = by + i * 25
        s.append(f'<rect x="{tx}" y="{yy - 9}" width="7" height="7" rx="2" fill="{ACCENT}" fill-opacity="{1 - i * 0.18:.2f}"/>')
        s.append(f'<text x="{tx + 18}" y="{yy}" font-size="14" fill="#D6D6D6" font-family="{SANS}">{e(b)}</text>')
    cx, cy = tx, 292
    for name in p["chips"]:
        c, adv = chip(cx, cy, name)
        s.append(c)
        cx += adv
    text_col = "".join(s)

    # --- browser frame
    fr = []
    r = 12
    fr.append(f'<rect x="{fx}" y="{fy}" width="{FRAME_W}" height="{FRAME_H}" rx="{r}" fill="#0d0d0d" stroke="#333" />')
    fr.append(f'<path d="M{fx} {fy + r}a{r} {r} 0 0 1 {r} -{r}h{FRAME_W - 2 * r}a{r} {r} 0 0 1 {r} {r}v{BAR_H - r}h-{FRAME_W}z" fill="#1d1d1d"/>')
    for i, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        fr.append(f'<circle cx="{fx + 16 + i * 16}" cy="{fy + BAR_H / 2}" r="4.5" fill="{col}"/>')
    fr.append(f'<rect x="{fx + 74}" y="{fy + 6}" width="{FRAME_W - 74 - 14}" height="16" rx="8" fill="#141414"/>')
    fr.append(f'<text x="{fx + 74 + (FRAME_W - 88) / 2}" y="{fy + 18}" text-anchor="middle" font-size="9.5" fill="#7d8590" letter-spacing="0.6" font-family="{MONO}">{e(p["url_label"])}</text>')
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
        fr.append(f'<rect x="{fx}" y="{fy + BAR_H}" width="{FRAME_W}" height="{content_h}" fill="url(#fade)" clip-path="url(#shotclip{p["slug"]})"/>')
    frame = "".join(fr)
    clip = (f'<clipPath id="shotclip{p["slug"]}"><path d="M{fx} {fy + BAR_H}h{FRAME_W}v{content_h - r}a{r} {r} 0 0 1 -{r} {r}h-{FRAME_W - 2 * r}a{r} {r} 0 0 1 -{r} -{r}z"/></clipPath>')

    glow_cx = (fx + FRAME_W / 2) / W
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
  <title id="t">{e(p["title"])}</title>
  <desc id="d">{e(p["title"])}: {e(" ".join(p["pitch"]))} {e(". ".join(p["bullets"]))}. Built with {e(", ".join(p["chips"]))}.</desc>
  <style>
    .float{{animation:float 6s ease-in-out infinite alternate}}
    @keyframes float{{from{{transform:translateY(0)}}to{{transform:translateY(-5px)}}}}
    .shine{{animation:shine 7s ease-in-out infinite}}
    @keyframes shine{{0%,62%{{transform:translateX(0)}}100%{{transform:translateX({W + 420}px)}}}}
    .pulse{{animation:pulse 2s ease-in-out infinite}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
    .caret{{animation:caret 1.1s steps(1,end) infinite}}
    @keyframes caret{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
    .bar{{transform-box:fill-box;transform-origin:bottom;animation:grow 3.6s ease-in-out infinite alternate}}
    @keyframes grow{{from{{transform:scaleY(.82)}}to{{transform:scaleY(1)}}}}
    @media (prefers-reduced-motion:reduce){{.float,.shine,.pulse,.caret,.bar{{animation:none}}}}
  </style>
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.55"/>
      <stop offset="0.45" stop-color="#2a2a2a"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0.30"/>
    </linearGradient>
    <radialGradient id="glow" cx="{glow_cx:.3f}" cy="0.5" r="0.5">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.13"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#fff" stop-opacity="0.07"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0.75" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity="0.35"/>
    </linearGradient>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
    {clip}
  </defs>

  <rect width="{W}" height="{H}" rx="20" fill="#151515"/>
  <rect width="{W}" height="{H}" rx="20" fill="url(#glow)"/>
  <rect x="0.75" y="0.75" width="{W - 1.5}" height="{H - 1.5}" rx="19.25" fill="none" stroke="url(#edge)" stroke-width="1.5"/>

  <g class="float">{frame}</g>
  {text_col}

  <g clip-path="url(#card)"><g class="shine"><rect x="-260" y="-40" width="130" height="{H + 80}" fill="url(#beam)" transform="skewX(-18)"/></g></g>
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
         desc=["160+ problems solved, 60+ written up here", "in clean, runnable, type-hinted Python."],
         chips=["Python", "Algorithms"]),
]


def mini(p):
    u = 8
    aw, ah = len(p["art"][0]) * u, len(p["art"]) * u
    bx, by, bw, bh = 24, 28, 112, MH - 56
    s = []
    s.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="14" fill="#101010" stroke="#2c2c2c"/>')
    ax, ay = bx + (bw - aw) / 2, by + (bh - ah) / 2
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
    s.append(f'<g class="bob" transform="translate({ax},{ay})" fill="{p["col"]}">{"".join(rects)}</g>')
    tx = bx + bw + 26
    pill_w = round((len(p["num"]) + 3 + len(p["tag"])) * 7.7 + 42)
    s.append(f'<rect x="{tx}" y="26" width="{pill_w}" height="22" rx="11" fill="{ACCENT}" fill-opacity="0.10" stroke="{ACCENT}" stroke-opacity="0.35"/>')
    s.append(f'<circle class="pulse" cx="{tx + 13}" cy="37" r="3.2" fill="{ACCENT}"/>')
    s.append(f'<text x="{tx + 25}" y="41" font-size="10.5" fill="{ACCENT}" letter-spacing="1.3" font-family="{MONO}">{p["num"]} · {e(p["tag"])}</text>')
    s.append(f'<text x="{tx}" y="82" font-size="22" font-weight="800" fill="#FFFFFF" font-family="{SANS}">{e(p["title"])}</text>')
    for i, line in enumerate(p["desc"]):
        s.append(f'<text x="{tx}" y="{108 + i * 18}" font-size="12.5" fill="#9aa0a6" font-family="{SANS}">{e(line)}</text>')
    cx, cy = tx, MH - 26 - 24
    for name in p["chips"]:
        c, adv = chip(cx, cy, name)
        s.append(c)
        cx += adv
    s.append(f'<text x="{MW - 24}" y="{MH - 33}" text-anchor="end" font-size="10.5" fill="#8b8b8b" letter-spacing="1.2" font-family="{MONO}">OPEN ↗</text>')
    body = "".join(s)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MW} {MH}" width="{MW}" height="{MH}" role="img" aria-labelledby="t d">
  <title id="t">{e(p["title"])}</title>
  <desc id="d">{e(p["title"])}: {e(" ".join(p["desc"]))} Built with {e(", ".join(p["chips"]))}.</desc>
  <style>
    .bob{{animation:bobm 2.6s ease-in-out infinite alternate}}
    @keyframes bobm{{from{{transform:translate({ax}px,{ay}px)}}to{{transform:translate({ax}px,{ay - 5}px)}}}}
    .shine{{animation:shine 8s ease-in-out infinite}}
    @keyframes shine{{0%,65%{{transform:translateX(0)}}100%{{transform:translateX({MW + 360}px)}}}}
    .pulse{{animation:pulse 2s ease-in-out infinite}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
    @media (prefers-reduced-motion:reduce){{.bob,.shine,.pulse{{animation:none}}}}
  </style>
  <defs>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0.5"/><stop offset="0.5" stop-color="#2a2a2a"/><stop offset="1" stop-color="{ACCENT}" stop-opacity="0.25"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.18" cy="0.5" r="0.5"><stop offset="0" stop-color="{p["col"]}" stop-opacity="0.12"/><stop offset="1" stop-color="{p["col"]}" stop-opacity="0"/></radialGradient>
    <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset="0.5" stop-color="#fff" stop-opacity="0.07"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="card"><rect width="{MW}" height="{MH}" rx="18"/></clipPath>
  </defs>
  <rect width="{MW}" height="{MH}" rx="18" fill="#151515"/>
  <rect width="{MW}" height="{MH}" rx="18" fill="url(#glow)"/>
  <rect x="0.75" y="0.75" width="{MW - 1.5}" height="{MH - 1.5}" rx="17.25" fill="none" stroke="url(#edge)" stroke-width="1.5"/>
  {body}
  <g clip-path="url(#card)"><g class="shine"><rect x="-220" y="-30" width="110" height="{MH + 60}" fill="url(#beam)" transform="skewX(-18)"/></g></g>
</svg>
'''
    with open(os.path.join(out_dir, f'{p["slug"]}.svg'), "w") as f:
        f.write(svg)
    return len(svg)


for p in PROJECTS:
    print(f'{p["slug"]}.svg', card(p) // 1024, "KB", file=sys.stderr)
for p in MINI:
    print(f'{p["slug"]}.svg', mini(p) // 1024, "KB", file=sys.stderr)
