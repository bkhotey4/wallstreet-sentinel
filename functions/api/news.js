// Cloudflare Pages Function: GET /api/news → the latest headlines from a fixed list of reliable feeds, newest first, each tagged
// with the markets it is likely to touch (keyword rules below, not AI).  Chinese sources first-class (中央社, BBC 中文, 自由時報, 經濟日報),
// plus official releases (Fed, ECB, BOJ), English business desks (BBC, MarketWatch, WSJ, Bloomberg, NYT, Guardian, FT) and CNBC
// (markets, finance, top news, world, politics — world/politics carry statements like "Trump says Iran strikes unlikely" that move
// oil before any market desk writes it up).  General-news feeds (all: false) keep only headlines that carry a market tag;
// business desks (biz: true) keep the untagged ones too, marked q: they are not listed, only counted by bursts().
// Nothing stored; the merged list is cached 120 s at the edge.
// Aggregators (Google News) are left out on purpose: too many click-bait titles for a beginner's page.
// `o` is the newsroom: several feeds of one newsroom count once when we ask "how many outlets are reporting this?" (see bursts()).
const FEEDS = [
  { s: "中央社財經", o: "cna", u: "https://feeds.feedburner.com/rsscna/finance", lang: "zh", all: true },
  { s: "中央社國際", o: "cna", u: "https://feeds.feedburner.com/rsscna/intworld", lang: "zh" },
  { s: "BBC 中文", o: "bbc", u: "https://feeds.bbci.co.uk/zhongwen/trad/rss.xml", lang: "zh" },
  { s: "聯準會", o: "fed", u: "https://www.federalreserve.gov/feeds/press_all.xml", lang: "en", off: true, all: true },
  { s: "歐洲央行", o: "ecb", u: "https://www.ecb.europa.eu/rss/press.html", lang: "en", off: true, all: true },
  { s: "日本央行", o: "boj", u: "https://www.boj.or.jp/en/rss/whatsnew.xml", lang: "en", off: true, all: true },
  { s: "BBC Business", o: "bbc", u: "https://feeds.bbci.co.uk/news/business/rss.xml", lang: "en", biz: true },
  { s: "MarketWatch", o: "mw", u: "https://feeds.content.dowjones.io/public/rss/mw_topstories", lang: "en", biz: true },
  { s: "CNBC 市場", o: "cnbc", u: "https://www.cnbc.com/id/15839069/device/rss/rss.html", lang: "en", biz: true },
  { s: "CNBC 財經", o: "cnbc", u: "https://www.cnbc.com/id/10000664/device/rss/rss.html", lang: "en", biz: true },
  { s: "CNBC 頭條", o: "cnbc", u: "https://www.cnbc.com/id/100003114/device/rss/rss.html", lang: "en" },
  { s: "CNBC 國際", o: "cnbc", u: "https://www.cnbc.com/id/100727362/device/rss/rss.html", lang: "en" },
  { s: "CNBC 政治", o: "cnbc", u: "https://www.cnbc.com/id/10000113/device/rss/rss.html", lang: "en" },
  // added 2026-11-14 so that "three newsrooms report the same thing within 45 minutes" has enough newsrooms to count
  { s: "自由時報財經", o: "ltn", u: "https://news.ltn.com.tw/rss/business.xml", lang: "zh", biz: true },
  { s: "經濟日報", o: "udn", u: "https://money.udn.com/rssfeed/news/1001/5591?ch=money", lang: "zh", biz: true },
  { s: "華爾街日報市場", o: "wsj", u: "https://feeds.content.dowjones.io/public/rss/RSSMarketsMain", lang: "en", biz: true },
  { s: "華爾街日報國際", o: "wsj", u: "https://feeds.content.dowjones.io/public/rss/RSSWorldNews", lang: "en" },
  { s: "彭博市場", o: "bbg", u: "https://www.bloomberg.com/feeds/markets/news.rss", lang: "en", biz: true },
  { s: "彭博政治", o: "bbg", u: "https://www.bloomberg.com/feeds/politics/news.rss", lang: "en" },
  { s: "紐約時報財經", o: "nyt", u: "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml", lang: "en", biz: true },
  { s: "衛報財經", o: "gdn", u: "https://www.theguardian.com/uk/business/rss", lang: "en", biz: true },
  { s: "金融時報", o: "ft", u: "https://www.ft.com/rss/home/international", lang: "en" },
  { s: "半島電視台", o: "aj", u: "https://www.aljazeera.com/xml/rss/all.xml", lang: "en" },
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
const ASCII = /^[ -~’]+$/;
const esc = (k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// one regex per tag for the English keywords (whole word, any case) + the Chinese ones as plain substrings
const RX = TAGS.map(([z, ks]) => {
  const en = ks.filter((k) => ASCII.test(k)), zh = ks.filter((k) => !ASCII.test(k));
  return [z, en.length ? new RegExp("(^|[^A-Za-z])(?:" + en.map(esc).join("|") + ")(?![A-Za-z])", "i") : null, zh];
});

export function tag(t) {                          // "AI" must not match "said"; "國AI監" still counts
  return RX.filter(([, rx, zh]) => (rx && rx.test(t)) || zh.some((k) => t.includes(k))).map(([z]) => z);
}

const unesc = (x) => {
  if (x.indexOf("<") >= 0) x = x.replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1").replace(/<[^>]+>/g, "");
  if (x.indexOf("&") >= 0) {
    x = x.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16))).replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n))
      .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
  }
  return x.replace(/\s+/g, " ").trim();
};

