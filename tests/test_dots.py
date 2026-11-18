"""本週串起來看（11-17）：事件時間表、交集、事件存檔、卡片。Run: python -m tests.test_dots"""
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from tools import dots as D

NOW = datetime(2026, 11, 17, 15, 0, tzinfo=timezone.utc).timestamp()
NAMES = {"NVDA": ("輝達", "NVIDIA Corp"), "GOOGL": ("Alphabet", "Alphabet Inc"), "AMD": ("超微", "Advanced Micro Devices"),
         "HD": ("家得寶", "Home Depot"), "WMT": ("沃爾瑪", "Walmart")}
SOF = {"alerts": [{"ts": datetime(2026, 11, 12, 1, 0, tzinfo=timezone.utc).timestamp(), "sym": "NVDA", "t": "SEC 申報：輝達（NVDA）執行長離職",
                   "flags": ["沒寫原因", "立即生效", "同時換董事長"]},
                  {"ts": NOW - 3600, "sym": "HD", "t": "SEC 申報：家得寶（HD）執行長離職", "flags": []}]}
DAYS = {"2026-11-17": {"rows": [{"sym": "NVDA", "mcap": 4e12}, {"sym": "HD", "mcap": 3.5e11}]},
        "2026-11-19": {"rows": [{"sym": "WMT", "mcap": 1e12}]}}
BIS = {"items": [{"id": "/press-release/r", "title": "BIS Issues Rule Addressing Remote Access to American Super Intelligence Technology",
                  "url": "https://www.bis.gov/press-release/r", "ts": datetime(2026, 11, 16, 5, 0, tzinfo=timezone.utc).timestamp()}]}
IPO = {"us": {"filers": {"1": {"name": "Anthropic, PBC", "last": "2026-11-17", "a12": "2026-11-17",
                               "cover": {"symbol": "ANT", "pp": [{"name": "NVIDIA Corporation", "usd": 1e10}, {"name": "Google LLC", "usd": 1e10}]}}}}}


def test_week_story():
    evs = D.events(NOW, NAMES, SOF, DAYS, {"docs": []}, BIS, IPO)
    cl = D.clusters(evs, {s: v[0] for s, v in NAMES.items()})
    top = cl[0]
    assert top["sym"] == "NVDA" and set(top["kinds"]) == {"sec", "policy", "pp", "earn"}, top
    assert "沒寫原因" in top["flags"] and top["events"][0]["date"] == "2026-11-12"
    syms = [c["sym"] for c in cl]
    assert "HD" in syms                                     # CEO departure on the earnings day
    assert "WMT" not in syms                                # one kind of event only
    assert "AMD" not in syms                                # hit by the policy alone: no event of its own
    assert "GOOGL" not in syms                              # private placement only (one kind)
    dup = evs + [{"kind": "pp", "date": "2026-11-17", "syms": ["NVDA"], "t": "輝達出資（手動補的另一份）"}]
    n = [e["kind"] for e in D.clusters(dup, {})[0]["events"]].count("pp")
    assert n == 1, n                                        # same company, same day: counted once


def test_archive_keeps_old_events():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "a.json"
        old = [{"kind": "sec", "date": "2026-11-12", "syms": ["NVDA"], "t": "x"}]
        D.remember(old, NOW, p)
        again = D.remember([], NOW, p)                      # the source no longer has it
        assert [e["t"] for e in again] == ["x"]
        assert D.remember([], NOW + 40 * 86400, p) == []   # dropped after 30 days


def test_card_renders_with_reads():
    from tools import site_dots as S
    cl = D.clusters(D.events(NOW, NAMES, SOF, DAYS, {"docs": []}, BIS, IPO), {s: v[0] for s, v in NAMES.items()})
    real_b, real_r = S.build, S._reads
    S.build = lambda eng=None: {"clusters": cl, "n_events": 9}
    S._reads = lambda: {"updated": "2026-11-17", "reads": [{"sym": "NVDA", "hypothesis": "H", "for": ["a"], "against": ["b"], "confirm": ["c"]}]}
    try:
        h = S.sec_dots(None)
    finally:
        S.build, S._reads = real_b, real_r
    assert "一句話看懂" in h and "輝達" in h and "可能的主線（假設，不是事實）" in h and "反對或還不確定的地方" in h, h[:300]


def test_same_filing_counted_once():
    """11-18: Home Depot's 8-K showed twice (unflagged copy + flagged copy) and inflated the group's weight."""
    from tools import dots as D
    t = "SEC 申報：家得寶（HD）執行長離職（8-K 第 5.02 項）"
    ev = [dict(kind="sec", date="2026-11-17", syms=["HD"], t=t, w=2),
          dict(kind="sec", date="2026-11-17", syms=["HD"], t=t + "；文件沒寫原因", w=2),
          dict(kind="earn", date="2026-11-17", syms=["HD"], t="家得寶財報", w=1)]
    c = D.clusters(ev, {"HD": "家得寶"})
    secs = [e for e in c[0]["events"] if e["kind"] == "sec"]
    assert len(secs) == 1 and secs[0]["t"].endswith("文件沒寫原因"), c


if __name__ == "__main__":
    test_same_filing_counted_once()
    print("ok test_same_filing_counted_once")
    test_week_story()
    print("ok test_week_story")
    test_archive_keeps_old_events()
    print("ok test_archive_keeps_old_events")
    test_card_renders_with_reads()
    print("ok test_card_renders_with_reads")
