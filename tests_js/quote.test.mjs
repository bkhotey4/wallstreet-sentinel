// node tests_js/quote.test.mjs — offline checks with a fake upstream; add LIVE=1 to also hit Yahoo for real.
import assert from "node:assert/strict";
import { one, parse, onRequestGet, rsi, tech, volRatio, sdAll, todayOpen } from "../functions/api/quote.js";

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
assert.equal(sdAll([1, 2, 3]), null);                                    // too short for a one-year normal move
const alt = Array.from({ length: 101 }, (_, i) => (i % 2 ? 101 : 100));
assert.ok(sdAll(alt) > 0.9 && sdAll(alt) < 1.1 && f.sd1y > 0);

// volume vs the same time on earlier days: 3 days × 4 bars; today has 2 bars so far with double the volume
const D = 86400, t0 = 1_000_000 * D + 13.5 * 3600, vts = [], vv = [], vc = [];
for (let d = 0; d < 3; d++) for (let b = 0; b < (d === 2 ? 2 : 4); b++) { vts.push(t0 + d * D + b * 300); vv.push(d === 2 ? 200 : 100); vc.push(10 + d); }
const vr = volRatio(vts, vv, vc, 0);
assert.equal(vr.vol, 400); assert.equal(vr.volx, 2); assert.equal(vr.prevDay, 11);
assert.deepEqual(volRatio(vts.slice(0, 4), vv.slice(0, 4), vc.slice(0, 4), 0), {});   // one day only: no baseline
const fakeVol = async () => new Response(JSON.stringify({ chart: { result: [{ meta: { regularMarketPrice: 9, regularMarketTime: vts.at(-1), chartPreviousClose: 1, shortName: "V" },
  timestamp: vts, indicators: { quote: [{ volume: vv, close: vc }] } }] } }));
const qv = await one("V", fakeVol, false, true);
assert.equal(todayOpen({ timestamp: vts, indicators: { quote: [{ open: vts.map((_, i) => i + 1) }] }, meta: { gmtoffset: 0 } }), 9);   // first bar of day 3
assert.equal(todayOpen({ timestamp: [], indicators: {} }), null);
assert.equal(qv.volx, 2); assert.equal(qv.prev, 11); assert.ok(Math.abs(qv.chg - (9 / 11 - 1) * 100) < 1e-9);

const bad = await onRequestGet({ request: new Request("https://x/api/quote?s=<<") });
assert.equal(bad.status, 400);

if (process.env.LIVE) {
  const r = await onRequestGet({ request: new Request("https://x/api/quote?s=^VIX,^VIX3M,2330.TW,NOPE_ZZZ") });
  const d = await r.json();
  assert.equal(r.status, 200);
  assert.ok(d.q["^VIX"].price > 0 && d.q["2330.TW"].price > 0 && !d.q["NOPE_ZZZ"]);
  const r2 = await (await onRequestGet({ request: new Request("https://x/api/quote?full=1&s=00878.TW,MSFT") })).json();
  assert.ok(r2.q["00878.TW"].div12 > 0 && r2.q["MSFT"].hi52 > 0 && r2.q["MSFT"].rsi14 > 0);
  const r3 = await (await onRequestGet({ request: new Request("https://x/api/quote?s=SPY,^VIX&vol=SPY") })).json();
  assert.ok(r3.q["SPY"].price > 0 && r3.q["SPY"].prev > 0 && r3.q["^VIX"].volx === undefined);
  console.log("live:", JSON.stringify(d.q["^VIX"]), JSON.stringify(r2.q["00878.TW"]), JSON.stringify(r3.q["SPY"]));
}
console.log("quote tests ok");

// extended hours: a post-market bar after the regular close, then the same chart with the last bar inside the session
{
  const { extFrom } = await import("../functions/api/quote.js");
  const meta = { regularMarketPrice: 100, currentTradingPeriod: { regular: { start: 1000, end: 2000 } } };
  const e = extFrom({ meta, timestamp: [1500, 2100], indicators: { quote: [{ close: [99, 104] }] } });
  assert.equal(e.sess, "post"); assert.ok(Math.abs(e.chg - 4) < 1e-9);
  assert.equal(extFrom({ meta, timestamp: [500, 1500], indicators: { quote: [{ close: [97, 99] }] } }), null);
  assert.equal(extFrom({ meta, timestamp: [500], indicators: { quote: [{ close: [97] }] } }).sess, "pre");
  console.log("ok ext");
}

// weekly history for the look-back calculator: a missed 1:7 split is repaired, dividends come back as [date, amount]
{
  const { histFrom, fixSplits } = await import("../functions/api/quote.js");
  const W = 7 * 86400, t0 = 1_700_000_000;
  const h = histFrom({ meta: { gmtoffset: 0, shortName: "X" }, timestamp: [0, 1, 2, 3, 4, 5].map((i) => t0 + i * W),
    indicators: { quote: [{ close: [350, 352, 50.4, 51, 52, 53] }] }, events: { dividends: { a: { amount: 1, date: t0 + 4 * W } } } });
  assert.ok(Math.abs(h.w[0][1] - 50) < 0.01 && h.w[2][1] === 50.4 && h.dv.length === 1);
  assert.equal(fixSplits([["a", 100], ["b", 55]])[0][1], 100);
  console.log("ok hist");
}

// fastest 15-minute move of the latest day (earlier days ignored)
{
  const { jumpOf } = await import("../functions/api/quote.js");
  const D = 86400, t0 = 1_000_000 * D;
  const ts = [t0 - D, t0 - D + 300, t0, t0 + 300, t0 + 600, t0 + 900, t0 + 1200, t0 + 1500];
  const c = [50, 10, 100, 100.1, 100.2, 99.0, 98.5, 98.6];
  const j = jumpOf(ts, c, 0);
  assert.equal(j.t, t0 + 1200); assert.ok(Math.abs(j.chg - (98.5 / 100.1 - 1) * 100) < 1e-9);
  assert.equal(jumpOf([], [], 0), null);
  console.log("ok jump");
}

// full mode carries the trend up to yesterday's close (p0 yesterday, p1 the day before, p5 / p20 sessions earlier)
{
  assert.deepEqual(f.trend, { p0: 358, p1: 357, p5: 353, p20: 338 });
  console.log("ok trend");
}
