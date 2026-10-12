"""Render only the portfolio with synthetic prices, for isolated browser tests."""
import sys
import types
from pathlib import Path
from tools import site_portfolio as SP

quotes = {"TWD=X": {"price": 32, "chg_pct": 0, "asof": "2026-10-13"},
          "NVDA": {"price": 120, "chg_pct": 1, "asof": "2026-10-13"}}
eng = types.SimpleNamespace(market=types.SimpleNamespace(quotes=quotes, q=lambda t: quotes.get(t)))
out = Path(sys.argv[1])
out.write_text('<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><style>' + SP.CSS +
               '</style></head><body>' + SP.sec_portfolio(eng) + '<script>' + SP.JS + '</script></body></html>', encoding='utf-8')
