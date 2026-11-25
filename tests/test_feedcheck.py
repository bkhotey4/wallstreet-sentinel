"""AI write-ups vs the site's own closes (tools/feedcheck.py).  Run: python -m tests.test_feedcheck"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import feedcheck as FC   # noqa: E402

CLOSES = {"^GSPC": (7549.94, 2.35, "2026-11-09"), "^VIX": (19.92, -22.31, "2026-11-09"), "^TNX": (4.864, 0.10, "2026-11-09"),
          "^TWII": (41661.7, 4.94, "2026-11-09"), "TWD=X": (33.109, 0.88, "2026-11-09"), "GC=F": (4132.0, 1.41, "2026-11-09"),
          "BZ=F": (92.29, -6.13, "2026-11-09")}
AM = "2026-11-10 07:45"


def _prime():
    q = {t: {"price": p, "chg_pct": c, "asof": a} for t, (p, c, a) in CLOSES.items()}
    FC.prime(SimpleNamespace(market=SimpleNamespace(q=lambda t: q.get(t))))


def _flag(text, when=AM, hint=None):
    return FC.check_text(text, when, hint)[1]


def test_flags_wrong_quotes():
    _prime()
    out, n = FC.check_text("CNA：11/9 美股收盤，道瓊 +2.19%、S&P 500 +2.58% 至 7,567.25、Nasdaq +2.84%。下一句。", AM)
    assert n == 1 and "〔數字查核：本站收盤 標普 500（11-09）7,550，+2.35%〕下一句。" in out, out
    assert _flag("台幣今天升值約 0.9%。") == 1                       # USD/TWD +0.88% means 台幣 fell
    assert _flag("美債 10 年 4.95%。") == 1 and _flag("VIX 收 21.5，跌 22%。") == 1


def test_leaves_right_or_other_numbers_alone():
    _prime()
    for t in ("標普 500 收 7,550（+2.35%），VIX 降到 19.92。", "台股大漲 1,960 點，收 41,662 點。", "台幣貶值 0.9%。",
              "10 年期殖利率 4.86%，上升 0.5 個基點。", "布蘭特跌 6.3% 到 92.13 美元，黃金漲 1.8% 到 4,150 美元。",
              "英國 10 年期殖利率 5.24%。", "S&P 500 本週累計跌 3%。", "若標普跌破 7,300 要小心。",
              "11/6 標普 500 收 7,376.86（+0.31%）。", "VIX 25.64→19.92。",
              "Nvidia 盤中一度跌近 9%；但 S&P 500 +2.35%。"):
        assert _flag(t) == 0, t


def test_only_the_same_session():
    _prime()
    bad = "標普 500 收 7,567（+2.58%）。"
    assert _flag(bad) == 1
    assert _flag(bad, "2026-11-10 03:07") == 0           # written before that close (intraday)
    assert _flag(bad, "2026-11-14 07:45") == 0           # days later: our close is no longer "that day"
    assert _flag(bad, AM, "2026-11-05") == 0             # an older day kept in a history list
    assert _flag("台股收 40,000 點。", "2026-11-10 10:30") == 0   # written while Taiwan trades again
    assert _flag("台股收 40,000 點。", "2026-11-09 15:00") == 1


def test_scrub_walks_feeds():
    _prime()
    d = {"updated": "2026-11-10 07:45 台北", "items": [
        {"date": "2026-11-09", "phase": "盤後", "one": "標普 500 收 7,567（+2.58%）。"},
        {"date": "2026-11-09", "phase": "盤中", "one": "標普 500 漲 2.8%。"},
        {"date": "2026-11-05", "one": "標普 500 收 7,354（-4.36%）。"}],
        "sources": [{"name": "標普 500 收 7,567", "url": "https://example.com"}]}
    out = FC.scrub(d)
    assert "數字查核" in out["items"][0]["one"] and "數字查核" not in json.dumps(out["items"][1:], ensure_ascii=False)
    assert out["sources"] == d["sources"] and out["updated"] == d["updated"]
    FC.FACTS.clear()
    assert FC.scrub(d) == d                               # not primed (tests, other callers): unchanged


def test_learn_card_shows_note():
    from tools import site_learn as L
    _prime()
    d = {"updated": "2026-11-10 07:45 台北",
         "stories": [{"date": "2026-11-10", "topic": "反彈", "one": "大盤反彈", "confirmed": ["11/9 S&P 500 +2.58% 至 7,567.25。"]}]}
    f = Path(tempfile.mkdtemp()) / "learn.json"
    f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    with patch.object(L, "FILE", f):
        assert "數字查核：本站收盤 標普 500" in json.dumps(L.load(), ensure_ascii=False)
    FC.FACTS.clear()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
