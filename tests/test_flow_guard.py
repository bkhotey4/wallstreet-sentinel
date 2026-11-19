from tools import flow_guard as FG

FLOWS = [{"date": "2026-11-18", "foreign": -765.6}, {"date": "2026-11-17", "foreign": -120.3}]


def test_digit_slip_fixed():
    out = FG.fix("台股：外資賣超 76.5 億元、期貨空單創新高", FLOWS)
    assert "765.6 億" in out and FG.TAG in out


def test_correct_and_unrelated_left_alone():
    s = "外資賣超 765.6 億；外資買超 300 億；營收約 76.5 億歐元"
    assert FG.fix(s, FLOWS) == s


def test_no_flows_noop():
    assert FG.fix("外資賣超 76.5 億", []) == "外資賣超 76.5 億"


if __name__ == "__main__":
    test_digit_slip_fixed(); test_correct_and_unrelated_left_alone(); test_no_flows_noop(); print("ok")