const PICK = {};
const pickRx = (tg) => PICK[tg] || (PICK[tg] = new RegExp("<" + tg + "[^>]*>([\\s\\S]*?)</" + tg + ">"));

export function parse(xml, f) {
  const out = [];
  const items = [];                                 // only the first 40: a feed can carry 70, and this runs on every cache miss
  const open = /<(item|entry)[\s>]/g;
  for (let m; items.length < 40 && (m = open.exec(xml));) {
    const end = xml.indexOf("</" + m[1] + ">", m.index);
    if (end < 0) break;
    items.push(xml.slice(m.index, end));
    open.lastIndex = end;
  }
  for (const it of items) {
    const pick = (tg) => { const m = it.match(pickRx(tg)); return m ? unesc(m[1]) : ""; };
    const t = pick("title");
    let u = pick("link");
    if (!u) { const m = it.match(/<link[^>]*href="([^"]+)"/); u = m ? m[1] : ""; }
    u = u.replace(/^http:\/\//, "https://");
    const d = Date.parse(pick("pubDate") || pick("updated") || pick("dc:date") || pick("published"));
    if (!t || !/^https:\/\//.test(u) || !d) continue;
    const tags = tag(t);
    if (!f.all && !tags.length && !f.biz) continue;
    const x = { t, u, s: f.s, o: f.o || f.s, ts: Math.floor(d / 1000), lang: f.lang, off: !!f.off, tags };
    if (!f.all && !tags.length) x.q = true;          // a business-desk headline without a market tag: counted in bursts(), not listed
    out.push(x);
  }
  return out;
}

// every item once, newest first: SEC alerts live 72 h, headlines 36 h; the same title from two feeds of one newsroom counts once
export function dedupe(lists, nowSec) {
  const seen = new Set();
  return lists.flat().filter((x) => nowSec - x.ts < (x.alert ? 72 : MAX_AGE_H) * 3600 && x.ts <= nowSec + 600)
    .sort((a, b) => b.ts - a.ts)
    .filter((x) => { const k = x.alert ? x.u : x.t.replace(/\s+/g, "").slice(0, 40); if (seen.has(k)) return false; seen.add(k); return true; });
}

export function merge(lists, nowSec) {
  const all = dedupe(lists, nowSec);
  const al = all.filter((x) => x.alert).slice(0, 10);              // SEC alerts are never pushed out by a busy news day
  return al.concat(all.filter((x) => !x.alert && !x.q).slice(0, 60 - al.length)).sort((a, b) => b.ts - a.ts);
}

// ---- 多家媒體同時報導（2026-11-14）：45 分鐘內有好幾家不同的新聞編輯室報導同一家公司（2 家以上）或同一件事（3 家以上），
// 而且至少是它前 6 小時最熱鬧那 45 分鐘的兩倍（天天上新聞的公司要比平常多一倍才算），就算一則「突發」，列 3 小時。
// 同一件事的判斷不用 AI：
//   * 公司：標題出現追蹤公司的中文名或英文名（/sec_watch.json 的 names，建置時產生）
//   * 事件：標題同時出現下面兩個主題，其中至少一個是「發生了什麼」（e）；只有「誰」加「哪個市場」（例如 聯準會＋美債）每天都有，不算
// 對得上只代表很多家同時在報，不代表消息是真的，也不代表市場一定會動。
export const TOPICS = [
  ["攻擊", "e", ["空襲", "飛彈", "開戰", "襲擊", "轟炸", "airstrike", "airstrikes", "missile", "missiles", "attack", "attacks", "invasion", "invades", "bombing", "strikes on"]],
  ["停火", "e", ["停火", "和談", "ceasefire", "truce", "peace deal", "peace talks"]],
  ["關稅", "e", ["關稅", "tariff", "tariffs"]],
  ["制裁", "e", ["制裁", "出口管制", "sanction", "sanctions", "export controls", "export curbs"]],
  ["降息", "e", ["降息", "rate cut", "rate cuts", "cuts rates", "cut rates"]],
  ["升息", "e", ["升息", "rate hike", "rate hikes", "raises rates", "hikes rates"]],
  ["人事", "e", ["辭職", "辭任", "請辭", "下台", "免職", "撤換", "resigns", "resign", "resignation", "steps down", "ousted", "fired", "removal", "removed", "sacked"]],
  ["違約", "e", ["破產", "違約", "倒閉", "bankruptcy", "bankrupt", "Chapter 11", "default", "defaults", "collapse", "collapses"]],
  ["暴跌", "e", ["崩盤", "暴跌", "重挫", "熔斷", "plunge", "plunges", "plunged", "crash", "crashes", "selloff", "sell-off", "rout", "tumble", "tumbles", "circuit breaker", "halted"]],
  ["關門", "e", ["政府關門", "shutdown"]],
  ["收購", "e", ["收購", "併購", "acquire", "acquires", "acquisition", "merger", "takeover", "buyout"]],
  ["裁員", "e", ["裁員", "layoffs", "job cuts"]],
  ["天災", "e", ["地震", "海嘯", "earthquake", "tsunami"]],
  ["伊朗", "a", ["伊朗", "德黑蘭", "Iran", "Iranian", "Tehran"]],
  ["以色列", "a", ["以色列", "Israel", "Israeli"]],
  ["荷姆茲", "a", ["荷姆茲", "Hormuz"]],
  ["俄羅斯", "a", ["俄羅斯", "普丁", "蒲亭", "Russia", "Russian", "Putin"]],
  ["烏克蘭", "a", ["烏克蘭", "Ukraine", "Ukrainian"]],
  ["中國", "a", ["中國", "北京", "習近平", "China", "Chinese", "Beijing", "Xi Jinping"]],
  ["台灣", "a", ["台灣", "臺灣", "台海", "Taiwan"]],
  ["日本", "a", ["日本", "日銀", "Japan", "Japanese", "BOJ"]],
  ["北韓", "a", ["北韓", "North Korea"]],
  ["川普", "a", ["川普", "白宮", "Trump", "White House"]],
  ["聯準會", "a", ["聯準會", "鮑爾", "Fed", "Federal Reserve", "Powell", "FOMC"]],
  ["歐洲央行", "a", ["歐洲央行", "ECB", "Lagarde"]],
  ["產油國", "a", ["OPEC", "沙烏地", "Saudi"]],
  ["原油", "m", ["油價", "原油", "oil", "crude", "Brent"]],
  ["黃金", "m", ["黃金", "金價", "gold"]],
  ["美債", "m", ["公債", "殖利率", "美債", "Treasury", "Treasuries", "yields", "bond market"]],
  ["美元", "m", ["美元", "匯率", "日圓", "dollar", "yen"]],
  ["股市", "m", ["美股", "台股", "股市", "標普", "那斯達克", "道瓊", "stocks", "Wall Street", "S&P 500", "Nasdaq", "Dow"]],
];
// English keyword → regex source: a lower-case keyword also matches with a capital first letter ("Tariffs"); names stay case-sensitive ("Fed")
const kwSrc = (k) => (/^[a-z]/.test(k) ? "[" + k[0].toUpperCase() + k[0] + "]" + esc(k.slice(1)) : esc(k));
const TRX = TOPICS.map(([id, kind, ks]) => {
  const en = ks.filter((k) => ASCII.test(k)), zh = ks.filter((k) => !ASCII.test(k));
  return [id, kind, en.length ? new RegExp("(^|[^A-Za-z])(?:" + en.map(kwSrc).join("|") + ")(?![A-Za-z])") : null, zh];
});
export const B_WIN = 45 * 60, B_KEEP = 3 * 3600, B_QUIET = 6 * 3600, B_MIN = { co: 2, topic: 3 };

// names: {SYM: [中文名, "English|Other spelling"]} → one regex for all English names, one for all Chinese names
export function matcher(names) {
  const en = new Map(), zh = new Map();
  for (const [sym, v] of Object.entries(names || {})) {
    if (v[0]) zh.set(v[0], sym);
    for (const a of String(v[1] || "").split("|")) if (a) en.set(a, sym);
  }
  const alt = (m) => [...m.keys()].sort((a, b) => b.length - a.length).map(esc).join("|");
  return { en, zh, enRx: en.size ? new RegExp("(?:^|[^A-Za-z0-9])(" + alt(en) + ")(?![A-Za-z0-9])", "g") : null,
           zhRx: zh.size ? new RegExp(alt(zh), "g") : null };
}

// what a headline is about: ["co:NVDA", "伊朗+攻擊", …]
export function sigs(t, m) {
  const out = new Set();
  if (m && m.enRx) for (const x of t.matchAll(m.enRx)) out.add("co:" + m.en.get(x[1]));
  if (m && m.zhRx) for (const x of t.matchAll(m.zhRx)) out.add("co:" + m.zh.get(x[0]));
  const tp = TRX.filter(([, , rx, zh]) => (rx && rx.test(t)) || zh.some((k) => t.includes(k)));
  for (let i = 0; i < tp.length; i++) for (let j = i + 1; j < tp.length; j++) {
    if (tp[i][1] === "e" || tp[j][1] === "e") out.add(tp[i][0] + "+" + tp[j][0]);
  }
  return [...out];
}

// newsrooms that carried it, counted in the busiest 45-minute stretch of a list
function busiest(xs) {
  let best = 0;
  for (let i = 0; i < xs.length; i++) {
    const s = new Set();
    for (let j = i; j < xs.length && xs[j].ts - xs[i].ts <= B_WIN; j++) s.add(xs[j].o || xs[j].s);
    if (s.size > best) best = s.size;
  }
  return best;
}

export function bursts(items, now, names, labels, min = B_MIN) {
  const m = matcher(names);
  const by = new Map();
  for (const x of items) {
    if (x.alert || now - x.ts > B_KEEP + B_WIN + B_QUIET || x.ts > now + 600) continue;
    for (const k of sigs(x.t, m)) { if (!by.has(k)) by.set(k, []); by.get(k).push(x); }
  }
  const out = [];
  for (const [key, all] of by) {
    const co = key.startsWith("co:"), sym = co ? key.slice(3) : "", need = co ? min.co : min.topic;
    const xs = all.slice().sort((a, b) => a.ts - b.ts);
    let hit = null;
    for (let i = 0; i < xs.length && !hit; i++) {                    // the first 45 minutes in the last 3 hours where it took off
      if (now - xs[i].ts > B_KEEP) continue;
      const end = xs[i].ts, win = xs.filter((x) => x.ts <= end && end - x.ts <= B_WIN);
      const n = new Set(win.map((x) => x.o || x.s)).size;
      if (n < need) continue;
      const start = win[0].ts;
      const base = busiest(xs.filter((x) => x.ts < start && start - x.ts <= B_QUIET));
      if (n >= 2 * base) hit = { start, n0: n, base };               // a name that is in the news all day needs twice its usual
    }
    if (!hit) continue;
    const story = xs.filter((x) => x.ts >= hit.start);
    const first = new Map();                                         // one headline per newsroom, the earliest
    for (const x of story) if (!first.has(x.o || x.s)) first.set(x.o || x.s, x);
    const heads = [...first.values()].sort((a, b) => (a.lang === "zh" ? 0 : 1) - (b.lang === "zh" ? 0 : 1) || a.ts - b.ts);
    const last = story[story.length - 1].ts;
    out.push({ key, kind: co ? "co" : "topic", sym, label: co ? ((labels || {})[sym] || sym) + "（" + sym + "）" : key.replace("+", "＋"),
               n: first.size, base: hit.base, first: hit.start, last, mins: Math.max(1, Math.round((last - hit.start) / 60)),
               sources: heads.map((x) => x.s), tags: [...new Set(story.flatMap((x) => x.tags || []))],
               items: heads.slice(0, 5).map((x) => ({ t: x.t, u: x.u, s: x.s, ts: x.ts, lang: x.lang })), _u: new Set(story.map((x) => x.u)) });
  }
  // the same headlines usually light several pairs (伊朗+攻擊, 以色列+攻擊): keep the company, then the one more newsrooms carry
  out.sort((a, b) => (b.kind === "co") - (a.kind === "co") || b.n - a.n || b._u.size - a._u.size);
  const keep = [];
  for (const b of out) {
    if (keep.some((k) => [...b._u].filter((u) => k._u.has(u)).length >= 2)) continue;
    keep.push(b);
  }
  return keep.slice(0, 6).map(({ _u, ...b }) => b).sort((a, b) => b.first - a.first);
}

// ---- SEC 重大申報警報：SEC 最新 8-K 清單（官方 Atom，約最近 100 份）裡，追蹤公司（/sec_watch.json，建置時產生）申報第 5.02 項
// （董事或高階主管離職、任命、薪酬安排）或下面幾種少見的項目，就列成一則官方新聞並標 alert；人事申報會點進原文判斷是哪一種。
// 另外讀最新的 Schedule 13D（有人持股逾 5% 而且不排除介入經營）。規則和 wsb/data/sec_officers.py 相同。
const SEC_FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&company=&dateb=&owner=include&count=100&output=atom";
const SEC_13D = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=SCHEDULE+13D&company=&dateb=&owner=include&count=100&output=atom";
const SEC_UA = "WallStreet Sentinel research site https://wallstreet-sentinel.pages.dev";

const ITEMS = { "1.03": "破產或接管", "1.05": "重大資安事件", "2.06": "重大資產減損", "3.01": "收到下市或不符上市規定通知",
  "4.02": "過去財報不可再信賴（須重編）", "2.04": "債務被要求提前清償（觸發違約或加速條款）", "5.01": "公司控制權變動",
  "2.05": "裁員或關廠重整（認列退出成本）", "2.01": "完成重大收購或資產出售", "5.02": "高層人事異動" };
export const SEV = { "1.03": 4, "1.05": 4, "2.06": 4, "3.01": 4, "4.02": 4, "2.04": 4, "5.01": 4, "2.05": 3, "2.01": 2, "13D": 3, "13D/A": 1 };
const sev502 = (t) => (/離職/.test(t) ? 2 : 0) + (/執行長|財務長|董事長/.test(t) ? 1 : 0);

export function parseSec(xml, watch) {
  const out = [];
  for (const e of xml.match(/<entry>[\s\S]*?<\/entry>/g) || []) {
    const sum = unesc((e.match(/<summary[^>]*>([\s\S]*?)<\/summary>/) || [])[1] || "");
    const have = (sum.match(/Item (\d\.\d\d)/g) || []).map((x) => x.slice(5));
    const rare = have.filter((i) => i !== "5.02" && ITEMS[i]).sort((a, b) => SEV[b] - SEV[a]);
    const item = rare[0] || (have.includes("5.02") ? "5.02" : null);
    if (!item) continue;
    const title = unesc((e.match(/<title>([\s\S]*?)<\/title>/) || [])[1] || "");
    const cm = title.match(/\((\d{10})\)/);
    if (!cm) continue;
    const hit = watch[String(parseInt(cm[1], 10))];
    if (!hit) continue;
    const u = ((e.match(/<link[^>]*href="([^"]+)"/) || [])[1] || "").replace(/^http:\/\//, "https://");
    const d = Date.parse((e.match(/<updated>([^<]+)<\/updated>/) || [])[1] || "");
    if (!/^https:\/\/www\.sec\.gov\//.test(u) || !d) continue;
    out.push({ t: `SEC 申報：${hit[1]}（${hit[0]}）${ITEMS[item]}（8-K 第 ${item} 項）`, u, s: "SEC 申報", ts: Math.floor(d / 1000),
               lang: "zh", off: true, tags: ["美股", item === "5.02" ? "人事" : "重大申報"], alert: true, sym: hit[0], item,
               sev: item === "5.02" ? 0 : SEV[item] });
  }
  return out;
}

// Schedule 13D: one filing = two entries (Subject = the company held, Filed by = the holder).  A new 13D is an alert;
// a 13D/A (an update to an old one) is listed as an official item but not pinned.
export function parse13d(xml, watch) {
  const by = new Map();
  for (const e of xml.match(/<entry>[\s\S]*?<\/entry>/g) || []) {
    const title = unesc((e.match(/<title>([\s\S]*?)<\/title>/) || [])[1] || "");
    const m = title.match(/^SCHEDULE 13D(\/A)?\s*-\s*(.*?)\s*\((\d{10})\)\s*\((Subject|Filed by)\)/);
    const acc = (e.match(/accession-number=([\d-]+)/) || [])[1];
    const u = ((e.match(/<link[^>]*href="([^"]+)"/) || [])[1] || "").replace(/^http:\/\//, "https://");
    const d = Date.parse((e.match(/<updated>([^<]+)<\/updated>/) || [])[1] || "");
    if (!m || !acc || !d || !/^https:\/\/www\.sec\.gov\//.test(u)) continue;
    if (!by.has(acc)) by.set(acc, { form: m[1] ? "13D/A" : "13D", ts: Math.floor(d / 1000), filer: "", cik: "", u: "" });
    const r = by.get(acc);
    if (m[4] === "Subject") { r.cik = String(parseInt(m[3], 10)); r.u = u; } else if (!r.filer) r.filer = m[2].trim();
  }
  const out = [];
  for (const r of by.values()) {
    const hit = watch[r.cik];
    if (!hit || !r.u) continue;
    const who = r.filer || "有股東";
    out.push({ t: r.form === "13D" ? `SEC 申報：${who} 申報持有 ${hit[1]}（${hit[0]}）逾 5% 股權，不排除介入經營（Schedule 13D）`
                 : `SEC 申報：${who} 更新對 ${hit[1]}（${hit[0]}）的大股東持股申報（Schedule 13D/A）`,
               u: r.u, s: "SEC 申報", ts: r.ts, lang: "zh", off: true, tags: ["美股", "大股東"], alert: r.form === "13D", sym: hit[0],
               item: r.form, sev: SEV[r.form] });
  }
  return out;
}

// what the filing says (same rules as wsb/data/sec_officers.kind): departure / appointment / pay, and the seat, judged on the
// sentence that carries the action — the item's standard heading and the new directors' biographies are left out
export function kind(text) {
  const t = text.slice(0, 12000);
  const i = t.search(/Item\s*5\.02/i);
  let w = i >= 0 ? t.slice(i, i + 4000) : t;
  w = w.replace(/Item\s*5\.02[.:]?\s*Departure of Directors[\s\S]*?Compensatory Arrangements of Certain Officers\.?/i, " ").split(/Item\s*9\.01/i)[0];
  const sents = w.split(/(?<=[.;])\s+/);
  const rules = [["離職", /resign|step(?:ped|s)? down|retire|depart|terminat|will not stand|leave the company/i],
    ["任命", /appoint|named|elect|promot/i], ["薪酬安排", /compensat|bonus|award|salary|incentive/i]];
  let what = "", sent = "";
  for (const [lab, rx] of rules) {
    sent = sents.find((x) => rx.test(x)) || "";
    if (sent) { what = lab; break; }
  }
  let seat = "";
  if (what === "離職" || what === "任命") {
    seat = /Chief Executive Officer|\bCEO\b/.test(sent) ? "執行長" : /Chief Financial Officer|\bCFO\b/.test(sent) ? "財務長"
      : /Chief Operating Officer|\bCOO\b/.test(sent) ? "營運長" : /Chair(?:man|woman|person)? of the Board|Chair\b/.test(sent) ? "董事長"
      : /independent director|to (?:its|the|our) Board|as (?:a )?director|board of directors/i.test(sent) ? "董事"
      : /President/.test(sent) ? "總裁" : /director|Board/i.test(sent) ? "董事" : "";
  }
  return { what, seat };
}

// the 8-K document itself from a filing index page (the row typed 8-K), not an exhibit such as the press release
export function mainDoc(html) {
  for (const row of html.match(/<tr[\s\S]*?<\/tr>/gi) || []) {
    const m = row.match(/href="(?:\/ix\?doc=)?(\/Archives\/edgar\/data\/[^"]+?\.htm)"/);
    if (m && />\s*8-K\s*</.test(row)) return m[1];
  }
  return "";
}

async function secItems(ctx, watch) {
  try {
    const get = (u) => fetch(u, { headers: { "user-agent": SEC_UA }, cf: { cacheTtl: 60 } }).then((r) => (r.ok ? r.text() : "")).catch(() => "");
    const [fx, dx] = await Promise.all([get(SEC_FEED), get(SEC_13D)]);
    const items = parseSec(fx, watch);
    for (const x of items.filter((y) => y.item === "5.02").slice(0, 5)) {   // personnel: read the filing itself (rare)
      try {
        const ix = await fetch(x.u, { headers: { "user-agent": SEC_UA }, cf: { cacheTtl: 86400 } });
        const doc = mainDoc(await ix.text());
        if (!doc) continue;
        const r = await fetch("https://www.sec.gov" + doc, { headers: { "user-agent": SEC_UA }, cf: { cacheTtl: 86400 } });
        const k = kind(unesc(await r.text()));
        if (k.what) x.t = x.t.replace("高層人事異動", (k.seat ? k.seat : "高層") + k.what);
        x.kind = k.what;
        x.sev = sev502(x.t);
      } catch (e) { /* keep the generic title */ }
    }
    for (const x of parse13d(dx, watch)) items.push(x);
    try {                                            // the build's record (3 days): alerts stay after the live list scrolls on
      const ar = await fetch(new URL("/sec_alerts.json", ctx.request.url).toString(), { cf: { cacheTtl: 300 } });
      if (ar.ok) {
        const have = new Set(items.map((x) => x.u));
        for (const x of ((await ar.json()) || {}).items || []) {
          if (have.has(x.u)) continue;
          if (x.item === "13D/A") x.alert = false;
          items.push(x);
        }
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
  let watch = {};
  try {
    const wr = await fetch(new URL("/sec_watch.json", ctx.request.url).toString(), { cf: { cacheTtl: 600 } });
    if (wr.ok) watch = (await wr.json()) || {};
  } catch (e) { /* no list: headlines only */ }
  const secP = watch.ciks ? secItems(ctx, watch.ciks) : Promise.resolve([]);
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
  let bs = [];
  try {
    const labels = {};
    for (const v of Object.values(watch.ciks || {})) labels[v[0]] = v[1];
    bs = bursts(dedupe(res, now), now, watch.names || {}, labels);
  } catch (e) { /* headlines still go out */ }
  const body = JSON.stringify({ ts: now, sources: ok, bursts: bs, items: merge(res, now) });
  const resp = new Response(body, { headers: { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=" + TTL } });
  ctx.waitUntil(cache.put(key, resp.clone()));
  return resp;
}
