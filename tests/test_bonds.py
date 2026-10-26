"""全球債市: MOF weekly / TIC parsing, the flow views, government and corporate bond rows, the plain-language read in both
directions (calm and stressed), and the cards' wording."""
import os
import re
import sys
import tempfile
import types
from pathlib import Path

os.environ["WSB_DATA_DIR"] = tempfile.mkdtemp()                       # never touch the real data_cache
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from wsb.analytics import bonds as BD  # noqa: E402
from wsb.data import bondflows as BF  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出")
MOF_ROW = '{w},"1","1",0 ,"1","1","{n}","0","1","1",0 ,"0","1","1",0 ,"1","1","{j}","0","1","1",0 ,"0"'


def test_parse_mof_and_view():
    lines = ["header,,,"] + [MOF_ROW.format(w=f"2025．{1 + i // 4}．{1 + (i % 4) * 7}〜{(i % 4) * 7 + 7}", n=f"{(-1) ** (i + 1) * 1000:,}", j="500")
                             for i in range(40)]
    lines += [MOF_ROW.format(w=f"2026．1．{1 + i}〜{7 + i}", n="-5,000", j="100") for i in range(30)]
    rows = BF.parse_mof("\n".join(lines))
    assert len(rows) == 70 and rows[0][2] == -1000 and rows[-1][2] == -5000 and rows[-1][3] == 100
    v = BF.mof_view({"mof": rows})
    assert v["run"] == 30 and abs(v["sum5"] + 2.5) < 1e-9 and v["since"] == "2025"


def test_parse_tic_and_view():
    months = [f"2025-{m:02d}" for m in range(12, 0, -1)] + ["2024-12"]
    head = "Country\t" + "\t".join(["2026-01"] + months[:-1])
    txt = "Table 5\n" + head + "\n" + "Japan\t" + "\t".join(str(1000 - i * 10) for i in range(13)) + "\n" \
          + "Grand Total\t" + "\t".join(str(9000 + i) for i in range(13)) + "\n" + "Of Which: Foreign Official\t" + "\t".join("3700" for _ in range(13)) + "\n"
    t = BF.parse_tic(txt)
    assert t["Japan"]["2026-01"] == 1000.0 and len(t["Japan"]) == 13
    v = BF.tic_view({"tic": t})
    jp = v["rows"][0]
    assert v["month"] == "2026-01" and jp["zh"] == "日本" and jp["chg6"] > 0 and v["official"]["zh"].startswith("外國官方")


def _eng(stress: bool):
    idx_d = pd.bdate_range("2023-10-01", "2026-10-22")
    idx_m = pd.date_range("1990-01-01", "2026-09-01", freq="MS")
    ser = {}
    for _, _, src, sid in BD.SOVEREIGN:
        if src == "fred":
            base = np.linspace(2, 4, len(idx_m)) if stress else np.linspace(5, 2, len(idx_m))
            ser[sid] = pd.Series(base + np.r_[np.zeros(len(idx_m) - 13), np.linspace(0, 1 if stress else -1, 13)], index=idx_m)
    for _, _, oas, ey, kind in BD.CORP:
        lv = 3.0 if kind == "hy" else 1.0
        path = np.r_[np.full(len(idx_d) - 63, lv), np.linspace(lv, lv * (1.6 if stress else 0.8), 63)]
        ser[oas] = pd.Series(path, index=idx_d)
        if ey:
            ser[ey] = pd.Series(path + 4, index=idx_d)
    ser["THREEFYTP10"] = pd.Series(np.linspace(-0.5, 1.0 if stress else -0.6, 1000), index=pd.bdate_range("2022-01-03", periods=1000))
    jgb = pd.Series(np.linspace(0.1, 3.0 if stress else 0.2, 3000), index=pd.bdate_range("2015-01-01", periods=3000))
    return types.SimpleNamespace(fred=types.SimpleNamespace(get=lambda s: ser.get(s, pd.Series(dtype=float))),
                                 global_yields=types.SimpleNamespace(get=lambda t: jgb if t == "10Y" else pd.Series(dtype=float)))


