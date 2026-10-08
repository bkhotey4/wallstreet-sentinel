"""LLM router with automatic failover:
Claude → Gemini (several models, cheapest last) → OpenAI.
Order can be changed with LLM_PRIMARY. Errors are summarised, never dumped raw."""
from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Awaitable, Callable, List, Tuple

from ..config import (ANTHROPIC_API_KEY, ANTHROPIC_MODEL, GEMINI_API_KEY, GEMINI_MODEL, LLM_PRIMARY, env)
from ..health import HEALTH

log = logging.getLogger(__name__)
_anthropic = None
_gemini = None

GEMINI_MODELS = [m for m in dict.fromkeys(
    [GEMINI_MODEL] + [x.strip() for x in env("GEMINI_FALLBACK_MODELS", "gemini-3.1-flash-lite,gemini-2.5-flash,gemini-2.0-flash").split(",")]) if m]
OPENAI_API_KEY = env("OPENAI_API_KEY")
OPENAI_MODEL = env("OPENAI_MODEL", "gpt-4o")

TOTAL_BUDGET_S = 480                                # whole failover chain must finish within 8 minutes
# model → unix time until which it is skipped (quota / 404)
_cooldown: dict = {}


async def _claude(system: str, user: str, max_tokens: int) -> str:
    global _anthropic
    from anthropic import AsyncAnthropic
    if _anthropic is None:
        _anthropic = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    msg = await _anthropic.messages.create(
        model=ANTHROPIC_MODEL, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}], temperature=0.3)
    txt = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    if getattr(msg, "stop_reason", "") == "max_tokens":
        txt += "\n\n（輸出達長度上限，內容可能不完整）"
    return txt


def _gem_factory(model: str) -> Callable[[str, str, int], Awaitable[str]]:
    async def _gem(system: str, user: str, max_tokens: int) -> str:
        global _gemini
        from google import genai
        from google.genai import types
        if _gemini is None:
            _gemini = genai.Client(api_key=GEMINI_API_KEY)
        r = await _gemini.aio.models.generate_content(
            model=model, contents=user,
            config=types.GenerateContentConfig(system_instruction=system, temperature=0.3,
                                               max_output_tokens=max_tokens * 2))   # headroom for "thinking" tokens
        return r.text or ""
    return _gem


async def _openai(system: str, user: str, max_tokens: int) -> str:
    from ..data import http
    s = await http.session()
    async with s.post("https://api.openai.com/v1/chat/completions",
                      headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                      json={"model": OPENAI_MODEL, "temperature": 0.3, "max_tokens": max_tokens,
                            "messages": [{"role": "system", "content": system},
                                         {"role": "user", "content": user}]}) as r:
        js = await r.json(content_type=None)
        if r.status >= 400:
            raise RuntimeError(f"{r.status} {js.get('error', {}).get('message', '')[:200]}")
        return js["choices"][0]["message"]["content"] or ""


def _short(e: Exception) -> str:
    t = str(e)
    if "no credits" in t.lower():
        return "帳戶無餘額(429)"
    if "RESOURCE_EXHAUSTED" in t or " 429" in t or t.startswith("429"):
        return "額度不足(429)"
    if "503" in t or "UNAVAILABLE" in t:
        return "伺服器忙碌(503)"
    if "NOT_FOUND" in t or "404" in t:
        return "模型不存在(404)"
    if "401" in t or "invalid" in t.lower() and "key" in t.lower():
        return "金鑰無效(401)"
    if isinstance(e, asyncio.TimeoutError):
        return "逾時"
    return re.sub(r"\s+", " ", t)[:80]


def _engines() -> List[Tuple[str, Callable]]:
    groups = {"claude": [], "gemini": [], "openai": []}
    if ANTHROPIC_API_KEY:
        groups["claude"].append((f"claude:{ANTHROPIC_MODEL}", _claude))
    if GEMINI_API_KEY:
        groups["gemini"] += [(f"gemini:{m}", _gem_factory(m)) for m in GEMINI_MODELS]
    if OPENAI_API_KEY:
        groups["openai"].append((f"openai:{OPENAI_MODEL}", _openai))
    order = [LLM_PRIMARY] + [k for k in ("claude", "gemini", "openai") if k != LLM_PRIMARY]
    return [e for k in order if k in groups for e in groups[k]]


async def complete(system: str, user: str, max_tokens: int = 3500) -> Tuple[str, str]:
    """Returns (text, engine_used)."""
    engines = _engines()
    if not engines:
        return "⚠️ 未設定任何 AI 金鑰（ANTHROPIC / GEMINI / OPENAI），AI 研判停用；量化數據不受影響。", "none"
    errors = []
    deadline = time.time() + TOTAL_BUDGET_S        # keep well inside Discord's 15-min interaction window
    for name, fn in engines:
        if _cooldown.get(name, 0) > time.time():
            continue
        if deadline - time.time() < 20:
            errors.append("時間預算用盡")
            break
        try:
            for attempt in range(3):                 # 503 "high demand" is transient → back off & retry
                try:
                    txt = await asyncio.wait_for(fn(system, user, max_tokens),
                                                 timeout=min(150, max(10, deadline - time.time())))
                    break
                except Exception as e:  # noqa: BLE001
                    if ("503" in str(e) or "UNAVAILABLE" in str(e)) and attempt < 2:
                        log.info("LLM %s busy (503), retry %d", name, attempt + 1)
                        await asyncio.sleep(8 * (attempt + 1))
                        continue
                    raise
            if txt.strip():
                HEALTH.ok(f"llm:{name}", 1, every=86400)
                return txt.strip(), name.split(":", 1)[1]
        except Exception as e:  # noqa: BLE001
            reason = _short(e)
            errors.append(f"{name.split(':',1)[1]} {reason}")
            log.warning("LLM %s failed: %s", name, str(e)[:300])
            HEALTH.fail(f"llm:{name}", reason, every=86400)
            if "429" in reason:
                _cooldown[name] = time.time() + 600          # skip this model 10 min
            elif "404" in reason or "401" in reason or "無餘額" in reason:
                _cooldown[name] = time.time() + 6 * 3600
    return ("⚠️ AI 研判暫時無法產生（" + "；".join(errors or ["全部引擎冷卻中"]) +
            "）。量化數據與警報不受影響，稍後會自動重試。"), "none"
