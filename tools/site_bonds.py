"""全球債市 page: what the bond market is saying in plain words, government bonds across regions, corporate bonds, and the
money flowing between them (Japan MOF weekly, US TIC).  Data and rules only; not a forecast or advice."""
from __future__ import annotations

import pandas as pd

from tools.sitekit import T, card, cls, esc, num

NOTE_SOV = ("10 年期公債殖利率＝政府借 10 年要付的利率，也是房貸、企業借款和股票估值的「地基」。"
            "美國與日本是每日資料（美國：FRED；日本：財務省），其他國家是 OECD 每月平均（FRED），所以日期不同。"
            "百分位是和自己的歷史比；「比美國」為正代表那國借錢比美國貴。兩邊都是每日資料時用同一天相減，否則改用兩邊都有資料的最近一個月的月均值相減（格內註明月份），不拿昨天的美債和上個月的歐債直接比。歐元區國家另列「比德國」：南歐比德國多付越多，市場越擔心那國的財政。")
NOTE_CORP = ("利差＝公司債殖利率減同年期公債，是借錢給企業的人要求的「違約風險補償」。利差越低＝市場要求的補償越少（不等於安全：也可能是估值偏貴、緩衝變薄），急速擴大＝開始擔心違約。"
             "投資級是體質較好的公司（BBB 是其中最低一級，最常被降成垃圾債），高收益債（垃圾債）是體質較弱的公司，CCC 是最弱的一群。"
             "資料：ICE 美銀債券指數（FRED），FRED 只提供近 3 年，本站每次抓取都會存檔，所以百分位的比較期間會越來越長（欄位註明起算月）。"
             "「急速擴大」＝3 個月內擴大超過原本的四分之一。殖利率是公司實際要付的利率，直接影響再融資壓力。")
NOTE_FLOW = ("日本財務省每週四公布「對外及對內證券買賣」（指定報告機構，週資料，2005 年起）：負數＝日本投資人淨賣超外國中長期債、把錢帶回日本。"
             "週資料波動很大，看連續幾週與 5 週合計在歷史上的位置比較有意義。"
             "美國財政部 TIC 每月公布各國持有美國公債的金額（約晚 6 週）；持有金額的變化同時包含買賣與價格漲跌（利率上升時，同樣的債券市值會變小），"
             "所以減少不全等於有人在賣。外國官方＝各國央行與政府機構。")


def _mon(m) -> str:
    """The month a cross-country gap was measured on, when the two series could not be compared on the same day."""
    return f'<div class="small muted">{T(f"{m} 月均", f"{m} avg")}</div>' if m else ""


def _sov_card(r, keys=None, title=("各國公債：美國、日本、歐洲、亞太", "Government bonds by market")) -> str:
    sv = [x for x in r["sov"] if keys is None or x["k"] in keys]
    if not sv:
        return ""
    rows = ""
    for x in sv:
        pct = f"第 {x['pct']:.0f}"
        mon = "" if x["daily"] else "（月）"
        rows += (f'<tr><td class="nw"><b>{T(x["zh"], "")}</b></td><td class="r"><b>{x["now"]:.2f}%</b></td>'
                 f'<td class="r {cls(x["chg1y"])}">{num(x["chg1y"], 2, sign=True)}</td>'
                 f'<td class="r">{T(pct, "")}<div class="small muted">{x["since"]} {T("年起", "")}</div></td>'
                 f'<td class="r">{num(x["vs_us"], 2, sign=True)}{_mon(x.get("vs_us_m"))}</td>'
                 f'<td class="r">{num(x["vs_de"], 2, sign=True)}{_mon(x.get("vs_de_m"))}</td>'
                 f'<td class="small muted">{esc(x["date"])}{T(mon, "")}</td></tr>')
    up = [x["zh"] for x in sv if (x["chg1y"] or 0) >= 0.25]
    hi = [x["zh"] for x in sv if x["pct"] >= 90]
    lead = (f"一句話看懂：{len(sv)} 個市場中 {len(up)} 個的長債利率比一年前高 0.25 個百分點以上"
            + (f"；{'、'.join(hi)} 在自己歷史的前 10% 高檔" if hi else "") + "。")
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p><div class="scroll"><table class="mini"><thead><tr><th>{T("市場", "Market")}</th>'
            f'<th class="r">{T("10 年期殖利率", "10Y yield")}</th><th class="r">{T("比一年前（百分點）", "1y chg (pp)")}</th>'
            f'<th class="r">{T("歷史百分位", "Pct")}</th><th class="r">{T("比美國", "vs US")}</th><th class="r">{T("比德國", "vs Germany")}</th>'
            f'<th>{T("資料日", "Date")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<details class="sgx"><summary>{T("這張表怎麼看", "How to read")}</summary><p class="note">{T(NOTE_SOV, "")}</p></details>')
    return card(*title, body, "wide")


