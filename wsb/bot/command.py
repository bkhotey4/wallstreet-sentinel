"""War-room views: /command (control room + playbook) and /shock (next-shock radar + model credibility).
Slide decks (PNG) with a plain Discord-embed fallback."""
from __future__ import annotations

import time
from typing import List, Optional

import discord

from ..analytics import playbook as PB
from ..analytics import watch as WATCH
from . import slides as S
from .slides import ACCENT, GREEN, M, MUTED, ORANGE, RED, TEXT, W, YELLOW, Slide, fmt, font, level_color, pn

STAGE_COL = [GREEN, YELLOW, ORANGE, RED]
SHORT = {"stock_bond": "股債同向", "double_kill": "股債雙殺", "haven_fail": "避險失靈"}
STATE_COL = {"高度警戒": RED, "點火中": RED, "留意": ORANGE, "升溫": ORANGE, "低": MUTED, "平靜": GREEN}


def _h63(engine) -> Optional[dict]:
    return next((h for h in (engine.odds or {}).get("horizons", []) if h["days"] == 63), None)


def _liq_events(engine, days: int = 21) -> List[dict]:
    return [e for e in engine.calendar.upcoming(days) if e["type"] in ("liquidity", "fomc")]


def _health(engine) -> dict:
    return WATCH.health_status(engine.stress, 10 ** 9)


# ------------------------------------------------------------------ slides
def _control(engine, tag: str) -> Slide:
    pbk = engine.playbook or {}
    st = engine.stress
    stage = pbk.get("stage", 0)
    col = STAGE_COL[stage]
    s = Slide("戰情總控台", tag, "把壓力指數、崩跌機率、衝擊雷達、避險有效性、持倉集中度與事件日合成一個階段")
    s.card((M, 235, 700, 1005), outline=col, width=4)
    s.d.text((385, 300), "目前風險階段", font=font(38, True), fill=MUTED, anchor="mm")
    s.d.text((385, 470), pbk.get("name", "計算中"), font=font(170, True), fill=col, anchor="mm")
    s.d.text((385, 600), f"風險分 {pbk.get('points', '—')} / 6+", font=font(44), fill=TEXT, anchor="mm")
    y = 660
    for pts, why in (pbk.get("why") or [])[:5]:
        s.d.text((110, y), f"+{pts}", font=font(34, True), fill=col if pts else MUTED, anchor="lm")
        s.d.text((175, y), why, font=s.fit(why, 30, 480, min_size=18), fill=TEXT if pts else MUTED, anchor="lm")
        y += 56
    if not pbk.get("why"):
        s.d.text((385, 700), "目前沒有任何風險規則被觸發", font=font(32), fill=MUTED, anchor="mm")
    nt = pbk.get("next_thr")
    if nt is not None:
        s.d.text((385, 965), f"再 +{max(nt - pbk.get('points', 0), 0)} 分升到下一階段", font=font(28), fill="#6E7781", anchor="mm")
    h = _h63(engine)
    pf = engine.portfolio or {}
    cc = WATCH.concentration(pf) if pf and not pf.get("error") else {"breaches": []}
    hl = _health(engine)
    sk = engine.shock or {}
    top = (sk.get("paths") or [None])[0]
    tiles = [
        ("SSI 壓力指數", fmt(st.score, 1) if st else "—", (st.label if st else ""), level_color(st.score if st else None)),
        ("3 個月跌≥10% 機率", f"{fmt(h.get('adjusted', h['conditional']), 1)}%" if h else "—",
         (h.get("lift_adj_text") or h.get("lift_text", "")) if h else "", S.lift_color(h.get("lift_adj", h.get("lift")) if h else None)),
        ("最可能的衝擊路徑", top["name"] if top else "—", f"點火 {top['ignition']:.0f}・{top['state']}" if top else "",
         STATE_COL.get(top["state"] if top else "低", MUTED)),
        ("避險機制", "失效訊號 %d" % len(engine.breaks.get("flags", [])) if engine.breaks.get("available") else "資料不足",
         "、".join(SHORT.get(f["key"], f["key"]) for f in engine.breaks.get("flags", [])[:3]) or "股債/避險仍正常",
         RED if engine.breaks.get("flags") else GREEN),
        ("持倉 β／VaR99", f"{fmt(pf.get('beta'), 2)}　{fmt(pf.get('var99_1d_usd'), 0, money=True)}" if pf and not pf.get("error") else "—",
         "單日最壞 1% 虧損", TEXT),
        ("持倉集中度", f"{len(cc['breaches'])} 項超標" if pf and not pf.get("error") else "—",
         "；".join(b["name"] for b in cc["breaches"][:2]) or "皆在限額內", ORANGE if cc["breaches"] else GREEN),
        ("資料健康", f"覆蓋 {hl['coverage'] * 100:.0f}%" if hl.get("coverage") is not None else "—",
         "正常" if hl["ok"] else "有異常（見 /status）", GREEN if hl["ok"] else RED),
        ("下個事件日", (_liq_events(engine, 30) or [{"event": "—", "date": ""}])[0]["event"][:14],
         (_liq_events(engine, 30) or [{"event": "", "date": ""}])[0]["date"], ACCENT),
    ]
    x0, gap = 735, 22
    w = (W - M - x0 - gap) / 2
    h = 170
    for i, (name, val, note, c) in enumerate(tiles):
        r, cc = divmod(i, 2)
        bx, by = x0 + cc * (w + gap), 235 + r * (h + gap)
        s.card((bx, by, bx + w, by + h), outline=c if c in (RED, GREEN) else S.BORDER, width=3)
        s.d.text((bx + 24, by + 34), name, font=s.fit(name, 28, w - 48), fill=MUTED, anchor="lm")
        s.d.text((bx + 24, by + 94), val, font=s.fit(val, 46, w - 48, True), fill=TEXT, anchor="lm")
        s.d.text((bx + 24, by + 142), note, font=s.fit(note, 28, w - 48), fill=c, anchor="lm")
    return s


