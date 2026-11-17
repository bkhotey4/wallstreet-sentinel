"""FRED's lag on Treasury yields is filled from Treasury's own XML: only missing dates, never overwriting FRED.
Run: python -m tests.test_treasury_fill"""
import pandas as pd

from wsb.data import fred as F

XML = """<feed><entry><content><m:properties><d:NEW_DATE m:type="Edm.DateTime">2026-11-13T00:00:00</d:NEW_DATE>
<d:BC_3MONTH m:type="Edm.Double">4.40</d:BC_3MONTH><d:BC_2YEAR m:type="Edm.Double">4.99</d:BC_2YEAR><d:BC_10YEAR m:type="Edm.Double">5.99</d:BC_10YEAR>
</m:properties></content></entry><entry><content><m:properties><d:NEW_DATE m:type="Edm.DateTime">2026-11-16T00:00:00</d:NEW_DATE>
<d:BC_3MONTH m:type="Edm.Double">4.41</d:BC_3MONTH><d:BC_2YEAR m:type="Edm.Double">4.83</d:BC_2YEAR><d:BC_10YEAR m:type="Edm.Double">5.12</d:BC_10YEAR>
<d:BC_30YEAR m:type="Edm.Double">5.40</d:BC_30YEAR></m:properties></content></entry></feed>"""


def test_parse_and_fill():
    got = F.parse_ust_all(XML)
    assert got["2026-11-16"] == {"DGS3MO": 4.41, "DGS2": 4.83, "DGS10": 5.12, "DGS30": 5.40}, got
    src = F.FredData.__new__(F.FredData)
    idx = pd.to_datetime(["2026-11-12", "2026-11-13"])
    src.series = {"DGS2": pd.Series([4.80, 4.88], idx), "DGS10": pd.Series([5.10, 5.15], idx),
                  "DGS3MO": pd.Series([4.39, 4.40], idx), "T10Y2Y": pd.Series([0.30, 0.27], idx)}
    filled = src.apply_treasury(got)
    assert src.series["DGS2"].iloc[-1] == 4.83 and src.series["DGS2"].loc["2026-11-13"] == 4.88   # FRED's 11-13 kept, not 4.99
    assert filled["DGS2"] == ["2026-11-16"] and filled["T10Y2Y"] == ["2026-11-16"]
    assert abs(src.series["T10Y2Y"].iloc[-1] - 0.29) < 1e-9
    assert "DGS30" not in src.series                                     # a series FRED never gave is not invented


if __name__ == "__main__":
    test_parse_and_fill()
    print("ok test_parse_and_fill")
