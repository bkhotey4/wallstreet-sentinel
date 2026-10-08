"""Builds a compact, number-dense DATA PACK from live engine state.
The AI may only reason over what is in this pack."""
from __future__ import annotations

from datetime import datetime
from typing import List
from zoneinfo import ZoneInfo

from ..config import SETTINGS
from ..health import HEALTH
from .. import store


def f(x, d=2, pct=False, sign=False):
    if x is None:
        return "NA"
    try:
        s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    except (TypeError, ValueError):
        return "NA"
    return s + ("%" if pct else "")


def market_lines(engine, groups: List[str]) -> List[str]:
    names = SETTINGS.names()
    out = []
    for g in groups:
        rows = engine.market.returns_table(SETTINGS.group(g))
        if not rows:
            continue
        out.append(f"[{g}]")
        for r in rows:
            out.append(f"{names.get(r['ticker'], r['ticker'])}({r['ticker']}) {f(r['price'])} "
                       f"1D {f(r['d1'], sign=True, pct=True)} 1W {f(r.get('w1'), 1, pct=True, sign=True)} "
                       f"1M {f(r.get('m1'), 1, pct=True, sign=True)} 3M {f(r.get('m3'), 1, pct=True, sign=True)} "
                       f"YTD {f(r.get('ytd'), 1, pct=True, sign=True)} σ {f(r.get('sigma'), 1, sign=True)} "
                       f"52週位置 {f(r.get('pct_52w'), 0)}% @{r.get('asof')}")
    return out


