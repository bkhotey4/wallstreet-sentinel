// Cloudflare Pages Function: GET /api/quote?s=^VIX,^GSPC,...  → live quotes for the page's strip, alert lights and ticker lookup.
// Add &full=1 for one year of daily data per symbol: 52-week high/low, dividends paid in the last 12 months, 200-day average,
// RSI(14) and recent volatility (portfolio dividend box, drawdown column, the browser-side watchlist).
// Add &vol=SPY,QQQ for those symbols' volume today vs the average of the previous days up to the same time (5-minute bars,
// 5 days): the live "heavy selling" light.
// Add &ext=NVDA,TSM for the pre-market / after-hours price of those symbols (US listings): ext = {px, chg vs the last
// regular close, sess "pre" | "post", t}.  Absent while the regular session is trading or when there is no extended trade.
// Add &iv=HYG,^TNX for an intraday picture from one month of 5-minute bars (see intraFrom): same-time relative volume,
// VWAP and the last three bars against it, 15 / 60-minute moves vs their own history, a close-high-low spread estimate.
// Add &hist=1 for five years of weekly closes and every cash dividend (w = [[date, close]], dv = [[date, amount]]): the ETF
// look-back calculator.  A one-week move of −40 % or +100 % within 5 % of a whole-number ratio is treated as a split Yahoo
// missed and earlier closes are rescaled (Taiwan ETF splits are often not recorded).
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

// the fastest 15-minute move (3 five-minute bars) of the latest exchange-local day: when the day's big swing happened
// ({t: unix end of the window, chg: %}), so the page can line headlines up with it
export function jumpOf(ts, closes, off) {
  if (!ts.length) return null;
  const day = (s) => Math.floor((s + off) / 86400), last = day(ts[ts.length - 1]);
  const pts = [];
  for (let i = 0; i < ts.length; i++) if (ts[i] != null && day(ts[i]) === last && typeof closes[i] === "number") pts.push([ts[i], closes[i]]);
  let best = null;
  for (let i = 3; i < pts.length; i++) {
    const c = (pts[i][1] / pts[i - 3][1] - 1) * 100;
    if (!best || Math.abs(c) > Math.abs(best.chg)) best = { t: pts[i][0], chg: c };
  }
  return best;
}

const median = (a) => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y), k = s.length >> 1; return s.length % 2 ? s[k] : (s[k - 1] + s[k]) / 2; };
const sdOf = (a) => { if (a.length < 30) return null; const m = a.reduce((x, y) => x + y, 0) / a.length; return Math.sqrt(a.reduce((x, y) => x + (y - m) ** 2, 0) / (a.length - 1)); };

// Abdi & Ranaldo (2017) close-high-low spread estimate for one day of 5-minute bars, in basis points (a stand-in: free
// data has no bid/ask).  s² = 4·mean[(c_t − η_t)(c_t − η_t+1)], η = mid of log high and log low; negative → 0
export function chlSpread(bars) {
  const p = [];
  for (let i = 0; i + 1 < bars.length; i++) {
    const a = bars[i], b = bars[i + 1];
    if (!(a.h > 0 && a.l > 0 && a.c > 0 && b.h > 0 && b.l > 0)) continue;
    const c = Math.log(a.c), e0 = (Math.log(a.h) + Math.log(a.l)) / 2, e1 = (Math.log(b.h) + Math.log(b.l)) / 2;
    p.push((c - e0) * (c - e1));
  }
  if (p.length < 6) return null;
  const s2 = 4 * p.reduce((x, y) => x + y, 0) / p.length;
  return Math.sqrt(Math.max(s2, 0)) * 1e4;
}

