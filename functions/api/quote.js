// Cloudflare Pages Function: GET /api/quote?s=^VIX,^GSPC,...  → live quotes for the page's strip, alert lights and ticker lookup.
// Public market data only (Yahoo chart meta); no keys, no holdings. Each symbol set is cached 30 s at the edge so many viewers = one upstream call.
const OK = /^[A-Za-z0-9^=.\-]{1,15}$/;
const MAX = 25;
const TTL = 30;

function json(body, status = 200, maxAge = TTL) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${maxAge}` },
  });
}

export async function one(sym, fetchImpl = fetch) {
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=1d&interval=5m`;
  const r = await fetchImpl(url, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!r.ok) return null;
  const m = (((await r.json()).chart || {}).result || [])[0]?.meta;
  if (!m || typeof m.regularMarketPrice !== "number") return null;
  const prev = m.previousClose ?? m.chartPreviousClose;
  return {
    price: m.regularMarketPrice,
    prev: prev ?? null,
    chg: prev ? (m.regularMarketPrice / prev - 1) * 100 : null,
    t: m.regularMarketTime ?? null,
    name: m.shortName || m.longName || sym,
    cur: m.currency || "",
  };
}

export function parse(q) {
  return [...new Set((q || "").split(",").map((s) => s.trim().toUpperCase()).filter((s) => OK.test(s)))].slice(0, MAX);
}

export async function onRequestGet({ request, waitUntil }) {
  const syms = parse(new URL(request.url).searchParams.get("s"));
  if (!syms.length) return json({ error: "no symbols" }, 400, 0);
  const cache = typeof caches !== "undefined" ? caches.default : null;
  const key = new Request(`https://quote.cache/${syms.slice().sort().join(",")}`);
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  const out = {};
  await Promise.all(syms.map(async (s) => {
    try {
      const q = await one(s);
      if (q) out[s] = q;
    } catch (e) { /* one bad symbol never breaks the rest */ }
  }));
  // unknown tickers just come back missing from q (200), so the page can say "not found" instead of "source down"
  const n = Object.keys(out).length;
  const res = json({ ts: Math.floor(Date.now() / 1000), q: out }, 200, n ? TTL : 0);
  if (cache && n) {
    const put = cache.put(key, res.clone());
    if (waitUntil) waitUntil(put); else await put;
  }
  return res;
}
