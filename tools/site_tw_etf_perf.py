"""台灣 ETF page, part 2 — every listed ETF on its own history: total return with dividends by kind (vs 0050), whether
payouts came out of capital, bond ETFs' sensitivity to the US 10-year yield, leveraged / inverse decay, and active
ETFs since launch.  Data and rules only (wsb.analytics.tw_etf_perf); not advice."""
from __future__ import annotations

from tools.sitekit import T, card, esc, num
from tools.site_tw_etf import KIND_EN, KIND_ORDER, _how, _lead, _r, _yi


def _p(eng):
    p = getattr(eng, "_tw_etf_perf", None)
    if p is None:
        from wsb.analytics import tw_etf_perf as P
        try:
            p = P.build()
        except Exception:  # noqa: BLE001
            p = {"available": False}
        eng._tw_etf_perf = p
    return p


def _pc(x, d=1) -> str:
    return "—" if x is None else _yi(x, d, True) + "%"


def _nm(x, n=12) -> str:
    return f'<b>{esc(x["code"])}</b> {esc(x["name"][:n])}'


def _ref(k) -> str:
    from wsb.analytics import tw_etf_perf as P
    return P.REF_ZH.get(k, k)


# ------------------------------------------------------------------ 1. 全部 ETF 含息報酬
def sec_etf_rank(eng) -> str:
    p = _p(eng)
    if not p.get("available"):
        return ""
    b, k = p.get("base") or {}, p.get("kinds") or {}
    n1 = sum(g["n1"] for g in k.values())
    beat = sum(g["beat1"] for g in k.values())
    meds = sorted(((g["med1"], n) for n, g in k.items() if g.get("med1") is not None and g["n1"] >= 3), reverse=True)
    lead = (f"一句話看懂：{p['n_px']} 檔有價格資料的 ETF 中，{n1} 檔滿一年；近 1 年含息報酬贏過 0050（{b.get('tr1y', 0):+.0f}%）的有 {beat} 檔"
            + (f"；各類型中位數最高的是{meds[0][1]}（{meds[0][0]:+.0f}%），最低的是{meds[-1][1]}（{meds[-1][0]:+.0f}%）" if len(meds) >= 2 else "")
            + "。不同類型的用途不同（債券求穩、槓桿短線），要搭配波動和最大回落一起看。")
    sr = []
    for name in KIND_ORDER:
        g = k.get(name)
        if not g:
            continue
        sr.append(f'<tr><td>{T(name, KIND_EN[name])}</td><td class="r">{g["n"]}</td><td class="r">{_pc(g.get("med1"), 0)}</td>'
                  f'<td class="r">{g["beat1"]} / {g["n1"]}</td><td class="r">{g["beat3"]} / {g["n3"]}</td></tr>')
    summ = (f'<div class="scroll"><table class="mini"><thead><tr><th>{T("類型", "Kind")}</th><th class="r">{T("檔數", "N")}</th>'
            f'<th class="r">{T("近 1 年含息中位數", "1y median")}</th><th class="r">{T("贏 0050 檔數（近 1 年）", "Beat 0050 1y")}</th>'
            f'<th class="r">{T("贏 0050 檔數（近 3 年）", "Beat 0050 3y")}</th></tr></thead><tbody>{"".join(sr)}</tbody></table></div>')
    head = "".join(f'<th class="r">{T(a, "")}</th>' for a in ("規模（億）", "近 1 年含息", "近 3 年（年化）", "近 5 年（年化）",
                                                                "年化波動", "3 年最大回落", "比 0050（近 1 年）"))
    det = []
    for name in KIND_ORDER:
        xs = [x for x in p["rows"] if x["kind"] == name]
        if not xs:
            continue
        tr = "".join(
            f'<tr><td>{_nm(x)}<div class="small muted">{T("上市 " + x["since"] if x["days"] < 365 * 5 - 10 else "", "")}</div></td>'
            f'<td class="r">{num(x.get("aum"), 0)}</td><td class="r">{_pc(x.get("tr1y"))}</td><td class="r">{_pc(x.get("tr3y"))}</td>'
            f'<td class="r">{_pc(x.get("tr5y"))}</td><td class="r">{num(x.get("vol1y"), 0)}{"%" if x.get("vol1y") is not None else ""}</td>'
            f'<td class="r">{_pc(x.get("mdd"))}</td><td class="r">{_pc(x.get("vs1y"))}</td></tr>' for x in xs)
        det.append(f'<details class="sgx"><summary>{T(name + "（" + str(len(xs)) + " 檔，依近 1 年含息排序）", KIND_EN[name])}</summary>'
                   f'<div class="scroll"><table class="mini"><thead><tr><th>ETF</th>{head}</tr></thead><tbody>{tr}</tbody></table></div></details>')
    how = ("含息報酬＝價格變化加上配息（配息在除息日再投入），是持有人實際拿到的報酬。3 年、5 年用年化（平均每年），方便和 1 年比較；"
           "上市不滿該期間的顯示「—」。年化波動＝過去一年每天漲跌的幅度換算成一年，越大代表越顛簸；3 年最大回落＝過去 3 年從高點到低點最多跌多少。"
           "比 0050＝近 1 年含息報酬減去 0050 的含息報酬（正數＝贏）。台股這一年大漲時，0050 本身就很難贏，債券和反向 ETF 輸給 0050 是正常的。"
           "價格與配息來自 Yahoo（每天更新一次），規模來自證交所。過去的報酬不代表未來，不是投資建議。")
    body = _lead(lead) + summ + "".join(det) + _how(how)
    return card("全部台灣 ETF 含息報酬：依類型比較", "Every Taiwan ETF: total return by kind", body, "wide")


