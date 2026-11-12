"""Counts the cards and the README show: the LeetCode solved count rounded down to a ten ("160+"), and GitHub followers.

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


def followers():
    """GitHub followers from tools/stats.json, or None until the Refresh stats workflow has fetched them."""
    try:
        with open(STATS) as f:
            return int(json.load(f)["github"]["followers"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
