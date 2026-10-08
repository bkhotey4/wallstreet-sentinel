"""Shared async HTTP client with retries + polite headers."""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

import aiohttp

log = logging.getLogger(__name__)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

_session: Optional[aiohttp.ClientSession] = None


async def session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=25),
            headers={"User-Agent": UA, "Accept": "*/*"},
        )
    return _session


async def get(url: str, *, kind: str = "json", headers: dict | None = None,
              params: dict | None = None, retries: int = 2, timeout: float = 25) -> Any:
    """kind: json | text | bytes"""
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            s = await session()
            async with s.get(url, headers=headers, params=params,
                             timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                if r.status == 429:
                    raise aiohttp.ClientResponseError(r.request_info, (), status=429, message="rate limited")
                r.raise_for_status()
                if kind == "json":
                    return await r.json(content_type=None)
                if kind == "bytes":
                    return await r.read()
                return await r.text()
        except Exception as e:  # noqa: BLE001
            last = e
            if attempt < retries:
                await asyncio.sleep(1.5 * (attempt + 1))
    if isinstance(last, asyncio.TimeoutError):
        raise TimeoutError(f"timeout after {timeout}s: {url.split('?')[0]}")
    raise last  # type: ignore[misc]


async def close() -> None:
    if _session and not _session.closed:
        await _session.close()