# ------------------------------------------------------------------ 2. 配息是不是吃老本
CLS_ZH = {"gain": "✅ 價格也漲：配息來自賺到的錢", "capital": "⚠️ 價格跌、含息仍賺：部分配息等於拿回本金", "short": "❌ 含息也賠：配息補不回價格跌幅"}


def sec_etf_payout(eng) -> str:
    p = _p(eng)
    if not p.get("available") or not p.get("payout"):
        return ""
    xs = p["payout"]
    n = {c: sum(1 for x in xs if x["cls"] == c) for c in CLS_ZH}
    hd = [x for x in xs if x["kind"] == "高股息"]
    hd_cap = [x for x in hd if x["cls"] != "gain"]
    bond_cap = sum(1 for x in xs if x["kind"] == "債券" and x["cls"] != "gain")
    lead = (f"一句話看懂：近一年有配息的 {len(xs)} 檔 ETF 中，{n['gain']} 檔價格也漲（配息來自賺到的錢），{n['capital']} 檔價格下跌、"
            f"部分配息等於拿回本金，{n['short']} 檔連含息都賠；高股息類 {len(hd)} 檔中 {len(hd_cap)} 檔屬於後兩種"
            + (f"；債券 ETF 有 {bond_cap} 檔價格下跌，主因是利率上升（看下面「債券 ETF 對利率有多敏感」）" if bond_cap else "") + "。")
    show = [x for x in xs if x["kind"] == "高股息" or x["yld"] >= 6 or (x["cls"] != "gain" and x["kind"] != "債券")]
    tr = "".join(
        f'<tr><td>{_nm(x)}<div class="small muted">{T(x["kind"], KIND_EN.get(x["kind"], ""))}</div></td>'
        f'<td class="r">{num(x["yld"], 1)}%</td><td>{T("近 " + str(x["yrs"]) + " 年", "")}</td>'
        f'<td class="r">{_pc(x["price"])}</td><td class="r">{num(x["paid"], 1)}%</td><td class="r">{_pc(x.get("tr"))}</td>'
        f'<td class="r">{_pc(x.get("base"))}</td><td class="small">{T(CLS_ZH[x["cls"]], "")}'
        + (f'<div class="muted">{T("配息中約 " + format(x["capital_share"], ".0f") + "% 等於本金", "")}</div>' if x["cls"] != "gain" else "")
        + '</td></tr>' for x in show)
    head = "".join(f'<th{" class=r" if i not in (2, 7) else ""}>{T(a, "")}</th>' for i, a in enumerate(
        ("ETF", "近 12 月配息率", "期間", "期間價格變化", "期間領到配息", "期間含息報酬", "0050 同期價格", "判斷")))
    tab = f'<div class="scroll"><table class="mini"><thead><tr>{head}</tr></thead><tbody>{tr}</tbody></table></div>'
    how = ("檢查方法：看過去 3 年（上市不滿 3 年的看 1 年）價格本身漲還是跌。價格漲＝配出去的錢來自賺到的收益，本金還在；"
           "價格跌但含息報酬仍為正＝配息裡有一部分其實是把本金還給你（「等於本金」的比例＝價格跌幅 ÷ 期間配息），"
           "配息率看起來高，但總資產沒有變多那麼多；連含息都是負的＝配息補不回價格跌幅。"
           "價格跌不一定是投信配太多，也可能是整個市場在跌，所以附上 0050 同期價格對照。"
           "另外配息要繳所得稅與二代健保補充保費，含息報酬還沒扣這些。列出：全部高股息類、配息率 6% 以上，以及其他非債券類中價格下跌的。"
           "這是歷史數據整理，不是投資建議。")
    return card("配息是不是在吃老本？", "Is the payout coming out of capital?", _lead(lead) + tab + _how(how, "怎麼判斷"), "wide")