def _paths(engine, tag: str) -> Slide:
    sk = engine.shock or {}
    s = Slide("衝擊雷達：下一次衝擊會從哪裡點火？", tag, "點火分數 = 區塊壓力水準 + 近 20 日升溫速度（相對歷史的百分位）；≥70 高度警戒、≥58 留意")
    paths = sk.get("paths") or []
    rows = [(p["name"], p["ignition"], f"{p['ignition']:.0f}") for p in paths[:6]]
    s.bars(rows, (M, 235, W - M, 620), label_w=420, size=36)
    y = 650
    if paths:
        p = paths[0]
        s.d.text((M, y), f"主軸：{p['name']}（{'＋'.join(p['blocks'])}）", font=font(38, True), fill=STATE_COL.get(p["state"], TEXT))
        y = s.paragraph(p["story"], M, y + 56, W - 2 * M, size=32, color=MUTED)
    dv = sk.get("divergence") or {}
    if dv.get("available"):
        y += 24
        hs = dv.get("hist") or {}
        txt = (f"股債背離：信用/利率/流動性/新興壓力 {dv['credit']:.0f} vs 股市恐慌指標 {dv['equity']:.0f}，差 {dv['gap']:+.0f}（門檻 {dv['threshold']:.0f}）"
               + ("【警示：信用已先反應，股市可能還沒】" if dv["flag"] else "【未背離】"))
        s.d.text((M, y), "股債背離檢查", font=font(36, True), fill=RED if dv["flag"] else GREEN)
        y = s.paragraph(txt, M, y + 52, W - 2 * M, size=30, color=TEXT)
        if hs and hs.get("prob_when_flagged") is not None:
            s.paragraph(f"歷史上出現背離時，63 日內標普跌≥10% 的機率 {hs['prob_when_flagged']:.1f}%（基準 {hs['base_rate']:.1f}%）。",
                        M, y + 6, W - 2 * M, size=28, color=MUTED)
    return s


def _radar(engine, tag: str) -> Slide:
    sk = engine.shock or {}
    s = Slide("區塊雷達：誰在升溫、過去準不準", tag, "水準＝目前壓力；升溫＝20 日變化的歷史百分位；AUC＝該區塊對『63 日內大跌』的歷史預警力（0.5=無鑑別力）")
    rows = []
    for r in (sk.get("radar") or [])[:9]:
        a = r.get("auc")
        rows.append([(r["block"], TEXT), (f"{r['level']:.0f}", level_color(r["level"])),
                     (f"{r['chg20']:+.1f}", RED if r["chg20"] > 3 else GREEN if r["chg20"] < -3 else MUTED),
                     (f"{r['accel_pctile']:.0f}%", MUTED), (r["state"], STATE_COL.get(r["state"], MUTED)),
                     (fmt(a, 2) if a is not None else "—", GREEN if (a or 0) >= 0.62 else MUTED)])
    s.table(["區塊", "水準", "20日變化", "升溫百分位", "狀態", "歷史AUC"], rows, 250, [0.22, 0.12, 0.16, 0.18, 0.16, 0.16], size=36, row_h=82)
    return s


def _playbook(engine, tag: str) -> Slide:
    pbk = engine.playbook or {}
    stage = pbk.get("stage", 0)
    s = Slide(f"風險劇本：階段「{pbk.get('name', '—')}」該做什麼", tag, "依階段自動產生的行動清單（規則式、可追溯；部位大小由你決定）")
    y = 240
    for i, a in enumerate(pbk.get("actions") or ["計算中"], 1):
        s.d.ellipse((M, y + 6, M + 52, y + 58), fill=STAGE_COL[stage])
        s.d.text((M + 26, y + 32), str(i), font=font(32, True), fill="#0B0F14", anchor="mm")
        y = s.paragraph(a, M + 80, y, W - 2 * M - 80, size=36, color=TEXT) + 26
    nt = pbk.get("next_thr")
    s.paragraph("階段規則：風險分 0–1 正常、2–3 留意、4–5 戒備、≥6 防禦。分數來自 SSI 水準、崩跌機率倍數、傳導路徑、股債背離、避險失靈，"
                "階段只在風險分下降 2 分以上才調降，避免來回震盪。", M, 905, W - 2 * M, size=26, color="#6E7781")
    return s