def build(engine, focus: str = "full", private: bool = True) -> str:
    """private=False → nothing about the owner's holdings (positions, P&L, x-ray, de-risk names) for public replies."""
    tz = ZoneInfo(SETTINGS.get("timezone", "Asia/Taipei"))
    L = [f"### DATA PACK 產生時間 {datetime.now(tz):%Y-%m-%d %H:%M} 台北 | 焦點={focus}"]
    if not private:
        L.append("（公開模式：本資料包不含使用者持倉；回答不得提及或推測使用者的部位）")
    st = engine.stress
    if st:
        L.append(f"## 系統性壓力指數 SSI {st.score:.1f}/100 [{st.label}] 歷史百分位 {f(st.pctile_all, 0)}% "
                 f"| 1D {f(st.chg_1d, 1, sign=True)} 5D {f(st.chg_5d, 1, sign=True)} 20D {f(st.chg_20d, 1, sign=True)} "
                 f"| 資料覆蓋 {st.coverage*100:.0f}%")
        ex = [f"{c.id}[{c.status}]" for c in st.components if c.score is None]
        if ex:
            L.append("未納入本次計算的因子（資料缺/過期）: " + ", ".join(ex))
        L.append("區塊: " + ", ".join(f"{k} {v:.0f}" for k, v in sorted(st.blocks.items(), key=lambda x: -x[1])))
        L.append("主要推升因子: " + "; ".join(f"{c.id}={f(c.raw, 4)} z{f(c.z, 2, sign=True)} 分{c.score:.0f}" for c in st.drivers(6)))
        L.append("主要緩解因子: " + "; ".join(f"{c.id}={f(c.raw, 4)} z{f(c.z, 2, sign=True)} 分{c.score:.0f}" for c in st.relief(3)))
    if engine.odds.get("horizons"):
        L.append(f"## 經驗崩跌機率 (SSI區間 {engine.odds.get('bucket')}, 樣本自 {engine.odds.get('sample_start')})")
        mom = engine.odds.get("momentum") or {}
        L.append(f"SSI 20日變化 {f(mom.get('chg20'), 1, sign=True)} 點，歷史百分位 {f(mom.get('pctile'), 0)}，升溫狀態={mom.get('state') or 'NA'}"
                 f"（門檻：升溫≥{f(mom.get('th_rising'), 1, sign=True)}、降溫≤{f(mom.get('th_falling'), 1, sign=True)}）")
        for h in engine.odds["horizons"]:
            L.append(f"{h['days']}交易日內跌≥{h['drawdown_pct']:.0f}%: 含升溫速度機率 {f(h.get('adjusted'), 1)}% "
                     f"(倍數 {f(h.get('lift_adj'), 2)}) | 僅看水準 {f(h['conditional'], 1)}% (倍數 {f(h['lift'], 2)}) | 基準 {f(h['base_rate'], 1)}% "
                     f"| 區間天數 {h['obs_in_zone']}, 獨立事件 {h['episodes_in_zone']}, 同升溫狀態天數 {h.get('cell_days')}")
        L.append("解讀規則：倍數>1 代表比歷史平常更危險，<1 代表較安全；以『含升溫速度』機率為主要數字。")
    sk = getattr(engine, "shock", None) or {}
    if sk.get("radar"):
        L.append("## 衝擊雷達（下一次衝擊可能從哪裡點火；水準＋升溫速度）")
        L.append("區塊: " + "; ".join(
            f"{r['block']} {r['level']:.0f}（20日{f(r['chg20'], 1, sign=True)}，升溫百分位{f(r['accel_pctile'], 0)}，{r['state']}"
            + (f"，歷史預警力AUC {f(r['auc'], 2)}" if r.get("auc") is not None else "") + "）" for r in sk["radar"][:6]))
        for p in sk.get("paths", [])[:3]:
            L.append(f"傳導路徑「{p['name']}」點火分數 {p['ignition']:.0f}[{p['state']}]（{'+'.join(p['blocks'])}）：{p['story']}")
        dv = sk.get("divergence") or {}
        if dv.get("available"):
            hs = dv.get("hist") or {}
            L.append(f"股債背離: 信用/利率/流動性/新興壓力 {dv['credit']:.0f} vs 股市隱含恐慌 {dv['equity']:.0f}，差 {dv['gap']:+.0f}（門檻 {dv['threshold']:.0f}）"
                     + ("【背離警示】" if dv["flag"] else "")
                     + (f"；歷史上背離時 63日內跌≥10% 機率 {f(hs.get('prob_when_flagged'), 1)}% vs 基準 {f(hs.get('base_rate'), 1)}%" if hs else ""))
        ql = sk.get("quality") or {}
        for w in ql.get("walk_forward", []):
            if w.get("n_test"):
                L.append(f"模型可信度（走步外樣本，{w['days']}日跌≥{w['drawdown_pct']:.0f}%）: AUC {f(w.get('auc_oos'), 2)}（{w.get('verdict')}），"
                         f"相對基準的 Brier 技能分數 {f(None if w.get('skill') is None else w['skill'] * 100, 0)}%")
        es = ql.get("episode_summary") or {}
        if es.get("n"):
            L.append(f"歷史 {es['n']} 次標普≥10%回檔：高點前已預警 {es['warned_before_peak']} 次，回檔期間才/曾預警共 {es['warned_any']} 次"
                     + (f"，領先中位數 {es['median_lead_days']:.0f} 個交易日" if es.get("median_lead_days") is not None else ""))
        lab = getattr(engine, "lab", None) or {}
        for hz in lab.get("horizons", []):
            if not hz.get("baseline"):
                continue
            e, now = hz.get("ensemble"), hz.get("now") or {}
            txt = f"特徵實驗室（{hz['days']}日跌≥{hz['drawdown_pct']:.0f}%）: 基準AUC {hz['baseline']['auc']:.2f}；"
            if e and e["accepted"]:
                txt += (f"採用 {','.join(hz['adopted'])}，增強模型AUC {e['auc']:.2f}（{e['d_auc']:+.2f}），校準後機率 {now['p_enh_cal']:.1f}% "
                        f"（僅SSI {now.get('p_base_cal', now['p_base']):.1f}%）")
            else:
                txt += "沒有候選指標通過走步檢驗與安慰劑對照，沿用原模型"
            L.append(txt)
        L.append("解讀規則：回答下一次衝擊時，以點火分數最高的傳導路徑為主軸，並誠實說明模型可信度（AUC<0.6 要提醒鑑別力有限）。")
    xr_ = (getattr(engine, "xray", None) or {}) if private else {}
    if xr_.get("available"):
        d = xr_.get("div") or {}
        if d.get("available"):
            L.append("## 持倉 X 光")
            L.append(f"持股 {d['n_positions']} 檔但只相當於 {d['enb']:.1f} 個獨立押注（ENB），加權平均相關 {d['avg_corr']:.2f}"
                     + ("；群聚：" + "；".join(f"{'+'.join(c['members'])} 合計{c['weight']:.0f}%" for c in d["clusters"][:3]) if d["clusters"] else ""))
        sc_ = xr_.get("scen") or {}
        if sc_.get("available"):
            L.append("自訂情境損益: " + "；".join(f"{r['name'][:14]} {r['pnl_pct']:+.1f}%" for r in sc_["scenarios"]))
        br = [r["sym"] for r in xr_.get("stops", []) if r["breached"]]
        if br:
            L.append("已跌破波動停損線: " + "、".join(br))
        v = xr_.get("vol") or {}
        if v.get("available") and v["scale"] < 1:
            L.append(f"持倉波動 {v['current']:.0f}% 超過目標 {v['target']:.0f}%，建議曝險縮到 {v['scale'] * 100:.0f}%")
    val = getattr(engine, "valuation", None) or {}
    if val.get("available"):
        from ..analytics import valuation as _va
        L.append("## 估值與泡沫觀察（慢變數：說明貴不貴，不負責抓時點）")
        L += _va.summary_lines(val)
    pbk = getattr(engine, "playbook", None) or {}
    if pbk:
        L.append("## 風險劇本（規則式階段，可追溯）")
        L.append(f"目前階段：{pbk['name']}（風險分 {pbk['points']}；0–1正常 2–3留意 4–5戒備 ≥6防禦）；觸發原因："
                 + ("；".join(w for _, w in pbk["why"]) or "無"))
        if pbk.get("actions") and private:
            L.append("系統建議行動：" + " / ".join(pbk["actions"]))
    br = getattr(engine, "breaks", None) or {}
    if br.get("available"):
        m = br["metrics"]
        sb = m.get("stock_bond_corr")
        L.append("## 避險有效性（股債/避險資產是否還有分散效果）")
        if sb:
            L.append(f"股債{sb['window']}日相關 {sb['value']:+.2f}（歷史{sb['pctile']:.0f}%分位，≥{sb['threshold']:+.2f}視為債券失去避險功能）")
        if m.get("double_kill_20d"):
            L.append(f"近20日股債雙殺日 {m['double_kill_20d']['value']} 天")
        if m.get("haven_fail"):
            L.append(f"股票跌≥1%的{m['haven_fail']['n']}天中，長債與黃金同跌比例 {m['haven_fail']['value']:.0f}%")
        for fl in br["flags"]:
            L.append("【警示】" + fl["detail"])
    liq = [e for e in engine.calendar.upcoming(21) if e["type"] == "liquidity" and e.get("importance", 0) >= 2]
    if liq:
        L.append("## 近期流動性事件: " + "；".join(f"{e['date']} {e['event']}" for e in liq[:6]))
    itl = getattr(engine, "intel", None) or {}
    v = itl.get("verdict") or {}
    if v.get("available"):
        L.append("## 情報融合（量化 × 總經 × 新聞情報 → 綜合風險）")
        L.append(f"{v['headline']}；三方一致度 {v['consensus']}，信心 {v['confidence']}"
                 + (f"；限制：{'；'.join(v['caveats'])}" if v["caveats"] else ""))
        for r in itl.get("channels", []):
            L.append(f"{r['channel']}［{r['state']}］融合 {r['fused']:.0f}：市場點火 {f(r['ignition'], 0)}({r['market_state'] or 'NA'}) "
                     f"新聞熱度 {r['news_level']:.0f}({r['news_state']}，{r['news_n']} 則風險/{r['relief_n']} 則緩和"
                     + ("，基準累積中" if r["warmup"] else "") + ")"
                     + (f"；頭條：{r['top'][0]['title'][:90]}" if r["top"] else "")
                     + (f"；{r['watch']}" if r["watch"] else ""))
        if itl.get("watch"):
            L.append("觀察清單: " + "；".join(itl["watch"]))
        L.append("解讀規則：『確認』= 新聞與價格同時示警，最可信；『敘事領先』= 只有新聞，需等價格確認，勿過度反應；"
                 "『無聲壓力』= 只有價格，常被低估。只有量化支柱有回測，綜合分數是透明的判斷框架而非預測模型。")
    rg = engine.regime
    if rg:
        L.append(f"## 總經情勢 象限={rg.get('quadrant','NA')} 成長z {f(rg.get('growth_z'))} 通膨z {f(rg.get('inflation_z'))} "
                 f"風險偏好={rg.get('risk_mode','NA')}(z {f(rg.get('risk_appetite_z'))}) "
                 f"淨流動性 {f(rg.get('net_liquidity_bn'), 0)}bn 13週變化 {f(rg.get('net_liquidity_chg_13w_bn'), 0, sign=True)}bn {rg.get('liquidity_mode','')}")
        if rg.get("drift"):
            L.append(f"總經漂移（vs 一個月前象限「{rg.get('quadrant_1m')}」）：{rg['drift']}" + ("【象限已轉換】" if rg.get("quadrant_changed") else ""))
    if focus in ("full", "macro", "us", "asia", "europe", "portfolio"):
        L.append("## FRED 總經/信用/流動性")
        for sid, name in SETTINGS.get("fred_series", {}).items():
            x = engine.fred.latest(sid)
            if x:
                L.append(f"{name}({sid}) {f(x['value'], 3)} @{x['date']} 1M {f(x['chg_1m'], 3, sign=True)} "
                         f"3M {f(x['chg_3m'], 3, sign=True)} 1Y {f(x['chg_1y'], 3, sign=True)} 3年百分位 {f(x.get('pctile_3y'), 0)}")
    groups = {
        "full": list(SETTINGS.universe.keys()),
        "us": ["us_equity", "volatility", "rates", "credit", "sectors", "fx", "commodities"],
        "asia": ["asia", "fx", "us_equity", "volatility", "commodities", "emerging"],
        "europe": ["europe", "fx", "rates", "credit", "volatility", "commodities"],
        "crypto": ["crypto", "us_equity", "fx", "volatility"],
        "macro": ["rates", "credit", "fx", "commodities", "volatility"],
        "portfolio": ["us_equity", "volatility", "sectors", "rates", "credit"],
    }.get(focus, list(SETTINGS.universe.keys()))
    L.append("## 全球跨資產報價 (σ=今日漲跌 / 自身60日波動)")
    L += market_lines(engine, groups)
    op = engine.options.spx
    if op:
        L.append(f"## SPX 選擇權部位 (CBOE) spot {f(op.get('spot'),0)} GEX {f(op.get('gex_usd_bn_per_1pct'),2,sign=True)}bn/1% "
                 f"零Gamma {f(op.get('zero_gamma'),0)} (spot相對 {f(op.get('spot_vs_flip_pct'),2,sign=True,pct=True)}) "
                 f"Call牆 {f(op.get('call_wall'),0)} Put牆 {f(op.get('put_wall'),0)} P/C OI {f(op.get('put_call_oi'))} P/C Vol {f(op.get('put_call_volume'))}")
    if engine.crypto.data:
        d = engine.crypto.data
        L.append("## 情緒/加密 " + " ".join(f"{k}={f(v) if isinstance(v, (int, float)) else v}" for k, v in d.items()))
    pf = engine.portfolio if private else None
    if pf and not pf.get("error"):
        L.append(f"## 使用者持倉 總值 ${f(pf['total_value_usd'],0)} 未實現 {f(pf['pnl_pct'],1,sign=True,pct=True)} "
                 f"今日 ${f(pf['day_pnl_usd'],0,sign=True)} β {f(pf['beta'])} 年化波動 {f(pf['vol_ann_pct'],1)}% "
                 f"VaR99(1D) ${f(pf['var99_1d_usd'],0)} CVaR97.5 ${f(pf['cvar975_1d_usd'],0)} 有效檔數 {f(pf['effective_n'],1)}")
        for p in pf["positions"]:
            if "value_usd" in p:
                L.append(f"{p['sym']} 權重{f(p['weight'],1)}% 今日{f(p['d1_pct'],2,sign=True,pct=True)} σ{f(p['sigma'],1,sign=True)} "
                         f"損益{f(p['pnl_pct'],1,sign=True,pct=True)} β{f(p.get('beta'))} 風險貢獻{f(p.get('risk_contrib_pct'),1)}%")
        for s in pf.get("scenarios", []):
            L.append(f"情境 {s['name']}: 大盤 {f(s['bench_pct'],1,pct=True)} 持倉 {f(s['port_pct'],1,pct=True)} (${f(s['pnl_usd'],0)})")
    tw = getattr(engine, "taiwan", None)
    if tw is not None and (tw.flows or tw.futures):
        L.append("## 台灣籌碼（證交所/期交所）")
        L += tw.summary_lines()
    if engine.calendar.events:
        L.append("## 未來14天事件 " + "; ".join(f"{e['date']} {e['event']}" for e in engine.calendar.upcoming(14)[:20]))
    if engine.news.items:
        L.append("## 新聞(風險分數排序)")
        for n in engine.news.top(18):
            L.append(f"[{n.score}] {n.source}: {n.title}")
    if engine.sec.recent:
        L.append("## SEC 持股公告 " + "; ".join(f"{s['date']} {s['ticker']} {s['form']}({s['label']})" for s in engine.sec.recent[:10]))
    al = store.recent_alerts(24)
    if al:
        L.append("## 過去24h警報 " + "; ".join(t for _, _, t in al[:10]))
    L.append(f"## 資料健康 {HEALTH.summary()}")
    return "\n".join(L)
