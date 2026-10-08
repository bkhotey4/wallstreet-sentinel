"""Optional read-only dashboard served on 127.0.0.1 only (settings.yaml → web.enabled). No secrets, no write actions."""
from __future__ import annotations

import html
import logging
import time
from datetime import datetime

from .config import SETTINGS
from .health import HEALTH
from . import store

log = logging.getLogger(__name__)


def render(engine) -> str:
    esc = html.escape
    st = engine.stress
    pb = engine.playbook or {}
    rows = []
    if st:
        rows.append(("壓力指數 SSI", f"{st.score:.0f}　{esc(str(st.label))}"))
    if pb:
        rows.append(("風險劇本", f"{esc(str(pb.get('emoji', '')))} {esc(str(pb.get('name', '')))}（{pb.get('points', 0)} 分）"))
        for w in (pb.get("why") or [])[:6]:
            rows.append(("　依據", esc(str(w[1] if isinstance(w, (list, tuple)) and len(w) > 1 else w))))
    pf = engine.portfolio or {}
    if pf.get("total_value"):
        rows.append(("持倉市值", f"{pf['total_value']:,.0f}"))
    body = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    health = "".join(
        f"<tr><th>{esc(s.name)}</th><td class='{s.state}'>{s.state}</td>"
        f"<td>{(s.age or 0) / 60:.0f} 分鐘前</td></tr>" for s in sorted(HEALTH.sources.values(), key=lambda x: x.name))
    alerts = "".join(
        f"<tr><td>{datetime.fromtimestamp(ts):%m/%d %H:%M}</td><td>{esc(str(sv))}</td><td>{esc(str(t))}</td></tr>"
        for ts, sv, t in store.recent_alerts(48)[:15])
    return f"""<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta http-equiv="refresh" content="60">
<title>WallStreet Sentinel</title><style>
body{{font-family:system-ui,"Microsoft JhengHei",sans-serif;background:#0b1020;color:#e6e9f2;margin:24px;max-width:900px}}
h1{{font-size:22px}}h2{{font-size:16px;color:#8fa1c7;margin-top:28px}}table{{border-collapse:collapse;width:100%}}
th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #1d2744;font-size:14px}}th{{color:#8fa1c7;font-weight:500;width:30%}}
.ok{{color:#3ddc97}}.degraded,.stale{{color:#ffb454}}.down{{color:#ff6b6b}}.pending{{color:#8fa1c7}}
</style><h1>WallStreet Sentinel　<small style="color:#8fa1c7">{datetime.now():%Y-%m-%d %H:%M:%S}（每分鐘自動更新）</small></h1>
<h2>風險總覽</h2><table>{body or '<tr><td>資料載入中…</td></tr>'}</table>
<h2>資料源健康</h2><table>{health}</table>
<h2>最近 48 小時警報</h2><table>{alerts or '<tr><td>無</td></tr>'}</table></html>"""


async def start(engine):
    """Bind 127.0.0.1 only. Returns the runner (or None when disabled / port busy)."""
    cfg = SETTINGS.get("web", {}) or {}
    if not cfg.get("enabled", False):
        return None
    from aiohttp import web
    app = web.Application()

    async def index(_):
        return web.Response(text=render(engine), content_type="text/html", charset="utf-8")

    async def health(_):
        return web.json_response({"ts": time.time(), "sources": {k: v.state for k, v in HEALTH.sources.items()}})
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    try:
        await web.TCPSite(runner, "127.0.0.1", int(cfg.get("port", 8787))).start()
    except OSError as e:
        log.warning("web dashboard not started: %s", e)
        await runner.cleanup()
        return None
    log.info("web dashboard on http://127.0.0.1:%s", cfg.get("port", 8787))
    return runner
