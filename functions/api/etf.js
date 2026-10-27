// Cloudflare Pages Function: GET /api/etf → every Taiwan-listed ETF from the TWSE "ETF 即時淨值" feed (price, issuer's
// estimated NAV, premium, units outstanding, today's change in units).  The page's ETF search uses it so a newly listed
// ETF appears without waiting for a site build.  Public data only; nothing stored.  Cached 60 s at the edge.
const SRC = "https://mis.twse.com.tw/stock/data/all_etf.txt";
const TTL = 60;

const num = (x) => {
  const v = parseFloat(String(x ?? "").replace(/,/g, ""));
  return Number.isFinite(v) ? v : null;
};

// [code, name, units, unit change, price, NAV, premium %, "YYYY-MM-DD", "HH:MM:SS"]; no NAV → premium unknown (null), never 0
export function parse(j) {
  const out = [];
  for (const g of (j && j.a1) || []) {
    for (const r of g.msgArray || []) {
      const code = String(r.a || "").trim();
      if (!code) continue;
      const px = num(r.e), nav = num(r.f), d = String(r.i || "");
      out.push([code, String(r.b || "").split(/[(（]/)[0].trim(), num(r.c), num(r.d), px || null, nav || null,
        px && nav ? num(r.g) : null, d.length === 8 ? `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6)}` : null, r.j || null]);
    }
  }
  return out;
}

export async function onRequestGet({ waitUntil }) {
  const cache = typeof caches !== "undefined" ? caches.default : null;
  const key = new Request("https://etf.cache/all");
  if (cache) {
    const hit = await cache.match(key);
    if (hit) return hit;
  }
  let rows = [];
  try {
    const r = await fetch(SRC, { headers: { "User-Agent": "Mozilla/5.0", Referer: "https://mis.twse.com.tw/" } });
    if (r.ok) rows = parse(await r.json());
  } catch (e) { /* source down → empty list; the page keeps its build-time copy */ }
  const res = new Response(JSON.stringify({ ts: Math.floor(Date.now() / 1000), rows }), {
    status: rows.length ? 200 : 502,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${rows.length ? TTL : 0}` },
  });
  if (cache && rows.length) {
    const put = cache.put(key, res.clone());
    if (waitUntil) waitUntil(put); else await put;
  }
  return res;
}
