// Cloudflare Pages Function: GET /api/news → the latest headlines from a fixed list of reliable feeds, newest first, each tagged
// with the markets it is likely to touch (keyword rules below, not AI).  Chinese sources first-class (中央社, BBC 中文), plus
// official releases (Fed, ECB, BOJ) and two English business desks.  General-news feeds (all: false) keep only headlines that
// carry a market tag.  Nothing stored; the merged list is cached 120 s at the edge.
// Aggregators (Google News) are left out on purpose: too many click-bait titles for a beginner's page.
const FEEDS = [
  { s: "中央社財經", u: "https://feeds.feedburner.com/rsscna/finance", lang: "zh", all: true },
  { s: "中央社國際", u: "https://feeds.feedburner.com/rsscna/intworld", lang: "zh" },
  { s: "BBC 中文", u: "https://feeds.bbci.co.uk/zhongwen/trad/rss.xml", lang: "zh" },
  { s: "聯準會", u: "https://www.federalreserve.gov/feeds/press_all.xml", lang: "en", off: true, all: true },
  { s: "歐洲央行", u: "https://www.ecb.europa.eu/rss/press.html", lang: "en", off: true, all: true },
  { s: "日本央行", u: "https://www.boj.or.jp/en/rss/whatsnew.xml", lang: "en", off: true, all: true },
  { s: "BBC Business", u: "https://feeds.bbci.co.uk/news/business/rss.xml", lang: "en" },
  { s: "MarketWatch", u: "https://feeds.content.dowjones.io/public/rss/mw_topstories", lang: "en" },
];
// tag → keywords.  Chinese: substring; English: whole word, any case.  A headline can carry several tags.
export const TAGS = [
  ["美股", ["美股", "道瓊", "標普", "那斯達克", "華爾街", "Wall Street", "S&P", "Nasdaq", "Dow Jones", "stocks", "shares"]],
  ["台股", ["台股", "加權指數", "台積電", "櫃買", "TSMC", "Taiwan stocks"]],
  ["利率", ["聯準會", "央行", "利率", "降息", "升息", "公債", "殖利率", "Fed", "Federal Reserve", "interest rate", "interest rates",
            "rate cut", "rate hike", "Treasury", "Treasuries", "yield", "yields", "bond", "bonds", "monetary policy"]],
  ["油價", ["油價", "原油", "石油", "OPEC", "天然氣", "oil", "crude", "natural gas"]],
  ["匯率", ["美元", "匯率", "日圓", "日元", "新台幣", "人民幣", "dollar", "yen", "currency", "currencies"]],
  ["黃金", ["黃金", "金價", "gold"]],
  ["科技", ["AI", "人工智慧", "輝達", "晶片", "半導體", "Nvidia", "chip", "chips", "semiconductor"]],
  ["地緣", ["關稅", "制裁", "戰爭", "飛彈", "台海", "tariff", "tariffs", "sanction", "sanctions", "war", "missile", "invasion"]],
  ["就業物價", ["通膨", "物價", "CPI", "就業", "非農", "失業", "inflation", "jobs", "payrolls", "unemployment"]],
];
const MAX_AGE_H = 36;
const TTL = 120;
const ASCII = /^[ -~]+$/;
const esc = (k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const RX = TAGS.map(([z, ks]) => [z, ks.map((k) => (ASCII.test(k) ? new RegExp("(^|[^A-Za-z])" + esc(k) + "(?![A-Za-z])", "i") : k))]);

export function tag(t) {                          // "AI" must not match "said"; "國AI監" still counts
  return RX.filter(([, ks]) => ks.some((k) => (typeof k === "string" ? t.includes(k) : k.test(t)))).map(([z]) => z);
}

const unesc = (x) => x.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/<[^>]+>/g, "")
  .replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16))).replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n))
  .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&")
  .replace(/\s+/g, " ").trim();

export function parse(xml, f) {
  const out = [];
  const items = xml.match(/<(item|entry)[\s>][\s\S]*?<\/(item|entry)>/g) || [];
  for (const it of items.slice(0, 40)) {
    const pick = (tg) => { const m = it.match(new RegExp("<" + tg + "[^>]*>([\\s\\S]*?)</" + tg + ">")); return m ? unesc(m[1]) : ""; };
    const t = pick("title");
    let u = pick("link");
    if (!u) { const m = it.match(/<link[^>]*href="([^"]+)"/); u = m ? m[1] : ""; }
    u = u.replace(/^http:\/\//, "https://");
    const d = Date.parse(pick("pubDate") || pick("updated") || pick("dc:date") || pick("published"));
    if (!t || !/^https:\/\//.test(u) || !d) continue;
    const tags = tag(t);
    if (!f.all && !tags.length) continue;
    out.push({ t, u, s: f.s, ts: Math.floor(d / 1000), lang: f.lang, off: !!f.off, tags });
  }
  return out;
}

export function merge(lists, nowSec) {
  const seen = new Set();
  return lists.flat().filter((x) => nowSec - x.ts < MAX_AGE_H * 3600 && x.ts <= nowSec + 600)
    .sort((a, b) => b.ts - a.ts)
    .filter((x) => { const k = x.t.replace(/\s+/g, "").slice(0, 40); if (seen.has(k)) return false; seen.add(k); return true; })
    .slice(0, 60);
}

export async function onRequest(ctx) {
  const cache = caches.default;
  const key = new Request(new URL("/api/news", ctx.request.url).toString());
  const hit = await cache.match(key);
  if (hit) return hit;
  const res = await Promise.all(FEEDS.map(async (f) => {
    try {
      const r = await fetch(f.u, { headers: { "user-agent": "Mozilla/5.0 (WallStreet Sentinel news)" }, cf: { cacheTtl: 60 } });
      return r.ok ? parse(await r.text(), f) : [];
    } catch (e) {
      return [];
    }
  }));
  const now = Math.floor(Date.now() / 1000);
  const ok = FEEDS.filter((f, i) => res[i].length).map((f) => f.s);
  const body = JSON.stringify({ ts: now, sources: ok, items: merge(res, now) });
  const resp = new Response(body, { headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=" + TTL } });
  ctx.waitUntil(cache.put(key, resp.clone()));
  return resp;
}