def _quality(engine, tag: str) -> Slide:
    ql = (engine.shock or {}).get("quality") or {}
    s = Slide("模型可信度與避險有效性", tag, "走步外樣本測試：只用當時已知的資料預測、再對照後來發生的事，避免自我感覺良好")
    rows = []
    for w in ql.get("walk_forward", []):
        if not w.get("n_test"):
            continue
        sk_ = (w.get("skill") or 0) * 100
        rows.append([(f"{w['days']}日跌≥{w['drawdown_pct']:.0f}%", TEXT), (fmt(w.get("auc_in"), 2), MUTED),
                     (fmt(w.get("auc_oos"), 2), GREEN if (w.get("auc_oos") or 0) >= 0.65 else ORANGE),
                     (f"{sk_:+.0f}%", GREEN if sk_ > 5 else MUTED), (w.get("verdict", "—"), TEXT)])
    y = 250
    if rows:
        y = s.table(["情境", "樣本內AUC", "樣本外AUC", "Brier技能分", "判讀"], rows, y, [0.26, 0.17, 0.17, 0.2, 0.2], size=36, row_h=80)
    es = ql.get("episode_summary") or {}
    y += 40
    if es.get("n"):
        lead = f"，領先高點中位數 {es['median_lead_days']:.0f} 個交易日" if es.get("median_lead_days") is not None else ""
        y = s.paragraph(f"歷史上 {es['n']} 次標普≥10% 回檔：高點前已預警 {es['warned_before_peak']} 次，期間曾預警 {es['warned_any']} 次{lead}。",
                        M, y, W - 2 * M, size=34, color=TEXT) + 14
    bm = (engine.breaks or {}).get("metrics", {})
    if bm.get("stock_bond_corr"):
        c = bm["stock_bond_corr"]
        y = s.paragraph(f"股債 {c['window']} 日相關係數 {c['value']:+.2f}（歷史 {c['pctile']:.0f}% 分位）；"
                        + (f"近 20 日雙殺日 {bm['double_kill_20d']['value']} 天；" if bm.get("double_kill_20d") else "")
                        + (f"股票跌≥1% 時長債與黃金同跌比例 {bm['haven_fail']['value']:.0f}%。" if bm.get("haven_fail") else ""),
                        M, y, W - 2 * M, size=32, color=MUTED) + 14
    for f in (engine.breaks or {}).get("flags", [])[:2]:
        y = s.paragraph("警示：" + f["detail"], M, y, W - 2 * M, size=30, color=RED) + 8
    return s


def _events(engine, tag: str) -> Slide:
    evs = _liq_events(engine, 28)
    s = Slide("事件日曆：流動性與供給衝擊", tag, "選擇權到期、月/季底再平衡、美債標售、FOMC —— 這些日子市場更容易被『機械式買賣』推動")
    imp = {3: ("重要", RED), 2: ("留意", ORANGE), 1: ("一般", MUTED)}
    rows = []
    for e in evs[:9]:
        lab, c = ("FOMC", RED) if e["type"] == "fomc" else imp.get(e.get("importance", 1), ("一般", MUTED))
        rows.append([(e["date"], TEXT), (lab, c), (e["event"], TEXT)])
    if not rows:
        rows = [[("—", MUTED), ("—", MUTED), ("近期無事件", MUTED)]]
    s.table(["日期", "等級", "事件"], rows, 250, [0.17, 0.12, 0.71], size=34, row_h=82, align=["l", "c", "l"])
    return s


def _lab(engine, tag: str) -> Slide:
    lab = getattr(engine, "lab", None) or {}
    s = Slide("特徵實驗室：新指標真的有用嗎？", tag,
              "每個候選指標都加進模型做走步外樣本檢驗，並對照『時間錯位的安慰劑』；沒贏過安慰劑的一律不採用")
    hz = next((h for h in lab.get("horizons", []) if h["days"] == 63), None) or (lab.get("horizons") or [None])[0]
    if not hz or not hz.get("baseline"):
        s.paragraph("實驗室尚在計算或資料不足。", M, 260, W - 2 * M, size=40)
        return s
    rows = []
    for f in hz["features"][:8]:
        rows.append([(f["label"][:28], TEXT), (f"{f['d_auc']:+.3f}", GREEN if f["adopt"] else MUTED),
                     (f"{f['years_better']}/{f['years']}", MUTED),
                     ("採用" if f["adopt"] else ("未勝過安慰劑" if not f.get("beats_placebo") else "未達門檻"), GREEN if f["adopt"] else MUTED)])
    y = s.table(["候選指標（%d日跌≥%d%%）" % (hz["days"], hz["drawdown_pct"]), "AUC 增益", "進步年數", "結論"], rows, 235,
                [0.5, 0.15, 0.15, 0.2], size=30, row_h=64)
    y += 28
    b, e, now = hz["baseline"], hz.get("ensemble"), hz.get("now") or {}
    line = f"基準（只用 SSI）樣本外 AUC {b['auc']:.2f}；安慰劑最高增益 {hz['null_max_d_auc']:+.3f}。"
    if e:
        line += f"增強模型 AUC {e['auc']:.2f}（{e['d_auc']:+.2f}），Brier 技能 {(e['skill'] or 0) * 100:+.0f}%：" + ("通過，採用。" if e["accepted"] else "未通過，沿用原模型。")
    else:
        line += "沒有任何候選通過檢驗，沿用原模型（誠實的結論：目前沒有找到更好的指標）。"
    y = s.paragraph(line, M, y, W - 2 * M, size=30, color=TEXT) + 6
    if now.get("p_enh_cal") is not None and e and e["accepted"]:
        s.paragraph(f"目前 {hz['days']} 日內跌≥{hz['drawdown_pct']:.0f}% 的機率：增強模型 {now['p_enh_cal']:.1f}%（校準後；原始 {now['p_enh']:.1f}%），"
                    f"僅用 SSI 為 {now['p_base_cal'] if now.get('p_base_cal') is not None else now['p_base']:.1f}%。", M, y, W - 2 * M, size=30, color=ACCENT)
    elif now.get("p_base_cal") is not None:
        s.paragraph(f"校準後的機率（僅用 SSI）：{now['p_base_cal']:.1f}%；用歷史樣本外表現修正過度自信。", M, y, W - 2 * M, size=30, color=MUTED)
    return s


