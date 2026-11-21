"""主線追蹤（11-21 盲點檢討）。Run: python -m tests.test_threads"""
import time

from wsb.analytics import threads as T


def test_match_and_view():
    assert T.match("Joint Investigation Report: China is Trying to Get U.S. Companies Addicted to Chinese AI Models") == ["uscn_tech"]
    assert T.match("BIS annual report on bank capital") == [] and T.match("日銀總裁暗示12月升息") == ["japan_yen"]
    now = 1_795_300_000.0
    old = [{"t": f"Huawei chip story {i}", "u": f"https://x/{i}", "s": "A", "ts": now - 86400 * (3 + i)} for i in range(3)]   # ~1.5 per 48 h? no: 3 in 12 days
    new = [{"t": "TSMC tightens China AI chip curbs", "u": "https://x/a", "s": "B", "ts": now - 3600},
           {"t": "Cursor weighs phasing out Chinese AI models", "u": "https://x/b", "s": "C", "ts": now - 7200},
           {"t": "Joint Investigation Report: Chinese AI Models", "u": "https://x/c", "s": "眾議院", "ts": now - 9000, "off": True}]
    arch = T.archive(new + old + [{"t": "dup", "u": "https://x/a", "ts": now}], now, old=[], save=False)
    assert len(arch) == 6
    v = T.view(arch, now)
    u = next(t for t in v["threads"] if t["id"] == "uscn_tech")
    assert u["n48"] == 3 and u["state"] == "升溫" and u["official"] == ["https://x/c"] and u["base"] == 0.5
    assert next(t for t in v["threads"] if t["id"] == "japan_yen")["state"] == "安靜"
    young = T.view(new, now)                                   # 2.5 hours of archive: no baseline → not 升溫, the official one still shows
    assert next(t for t in young["threads"] if t["id"] == "uscn_tech")["state"] == "官方新文件"
    gone = T.archive([], now + 40 * 86400, old=arch, save=False)
    assert gone == []


def test_push_rules():
    import tools.sec_push as P
    d = {"days": 2, "threads": [{"id": "uscn_tech", "zh": "美中科技脫鉤", "state": "升溫", "n48": 3, "base": 0.5, "why": "w", "items": []},
                                {"id": "fed_path", "zh": "聯準會", "state": "官方新文件", "n48": 1, "base": 1, "why": "w",
                                 "items": [{"t": "FOMC statement", "u": "https://fed", "s": "聯準會", "ts": 1.79e9, "off": True}]}]}
    todo = P.threads_todo(d, {}, 1.8e9)
    assert [t["id"] for t in todo] == ["fed_path"]                     # 升溫 waits for 5 days of history; official doesn't
    d["days"] = 6
    assert [t["id"] for t in P.threads_todo(d, {"thread:fed_path": 1.8e9 - 3600}, 1.8e9)] == ["uscn_tech"]
    e = P.thread_embed(todo[0], ["・相關行情現在：x"])
    assert "官方新文件" in e["title"] and "📄 [FOMC statement](https://fed)" in e["description"] and "相關行情" in e["description"]


def test_card():
    from tools import site_threads as S
    now = time.time()
    S.VIEW.clear()
    S.VIEW.update(T.view([{"t": "TSMC tightens China AI chip curbs", "u": "https://x/a", "s": "B", "ts": now - 60}], now))

    class E:
        class market:
            @staticmethod
            def q(sym):
                return {"chg_pct": -10.7} if sym == "^SOX" else None
    h = S.sec_threads(E())
    assert "主線追蹤" in h and "美中科技脫鉤" in h and "費城半導體 -10.7%" in h and "資料從開始累積" in h
    import json
    import tempfile
    from pathlib import Path
    from unittest.mock import patch
    f = Path(tempfile.mkdtemp()) / "threads_read.json"
    f.write_text(json.dumps({"threads": {"uscn_tech": {"hypothesis": "從晶片擴大到模型", "for": ["三層收緊"], "against": ["只是研究"],
                                                       "confirm": ["法案"], "sources": [{"name": "報告", "url": "https://house.gov/r"}]}}}), encoding="utf-8")
    with patch.object(S, "READ", f):
        h = S.sec_threads(E())
    assert "📝 讀過原文的判斷" in h and "從晶片擴大到模型" in h and "只是研究" in h and 'href="https://house.gov/r"' in h and "<details class=\"sgx\" open>" in h


if __name__ == "__main__":
    test_match_and_view()
    test_push_rules()
    test_card()
    print("ok threads")
