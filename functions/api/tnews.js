// Cloudflare Pages Function: GET /api/tnews?s=NVDA,TSM → each ticker's own headlines of the last 24 h (Yahoo Finance per-ticker RSS).
// Added 2026-11-18 for the 我的持股 tab's 「今天為什麼動」: the page asks only for the tickers the visitor typed in their own browser,
// the same way it already asks /api/quote; nothing is stored here, the answer is cached 300 s at the edge per ticker.
// Analyst notes (price target / upgrade / downgrade / rating) are flagged so the page can mark them.
const TTL = 300, MAX = 15, HOURS = 24;
export const ANALYST = /price target|downgrade|upgrade|initiat\w* coverage|\bPT\b|rating/i;
const unesc = (x) => x.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/<[^>]+>/g, "")
  .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n)).replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();

export function parseYahoo(xml, nowSec) {
  const out = [];
  for (const m of xml.matchAll(/<item>([\s\S]*?)<\/item>/g)) {
    const g = (tg) => { const x = m[1].match(new RegExp("<" + tg + "[^>]*>([\\s\\S]*?)</" + tg + ">")); return x ? unesc(x[1]) : ""; };
    const t = g("title"), u = g("link").replace(/^http:\/\//, "https://"), d = Date.parse(g("pubDate"));
    if (!t || !/^https:\/\//.test(u) || !d) continue;
    const ts = Math.floor(d / 1000);
    if (nowSec - ts > HOURS * 3600 || ts > nowSec + 600) continue;
    out.push({ t, u, ts, a: ANALYST.test(t) });
  }
  return out.sort((a, b) => b.ts - a.ts).slice(0, 8);
}

export async function onRequestGet(ctx) {
  const url = new URL(ctx.request.url);
  const syms = [...new Set((url.searchParams.get("s") || "").toUpperCase().split(",").map((s) => s.trim())
    .filter((s) => /^[A-Z][A-Z0-9.\-]{0,9}$/.test(s)))].slice(0, MAX);
  const now = Math.floor(Date.now() / 1000);
  const res = await Promise.all(syms.map(async (s) => {
    try {
      const r = await fetch("https://feeds.finance.yahoo.com/rss/2.0/headline?s=" + encodeURIComponent(s) + "&region=US&lang=en-US",
        { headers: { "user-agent": "Mozilla/5.0 (WallStreet Sentinel news)" }, cf: { cacheTtl: TTL }, signal: AbortSignal.timeout(6000) });
      return [s, r.ok ? parseYahoo(await r.text(), now) : []];
    } catch (e) { return [s, []]; }
  }));
  return new Response(JSON.stringify({ ts: now, n: Object.fromEntries(res) }), {
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=" + TTL },
  });
}
