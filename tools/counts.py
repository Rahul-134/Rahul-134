"""The LeetCode solved count as the cards and the README show it: rounded down to a ten, "160+".

It comes from tools/stats.json, which the Refresh stats workflow keeps up to date; that workflow then runs
`python tools/theme.py --counts` to redraw the cards that show it and fix the number in README.md.
"""
import json
import os

STATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.json")
FALLBACK = 160                     # used only if stats.json is missing or has no LeetCode numbers


def solved_number():
    try:
        with open(STATS) as f:
            n = int(json.load(f)["leetcode"]["solved"]["All"])
    except (OSError, ValueError, KeyError, TypeError):
        n = FALLBACK
    return n // 10 * 10


def solved():
    return f"{solved_number()}+"