# ------------------------------------------------------------------ 3. 債券 ETF 對利率的敏感度
def sec_etf_rate(eng) -> str:
    p = _p(eng)
    rs = p.get("rate") or [] if p.get("available") else []
    if not rs:
        return ""
    clear = [x for x in rs if x["clear"]]
    y0 = rs[0]
    big = sorted(clear, key=lambda x: -(x.get("aum") or 0))[:25]
    long_ = min(clear, key=lambda x: x["beta10"]) if clear else None
    head = (f"一句話看懂：{len(rs)} 檔債券 ETF 中有 {len(clear)} 檔明顯跟著美國 10 年期公債殖利率走"
            + (f"；最敏感的 {long_['code']} {long_['name'][:10]}，殖利率每上升 0.1 個百分點約 {long_['beta10']:+.1f}%" if long_ else "")
            + f"。10 年期殖利率現在 {y0['y_now']:.2f}%" + (f"，一年來 {y0['y_1y']:+.2f} 個百分點" if y0.get("y_1y") is not None else "")
            + "；殖利率下跌時債券 ETF 漲，上升時跌。")
    tr = "".join(
        f'<tr><td>{_nm(x)}</td><td class="r">{num(x.get("aum"), 0)}</td><td class="r">{_yi(x["beta10"], 2, True)}%</td>'
        f'<td class="r">{num(x["dur"], 0)} {T("年", "y")}</td><td class="r">{_yi(x["fxb"], 2, True)}%</td>'
        f'<td class="r">{num(x["r2"] * 100, 0)}%</td><td class="r">{_pc(x.get("tr1y"))}</td></tr>' for x in big)
    hd = "".join(f'<th{" class=r" if i else ""}>{T(a, "")}</th>' for i, a in enumerate(
        ("ETF", "規模（億）", "殖利率 +0.1 個百分點", "相當於存續期間", "美元兌台幣 +1%", "解釋力", "近 1 年含息")))
    tab = (f'<h3>{T("規模最大的 " + str(len(big)) + " 檔（和利率關係明顯的）", "")}</h3>'
           f'<div class="scroll"><table class="mini"><thead><tr>{hd}</tr></thead><tbody>{tr}</tbody></table></div>')
    weak = [x for x in rs if not x["clear"]]
    wl = ("、".join(f'{esc(x["code"])} {esc(x["name"][:8])}' for x in weak[:12]) + (" 等" if len(weak) > 12 else "")) if weak else ""
    wb = (f'<p class="small muted">{T(f"和美債殖利率關係不明顯的 {len(weak)} 檔：" + wl + "（多半是投資等級公司債、短天期、新興市場或非美元債，主要受信用利差或其他因素影響）。", "")}</p>'
          if weak else "")
    fx = (_r(eng) or {}).get("fx")
    fb = ""
    if fx:
        tx = (f"過去一年 00679B（元大美債 20 年）含息 {fx['etf']:+.1f}%；同期美國 20 年公債 ETF（TLT，美元計價）{fx['usd']:+.1f}%，"
              f"美元兌台幣 {fx['fx']:+.1f}%，兩者合起來約 {fx['combo']:+.1f}%。台灣掛牌的美債 ETF 同時承擔美國利率和美元匯率兩個風險："
              "美國降息時債券漲，但如果新台幣同時升值，台幣報酬會被吃掉一部分。")
        fb = (f'<h3>{T("💱 利率之外還有匯率", "Currency too")}</h3><p>{T(tx, "")}</p>'
              f'<p class="small"><a class="golink" href="#bonds" data-p="bonds">{T("看美國公債 →", "US Treasuries →")}</a></p>')
    how = ("用過去兩年每週的含息報酬（台幣），同時對「美國 10 年期公債殖利率的變化」和「美元兌台幣的變化」做迴歸，"
           "得到兩個敏感度：殖利率每上升 0.1 個百分點、美元每升值 1%，這檔 ETF 平均漲跌多少。美國的收盤在台北開盤前就知道，所以用前一天的美國數字對齊。"
           "相當於存續期間＝殖利率每變動 1 個百分點的漲跌幅（%），長天期美債約 15～20 年；數字越大，利率變動時漲跌越大。"
           "解釋力＝這兩個因素能解釋多少每週漲跌（低於 30% 或方向不對的列為「關係不明顯」）。這是過去的平均關係，利率大幅變動時不一定成立，也不是對利率的預測。")
    return card("債券 ETF 對利率有多敏感", "How bond ETFs move with US yields", _lead(head) + tab + wb + fb + _how(how, "怎麼算的"), "wide")


