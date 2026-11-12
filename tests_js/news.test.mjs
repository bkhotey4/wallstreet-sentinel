// node tests_js/news.test.mjs — SEC officer-filing alerts in /api/news
import assert from "node:assert/strict";
import { parseSec, kind, mainDoc, merge } from "../functions/api/news.js";
const entry = (name, cik, item, upd) => `<entry>
<title>8-K - ${name} (${String(cik).padStart(10, "0")}) (Filer)</title>
<link rel="alternate" type="text/html" href="https://www.sec.gov/Archives/edgar/data/${cik}/x/x-index.htm"/>
<summary type="html"> &lt;b&gt;Filed:&lt;/b&gt; 2026-11-12
&lt;br&gt;Item ${item}: Departure of Directors or Certain Officers
&lt;br&gt;Item 9.01: Financial Statements and Exhibits</summary>
<updated>${upd}</updated></entry>`;
const xml = "<feed>" + entry("NVIDIA CORP", 1045810, "5.02", "2026-11-12T08:52:41-05:00") + entry("SMALL CO", 99, "5.02", "2026-11-12T08:50:00-05:00")
  + entry("NVIDIA CORP", 1045810, "7.01", "2026-11-12T08:40:00-05:00") + "</feed>";
const items = parseSec(xml, { "1045810": ["NVDA", "輝達"] });
assert.equal(items.length, 1);                                    // untracked company and other items are skipped
assert.equal(items[0].t, "SEC 申報：輝達（NVDA）高層人事異動（8-K 第 5.02 項）");
assert.equal(items[0].ts, 1794491561); assert.ok(items[0].alert && items[0].off);
const H = "Item 5.02. Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers. ";
assert.deepEqual(kind(H + "On November 11, 2026, the Board accepted the resignation of Jen-Hsun Huang, as President, Chief Executive Officer and member of the Board."),
  { what: "離職", seat: "執行長" });
// three new directors whose biographies mention past CEO jobs: still a board appointment, and the heading's "Departure" is ignored
assert.deepEqual(kind(H + "On November 11, 2026 the Board approved the appointments of A, B and C to the Board. Ms. A was Chief Executive Officer of X."),
  { what: "任命", seat: "董事" });
assert.equal(mainDoc('<tr><td>1</td><td>8-K</td><td><a href="/ix?doc=/Archives/edgar/data/1/2/a-8k.htm">a</a></td></tr>'
  + '<tr><td>2</td><td>EX-99.1</td><td><a href="/Archives/edgar/data/1/2/pr.htm">pr</a></td></tr>'), "/Archives/edgar/data/1/2/a-8k.htm");
assert.deepEqual(kind("Item 5.02 The Board appointed Jane Roe as Chief Financial Officer."), { what: "任命", seat: "財務長" });
// a busy news day never pushes an alert out, and alerts live 72 h
const now = 1794491561 + 3600;
const news = Array.from({ length: 80 }, (_, i) => ({ t: "headline " + i, u: "https://x/" + i, s: "CNBC", ts: now - i * 60, tags: [] }));
const old = { ...items[0], ts: now - 50 * 3600, u: "https://www.sec.gov/old" };
const m = merge([news, items, [old]], now);
assert.equal(m.length, 60);
assert.ok(m.some((x) => x.alert && x.u === items[0].u) && m.some((x) => x.u === "https://www.sec.gov/old"));
assert.ok(m.every((x, i) => i === 0 || m[i - 1].ts >= x.ts));
console.log("news tests ok");
