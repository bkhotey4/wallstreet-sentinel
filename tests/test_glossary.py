"""名詞小辭典: every entry is a plain sentence, no advice wording, and the script reaches the page."""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools import site_glossary as SG  # noqa: E402

BANNED = ("目標價", "上漲空間", "低估", "高估", "買進", "賣出", "建議買", "建議賣")


def main():
    assert len(SG.GLOSS) >= 40
    for k, v in SG.GLOSS.items():
        assert k.strip() == k and v.endswith("。"), k
        assert 10 <= len(v) <= 90, (k, len(v))
        assert not any(b in v for b in BANNED), k
    assert "零 Gamma" in SG.JS and "wss:page" in SG.JS and ".gltip" in SG.CSS
    # the generated regex must compile in a browser engine (look-behind for the ASCII terms)
    try:
        js = SG.JS.replace("(function(){", "(function(){var document={documentElement:{lang:'zh'},querySelectorAll:function(){return []},"
                           "createElement:function(){return {setAttribute:function(){},style:{}}},body:{appendChild:function(){}},"
                           "addEventListener:function(){},getElementById:function(){return null}};var window={addEventListener:function(){},innerWidth:1000,innerHeight:800};", 1)
        r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=30)
        assert r.returncode == 0, r.stderr[-400:]
    except FileNotFoundError:
        pass                                                           # no node on this machine: skip the engine check
    # ASCII terms are matched whole: VIX must not light up inside VIX3M
    keys = sorted(SG.GLOSS, key=len, reverse=True)
    pat = "|".join((r"(?<![A-Za-z0-9])" + re.escape(k) + r"(?![A-Za-z0-9])") if re.match("[A-Za-z]", k) else re.escape(k) for k in keys)
    assert re.findall(pat, "VIX3M 比 VIX 高") == ["VIX3M", "VIX"]
    assert re.findall(pat, "跌破零 Gamma 翻轉點") == ["零 Gamma"]
    from tools import build_site
    assert build_site.SGL is SG
    print("ok")


if __name__ == "__main__":
    main()