# ------------------------------------------------------------------ 4. 槓桿／反向 ETF 的長期耗損
def sec_etf_lev(eng) -> str:
    p = _p(eng)
    xs = [x for x in (p.get("lev") or []) if x.get("ref")] if p.get("available") else []
    if not xs:
        return ""
    one = [x for x in xs if x.get("gap1y") is not None]
    short = [x for x in one if x["gap1y"] < 0]
    worst = min(one, key=lambda x: x["gap1y"]) if one else None
    up3 = max((x for x in xs if x.get("gap3y") is not None and x["L"] > 1), key=lambda x: x["gap3y"], default=None)
    lead = (f"一句話看懂：槓桿／反向 ETF 是「每天」維持倍數，長期報酬不會剛好是指數的倍數。過去一年 {len(one)} 檔中 {len(short)} 檔比「倍數 × 指數」少"
            + (f"，差最多的是 {worst['code']} {worst['name'][:10]}（{worst['gap1y']:+.0f} 個百分點）" if worst else "")
            + (f"；但在一路上漲的行情，正 2 也可能比兩倍多（{up3['code']} 近 3 年多了 {up3['gap3y']:+.0f} 個百分點）" if up3 and up3["gap3y"] > 0 else "")
            + "。來回震盪越大，耗損越多。")
    tr = "".join(
        f'<tr><td>{_nm(x, 10)}</td><td class="small">{T(_ref(x["ref"]), "")}</td><td class="r">{x["L"]:+.0f}×</td>'
        f'<td class="r">{_pc(x.get("act1y"))}</td><td class="r">{_pc(x.get("mult1y"))}</td><td class="r"><b>{_pc(x.get("gap1y"))}</b></td>'
        f'<td class="r">{_pc(x.get("act3y"), 0)}</td><td class="r">{_pc(x.get("mult3y"), 0)}</td><td class="r">{_pc(x.get("gap3y"), 0)}</td>'
        f'<td class="r">{num(x.get("vol"), 0)}{"%" if x.get("vol") is not None else ""}</td></tr>' for x in xs)
    hd = "".join(f'<th{" class=r" if i > 1 else ""}>{T(a, "")}</th>' for i, a in enumerate(
        ("ETF", "對照（自動挑選）", "倍數", "近 1 年實際", "倍數 × 對照", "差距", "近 3 年實際", "倍數 × 對照", "差距", "對照年化波動")))
    tab = f'<div class="scroll"><table class="mini"><thead><tr>{hd}</tr></thead><tbody>{tr}</tbody></table></div>'
    miss = [x for x in (p.get("lev") or []) if not x.get("ref")]
    mb = (f'<p class="small muted">{T("找不到可對照的指數資料（免費來源沒有，或相關性不夠高）：" + "、".join(esc(x["code"]) + " " + esc(x["name"][:10]) for x in miss) + "。", "")}</p>'
          if miss else "")
    how = ("倍數從 ETF 名稱判斷（正 2＝2 倍、反 1＝−1 倍）。對照指數不是人工指定，而是從加權指數、0050、美股與各國指數、原油、黃金、美元、日圓、美債中，"
           "挑過去兩年每週漲跌最一致的一個（台灣交易時美國休市，所以也比較美國前一天的收盤）。"
           "差距＝實際含息報酬 − 倍數 × 對照的漲跌：負數＝耗損（震盪、管理費、期貨轉倉與避險成本），正數＝一路單邊行情讓複利放大。"
           "反向 ETF 遇到對照大漲超過 100% 時，「−1 × 對照」低於 −100%（不可能的報酬），這時不計算差距（顯示「—」）。"
           "海外指數的差距還包含匯率與時差；期貨型的差距包含轉倉成本。這些 ETF 主要設計給短期操作，不是投資建議。")
    return card("槓桿／反向 ETF：長期不是剛好幾倍", "Leveraged / inverse ETFs over time", _lead(lead) + tab + mb + _how(how, "怎麼算的"), "wide")


