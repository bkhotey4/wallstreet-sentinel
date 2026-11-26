"""Gemini CODE items 11-26: signed zero in 億元 / z-scores, past index date in the forced-flows lead, zero-revenue guidance."""
from datetime import date, timedelta

from tools.sitekit import tidy_zero


def test_tidy_zero_units():
    assert tidy_zero("合計 +0.0 億元") == "合計 0.0 億元"
    assert tidy_zero("z +0.0（11/26）") == "z 0.0（11/26）"
    assert tidy_zero("z −0.00") == "z 0.00"
    assert tidy_zero("+0.05 億") == "+0.05 億"          # not a zero: keep the sign
    assert tidy_zero("+0.0%") == "0.0%"                  # old behaviour unchanged
    assert tidy_zero("z +0.3") == "z +0.3"
    assert tidy_zero("<script>x='+0.0 億'</script>") == "<script>x='+0.0 億'</script>"


def test_forced_lead_skips_past_dates():
    import tools.site_forced as SF
    today = date.today()
    y, t3 = (today - timedelta(days=1)).isoformat(), (today + timedelta(days=3)).isoformat()
    fake = {"events": [{"date": y, "kind": "msci"}, {"date": t3, "kind": "msci"}], "past_med": {}, "past": {}}
    orig = SF._view
    SF._view = lambda: fake
    try:
        out = SF.sec_index_events(None)
    finally:
        SF._view = orig
    assert "-1 天" not in out and "還有 3 天" in out


def test_outlook_zero_revenue():
    import inspect
    from wsb.data import earn_release as ER
    src = inspect.getsource(ER)
    assert 'g["unit"] == "B" and not a["v"]' in src


if __name__ == "__main__":
    test_tidy_zero_units()
    test_forced_lead_skips_past_dates()
    test_outlook_zero_revenue()
    print("ok")