def _w_review(f: dict, tag: str) -> Slide:
    s = Slide("每週復盤：本週發生了什麼", tag, f"{f['asof']} 週日｜客觀數據由程式計算")
    sp = f.get("spx_week")
    pf = f.get("pf_week")
    st_txt = f.get("stage") or "—"
    if f.get("stage_prev") and f["stage_prev"] != f.get("stage"):
        st_txt += f"（上週 {f['stage_prev']}）"
    y = s.kpis([("標普500 週漲跌", f"{sp:+.1f}%" if sp is not None else "—", GREEN if (sp or 0) >= 0 else RED),
                ("SSI 壓力指數", f"{f['ssi']:.0f}（{f['ssi_chg']:+.0f}）" if f.get("ssi") is not None and f.get("ssi_chg") is not None else "—",
                 level_color(f.get("ssi"))),
                ("風險階段", st_txt, STAGE_COL[f["stage_idx"]] if f.get("stage_idx") is not None else TEXT),
                ("持倉週報酬", f"{pf:+.1f}%" if pf is not None else "—", GREEN if (pf or 0) >= 0 else RED)], 235)
    rows = [[(sev.split(" ")[0] if sev else "", RED if sev.startswith("🚨") else ORANGE), (t, TEXT)] for sev, t in f["alerts_top"]]
    if not rows:
        rows = [[("—", MUTED), ("本週沒有風險警報", MUTED)]]
    s.d.text((M, y + 50), f"本週警報 {f['alerts_total']} 則（緊急 {f['alerts_crit']}）", font=font(36, True), fill=TEXT, anchor="lm")
    s.table(["等級", "內容"], rows, y + 90, [0.12, 0.88], size=30, row_h=62, align=["l", "l"])
    return s


def _w_pf(f: dict, tag: str) -> Slide:
    s = Slide("持倉週歸因：誰貢獻、誰拖累", tag, "近 5 個交易日；貢獻 = 該持股報酬 × 期初權重（百分點）")
    cs = sorted(f.get("pf_contrib") or [], key=lambda c: -c.get("contrib", 0))
    rows = [[(c["sym"], TEXT), (f"{c['ret']:+.1f}%", GREEN if c["ret"] >= 0 else RED),
             (f"{c['contrib']:+.2f}", GREEN if c["contrib"] >= 0 else RED)] for c in cs[:10]]
    if not rows:
        rows = [[("—", MUTED), ("無持倉資料", MUTED), ("", MUTED)]]
    s.table(["代號", "週報酬", "貢獻（百分點）"], rows, 235, [0.4, 0.3, 0.3], size=36, row_h=72)
    return s


def _w_next(f: dict, tag: str) -> Slide:
    s = Slide("下週展望與預警成績單", tag, "事件日 + 我們的警報規則過去到底準不準（對照歷史基準）")
    kind = {"fomc": ("FOMC", RED), "macro": ("總經", YELLOW), "earnings": ("財報", ACCENT), "liquidity": ("流動性", ORANGE)}
    rows = [[(e["date"][5:], TEXT), (kind.get(e["type"], ("", TEXT))[0], kind.get(e["type"], ("", TEXT))[1]), (e["event"][:26], TEXT)]
            for e in f["events"][:6]] or [[("—", MUTED), ("—", MUTED), ("下週無重大事件", MUTED)]]
    y = s.table(["日期", "類型", "事件"], rows, 235, [0.14, 0.16, 0.7], size=30, row_h=58, align=["l", "c", "l"])
    fam = f.get("families") or {}
    frows = []
    for name, fm in sorted(fam.items(), key=lambda kv: -kv[1]["episodes"])[:5]:
        r = fm["by_horizon"].get(max(fm["by_horizon"])) if fm["by_horizon"] else None
        if r and r.get("episodes"):
            frows.append([(name, TEXT), (str(r["episodes"]), MUTED), (f"{r['hit_rate']:.0f}%", ORANGE), (f"{r['base_rate']:.0f}%", MUTED),
                          (fm["verdict"], GREEN if fm["verdict"] == "有用" else RED if fm["verdict"] == "反效果" else MUTED)])
        else:
            frows.append([(name, TEXT), ("0", MUTED), ("待評分", MUTED), ("—", MUTED), ("樣本不足", MUTED)])
    if not frows:
        frows = [[("尚無可評分的警報", MUTED), ("", MUTED), ("", MUTED), ("", MUTED), ("", MUTED)]]
    s.table(["警報規則", "次數", "命中率", "基準", "評語"], frows, y + 50, [0.32, 0.14, 0.18, 0.16, 0.2], size=30, row_h=58)
    return s


