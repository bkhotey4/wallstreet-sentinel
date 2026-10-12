const {test} = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {JSDOM} = require(path.join(process.env.WSS_TEST_DEPS, 'jsdom'));
const html = fs.readFileSync(process.env.WSS_TEST_HTML, 'utf8');
const tick = () => new Promise(r => setTimeout(r, 30));
async function browser(configured = true) {
  let callback, logged = false;
  let row = {document: {v: 1, h: [], cash: []}, version: 0, updated_at: '2026-10-13T00:00:00Z'};
  const session = {user: {id: 'owner', email: 'owner@example.test'}};
  const client = {
    auth: {
      getSession: async () => ({data: {session: null}}),
      onAuthStateChange: cb => { callback = cb; },
      signInWithOAuth: async options => { assert.equal(options.provider, 'google'); logged = true; callback('SIGNED_IN', session); return {}; },
      signOut: async () => { callback('SIGNED_OUT', null); return {}; }
    },
    rpc: async (name, args) => {
      if (name === 'wss_portfolio_save') row = {...row, version: row.version + 1, document: args.document};
      return {data: structuredClone(row)};
    }
  };
  const dom = new JSDOM(html, {url: 'https://example.test/wallstreet-sentinel/#portfolio', runScripts: 'outside-only'});
  const w = dom.window;
  w.confirm = () => true;
  w.fetch = async () => ({ok: true, json: async () => ({cols: ['sym','name','px','r1d'], rows: [], asof: '2026-10-13'})});
  w.supabase = {createClient: () => client};
  const append = w.document.head.appendChild.bind(w.document.head);
  w.document.head.appendChild = node => { if (node.tagName === 'SCRIPT') { setTimeout(() => node.onload(), 0); return node; } return append(node); };
  w.document.getElementById('pf-cloud-config').textContent = JSON.stringify(configured ? {url: 'https://test.supabase.co', key: 'sb_publishable_test'} : {url: '', key: ''});
  // jsdom does not implement legacy form named properties, which browsers do.
  for (const form of w.document.forms) for (const input of form.elements) if (input.name) form[input.name] = input;
  for (const script of w.document.querySelectorAll('script:not([type])')) w.eval(script.textContent);
  await tick();
  return {dom, w, row: () => row, logged: () => logged};
}
test('no configuration stays locked while preserving local export', async () => {
  const {dom,w} = await browser(false);
  assert.equal(w.document.getElementById('pfprivate').hidden, true);
  assert.equal(w.document.getElementById('pflogin').disabled, true);
  assert.match(w.document.getElementById('pfcloudstatus').textContent, /尚未啟用/);
  dom.window.close();
});
test('login, add, cash, import migration and logout clear the rendered portfolio', async () => {
  const {dom,w,row} = await browser(); const get = id => w.document.getElementById(id);
  assert.equal(get('pfprivate').hidden, true);
  get('pflogin').click(); await tick(); await tick();
  assert.equal(get('pfprivate').hidden, false);
  const form = get('pfadd'); form.s.value = 'NVDA'; form.n.value = '2'; form.c.value = '100';
  form.dispatchEvent(new w.Event('submit', {cancelable: true})); await tick();
  assert.equal(row().document.h[0].s, 'NVDA');
  assert.match(get('pft').textContent, /NVDA/);
  const cash = get('pfcash'); cash.cur.value = 'TWD'; cash.a.value = '500';
  cash.dispatchEvent(new w.Event('submit', {cancelable: true})); await tick();
  assert.equal(row().document.cash[0].a, 500);
  assert.match(get('pfsum').textContent, /8,180/);
  w.localStorage.setItem('wss_portfolio_v1', JSON.stringify({v: 1, h: [{s: 'NVDA', n: 3, c: 1, p: 0}], cash: []}));
  await w.wssPortfolioStore.reload(); await tick(); get('pfmigrate').click(); await tick();
  assert.equal(row().document.h[0].n, 3);
  assert.ok(w.localStorage.getItem('wss_portfolio_v1'));
  get('pfpaste').value = 'NVDA 99 100';
  get('pflogout').click(); await tick();
  assert.equal(get('pfprivate').hidden, true);
  assert.equal(get('pfpaste').value, ''); assert.equal(get('pft').tBodies[0].textContent, '');
  assert.equal(get('pfsum').textContent, ''); assert.equal(get('pfaccount').textContent, '');
  dom.window.close();
});
