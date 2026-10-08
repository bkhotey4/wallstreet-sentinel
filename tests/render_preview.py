"""Render sample slides from synthetic data → data_cache/preview/*.png
Run: python -m tests.render_preview"""
import types
from pathlib import Path

import tests.test_offline as T
from wsb.analytics.stress import StressEngine
from wsb.analytics import crash_odds, regime, portfolio, hedge as HG, scorecard as SC
from wsb.bot import slides as S
from wsb.config import DATA_DIR

out = Path(DATA_DIR) / "preview"
out.mkdir(parents=True, exist_ok=True)
st = StressEngine(T.m, T.fr).compute()
eng = types.SimpleNamespace(market=T.m, fred=T.fr, stress=st,
                            odds=crash_odds.crash_odds(st.history, T.m.series("^GSPC"), st.score),
                            regime=regime.classify(T.m, T.fr))
hold = {"NVDA": {"shares": 15, "cost": 50, "currency": "USD", "name": "NVDA"},
        "TSM": {"shares": 12, "cost": 60, "currency": "USD", "name": "TSM"},
        "NEWCO": {"shares": 10, "cost": 30, "currency": "USD", "name": "NEWCO"}}
eng.portfolio = portfolio.analyze(T.m, hold)
md = """**⚡ 一句話結論**
信用市場與波動率同步升溫，SSI 62（升溫），建議降低半導體集中度。

**🎯 情境推演（未來 1–4 週）**
| 情境 | 機率 | 觸發條件 | 標普 |
|---|---|---|---|
| 基準 | 55% | 利差持穩 | 震盪 |
| 空頭 | 30% | HY OAS 突破 4.5% | -8% |
| 多頭 | 15% | CPI 降溫 | +4% |

**🛡️ 持倉作戰指令**
- NVDA 風險貢獻 48%，建議減碼 1/3，停損 165
- TSM 維持，跌破 200 日線再減碼
- 以 SPY 90 天 5% 價外賣權保護核心部位
"""
decks = {"risk": S.deck_risk(eng, ("overview", "blocks", "markets", "trend", "crash")),
         "portfolio": S.deck_portfolio(eng),
         "text": S.deck_text("首席策略師研判", md, "gemini-3.1-flash-lite"),
         "alert": S.deck_alert("緊急風險警報", [("🚨 CRITICAL", "VIX 期限結構倒掛：VIX 24.1 > VIX3M 22.8", "近月恐慌高於遠月"),
                                              ("⚠️ WARNING", "異常波動：區域銀行 KRE -4.2%（-3.4σ）", "自身60日波動的 3.4 倍")], 66.0)}
from datetime import date, timedelta
import numpy as np
def chain(spot):
    rows = []
    for dte in (44, 91):
        exp = (date.today() + timedelta(days=dte)).isoformat()
        for k in range(int(spot * 0.8), int(spot * 1.1), 5):
            mid = max(k - spot, 0) + spot * 0.2 * (dte / 365) ** 0.5 * 0.4 * np.exp(-abs(k / spot - 1) * 4)
            rows.append({"type": "P", "strike": float(k), "expiry": exp, "dte": float(dte), "bid": mid, "ask": mid,
                         "mid": mid, "iv": 0.2, "oi": 1, "delta": 0})
    return {"spot": spot, "rows": rows}
eng.portfolio["betas"] = {"SPY": 1.3, "QQQ": 1.05}
decks["hedge"] = S.deck_hedge(eng, HG.analyze(eng.portfolio, {"SPY": chain(650.0), "QQQ": chain(560.0)}, 62.0))
decks["scorecard"] = S.deck_scorecard(eng, SC.evaluate([], T.m.series("^GSPC")))
from wsb.bot import present as P
from wsb.data.news import NewsItem
eng.news = types.SimpleNamespace(items=[], top=lambda n=12, q=None: [NewsItem("Bloomberg", "Regional bank shares slump as private-credit fund gates redemptions amid contagion fears", "", 0, 11),
                                                                   NewsItem("CNBC", "Fed's Waller says rate cuts remain on the table if labor market weakens further", "", 0, 3),
                                                                   NewsItem("GNews 中文", "台積電法說會前外資連三賣，台股加權指數收黑", "", 0, 0)],
                                 latest=lambda n=12: [])
