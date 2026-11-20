"""台股規則 v1 紙上交易前測（2026-11-21 開始）：用 tools/tw_rules_backtest.py 同一套訊號與出場程式，往後每天照規則記帳。

只是紙上記帳：不下單、不登入券商、不碰任何下單程式。金額是假設的 100 萬元本金，網站只顯示百分比與這個假設本金。

做法（每個交易日收盤後重算一次）：
- 名單：開始那天凍結的台灣 50＋中型 100（tools/tw_paper_universe.json），之後不改，避免事後挑選。
- 價格：yfinance 日線「原始價格」（不還原權息），等於實際看得到的成交價；所以除息那天的跌幅會算進去、股利沒有加回，
  帳上報酬會比實際少一點。
- 從開始日（2026-11-20 收盤）往後每天用回測引擎重跑一次：引擎只用當天收盤以前的資料決定、隔天開盤成交，
  所以重跑結果和逐日記帳一樣，快取不見也能完整重建。
- 主帳本：B 突破 50 日新高＋量增｜不加大盤濾網｜停損 −7.5%｜漲 20% 出一半（回測樣本外最好的一組）。
  對照帳本：同一組加上「加權指數在 200 日線之上才開新部位」。每筆進場都記下當時濾網是開還是關。
- 狀態存在 data_cache/econ_tw_paper.json（econ_* 在 GitHub Actions 的資料快取裡，每次建置會還原）。
"""
from __future__ import annotations

import json
import logging
import math
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from tools import tw_rules_backtest as TB
from wsb.config import DATA_DIR

log = logging.getLogger(__name__)
TPE = timezone(timedelta(hours=8))
UNIV = Path(__file__).with_name("tw_paper_universe.json")
STATE = DATA_DIR / "econ_tw_paper.json"
NOTIONAL = 1_000_000
WARM_DAYS = 420                                     # 200 日線＋50 日新高＋ATR 暖機（日曆天）
CLOSE_HM = (14, 30)                                 # 台股 13:30 收盤，日線約 14:30 後穩定
MAIN = TB.Params(signal="B", market_filter=False, stop="pct", stop_pct=0.075, tp1=0.20)
FILT = replace(MAIN, market_filter=True)
KIND = {"entry": "進場（隔天開盤紙上成交）", "tp": "漲 20% 先出一半", "stop": "碰到停損出場", "trail_ma": "收盤跌破 20 日均線出場",
        "trail_dd": "從最高回落 8% 出場", "time": "60 個交易日沒漲到 20%，時間到出場", "trail": "移動停利出場"}
V = 2                                               # 計算方式改了就加 1：快取裡的舊版會立刻重算
ENOUGH = 30                                         # 已出場筆數到 30 筆前，成績只能當參考


def universe() -> Dict:
    return json.loads(UNIV.read_text(encoding="utf-8"))


def boundary(now: datetime) -> datetime:
    """The latest weekday 14:30 Taipei at or before `now` (holidays just recompute once with no new bar)."""
    t = now.astimezone(TPE)
    b = t.replace(hour=CLOSE_HM[0], minute=CLOSE_HM[1], second=0, microsecond=0)
    if t < b:
        b -= timedelta(days=1)
    while b.weekday() >= 5:
        b -= timedelta(days=1)
    return b


def due(state: Optional[Dict], now: datetime) -> bool:
    if not state or not state.get("computed_at") or state.get("v") != V:
        return True
    try:
        last = datetime.fromisoformat(state["computed_at"])
    except ValueError:
        return True
    return last < boundary(now)


def fetch(codes: List[str], start: str) -> Dict[str, pd.DataFrame]:
    import yfinance as yf
    first = (pd.Timestamp(start) - pd.Timedelta(days=WARM_DAYS)).strftime("%Y-%m-%d")
    tick = [c + ".TW" for c in codes] + ["^TWII", "0050.TW"]
    df = yf.download(tick, start=first, auto_adjust=False, progress=False, group_by="column", threads=True, timeout=30)
    return {k: df[k].copy() for k in ("Open", "High", "Low", "Close", "Volume")}


def _ds(ts) -> str:
    return pd.Timestamp(ts).strftime("%Y-%m-%d")


def _maxdd(e: List[float]) -> float:
    peak, dd = -math.inf, 0.0
    for v in e:
        peak = max(peak, v)
        dd = min(dd, v / peak - 1)
    return dd


