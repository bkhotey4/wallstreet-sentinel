"""PC → cloud relay of public Taiwan data the cloud build often cannot fetch (公開資訊觀測站 blocks datacenter addresses).
Writes research_feed/tw_rev_seed.json (monthly revenue, 24 months), tw_irs_seed.json (法說會 calendar) and tw_corp_seed.json (庫藏股) in
wallstreet-sentinel, each with its own fetch time.  Run daily by the wss-daily-maintain-expand and wss-tw-forecast-daily routines
(added 2026-11-22: the revenue seed had been written once by hand and would have stayed at October forever).
Run: python -m tools.relay_seeds"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

FEED = Path(__file__).resolve().parents[2] / "wallstreet-sentinel" / "research_feed"


def main() -> dict:
    from wsb.data import tw_desk as D
    from wsb.data import tw_irs as I
    out = {}
    try:
        asyncio.run(D.refresh_rev(120))
        s = D.rev_seed(FEED / "tw_rev_seed.json")
        out["rev"] = {"fetched": s.get("fetched"), "months": sorted(s.get("months") or {})[-1:]}
    except Exception as e:  # noqa: BLE001
        out["rev"] = {"error": str(e)}
    try:
        s = I.write_seed(FEED / "tw_irs_seed.json")
        out["irs"] = {"fetched": s.get("fetched"), "rows": len(s.get("rows") or [])}
    except Exception as e:  # noqa: BLE001
        out["irs"] = {"error": str(e)}
    try:
        from wsb.data import tw_corp as C
        s = C.write_seed(FEED / "tw_corp_seed.json")
        out["corp"] = {"fetched": s.get("fetched"), "buybacks": len(s.get("buybacks") or [])}
    except Exception as e:  # noqa: BLE001
        out["corp"] = {"error": str(e)}
    try:
        from wsb.data import tw_chips as CH
        s = CH.write_seed(FEED / "tw_chips_seed.json")
        out["chips"] = {"fetched": s.get("fetched"), "large": bool(s.get("large"))}
    except Exception as e:  # noqa: BLE001
        out["chips"] = {"error": str(e)}
    try:
        from wsb.data import tw_macro2 as M2
        s = M2.write_seed(FEED / "tw_macro2_seed.json")
        out["macro2"] = {"fetched": s.get("fetched"), "pmi": (s.get("pmi") or [{}])[-1].get("ym"), "unemp": (s.get("unemp") or [{}])[-1].get("ym")}
    except Exception as e:  # noqa: BLE001
        out["macro2"] = {"error": str(e)}
    try:                                                   # quarterly statements: when stale (> 3 days) or a newer quarter is filed
        import time as _t
        from wsb.data import tw_chips as CH
        f = FEED / "tw_fin_seed.json"
        have = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        want = {f"{y}Q{q}" for y, q in CH.latest_quarters()}
        if _t.time() - (f.stat().st_mtime if f.exists() else 0) > 3 * 86400 or not want <= set(have.get("snaps") or {}):
            s = CH.write_fin_seed(f)
            out["fin"] = {"fetched": s.get("fetched"), "quarters": sorted(s.get("snaps") or {})}
        else:
            out["fin"] = {"kept": have.get("fetched")}
    except Exception as e:  # noqa: BLE001
        out["fin"] = {"error": str(e)}
    return out


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
