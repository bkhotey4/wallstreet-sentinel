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
    print("test_sec_officers ok")


if __name__ == "__main__":
    main()
