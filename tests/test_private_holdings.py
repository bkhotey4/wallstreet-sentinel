"""Private holdings: local settings override, holdings-only-to-owner routing, public views hide holdings.
Run: python -m tests.test_private_holdings"""
from __future__ import annotations

import os
import tempfile
import time
import types
from pathlib import Path

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_priv_"))

import tests.test_offline as T  # noqa: E402
from wsb import config as C, store  # noqa: E402


def main():
    # ---------------------------------------------------------------- settings.local.yaml deep-merges over settings.yaml
    d = Path(tempfile.mkdtemp())
    (d / "settings.yaml").write_text("portfolio:\n  enabled: false\n  benchmark: SPY\nalerts:\n  sigma_move: 3\n", encoding="utf-8")
    assert C.load_settings(d / "settings.yaml").get("portfolio")["enabled"] is False          # no local file → unchanged
    (d / "settings.local.yaml").write_text("portfolio:\n  enabled: true\n  file: data_cache/holdings.json\n", encoding="utf-8")
    m = C.load_settings(d / "settings.yaml").get("portfolio")
    assert m["enabled"] is True and m["file"] == "data_cache/holdings.json" and m["benchmark"] == "SPY"
    assert C.load_settings(d / "settings.yaml").get("alerts")["sigma_move"] == 3

    # ---------------------------------------------------------------- a malformed holdings entry never raises
    from wsb.analytics import portfolio as PF
    assert PF._raw_holdings({"holdings": [{"sym": "NVDA", "shares": 1, "cost": 1}]}, "")["NVDA"]["shares"] == 1
    try:
        PF._raw_holdings({"holdings": [{"shares": 1}]}, "")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
    assert PF._raw_holdings({"548": {"holdings": {"TSM": {"shares": 2}}}}, "548") == {"TSM": {"shares": 2}}
    assert PF._raw_holdings([], "") is None

    # ---------------------------------------------------------------- holdings alerts never show in public lists
    store.alert_mark("pf_dd:2026-10-13", "🚨 CRITICAL", "持倉單日回撤 -3.2%（$-12,345）", kind="risk")
    store.alert_mark("ssi_level_3", "⚠️ WARNING", "系統性壓力升級", kind="risk")
    store.alert_mark("stop:NVDA:2026-10-13", "⚠️ WARNING", "NVDA 跌破波動停損線", kind=None)
    pub = [t for _, _, t in store.recent_alerts(24)]
    priv = [t for _, _, t in store.recent_alerts(24, include_private=True)]
    assert "系統性壓力升級" in pub and not any("持倉" in t or "NVDA" in t for t in pub), pub
    assert any("持倉" in t for t in priv) and any("NVDA" in t for t in priv)
    assert store.is_private_alert("pf_dd:x") and store.is_private_alert("conc:2026W41") and not store.is_private_alert("danger:us:1")

    # ---------------------------------------------------------------- DM-only detection
    from wsb.bot.app import Sentinel
    import discord
    dm = types.SimpleNamespace(recipient=object(), id=1)
    ch = types.SimpleNamespace(id=2, guild=object())
    assert Sentinel._all_dm([dm]) and not Sentinel._all_dm([dm, ch]) and not Sentinel._all_dm([]) and not Sentinel._all_dm([ch])

    # ---------------------------------------------------------------- public DATA PACK / calendar hide holdings' earnings
    import tests.test_intel as TI
    from wsb.ai import context
    from wsb.analytics import regime as RG, shock as SK
    from wsb.analytics.stress import StressEngine
    st = StressEngine(T.m, T.fr).compute()
    full = TI.T_engine(st, RG.classify(T.m, T.fr), SK.build(st, T.m.series("^GSPC")), [])
    evs = [{"date": "2026-10-20", "event": "CPI", "type": "macro"}, {"date": "2026-10-22", "event": "NVDA 財報", "type": "earnings", "ticker": "NVDA"}]
    full.calendar = types.SimpleNamespace(events=evs, upcoming=lambda d=14: evs)
    full.age_str = lambda: "test"
    assert "NVDA 財報" in context.build(full, "full") and "NVDA 財報" not in context.build(full, "full", private=False)
    from wsb.bot import embeds as E
    assert "NVDA 財報" in E.calendar(full, True).description and "NVDA 財報" not in E.calendar(full, False).description
    print("PRIVATE HOLDINGS TESTS PASSED ✅")


if __name__ == "__main__":
    main()
