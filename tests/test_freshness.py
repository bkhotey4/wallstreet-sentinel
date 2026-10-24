"""Every site card and every Discord embed / slide says when it was made and how old its data is.
Run: python -m tests.test_freshness"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
import types

os.environ.setdefault("WSB_DATA_DIR", tempfile.mkdtemp(prefix="wsb_fr_"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord  # noqa: E402

from tools import site_stamp as STP  # noqa: E402
from wsb.bot import embeds as E  # noqa: E402
from wsb.bot import slides as SL  # noqa: E402


class Mkt:
    quotes_ts = time.time() - 300

    def q(self, t):
        return {"asof": "2026-10-23", "price": 1.0}

    def series(self, t):
        import pandas as pd
        return pd.Series(dtype=float)


ENG = types.SimpleNamespace(market=Mkt(), recompute_ts=time.time() - 120)


def test_site_inject_and_fallback():
    h = '<section id="ai-x" class="card wide"><h2>A</h2><p>x</p></section><section class="card"><h2>B</h2></section>'
    out = STP.inject(h, "<p class=upd>S</p>")
    assert out.count("<p class=upd>S</p>") == 2, out                              # an id before class is still a card
    nt = STP.inject('<section class="card wide pmcard"><details><summary>x</summary></details></section>', "<p class=upd>S</p>")
    assert nt.startswith('<section class="card wide pmcard"><p class=upd>S</p><details'), nt   # a card without a title still gets one
    st = STP.stamp(ENG, "sec_terms", "about")
    assert "系統更新" in st and "data-ts" in st                                    # static cards say when the page was built
    st2 = STP.stamp(types.SimpleNamespace(), "sec_unknown_card", "nosuchtab")
    assert "系統更新" in st2                                                       # nothing known → still a time, never blank
    print("ok site stamps")


def test_embed_stamp_once():
    e = discord.Embed(title="t")
    e.set_footer(text="資料：Nasdaq")
    E.stamp_embed(e, ENG)
    E.stamp_embed(e, ENG)
    ft = e.footer.text
    assert ft.startswith("資料：Nasdaq") and ft.count("🕒") == 1 and "系統更新" in ft and "報價" in ft and "美股資料日 10-23" in ft, ft
    f = E.footer(discord.Embed(title="u"), ENG)
    assert "🕒 系統更新" in f.footer.text and "非投資建議" in f.footer.text
    big = discord.Embed(title="b", description="x" * 4096)
    for i in range(3):
        big.add_field(name="f", value="y" * 630)
    E.stamp_embed(big, ENG)
    assert not big.footer.text and len(big) <= 6000                              # an embed near the limit is left alone
    old = types.SimpleNamespace(market=types.SimpleNamespace(quotes_ts=time.time() - 7200, q=lambda t: {}), recompute_ts=None)
    assert "報價偏舊" in E.data_stamp(old)
    print("ok embed stamp")


def test_install_wraps_sends():
    rec = {}

    async def recorder(*a, **k):
        rec.update(k)
    em, ems = discord.Embed(title="x"), [discord.Embed(title="y"), discord.Embed(title="z")]
    asyncio.run(E.wrap_send(recorder, ENG)("ch", content="hi", embed=em))
    asyncio.run(E.wrap_send(recorder, ENG)("ch", embeds=ems))
    assert "🕒" in em.footer.text and all("🕒" in e.footer.text for e in ems) and rec["embeds"] is ems
    E._INSTALLED["done"] = False
    orig = discord.abc.Messageable.send
    try:
        E.install_stamps(ENG)
        assert discord.abc.Messageable.send.__wrapped__ is orig
        assert "報價" in SL.DATA_STAMP()                                          # slides read the same stamp
    finally:
        discord.abc.Messageable.send = orig
    print("ok install")


def test_slide_footer_renders():
    SL.DATA_STAMP = lambda: "系統更新 10/24 14:05 台北｜報價 10/24 14:00（5 分鐘前）"
    s = SL.Slide("測試", "1/1", "副標")
    assert s.im.size[0] > 0
    print("ok slide")


if __name__ == "__main__":
    test_site_inject_and_fallback()
    test_embed_stamp_once()
    test_install_wraps_sends()
    test_slide_footer_renders()
    print("all freshness tests passed")
