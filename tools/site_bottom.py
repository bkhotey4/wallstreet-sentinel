"""抄底四訊號 card (情緒與警報 page): the four contrarian conditions, how many hold now, and what the S&P 500 did after
the two long-history ones fired in the past.  Market data only; history, not advice."""
from __future__ import annotations

from tools.sitekit import T, card, cls, esc, num

_LV = {"all": ("四項全部成立：極端恐慌", "All four: extreme fear", "dn"), "near": ("三項成立：接近極端恐慌", "Three of four", "dn"),
       "watch": ("兩項成立：恐慌升溫", "Two of four", "warn"), "none": ("尚未出現極端恐慌", "No extreme fear yet", "muted")}


def _cell(x) -> str:
    if not x or x.get("med") is None:
        return '<span class="muted">—</span>'
    return f'<b class="{cls(x["med"])}">{num(x["med"], 1, sign=True, pct=True)}</b><div class="small muted">{T("上漲", "up")} {x["win"]:.0f}%</div>'


def sec_bottom(eng) -> str:
    from wsb.analytics import bottom as BT
    try:
        r = BT.build(eng)
    except Exception:  # noqa: BLE001
        return ""
    if not r.get("available"):
        return ""
    zh, en, c = _LV[r["level"]]
    rows = ""
    for s in r["signals"]:
        v = s["fmt"].format(s["v"]) if s["v"] is not None else "—"
        st = (f'<span class="muted">{T("資料過舊", "stale")}</span>' if s["stale"] else
              f'<b class="dn">✅ {T("成立", "met")}</b>' if s["hit"] else
              f'<span class="muted">{T("未成立", "not met")}</span>' if s["avail"] else f'<span class="muted">{T("取不到", "n/a")}</span>')
        rows += (f'<tr><td>{T(s["zh"], s["en"])}</td><td class="r"><b>{esc(v)}</b></td><td class="r">{esc(s["rule"])}</td>'
                 f'<td>{st}</td><td class="small muted">{esc(s["date"] or "")}</td></tr>')
    bt = r["bt"]
    labs = [("both", "VIX > 40 且 RSI < 30（同一天）", "VIX > 40 and RSI < 30"), ("vix", "VIX > 40", "VIX > 40"), ("rsi", "RSI < 30", "RSI < 30")]
    brow = ""
    for k, z, e in labs:
        x = bt[k]
        brow += (f'<tr><td>{T(z, e)}</td><td class="r">{x["n"]}</td>' + "".join(f'<td class="r">{_cell(x[h])}</td>' for h in ("1m", "3m", "6m", "12m"))
                 + f'<td class="r">{num(x.get("further"), 1, pct=True)}<div class="small muted">{T("最深", "worst")} {num(x.get("worst"), 1, pct=True)}{"（走完 3 個月的 " + str(x["further_n"]) + " 次）" if x.get("further_n") is not None else ""}</div></td></tr>')
    a = bt["all"]
    brow += (f'<tr><td class="muted">{T("任何一天（對照）", "Any day (baseline)")}</td><td class="r muted">—</td>'
             + "".join(f'<td class="r">{_cell(a[h])}</td>' for h in ("1m", "3m", "6m", "12m")) + '<td class="r muted">—</td></tr>')
    last = bt["both"]["dates"][-4:]
    cn = r.get("cnn") or {}
    cnn_txt = ""
    if cn:
        cnn_txt = T(f"CNN 兩項的歷史只有 {cn.get('fg_since', '—')} 起（每天存檔，會越來越長）：恐懼貪婪 < 10 最近一次 {cn.get('fg_last') or '這段期間沒有'}；"
                    f"Put/Call 5 日平均 > 0.9 最近一次 {cn.get('pc_last') or '這段期間沒有'}。",
                    f"CNN history from {cn.get('fg_since', '—')} only (archived daily).")
    note = T(f"四項是常見的逆勢「抄底」檢查表：恐懼貪婪、VIX、標普 RSI(14)、Put/Call 5 日平均（後兩項取自 CNN 恐懼與貪婪指數的分項，來源是 CBOE）。"
             f"回測用歷史最長的 VIX 與 RSI（{r['since']} 年起），每一波只算第一天（之前 20 個交易日沒有出現過才算新的一波），避免一次崩盤被算成幾十次。"
             f"「之後再跌」是訊號出現後 3 個月內，標普從訊號當天再往下跌的中位數：訊號出現不代表已經是最低點。"
             f"最近幾次 VIX 與 RSI 同時成立：{'、'.join(last) or '—'}。歷史統計，不是預測，也不是買賣建議。",
             "Contrarian checklist. Back-test on VIX and RSI, one count per episode. History, not a forecast or advice.")
    body = (f'<div class="bth"><span class="bign {c}">{r["n_hit"]} / 4</span> <b class="{c}">{T(zh, en)}</b>'
            f'<span class="small muted">（{T("可取得的訊號", "available")} {r["n_avail"]} {T("項", "")}）</span></div>'
            f'<table class="mini"><thead><tr><th>{T("訊號", "Signal")}</th><th class="r">{T("目前", "Now")}</th><th class="r">{T("門檻", "Rule")}</th>'
            f'<th>{T("狀態", "State")}</th><th>{T("資料日", "Date")}</th></tr></thead><tbody>{rows}</tbody></table>'
            f'<h3>{T("過去出現時，標普 500 之後怎麼走", "What the S&P 500 did next")}</h3>'
            f'<div class="scroll"><table class="mini"><thead><tr><th>{T("情況", "Case")}</th><th class="r">{T("次數", "Episodes")}</th>'
            f'<th class="r">{T("1 個月", "1m")}</th><th class="r">{T("3 個月", "3m")}</th><th class="r">{T("6 個月", "6m")}</th><th class="r">{T("12 個月", "12m")}</th>'
            f'<th class="r">{T("之後再跌（中位數）", "Further fall (median)")}</th></tr></thead><tbody>{brow}</tbody></table></div>'
            + (f'<p class="note">{cnn_txt}</p>' if cnn_txt else "") + f'<p class="note">{note}</p>')
    return card("抄底四訊號：恐慌到極點了嗎", "Bottom checklist: is fear extreme?", body, "wide")


CSS = ".bth .warn{color:var(--warn)}.bth{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin:2px 0 10px}.bign{font-size:30px;font-weight:800;font-variant-numeric:tabular-nums}"
