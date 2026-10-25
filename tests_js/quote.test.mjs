// node tests_js/quote.test.mjs — offline checks with a fake upstream; add LIVE=1 to also hit Yahoo for real.
import assert from "node:assert/strict";
import { one, parse, onRequestGet } from "../functions/api/quote.js";

assert.deepEqual(parse("^vix, ^VIX ,bad sym,<x>,2330.TW"), ["^VIX", "2330.TW"]);
assert.equal(parse(Array.from({ length: 40 }, (_, i) => "A" + i).join(",")).length, 25);

const fake = async () => new Response(JSON.stringify({ chart: { result: [{ meta: {
  regularMarketPrice: 110, previousClose: 100, regularMarketTime: 1, shortName: "Fake", currency: "USD" } }] } }));
const q = await one("FAKE", fake);
assert.equal(q.price, 110);
assert.ok(Math.abs(q.chg - 10) < 1e-9);
assert.equal(await one("X", async () => new Response("", { status: 404 })), null);

const bad = await onRequestGet({ request: new Request("https://x/api/quote?s=<<") });
assert.equal(bad.status, 400);

if (process.env.LIVE) {
  const r = await onRequestGet({ request: new Request("https://x/api/quote?s=^VIX,^VIX3M,2330.TW,NOPE_ZZZ") });
  const d = await r.json();
  assert.equal(r.status, 200);
  assert.ok(d.q["^VIX"].price > 0 && d.q["2330.TW"].price > 0 && !d.q["NOPE_ZZZ"]);
  console.log("live:", JSON.stringify(d.q["^VIX"]));
}
console.log("quote tests ok");
