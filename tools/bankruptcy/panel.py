"""Step 2/3. Point-in-time panel for the bankruptcy study.

For every company in SEC's companyfacts bulk file and every snapshot date (30 Jun / 31 Dec, 2010-2025) the radar's own
parser (wsb.data.distress_data.parse_balance) is run on ONLY the facts filed on or before that date, so each row is
exactly what the radar would have seen then.  Label = first 8-K item 1.03 filed within the next 365 days.
Download https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip (~1.4 GB) first.
Usage: python -m tools.bankruptcy.panel <companyfacts.zip> <bk_labels.json> <out.pkl>"""
import json
import sys
import zipfile
from datetime import date, timedelta
from multiprocessing import Pool

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))

SNAPS = [date(y, m, d) for y in range(2010, 2026) for (m, d) in ((6, 30), (12, 31)) if date(y, m, d) <= date(2025, 6, 30)]
MIN_ASSETS = 5e7            # $50M: below that most filers are shells
MAX_LAG = 400               # the radar still scores a balance sheet up to 400 days old
ZIP, FIRST = None, None


def _init(zp, first):
    global ZIP, FIRST
    ZIP, FIRST = zipfile.ZipFile(zp), first


def _tags():
    from wsb.data import distress_data as DD
    t = set()
    for v in list(DD.INSTANT.values()) + list(DD.FLOWS.values()):
        t |= set(v)
    return t


def work(name):
    from wsb.data import distress_data as DD
    from wsb.analytics import distress as DZ
    try:
        cf = json.loads(ZIP.read(name))
    except Exception:  # noqa: BLE001
        return []
    g = (cf.get("facts") or {}).get("us-gaap") or {}
    if "Assets" not in g:
        return []
    keep = _tags()
    facts = {}
    for t in keep:
        u = (g.get(t) or {}).get("units") or {}
        fs = u.get("USD")
        if fs:
            facts[t] = sorted(fs, key=lambda f: f.get("filed", ""))
    av = [f["val"] for f in facts.get("Assets", []) if f.get("val")]
    if not av or max(av) < MIN_ASSETS:
        return []
    cik = int(cf.get("cik") or name[3:13])
    bk = FIRST.get(cik)
    rows = []
    for d in SNAPS:
        ds = d.isoformat()
        if bk and bk <= ds:
            break                                            # already filed for bankruptcy: out of the sample
        mini = {"facts": {"us-gaap": {t: {"units": {"USD": [f for f in fs if f.get("filed", "9") <= ds]}} for t, fs in facts.items()}}}
        try:
            b = DD.parse_balance(mini)
        except Exception:  # noqa: BLE001
            continue
        if not b or not b.get("assets") or b["assets"] < MIN_ASSETS:
            continue
        lag = (d - date.fromisoformat(b["end"])).days
        if lag < 0 or lag > MAX_LAG:
            continue
        y = int(bool(bk) and ds < bk <= (d + timedelta(days=365)).isoformat())
        pts = sum(DZ.PTS[s["state"]] for s in DZ._corp(b, __import__("pandas").Series(dtype=float)))
        from wsb.analytics import bankruptcy as BK
        rows.append({"cik": cik, "d": ds, "y": y, "pts": pts, "z2": DZ.altman(b), **BK.row(b, lag)})       # the live code path
    return rows


def main():
    zp, lab, out = sys.argv[1:4]
    L = json.load(open(lab, encoding="utf-8"))
    first = {int(k): v["date"] for k, v in L["first"].items()}
    names = [n for n in zipfile.ZipFile(zp).namelist() if n.endswith(".json")]
    print("companies in bulk file:", len(names), flush=True)
    rows = []
    with Pool(14, initializer=_init, initargs=(zp, first)) as pool:
        for i, r in enumerate(pool.imap_unordered(work, names, chunksize=50)):
            rows += r
            if i % 2000 == 0:
                print(i, "files,", len(rows), "rows", flush=True)
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_pickle(out)
    print("rows", len(df), "companies", df["cik"].nunique(), "positives", int(df["y"].sum()),
          "bankrupt companies in panel", df.loc[df["y"] == 1, "cik"].nunique())


if __name__ == "__main__":
    main()
