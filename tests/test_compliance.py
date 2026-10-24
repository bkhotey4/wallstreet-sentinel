"""Compliance wording, the research-tool banner, the event countdown and the position-size calculator.
Run: python -m tests.test_compliance"""
from __future__ import annotations

import glob
import os
import sys
import tempfile
import types
from datetime import datetime
from zoneinfo import ZoneInfo

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_cp_"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BANNED = ("買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池")


def test_no_trading_instruction_words():
    files = glob.glob(os.path.join(ROOT, "tools", "*.py")) + glob.glob(os.path.join(ROOT, "wsb", "**", "*.py"), recursive=True)
    hits = []
    for p in files:
        t = "\n".join(ln for ln in open(p, encoding="utf-8").read().splitlines() if "_LEGACY" not in ln)   # old→new label maps
        hits += [(os.path.basename(p), w) for w in BANNED if w in t]
    assert not hits, hits


def test_ai_text_rewording():
    from tools.sitekit import guard_safe
    assert guard_safe("精選池中 9 成企業；有買點訊號") == "追蹤池中 9 成企業；型態成立"


def test_banner():
    from tools import build_site as BS
    b = BS.comply_bar()
    assert 'id="comply"' in b and "不是經主管機關核准的證券投資顧問" in b and 'id="complyX"' in b
    assert "disclaimer_closed" in BS.COMPLY_JS and "try{" in BS.COMPLY_JS            # storage access is guarded


def test_event_clock():
    from wsb.analytics import event_clock as EC
    q = EC.quad_witching(2026, 2026)
    assert q == ["2026-03-20", "2026-06-18", "2026-09-18", "2026-12-18"]          # 06-19 is Juneteenth → Thursday
    idx = pd.bdate_range("2020-01-01", "2026-10-23")
    rng = np.random.default_rng(5)
    r = pd.Series(rng.normal(0, 0.008, len(idx)), index=idx)
    ev = [d.strftime("%Y-%m-%d") for d in idx[::21]]
    r.loc[pd.to_datetime(ev)] *= 3                                            # event days move more
    spx = (1 + r).cumprod() * 100
    s = EC.move_stats(spx, ev, "2020-01-01")
    assert s["n"] >= 70 and s["mean"] > s["base_mean"] * 1.5
    d = EC.load()
    d.update(cpi=["2026-10-14", "2026-11-10"], nfp=["2026-11-06"])
    EC.FILE.write_text(__import__("json").dumps(d), encoding="utf-8")
    eng = types.SimpleNamespace(market=types.SimpleNamespace(series=lambda t: spx if t == "^GSPC" else pd.Series(dtype=float)),
                                econ=types.SimpleNamespace(fomc=[{"date": "2026-10-28"}]))
    b = EC.build(eng, now=datetime(2026, 10, 24, 12, 0, tzinfo=ZoneInfo("America/New_York")))
    keys = [e["key"] for e in b["events"] if e["ts"]]
    assert keys[0] == "fomc" and set(keys) == {"fomc", "cpi", "nfp", "opex"}
    from tools import site_events as SEV
    h = SEV.sec_event_clock(eng)
    assert "重大事件倒數" in h and 'class="ecc" data-ts=' in h and "不是投資建議" in h


def test_calculator():
    from tools import site_calc as SC
    h = SC.sec_sizing(None)
    for i in ("cap", "px", "stop", "risk", "win", "rr"):
        assert f'id="sz_{i}"' in h
    assert "不會送出或儲存" in h and "不是投資建議" in h and "Math.floor(loss/ps)" in SC.JS


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
