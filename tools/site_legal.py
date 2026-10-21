"""條款與隱私 — data sources and their owners, terms of use, privacy policy (the Google sync needs one)."""
from __future__ import annotations

from tools.sitekit import T, card

REPO = "https://github.com/bkhotey4/wallstreet-sentinel"

SOURCES = [
    ("Yahoo Finance", "股價、指數、匯率、期貨、ETF（延遲報價）", "Prices, indices, FX, futures, ETFs (delayed)", "Yahoo Inc. 及其資料供應商"),
    ("FRED（聖路易聯邦準備銀行）", "總經、利率、流動性序列", "Macro, rates, liquidity series", "各序列原始發布機構"),
    ("ICE BofA 債券指數（經 FRED）", "信用利差：本站只顯示百分位、變化方向與分數，不顯示原始數值", "Credit spreads: percentiles, directions and scores only — no raw values", "© ICE Data Indices, LLC"),
    ("Moody's（經 FRED）", "Baa 公司債利差：同上，只顯示衍生指標", "Baa spread: derived figures only", "© Moody's"),
    ("CBOE", "選擇權延遲報價（隱含波動、Gamma）", "Delayed option quotes (implied moves, gamma)", "Cboe Global Markets"),
    ("Nasdaq", "財報日曆、經濟日曆、EPS 結果", "Earnings & economic calendars, EPS results", "Nasdaq, Inc."),
    ("SEC EDGAR", "財報 XBRL、8-K、13F、Form 4（美國政府公開資料）", "XBRL financials, 8-K, 13F, Form 4 (US government public data)", "U.S. SEC"),
    ("臺灣證券交易所、證券櫃檯買賣中心", "台股報價、月營收、法人買賣超（政府資料開放授權）", "Taiwan quotes, monthly revenue, institutional flows (open government data)", "TWSE / TPEx"),
    ("FINRA、TreasuryDirect", "融資餘額、美債標售（美國公開資料）", "Margin debt, Treasury auctions", "FINRA / U.S. Treasury"),
    ("公開新聞 RSS（含 Google 新聞）", "只列標題並連回原網站；不轉載內文；新聞只當背景，不進入任何風險計算", "Headlines linking to the source only; never used in risk scores", "各新聞媒體"),
    ("AI 模型（Google Gemini、Anthropic Claude）", "依本頁公開數據自動撰寫市場評論，可能有誤", "Automated commentary from this page’s public data; may contain errors", "—"),
]


def sec_terms(eng) -> str:
    rows = "".join(f'<tr><td><b>{T(n, n)}</b></td><td>{T(zh, en)}</td><td class="small muted">{T(o, o)}</td></tr>' for n, zh, en, o in SOURCES)
    body = (f'<table class="mini"><thead><tr><th>{T("來源", "Source")}</th><th>{T("用途", "Used for")}</th><th>{T("權利人", "Owner")}</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
            f'<h3>{T("使用條款", "Terms of use")}</h3><ul class="small">'
            f'<li>{T("本站是個人、非商業的研究專案：完全免費、沒有廣告、不收費、不提供付費服務或會員群組。", "A personal, non-commercial research project: free, no ads, no paid services.")}</li>'
            f'<li>{T("本站內容是數據整理與規則計算的結果，「不是投資建議，也不是任何證券的推介」；站主不是持牌的證券投資顧問。所有分數、訊號、機率、範圍都只描述數據，不保證未來，請自行判斷並承擔投資風險。", "Data and rule-based calculations — not investment advice or a recommendation; the author is not a licensed adviser.")}</li>'
            f'<li>{T("報價多為延遲資料（約 15 分鐘以上），可能有錯誤或中斷；請以券商與官方公告為準。", "Quotes are delayed and may contain errors; rely on your broker and official sources.")}</li>'
            f'<li>{T("各項資料的權利屬於上表所列的權利人。本站只在呈現分析所需的範圍內引用，並依各來源條款標註出處；有版權限制的指數只顯示衍生指標。", "Data belongs to the owners above; licensed indices are shown as derived figures only.")}</li>'
            f'<li>{T("如果你是資料或內容的權利人，認為本站的使用不妥，請在 GitHub 開 issue 告知，收到後會儘快移除或調整：", "Rights holders: open a GitHub issue and the content will be removed or adjusted promptly: ")}'
            f'<a href="{REPO}/issues" target="_blank" rel="noopener">{REPO}/issues</a></li>'
            f'<li>{T("程式碼公開以便檢視，但未授權重製或商業使用（保留所有權利）。", "Source is public for review; all rights reserved.")}</li></ul>')
    return card("資料來源與使用條款", "Data sources & terms of use", body, "wide")


def sec_privacy(eng) -> str:
    items = [
        ("本站沒有後端伺服器、沒有帳號系統，也不使用追蹤 Cookie、分析工具或廣告。網站本身是 GitHub Pages 上的靜態網頁。",
         "No server, no accounts, no tracking cookies, analytics or ads — a static site on GitHub Pages."),
        ("「我的持股」的股數、成本、現金只存在你自己這個瀏覽器的本機儲存空間（localStorage），不會上傳到本站或 GitHub。所有計算（損益、規則檢查、因子曝險、營收曝險、事件雷達）都在你的瀏覽器裡完成。",
         "Holdings live only in your browser’s local storage; every calculation runs in your browser."),
        ("選擇「用 Google 同步」時，網頁會向 Google 申請 drive.appdata 權限：只能讀寫你自己 Google 雲端硬碟裡一個專屬於本網頁、你看不到的隱藏資料夾，用來存同一份持股檔。本網頁看不到你雲端硬碟裡的其他任何檔案，站主也看不到這個資料夾。",
         "Google sync requests only drive.appdata: a hidden app folder in YOUR Drive holding the same file. No other Drive files are visible, and the author cannot see the folder."),
        ("Google 登入權杖只在你的瀏覽器裡使用，用來存取上述資料夾，不會傳給本站或任何第三方。",
         "The Google token is used only in your browser for that folder."),
        ("刪除資料：在「我的持股」按「清除全部」刪除本機資料；到 Google 帳戶 → 安全性 → 第三方存取權，移除本網頁的存取權；雲端硬碟的隱藏資料可在 Google 雲端硬碟 → 設定 → 管理應用程式中刪除。",
         "To delete: ‘Clear all’ on My holdings; remove access in your Google account; delete hidden app data in Drive → Settings → Manage apps."),
        ("網站會在你的瀏覽器裡快取公開頁面（Service Worker），讓網頁更快、可以離線開啟；快取內容只有公開資料。",
         "A service worker caches the public pages in your browser."),
    ]
    body = '<ul class="small">' + "".join(f"<li>{T(zh, en)}</li>" for zh, en in items) + "</ul>"
    body += f'<p class="note">{T("隱私相關問題同樣可以在 GitHub 開 issue。", "Privacy questions: open a GitHub issue.")} <a href="{REPO}/issues" target="_blank" rel="noopener">{REPO}/issues</a></p>'
    return card("隱私權政策", "Privacy policy", body, "wide")