def _corp_card(r, keys=None, title=("公司債：美國、歐洲、新興市場與亞洲", "Corporate bonds")) -> str:
    cp = [x for x in r["corp"] if keys is None or x["k"] in keys]
    if not cp:
        return ""
    col = {"急速擴大": "dn", "緊張": "dn", "利差偏低": "up", "正常": ""}
    rows = ""
    for x in cp:
        pct = f"第 {x['pct']:.0f}"
        ch = None if x["chg3m"] is None else x["chg3m"] * 100
        ey = (f'{x["ey"]:.2f}%' if x["ey"] is not None else "—") + (f'<div class="small muted">{T("一年", "1y")} {x["ey_1y"]:+.2f}</div>' if x.get("ey_1y") is not None else "")
        rows += (f'<tr><td class="nw">{T(x["zh"], "")}</td><td class="r"><b>{x["oas"]:.2f}%</b></td>'
                 f'<td class="r {cls(-(x["chg3m"] or 0))}">{num(ch, 0, sign=True)} bp</td>'
                 f'<td class="r">{T(pct, "")}<div class="small muted">{x["since"]} {T("起", "")}</div></td>'
                 f'<td><b class="{col[x["state"]]}">{T(x["state"], "")}</b></td><td class="r">{ey}</td></tr>')
    wide = [x["zh"] for x in cp if x["state"] in ("緊張", "急速擴大")]
    calm = [x["zh"] for x in cp if x["state"] == "利差偏低"]
    lead = ("一句話看懂：" + (f"{'、'.join(wide)} 的利差在擴大或處在高檔，債市開始擔心這些企業還不出錢。" if wide else
                         f"{len(cp)} 類公司債中有 {len(calm)} 類利差在自己歷史的低檔：市場要求的違約補償偏低，這不等於安全（估值偏貴、緩衝變薄）。" if calm else
                         "各類公司債利差都在正常範圍。"))
    dec = ""
    for x in cp:
        d = x.get("dec")
        if not d:
            continue
        main = "主要來自公債利率" if abs(d["rate"]) > abs(d["spread"]) else "主要來自信用利差"
        dec += (f'<li>{T(x["zh"], "")}：近 3 個月企業借錢利率 {d["total"] * 100:+.0f} bp ＝ 公債利率 {d["rate"] * 100:+.0f} bp ＋ '
                f'信用利差 {d["spread"] * 100:+.0f} bp，{main}。</li>')
    if dec:
        how = ("指數殖利率＝同期公債利率＋利差（OAS），所以兩者變化相減就是公債利率的部分。這是整個指數的拆解，不是單一檔債券；"
               "利差擴大才是市場在擔心違約，單純利率上升是整體借錢成本變貴。")
        dec = (f'<details class="sgx"><summary>{T("公司債利率變動拆解：是利率還是信用？", "Rates vs credit")}</summary><ul class="small">{dec}</ul>'
               f'<p class="note">{T(how, "")}</p></details>')
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p><div class="scroll"><table class="mini"><thead><tr><th>{T("類別", "Type")}</th>'
            f'<th class="r">{T("利差", "Spread")}</th><th class="r">{T("3 個月變化", "3m chg")}</th><th class="r">{T("歷史百分位", "Pct")}</th>'
            f'<th>{T("狀態", "State")}</th><th class="r">{T("企業實際借錢利率", "Yield")}</th></tr></thead><tbody>{rows}</tbody></table></div>'
            f'<p class="small"><a class="golink" href="#cb_us" data-p="cb_us">{T("美國信用利差回測與 EBP →", "US credit detail →")}</a>　'
            f'<a class="golink" href="#industry" data-p="industry">{T("各產業公司財務體檢 →", "Sector credit →")}</a></p>{dec}'
            f'<details class="sgx"><summary>{T("這張表怎麼看", "How to read")}</summary><p class="note">{T(NOTE_CORP, "")}</p></details>')
    return card(*title, body, "wide")