// one month of regular-session 5-minute bars → today's intraday picture, each piece against the same stock's own history:
//   rvol   volume so far ÷ the median volume of the previous (≤ 20) days up to the same time of day
//   vwap   Σ(typical price × volume) / Σ volume today; vgap = last vs vwap (%); below3 / above3 = the last three COMPLETED bars
//          all closed below / above the running vwap (the newest bar is still forming)
//   m15 / m60  the last 15 / 60 minutes (% for prices, basis points for yields), sd15 / sd60 the spread of that window on
//          earlier days (non-overlapping), so the page can say "x times its normal 15-minute move"
//   spr    today's close-high-low spread estimate (bp); sprx = ÷ median of earlier days, sprp = share of earlier days below it
export function intraFrom(res, yieldBp = false) {
  const m = res?.meta, ts = res?.timestamp || [];
  if (!m || ts.length < 50) return null;
  const qd = ((res.indicators || {}).quote || [])[0] || {}, off = m.gmtoffset || 0;
  const day = (s) => Math.floor((s + off) / 86400), tod = (s) => (s + off) % 86400;
  const byDay = new Map();
  for (let i = 0; i < ts.length; i++) {
    const c = qd.close?.[i];
    if (ts[i] == null || typeof c !== "number") continue;
    const d = day(ts[i]);
    if (!byDay.has(d)) byDay.set(d, []);
    byDay.get(d).push({ t: ts[i], k: tod(ts[i]), c, h: qd.high?.[i], l: qd.low?.[i], v: typeof qd.volume?.[i] === "number" ? qd.volume[i] : 0 });
  }
  const days = [...byDay.keys()].sort((a, b) => a - b);
  if (days.length < 6) return null;
  const today = byDay.get(days[days.length - 1]), past = days.slice(0, -1).slice(-20).map((d) => byDay.get(d));
  const cut = today[today.length - 1].k, out = { t: today[today.length - 1].t, n_days: past.length, bars: today.length };
  const mv = (a, b) => (yieldBp ? (a - b) * 100 : (a / b - 1) * 100);
  const vol = (bars) => bars.filter((b) => b.k <= cut).reduce((a, b) => a + b.v, 0);
  const pv = past.map(vol).filter((v) => v > 0), vt = vol(today);
  if (!yieldBp && pv.length >= 5 && vt > 0) out.rvol = vt / median(pv);
  if (!yieldBp && vt > 0) {
    let pvSum = 0, vSum = 0;
    const run = today.map((b) => { const tp = b.h > 0 && b.l > 0 ? (b.h + b.l + b.c) / 3 : b.c; pvSum += tp * b.v; vSum += b.v; return vSum ? pvSum / vSum : null; });
    out.vwap = run[run.length - 1];
    if (out.vwap) out.vgap = (today[today.length - 1].c / out.vwap - 1) * 100;
    if (today.length >= 5) {
      const done = [1, 2, 3].map((j) => today.length - 1 - j);              // the three bars before the forming one
      out.below3 = done.every((i) => run[i] && today[i].c < run[i]);
      out.above3 = done.every((i) => run[i] && today[i].c > run[i]);
      out.was_below = today.slice(0, -4).some((b, i) => run[i] && b.c < run[i]);   // earlier today it traded under vwap
    }
  }
  const last = today[today.length - 1].c;
  if (today.length > 3) out.m15 = mv(last, today[today.length - 4].c);
  if (today.length > 12) out.m60 = mv(last, today[today.length - 13].c);
  const w15 = [], w60 = [];
  past.forEach((bars) => { for (let i = 3; i < bars.length; i += 3) w15.push(mv(bars[i].c, bars[i - 3].c)); for (let i = 12; i < bars.length; i += 12) w60.push(mv(bars[i].c, bars[i - 12].c)); });
  out.sd15 = sdOf(w15); out.sd60 = sdOf(w60);
  if (!yieldBp) {
    const sp = chlSpread(today.slice(0, -1)), ps = past.map((b) => chlSpread(b)).filter((x) => x != null);
    if (sp != null && ps.length >= 10) { out.spr = sp; const md = median(ps); out.sprx = md ? sp / md : null; out.sprp = ps.filter((x) => x < sp).length / ps.length; }
  }
  return out;
}

