"""build_site import aliases are unique (11-26: `site_freight as SFR` was shadowed by `site_fedreg as SFR` eight lines later,
and the CI build died with AttributeError: module 'tools.site_fedreg' has no attribute 'sec_freight').
Run: python -m tests.test_build_imports"""
import collections
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_unique_aliases():
    """The same alias for two different modules anywhere in the file (re-importing one module under its alias is fine)."""
    src = (ROOT / "tools" / "build_site.py").read_text(encoding="utf-8")
    seen = collections.defaultdict(set)
    for frm, mod, a in re.findall(r"^\s*(?:from (\S+) )?import (\S+) as (\w+)\s*$", src, re.M):
        seen[a].add(f"{frm}.{mod}" if frm else mod)
    dup = {a: sorted(m) for a, m in seen.items() if len(m) > 1}
    assert not dup, f"one alias for different modules in build_site.py: {dup}"


if __name__ == "__main__":
    test_unique_aliases()
    print("ok build imports")


def test_card_functions_exist():
    """Every `ALIAS.sec_x` the page list names exists on the module that alias points to (the 11-26 failure, by its effect)."""
    import tools.build_site as B
    src = (ROOT / "tools" / "build_site.py").read_text(encoding="utf-8")
    bad = sorted(f"{a}.{f}" for a, f in set(re.findall(r"\b([A-Z][A-Z0-9]+)\.(sec_\w+)", src)) if not hasattr(getattr(B, a, None), f))
    assert not bad, f"card functions not found: {bad}"


if __name__ == "__main__":
    test_card_functions_exist()
    print("ok card functions")