def _flow_card(r, show=("mof", "tic"), title=("跨國資金：日本資金回流、誰在買賣美債", "Cross-border bond flows")) -> str:
    mof = (r["flows"].get("mof") or {}) if "mof" in show else {}
    tic = (r["flows"].get("tic") or {}) if "tic" in show else {}
    if not mof and not tic:
        return ""
    parts = []
    if mof:
        run = mof["run"]
        streak = (f"連續 {run} 週賣超" if run > 0 else f"連續 {-run} 週買超" if run < 0 else "")
        where = ("是 " + mof["since"] + f" 年以來最大的 {mof['pct5']:.0f}% 之一" if mof["pct5"] <= 10 else
                 "是 " + mof["since"] + f" 年以來最大的 {100 - mof['pct5']:.0f}% 之一（買超）" if mof["pct5"] >= 90 else "在歷史正常範圍")
        mtxt = f"最近 5 週合計 {mof['sum5']:+.2f} 兆日圓（{streak}），{where}；近 13 週 {mof['sum13']:+.2f} 兆、近 52 週 {mof['sum52']:+.2f} 兆。"
        wk = "".join(f'<tr><td class="small">{esc(w)}</td><td class="r {cls(v)}">{v:+.2f}</td></tr>' for w, v in mof["weeks"])
        parts.append(f'<h3>{T("🇯🇵 日本投資人買賣外國中長期債（每週）", "Japan: foreign bond flows")}</h3>'
                     f'<p>{T(mtxt, "")}</p>'
                     f'<div class="scroll"><table class="mini"><thead><tr><th>{T("週", "Week")}</th><th class="r">{T("淨買賣（兆日圓）", "Net (¥tn)")}</th></tr></thead>'
                     f'<tbody>{wk}</tbody></table></div>')
    if tic:
        ttxt = f"{tic['month']} 外國合計持有 {tic['total'] / 1000:,.2f} 兆美元，半年 {num(tic['total_chg6'], 1, sign=True, pct=True)}。"
        rows = "".join(f'<tr><td>{T(x["zh"], x["name"])}</td><td class="r">{x["now"]:,.0f}</td><td class="r {cls(x["chg6"])}">{num(x["chg6"], 1, sign=True, pct=True)}</td>'
                       f'<td class="r {cls(x["chg12"])}">{num(x["chg12"], 1, sign=True, pct=True)}</td></tr>' for x in tic["rows"] + ([tic["official"]] if tic.get("official") else []))
        parts.append(f'<h3>{T("🇺🇸 誰持有美國公債（每月，TIC）", "Who holds US Treasuries")}</h3>'
                     f'<p>{T(ttxt, "")}</p>'
                     + f'<div class="scroll"><table class="mini"><thead><tr><th>{T("國家", "Country")}</th><th class="r">{T("持有（十億美元）", "$bn")}</th>'
                     f'<th class="r">{T("半年變化", "6m")}</th><th class="r">{T("一年變化", "12m")}</th></tr></thead><tbody>{rows}</tbody></table></div>')
    jp = next((x for x in tic.get("rows") or [] if x["name"] == "Japan"), None)
    lead = "一句話看懂：" + "；".join(x for x in (
        (f"日本投資人最近 5 週賣超外國債券 {abs(mof['sum5']):.1f} 兆日圓" if mof and mof["sum5"] < 0 else f"日本投資人最近 5 週買超外國債券 {mof['sum5']:.1f} 兆日圓" if mof else ""),
        (f"日本持有的美債半年{'減少' if jp['chg6'] < 0 else '增加'} {abs(jp['chg6']):.0f}%" if jp and jp.get("chg6") is not None else "")) if x) + "。"
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p>' + "".join(parts)
            + f'<p class="small"><a class="golink" href="#stability" data-p="stability">{T("外國央行託管的美債、日圓套利交易（金融穩定頁）→", "Custody & yen carry →")}</a></p>'
            f'<details class="sgx"><summary>{T("資料怎麼來", "Sources")}</summary><p class="note">{T(NOTE_FLOW, "")}</p></details>')
    return card(*title, body, "wide")


