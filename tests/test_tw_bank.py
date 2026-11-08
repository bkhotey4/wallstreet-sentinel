"""台灣家庭與銀行壓力: Banking Bureau CSV parsing, monthly snapshots, the lights, the card.
Run: python -m tests.test_tw_bank"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_twb_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wsb.data import tw_bank as B  # noqa: E402


def csv(lines):
    return ("﻿" + "\n".join(lines)).encode("utf-8")


def test_parse_and_view():
    q = B.parse_quality(csv(["基準年,基準月,總額,第一類"] + [f"{102 + i // 4},{(i % 4 + 1) * 3:02d},1000,{97 + i * 0.04:.2f}" for i in range(54)]))
    assert q["2013-03"] == 3.0 and len(q) == 54
    sme = B.parse_sme(csv(["年月,總計,a,b,中小企業放款平均逾放比"] + [f'{97 + i // 12}年{i % 12 + 1}月,"1,000",1%,1%,{0.2 + i * 0.01:.2f}%' for i in range(150)]))
    assert len(sme) == 150 and sme["2008-01"] == 0.2
    banks = [f"銀行{i},100,1,{200000 + i},{100 + i},500,9000,{0.05 + i / 100:.2f},500" for i in range(25)]
    npl = B.parse_npl(csv(["銀行別,存款,稅前盈餘,放款總額,逾期放款總額,備抵,淨值,逾放比率(%),覆蓋"] + banks + ["單位:百萬元,資料月份：115年08月,,,,,,,"]))
    assert npl["month"] == "2026-08" and len(npl["banks"]) == 25
    land = B.parse_land(csv(["金融機構,土地,放款"] + [f"銀行{i},{1000 * i},200000" for i in range(25)] + ["資料月份：115年08月底,,"]))
    assert land["month"] == "2026-08"
    B.FILE.write_text(json.dumps({"quality": q, "sme": sme, "npl": npl, "land": land, "land_snaps": {"2026-08": land}}), encoding="utf-8")
    v = B.view()
    assert v["sme"]["pct"] == 100 and v["emoji"] == "🟡" and "中小企業逾放比" in v["hot"]   # rising every month → record high
    assert v["npl"]["top"][0]["name"] == "銀行24" and v["land"]["top"][0]["name"] == "銀行24"
    assert len(B.alerts(v)) == 1                       # loan quality improves in the fake data, so only the SME line fires
    from tools import site_twbank as S
    h = S.sec_tw_bank(types.SimpleNamespace(_twbank_view=v))
    assert 'id="twbank"' in h and "一句話看懂" in h and "金管會銀行局" in h
    for w in ("目標價", "買進", "賣出", "低估", "高估", "未實現"):
        assert w not in h, w


if __name__ == "__main__":
    test_parse_and_view()
    print("TW BANK TESTS PASSED [OK]")
