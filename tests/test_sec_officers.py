"""SEC 人事申報警報（建置端）：8-K 清單解析、離職／任命判斷、翻頁到上次看過的地方、保留 3 天（不連網）。"""
from __future__ import annotations

import asyncio
import pathlib
import tempfile

ENTRY = """<entry>
<title>8-K - {name} ({cik:010d}) (Filer)</title>
<link rel="alternate" type="text/html" href="https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{acc}-index.htm"/>
<summary type="html">
 &lt;b&gt;Filed:&lt;/b&gt; 2026-11-12 &lt;b&gt;AccNo:&lt;/b&gt; {acc} &lt;b&gt;Size:&lt;/b&gt; 153 KB
&lt;br&gt;Item {item}: Something
&lt;br&gt;Item 9.01: Financial Statements and Exhibits
</summary>
<updated>{upd}</updated>
<id>urn:tag:sec.gov,2008:accession-number={acc}</id>
</entry>"""


def feed(*es):
    return "<feed>" + "".join(ENTRY.format(**e) for e in es) + "</feed>"


def main() -> None:
    from wsb.data import sec_officers as S
    S.FILE = pathlib.Path(tempfile.mkdtemp()) / "s.json"
    nv = {"name": "NVIDIA CORP", "cik": 1045810, "acc": "0001045810-26-000082", "item": "5.02", "upd": "2026-11-12T08:52:41-05:00"}
    ot = {"name": "SMALL CO", "cik": 99, "acc": "0000000099-26-1", "item": "5.02", "upd": "2026-11-12T08:50:00-05:00"}
    pr = {"name": "NVIDIA CORP", "cik": 1045810, "acc": "0001045810-26-000081", "item": "7.01", "upd": "2026-11-12T08:40:00-05:00"}
    rows = S.parse_feed(feed(nv, ot, pr))
    nv_url = "https://www.sec.gov/Archives/edgar/data/1045810/0001045810-26-000082/0001045810-26-000082-index.htm"
    assert rows[0] == {"cik": "1045810", "ts": 1794491561, "acc": "0001045810-26-000082", "items": ["5.02", "9.01"],
                       "url": "https://www.sec.gov/Archives/edgar/data/1045810/0001045810-26-000082/0001045810-26-000082-index.htm"}, rows[0]

    head = ("Item 5.02. Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; "
            "Compensatory Arrangements of Certain Officers. ")
    doc = ("<html><p>" + head + "</p><p>On November 11, 2026, the Board accepted the resignation of Jen-Hsun Huang, as "
           "President, Chief Executive Officer and member of the Board, effective immediately.</p><p>Item 9.01. Exhibits</p></html>")
    assert S.kind(S._text(doc)) == {"what": "離職", "seat": "執行長"}
    # Marvell 11/12: three new directors; a bio mentions a past CEO job and the heading says "Departure" — still 董事任命
    mr = (head + "On November 11, 2026 the Board of Directors approved the appointments of Donna Morris, Douglas Bettinger and "
          "Sasan Goodarzi to the Board. Mr. Goodarzi was Chief Executive Officer of Intuit.")
    assert S.kind(mr) == {"what": "任命", "seat": "董事"}, S.kind(mr)
    assert S.kind(head.replace("5.02.", "5.02:") + "Appointment of Chief Operating Officer. The Board appointed Ann Lee as Chief "
                  "Operating Officer.") == {"what": "任命", "seat": "營運長"}
    ix = ('<tr><td>1</td><td>8-K</td><td><a href="/ix?doc=/Archives/edgar/data/1/2/a-8k.htm">a</a></td><td>8-K</td></tr>'
          '<tr><td>2</td><td>EX-99.1</td><td><a href="/Archives/edgar/data/1/2/pr.htm">pr</a></td><td>EX-99.1</td></tr>')
    assert S.main_doc(ix) == "/Archives/edgar/data/1/2/a-8k.htm"
    assert S.kind("Item 5.02 The Board appointed Jane Roe as Chief Financial Officer.") == {"what": "任命", "seat": "財務長"}
    assert S.kind("Item 5.02 The Committee approved the annual bonus plan for executive officers.")["what"] == "薪酬安排"
    assert S.title_of("NVDA", "輝達", {"what": "", "seat": ""}) == "SEC 申報：輝達（NVDA）高層人事異動（8-K 第 5.02 項）"

    real = S.http.get
    asked = []

    async def fake(url, **k):
        asked.append(url)
        if "getcurrent" in url:
            return feed(nv, ot, pr) if "start=0" in url else feed()
        if url.endswith("-index.htm"):
            return ('<tr><td>1</td><td>8-K</td><td><a href="/ix?doc=/Archives/edgar/data/1045810/000104581026000082/nvda-20261111.htm">'
                    'nvda-20261111.htm</a></td><td>8-K</td></tr>')
        return doc
    try:
        S.http.get = fake
        now = 1794491561 + 1800
        st = asyncio.run(S.refresh({"1045810": ["NVDA", "輝達"]}, now=now))
        assert [a["t"] for a in st["alerts"]] == ["SEC 申報：輝達（NVDA）執行長離職（8-K 第 5.02 項）"], st
        assert st["last_ts"] == 1794491561
        n = len(asked)
        st = asyncio.run(S.refresh({"1045810": ["NVDA", "輝達"]}, now=now + 60))      # seen already: no second read of the filing
        assert len(st["alerts"]) == 1 and not any("nvda-2026" in u for u in asked[n:])
        st = asyncio.run(S.refresh({"1045810": ["NVDA", "輝達"]}, now=now + 4 * 86400))  # older than 3 days → dropped
        assert st["alerts"] == []
        # an alert stored under the old rules (no "v") is read again and its title corrected
        import json
        S.FILE.write_text(json.dumps({"last_ts": now, "alerts": [{"acc": "old", "ts": now - 60, "sym": "NVDA", "zh": "輝達", "item": "5.02",
                                                                 "url": nv_url, "what": "任命", "seat": "董事長", "t": "wrong"}]}), encoding="utf-8")
        st = asyncio.run(S.refresh({"1045810": ["NVDA", "輝達"]}, now=now + 120))
        assert st["alerts"][0]["t"] == "SEC 申報：輝達（NVDA）執行長離職（8-K 第 5.02 項）" and st["alerts"][0]["v"] == S.KIND_V, st
    finally:
        S.http.get = real
    pub = S.public({"ts": 1, "alerts": [{"acc": "a", "ts": 5, "sym": "NVDA", "url": "https://www.sec.gov/x", "t": "T", "what": "離職"}]})
    assert pub["items"][0]["alert"] and pub["items"][0]["off"] and pub["items"][0]["tags"] == ["美股", "人事"]

    # ---- 2026-11-14: more 8-K items, the loudest one wins, and Schedule 13D
    assert S.pick_item(["2.01", "2.05", "9.01"]) == "2.05" and S.pick_item(["5.02", "2.01"]) == "2.01"
    assert S.pick_item(["1.01", "9.01"]) is None and S.pick_item(["5.02", "9.01"]) == "5.02" and S.pick_item(["2.01", "1.03"]) == "1.03"
    assert S.severity({"item": "2.01", "t": "x"}) == 2 and S.severity({"item": "2.05", "t": "x"}) == 3 and S.severity({"item": "4.02", "t": "x"}) == 4
    assert S.severity({"item": "13D", "t": "x"}) == 3 and S.severity({"item": "13D/A", "t": "x"}) == 1
    assert S.severity({"item": "5.02", "t": "執行長離職"}) == 3 and S.severity({"t": "董事任命"}) == 0
    assert "裁員或關廠重整" in S.title_of("X", "某公司", {}, "2.05")
    D13 = ('<entry><title>SCHEDULE {form} - {name} ({cik:010d}) ({role})</title>'
           '<link rel="alternate" type="text/html" href="https://www.sec.gov/Archives/edgar/data/{cik}/{acc}-index.htm"/>'
           '<summary type="html"> &lt;b&gt;Filed:&lt;/b&gt; 2026-11-13</summary><updated>2026-11-13T21:30:46-05:00</updated>'
           '<id>urn:tag:sec.gov,2008:accession-number={acc}</id></entry>')
    x13 = "<feed>" + "".join(D13.format(**e) for e in (
        {"form": "13D", "name": "ICAHN CARL C", "cik": 921669, "role": "Filed by", "acc": "0001-26-1"},
        {"form": "13D", "name": "NVIDIA CORP", "cik": 1045810, "role": "Subject", "acc": "0001-26-1"},
        {"form": "13D/A", "name": "NVIDIA CORP", "cik": 1045810, "role": "Subject", "acc": "0002-26-2"},
        {"form": "13D/A", "name": "SOMEONE LP", "cik": 5, "role": "Filed by", "acc": "0002-26-2"},
        {"form": "13D", "name": "NO SUBJECT LP", "cik": 7, "role": "Filed by", "acc": "0003-26-3"})) + "</feed>"
    r13 = S.parse_13d(x13)
    assert [(r["form"], r["cik"], r["filer"]) for r in r13] == [("13D", "1045810", "ICAHN CARL C"), ("13D/A", "1045810", "SOMEONE LP")], r13
    assert r13[0]["url"].endswith("/1045810/0001-26-1-index.htm")

    async def fake13(url, **k):
        if "SCHEDULE" in url:
            return x13 if "start=0" in url else "<feed></feed>"
        return "<feed></feed>"
    try:
        S.http.get = fake13
        S.FILE = pathlib.Path(tempfile.mkdtemp()) / "s13.json"
        t13 = r13[0]["ts"] + 600
        st = asyncio.run(S.refresh({"1045810": ["NVDA", "輝達"]}, now=t13))
        assert sorted(a["item"] for a in st["alerts"]) == ["13D", "13D/A"], st
        new = next(a for a in st["alerts"] if a["item"] == "13D")
        assert new["t"] == "SEC 申報：ICAHN CARL C 申報持有 輝達（NVDA）逾 5% 股權，不排除介入經營（Schedule 13D）" and st["last_13d"] == r13[0]["ts"]
        pub = S.public(st)
        by = {x["item"]: x for x in pub["items"]}
        assert by["13D"]["alert"] and by["13D"]["sev"] == 3 and by["13D"]["tags"] == ["美股", "大股東"]
        assert by["13D/A"]["alert"] is False and by["13D/A"]["sev"] == 1                 # an update is listed, never pinned
        assert len(asyncio.run(S.refresh({"1045810": ["NVDA", "輝達"]}, now=t13 + 60))["alerts"]) == 2      # not added twice
    finally:
        S.http.get = real

    # the names /api/news matches headlines with: tracked short names, legal tails dropped, everyday words left out
    from tools import site_secwatch as W
    assert W.short_en("Gilead Sciences, Inc.") == "Gilead" and W.short_en("Williams Companies, Inc. (The)") == ""
    assert W.short_en("Petroleo Brasileiro S.A.- Petrobras") == "Petrobras" and W.short_en("HSBC Holdings plc") == "HSBC"
    assert W.short_en("Progressive Corporation (The)") == "" and W.short_en("Toyota Motor Corp Ltd Ord") == "Toyota"
    assert W.zh_key("台積電 ADR") == "台積電" and W.zh_key("Constellation 能源") == "" and W.zh_key("Nu Holdings（巴西數位銀行）") == ""
    nm = W.names_of({"NVDA": ("輝達", "Nvidia"), "V": ("Visa", "Visa"), "GOOGL": ("Alphabet", "Google")}, {"GILD": {"name": "Gilead Sciences, Inc."}},
                    ["NVDA", "V", "GOOGL", "GILD"])
    assert nm == {"NVDA": ["輝達", "Nvidia"], "GOOGL": ["", "Google|Alphabet"], "GILD": ["", "Gilead"]}, nm
    print("test_sec_officers ok")


if __name__ == "__main__":
    main()
