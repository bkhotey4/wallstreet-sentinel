"""PC → cloud relay of public Taiwan data the cloud build often cannot fetch (公開資訊觀測站 blocks datacenter addresses).
Writes research_feed/tw_rev_seed.json (monthly revenue, 24 months) and research_feed/tw_irs_seed.json (法說會 calendar) in
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
    return out


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False))
