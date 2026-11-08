/*
 * Global leaderboard for the dino game.
 *
 * Talks to a Firebase Realtime Database through its REST API (no SDK, no keys in the page).
 * Setup: see /leaderboard/README.md. Until `databaseURL` is set in leaderboard-config.js
 * this file does nothing and the game behaves exactly as before.
 *
 * The game calls:  DinoLB.runStarted()  and  DinoLB.runEnded(score, runMs)
 */
(function () {
  'use strict';

  var CFG = window.DINO_LEADERBOARD || {};
  var DB = String(CFG.databaseURL || '').trim().replace(/\/+$/, '');
  var ENABLED = /^https:\/\/[^\s\/]+(\/\S*)?$/i.test(DB) || /^http:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(DB);

  function noop() {}
  if (!ENABLED) { window.DinoLB = { enabled: false, runStarted: noop, runEnded: noop }; return; }

  var TOP = 10;               // rows shown
  var FETCH = 80;             // rows fetched, so repeat players can be collapsed to their best run
  var MIN_SCORE = 30;         // below this a run is not worth putting on a board
  var MAX_NAME = 12;
  var POLL_MS = 45000;
  var TIMEOUT_MS = 9000;

  var board = [];             // [{id,name,score}] best run per name, best first
  var owner = normaliseOwner(CFG.owner);
  var mine = loadMine();      // ids of entries submitted from this browser
  var myBest = Number(recall('dinoLbBest')) || 0;   // best score this browser has put on the board
  var myUid = recall('dinoLbUid');                  // anonymous id that ties this browser's entries together
  if (!/^[A-Za-z0-9]{12,32}$/.test(myUid || '')) { myUid = randomId(); store('dinoLbUid', myUid); }
  var legacy = false;         // true once the database rules turned out not to accept the optional id
  var run = null;             // {score, ms, id, submitted}
  var runCounter = 0;
  var lastSubmitAt = 0;
  var busy = false;
  var loadOk = false;         // did the most recent board fetch succeed?
  var allRows = [];           // every entry after "one row per browser", best first (before the time filter)
  var view = recall('dinoLbView') || 'all';   // 'all' | 'week' | 'day'
  if (['all', 'week', 'day'].indexOf(view) === -1) view = 'all';
  var loadedAt = 0;           // when the board was last fetched successfully
  var loading = true;         // first fetch still running
  var selected = null;        // id of the entry whose details are open
  var seen = {};              // ids already shown, so only genuinely new entries flash
  var seenInit = false;       // true once the first real board has been drawn
  var lastSig = '';
  var motion = !(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) && !navigator.webdriver;

  /* ---------- tiny helpers ---------- */
  function $(sel, root) { return (root || document).querySelector(sel); }
  function el(tag, cls, text) { var n = document.createElement(tag); if (cls) n.className = cls; if (text != null) n.textContent = text; return n; }
  function pad5(n) { return ('00000' + n).slice(-5); }
  function store(key, val) { try { localStorage.setItem(key, val); } catch (e) {} }
  function recall(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function randomId() {
    var s = '', n = 20, b = null;
    try { b = new Uint8Array(n); (window.crypto || window.msCrypto).getRandomValues(b); } catch (e) { b = null; }
    for (var i = 0; i < n; i++) s += ((b ? b[i] : Math.floor(Math.random() * 256)) % 36).toString(36);
    return s;
  }
  function loadMine() { try { return JSON.parse(recall('dinoLbMine') || '[]').slice(-40); } catch (e) { return []; } }
  function normaliseOwner(o) {
    if (!o || typeof o !== 'object') return null;
    var s = Number(o.score);
    if (!isFinite(s) || s <= 0) return null;
    return { name: String(o.name || 'Rahul').slice(0, 20), score: Math.floor(s) };
  }

  function request(path, opts) {
    var ctl = typeof AbortController === 'function' ? new AbortController() : null;
    var timer = ctl ? setTimeout(function () { ctl.abort(); }, TIMEOUT_MS) : null;
    var init = Object.assign({ cache: 'no-store' }, opts || {});
    if (ctl) init.signal = ctl.signal;
    return fetch(DB + path, init).then(function (r) {
      if (timer) clearTimeout(timer);
      if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
      return r.json();
    }, function (err) { if (timer) clearTimeout(timer); throw err; });
  }

  /* ---------- names ---------- */
  var BLOCK = ['fuck', 'shit', 'bitch', 'cunt', 'slut', 'whore', 'nigg', 'fagg', 'rape', 'nazi', 'hitler', 'porn'];
  function squash(s) {
    return s.toLowerCase().replace(/0/g, 'o').replace(/[1!|]/g, 'i').replace(/3/g, 'e').replace(/[4@]/g, 'a')
      .replace(/[5$]/g, 's').replace(/7/g, 't').replace(/[^a-z]/g, '');
  }
  function cleanName(raw) { return String(raw || '').replace(/[^A-Za-z0-9 ._-]/g, '').replace(/\s+/g, ' ').trim().slice(0, MAX_NAME); }
  function nameProblem(name) {
    if (!name) return 'Pick a name first.';
    var flat = squash(name);
    // look-alikes: 1, |, ! and capital-I all read as "l" or "i", so fold them together for this check
    if (flat.replace(/i/g, 'l').indexOf('rahul') !== -1) return 'That name is reserved for the creator.';
    for (var i = 0; i < BLOCK.length; i++) if (flat.indexOf(BLOCK[i]) !== -1) return 'Please pick a different name.';
    return '';
  }

  /* ---------- UI ---------- */
  var css = [
    '@font-face{font-family:Nunito;font-style:normal;font-weight:200 1000;font-display:swap;src:url(fonts/nunito-latin-wght-normal.woff2) format("woff2")}',
    '.stage{position:relative}',
    '.lb{--ink:#f6f2ea;--ink2:#c3bdb2;--ink3:#948f86;--gold:#f2c46d;--silver:#cfd5df;--bronze:#dca071;--glass:linear-gradient(180deg,rgba(255,255,255,.11),rgba(255,255,255,.045));--rim:inset 0 1px 0 rgba(255,255,255,.2);position:relative;isolation:isolate;overflow:hidden;width:min(100%,900px);padding:18px;border-radius:32px;color:var(--ink);font-family:Nunito,ui-rounded,"SF Pro Rounded",system-ui,-apple-system,"Segoe UI",sans-serif;font-weight:600;background:radial-gradient(460px 280px at 8% -6%,rgba(var(--accent-rgb),.30),transparent 70%),radial-gradient(420px 320px at 105% 22%,rgba(255,168,140,.17),transparent 70%),radial-gradient(460px 340px at 38% 112%,rgba(140,150,255,.18),transparent 70%),linear-gradient(160deg,#26262c,#18181d);border:1px solid rgba(255,255,255,.11);box-shadow:0 34px 60px -24px rgba(0,0,0,.7),inset 0 1px 0 rgba(255,255,255,.12)}',
    '.lb button{font-family:inherit;font-size:14px;font-weight:800;color:#1d1a15;background:var(--accent);border:0;border-radius:99px;padding:10px 20px;min-height:0;box-shadow:inset 0 2px 3px rgba(255,255,255,.55),inset 0 -3px 5px rgba(0,0,0,.18),0 6px 12px rgba(0,0,0,.35);transition:transform .2s,filter .2s}',
    '.lb button:hover{transform:translateY(-1px);filter:brightness(1.05)}',
    '.lb button.ghost{color:var(--ink);background:var(--glass);border:1px solid rgba(255,255,255,.13);box-shadow:var(--rim),0 6px 14px rgba(0,0,0,.3)}',
    '.lb header,.lb .foot,.lb .own,.lb .detail{-webkit-backdrop-filter:blur(16px) saturate(1.4);backdrop-filter:blur(16px) saturate(1.4)}',
    '.lb header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:14px;padding:10px 12px 10px 18px;border-radius:24px;background:var(--glass);border:1px solid rgba(255,255,255,.13);box-shadow:var(--rim),0 12px 26px rgba(0,0,0,.25)}',
    '.lb h2{margin:0;display:flex;align-items:center;gap:10px;font-size:21px;font-weight:900;letter-spacing:-.01em;color:var(--ink)}',
    '.lb h2 small{margin:0;padding:3px 10px;border-radius:99px;background:rgba(0,0,0,.22);box-shadow:inset 0 1px 3px rgba(0,0,0,.4);color:var(--ink3);font-size:12px;font-weight:700;letter-spacing:.02em}',
    '.lb .tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap}',
    '.lb .tabs{display:inline-flex;padding:4px;border-radius:99px;background:rgba(0,0,0,.26);box-shadow:inset 0 2px 5px rgba(0,0,0,.45),0 1px 0 rgba(255,255,255,.07)}',
    '.lb .tab{padding:7px 15px;font-size:13px;font-weight:700;border-radius:99px;background:transparent;color:var(--ink2);box-shadow:none;letter-spacing:0}',
    '.lb .tab:hover{color:#fff;transform:none;filter:none}',
    '.lb .tab[aria-selected=true]{background:var(--accent);color:#1d1a15;font-weight:900;box-shadow:inset 0 2px 3px rgba(255,255,255,.55),inset 0 -3px 5px rgba(0,0,0,.2),0 5px 10px rgba(0,0,0,.4)}',
    '.lb .icon{padding:9px 16px;font-size:13px;white-space:nowrap}',
    '.lb .icon.spin::first-letter{display:inline-block;animation:lbspin .8s linear infinite}',
    '.lb ol{list-style:none;margin:0;padding:0}',
    '.lb .own{margin-bottom:16px;padding:14px 18px 15px;border-radius:26px;background:linear-gradient(135deg,rgba(var(--accent-rgb),.24),rgba(255,255,255,.05) 72%);border:1px solid rgba(255,255,255,.15);box-shadow:var(--rim),0 14px 28px rgba(0,0,0,.28)}',
    '.lb .ownrow{display:flex;align-items:center;gap:12px;font-size:15px}',
    '.lb .ownrow>span:first-child{flex:none;width:36px;height:36px;border-radius:50%;display:grid;place-items:center;font-size:18px;background:linear-gradient(180deg,#fff0c4,var(--gold));box-shadow:inset 0 -3px 4px rgba(0,0,0,.2),0 4px 8px rgba(0,0,0,.35)}',
    '.lb .own b{color:var(--ink);font-size:17px;font-weight:900}',
    '.lb .own .d{color:var(--ink2);font-size:13px;font-weight:600;flex:1}',
    '.lb .own i{font-style:normal;padding:4px 14px;border-radius:99px;background:rgba(0,0,0,.28);box-shadow:inset 0 2px 4px rgba(0,0,0,.45);color:var(--ink);font-size:19px;font-weight:900;letter-spacing:.03em}',
    '.lb .track{position:relative;height:12px;margin-top:12px;border-radius:99px;background:rgba(0,0,0,.3);box-shadow:inset 0 2px 4px rgba(0,0,0,.5),0 1px 0 rgba(255,255,255,.07);overflow:hidden}',
    '.lb .track .fill{display:block;height:100%;width:0;border-radius:99px;background:var(--accent);box-shadow:inset 0 2px 2px rgba(255,255,255,.55),inset 0 -2px 3px rgba(0,0,0,.2);transition:width 1s cubic-bezier(.2,.8,.2,1)}',
    '.lb .tl{margin:8px 2px 0;font-size:13px;font-weight:600;color:var(--ink2)}',
    '.lb .podium{display:flex;align-items:flex-end;justify-content:center;gap:8px;margin:4px 0 0;padding-top:12px;background:radial-gradient(ellipse 55% 65% at 50% 38%,rgba(255,255,255,.08),transparent 72%)}',
    '.lb .pod{--d:68px;flex:1 1 0;max-width:236px;min-width:0;display:flex;flex-direction:column;align-items:center;text-align:center;cursor:pointer;outline:none}',
    '.lb .pod.p1{order:2;--d:92px;--m:var(--gold);--mrgb:242,196,109}.lb .pod.p2{order:1;--m:var(--silver);--mrgb:207,213,223}.lb .pod.p3{order:3;--m:var(--bronze);--mrgb:220,160,113}',
    '.lb .pod.empty{cursor:default}',
    '.lb .mw{position:relative;width:calc(var(--d) + 34px);height:calc(var(--d) + 34px);display:grid;place-items:center;transition:transform .25s}',
    '.lb .pod:hover .mw,.lb .pod:focus-visible .mw{transform:translateY(-4px)}.lb .pod.empty:hover .mw{transform:none}',
    '.lb .wr{position:absolute;inset:0;width:100%;height:100%;color:var(--m);overflow:visible;filter:drop-shadow(0 3px 4px rgba(0,0,0,.4))}',
    '.lb .av{position:relative;width:var(--d);height:var(--d);flex:none;border-radius:50%;overflow:hidden;display:block}',
    '.lb .av::after{content:"";position:absolute;inset:0;border-radius:50%;pointer-events:none;box-shadow:inset 0 4px 6px rgba(255,255,255,.38),inset 0 -6px 10px rgba(0,0,0,.28)}',
    '.lb .av svg{display:block;width:100%;height:100%;shape-rendering:crispEdges}',
    '.lb .pod .av{border:4px solid var(--m);box-shadow:0 12px 22px rgba(0,0,0,.45)}',
    '.lb .pod .rkd{position:absolute;left:50%;bottom:2px;transform:translateX(-50%);min-width:26px;height:26px;padding:0 5px;border-radius:99px;display:grid;place-items:center;font-size:13px;font-weight:900;color:#3a2c14;background:linear-gradient(180deg,#fffaf0,var(--m));box-shadow:inset 0 -2px 3px rgba(0,0,0,.2),0 3px 7px rgba(0,0,0,.45)}',
    '.lb .pod.empty .av{background:rgba(0,0,0,.25);border:2px solid rgba(255,255,255,.09);box-shadow:inset 0 4px 9px rgba(0,0,0,.55);display:grid;place-items:center;color:var(--ink3);font-size:26px;font-weight:800}',
    '.lb .pod.empty .av::after{display:none}',
    '.lb .pod.empty .wr,.lb .pod.empty .rkd{display:none}',
    '.lb .pod .nm{max-width:100%;margin-top:2px;font-size:16px;font-weight:800;color:var(--ink)}',
    '.lb .sc{display:inline-flex;align-items:center;gap:7px;color:var(--ink);font-weight:900;letter-spacing:.03em;font-variant-numeric:tabular-nums}',
    '.lb .sc::before{content:"";flex:none;width:17px;height:17px;border-radius:50%;background:radial-gradient(circle at 35% 28%,#fff6d6,var(--gold) 52%,#c98f2d);box-shadow:inset 0 -2px 3px rgba(0,0,0,.28),0 2px 3px rgba(0,0,0,.4)}',
    '.lb .pod .sc{margin:7px 0 12px;padding:4px 14px 4px 8px;border-radius:99px;background:rgba(0,0,0,.28);box-shadow:inset 0 2px 4px rgba(0,0,0,.45),0 1px 0 rgba(255,255,255,.08);font-size:17px}',
    '.lb .pod.empty .sc{background:none;box-shadow:none;color:var(--ink3)}.lb .pod.empty .sc::before{display:none}',
    '.lb .pod .blk{width:100%;display:flex;align-items:flex-start;justify-content:center;padding-top:8px;border-radius:24px 24px 10px 10px;color:rgba(58,40,12,.5);font-weight:900;font-size:46px;line-height:1.05;text-shadow:0 1px 0 rgba(255,255,255,.5);background:linear-gradient(180deg,rgba(var(--mrgb),1),rgba(var(--mrgb),.7));box-shadow:inset 0 5px 7px rgba(255,255,255,.5),inset 0 -12px 18px rgba(0,0,0,.2),0 16px 26px rgba(0,0,0,.4);transition:filter .2s}',
    '.lb .pod:hover .blk,.lb .pod:focus-visible .blk{filter:brightness(1.08)}',
    '.lb .p1 .blk{height:100px}.lb .p2 .blk{height:76px}.lb .p3 .blk{height:58px}',
    '.lb .pod.empty .blk{background:rgba(255,255,255,.05);box-shadow:inset 0 4px 9px rgba(0,0,0,.45),0 1px 0 rgba(255,255,255,.06);color:rgba(255,255,255,.16);text-shadow:none}',
    '.lb .pod.me .av{box-shadow:0 0 0 4px rgba(var(--accent-rgb),1),0 12px 22px rgba(0,0,0,.45)}',
    '.lb .pod.me .nm{color:var(--accent)}',
    '.lb .pod.sel .av{box-shadow:0 0 0 4px #fff,0 12px 22px rgba(0,0,0,.45)}',
    '.lb .rest{display:grid;gap:10px;margin:16px 0 0;padding:0}',
    '.lb .row{--d:44px}',
    '.lb .rowbtn{width:100%;min-height:0;display:grid;grid-template-columns:34px 46px minmax(0,1fr) auto;align-items:center;gap:13px;padding:10px 14px 10px 12px;font:inherit;font-size:15px;font-weight:700;color:var(--ink);background:var(--glass);border:1px solid rgba(255,255,255,.12);border-radius:24px;text-align:left;cursor:pointer;box-shadow:var(--rim),0 12px 22px rgba(0,0,0,.28);-webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);transition:transform .2s,border-color .2s,filter .2s}',
    '.lb .rowbtn:hover{transform:translateY(-2px);filter:brightness(1.08)}',
    '.lb .rowbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}',
    '.lb .row.me .rowbtn{background:linear-gradient(135deg,rgba(var(--accent-rgb),.3),rgba(255,255,255,.07));border-color:rgba(var(--accent-rgb),.6)}',
    '.lb .row.sel .rowbtn{border-color:rgba(255,255,255,.65)}',
    '.lb .row .rk{width:32px;height:32px;display:grid;place-items:center;border-radius:50%;background:rgba(0,0,0,.26);box-shadow:inset 0 2px 4px rgba(0,0,0,.45),0 1px 0 rgba(255,255,255,.07);color:var(--ink2);font-size:14px;font-weight:900}',
    '.lb .row .av{--d:46px;border:3px solid rgba(255,255,255,.22);box-shadow:0 6px 12px rgba(0,0,0,.35)}.lb .row.me .av{border-color:var(--accent)}',
    '.lb .info{display:grid;gap:7px;min-width:0}',
    '.lb .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
    '.lb .nm em{font-style:normal;margin-left:8px;padding:2px 8px;border-radius:99px;background:var(--accent);color:#1d1a15;font-size:10px;font-weight:900;letter-spacing:.08em;vertical-align:2px;box-shadow:inset 0 1px 2px rgba(255,255,255,.55),0 2px 4px rgba(0,0,0,.3)}',
    '.lb .bar{display:block;height:7px;max-width:260px;border-radius:99px;background:rgba(0,0,0,.3);box-shadow:inset 0 1px 3px rgba(0,0,0,.5);overflow:hidden}',
    '.lb .bar i{display:block;height:100%;width:0;border-radius:99px;background:linear-gradient(180deg,rgba(255,255,255,.35),rgba(var(--accent-rgb),.9) 45%,rgba(var(--accent-rgb),.8));transition:width .8s cubic-bezier(.2,.8,.2,1)}',
    '.lb .rowbtn .sc{padding:6px 14px 6px 9px;border-radius:99px;background:rgba(0,0,0,.28);box-shadow:inset 0 2px 4px rgba(0,0,0,.45),0 1px 0 rgba(255,255,255,.08);font-size:17px}',
    '.lb .detail{margin-top:16px;padding:16px 18px;border-radius:26px;display:grid;gap:14px;background:var(--glass);border:1px solid rgba(255,255,255,.13);box-shadow:var(--rim),0 14px 28px rgba(0,0,0,.28)}',
    '.lb .detail.mine{background:linear-gradient(135deg,rgba(var(--accent-rgb),.26),rgba(255,255,255,.05) 70%);border-color:rgba(var(--accent-rgb),.5)}',
    '.lb .detail[hidden]{display:none}',
    '.lb .dhead{display:flex;align-items:center;gap:14px}',
    '.lb .dbadge{flex:none;width:50px;height:50px;border-radius:18px;display:grid;place-items:center;background:linear-gradient(180deg,rgba(255,255,255,.16),rgba(255,255,255,.06));box-shadow:inset 0 2px 2px rgba(255,255,255,.25),inset 0 -3px 5px rgba(0,0,0,.25),0 6px 12px rgba(0,0,0,.3);font-size:24px;font-weight:900;color:var(--ink2)}',
    '.lb .dwho{flex:1;min-width:0;display:grid;gap:3px}',
    '.lb .dname{font-size:19px;font-weight:900;color:var(--ink);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
    '.lb .dname em{font-style:normal;margin-left:9px;padding:2px 8px;border-radius:99px;background:var(--accent);color:#1d1a15;font-size:10px;font-weight:900;letter-spacing:.08em;vertical-align:3px}',
    '.lb .dsub{font-size:13px;font-weight:600;color:var(--ink3)}',
    '.lb .dscore{flex:none;text-align:right;font-size:34px;font-weight:900;line-height:1;letter-spacing:.02em;color:var(--ink);font-variant-numeric:tabular-nums}',
    '.lb .dscore small{display:block;margin-top:6px;font-size:11px;font-weight:800;letter-spacing:.14em;color:var(--ink3)}',
    '.lb .dprog{display:grid;gap:8px}',
    '.lb .dprog p{margin:0;display:flex;justify-content:space-between;gap:10px;font-size:13px;font-weight:700;color:var(--ink2)}',
    '.lb .dprog .track{margin:0;height:10px}',
    '.lb .dacts{display:flex;gap:8px;flex-wrap:wrap}',
    '.lb .dacts button{padding:8px 18px;font-size:13px}',
    '.lb .empty-state{margin-top:6px;padding:26px 14px 22px;text-align:center;color:var(--ink2);font-size:15px;font-weight:600;border-radius:26px;background:var(--glass);border:1px solid rgba(255,255,255,.12);box-shadow:var(--rim),0 12px 24px rgba(0,0,0,.25)}',
    '.lb .empty-state .big{display:block;font-size:44px;margin-bottom:8px}.lb .empty-state b{display:block;color:var(--ink);font-size:18px;font-weight:900;margin-bottom:4px}',
    '.lb .empty-state button{margin-top:14px;padding:11px 24px;font-size:14px}',
    '.lb .skel{display:grid;gap:10px;margin:4px 0}.lb .skel i{display:block;height:62px;border-radius:24px;background:linear-gradient(90deg,rgba(255,255,255,.05) 25%,rgba(255,255,255,.12) 50%,rgba(255,255,255,.05) 75%);background-size:300% 100%;animation:lbshim 1.3s linear infinite}',
    '.lb .msg{margin:14px 0 0;padding:12px 16px;border-radius:22px;font-size:14px;font-weight:700;line-height:1.45;color:var(--ink2);background:var(--glass);border:1px solid rgba(255,255,255,.13);box-shadow:var(--rim),0 10px 22px rgba(0,0,0,.25);-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px)}',
    '.lb .msg:empty{display:none}.lb .msg b{color:#bff0d1;font-weight:900}',
    '.lb .msg.ok{color:#e9f8ef;background:linear-gradient(135deg,rgba(120,210,160,.26),rgba(255,255,255,.05));border-color:rgba(150,225,180,.42)}',
    '.lb .msg.ok::before,.lb .msg.err::before{display:inline-grid;place-items:center;width:22px;height:22px;margin-right:10px;border-radius:50%;font-size:12px;font-weight:900;vertical-align:1px;box-shadow:inset 0 -2px 3px rgba(0,0,0,.2),0 2px 5px rgba(0,0,0,.35)}',
    '.lb .msg.ok::before{content:"\\2713";background:linear-gradient(180deg,#d6f7e2,#78d29a);color:#14351f}',
    '.lb .msg.err{color:#ffe4e0;background:linear-gradient(135deg,rgba(255,130,120,.26),rgba(255,255,255,.05));border-color:rgba(255,160,150,.45)}.lb .msg.err b{color:#ffc4bd}',
    '.lb .msg.err::before{content:"!";background:linear-gradient(180deg,#ffd9d4,#ff8f84);color:#451410}',
    '.lb .foot{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-top:16px;padding:10px 16px 10px 12px;border-radius:24px;font-size:13px;font-weight:700;color:var(--ink3);background:var(--glass);border:1px solid rgba(255,255,255,.13);box-shadow:var(--rim),0 12px 26px rgba(0,0,0,.25)}',
    '.lb .who{display:inline-flex;align-items:center;gap:11px}',
    '.lb .who .av{width:36px;height:36px;display:grid;place-items:center;border-radius:50%;background:var(--accent);color:#1d1a15;font-size:15px;font-weight:900;text-transform:uppercase;box-shadow:inset 0 2px 3px rgba(255,255,255,.55),inset 0 -3px 5px rgba(0,0,0,.2),0 4px 8px rgba(0,0,0,.35)}',
    '.lb .who .av::after{display:none}',
    '.lb .who .pn{display:grid;line-height:1.2}.lb .who .pn small{font-size:10.5px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:var(--ink3)}.lb .who .pn b{color:var(--ink);font-size:16px;font-weight:900}',
    '.lb .linklike{padding:7px 14px;margin-left:2px;font-size:12px;color:var(--ink);background:var(--glass);border:1px solid rgba(255,255,255,.13);border-radius:99px;box-shadow:var(--rim),0 5px 12px rgba(0,0,0,.28)}',
    '.lb .upd{display:inline-flex;align-items:center;gap:8px}.lb .upd:empty{display:none}.lb .upd::before{content:"";width:9px;height:9px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#d6f7e2,#78d29a 60%);box-shadow:inset 0 -1px 2px rgba(0,0,0,.25),0 1px 3px rgba(0,0,0,.4)}',
    '@keyframes lbrise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}',
    '@keyframes lbgrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}',
    '@keyframes lbflash{0%{box-shadow:0 0 0 0 rgba(var(--accent-rgb),.7)}100%{box-shadow:0 0 0 14px rgba(var(--accent-rgb),0)}}',
    '@keyframes lbspin{to{transform:rotate(360deg)}}@keyframes lbshim{to{background-position:-300% 0}}@keyframes lbpulse{50%{opacity:.4}}',
    '.lb.fx .pod{animation:lbrise .55s cubic-bezier(.2,.9,.3,1.2) both;animation-delay:calc(var(--i,0)*90ms)}',
    '.lb.fx .pod .blk{transform-origin:bottom;animation:lbgrow .6s cubic-bezier(.2,.9,.3,1) both;animation-delay:calc(var(--i,0)*90ms + 80ms)}',
    '.lb.fx .row{animation:lbrise .45s ease both;animation-delay:calc(var(--i,0)*45ms + 250ms)}',
    '.lb.fx .msg:not(:empty),.lb.fx .detail:not([hidden]){animation:lbrise .4s cubic-bezier(.2,.9,.3,1.1) both}',
    '.lb.fx .upd::before{animation:lbpulse 2s ease-in-out infinite}',
    '.lb.fx .fresh .rowbtn,.lb.fx .pod.fresh .av{animation:lbflash 1.2s ease-out 2}',
    '.sub-ov{position:absolute;top:0;left:0;width:100%;aspect-ratio:900/260;display:flex;align-items:center;justify-content:center;background:rgba(12,12,16,.5);-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);border-radius:14px;z-index:5;padding:10px;font-family:Nunito,ui-rounded,system-ui,sans-serif}',
    '.sub-ov[hidden]{display:none}',
    '.sub-card{width:min(100%,400px);padding:20px 22px;border-radius:30px;text-align:center;color:#f6f2ea;background:linear-gradient(180deg,rgba(255,255,255,.17),rgba(255,255,255,.07));border:1px solid rgba(255,255,255,.2);box-shadow:inset 0 1px 0 rgba(255,255,255,.3),0 24px 50px rgba(0,0,0,.5);-webkit-backdrop-filter:blur(20px) saturate(1.4);backdrop-filter:blur(20px) saturate(1.4)}',
    '.sub-card h3{margin:0 0 4px;font-size:18px;font-weight:900;color:#fff;letter-spacing:0}.sub-card h3 b{color:var(--accent)}',
    '.sub-card p{margin:0 0 12px;font-size:13px;font-weight:600;color:#c3bdb2}',
    '.sub-card input{width:100%;font:inherit;font-size:18px;font-weight:800;text-align:center;letter-spacing:.02em;color:#fff;background:rgba(0,0,0,.3);border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:12px 14px;outline:none;box-shadow:inset 0 3px 7px rgba(0,0,0,.5)}',
    '.sub-card input:focus{border-color:var(--accent)}',
    '.sub-card .row{display:flex;gap:10px;margin-top:12px;justify-content:center}',
    '.sub-card .row button{min-height:0;padding:11px 22px;font-family:inherit;font-size:14px;font-weight:800;border-radius:99px;color:#1d1a15;background:var(--accent);border:0;box-shadow:inset 0 2px 3px rgba(255,255,255,.55),inset 0 -3px 5px rgba(0,0,0,.18),0 6px 12px rgba(0,0,0,.35)}',
    '.sub-card .row button.ghost{color:#f6f2ea;background:linear-gradient(180deg,rgba(255,255,255,.14),rgba(255,255,255,.05));border:1px solid rgba(255,255,255,.16);box-shadow:inset 0 1px 0 rgba(255,255,255,.2),0 6px 12px rgba(0,0,0,.3)}',
    '.sub-card .msg{margin:8px 0 0;min-height:1.3em;font-size:13px;font-weight:700;color:#ffb3aa}',
    '@media (max-width:560px){.sub-ov{aspect-ratio:auto;min-height:240px}.lb{padding:12px;border-radius:26px}.lb header{padding:10px 12px;border-radius:20px}.lb h2{font-size:18px}.lb h2 small{display:none}.lb .podium{gap:4px}.lb .pod{--d:56px}.lb .pod.p1{--d:74px}.lb .mw{width:calc(var(--d) + 26px);height:calc(var(--d) + 26px)}.lb .pod .nm{font-size:13px}.lb .pod .sc{font-size:14px;padding:3px 10px 3px 6px}.lb .pod .sc::before{width:13px;height:13px}.lb .pod .blk{font-size:34px}.lb .p1 .blk{height:86px}.lb .p2 .blk{height:64px}.lb .p3 .blk{height:48px}.lb .rowbtn{grid-template-columns:28px 40px minmax(0,1fr) auto;font-size:14px;gap:9px;padding:9px 10px 9px 9px;border-radius:20px}.lb .row .av{--d:40px}.lb .row .rk{width:28px;height:28px;font-size:13px}.lb .rowbtn .sc{font-size:15px;padding:5px 11px 5px 7px}.lb .own .d{display:none}.lb .own{padding:12px 14px}.lb .tab{padding:6px 11px}.lb .dscore{font-size:28px}.lb .foot{border-radius:20px}}',
    '@media (prefers-reduced-motion:reduce){.lb *{animation:none!important;transition:none!important}}'
  ].join('');
  var style = el('style'); style.textContent = css; document.head.appendChild(style);

  var stage = $('.stage');
  var panel = el('section', 'lb' + (motion ? ' fx' : '')); panel.setAttribute('aria-label', 'Leaderboard');
  var head = el('header');
  var title = el('h2', null, '🏆 Leaderboard'); title.appendChild(el('small', null, 'top runners'));
  var tools = el('div', 'tools');
  var tabs = el('div', 'tabs'); tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', 'Time range');
  var TABS = [['all', 'All time'], ['week', 'This week'], ['day', 'Today']];
  var tabBtns = TABS.map(function (t) {
    var b = el('button', 'tab', t[1]); b.type = 'button'; b.setAttribute('role', 'tab'); b.dataset.view = t[0]; tabs.appendChild(b); return b;
  });
  var refreshBtn = el('button', 'ghost icon', '↻ Refresh'); refreshBtn.type = 'button';
  tools.appendChild(tabs); tools.appendChild(refreshBtn);
  head.appendChild(title); head.appendChild(tools);
  var ownerBox = el('div', 'own'); ownerBox.hidden = true;
  var body = el('div', 'lbbody');
  var detail = el('div', 'detail'); detail.hidden = true;
  var status = el('p', 'msg'); status.setAttribute('aria-live', 'polite');
  var foot = el('div', 'foot'); var who = el('span', 'who'); var upd = el('span', 'upd'); foot.appendChild(who); foot.appendChild(upd);
  panel.appendChild(head); panel.appendChild(ownerBox); panel.appendChild(body); panel.appendChild(status); panel.appendChild(detail); panel.appendChild(foot);
  var after = $('.hint');
  if (after && after.parentNode) after.parentNode.insertBefore(panel, after); else document.body.appendChild(panel);

  var ov = el('div', 'sub-ov'); ov.hidden = true;
  ov.setAttribute('role', 'dialog'); ov.setAttribute('aria-modal', 'true'); ov.setAttribute('aria-labelledby', 'subTitle');
  var card = el('div', 'sub-card');
  var h3 = el('h3'); h3.id = 'subTitle';
  var sTxt = document.createTextNode('NEW TOP SCORE · '); var sNum = el('b', null, '0'); h3.appendChild(sTxt); h3.appendChild(sNum);
  var hint = el('p', null, 'Add your name to the public leaderboard');
  var input = el('input'); input.type = 'text'; input.maxLength = MAX_NAME; input.autocomplete = 'nickname';
  input.spellcheck = false; input.placeholder = 'YOUR NAME'; input.setAttribute('aria-label', 'Your name for the leaderboard');
  var subMsg = el('p', 'msg'); subMsg.setAttribute('aria-live', 'assertive');
  var row = el('div', 'row');
  var submitBtn = el('button', null, 'Submit score'); submitBtn.type = 'button';
  var skipBtn = el('button', 'ghost', 'Skip'); skipBtn.type = 'button';
  row.appendChild(submitBtn); row.appendChild(skipBtn);
  var fine = el('p', null, 'Scores are public — use a nickname.'); fine.style.margin = '10px 0 0'; fine.style.fontSize = '11px';
  card.appendChild(h3); card.appendChild(hint); card.appendChild(input); card.appendChild(subMsg); card.appendChild(row); card.appendChild(fine);
  ov.appendChild(card);
  if (stage) stage.appendChild(ov);

  var sticky = false;   // a success message stays until the next run starts
  function setStatus(text, kind, keep, lead) {
    status.textContent = '';
    if (text && lead) { status.appendChild(el('b', null, lead)); status.appendChild(document.createTextNode(' ')); }
    status.appendChild(document.createTextNode(text || ''));
    status.className = 'msg' + (kind ? ' ' + kind : ''); sticky = !!keep; }

  /* ---- small formatters ---- */
  function ago(t) {
    if (!t) return '';
    var s = Math.max(0, (Date.now() - t) / 1000);
    if (s < 60) return 'just now';
    if (s < 3600) return Math.floor(s / 60) + ' min ago';
    if (s < 86400) return Math.floor(s / 3600) + ' h ago';
    var d = Math.floor(s / 86400); return d + (d === 1 ? ' day ago' : ' days ago');
  }
  function runTime(ms) { var s = Math.round(ms / 1000); return Math.floor(s / 60) + ':' + ('0' + (s % 60)).slice(-2); }
  function isMine(id) { return mine.indexOf(id) !== -1; }

  function countUp(node, to) {
    if (!motion || to < 2) { node.textContent = pad5(to); return; }
    var t0 = performance.now(), dur = 650;
    (function step(now) {
      var k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      node.textContent = pad5(Math.round(to * e));
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }

  /* what the current tab shows: best entry per name inside the time window */
  function windowed() {
    var now = Date.now(), cut = view === 'day' ? now - 864e5 : view === 'week' ? now - 6048e5 : 0;
    var names = {}, out = [];
    allRows.forEach(function (r) {
      if (r.t < cut) return;
      var k = r.name.toLowerCase(); if (names[k]) return; names[k] = 1; out.push(r);
    });
    return out.slice(0, TOP);
  }

  function nameCell(e) {
    var nm = el('span', 'nm', e.name);
    if (e.mine) nm.appendChild(el('em', null, 'YOU'));
    return nm;
  }

  function selectEntry(rows, id) {
    selected = (selected === id) ? null : id;
    Array.prototype.forEach.call(body.querySelectorAll('[data-id]'), function (n) { n.classList.toggle('sel', n.dataset.id === selected); });
    var e = rows.filter(function (r) { return r.id === selected; })[0];
    if (!e) { detail.hidden = true; return; }
    detail.textContent = ''; detail.className = 'detail' + (e.mine ? ' mine' : '');
    var rank = rows.indexOf(e);
    var head = el('div', 'dhead');
    head.appendChild(el('span', 'dbadge', rank > -1 && rank < 3 ? ['🥇', '🥈', '🥉'][rank] : '#' + (rank + 1)));
    var who = el('div', 'dwho'), nm = el('span', 'dname', e.name);
    if (e.mine) nm.appendChild(el('em', null, 'YOU'));
    var bits = [];
    if (e.ms) bits.push('ran for ' + runTime(e.ms));
    if (e.t) bits.push(ago(e.t));
    who.appendChild(nm); who.appendChild(el('span', 'dsub', bits.join(' · ')));
    head.appendChild(who);
    var sc = el('span', 'dscore', pad5(e.score)); sc.appendChild(el('small', null, 'POINTS')); head.appendChild(sc);
    detail.appendChild(head);
    if (owner) {
      var pct = Math.round(e.score / owner.score * 100), wd = Math.min(100, Math.max(2, pct));
      var prog = el('div', 'dprog'), cap = el('p'), tr = el('div', 'track'), fl = el('span', 'fill');
      cap.appendChild(el('span', null, pct + '% of ' + owner.name + "'s best")); cap.appendChild(el('span', null, '👑 ' + pad5(owner.score)));
      tr.appendChild(fl); prog.appendChild(cap); prog.appendChild(tr); detail.appendChild(prog);
      if (motion) requestAnimationFrame(function () { requestAnimationFrame(function () { fl.style.width = wd + '%'; }); }); else fl.style.width = wd + '%';
    }
    if (e.mine) {
      var acts = el('div', 'dacts');
      var sh = el('button', 'ghost', '↗ Share'); sh.type = 'button';
      sh.addEventListener('click', function () { share(e); });
      acts.appendChild(sh);
      detail.appendChild(acts);
    }
    detail.hidden = false;
  }

  /* ---- generated avatars: a pixel dino head on a per-player colour, plus laurel wreaths for the podium ---- */
  var SVGNS = 'http://www.w3.org/2000/svg';
  function svg(tag, attrs, parent) { var n = document.createElementNS(SVGNS, tag); for (var k in attrs) n.setAttribute(k, attrs[k]); if (parent) parent.appendChild(n); return n; }
  var HEAD = ['..LLLLLLLL..', '.LYYYYYYYYY.', '.YYYYYYYYKYY', '.YYWKYYYYYYY', '.YYKKYYYYYYY', '.YYYYYYYYYYY', '.YYYYYYYYYYD', '.YYYYYYKKKKK', '.DYYYYYYYYD.', '..DDYYYYYD..', '...DDDDDD...'];
  var HEAD_COL = { Y: '#FFF1D0', L: '#FFFFFF', W: '#FFFFFF', K: '#1b1b1b', D: '#E3C98F' };
  function hueOf(str) { var h = 7; for (var i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) >>> 0; return h % 360; }
  function avatar(e) {
    var key = e.mine ? myUid : (e.u || e.name.toLowerCase()), h = hueOf(key);
    var a = el('span', 'av'); a.style.background = 'linear-gradient(145deg,hsl(' + h + ',72%,62%),hsl(' + ((h + 40) % 360) + ',70%,40%))';
    var s = svg('svg', { viewBox: '-2.5 -2.5 17 17', 'aria-hidden': 'true' });
    HEAD.forEach(function (row, y) {
      for (var x = 0; x < row.length; x++) {
        var c = row.charAt(x); if (c === '.') continue;
        var x2 = x; while (x2 + 1 < row.length && row.charAt(x2 + 1) === c) x2++;
        svg('rect', { x: x, y: y, width: x2 - x + 1, height: 1, fill: HEAD_COL[c] }, s); x = x2;
      }
    });
    a.appendChild(s); return a;
  }
  function wreath() {
    var s = svg('svg', { viewBox: '-60 -60 120 120', 'class': 'wr', 'aria-hidden': 'true' });
    [-1, 1].forEach(function (side) {
      for (var i = 0; i < 8; i++) {
        var t = (24 + i * 17) * Math.PI / 180, R = 50;
        var x = side * R * Math.sin(t), y = R * Math.cos(t);
        var tan = Math.atan2(-R * Math.sin(t), side * R * Math.cos(t)) * 180 / Math.PI;
        var k = 1 - i * 0.045;
        svg('ellipse', { cx: x.toFixed(1), cy: y.toFixed(1), rx: (7.5 * k).toFixed(1), ry: (3.2 * k).toFixed(1), fill: 'currentColor', opacity: (0.95 - i * 0.03).toFixed(2), transform: 'rotate(' + (tan + side * 28).toFixed(1) + ' ' + x.toFixed(1) + ' ' + y.toFixed(1) + ')' }, s);
      }
    });
    return s;
  }

  function podiumCard(e, i, rows, top) {
    var li = document.createElement('li');
    li.className = 'pod p' + (i + 1) + (e && e.mine ? ' me' : '') + (!e ? ' empty' : '');
    li.style.setProperty('--i', String(i === 0 ? 0 : i));
    var mw = el('span', 'mw'); mw.appendChild(wreath());
    if (e) {
      mw.appendChild(avatar(e)); mw.appendChild(el('span', 'rkd', String(i + 1)));
      li.appendChild(mw);
      li.dataset.id = e.id; li.tabIndex = 0; li.setAttribute('role', 'button');
      if (e.id === selected) li.classList.add('sel');
      if (seenInit && !seen[e.id]) li.classList.add('fresh');
      li.appendChild(nameCell(e));
      var sc = el('span', 'sc'); li.appendChild(sc); countUp(sc, e.score);
      li.addEventListener('click', function () { selectEntry(rows, e.id); });
      li.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); ev.stopPropagation(); selectEntry(rows, e.id); } });
    } else {
      mw.appendChild(el('span', 'av', '?')); li.appendChild(mw);
      li.setAttribute('aria-hidden', 'true'); li.setAttribute('role', 'presentation');
      li.appendChild(el('span', 'nm', 'open spot')); li.appendChild(el('span', 'sc', '—'));
    }
    li.appendChild(el('span', 'blk', String(i + 1)));
    return li;
  }

  function rowEntry(e, i, rows, top) {
    var li = el('li', 'row' + (e.mine ? ' me' : '')); li.dataset.id = e.id; li.style.setProperty('--i', String(i));
    if (e.id === selected) li.classList.add('sel');
    if (seenInit && !seen[e.id]) li.classList.add('fresh');
    var b = el('button', 'rowbtn'); b.type = 'button';
    b.appendChild(el('span', 'rk', String(i + 4)));
    b.appendChild(avatar(e));
    var info = el('span', 'info'); info.appendChild(nameCell(e));
    var bar = el('span', 'bar'), fill = el('i'); bar.appendChild(fill); info.appendChild(bar); b.appendChild(info);
    var sc = el('span', 'sc'); b.appendChild(sc); countUp(sc, e.score);
    var w = Math.max(4, Math.round(e.score / Math.max(1, top) * 100));
    if (motion) requestAnimationFrame(function () { requestAnimationFrame(function () { fill.style.width = w + '%'; }); }); else fill.style.width = w + '%';
    b.addEventListener('click', function () { selectEntry(rows, e.id); });
    li.appendChild(b);
    return li;
  }

  function render(force) {
    var rows = windowed();
    var top = rows.length ? rows[0].score : 0;
    var sig = [view, loading, loadOk, owner ? owner.score : '', rows.map(function (r) { return r.id + ':' + r.score + ':' + r.name + (r.mine ? '*' : ''); }).join(',')].join('|');
    TABS.forEach(function (t, i) { var on = t[0] === view; tabBtns[i].setAttribute('aria-selected', on ? 'true' : 'false'); tabBtns[i].tabIndex = on ? 0 : -1; });
    if (sig === lastSig && !force) return;
    lastSig = sig;

    /* creator card with the race to the crown */
    if (owner) {
      ownerBox.hidden = false; ownerBox.textContent = '';
      var orow = el('div', 'ownrow');
      orow.appendChild(el('span', null, '👑')); orow.appendChild(el('b', null, owner.name));
      orow.appendChild(el('span', 'd', "the creator's best — can you beat it?")); orow.appendChild(el('i', null, pad5(owner.score)));
      var all = allRows.length ? allRows[0].score : 0;
      var pct = Math.min(100, Math.round(all / owner.score * 100));
      var track = el('div', 'track'), fill = el('span', 'fill'); track.appendChild(fill);
      var label = !all ? 'Nobody has challenged the crown yet.' : all > owner.score ? '🔥 The crown has been taken — a visitor beat the creator!' : 'The best runner is ' + Math.max(1, pct) + '% of the way to the crown.';
      ownerBox.appendChild(orow); ownerBox.appendChild(track); ownerBox.appendChild(el('p', 'tl', label));
      if (motion) requestAnimationFrame(function () { requestAnimationFrame(function () { fill.style.width = (all ? Math.max(2, pct) : 0) + '%'; }); }); else fill.style.width = (all ? Math.max(2, pct) : 0) + '%';
    } else { ownerBox.hidden = true; }

    body.textContent = '';
    if (loading) {
      var sk = el('div', 'skel'); sk.setAttribute('aria-hidden', 'true'); for (var k = 0; k < 4; k++) sk.appendChild(el('i')); body.appendChild(sk);
    } else if (!rows.length) {
      if (loadOk) {
        var es = el('div', 'empty-state');
        es.appendChild(el('span', 'big', '🦖'));
        es.appendChild(el('b', null, view === 'all' ? 'No scores yet' : view === 'week' ? 'No scores this week yet' : 'No scores today yet'));
        es.appendChild(document.createTextNode(view === 'all' ? 'Be the first name on the board.' : 'Be the first of the ' + (view === 'week' ? 'week' : 'day') + '.'));
        var go = el('button', null, '▶ Play now'); go.type = 'button';
        go.addEventListener('click', function () { var c = $('#game'); if (c) { c.scrollIntoView({ behavior: motion ? 'smooth' : 'auto', block: 'center' }); c.focus({ preventScroll: true }); } });
        es.appendChild(el('br')); es.appendChild(go); body.appendChild(es);
      }
    } else {
      var pod = el('ol', 'podium'); pod.setAttribute('aria-label', 'Top three');
      for (var i = 0; i < 3; i++) pod.appendChild(podiumCard(rows[i], i, rows, top));
      body.appendChild(pod);
      if (rows.length > 3) {
        var rest = el('ol', 'rest'); rest.setAttribute('start', '4');
        rows.slice(3).forEach(function (e, j) { rest.appendChild(rowEntry(e, j, rows, top)); });
        body.appendChild(rest);
      }
    }
    rows.forEach(function (r) { seen[r.id] = 1; });
    if (!loading && loadOk) seenInit = true;
    if (selected && !rows.some(function (r) { return r.id === selected; })) { selected = null; detail.hidden = true; }
    else if (selected) { var keep = selected; selected = null; selectEntry(rows, keep); }
    tick();
  }

  function tick() { upd.textContent = loadedAt ? 'Updated ' + (ago(loadedAt) === 'just now' ? 'just now' : ago(loadedAt)) : ''; }
  setInterval(tick, 10000);

  /* tabs */
  tabBtns.forEach(function (b, i) {
    b.addEventListener('click', function () { view = b.dataset.view; store('dinoLbView', view); selected = null; detail.hidden = true; render(true); });
    b.addEventListener('keydown', function (e) {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault(); var n = tabBtns[(i + (e.key === 'ArrowRight' ? 1 : tabBtns.length - 1)) % tabBtns.length]; n.focus(); n.click();
    });
  });

  /* share your own entry */
  function share(e) {
    var text = 'I scored ' + e.score + " on Rahul's dino game — can you beat me?";
    var url = location.href.split('#')[0];
    if (navigator.share) { navigator.share({ title: 'Dino Run', text: text, url: url }).catch(noop); return; }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text + ' ' + url).then(function () { setStatus('Copied to your clipboard — go brag!', 'ok', true); }, noop);
  }

  /* confetti for a #1 or for beating the creator */
  function burst() {
    if (!motion) return;
    var cv = document.createElement('canvas'); cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:60';
    cv.width = window.innerWidth; cv.height = window.innerHeight; document.body.appendChild(cv);
    var g = cv.getContext('2d');
    var accent = (getComputedStyle(document.documentElement).getPropertyValue('--accent') || '#ffffff').trim();
    var colors = [accent, '#ffffff', '#f5c542', '#7ee787', '#ff8fb1'], ps = [];
    for (var i = 0; i < 110; i++) ps.push({ x: cv.width / 2 + (Math.random() - .5) * 160, y: cv.height * .5, vx: (Math.random() - .5) * 13, vy: -(5 + Math.random() * 10), r: 3 + Math.random() * 4, c: colors[i % colors.length], a: Math.random() * 6, va: (Math.random() - .5) * .35 });
    var t0 = 0;
    requestAnimationFrame(function frame(now) {
      if (!t0) t0 = now; var k = (now - t0) / 2000;
      g.clearRect(0, 0, cv.width, cv.height);
      ps.forEach(function (p) { p.vy += .25; p.x += p.vx; p.y += p.vy; p.a += p.va; g.save(); g.translate(p.x, p.y); g.rotate(p.a); g.globalAlpha = Math.max(0, 1 - k); g.fillStyle = p.c; g.fillRect(-p.r, -p.r / 2, p.r * 2, p.r); g.restore(); });
      if (k < 1) requestAnimationFrame(frame); else cv.remove();
    });
  }

  /* ---------- data ---------- */
  function loadBoard() {
    refreshBtn.classList.add('spin');
    return request('/scores.json?orderBy=%22score%22&limitToLast=' + FETCH).then(function (data) {
      var rows = [];
      Object.keys(data || {}).forEach(function (id) {
        var v = data[id];
        if (v && typeof v.name === 'string' && typeof v.score === 'number') {
          var u = typeof v.u === 'string' ? v.u : '';
          rows.push({ id: id, name: v.name, score: v.score, ms: typeof v.ms === 'number' ? v.ms : 0, t: v.t || 0, u: u, mine: (u !== '' && u === myUid) || isMine(id) });
        }
      });
      // One row per player. Entries share a player when they carry the same anonymous id; this
      // browser's older entries (from before ids existed) are folded into its own id.
      var groups = {};
      rows.forEach(function (r) { var k = r.mine ? myUid : (r.u || 'id:' + r.id); (groups[k] = groups[k] || []).push(r); });
      var reps = Object.keys(groups).map(function (k) {
        var g = groups[k], max = Math.max.apply(null, g.map(function (r) { return r.score; }));
        var tops = g.filter(function (r) { return r.score === max; }).sort(function (x, y) { return x.t - y.t; });
        var first = tops[0], last = tops[tops.length - 1];
        // the name comes from the newest entry at the best score (so a rename wins), the time from the first
        // (so renaming an old best does not make it look new)
        return { id: last.id, name: last.name, score: max, ms: last.ms, t: first.t, u: last.u, mine: g.some(function (r) { return r.mine; }) };
      });
      reps.sort(function (x, y) { return y.score - x.score || x.t - y.t; });
      var mineTop = reps.filter(function (r) { return r.mine; })[0];
      if (mineTop && mineTop.score > myBest) { myBest = mineTop.score; store('dinoLbBest', String(myBest)); }
      allRows = reps;
      var names = {}, best = [];
      allRows.forEach(function (r) { var k = r.name.toLowerCase(); if (!names[k]) { names[k] = 1; best.push(r); } });
      board = best.slice(0, TOP);
      loadOk = true; loading = false; loadedAt = Date.now();
      render();
      if (!sticky) setStatus('');
      return board;
    }).catch(function () {
      loadOk = false; loading = false;
      render(true);
      if (!sticky) setStatus("Couldn't reach the leaderboard right now. Your run still counts locally.", 'err');
      return board;
    }).then(function (b) { refreshBtn.classList.remove('spin'); return b; });
  }

  function loadOwner() {
    return request('/owner.json').then(function (o) {
      var n = normaliseOwner(o); if (n) owner = n; render(true);
    }).catch(noop);
  }

  function qualifies(score) { return board.length < TOP || score > board[board.length - 1].score; }

  /* ---------- submitting scores and renaming ---------- */
  var mode = 'score';          // what the prompt is for right now: 'score' | 'rename'

  function savedName() { return cleanName(recall('dinoLbName') || ''); }
  function myEntry() { for (var i = 0; i < allRows.length; i++) if (allRows[i].mine) return allRows[i]; return null; }
  function nameTaken(name) {   // is this name already used by somebody else on the board?
    var k = name.toLowerCase();
    return allRows.some(function (r) { return !r.mine && r.name.toLowerCase() === k; });
  }
  function failText(err) { return err && err.status === 401 ? 'The leaderboard rejected that.' : "Couldn't save — check your connection and try again."; }

  function showWho() {
    who.textContent = '';
    var n = savedName(); if (!n) return;
    who.appendChild(el('span', 'av', n.charAt(0)));
    var pn = el('span', 'pn'); pn.appendChild(el('small', null, 'Playing as')); pn.appendChild(el('b', null, n)); who.appendChild(pn);
    var b = el('button', 'linklike', '✎ Edit name'); b.type = 'button';
    b.addEventListener('click', function () { openPrompt('rename'); });
    who.appendChild(b);
  }

  /* POST an entry. It carries this browser's anonymous id; if the database rules predate ids and reject it,
     retry once without it so scoring keeps working. */
  function post(name, score, ms) {
    function send(withId) {
      var body = { name: name, score: score, ms: ms, t: { '.sv': 'timestamp' } };
      if (withId) body.u = myUid;
      return request('/scores.json', { method: 'POST', body: JSON.stringify(body) });
    }
    if (legacy) return send(false);
    return send(true).catch(function (err) {
      if (!err || err.status !== 401) throw err;
      return send(false).then(function (res) { legacy = true; return res; });
    });
  }

  function remember(res, name, score) {
    if (res && res.name) { mine.push(res.name); store('dinoLbMine', JSON.stringify(mine.slice(-40))); }
    store('dinoLbName', name);
    myBest = Math.max(myBest, score); store('dinoLbBest', String(myBest));
    showWho();
  }

  function afterSave(score, message, lead) {
    return loadBoard().then(function () {
      var rank = -1;
      board.forEach(function (e, i) { if (e.mine) rank = i + 1; });
      selected = null;
      var me = windowed().filter(function (r) { return r.mine; })[0];
      if (me) selectEntry(windowed(), me.id);
      setStatus(message(rank), 'ok', true, lead);
      if (score && (rank === 1 || (owner && score > owner.score))) burst();
      panel.scrollIntoView({ behavior: motion ? 'smooth' : 'auto', block: 'nearest' });
    });
  }

  function openPrompt(m) {
    if (m === 'score' && (!run || run.submitted)) return;
    mode = m; subMsg.textContent = ''; submitBtn.disabled = false;
    var me = myEntry();
    input.value = savedName() || (me ? cleanName(me.name) : '');
    if (m === 'rename') {
      sTxt.nodeValue = 'EDIT YOUR NAME'; sNum.textContent = '';
      hint.textContent = me ? 'Your best of ' + pad5(me.score) + ' will show under the new name' : 'This name will be used for your next score';
      submitBtn.textContent = 'Save name';
    } else {
      sTxt.nodeValue = 'NEW TOP SCORE · '; sNum.textContent = pad5(run.score);
      hint.textContent = 'Add your name to the public leaderboard';
      submitBtn.textContent = 'Submit score';
    }
    ov.hidden = false;
    setTimeout(function () { input.focus(); input.select(); }, 30);
  }
  function closeSubmit() { ov.hidden = true; var c = $('#game'); if (c) c.focus({ preventScroll: true }); }

  /* a returning player's new personal best is saved straight away under their saved name */
  function autoSave(r, name) {
    busy = true; lastSubmitAt = Date.now(); setStatus('Saving your new best…');
    post(name, r.score, r.ms).then(function (res) {
      r.submitted = true; remember(res, name, r.score);
      return afterSave(r.score, function (rank) { return pad5(r.score) + ' saved as ' + name + (rank > 0 ? ' — you are #' + rank + '.' : '.'); }, 'New personal best!');
    }).catch(function (err) {
      setStatus(''); openPrompt('score'); subMsg.textContent = failText(err);
    }).then(function () { busy = false; });
  }

  function rename(name) {
    var me = myEntry(), current = savedName() || (me ? me.name : '');
    if (name === current) { closeSubmit(); return; }
    if (!me) {   // nothing on the board yet: just remember the name for the next score
      store('dinoLbName', name); showWho(); closeSubmit();
      setStatus('Saved — "' + name + '" will be used for your next score.', 'ok', true); return;
    }
    busy = true; submitBtn.disabled = true; subMsg.textContent = ''; lastSubmitAt = Date.now();
    post(name, me.score, Math.max(1000, me.ms)).then(function (res) {
      remember(res, name, me.score); closeSubmit();
      return afterSave(0, function () {
        return 'Name updated to ' + name + '.' + (legacy ? ' (Other visitors may still see your old name until the database rules are updated — see leaderboard/README.md.)' : '');
      });
    }).catch(function (err) { submitBtn.disabled = false; subMsg.textContent = failText(err); })
      .then(function () { busy = false; });
  }

  function submit() {
    if (busy) return;
    var name = cleanName(input.value);
    var problem = nameProblem(name) || (nameTaken(name) ? 'That name is already on the board — pick another.' : '');
    if (problem) { subMsg.textContent = problem; return; }
    if (Date.now() - lastSubmitAt < 2000) { subMsg.textContent = 'One moment…'; return; }
    if (mode === 'rename') { rename(name); return; }
    if (!run || run.submitted) return;
    busy = true; submitBtn.disabled = true; subMsg.textContent = ''; lastSubmitAt = Date.now();
    var r = run;
    post(name, r.score, r.ms).then(function (res) {
      r.submitted = true; remember(res, name, r.score); closeSubmit();
      return afterSave(r.score, function (rank) { return rank > 0 ? 'Submitted — you are #' + rank + '! Press Space to play again.' : 'Submitted! Press Space to play again.'; });
    }).catch(function (err) { submitBtn.disabled = false; subMsg.textContent = failText(err); })
      .then(function () { busy = false; });
  }

  submitBtn.addEventListener('click', submit);
  skipBtn.addEventListener('click', closeSubmit);
  input.addEventListener('keydown', function (e) {
    e.stopPropagation();
    if (e.key === 'Enter') { e.preventDefault(); submit(); }
    else if (e.key === 'Escape') { e.preventDefault(); closeSubmit(); }
  });
  input.addEventListener('keyup', function (e) { e.stopPropagation(); });
  refreshBtn.addEventListener('click', function () { setStatus('Refreshing…'); loadBoard(); loadOwner(); });

  /* ---------- game hooks ---------- */
  window.DinoLB = {
    enabled: true,
    runStarted: function () { run = null; if (!ov.hidden) ov.hidden = true; if (sticky) setStatus(''); },
    runEnded: function (score, ms) {
      run = { score: score, ms: Math.max(1000, Math.round(ms)), id: ++runCounter, submitted: false };
      var mineRun = run;
      if (owner && score > owner.score) setStatus("👑 You beat the creator's best!", 'ok', true);
      if (score < MIN_SCORE) return;
      loadBoard().then(function () {
        if (run !== mineRun || mineRun.submitted) return;
        if (mineRun.score <= myBest) { setStatus('Not a new personal best — yours on the board is ' + pad5(myBest) + '.', null, true); return; }
        if (!loadOk || !qualifies(mineRun.score)) return;
        var name = savedName();
        if (name && !nameProblem(name) && !nameTaken(name)) { autoSave(mineRun, name); return; }
        openPrompt('score');
        if (name) subMsg.textContent = nameProblem(name) || '"' + name + '" is already on the board — pick another name.';
      });
    }
  };

  showWho();
  loadBoard(); loadOwner();
  setInterval(function () { if (!document.hidden && ov.hidden) loadBoard(); }, POLL_MS);
})();
