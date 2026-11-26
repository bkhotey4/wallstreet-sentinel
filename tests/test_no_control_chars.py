"""No invisible control characters in code (11-26): a shell heredoc turned the two characters backslash-b into a real
backspace inside regexes, three times — ipo_data's AEDT/AEST check never matched, and research_press classified nothing.
Run: python -m tests.test_no_control_chars"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BAD = {chr(c) for c in range(32)} - {"\t", "\n", "\r", "\f"}


def test_no_control_chars():
    hits = []
    for p in list((ROOT / "tools").rglob("*.py")) + list((ROOT / "wsb").rglob("*.py")) + list((ROOT / "tests").rglob("*.py")):
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if any(ch in BAD for ch in line):
                hits.append(f"{p.relative_to(ROOT)}:{i}")
    assert not hits, "control characters (probably a mangled backslash escape): " + ", ".join(hits[:20])


if __name__ == "__main__":
    test_no_control_chars()
    print("ok no control chars")
