#!/usr/bin/env python3
"""A tiny local stand-in for the Firebase Realtime Database, for trying the leaderboard offline.

    python3 leaderboard/mock_server.py                      # serves http://127.0.0.1:9000
    python3 leaderboard/mock_server.py --owner Rahul:1337   # also pins a creator score

Then point dino/leaderboard-config.js at "http://127.0.0.1:9000" and open dino/index.html.

It applies the same checks as database.rules.json (name, score cap, score-vs-run-time, no extra
fields, no overwrites, owner node read-only). Data lives in memory and vanishes on exit.
Test helper: GET /__mode?v=down makes every request fail with 503, /__mode?v=ok restores it.
"""
import argparse
import json
import re
import secrets
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

SCORES = {}
OWNER = {}
MODE = {"down": False}
NAME_OK = re.compile(r"^[A-Za-z0-9 ._-]+$")


def valid(entry):
    """Mirror of the .validate rules in database.rules.json."""
    if not isinstance(entry, dict) or set(entry) != {"name", "score", "ms", "t"}:
        return False
    name, score, ms = entry["name"], entry["score"], entry["ms"]
    if not (isinstance(name, str) and 1 <= len(name) <= 12 and NAME_OK.match(name) and "rahul" not in name.lower()):
        return False
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
    if not (num(score) and 1 <= score <= 30000 and score == int(score)):
        return False
    if not (num(ms) and 1000 <= ms <= 3600000):
        return False
    return score <= ms / 1000 * 25 + 30


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body=None):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204, None)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/__mode":
            MODE["down"] = parse_qs(u.query).get("v", ["ok"])[0] == "down"
            return self._send(200, {"down": MODE["down"]})
        if MODE["down"]:
            return self._send(503, {"error": "down"})
        if u.path == "/scores.json":
            q = parse_qs(u.query)
            n = int(q.get("limitToLast", ["100"])[0])
            top = sorted(SCORES.items(), key=lambda kv: kv[1]["score"])[-n:]
            return self._send(200, dict(top) or None)
        if u.path == "/owner.json":
            return self._send(200, OWNER or None)
        return self._send(401, {"error": "Permission denied"})

    def do_POST(self):
        if MODE["down"]:
            return self._send(503, {"error": "down"})
        if urlparse(self.path).path != "/scores.json":
            return self._send(401, {"error": "Permission denied"})
        try:
            entry = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        except ValueError:
            return self._send(400, {"error": "bad json"})
        if isinstance(entry, dict) and entry.get("t") == {".sv": "timestamp"}:
            entry["t"] = int(time.time() * 1000)
        else:
            return self._send(401, {"error": "Permission denied"})
        if not valid(entry):
            return self._send(401, {"error": "Permission denied"})
        key = "-" + secrets.token_urlsafe(9)
        SCORES[key] = entry
        return self._send(200, {"name": key})

    def do_PUT(self):
        self._send(401, {"error": "Permission denied"})

    do_DELETE = do_PATCH = do_PUT


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--owner", help="pin a creator score, e.g. Rahul:1337")
    args = ap.parse_args()
    if args.owner:
        name, _, score = args.owner.partition(":")
        OWNER.update({"name": name or "Rahul", "score": int(score)})
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"mock leaderboard on http://127.0.0.1:{args.port}  (Ctrl+C to stop)", file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
