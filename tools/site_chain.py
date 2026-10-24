"""AI 視角看風險頁：AI 產業鏈連動——泡沫洩氣時誰會被拖下水（歷史：1970 年以來半導體崩跌期間各產業 vs 大盤；現在：產業鏈各環節對費半的下跌連動度）。"""
from __future__ import annotations

from tools.site_ai import _anchor
from tools.sitekit import T, card, esc, num

NOTE = ("怎麼看：人類通常只盯主角（輝達、台積電），但泡沫洩氣時被拖下水的常是周邊被當成「AI 受惠股」的產業。"
        "「下跌連動度」＝費半單日跌 ≥2% 的那些天，這一組平均跟著跌幾倍（1＝跟費半一樣，>1＝更兇，接近 0＝幾乎不受影響），用最近約兩年的日資料；台股收盤比美股開盤早，所以台股用費半大跌「隔天」的漲跌來算。"
        "「如果費半再跌 20%」只是用連動度線性換算的粗估，真正的大跌常常連動度會變高。歷史部分用 Ken French 49 產業月報酬，"
        "每一次都是同一個起訖月，和全部產業的平均比，看「同一場風暴裡誰比較慘」；其中 1974、2009 是全面股災。不是投資建議。")


def _ac(eng) -> dict:
    c = getattr(eng, "_ai_chain", None)
    if c is None:
        try:
            from wsb.analytics import ai_chain as AC
            c = AC.build(eng)
        except Exception:  # noqa: BLE001
            c = {}
        try:
            eng._ai_chain = c
        except Exception:  # noqa: BLE001
            pass
    return c


def headline(now: dict) -> str:
    g = {x["zh"]: x for x in now["groups"]}
    top = now["groups"][0]
    parts = [f"最敏感的是「{top['zh']}」：費半大跌時平均跌到 {top['beta']:.2f} 倍"]
    pw, ut = g.get("電力與電網"), g.get("公用事業（對照）")
    if pw and pw["beta"] >= 0.5:
        parts.append(f"被當成防禦股的「電力與電網」連動度 {pw['beta']:.2f}" + (f"，遠高於真正的公用事業 {ut['beta']:.2f}" if ut else "") + "——它已經和 AI 綁在同一台車上")
    hs = g.get("雲端巨頭")
    if hs and hs["beta"] < 0.5:
        parts.append(f"雲端巨頭只有 {hs['beta']:.2f}，反而最穩")
    return "；".join(parts) + "。"


@_anchor("ai-chain")
def sec_ai_chain(eng) -> str:
    c = _ac(eng)
    now, hist = c.get("now"), c.get("history")
    if not now and not hist:
        return ""
    body = ""
    if now:
        rows = ""
        for g in now["groups"]:
            mem = "、".join(f"{esc(m['sym'])} {m['beta']:.2f}" for m in g["members"])
            rows += (f'<tr><td><b>{T(g["zh"], g["en"])}</b><br><span class="small muted">{mem}</span></td>'
                     f'<td class="r"><b class="{"dn" if g["beta"] >= 1 else ""}">{g["beta"]:.2f}</b></td>'
                     f'<td class="r">{num(g["ret1y"], 0, sign=True)}%</td><td class="r">{g["off"]:+.0f}%</td><td class="r">{g["if20"]:+.0f}%</td></tr>')
        miss = ("（資料中心 REIT 等 " + "、".join(now["missing"]) + " 本站沒有價格，未列入）") if now.get("missing") else ""
        ctx = f"費半目前離一年高點 {now['sox_off']:+.0f}%；最近約兩年費半單日跌 ≥2% 的有 {now['sox_down_days']} 天。" + miss
        body += (f'<p class="rimp big2"><b>{T(headline(now), "")}</b></p>'
                 f'<p class="small muted">{T(ctx, "")}</p>'
                 f'<div class="scroll"><table class="mini"><thead><tr><th>{T("產業鏈環節（成員與各自連動度）", "")}</th><th class="r">{T("下跌連動度", "")}</th>'
                 f'<th class="r">{T("1 年漲幅", "")}</th><th class="r">{T("離一年高點", "")}</th><th class="r">{T("若費半再跌 20%（粗估）", "")}</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div>')
    if hist:
        eps = "、".join(f"{e['peak']}→{e['trough']}（{e['fall'] * 100:.0f}%）" for e in hist["episodes"])
        worst = "".join(f"<li>{T(r['zh'], '')}：比大盤 {r['rel']:+.0f} 個百分點（{r['worse']}/{r['n']} 次比大盤差）</li>" for r in hist["rows"][:6] if r["ind"] != "Chips")
        best = "".join(f"<li>{T(r['zh'], '')}：比大盤 {r['rel']:+.0f} 個百分點（{r['n'] - r['worse']}/{r['n']} 次比大盤好）</li>" for r in hist["rows"][::-1][:6])
        body += (f'<p><b>{T("歷史：半導體每一次崩跌時，其他產業怎麼走", "")}</b>（{T("1970 年以來 " + str(len(hist["episodes"])) + " 次：" + eps, "")}）</p>'
                 f'<div class="g2"><div><b class="dn">{T("跟著崩得最慘", "")}</b><ul class="small">{worst}</ul></div>'
                 f'<div><b class="up">{T("撐得最好", "")}</b><ul class="small">{best}</ul></div></div>')
    body += f'<p class="note">{T(NOTE, "")}</p>'
    return card("AI 產業鏈連動：泡沫洩氣時誰會被拖下水", "AI supply chain: who gets dragged down", body, "wide")


def tile(eng):
    c = _ac(eng)
    now = c.get("now")
    if not now:
        return None
    top = now["groups"][0]
    pw = next((g for g in now["groups"] if g["zh"] == "電力與電網"), None)
    sub = f"最敏感：{top['zh']}（{top['beta']:.2f} 倍）" + (f"・電力股 {pw['beta']:.2f}" if pw else "")
    return ("ai-chain", "🔗 AI 產業鏈連動", f"{top['beta']:.2f}<small> 倍</small>", sub, "")
