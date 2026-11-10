#!/usr/bin/env python3
"""Build the GitHub Activity and LeetCode cards in the Playful style: stats/github.svg,
stats/activity.svg and stats/leetcode.svg.

    python3 tools/gen_stats.py OUT_DIR            # draw the cards from the saved numbers (tools/stats.json)
    python3 tools/gen_stats.py OUT_DIR --fetch    # fetch fresh numbers first (needs GITHUB_TOKEN), then draw

The numbers are fetched by the "Refresh stats" workflow (.github/workflows/stats.yml) once a day: GitHub
through its GraphQL API, LeetCode through leetcode.com/graphql. They are saved in tools/stats.json, so
switching themes redraws the cards without any network access. If a source cannot be reached, the
last saved numbers for it are kept.

Colours follow the `activity` section theme (RAHUL_THEME, set by tools/theme.py; otherwise read from
tools/theme.json).
"""
import datetime as dt
import html
import json
import math
import os
import sys
import urllib.request

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sprites as S  # noqa: E402
import theme_colors  # noqa: E402
import banner  # noqa: E402

GH_USER = "Rahul-134"
LC_USER = "Rahul_134"
DATA = os.path.join(HERE, "stats.json")

if "RAHUL_THEME" not in os.environ:                     # run on its own (the workflow): use the saved theme
    import theme as _theme
    os.environ["RAHUL_THEME"] = _theme.effective(_theme.load())[0]["activity"]
T = theme_colors.current()
ACCENT = T.accent
INK, SKY, PAPER = banner.INK, banner.SKY, "#FFFDF7"
EMPTY = "#F1E7D0"                                       # an empty heat-map cell / progress track
EASY, MEDIUM, HARD = "#5BD68A", "#FFC83D", "#FF7A6B"
ROUND = "'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',system-ui,sans-serif"
e = html.escape
W = 900


# ------------------------------------------------------------------ fetching
def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "User-Agent": "profile-stats-card", **headers})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"][0].get("message", "GraphQL error"))
    return out["data"]


def fetch_github(token):
    gql = lambda q, **v: post("https://api.github.com/graphql", {"query": q, "variables": v},
                              {"Authorization": f"bearer {token}"})
    u = gql("""query($login:String!){user(login:$login){
      createdAt
      pullRequests{totalCount} issues{totalCount}
      repositoriesContributedTo(contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,REPOSITORY],includeUserRepositories:false){totalCount}
      repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){totalCount nodes{
        stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}""",
            login=GH_USER)["user"]
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            n = edge["node"]
            langs.setdefault(n["name"], [n["name"], n["color"] or "#A8A29E", 0])[2] += edge["size"]
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    days, commits = {}, 0
    for year in range(int(u["createdAt"][:4]), now.year + 1):
        start = dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc)
        end = min(dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc), now)
        c = gql("""query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
          contributionsCollection(from:$from,to:$to){totalCommitContributions
            contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""",
                login=GH_USER, **{"from": start.isoformat(), "to": end.isoformat()})["user"]["contributionsCollection"]
        commits += c["totalCommitContributions"]
        for w in c["contributionCalendar"]["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    return {
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "commits": commits,
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "contributed": u["repositoriesContributedTo"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "languages": sorted(langs.values(), key=lambda l: -l[2]),
        "days": days_summary(days, now.date()),
    }


def days_summary(days, today):
    """Totals, streaks and the last 53 weeks of the calendar from {date: count}."""
    first = min((d for d, n in days.items() if n), default=today.isoformat())
    total = sum(days.values())
    run, best, best_end = 0, 0, None
    d = dt.date.fromisoformat(first)
    while d <= today:
        run = run + 1 if days.get(d.isoformat(), 0) else 0
        if run > best:
            best, best_end = run, d
        d += dt.timedelta(days=1)
    cur, d = 0, today if days.get(today.isoformat(), 0) else today - dt.timedelta(days=1)
    cur_end = d
    while days.get(d.isoformat(), 0):
        cur, d = cur + 1, d - dt.timedelta(days=1)
    span = lambda n, end: {"days": n, "start": (end - dt.timedelta(days=n - 1)).isoformat() if n else None,
                           "end": end.isoformat() if n else None}
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7 + 52 * 7)     # a Sunday, 53 columns back
    cal = [[(start + dt.timedelta(days=i)).isoformat(), days.get((start + dt.timedelta(days=i)).isoformat(), 0)]
           for i in range((today - start).days + 1)]
    year = sum(n for day, n in cal if day > (today - dt.timedelta(days=365)).isoformat())
    return {"today": today.isoformat(), "first": first, "total": total, "year": year,
            "current": span(cur, cur_end), "longest": span(best, best_end or today), "calendar": cal}