# ------------------------------------------------------------------ 5. 主動式 ETF 成績單
def sec_etf_active(eng) -> str:
    p = _p(eng)
    xs = p.get("active") or [] if p.get("available") else []
    if not xs:
        return ""
    with_ref = [x for x in xs if x.get("diff") is not None]
    beat = [x for x in with_ref if x["diff"] > 0]
    old = [x for x in with_ref if x["days"] >= 250]
    ob = [x for x in old if x["diff"] > 0]
    lead = (f"一句話看懂：{len(xs)} 檔主動式 ETF 中，{len(with_ref)} 檔找得到對照指數，自上市以來 {len(beat)} 檔贏過同期對照"
            + (f"；上市滿一年的 {len(old)} 檔中 {len(ob)} 檔贏" if old else "")
            + "。多數上市不到一年，時間太短，成績很容易因為一兩個月的行情翻盤。")
    tr = "".join(
        f'<tr><td>{_nm(x, 10)}<div class="small muted">{T("上市 " + x["since"] + "（" + str(x["days"]) + " 個交易日" + ("，不到半年" if x["days"] < 120 else "") + "）", "")}</div></td>'
        f'<td class="r">{num(x.get("aum"), 0)}</td><td class="r">{_pc(x["tr"])}</td>'
        f'<td class="small">{T(_ref(x["ref"]) if x.get("ref") else "找不到相關性夠高的對照", "")}</td>'
        f'<td class="r">{_pc(x.get("ref_tr"))}</td><td class="r"><b>{_pc(x.get("diff"))}</b></td>'
        f'<td class="r">{_pc(x.get("mdd"))}</td><td class="r">{_pc(x.get("ref_mdd"))}</td></tr>' for x in xs)
    hd = "".join(f'<th{" class=r" if i not in (0, 3) else ""}>{T(a, "")}</th>' for i, a in enumerate(
        ("ETF", "規模（億）", "上市以來含息", "對照（自動挑選）", "對照同期", "差距", "最大回落", "對照最大回落")))
    tab = f'<div class="scroll"><table class="mini"><thead><tr>{hd}</tr></thead><tbody>{tr}</tbody></table></div>'
    how = ("主動式 ETF 由經理人自己選股，收費通常比指數型高，所以要看它有沒有比「不用選股的指數」好。"
           "對照從 0050（台股）、SPY（標普 500）、QQQ（那斯達克 100）、SOXX（美國半導體）、TLT（美債）中，挑和這檔漲跌最一致的一個；美國 ETF 都含息並換算成台幣。"
           "上市以來含息＝從第一個收盤價算起（含配息再投入），對照用同一段時間。最大回落一起比，看它是不是用更大的波動換來報酬。"
           "上市未滿半年的結果參考價值很低。不是投資建議。")
    return card("主動式 ETF 成績單：有沒有比指數好", "Active ETFs vs their benchmark", _lead(lead) + tab + _how(how, "怎麼算的"), "wide")


def perf_map(eng) -> dict:
    """{code: [1-year total return, 3-year annualised]} for the search table."""
    p = _p(eng)
    return {x["code"]: [None if x.get("tr1y") is None else round(x["tr1y"], 1), None if x.get("tr3y") is None else round(x["tr3y"], 1)]
            for x in (p.get("rows") or [])} if p.get("available") else {}
