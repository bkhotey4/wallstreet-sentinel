"""金額單位（11-18）：AI 供應鏈小公司加進財報倒數後，HP 顯示「市值約 0.0 兆美元」——一律用兆、沒有改用億的寫法，
小一點的數字就變成 0。這支掃 tools/ 與 wsb/：一行裡把金額除以 1e12 印成「兆」，同一行卻沒有條件（if）改用億，就算錯。
要印兆請用 tools.site_events.cap_txt（或同一行自己寫 `if v >= 1e12 else …億`）。Run: python -m tests.test_unit_words"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAD = re.compile(r"/\s*1e12\s*:[,.\d]*f\}\s*兆")


def offenders():
    out = []
    for d in ("tools", "wsb"):
        for f in (ROOT / d).rglob("*.py"):
            for n, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if BAD.search(line) and " if " not in line:
                    out.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()[:100]}")
    return out


def test_no_bare_trillion():
    got = offenders()
    assert not got, "金額只用兆、沒有改用億的寫法（小公司會印成 0.0 兆）：\n" + "\n".join(got)


def test_cap_txt():
    from tools.site_events import cap_txt
    assert cap_txt(2.4e10) == "240 億美元" and cap_txt(4.6e12) == "4.6 兆美元"


if __name__ == "__main__":
    test_cap_txt()
    print("ok test_cap_txt")
    test_no_bare_trillion()
    print("ok test_no_bare_trillion")
