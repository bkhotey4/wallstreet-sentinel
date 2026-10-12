const {test} = require('node:test');
const assert = require('node:assert/strict');
const {Store, clean} = require('../tools/static/portfolio-cloud.js');
const empty = () => ({v: 1, h: [], cash: []});
const doc = () => ({v: 1, h: [{s: 'NVDA', n: 2, c: 100, p: 0}], cash: [{cur: 'TWD', a: 500}]});
const session = {user: {id: 'owner'}};
function server() {
  let row = {document: empty(), version: 0, updated_at: '2026-10-13T00:00:00Z'};
  return {rpc: async (name, args) => {
    if (name === 'wss_portfolio_save') {
      if (args.expected_version !== row.version) return {error: {code: 'PT409'}};
      row = {...row, document: structuredClone(args.document), version: row.version + 1};
    }
    return {data: structuredClone(row)};
  }};
}
test('signed-out clients never read or write private RPCs', async () => {
  const store = new Store({rpc() { throw Error('must not call'); }}, () => {});
  assert.equal(await store.put(doc()), false);
  assert.equal(await store.reload(), false);
  assert.deepEqual(store.get(), empty());
});
test('two devices cannot silently overwrite newer data', async () => {
  const client = server(), a = new Store(client, () => {}), b = new Store(client, () => {});
  await a.session(session); await b.session(session);
  assert.equal(await a.put(doc()), true);
  assert.equal(await b.put(empty()), false);
  assert.match(b.message, /另一台/);
  await b.reload(); assert.deepEqual(b.get(), doc());
  assert.equal(await b.put(empty()), true);
  await a.reload(); assert.deepEqual(a.get(), empty());
});
test('logout during a read or save discards late responses', async () => {
  let resolve;
  const client = {rpc: () => new Promise(r => { resolve = r; })};
  const store = new Store(client, () => {});
  const pending = store.session(session); store.reset(null);
  resolve({data: {document: doc(), version: 1}}); await pending;
  assert.deepEqual(store.get(), empty()); assert.equal(store.ready, false);
  store.user = session.user; store.ready = true;
  const saving = store.put(doc()); store.reset(null);
  resolve({data: {document: doc(), version: 2}});
  assert.equal(await saving, false); assert.deepEqual(store.get(), empty());
});
test('failed saves retain confirmed state and expose a failure status', async () => {
  const client = server(), store = new Store(client, () => {});
  await store.session(session);
  client.rpc = async () => { throw Error('offline'); };
  assert.equal(await store.put(doc()), false);
  assert.deepEqual(store.get(), empty()); assert.match(store.message, /未確認/);
  assert.equal(store.busy, false);
});
test('revoked access clears the visible state', async () => {
  const client = server(), store = new Store(client, () => {});
  await store.session(session); await store.put(doc());
  client.rpc = async () => ({error: {code: '42501'}});
  await store.put(empty()); assert.equal(store.ready, false); assert.deepEqual(store.get(), empty());
});
test('concurrent saves are blocked, and data returned to UI is a copy', async () => {
  const store = new Store(server(), () => {}); await store.session(session);
  let resolve; store.client.rpc = () => new Promise(r => { resolve = r; });
  const pending = store.put(doc()); assert.equal(await store.put(empty()), false);
  resolve({data: {document: doc(), version: 1}}); await pending;
  const data = store.get(); data.h[0].n = 999; assert.equal(store.get().h[0].n, 2);
});
test('invalid and duplicate holdings are rejected before upload', () => {
  for (const value of [null, {v: 1}, {...doc(), cash: [{cur: 'XXX', a: 1}]},
    {...doc(), h: [doc().h[0], doc().h[0]]}, {...doc(), h: [{...doc().h[0], n: Infinity}]}]) {
    assert.throws(() => clean(value));
  }
  assert.deepEqual(clean(doc()), doc());
});
