"""積木編號：網站每一張卡片、Discord 每一個指令與推播類型都有固定編號（2026-11-21，使用者：「把網頁跟 discord bot 用個積木並標上編號，
這樣你之後也好整理」）。

規則
  * 網站：「頁碼-卡片碼」，例如 38-02＝第 38 頁的第 2 張卡。頁碼與卡片碼一旦給出就不再改、不重複使用；新頁拿下一個頁碼，
    新卡拿那一頁下一個號碼。卡片用「頁的代號＋標題（數字換成 #）」認，標題裡的數字變了也還是同一張。
  * Discord：指令 D-C01…（wsb/bot/app.py 的 /指令），推播 D-A01…（tools/sec_push.py 裡每一種 *_embed 推播）。
  * 編號表存在 tools/blocks.json。雲端建置不能寫回 repo，所以新編號在建置時依同一份表「算」出來（同樣的輸入每次結果一樣），
    並輸出 site/blocks.json；之後把它存回 tools/blocks.json，就固定下來。
"""
from __future__ import annotations

import html
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)
REG = Path(__file__).resolve().with_name("blocks.json")
ROOT = Path(__file__).resolve().parents[1]
_NUM = re.compile(r"[0-9０-９][0-9０-９,，.]*")


def key_of(page: str, title: str) -> str:
    t = _NUM.sub("#", re.sub(r"\s+", " ", title or "").strip())
    return f"{page}::{t}"


def load(path: Path = REG) -> Dict:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def assign(reg: Dict, page_order: List[str], cards: Dict[str, List[Tuple[str, str, str]]],
           discord: Optional[Dict[str, List[str]]] = None) -> Tuple[Dict, List[str]]:
    """Return (registry with every current block numbered, list of newly numbered keys).  Never renumbers."""
    reg = {"pages": dict(reg.get("pages") or {}), "cards": dict(reg.get("cards") or {}),
           "discord": {k: dict(v) for k, v in (reg.get("discord") or {}).items()}}
    new: List[str] = []
    nxt_page = max([0] + list(reg["pages"].values())) + 1
    for p in page_order:
        if p not in reg["pages"]:
            reg["pages"][p] = nxt_page
            nxt_page += 1
            new.append(f"page {p}")
    for p in page_order:
        pn = reg["pages"][p]
        used = [int(v.split("-")[1]) for k, v in reg["cards"].items() if k.split("::")[0] == p]
        nxt = max([0] + used) + 1
        for _cid, zh, _en in cards.get(p) or []:
            k = key_of(p, zh)
            if k not in reg["cards"]:
                reg["cards"][k] = f"{pn:02d}-{nxt:02d}"
                nxt += 1
                new.append(k)
    for kind, pre in (("commands", "D-C"), ("alerts", "D-A")):
        have = reg["discord"].setdefault(kind, {})
        nxt = max([0] + [int(v[len(pre):]) for v in have.values()]) + 1
        for name in (discord or {}).get(kind) or []:
            if name not in have:
                have[name] = f"{pre}{nxt:02d}"
                nxt += 1
                new.append(f"discord {name}")
    return reg, new


def discord_inventory() -> Dict[str, List[str]]:
    """Slash commands and push types read from the bot's source (read only; nothing in the bot is changed)."""
    out: Dict[str, List[str]] = {"commands": [], "alerts": []}
    try:
        src = (ROOT / "wsb" / "bot" / "app.py").read_text(encoding="utf-8")
        out["commands"] = list(dict.fromkeys(re.findall(r'@tree\.command\(name="([^"]+)"', src)))
    except OSError:
        pass
    try:
        src = (ROOT / "tools" / "sec_push.py").read_text(encoding="utf-8")
        out["alerts"] = list(dict.fromkeys(re.findall(r"^(?:async\s+)?def\s+([a-z0-9_]+_embed)\(", src, re.M)))
    except OSError:
        pass
    return out


