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

// ---- 2026-11-14: more 8-K items, Schedule 13D, and "several newsrooms at once"
import { parse13d, bursts, sigs, matcher, parse, tag, SEV } from "../functions/api/news.js";
const e2 = (items, upd) => `<entry><title>8-K - NVIDIA CORP (0001045810) (Filer)</title>
<link rel="alternate" type="text/html" href="https://www.sec.gov/Archives/edgar/data/1045810/y/y-index.htm"/>
<summary type="html">${items.map((i) => "&lt;br&gt;Item " + i + ": x").join("")}</summary><updated>${upd}</updated></entry>`;
const more = parseSec("<feed>" + e2(["2.01", "2.05", "9.01"], "2026-11-12T09:00:00-05:00") + e2(["5.02", "2.01"], "2026-11-12T09:01:00-05:00")
  + e2(["1.01", "9.01"], "2026-11-12T09:02:00-05:00") + "</feed>", { "1045810": ["NVDA", "輝達"] });
assert.equal(more.length, 2);                                     // 1.01 alone is not an alert
assert.ok(more[0].t.includes("裁員或關廠重整") && more[0].item === "2.05" && more[0].sev === 3);   // the louder of two items
assert.ok(more[1].item === "2.01" && more[1].sev === SEV["2.01"]);                              // a rare item beats 5.02
const d13 = (form, name, cik, role, acc) => `<entry><title>SCHEDULE ${form} - ${name} (${String(cik).padStart(10, "0")}) (${role})</title>
<link rel="alternate" type="text/html" href="https://www.sec.gov/Archives/edgar/data/${cik}/${acc}-index.htm"/>
<summary type="html"> &lt;b&gt;Filed:&lt;/b&gt; 2026-11-13</summary><updated>2026-11-13T21:30:46-05:00</updated>
<id>urn:tag:sec.gov,2008:accession-number=${acc}</id></entry>`;
const x13 = parse13d("<feed>" + d13("13D", "ICAHN CARL C", 921669, "Filed by", "0001-26-1") + d13("13D", "NVIDIA CORP", 1045810, "Subject", "0001-26-1")
  + d13("13D/A", "NVIDIA CORP", 1045810, "Subject", "0002-26-2") + d13("13D/A", "SOMEONE LP", 5, "Filed by", "0002-26-2")
  + d13("13D", "SMALL CO", 99, "Subject", "0003-26-3") + "</feed>", { "1045810": ["NVDA", "輝達"] });
assert.equal(x13.length, 2);
assert.equal(x13[0].t, "SEC 申報：ICAHN CARL C 申報持有 輝達（NVDA）逾 5% 股權，不排除介入經營（Schedule 13D）");
assert.ok(x13[0].alert && x13[0].sev === 3 && x13[0].u.includes("/1045810/"));
assert.ok(!x13[1].alert && x13[1].item === "13D/A" && x13[1].t.includes("SOMEONE LP 更新"));   // an update is listed, not pinned

// tags: one regex per tag behaves like the old keyword list
assert.deepEqual(tag("Fed said AI chips"), ["利率", "科技"]);
assert.deepEqual(tag("He said paid"), []);
// a business desk keeps untagged headlines for counting only; a general feed drops them
const rss = (t) => `<rss><item><title>${t}</title><link>https://x.test/a</link><pubDate>Thu, 12 Nov 2026 14:00:00 GMT</pubDate></item></rss>`;
assert.equal(parse(rss("Boeing names new finance chief"), { s: "A", o: "a", lang: "en" }).length, 0);
const q = parse(rss("Boeing names new finance chief"), { s: "A", o: "a", lang: "en", biz: true });
assert.ok(q.length === 1 && q[0].q === true && q[0].o === "a");
assert.equal(merge([q], q[0].ts + 60).length, 0);