def ledger(px: Dict[str, pd.DataFrame], p: TB.Params, start: str, names: Dict[str, str]) -> Dict:
    """One variant's paper ledger: fills, open positions, equity vs 0050."""
    stocks = [c for c in px["Close"].columns if c not in ("^TWII", "0050.TW")]
    pu = {k: v[stocks] for k, v in px.items()}
    idx = px["Close"]["^TWII"].ffill()                # 指數某天缺資料（Yahoo 晚更新）時沿用前一天，不讓濾網誤判成「線下」
    sig = TB.signals(pu, "B")
    ev: List[Dict] = []
    res = TB.backtest(pu, sig, p, start, index_close=idx, events=ev, settle_end=False)
    dates = pu["Close"].index
    nm = lambda t: names.get(t.replace(".TW", ""), "")  # noqa: E731
    fills = [{"date": _ds(dates[e["i"]]), "sym": e["t"], "name": nm(e["t"]), "kind": e["kind"], "px": round(e["px"], 2),
              **({"stop": round(e["stop"], 2), "w": round(e["w"], 4), "mkt_ok": e["mkt_ok"]} if e["kind"] == "entry" else {}),
              **({"ret": round(e["ret"], 4)} if "ret" in e else {})} for e in ev]
    opened = [{"sym": o["t"], "name": nm(o["t"]), "since": _ds(dates[o["entry_i"]]), "entry": round(o["entry"], 2),
               "stop": round(o["stop"], 2), "half_out": o["tp_done"], "exit_next_open": o["pending_exit"],
               "why": KIND.get(o["why"], "") if o["pending_exit"] else "", "ret": round(o["ret"], 4),
               "w": round(o["value"] / res["equity"].iloc[-1], 4) if len(res["equity"]) else 0.0} for o in res["open"]]
    closed = [t for t in res["trades"]]
    eq = [float(v) for v in res["equity"].values]
    b = px["Close"]["0050.TW"].ffill().reindex(res["equity"].index).ffill()
    bench = [float(v / b.iloc[0]) for v in b.values] if len(b) and b.iloc[0] == b.iloc[0] else []
    rets = [t["ret"] for t in closed]
    last = dates[-1]
    nxt = []                                      # 今天收盤出現的進場訊號 → 下一個交易日開盤（若名額、濾網、暫停都允許）
    if len(dates):
        held = {o["t"] for o in res["open"]}
        mkt_ok = bool(idx.iloc[-1] > idx.rolling(200).mean().iloc[-1]) if len(idx) >= 200 else False
        blocked = res.get("paused") or (p.market_filter and not mkt_ok) or len(held) >= p.max_pos
        for t in sig.columns[sig.iloc[-1].fillna(False).values]:
            if t not in held:
                nxt.append({"sym": t, "name": nm(t), "close": round(float(pu["Close"][t].iloc[-1]), 2), "blocked": bool(blocked)})
    return {
        "label": p.label(), "fills": fills, "open": opened,
        "equity": [[_ds(d), round(v, 5)] for d, v in zip(res["equity"].index, eq)],
        "bench": [[_ds(d), round(v, 5)] for d, v in zip(res["equity"].index, bench)],
        "total": round(eq[-1] - 1, 4) if eq else 0.0, "bench_total": round(bench[-1] - 1, 4) if bench else None,
        "maxdd": round(_maxdd(eq), 4) if eq else 0.0, "closed": len(closed),
        "hit": round(sum(r > 0 for r in rets) / len(rets), 3) if rets else None,
        "avg": round(sum(rets) / len(rets), 4) if rets else None, "paused": bool(res.get("paused")),
        "next": nxt, "data_end": _ds(last),
    }


def compute(px: Dict[str, pd.DataFrame], u: Dict, now: datetime) -> Dict:
    idx = px["Close"]["^TWII"].dropna()
    m200 = idx.rolling(200).mean()
    return {
        "v": V, "computed_at": now.astimezone(TPE).isoformat(timespec="seconds"), "start": u["start"], "notional": NOTIONAL,
        "universe": {"n": len(u["codes"]), "frozen": u["frozen"], "source": u["source"]},
        "mkt": {"twii": round(float(idx.iloc[-1]), 2), "ma200": round(float(m200.iloc[-1]), 2) if m200.notna().iloc[-1] else None,
                "date": _ds(idx.index[-1])},
        "main": ledger(px, MAIN, u["start"], u.get("names") or {}),
        "filter": ledger(px, FILT, u["start"], u.get("names") or {}),
        "src": "Yahoo Finance 日線（原始價格，不還原權息）；規則與程式：tools/tw_rules_backtest.py",
    }


def load() -> Dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def refresh(now: Optional[datetime] = None, force: bool = False) -> Dict:
    now = now or datetime.now(TPE)
    st = load()
    if not force and not due(st, now):
        return st
    try:
        u = universe()
        out = compute(fetch(u["codes"], u["start"]), u, now)
    except Exception as e:  # noqa: BLE001  (keep the last good ledger; the card says it is stale)
        log.warning("tw_paper refresh failed: %s", e)
        return dict(st, err=f"{type(e).__name__}: {str(e)[:120]}") if st else {"err": f"{type(e).__name__}"}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def events(d: Dict) -> List[Dict]:
    """Main-ledger fills with a stable key, for the Discord relay (tools/sec_push.py)."""
    out = []
    for f in ((d.get("main") or {}).get("fills") or []):
        out.append({**f, "key": f"paper:{f['date']}:{f['sym']}:{f['kind']}"})
    return out


def public(d: Optional[Dict] = None) -> Dict:
    d = load() if d is None else d
    return {"ts": d.get("computed_at"), "data_end": (d.get("main") or {}).get("data_end"), "events": events(d)} if d else {"ts": None, "events": []}


if __name__ == "__main__":
    import sys
    r = refresh(force="--force" in sys.argv)
    m = r.get("main") or {}
    print(r.get("computed_at"), r.get("err", ""), "資料到", m.get("data_end"), "持有", len(m.get("open") or []),
          "成交", len(m.get("fills") or []), "明天訊號", [(x["sym"], x["name"], x["blocked"]) for x in m.get("next") or []])
