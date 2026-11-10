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
    '@font-face{font-family:"Baloo 2";font-style:normal;font-weight:400 800;font-display:swap;src:url(fonts/baloo-2-latin-wght-normal.woff2) format("woff2")}',
    '.stage{position:relative}',
    '.lb{--gold:#FFC83D;--silver:#C9D6E2;--bronze:#F2A66B;--sun:#FFC83D;--tint:rgba(var(--accent-rgb),.38);--hs:4px 5px 0 var(--ink);position:relative;width:min(100%,940px);padding:22px;border-radius:30px;background:var(--paper);border:3px solid var(--ink);box-shadow:8px 10px 0 var(--ink);color:var(--ink);font-family:var(--body);font-weight:700}',
    '.lb button{font-family:var(--display);font-size:17px;font-weight:700;color:var(--ink);background:var(--accent);border:3px solid var(--ink);border-radius:14px;padding:8px 18px;min-height:0;box-shadow:3px 4px 0 var(--ink);cursor:pointer;transition:transform .12s,box-shadow .12s}',
    '.lb button:hover{transform:translate(-1px,-1px);box-shadow:4px 5px 0 var(--ink)}',
    '.lb button:active{transform:translate(2px,3px);box-shadow:1px 1px 0 var(--ink)}',
    '.lb button.ghost{background:#fff}',
    '.lb header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:18px}',
    '.lb h2{margin:0;display:flex;align-items:center;gap:12px;font-family:var(--display);font-size:34px;font-weight:800;line-height:1;color:var(--ink)}',
    '.lb h2 small{padding:4px 12px;border:2.5px solid var(--ink);border-radius:99px;background:var(--sun);font-family:var(--body);font-size:13px;font-weight:800;letter-spacing:.02em}',
    '.lb .tools{display:flex;align-items:center;gap:12px;flex-wrap:wrap}',
    '.lb .tabs{display:inline-flex;gap:4px;padding:4px;border:3px solid var(--ink);border-radius:99px;background:var(--sand)}',
    '.lb .tab{padding:5px 16px;font-size:16px;border:3px solid transparent;border-radius:99px;background:transparent;color:rgba(43,26,18,.7);box-shadow:none}',
    '.lb .tab:hover{color:var(--ink);transform:none;box-shadow:none}',
    '.lb .tab[aria-selected=true]{background:var(--accent);color:var(--ink);border-color:var(--ink);box-shadow:2px 3px 0 var(--ink)}',
    '.lb .icon{padding:6px 16px;white-space:nowrap}',
    '.lb .icon.spin::first-letter{display:inline-block;animation:lbspin .8s linear infinite}',
    '.lb ol{list-style:none;margin:0;padding:0}',
    '.lb .own{margin-bottom:20px;padding:14px 18px 16px;border:3px solid var(--ink);border-radius:22px;background:var(--sun);box-shadow:var(--hs)}',
    '.lb .ownrow{display:flex;align-items:center;gap:12px}',
    '.lb .ownrow>span:first-child{flex:none;width:40px;height:40px;display:grid;place-items:center;border:3px solid var(--ink);border-radius:50%;background:#fff;font-size:20px}',
    '.lb .own b{font-family:var(--display);font-size:24px;font-weight:800;color:var(--ink)}',
    '.lb .own .d{flex:1;font-size:14px;font-weight:700;color:rgba(43,26,18,.8)}',
    '.lb .own i{font-style:normal;padding:2px 14px;border:3px solid var(--ink);border-radius:99px;background:#fff;font-family:var(--display);font-size:24px;font-weight:800;color:var(--ink)}',
    '.lb .track{position:relative;height:20px;margin-top:12px;border:3px solid var(--ink);border-radius:99px;background:#fff;overflow:hidden}',
    '.lb .track .fill{display:block;height:100%;width:0;border-radius:99px;background:repeating-linear-gradient(135deg,var(--accent) 0 10px,rgba(255,255,255,.55) 10px 20px);background-color:var(--accent);box-shadow:inset 0 -4px 0 rgba(43,26,18,.12);transition:width 1s cubic-bezier(.2,.8,.2,1)}',
    '.lb .tl{margin:9px 2px 0;font-size:14px;font-weight:800;color:rgba(43,26,18,.85)}',
    '.lb .podium{display:flex;align-items:flex-end;justify-content:center;gap:12px;margin:6px 0 0;padding:10px 6px 0;border-radius:22px 22px 0 0;background:radial-gradient(rgba(43,26,18,.1) 1.4px,transparent 1.6px) 0 0/16px 16px,var(--sky);border:3px solid var(--ink);border-bottom:0}',
    '.lb .pod{--d:68px;flex:1 1 0;max-width:236px;min-width:0;display:flex;flex-direction:column;align-items:center;text-align:center;cursor:pointer;outline:none}',
    '.lb .pod.p1{order:2;--d:92px;--m:var(--gold)}.lb .pod.p2{order:1;--m:var(--silver)}.lb .pod.p3{order:3;--m:var(--bronze)}',
    '.lb .pod.empty{cursor:default}',
    '.lb .mw{position:relative;width:calc(var(--d) + 50px);height:calc(var(--d) + 46px);display:grid;place-items:center;transition:transform .2s}',
    '.lb .pod:hover .mw,.lb .pod:focus-visible .mw{transform:translateY(-5px)}.lb .pod.empty:hover .mw{transform:none}',
    '.lb .wr{position:absolute;inset:0;width:100%;height:100%;color:var(--m);overflow:visible}',
    '.lb .wr ellipse{stroke:var(--ink);stroke-width:2.2}',
    '.lb .av{position:relative;width:var(--d);height:var(--d);flex:none;border-radius:50%;overflow:hidden;display:block}',
    '.lb .av svg{display:block;width:100%;height:100%;shape-rendering:crispEdges}',
    '.lb .pod .av{border:3px solid var(--ink);box-shadow:0 0 0 5px var(--m),0 0 0 8px var(--ink),0 6px 0 8px var(--ink)}',
    '.lb .pod .rkd{position:absolute;left:50%;bottom:2px;transform:translateX(-50%);min-width:30px;height:30px;padding:0 6px;border:3px solid var(--ink);border-radius:99px;display:grid;place-items:center;background:var(--m);font-family:var(--display);font-size:17px;font-weight:800;color:var(--ink);box-shadow:2px 3px 0 var(--ink)}',
    '.lb .pod.empty .av{background:rgba(255,255,255,.55);border:3px dashed rgba(43,26,18,.5);box-shadow:none;display:grid;place-items:center;font-family:var(--display);font-size:32px;color:rgba(43,26,18,.5)}',
    '.lb .pod.empty .wr,.lb .pod.empty .rkd{display:none}',
    '.lb .pod .nm{max-width:100%;margin-top:4px;font-family:var(--display);font-size:20px;font-weight:800;line-height:1.1;color:var(--ink)}',
    '.lb .sc{display:inline-flex;align-items:center;gap:7px;font-family:var(--display);font-weight:800;letter-spacing:.02em;color:var(--ink);font-variant-numeric:tabular-nums}',
    '.lb .sc::before{content:"";flex:none;width:18px;height:18px;border:2.5px solid var(--ink);border-radius:50%;background:radial-gradient(circle at 50% 50%,transparent 0 4px,var(--gold) 4.5px)}',
    '.lb .pod .sc{margin:7px 0 12px;padding:2px 14px 2px 9px;border:3px solid var(--ink);border-radius:99px;background:#fff;box-shadow:2px 3px 0 var(--ink);font-size:20px}',
    '.lb .pod.empty .sc{background:none;border-color:transparent;box-shadow:none;color:rgba(43,26,18,.5)}.lb .pod.empty .sc::before{display:none}',
    '.lb .pod .blk{width:100%;display:flex;align-items:flex-start;justify-content:center;padding-top:2px;border:3px solid var(--ink);border-bottom:0;border-radius:16px 16px 0 0;background:linear-gradient(180deg,rgba(255,255,255,.4) 0 12px,transparent 12px),var(--m);box-shadow:inset 0 -3px 0 rgba(43,26,18,.12);font-family:var(--display);font-weight:900;font-size:56px;line-height:1.05;color:#fff;-webkit-text-stroke:3px var(--ink);paint-order:stroke fill;transition:filter .2s}',
    '.lb .pod:hover .blk,.lb .pod:focus-visible .blk{filter:brightness(1.07)}',
    '.lb .p1 .blk{height:104px}.lb .p2 .blk{height:78px}.lb .p3 .blk{height:58px}',
    '.lb .pod.empty .blk{background:repeating-linear-gradient(135deg,rgba(43,26,18,.06) 0 8px,transparent 8px 16px),var(--sand);border-style:dashed;color:rgba(43,26,18,.3);-webkit-text-stroke:0}',
    '.lb .pod.me .nm{padding:0 12px;border:3px solid var(--ink);border-radius:99px;background:var(--accent);box-shadow:2px 3px 0 var(--ink)}',
    '.lb .pod.me .av{box-shadow:0 0 0 5px var(--accent),0 0 0 8px var(--ink),0 6px 0 8px var(--ink)}',
    '.lb .pod.sel .av{box-shadow:0 0 0 5px #fff,0 0 0 8px var(--ink),0 6px 0 8px var(--ink)}',
    '.lb .rest{display:grid;gap:12px;margin:0;padding:16px 12px 14px;border:3px solid var(--ink);border-radius:0 0 22px 22px;background:var(--sand)}',
    '.lb .row{--d:46px}',
    '.lb .rowbtn{width:100%;display:grid;grid-template-columns:36px 46px minmax(0,1fr) auto;align-items:center;gap:14px;padding:9px 14px 9px 10px;border:3px solid var(--ink);border-radius:18px;background:#fff;text-align:left;font-family:var(--body);font-size:16px;font-weight:800;color:var(--ink);box-shadow:3px 4px 0 var(--ink);cursor:pointer;transition:transform .12s,box-shadow .12s}',
    '.lb .rowbtn:hover{transform:translate(-1px,-2px);box-shadow:4px 6px 0 var(--ink)}',
    '.lb .rowbtn:focus-visible{outline:3px solid var(--ink);outline-offset:3px}',
    '.lb .row.me .rowbtn{background:linear-gradient(var(--tint),var(--tint)),#fff}',
    '.lb .row.sel .rowbtn{transform:translate(2px,3px);box-shadow:1px 1px 0 var(--ink)}',
    '.lb .row .rk{width:34px;height:34px;display:grid;place-items:center;border:3px solid var(--ink);border-radius:50%;background:var(--sand);font-family:var(--display);font-size:18px;font-weight:800}',
    '.lb .row .av{--d:46px;border:3px solid var(--ink)}',
    '.lb .info{display:grid;gap:6px;min-width:0}',
    '.lb .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
    '.lb .row .nm{font-family:var(--display);font-size:21px;font-weight:700;line-height:1.1}',
    '.lb .nm em{font-style:normal;margin-left:9px;padding:1px 9px;border:2.5px solid var(--ink);border-radius:99px;background:var(--accent);font-family:var(--display);font-size:13px;font-weight:800;letter-spacing:.06em;vertical-align:3px}',
    '.lb .bar{display:block;height:11px;max-width:280px;border:2.5px solid var(--ink);border-radius:99px;background:#fff;overflow:hidden}',
    '.lb .bar i{display:block;height:100%;width:0;background:repeating-linear-gradient(135deg,var(--accent) 0 8px,rgba(255,255,255,.55) 8px 16px);background-color:var(--accent);transition:width .8s cubic-bezier(.2,.8,.2,1)}',
    '.lb .rowbtn .sc{padding:2px 14px 2px 9px;border:3px solid var(--ink);border-radius:99px;background:var(--sun);font-size:20px}',
    '.lb .detail{margin-top:20px;padding:16px 18px;border:3px solid var(--ink);border-radius:22px;display:grid;gap:14px;background:var(--paper);box-shadow:var(--hs)}',
    '.lb .detail.mine{background:linear-gradient(var(--tint),var(--tint)),#fff}',
    '.lb .detail[hidden]{display:none}',
    '.lb .dhead{display:flex;align-items:center;gap:14px}',
    '.lb .dbadge{flex:none;width:54px;height:54px;display:grid;place-items:center;border:3px solid var(--ink);border-radius:16px;background:#fff;font-family:var(--display);font-size:26px;font-weight:800;box-shadow:2px 3px 0 var(--ink)}',
    '.lb .dwho{flex:1;min-width:0;display:grid;gap:2px}',
    '.lb .dname{font-family:var(--display);font-size:26px;font-weight:800;line-height:1.1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
    '.lb .dname em{font-style:normal;margin-left:9px;padding:1px 9px;border:2.5px solid var(--ink);border-radius:99px;background:var(--accent);font-size:13px;font-weight:800;letter-spacing:.06em;vertical-align:4px}',
    '.lb .dsub{font-size:14px;font-weight:700;color:rgba(43,26,18,.7)}',
    '.lb .dscore{flex:none;text-align:right;font-family:var(--display);font-size:42px;font-weight:800;line-height:1;color:var(--ink)}',
    '.lb .dscore small{display:block;margin-top:4px;font-family:var(--body);font-size:12px;font-weight:800;letter-spacing:.14em;color:rgba(43,26,18,.65)}',
    '.lb .dprog{display:grid;gap:8px}',
    '.lb .dprog p{margin:0;display:flex;justify-content:space-between;gap:10px;font-size:14px;font-weight:800}',
    '.lb .dprog .track{margin:0;height:16px}',
    '.lb .dacts{display:flex;gap:10px;flex-wrap:wrap}',
    '.lb .empty-state{margin-top:4px;padding:26px 14px 24px;text-align:center;border:3px dashed var(--ink);border-radius:22px;background:var(--sand);font-size:16px;font-weight:700;color:rgba(43,26,18,.8)}',
    '.lb .empty-state .big{display:block;font-size:48px;margin-bottom:6px}.lb .empty-state b{display:block;margin-bottom:4px;font-family:var(--display);font-size:26px;font-weight:800;color:var(--ink)}',
    '.lb .empty-state button{margin-top:14px;padding:10px 26px;font-size:20px}',
    '.lb .skel{display:grid;gap:12px;margin:4px 0}.lb .skel i{display:block;height:62px;border:3px solid var(--ink);border-radius:18px;background:linear-gradient(90deg,var(--sand) 25%,#fff 50%,var(--sand) 75%);background-size:300% 100%;animation:lbshim 1.3s linear infinite}',
    '.lb .msg{margin:18px 0 0;padding:11px 16px;border:3px solid var(--ink);border-radius:18px;background:var(--sand);box-shadow:3px 4px 0 var(--ink);font-size:16px;font-weight:800;line-height:1.4;color:var(--ink)}',
    '.lb .msg:empty{display:none}.lb .msg b{font-family:var(--display);font-size:19px;font-weight:800}',
    '.lb .msg.ok{background:var(--mint)}.lb .msg.err{background:#FFC9BD}',
    '.lb .msg.ok::before,.lb .msg.err::before{display:inline-grid;place-items:center;width:24px;height:24px;margin-right:10px;border:2.5px solid var(--ink);border-radius:50%;background:#fff;font-size:13px;font-weight:900;vertical-align:1px}',
    '.lb .msg.ok::before{content:"\\2713"}.lb .msg.err::before{content:"!"}',
    '.lb .foot{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;margin-top:20px;padding:10px 16px 10px 12px;border:3px solid var(--ink);border-radius:18px;background:var(--sand);font-size:14px;font-weight:800}',
    '.lb .who{display:inline-flex;align-items:center;gap:11px}',
    '.lb .who .av{width:38px;height:38px;display:grid;place-items:center;border:3px solid var(--ink);border-radius:50%;background:var(--accent);font-family:var(--display);font-size:19px;font-weight:800;text-transform:uppercase}',
    '.lb .who .pn{display:grid;line-height:1.15}.lb .who .pn small{font-size:11px;font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:rgba(43,26,18,.65)}.lb .who .pn b{font-family:var(--display);font-size:20px;font-weight:800}',
    '.lb .linklike{padding:5px 14px;margin-left:4px;font-family:var(--body);font-size:13px;font-weight:800;background:#fff;box-shadow:2px 3px 0 var(--ink)}',
    '.lb .upd{display:inline-flex;align-items:center;gap:8px;color:rgba(43,26,18,.75)}.lb .upd:empty{display:none}.lb .upd::before{content:"";width:12px;height:12px;border:2.5px solid var(--ink);border-radius:50%;background:#5BD68A}',
    '@keyframes lbrise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}',
    '@keyframes lbgrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}',
    '@keyframes lbflash{0%{box-shadow:0 0 0 0 rgba(var(--accent-rgb),.9)}100%{box-shadow:0 0 0 16px rgba(var(--accent-rgb),0)}}',
    '@keyframes lbspin{to{transform:rotate(360deg)}}@keyframes lbshim{to{background-position:-300% 0}}@keyframes lbpulse{50%{opacity:.4}}',
    '.lb.fx .pod{animation:lbrise .55s cubic-bezier(.2,.9,.3,1.2) both;animation-delay:calc(var(--i,0)*90ms)}',
    '.lb.fx .pod .blk{transform-origin:bottom;animation:lbgrow .6s cubic-bezier(.2,.9,.3,1) both;animation-delay:calc(var(--i,0)*90ms + 80ms)}',
    '.lb.fx .row{animation:lbrise .45s ease both;animation-delay:calc(var(--i,0)*45ms + 250ms)}',
    '.lb.fx .msg:not(:empty),.lb.fx .detail:not([hidden]){animation:lbrise .4s cubic-bezier(.2,.9,.3,1.1) both}',
    '.lb.fx .upd::before{animation:lbpulse 2s ease-in-out infinite}',
    '.lb.fx .fresh .rowbtn,.lb.fx .pod.fresh .av{animation:lbflash 1.2s ease-out 2}',
    '.sub-ov{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:rgba(43,26,18,.62);z-index:50;padding:14px;overflow:auto;font-family:var(--body)}',
    '.sub-ov[hidden]{display:none}',
    '.sub-card{width:min(100%,400px);padding:18px 22px 16px;border:3px solid var(--ink);border-radius:26px;text-align:center;color:var(--ink);background:var(--paper);box-shadow:6px 8px 0 var(--ink)}',
    '.sub-card h3{margin:0 0 2px;font-family:var(--display);font-size:26px;font-weight:800;line-height:1.1}.sub-card h3 b{display:inline-block;white-space:nowrap;padding:0 10px;border:3px solid var(--ink);border-radius:99px;background:var(--accent)}',
    '.sub-card p{margin:6px 0 12px;font-size:14px;font-weight:700;color:rgba(43,26,18,.78)}',
    '.sub-card input{width:100%;font-family:var(--display);font-size:22px;font-weight:700;text-align:center;color:var(--ink);background:#fff;border:3px solid var(--ink);border-radius:14px;padding:8px 12px;outline:none;box-shadow:inset 0 3px 0 rgba(43,26,18,.1)}',
    '.sub-card input:focus{background:#FFFBE8;box-shadow:0 0 0 4px var(--accent)}',
    '.sub-card .row{display:flex;gap:10px;margin-top:12px;justify-content:center}',
    '.sub-card .row button{padding:8px 22px;font-family:var(--display);font-size:20px;font-weight:700;color:var(--ink);background:var(--accent);border:3px solid var(--ink);border-radius:14px;box-shadow:3px 4px 0 var(--ink);cursor:pointer}',
    '.sub-card .row button:active{transform:translate(2px,3px);box-shadow:1px 1px 0 var(--ink)}',
    '.sub-card .row button.ghost{background:#fff}',
    '.sub-card .row button:disabled{opacity:.6;cursor:default}',
    '.sub-card .msg{margin:8px 0 0;min-height:1.3em;font-size:14px;font-weight:800;color:#C23A1C}',
    '@media (max-width:560px){.lb{padding:14px 12px;border-radius:24px;box-shadow:6px 8px 0 var(--ink)}.lb h2{font-size:26px}.lb h2 small{display:none}.lb .podium{gap:4px;padding:8px 2px 0}.lb .pod{--d:54px}.lb .pod.p1{--d:70px}.lb .mw{width:calc(var(--d) + 36px);height:calc(var(--d) + 34px)}.lb .pod .nm{font-size:16px}.lb .pod .sc{font-size:16px;padding:1px 10px 1px 6px}.lb .pod .sc::before{width:14px;height:14px}.lb .pod .blk{font-size:40px}.lb .p1 .blk{height:86px}.lb .p2 .blk{height:64px}.lb .p3 .blk{height:48px}.lb .rest{padding:12px 8px}.lb .rowbtn{grid-template-columns:30px 40px minmax(0,1fr) auto;gap:9px;padding:8px 10px 8px 8px}.lb .row .av{--d:40px}.lb .row .rk{width:30px;height:30px;font-size:16px}.lb .row .nm{font-size:18px}.lb .rowbtn .sc{font-size:17px;padding:1px 10px 1px 6px}.lb .own .d{display:none}.lb .own b{font-size:20px}.lb .dscore{font-size:32px}.lb .tab{padding:4px 11px;font-size:15px}}',
    // Night: the page's Day / Night toggle sets data-mode="dark" on <html>; these only recolour, the layout stays
    'html[data-mode=dark] .lb,html[data-mode=dark] .lb .detail,html[data-mode=dark] .lb .foot,html[data-mode=dark] .lb .rest,html[data-mode=dark] .lb .msg,html[data-mode=dark] .lb .empty-state{color:var(--tx)}',
    'html[data-mode=dark] .lb h2,html[data-mode=dark] .lb .pod .nm,html[data-mode=dark] .lb .dscore,html[data-mode=dark] .lb .empty-state b,html[data-mode=dark] .lb .msg{color:var(--tx)}',
    'html[data-mode=dark] .lb h2 small,html[data-mode=dark] .lb .pod.me .nm,html[data-mode=dark] .lb .nm em,html[data-mode=dark] .lb .dname em,html[data-mode=dark] .lb .who .av,html[data-mode=dark] .lb .own,html[data-mode=dark] .lb .own b,html[data-mode=dark] .lb .tab[aria-selected=true],html[data-mode=dark] .lb .msg.ok::before,html[data-mode=dark] .lb .msg.err::before{color:#1A1626}',
    'html[data-mode=dark] .lb .tab{color:rgba(var(--tx-rgb),.7)}',
    'html[data-mode=dark] .lb .tab:hover{color:var(--tx)}',
    'html[data-mode=dark] .lb button.ghost,html[data-mode=dark] .lb .linklike{background:var(--sand);color:var(--tx)}',
    'html[data-mode=dark] .lb .podium{background:radial-gradient(rgba(var(--tx-rgb),.12) 1.4px,transparent 1.6px) 0 0/16px 16px,linear-gradient(180deg,#1F2A52,#34437A)}',
    'html[data-mode=dark] .lb .pod.empty .av{background:rgba(255,255,255,.08);border-color:rgba(var(--tx-rgb),.5);color:rgba(var(--tx-rgb),.55)}',
    'html[data-mode=dark] .lb .pod.empty .sc{color:rgba(var(--tx-rgb),.55)}',
    'html[data-mode=dark] .lb .pod.empty .blk{background:repeating-linear-gradient(135deg,rgba(255,255,255,.05) 0 8px,transparent 8px 16px),var(--sand);color:rgba(var(--tx-rgb),.3)}',
    'html[data-mode=dark] .lb .rowbtn{background:var(--paper);color:var(--tx)}',
    'html[data-mode=dark] .lb .row.me .rowbtn,html[data-mode=dark] .lb .detail.mine{background:linear-gradient(var(--tint),var(--tint)),var(--paper)}',
    'html[data-mode=dark] .lb .bar{background:#1A1828}',
    'html[data-mode=dark] .lb .dbadge{background:var(--sand)}',
    'html[data-mode=dark] .lb .dsub{color:rgba(var(--tx-rgb),.7)}',
    'html[data-mode=dark] .lb .dscore small,html[data-mode=dark] .lb .who .pn small{color:rgba(var(--tx-rgb),.65)}',
    'html[data-mode=dark] .lb .empty-state{color:rgba(var(--tx-rgb),.8)}',
    'html[data-mode=dark] .lb .upd{color:rgba(var(--tx-rgb),.75)}',
    'html[data-mode=dark] .lb .skel i{background:linear-gradient(90deg,var(--sand) 25%,#4A4668 50%,var(--sand) 75%);background-size:300% 100%}',
    'html[data-mode=dark] .lb .msg.err{background:#6B2E2A}',
    'html[data-mode=dark] .sub-ov{background:rgba(5,5,12,.72)}',
    'html[data-mode=dark] .sub-card{color:var(--tx)}',
    'html[data-mode=dark] .sub-card h3 b{color:#1A1626}',
    'html[data-mode=dark] .sub-card p{color:rgba(var(--tx-rgb),.78)}',
    'html[data-mode=dark] .sub-card input{background:#1A1828;color:var(--tx);box-shadow:inset 0 3px 0 rgba(0,0,0,.35)}',
    'html[data-mode=dark] .sub-card input:focus{background:#232038}',
    'html[data-mode=dark] .sub-card .row button{color:#1A1626}',
    'html[data-mode=dark] .sub-card .row button.ghost{background:var(--sand);color:var(--tx)}',
    'html[data-mode=dark] .sub-card .msg{color:#FF8A73}',
    '@media (prefers-reduced-motion:reduce){.lb *{animation:none!important;transition:none!important}}'
  ].join('');
  var style = el('style'); style.textContent = css; document.head.appendChild(style);

  var stage = $('.stage');
  var panel = el('section', 'lb' + (motion ? ' fx' : '')); panel.id = 'board'; panel.setAttribute('aria-label', 'Leaderboard');
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
  document.body.appendChild(ov);   // a page-level modal, so it sits above every section

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
