// node tests_js/quote.test.mjs — offline checks with a fake upstream; add LIVE=1 to also hit Yahoo for real.
import assert from "node:assert/strict";
import { one, parse, onRequestGet, rsi, tech } from "../functions/api/quote.js";

assert.deepEqual(parse("^vix, ^VIX ,bad sym,<x>,2330.TW"), ["^VIX", "2330.TW"]);
assert.equal(parse(Array.from({ length: 40 }, (_, i) => "A" + i).join(",")).length, 25);

const fake = async () => new Response(JSON.stringify({ chart: { result: [{ meta: {
  regularMarketPrice: 110, previousClose: 100, regularMarketTime: 1, shortName: "Fake", currency: "USD" } }] } }));
const q = await one("FAKE", fake);
assert.equal(q.price, 110);
assert.ok(Math.abs(q.chg - 10) < 1e-9);
assert.equal(await one("X", async () => new Response("", { status: 404 })), null);

// full mode: 260 rising closes, two dividends inside the year and one older
const now = Math.floor(Date.now() / 1000);
const closes = Array.from({ length: 260 }, (_, i) => 100 + i);
const fakeFull = async () => new Response(JSON.stringify({ chart: { result: [{
  meta: { regularMarketPrice: 359, chartPreviousClose: 50, regularMarketTime: now, shortName: "F", currency: "TWD" },
  timestamp: closes.map((_, i) => now - (259 - i) * 86400), indicators: { quote: [{ close: closes }] },
  events: { dividends: { a: { amount: 1, date: now - 100 * 86400 }, b: { amount: 0.5, date: now - 10 * 86400 }, c: { amount: 9, date: now - 400 * 86400 } } } }] } }));
const f = await one("F", fakeFull, true);
assert.equal(f.prev, 358);                                               // second-to-last close, not the year-ago close
assert.equal(f.hi52, 359) && assert.equal(f.lo52, 108);
assert.equal(f.div12, 1.5);
assert.ok(f.rsi14 === 100 && f.ma_gap > 0 && f.m1[0] < 359 && f.m1[1] > 359);
assert.ok(Math.abs(rsi([1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]) - 50) < 10);
assert.equal(tech([5], {}, now).hi52, undefined);

const bad = await onRequestGet({ request: new Request("https://x/api/quote?s=<<") });
assert.equal(bad.status, 400);

if (process.env.LIVE) {
  const r = await onRequestGet({ request: new Request("https://x/api/quote?s=^VIX,^VIX3M,2330.TW,NOPE_ZZZ") });
  const d = await r.json();
  assert.equal(r.status, 200);
  assert.ok(d.q["^VIX"].price > 0 && d.q["2330.TW"].price > 0 && !d.q["NOPE_ZZZ"]);
  const r2 = await (await onRequestGet({ request: new Request("https://x/api/quote?full=1&s=00878.TW,MSFT") })).json();
  assert.ok(r2.q["00878.TW"].div12 > 0 && r2.q["MSFT"].hi52 > 0 && r2.q["MSFT"].rsi14 > 0);
  console.log("live:", JSON.stringify(d.q["^VIX"]), JSON.stringify(r2.q["00878.TW"]));
}
console.log("quote tests ok");
