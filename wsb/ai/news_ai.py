"""AI news reader: Claude Haiku (Gemini as fallback) tags each headline with transmission channel(s), direction and severity.

Why: keyword matching cannot tell "bond sell-off deepens" from "bond sell-off fears fade", counts routine data releases
("Bank of Japan Accounts") as risk, and misses headlines that use none of the keywords.  A small model reads every NEW
headline once (cached in SQLite), using structured outputs so the reply is always valid JSON.  When no API key is set or
the call fails, the intelligence-fusion layer silently falls back to keyword matching for the untagged headlines.
Engine order: Claude (ANTHROPIC_API_KEY) -> the configured Gemini models (GEMINI_API_KEY); the first that answers wins."""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List

from ..config import ANTHROPIC_API_KEY, GEMINI_API_KEY, SETTINGS
from ..health import HEALTH
from .. import store

log = logging.getLogger(__name__)
CFG = (SETTINGS.get("intel", {}) or {}).get("ai_classifier", {}) or {}

# schema keys are ASCII; the fusion layer uses the Chinese path names of the shock radar
CHANNEL_KEYS = {"credit": "信用事件", "rates": "利率／債市衝擊", "carry": "套息拆倉", "vol": "波動率／槓桿去化",
                "recession": "景氣衰退", "commodity_geo": "商品／地緣能源"}

SYSTEM = """You classify financial news headlines for a cross-asset risk monitor. For EACH headline decide:

channels — which shock-transmission paths it is evidence about (zero, one or several):
  credit: defaults, bankruptcies, credit spreads, private credit / BDC stress, bank runs, regional banks, loan losses, downgrades
  rates: government-bond selloffs/rallies, yields, term premium, auctions, deficits, central-bank rate path (hawkish/dovish)
  carry: yen / BOJ, FX intervention, dollar squeeze, carry-trade unwinds, EM currency stress, capital flows
  vol: equity selloffs/crashes, volatility spikes, deleveraging, margin calls, hedge-fund losses, liquidations
  recession: jobs, layoffs, consumer weakness, PMIs, earnings/guidance warnings, growth slowdown
  commodity_geo: oil/gas/commodities, wars, sanctions, tariffs, export controls, geopolitical escalation
direction — "risk" if it signals rising stress or escalation, "relief" if stress is easing (ceasefire, rescue, rally,
  cooling inflation, rate cuts that calm markets), "neutral" if it is informational with no clear direction.
severity — 0 routine/noise (scheduled data releases with no surprise, previews, opinion columns, single-stock news with
  no macro read-through), 1 minor, 2 notable for the asset class, 3 major market-moving / systemic.

Judge only from the headline text. Return one entry per headline using its id."""

SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "channels": {"type": "array", "items": {"type": "string", "enum": list(CHANNEL_KEYS)}},
                    "direction": {"type": "string", "enum": ["risk", "relief", "neutral"]},
                    "severity": {"type": "integer", "enum": [0, 1, 2, 3]},
                },
                "required": ["id", "channels", "direction", "severity"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


def _gemini_schema(node):
    """Gemini's response_json_schema: same shape, integer range instead of an integer enum, no additionalProperties."""
    if isinstance(node, dict):
        out = {k: _gemini_schema(v) for k, v in node.items() if k != "additionalProperties"}
        if out.get("type") == "integer" and "enum" in out:
            vals = out.pop("enum")
            out.update(minimum=min(vals), maximum=max(vals))
        return out
    if isinstance(node, list):
        return [_gemini_schema(x) for x in node]
    return node


GEMINI_SCHEMA = _gemini_schema(SCHEMA)


class NewsClassifier:
    def __init__(self) -> None:
        self.tags: Dict[str, Dict] = store.news_tags_load(days=3)
        self.ts = 0.0
        self._client = None

    @property
    def enabled(self) -> bool:
        return bool(ANTHROPIC_API_KEY or GEMINI_API_KEY) and bool(CFG.get("enabled", True))

    @property
    def engine(self) -> str:
        return "claude" if ANTHROPIC_API_KEY else "gemini" if GEMINI_API_KEY else "none"

    def _api(self):
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY, timeout=90.0, max_retries=2)
        return self._client

    async def classify(self, items) -> int:
        """Tag the newest untagged headlines (one call, ≤ max_per_call).  Returns how many were tagged."""
        if not self.enabled:
            return 0
        todo = [it for it in sorted(items, key=lambda i: -i.ts) if it.uid not in self.tags][:int(CFG.get("max_per_call", 80))]
        if not todo:
            return 0
        listing = "\n".join(f"{k}|{it.title[:220]}" for k, it in enumerate(todo))
        user = f"Headlines (id|title):\n{listing}"
        rows, used = None, ""
        if ANTHROPIC_API_KEY:
            rows, used = await self._claude(user, len(todo)), "claude"
        if rows is None and GEMINI_API_KEY:
            rows, used = await self._gemini(user)
        if rows is None:
            return 0
        fresh: Dict[str, Dict] = {}
        for r in rows:
            k = r.get("id")
            if not isinstance(k, int) or not 0 <= k < len(todo):
                continue
            try:
                d, sev = r["direction"], int(r["severity"])
            except (KeyError, TypeError, ValueError):
                continue
            if d not in ("risk", "relief", "neutral"):
                continue
            fresh[todo[k].uid] = {"ch": [CHANNEL_KEYS[c] for c in dict.fromkeys(r.get("channels") or []) if c in CHANNEL_KEYS],
                                  "dir": d, "sev": max(0, min(3, sev))}
        self.tags.update(fresh)
        store.news_tags_save(fresh)
        self.ts = time.time()
        HEALTH.ok("news_ai", len(fresh), every=SETTINGS["refresh"]["news"])
        log.info("news AI (%s) tagged %d/%d headlines", used, len(fresh), len(todo))
        return len(fresh)

    async def _claude(self, user: str, n: int):
        import anthropic
        every = SETTINGS["refresh"]["news"]
        try:
            msg = await self._api().messages.create(
                model=CFG.get("model", "claude-haiku-5-5"),
                max_tokens=int(CFG.get("max_tokens", 12000)),
                system=SYSTEM,
                output_config={"effort": CFG.get("effort", "low"),
                               "format": {"type": "json_schema", "schema": SCHEMA}},
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.RateLimitError as e:
            HEALTH.fail("news_ai:claude", "429", every=every)
            log.warning("news AI (claude) rate-limited: %s", str(e)[:120])
            return None
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            HEALTH.fail("news_ai:claude", type(e).__name__, every=every)
            log.warning("news AI (claude) failed: %s", str(e)[:200])
            return None
        if msg.stop_reason in ("refusal", "max_tokens"):
            HEALTH.fail("news_ai:claude", msg.stop_reason, every=every)
            log.warning("news AI (claude) stop_reason=%s (batch of %d)", msg.stop_reason, n)
            return None
        log.info("news AI (claude) usage: %s in / %s out tokens", msg.usage.input_tokens, msg.usage.output_tokens)
        return self._parse(next((b.text for b in msg.content if b.type == "text"), ""), "claude")

    async def _gemini(self, user: str):
        from google import genai
        from google.genai import types
        from .llm import GEMINI_MODELS, _cooldown
        every = SETTINGS["refresh"]["news"]
        if getattr(self, "_gem", None) is None:
            self._gem = genai.Client(api_key=GEMINI_API_KEY)
        models = [m for m in ([CFG.get("gemini_model")] + GEMINI_MODELS) if m]
        for m in dict.fromkeys(models):
            if _cooldown.get(f"gemini:{m}", 0) > time.time():
                continue
            try:
                r = await self._gem.aio.models.generate_content(
                    model=m, contents=user,
                    config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.0,
                                                       response_mime_type="application/json",
                                                       response_json_schema=GEMINI_SCHEMA,
                                                       automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
            except Exception as e:  # noqa: BLE001  (google-genai raises its own error classes per transport)
                log.warning("news AI (gemini:%s) failed: %s", m, str(e)[:160])
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    _cooldown[f"gemini:{m}"] = time.time() + 600
                continue
            rows = self._parse(r.text or "", f"gemini:{m}")
            if rows is not None:
                HEALTH.ok("news_ai:gemini", len(rows), every=every)
                return rows, f"gemini:{m}"
        HEALTH.fail("news_ai:gemini", "all models failed", every=every)
        return None, ""

    @staticmethod
    def _parse(text: str, who: str):
        try:
            rows = json.loads(text)["items"]
            return rows if isinstance(rows, list) else None
        except (ValueError, KeyError, TypeError) as e:
            log.warning("news AI (%s) returned unparsable output: %s", who, e)
            return None

    async def classify_all(self, items, max_batches: int = 0) -> int:
        """Keep calling classify() until every headline is tagged or `max_batches` calls were made (startup / site build:
        a fresh process would otherwise read only one batch and leave most headlines to keyword matching)."""
        max_batches = max_batches or int(CFG.get("bootstrap_batches", 4))
        total = 0
        for _ in range(max_batches):
            n = await self.classify(items)
            total += n
            if n == 0 or all(it.uid in self.tags for it in items):
                break
        return total

    def coverage(self, items) -> float:
        return sum(1 for it in items if it.uid in self.tags) / len(items) if items else 0.0
