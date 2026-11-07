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
  var css =
    '.stage{position:relative}' +
    '.lb{--gold:#f5c542;--silver:#c5ccd6;--bronze:#d08a52;width:min(100%,900px);background:linear-gradient(180deg,rgba(var(--accent-rgb),.05),transparent 160px),var(--card,#1d1d1d);border:1px solid var(--line,#2a2a2a);border-radius:16px;padding:18px 20px 14px;position:relative;overflow:hidden}' +
    '.lb header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:12px}' +
    '.lb h2{margin:0;font-size:16px;color:#fff;letter-spacing:.4px}' +
    '.lb h2 small{color:var(--muted,#8b8b8b);font-weight:400;margin-left:8px;font-size:12px}' +
    '.lb .tools{display:flex;align-items:center;gap:8px;flex-wrap:wrap}' +
    '.lb .tabs{display:inline-flex;padding:3px;border-radius:11px;background:rgba(255,255,255,.04);border:1px solid var(--line,#2a2a2a)}' +
    '.lb .tab{min-height:30px;padding:4px 12px;font-size:12px;border-radius:8px;background:transparent;color:var(--muted,#8b8b8b);border:0;letter-spacing:.3px;transition:background .2s,color .2s}' +
    '.lb .tab:hover{color:#fff}.lb .tab[aria-selected=true]{background:var(--accent);color:#161616;font-weight:700}' +
    '.lb .icon{min-height:34px;padding:6px 12px;font-size:13px;white-space:nowrap}' +
    '.lb .icon.spin::first-letter{display:inline-block;animation:lbspin .8s linear infinite}' +
    '.lb ol{list-style:none;margin:0;padding:0}' +
    /* creator card + race track */
    '.lb .own{margin-bottom:14px;padding:11px 14px 12px;border-radius:12px;border:1px dashed rgba(var(--accent-rgb),.55);background:linear-gradient(90deg,rgba(var(--accent-rgb),.12),rgba(var(--accent-rgb),.03))}' +
    '.lb .ownrow{display:flex;align-items:center;gap:10px;font-size:14px}' +
    '.lb .own b{color:#fff}.lb .own .d{color:var(--muted,#8b8b8b);font-size:12px;flex:1}.lb .own i{font-style:normal;color:var(--accent);letter-spacing:1px}' +
    '.lb .track{position:relative;height:8px;margin-top:10px;border-radius:99px;background:rgba(255,255,255,.07);overflow:hidden}' +
    '.lb .track .fill{display:block;height:100%;width:0;border-radius:99px;background:linear-gradient(90deg,rgba(var(--accent-rgb),.5),var(--accent));box-shadow:0 0 12px rgba(var(--accent-rgb),.6);transition:width 1s cubic-bezier(.2,.8,.2,1)}' +
    '.lb .tl{margin:6px 0 0;font-size:11px;color:var(--muted,#8b8b8b)}' +
    /* podium */
    '.lb .podium{display:flex;align-items:flex-end;justify-content:center;gap:10px;margin:6px 0 12px}' +
    '.lb .pod{flex:1 1 0;max-width:230px;min-width:0;display:flex;flex-direction:column;align-items:center;text-align:center;cursor:pointer;border-radius:12px;outline:none}' +
    '.lb .pod.p1{order:2}.lb .pod.p2{order:1}.lb .pod.p3{order:3}' +
    '.lb .pod.empty{cursor:default;opacity:.55}' +
    '.lb .pod .medal{font-size:26px;line-height:1;filter:drop-shadow(0 2px 6px rgba(0,0,0,.5));transition:transform .25s}' +
    '.lb .pod:hover .medal,.lb .pod:focus-visible .medal{transform:translateY(-3px) scale(1.12)}' +
    '.lb .pod.empty:hover .medal{transform:none}' +
    '.lb .pod .nm{max-width:100%;margin-top:4px;font-size:14px;font-weight:700;color:#fff}' +
    '.lb .pod .sc{margin:2px 0 8px;font-size:15px}' +
    '.lb .pod .blk{width:100%;display:flex;align-items:flex-start;justify-content:center;padding-top:8px;border-radius:10px 10px 4px 4px;color:rgba(0,0,0,.55);font-weight:800;font-size:18px;border:1px solid rgba(255,255,255,.12);transform-origin:bottom;transition:filter .2s}' +
    '.lb .pod:hover .blk,.lb .pod:focus-visible .blk{filter:brightness(1.18)}' +
    '.lb .p1 .blk{height:84px;background:linear-gradient(180deg,#ffe27a,var(--gold) 55%,#b98a14)}' +
    '.lb .p2 .blk{height:62px;background:linear-gradient(180deg,#eef1f6,var(--silver) 55%,#8c95a3)}' +
    '.lb .p3 .blk{height:46px;background:linear-gradient(180deg,#f0b887,var(--bronze) 55%,#8f5a2c)}' +
    '.lb .pod.empty .blk{background:repeating-linear-gradient(135deg,rgba(255,255,255,.05) 0 8px,transparent 8px 16px);border-style:dashed;color:var(--muted,#8b8b8b)}' +
    '.lb .pod.me .nm{color:var(--accent)}.lb .pod.me .blk{box-shadow:0 0 0 2px rgba(var(--accent-rgb),.9),0 0 22px rgba(var(--accent-rgb),.45)}' +
    '.lb .pod.sel .blk{box-shadow:0 0 0 2px #fff}' +
    /* rows */
    '.lb .rest{display:grid;gap:5px}' +
    '.lb .row{border-radius:10px}' +
    '.lb .rowbtn{width:100%;min-height:0;display:grid;grid-template-columns:34px minmax(0,1.1fr) minmax(40px,1fr) auto;align-items:center;gap:12px;padding:9px 12px;font:inherit;font-size:14px;color:var(--fg,#d6d6d6);background:rgba(255,255,255,.03);border:1px solid transparent;border-radius:10px;text-align:left;cursor:pointer;transition:background .2s,transform .2s,border-color .2s}' +
    '.lb .rowbtn:hover{background:rgba(255,255,255,.07);transform:translateX(3px)}' +
    '.lb .rowbtn:focus-visible{outline:2px solid var(--accent);outline-offset:1px}' +
    '.lb .row.me .rowbtn{background:rgba(var(--accent-rgb),.13);border-color:rgba(var(--accent-rgb),.55)}' +
    '.lb .row.sel .rowbtn{border-color:#fff}' +
    '.lb .row .rk{color:var(--muted,#8b8b8b);text-align:center;font-weight:700}' +
    '.lb .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
    '.lb .row.me .nm{color:#fff}.lb .nm em{font-style:normal;color:var(--accent);font-size:10px;margin-left:7px;letter-spacing:1.2px;padding:1px 5px;border:1px solid rgba(var(--accent-rgb),.6);border-radius:6px;vertical-align:1px}' +
    '.lb .bar{display:block;height:6px;border-radius:99px;background:rgba(255,255,255,.06);overflow:hidden}' +
    '.lb .bar i{display:block;height:100%;width:0;border-radius:99px;background:linear-gradient(90deg,rgba(var(--accent-rgb),.35),rgba(var(--accent-rgb),.95));transition:width .8s cubic-bezier(.2,.8,.2,1)}' +
    '.lb .sc{color:var(--accent);font-variant-numeric:tabular-nums;letter-spacing:1px;font-weight:700}' +
    /* details strip */
    '.lb .detail{margin-top:10px;padding:10px 14px;border-radius:10px;background:rgba(255,255,255,.04);border:1px solid var(--line,#2a2a2a);font-size:13px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}' +
    '.lb .detail[hidden]{display:none}.lb .detail b{color:#fff}.lb .detail span{color:var(--muted,#8b8b8b)}.lb .detail .grow{flex:1}' +
    '.lb .detail button{min-height:30px;padding:4px 12px;font-size:12px}' +
    /* states */
    '.lb .empty-state{padding:22px 10px 10px;text-align:center;color:var(--muted,#8b8b8b);font-size:14px}' +
    '.lb .empty-state .big{display:block;font-size:40px;margin-bottom:6px}.lb .empty-state b{display:block;color:#fff;margin-bottom:4px}' +
    '.lb .empty-state button{margin-top:12px;min-height:38px;padding:6px 16px;font-size:13px}' +
    '.lb .skel{display:grid;gap:6px;margin:4px 0}.lb .skel i{display:block;height:38px;border-radius:10px;background:linear-gradient(90deg,rgba(255,255,255,.04) 25%,rgba(255,255,255,.1) 50%,rgba(255,255,255,.04) 75%);background-size:300% 100%;animation:lbshim 1.3s linear infinite}' +
    '.lb .msg{margin:10px 0 0;min-height:1.4em;font-size:12px;color:var(--muted,#8b8b8b)}' +
    '.lb .msg.err{color:#ff8a8a}.lb .msg.ok{color:#7ee787}' +
    '.lb .foot{display:flex;justify-content:flex-end;margin-top:2px;font-size:11px;color:var(--muted,#8b8b8b);opacity:.8}' +
    /* motion */
    '@keyframes lbrise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}' +
    '@keyframes lbgrow{from{transform:scaleY(0)}to{transform:scaleY(1)}}' +
    '@keyframes lbflash{0%{box-shadow:0 0 0 0 rgba(var(--accent-rgb),.9)}100%{box-shadow:0 0 0 14px rgba(var(--accent-rgb),0)}}' +
    '@keyframes lbspin{to{transform:rotate(360deg)}}@keyframes lbshim{to{background-position:-300% 0}}' +
    '.lb.fx .pod{animation:lbrise .55s cubic-bezier(.2,.9,.3,1.2) both;animation-delay:calc(var(--i,0)*90ms)}' +
    '.lb.fx .pod .blk{animation:lbgrow .6s cubic-bezier(.2,.9,.3,1) both;animation-delay:calc(var(--i,0)*90ms + 80ms)}' +
    '.lb.fx .row{animation:lbrise .45s ease both;animation-delay:calc(var(--i,0)*45ms + 250ms)}' +
    '.lb.fx .fresh .rowbtn,.lb.fx .pod.fresh .blk{animation:lbflash 1.2s ease-out 2}' +
    /* submit prompt (unchanged) */
    '.sub-ov{position:absolute;top:0;left:0;width:100%;aspect-ratio:900/260;display:flex;align-items:center;justify-content:center;background:rgba(10,10,10,.78);border-radius:14px;z-index:5;padding:10px}' +
    '.sub-ov[hidden]{display:none}' +
    '.sub-card{width:min(100%,380px);background:var(--card,#1d1d1d);border:1px solid var(--line,#2a2a2a);border-radius:14px;padding:16px 18px;text-align:center;box-shadow:0 10px 40px rgba(0,0,0,.5)}' +
    '.sub-card h3{margin:0 0 4px;font-size:15px;color:#fff;letter-spacing:.5px}.sub-card h3 b{color:var(--accent)}' +
    '.sub-card p{margin:0 0 10px;font-size:12px;color:var(--muted,#8b8b8b)}' +
    '.sub-card input{width:100%;font:inherit;font-size:16px;text-align:center;letter-spacing:1px;color:#fff;background:#121212;border:1px solid var(--line,#2a2a2a);border-radius:10px;padding:10px 12px;outline:none}' +
    '.sub-card input:focus{border-color:var(--accent)}' +
    '.sub-card .row{display:flex;gap:8px;margin-top:10px;justify-content:center}' +
    '.sub-card .row button{min-height:40px;padding:8px 16px}' +
    '.sub-card .msg{margin:8px 0 0;min-height:1.3em;font-size:12px;color:#ff8a8a}' +
    '@media (max-width:560px){.sub-ov{aspect-ratio:auto;min-height:230px}.lb{padding:14px 12px}.lb h2 small{display:none}.lb .podium{gap:6px}.lb .pod .nm{font-size:12px}.lb .pod .sc{font-size:13px}.lb .pod .medal{font-size:22px}.lb .rowbtn{grid-template-columns:26px minmax(0,1fr) auto;font-size:13px;gap:8px}.lb .rowbtn .bar{display:none}.lb .own .d{display:none}.lb .tab{padding:4px 9px}}' +
    '@media (prefers-reduced-motion:reduce){.lb *{animation:none!important;transition:none!important}}';
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
  var foot = el('div', 'foot'); var upd = el('span'); foot.appendChild(upd);
  panel.appendChild(head); panel.appendChild(ownerBox); panel.appendChild(body); panel.appendChild(detail); panel.appendChild(status); panel.appendChild(foot);
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
  function setStatus(text, kind, keep) { status.textContent = text || ''; status.className = 'msg' + (kind ? ' ' + kind : ''); sticky = !!keep; }

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
    if (isMine(e.id)) nm.appendChild(el('em', null, 'YOU'));
    return nm;
  }

  function selectEntry(rows, id) {
    selected = (selected === id) ? null : id;
    Array.prototype.forEach.call(body.querySelectorAll('[data-id]'), function (n) { n.classList.toggle('sel', n.dataset.id === selected); });
    var e = rows.filter(function (r) { return r.id === selected; })[0];
    if (!e) { detail.hidden = true; return; }
    detail.textContent = '';
    detail.appendChild(el('b', null, e.name)); detail.appendChild(el('b', null, pad5(e.score)));
    var bits = [];
    if (e.ms) bits.push('ran for ' + runTime(e.ms));
    if (e.t) bits.push(ago(e.t));
    if (owner) bits.push(Math.round(e.score / owner.score * 100) + '% of ' + owner.name + "'s best");
    detail.appendChild(el('span', 'grow', bits.join(' · ')));
    if (isMine(e.id)) {
      var sh = el('button', 'ghost', '↗ Share'); sh.type = 'button';
      sh.addEventListener('click', function () { share(e); });
      detail.appendChild(sh);
    }
    detail.hidden = false;
  }

  function podiumCard(e, i, rows, top) {
    var li = document.createElement('li');
    li.className = 'pod p' + (i + 1) + (e && isMine(e.id) ? ' me' : '') + (!e ? ' empty' : '');
    li.style.setProperty('--i', String(i === 0 ? 0 : i));
    var medals = ['🥇', '🥈', '🥉'];
    li.appendChild(el('span', 'medal', e ? medals[i] : '·'));
    if (e) {
      li.dataset.id = e.id; li.tabIndex = 0; li.setAttribute('role', 'button');
      if (e.id === selected) li.classList.add('sel');
      if (seenInit && !seen[e.id]) li.classList.add('fresh');
      li.appendChild(nameCell(e));
      var sc = el('span', 'sc'); li.appendChild(sc); countUp(sc, e.score);
      li.addEventListener('click', function () { selectEntry(rows, e.id); });
      li.addEventListener('keydown', function (ev) { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); ev.stopPropagation(); selectEntry(rows, e.id); } });
    } else {
      li.setAttribute('aria-hidden', 'true'); li.setAttribute('role', 'presentation');
      li.appendChild(el('span', 'nm', 'open spot')); li.appendChild(el('span', 'sc', '—'));
    }
    var blk = el('span', 'blk', String(i + 1)); li.appendChild(blk);
    return li;
  }

  function rowEntry(e, i, rows, top) {
    var li = el('li', 'row' + (isMine(e.id) ? ' me' : '')); li.dataset.id = e.id; li.style.setProperty('--i', String(i));
    if (e.id === selected) li.classList.add('sel');
    if (seenInit && !seen[e.id]) li.classList.add('fresh');
    var b = el('button', 'rowbtn'); b.type = 'button';
    b.appendChild(el('span', 'rk', String(i + 4)));
    b.appendChild(nameCell(e));
    var bar = el('span', 'bar'), fill = el('i'); bar.appendChild(fill); b.appendChild(bar);
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
    var sig = [view, loading, loadOk, owner ? owner.score : '', rows.map(function (r) { return r.id + ':' + r.score + (isMine(r.id) ? '*' : ''); }).join(',')].join('|');
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
        if (v && typeof v.name === 'string' && typeof v.score === 'number') rows.push({ id: id, name: v.name, score: v.score, ms: typeof v.ms === 'number' ? v.ms : 0, t: v.t || 0 });
      });
      rows.sort(function (a, b) { return b.score - a.score || a.t - b.t; });
      var myTop = null;   // this browser's best entry; the others it submitted are hidden from its owner
      rows.forEach(function (r) { if (!myTop && isMine(r.id)) myTop = r; });
      if (myTop && myTop.score > myBest) { myBest = myTop.score; store('dinoLbBest', String(myBest)); }
      allRows = rows.filter(function (r) { return !isMine(r.id) || r === myTop; });
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

  /* ---------- submit flow ---------- */
  function openSubmit() {
    if (!run || run.submitted) return;
    sNum.textContent = pad5(run.score); subMsg.textContent = '';
    input.value = cleanName(recall('dinoLbName') || '');
    hint.textContent = myBest > 0 ? 'Beats your best of ' + pad5(myBest) + ' — keep the same name for a single entry' : 'Add your name to the public leaderboard';
    ov.hidden = false; submitBtn.disabled = false;
    setTimeout(function () { input.focus(); input.select(); }, 30);
  }
  function closeSubmit() { ov.hidden = true; var c = $('#game'); if (c) c.focus({ preventScroll: true }); }

  function submit() {
    if (!run || run.submitted || busy) return;
    var name = cleanName(input.value);
    var problem = nameProblem(name);
    if (problem) { subMsg.textContent = problem; return; }
    if (Date.now() - lastSubmitAt < 2000) { subMsg.textContent = 'One moment…'; return; }
    busy = true; submitBtn.disabled = true; subMsg.textContent = '';
    lastSubmitAt = Date.now();
    var body = JSON.stringify({ name: name, score: run.score, ms: run.ms, t: { '.sv': 'timestamp' } });
    request('/scores.json', { method: 'POST', body: body }).then(function (res) {
      run.submitted = true;
      if (res && res.name) { mine.push(res.name); store('dinoLbMine', JSON.stringify(mine.slice(-40))); }
      store('dinoLbName', name);
      myBest = Math.max(myBest, run.score); store('dinoLbBest', String(myBest));
      closeSubmit();
      return loadBoard().then(function () {
        var rank = -1;
        board.forEach(function (e, i) { if (res && e.id === res.name) rank = i + 1; });
        setStatus(rank > 0 ? 'Submitted — you are #' + rank + '! Press Space to play again.' : 'Submitted! Press Space to play again.', 'ok', true);
        if (res && res.name) { selected = null; var me = windowed().filter(function (r) { return r.id === res.name; })[0]; if (me) selectEntry(windowed(), me.id); }
        if (rank === 1 || (owner && run.score > owner.score)) burst();
        panel.scrollIntoView({ behavior: motion ? 'smooth' : 'auto', block: 'nearest' });
      });
    }).catch(function (err) {
      submitBtn.disabled = false;
      subMsg.textContent = err && err.status === 401 ? 'The leaderboard rejected that score.' : "Couldn't submit — check your connection and try again.";
    }).then(function () { busy = false; });
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
        if (loadOk && qualifies(mineRun.score)) openSubmit();
      });
    }
  };

  loadBoard(); loadOwner();
  setInterval(function () { if (!document.hidden && ov.hidden) loadBoard(); }, POLL_MS);
})();