const NAMES = { NVDA: ["輝達", "Nvidia"], META: ["", "Meta|Facebook"], TSM: ["台積電", "TSMC"] };
const mm = matcher(NAMES);
assert.deepEqual(sigs("輝達執行長黃仁勳辭職", mm).sort(), ["co:NVDA"]);          // one topic alone is not a pair
assert.deepEqual(sigs("Nvidia CEO Huang resigns; Metals rally", mm), ["co:NVDA"]);  // "Metals" is not Meta
assert.ok(sigs("Iran fires missiles at Israel, oil jumps", mm).includes("攻擊+伊朗") && sigs("Iran fires missiles at Israel", mm).includes("攻擊+以色列"));
assert.deepEqual(sigs("Fed officials see Treasury yields rising", mm), []);         // who + which market, nothing happened
const T0 = 1794500000;
const it = (t, o, min, lang) => ({ t, u: "https://x.test/" + o + min, s: o.toUpperCase(), o, ts: T0 + min * 60, lang: lang || "en", tags: tag(t) });
const LAB = { NVDA: "輝達" };
// two newsrooms within 45 minutes on a quiet name → a company burst; one newsroom twice is not
let bs = bursts([it("Nvidia CEO Huang resigns", "cnbc", 0), it("輝達執行長黃仁勳辭職", "cna", 20, "zh")], T0 + 30 * 60, NAMES, LAB);
assert.equal(bs.length, 1);
assert.ok(bs[0].key === "co:NVDA" && bs[0].label === "輝達（NVDA）" && bs[0].n === 2 && bs[0].first === T0 && bs[0].items[0].lang === "zh");
assert.equal(bursts([it("Nvidia CEO Huang resigns", "cnbc", 0), it("Nvidia shares fall", "cnbc", 20)], T0 + 30 * 60, NAMES, LAB).length, 0);
assert.equal(bursts([it("Nvidia CEO Huang resigns", "cnbc", 0), it("Nvidia board meets", "wsj", 60)], T0 + 70 * 60, NAMES, LAB).length, 0);   // 60 minutes apart
// a name already carried by two newsrooms in the hours before needs twice that
const busy = [it("Nvidia unveils chip", "cnbc", -200), it("Nvidia unveils new chip", "mw", -190)];
assert.equal(bursts(busy.concat([it("Nvidia CEO Huang resigns", "cnbc", 0), it("輝達執行長辭職", "cna", 10, "zh"), it("Nvidia chief quits", "wsj", 15)]), T0 + 20 * 60, NAMES, LAB).length, 0);
bs = bursts(busy.concat([it("Nvidia CEO Huang resigns", "cnbc", 0), it("輝達執行長辭職", "cna", 10, "zh"), it("Nvidia chief quits", "wsj", 15), it("Nvidia's Huang out", "bbg", 18)]),
  T0 + 20 * 60, NAMES, LAB);
assert.ok(bs.length === 1 && bs[0].n === 4 && bs[0].base === 2);
// it stays listed (anchored at the first 45 minutes) while more newsrooms follow, and drops out after 3 hours
bs = bursts([it("Nvidia CEO Huang resigns", "cnbc", 0), it("輝達執行長辭職", "cna", 10, "zh"), it("Nvidia after Huang", "ft", 100)], T0 + 110 * 60, NAMES, LAB);
assert.ok(bs.length === 1 && bs[0].first === T0 && bs[0].n === 3 && bs[0].mins === 100);
assert.equal(bursts([it("Nvidia CEO Huang resigns", "cnbc", 0), it("輝達執行長辭職", "cna", 10, "zh")], T0 + 200 * 60, NAMES, LAB).length, 0);
// an event needs three newsrooms; the same three headlines light several pairs but give one burst
const war = [it("Iran fires missiles at Israel", "cnbc", 0), it("伊朗向以色列發射飛彈", "cna", 5, "zh"), it("Israel says Iran missile attack under way", "bbc", 12)];
assert.equal(bursts(war.slice(0, 2), T0 + 15 * 60, NAMES, LAB).length, 0);
bs = bursts(war, T0 + 15 * 60, NAMES, LAB);
assert.ok(bs.length === 1 && bs[0].kind === "topic" && bs[0].n === 3 && bs[0].tags.includes("地緣"), JSON.stringify(bs));
console.log("news tests 2 ok");
