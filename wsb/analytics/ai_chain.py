"""AI 產業鏈連動：人類只盯著主角（輝達、台積電），泡沫洩氣時被拖下水的常是周邊的「AI 受惠股」。兩個角度，都用數據：

1. 歷史（Ken French 49 產業，1970 年起）：半導體產業（Chips）每一次從高點跌 ≥35% 的期間，其他產業同一段時間的報酬——
   誰跟著崩、誰撐住。每段期間都是同一個起訖月，所以比的是「同一場風暴裡誰比較慘」。
2. 現在（本站追蹤池，約 2 年日資料）：AI 產業鏈各環節對費半的「下跌連動度」——費半單日跌 ≥2% 的那些天，平均跟著跌幾 %
   （下行貝他，>1＝跌得比費半兇）；以及 1 年漲幅、離高點多遠，看 AI 題材被定價到什麼程度。
   「如果費半再跌 20%」只用下行貝他做線性換算，是粗估，不是預測。"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

CHAIN = (("核心晶片", "Core chips", ("NVDA", "AVGO", "AMD", "TSM", "2330.TW")),
         ("半導體設備", "Equipment", ("ASML", "AMAT", "LRCX", "KLAC")),
         ("記憶體", "Memory", ("MU",)),
         ("雲端巨頭", "Hyperscalers", ("MSFT", "GOOGL", "AMZN", "META")),
         ("甲骨文與新雲端", "Oracle & neoclouds", ("ORCL", "CRWV", "NBIS")),
         ("伺服器與組裝", "Servers & ODMs", ("SMCI", "DELL", "2317.TW", "2382.TW", "3231.TW", "2376.TW")),
         ("網通與散熱", "Networking & cooling", ("ANET", "VRT", "3017.TW", "2308.TW")),
         ("電力與電網", "Power & grid", ("VST", "CEG", "GEV", "ETN")),
         ("公用事業（對照）", "Utilities (control)", ("XLU",)))
FF_ZH = {"Chips": "半導體", "Hardw": "電腦硬體", "Softw": "軟體", "Telcm": "電信", "LabEq": "量測設備", "ElcEq": "電機設備", "BusSv": "商業服務",
         "Util": "公用事業", "Gold": "黃金", "Smoke": "菸草", "Food ": "食品", "Food": "食品", "Hshld": "家用品", "Drugs": "製藥", "Hlth": "醫療服務",
         "Beer": "啤酒", "Soda": "飲料", "Oil": "石油", "Coal": "煤礦", "Banks": "銀行", "Insur": "保險", "RlEst": "不動產", "Fin": "金融",
         "Rtail": "零售", "Whlsl": "批發", "Meals": "餐飲", "Trans": "運輸", "Aero": "航太", "Guns": "國防", "Mach": "機械", "Autos": "汽車",
         "Steel": "鋼鐵", "Chems": "化工", "Cnstr": "營建", "BldMt": "建材", "Paper": "紙業", "Boxes": "包裝", "Rubbr": "橡膠塑膠", "Txtls": "紡織",
         "Clths": "服飾", "Toys": "玩具", "Fun": "娛樂", "Books": "出版", "PerSv": "個人服務", "MedEq": "醫療器材", "Agric": "農業", "Ships": "造船",
         "Mines": "礦業", "FabPr": "金屬製品", "Other": "其他", "Agric ": "農業"}


def chip_crashes(ff: Dict[str, Dict[str, float]], dd: float = -0.35, start: str = "1970") -> List[Dict]:
    """Peak→trough windows where the Chips industry fell ≥35 % (monthly), non-overlapping."""
    c = pd.Series(ff.get("Chips") or {})
    if len(c) < 200:
        return []
    c.index = pd.to_datetime(c.index + "-01")
    c = c.sort_index()
    px = (1 + c).cumprod()
    out, i = [], 0
    vals, idx = px.values, px.index
    peak_i = 0
    in_dd = False
    for i in range(1, len(vals)):
        if vals[i] > vals[peak_i] and not in_dd:
            peak_i = i
        draw = vals[i] / vals[peak_i] - 1
        if draw <= dd and not in_dd:
            in_dd = True
        if in_dd:
            seg = vals[peak_i:i + 1]
            tr = peak_i + int(np.argmin(seg))
            if vals[i] >= vals[tr] * 1.5 or i == len(vals) - 1:      # recovered 50 % off the low → close the episode
                if idx[peak_i] >= pd.Timestamp(f"{start}-01-01"):
                    out.append({"peak": idx[peak_i].strftime("%Y-%m"), "trough": idx[tr].strftime("%Y-%m"), "fall": float(vals[tr] / vals[peak_i] - 1)})
                in_dd, peak_i = False, i
    return out


def contagion(ff: Dict[str, Dict[str, float]]) -> Optional[Dict]:
    eps = chip_crashes(ff)
    if len(eps) < 3:
        return None
    rows = []
    mkt = {}                                              # equal-weight average of all industries over each window = "the market"
    allr = pd.DataFrame({k: pd.Series(v) for k, v in ff.items()})
    allr.index = pd.to_datetime(allr.index + "-01")
    allr = allr.sort_index()
    for e in eps:
        w = allr[(allr.index > pd.Timestamp(e["peak"] + "-01")) & (allr.index <= pd.Timestamp(e["trough"] + "-01"))]
        mkt[e["peak"]] = float(((1 + w).prod() - 1).mean())
    for ind, rets in ff.items():
        r = pd.Series(rets)
        r.index = pd.to_datetime(r.index + "-01")
        r = r.sort_index()
        res, rel = [], []
        for e in eps:
            w = r[(r.index > pd.Timestamp(e["peak"] + "-01")) & (r.index <= pd.Timestamp(e["trough"] + "-01"))]
            if len(w) >= 2:
                res.append(float((1 + w).prod() - 1))
                rel.append(res[-1] - mkt[e["peak"]])
        if len(res) >= len(eps) - 1:
            rows.append({"ind": ind, "zh": FF_ZH.get(ind, FF_ZH.get(ind.strip(), ind)), "med": float(np.median(res)) * 100,
                         "neg": int(sum(x < 0 for x in res)), "n": len(res),
                         "rel": float(np.median(rel)) * 100, "worse": int(sum(x < 0 for x in rel))})
    rows.sort(key=lambda x: x["rel"])
    return {"episodes": eps, "rows": rows, "mkt": {k: v * 100 for k, v in mkt.items()}}


def chain_now(eng) -> Optional[Dict]:
    sp = getattr(eng, "stockprices", None)
    close = getattr(sp, "close", None) if sp is not None else None
    try:
        sox = eng.market.series("^SOX").dropna()
    except Exception:  # noqa: BLE001
        sox = pd.Series(dtype=float)
    if len(sox) < 300:
        return None

    def ser(t):
        if close is not None and t in close.columns and close[t].notna().sum() > 200:
            return close[t].dropna()
        try:
            s = eng.market.series(t).dropna()
            return s if len(s) > 200 else None
        except Exception:  # noqa: BLE001
            return None
    rs = sox.pct_change()
    groups, missing = [], []
    for zh, en, syms in CHAIN:
        mem = []
        for t in syms:
            s = ser(t)
            if s is None:
                missing.append(t)
                continue
            ra = s.pct_change()
            if str(t).endswith((".TW", ".TWO")):               # Taipei closes before New York opens → it answers a SOX move the next session
                tw = ra.dropna()
                pos = tw.index.searchsorted(rs.index, side="right")
                ok = pos < len(tw)
                ra = pd.Series(np.where(ok, tw.values[np.minimum(pos, len(tw) - 1)], np.nan), index=rs.index)
            j = pd.concat({"a": ra, "b": rs}, axis=1).dropna().tail(504)
            down = j[j["b"] <= -0.02]
            if len(down) < 15:
                continue
            beta = float((down["a"] * down["b"]).sum() / (down["b"] ** 2).sum())      # regression through 0 on SOX down days
            one = float(s.iloc[-1] / s.iloc[-253] - 1) * 100 if len(s) > 253 else None
            mem.append({"sym": t, "beta": beta, "avg_down": float(down["a"].mean()) * 100, "ret1y": one,
                        "off": float(s.iloc[-1] / s.tail(252).max() - 1) * 100, "n_down": int(len(down))})
        if mem:
            groups.append({"zh": zh, "en": en, "members": mem, "beta": float(np.mean([m["beta"] for m in mem])),
                           "ret1y": float(np.nanmean([m["ret1y"] for m in mem if m["ret1y"] is not None])) if any(m["ret1y"] is not None for m in mem) else None,
                           "off": float(np.mean([m["off"] for m in mem])), "if20": float(np.mean([m["beta"] for m in mem])) * -20})
    if not groups:
        return None
    sox_down = int((rs.tail(504) <= -0.02).sum())
    return {"groups": sorted(groups, key=lambda g: -g["beta"]), "missing": missing, "sox_down_days": sox_down,
            "sox_off": float(sox.iloc[-1] / sox.tail(252).max() - 1) * 100}


def build(eng) -> Dict:
    out: Dict = {}
    try:
        from . import bubble as BB
        ff = BB.load().get("ff") or {}
        out["history"] = contagion(ff) if ff else None
    except Exception:  # noqa: BLE001
        out["history"] = None
    out["now"] = chain_now(eng)
    return out
