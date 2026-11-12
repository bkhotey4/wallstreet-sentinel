// Cloudflare Pages Function: GET /api/news → the latest headlines from a fixed list of reliable feeds, newest first, each tagged
// with the markets it is likely to touch (keyword rules below, not AI).  Chinese sources first-class (中央社, BBC 中文), plus
// official releases (Fed, ECB, BOJ), English business desks (BBC, MarketWatch) and CNBC (markets, finance, top news, world, politics —
// world/politics carry statements like "Trump says Iran strikes unlikely" that move oil before any market desk writes it up).  General-news feeds (all: false) keep only headlines that
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
  { s: "CNBC 市場", u: "https://www.cnbc.com/id/15839069/device/rss/rss.html", lang: "en" },
  { s: "CNBC 財經", u: "https://www.cnbc.com/id/10000664/device/rss/rss.html", lang: "en" },
  { s: "CNBC 頭條", u: "https://www.cnbc.com/id/100003114/device/rss/rss.html", lang: "en" },
  { s: "CNBC 國際", u: "https://www.cnbc.com/id/100727362/device/rss/rss.html", lang: "en" },
  { s: "CNBC 政治", u: "https://www.cnbc.com/id/10000113/device/rss/rss.html", lang: "en" },
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
  ["地緣", ["關稅", "制裁", "戰爭", "飛彈", "台海", "伊朗", "以色列", "中東", "荷姆茲", "烏克蘭", "俄羅斯", "tariff", "tariffs", "sanction",
            "sanctions", "war", "missile", "invasion", "strike", "strikes", "airstrike", "ceasefire", "Iran", "Iranian", "Israel", "Middle East", "Hormuz", "Ukraine", "Russia"]],
  ["人事", ["辭職", "辭任", "下台", "接任", "執行長", "resigns", "steps down", "CEO"]],
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
  const all = lists.flat().filter((x) => nowSec - x.ts < (x.alert ? 72 : MAX_AGE_H) * 3600 && x.ts <= nowSec + 600)
    .sort((a, b) => b.ts - a.ts)
    .filter((x) => { const k = x.alert ? x.u : x.t.replace(/\s+/g, "").slice(0, 40); if (seen.has(k)) return false; seen.add(k); return true; });
  const al = all.filter((x) => x.alert).slice(0, 10);              // SEC alerts are never pushed out by a busy news day
  return al.concat(all.filter((x) => !x.alert).slice(0, 60 - al.length)).sort((a, b) => b.ts - a.ts);
}

// ---- SEC 人事申報警報：SEC 最新 8-K 清單（官方 Atom，約最近 100 份）裡，追蹤公司（/sec_watch.json，建置時產生）申報第 5.02 項
// （董事或高階主管離職、任命、薪酬安排）就列成一則官方新聞並標 alert；點進申報原文判斷是哪一種，關鍵字只在原文前段找。
const SEC_FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&count=100&output=atom";
const SEC_UA = "WallStreet Sentinel research site https://wallstreet-sentinel.pages.dev";

