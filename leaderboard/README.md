# Dino game leaderboard

A public top-10 board for the dino game, shown under the game with an arcade-style name
prompt when a visitor makes the list. The creator's own best score is pinned above it with a
crown. It uses a free **Firebase Realtime Database** through its plain REST API, so there is
no SDK, no server of your own, and no secret key anywhere in the page.

Until you finish the setup below the game behaves exactly as before and no leaderboard is shown.

## Set it up (about 5 minutes)

1. Go to <https://console.firebase.google.com> and **Add project** (for example
   `rahul-dino-leaderboard`). Google Analytics isn't needed.
2. **Build -> Realtime Database -> Create Database.** Pick the region closest to you and start
   in **locked mode**.
3. Open the **Rules** tab, replace everything with the contents of
   [`database.rules.json`](database.rules.json) and press **Publish**.
   *Already set up before "Edit name" existed? Do this step again. The game keeps working with the
   old rules, but renaming then leaves your old name visible to other visitors until you publish.*
4. On the **Data** tab copy the database URL shown at the top, like
   `https://rahul-dino-leaderboard-default-rtdb.firebaseio.com`.
5. Put that URL in [`dino/leaderboard-config.js`](../dino/leaderboard-config.js) as `databaseURL`
   and commit it (or send it to whoever is helping you, it is safe to share).
6. **Pin your own score:** on the Data tab hover the root, click `+`, add a node `owner`, and give
   it two children: `name` = `Rahul` and `score` = your best (a number). Edit it any time; the
   game reads it live, no redeploy needed.
7. Check the lock-down: `bash leaderboard/verify.sh <your database url>` should end with
   `All checks passed.` It only sends requests that should be refused, so it leaves nothing behind.

Then play a run of 30+ points: when it ends you should be asked for a name.

## What visitors see

- A **podium** for the top three and a list with score bars for ranks 4-10, topped by a pinned
  crown card with a "race to the crown" bar showing how close the best runner is to your score.
- **All time / This week / Today** tabs. The choice is remembered, and the arrow keys switch tabs.
- Click (or press Enter on) any entry to see how long that run lasted, when it happened and what
  share of your best it reached. Your own entry also gets a **Share** button.
- A new entry flashes, scores count up, and a **#1 or a crown-beating run** fires confetti. All
  motion switches off for visitors who have "reduce motion" set.
- A loading skeleton while the board loads, and an empty state with a **Play now** button.
- **Returning players are never asked twice.** The first time, a name prompt appears. After that, a
  new personal best is saved straight away under the same name ("New personal best! 00178 saved as
  Pat — you are #2"). A run that doesn't beat your best just says so and adds nothing.
- **Edit name**: a "Playing as Pat · ✎ Edit name" line under the board (and a button on your own
  entry's details) lets you change it. Your best score moves to the new name, and nobody sees both.

The tabs look at the 80 highest scores, so on a very busy board a recent low score can be
missing from "This week" or "Today". For a profile game that is rarely noticeable.

## How it works

- Scores are stored under `scores/<id>` as `{ name, score, ms, t, u }`. `ms` is how long the run
  lasted, `t` is the server timestamp, and `u` is an anonymous random id that this browser generates
  once. It is what lets the board treat "the same player under a new name" as one row.
- The page reads the top entries, keeps each player's best run, and shows the top 10.
- A prompt appears only when a run scores at least 30 **and** makes the top 10, and only if the
  board could be reached.
- Names are 1-12 characters (letters, digits, space, `.` `_` `-`). `Rahul` and look-alikes are
  reserved, and an obvious-profanity filter rejects a few words in the page.

## What the rules enforce (and what they can't)

The rules in `database.rules.json` make sure that nobody can delete or edit entries, that every
entry has exactly the expected fields (the player id `u` is optional), that the name is clean, that the score is a whole number up to
30,000, that it is plausible for the run time (at most about 25 points a second), and that the
timestamp is the server's.

A browser game cannot be made cheat-proof, though. Anyone can still post a plausible-looking score
straight to the API, and the profanity filter and the "reserved name" check live in the page and
can be bypassed the same way. For a profile game that is usually fine, and you can tidy up in
seconds: on the **Data** tab hover an entry under `scores` and click the **x** to delete it.
If it ever gets abused, set the rules back to `".write": false` to freeze the board.

The free Spark plan has generous limits; the page reads the board once on load, every 45 seconds
while open, and after each run.

The player id is not a secret: it is stored with each entry, so anyone can read it. Nothing can be
taken over with it (entries can't be edited), but someone who copies another player's id could post an
entry that makes the board show *their* chosen name for that player. That is the same kind of
tampering as posting a fake score, and the same clean-up applies: delete the entry in the console.

## Try it locally without Firebase

```bash
python3 leaderboard/mock_server.py --owner Rahul:1337
# then set databaseURL to "http://127.0.0.1:9000" in dino/leaderboard-config.js
# and open dino/index.html in a browser (change it back before committing)
```

The mock applies the same checks as the real rules, and `bash leaderboard/verify.sh
http://127.0.0.1:9000` passes against it.
