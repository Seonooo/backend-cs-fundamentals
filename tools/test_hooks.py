"""Tests for tools/hooks: feed each hook the JSON Claude Code would send and check its reaction.

  py tools/test_hooks.py

Add a case here whenever a hook misses something in practice (guides/lessons.md).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "tools" / "hooks"


def run(script: str, payload: dict, env_log: Path | None = None) -> str:
    env = {**os.environ, "CLAUDE_ACCESS_LOG": str(env_log)} if env_log else None
    r = subprocess.run([sys.executable, str(HOOKS / script)], input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                       capture_output=True, cwd=ROOT, timeout=30, env=env)
    assert r.returncode == 0, f"{script} exited {r.returncode}: {r.stderr.decode('utf-8', 'replace')}"
    return r.stdout.decode("utf-8")  # also proves the output is valid UTF-8 (L-13)


def reminder(prompt: str) -> bool:
    out = run("on_prompt.py", {"hook_event_name": "UserPromptSubmit", "prompt": prompt})
    return bool(out.strip()) and "lessons.md" in json.loads(out)["hookSpecificOutput"]["additionalContext"]


CASES = [
    ("on_prompt: real correction from 2026-09-28 is detected", lambda: reminder("2번의 경우 텍스트가 맞아? 다시 생각해봐")),
    ("on_prompt: '틀렸' is detected", lambda: reminder("그 설명은 틀렸어")),
    ("on_prompt: approval is not flagged", lambda: not reminder("좋아 진행해")),
    ("on_prompt: plain request is not flagged", lambda: not reminder("README도 새 구조에 맞게 점검해줘")),
    ("log_access: survives invalid input", lambda: run("log_access.py", {}) == ""),
]


def decision(log_lines: list[dict] | None, tool: str, tool_input: dict) -> str:
    """Run decide.py against a temporary access log; return "deny", "warn" or "allow"."""
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "access.jsonl"
        if log_lines is not None:
            log.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in log_lines), encoding="utf-8")
        out = run("decide.py", {"hook_event_name": "PreToolUse", "session_id": "sess1234abcd", "tool_name": tool,
                                "tool_input": tool_input}, env_log=log).strip()
    if not out:
        return "allow"
    hso = json.loads(out)["hookSpecificOutput"]
    return "deny" if hso.get("permissionDecision") == "deny" else "warn"


PAGE = {"file_path": str(ROOT / "docs" / "os" / "01-process-thread.html"), "old_string": "a", "new_string": "b"}
SVG_EDIT = {**PAGE, "new_string": "<svg viewBox"}
READ = lambda path, session="sess1234": {"event": "PostToolUse", "session": session, "tool": "Read", "paths": [path]}  # noqa: E731
COMPACT = {"event": "PreCompact", "session": "sess1234"}

CASES += [
    ("decide: page edit without page-format.md → deny", lambda: decision([], "Edit", PAGE) == "deny"),
    ("decide: page edit after reading page-format.md → allow", lambda: decision([READ("guides/page-format.md")], "Edit", PAGE) == "allow"),
    ("decide: read in another session does not count", lambda: decision([READ("guides/page-format.md", "other000")], "Edit", PAGE) == "deny"),
    ("decide: read before compaction does not count", lambda: decision([READ("guides/page-format.md"), COMPACT], "Edit", PAGE) == "deny"),
    ("decide: SVG edit also needs svg.md", lambda: decision([READ("guides/page-format.md")], "Edit", SVG_EDIT) == "deny"),
    ("decide: SVG edit with both guides → allow", lambda: decision([READ("guides/page-format.md"), READ("guides/svg.md")], "Edit", SVG_EDIT) == "allow"),
    ("decide: new page needs new-article.md", lambda: decision([READ("guides/page-format.md")], "Write",
                                                               {"file_path": str(ROOT / "docs" / "os" / "99-new.html"), "content": "x"}) == "deny"),
    ("decide: non-page edit is never blocked", lambda: decision([], "Edit", {"file_path": str(ROOT / "tools" / "check.py")}) == "allow"),
    ("decide: missing access log fails open", lambda: decision(None, "Edit", PAGE) == "allow"),
    ("decide: heredoc with backslash → warn (L-15)", lambda: decision([], "Bash", {"command": "py - <<'EOF'\nprint('a\\\\b')\nEOF"}) == "warn"),
    ("decide: plain Bash → allow", lambda: decision([], "Bash", {"command": "git status"}) == "allow"),
]


def log_access_records_paths() -> bool:
    """Windows paths and Git Bash paths both map to repo-relative paths; failed Bash reads are kept (L-12)."""
    sys.path.insert(0, str(HOOKS))
    import log_access as h
    win = h.record({"hook_event_name": "PostToolUse", "tool_name": "Read",
                    "tool_input": {"file_path": str(ROOT / "guides" / "svg.md")}})
    bash_fail = h.record({"hook_event_name": "PostToolUseFailure", "tool_name": "Bash",
                          "tool_input": {"command": 'grep -n "x\\" guides/plan.md'}})
    failed_edit = h.record({"hook_event_name": "PostToolUseFailure", "tool_name": "Edit",
                            "tool_input": {"file_path": str(ROOT / "docs" / "index.html")}})
    return win["paths"] == ["guides/svg.md"] and bash_fail["paths"] == ["guides/plan.md"] and failed_edit is None


CASES.append(("log_access: path normalisation and failure handling", log_access_records_paths))


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    failed = 0
    for name, test in CASES:
        try:
            ok = test()
        except Exception as e:  # noqa: BLE001
            ok, name = False, f"{name} ({e})"
        if not ok:
            print(f"FAIL {name}")
            failed += 1
    print(f"{len(CASES) - failed}/{len(CASES)} hook tests passed" if failed else f"OK ({len(CASES)} hook tests)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
