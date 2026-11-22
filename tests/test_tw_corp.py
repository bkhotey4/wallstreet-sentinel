"""庫藏股／內部人／台股覆蓋清單（11-22）。Run: python -m tests.test_tw_corp"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from wsb.data import tw_corp as C

ROW = ("<tr><td align='center'>1</td><td align='center'>2474</td><td align='center' nowrap>可成</td><td align='center'>115/11/13</td>"
       "<td align='center'>3</td><td align='right'>  9,000,000,000</td><td align='right'> 20,000,000</td><td align='right'>137.00</td>"
       "<td align='right'>293.00</td><td align='center'>115/11/16</td><td align='center'>116/01/15</td><td align='center'>N</td>"
       "<td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>")


def test_parse():
    b = C.parse_buybacks(ROW, "上市")
    assert b == [{"code": "2474", "name": "可成", "date": "2026-11-13", "purpose": "維護公司信用及股東權益", "purpose_id": "3",
                  "max_amt": 9e9, "shares": 2e7, "lo": 137.0, "hi": 293.0, "start": "2026-11-16", "end": "2027-01-15", "done": False, "board": "上市"}]
    ins = C.parse_insiders([{"公司代號": "1540", "公司名稱": "喬福", "出表日期": "1151120", "申報人身分": "董事本人",
                             "預定轉讓方式及股數-轉讓方式": "贈與", "預定轉讓總股數-自有持股": "190800", "目前持有股數-自有持股": "1153171", "有效轉讓期間": "1151120~1151122"}])
    assert ins[0]["date"] == "2026-11-20" and ins[0]["shares"] == 190800.0 and ins[0]["how"] == "贈與"


def test_push():
    import tools.sec_push as P
    now = 1795297000.0                                                   # 2026-11-22 ~09:00 Taipei
    d = {"buybacks": [{"code": "2474", "name": "可成", "date": "2026-11-21", "big": True, "purpose": "維護公司信用及股東權益", "shares": 2e7,
                       "lo": 137, "hi": 293, "start": "2026-11-23", "end": "2027-01-15"},
                      {"code": "9999", "name": "小公司", "date": "2026-11-21", "big": False},
                      {"code": "2330", "name": "台積電", "date": "2026-10-01", "big": True}]}
    todo = P.buyback_todo(d, {}, now)
    assert [x["code"] for x in todo] == ["2474"] and P.buyback_todo(d, {"tsb:2474:2026-11-21": now}, now) == []
    e = P.buyback_embed(todo[0])
    assert "可成" in e["title"] and "20,000 張" in e["description"] and "137～293" in e["description"]


def test_coverage_card():
    from tools import site_tw_coverage as S
    f = Path(tempfile.mkdtemp()) / "c.json"
    f.write_text(json.dumps({"items": [{"group": "公司", "zh": "月營收", "status": "有"}, {"group": "公司", "zh": "單季財報", "status": "缺", "next": "存快照"}]}), encoding="utf-8")
    with patch.object(S, "FILE", f):
        h = S.sec_tw_coverage()
    assert "有 1 項" in h and "還缺 1 項" in h and "下一項是「單季財報」" in h and "還要做：存快照" in h





def test_distress_drops_delisted():
    """11-22: a ticker SEC no longer maps (acquired / deregistered) leaves the auto distress list at once."""
    from datetime import date
    from wsb.data import distress_data as D
    f = Path(tempfile.mkdtemp()) / "auto.json"
    f.write_text(json.dumps({"CCO": {"added": "2026-10-16", "zh": "CC", "kind": "auto", "why": "x", "src": "screen", "last_hit": "2026-11-21"},
                             "KHC": {"added": "2026-10-16", "zh": "KHC", "kind": "auto", "why": "x", "src": "screen", "last_hit": "2026-11-21"}}), encoding="utf-8")
    tmap = {f"T{i}": {"cik": i} for i in range(6000)}
    tmap["KHC"] = {"cik": 1637459}
    with patch.object(D, "F_AUTO", f):
        out = D.update_auto({}, {}, tmap, set(), date(2026, 11, 22))
    assert "CCO" not in out and "KHC" in out


if __name__ == "__main__":
    test_parse()
    test_push()
    test_coverage_card()
    test_distress_drops_delisted()
    print("ok tw corp")
