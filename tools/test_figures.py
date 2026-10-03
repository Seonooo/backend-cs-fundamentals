"""Reproduction tests for tools/check_figures.py: break a copy of a figure on purpose and make sure each check notices.

  py tools/test_figures.py

Needs headless Chrome (and network for the web font, like the real check).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import ROOT  # noqa: E402
from check_figures import probe  # noqa: E402

PAGE = "docs/distributed/27-why-redis.html"
# (kind that must be reported, text to find, replacement)
MUTATIONS = [
    ("box", '<text x="51" y="64" text-anchor="middle">서버 1</text>',
     '<text x="51" y="64" text-anchor="middle">서버 1 (아주 긴 이름)</text>'),
    ("overlap", '<text x="20" y="200" class="bug-t">서로의 값을 못 봄</text>',
     '<text x="20" y="222" class="bug-t">서로의 값을 못 봄</text>'),
    ("out", '<text x="530" y="26" class="t-b">③ Redis에 둠</text>',
     '<text x="700" y="26" class="t-b">③ Redis에 둠 (공유 저장소)</text>'),
]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "docs"
        shutil.copytree(ROOT / "docs", base)
        original = (ROOT / PAGE).read_text(encoding="utf-8")
        pages = []
        for n, (kind, old, new) in enumerate(MUTATIONS, 1):
            if original.count(old) != 1:
                print(f"SETUP  #{n} {kind}: text not found once in {PAGE}: {old!r}")
                failures += 1
                continue
            page = base / "distributed" / f"zz-mutation-{n}.html"
            page.write_text(original.replace(old, new), encoding="utf-8")
            pages.append((n, kind, page))
        res = probe([p for _, _, p in pages] + [base / "distributed" / "27-why-redis.html"])
        if res is None:
            print("ERROR: headless Chrome did not finish the probe")
            return 2
        for n, kind, page in pages:
            hits = [r for r in res["problems"] if r["name"].endswith(page.name) and r["kind"] == kind]
            if not hits:
                print(f"MISSED #{n} {kind}")
                failures += 1
        clean = [r for r in res["problems"] if r["name"].endswith("27-why-redis.html")]
        if clean:
            print(f"BASELINE not clean: {clean}")
            failures += 1
    total = len(MUTATIONS)
    print(f"{total - failures}/{total} figure mutations caught" if failures else f"OK ({total} figure mutations caught)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
