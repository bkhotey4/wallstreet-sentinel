"""Shared test setup (2026-11-26): the unattended routines ran tests as `PYTHONIOENCODING=utf-8 WSB_AI_OFF=0 python -m tests.x`,
and the env prefix is not on the allow-list, so every run stopped at a permission prompt.  The same setup lives here, so a
bare `.venv/Scripts/python -m tests.x` works: AI code paths on (the local .env turns them off for the bot; load_dotenv does
not override a value set here), and UTF-8 output on a cp950 console."""
import os
import sys

os.environ.setdefault("WSB_AI_OFF", "0")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
