"""market/tw_inputs.json: what the monthly Taiwan-note routine reads instead of the government sites."""
from wsb.data import twmacro as T


def main() -> None:
    d = {"ts": 1.0, "cbc": {"tw10y": [[f"2024-{m:02d}", 1.5] for m in range(1, 13)] + [["2025-01", 1.6]]},
         "ndc": {"light": [["2026-08", "紅"], ["2026-09", "紅"]]}, "taipei": [["2026-07", 131.2]],
         "daily": {"2026-11-09": {"gov": {"10": 2.0}}, "2026-11-10": {"gov": {"10": 2.03}}}}
    o = T.public_inputs(d, months=5, us10y=[["2026-10", 4.9]])
    assert len(o["cbc"]["tw10y"]) == 5 and o["cbc"]["tw10y"][-1] == ["2025-01", 1.6]
    assert o["ndc"]["light"][-1] == ["2026-09", "紅"]
    assert o["tpex_curve"]["date"] == "2026-11-10" and o["tpex_curve"]["gov"]["10"] == 2.03
    assert o["us10y_monthly"] == [["2026-10", 4.9]] and o["sources"]["tpex"].startswith("https://")
    e = T.public_inputs({}, us10y=None)
    assert e["tpex_curve"] is None and "us10y_monthly" not in e and e["cbc"] == {}
    print("test_tw_inputs: ok")


if __name__ == "__main__":
    main()
