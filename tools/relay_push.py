"""PC → public site data relay that uploads by itself (2026-11-26).

The cloud build is refused by a few official sources the PC reads fine: 公開資訊觀測站 revenue and 法說會, TWSE chips and
margin pages, 主計總處 stat pages, Invesco's QQQ flows.  tools.relay_seeds / etf_flows.write_seed copy the PC's clean rows
into research_feed/*_seed.json.  Until today those files reached the site only when the 10:40 daily task remembered to
commit them, so on 11-26 the ETF flows card sat at 11-23 for 37 hours (the seed was written locally and never pushed).

This module writes the seeds into its own shallow clone of the public repo (data_cache/relay_repo), commits only
research_feed/*_seed.json files that parse as JSON, and pushes.  Nothing else in that clone is ever edited, so it never
touches a working tree someone (or another session) is editing.  tools/sec_push launches it on the PC every EVERY seconds
between 06:00 and 23:59 Taipei; the seeds keep their own fetch time, so relayed rows never look fresher than they are.
Run: python -m tools.relay_push"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wsb.config import DATA_DIR  # noqa: E402

MAIN = ROOT.parent / "wallstreet-sentinel"
CLONE = DATA_DIR / "relay_repo"
STATE = DATA_DIR / "relay_push.json"
LOG = DATA_DIR / "relay_push.log"
EVERY = 3 * 3600
HOURS = range(6, 24)                    # Taipei hours a run may start (official pages publish in the day)
RUNNING_MAX = 30 * 60                   # a run older than this is treated as dead
SEED = re.compile(r"research_feed/[a-z0-9_]+_seed\.json")


def _tpe_hour(now: float) -> int:
    return datetime.fromtimestamp(now, timezone(timedelta(hours=8))).hour


def load() -> Dict:
    try:
        return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _save(d: Dict) -> None:
    STATE.write_text(json.dumps(d, ensure_ascii=False, default=str), encoding="utf-8")


def due(st: Dict, now: float) -> bool:
    """Pure: start a run?  Not while one is running (unless it is older than RUNNING_MAX), not at night."""
    if _tpe_hour(now) not in HOURS:
        return False
    started = float(st.get("started") or 0)
    if st.get("running") and now - started < RUNNING_MAX:
        return False
    return now - started >= EVERY


def keep(paths: List[str]) -> List[str]:
    """Pure: only seed files under research_feed may be committed."""
    return [p for p in paths if SEED.fullmatch(p)]


def _empty(v) -> bool:
    return v is None or v == {} or v == [] or v == ""


def merge_empty(old, new):
    """Pure: a part that came back empty this run (the official page had not published yet, or a fetch failed at night:
    11-26 22:47 the large-trader and margin-ratio parts were blank) keeps the last good value; each part carries its own
    date, so the card still shows how old it is.  Only top-level keys and one level below are merged."""
    if not isinstance(old, dict) or not isinstance(new, dict):
        return new
    out = dict(new)
    for k, ov in old.items():
        nv = new.get(k)
        if _empty(nv) and not _empty(ov):
            out[k] = ov
        elif isinstance(nv, dict) and isinstance(ov, dict):
            out[k] = {**nv, **{kk: vv for kk, vv in ov.items() if _empty(nv.get(kk)) and not _empty(vv)}}
    return out


def git(*a: str, cwd: Path = CLONE, check: bool = True, timeout: int = 180) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *a], cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(a)}: {(r.stderr or r.stdout).strip()[:300]}")
    return r


def prepare() -> None:
    if not (CLONE / ".git").is_dir():
        url = git("remote", "get-url", "origin", cwd=MAIN).stdout.strip()
        git("clone", "-q", "--depth", "5", url, str(CLONE), cwd=DATA_DIR, timeout=600)
    git("fetch", "-q", "--depth", "5", "origin", "main")
    git("reset", "-q", "--hard", "origin/main")        # this clone is ours alone: nobody edits files in it


def write(feed: Path) -> Dict:
    from tools import relay_seeds as RS
    out = RS.main(feed)
    try:
        from wsb.data import etf_flows as EF
        out["etf"] = EF.write_seed(feed / "etf_flows_seed.json")
    except Exception as e:  # noqa: BLE001
        out["etf"] = {"error": str(e)}
    try:                                                # 11-26: TrendForce press list (cloud reach unknown)
        import asyncio
        from wsb.data import research_press as RPR
        asyncio.run(RPR.refresh())
        out["respress"] = len((RPR.write_seed(feed / "research_press_seed.json") or {}).get("items") or [])
        from wsb.data import mem_spot as MSP
        asyncio.run(MSP.refresh())
        out["memspot"] = len((MSP.write_seed(feed / "mem_spot_seed.json") or {}).get("snap") or {})
        from wsb.data import freight as FRT
        asyncio.run(FRT.refresh())
        out["freight"] = len((FRT.write_seed(feed / "freight_seed.json") or {}).get("scfi") or [])
    except Exception as e:  # noqa: BLE001
        out["respress"] = {"error": str(e)}
    return out


def changed() -> List[str]:
    s = git("status", "--porcelain", "--", "research_feed").stdout
    return [ln[3:].strip().strip('"') for ln in s.splitlines() if ln.strip()]


def run(push: bool = True) -> Dict:
    now = time.time()
    st = load()
    _save({**st, "running": True, "started": now, "pid": os.getpid()})
    res: Dict = {"started": now}
    try:
        prepare()
        res["seeds"] = write(CLONE / "research_feed")
        paths = changed()
        bad = [p for p in paths if p not in keep(paths)]
        if bad:                                         # a writer touched something else: never upload it
            git("checkout", "--", *[p for p in bad if (CLONE / p).exists()], check=False)
            res["dropped"] = bad
        paths = keep(paths)
        for p in list(paths):
            try:
                cur = json.loads((CLONE / p).read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                git("checkout", "--", p, check=False)
                paths.remove(p)
                res.setdefault("broken", []).append(p)
                continue
            r = git("show", f"HEAD:{p}", check=False)
            if r.returncode == 0:
                try:
                    merged = merge_empty(json.loads(r.stdout), cur)
                    if merged != cur:
                        (CLONE / p).write_text(json.dumps(merged, ensure_ascii=False), encoding="utf-8")
                        res.setdefault("kept_old", []).append(p)
                except Exception:  # noqa: BLE001
                    pass
        paths = [p for p in paths if p in changed()]     # a file may now equal HEAD again
        res["files"] = paths
        if paths and push:
            git("add", "--", *paths)
            names = "、".join(Path(p).stem.replace("_seed", "") for p in paths)
            stamp = datetime.fromtimestamp(now, timezone(timedelta(hours=8))).strftime("%m-%d %H:%M")
            git("commit", "-q", "-m", f"電腦端接力資料自動上傳（{stamp}）：{names}")
            for i in range(3):
                r = git("push", "-q", "origin", "HEAD:main", check=False)
                if r.returncode == 0:
                    res["pushed"] = len(paths)
                    break
                git("fetch", "-q", "--depth", "5", "origin", "main")
                git("rebase", "-q", "origin/main")       # only seed files differ, and only this job writes them
            else:
                res["error"] = "push refused 3 times: " + (r.stderr or "").strip()[:200]
    except Exception as e:  # noqa: BLE001
        res["error"] = str(e)[:400]
    res["ts"] = time.time()
    _save({"running": False, "started": now, "last": res})
    return res


def launch(now: Optional[float] = None) -> bool:
    """Called from tools.sec_push every few minutes on the PC: start a detached run when due; never waits for it."""
    now = time.time() if now is None else now
    if not due(load(), now):
        return False
    _save({**load(), "running": True, "started": now})
    flags = 0
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    with open(LOG, "a", encoding="utf-8") as log:
        subprocess.Popen([sys.executable, "-X", "utf8", "-m", "tools.relay_push"], cwd=str(ROOT), stdout=log, stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL, creationflags=flags)
    return True


def summary(st: Dict, now: float) -> Optional[str]:
    """For daily_audit / sys_health: say so when uploads stopped (PC off, git refused) — None when fine."""
    last = st.get("last") or {}
    ts = float(last.get("ts") or st.get("started") or 0)
    if last.get("error"):
        return f"電腦端接力資料上傳失敗：{last['error'][:160]}"
    if ts and now - ts > 2 * EVERY + 9 * 3600:
        return f"電腦端接力資料 {(now - ts) / 3600:.0f} 小時沒有上傳（電腦關機或排程沒跑）"
    return None


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, default=str))