def deck_weekly(f: dict) -> List[bytes]:
    bs = [_w_review, _w_pf, _w_next]
    return [b(f, f"{i}/{len(bs)}").png() for i, b in enumerate(bs, 1)]


def embed_weekly(f: dict) -> discord.Embed:
    from .. import weekly as WK
    e = discord.Embed(title="📅 每週復盤", description=WK.facts_text(f)[:4000], color=0x3498DB)
    return e


def _x_div(x: dict, tag: str) -> Slide:
    d = x.get("div") or {}
    s = Slide("持倉 X 光①：你其實押了幾個獨立的賭注？", tag, "用過去 1 年的實際報酬相關性還原：看起來分散，不代表風險分散")
    if not d.get("available"):
        s.paragraph("持股少於 2 檔或歷史資料不足，無法計算。", M, 260, W - 2 * M, size=40)
        return s
    y = s.kpis([("持股檔數", str(d["n_positions"]), TEXT), ("依權重的有效檔數", f"{d['eff_n_weight']:.1f}", TEXT),
                ("獨立押注數（ENB）", f"{d['enb']:.1f}", RED if d["enb"] < d["n_used"] * 0.5 else GREEN),
                ("加權平均相關", f"{d['avg_corr']:.2f}", RED if d["avg_corr"] >= 0.6 else ORANGE if d["avg_corr"] >= 0.4 else GREEN)], 235)
    rows = [[("、".join(c["members"])[:30], TEXT), (f"{c['weight']:.0f}%", ORANGE), (f"{c['avg_corr']:.2f}", RED)] for c in d["clusters"][:5]]
    if not rows:
        rows = [[("沒有相關係數 ≥ %.1f 的群聚" % d["cluster_thr"], GREEN), ("", MUTED), ("", MUTED)]]
    y = s.table(["同漲同跌的群聚（相關 ≥ %.1f）" % d["cluster_thr"], "合計權重", "群內相關"], rows, y + 40, [0.6, 0.2, 0.2], size=34, row_h=70)
    s.paragraph(f"ENB（有效獨立押注數）用主成分分析計算風險真正來自幾個互不相關的來源；{d['n_positions']} 檔持股只相當於 {d['enb']:.1f} 個獨立押注，"
                f"表示大跌時多數持股會一起跌。分散比 {d['div_ratio']:.2f}（1 = 完全沒分散）。" if d.get("div_ratio") else "",
                M, y + 40, W - 2 * M, size=30, color=MUTED)
    return s


def _x_scen(x: dict, tag: str) -> Slide:
    sc = x.get("scen") or {}
    s = Slide("持倉 X 光②：自訂情境壓力測試", tag, "用多因子迴歸（大盤、利率、美元、半導體）估算各持股的敏感度；其他因子假設不變")
    if not sc.get("available"):
        s.paragraph("因子資料不足。", M, 260, W - 2 * M, size=40)
        return s
    rows = []
    for r in sc["scenarios"]:
        worst = "、".join(f"{w['sym']} {w['ret_pct']:+.0f}%" for w in r["worst"][:2])
        rows.append([(r["name"][:26], TEXT), (f"{r['pnl_pct']:+.1f}%", pn(r["pnl_pct"])), (fmt(r["pnl_usd"], 0, money=True, sign=True), pn(r["pnl_usd"])),
                     (worst, MUTED)])
    y = s.table(["情境", "持倉損益", "金額", "最受傷"], rows, 235, [0.38, 0.14, 0.18, 0.30], size=30, row_h=84, align=["l", "r", "r", "r"])
    r2 = sc.get("r2")
    s.paragraph(f"模型解釋力 R² 約 {r2 * 100:.0f}%（越低，情境估計越不可靠）。" if r2 is not None else "", M, y + 40, W - 2 * M, size=30, color=MUTED)
    if sc.get("n_proxy"):
        s.paragraph(f"{sc['n_proxy']} 檔歷史不足，以大盤 β 估計。", M, y + 100, W - 2 * M, size=28, color=MUTED)
    return s


