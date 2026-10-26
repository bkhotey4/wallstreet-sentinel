"""美股全市場財報判讀: one plain-language reading per US company, worked backwards from its latest SEC quarter — is growth
speeding up or slowing, is it bought with lower prices (gross margin) or does it carry operating leverage (operating
margin), are receivables or inventory growing faster than revenue (quality of the revenue), is the growth bought through
acquisitions (goodwill), how capital-hungry it is (capex ÷ revenue, fiscal year) and how long the cash lasts.
Every tag is a rule on the numbers; a description of the filing, not a forecast or advice."""
from __future__ import annotations

from typing import Dict, List, Optional

from ..data import earnings_data as ED

AR_TAG, INV_TAG = "AccountsReceivableNetCurrent", "InventoryNet"


def _pct(a, b) -> Optional[float]:
    return (a / b - 1) * 100 if a is not None and b not in (None, 0) and b > 0 else None


def extras(fr: "ED.FrameReader", cik: str, qs: List[str], per: str, years: List[str]) -> Dict:
    """Year-on-year margin changes for the latest quarter, receivables / inventory growth, capex ÷ revenue (fiscal year)."""
    out: Dict = {}
    pk = "CY" + per                                                     # "2026Q3" → "CY2026Q3"
    if pk not in qs:
        return out
    i = qs.index(pk)
    if i + 4 >= len(qs):
        return out
    now, ago = qs[i], qs[i + 4]
    rev, rev0 = fr.val("rev", cik, now), fr.val("rev", cik, ago)
    for k, key in (("gp", "gm_chg"), ("op", "om_chg")):
        a, b = fr.val(k, cik, now), fr.val(k, cik, ago)
        if a is not None and b is not None and rev and rev0 and (k != "gp" or (a < rev * 0.99 and b < rev0 * 0.99)):
            out[key] = (a / rev - b / rev0) * 100
    out["rev_q_yoy"] = _pct(rev, rev0)
    for tag, key in ((AR_TAG, "ar_yoy"), (INV_TAG, "inv_yoy")):
        a, b = fr._raw(tag, cik, now + "I"), fr._raw(tag, cik, ago + "I")
        if a is not None and b is not None and b > 0 and rev and a > 0.02 * rev:        # ignore balances too small to matter
            out[key] = _pct(a, b)
    cx_tag, rv_tag = ED.FRAME_TAGS["capex"][0], fr.best("rev", cik)
    for y in years:
        cx, rv = fr._raw(cx_tag, cik, y), (fr._raw(rv_tag, cik, y) if rv_tag else None)
        if cx is not None and rv:
            out["capex_pct"], out["capex_y"] = cx / rv * 100, y[2:]
            break
    return out


def read(r: Dict) -> Dict:
    """{"tags": [...], "read": "…"} — at most four sentences, most informative first."""
    tags, s = [], []
    g, acc = r.get("q_yoy"), r.get("accel")
    if g is not None:
        if g >= 25 and (acc or 0) >= 5:
            tags.append("加速成長")
            s.append(f"營收年增 {g:.0f}%，比上一季再快 {acc:.0f} 個百分點：需求在加速。")
        elif g >= 15 and (acc or 0) <= -10:
            tags.append("成長放緩")
            s.append(f"營收年增 {g:.0f}%，但比上一季慢了 {abs(acc):.0f} 個百分點：成長還在，速度在降。")
        elif g < 0 and (acc or 0) >= 5:
            tags.append("衰退收斂")
            s.append(f"營收年減 {abs(g):.0f}%，但比上一季的衰退小：最差的時候可能過了。")
        elif g < -5:
            tags.append("營收衰退")
            s.append(f"營收年減 {abs(g):.0f}%。")
        elif abs(g) < 1:
            s.append("營收和一年前差不多。")
        else:
            s.append(f"營收年{'增' if g > 0 else '減'} {abs(g):.0f}%。")
    gm_c, om_c = r.get("gm_chg"), r.get("om_chg")
    if g is not None and g > 10 and gm_c is not None and gm_c <= -2:
        tags.append("以價換量")
        s.append(f"毛利率比一年前低 {abs(gm_c):.1f} 個百分點：成長靠降價或賣較低毛利的產品換來。")
    elif gm_c is not None and gm_c >= 2:
        tags.append("毛利率提升")
        s.append(f"毛利率比一年前高 {gm_c:.1f} 個百分點：定價力或產品組合在變好。")
    if g is not None and g > 0 and om_c is not None and om_c >= 3:
        tags.append("營運槓桿")
        s.append(f"營益率比一年前高 {om_c:.1f} 個百分點：營收成長、費用沒有跟著漲，多賺的錢大多變成利潤。")
    elif g is not None and g > 0 and om_c is not None and om_c <= -3:
        tags.append("越長越燒錢")
        s.append(f"營收在長，營益率卻比一年前低 {abs(om_c):.1f} 個百分點：擴張的成本吃掉了成長。")
    ar, inv, rg = r.get("ar_yoy"), r.get("inv_yoy"), r.get("rev_q_yoy") if r.get("rev_q_yoy") is not None else g
    if ar is not None and rg is not None and ar >= 25 and ar - rg >= 20:
        tags.append("應收帳款膨脹")
        s.append(f"應收帳款年增 {ar:.0f}%，比營收（{rg:.0f}%）快很多：營收收到現金的速度變慢，要留意是否放寬收款條件。")
    if inv is not None and rg is not None and inv >= 30 and inv - rg >= 25:
        tags.append("庫存堆積")
        s.append(f"庫存年增 {inv:.0f}%，比營收（{rg:.0f}%）快很多：貨賣得比進得慢，之後可能要降價出清。")
    if r.get("ma"):
        tags.append("含併購")
        s.append("商譽一年內大增：成長有一部分是買公司買來的，不全是本業自己長出來的。")
    cx = r.get("capex_pct")
    if cx is not None and cx >= 30:
        tags.append("重資本")
        s.append(f"{r.get('capex_y', '')} 年度資本支出是營收的 {cx:.0f}%：每賺 1 元營收就花 {cx / 100:.2f} 元蓋設備，成長要靠持續投資，現金流壓力大。")
    run, burn = r.get("runway"), r.get("burn")
    if run is not None and burn and run < 2:
        tags.append("現金吃緊")
        s.append(f"照目前燒錢速度，現金約 {run:.1f} 年用完：可能需要增資或借錢（股本被稀釋）。")
    om = r.get("om")
    if om is not None and om < 0 and (r.get("r40") or 0) >= 40:
        tags.append("虧損但成長夠快")
        s.append(f"還在虧損（營益率 {om:.0f}%），但成長加營益率合計 {r['r40']:.0f}，高於成長股常用的 40 分門檻。")
    elif om is not None and om >= 30:
        tags.append("高利潤")
    if not s:
        return {"tags": "", "read": ""}
    return {"tags": "・".join(tags[:4]), "read": "".join(s[:4])}


