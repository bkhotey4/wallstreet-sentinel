"""台股規則回測（研究用）：台灣 50＋中型 100，四種進場訊號 × 出場規則。

只做歷史回測：不下單、不登入券商、不發 Discord、不上網站。
資料：
- 成分股：MoneyDJ 的 0050／0051 持股明細（今天的名單 → 有存活者偏差，報告會寫明）。
- 價格：yfinance 日線（還原權息），^TWII 加權指數，0050.TW 當對照。
- 外資買賣超：證交所 T86（個股三大法人），只抓 2022 年起（逐日抓，會慢；可續抓）。
執行假設：
- 訊號用當天收盤以前的資料算，隔天開盤成交（不偷看未來）。
- 手續費買賣各 0.1425%（另測折扣 0.06%），出場證交稅 0.3%。
- 漲停開盤不進場；鎖跌停（最高＝最低且收在 −9.5% 以下）當天賣不掉。
- 股數可為零股（本金未定，報告全部用百分比）。

用法：
  python -m tools.tw_rules_backtest universe     # 抓成分股
  python -m tools.tw_rules_backtest prices       # 抓價格
  python -m tools.tw_rules_backtest t86          # 抓外資（可中斷續抓）
  python -m tools.tw_rules_backtest run          # 跑全部組合，輸出 JSON 結果
"""
from __future__ import annotations

import json
import math
import pickle
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
CACHE = BASE / "data_cache"
F_UNIV = CACHE / "twbt_universe.json"
F_PX = CACHE / "twbt_prices.pkl"
F_T86 = CACHE / "twbt_t86.json"
F_RES = CACHE / "twbt_results.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
START = "2014-01-01"                  # 多抓一年給 200 日均線暖機
IS_END = "2021-12-31"                 # 樣本內 2015–2021；樣本外 2022 起
T86_START = date(2022, 1, 3)


# ───────────────────────── 成本 ─────────────────────────
@dataclass
class Costs:
    fee: float = 0.001425
    tax: float = 0.003

    def buy_cash(self, value: float) -> float:          # 買 value 元股票要付的現金
        return value * (1 + self.fee)

    def sell_cash(self, value: float) -> float:         # 賣 value 元股票拿回的現金
        return value * (1 - self.fee - self.tax)

    def round_trip(self) -> float:
        return 1 - self.sell_cash(1) / self.buy_cash(1)


# ───────────────────────── 參數 ─────────────────────────
@dataclass
class Params:
    signal: str = "A"                 # A 回檔均線、B 突破新高、C 外資連買、D 跌深反彈
    market_filter: bool = True        # 加權指數在 200 日均線之上才開新部位
    stop: str = "pct"                 # pct = −7.5%；atr = 2×ATR(14)
    stop_pct: float = 0.075
    atr_mult: float = 2.0
    tp1: Optional[float] = 0.15       # None = 不分批，全部用移動停利
    trail_ma: int = 20
    trail_dd: float = 0.08
    time_stop: int = 60
    risk: float = 0.01
    cap: float = 0.20
    max_pos: int = 8
    breaker_dd: float = 0.10
    breaker_days: int = 10
    foreign_days: int = 3
    costs: Costs = field(default_factory=Costs)

    def label(self) -> str:
        tp = "純移動停利" if self.tp1 is None else f"停利{int(self.tp1 * 100)}%賣半"
        st = "停損7.5%" if self.stop == "pct" else "停損2ATR"
        return f"{self.signal}｜{'大盤濾網' if self.market_filter else '無濾網'}｜{st}｜{tp}"


# ───────────────────────── 資料 ─────────────────────────
def fetch_universe() -> Dict:
    import requests
    out = {"asof": datetime.now().isoformat(timespec="seconds"), "source": "MoneyDJ ETF 持股明細（Basic0007B）"}
    for etf in ("0050", "0051"):
        r = requests.get(f"https://www.moneydj.com/ETF/X/Basic/Basic0007B.xdjhtm?etfid={etf}.TW", headers=UA, timeout=30)
        r.encoding = "utf-8"
        codes = re.findall(r"etfid=(\d{4})\.TW", r.text) + re.findall(r"\((\d{4})\.TW\)", r.text) + re.findall(r">(\d{4})\.TW<", r.text)
        d = re.search(r"資料日期[：:]\s*(\d{4}/\d{2}/\d{2})", r.text)
        out[etf] = sorted({c for c in codes if not c.startswith("00")})
        out[etf + "_date"] = d.group(1) if d else ""
    F_UNIV.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def load_universe() -> List[str]:
    u = json.loads(F_UNIV.read_text(encoding="utf-8"))
    return sorted(set(u["0050"]) | set(u["0051"]))