def _r(eng):
    r = getattr(eng, "_bonds", None)
    if r is None:
        from wsb.analytics import bonds as BD
        try:
            r = BD.build(eng)
        except Exception:  # noqa: BLE001
            r = {"available": False}
        eng._bonds = r
    return r


def sec_gb_brief(eng) -> str:
    from wsb.analytics import bonds as BD
    r = _r(eng)
    if not r.get("available"):
        return ""
    rd = BD.read(r)
    lis = "".join(f"<li>{T(x, '')}</li>" for x in rd["imp"])
    body = (f'<p class="rimp big2"><b>{T(rd["head"], "")}</b></p><h3>{T("白話：這對我們代表什麼", "What it means")}</h3><ul>{lis}</ul>'
            f'<p class="note">{T("每一句都是依下面幾張卡片的數字自動選出來的，數字變了句子會跟著變。描述現況與歷史，不是預測，也不是投資建議。", "")}</p>')
    return card("債市在說什麼：全球債券一句話", "What the bond market is saying", body, "wide")


def _jgb_card(eng) -> str:
    try:
        df = eng.global_yields.jgb
    except Exception:  # noqa: BLE001
        return ""
    if df is None or not len(df):
        return ""
    rows, ten = "", None
    for t in ("1Y", "2Y", "5Y", "10Y", "20Y", "30Y", "40Y"):
        if t not in df.columns:
            continue
        s = df[t].dropna()
        if len(s) < 260:
            continue
        now = float(s.iloc[-1])
        prev = s[s.index <= s.index[-1] - pd.Timedelta(days=365)]
        ch = now - float(prev.iloc[-1]) if len(prev) else None
        pct = float((s.iloc[:-1] < now).mean() * 100)
        if t == "10Y":
            ten = (now, ch, pct, s.index[0].strftime("%Y"), s.index[-1].strftime("%Y-%m-%d"))
        ptxt = f"第 {pct:.0f}"
        rows += (f'<tr><td>{T(t.replace("Y", " 年"), t)}</td><td class="r"><b>{now:.2f}%</b></td><td class="r {cls(ch)}">{num(ch, 2, sign=True)}</td>'
                 f'<td class="r">{T(ptxt, "")}<div class="small muted">{s.index[0].strftime("%Y")} {T("年起", "")}</div></td></tr>')
    if not rows:
        return ""
    lead = ("一句話看懂：" + (f"日本 10 年期公債殖利率 {ten[0]:.2f}%" + (f"，比一年前{'高' if ten[1] >= 0 else '低'} {abs(ten[1]):.2f} 個百分點" if ten[1] is not None else "") + f"，"
                         f"在 {ten[3]} 年以來第 {ten[2]:.0f} 百分位。" if ten else "")
            + "日本國內利率越高，日本的壽險、銀行和退休基金越不需要出國買外國債券。")
    note = ("日本公債殖利率來自日本財務省每日公布的固定期限殖利率。日本曾經長期零利率甚至負利率，所以日本資金大量買美債與歐債賺利差；"
            "國內利率回升後，這股資金有回流日本的動機，這是「日本撤資」說法背後的邏輯。實際有沒有在賣，要看下面財務省的每週買賣資料。")
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p><div class="scroll"><table class="mini"><thead><tr><th>{T("期限", "Tenor")}</th>'
            f'<th class="r">{T("殖利率", "Yield")}</th><th class="r">{T("比一年前（百分點）", "1y chg")}</th><th class="r">{T("歷史百分位", "Pct")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div><p class="small muted">{T("資料日 " + (ten[4] if ten else ""), "")}</p>'
            f'<details class="sgx"><summary>{T("為什麼日本利率重要", "Why it matters")}</summary><p class="note">{T(note, "")}</p></details>')
    return card("日本公債殖利率曲線：日本國內利率回來了嗎", "Japanese government bond yields", body, "wide")


