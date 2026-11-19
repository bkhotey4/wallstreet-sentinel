import json
import tempfile
from datetime import datetime
from pathlib import Path

from tools import site_event_board as EB
from tools import site_tracker as TR

NOW = datetime(2026, 11, 20, 1, 20, tzinfo=EB.TPE)
BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "買點", "何時買", "何時放棄", "加碼參考區", "進場參考區", "精選池", "未實現", "持倉")


def _d():
    return {"updated": "x", "events": [
        {"name": "舊事件", "when_tpe": "2026-11-10 21:30", "status": "done"},
        {"name": "下週", "when_tpe": "2026-11-25 21:30", "status": "upcoming"},
        {"name": "更晚", "when_tpe": "2026-12-10 03:00", "status": "upcoming"},
        {"name": "今晚", "when_tpe": "2026-11-19 22:30", "status": "live", "one": "ANT 開高",
         "symbols": [{"s": "ANT", "ref": 83, "ref_label": "發行價"}, {"s": "QQQ"}],
         "before": {"up": ["熱度擴散"], "down": ["資金搬家"], "odds": "一半一半"},
         "facts": ["開盤 111.50"]},
        {"bad": 1}]}


def test_pick_order_and_drop():
    names = [e["name"] for e in EB.pick(_d()["events"], NOW)]
    assert names == ["今晚", "下週", "更晚"], names


def test_render_static_fallback():
    h = EB.render(_d(), NOW)
    assert "一句話看懂：ANT 開高" in h
    assert 'data-evsym="ANT" data-evref="83.0"' in h and 'data-evsym="QQQ">' in h
    assert "熱度擴散" in h and "資金搬家" in h and "一半一半" in h and "開盤 111.50" in h
    assert "待事前分析" in h                      # upcoming events without a pre-analysis say so
    assert EB.render({}, NOW) == "" and EB.render({"events": []}, NOW) == ""


def test_load_bad_file():
    with tempfile.TemporaryDirectory() as t:
        p = Path(t) / "e.json"
        p.write_text("not json", encoding="utf-8")
        assert EB.load(p) == {}
        p.write_text(json.dumps(_d()), encoding="utf-8")
        assert len(EB.load(p)["events"]) == 5


def test_seed_file_and_wording():
    seed = Path(__file__).resolve().parents[2] / "wallstreet-sentinel" / "research_feed" / "event_board.json"
    if seed.exists():
        d = EB.load(seed)
        assert EB.render(d, NOW).count("evb") >= 2
    for txt in (EB.render(_d(), NOW), TR.sec_tracker(None), TR.NOTE, TR.JS, EB.JS):
        for w in BANNED:
            assert w not in txt, w


def test_tracker_js_filled():
    assert "__" not in TR.JS.replace("__proto__", "") and "__POLL__" not in EB.JS
    assert "localStorage" in TR.JS and "api/quote" in TR.JS and "TWD=X" in TR.JS


if __name__ == "__main__":
    test_pick_order_and_drop(); test_render_static_fallback(); test_load_bad_file(); test_seed_file_and_wording(); test_tracker_js_filled()
    print("ok")
