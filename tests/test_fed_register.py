"""政府做了什麼：主題判斷、行政雜項過濾、刊登當天反應、卡片輸出（不連網）。"""
from __future__ import annotations

import numpy as np
import pandas as pd


def main() -> None:
    from wsb.data import fed_register as FR
    assert FR.topic("Adjusting Imports of Robotics, Industrial Machinery, and Their Parts")["topic"] == "關稅與貿易"
    assert FR.topic("Extension of the Suspension of Expansion of End-User Controls for Affiliates")["sym"] == "SMH"
    assert FR.topic("Continuation of the National Emergency With Respect to Iran")["topic"] == "能源與制裁"
    assert FR.topic("Agency Information Collection Activities; Submission to OMB for semiconductor") is None
    assert FR.topic("Anti-Communism Week, 2026") is None
    assert FR.topic("Establishment of the Oval Office National Monument") is None
    assert FR.topic("Order Renewing Order Temporarily Denying Export Privileges") is None
    raw = {"document_number": "2026-1", "title": "Adjusting Imports of Wind Turbines", "publication_date": "2026-11-10",
           "subtype": "Proclamation", "html_url": "https://www.federalregister.gov/d/2026-1", "agencies": [{"name": "Executive Office of the President"}]}
    k = FR.keep(raw)
    assert k["topic"] == "關稅與貿易" and k["sym"] == "^GSPC" and FR.type_zh(k["type"]) == "總統公告"

    import tools.site_fedreg as S
    idx = pd.bdate_range("2026-06-01", "2026-11-10")
    px = pd.Series(100 * np.cumprod(1 + np.random.default_rng(2).normal(0, 0.005, len(idx))), index=idx)
    px.iloc[-1] = px.iloc[-2] * 1.03                                               # +3% on the publication day
    m = S.day_move(px, "2026-11-10")
    assert round(m["pct"], 1) == 3.0 and m["k"] > 2, m
    assert S.day_move(px, "2026-11-08") is None

    d = {"docs": [k]}
    FR.load, real = (lambda: d), FR.load

    class M:
        def series(self, sym):
            return px

    class E:
        market = M()
    try:
        html = S.sec_fed_register(E())
    finally:
        FR.load = real
    assert "正式刊登 1 項" in html and "關稅與貿易 1 項" in html and "標普 500 +3.0%，大動" in html, html[:500]
    for w in ("買進", "賣出", "目標價", "低估", "高估"):
        assert w not in html
    print("test_fed_register ok")


if __name__ == "__main__":
    main()
