"""國安基金官方動態（11-22）。Run: python -m tests.test_tw_nsf"""
from datetime import date

from wsb.data import tw_nsf as N
from tools import site_tw_nsf as S

LIST = ('<tr><td>1</td><td><a href="/singlehtml/383?cntId=aa11" title="x">國安基金決定啟動安定市場任務，維護臺股穩定</a></td><td>2026-11-06</td></tr>'
        '<tr><td>2</td><td><a href="/singlehtml/383?cntId=bb22">國家金融安定基金停止執行安定市場任務</a></td><td>2026-01-12</td></tr>'
        '<tr><td>3</td><td><a href="/singlehtml/383?cntId=cc33">國安基金澄清未與某公司攜手啟動「守護之橋」合作計畫</a></td><td>2025-05-15</td></tr>'
        '<tr><td>4</td><td><a href="/singlehtml/383?cntId=dd44">國安基金決定啟動安定市場任務，維護臺股穩定</a></td><td>2025-04-08</td></tr>')


def test_parse_status_episodes():
    n = N.parse_news(LIST)
    assert [r["date"] for r in n] == ["2026-11-06", "2026-01-12", "2025-05-15", "2025-04-08"]
    assert n[0]["url"] == "https://www.mof.gov.tw/singlehtml/383?cntId=aa11"
    assert N.status(n)["state"] == "on" and N.status(n)["since"] == "2026-11-06"
    assert N.status(n[1:])["state"] == "off"
    assert N.status(n[2:3]) == {}                       # 澄清 release mentions 啟動 but is not a decision
    assert S.episodes(n) == [{"start": "2026-11-06", "stop": None, "days": None},
                             {"start": "2025-04-08", "stop": "2026-01-12", "days": 279}]
    assert S.next_report(date(2026, 11, 22), "2026-10-12") == "2027 年 1 月中"
    assert S.next_report(date(2026, 4, 20), "2026-04-13") == "2026 年 7 月中"


def test_body_and_reports():
    page = "<div><h3>國安基金決定啟動安定市場任務，維護臺股穩定</h3><p>本日召開臨時委員會議。</p><p>第二段。</p><p>新聞稿聯絡人：某某</p></div>"
    assert N.parse_body(page, "國安基金決定啟動安定市場任務，維護臺股穩定") == "本日召開臨時委員會議。\n第二段。"
    rp = ('<li>國家金融安定基金115年第3季收支及資產負債情形<a href="/download/p1">(PDF)</a><a href="/download/x1">(XLS)</a>'
          '(國家金融安定基金管理委員會-2026/10/12)</li>')
    assert N.parse_reports(rp) == [{"title": "國家金融安定基金115年第3季收支及資產負債情形", "date": "2026-10-12",
                                    "pdf": "https://www.mof.gov.tw/download/p1", "xls": "https://www.mof.gov.tw/download/x1"}]


def test_alert_window():
    from tools import sec_push as P
    import calendar
    now = calendar.timegm((2026, 11, 7, 2, 0, 0)) # 10:00 Taipei on 11/07
    d = {"nsf": {"date": "2026-11-06", "url": "u1", "title": "t", "status": {"state": "on"}}}
    a = P.twal_todo(d, {}, now)
    assert [x["key"] for x in a] == ["twnsf:u1"] and "國安基金" in P.twal_embed(a[0])["title"]
    assert P.twal_todo(d, {"twnsf:u1": 1.0}, now) == []
    assert P.twal_todo(d, {}, calendar.timegm((2026, 11, 22, 2, 0, 0))) == []   # 16 days old: not news any more


def test_fsc():
    page = ('<li role="row"><span class="date" role="cell">2026-11-21</span>\n<span class="unit" role="cell">證券期貨局</span>\n'
            '<span class="title" role="cell">\n<a href="home.jsp?id=96&amp;dataserno=202611210001&dtable=News" title="金管會宣布「全面禁止平盤以下放空」等5項措施">金管會宣布「全面禁止平盤以下放......</a></span></li>'
            '<li role="row"><span class="date" role="cell">2026-11-20</span><span class="unit" role="cell">證券期貨局</span>'
            '<span class="title" role="cell"><a href="home.jsp?id=96&dataserno=202611200003&dtable=News" title="證券期貨局每日新聞（115年11月20日）">x</a></span></li>')
    f = N.parse_fsc(page)
    assert [r["date"] for r in f] == ["2026-11-21"] and f[0]["url"].startswith("https://www.fsc.gov.tw/ch/home.jsp?id=96&dataserno=")
    assert "全面禁止平盤以下放空" in f[0]["title"]           # whole title from the attribute, not the cut link text
    body = N.parse_fsc_body("<p>金管會宣布「全面禁止平盤以下放空」等5項措施</p><p>2026-11-21</p><p>自115年11月23日起採行：</p><p>聯絡單位：x</p>", f[0]["title"])
    assert body == "自115年11月23日起採行："
    from tools import sec_push as P
    import calendar
    now = calendar.timegm((2026, 11, 22, 4, 0, 0))   # Sunday 12:00 Taipei
    a = P.twal_todo({"fsc": {"date": "2026-11-21", "url": "f1", "title": "t", "body": "b"}}, {}, now)
    assert [x["key"] for x in a] == ["twfsc:f1"] and "金管會" in P.twal_embed(a[0])["title"]


if __name__ == "__main__":
    test_fsc()
    test_parse_status_episodes()
    test_body_and_reports()
    test_alert_window()
    print("ok tw nsf")
