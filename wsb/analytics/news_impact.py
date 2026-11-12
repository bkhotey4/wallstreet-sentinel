"""個股重大消息的「影響估算」對照表：每次建置替每一家警報名單公司算好，瀏覽器拿即時漲跌乘上去。

對每一家公司 S：
  * 大盤：S 在標普 500 的權重（State Street SPY 官方每日持股檔）→ S 動 x%，標普約動 權重 × x%（只算 S 本身，不含連帶效應）
  * 同族群：同主題（本站追蹤池）＋全部追蹤池裡，過去 120 個交易日和 S 日報酬相關最高的 5 檔；β＝S 動 1% 時它平均動幾 %
  * 台股：tw_link（個股台美連動，樣本外驗證過）裡「最連動的美股」就是 S、而且通過驗證的台股；β＝S 昨晚動 1% 時隔天平均動幾 %
結果寫 impact_map.json（公開、只有行情統計）。這是過去的平均關係，不是預測；重大消息當天常比平均更極端。"""
from __future__ import annotations

import io
import json
import logging
import time
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR
from ..data import http

log = logging.getLogger(__name__)
SPY_URL = "https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"
SPY_FILE = DATA_DIR / "econ_spy_weights.json"
WIN = 120
MIN_OBS = 80
TOP = 5


def parse_spy(raw: bytes) -> Dict:
    d = pd.read_excel(io.BytesIO(raw), header=None)
    hdr = next((i for i in range(min(15, len(d))) if str(d.iloc[i, 0]).strip() == "Name"), None)
    if hdr is None:
        return {}
    cols = [str(c).strip() for c in d.iloc[hdr]]
    t, w = cols.index("Ticker"), cols.index("Weight")
    asof = next((str(d.iloc[i, 1]).replace("As of", "").strip() for i in range(hdr) if "Holdings" in str(d.iloc[i, 0])), "")
    out = {}
    for i in range(hdr + 1, len(d)):
        tk, wt = str(d.iloc[i, t]).strip().upper(), d.iloc[i, w]
        try:
            wt = float(wt)
        except (TypeError, ValueError):
            continue
        if tk and tk != "NAN" and wt == wt:
            out[tk.replace(".", "-")] = round(wt, 4)
    return {"asof": asof, "w": out}


async def spy_weights() -> Dict:
    try:
        old = json.loads(SPY_FILE.read_text(encoding="utf-8")) if SPY_FILE.exists() else {}
    except (OSError, ValueError):
        old = {}
    if old.get("w") and time.time() - float(old.get("ts", 0)) < 20 * 3600:
        return old
    try:
        got = parse_spy(await http.get(SPY_URL, kind="bytes", timeout=60, retries=1))
        if len(got.get("w") or {}) > 400:
            got["ts"] = time.time()
            SPY_FILE.write_text(json.dumps(got), encoding="utf-8")
            return got
    except Exception as e:  # noqa: BLE001
        log.warning("SPY holdings: %s", e)
    return old


def peers(ret: pd.DataFrame, s: str, us: List[str], names: Dict[str, tuple]) -> List[Dict]:
    """The US names that moved most with S over the last WIN sessions: correlation and beta (their % per 1% of S)."""
    if s not in ret.columns:
        return []
    r = ret.iloc[-WIN:]
    x = r[s]
    out = []
    for p in us:
        if p == s or p not in r.columns:
            continue
        both = pd.concat([x, r[p]], axis=1).dropna()
        if len(both) < MIN_OBS or both.iloc[:, 0].std() == 0:
            continue
        c = float(both.corr().iloc[0, 1])
        b = float(np.cov(both.iloc[:, 1], both.iloc[:, 0])[0, 1] / both.iloc[:, 0].var())
        out.append({"sym": p, "zh": names.get(p, (p,))[0], "corr": round(c, 2), "beta": round(b, 2)})
    out.sort(key=lambda d: -d["corr"])
    return [d for d in out if d["corr"] >= 0.4][:TOP]


def build(eng, watch: Dict[str, list], spy: Dict) -> Dict:
    """{sym: {zh, w_spx, peers, tw}} for every company in the alert watch list."""
    from ..data.stocks import universe
    sp = getattr(eng, "stockprices", None)
    cl = getattr(sp, "close", None)
    allu = {}
    for mk in ("us", "tw"):
        for k, v in ((universe().get(mk) or {}).get("symbols") or {}).items():
            allu[k] = (v[0], v[1] if len(v) > 1 else k, mk)
    us = [k for k, v in allu.items() if v[2] == "us"]
    ret = cl.pct_change(fill_method=None) * 100 if cl is not None and not cl.empty else pd.DataFrame()
    tl = ((getattr(eng, "sx", None) or {}).get("tlink") or {}).get("rows") or []
    w = spy.get("w") or {}
    out = {}
    for _cik, (s, zh) in watch.items():
        tw = [{"sym": r["sym"], "zh": r["name"], "beta": round(float(r["beta"]), 2), "corr": round(float(r["corr"]), 2)}
              for r in tl if r.get("p") == s and r.get("ok")]
        out[s] = {"zh": zh, "w_spx": w.get(s), "peers": peers(ret, s, us, allu) if not ret.empty else [],
                  "tw": sorted(tw, key=lambda d: -d["corr"])[:TOP]}
    return {"ts": int(time.time()), "spy_asof": spy.get("asof", ""), "win": WIN, "map": out}
