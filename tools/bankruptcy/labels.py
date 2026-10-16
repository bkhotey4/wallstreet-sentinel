"""Step 1/3. Every 8-K with item 1.03 (bankruptcy or receivership) since 2005, from SEC full-text search → labels.json.
Usage: python -m tools.bankruptcy.labels <labels.json>"""
import asyncio, json, sys, time
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from wsb.data import http
from wsb.data.distress_data import EFTS, parse_efts
from wsb.data.earnings_data import SEC_HDR

OUT = sys.argv[1]


async def window(lo, hi):
    out, p = [], 0
    while True:
        js = await http.get(EFTS, params={"q": '"Item 1.03"', "forms": "8-K", "dateRange": "custom", "startdt": lo, "enddt": hi,
                                          "from": p * 100}, headers=SEC_HDR, timeout=40, retries=2)
        got = parse_efts(js)
        total = (((js or {}).get("hits") or {}).get("total") or {}).get("value") or 0
        out += got
        p += 1
        await asyncio.sleep(0.15)
        if len(got) < 100 or p * 100 >= total:
            return out, total


async def main():
    hits = []
    for y in range(2005, 2027):
        for (a, b) in (("01-01", "03-31"), ("04-01", "06-30"), ("07-01", "09-30"), ("10-01", "12-31")):
            got, total = await window(f"{y}-{a}", f"{y}-{b}")
            if total >= 10000:
                print("WARNING window capped", y, a, total)
            keep = [g for g in got if "1.03" in g["items"]]
            hits += keep
            print(y, a, "hits", len(got), "with 1.03", len(keep), flush=True)
    first = {}
    for h in hits:
        c = h["cik"]
        if c not in first or h["date"] < first[c]["date"]:
            first[c] = h
    json.dump({"ts": time.time(), "filings": hits, "first": {str(k): v for k, v in first.items()}}, open(OUT, "w", encoding="utf-8"))
    print("companies with a 1.03 filing:", len(first), "filings:", len(hits))


asyncio.run(main())