def sec_cb_brief(eng) -> str:
    from wsb.analytics import bonds as BD
    r = _r(eng)
    if not r.get("available") or not r.get("corp"):
        return ""
    rd = BD.corp_read(r)
    lis = "".join(f"<li>{T(x, '')}</li>" for x in rd["imp"])
    body = (f'<p class="rimp big2"><b>{T(rd["head"], "")}</b></p><h3>{T("白話：這對我們代表什麼", "What it means")}</h3><ul>{lis}</ul>'
            f'<p class="small"><a class="golink" href="#risk" data-p="risk">{T("個別公司的破產預警與財務體檢（風險模型頁）→", "Company distress →")}</a></p>'
            f'<p class="note">{T("每一句都依各區公司債的數字自動選出，數字變了句子會跟著變。描述現況與歷史，不是預測，也不是投資建議。", "")}</p>')
    return card("公司債在說什麼：借錢給企業的人放不放心", "What corporate bonds are saying", body, "wide")


# prices only: these describe how the two markets moved, which fits (but does not prove) money moving between them
ROT_WORD = {"股跌債漲": "股票跌、國債漲（利率降）：符合資金避險轉進國債的表現",
            "股債雙殺": "股票和國債一起被賣：符合換現金的表現，不像轉進國債",
            "股漲債跌": "股票漲、國債跌（利率升）：符合風險偏好升溫的表現",
            "股債齊漲": "股票和國債一起漲：通常是市場預期降息",
            "沒有明顯轉移": "股市和國債利率都沒有大幅變動，看不出資金大舉從股票轉進國債"}
NOTE_ROT = ("判斷規則：近一個月標普 500 跌 3% 以上、同時 10 年期國債利率降 20bp 以上＝「股跌債漲」（資金轉進國債）；股跌而利率升 20bp 以上＝「股債雙殺」（換現金）。"
            "國債被搶買時價格上漲、利率下降，所以看利率方向就知道錢有沒有進國債。"
            "貨幣市場基金資料來自美國金融研究辦公室（OFR）的貨幣市場基金監測（根據各基金向 SEC 申報，每月、約晚一個月，2010 年起）。"
            "「最大單日降幅」用來抓單日的避險潮（例如財報或數據引發的恐慌）。"
            "這些狀態只看價格，價格同向變動「符合」資金移動，但不等於已證實有資金從一邊搬到另一邊；實際資金流請看下方的資金流資料與其期間。這是對數據的描述，不是預測。")


