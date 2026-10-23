"""產業簡報的公司層級體檢：每個產業權重最大的幾家公司，好在哪、未來往哪走、自身財務風險、大環境拖累時會被套多深多久。

For each leader (largest SPDR weights):
  * 好在哪 — revenue growth, operating margin against the sector median and its change from a year ago, capex covered
    by operating cash flow, this season's EPS against the estimate;
  * 未來 — the consensus EPS revision for its next report (daily snapshots), capex growth (building capacity or not),
    construction in progress, the next report date;
  * 自身風險 — the six SEC-filing strain rules (fundamentals.RULES), debt growth, interest burden, distress-radar flags;
  * 大環境拖累 — beta to the S&P 500 and to the 10-year yield (2 years, weekly), and what actually happened in the two
    big shocks since 2007: the peak-to-trough fall and how long it took to get back to the old high (2008–09 crisis,
    2022 rate shock), plus the deepest fall since 2007 and where the price stands against its own high today.
Rules on public data; the history shows what happened, not what will happen."""
from __future__ import annotations

import json
from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import DATA_DIR

SHOCKS = (("2008 金融海嘯", "2007-07-01", "2008-08-31", "2009-12-31"),
          ("2022 升息衝擊", "2021-07-01", "2022-03-31", "2022-12-31"))


def _load(name: str) -> Dict:
    try:
        f = DATA_DIR / name
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def shock(s: pd.Series, peak_from: str, peak_to: str, trough_to: str) -> Optional[Dict]:
    """Peak in [peak_from, peak_to], trough after it up to trough_to, then the first close back at the peak."""
    s = s.dropna()
    if not isinstance(s.index, pd.DatetimeIndex) or not len(s):
        return None
    pk = s[(s.index >= peak_from) & (s.index <= peak_to)]
    if len(pk) < 20 or s.index[0] > pd.Timestamp(peak_from) + pd.Timedelta(days=30):
        return None
    pv = float(pk.max())
    pdt = pk[pk >= pv].index[-1]                       # last close at the peak: the fall starts there
    tr = s[(s.index > pdt) & (s.index <= trough_to)]
    if not len(tr):
        return None
    tdt, tv = tr.idxmin(), float(tr.min())
    back = s[(s.index > tdt) & (s >= pv)]
    rec = back.index[0] if len(back) else None
    return {"dd": (tv / pv - 1) * 100, "peak": pdt.strftime("%Y-%m"), "trough": tdt.strftime("%Y-%m"),
            "months": round((rec - pdt).days / 30.4) if rec is not None else None,
            "under": round((s.index[-1] - pdt).days / 30.4) if rec is None else None}


def worst(s: pd.Series) -> Optional[Dict]:
    s = s.dropna()
    if len(s) < 250 or not isinstance(s.index, pd.DatetimeIndex):
        return None
    dd = s / s.cummax() - 1
    t = dd.idxmin()
    pk = s[:t].idxmax()
    back = s[(s.index > t) & (s >= s[pk])]
    rec = back.index[0] if len(back) else None
    return {"dd": float(dd.min()) * 100, "peak": pk.strftime("%Y-%m"), "months": round((rec - pk).days / 30.4) if rec is not None else None,
            "now": float(s.iloc[-1] / s.max() - 1) * 100}


def sens(s: pd.Series, spy: pd.Series, dgs10: pd.Series, weeks: int = 104) -> Dict:
    w = pd.concat({"s": s, "m": spy}, axis=1).dropna().resample("W-FRI").last().pct_change().dropna().iloc[-weeks:]
    out: Dict = {}
    if len(w) < 52:
        return out
    out["beta"] = float(np.cov(w["s"], w["m"])[0, 1] / np.var(w["m"], ddof=1))
    if len(dgs10):
        dy = dgs10.resample("W-FRI").last().diff().reindex(w.index)
        j = pd.concat({"r": w["s"], "dy": dy}, axis=1).dropna()
        if len(j) >= 52 and j["dy"].var() > 0:
            out["rate"] = float(np.cov(j["r"], j["dy"])[0, 1] / np.var(j["dy"], ddof=1)) * 100      # % per +1 pp
    return out