def discord_desc() -> Dict[str, str]:
    """name → the command's own description (from app.py) / the push function's first docstring line."""
    d: Dict[str, str] = {}
    try:
        src = (ROOT / "wsb" / "bot" / "app.py").read_text(encoding="utf-8")
        for n, desc in re.findall(r'@tree\.command\(name="([^"]+)",\s*description="([^"]*)"', src):
            d[n] = desc
    except OSError:
        pass
    return d


_H2 = re.compile(r'(<section id="([^"]+)"[^>]*>\s*<h2>)(.*?)(</h2>)', re.S)


def badge(bodies: Dict[str, str], cards: Dict[str, List[Tuple[str, str, str]]], reg: Dict) -> Dict[str, str]:
    """Append the block number to every card's title: <span class="blk">#38-02</span>."""
    out = {}
    for p, h in bodies.items():
        ids = {cid: reg["cards"].get(key_of(p, zh)) for cid, zh, _en in cards.get(p) or []}

        def rep(m):
            b = ids.get(m.group(2))
            if not b:
                return m.group(0)
            return f'{m.group(1)}{m.group(3)} <span class="blk" title="積木編號（整理網站用）">#{b}</span>{m.group(4)}'
        out[p] = _H2.sub(rep, h)
    return out


def inventory_card(reg: Dict, names: Dict[str, Tuple[str, str]], cards: Dict[str, List[Tuple[str, str, str]]]) -> str:
    """積木清單: every page, card, Discord command and push type with its number (on 工具 page)."""
    e = html.escape
    pages = sorted(((n, p) for p, n in reg["pages"].items() if p in names), key=lambda x: x[0])
    rows = []
    for n, p in pages:
        lst = "".join(f'<li><code>#{e(reg["cards"].get(key_of(p, zh), "—"))}</code> {e(zh)}</li>' for _c, zh, _en in cards.get(p) or [])
        rows.append(f'<details class="sgx"><summary><code>{n:02d}</code> {e(names[p][0])}（{len(cards.get(p) or [])} 張）</summary><ul class="small">{lst}</ul></details>')
    desc = discord_desc()
    dc = reg.get("discord") or {}
    cmd = "".join(f'<li><code>{e(v)}</code> /{e(k)}' + (f'<span class="muted">：{e(desc[k])}</span>' if desc.get(k) else "") + "</li>"
                  for k, v in sorted((dc.get("commands") or {}).items(), key=lambda x: x[1]))
    alr = "".join(f'<li><code>{e(v)}</code> {e(k.replace("_embed", ""))}</li>' for k, v in sorted((dc.get("alerts") or {}).items(), key=lambda x: x[1]))
    n_cards = sum(len(v) for v in cards.values())
    body = (f'<p class="rimp"><b>一句話看懂：網站 {len(pages)} 頁、{n_cards} 張卡片，Discord {len(dc.get("commands") or {})} 個指令、'
            f'{len(dc.get("alerts") or {})} 種推播，每一塊都有固定編號。</b></p>'
            '<p class="small">卡片標題右邊的 <code>#38-02</code> 就是編號：38 是第幾頁，02 是那一頁的第幾張。要回報問題或要求修改時，直接說編號最快。'
            '編號一旦給出就不會改；卡片換位置、標題裡的數字變了，編號都一樣。</p>'
            + "".join(rows)
            + f'<details class="sgx"><summary>Discord 指令（{len(dc.get("commands") or {})} 個）</summary><ul class="small">{cmd}</ul></details>'
            + f'<details class="sgx"><summary>Discord 推播類型（{len(dc.get("alerts") or {})} 種）</summary><ul class="small">{alr}</ul></details>'
            '<p class="note">編號表存在程式的 tools/blocks.json；新卡片在下一次建置時自動拿到下一個號碼。Discord 的編號目前列在這裡，訊息本身還沒有顯示編號。</p>')
    from tools.sitekit import card
    return card("積木清單（網站與 Discord 的編號）", "Block index", body, "wide")