def fetch_prices(codes: List[str]) -> Dict[str, pd.DataFrame]:
    import yfinance as yf
    tick = [c + ".TW" for c in codes] + ["^TWII", "0050.TW"]
    df = yf.download(tick, start=START, auto_adjust=True, progress=False, group_by="column", threads=True)
    px = {k: df[k].copy() for k in ("Open", "High", "Low", "Close", "Volume")}
    with open(F_PX, "wb") as f:
        pickle.dump({"fetched": datetime.now().isoformat(timespec="seconds"), "px": px}, f)
    return px


def load_prices() -> Dict[str, pd.DataFrame]:
    with open(F_PX, "rb") as f:
        return pickle.load(f)["px"]


def fetch_t86(end: Optional[date] = None, sleep: float = 2.5) -> int:
    """逐日抓 T86 外資買賣超（股），存成 {日期: {代號: 股數}}；已抓過的日子跳過。"""
    import requests
    try:
        hist = json.loads(F_T86.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        hist = {}
    d, end = T86_START, end or date.today()
    n = 0
    while d <= end:
        k = d.isoformat()
        if d.weekday() < 5 and k not in hist:
            try:
                js = requests.get("https://www.twse.com.tw/rwd/zh/fund/T86", headers=UA, timeout=30,
                                  params={"date": d.strftime("%Y%m%d"), "selectType": "ALLBUT0999", "response": "json"}).json()
            except Exception:  # noqa: BLE001
                time.sleep(sleep * 4)
                continue
            if js.get("stat") == "OK" and js.get("data"):
                f = js["fields"]
                i = next(j for j, x in enumerate(f) if x.startswith("外陸資買賣超"))
                hist[k] = {r[0].strip(): int(str(r[i]).replace(",", "") or 0)
                           for r in js["data"] if re.fullmatch(r"\d{4}", r[0].strip())}
            else:
                hist[k] = None                               # 休市日
            n += 1
            if n % 20 == 0:
                F_T86.write_text(json.dumps(hist), encoding="utf-8")
            time.sleep(sleep)
        d += timedelta(days=1)
    F_T86.write_text(json.dumps(hist), encoding="utf-8")
    return n


def load_t86(index: pd.DatetimeIndex, cols: List[str]) -> Optional[pd.DataFrame]:
    try:
        hist = json.loads(F_T86.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    rows = {pd.Timestamp(k): v for k, v in hist.items() if v}
    if not rows:
        return None
    df = pd.DataFrame.from_dict(rows, orient="index").reindex(columns=[c.replace(".TW", "") for c in cols])
    df.columns = cols
    return df.sort_index().reindex(index)


# ───────────────────────── 訊號（只用收盤以前的資料） ─────────────────────────
def atr(H, L, C, n=14):
    pc = C.shift(1)
    tr = np.maximum(H - L, np.maximum((H - pc).abs(), (L - pc).abs()))
    return tr.rolling(n).mean()


def signals(px: Dict[str, pd.DataFrame], kind: str, foreign: Optional[pd.DataFrame] = None, foreign_days=3) -> pd.DataFrame:
    O, H, L, C, V = (px[k] for k in ("Open", "High", "Low", "Close", "Volume"))
    if kind == "A":                                            # 回檔到上升中的 60 日均線
        m60 = C.rolling(60).mean()
        return (m60 > m60.shift(20)) & (L <= m60 * 1.01) & (C >= m60)
    if kind == "B":                                            # 突破 50 日新高且量增
        return (C > H.shift(1).rolling(50).max()) & (V > 1.5 * V.shift(1).rolling(20).mean())
    if kind == "C":                                            # 外資連買 N 天且站上 20 日均線
        if foreign is None:
            return pd.DataFrame(False, index=C.index, columns=C.columns)
        pos = (foreign > 0).astype(float).where(foreign.notna())
        streak = pos.rolling(foreign_days).sum() >= foreign_days
        return streak & (C > C.rolling(20).mean())
    if kind == "D":                                            # 跌深（5 日跌幅 < −2σ）後的第一根上漲
        r5 = C / C.shift(5) - 1
        sd = r5.rolling(250).std()
        z = (r5 / sd).shift(1)
        return (z < -2) & (C > C.shift(1))
    raise ValueError(kind)


# ───────────────────────── 回測引擎 ─────────────────────────
@dataclass
class Pos:
    t: str
    entry_i: int
    entry: float
    shares: float
    stop: float
    peak: float
    tp_done: bool = False
    cost_in: float = 0.0          # 買進付出的現金（含手續費）
    cash_out: float = 0.0         # 已拿回的現金（含稅費）
    pending_exit: bool = False
    armed: bool = False           # 收盤曾站上移動均線後，均線出場才生效（回檔／跌深進場本來就在均線下）
    why: str = ""                 # 隔天開盤出場的原因：trail_ma／trail_dd／time（紙上交易帳本用）


def backtest(px: Dict[str, pd.DataFrame], sig: pd.DataFrame, p: Params, start: str, end: Optional[str] = None,
             index_close: Optional[pd.Series] = None, events: Optional[List[Dict]] = None, settle_end: bool = True) -> Dict:
    """events: when a list is given, every fill is appended as {i, t, kind, px, ...} (kind = entry／tp／stop／trail_ma／
    trail_dd／time) — the paper-trading ledger (tools/tw_paper.py) reads it.  settle_end=False keeps the positions open at
    the end and returns them under "open" instead of closing them at the last close."""
    ev = events.append if events is not None else (lambda _e: None)
    O, H, L, C, V = (px[k] for k in ("Open", "High", "Low", "Close", "Volume"))
    A = atr(H, L, C)
    M = C.rolling(p.trail_ma).mean()
    liq = (C * V).rolling(20).mean()
    if index_close is not None:
        im = index_close.rolling(200).mean()
        mkt_ok = (index_close > im).reindex(C.index).fillna(False)
    else:
        mkt_ok = pd.Series(True, index=C.index)
    dates = C.index
    i0 = int(dates.searchsorted(pd.Timestamp(start)))
    i1 = len(dates) if end is None else int(dates.searchsorted(pd.Timestamp(end), side="right"))
    o, h, l, c = O.values, H.values, L.values, C.values
    cm = C.ffill().values                                  # 停牌／缺資料日用最後收盤估值
    a, m, sg, lq = A.values, M.values, sig.reindex_like(C).fillna(False).values, liq.values
    cols = list(C.columns)
    cash, equity_peak, pause_until = 1.0, 1.0, -1
    pos: Dict[int, Pos] = {}
    eq, expo, trades = [], [], []

    def close_out(j, P, price, frac):
        nonlocal cash
        sh = P.shares * frac
        got = p.costs.sell_cash(sh * price)
        cash += got
        P.cash_out += got
        P.shares -= sh

    for i in range(i0, i1):
        # 1) 開盤：處理昨天收盤決定的出場、和昨天收盤的進場訊號
        for j, P in list(pos.items()):
            if P.pending_exit and not math.isnan(o[i, j]):
                locked = h[i, j] == l[i, j] and c[i, j] <= c[i - 1, j] * 0.905
                if not locked:
                    close_out(j, P, o[i, j], 1.0)
                    ev({"i": i, "t": cols[j], "kind": P.why or "trail", "px": float(o[i, j]), "ret": P.cash_out / P.cost_in - 1})
                    trades.append(_trade(P, cols[j], i))
                    del pos[j]
        can_open = i > i0 and i - 1 >= pause_until and (bool(mkt_ok.iloc[i - 1]) or not p.market_filter)
        if can_open:
            cand = [j for j in np.where(sg[i - 1])[0] if j not in pos and not math.isnan(o[i, j])
                    and not math.isnan(c[i - 1, j]) and o[i, j] < c[i - 1, j] * 1.095]
            cand.sort(key=lambda j: -(lq[i - 1, j] if not math.isnan(lq[i - 1, j]) else 0))
            eq_now = cash + sum(P.shares * cm[i - 1, j] for j, P in pos.items())
            for j in cand:
                if len(pos) >= p.max_pos:
                    break
                entry = o[i, j]
                if p.stop == "pct":
                    stop = entry * (1 - p.stop_pct)
                else:
                    if math.isnan(a[i - 1, j]):
                        continue
                    stop = entry - p.atr_mult * a[i - 1, j]
                dist = (entry - stop) / entry
                if dist <= 0.005:
                    continue
                value = min(eq_now * p.risk / dist, eq_now * p.cap, cash / (1 + p.costs.fee))
                if value <= eq_now * 0.01:
                    continue
                cost = p.costs.buy_cash(value)
                cash -= cost
                pos[j] = Pos(cols[j], i, entry, value / entry, stop, entry, cost_in=cost)
                ev({"i": i, "t": cols[j], "kind": "entry", "px": float(entry), "stop": float(stop), "w": value / eq_now,
                    "mkt_ok": bool(mkt_ok.iloc[i - 1])})
        # 2) 盤中：停損優先（同一天同時碰到停損與停利，保守假設先停損），再停利
        for j, P in list(pos.items()):
            if math.isnan(o[i, j]):
                continue
            if i == P.entry_i:                                  # 進場當天開盤後才看盤中
                lo, hi = l[i, j], h[i, j]
                op = None
            else:
                lo, hi, op = l[i, j], h[i, j], o[i, j]
            locked = h[i, j] == l[i, j] and c[i, j] <= c[i - 1, j] * 0.905
            if lo <= P.stop and not locked:
                px_exit = op if (op is not None and op <= P.stop) else P.stop
                close_out(j, P, px_exit, 1.0)
                ev({"i": i, "t": cols[j], "kind": "stop", "px": float(px_exit), "ret": P.cash_out / P.cost_in - 1})
                trades.append(_trade(P, cols[j], i))
                del pos[j]
                continue
            if p.tp1 is not None and not P.tp_done:
                lvl = P.entry * (1 + p.tp1)
                if hi >= lvl:
                    px_tp = op if (op is not None and op >= lvl) else lvl
                    close_out(j, P, px_tp, 0.5)
                    ev({"i": i, "t": cols[j], "kind": "tp", "px": float(px_tp)})
                    P.tp_done = True
                    P.stop = max(P.stop, P.entry)                # 賣一半後，剩下的停損拉到成本
        # 3) 收盤：更新高點、決定隔天開盤要不要出場
        for j, P in pos.items():
            if math.isnan(c[i, j]):
                continue
            P.peak = max(P.peak, c[i, j])
            if not math.isnan(m[i, j]) and c[i, j] > m[i, j]:
                P.armed = True
            trail_on = p.tp1 is None or P.tp_done
            trail_hit = trail_on and ((P.armed and c[i, j] < m[i, j]) or c[i, j] <= P.peak * (1 - p.trail_dd))
            time_hit = (i - P.entry_i) >= p.time_stop and not P.tp_done
            P.pending_exit = bool(trail_hit or time_hit)
            if P.pending_exit:
                P.why = ("trail_ma" if (P.armed and c[i, j] < m[i, j]) else "trail_dd") if trail_hit else "time"
        val = cash + sum(P.shares * cm[i, j] for j, P in pos.items())
        eq.append(val)
        expo.append((val - cash) / val if val > 0 else 0)
        if val > equity_peak:
            equity_peak = val
        elif val < equity_peak * (1 - p.breaker_dd) and i >= pause_until:
            pause_until = i + p.breaker_days
            equity_peak = val                                    # 暫停後重新計算高點
    e = pd.Series(eq, index=dates[i0:i1])
    if not settle_end:                                          # 紙上交易：留著還沒出場的部位
        still = [{"t": P.t, "entry_i": P.entry_i, "entry": P.entry, "stop": P.stop, "peak": P.peak, "tp_done": P.tp_done,
                  "pending_exit": P.pending_exit, "why": P.why, "value": P.shares * cm[i1 - 1, j],
                  "ret": (P.cash_out + p.costs.sell_cash(P.shares * cm[i1 - 1, j])) / P.cost_in - 1}
                 for j, P in pos.items()]
        return {"equity": e, "exposure": float(np.mean(expo)) if expo else 0.0, "trades": trades, "open": still,
                "cash": cash, "paused": i1 - 1 < pause_until}
    for j, P in list(pos.items()):                              # 期末按收盤結算（不計入已平倉統計）
        close_out(j, P, cm[i1 - 1, j], 1.0)
        trades.append({**_trade(P, cols[j], i1 - 1), "open_at_end": True})
    return {"equity": e, "exposure": float(np.mean(expo)) if expo else 0.0, "trades": trades}


def _trade(P: Pos, t: str, i: int) -> Dict:
    ret = P.cash_out / P.cost_in - 1 if P.cost_in else 0.0
    return {"t": t, "entry_i": P.entry_i, "exit_i": i, "ret": ret, "tp": P.tp_done}


def metrics(res: Dict) -> Dict:
    e = res["equity"]
    if len(e) < 2:
        return {}
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    r = e.pct_change().dropna()
    tr = [t["ret"] for t in res["trades"]]
    wins, loss = [x for x in tr if x > 0], [x for x in tr if x <= 0]
    dd = (e / e.cummax() - 1).min()
    return {"trades": len(tr), "win": len(wins) / len(tr) if tr else 0, "avg_win": float(np.mean(wins)) if wins else 0,
            "avg_loss": float(np.mean(loss)) if loss else 0, "cagr": e.iloc[-1] ** (1 / yrs) - 1 if yrs > 0 else 0,
            "maxdd": float(dd), "sharpe": float(r.mean() / r.std() * math.sqrt(252)) if r.std() > 0 else 0,
            "exposure": res["exposure"], "total": float(e.iloc[-1] - 1)}


def buy_hold(series: pd.Series, start: str, end: Optional[str], costs: Costs) -> Dict:
    s = series.dropna()
    s = s[(s.index >= pd.Timestamp(start)) & ((s.index <= pd.Timestamp(end)) if end else True)]
    e = s / s.iloc[0] / costs.buy_cash(1)
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    r = e.pct_change().dropna()
    return {"cagr": e.iloc[-1] ** (1 / yrs) - 1, "maxdd": float((e / e.cummax() - 1).min()),
            "sharpe": float(r.mean() / r.std() * math.sqrt(252)), "total": float(e.iloc[-1] - 1)}


# ───────────────────────── 全部組合 ─────────────────────────
def grid() -> List[Params]:
    out = []
    for s in "ABCD":
        for mf in (True, False):
            for st in ("pct", "atr"):
                for tp in (0.10, 0.15, 0.20, None):
                    out.append(Params(signal=s, market_filter=mf, stop=st, tp1=tp))
    return out


def run_all() -> Dict:
    px = load_prices()
    idx = px["Close"]["^TWII"]
    bench = px["Close"]["0050.TW"]
    stocks = [c for c in px["Close"].columns if c not in ("^TWII", "0050.TW")]
    spx = {k: v[stocks] for k, v in px.items()}
    foreign = load_t86(spx["Close"].index, stocks)
    sigs = {k: signals(spx, k, foreign) for k in "ABCD"}
    periods = {"IS": ("2015-01-01", IS_END), "OOS": ("2022-01-01", None)}
    rows = []
    for p in grid():
        row = {"label": p.label(), "params": {k: v for k, v in asdict(p).items() if k != "costs"}}
        for name, (s, e) in periods.items():
            if p.signal == "C" and name == "IS":
                row[name] = None                                     # 外資資料 2022 才開始
                continue
            row[name] = metrics(backtest(spx, sigs[p.signal], p, s, e, idx))
        rows.append(row)
    # 折扣手續費情境：只重跑樣本外
    disc = []
    for p in grid():
        p.costs = Costs(fee=0.0006)
        disc.append({"label": p.label(), "OOS": metrics(backtest(spx, sigs[p.signal], p, "2022-01-01", None, idx))})
    t86_days = 0
    if foreign is not None:
        t86_days = int(foreign.notna().any(axis=1).sum())
    out = {"generated": datetime.now().isoformat(timespec="seconds"), "stocks": len(stocks),
           "data_end": str(spx["Close"].index[-1].date()), "t86_days": t86_days,
           "bench": {n: buy_hold(bench, s, e, Costs()) for n, (s, e) in periods.items()},
           "rows": rows, "discount_fee_oos": disc}
    F_RES.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "universe":
        u = fetch_universe()
        print(len(u["0050"]), len(u["0051"]), u.get("0050_date"), u.get("0051_date"))
    elif cmd == "prices":
        px = fetch_prices(load_universe())
        print(px["Close"].shape, px["Close"].index[-1])
    elif cmd == "t86":
        print("fetched days:", fetch_t86())
    else:
        r = run_all()
        print("rows", len(r["rows"]), "data_end", r["data_end"], "t86_days", r["t86_days"])
