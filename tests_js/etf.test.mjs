// node tests_js/etf.test.mjs — parser checks for /api/etf
import assert from "node:assert/strict";
import { parse } from "../functions/api/etf.js";
const rows = parse({ a1: [{ msgArray: [
  { a: "00999A", b: "主動野村臺灣高息", c: "997,017,000", d: "0", e: "10.48", f: "10.46", g: "0.19", i: "20261027", j: "13:31:00" },
  { a: "00X", b: "某基金(原名)", c: 5, d: 0, e: 10, f: 0, g: "4" }] }] });
assert.equal(rows.length, 2);
assert.deepEqual(rows[0].slice(0, 8), ["00999A", "主動野村臺灣高息", 997017000, 0, 10.48, 10.46, 0.19, "2026-10-27"]);
assert.equal(rows[1][1], "某基金"); assert.equal(rows[1][6], null);       // no NAV → premium unknown
console.log("etf tests ok");