def attach(ed, rows: List[Dict], tmap: Dict[str, Dict], today=None) -> List[Dict]:
    """Adds the extra figures and the reading to growth.us_rows() output (SEC-sourced rows only)."""
    from ..data.econcal import us_today
    today = today or us_today()
    qs = ED.cy_quarters(today, 10)
    fr = ED.FrameReader(ed.frames or {}, qs)
    years = [f"CY{y}" for y in range(today.year, today.year - 3, -1)]
    for r in rows:
        if r.get("src") != "SEC" or not r.get("per", "").count("Q"):
            r.update(read(r))
            continue
        cik = str((tmap.get(r["sym"]) or tmap.get(r["sym"].replace("-", ".")) or {}).get("cik") or "")
        if cik:
            try:
                r.update(extras(fr, cik, qs, r["per"], years))
            except Exception:  # noqa: BLE001  (one odd filer never stops the table)
                pass
        r.update(read(r))
    return rows


def add_missing(ed, rows: List[Dict], items: List[Dict], tmap: Dict[str, Dict], today=None) -> List[Dict]:
    """Companies the growth table skips (fewer than 4 quarters on file — e.g. a recent IPO such as SPCX — or a gap in
    the quarters) still get a reading from their latest quarter vs the same quarter a year earlier.  Added unranked."""
    from ..data.econcal import us_today
    today = today or us_today()
    qs = ED.cy_quarters(today, 10)
    fr = ED.FrameReader(ed.frames or {}, qs)
    years = [f"CY{y}" for y in range(today.year, today.year - 3, -1)]
    seen = {str((tmap.get(r["sym"]) or tmap.get(r["sym"].replace("-", ".")) or {}).get("cik") or "") for r in rows} - {""}
    for it in sorted(items, key=lambda x: -(x.get("mcap") or 0)):
        cik = str((tmap.get(it["sym"]) or tmap.get(it["sym"].replace("-", ".")) or {}).get("cik") or "")
        if not cik or cik in seen or (it.get("mcap") or 0) < 1e9:
            continue
        seen.add(cik)
        i = next((j for j, p in enumerate(qs) if fr.val("rev", cik, p) is not None), None)
        if i is None or i + 4 >= len(qs):
            continue
        now, ago = fr.val("rev", cik, qs[i]), fr.val("rev", cik, qs[i + 4])
        if not now or not ago or now <= 0 or ago <= 0:
            continue
        g = (now / ago - 1) * 100
        p1, a1 = (fr.val("rev", cik, qs[i + 1]), fr.val("rev", cik, qs[i + 5])) if i + 5 < len(qs) else (None, None)
        g1 = (p1 / a1 - 1) * 100 if p1 and a1 and a1 > 0 else None
        r = {"sym": it["sym"], "name": it.get("name", ""), "ind": it.get("ind", ""), "sub": it.get("sub", ""), "mcap": it.get("mcap"),
             "per": qs[i][2:6] + "Q" + qs[i][-1], "ttm": None, "g": None, "q_yoy": g, "accel": (g - g1) if g1 is not None else None,
             "src": "SEC", "partial": True}
        try:
            r.update(extras(fr, cik, qs, r["per"], years))
        except Exception:  # noqa: BLE001
            pass
        r.update(read(r))
        if r["read"]:
            rows.append(r)
    return rows
