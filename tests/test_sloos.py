"""銀行放款調查卡：燈號只和自己歷史比、整體燈號、一句話、卡片會出現。Run: python -m tests.test_sloos"""
import pandas as pd

from wsb.analytics import sloos as SL


def _q(vals, start="2000-01-01"):
    return pd.Series(vals, index=pd.date_range(start, periods=len(vals), freq="QS"))


def test_lights_and_lead():
    calm = [0.0] * 40 + [5.0, 10.0, 60.0, 30.0] + [0.0] * 20      # one crisis peak in the past
    data = {
        "DRTSCILM": _q(calm[:-1] + [2.0]),                           # now normal
        "DRSDCILM": _q([0.0] * 63 + [-12.0]),
        "SUBLPDRCSN": _q(calm[:-1] + [45.0]),                        # now near the top → red (business)
        "DRTSCLCC": _q(calm[:-5] + [0.0, 0.0, 0.0, 0.0, 25.0]),      # +25 in a year → at least yellow
        "STDSAUTO": _q(calm[:-1] + [-3.0]),                          # loosening → green
    }
    v = SL.view(lambda sid: data.get(sid))
    by = {r["key"]: r for r in v["rows"]}
    assert set(by) == {"ci_big", "cre_office", "card", "auto"}, by.keys()
    assert by["ci_big"]["emoji"] == "🟢" and by["ci_big"]["dem"] == -12.0 and by["ci_big"]["max"] == 60.0
    assert by["cre_office"]["emoji"] == "🔴" and by["card"]["emoji"] in ("🟡", "🔴") and by["auto"]["emoji"] == "🟢"
    assert by["auto"]["state"] == "放寬"
    assert v["emoji"] == "🔴" and v["n_tight"] == 3 and v["n_loose"] == 1
    t = SL.lead(v)
    assert "4 類貸款裡，3 類銀行在收緊、1 類在放寬" in t and "商辦與其他商用不動產" in t and "企業借錢的需求淨 -12%（變弱）" in t, t
    assert SL.view(lambda sid: None) == {}


def test_card_renders():
    from tools import site_stability as SST

    class E:
        pass
    e = E()
    data = {"DRTSCILM": _q([0.0] * 40 + [60.0] + [0.0] * 20 + [1.7])}
    e.fred = data
    h = SST.sec_st_sloos(e)
    assert 'id="st-sloos"' in h and "一句話看懂" in h and "+2%" in h and "回到重點" in h, h[:300]
    assert "歷史最緊" in h and "+60%（2010-01）" in h


if __name__ == "__main__":
    test_lights_and_lead()
    print("ok test_lights_and_lead")
    test_card_renders()
    print("ok test_card_renders")
