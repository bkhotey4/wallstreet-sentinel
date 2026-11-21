"""台股財報頁（11-22）：法說會解析、本季營收進度、頁面。Run: python -m tests.test_tw_earn"""
from datetime import date

from tools import site_tw_earn as S
from wsb.data import tw_irs as I

ROW = """<tr class='even' data-type='body' >
<td style='text-align:left !important;'>2303</td><td>聯電</td>
<td align='center'>115/11/23</td>
<td align='center'>09:00</td>
<td style='text-align:left !important;'>台北</td>
<td style='text-align:left !important;'>本公司受邀參加花旗證券舉辦之法人說明會。</td>
<td><a href='#' onclick='x="1.pdf"'>1.pdf</a></td><td></td><td></td><td></td><td></td><td></td></tr>
<tr class='odd' data-type='body' >
<td style='text-align:left !important;'>2382</td><td>廣達</td>
<td align='center'>115/11/27</td><td align='center'>14:00</td><td>台北</td><td>本公司召開第三季法人說明會。</td><td></td><td></td><td></td><td></td><td></td><td></td></tr>"""


def test_parse():
    rows = I.parse(ROW, "上市")
    assert [(r["code"], r["date"], r["kind"]) for r in rows] == [("2303", "2026-11-23", "券商論壇"), ("2382", "2026-11-27", "自辦法說")]
    assert rows[0]["slides"] and not rows[1]["slides"] and I.roc_to_iso("115/02/30") is None
    assert I.months_ahead(date(2026, 12, 5)) == [(115, 12), (116, 1)]
    cd = ROW.replace("本公司受邀參加花旗證券舉辦之法人說明會。", "2026 Taiwan Corporate Day")
    assert I.parse(cd, "上市")[0]["kind"] == "券商論壇"
    assert "金融股的月營收" in S._prog_text({"ym": "2026-10", "yoy": -83.0}, "2881") and "金融股" not in S._prog_text({"ym": "2026-10", "yoy": 5.0, "months": 1, "qtd_yoy": 5.0, "q_vs_prev": 1.0}, "2382")


def test_view_and_card():
    ms = {"2025-10": {"2382": [100.0, None, None, "廣達"]}, "2026-07": {"2382": [150.0, None, 40.0, "廣達"]},
          "2026-08": {"2382": [150.0, None, 40.0, "廣達"]}, "2026-09": {"2382": [150.0, None, 40.0, "廣達"]},
          "2026-10": {"2382": [130.0, None, 30.0, "廣達"]}, "2026-06": {"2382": [140.0, None, 60.0, "廣達"]},
          "2026-05": {"2382": [140.0, None, 60.0, "廣達"]}, "2026-04": {"2382": [140.0, None, 60.0, "廣達"]}}
    irs = {"fetched": "2026-11-22 00:20", "rows": I.parse(ROW, "上市")}
    v = S.view(date(2026, 11, 22), irs, ms, {"codes": ["2382"], "tw50": ["2382"]})
    q = next(r for r in v["up"] if r["code"] == "2382")
    assert q["big"] and q["tw50"] and q["layer"] == "AI 伺服器組裝（ODM）"
    assert abs(q["prog"]["qtd_yoy"] - 30.0) < 1e-6 and q["prog"]["months"] == 1 and abs(q["prog"]["q_vs_prev"] - (390 / 450 - 1) * 100) < 1e-6
    assert [r["code"] for r in v["up"]] == ["2303", "2382"]   # both tracked (聯電 is in the AI-chain list) → by date
    S.view = lambda: v                                   # card uses the same view
    h = S.sec_tw_earn_preview()
    assert "台股財報前瞻" in h and "⭐ 廣達" in h and "本季已公布 1 個月，比去年同期 <b>+30%</b>" in h and "自辦法說" in h and "券商論壇" in h


if __name__ == "__main__":
    test_parse()
    test_view_and_card()
    print("ok tw earn")