def _x_stops(x: dict, tag: str) -> Slide:
    s = Slide("持倉 X 光③：波動停損線與波動率目標", tag, "停損線 = 22 日最高收盤 − 3 × 14 日平均波幅（由波動決定，不是固定百分比）")
    rows = []
    for r in (x.get("stops") or [])[:8]:
        rows.append([(r["sym"], TEXT), (fmt(r["price"], 2), TEXT), (fmt(r["stop"], 2), MUTED),
                     (f"{r['dist_pct']:+.1f}%", RED if r["breached"] else ORANGE if r["dist_pct"] < 3 else GREEN),
                     ("已跌破" if r["breached"] else "安全", RED if r["breached"] else GREEN)])
    y = s.table(["持股", "現價", "停損線", "距離", "狀態"], rows or [[("—", MUTED)] + [("", MUTED)] * 4], 235, [0.2, 0.2, 0.2, 0.2, 0.2], size=32, row_h=62)
    v = x.get("vol") or {}
    if v.get("available"):
        col = RED if v["scale"] < 0.8 else ORANGE if v["scale"] < 1 else GREEN
        line = (f"持倉年化波動：20 日 {v['vol20']:.0f}%、60 日 {v['vol60']:.0f}%、1 年 {v['vol252']:.0f}%；目標 {v['target']:.0f}%。")
        line2 = (f"波動已超標：依目標建議把曝險縮到 {v['scale'] * 100:.0f}%（減 {fmt(v['trim_usd'], 0, money=True)}）。" if v["scale"] < 1
                 else "波動在目標之內，不需要縮減曝險。")
        s.paragraph(line, M, y + 40, W - 2 * M, size=30, color=TEXT)
        s.paragraph(line2, M, y + 100, W - 2 * M, size=32, color=col, bold=True)
    return s


def _x_events(x: dict, tag: str) -> Slide:
    ev = x.get("events") or {}
    s = Slide("持倉 X 光④：未來 14 天的事件暴露", tag, f"財報部位合計權重 {ev.get('earnings_weight', 0):.0f}%")
    rows = [[(e["date"], TEXT), (e["sym"], TEXT), (f"{e['weight']:.0f}%", ORANGE)] for e in ev.get("earnings", [])[:7]]
    y = 235
    if rows:
        y = s.table(["日期", "持股財報", "權重"], rows, 235, [0.3, 0.4, 0.3], size=34, row_h=66)
    else:
        s.paragraph("未來 14 天沒有持股財報。", M, 245, W - 2 * M, size=36, color=GREEN)
        y = 330
    if ev.get("macro"):
        s.paragraph("全市場事件：" + "；".join(f"{e['date'][5:]} {e['event'][:14]}" for e in ev["macro"][:5]), M, y + 40, W - 2 * M, size=30, color=MUTED)
    return s


def deck_xray(engine) -> List[bytes]:
    x = getattr(engine, "xray", None) or {}
    if not x.get("available"):
        s = Slide("持倉 X 光", "1/1")
        s.paragraph("持倉資料尚未就緒或為空。", M, 260, W - 2 * M, size=44)
        return [s.png()]
    bs = [_x_div, _x_scen, _x_stops, _x_events]
    return [b(x, f"{i}/{len(bs)}").png() for i, b in enumerate(bs, 1)]


def embed_xray(engine) -> discord.Embed:
    x = getattr(engine, "xray", None) or {}
    e = discord.Embed(title="🩻 持倉 X 光", color=0x1ABC9C)
    d = x.get("div") or {}
    if d.get("available"):
        e.add_field(name="分散度", value=f"{d['n_positions']} 檔 ≈ {d['enb']:.1f} 個獨立押注；平均相關 {d['avg_corr']:.2f}", inline=False)
        for c in d["clusters"][:3]:
            e.add_field(name=f"群聚 {c['weight']:.0f}%", value="、".join(c["members"]), inline=True)
    for r in (x.get("scen") or {}).get("scenarios", [])[:5]:
        e.add_field(name=r["name"][:40], value=f"{r['pnl_pct']:+.1f}%（{r['pnl_usd']:+,.0f} USD）", inline=False)
    br = [r["sym"] for r in x.get("stops", []) if r["breached"]]
    e.add_field(name="跌破停損線", value="、".join(br) or "無", inline=False)
    return e


def deck_command(engine) -> List[bytes]:
    if not engine.stress or not engine.playbook:
        s = Slide("戰情總控台", "1/1")
        s.paragraph("資料引擎尚在計算，請稍後再試。", M, 260, W - 2 * M, size=48)
        return [s.png()]
    builders = [_control, _paths, _playbook, _quality, _lab, _events]
    return [b(engine, f"{i}/{len(builders)}").png() for i, b in enumerate(builders, 1)]


def deck_shock(engine) -> List[bytes]:
    if not engine.shock:
        s = Slide("衝擊雷達", "1/1")
        s.paragraph("衝擊雷達尚在計算（需要完整歷史資料），請稍後再試。", M, 260, W - 2 * M, size=44)
        return [s.png()]
    builders = [_paths, _radar, _quality, _lab]
    return [b(engine, f"{i}/{len(builders)}").png() for i, b in enumerate(builders, 1)]


