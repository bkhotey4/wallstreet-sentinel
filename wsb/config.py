"""Configuration: .env secrets + settings.yaml (all tunables live in YAML)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("WSB_DATA_DIR") or ROOT / "data_cache")
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover
        return
    load_dotenv(ROOT / ".env", override=False)


_load_env()


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Settings:
    raw: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.raw[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.raw.get(key, default)

    # ---- universe helpers ----
    @property
    def universe(self) -> Dict[str, Dict[str, str]]:
        return self.raw.get("universe", {})

    def names(self) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for grp in self.universe.values():
            out.update(grp)
        return out

    def group(self, name: str) -> List[str]:
        return list(self.universe.get(name, {}).keys())

    def all_tickers(self) -> List[str]:
        """Universe + every ticker referenced by stress components / portfolio benchmark."""
        tickers = set(self.names().keys())
        for comp in self.raw.get("stress_components", []):
            if comp.get("src") != "px":
                continue
            if comp["series"] != "sectors":
                tickers.add(comp["series"])
            kind = str(comp.get("kind", ""))
            m = re.match(r"(rel:\d+:|ratio:)(.+)$", kind)
            if m:
                tickers.add(m.group(2))
        tickers.add(self.raw.get("crash_odds", {}).get("benchmark", "^GSPC"))
        tickers.add(self.raw.get("portfolio", {}).get("benchmark", "SPY"))
        tickers.update(["SPY", "IEF"])
        tickers.update(self.raw.get("valuation", {}).get("tickers", []))
        return sorted(tickers)


def load_settings(path: Path | None = None) -> Settings:
    p = path or ROOT / "settings.yaml"
    with open(p, encoding="utf-8") as fh:
        return Settings(yaml.safe_load(fh) or {})


SETTINGS = load_settings()


def history_start():
    """Fixed sample start (settings.history_start) so crises such as 2008 never roll out of the backtests;
    falls back to a rolling `history_years` window only when no start date is configured."""
    from datetime import date, timedelta
    v = SETTINGS.get("history_start")
    if v:
        return v if isinstance(v, date) else date.fromisoformat(str(v))
    return date.today() - timedelta(days=365 * int(SETTINGS.get("history_years", 20)))

# ---- secrets / runtime env ----
DISCORD_TOKEN = env("DISCORD_BOT_TOKEN")
DISCORD_GUILD_ID = env("DISCORD_GUILD_ID")          # optional: instant slash-command sync
ALERT_CHANNEL_ID = env("ALERT_CHANNEL_ID")
BRIEFING_CHANNEL_ID = env("BRIEFING_CHANNEL_ID")
OWNER_USER_ID = env("OWNER_USER_ID")                # DM copies of critical alerts

ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = env("ANTHROPIC_MODEL", "claude-sonnet-4-5")
GEMINI_API_KEY = env("GEMINI_API_KEY")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-3.1-pro-preview")
LLM_PRIMARY = env("LLM_PRIMARY", "claude").lower()

FRED_API_KEY = env("FRED_API_KEY")
# SEC asks for "Company contact@domain"; tested: user agents mentioning github.com are refused (403), this form is accepted
SEC_USER_AGENT = env("SEC_USER_AGENT") or "WallStreetSentinel research contact@example.com"   # empty secret → default
