"""Which guide must have been read before an edit. Shared by decide.py (enforce) and check_reads.py (report).

Levels: "error" = decide.py blocks the edit until the guide is read; "warn" = only reported by check_reads.py.
"""
from __future__ import annotations

import json
from pathlib import Path


def is_page(path: str) -> bool:
    return path.startswith("docs/") and path.endswith(".html")


def required_guides(tool: str, path: str, content: str = "", is_new: bool = False) -> list[tuple[str, str, str]]:
    """Return (level, guide, reason) for an Edit/Write on repo-relative `path`."""
    needs = []
    if is_page(path):
        needs.append(("error", "guides/page-format.md", "페이지 HTML 수정"))
        if "<svg" in content:
            needs.append(("error", "guides/svg.md", "SVG 추가·수정"))
        if tool == "Write" and is_new:
            needs.append(("error", "guides/new-article.md", "새 페이지 생성"))
    if is_page(path) or path == "README.md":
        needs.append(("warn", "guides/writing.md", "본문 문장 수정 가능성"))
    if path.startswith("plan/"):
        needs.append(("warn", "guides/plan.md", "계획 파일 작성·수정"))
    return [n for n in needs if n[1] != path]


def reads_since_compaction(log: Path, session: str) -> set[str] | None:
    """Paths read in this session after its last compaction. None if the log is unavailable (caller must fail open)."""
    try:
        lines = log.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    reads: set[str] = set()
    for line in lines:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("session") != session[:8]:
            continue
        if r.get("event") == "PreCompact":
            reads.clear()
        elif r.get("tool") not in ("Edit", "Write"):
            reads.update(r.get("paths", []))
    return reads