# ------------------------------------------------------------------ embeds (classic style)
def embed_command(engine) -> discord.Embed:
    pbk = engine.playbook or {}
    e = discord.Embed(title=f"🎛️ 戰情總控台：{pbk.get('emoji', '')} {pbk.get('name', '計算中')}（風險分 {pbk.get('points', '—')}）",
                      color=[0x2ECC71, 0xF1C40F, 0xE67E22, 0xE74C3C][pbk.get("stage", 0)])
    if pbk.get("why"):
        e.add_field(name="為什麼", value="\n".join(f"+{p} {w}" for p, w in pbk["why"])[:1000], inline=False)
    e.add_field(name="該做什麼", value="\n".join(f"{i}. {a}" for i, a in enumerate(pbk.get("actions", []), 1))[:1000] or "—", inline=False)
    sk = engine.shock or {}
    if sk.get("paths"):
        e.add_field(name="衝擊路徑", value="\n".join(f"{p['name']} {p['ignition']:.0f}［{p['state']}］" for p in sk["paths"][:4]), inline=True)
    for f in (engine.breaks or {}).get("flags", [])[:2]:
        e.add_field(name="⚠ " + f["title"], value=f["detail"][:300], inline=False)
    ev = _liq_events(engine, 14)[:5]
    if ev:
        e.add_field(name="近期事件", value="\n".join(f"`{x['date']}` {x['event']}" for x in ev), inline=False)
    return e


def embed_shock(engine) -> discord.Embed:
    sk = engine.shock or {}
    e = discord.Embed(title="📡 衝擊雷達", color=0x8E44AD)
    e.description = "\n".join(f"**{p['name']}** 點火 {p['ignition']:.0f}［{p['state']}］— {p['story']}" for p in sk.get("paths", [])[:6])[:4000] or "計算中"
    return e


# ------------------------------------------------------------------ /intel: news × prices × macro fusion
FUSE_COL = {"確認": RED, "無聲壓力": ORANGE, "敘事領先": YELLOW, "平靜": GREEN}
LEVEL_COL = {"高": RED, "偏高": ORANGE, "中性": YELLOW, "低": GREEN}
_ID_RE = None


def _zh(text: str) -> str:
    """Show SSI component ids (spx_trend, hy_oas…) under their Chinese names on human-facing views."""
    global _ID_RE
    import re
    if _ID_RE is None:
        _ID_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, S.COMP_NAMES), key=len, reverse=True)) + r")\b")
    return _ID_RE.sub(lambda m: S.COMP_NAMES[m.group(1)], text or "")


def _i_verdict(engine, tag: str) -> Slide:
    itl = engine.intel or {}
    v = itl.get("verdict") or {}
    col = LEVEL_COL.get(v.get("label"), MUTED)
    s = Slide("情報融合：綜合風險判斷", tag, "量化（壓力指數）× 總經（象限／流動性）× 情報（新聞傳導路徑），每一分都可追溯")
    s.card((M, 235, 700, 1005), outline=col, width=4)
    s.d.text((385, 300), "綜合風險", font=font(38, True), fill=MUTED, anchor="mm")
    s.d.text((385, 450), v.get("label", "計算中"), font=font(150, True), fill=col, anchor="mm")
    s.d.text((385, 580), f"{v['score']:.0f} / 100" if v.get("available") else "—", font=font(56, True), fill=TEXT, anchor="mm")
    s.d.text((385, 660), f"信心：{v.get('confidence', '—')}", font=font(40, True), fill=TEXT, anchor="mm")
    s.d.text((385, 720), v.get("consensus", ""), font=s.fit(v.get("consensus", ""), 30, 560), fill=MUTED, anchor="mm")
    y = 790
    for c in (v.get("caveats") or [])[:3]:
        y = s.paragraph("· " + c, 110, y, 550, size=24, color="#6E7781") + 4
    rows = [(f"{k}（權重 {v.get('weights', {}).get(k, 0):.0%}）", val, fmt(val, 0) if val is not None else "資料缺")
            for k, val in (v.get("pillars") or {}).items()]
    s.d.text((760, 260), "三大支柱（0–100，越高越危險）", font=font(34, True), fill=TEXT, anchor="lm")
    s.bars([(a, b if b is not None else 0, c) for a, b, c in rows], (760, 300, W - M, 560), label_w=380, size=34)
    rg = itl.get("regime") or {}
    y = 600
    s.d.text((760, y), "總經背景", font=font(34, True), fill=TEXT, anchor="lm")
    q1 = rg.get("quadrant_1m")
    txt = (f"象限「{rg.get('quadrant') or '—'}」"
           + ((f"（一個月前「{q1}」，已轉換）" if rg.get("quadrant_changed") else "（與一個月前相同）") if q1 else "")
           + (f"；{rg['drift']}" if rg.get("drift") else "") + f"；{rg.get('risk_mode') or '—'}；流動性 {rg.get('liquidity_mode') or '—'}")
    y = s.paragraph(txt, 760, y + 40, W - M - 760, size=30, color=MUTED) + 44
    lead = next((r for r in itl.get("channels", []) if r["state"] != "平靜"), None)
    s.d.text((760, y), "主軸", font=font(34, True), fill=TEXT, anchor="lm")
    if lead:
        s.paragraph(f"{lead['channel']}［{lead['state']}］— {lead['explain']}", 760, y + 40, W - M - 760, size=30,
                    color=FUSE_COL[lead["state"]])
    else:
        s.paragraph("六條傳導路徑的新聞與價格都沒有異常。", 760, y + 40, W - M - 760, size=30, color=GREEN)
    return s


