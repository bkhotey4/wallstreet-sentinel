// Cloudflare Pages Function: GET /api/quote?s=^VIX,^GSPC,...  → live quotes for the page's strip, alert lights and ticker lookup.
// Add &full=1 for one year of daily data per symbol: 52-week high/low, dividends paid in the last 12 months, 200-day average,
// RSI(14) and recent volatility (portfolio dividend box, drawdown column, the browser-side watchlist).
// Public market data only (Yahoo chart); no keys, nothing stored. Each symbol set is cached 30 s (full: 10 min) at the edge.
const OK = /^[A-Za-z0-9^=.\-]{1,15}$/;
const MAX = 25;
const TTL = 30;
const TTL_FULL = 600;

function json(body, status = 200, maxAge = TTL) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${maxAge}` },
  });
}

export function rsi(closes, n = 14) {
  if (closes.length <= n) return null;
  let up = 0, dn = 0;
  for (let i = 1; i <= n; i++) {
    const d = closes[i] - closes[i - 1];
    if (d > 0) up += d; else dn -= d;
  }
  up /= n; dn /= n;
  for (let i = n + 1; i < closes.length; i++) {                     // Wilder smoothing
    const d = closes[i] - closes[i - 1];
    up = (up * (n - 1) + Math.max(d, 0)) / n;
    dn = (dn * (n - 1) + Math.max(-d, 0)) / n;
  }
  return dn === 0 ? 100 : 100 - 100 / (1 + up / dn);
}

export function tech(closes, divs, nowSec) {
  const c = closes.filter((x) => typeof x === "number" && x > 0);
  if (c.length < 2) return {};
  const last = c[c.length - 1];
  const ma200 = c.length >= 200 ? c.slice(-200).reduce((a, b) => a + b, 0) / 200 : null;
  const r = [];
  for (let i = Math.max(1, c.length - 20); i < c.length; i++) r.push(Math.log(c[i] / c[i - 1]));
  const mean = r.reduce((a, b) => a + b, 0) / (r.length || 1);
  const sd = r.length > 2 ? Math.sqrt(r.reduce((a, b) => a + (b - mean) ** 2, 0) / (r.length - 1)) : null;
  const yearAgo = nowSec - 365 * 86400;
  const div12 = Object.values(divs || {}).filter((d) => d && d.date >= yearAgo).reduce((a, d) => a + (d.amount || 0), 0);
  return {
    hi52: Math.max(...c.slice(-252)), lo52: Math.min(...c.slice(-252)),
    ma200, ma_gap: ma200 ? (last / ma200 - 1) * 100 : null, rsi14: rsi(c),
    vol20: sd != null ? sd * Math.sqrt(252) * 100 : null,                // annualised, %
    m1: sd != null ? [last * Math.exp(-sd * Math.sqrt(21)), last * Math.exp(sd * Math.sqrt(21))] : null,   // ±1σ over ~1 month
    div12,
  };
}

export async function one(sym, fetchImpl = fetch, full = false) {
  const q = full ? "range=1y&interval=1d&events=div" : "range=1d&interval=5m";
  const r = await fetchImpl(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?${q}`, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!r.ok) return null;
  const res = (((await r.json()).chart || {}).result || [])[0];
  const m = res?.meta;
  if (!m || typeof m.regularMarketPrice !== "number") return null;
  let prev = m.previousClose ?? m.chartPreviousClose;
  const out = { name: m.shortName || m.longName || sym, cur: m.currency || "", t: m.regularMarketTime ?? null, price: m.regularMarketPrice };
  if (full) {
    const closes = (((res.indicators || {}).quote || [])[0] || {}).close || [];
    // previous close = last daily bar from an earlier exchange-local day than the latest trade (chartPreviousClose is a year ago)
    const ts = res.timestamp || [], off = m.gmtoffset || 0, day = (s) => Math.floor((s + off) / 86400);
    const today = day(m.regularMarketTime || ts[ts.length - 1] || 0);
    prev = null;
    for (let i = closes.length - 1; i >= 0; i--) {
      if (typeof closes[i] === "number" && ts[i] != null && day(ts[i]) < today) { prev = closes[i]; break; }
    }
    Object.assign(out, tech(closes, (res.events || {}).dividends, Math.floor(Date.now() / 1000)));
  }
  out.prev = prev ?? null;
  out.chg = prev ? (out.price / prev - 1) * 100 : null;
  return out;
}

export function parse(q) {
  return [...new Set((q || "").split(",").map((s) => s.trim().toUpperCase()).filter((s) => OK.test(s)))].slice(0, MAX);
}

export async function onRequestGet({ request, waitUntil }) {
  const u = new URL(request.url);
  const syms = parse(u.searchParams.get("s"));
  const full = u.searchParams.get("full") === "1";
  if (!syms.length) return json({ error: "no symbols" }, 400, 0);
  const cache = typeof caches !== "undefined" ? caches.default : null;
  const key = new Request(`https://quote.cache/${full ? "f/" : ""}${syms.slice().sort().join(",")}`);
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  const out = {};
  await Promise.all(syms.map(async (s) => {
    try {
      const q = await one(s, fetch, full);
      if (q) out[s] = q;
    } catch (e) { /* one bad symbol never breaks the rest */ }
  }));
  // unknown tickers just come back missing from q (200), so the page can say "not found" instead of "source down"
  const n = Object.keys(out).length;
  const res = json({ ts: Math.floor(Date.now() / 1000), q: out }, 200, n ? (full ? TTL_FULL : TTL) : 0);
  if (cache && n) {
    const put = cache.put(key, res.clone());
    if (waitUntil) waitUntil(put); else await put;
  }
  return res;
}