def company(sym: str, name: str, rec: Dict, med_margin: Optional[float], season: Optional[Dict], revs: List, info: Dict,
            distress: Dict, px: pd.Series, spy: pd.Series, dgs10: pd.Series, nxt: Optional[str]) -> Dict:
    from ..data import fundamentals as FU
    p, m = (rec or {}).get("p") or {}, (rec or {}).get("m") or {}

    def g(k, f="v"):
        return (p.get(k) or {}).get(f)
    good, fut, own, env = [], [], [], []
    # ---- 好在哪
    rg = m.get("rev_growth")
    if rg is not None:
        if rg >= 10:
            good.append(f"營收年增 {rg:+.0f}%")
        elif rg < 0:
            own.append(f"營收衰退 {rg:+.0f}%")
    mg = g("ebit") / g("rev") * 100 if g("rev") and g("ebit") is not None and g("rev") > 0 else None
    mg0 = g("ebit", "prev") / g("rev", "prev") * 100 if g("rev", "prev") and g("ebit", "prev") is not None and g("rev", "prev") > 0 else None
    if mg is not None and med_margin is not None and mg >= med_margin + 5:
        good.append(f"營業利益率 {mg:.0f}%（產業中位數 {med_margin:.0f}%）")
    if mg is not None and mg0 is not None:
        if mg - mg0 >= 1:
            good.append(f"利潤率比一年前 {mg - mg0:+.1f} 個百分點")
        elif mg - mg0 <= -2:
            own.append(f"利潤率比一年前 {mg - mg0:+.1f} 個百分點")
    co = m.get("capex_ocf")
    if co is not None and co < 0.5 and (g("ocf") or 0) > 0:
        good.append("營運現金流足以支應投資")
    if season and season.get("surprise") is not None:
        sp = float(season["surprise"])
        (good if sp > 0 else own).append(f"本季 EPS {'優於' if sp > 0 else '低於'}預估 {sp:+.1f}%")
    # ---- 未來
    if revs and len(revs) >= 2 and revs[0][1]:
        ch = (revs[-1][1] - revs[0][1]) / abs(revs[0][1]) * 100
        days = (date.fromisoformat(revs[-1][0]) - date.fromisoformat(revs[0][0])).days
        if days >= 3:
            fut.append(f"下次財報 EPS 預估 {days} 天內" + ("持平" if abs(ch) <= 0.5 else f"{'上修' if ch > 0 else '下修'} {ch:+.1f}%"))
    if g("capex") is not None and g("capex", "prev"):
        cg = (g("capex") / g("capex", "prev") - 1) * 100 if g("capex", "prev") > 0 else None
        if cg is not None and cg >= 20:
            fut.append(f"資本支出年增 {cg:+.0f}%（擴產中，未來營收要跟上）")
        elif cg is not None and cg <= -15:
            fut.append(f"資本支出年減 {cg:.0f}%（投資放緩）")
    if m.get("cip_share") is not None and m["cip_share"] >= 20:
        fut.append(f"在建工程佔固定資產 {m['cip_share']:.0f}%（已投入、尚未產生收入）")
    up = info.get("up")
    if up is not None and info.get("n"):
        fut.append(f"分析師目標價中位數比現價 {up:+.0f}%（{int(info['n'])} 位）")
    if nxt:
        fut.append(f"下次財報 {nxt[5:]}")
    # ---- 自身風險
    lab = {k: zh.split("：")[0] for k, zh, _en, _f in FU.RULES}
    fl = FU.flags(m) if m else []
    if fl:
        own.append("財報壓力：" + "、".join(lab[k] for k in fl))
    if m.get("debt_growth") is not None and m["debt_growth"] >= 15 and "debt" not in fl:
        own.append(f"負債年增 {m['debt_growth']:+.0f}%")
    if m.get("int_burden") is not None and m["int_burden"] >= 15 and "int" not in fl:
        own.append(f"利息佔營業利益 {m['int_burden']:.0f}%")
    # SEC 8-K events from the distress radar, last 12 months; a listing transfer (3.01 watch) is usually routine
    cut = (pd.Timestamp.today() - pd.DateOffset(years=1)).strftime("%Y-%m-%d")
    dfl = [x for x in (distress or {}).get("flags") or [] if isinstance(x, dict) and str(x.get("date", "")) >= cut
           and (x.get("level") == "alert" or x.get("code") != "3.01")]
    if dfl:
        own.append("SEC 重大事件：" + "、".join(f"{x.get('zh', x.get('code'))}（{str(x.get('date'))[:7]}）" for x in dfl[:2]))
    # ---- 大環境拖累
    sv = sens(px, spy, dgs10) if len(px.dropna()) else {}
    if sv.get("beta") is not None:
        env.append(f"β {sv['beta']:.2f}：大盤跌 20% 時，以過去兩年連動推估約 {sv['beta'] * -20:+.0f}%")
    if sv.get("rate") is not None and abs(sv["rate"] * 0.5) >= 2:
        env.append(f"10 年期殖利率升 0.5 個百分點，過去兩年平均 {sv['rate'] * 0.5:+.1f}%")
    shocks = []
    for nm, a, b, c in SHOCKS:
        r = shock(px, a, b, c)
        if r:
            shocks.append({"name": nm, **r})
            if r["dd"] > -10:
                env.append(f"{nm}：最多只跌 {r['dd']:.0f}%，幾乎沒受影響")
            else:
                env.append(f"{nm}：最深 {r['dd']:.0f}%，" + (f"{r['months']} 個月才回到前高" if r["months"] is not None else f"至今仍未回到 {r['peak']} 的高點"))
    w = worst(px)
    if w and w["now"] < -15:
        env.append(f"目前比歷史高點低 {-w['now']:.0f}%")
    # ---- summaries
    trap = None
    if shocks:
        mm = [x["months"] if x["months"] is not None else 999 for x in shocks]
        trap = max(mm)
    env_lvl = ("高" if (sv.get("beta") or 1) >= 1.3 or (trap or 0) >= 36 else "低" if (sv.get("beta") or 1) <= 0.8 and (trap or 0) <= 12 else "中")
    body = "強" if len(good) >= 3 and len([x for x in own if not x.startswith("本季")]) <= 1 else "弱" if len(own) >= 3 and len(good) <= 1 else "中"
    return {"sym": sym, "name": name, "good": good, "future": fut, "own": own, "env": env, "beta": sv.get("beta"),
            "rate": sv.get("rate"), "shocks": shocks, "worst": w, "body": body, "env_lvl": env_lvl, "trap": trap, "margin": mg}


