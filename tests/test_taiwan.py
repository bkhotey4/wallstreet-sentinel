"""Offline test of Taiwan parsers using real response samples captured on the user's machine."""
import asyncio
import tests.test_offline as T  # noqa: F401  (stubs + synthetic market)
from datetime import date
from wsb.data import taiwan as TW

BFI = {"stat": "OK", "date": "20260930", "fields": ["單位名稱", "買進金額", "賣出金額", "買賣差額"],
       "data": [["自營商(自行買賣)", "7,572,941,960", "6,191,730,730", "1,381,211,230"],
                ["自營商(避險)", "25,863,300,029", "26,004,444,881", "-141,144,852"],
                ["投信", "20,808,199,934", "13,026,992,293", "7,781,207,641"],
                ["外資及陸資(不含外資自營商)", "384,684,234,860", "355,048,279,194", "29,635,955,666"],
                ["外資自營商", "0", "0", "0"], ["合計", "438,928,676,783", "400,271,447,098", "38,657,229,685"]]}
T86 = {"stat": "OK", "fields": ["證券代號", "證券名稱", "外陸資買進股數(不含外資自營商)", "外陸資賣出股數(不含外資自營商)",
                                "外陸資買賣超股數(不含外資自營商)", "外資自營商買進股數", "外資自營商賣出股數", "外資自營商買賣超股數",
                                "投信買進股數", "投信賣出股數", "投信買賣超股數", "自營商買賣超股數", "自營商買進股數(自行買賣)",
                                "自營商賣出股數(自行買賣)", "自營商買賣超股數(自行買賣)", "自營商買進股數(避險)", "自營商賣出股數(避險)",
                                "自營商買賣超股數(避險)", "三大法人買賣超股數"],
       "data": [["3481", "群創            ", "156,794,286", "57,695,183", "99,099,103", "0", "0", "0", "0", "0", "0", "7,181,060",
                 "4,476,000", "534,000", "3,942,000", "3,821,942", "582,882", "3,239,060", "106,280,163"],
                ["00403A", "主動統一升級50  ", "1", "1", "25,012,980", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "1"],
                ["2330", "台積電          ", "23,816,918", "23,114,324", "702,594", "0", "0", "0", "795,000", "43,000", "752,000",
                 "399,899", "312,000", "68,223", "243,777", "287,616", "131,494", "156,122", "1,854,493"],
                ["2409", "友達", "1", "1", "-67,780,477", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "-1"]]}
INST = [{"Date": "20260929", "ContractCode": "臺股期貨", "Item": it, "TradingVolume(Net)": v, "OpenInterest(Net)": oi}
        for it, v, oi in (("自營商", "981", "-488"), ("投信", "-52", "72812"), ("外資及陸資", "-1009", "-79029"))]
DAILY = [{"Date": "20260929", "Contract": "TX", "ContractMonth(Week)": "202610", "Last": "25880", "Change": "-120", "%": "-0.46%",
          "Volume": "90000", "OpenInterest": "80000", "TradingSession": "一般"},
         {"Date": "20260929", "Contract": "TX", "ContractMonth(Week)": "202610", "Last": "25950", "Change": "70", "%": "0.27%",
          "Volume": "30000", "OpenInterest": "-", "TradingSession": "盤後"},
         {"Date": "20260929", "Contract": "TX", "ContractMonth(Week)": "202611", "Last": "25900", "Change": "-100", "%": "-0.4%",
          "Volume": "900", "OpenInterest": "5000", "TradingSession": "一般"}]
PCR = [{"Date": "20260929", "PutCallVolumeRatio%": "90.39", "PutCallOIRatio%": "75.30"}]
REV = [{"資料年月": "11508", "公司代號": "2330", "公司名稱": "台積電", "營業收入-當月營收": "335772150",
        "營業收入-上月比較增減(%)": "3.2", "營業收入-去年同月增減(%)": "33.8", "累計營業收入-前期比較增減(%)": "37.1"}]


async def fake_get(url, **kw):
    if "BFI82U" in url:
        return BFI
    if "MI_MARGN" in url:
        return {"stat": "OK", "tables": [{"data": [["融資金額(仟元)", "1", "1", "1", "300,000,000", "290,000,000"]]}]}
    if "T86" in url:
        return T86
    if "Institutional" in url:
        return INST
    if "DailyMarketReportFut" in url:
        return DAILY
    if "PutCallRatio" in url:
        return PCR
    if "t187ap05" in url:
        return REV
    raise RuntimeError(url)


async def fake_sleep(_):
    return None


def main():
    TW.http.get = fake_get
    TW.asyncio.sleep = fake_sleep
    TW.date = type("D", (), {"today": staticmethod(lambda: date(2026, 9, 30)), "fromisoformat": staticmethod(date.fromisoformat)})
    tw = TW.TaiwanData()
    asyncio.run(tw.refresh())
    assert len(tw.flows) == 5 and abs(tw.flows[0]["foreign"] - 296.36) < 0.1, tw.flows[0]
    assert tw.stocks["top_buy"][0]["code"] == "3481" and tw.stocks["top_sell"][0]["code"] == "2409"
    assert all(r["foreign"] > 0 for r in tw.stocks["top_buy"]) and all(r["foreign"] < 0 for r in tw.stocks["top_sell"])
    assert all(r["code"] != "00403A" for r in tw.stocks["top_buy"])
    assert tw.futures["oi_foreign"] == -79029 and tw.futures["tx"]["month"] == "202610" and tw.futures["tx"]["night_last"] == 25950
    assert abs(tw.revenue[0]["rev_bn"] - 3357.7) < 1
    assert abs(tw.margin["chg_pct"] + 3.333) < 0.01 and "融資餘額" in "\n".join(tw.summary_lines())
    print("\n".join(tw.summary_lines()))
    import types
    from wsb.bot import slides as S
    eng = types.SimpleNamespace(market=T.m, taiwan=tw)
    from pathlib import Path
    out = Path("/tmp/wsbprev/preview"); out.mkdir(parents=True, exist_ok=True)
    for i, b in enumerate(S.deck_taiwan(eng), 1):
        (out / f"taiwan_{i}.png").write_bytes(b)
    print("TAIWAN TESTS PASSED ✅")


if __name__ == "__main__":
    main()