def fetch_leetcode():
    q = """query($u:String!){
      allQuestionsCount{difficulty count}
      matchedUser(username:$u){profile{ranking} badges{id}
        submitStatsGlobal{acSubmissionNum{difficulty count}}
        userCalendar{streak totalActiveDays}}}"""
    d = post("https://leetcode.com/graphql", {"query": q, "variables": {"u": LC_USER}},
             {"Referer": f"https://leetcode.com/u/{LC_USER}/", "User-Agent": "Mozilla/5.0 (profile-stats-card)"})
    m = d["matchedUser"]
    if not m:
        raise RuntimeError(f"LeetCode user {LC_USER} not found")
    return {
        "solved": {x["difficulty"]: x["count"] for x in m["submitStatsGlobal"]["acSubmissionNum"]},
        "total": {x["difficulty"]: x["count"] for x in d["allQuestionsCount"]},
        "ranking": m["profile"]["ranking"],
        "badges": len(m["badges"] or []),
        "streak": (m["userCalendar"] or {}).get("streak", 0),
        "active_days": (m["userCalendar"] or {}).get("totalActiveDays", 0),
    }


def refresh(data):
    """Fetch every source; keep the saved numbers of a source that fails. Returns the names that failed."""
    failed = []
    token = os.environ.get("GITHUB_TOKEN")
    sources = [("github", lambda: fetch_github(token) if token else (_ for _ in ()).throw(RuntimeError("GITHUB_TOKEN is not set"))),
               ("leetcode", fetch_leetcode)]
    for name, fn in sources:
        try:
            data[name] = fn()
        except Exception as exc:                        # network, rate limit, API change: keep the old numbers
            print(f"::warning::{name} stats not refreshed: {exc}", file=sys.stderr)
            failed.append(name)
    return failed


# ------------------------------------------------------------------ drawing helpers
def tw(text, size):
    return len(text) * size * 0.56


def num(n):
    if n is None:
        return "—"
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 10000 else f"{n:,}"


def pct(part, whole):
    p = 100 * part / whole
    return "<1%" if 0 < p < 0.5 else f"{p:.0f}%"


def mix(a, b, t):
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * t + int(b[i:i + 2], 16) * (1 - t)):02X}" for i in (0, 2, 4))


def shell(w, h, fill=PAPER, rx=24):
    return (f'<rect x="11" y="11" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{INK}"/>'
            f'<rect x="3" y="3" width="{w - 14}" height="{h - 14}" rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="4"/>')


def tile(x, y, w, h, fill="#FFFFFF", rx=16, sh=4, sw=3):
    return (f'<rect x="{x + sh}" y="{y + sh}" width="{w}" height="{h}" rx="{rx}" fill="{INK}"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{INK}" stroke-width="{sw}"/>')


def pill(x, y, text, fill=ACCENT, size=12.5, h=30, anchor="start"):
    w = tw(text, size) + 1.5 * len(text) + 30
    if anchor == "end":
        x -= w
    return (f'<rect x="{x + 3:.1f}" y="{y + 3}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{INK}"/>'
            f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill}" stroke="{INK}" stroke-width="2.5"/>'
            f'<text x="{x + 15:.1f}" y="{y + h / 2 + size * 0.36:.1f}" font-size="{size}" font-weight="800" fill="{INK}" letter-spacing="1.5">{e(text)}</text>')


def head(label, title, extra=""):
    return (pill(36, 26, label) +
            f'<text x="36" y="92" font-size="32" font-weight="800" fill="{INK}">{e(title)}</text>{extra}')


