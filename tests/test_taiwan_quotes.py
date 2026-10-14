"""Official prices: dates, partial outages, split-safe history and published consumers."""
import asyncio
import json
import os
import tempfile
import sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import unittest
from unittest.mock import AsyncMock, patch

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wss_tw_quotes_"))
import pandas as pd
from wsb.data import taiwan_quotes as TQ
from wsb.data import market as M


class OfficialQuoteTests(unittest.TestCase):
    def test_stock_dates_prices_and_missing_changes(self):
        rows = [dict(Date="1151013", Code="2330", Name="台積電", ClosingPrice="1,000", Change="-20", TradeVolume="1,234"),
                dict(Date="1151013", Code="0050", ClosingPrice="60", Change="除息"),
                dict(Date="1151013", Code="00400A", ClosingPrice="15", Change="0"),
                dict(Date="1151013", Code="1111", ClosingPrice="--", Change="0"),
                dict(Date="9990101", Code="2222", ClosingPrice="12", Change="0")]
        q = TQ.parse(rows, "TWSE")
        self.assertEqual(set(q), {"2330.TW", "0050.TW", "00400A.TW"})
        self.assertEqual(q["2330.TW"]["asof"], "2026-10-13")
        self.assertEqual(q["2330.TW"]["prev"], 1020)
        self.assertEqual(q["2330.TW"]["volume"], 1234)
        self.assertIsNone(q["0050.TW"]["chg_pct"])
        self.assertEqual(q["00400A.TW"]["chg_pct"], 0)
        otc = TQ.parse([dict(Date="115/10/13", SecuritiesCompanyCode="6488", Close="100", Change="+5")], "TPEx")
        self.assertEqual(otc["6488.TWO"]["prev"], 95)
        self.assertEqual(TQ.trading_date("2026-10-13"), "2026-10-13")

    def test_index_single_bar_does_not_invent_previous_close(self):
        q = TQ.parse([dict(Date="1151001", ClosingIndex="20000")], "TWSE-index")
        self.assertIsNone(q["^TWII"]["prev"])
        self.assertEqual(TQ.index_frame(q).iloc[-1, 0], 20000)

    def test_cache_survives_partial_failure_and_does_not_regress(self):
        async def scenario():
            async def get(url, **kw):
                if url == TQ.URLS["TWSE"]:
                    return [dict(Date="1151012", Code="2330", ClosingPrice="900", Change="0")]
                raise OSError("offline")
            with tempfile.TemporaryDirectory() as tmp, patch.object(TQ, "FILE", Path(tmp) / "quotes.json"):
                old = dict(price=1000, asof="2026-10-13", source="TWSE")
                TQ.FILE.write_text(json.dumps({"quotes": {"2330.TW": old}}))
                with patch.object(TQ.http, "get", side_effect=get):
                    result = await TQ.refresh(force=True)
                self.assertEqual(result["2330.TW"], old)
        asyncio.run(scenario())

    def test_yahoo_failure_still_updates_official_quotes_without_mixing_equity_history(self):
        market = M.MarketData()
        market.tickers = ["2330.TW", "^TWII", "SPY"]
        market.history = pd.DataFrame({"2330.TW": [100., 101.], "^TWII": [20000., 20100.]}, index=pd.to_datetime(["2026-10-09", "2026-10-12"]))
        official = {"2330.TW": dict(price=1000, prev=990, asof="2026-10-13", source="TWSE"),
                    "^TWII": dict(price=20200, asof="2026-10-13", bars={"2026-10-13": 20200})}
        with patch.object(M, "_download", side_effect=OSError("Yahoo down")) as download, patch.object(TQ, "refresh", AsyncMock(return_value=official)):
            asyncio.run(market.refresh_quotes())
        self.assertEqual(download.call_args.args[0], ["SPY"])
        self.assertEqual(market.q("2330.TW")["price"], 1000)
        self.assertEqual(market.series("2330.TW").iloc[-1], 101)
        self.assertEqual(market.series("^TWII").iloc[-1], 20200)

    def test_published_quotes_hide_outdated_signals_keep_dates_and_add_etfs(self):
        cols = ["sym", "px", "st", "zlo", "inz", "pk", "history_asof"]
        original = dict(cols=cols, rows=[["2330.TW", 100, "signal", 99, True, 1, "2026-10-12"]], asof="2026-10-13")
        quotes = {s: dict(price=p, chg_pct=1, asof="2026-10-13", source="TWSE") for s, p in [("2330.TW", 102), ("0050.TW", 60)]}
        data = TQ.overlay_published(original, quotes)
        rows = {r[0]: dict(zip(data["cols"], r)) for r in data["rows"]}
        self.assertEqual(rows["2330.TW"]["quote_asof"], "2026-10-13")
        self.assertEqual(rows["2330.TW"]["history_asof"], "2026-10-12")
        self.assertIsNone(rows["2330.TW"]["zlo"])
        self.assertIsNone(rows["2330.TW"]["pk"])
        self.assertEqual(rows["0050.TW"]["px"], 60)
        self.assertEqual(original["rows"][0][2], "signal")
        self.assertNotIn("quote_asof", cols)


if __name__ == "__main__":
    unittest.main()
