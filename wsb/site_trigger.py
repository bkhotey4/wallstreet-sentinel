"""Kick the public site's GitHub Actions build from the bot (workflow_dispatch).

Why: GitHub's own cron is best-effort — in practice the "hourly" schedule ran 3–5 times a day with gaps up to 10 h.
Dispatch events (like pushes) start right away, so the 24/7 bot drives the cadence instead:
  • every `hourly_minutes` → full build (whole-market scan)
  • the moment a RISK alert fires (SSI level cross, intraday danger, playbook stage up, VIX inversion, shock path…)
    → fast build (no whole-market scan, ~5 min) so the page never lags a deteriorating market
Needs GITHUB_SITE_TOKEN in .env: a fine-grained token limited to the site repo with Actions: Read and write."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from .config import SETTINGS, env
from .data import http
from .health import HEALTH
from . import store

log = logging.getLogger(__name__)
CFG = SETTINGS.get("site_trigger", {}) or {}
API = "https://api.github.com"


class SiteTrigger:
    def __init__(self) -> None:
        self.repo = CFG.get("repo", "bkhotey4/wallstreet-sentinel")
        self.workflow = CFG.get("workflow", "update.yml")
        self.ref = CFG.get("ref", "main")
        self.token = env("GITHUB_SITE_TOKEN")

    @property
    def enabled(self) -> bool:
        return bool(CFG.get("enabled", True)) and bool(self.token)

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"}

    # ------------------------------------------------------------------ decision rules (pure, tested)
    @staticmethod
    def gap_ok(last: Optional[dict], min_gap_min: float, now: Optional[float] = None) -> bool:
        return not last or (now or time.time()) - float(last.get("ts", 0)) >= min_gap_min * 60

    @staticmethod
    def running_is_fresh(runs: list, max_age_min: float, now: Optional[datetime] = None) -> bool:
        """True when a build is already in progress and started less than `max_age_min` ago (it will carry data
        about as fresh as a new one would — dispatching again would only cancel it)."""
        now = now or datetime.now(timezone.utc)
        for r in runs:
            try:
                t = datetime.strptime(r["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError, TypeError):
                continue
            if (now - t).total_seconds() < max_age_min * 60:
                return True
        return False

    # ------------------------------------------------------------------ token expiry (GitHub sends the date in a header)
    @staticmethod
    def parse_expiry(header: Optional[str]) -> Optional[datetime]:
        """'2027-10-12 15:34:56 UTC' → aware datetime; None when absent (token without expiration) or unparsable."""
        if not header:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S UTC", "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                d = datetime.strptime(header.strip(), fmt)
                return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    @staticmethod
    def expiry_stage(days_left: float) -> Optional[str]:
        """Which reminder applies: 'expired' | '1d' | '7d' | '14d' | '30d' | None (nothing yet)."""
        if days_left < 0:
            return "expired"
        for t in (1, 7, 14, 30):
            if days_left <= t:
                return f"{t}d"
        return None

    async def token_expiry(self) -> Tuple[Optional[datetime], Optional[str]]:
        """(expiry, error).  expiry None with no error = token never expires."""
        try:
            s = await http.session()
            async with s.get(f"{API}/user", headers=self._headers(), timeout=20) as r:
                if r.status == 401:
                    return None, "HTTP 401（token 無效或已過期）"
                return self.parse_expiry(r.headers.get("github-authentication-token-expiration")), None
        except Exception as e:  # noqa: BLE001
            return None, f"連線失敗：{e}"

    # ------------------------------------------------------------------ GitHub calls
    async def in_progress(self) -> list:
        try:
            d = await http.get(f"{API}/repos/{self.repo}/actions/runs", headers=self._headers(),
                               params={"status": "in_progress", "per_page": 3}, retries=0, timeout=20)
            return list((d or {}).get("workflow_runs", []))
        except Exception as e:  # noqa: BLE001
            log.debug("site trigger: cannot list runs: %s", e)
            return []

    async def dispatch(self, reason: str, fast: bool = False, force: bool = False) -> Tuple[bool, str]:
        """Returns (dispatched, message).  Rate-limited by min_gap and skipped when a fresh build is already running."""
        if not CFG.get("enabled", True):
            return False, "site_trigger 已停用（settings.yaml）"
        if not self.token:
            return False, "未設定 GITHUB_SITE_TOKEN（.env），無法觸發網站建置"
        last = store.kv_get("site_trigger_last")
        if not force and not self.gap_ok(last, float(CFG.get("min_gap_minutes", 20))):
            return False, f"距上次觸發不到 {CFG.get('min_gap_minutes', 20)} 分鐘（{last.get('reason')}），略過"
        if not force and self.running_is_fresh(await self.in_progress(), float(CFG.get("skip_if_running_minutes", 8))):
            return False, "已有建置在進行中（剛開始不久），略過"
        url = f"{API}/repos/{self.repo}/actions/workflows/{self.workflow}/dispatches"
        body = {"ref": self.ref, "inputs": {"fast": "true" if fast else "false"}}
        try:
            s = await http.session()
            async with s.post(url, headers=self._headers(), json=body, timeout=20) as r:
                status = r.status
                txt = (await r.text())[:200]
        except Exception as e:  # noqa: BLE001
            HEALTH.fail("site_trigger", type(e).__name__, every=3600)
            return False, f"GitHub 連線失敗：{e}"
        if status == 204:
            store.kv_set("site_trigger_last", {"ts": time.time(), "reason": reason, "fast": fast})
            HEALTH.ok("site_trigger", 1, every=3600)
            log.info("site build dispatched (%s, fast=%s)", reason, fast)
            return True, f"已觸發網站{'快速' if fast else '完整'}建置（{reason}），約 {'5' if fast else '15–20'} 分鐘後更新"
        hint = {401: "token 無效或過期", 403: "token 缺少 Actions: Read and write 權限",
                404: "找不到 repo/workflow，或 token 未授權此 repo", 422: "ref 或 inputs 不符"}.get(status, "")
        HEALTH.fail("site_trigger", f"HTTP {status}", every=3600)
        log.warning("site build dispatch failed: HTTP %s %s %s", status, hint, txt)
        return False, f"GitHub 回應 HTTP {status}{'：' + hint if hint else ''}"


TRIGGER = SiteTrigger()