export function parseSec(xml, watch) {
  const out = [];
  for (const e of xml.match(/<entry>[\s\S]*?<\/entry>/g) || []) {
    const sum = unesc((e.match(/<summary[^>]*>([\s\S]*?)<\/summary>/) || [])[1] || "");
    if (!/Item 5\.02/.test(sum)) continue;
    const title = unesc((e.match(/<title>([\s\S]*?)<\/title>/) || [])[1] || "");
    const cm = title.match(/\((\d{10})\)/);
    if (!cm) continue;
    const hit = watch[String(parseInt(cm[1], 10))];
    if (!hit) continue;
    const u = ((e.match(/<link[^>]*href="([^"]+)"/) || [])[1] || "").replace(/^http:\/\//, "https://");
    const d = Date.parse((e.match(/<updated>([^<]+)<\/updated>/) || [])[1] || "");
    if (!/^https:\/\/www\.sec\.gov\//.test(u) || !d) continue;
    out.push({ t: `SEC 申報：${hit[1]}（${hit[0]}）高層人事異動（8-K 第 5.02 項）`, u, s: "SEC 申報", ts: Math.floor(d / 1000),
               lang: "zh", off: true, tags: ["美股", "人事"], alert: true, sym: hit[0] });
  }
  return out;
}

// what the filing says, from its first pages: departure / appointment / pay only, and which seat (CEO, CFO, chair, director)
export function kind(text) {
  const t = text.slice(0, 12000);
  const i = t.search(/Item\s*5\.02/i);
  const w = i >= 0 ? t.slice(i, i + 4000) : t;
  const what = /resign|step(?:ped|s)? down|retire|depart|terminat|will not stand|leave the company/i.test(w) ? "離職"
    : /appoint|named|elect|promot/i.test(w) ? "任命" : /compensat|bonus|award|salary|incentive/i.test(w) ? "薪酬安排" : "";
  const seat = /Chief Executive Officer|CEO/.test(w) ? "執行長" : /Chief Financial Officer|CFO/.test(w) ? "財務長"
    : /Chair(?:man|woman|person)? of the Board|Chair/.test(w) ? "董事長" : /President/.test(w) ? "總裁" : /director/i.test(w) ? "董事" : "";
  return { what, seat };
}

async function secItems(ctx) {
  try {
    const [fr, wr] = await Promise.all([
      fetch(SEC_FEED, { headers: { "user-agent": SEC_UA }, cf: { cacheTtl: 60 } }),
      fetch(new URL("/sec_watch.json", ctx.request.url).toString(), { cf: { cacheTtl: 600 } }),
    ]);
    if (!wr.ok) return [];
    const items = fr.ok ? parseSec(await fr.text(), ((await wr.json()) || {}).ciks || {}) : [];
    for (const x of items.slice(0, 5)) {             // read the filing itself (rare: only tracked companies)
      try {
        const ix = await fetch(x.u, { headers: { "user-agent": SEC_UA }, cf: { cacheTtl: 86400 } });
        const doc = ((await ix.text()).match(/href="(\/Archives\/edgar\/data\/[^"]+?\.htm)"/) || [])[1];
        if (!doc) continue;
        const r = await fetch("https://www.sec.gov" + doc, { headers: { "user-agent": SEC_UA }, cf: { cacheTtl: 86400 } });
        const k = kind(unesc(await r.text()));
        if (k.what) x.t = x.t.replace("高層人事異動", (k.seat ? k.seat : "高層") + k.what);
        x.kind = k.what;
      } catch (e) { /* keep the generic title */ }
    }
    try {                                            // the build's record (3 days): alerts stay after the live list scrolls on
      const ar = await fetch(new URL("/sec_alerts.json", ctx.request.url).toString(), { cf: { cacheTtl: 300 } });
      if (ar.ok) {
        const have = new Set(items.map((x) => x.u));
        for (const x of ((await ar.json()) || {}).items || []) if (!have.has(x.u)) items.push(x);
      }
    } catch (e) { /* live list only */ }
    return items;
  } catch (e) {
    return [];
  }
}

export async function onRequest(ctx) {
  const cache = caches.default;
  const key = new Request(new URL("/api/news", ctx.request.url).toString());
  const hit = await cache.match(key);
  if (hit) return hit;
  const secP = secItems(ctx);
  const res = await Promise.all(FEEDS.map(async (f) => {
    try {
      const r = await fetch(f.u, { headers: { "user-agent": "Mozilla/5.0 (WallStreet Sentinel news)" }, cf: { cacheTtl: 60 } });
      return r.ok ? parse(await r.text(), f) : [];
    } catch (e) {
      return [];
    }
  }));
  const sec = await secP;
  res.push(sec);
  const now = Math.floor(Date.now() / 1000);
  const ok = FEEDS.filter((f, i) => res[i].length).map((f) => f.s).concat(sec.length ? ["SEC 申報"] : []);
  const body = JSON.stringify({ ts: now, sources: ok, items: merge(res, now) });
  const resp = new Response(body, { headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=" + TTL } });
  ctx.waitUntil(cache.put(key, resp.clone()));
  return resp;
}
