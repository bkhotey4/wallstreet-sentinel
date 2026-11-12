"""個股重大消息影響估算：SPY 權重解析、最常一起動的美股（β）、台股連動篩選（不連網）。"""
from __future__ import annotations

import io

import numpy as np
import pandas as pd


def main() -> None:
    from wsb.analytics import news_impact as NI

    rows = [["Fund Name:", "SPY"], ["Ticker Symbol:", "SPY"], ["Holdings:", "As of 11-Nov-2026"], [None, None],
            ["Name", "Ticker", "Identifier", "SEDOL", "Weight", "Sector"],
            ["APPLE INC", "AAPL", "x", "x", 7.887675, "-"], ["NVIDIA CORP", "NVDA", "x", "x", 7.41, "-"],
            ["BERKSHIRE HATHAWAY INC CL B", "BRK.B", "x", "x", 1.6, "-"], ["US DOLLAR", "-", "x", "x", "n/a", "-"]]
    buf = io.BytesIO()
    pd.DataFrame(rows).to_excel(buf, header=False, index=False)
    got = NI.parse_spy(buf.getvalue())
    assert got["asof"] == "11-Nov-2026" and got["w"]["NVDA"] == 7.41 and got["w"]["BRK-B"] == 1.6 and "-" not in got["w"], got

    rng = np.random.default_rng(1)
    n = 200
    x = rng.normal(0, 2, n)
    ret = pd.DataFrame({"NVDA": x, "AMD": 1.2 * x + rng.normal(0, 0.8, n), "KO": rng.normal(0, 1, n)},
                       index=pd.bdate_range("2026-01-01", periods=n))
    names = {"NVDA": ("輝達", "Nvidia", "us"), "AMD": ("超微", "AMD", "us"), "KO": ("可口可樂", "Coca-Cola", "us")}
    p = NI.peers(ret, "NVDA", ["NVDA", "AMD", "KO"], names)
    assert [d["sym"] for d in p] == ["AMD"] and abs(p[0]["beta"] - 1.2) < 0.15 and p[0]["zh"] == "超微", p   # KO: not related
    assert NI.peers(ret, "XXX", ["AMD"], names) == []

    class SP:
        close = (1 + ret / 100).cumprod() * 100

    class E:
        stockprices = SP()
        sx = {"tlink": {"rows": [{"sym": "2330.TW", "name": "台積電", "p": "NVDA", "beta": 0.33, "corr": 0.5, "ok": True},
                                 {"sym": "3231.TW", "name": "緯創", "p": "NVDA", "beta": 0.6, "corr": 0.2, "ok": False},
                                 {"sym": "2454.TW", "name": "聯發科", "p": "^SOX", "beta": 0.4, "corr": 0.5, "ok": True}]}}
    import wsb.data.stocks as ST
    real = ST.universe
    try:
        ST.universe = lambda: {"us": {"symbols": {"NVDA": ("輝達", "Nvidia"), "AMD": ("超微", "AMD"), "KO": ("可口可樂", "Coca-Cola")}},
                               "tw": {"symbols": {"2330.TW": ("台積電", "TSMC")}}}
        out = NI.build(E(), {"1045810": ["NVDA", "輝達"]}, got)
    finally:
        ST.universe = real
    m = out["map"]["NVDA"]
    assert m["w_spx"] == 7.41 and [d["sym"] for d in m["peers"]] == ["AMD"]
    assert m["tw"] == [{"sym": "2330.TW", "zh": "台積電", "beta": 0.33, "corr": 0.5}]          # unverified / other partners left out
    assert out["spy_asof"] == "11-Nov-2026"
    print("test_news_impact ok")


if __name__ == "__main__":
    main()
