// Run the real portfolio-page JS against a fake DOM, localStorage and Google Drive; check the sync rules.
const fs = require('fs');
let src = fs.readFileSync(process.argv[2], 'utf8').trim();
src = src.slice('(function(){'.length, src.length - '})();'.length);
function fakeEl() {
  const t = function () { return P; };
  const P = new Proxy(t, {
    get(_, k) {
      if (k === 'textContent' || k === 'innerHTML' || k === 'value') return '';
      if (k === 'style' || k === 'dataset' || k === 'classList') return new Proxy({}, { get: () => () => {}, set: () => true });
      if (k === 'files') return [];
      if (k === Symbol.toPrimitive) return () => '';
      if (k === 'getBoundingClientRect') return () => ({ width: 300, height: 100, left: 0, top: 0 });
      if (k === 'querySelectorAll' || k === 'getElementsByTagName') return () => [];
      if (k === 'getContext') return () => null;
      return P;
    },
    set: () => true, apply: () => P,
  });
  return P;
}
function run(store, drive, opts) {
  const LS = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: k => { delete store[k]; } };
  const pub = JSON.stringify({ fx: { USD: 32.4 }, q: {}, gcid: 'cid', hist: {} });
  const doc = { getElementById: id => (id === 'pf-data' ? { textContent: pub } : fakeEl()), createElement: () => fakeEl(),
    createElementNS: () => fakeEl(), head: fakeEl(), body: fakeEl(), documentElement: { lang: 'zh' }, querySelectorAll: () => [],
    addEventListener: () => {} };
  const msgs = [];
  const fetchFake = async (url, o) => {
    o = o || {};
    if (url.includes('/revisions?')) return { ok: true, status: 200, json: async () => ({ revisions: drive.revs.map((r, i) => ({ id: 'r' + i, modifiedTime: r.t })) }) };
    if (url.includes('/revisions/')) { const i = +url.split('/revisions/r')[1].split('?')[0]; return { ok: true, status: 200, json: async () => drive.revs[i].d }; }
    if (url.includes('files?spaces')) return { ok: true, status: 200, json: async () => ({ files: drive.file ? [{ id: 'F' }] : [] }) };
    if (url.includes('upload')) { drive.file = JSON.parse(o.body); drive.writes++; return { ok: true, status: 200, json: async () => ({ id: 'F' }) }; }
    if (url.includes('alt=media')) return { ok: true, status: 200, json: async () => drive.file };
    return { ok: true, status: 200, json: async () => ({}) };
  };
  const ctx = { document: doc, localStorage: LS, window: {}, navigator: { language: 'zh' }, fetch: fetchFake, console,
    confirm: () => true, setTimeout: (f) => { try { f(); } catch (e) {  } return 0; }, Node: function(){}, Element: function(){}, requestAnimationFrame: (f)=>0, MutationObserver: function(){ this.observe=()=>{}; }, clearTimeout: () => {}, setInterval: () => 0, location: { hash: '' },
    google: { accounts: { oauth2: { initTokenClient: (c) => ({ requestAccessToken: () => c.callback({ access_token: 't', expires_in: 3600 }) }) } } },
    Blob: function () {}, URL: { createObjectURL: () => '' }, FileReader: function () {}, Intl, Date, Math, JSON, Promise, Object, Array, Number, String, isFinite, parseFloat, parseInt, Proxy, Symbol, encodeURIComponent };
  ctx.window = ctx; ctx.window.google = ctx.google;
  store['wss_portfolio_gsync'] = '1';
  const f = new Function(...Object.keys(ctx), src + '\n;return {get, put, gsync, grestore, G, _n, BKEY: typeof BKEY!=="undefined"?BKEY:null, gmsgs: (typeof __m!=="undefined"?__m:null)};');
  let api;
  try { api = f(...Object.values(ctx)); } catch (e) { console.log('RUNTIME ERROR', e.message); process.exit(1); }
  return api;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const H = { v: 1, h: [{ s: 'NVDA', n: 10, c: 100, p: 0 }, { s: '2330', n: 1000, c: 500, p: 0 }], cash: [], nav: [], updated: 1000 };
  let ok = true;
  const check = (c, m) => { console.log((c ? 'PASS ' : 'FAIL ') + m); ok = ok && c; };
  // 1) wiped device (empty local, timestamp newer) must NOT erase Drive; it should load Drive instead
  let drive = { file: JSON.parse(JSON.stringify(H)), writes: 0, revs: [] };
  let store = { wss_portfolio_v1: JSON.stringify({ v: 1, h: [], cash: [], nav: [], updated: 5000 }) };
  let api = run(store, drive); await sleep(50); api.G.busy = false; api.G.on = true; api.G.tok = 't'; api.G.exp = Date.now() + 1e6; api.gsync(); await sleep(100);
  check(drive.file.h.length === 2, 'empty device does not overwrite Drive');
  check(JSON.parse(store.wss_portfolio_v1).h.length === 2, 'empty device loads the holdings from Drive');
  // 2) empty Drive (newer, not an explicit clear) must not wipe a device that has holdings; device re-uploads
  drive = { file: { v: 1, h: [], cash: [], nav: [], updated: 9000 }, writes: 0, revs: [] };
  store = { wss_portfolio_v1: JSON.stringify(H) };
  api = run(store, drive); await sleep(50); api.G.busy = false; api.G.on = true; api.G.tok = 't'; api.G.exp = Date.now() + 1e6; api.gsync(); await sleep(100);
  check(JSON.parse(store.wss_portfolio_v1).h.length === 2, 'device keeps its holdings when Drive is empty');
  check(drive.file.h.length === 2, 'device restores Drive');
  // 3) explicit 清除全部 on another device DOES propagate
  drive = { file: { v: 1, h: [], cash: [], nav: [], updated: 9000, cleared: true }, writes: 0, revs: [] };
  store = { wss_portfolio_v1: JSON.stringify(H) };
  api = run(store, drive); await sleep(50); api.G.busy = false; api.G.on = true; api.G.tok = 't'; api.G.exp = Date.now() + 1e6; api.gsync(); await sleep(100);
  check(JSON.parse(store.wss_portfolio_v1).h.length === 0, 'an explicit clear still propagates');
  // 4) overwriting Drive keeps the replaced version as .prev
  drive = { file: JSON.parse(JSON.stringify(H)), writes: 0, revs: [] };
  store = { wss_portfolio_v1: JSON.stringify({ ...H, h: [H.h[0]], updated: 5000 }) };
  api = run(store, drive); await sleep(50); api.G.busy = false; api.G.on = true; api.G.tok = 't'; api.G.exp = Date.now() + 1e6; api.gsync(); await sleep(100);
  check(drive.file.h.length === 1 && drive.file.prev && drive.file.prev.h.length === 2, 'Drive keeps the replaced version as prev');
  // 5) restore from Drive revision history when both sides are empty
  drive = { file: { v: 1, h: [], cash: [], nav: [], updated: 9000 }, writes: 0,
            revs: [{ t: '2026-10-10T00:00:00Z', d: H }, { t: '2026-10-17T00:00:00Z', d: { v: 1, h: [], cash: [], nav: [] } }] };
  store = { wss_portfolio_v1: JSON.stringify({ v: 1, h: [], cash: [], nav: [], updated: 9000 }) };
  api = run(store, drive); await sleep(50); api.G.on = true; api.G.tok = 't'; api.G.exp = Date.now() + 1e6; api.grestore(); await sleep(200);
  check(JSON.parse(store.wss_portfolio_v1).h.length === 2, 'restore finds the last non-empty Drive revision');
  // 6) local backup is kept when a save replaces a non-empty portfolio
  store = { wss_portfolio_v1: JSON.stringify(H) };
  drive = { file: null, writes: 0, revs: [] };
  api = run(store, drive); await sleep(50); api.G.on = false; api.put({ v: 1, h: [], cash: [], nav: [], cleared: true });
  check(store.wss_portfolio_backup_v1 && JSON.parse(store.wss_portfolio_backup_v1).h.length === 2, 'this browser keeps the previous version');
  console.log(ok ? 'ALL SIM PASS' : 'SIM FAILED');
  process.exit(ok ? 0 : 1);
})();
