"""AI 視角看進場: cool-down episodes, baselines, the AI use rule, valuation buckets, phased investing, and no advice wording."""
import re
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wsb.analytics import cooldown as CD, entry_env as EE  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出")


def _text(h: str) -> str:
    return re.sub(r"<[^>]+>", " ", h)


def test_vix_cooldowns_counts_each_episode_once():
    idx = pd.bdate_range("2020-01-01", periods=12)
    vix = pd.Series([15, 32, 35, 25, 19, 18, 31, 22, 19, 33, 30, 21], index=idx, dtype=float)
    cd = CD.vix_cooldowns(vix)
    assert [d.strftime("%Y-%m-%d") for d in cd] == [idx[4].strftime("%Y-%m-%d"), idx[8].strftime("%Y-%m-%d")]


def test_gauge_cooldowns_need_a_low_first():
    idx = pd.bdate_range("2015-01-01", periods=400)
    sc = np.full(400, 5)
    sc[100:130] = 1                                    # stress
    sc[130:140] = 3
    f = pd.DataFrame({"a": (sc >= 1).astype(int), "b": (sc >= 2).astype(int), "c": (sc >= 3).astype(int),
                      "d": (sc >= 4).astype(int), "e": (sc >= 5).astype(int)}, index=idx)
    out = CD.gauge_cooldowns(f)
    assert len(out) == 1 and out[0] == idx[140]       # calm periods with no prior low never count


def test_fwd_stats_and_baseline():
    idx = pd.bdate_range("2000-01-03", periods=1200)
    spx = pd.Series(np.linspace(100, 200, 1200), index=idx)
    vix = pd.Series(15.0, index=idx)
    r = CD._fwd_stats(spx, vix, [idx[10]])
    assert r["rows"][0]["12m"] > 0 and r["rows"][0]["reflare"] is False and r["sum"]["12m"]["up"] == 100
    b = CD.baseline(spx, vix, idx[0])
    assert b["12m"]["up"] == 100 and b["reflare"]["pct"] == 0


def test_phase():
    assert CD.phase({"n": 7, "n_ok": 2}) == "stress"
    assert CD.phase({"n": 7, "n_ok": 6, "since_hot": 30}) == "cooling"
    assert CD.phase({"n": 7, "n_ok": 5, "since_hot": 300}) == "mixed"
    assert CD.phase({"n": 7, "n_ok": 7, "since_hot": 300}) == "calm"


class _Mkt:
    def __init__(self, d):
        self.d = d

    def series(self, s):
        return self.d.get(s, pd.Series(dtype=float))


def _eng():
    idx = pd.bdate_range("1994-01-03", "2026-10-23")
    rng = np.random.default_rng(1)
    spx = pd.Series(100 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, len(idx)))), index=idx)
    vix = pd.Series(np.clip(18 + np.cumsum(rng.normal(0, 0.8, len(idx))) % 25, 10, 45), index=idx)
    q = pd.date_range("1950-01-01", "2026-04-01", freq="QS")
    gdp = pd.Series(np.linspace(300, 32000, len(q)), index=q)
    mv = gdp * 1000 * np.linspace(0.4, 2.0, len(q)) * (1 + 0.1 * np.sin(np.arange(len(q)) / 6))
    fred = types.SimpleNamespace(get=lambda s: {"GDP": gdp, "NCBEILQ027S": mv}.get(s, pd.Series(dtype=float)))
    st = types.SimpleNamespace(history=pd.Series(50 + 10 * np.sin(np.arange(len(idx)) / 50), index=idx))
    return types.SimpleNamespace(market=_Mkt({"^GSPC": spx, "^VIX": vix, "XLY": spx * 1.01, "XLP": spx}), fred=fred, stress=st,
                                 rotation={"breadth": {"us": {"now": 60.0}}, "equal_weight": {"chg_3m": 1.5}}, canary={})


def test_env_parts():
    e = _eng()
    b = EE.bull_env(e)
    assert any("市場寬度" in x["zh"] and x["ok"] for x in b) and any("等權重" in x["zh"] for x in b)
    v = EE.valuation_10y(e)
    assert v and len(v["rows"]) == 4 and sum(x["now"] for x in v["rows"]) == 1 and v["since"] == "1950"
    p = EE.phased(e)
    assert p and 0 <= p["lump_win"] <= 100 and p["n"] > 300


def test_cards_render_without_advice_words():
    from tools import site_cooldown as SCD, site_entry as SEN
    e = _eng()
    e._entry_ai = {"available": True, "up12": {"auc": 0.45, "used": False, "p": 70.0, "base": 80.0},
                   "dd10": {"auc": 0.6, "used": True, "p": 20.0, "base": 22.0},
                   "memory": {"auc": 0.4, "used": False, "med12": 9.0, "up12": 70.0, "dd10": 20.0, "dates": ["2012-01"]}}
    html = "".join(f(e) for f in (SEN.sec_ai_entry, SCD.sec_cool_check, SCD.sec_cool_history, SEN.sec_bull_env, SEN.sec_cheap,
                                   SEN.sec_phased, SEN.sec_entry_links))
    t = _text(html)
    assert "一句話看懂" in t and "不採計" in t and "採計" in t and "不是投資建議" in t
    assert not [b for b in BANNED if b in t], [b for b in BANNED if b in t]
    assert "1 個通過檢驗" in t                                       # dd10 passes in this fixture


def test_page_is_in_the_stock_group():
    from tools import site_layout as LY
    assert LY.GROUP_OF["entry"] == "stock"
    from tools import build_site
    assert build_site.SEN and build_site.SCD


def main():
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)


if __name__ == "__main__":
    main()