def sec_gb_rotation(eng) -> str:
    r = _r(eng)
    x = r.get("rot") if r.get("available") else None
    if not x or not x.get("state"):
        return ""
    lead = (f"一句話看懂：{x['state']}——{ROT_WORD[x['state']]}。（近一個月標普 {x['spx_1m']:+.1f}%、10 年期國債利率 {x['d10']:+.0f} bp）")
    facts = [f"10 年期國債利率 {x['y10']:.2f}%" + (f"、2 年期 {x['y2']:.2f}%" if x.get("y2") is not None else "") + f"（{x['date']}）。"]
    b = x.get("big")
    if b and b["bp"] <= -10:
        facts.append(f"近 20 個交易日最大單日降幅：{b['date']} 10 年期利率 {b['bp']:.0f} bp，是 {b['since']} 以來最大的單日降幅之一：那天有明顯的資金湧入國債避險。")
    m = x.get("mm")
    if m:
        pace = ("增加速度是 " + m["since"] + " 年以來最快的 10% 之一：大量資金停在現金觀望" if m["pct3"] >= 90 else
                "增加偏快" if m["pct3"] >= 75 else "大致持平" if abs(m["chg3"]) < 1 else "在減少：停在場邊的現金正被拿去投資或花掉" if m["chg3"] < 0 else "穩定增加")
        facts.append(f"貨幣市場基金（把錢停在短期國庫券等現金工具）總額 {m['now']:.2f} 兆美元（{m['month']}）"
                     + ("，創歷史新高" if m["high"] else "") + f"；近 3 個月 {m['chg3']:+.1f}%、一年 {m['chg12']:+.1f}%：{pace}。"
                     + (f"其中 {m['tsy_share']:.0f}% 投資在美國國債。" if m.get("tsy_share") else ""))
    lis = "".join(f"<li>{T(f, '')}</li>" for f in facts)
    body = (f'<p class="rimp big2"><b>{T(lead, "")}</b></p><ul>{lis}</ul>'
            f'<p class="small"><a class="golink" href="#overview" data-p="overview">{T("即時燈號裡也有「股市下跌＋國債利率下降」組合 →", "Live pattern light →")}</a></p>'
            f'<details class="sgx"><summary>{T("怎麼判斷", "How it is judged")}</summary><p class="note">{T(NOTE_ROT, "")}</p></details>')
    return card("資金往哪跑：從股票轉進國債了嗎", "Is money rotating from stocks into Treasuries?", body, "wide")


def sec_gb_sovereign(eng) -> str:
    r = _r(eng)
    return _sov_card(r) if r.get("available") else ""


def sec_gb_europe(eng) -> str:
    r = _r(eng)
    return _sov_card(r, ("de", "gb", "fr", "it", "es", "gr"), ("歐洲公債：德國、英國與南歐", "European government bonds")) if r.get("available") else ""


def sec_gb_jgb(eng) -> str:
    return _jgb_card(eng)


def sec_gb_mof(eng) -> str:
    r = _r(eng)
    return _flow_card(r, ("mof",), ("日本資金：日本投資人每週買賣外國債券", "Japan: weekly foreign bond flows")) if r.get("available") else ""


def sec_gb_tic(eng) -> str:
    r = _r(eng)
    return _flow_card(r, ("tic",), ("誰持有美國公債：各國每月持有變化（TIC）", "Who holds US Treasuries")) if r.get("available") else ""


def sec_gb_flows(eng) -> str:
    r = _r(eng)
    return _flow_card(r) if r.get("available") else ""


def sec_cb_us(eng) -> str:
    r = _r(eng)
    return _corp_card(r, ("us_ig", "us_bbb", "us_hy", "us_ccc"), ("美國公司債：投資級、BBB、垃圾債、CCC", "US corporate bonds")) if r.get("available") else ""


def sec_cb_eu(eng) -> str:
    r = _r(eng)
    return _corp_card(r, ("eu_hy", "us_hy"), ("歐洲公司債：歐洲垃圾債（對照美國）", "European corporate bonds")) if r.get("available") else ""


def sec_cb_em(eng) -> str:
    r = _r(eng)
    return _corp_card(r, ("em", "asia", "em_hy"), ("新興市場與亞洲公司債", "Emerging-market & Asian corporate bonds")) if r.get("available") else ""


def sec_gb_corp(eng) -> str:
    r = _r(eng)
    return _corp_card(r) if r.get("available") else ""
