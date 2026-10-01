"""Mutation tests for tools/checks: break a copy of the site on purpose and make sure each rule notices.

  py tools/test_checks.py

When you add a rule after a problem (guides/lessons.md), add a mutation here that reproduces the problem.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import ROOT, run  # noqa: E402

# (rule id that must fire, file relative to repo root, text to find, replacement[, {extra file: content} created first])
REDIRECT_STUB = {"docs/os/98-old.html": '<!DOCTYPE html><title>x</title><meta http-equiv="refresh" content="0; url=01-process-thread.html"><h1>x</h1>'}
MUTATIONS = [
    ("links", "docs/os/01-process-thread.html", 'href="../index.html"', 'href="../nowhere.html"'),
    ("links", "docs/network/12-http.html", 'href="#idempotent"', 'href="#no-such-id"'),
    ("links", "docs/network/12-http.html", 'marker-end="url(#m12-a)"', 'marker-end="url(#m12-zz)"'),
    ("links", "docs/os/02-memory.html", 'href="../assets/style.css"', 'href="../assets/missing.css"'),
    ("links", "README.md", "/os/02-memory.html)", "/os/02-memoryy.html)"),
    # generated regions edited by hand, or articles.json changed without running build.py
    ("generated", "docs/os/08-virtual-thread.html", 'class="nx" href="../network/09-layers.html"', 'class="nx" href="../network/10-dns.html"'),
    ("generated", "docs/network/09-layers.html", "<span>← 이전 08</span>", "<span>← 이전 07</span>"),
    ("generated", "docs/os/07-thread-pool.html", "· 운영체제 · 07", "· 네트워크 · 07"),
    ("generated", "docs/database/19-explain.html", "· 19편", "· 18편"),
    ("generated", "docs/index.html", "<b>06</b>데드락", "<b>06</b>교착 상태"),
    ("generated", "README.md", "| [데드락]", "| [교착 상태]"),
    ("generated", "README.md", "01 → 05 → 06 → 21 → 22 → 26(캐시 키)", "01 → 05 → 06 → 21 → 22 → 26"),
    ("generated", "docs/index.html", "<td><b>일관성 트레이드오프</b>", "<td><b>일관성</b>"),
    ("generated", "docs/articles.json", '"title": "DNS와 요청의 전체 흐름"', '"title": "DNS와 요청 흐름"'),
    ("generated", "docs/articles.json", '"flow": [10, 24, 25, 26', '"flow": [10, 24, 25, 99'),  # prefix only: flows grow as articles are added
    ("generated", "docs/os/99-orphan.html", None, "<!DOCTYPE html><title>x</title><h1>x</h1>"),
    ("generated", "docs/index.html", "<!-- /gen:index-map -->", ""),
    # redirects (articles.json already has a "redirects" list; add one entry to it):
    # stub not built yet, target article missing, old address still used by a current article
    ("generated", "docs/articles.json", '"redirects": [\n', '"redirects": [\n    {"from": "os/00-old-name.html", "to": 1},\n'),
    ("generated", "docs/articles.json", '"redirects": [\n', '"redirects": [\n    {"from": "os/00-old-name.html", "to": 999},\n'),
    ("generated", "docs/articles.json", '"redirects": [\n', '"redirects": [\n    {"from": "os/01-process-thread.html", "to": 2},\n'),
    ("redirect-links", "docs/os/02-memory.html", 'href="../index.html"', 'href="98-old.html"', REDIRECT_STUB),
    ("banned-phrases", "docs/os/01-process-thread.html", "· 01편", "· 01 / 26"),
    ("titles", "docs/database/20-transaction.html", "<title>트랜잭션과 @Transactional</title>", "<title>트랜잭션</title>"),
    ("titles", "docs/articles.json", '"title": "가상 메모리와 페이지 캐시"', '"title": "가상 메모리"'),
    ("next-links", "docs/os/07-thread-pool.html", "<b>→ 08 가상 스레드</b>", "<b>→ 09 가상 스레드</b>"),
    ("next-links", "docs/database/21-isolation.html", "<b>→ 05 동기화 (복습)</b>", "<b>→ 05 동시성 (복습)</b>"),
    ("tags", "docs/os/05-sync.html", "</figure>", "</div>"),
    ("tags", "docs/network/11-tcp.html", "</details>", ""),
    ("banned-phrases", "docs/os/04-context-switch.html", "<p class=\"lead\">", "<p class=\"lead\">마지막 편입니다. "),
    ("svg-classes", "docs/network/12-http.html", 'class="bug-t">✕ 응답 1이', 'class="t-s bug-t">✕ 응답 1이'),
]


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "base"
        base.mkdir()
        shutil.copytree(ROOT / "docs", base / "docs")
        shutil.copy2(ROOT / "README.md", base / "README.md")
        _, baseline = run(base)
        baseline_keys = {(r.id, i.file, i.line, i.msg) for r, i in baseline}
        for n, (rule_id, rel, old, new, *extra) in enumerate(MUTATIONS, 1):
            work = Path(tmp) / f"m{n}"
            shutil.copytree(base, work)
            for extra_rel, content in (extra[0] if extra else {}).items():
                (work / extra_rel).write_text(content, encoding="utf-8")
            path = work / rel
            if old is None:  # create a new file
                path.write_text(new, encoding="utf-8")
            else:
                text = path.read_text(encoding="utf-8")
                if text.count(old) < 1:
                    print(f"SETUP  #{n} {rule_id}: text not found in {rel}: {old!r}")
                    failures += 1
                    shutil.rmtree(work)
                    continue
                path.write_text(text.replace(old, new, 1), encoding="utf-8")
            _, results = run(work)
            fired = [i for r, i in results if r.id == rule_id and (r.id, i.file, i.line, i.msg) not in baseline_keys]
            if not fired:
                print(f"MISSED #{n} {rule_id}: {rel} {old!r} -> {new!r}")
                failures += 1
            shutil.rmtree(work)
    print(f"{len(MUTATIONS) - failures}/{len(MUTATIONS)} mutations caught" if failures else f"OK ({len(MUTATIONS)} mutations caught)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
