#!/usr/bin/env python3
"""Point the README's cards at the Day or the Night set.

    python tools/daynight.py            # auto: Night from 7 pm to 7 am in TIMEZONE, Day otherwise
    python tools/daynight.py night      # force one look
    python tools/daynight.py day
    python tools/daynight.py --status   # print which look the README shows now

The Night cards are the same files under night/ (tools/theme.py draws both sets). This only rewrites
the image paths in README.md, so switching is instant and never redraws anything. The "Day / Night"
workflow runs it at 7 am and 7 pm.
"""
import datetime as dt
import os
import re
import sys

try:
    from zoneinfo import ZoneInfo
except ImportError:                      # Python < 3.9
    ZoneInfo = None

TIMEZONE = "Asia/Kolkata"                # whose 7 am / 7 pm the README follows
DAY_STARTS, NIGHT_STARTS = 7, 19         # hours, 24-hour clock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(ROOT, "README.md")
# local card images: the banner, About (card, intro and its rows), Tech Stack, project, stats and Connect cards,
# and the headings, captions and link buttons (labels/)
CARD = re.compile(r'((?:src|srcset)=")(night/)?((?:dino-banner(?:-mobile)?|about-card|tech-stack|(?:about|labels|projects|stats|connect)/[\w-]+)\.svg)(")')


def wanted_now():
    now = dt.datetime.now(ZoneInfo(TIMEZONE)) if ZoneInfo else dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)
    return "day" if DAY_STARTS <= now.hour < NIGHT_STARTS else "night"


def current(text):
    found = CARD.findall(text)
    if not found:
        return None
    return "night" if all(m[1] for m in found) else "day" if not any(m[1] for m in found) else "mixed"


def switch(text, mode):
    def sub(m):
        path = m.group(3)
        if mode == "night" and not os.path.exists(os.path.join(ROOT, "night", path)):
            return m.group(1) + path + m.group(4)          # no night file yet: keep the day one
        return m.group(1) + ("night/" if mode == "night" else "") + path + m.group(4)
    return CARD.sub(sub, text)


def main():
    args = sys.argv[1:]
    with open(README, encoding="utf-8") as f:
        text = f.read()
    if "--status" in args:
        print(current(text))
        return
    mode = args[0].lower() if args else "auto"
    if mode == "auto":
        mode = wanted_now()
    if mode not in ("day", "night"):
        raise SystemExit("usage: daynight.py [auto|day|night|--status]")
    new = switch(text, mode)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"README switched to {mode}")
    else:
        print(f"README already shows {mode}")


if __name__ == "__main__":
    main()