export async function intra(sym, fetchImpl = fetch) {
  const r = await fetchImpl(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=1mo&interval=5m`, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!r.ok) return null;
  return intraFrom((((await r.json()).chart || {}).result || [])[0], /^\^(IRX|FVX|TNX|TYX)$/.test(sym));
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
    const past = [];                                                    // closes of earlier days, newest first
    const vols = (((res.indicators || {}).quote || [])[0] || {}).volume || [];
    const tw = /.TWO?$/.test(sym);                                     // Yahoo copies the last close onto Taiwan holidays (volume 0)
    for (let i = closes.length - 1; i >= 0; i--) {
      if (tw && vols[i] === 0) continue;
      if (typeof closes[i] === "number" && ts[i] != null && day(ts[i]) < today) past.push(closes[i]);
    }
    prev = past.length ? past[0] : null;
    // the trend up to yesterday's close: yesterday, the day before, 5 and 20 sessions earlier (the page compares today with it)
    if (past.length > 20) out.trend = { p0: past[0], p1: past[1], p5: past[5], p20: past[20] };
    Object.assign(out, tech(closes, (res.events || {}).dividends, Math.floor(Date.now() / 1000)));
  }
  if (vol && !full) {
    const qd = ((res.indicators || {}).quote || [])[0] || {};
    const v = volRatio(res.timestamp || [], qd.volume || [], qd.close || [], m.gmtoffset || 0);
    prev = m.previousClose ?? v.prevDay ?? null;                      // with range=5d, chartPreviousClose is 5 days old
    if (v.volx != null) { out.vol = v.vol; out.volx = v.volx; }
    const j = jumpOf(res.timestamp || [], qd.close || [], m.gmtoffset || 0);
    if (j) out.jump = j;
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

export function fixSplits(w, divDays = new Set()) {
  const out = w.map((x) => [x[0], x[1]]);
  for (let i = 1; i < out.length; i++) {
    const a = out[i - 1][1], b = out[i][1];
    if (!a || !b || divDays.has(out[i][0])) continue;
    const k = b < a ? a / b : b / a, r = Math.round(k);
    if ((b / a <= 0.6 || b / a >= 2) && r >= 2 && Math.abs(k / r - 1) <= 0.05) {
      const f = b < a ? r : 1 / r;
      for (let j = 0; j < i; j++) out[j][1] = Math.round((out[j][1] / f) * 1e4) / 1e4;
    }
  }
  return out;
}

export function histFrom(res) {
  const m = res?.meta;
  if (!m) return null;
  const off = m.gmtoffset || 0, d = (t) => new Date((t + off) * 1000).toISOString().slice(0, 10);
  const ts = res.timestamp || [], c = ((((res.indicators || {}).quote || [])[0]) || {}).close || [];
  const dv = Object.values((res.events || {}).dividends || {}).filter((x) => x && x.amount).map((x) => [d(x.date), x.amount]).sort();
  const w = [];
  for (let i = 0; i < ts.length; i++) if (typeof c[i] === "number" && ts[i] != null) w.push([d(ts[i]), Math.round(c[i] * 1e4) / 1e4]);
  if (w.length < 5) return null;
  return { name: m.shortName || m.longName || "", w: fixSplits(w, new Set(dv.map((x) => x[0]))), dv };
}

export async function hist(sym, fetchImpl = fetch) {
  const r = await fetchImpl(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=5y&interval=1wk&events=div`, { headers: { "User-Agent": "Mozilla/5.0" } });
  if (!r.ok) return null;
  return histFrom((((await r.json()).chart || {}).result || [])[0]);
}

export function parse(q) {
  return [...new Set((q || "").split(",").map((s) => s.trim().toUpperCase()).filter((s) => OK.test(s)))].slice(0, MAX);
}

export async function onRequestGet({ request, waitUntil }) {
  const u = new URL(request.url);
  const syms = parse(u.searchParams.get("s"));
  const full = u.searchParams.get("full") === "1";
  const hst = u.searchParams.get("hist") === "1";
  const vols = new Set(parse(u.searchParams.get("vol")));
  const exts = new Set(parse(u.searchParams.get("ext")));
  const ivs = new Set(parse(u.searchParams.get("iv")));
  if (!syms.length) return json({ error: "no symbols" }, 400, 0);
  const cache = typeof caches !== "undefined" ? caches.default : null;
  const key = new Request(`https://quote.cache/${hst ? "h/" : ""}${full ? "f/" : ""}${syms.slice().sort().join(",")}${vols.size ? "/v/" + [...vols].sort().join(",") : ""}${exts.size ? "/e/" + [...exts].sort().join(",") : ""}${ivs.size ? "/i/" + [...ivs].sort().join(",") : ""}`);
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  const out = {};
  if (hst) {
    await Promise.all(syms.slice(0, 5).map(async (s) => {
      try { const h = await hist(s); if (h) out[s] = h; } catch (e) { /* skip */ }
    }));
    const hr = json({ ts: Math.floor(Date.now() / 1000), q: out }, 200, Object.keys(out).length ? TTL_FULL : 0);
    if (cache && Object.keys(out).length) { const put = cache.put(key, hr.clone()); if (waitUntil) waitUntil(put); else await put; }
    return hr;
  }
  await Promise.all(syms.map(async (s) => {
    try {
      const [q, e, iv] = await Promise.all([one(s, fetch, full, vols.has(s)), exts.has(s) && !full ? ext(s).catch(() => null) : null,
        ivs.has(s) && !full ? intra(s).catch(() => null) : null]);
      if (q) out[s] = { ...q, ...(e ? { ext: e } : {}), ...(iv ? { iv } : {}) };
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
