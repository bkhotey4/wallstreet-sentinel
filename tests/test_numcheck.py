"""AI number post-check (2026-10-23 audit): numbers the model writes must come from its prompt.
Run: python -m tests.test_numcheck"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_numcheck_"))

from wsb.ai import llm, numcheck as NC  # noqa: E402

PACK = ("## 系統性壓力指數 SSI 61.98/100 [升溫] 歷史百分位 86% SSI 20日變化 +15.6 點\n"
        "外資近5日 -2817.7億 台指期未平倉淨額 -87297 口\n"
        "10年-2年 利差 +32bp\n10年期殖利率(DGS10) 4.953 @2026-10-21 1M -0.120 3年百分位 98\n"
        "標普500 7663.43 -1.21% 崩跌機率 24.5% 基準 17.1% 自由現金流 -1.2B")


def test_sourced_numbers_kept():
    t = ("SSI 升至 62.0，歷史百分位 86%，20 日增加 15.6 點。外資賣超 2,817.7 億元，台指期淨額 -87,297 口。"
         "10 年-2 年利差 +32bp，即 0.32 個百分點。標普收 7,663（-1.21%），2026-10-22 收盤。自由現金流約 -12 億美元。"
         "機率 24.5%，是基準 17.1% 的 1.43 倍。未來 72 小時觀察 3 個指標。")
    out, dropped = NC.check(t, PACK)
    assert dropped == [], dropped
    assert out == t


def test_invented_numbers_dropped():
    t = "SSI 62.0。2008 年 VIX 曾到 80，市場重挫。若標普跌破 7,450 點要注意。"
    out, dropped = NC.check(t, PACK)
    assert len(dropped) == 2, dropped
    assert "80" not in out and "7,450" not in out and "SSI 62.0" in out
    assert NC.NOTE.format(n=2) in out


def test_period_label_restored():
    out, _ = NC.check("10 年期殖利率處於歷史百分位 98% 的高位。SSI 歷史百分位 86%。", PACK)
    assert "3年百分位 98" in out and "歷史百分位 98" not in out, out
    assert "SSI 歷史百分位 86%" in out, out          # a label that matches the source is left alone


def test_complete_checks_by_default():
    async def fake(system, user, max_tokens):
        return "SSI 62.0。標普目標 9,999 點。"
    saved = llm._engines
    llm._engines = lambda: [("claude:test", fake)]
    try:
        txt, _ = asyncio.run(llm.complete("sys", PACK))
        assert "9,999" not in txt and "SSI 62.0" in txt, txt
        raw, _ = asyncio.run(llm.complete("sys", PACK, check=False))
        assert "9,999" in raw
    finally:
        llm._engines = saved


def main():
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("ALL PASS")


if __name__ == "__main__":
    main()
