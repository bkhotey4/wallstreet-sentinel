// Cloudflare Pages Function: GET /api/quote?s=^VIX,^GSPC,...  → live quotes for the page's strip, alert lights and ticker lookup.
// Add &full=1 for one year of daily data per symbol: 52-week high/low, dividends paid in the last 12 months, 200-day average,
// RSI(14) and recent volatility (portfolio dividend box, drawdown column, the browser-side watchlist).
// Add &vol=SPY,QQQ for those symbols' volume today vs the average of the previous days up to the same time (5-minute bars,
// 5 days): the live "heavy selling" light.
// Add &ext=NVDA,TSM for the pre-market / after-hours price of those symbols (US listings): ext = {px, chg vs the last
// regular close, sess "pre" | "post", t}.  Absent while the regular session is trading or when there is no extended trade.
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

export function sdAll(c) {
  const r = [];
  for (let i = 1; i < c.length; i++) r.push((c[i] / c[i - 1] - 1) * 100);
  if (r.length < 60) return null;
  const m = r.reduce((a, b) => a + b, 0) / r.length;
  return Math.sqrt(r.reduce((a, b) => a + (b - m) ** 2, 0) / (r.length - 1));
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
    sd1y: sdAll(c.slice(-253)),                                         // one-year std of daily % change (live unusual-move scan)
    m1: sd != null ? [last * Math.exp(-sd * Math.sqrt(21)), last * Math.exp(sd * Math.sqrt(21))] : null,   // ±1σ over ~1 month
    div12,
  };
}

// today's cumulative volume ÷ the average cumulative volume of earlier days up to the same exchange-local time of day
export function volRatio(ts, vols, closes, off) {
  const day = (s) => Math.floor((s + off) / 86400), tod = (s) => (s + off) % 86400;
  const byDay = new Map();
  for (let i = 0; i < ts.length; i++) {
    if (ts[i] == null) continue;
    const d = day(ts[i]);
    if (!byDay.has(d)) byDay.set(d, []);
    byDay.get(d).push([tod(ts[i]), typeof vols[i] === "number" ? vols[i] : 0, closes[i]]);
  }
  const days = [...byDay.keys()].sort((a, b) => a - b);
  if (days.length < 3) return {};
  const today = byDay.get(days[days.length - 1]), cut = today[today.length - 1][0];
  const cum = (bars) => bars.filter((b) => b[0] <= cut).reduce((a, b) => a + b[1], 0);
  const past = days.slice(0, -1).map((d) => cum(byDay.get(d))).filter((v) => v > 0);
  const prevBars = byDay.get(days[days.length - 2]).filter((b) => typeof b[2] === "number");
  const out = { prevDay: prevBars.length ? prevBars[prevBars.length - 1][2] : null };
  if (past.length >= 2) {
    const avg = past.reduce((a, b) => a + b, 0) / past.length;
    out.vol = cum(today);
    out.volx = avg ? out.vol / avg : null;
  }
  return out;
}

// first trade of the latest exchange-local day in the 5-minute bars (the session's opening price; null if none yet)
export function todayOpen(res) {
  const ts = res.timestamp || [], o = ((((res.indicators || {}).quote || [])[0]) || {}).open || [], off = (res.meta || {}).gmtoffset || 0;
  if (!ts.length) return null;
  const day = (s) => Math.floor((s + off) / 86400), last = day(ts[ts.length - 1]);
  for (let i = 0; i < ts.length; i++) if (day(ts[i]) === last && typeof o[i] === "number") return o[i];
  return null;
}

export async function one(sym, fetchImpl = fetch, full = false, vol = false) {
  const q = full ? "range=1y&interval=1d&events=div" : vol ? "range=5d&interval=5m" : "range=1d&interval=5m";
  const r = await fetchImpl(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?${q}`, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!r.ok) return null;
  const res = (((await r.json()).chart || {}).result || [])[0];
  const m = res?.meta;
  if (!m || typeof m.regularMarketPrice !== "number") return null;
  let prev = m.previousClose ?? m.chartPreviousClose;
  const out = { name: m.shortName || m.longName || sym, cur: m.currency || "", t: m.regularMarketTime ?? null, price: m.regularMarketPrice };
  if (!full) out.open = todayOpen(res);
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
  if (vol && !full) {
    const qd = ((res.indicators || {}).quote || [])[0] || {};
    const v = volRatio(res.timestamp || [], qd.volume || [], qd.close || [], m.gmtoffset || 0);
    prev = m.previousClose ?? v.prevDay ?? null;                      // with range=5d, chartPreviousClose is 5 days old
    if (v.volx != null) { out.vol = v.vol; out.volx = v.volx; }
  }
  out.prev = prev ?? null;
  out.chg = prev ? (out.price / prev - 1) * 100 : null;
  return out;
}

// last extended-hours trade in a 1-day, 5-minute, includePrePost chart (null inside the regular session or without one)
export function extFrom(res) {
  const m = res?.meta, reg = m?.currentTradingPeriod?.regular;
  if (!m || typeof m.regularMarketPrice !== "number" || !reg) return null;
  const ts = res.timestamp || [], c = ((((res.indicators || {}).quote || [])[0]) || {}).close || [];
  for (let i = ts.length - 1; i >= 0; i--) {
    if (typeof c[i] !== "number" || ts[i] == null) continue;
    const sess = ts[i] >= reg.end ? "post" : ts[i] < reg.start ? "pre" : null;
    if (!sess) return null;                                           // latest trade is a regular-session one
    return { px: c[i], chg: (c[i] / m.regularMarketPrice - 1) * 100, sess, t: ts[i], base: m.regularMarketPrice };
  }
  return null;
}

export async function ext(sym, fetchImpl = fetch) {
  const r = await fetchImpl(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=1d&interval=5m&includePrePost=true`, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!r.ok) return null;
  return extFrom((((await r.json()).chart || {}).result || [])[0]);
}

export function parse(q) {
  return [...new Set((q || "").split(",").map((s) => s.trim().toUpperCase()).filter((s) => OK.test(s)))].slice(0, MAX);
}

export async function onRequestGet({ request, waitUntil }) {
  const u = new URL(request.url);
  const syms = parse(u.searchParams.get("s"));
  const full = u.searchParams.get("full") === "1";
  const vols = new Set(parse(u.searchParams.get("vol")));
  const exts = new Set(parse(u.searchParams.get("ext")));
  if (!syms.length) return json({ error: "no symbols" }, 400, 0);
  const cache = typeof caches !== "undefined" ? caches.default : null;
  const key = new Request(`https://quote.cache/${full ? "f/" : ""}${syms.slice().sort().join(",")}${vols.size ? "/v/" + [...vols].sort().join(",") : ""}${exts.size ? "/e/" + [...exts].sort().join(",") : ""}`);
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  const out = {};
  await Promise.all(syms.map(async (s) => {
    try {
      const [q, e] = await Promise.all([one(s, fetch, full, vols.has(s)), exts.has(s) && !full ? ext(s).catch(() => null) : null]);
      if (q) out[s] = e ? { ...q, ext: e } : q;
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