def _i_channels(engine, tag: str) -> Slide:
    itl = engine.intel or {}
    s = Slide("傳導路徑：新聞有沒有被價格確認？", tag,
              "市場點火＝衝擊雷達（價格）；新聞熱度＝該路徑新聞量相對自身 30 日的百分位；融合＝65% 價格 + 35% 新聞")
    rows = []
    for r in itl.get("channels", [])[:6]:
        ign = r["ignition"]
        rows.append([(r["channel"], TEXT), (r["state"], FUSE_COL[r["state"]]),
                     (fmt(ign, 0) if ign is not None else "—", level_color(ign)),
                     (f"{r['news_level']:.0f}（{r['news_n']}則）" + ("*" if r["warmup"] else ""), level_color(r["news_level"])),
                     (f"{r['fused']:.0f}", level_color(r["fused"]))])
    y = s.table(["傳導路徑", "狀態", "市場點火", "新聞熱度", "融合"], rows, 235, [0.3, 0.17, 0.15, 0.22, 0.16],
                size=34, row_h=74, align=["l", "c", "r", "r", "r"]) + 30
    for r in [x for x in itl.get("channels", []) if x["state"] != "平靜"][:2]:
        if y > 960:
            break
        s.d.text((M, y), f"{r['channel']}［{r['state']}］", font=font(32, True), fill=FUSE_COL[r["state"]])
        y += 46
        if r["top"]:
            y = s.paragraph(f"頭條（{r['top'][0]['source']}）：{r['top'][0]['title']}", M, y, W - 2 * M, size=26, color=TEXT) + 2
        if r["watch"]:
            y = s.paragraph(_zh(r["watch"]), M, y, W - 2 * M, size=26, color=MUTED) + 14
    if any(r["warmup"] for r in itl.get("channels", [])):
        s.d.text((M, 1030), "* 新聞熱度基準仍在累積，暫以絕對熱度估計", font=font(24), fill="#6E7781", anchor="lm")
    return s


def _i_ledger(engine, tag: str) -> Slide:
    itl = engine.intel or {}
    v = itl.get("verdict") or {}
    s = Slide("證據帳本與觀察清單", tag, "推升（＋）與緩解（－）綜合風險的每一項證據；以及什麼數據會改變判斷")
    y = 235
    pc = {"量化": ACCENT, "總經": YELLOW, "情報": ORANGE, "融合": RED}
    for e in (v.get("ledger") or [])[:10]:
        if y > 700:
            break
        if e["dir"] == "=":
            tag_ = f"{e['pillar']} 基準"
        else:
            tag_ = f"{e['pillar']} {e['dir']}" + (f"{abs(e['pts']):.0f}" if e.get("pts") is not None else "")
        s.d.text((M, y + 20), tag_, font=font(30, True), fill=pc.get(e["pillar"], MUTED), anchor="lm")
        y = s.paragraph(_zh(e["text"]), M + 190, y, W - 2 * M - 190, size=28, color=GREEN if e["dir"] == "-" else TEXT) + 8
    y = max(y + 20, 730)
    s.d.text((M, y), "觀察清單（確認／轉向條件）", font=font(34, True), fill=ACCENT)
    y += 52
    for w_ in (itl.get("watch") or ["目前沒有需要特別追蹤的條件"])[:5]:
        if y > 1010:
            break
        y = s.paragraph("· " + _zh(w_), M, y, W - 2 * M, size=26, color=MUTED) + 4
    return s


def deck_intel(engine) -> List[bytes]:
    if not (engine.intel or {}).get("verdict", {}).get("available"):
        s = Slide("情報融合", "1/1")
        s.paragraph("情報融合尚在計算（需要壓力指數、總經與新聞資料），請稍後再試。", M, 260, W - 2 * M, size=44)
        return [s.png()]
    builders = [_i_verdict, _i_channels, _i_ledger]
    return [b(engine, f"{i}/{len(builders)}").png() for i, b in enumerate(builders, 1)]


def embed_intel(engine) -> discord.Embed:
    itl = engine.intel or {}
    v = itl.get("verdict") or {}
    e = discord.Embed(title="🧩 情報融合：" + (v.get("headline", "計算中") if v.get("available") else "計算中")[:240],
                      color={"高": 0xE74C3C, "偏高": 0xE67E22, "中性": 0xF1C40F, "低": 0x2ECC71}.get(v.get("label"), 0x95A5A6))
    if v.get("available"):
        e.description = (f"信心 **{v['confidence']}** · {v['consensus']}"
                         + ("\n" + "；".join(v["caveats"]) if v["caveats"] else ""))[:4000]
    ch = itl.get("channels") or []
    if ch:
        e.add_field(name="傳導路徑（新聞 × 價格）", inline=False, value="\n".join(
            f"**{r['channel']}**［{r['state']}］融合 {r['fused']:.0f}｜點火 {fmt(r['ignition'], 0)}｜新聞 {r['news_level']:.0f}（{r['news_n']}則）"
            for r in ch)[:1024])
    led = [x for x in (v.get("ledger") or [])][:8]
    if led:
        e.add_field(name="證據帳本", inline=False,
                    value="\n".join(f"{x['pillar']}{'' if x['dir'] == '=' else x['dir']} {_zh(x['text'])}" for x in led)[:1024])
    if itl.get("watch"):
        e.add_field(name="觀察清單", inline=False, value="\n".join("· " + _zh(w) for w in itl["watch"])[:1024])
    return e
