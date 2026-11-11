"""航道監測：IMF PortWatch 每天統計通過全球主要海峽／運河的船隻數（衛星收到的船舶 AIS 訊號，2019 年起）。

看七個和市場最有關的航道：荷姆茲（波斯灣油輪出口）、曼德海峽與蘇伊士運河（紅海 → 歐洲）、好望角（繞道路線）、
巴拿馬運河、麻六甲海峽、台灣海峽。每個航道算「最近 7 天平均每天幾艘」，和
  * 平常水準比：一年前以前（2019 年起）所有 7 天平均的中位數；也列出去年同一段 7 天
  * 自己 2019 年以來所有 7 天平均的排名（百分位）
燈號（本站自訂）：比平常少一半以上 → 🔴；少 25% 以上，或落在自己 2019 年以來最低 10% → 🟡；其他 🟢。
繞道：曼德海峽／蘇伊士變少、好望角變多，代表船改走非洲南端，航程多 1～2 週，運費和到貨時間跟著變。
限制：數的是有開 AIS 的船；戰區船隻常關掉訊號，所以數字可能比實際少。PortWatch 大約每週更新，最新一天通常落後 3～7 天。
另外看紐約聯準會「全球供應鏈壓力指數」GSCPI（月資料，1998 年起，單位是「比長期平均高幾個標準差」）：
船過不去是一條航道的事，GSCPI 把運費、交貨時間、積壓訂單合起來看整體供應鏈有沒有塞住；≥1 偏高 🟡、≥2 很高 🔴（2021 年塞港高峰約 4）。
快取 data_cache/econ_chokepoints.json（CI 保留 econ_*）；第一次抓 2019 年起全部，之後只補最近 30 天。描述現況，不是預測。"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import date, timedelta
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR
from ..health import HEALTH
from . import http

log = logging.getLogger(__name__)
FILE = DATA_DIR / "econ_chokepoints.json"
TTL = 12 * 3600
API = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0/query"
PAGE = "https://portwatch.imf.org/pages/chokepoints"
GSCPI = "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xls"
GSCPI_PAGE = "https://www.newyorkfed.org/research/policy/gscpi"
START = "2019-01-01"
# (PortWatch id, 中文, 英文, 這條路上走的是什麼, 出事時先動的資產)
PORTS = (
    ("chokepoint6", "荷姆茲海峽", "Strait of Hormuz", "波斯灣產油國（沙烏地、伊拉克、阿聯、科威特、卡達）的原油與天然氣出口", "油價、天然氣價、油輪運價"),
    ("chokepoint4", "曼德海峽", "Bab el-Mandeb", "紅海南口：亞洲 ↔ 歐洲貨櫃船走蘇伊士運河的必經之路", "貨櫃運價、歐洲進口物價"),
    ("chokepoint1", "蘇伊士運河", "Suez Canal", "紅海北口：亞洲 ↔ 歐洲最短的海路", "貨櫃運價、埃及外匯收入"),
    ("chokepoint7", "好望角", "Cape of Good Hope", "非洲南端：紅海不能走時的繞道路線（多 1～2 週）", "航程拉長 → 運費、到貨時間"),
    ("chokepoint2", "巴拿馬運河", "Panama Canal", "美國東岸 ↔ 亞洲；乾旱時運河限水會減少通行", "美國農產品出口、液化天然氣運輸"),
    ("chokepoint5", "麻六甲海峽", "Malacca Strait", "中東原油 → 中日韓台的主要航道", "亞洲進口油價、亞洲製造業成本"),
    ("chokepoint11", "台灣海峽", "Taiwan Strait", "中國沿海、台灣、日韓之間的貨櫃與原料航線", "台灣與東亞貿易、半導體供應鏈風險"),
)
RED_RATIO, YEL_RATIO = 0.5, 0.75      # 7 天平均 ÷ 平常水準
YEL_PCT = 10.0                        # 在自己 2019 年以來 7 天平均的百分位


def load() -> Dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8")) if FILE.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


async def _fetch(pid: str, since: str) -> Dict[str, List[int]]:
    """{date: [n_total, n_tanker, n_container]} for one chokepoint since `since` (paged, 1000 rows per call)."""
    out, off = {}, 0
    while True:
        js = await http.get(API, params={"where": f"portid='{pid}' AND date>=DATE '{since}'",
                                         "outFields": "date,n_total,n_tanker,n_container", "orderByFields": "date",
                                         "resultOffset": str(off), "resultRecordCount": "1000", "f": "json"},
                            timeout=60, retries=1)
        if js.get("error"):
            raise ValueError(f"PortWatch: {js['error'].get('message')}")
        fs = [f["attributes"] for f in js.get("features") or []]
        for a in fs:
            if a.get("date") and a.get("n_total") is not None:
                out[str(a["date"])[:10]] = [int(a["n_total"]), int(a.get("n_tanker") or 0), int(a.get("n_container") or 0)]
        if len(fs) < 1000 and not js.get("exceededTransferLimit"):
            return out
        off += len(fs)
        if off > 20000:
            return out


def parse_gscpi(raw: bytes) -> Dict[str, float]:
    """NY Fed workbook → {YYYY-MM: index in standard deviations from its average}."""
    import io
    df = pd.read_excel(io.BytesIO(raw), header=None)
    out = {}
    for dt, v in zip(df.iloc[:, 0], df.iloc[:, 1]):
        t = pd.to_datetime(dt, errors="coerce", format="mixed")
        if pd.notna(t) and isinstance(v, (int, float)) and pd.notna(v):
            out[t.strftime("%Y-%m")] = round(float(v), 3)
    return out


async def refresh(force: bool = False) -> Dict:
    from .freshness import bundle_ts, due
    d = load()
    now = time.time()
    d["ts_check"] = now
    keys = ["ports", "gscpi"]
    todo = due(d, keys, TTL, now, force)
    if not todo:
        return d
    bad = []
    if "ports" in todo:
        d["try_each"]["ports"] = now
        ports = d.get("ports") or {}
        pbad = []
        for pid, *_ in PORTS:
            old = ports.get(pid) or {}
            since = START if len(old) < 365 else (date.fromisoformat(max(old)) - timedelta(days=30)).isoformat()
            try:
                new = await _fetch(pid, since)
                if not new and not old:
                    raise ValueError("no rows")
                ports[pid] = {**old, **new}
            except Exception as e:  # noqa: BLE001
                pbad.append(f"{pid}: {e if str(e) else type(e).__name__}")
        if len(pbad) < len(PORTS):
            d["ports"], d["ts_each"]["ports"] = ports, now
        bad += pbad
    if "gscpi" in todo:
        d["try_each"]["gscpi"] = now
        try:
            g = parse_gscpi(await http.get(GSCPI, kind="bytes", headers={"User-Agent": "Mozilla/5.0"}, timeout=60, retries=1))
            if len(g) < 300:
                raise ValueError("GSCPI: too few months")
            d["gscpi"], d["ts_each"]["gscpi"] = g, now
        except Exception as e:  # noqa: BLE001
            bad.append(f"gscpi: {e if str(e) else type(e).__name__}")
    d["ts"] = bundle_ts(d, keys)
    if bad:
        log.warning("chokepoints: %s", "; ".join(bad))
        HEALTH.fail("chokepoints", "; ".join(bad), every=TTL)
    else:
        HEALTH.ok("chokepoints", len(d.get("ports") or {}), every=TTL)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d), encoding="utf-8")
    os.replace(tmp, FILE)
    return d


def gscpi_view(g: Dict[str, float]) -> Optional[Dict]:
    """Latest GSCPI, its rank since 1998, the peak and the change over 3 months."""
    if not g or len(g) < 60:
        return None
    s = pd.Series(g).sort_index()
    cur, m = float(s.iloc[-1]), s.index[-1]
    pk = s.idxmax()
    ago = s.iloc[-4] if len(s) > 4 else None
    st = "red" if cur >= 2 else "yellow" if cur >= 1 else "green"
    return {"month": m, "v": cur, "pct": float(((s < cur).mean() + (s == cur).mean() / 2) * 100), "peak": float(s[pk]), "peak_m": pk,
            "chg3": cur - float(ago) if ago is not None else None, "st": st, "start": s.index[0][:4]}


def _series(rows: Dict[str, List[int]], k: int = 0) -> pd.Series:
    if not rows:
        return pd.Series(dtype=float)
    s = pd.Series({pd.Timestamp(t): float(v[k]) for t, v in rows.items()}).sort_index()
    return s.asfreq("D")                         # gaps stay NaN (not zero ships)


def _low_since(m7: pd.Series, line: float, gap: int = 14) -> Optional[str]:
    """Start of the current stretch below `line`; breaks shorter than `gap` days do not end the stretch."""
    if not len(m7) or m7.iloc[-1] >= line:
        return None
    start, run = m7.index[-1], 0
    for t, v in zip(reversed(m7.index), reversed(m7.values)):
        if v < line:
            start, run = t, 0
        else:
            run += 1
            if run >= gap:
                break
    return start.strftime("%Y-%m-%d")


def one(rows: Dict[str, List[int]]) -> Optional[Dict]:
    s = _series(rows)
    if s.dropna().shape[0] < 400:
        return None
    m7 = s.rolling(7, min_periods=5).mean().dropna()
    last_day = m7.index[-1]
    cur = float(m7.iloc[-1])
    yago = m7[m7.index <= last_day - pd.Timedelta(days=364)]
    yoy = float(yago.iloc[-1]) if len(yago) and (last_day - pd.Timedelta(days=364) - yago.index[-1]).days <= 7 else None
    norm = m7[m7.index <= last_day - pd.Timedelta(days=365)]
    base = float(norm.median()) if len(norm) >= 365 else None     # 平常水準：一年前以前所有 7 天平均的中位數
    ratio = cur / base if base else None
    pct = float(((m7 < cur).mean() + (m7 == cur).mean() / 2) * 100)   # mid-rank, so ties do not read as the bottom
    tk = _series(rows, 1).rolling(7, min_periods=5).mean().dropna()
    tk_cur = float(tk.iloc[-1]) if len(tk) else None
    tk_n = tk[tk.index <= last_day - pd.Timedelta(days=365)]
    tk_base = float(tk_n.median()) if len(tk_n) >= 365 else None
    if ratio is not None and ratio < RED_RATIO:      # a long closure fills the low end of the history, so rank alone is not used for red
        st = "red"
    elif (ratio is not None and ratio < YEL_RATIO) or pct <= YEL_PCT:
        st = "yellow"
    else:
        st = "green"
    since = _low_since(m7, base * YEL_RATIO) if base and st != "green" else None
    wk = m7.resample("W").last().dropna()
    return {"date": last_day.strftime("%Y-%m-%d"), "cur": cur, "base": base, "yoy": yoy, "ratio": ratio, "pct": pct, "st": st,
            "tk": tk_cur, "tk_base": tk_base, "since": since, "weekly": wk[wk.index >= last_day - pd.Timedelta(days=730)]}


def view(d: Optional[Dict] = None) -> Optional[Dict]:
    d = load() if d is None else d
    ports = d.get("ports") or {}
    rows = []
    for pid, zh, en, what, first in PORTS:
        r = one(ports.get(pid) or {})
        if r:
            rows.append({"id": pid, "zh": zh, "en": en, "what": what, "first": first, **r})
    if not rows:
        return None
    by = {r["id"]: r for r in rows}
    detour = None
    bm, cape = by.get("chokepoint4"), by.get("chokepoint7")
    if bm and cape and bm["ratio"] is not None and cape["ratio"] is not None:
        detour = {"bm": bm["ratio"], "cape": cape["ratio"], "on": bm["ratio"] < YEL_RATIO and cape["ratio"] > 1.1}
    return {"rows": rows, "detour": detour, "ts": d.get("ts"), "date": max(r["date"] for r in rows),
            "gscpi": gscpi_view(d.get("gscpi") or {})}
