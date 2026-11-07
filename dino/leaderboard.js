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
  var run = null;             // {score, ms, id, submitted}
  var runCounter = 0;
  var lastSubmitAt = 0;
  var busy = false;
  var loadOk = false;         // did the most recent board fetch succeed?

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
    '.lb{width:min(100%,900px);background:var(--card,#1d1d1d);border:1px solid var(--line,#2a2a2a);border-radius:14px;padding:18px 20px 16px}' +
    '.lb header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}' +
    '.lb h2{margin:0;font-size:16px;color:#fff;letter-spacing:.4px}' +
    '.lb h2 small{color:var(--muted,#8b8b8b);font-weight:400;margin-left:8px;font-size:12px}' +
    '.lb .icon{min-height:34px;padding:6px 12px;font-size:13px;white-space:nowrap}' +
    '.lb ol{list-style:none;margin:0;padding:0;display:grid;gap:4px}' +
    '.lb li{display:grid;grid-template-columns:38px 1fr auto;align-items:center;gap:10px;padding:8px 12px;border-radius:9px;background:rgba(255,255,255,.025);font-size:14px}' +
    '.lb li.me{background:rgba(var(--accent-rgb),.14);outline:1px solid rgba(var(--accent-rgb),.5)}' +
    '.lb .rk{color:var(--muted,#8b8b8b);text-align:center}' +
    '.lb .nm{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--fg,#d6d6d6)}' +
    '.lb li.me .nm{color:#fff}.lb .nm em{font-style:normal;color:var(--accent);font-size:11px;margin-left:8px;letter-spacing:1px}' +
    '.lb .sc{color:var(--accent);font-variant-numeric:tabular-nums;letter-spacing:1px}' +
    '.lb .own{display:flex;align-items:center;gap:10px;margin-bottom:10px;padding:10px 12px;border-radius:9px;border:1px dashed rgba(var(--accent-rgb),.55);background:rgba(var(--accent-rgb),.07);font-size:14px}' +
    '.lb .own b{color:#fff}.lb .own .d{color:var(--muted,#8b8b8b);font-size:12px;flex:1}.lb .own i{font-style:normal;color:var(--accent);letter-spacing:1px}' +
    '.lb .msg{margin:10px 0 0;min-height:1.4em;font-size:12px;color:var(--muted,#8b8b8b)}' +
    '.lb .msg.err{color:#ff8a8a}.lb .msg.ok{color:#7ee787}' +
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
    '@media (max-width:560px){.sub-ov{aspect-ratio:auto;min-height:230px}.lb{padding:14px}.lb h2 small{display:none}.lb li{grid-template-columns:30px 1fr auto;font-size:13px}}';
  var style = el('style'); style.textContent = css; document.head.appendChild(style);

  var stage = $('.stage');
  var panel = el('section', 'lb'); panel.setAttribute('aria-label', 'Leaderboard');
  var head = el('header');
  var title = el('h2', null, '🏆 Leaderboard'); title.appendChild(el('small', null, 'top runners'));
  var refreshBtn = el('button', 'ghost icon', '↻ Refresh'); refreshBtn.type = 'button';
  head.appendChild(title); head.appendChild(refreshBtn);
  var ownerBox = el('div', 'own'); ownerBox.hidden = true;
  var list = el('ol');
  var status = el('p', 'msg'); status.setAttribute('aria-live', 'polite');
  panel.appendChild(head); panel.appendChild(ownerBox); panel.appendChild(list); panel.appendChild(status);
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

  function render() {
    list.textContent = '';
    var medals = ['🥇', '🥈', '🥉'];
    board.slice(0, TOP).forEach(function (e, i) {
      var li = el('li', mine.indexOf(e.id) !== -1 ? 'me' : '');
      li.appendChild(el('span', 'rk', i < 3 ? medals[i] : String(i + 1)));
      var nm = el('span', 'nm', e.name);
      if (mine.indexOf(e.id) !== -1) nm.appendChild(el('em', null, 'YOU'));
      li.appendChild(nm);
      li.appendChild(el('span', 'sc', pad5(e.score)));
      list.appendChild(li);
    });
    if (owner) {
      ownerBox.hidden = false; ownerBox.textContent = '';
      ownerBox.appendChild(el('span', null, '👑'));
      ownerBox.appendChild(el('b', null, owner.name));
      ownerBox.appendChild(el('span', 'd', "the creator's best — can you beat it?"));
      ownerBox.appendChild(el('i', null, pad5(owner.score)));
    } else { ownerBox.hidden = true; }
  }

  /* ---------- data ---------- */
  function loadBoard() {
    return request('/scores.json?orderBy=%22score%22&limitToLast=' + FETCH).then(function (data) {
      var rows = [];
      Object.keys(data || {}).forEach(function (id) {
        var v = data[id];
        if (v && typeof v.name === 'string' && typeof v.score === 'number') rows.push({ id: id, name: v.name, score: v.score, t: v.t || 0 });
      });
      rows.sort(function (a, b) { return b.score - a.score || a.t - b.t; });
      var seen = {}, best = [];
      rows.forEach(function (r) { var k = r.name.toLowerCase(); if (!seen[k]) { seen[k] = 1; best.push(r); } });
      board = best.slice(0, TOP);
      loadOk = true;
      render();
      if (!sticky) setStatus(board.length ? '' : 'No scores yet — be the first on the board!');
      return board;
    }).catch(function () { loadOk = false; if (!sticky) setStatus("Couldn't reach the leaderboard right now. Your run still counts locally.", 'err'); return board; });
  }

  function loadOwner() {
    return request('/owner.json').then(function (o) {
      var n = normaliseOwner(o); if (n) owner = n; render();
    }).catch(noop);
  }

  function qualifies(score) { return board.length < TOP || score > board[board.length - 1].score; }

  /* ---------- submit flow ---------- */
  function openSubmit() {
    if (!run || run.submitted) return;
    sNum.textContent = pad5(run.score); subMsg.textContent = '';
    input.value = cleanName(recall('dinoLbName') || '');
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
      closeSubmit();
      return loadBoard().then(function () {
        var rank = -1;
        board.forEach(function (e, i) { if (res && e.id === res.name) rank = i + 1; });
        setStatus(rank > 0 ? 'Submitted — you are #' + rank + '! Press Space to play again.' : 'Submitted! Press Space to play again.', 'ok', true);
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
        if (loadOk && run === mineRun && !mineRun.submitted && qualifies(mineRun.score)) openSubmit();
      });
    }
  };

  loadBoard(); loadOwner();
  setInterval(function () { if (!document.hidden && ov.hidden) loadBoard(); }, POLL_MS);
})();
