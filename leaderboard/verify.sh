#!/usr/bin/env bash
# Checks that your leaderboard database is locked down the way the game expects.
#
#   bash leaderboard/verify.sh https://YOUR-PROJECT-default-rtdb.firebaseio.com
#
# It only sends requests that SHOULD be rejected, plus two reads, so it leaves no data behind.
set -u
DB="${1:-}"
if [ -z "$DB" ]; then echo "usage: bash leaderboard/verify.sh <database-url>"; exit 2; fi
DB="${DB%/}"
fail=0

expect() {   # expect <label> <expected http code> <curl args...>
  local label="$1" want="$2"; shift 2
  local got; got=$(curl -s -o /dev/null -w '%{http_code}' "$@")
  if [ "$got" = "$want" ]; then printf '  ok    %-52s (%s)\n' "$label" "$got"
  else printf '  FAIL  %-52s (got %s, wanted %s)\n' "$label" "$got" "$want"; fail=1; fi
}
NOW='{".sv":"timestamp"}'

echo "Reads that must work:"
expect "anyone can read the scores"        200 "$DB/scores.json?orderBy=%22score%22&limitToLast=1"
expect "anyone can read the owner node"    200 "$DB/owner.json"

echo "Writes that must be refused:"
expect "score above the cap"               401 -X POST -d "{\"name\":\"Cheat\",\"score\":99999,\"ms\":600000,\"t\":$NOW}" "$DB/scores.json"
expect "score impossible for the run time" 401 -X POST -d "{\"name\":\"Cheat\",\"score\":9000,\"ms\":5000,\"t\":$NOW}"    "$DB/scores.json"
expect "reserved name"                     401 -X POST -d "{\"name\":\"Rahul\",\"score\":40,\"ms\":4000,\"t\":$NOW}"        "$DB/scores.json"
expect "name with markup characters"       401 -X POST -d "{\"name\":\"<b>x</b>\",\"score\":40,\"ms\":4000,\"t\":$NOW}"     "$DB/scores.json"
expect "name too long"                     401 -X POST -d "{\"name\":\"ABCDEFGHIJKLM\",\"score\":40,\"ms\":4000,\"t\":$NOW}" "$DB/scores.json"
expect "extra field"                       401 -X POST -d "{\"name\":\"Bob\",\"score\":40,\"ms\":4000,\"t\":$NOW,\"x\":1}"  "$DB/scores.json"
expect "player id too short"               401 -X POST -d "{\"name\":\"Bob\",\"score\":40,\"ms\":4000,\"t\":$NOW,\"u\":\"abc\"}"   "$DB/scores.json"
expect "player id with odd characters"     401 -X POST -d "{\"name\":\"Bob\",\"score\":40,\"ms\":4000,\"t\":$NOW,\"u\":\"<script>alert(1)</script>\"}" "$DB/scores.json"
expect "fake timestamp"                    401 -X POST -d '{"name":"Bob","score":40,"ms":4000,"t":1}'                        "$DB/scores.json"
expect "writing the owner node"            401 -X PUT  -d '{"name":"Me","score":99999}'                                       "$DB/owner.json"
expect "deleting all scores"               401 -X DELETE                                                                      "$DB/scores.json"
expect "reading the whole database"        401 "$DB/.json"

echo
if [ "$fail" = 0 ]; then echo "All checks passed."; else echo "Some checks failed - re-publish leaderboard/database.rules.json and try again."; fi
exit "$fail"
