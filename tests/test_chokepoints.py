"""航道監測：燈號、偏低起始日、繞道判斷、卡片輸出（合成資料，不連網）。"""
from __future__ import annotations

from datetime import date, timedelta

import pandas as pd


def _rows(days: int, level, drop_at=None, after=None):
    d0 = date(2020, 1, 1)
    out = {}
    for i in range(days):
        n = level if drop_at is None or i < drop_at else after
        out[(d0 + timedelta(days=i)).isoformat()] = [int(n), int(n // 3), int(n // 4)]
    return out


def main() -> None:
    from wsb.data import chokepoints as CP
    flat = CP.one(_rows(1500, 80))
    assert flat["st"] == "green" and flat["since"] is None, flat
    closed = CP.one(_rows(1500, 80, drop_at=1300, after=3))
    assert closed["st"] == "red", closed
    assert closed["since"] == (date(2020, 1, 1) + timedelta(days=1301)).isoformat(), closed["since"]
    assert abs(closed["base"] - 80) < 1e-6 and closed["ratio"] < 0.1
    thin = CP.one(_rows(1500, 80, drop_at=1450, after=55))
    assert thin["st"] == "yellow", thin
    assert CP.one(_rows(100, 80)) is None                       # too little history
    data = {"ts": 1.0, "ports": {"chokepoint6": _rows(1500, 80, 1300, 3), "chokepoint4": _rows(1500, 60, 1300, 20),
                                 "chokepoint7": _rows(1500, 50, 1300, 80)}}
    v = CP.view(data)
    assert v["detour"]["on"] is True, v["detour"]
    assert [r["id"] for r in v["rows"]] == ["chokepoint6", "chokepoint4", "chokepoint7"]

    import tools.site_chokepoints as S
    CP.view, real = (lambda d=None: v), CP.view

    class M:
        def series(self, sym):
            idx = pd.date_range("2023-01-01", "2024-02-10", freq="B")
            return pd.Series(range(70, 70 + len(idx)), index=idx, dtype=float)

    class E:
        market = M()
    try:
        html = S.sec_chokepoints(E())
    finally:
        CP.view = real
    assert "荷姆茲海峽最近 7 天平均每天 3 艘" in html and "平常約 80 艘" in html, html[:400]
    assert "好望角是平常的 160%" in html
    assert "布蘭特原油" in html                                 # price since the closure started
    for w in ("買進", "賣出", "目標價", "低估", "高估"):
        assert w not in html
    print("test_chokepoints ok")


if __name__ == "__main__":
    main()
