"""台灣總經展望 renderer: reads research_feed/tw_forecast.json (written by the daily routine), tolerant to field spellings.
Run: python -m tests.test_tw_forecast"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import site_twforecast as F  # noqa: E402

SAMPLE = {
    "updated": "2026-11-20 01:10 台北",
    "one": "一句話看懂：出口還在高檔，但股市已經先跌。",
    "chain": [{"step": "聯準會", "kind": "事實", "read": "12/9 升息機率約 90%", "evidence": "FRED"},
              {"name": "訂單會不會放慢", "type": "假設", "what": "基期變高"}, "央行與新台幣"],
    "hypothesis": {"name": "台股 2027 下半年泡沫破裂", "status": "追蹤中", "for": ["融資偏高"], "against": ["本益比中位數不高"]},
    "scenarios": [{"name": "震盪築底", "prob": 45, "what": "x"}, {"name": "修正延長", "prob": 35, "what": "y"}],
    "calls": [{"name": "央行 12 月", "call": "維持 2.0%", "prob": 65, "by": "2099-12-31", "measure": "決議後仍為 2.0% 算對", "now": "2.0%", "why": "a", "wrong": "b"},
              {"name": "舊題", "call": "x", "prob": 70, "by": "2026-01-01", "measure": "m", "result": "對", "note": "官方 2026-01"}],
    "sources": [{"name": "中央銀行", "url": "https://cpx.cbc.gov.tw/"}]}


def test_render():
    f = Path(tempfile.mkdtemp()) / "tw_forecast.json"
    f.write_text(json.dumps(SAMPLE, ensure_ascii=False), encoding="utf-8")
    F.FILE = f
    h = F.sec_tw_forecast(None)
    assert 'id="twforecast"' in h and h.count("一句話看懂：") == 1
    assert "1. 聯準會" in h and "2. 訂單會不會放慢" in h and "3. 央行與新台幣" in h and "假設" in h
    assert "追蹤中的假設" in h and "融資偏高" in h and "震盪築底" in h and "45%" in h
    assert "1 題對 1 題" in h and "cpx.cbc.gov.tw" in h
    for w in ("目標價", "上漲空間", "買進", "賣出", "低估", "高估", "買點", "精選池"):
        assert w not in h, w
    f.write_text("{}", encoding="utf-8")
    assert F.sec_tw_forecast(None) == ""
    F.FILE = f.with_name("missing.json")
    assert F.sec_tw_forecast(None) == ""


def test_draft_edition_renders():
    fx = Path(__file__).with_name("fixture_tw_forecast.json")
    if not fx.exists():
        return
    F.FILE = fx
    h = F.sec_tw_forecast(None)
    assert "全球到台灣的因果鏈" in h and "38,427" in h


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
