// /api/quote?iv=: same-time relative volume, VWAP + last three bars, 15/60-minute speed vs own history, CHL spread estimate
import assert from "node:assert/strict";
import { intraFrom, chlSpread } from "../functions/api/quote.js";

const D0 = 1790000000 - (1790000000 % 86400) + 14 * 3600 + 1800;
function res(today, vol, yieldBp = false) {
  const ts = [], c = [], h = [], l = [], v = [];
  for (let d = 0; d < 21; d++) for (let k = 0; k < 78; k++) {
    const p = 100 + 0.02 * Math.sin(k + d);
    ts.push(D0 + d * 86400 + k * 300); c.push(p); h.push(p + 0.03); l.push(p - 0.03); v.push(yieldBp ? null : 1000);
  }
  today.forEach((p, k) => { ts.push(D0 + 21 * 86400 + k * 300); c.push(p); h.push(p + 0.03); l.push(p - 0.03); v.push(yieldBp ? null : vol); });
  return { meta: { gmtoffset: 0 }, timestamp: ts, indicators: { quote: [{ close: c, high: h, low: l, volume: v }] } };
}

const down = [100, 99.9, 99.8, 99.7, 99.6, 99.5, 99.4, 99.3, 99.2, 99.1, 99.0, 98.9, 98.8, 98.7];
const r = intraFrom(res(down, 2500));
assert.ok(Math.abs(r.rvol - 2.5) < 1e-9 && r.below3 && !r.above3 && r.vgap < 0);
assert.ok(r.sd15 > 0 && Math.abs(r.m60 - (98.7 / 99.9 - 1) * 100) < 1e-9 && Math.abs(r.m60 / r.sd60) > 3);
// yields: basis points, no volume pieces
const y = intraFrom(res([4.20, 4.21, 4.22, 4.23, 4.25, 4.27, 4.29, 4.31, 4.33, 4.35, 4.37, 4.39, 4.41, 4.43], 0, true), true);
assert.ok(y.rvol === undefined && y.vwap === undefined && Math.abs(y.m60 - 22) < 1e-6);
// spread: a bar whose close sits at its low then the next bar's mid jumps → positive estimate; flat → 0
const bars = Array.from({ length: 20 }, (_, i) => ({ c: i % 2 ? 100.1 : 99.9, h: 100.1, l: 99.9 }));
assert.ok(chlSpread(bars) >= 0);
assert.equal(intraFrom({ meta: {}, timestamp: [] }), null);
console.log("intra ok");