def svg(w, h, title, desc, body, css=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t d">
  <title id="t">{e(title)}</title>
  <desc id="d">{e(desc)}</desc>
  <style>
    {banner.font_face()}
    text{{font-family:{ROUND}}}{css}
  </style>
  {shell(w, h)}
  {body}
</svg>
"""


DINO_H = (len(S.ART["dinoBody"]) + len(S.ART["legsA"])) * S.DINO_U


def dino(x, y_bottom, k, flip=False):
    body = banner.shapes(S.pad(S.ART["dinoBody"], S.DINO_W), S.DINO_U)
    legs = banner.shapes(S.pad(S.ART["legsA"], S.DINO_W), S.DINO_U)
    w = S.DINO_W * S.DINO_U
    flipt = f" translate({w},0) scale(-1,1)" if flip else ""
    return (f'<g transform="translate({x},{y_bottom - DINO_H * k:.1f}) scale({k}){flipt}">'
            f'{body}<g transform="translate(0,{len(S.ART["dinoBody"]) * S.DINO_U})">{legs}</g></g>')


def cactus(x, y_bottom, k=1.0, kind="small"):
    rows = S.ART[kind]
    return (f'<g transform="translate({x},{y_bottom - len(rows) * S.OBJ_U * k:.1f}) scale({k})">'
            f'{banner.shapes(rows, S.OBJ_U)}</g>')


# small ink glyphs, centred on (cx, cy), drawn on an accent circle
def glyph(kind, cx, cy):
    st = f'stroke="{INK}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"'
    if kind == "star":
        pts = " ".join(f"{cx + (9 if i % 2 == 0 else 4) * math.sin(i * math.pi / 5):.1f},"
                       f"{cy + 0.6 - (9 if i % 2 == 0 else 4) * math.cos(i * math.pi / 5):.1f}" for i in range(10))
        return f'<polygon points="{pts}" fill="#FFF" {st}/>'
    if kind == "commit":
        return f'<path d="M{cx - 11} {cy}H{cx + 11}" {st}/><circle cx="{cx}" cy="{cy}" r="5" fill="#FFF" {st}/>'
    if kind == "pr":
        return (f'<path d="M{cx - 5} {cy - 5}V{cy + 5}M{cx + 5} {cy + 5}V{cy - 2}Q{cx + 5} {cy - 6} {cx + 1} {cy - 6}H{cx - 1}'
                f'M{cx + 1} {cy - 9}L{cx - 2} {cy - 6}L{cx + 1} {cy - 3}" fill="none" {st}/>'
                f'<circle cx="{cx - 5}" cy="{cy - 6}" r="2.8" fill="#FFF" {st}/><circle cx="{cx - 5}" cy="{cy + 6}" r="2.8" fill="#FFF" {st}/>'
                f'<circle cx="{cx + 5}" cy="{cy + 6}" r="2.8" fill="#FFF" {st}/>')
    if kind == "issue":
        return f'<circle cx="{cx}" cy="{cy}" r="8.5" fill="#FFF" {st}/><circle cx="{cx}" cy="{cy}" r="2.4" fill="{INK}"/>'
    if kind == "repo":
        return (f'<rect x="{cx - 7.5}" y="{cy - 9}" width="15" height="18" rx="2.5" fill="#FFF" {st}/>'
                f'<path d="M{cx - 3} {cy - 9}V{cy + 9}" {st}/>')
    if kind == "fork":
        return (f'<path d="M{cx - 5} {cy - 5}V{cy - 2}Q{cx - 5} {cy + 1} {cx} {cy + 1}Q{cx + 5} {cy + 1} {cx + 5} {cy - 2}V{cy - 5}M{cx} {cy + 1}V{cy + 5}" fill="none" {st}/>'
                f'<circle cx="{cx - 5}" cy="{cy - 7}" r="2.8" fill="#FFF" {st}/><circle cx="{cx + 5}" cy="{cy - 7}" r="2.8" fill="#FFF" {st}/>'
                f'<circle cx="{cx}" cy="{cy + 7}" r="2.8" fill="#FFF" {st}/>')
    if kind == "flame":
        return (f'<g transform="translate({cx},{cy + 2})"><path d="M0 -17C8 -8 13 -2 11 6C9 13 -9 13 -11 6C-13 -1 -7 -4 -5 -11C-2 -6 1 -5 2 -8C3 -11 1 -14 0 -17Z" '
                f'fill="#FF8A3D" {st}/><path d="M0 -2C4 2 5 5 4 7C3 10 -3 10 -4 7C-5 4 -2 2 0 -2Z" fill="#FFD166"/></g>')
    return ""


def icon(kind, cx, cy, r=17, fill=ACCENT):
    return (f'<circle cx="{cx + 2.5}" cy="{cy + 2.5}" r="{r}" fill="{INK}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="2.6"/>{glyph(kind, cx, cy)}')


def fmt_day(iso, year=False):
    if not iso:
        return ""
    d = dt.date.fromisoformat(iso)
    return d.strftime("%b %-d, %Y") if year else d.strftime("%b %-d")


def fmt_span(s, today):
    if not s or not s.get("days"):
        return "start one today!"
    a, b = s["start"], s["end"]
    if a == b:
        return fmt_day(a)
    return f"{fmt_day(a)} – {'today' if b == today else fmt_day(b)}"


# ------------------------------------------------------------------ card 1: player stats + top languages
def github_card(g):
    H = 360
    v = lambda k: (g or {}).get(k)
    stats = [("star", "Stars earned", v("stars")), ("commit", "Commits", v("commits")),
             ("pr", "Pull requests", v("prs")), ("issue", "Issues", v("issues")),
             ("fork", "Contributed to", v("contributed")), ("repo", "Public repos", v("repos"))]
    tiles, TW, TH, GX, GY, X0, Y0 = [], 150, 98, 16, 16, 36, 112
    for i, (kind, label, val) in enumerate(stats):
        x, y = X0 + (i % 3) * (TW + GX), Y0 + (i // 3) * (TH + GY)
        tiles.append(tile(x, y, TW, TH) + icon(kind, x + 30, y + 30) +
                     f'<text x="{x + 54}" y="{y + 35}" font-size="13" font-weight="700" fill="{INK}" fill-opacity=".7">{e(label)}</text>'
                     f'<text x="{x + 18}" y="{y + 80}" font-size="32" font-weight="800" fill="{INK}">{num(val)}</text>')
    # top languages panel
    PX, PY, PW, PH = X0 + 3 * TW + 2 * GX + 22, Y0, 0, 2 * TH + GY
    PW = W - 36 - 4 - PX
    langs = (g or {}).get("languages") or []
    total = sum(l[2] for l in langs) or 1
    top = langs[:6]
    alias = {"Jupyter Notebook": "Jupyter"}
    bar, x, BX, BW = [], PX + 20, PX + 20, PW - 40
    for name, colour, size in top:
        w = BW * size / total
        bar.append(f'<rect x="{x:.1f}" y="{PY + 50}" width="{w + 0.4:.1f}" height="20" fill="{colour}"/>')
        x += w
    if len(langs) > len(top):
        bar.append(f'<rect x="{x:.1f}" y="{PY + 50}" width="{BX + BW - x:.1f}" height="20" fill="#D6CCB8"/>')
    rows = []
    for i, (name, colour, size) in enumerate(top):
        cx, cy = PX + 20 + (i % 2) * (BW / 2 + 6), PY + 104 + (i // 2) * 30
        rows.append(f'<circle cx="{cx + 7}" cy="{cy - 5}" r="7" fill="{colour}" stroke="{INK}" stroke-width="2"/>'
                    f'<text x="{cx + 21}" y="{cy}" font-size="15" font-weight="700" fill="{INK}">{e(alias.get(name, name))}</text>'
                    f'<text x="{cx + BW / 2 - 8:.1f}" y="{cy}" text-anchor="end" font-size="15" font-weight="800" fill="{INK}" fill-opacity=".6">{e(pct(size, total))}</text>')
    if not top:
        rows.append(f'<text x="{PX + PW / 2}" y="{PY + 130}" text-anchor="middle" font-size="16" font-weight="700" fill="{INK}" fill-opacity=".6">syncing…</text>')
    panel = (tile(PX, PY, PW, PH) +
             f'<text x="{PX + 20}" y="{PY + 33}" font-size="13" font-weight="800" fill="{INK}" letter-spacing="1.5">TOP LANGUAGES</text>'
             f'<clipPath id="bar"><rect x="{BX}" y="{PY + 50}" width="{BW}" height="20" rx="10"/></clipPath>'
             f'<rect x="{BX}" y="{PY + 50}" width="{BW}" height="20" rx="10" fill="{EMPTY}"/>'
             f'<g clip-path="url(#bar)">{"".join(bar)}</g>'
             f'<rect x="{BX}" y="{PY + 50}" width="{BW}" height="20" rx="10" fill="none" stroke="{INK}" stroke-width="2.5"/>'
             + "".join(rows))
    # the T-rex stands on the language panel, next to a little cactus
    deco = (f'<g class="bob">{dino(PX + PW - 96, PY + 1.5, 0.8)}</g>' + cactus(PX + PW - 150, PY + 1.5, 0.7, "saguaro"))
    css = """
    .bob{animation:bob 2.8s ease-in-out infinite}
    @keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}
    @media (prefers-reduced-motion:reduce){.bob{animation:none}}"""
    body = head("GITHUB STATS", f"@{GH_USER}") + "".join(tiles) + panel + deco
    vals = ", ".join(f"{label}: {num(val)}" for _, label, val in stats)
    lang_txt = ", ".join(f"{n} {pct(s, total)}" for n, _, s in top)
    return svg(W, H, "GitHub stats", f"{vals}. Top languages: {lang_txt or 'syncing'}.", body, css)


# ------------------------------------------------------------------ card 2: streaks + contribution calendar
def activity_card(g):
    d = (g or {}).get("days") or {}
    today = d.get("today") or dt.date.today().isoformat()
    cal = d.get("calendar") or days_summary({}, dt.date.fromisoformat(today))["calendar"]   # empty grid until synced
    CELL, GAP = 11, 3
    STEP = CELL + GAP
    tiles_y, TH = 116, 102
    TW = (W - 72 - 4 - 2 * 18) // 3
    since = fmt_day(d.get("first"), year=True)
    hud = [("Total contributions", d.get("total"), f"since {since}" if since else "syncing…", "commit", "#FFFFFF"),
           ("Current streak", (d.get("current") or {}).get("days"), fmt_span(d.get("current"), today), "flame", ACCENT),
           ("Longest streak", (d.get("longest") or {}).get("days"), fmt_span(d.get("longest"), today), "star", "#FFFFFF")]
    tiles = []
    for i, (label, val, sub, kind, fill) in enumerate(hud):
        x = 36 + i * (TW + 18)
        unit = "" if i == 0 or val is None else (" day" if val == 1 else " days")
        tiles.append(tile(x, tiles_y, TW, TH, fill) + icon(kind, x + 32, tiles_y + 32, 18, "#FFFFFF" if fill == ACCENT else ACCENT) +
                     f'<text x="{x + 60}" y="{tiles_y + 37}" font-size="14" font-weight="800" fill="{INK}" fill-opacity=".75">{e(label)}</text>'
                     f'<text x="{x + 20}" y="{tiles_y + 82}" font-size="32" font-weight="800" fill="{INK}">{num(val)}'
                     f'<tspan font-size="18" fill-opacity=".7">{unit}</tspan></text>'
                     f'<text x="{x + TW - 18}" y="{tiles_y + 82}" text-anchor="end" font-size="13" font-weight="700" fill="{INK}" fill-opacity=".65">{e(sub)}</text>')
    # calendar panel
    PX, PY = 36, tiles_y + TH + 24
    PW = W - 72 - 4
    weeks = math.ceil(len(cal) / 7) if cal else 53
    GXL = PX + 20 + 30                                  # grid left (after the day labels)
    GXL += (PW - 40 - 30 - (weeks * STEP - GAP)) / 2    # centre the grid in what is left
    GY = PY + 40
    counts = sorted(n for _, n in cal if n)
    q = [counts[min(len(counts) - 1, int(len(counts) * f))] for f in (0.25, 0.5, 0.75)] if counts else [1, 2, 3]
    shades = [EMPTY, mix(ACCENT, PAPER, 0.35), mix(ACCENT, PAPER, 0.62), ACCENT, T.shade]

    def level(n):
        return 0 if not n else 1 + sum(n > t for t in q)
    cells, months, last_m = [], [], None
    for i, (day, n) in enumerate(cal):
        wk, dow = divmod(i, 7)
        x, y = GXL + wk * STEP, GY + dow * STEP
        lv = level(n)
        stroke = f'stroke="{INK}" stroke-opacity=".45" stroke-width="1.2"' if lv else f'stroke="{INK}" stroke-opacity=".1" stroke-width="1"'
        if day == today:
            stroke = f'stroke="{INK}" stroke-width="2.4"'
        cells.append(f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="3.5" fill="{shades[lv]}" {stroke}>'
                     f'<title>{n} contribution{"s" if n != 1 else ""} on {fmt_day(day, True)}</title></rect>')
        m = day[:7]
        if dow == 0 and m != last_m and int(day[8:]) <= 7:
            if not months or x - months[-1][0] > 3 * STEP:
                months.append((x, dt.date.fromisoformat(day).strftime("%b")))
            last_m = m
    mlabels = "".join(f'<text x="{x:.1f}" y="{GY - 10}" font-size="12.5" font-weight="700" fill="{INK}" fill-opacity=".65">{t}</text>' for x, t in months)
    dlabels = "".join(f'<text x="{GXL - 8:.1f}" y="{GY + r * STEP + 10}" text-anchor="end" font-size="11.5" font-weight="700" fill="{INK}" fill-opacity=".55">{t}</text>'
                      for r, t in ((1, "Mon"), (3, "Wed"), (5, "Fri")))
    LY = GY + 7 * STEP + 22
    gx_right = GXL + weeks * STEP - GAP
    more_w = tw("More", 12.5) + 4
    lx = gx_right - more_w - 6 - 5 * STEP + GAP                 # first legend cell
    legend = "".join(f'<rect x="{lx + i * STEP:.1f}" y="{LY - 10}" width="{CELL}" height="{CELL}" rx="3.5" fill="{c}" '
                     f'stroke="{INK}" stroke-opacity="{.45 if i else .1}" stroke-width="1.2"/>' for i, c in enumerate(shades))
    legend += (f'<text x="{lx - 6:.1f}" y="{LY}" text-anchor="end" font-size="12.5" font-weight="700" fill="{INK}" fill-opacity=".6">Less</text>'
               f'<text x="{gx_right:.1f}" y="{LY}" text-anchor="end" font-size="12.5" font-weight="700" fill="{INK}" fill-opacity=".6">More</text>')
    year = d.get("year")
    caption = (f'<text x="{GXL:.1f}" y="{LY}" font-size="13.5" font-weight="800" fill="{INK}">{num(year)}'
               f'<tspan font-weight="700" fill-opacity=".65"> contributions in the last year</tspan></text>')
    PH = LY + 18 - PY
    panel = tile(PX, PY, PW, PH) + mlabels + dlabels + "".join(cells) + legend + caption
    H = PY + PH + 4 + 11 + 14
    active = sum(1 for _, n in cal[-365:] if n) if cal else None
    title_extra = pill(W - 36 - 4, 26, f"{active} ACTIVE DAYS THIS YEAR" if active is not None else "SYNCING", "#FFFFFF", anchor="end")
    body = head("ACTIVITY", "Contributions & streaks", title_extra) + "".join(tiles) + panel
    cur, lng = (d.get("current") or {}).get("days"), (d.get("longest") or {}).get("days")
    desc = (f"{num(d.get('total'))} contributions since {since or 'joining'}; current streak {num(cur)} days; "
            f"longest streak {num(lng)} days; {num(year)} contributions in the last year.")
    return svg(W, H, "GitHub contributions and streaks", desc, body)


# ------------------------------------------------------------------ card 3: LeetCode
def leetcode_card(lc):
    H = 318
    solved = (lc or {}).get("solved") or {}
    total = (lc or {}).get("total") or {}
    diffs = [("Easy", EASY), ("Medium", MEDIUM), ("Hard", HARD)]
    all_solved = solved.get("All")
    # ring: what the solved problems are made of
    CX, CY, R, SW = 160, 206, 70, 24
    ring = [f'<circle cx="{CX + 4}" cy="{CY + 4}" r="{R + SW / 2 + 2}" fill="{INK}"/>',
            f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="none" stroke="{EMPTY}" stroke-width="{SW}"/>']
    if all_solved:
        a0 = -90.0
        for name, colour in diffs:
            n = solved.get(name, 0)
            if not n:
                continue
            sweep = 360 * n / all_solved
            a1 = a0 + sweep
            large = 1 if sweep > 180 else 0
            p = lambda a: (CX + R * math.cos(math.radians(a)), CY + R * math.sin(math.radians(a)))
            (x0, y0), (x1, y1) = p(a0), p(a1 - 0.01 if sweep >= 360 else a1)
            ring.append(f'<path d="M{x0:.2f} {y0:.2f}A{R} {R} 0 {large} 1 {x1:.2f} {y1:.2f}" fill="none" stroke="{colour}" stroke-width="{SW}"/>')
            if sweep < 360:
                ring.append(f'<path d="M{CX + (R - SW / 2) * math.cos(math.radians(a0)):.2f} {CY + (R - SW / 2) * math.sin(math.radians(a0)):.2f}'
                            f'L{CX + (R + SW / 2) * math.cos(math.radians(a0)):.2f} {CY + (R + SW / 2) * math.sin(math.radians(a0)):.2f}" stroke="{INK}" stroke-width="2.5"/>')
            a0 = a1
    ring += [f'<circle cx="{CX}" cy="{CY}" r="{R + SW / 2}" fill="none" stroke="{INK}" stroke-width="3"/>',
             f'<circle cx="{CX}" cy="{CY}" r="{R - SW / 2}" fill="#FFFFFF" stroke="{INK}" stroke-width="3"/>',
             f'<text x="{CX}" y="{CY + 8}" text-anchor="middle" font-size="40" font-weight="800" fill="{INK}">{num(all_solved)}</text>',
             f'<text x="{CX}" y="{CY + 30}" text-anchor="middle" font-size="12" font-weight="800" fill="{INK}" fill-opacity=".6" letter-spacing="1.5">SOLVED</text>']
    # one chunky progress bar per difficulty
    BX, BW = 296, W - 36 - 4 - 296 - 2
    bars = []
    for i, (name, colour) in enumerate(diffs):
        y = 128 + i * 60
        n, t = solved.get(name), total.get(name)
        frac = (n or 0) / t if t else 0
        bars.append(f'<circle cx="{BX + 7}" cy="{y - 6}" r="7" fill="{colour}" stroke="{INK}" stroke-width="2"/>'
                    f'<text x="{BX + 22}" y="{y}" font-size="18" font-weight="800" fill="{INK}">{name}</text>'
                    f'<text x="{BX + BW}" y="{y}" text-anchor="end" font-size="18" font-weight="800" fill="{INK}">{num(n)}'
                    f'<tspan font-size="14" fill-opacity=".55"> / {num(t)}</tspan></text>'
                    f'<rect x="{BX + 3}" y="{y + 13}" width="{BW}" height="22" rx="11" fill="{INK}"/>'
                    f'<rect x="{BX}" y="{y + 10}" width="{BW}" height="22" rx="11" fill="{EMPTY}"/>')
        if n:
            fw = max(22, BW * frac)
            bars.append(f'<rect x="{BX}" y="{y + 10}" width="{fw:.1f}" height="22" rx="11" fill="{colour}" stroke="{INK}" stroke-width="2.5"/>'
                        f'<rect x="{BX + 7}" y="{y + 14}" width="{max(0, fw - 14):.1f}" height="5" rx="2.5" fill="#FFFFFF" opacity=".55"/>')
        bars.append(f'<rect x="{BX}" y="{y + 10}" width="{BW}" height="22" rx="11" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    rank = (lc or {}).get("ranking")
    extra = pill(W - 36 - 4, 26, f"RANK #{rank:,}" if rank else "RANK —", "#FFFFFF", anchor="end")
    streak = (lc or {}).get("streak")
    if streak:
        extra += pill(W - 36 - 4 - tw(f"RANK #{rank:,}" if rank else "RANK —", 12.5) - 1.5 * len(f"RANK #{rank:,}" if rank else "RANK —") - 30 - 12,
                      26, f"MAX STREAK {streak}", ACCENT, anchor="end")
    body = head("LEETCODE", f"@{LC_USER}", extra) + "".join(ring) + "".join(bars)
    desc = (f"{num(all_solved)} problems solved: " +
            ", ".join(f"{n} {num(solved.get(n))} of {num(total.get(n))}" for n, _ in diffs) +
            (f". Global ranking {rank:,}." if rank else "."))
    return svg(W, H, "LeetCode stats", desc, body)


# ------------------------------------------------------------------ main
def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out = os.path.join(sys.argv[1], "stats")
    try:
        with open(DATA) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    failed = []
    if "--fetch" in sys.argv:
        failed = refresh(data)
        with open(DATA, "w") as f:
            json.dump(data, f, indent=1, sort_keys=True)
            f.write("\n")
    os.makedirs(out, exist_ok=True)
    for name, text in (("github.svg", github_card(data.get("github"))),
                       ("activity.svg", activity_card(data.get("github"))),
                       ("leetcode.svg", leetcode_card(data.get("leetcode")))):
        with open(os.path.join(out, name), "w") as f:
            f.write(text)
    print("stats: github.svg, activity.svg, leetcode.svg", file=sys.stderr)
    missing = [n for n in failed if n not in data]
    if missing:
        raise SystemExit(f"no {' or '.join(missing)} numbers yet; the cards show placeholders")


if __name__ == "__main__":
    main()
