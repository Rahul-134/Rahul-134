/*
 * Leaderboard settings. Edit this file by hand; the theme tool never touches it.
 *
 * 1. Create a free Firebase Realtime Database (see /leaderboard/README.md).
 * 2. Paste its URL below, e.g. "https://rahul-dino-default-rtdb.firebaseio.com".
 *
 * Leave databaseURL empty and the game simply runs without a leaderboard.
 *
 * `owner` is a fallback for the pinned crown line. The live value is read from the
 * database's /owner node (editable in the Firebase console), so you can update your
 * best score without redeploying anything.
 */
window.DINO_LEADERBOARD = {
  databaseURL: "https://rahul-dino-leaderboard-default-rtdb.asia-southeast1.firebasedatabase.app",
  owner: { name: "Rahul", score: null }
};