def build(sector_members: List, fcache: Dict, season_rows: List[Dict], snap: Dict, ahead: List[Dict], px: pd.DataFrame,
          spy: pd.Series, dgs10: pd.Series, n: int = 8) -> List[Dict]:
    info = _load("sinfo_yf.json")
    dist = _load("earn_distress.json")
    lead = sorted(sector_members or [], key=lambda x: -x[1])[:n]
    margins = []
    for t, *_ in sorted(sector_members or [], key=lambda x: -x[1])[:15]:
        p = ((fcache.get(t) or fcache.get(t.replace(".", "-")) or {}).get("p") or {})
        r, e = (p.get("rev") or {}).get("v"), (p.get("ebit") or {}).get("v")
        if r and e is not None and r > 0:
            margins.append(e / r * 100)
    med = float(np.median(margins)) if len(margins) >= 3 else None
    seas = {r["sym"]: r for r in season_rows}
    out = []
    for row in lead:
        t, name = row[0], (row[2] if len(row) > 2 else row[0])
        y = t.replace(".", "-")
        alt = {t, y, t.replace("-", ".")}
        revs = next((v for k, v in sorted(snap.items()) if k.split("|")[0] in alt), [])
        nx = next((r["date"] for r in ahead if r["sym"] in alt), None)
        s = px[y] if y in px.columns else pd.Series(dtype=float)
        rec = next((fcache[k] for k in alt if k in fcache), {})
        out.append(company(t, name, rec, med, next((seas[k] for k in alt if k in seas), None), revs,
                           next((info[k] for k in alt if k in info), {}), next((dist[k] for k in alt if k in dist), {}),
                           s, spy, dgs10, nx))
    return out
