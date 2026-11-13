"""招股書財務表解析：摘要表（三年＋兩個期中）、季度營運表的季增／年增／放緩判斷、括號負數與單位（不連網）。"""
from __future__ import annotations


def tr(*cells):
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def main() -> None:
    from wsb.data import ipo_fin as F
    import tools.site_ipo as S

    summary = ("<p>Summary Consolidated Financial and Other Data</p><table>"
               + tr("Year Ended December 31,", "Nine Months Ended September 30,")
               + tr("(in millions, except share and per share amounts)", "2023", "2024", "2025", "2025", "2026")
               + tr("Revenue", "$", "41", "$", "386", "$", "4,585", "$", "2,545", "$", "33,242")
               + tr("Operating loss", "(551", ")", "(2,980", ")", "(8,060", ")", "(5,224", ")", "(1,260", ")")
               + tr("Net loss", "$ (1,000)", "$ (5,000)", "$ (41,965)", "$ (25,107)", "$ (104,039)") + "</table>")
    r = F.parse_fin(summary)
    assert [(p["year"], p["months"]) for p in r["periods"]] == [(2023, 12), (2024, 12), (2025, 12), (2025, 9), (2026, 9)]
    assert r["interim"]["rev"] == 33242e6 and round(r["interim"]["rev_yoy"]) == 1206 and round(r["interim"]["op_m"], 1) == -3.8
    assert round(r["annual"]["rev_yoy"]) == 1088 and r["annual"]["ni"] == -41965e6

    quarterly = ("<p>Quarterly Results of Operations</p><table>" + tr("Three Months Ended")
                 + tr("(in millions)", "March 31, 2025", "June 30, 2025", "September 30, 2025", "December 31, 2025", "March 31, 2026",
                      "June 30, 2026", "September 30, 2026")
                 + tr("Revenue", "$ 376", "$ 787", "$ 1,382", "$ 2,040", "$ 4,731", "$ 11,555", "$ 16,956")
                 + tr("Operating income (loss)", "(935)", "(1,200)", "(3,089)", "(2,836)", "(1,667)", "974", "(567)")
                 + tr("Net loss", "$ (6,592)", "$ (6,377)", "$ (12,138)", "$ (16,858)", "$ (14,439)", "$ (66,309)", "$ (23,291)")
                 + "</table><table>" + tr("Revenue", "100 %", "100 %", "100 %", "100 %", "100 %", "100 %", "100 %") + "</table>")
    q = F.parse_quarters(quarterly)
    last = q["quarters"][-1]
    assert last["end"] == "2026-09-30" and last["rev"] == 16956e6 and round(last["qoq"]) == 47 and round(last["yoy"]) == 1127
    assert q["slowing"] and round(q["qoq_prev"]) == 144 and q["add_last"] == 5401e6 and q["add_prev"] == 6824e6
    assert round(q["quarters"][-2]["op_m"], 1) == 8.4 and q["quarters"][0]["qoq"] is None
    assert F.parse_quarters("<p>nothing here</p>") is None and F.parse_fin("<table><tr><td>x</td></tr></table>") is None

    # thousands; a 4-column even split; dashes are zero
    k = ("<p>Summary Financial Data</p><p>(in thousands, except per share data)</p><table>"
         + tr("Year Ended December 31,", "Nine Months Ended September 30,") + tr("2025", "2024", "2026", "2025")
         + tr("Revenues, net", "$", "47,178", "$", "42,477", "$", "46,526", "$", "35,798")
         + tr("Gross profit", "9,370", "10,195", "9,029", "6,874") + tr("Net loss", "(15,100)", "—", "(50,900)", "(9,000)") + "</table>")
    r = F.parse_fin(k)
    assert r["annual"]["year"] == 2025 and r["annual"]["rev"] == 47178e3 and round(r["annual"]["rev_yoy"], 1) == 11.1
    assert round(r["interim"]["gp_m"], 1) == 19.4 and r["periods"][1]["ni"] == 0.0

    h = S.fin_block({"summary": F.parse_fin(summary), "q": q})
    assert "季增 +47%" in h and "放緩" in h and "54.0 億美元" in h and "前 9 個月" in h, h
    for w in ("買進", "賣出", "目標價", "低估", "高估", "清空"):
        assert w not in h
    assert S.fin_block(None) == ""
    from wsb.data import ipo_data as D                     # Anthropic's wording: "price per share will be between $70.00 and $78.00"
    cv = D.parse_cover("It is currently estimated that the initial public offering price per share will be between $70.00 and $78.00 . "
                       "We have applied to list our Class A common stock on the Nasdaq Global Select Market under the symbol “ANT.”")
    assert cv["lo"] == 70.0 and cv["hi"] == 78.0 and cv["symbol"] == "ANT"
    assert "lo" not in D.parse_cover("revenue grew between $70.00 and $78.00 million")         # not a price range
    print("test_ipo_fin ok")


if __name__ == "__main__":
    main()