eng.calendar = types.SimpleNamespace(upcoming=lambda d=14: [{"date": "2026-10-07", "event": "FOMC 利率決議", "type": "fomc"},
                                                          {"date": "2026-10-10", "event": "Consumer Price Index", "type": "macro"},
                                                          {"date": "2026-10-16", "event": "TSM 財報", "type": "earnings"}])
eng.options = types.SimpleNamespace(spx={"spot": 6612, "zero_gamma": 6540, "spot_vs_flip_pct": 1.1, "gex_usd_bn_per_1pct": 2.3,
                                          "call_wall": 6700, "put_wall": 6400, "put_call_oi": 1.35, "put_call_volume": 1.1})
decks["market"] = P.v_market_group(eng, "asia")
decks["macro"] = P.v_macro(eng)
decks["gamma"] = P.v_gamma(eng)
decks["news"] = P.v_news(eng)
decks["calendar"] = P.v_calendar(eng)
decks["quote"] = P.v_quote("NVDA", "NVIDIA", {"price": 182.3, "d1": -1.2, "3M": 8.5, "from_52w_high": -6.1, "vs_ma200": 12.4,
                                             "rsi14": 55, "vol20_ann": 38, "beta_1y": 1.9}, {"forwardPE": 31.2, "marketCap": 4.4e12})
from wsb import morning as MO
md2 = "**今日主題**\n信用利差走闊壓過科技財報樂觀，今天先守不攻。\n\n**交易台觀點**\n- 標普：中性，等 CPI\n- 美債：偏多，避險買盤回流"
facts = {"trade_date": "2026-09-30", "movers": MO.movers(types.SimpleNamespace(market=T.m, holding_tickers=lambda: ["NVDA"])),
         "sectors": MO.sectors(eng), "macro": [{"date": "2026-09-30", "event": "Consumer Price Index", "type": "macro"}],
         "earnings": [{"when": "盤後", "symbol": "NKE", "name": "Nike", "eps_fc": 0.27, "mcap": 1.15e11},
                      {"when": "盤前", "symbol": "CCL", "name": "Carnival", "eps_fc": 1.32, "mcap": 3.1e10}]}
decks["morning"] = S.deck_morning(eng, facts, MO.first_section(md2), "華爾街晨會簡報", "美股開盤前")
board = {"ahead": {"2026-10-01": [{"when": "盤後", "symbol": "NKE", "name": "Nike", "eps_fc": 0.27, "eps_ly": 0.7, "mcap": 1.15e11}],
                   "2026-10-02": [{"when": "盤前", "symbol": "STZ", "name": "Constellation Brands", "eps_fc": 4.3, "eps_ly": 4.32, "mcap": 5.2e10}]},
         "past": [{"symbol": "MU", "name": "Micron", "eps_act": 2.1, "eps_est": 1.95, "surprise": 7.7, "reaction": -3.2},
                  {"symbol": "FDX", "name": "FedEx", "eps_act": 3.9, "eps_est": 3.6, "surprise": 8.3, "reaction": 5.1},
                  {"symbol": "COST", "name": "Costco", "eps_act": 5.0, "eps_est": 5.2, "surprise": -3.8, "reaction": -2.0}]}
decks["earnboard"] = S.deck_earnings_board(board)
print("theme:", MO.first_section(md2))
for name, pngs in decks.items():
    for i, b in enumerate(pngs, 1):
        (out / f"{name}_{i}.png").write_bytes(b)
print("rendered", sum(len(v) for v in decks.values()), "slides →", out)
