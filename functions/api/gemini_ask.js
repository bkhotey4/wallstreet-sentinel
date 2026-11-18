// Cloudflare Pages Function: GET /api/gemini_ask → a plain-text question sheet for a Gemini app scheduled action (2026-11-18).
// The owner asked for Gemini as a second pair of eyes after a night when two stories that moved TSMC/NVIDIA never reached this
// site.  The Gemini API free tier ran out of quota, so the work goes through the Gemini app's own scheduled actions: Gemini reads
// this sheet, searches, and writes the answers into a Google Doc the bot reads back (tools/gemini_reply.py).
// Live on every request (cached 120 s): the tracked companies (/sec_watch.json, the same list as the alerts) that moved most today,
// each with the headlines this site already matched to it, or "no reason found here".  Public data only — never the holdings.
const TTL = 120, MOVE = 3.0, TOP = 12;

export function pick(q, names, news) {
  const rows = [];
  for (const [s, v] of Object.entries(q)) {
    const x = v || {}, e = x.ext || {};
    const chg = typeof e.chg === "number" ? e.chg : x.chg;
    if (typeof chg !== "number") continue;
    rows.push({ s, zh: (names[s] || [])[0] || s, en: (names[s] || [])[1] || x.name || s, chg, sess: typeof e.chg === "number" ? e.sess : "" });
  }
  rows.sort((a, b) => Math.abs(b.chg) - Math.abs(a.chg));
  const big = rows.filter((r) => Math.abs(r.chg) >= MOVE);
  const out = (big.length >= 3 ? big : rows.slice(0, 3)).slice(0, TOP);
  for (const r of out) {
    const keys = [r.s, r.zh, r.en.split(/[\s,.(]/)[0]].filter((k) => k && k.length >= 2);
    r.heads = news.filter((n) => keys.some((k) => /^[ -~]+$/.test(k)
      ? new RegExp("(^|[^A-Za-z])" + k.replace(/[^A-Za-z0-9]/g, "") + "(?![A-Za-z])", "i").test(n.t) : n.t.includes(k))).slice(0, 3);
  }
  return out;
}

export function sheet(rows, nowSec) {
  const tpe = new Date((nowSec + 8 * 3600) * 1000).toISOString().slice(0, 16).replace("T", " ");
  const L = [`WallStreet Sentinel 題目清單（台北 ${tpe}；每次打開都是即時的）`, "",
    "請針對下面每一家公司，用 Google 搜尋找出「今天股價為什麼這樣動」：",
    "1. 每一條原因都要附來源網址與發布時間（台北時間）；找不到來源就寫「找不到來源」，不要猜。",
    "2. 分清楚「已證實的事實」和「市場推測／傳聞」，傳聞要寫明是誰說的。",
    "3. 特別找：分析師調整評等或看法、供應鏈（台灣、日本、韓國）的報導、公司或主管機關公告、人事變動。",
    "4. 如果本站列的標題已經足以解釋，回「同意本站」並補充本站漏掉的。",
    "5. 最後另列：今天還有哪些會影響美股或台股、但下面沒列到的大事（附來源）。",
    "回覆格式（每家一段）：", "### 代號｜一句話原因", "- 事實：…（來源網址，時間）", "- 傳聞：…（誰說的，來源網址）", "- 本站漏掉的：…", "",
    "---- 今天的題目 ----"];
  for (const r of rows) {
    L.push("", `### ${r.s}｜${r.zh}（${r.en}）今天 ${r.chg > 0 ? "+" : ""}${r.chg.toFixed(1)}%${r.sess ? (r.sess === "pre" ? "（盤前）" : "（盤後）") : ""}`);
    if (r.heads.length) r.heads.forEach((h) => L.push(`- 本站已有：${h.t}（${h.s || ""}）${h.u || ""}`));
    else L.push("- 本站沒有找到對得上的新聞");
  }
  return L.join("\n");
}

export async function onRequestGet(ctx) {
  const base = new URL(ctx.request.url);
  const get = (p) => fetch(new URL(p, base).toString(), { signal: AbortSignal.timeout(8000) }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  const w = await get("/sec_watch.json");
  const names = (w && w.names) || {};
  const syms = Object.keys(names).filter((s) => /^[A-Z][A-Z.\-]{0,6}$/.test(s));
  const parts = [];
  for (let i = 0; i < syms.length; i += 25) parts.push(syms.slice(i, i + 25));
  const qs = await Promise.all(parts.map((p) => get("/api/quote?s=" + encodeURIComponent(p.join(",")) + "&ext=" + encodeURIComponent(p.join(",")))));
  const q = Object.assign({}, ...qs.map((x) => (x && x.q) || {}));
  const nj = await get("/api/news");
  const now = Math.floor(Date.now() / 1000);
  const body = sheet(pick(q, names, (nj && nj.items) || []), now);
  return new Response(body, { headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "public, max-age=" + TTL } });
}
