"""2026-11-26: UTF-8 output for every `python -m tools.x`, so unattended routines need no PYTHONIOENCODING=… prefix (not on
the allow-list; a cp950 console crashed daily_audit on ⚠ after it had written its report)."""
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001  (a redirected or wrapped stream)
        pass