def test_read_both_directions():
    hot = BD.build(_eng(True))
    hot["flows"] = {"mof": {"sum5": -3.4, "pct5": 2.0}, "tic": {"rows": [{"name": "Japan", "chg6": -14.0}]}}
    rd = BD.read(hot)
    assert "政府借錢變貴" in rd["head"] and "利差在擴大" in rd["head"] and "日本資金在回家" in rd["head"]
    assert any("大買家" in x for x in rd["imp"]) and any("期限溢酬" in x for x in rd["imp"])
    calm = BD.build(_eng(False))
    calm["flows"] = {"mof": {"sum5": 0.5, "pct5": 60.0}, "tic": {}}
    rc = BD.read(calm)
    assert "政府借錢變便宜" in rc["head"] and "低檔" in rc["head"] and "日本資金" not in rc["head"]


def test_cards_wording():
    from tools import site_bonds as SB
    e = _eng(True)
    e._bonds = BD.build(e)
    e._bonds["flows"] = {"mof": {"sum5": -3.4, "pct5": 2.0, "run": 5, "since": "2005", "sum13": -2.6, "sum52": -5.3,
                                 "weeks": [["2026．10．11〜10．17", -0.16]]},
                         "tic": {"month": "2026-08", "total": 9331.7, "total_chg6": -1.6,
                                 "rows": [{"name": "Japan", "zh": "日本", "now": 1068.3, "chg6": -13.8, "chg12": -9.8}], "official": None}}
    jgb = pd.DataFrame({t: np.linspace(0.1, 2.0, 3000) for t in ("1Y", "2Y", "5Y", "10Y", "20Y", "30Y")}, index=pd.bdate_range("2015-01-01", periods=3000))
    e.global_yields.jgb = jgb
    fs = (SB.sec_gb_brief, SB.sec_gb_flows, SB.sec_gb_tic, SB.sec_gb_jgb, SB.sec_gb_mof, SB.sec_gb_europe, SB.sec_gb_sovereign,
          SB.sec_cb_brief, SB.sec_gb_corp, SB.sec_cb_us, SB.sec_cb_eu, SB.sec_cb_em)
    h = "".join(f(e) for f in fs)
    t = re.sub(r"<[^>]+>", " ", h)
    assert t.count("一句話看懂") == len(fs) and "日本" in t and "CCC" in t and "不是投資建議" in t and "歐洲公債" in t
    assert "連體質好的公司都被要求付更高的利息" in t                               # stressed fixture: investment grade widens too
    assert not [b for b in BANNED if b in t], [b for b in BANNED if b in t]
    from tools import site_layout as LY
    assert LY.GROUP_OF["gbonds"] == LY.GROUP_OF["jgb"] == "bond" and LY.GROUP_OF["cb_us"] == "credit"


def test_rotation():
    import types
    idx = pd.bdate_range("2025-01-01", periods=400)
    y = pd.Series(4.5, index=idx)
    y.iloc[-1] = 4.10                                                   # one big drop on the last day: -40 bp
    spx = pd.Series(100.0, index=idx)
    spx.iloc[-10:] = 95.0                                               # -5% within the month
    eng = types.SimpleNamespace(fred=types.SimpleNamespace(get=lambda s: y if s in ("DGS10", "DGS2") else pd.Series(dtype=float)),
                                market=types.SimpleNamespace(series=lambda t: spx))
    r = BD.rotation(eng)
    assert r["state"] == "股跌債漲" and abs(r["d10"] + 40) < 1e-6 and abs(r["big"]["bp"] + 40) < 1e-6
    y2 = y.copy()
    y2.iloc[-1] = 4.9
    eng.fred.get = lambda s: y2 if s in ("DGS10", "DGS2") else pd.Series(dtype=float)
    assert BD.rotation(eng)["state"] == "股債雙殺"
    from tools import site_bonds as SB
    eng._bonds = {"available": True, "rot": r}
    h = SB.sec_gb_rotation(eng)
    assert "一句話看懂：股跌債漲" in h and not [b for b in BANNED if b in h]


def test_mmf_view():
    tot = [[f"{2010 + i // 12}-{i % 12 + 1:02d}", 3e12 * (1.01 ** i)] for i in range(60)]
    v = BF.mmf_view({"mmf": {"tot": tot, "tsy": [[tot[-1][0], tot[-1][1] * 0.4]]}})
    assert v["high"] and abs(v["chg1"] - 1) < 1e-6 and abs(v["tsy_share"] - 40) < 1e-6 and v["since"] == "2010"
    assert BF.mmf_view({"mmf": {"tot": tot[:10]}}) is None


def main():
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f()
            print("ok", k)


if __name__ == "__main__":
    main()
