"""開盤後即時盤勢: the card ships its gamma levels and placeholders, the JS carries the 11 sectors, and it sits on the
開盤前 30 秒 page.  Run: python -m tests.test_intraday"""
from __future__ import annotations

import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_intraday_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_intraday as SI  # noqa: E402


def test_card_and_js():
    eng = types.SimpleNamespace(options=types.SimpleNamespace(spx={"zero_gamma": 7714.0, "call_wall": 7800, "put_wall": None}))
    assert SI.levels(eng) == {"zero_gamma": 7714.0, "call_wall": 7800.0} and SI.levels(None) == {}
    h = SI.sec_intraday(eng)
    assert "一句話看懂" in h and 'id="idbox"' in h and "zero_gamma" in h and "pages.dev" in h and "不是投資建議" in h
    assert len(SI.SECTORS) == 11 and len(SI.CORE) + len(SI.SECTORS) <= 25 and {k for *_x, k in SI.SECTORS} == {"cyc", "def"}
    assert "__SEC__" not in SI.JS and "XLK" in SI.JS and "&vol=SPY,QQQ" in SI.JS and "America/New_York" in SI.JS
    for b in ("目標價", "上漲空間", "低估", "高估", "買進", "賣出"):
        assert b not in h and b not in SI.JS


def test_on_premarket_page():
    from tools import build_site as B
    import inspect
    src = inspect.getsource(B.render)
    assert "SID.sec_intraday" in src and src.index("SQ.sec_premarket") < src.index("SID.sec_intraday")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
